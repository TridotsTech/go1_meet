# Copyright (c) 2024, Tridots Tech and contributors
# For license information, please see license.txt

import frappe,requests,msal,json,pytz
from datetime import datetime,timedelta
from frappe.model.document import Document
from go1_meeting.go1_meeting.integration.validation import create_access_token_from_refresh_token

class MeetingIntegration(Document):
	pass

@frappe.whitelist()
def create_meeting(internal_attendees,external_attendees,from_time,to_time,subject,record,online):
	headers = get_headers()
	validate = validate_user_credentials(headers = headers)
	if validate.get("directory"):
		if validate.get("is_updated"):
			headers = get_headers()
		user_directory = validate.get("directory")
		meeting_users = []
		internal_attendees = json.loads(internal_attendees)
		external_attendees = json.loads(external_attendees) if external_attendees else []

		if internal_attendees:
			for i in internal_attendees:
				for j in user_directory:
					if j['mail'] == i['user']:
						meeting_users.append({"identity": {"user": {"id": j['id']}}})
		from_time , to_time = convert_local_to_utc(from_time,to_time)
		from_time = datetime.strftime(from_time,"%Y-%m-%dT%H:%M:%SZ")
		to_time = datetime.strftime(to_time,"%Y-%m-%dT%H:%M:%SZ")
		frappe.log_error("meet link utc",[from_time,to_time])
		meeting_data = {
			"subject": subject,
			"startDateTime": from_time,
			"endDateTime": to_time,
			"participants": {
				"attendees": meeting_users
				},
			"isOnlineMeeting": True if online else False, 
			"onlineMeetingProvider": "teamsForBusiness", 
			"recordAutomatically": True if record else False
			}
		# frappe.log_error("meeting_data",meeting_data)
		# frappe.log_error("meeting_data tp",type(meeting_data))
		response = requests.post(
			url="https://graph.microsoft.com/v1.0/me/onlineMeetings",
			headers=headers,
			json=meeting_data
		)
		frappe.log_error("meet response",response)
		frappe.log_error("meet response code",response.status_code)
		if response.status_code == 201:
			meeting_response = response.json()
			frappe.log_error("meeting_response json",meeting_response)
			join_url = meeting_response['joinUrl']
			frappe.log_error("join_url",join_url)
			
			return create_calender_event(meeting_response , headers , internal_attendees , external_attendees,user_directory,subject = subject )

def create_calender_event(data,headers,internal_attendees,external_attendees,user_directory,subject = None):
	people = []
	for i in internal_attendees:
		people.append({
					"emailAddress": {
						"address": i['user'],
						"name": frappe.db.get_value("User",i['user'],"full_name")
					},
					"type": "required"
					})	
	for j in external_attendees:
		people.append({
			"emailAddress": {
						"address": j['email'],
						"name": j['attendee_name']
			},
			"type": "required"
		})
	join_url = data['joinUrl']
	calendar_api_url = 'https://graph.microsoft.com/v1.0/me/events'
	frappe.log_error("people",people)
	event = {
			"subject": subject,
			"body": {
				"contentType": "HTML",
				"content": f"<h3>Please join the meeting using the following link: <a href='{join_url}'>Join the Meeting</a></h3>"
			},
			"start": {
				"dateTime": data['startDateTime'],
				"timeZone": frappe.db.get_value("User",frappe.session.user,"time_zone")
			},
			"end": {
				"dateTime": data["endDateTime"],
				"timeZone": frappe.db.get_value("User",frappe.session.user,"time_zone")
			},
			"location": {
				"displayName": "Microsoft Teams Meeting",
				 "locationUri":join_url
			},
			"attendees": people
		}
	cal_response = requests.post(calendar_api_url, headers=headers, json = event)
	frappe.log_error("cal response",cal_response.json())
	if cal_response.status_code == 201:
		return {"status":"success","join_url":join_url,
		  'event_id':cal_response.json()['id'],'meeting_id':data['id']}
	return{"status":"failed"}
	# frappe.log_error("cal_response json",cal_response.json())
	# frappe.log_error("cal_response",cal_response.status_code)


def convert_local_to_utc(from_time_str,to_time_str):
	datetime_format = "%Y-%m-%d %H:%M:%S"
	from_time_obj = datetime.strptime(from_time_str,datetime_format)
	to_time_obj = datetime.strptime(to_time_str,datetime_format)
	user_time_zone = frappe.db.get_value("User",frappe.session.user,"time_zone")
	local_from_time = pytz.timezone(user_time_zone).localize(from_time_obj)
	local_to_time = pytz.timezone(user_time_zone).localize(to_time_obj)
	utc_from_time = local_from_time.astimezone(pytz.timezone("UTC"))
	utc_to_time = local_to_time.astimezone(pytz.timezone("UTC"))
	frappe.log_error("utc_from_time",utc_from_time)
	frappe.log_error("utc_to_time",utc_to_time)
	return utc_from_time, utc_to_time

def convert_utc_to_local(from_time_str):
	from dateutil.parser import isoparse
	# Example timestamp
	timestamp = from_time_str
	# Parse the timestamp
	dt = isoparse(timestamp)
	# Format it to '%Y-%m-%dT%H:%M:%S'
	formatted_timestamp = dt.strftime('%Y-%m-%dT%H:%M:%SZ')
	utc_from_time_str = formatted_timestamp
	from_time = datetime.strptime(utc_from_time_str, "%Y-%m-%dT%H:%M:%SZ")
	utc = pytz.utc
	utc_from_time = utc.localize(from_time)
	local_tz = pytz.timezone(frappe.db.get_value("User",frappe.session.user,"time_zone")) 
	local_from_time = utc_from_time.astimezone(local_tz)
	# Format the result to only show date and time (excluding milliseconds)
	return local_from_time.strftime("%Y-%m-%d %H:%M:%S")

@frappe.whitelist()
def cancel_event(event_id):
	headers = get_headers()
	validate = validate_user_credentials(headers = headers)
	if validate.get("directory"):
		if validate.get("is_updated"):
			headers = get_headers()
	# event_id = 'AAMkAGMwZmM1ZTNkLTI2ZDUtNGM0My1hN2E3LWVhZjM5NzM2MDllNQBGAAAAAAD6y3yaxeGnR5BGS2eepRmWBwDML2N9N9lsRYVSK4VuVul-AAAAAAENAADML2N9N9lsRYVSK4VuVul-AAB9WYeeAAA='
	url = f"https://graph.microsoft.com/v1.0/me/events/{event_id}"
	headers = headers
	response = requests.delete(url, headers=headers)
	frappe.log_error("response",response.status_code)
	if response.status_code == 204:
		return {"status":"success"}

def get_headers():
	access_token = frappe.db.get_value("User Platform Credentials",{"user":frappe.session.user,"platform":"Teams"},['access_token'])
	if access_token:
		headers = {"Authorization": "Bearer " + access_token}
		return headers
	frappe.throw(f"{frappe.session.user} is not authorized to access this resource")
def validate_user_credentials(headers, is_updated = None):
	user_directory = get_users(headers)
	# frappe.log_error("user_directory_if",user_directory.status_code)

	if user_directory.status_code != 200:
		# frappe.log_error("user_directory if js",user_directory.json())
		refresh_token = frappe.db.get_value("User Platform Credentials",
				{"user":frappe.session.user,"platform":"Teams"},['refresh_token'])
		token_response = create_access_token_from_refresh_token(refresh_token)
		if "access_token" in token_response:
			exist = frappe.db.exists("User Platform Credentials",{"user":frappe.session.user,"platform":"Teams"})
			if exist:
				frappe.db.set_value("User Platform Credentials",exist,{
					"access_token":token_response['access_token'],
					"refresh_token":token_response['refresh_token']
				})
				frappe.db.commit()
			access_token = token_response['access_token']
			headers = {"Authorization": "Bearer " + access_token}
			is_updated = 1
			updated_directory = get_users(headers)
		if is_updated:
			return {'directory':updated_directory.json()['value'],"is_updated":1}
	return {'directory':user_directory.json()['value']}

def get_users(headers):
	user_directory = requests.get(
			url ="https://graph.microsoft.com/v1.0/users",
			headers=headers
		)
	return user_directory

@frappe.whitelist()
def edit_meeting(from_time,to_time,subject,event_id,meeting_id):
	headers = get_headers()
	validate = validate_user_credentials(headers = get_headers())
	if validate.get("directory"):
		if validate.get("is_updated"):
			headers = get_headers()
	# from_time = datetime.strftime(from_time,"%Y-%m-%d %H:%M:%S")
	# to_time = datetime.strftime(to_time,"%Y-%m-%d %H:%M:%S")
	frappe.log_error("from time type",type(from_time))
	from_time , to_time = from_time.replace(" ","T"),to_time.replace(" ","T")
	frappe.log_error("time format",[from_time,to_time])
	event_payload = {
		"subject": subject,
		"start": {
			"dateTime": from_time,
			"timeZone": frappe.db.get_value("User",frappe.session.user,"time_zone")
		},
		"end": {
			"dateTime": to_time,
			"timeZone": frappe.db.get_value("User",frappe.session.user,"time_zone")
		}
	}
	update_event = requests.patch(
		url = f"https://graph.microsoft.com/v1.0/me/events/{event_id}",
		headers = headers,
		json = event_payload
	)
	from_time,to_time = convert_local_to_utc(from_time.replace("T"," "),to_time.replace("T"," "))
	new_start_time_utc = datetime.strftime(from_time,"%Y-%m-%dT%H:%M:%SZ")
	new_end_time_utc = datetime.strftime(to_time,"%Y-%m-%dT%H:%M:%SZ")
	meet_payload = {
		"subject": subject,
		"startDateTime": new_start_time_utc,
        "endDateTime": new_end_time_utc
	}
	update_meeting = requests.patch(
		url = f"https://graph.microsoft.com/v1.0/me/onlineMeetings/{meeting_id}",
		headers = headers,
		json = meet_payload
	)
	frappe.log_error("update_meeting code",update_meeting.status_code)
	frappe.log_error("update_meeting",update_meeting.json())
	if update_meeting.status_code == 200:
		if update_event.status_code == 200:
			return {"status":"success"}
	return {"status":"failed"}	

@frappe.whitelist()
def get_attendance(meeting_id):
	headers = get_headers()
	validate = validate_user_credentials(headers = get_headers())
	if validate.get("directory"):
		if validate.get("is_updated"):
			headers = get_headers()
	attendance = requests.get(
		url = f"https://graph.microsoft.com/v1.0/me/onlineMeetings/{meeting_id}/attendanceReports",
		headers = headers
	)
	attendance_data = attendance.json()
	frappe.log_error("attendance data",[meeting_id,attendance_data])
	return fetch_attendance_reports(meeting_id,attendance_data['value'][0]['id'])

def fetch_attendance_reports(meeting_id,attendance_report_id):
	headers = get_headers()
	frappe.log_error("attendance report id",attendance_report_id)
	validate = validate_user_credentials(headers = get_headers())
	if validate.get("directory"):
		if validate.get("is_updated"):
			headers = get_headers()
	attendance = requests.get(
		url = f"https://graph.microsoft.com/v1.0/me/onlineMeetings/{meeting_id}/attendanceReports/{attendance_report_id}/attendanceRecords",
		headers = headers
	)
	data = []
	frappe.log_error("records josn",attendance.json())
	attendance_records = attendance.json()
	for i in attendance_records["value"]:
		data.append({
			'email':i['emailAddress'],
			'duration':str(timedelta(seconds=int(i['totalAttendanceInSeconds']))),
			'name':i['identity']['displayName'],
			'first_join':convert_utc_to_local(i['attendanceIntervals'][0]['joinDateTime']),
			'last_join':convert_utc_to_local(i['attendanceIntervals'][0]['leaveDateTime']),
			'role': i['role']
		})
	return {"status":"success","data":data}
