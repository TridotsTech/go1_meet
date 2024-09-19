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
        //Attendance API Call
        // if (frm.doc.url && frm.doc.platform =="Teams" && frm.doc.status != "Cancelled") {
        //     frappe.call({
        //         method: "go1_meeting.go1_meeting.doctype.meeting_integration.meeting_integration.get_attendance",
        //         args: {
        //             "doc": frm.doc
        //         },
        //         // freeze: true,
        //         // freeze_message: "Fetching attendence",
        //         callback(r) {
        //             let format_html = `<table class="roundedCorners">
        //                     <tr>
        //                         <th>Name</th>
        //                         <th>Mail</th>
        //                         <th>Duration</th>
        //                         <th>First join</th>
        //                         <th>Last join</th>
        //                         <th>Role</th>
        //                     </tr>`
        //             if (r.message) {
        //                 console.log(r.message)
        //                 if (r.message.status == "success") {
        //                     for (let i of r.message.data) {
        //                         let duration = i.duration.split(":")
        //                         format_html += `<tr>
        //                             <td>${i.name}</td>
        //                             <td>${i.email}</td>
        //                             <td>${(duration[0] > 0) ? duration[0] + "h " : ""}${(duration[1] > 0) ? duration[1] + "m " : ""}${(duration[2] > 0) ? duration[2] + "s" : ""}</td>
        //                             <td>${i.first_join}</td>
        //                             <td>${i.last_join}</td>
        //                             <td>${i.role}</td>
        //                         </tr>`
        //                     }
        //                     format_html += `</table>`
        //                     frm.fields_dict['attendance'].$wrapper.html(format_html)
        //                     // frappe.show_alert({
        //                     //     message: "Attendence fetched successfully",
        //                     //     indicator: "green"  
        //                     // }, 5)
        //                 }
        //             } else {
        //                 format_html = "<div>"
        //                 frm.fields_dict['attendance'].$wrapper.html(format_html)
        //             }
        //         }
        //     })
        // }
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
                    method: "go1_meeting.go1_meeting.integration.validation.",
                    args: {
                        doc: frm.doc
                    },
                    freeze: true,
                    freeze_message: "Authenticating and create meeting...",
                    callback(r) {
                        console.log(r.message)
                        if (r.message) {

                            if (frm.doc.platform == "Teams") {
                                if (r.message.status == "not_authorized") {
                                    window.location.href = r.message.message
                                } else if (r.message.status == "authorized") {
                                    frappe.call({
                                        method: 'go1_meeting.go1_meeting.doctype.meeting_integration.meeting_integration.create_teams_meeting',
                                        args: {
                                            internal_attendees: frm.doc.participants,
                                            external_attendees: frm.doc.external_participants,
                                            from_time: frm.doc.from,
                                            to_time: frm.doc.to,
                                            subject: frm.doc.subject,
                                            record: frm.doc.is_record_automatically,
                                            online: frm.doc.is_online_meeting
                                        },
                                        // async: false,
                                        freeze: true,
                                        freeze_message: "Creating meeting",
                                        callback(r) {
                                            // d.hide();
                                            if (r.message) {
                                                frm.set_value("url", r.message.join_url)
                                                frm.set_value("meeting_id", r.message.meeting_id)
                                                frm.set_value("event_id", r.message.event_id)
                                                frm.set_value("status", "Scheduled")
                                                frm.save()
                                            }
                                        }
                                    })
                                }
                            }
                            if (frm.doc.platform == "Zoom") {
                                console.log("Zoom", r.message)
                                if (r.message) {
                                    if (r.message.message == "authorized") {
                                        frappe.call({
                                            method: "go1_meeting.go1_meeting.doctype.meeting_integration.meeting_integration.create_zoom_meeting",
                                            args: {
                                                token: r.message.access_token,
                                                doc: frm.doc
                                            },
                                            freeze: true,
                                            freeze_message: "Creating Zoom Meeting...",
                                            callback(r) {
                                                console.log(r.message)
                                                if (r.message) {
                                                    if (r.message.id) {
                                                        frm.set_value("zoom_meeting_id", r.message.id)
                                                    }
                                                    frm.set_value("url", r.message.join_url)
                                                    frm.save()
                                                }
                                            }
                                        })
                                    }
                                }
                            }
                            if (frm.doc.platform == "Google Meet") {
                                console.log(r.message)
                                if (r.message.status == "authorized") {
                                    // window.location.href = r.message.url
                                    frappe.call({
                                        method:"go1_meeting.go1_meeting.doctype.meeting_integration.meeting_integration.create_google_meet",
                                        args:{
                                            doc:frm.doc
                                        },
                                        freeze:true,
                                        freeze_message : "Creating Google Meet...",
                                        callback(r){
                                            console.log(r.message)
                                            // if(r.message){
                                            //     frm.set_value("url",r.message)
                                            //     frm.save()
                                            // }
                                        }
                                    })
                                }
                            }
                            if (frm.doc.platform == "WhereBy") {
                                if (r.message.status == "success" && r.message.message == "authorized") {
                                    frappe.call({
                                        method: "go1_meeting.go1_meeting.doctype.meeting_integration.meeting_integration.create_whereby_room",
                                        args: {
                                            'doc': frm.doc
                                        },
                                        freeze: true,
                                        freeze_message: "Creating WhereBy Room...",
                                        callback(r) {
                                            if (r.message.status == "success") {
                                                frm.set_value("url",r.message.data.viewerRoomUrl)
                                                frm.set_value("host_room_url",r.message.data.hostRoomUrl)
                                                frm.set_value("meeting_id",r.message.data.meetingId)
                                                frm.save()
                                            }
                                        }
                                    })
                                }
                            }
                        }
                    }
                })
            })
        }

        if (frm.doc.url && frm.doc.status != "Cancelled") {
            if (frm.doc.platform == "Zoom") {
                var add_field = [
                    {
                        'label': 'Duration',
                        'fieldname': 'duration',
                        'fieldtype': 'Duration'
                    }
                ]
            }
            if (frm.doc.platform == "Teams") {
                add_field = [
                    {
                        'label': 'To Time',
                        'fieldname': 'to_time',
                        'fieldtype': 'Datetime'
                    }
                ]
            }
            if(frm.doc.platform == "Teams" && frm.doc.platform == "Zoom" && frm.doc.platform == "Google Meet" ){

                frm.add_custom_button("Edit Meeting", function () {
                    let fields = [
    
                        {
                            'label': 'Subject',
                            'fieldname': 'subject',
                            'fieldtype': 'Data'
                        },
                        {
                            'label': '',
                            'fieldname': 'section_break2',
                            'fieldtype': 'Section Break'
                        },
                        {
                            'label': 'From Time',
                            'fieldname': 'from_time',
                            'fieldtype': 'Datetime'
                        },
                        {
                            'label': '',
                            'fieldname': 'column_break_2',
                            'fieldtype': 'Column Break'
                        }
                    ].concat(add_field)
                    let d = new frappe.ui.Dialog({
                        title: "Edit meeting",
                        fields: fields,
                        primary_action: function (value) {
                            let args = {}
                            if (frm.doc.platform == "Teams") {
                                args = {
                                    "from_time": value.from_time,
                                    "to_time": value.to_time,
                                    "subject": value.subject,
                                    "event_id": frm.doc.event_id,
                                    "meeting_id": frm.doc.meeting_id
                                }
                            } else if (frm.doc.platform == "Zoom") {
                                args = {
                                    "from_time": value.from_time,
                                    // "to_time": value.to_time,
                                    "subject": value.subject,
                                    // "event_id": frm.doc.event_id,
                                    "meeting_id": frm.doc.zoom_meeting_id,
                                    "doc": frm.doc,
                                    "duration": value.duration
                                }
                            }
                            console.log(value.duration)
                            frappe.call({
                                method: "go1_meeting.go1_meeting.doctype.meeting_integration.meeting_integration.edit_meeting",
                                args: args,
                                freeze: true,
                                freeze_message: 'Updating meeting',
                                callback(r) {
                                    console.log(r.message)
                                    if (r.message) {
                                        if (r.message.status == "success") {
                                            frappe.show_alert({
                                                message: "Meeting updated successfully",
                                                indicator: "green"
                                            }, 5)
                                            frm.set_value("subject", value.subject)
                                            frm.set_value("from", value.from_time)
                                            if (frm.doc.platform == "Zoom") { frm.set_value("duration", value.duration) }
                                            if (frm.doc.platform == "Teams") { frm.set_value("to", value.to_time) }
                                            frm.save()
                                            d.hide()
                                        }
                                    }
                                }
                            })
                        }
                    })
                    d.fields_dict['subject'].value = frm.doc.subject
                    d.fields_dict['from_time'].value = frm.doc.from
                    frm.doc.platform == "Teams" ? d.fields_dict['to_time'].value = frm.doc.to : ""
                    d.refresh()
                    d.show()
                }, __("Actions"))
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
                            } else {
                                format_html = "<div>"
                                frm.fields_dict['attendance'].$wrapper.html(format_html)
                            }
                        }
                    })
                })
            }
            frm.add_custom_button('Cancel Meeting', function () {
                frappe.confirm("Do you need to cancel the meeting", () => {
                    console.log("working")
                    if (frm.doc.platform == "Teams") {
                        frappe.call({
                            method: "go1_meeting.go1_meeting.doctype.meeting_integration.meeting_integration.cancel_event",
                            args: {
                                event_id: frm.doc.event_id,
                                platform: frm.doc.platform
                            },
                            freeze: true,
                            freeze_message: "cancelling meeting",
                            callback(r) {
                                if (r.message) {
                                    console.log(r.message)
                                    if (r.message.status == "success") {
                                        // window.location.href = r.message
                                        frm.set_value("status", "Cancelled")
                                        frm.save()
                                        console.log("success")

                                    }
                                }
                            }
                        })
                    } else if (frm.doc.platform == "Zoom") {
                        frappe.call({
                            method: "go1_meeting.go1_meeting.doctype.meeting_integration.meeting_integration.cancel_event",
                            args: {
                                event_id: frm.doc.zoom_meeting_id,
                                platform: frm.doc.platform,
                                doc: frm.doc
                            },
                            freeze: true,
                            freeze_message: "cancelling meeting",
                            callback(r) {
                                if (r.message) {
                                    console.log(r.message)
                                    if (r.message.status == "success") {
                                        frm.set_value("status", "Cancelled")
                                        frm.save()
                                    }
                                }
                            }
                        })
                    }
                    else if(frm.doc.platform == "WhereBy"){
                        frappe.call({
                            method: "go1_meeting.go1_meeting.doctype.meeting_integration.meeting_integration.cancel_event",
                            args: {
                                event_id: frm.doc.meeting_id,
                                platform: frm.doc.platform,
                                doc: frm.doc
                            },
                            freeze: true,
                            freeze_message: "cancelling meeting",
                            callback(r) {
                                if (r.message) {
                                    console.log(r.message)
                                    if (r.message.status == "success") {
                                        frm.set_value("status", "Cancelled")
                                        frm.save()
                                    }
                                }
                            }
                        })
                    }
                }), () => {

                }
            }, __("Actions"))

            if(frm.doc.host_room_url && frm.doc.status != "Cancelled"){
                frm.add_custom_button("Join Meeting", function () {
                    window.open(`/app/whereby-embed?meeting_id=${frm.doc.host_room_url}`,'_blank')
                })
                // frm.add_custom_button("Customize Room",function(){
                //     let d = 
                // })
            }
            if(frm.doc.platform == "Google Meet"){
                frm.add_custom_button('Add Calendar',{
                    method:"go1_meeting.go1_meeting.doctype.meeting_integration.meeting_integration.create_gmeet",
                    
                })
            }
        }

        if(!frm.doc.url && frm.doc.status != "Cancelled" && state == "authorized"){
            if(frm.doc.platform == "Google Meet"){
                frappe.call({   
                    method : "go1_meeting.go1_meeting.doctype.meeting_integration.meeting_integration.check_calendar",
                    args:{
                        "doc":frm.doc
                    },

                })
            }
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