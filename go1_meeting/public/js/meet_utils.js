frappe.provide("go1_meeting.meeting")
go1_meeting.meeting.auth_callback = function (frm, r) {
    if (frm.doc.platform == "Teams") {
        this.teams_meeting_callback(frm, r)
    } else if (frm.doc.platform == "Zoom") {
        this.zoom_meeting_callback(frm, r)
    } else if (frm.doc.platform == "Google Meet") {
        this.google_meet_callback(frm, r)
    } else if (frm.doc.platform == "WhereBy") {
        this.whereby_callback(frm, r)
    }

}
go1_meeting.meeting.call_cancel = function (frm, r) {
    let args;
    if (frm.doc.platform == "Teams") {
        args = {
            event_id: frm.doc.event_id,
            platform: frm.doc.platform
        }
    } else if (frm.doc.platform == "Zoom") {
        args = {
            event_id: frm.doc.zoom_meeting_id,
            platform: frm.doc.platform,
            doc: frm.doc
        }
    } else if (frm.doc.platform == "Google Meet") {
        args = {
            event_id: frm.doc.meeting_id,
            platform: frm.doc.platform,
            doc: frm.doc
        }
    } else if (frm.doc.platform == "WhereBy") {
        args = {
            event_id: frm.doc.meeting_id,
            platform: frm.doc.platform,
            doc: frm.doc
        }
    }
    this.cancel_meeting(frm, args)
}
go1_meeting.meeting.cancel_meeting = function (frm, args) {
    frappe.call({
        method: "go1_meeting.go1_meeting.doctype.meeting_integration.meeting_integration.cancel_event",
        args: args,
        freeze: true,
        freeze_message: "Cancelling meeting",
        callback(r) {
            if (r.message) {
                if (r.message.status == "success") {
                    frm.set_value("status", "Cancelled")
                    frm.save()
                }
            }
        }
    })
}


go1_meeting.meeting.teams_meeting_callback = function (frm, r) {
    if (r.message) {
        if (r.message.status == "not_authorized") {
            window.location.href = r.message.message
        }
        else if (r.message.status == "authorized") {
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
}

go1_meeting.meeting.zoom_meeting_callback = function (frm, r) {
    if (r.message) {
        if (r.message.message == "authorized") {
            console.log("working from meet utils")
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
                        frm.set_value("host_room_url", r.message.start_url)
                        frm.set_value("status", "Scheduled")
                        frm.save()
                    }
                }
            })
        }
    }
}

go1_meeting.meeting.google_meet_callback = function (frm, r) {
    if (r.message.status == "authorized") {
        // window.location.href = r.message.url
        frappe.call({
            method: "go1_meeting.go1_meeting.doctype.meeting_integration.meeting_integration.create_google_meet",
            args: {
                doc: frm.doc
            },
            freeze: true,
            freeze_message: "Creating Google Meet...",
            callback(r) {
                console.log(r.message)
                if (r.message && r.message.status == "success") {
                    frm.set_value("url", r.message.message.hangoutLink)
                    frm.set_value("meeting_id", r.message.message.id)
                    frm.set_value("g_calendar_id", r.message.calendar_id)
                    frm.save()
                }
            }
        })
    }
}

go1_meeting.meeting.whereby_callback = function (frm, r) {
    if (r.message.status == "success" && r.message.message == "authorized") {
        frappe.call({
            method: "go1_meeting.go1_meeting.doctype.meeting_integration.meeting_integration.create_whereby_room",
            args: {
                'doc': frm.doc
            },
            freeze: true,
            freeze_message: "Creating WhereBy Room...",
            callback(r) {
                console.log(r.message)
                if (r.message.status == "success") {
                    frm.set_value("url", r.message.data.viewerRoomUrl)
                    frm.set_value("host_room_url", r.message.data.hostRoomUrl)
                    frm.set_value("meeting_id", r.message.data.meetingId)
                    frm.set_value("status", "Scheduled")
                    frm.save()
                }
            }
        })
    }
}

go1_meeting.meeting.call_edit_meeting = function (frm) {
    let add_field;
    if (frm.doc.platform == "Zoom") {
        add_field = [
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
                        "meeting_id": frm.doc.meeting_id,
                        "doc": frm.doc
                    }
                } else if (frm.doc.platform == "Zoom") {
                    args = {
                        "from_time": value.from_time,
                        "subject": value.subject,
                        "meeting_id": frm.doc.zoom_meeting_id,
                        "doc": frm.doc,
                        "duration": value.duration
                    }
                }
                go1_meeting.meeting.edit_meeting(frm, args, d)
            }
        })
        d.fields_dict['subject'].value = frm.doc.subject
        d.fields_dict['from_time'].value = frm.doc.from
        frm.doc.platform == "Teams" ? d.fields_dict['to_time'].value = frm.doc.to : ""
        d.refresh()
        d.show()
    }, __("Actions"))
}

go1_meeting.meeting.edit_meeting = function (frm, args, d) {
    frappe.call({
        method: "go1_meeting.go1_meeting.doctype.meeting_integration.meeting_integration.edit_meeting",
        args: args,
        freeze: true,
        freeze_message: 'Updating meeting',
        callback(r) {
            console.log(r.message)
            if (r.message) {
                if (r.message.status == "success") {
                    d.hide()
                    frappe.show_alert({
                        message: "Meeting updated successfully",
                        indicator: "green"
                    }, 5)
                    frm.set_value("subject", args.subject)
                    frm.set_value("from", args.from_time)
                    if (frm.doc.platform == "Zoom") { frm.set_value("duration", args.duration) }
                    if (frm.doc.platform == "Teams") { frm.set_value("to", args.to_time) }
                    frm.save()
                }
            }
        }
    })
}

go1_meeting.meeting.join_meeting = function (frm) {
    if (frm.doc.platform == "WhereBy" && frm.doc.host_room_url && frm.doc.status != "Cancelled") {
        frm.add_custom_button("Join Meeting", function () {
            window.open(`/app/whereby-embed?meeting_id=${frm.doc.host_room_url}`, '_blank')
        })
    }
}

go1_meeting.meeting.append_attendance_styles = function () {
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
}
go1_meeting.meeting.fetch_attendace = function (frm) {
    if ((frm.doc.platform == "Zoom" || frm.doc.platform == "Teams") && frm.doc.status != "Cancelled") {
        frm.add_custom_button("Fetch Participants", function () {
            frappe.call({
                method: "go1_meeting.go1_meeting.doctype.meeting_integration.meeting_integration.get_attendance",
                args: {
                    "doc": frm.doc
                },
                freeze: true,
                freeze_message: "Fetching attendence",
                callback(r) {
                    if (r.message) {
                        console.log(r.message)
                        if (r.message.status == "success") {
                            frm.set_value("attendance_json", JSON.stringify(r.message.data))
                            frm.save()
                            frappe.show_alert({
                                message: "Attendence fetched successfully",
                                indicator: "green"
                            }, 5)
                        }
                    }
                }
            })
        })
    }
}

go1_meeting.meeting.show_attendance = function (frm) {
    if ((frm.doc.platform == "Zoom" || frm.doc.platform == "Teams") && frm.doc.status != "Cancelled") {
        let format_html = ""
        if (frm.doc.attendance_json && frm.doc.platform == "Teams") {
            let data = JSON.parse(frm.doc.attendance_json)
            if (data.length > 0) {
                frm.set_df_property("attendance", "options", "")
                format_html = `<table class="roundedCorners">
                                <tr>
                                    <th>Name</th>
                                    <th>Mail</th>
                                    <th>Duration</th>
                                    <th>First Join</th>
                                    <th>Last Leave</th>
                                    <th>Role</th>
                                </tr>`
                for (let i of JSON.parse(frm.doc.attendance_json)) {
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
            } else {

                let dummy_data = `<div style="min-height:350px;display:flex;align-items:center;justify-content:center;"><h5><i class="fa fa-history" style="font-size:18px;"></i> No Attendance....</h5></div>`
                frm.set_df_property("attendance", "options", dummy_data)
                frm.refresh_field("attendance")
            }
        }

        if (format_html.length == 0) {
            if (frm.doc.platform == "Zoom" && frm.doc.attendance_json) {
                let data = JSON.parse(frm.doc.attendance_json)
                if (data.length > 0 || frm.doc.attendance_json) {
                    frm.set_df_property("attendance", "options", "")
                    let teams_format_html = `<table class="roundedCorners">
                                <tr>
                                    <th>Name</th>
                                    <th>Mail</th>
                                    <th>Duration</th>
                                    <th>First join</th>
                                    <th>Last join</th>
                                    <th>Role</th>
                                </tr>`
                    for (let i of JSON.parse(frm.doc.attendance_json)) {
                        let duration = i.duration.split(":")
                        teams_format_html += `<tr>
                        <td>${i.name}</td>
                        <td>${i.email}</td>
                        <td>${(duration[0] > 0) ? duration[0] + "h " : ""}${(duration[1] > 0) ? duration[1] + "m " : ""}${(duration[2] > 0) ? duration[2] + "s" : ""}</td>
                        <td>${i.first_join}</td>
                        <td>${i.last_join}</td>
                        <td>${i.role}</td>
                    </tr>`
                    }
                    teams_format_html += `</table>`
                    frm.fields_dict['attendance'].$wrapper.html(teams_format_html)
                }
            } else {
                console.log("working in zoom else")
                let dummy_data = `<div style="min-height:350px;display:flex;align-items:center;justify-content:center;"><h5><i class="fa fa-history" style="font-size:18px;"></i> No Attendance....</h5></div>`
                frm.set_df_property("attendance", "options", dummy_data)
                frm.refresh_field("attendance")
            }
        }
    }
}
