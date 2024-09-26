// Copyright (c) 2024, Tridots Tech and contributors
// For license information, please see license.txt

frappe.ui.form.on("Go1 Meet", {
    refresh(frm) {
        const searchParam = new URLSearchParams(window.location.search)
        console.log(searchParam.has("state"))
        if (searchParam.has("state")) {
            console.log("working...")
        }
        console.log(searchParam.get("state"))
        const state = searchParam.get("state")
        $('head').append(`
            <style>
            table.roundedCorners { 
              border: 1px solid #d1d8dd;
              border-radius: 13px; 
              border-spacing: 0;
              width: 100%;
            }
            table.roundedCorners td, 
            table.roundedCorners th { 
              border-right: 1px solid #d1d8dd;
              border-bottom: 1px solid #d1d8dd;
              padding: 10px; 
            }
            table.roundedCorners tr:last-child > td {
              border-bottom: none;
            }
            table.roundedCorners tr > td:last-child, 
            table.roundedCorners tr > th:last-child {
              border-right: none;
            }
            table.roundedCorners tr:first-child th:first-child {
              border-top-left-radius: 13px;
            }
            table.roundedCorners tr:first-child th:last-child {
              border-top-right-radius: 13px;
            }
            table.roundedCorners tr:last-child td:first-child {
              border-bottom-left-radius: 13px;
            }
            table.roundedCorners tr:last-child td:last-child {
              border-bottom-right-radius: 13px;
            }
            </style>
        `);
        let platform = frm.doc.platform
        if (!frm.doc.__islocal && !frm.doc.url && !frm.doc.__unsaved) {
            frm.add_custom_button(`Create ${platform} Meeting`, function () {
                frappe.call({
                    method: "go1_meeting.go1_meeting.integration.validation.authorize_user_access_token",
                    args: {
                        doc: frm.doc
                    },
                    freeze: true,
                    freeze_message: "Authenticating and create meeting...",
                    callback(r) {
                        if (r.message) {
                            go1_meeting.meeting.auth_callback(frm, r)
                        }
                    }
                })
            })
        }

        if (frm.doc.url && frm.doc.status != "Cancelled") {
            if (frm.doc.platform == "Teams" || frm.doc.platform == "Zoom") {
                go1_meeting.meeting.call_edit_meeting(frm)
                frm.add_custom_button("Fetch Attendence", function () {
                    frappe.call({
                        method: "go1_meeting.go1_meeting.doctype.meeting_integration.meeting_integration.get_attendance",
                        args: {
                            "doc": frm.doc
                        },
                        freeze: true,
                        freeze_message: "Fetching attendence",
                        callback(r) {
                            if (frm.doc.platform == "Zoom") {
                                if (r.message) {
                                    console.log(r.message)
                                }
                            }
                            let format_html = `<table class="roundedCorners">
                                    <tr>
                                        <th>Name</th>
                                        <th>Mail</th>
                                        <th>Duration</th>
                                        <th>First join</th>
                                        <th>Last join</th>
                                        <th>Role</th>
                                    </tr>`
                            if (r.message) {
                                console.log(r.message)
                                if (r.message.status == "success") {
                                    for (let i of r.message.data) {
                                        let duration = i.duration.split(":")
                                        format_html += `<tr>
                                            <td>${i.name}</td>
                                            <td>${i.email}</td>
                                            <td>${(duration[0] > 0) ? duration[0] + "h " : ""}${(duration[1] > 0) ? duration[1] + "m " : ""}${(duration[2] > 0) ? duration[2] + "s" : ""}</td>
                                            <td>${i.first_join}</td>
                                            <td>${i.last_join}</td>
                                            <td>${i.role}</td>
                                        </tr>`
                                    }
                                    format_html += `</table>`
                                    frm.fields_dict['attendance'].$wrapper.html(format_html)
                                    frappe.show_alert({
                                        message: "Attendence fetched successfully",
                                        indicator: "green"
                                    }, 5)
                                }
                            } else if (r.message.status == "pending") {
                                console.log("penfing")
                            } else {

                            }
                        }
                    })
                })
            }
            frm.add_custom_button('Cancel Meeting', function () {
                frappe.confirm("Do you need to cancel the meeting", () => {
                    go1_meeting.meeting.call_cancel(frm)
                }), () => {
                }
            }, __("Actions"))
            go1_meeting.meeting.join_meeting(frm)
        }
    },
    platform(frm) {
        if (frm.doc.platform == "Zoom") {
            get_meeting_id(frm)
            frm.set_value("is_secured", 1)
            let random_str = generate_random_string(6)
            console.log(random_str)
            frm.set_value("generate_meeting_id", 1)
            frm.set_value("passcode", random_str)
            frm.set_df_property("is_record_automatically", "description", "For zoom record will store in local")
        } else {
            frm.set_value("is_secured", 0)
        }
    },
    generate_meeting_id(frm) {
        if (frm.doc.generate_meeting_id) {
            frm.set_df_property("zoom_meeting_id", "description", "if generate meeting is checked then meeting id will be generated automatically")
        } else {
            frm.set_df_property("zoom_meeting_id", "description", "")
        }
    }
});
function generate_random_string(length) {
    const characters = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789';
    let result = '';
    const characters_length = characters.length
    for (let i = 0; i < length; i++) {
        result += characters.charAt(Math.floor(Math.random() * characters_length))
    }
    return result
}
function get_meeting_id(frm) {
    if (frm.doc.platform == "Zoom") {
        frappe.call({
            method: "go1_meeting.go1_meeting.integration.validation.authorize_zoom",
            args: {
                "doc": frm.doc
            },
            callback(r) {
                if (r.message) {
                    console.log(r.message)
                    frm.set_value("zoom_meeting_id", r.message.auth_response.pmi)
                }
            }
        })
    }
}