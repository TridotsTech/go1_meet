// Copyright (c) 2024, Tridots Tech and contributors
// For license information, please see license.txt

frappe.ui.form.on("Go1 Meet", {
    refresh(frm) {
        //Attendance API Call
        if(frm.doc.url){
            frappe.call({
                method: "go1_meeting.go1_meeting.doctype.meeting_integration.meeting_integration.get_attendance",
                args: {
                    "meeting_id": frm.doc.meeting_id
                },
                // freeze: true,
                // freeze_message: "Fetching attendence",
                callback(r) {
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
                            for(let i of r.message.data){
                                let duration = i.duration.split(":")
                                format_html += `<tr>
                                    <td>${i.name}</td>
                                    <td>${i.email}</td>
                                    <td>${(duration[0]>0)?duration[0]+"h ": ""}${(duration[1]>0)?duration[1]+"m ":""}${(duration[2]>0)?duration[2]+"s":""}</td>
                                    <td>${i.first_join}</td>
                                    <td>${i.last_join}</td>
                                    <td>${i.role}</td>
                                </tr>`
                            }
                            format_html+=`</table>`
                            frm.fields_dict['attendance'].$wrapper.html(format_html) 
                            // frappe.show_alert({
                            //     message: "Attendence fetched successfully",
                            //     indicator: "green"  
                            // }, 5)
                        }
                    }else{
                        format_html = "<div>"
                        frm.fields_dict['attendance'].$wrapper.html(format_html) 
                    }
                }
            })
        }
        
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
        if (!frm.doc.__islocal && !frm.doc.url) {
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
                            console.log(r.message)
                            if (r.message.status == "not_authorized") {
                                window.location.href = r.message.message
                            } else if (r.message.status == "authorized") {
                                frappe.call({
                                    method: 'go1_meeting.go1_meeting.doctype.meeting_integration.meeting_integration.create_meeting',
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
                    }
                })
            })
        }

        if (frm.doc.url) {
            frm.add_custom_button("Edit Meeting", function () {
                let d = new frappe.ui.Dialog({
                    title: "Edit meeting",
                    fields: [

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
                        },
                        {
                            'label': 'To Time',
                            'fieldname': 'to_time',
                            'fieldtype': 'Datetime'
                        }
                    ],
                    primary_action: function (value) {
                        console.log(value)
                        frappe.call({
                            method: "go1_meeting.go1_meeting.doctype.meeting_integration.meeting_integration.edit_meeting",
                            args: {
                                "from_time": value.from_time,
                                "to_time": value.to_time,
                                "subject": value.subject,
                                "event_id":frm.doc.event_id,
                                "meeting_id": frm.doc.meeting_id
                            }, freeze: true,
                            freeze_message: 'Updating meeting',
                            callback(r) {
                                if (r.message) {
                                    if (r.message.status == "success") {
                                        frappe.show_alert({
                                            message: "Meeting updated successfully",
                                            indicator: "green"
                                        }, 5)
                                        frm.set_value("subject",value.subject)
                                        frm.set_value("from",value.from_time)
                                        frm.set_value("to",value.to_time)
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
                d.fields_dict['to_time'].value = frm.doc.to
                d.refresh()
                d.show()
            }, __("Actions"))
            frm.add_custom_button('Cancel Meeting', function () {
                frappe.confirm("Do you need to cancel the meeting", () => {
                    console.log("working")
                    frappe.call({
                        method: "go1_meeting.go1_meeting.doctype.meeting_integration.meeting_integration.cancel_event",
                        args: {
                            event_id: frm.doc.event_id
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
                }), () => {

                }
            }, __("Actions"))

            frm.add_custom_button("Fetch Attendence",function(){
                frappe.call({
                    method: "go1_meeting.go1_meeting.doctype.meeting_integration.meeting_integration.get_attendance",
                    args: {
                        "meeting_id": frm.doc.meeting_id
                    },
                    freeze: true,
                    freeze_message: "Fetching attendence",
                    callback(r) {
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
                                for(let i of r.message.data){
                                    let duration = i.duration.split(":")
                                    format_html += `<tr>
                                        <td>${i.name}</td>
                                        <td>${i.email}</td>
                                        <td>${(duration[0]>0)?duration[0]+"h ": ""}${(duration[1]>0)?duration[1]+"m ":""}${(duration[2]>0)?duration[2]+"s":""}</td>
                                        <td>${i.first_join}</td>
                                        <td>${i.last_join}</td>
                                        <td>${i.role}</td>
                                    </tr>`
                                }
                                format_html+=`</table>`
                                frm.fields_dict['attendance'].$wrapper.html(format_html) 
                                frappe.show_alert({
                                    message: "Attendence fetched successfully",
                                    indicator: "green"  
                                }, 5)
                            }
                        }else{
                            format_html = "<div>"
                            frm.fields_dict['attendance'].$wrapper.html(format_html) 
                        }
                    }
                })
            })
        }
    },
});
