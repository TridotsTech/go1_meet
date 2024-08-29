// Copyright (c) 2024, Tridots Tech and contributors
// For license information, please see license.txt

frappe.ui.form.on("Meeting Integration", {
    refresh(frm) {
        let platform = frm.doc.platform
        frm.add_custom_button(`Create ${platform} Meeting`, function () {
            frappe.call({
                method: "go1_meeting.go1_meeting.integration.validation._redirect_uri",
                args: {
                    doc: frm.doc
                },
                freeze: true,
                freeze_message: "Authenticating user",
                callback(r) {
                    if (r.message) {
                        window.location.href = r.message
                    }
                }
            })
            
        })
       
    },
});

// let d = new frappe.ui.Dialog({
//     title: "Sign in with your teams account",
//     fields: [
//         {
//             'label': 'Username',
//             'fieldname': 'username',
//             'fieldtype': 'Data',
//             'reqd': 1
//         },
//         {
//             'label': 'Password',
//             'fieldname': 'password',
//             'fieldtype': 'Password',
//             'reqd': 1
//         }
//     ],
//     size: 'small',
//     primary_action: function (values) {
//         frappe.call({
//             method: 'go1_meeting.go1_meeting.integration.validation.create_access_token',
//             args: {
//                 doc:frm.doc,
//                 usr: values.username,
//                 pwd: values.password
//             },
//             freeze: true,
//             freeze_message: "Authenticating... and create meeting",
//             callback(r) {
                
//             }
//         })
//         d.hide();
//     },
// })
// // d.show();
// // }else{
// // console.log("Already Logged in")
// // let meet = new frappe.ui.Dialog({
// //     title:"New teams meeting",
// //     fields:[
// //         {
// //             'label': 'Subject',
// //             'fieldname': 'subject',
// //             'fieldtype': 'Data',
// //             'reqd': 1
// //         },
// //         {
// //             'label': 'Start Time',
// //             'fieldname': 'start_time',
// //             'fieldtype': 'Datetime',
// //             'reqd': 1
// //         },
// //         {
// //             'label': 'End Time',
// //             'fieldname': 'end_time',
// //             'fieldtype': 'Datetime',
// //             'reqd': 1
// //         }
// //     ],
// //     primary_action: function (values) {
// //         console.log(values)
// //         console.log(frm.doc.meeting_participants)
// //         frappe.call({
// //             method: 'go1_meeting.go1_meeting.doctype.meeting_integration.meeting_integration.create_meeting_link',
// //             args: {
// //                 attendees:frm.doc.meeting_participants,
// //                 subject: values.subject,
// //                 from_time: values.start_time,
// //                 to_time: values.end_time
// //             },
// //             // async: false,
// //             freeze: true,
// //             freeze_message: "Creating meeting",
// //             callback(r) {
// //                 // d.hide();
// //             }
// //         })
// //     }
// // })
// // meet.show()