# Copyright (c) 2024, Tridots Tech and contributors
# For license information, please see license.txt

import frappe,requests,msal,json,pytz
from datetime import datetime,timedelta
from frappe.model.document import Document
from go1_meeting.go1_meeting.integration.validation import validate_gmeet_user
from go1_meeting.go1_meeting.integration.validation import create_access_token_from_refresh_token,authorize_zoom

class MeetingIntegration(Document):
	pass

@frappe.whitelist()
def create_teams_meeting(internal_attendees,external_attendees,from_time,to_time,subject,record,online):
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


def convert_local_to_utc(from_time_str,to_time_str=None):
	datetime_format = "%Y-%m-%d %H:%M:%S"
	from_time_obj = datetime.strptime(from_time_str,datetime_format)
	to_time_obj = datetime.strptime(to_time_str,datetime_format) if to_time_str else None
	user_time_zone = frappe.db.get_value("User",frappe.session.user,"time_zone")
	local_from_time = pytz.timezone(user_time_zone).localize(from_time_obj)
	local_to_time = pytz.timezone(user_time_zone).localize(to_time_obj) if to_time_obj else None
	utc_from_time = local_from_time.astimezone(pytz.timezone("UTC"))
	utc_to_time = local_to_time.astimezone(pytz.timezone("UTC")) if local_to_time else None
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
def cancel_event(event_id,platform,doc = None):
	if(platform == "Teams"):
		headers = get_headers()
		validate = validate_user_credentials(headers = headers)
		if validate.get("directory"):
			if validate.get("is_updated"):
				headers = get_headers()
		# event_id = 'AAMkAGMwZmM1ZTNkLTI2ZDUtNGM0My1hN2E3LWVhZjM5NzM2MDllNQBGAAAAAAD6y3yaxeGnR5BGS2eepRmWBwDML2N9N9lsRYVSK4VuVul-AAAAAAENAADML2N9N9lsRYVSK4VuVul-AAB9WYeeAAA='
		url = f"https://graph.microsoft.com/v1.0/me/events/{event_id}"
		headers = headers
	elif platform == "Zoom":
		frappe.log_error("working","working....")
		if type(doc) == str:
			doc = json.loads(doc)
		auth_response = authorize_zoom(doc)
		frappe.log_error("zoom auth",auth_response.get("access_token"))
		if auth_response.get("status") == "success" and auth_response.get("access_token"):
			headers = {"Authorization":f"Bearer {auth_response.get('access_token')}"}
			url = f"https://api.zoom.us/v2/meetings/{event_id}"
			frappe.log_error("dev",[url,headers])
	elif platform == "WhereBy":
		whereby_doc = frappe.get_doc("Meeting Integration",{"platform":platform})
		url = f"https://api.whereby.dev/v1/meetings/{event_id}"
		headers = {"Authorization":f"Bearer {whereby_doc.get('api_key')}"}
	elif platform == "Google Meet":
		validate = validate_gmeet_user(doc)
		frappe.log_error("validate cancel",validate)
		if validate.get("status") == "authorized":
			cred_doc = frappe.get_doc("Meeting Integration",{"platform":platform})
			calendar_id = cred_doc.calendar_id
			url = f"https://www.googleapis.com/calendar/v3/calendars/{calendar_id}/events/{event_id}"
			access_token = frappe.db.get_value("User Platform Credentials",
										{"user":"Administrator","platform":platform},['access_token'])
			frappe.log_error("access cance;",access_token)
			headers = {
				"Authorization": f"Bearer {access_token}"
			}
	frappe.log_error("WhereBy",headers)
	response = requests.delete(url = url, headers=headers)
	frappe.log_error("cancel response",response.status_code)
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
	frappe.log_error("user_directory_if",user_directory.status_code)

	if user_directory.status_code == 200:
		return {'directory':user_directory.json()['value']}
	else:
		# frappe.log_error("user_directory if js",user_directory.json())
		refresh_token = frappe.db.get_value("User Platform Credentials",
				{"user":frappe.session.user,"platform":"Teams"},['refresh_token'])
		frappe.log_error("teams ref tk",refresh_token)
		token_response = create_access_token_from_refresh_token("Teams",refresh_token)
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

def get_users(headers):
	user_directory = requests.get(
			url ="https://graph.microsoft.com/v1.0/users",
			headers=headers
		)
	return user_directory

@frappe.whitelist()
def edit_meeting(from_time,subject,meeting_id,event_id=None,doc=None,to_time = None,duration=None):
	if type(doc) == str:
		doc = json.loads(doc)
	if doc['platform'] == "Teams":
		headers = get_headers()
		validate = validate_user_credentials(headers = get_headers())
		if validate.get("directory"):
			if validate.get("is_updated"):
				headers = get_headers()
		return edit_teams_meeting(subject,headers,from_time,event_id,meeting_id,to_time)
	elif doc['platform'] == "Zoom":
		return edit_zoom_meeting(from_time,subject,meeting_id,duration = duration,doc = doc)
	# from_time = datetime.strftime(from_time,"%Y-%m-%d %H:%M:%S")
	# to_time = datetime.strftime(to_time,"%Y-%m-%d %H:%M:%S")
	frappe.log_error("from time type",type(from_time))
	
def edit_teams_meeting(subject,headers,from_time,event_id,meeting_id,to_time=None):
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

def edit_zoom_meeting(from_time,subject,meeting_id,duration,doc):
	frappe.log_error("from time",from_time)
	from_time ,to_time = convert_local_to_utc(from_time)
	utc_start_time = datetime.strftime(from_time,"%Y-%m-%dT%H:%M:%SZ")
	frappe.log_error('utc time',utc_start_time)
	authorize = authorize_zoom(doc)
	frappe.log_error("edit rsp",authorize)
	headers = {"Authorization":f"Bearer {authorize.get('access_token')}"}
	url = f"https://api.zoom.us/v2/meetings/{meeting_id}"
	frappe.log_error("type dur",type(duration))
	payload={
		"topic":subject,
		"start_time":utc_start_time,	
		"duration":int(duration) // 60,
	}
	frappe.log_error("payload",[payload,url])
	edit_response = requests.patch(url = url , headers=headers,json=payload)
	frappe.log_error("edit zoom response",edit_response.status_code)
	if edit_response.status_code == 204:
		return {
			"status":"success",
			"message":"zoom meeting edited successfully"
		}
@frappe.whitelist()
def get_attendance(doc):
	if type(doc) == str:
		doc = json.loads(doc)
	if doc['platform'] == "Teams":
		headers = get_headers()
		validate = validate_user_credentials(headers = get_headers())
		if validate.get("directory"):
			if validate.get("is_updated"):
				headers = get_headers()
		attendance = requests.get(
			url = f"https://graph.microsoft.com/v1.0/me/onlineMeetings/{doc['meeting_id']}/attendanceReports",
			headers = headers
		)
		if attendance_data:
			attendance_data = attendance.json()
			# frappe.log_error("attendance data",[meeting_id,attendance_data])
			return fetch_teams_attendance_reports(doc['meeting_id'],attendance_data['value'][0]['id'])
		else:
			return {"status":"pending","message":"Meeting not yet started"}
	elif doc['platform'] == "Zoom":
		fetch_zoom_attendance_report(doc)

def fetch_teams_attendance_reports(meeting_id,attendance_report_id):
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

def fetch_zoom_attendance_report(doc,page_size = 300):
	auth_response = authorize_zoom(doc)
	if auth_response.get("access_token"):
		url = f"https://api.zoom.us/v2/report/meetings/{doc['zoom_meeting_id']}/participants"
		frappe.log_error("att url",url)
		headers = {"Authorization":f"Bearer {auth_response['access_token']}"}
		payload = {"page_size":300}
		attendance = requests.get(url = url , headers = headers , params = payload)
		frappe.log_error("att sts code",attendance.status_code)
		if attendance.status_code == 200:
			frappe.log_error("att rec",attendance.text)
			return {"status":"success","data":attendance.json()}
		elif attendance.status_code == 400:
			return{
				"status":"success",
				"message":"Only available for Paid or ZMP account"
			}

@frappe.whitelist()
def create_zoom_meeting(token , doc):
	doc = json.loads(doc)
	from_time , to_time = convert_local_to_utc(doc['from'])
	utc_start_time = datetime.strftime(from_time,"%Y-%m-%dT%H:%M:%SZ")
	frappe.log_error("times",[from_time,to_time])
	headers = {
		"Authorization":f"Bearer {token}"
	}
	frappe.log_error("duration",doc['duration'])
	data = {
		"topic":doc['subject'],
		"agenda":doc['description'] if doc.get("description") else "",
		"start_time":utc_start_time,
		"password":doc['passcode'],
		"type":2,
		"timezone": frappe.db.get_value("User",frappe.session.user,"time_zone"),
		"duration" : doc['duration'] // 60,
		"settings":{
			"host_video": True if doc['enable_video_for_host'] else False,
			"participant_video": True if doc['enable_video_for_participant'] else False,
			"join_before_host": False if doc['waiting_room'] else True,
			"mute_upon_entry": True if doc['mute_participants_upon_entry'] else False,
			"waiting_room": True if doc['waiting_room'] else False,
			"approval_type": 1 if doc['registered_meeting'] and doc['approval_for_registration'] == "Manual"\
				  else 0,
			"audio": "voip",
			"auto_recording": "local" if doc['is_record_automatically'] else None,
			"use_pmi": False if doc['generate_meeting_id'] else True
		}
	}
	if doc['registered_meeting']:
		data['settings']['registration_type'] = 1
	frappe.log_error("Meeting payload",data)
	url = "https://api.zoom.us/v2/users/me/meetings"
	meeting_response = requests.post(url = url,headers = headers , json= data)
	frappe.log_error("meeting response code",meeting_response.status_code)
	if meeting_response.status_code == 201:
		frappe.log_error("meeting_response",meeting_response.json())
		return meeting_response.json()

@frappe.whitelist()
def create_whereby_room(doc):
	import re
	if type(doc) == str:
		doc = json.loads(doc)
		if doc['room_prefix']:
			room_prefix = doc['room_prefix'].lower()
			room_prefix_formatted = re.sub(r'[_\s]+', '-', room_prefix)  # Replace spaces/underscores with hyphen
			room_prefix_formatted = re.sub(r'[^\w-]', '', room_prefix_formatted)  
	# frappe.log_error('room_prefix_formatted',room_prefix_formatted)
	where_doc = frappe.get_doc("Meeting Integration",{"platform":doc['platform']})
	headers = {"Authorization": f"Bearer {where_doc.get('api_key')}",
				"Content-Type":"application/json"}	
	cur_time = datetime.strptime(frappe.utils.nowtime().split('.')[0],"%H:%M:%S")
	end_date = convert_local_to_utc(doc['end_date']+" "+datetime.strftime(cur_time,"%H:%M:%S"))[0]
	payload = {
		"endDate":datetime.strftime(end_date,"%Y-%m-%dT%H:%M:%SZ"),
		"isLocked":False if not doc['is_secured'] else True,
		"roomMode":"group" if doc['room_type'] == "Group" else "normal",
		"roomNamePrefix": room_prefix_formatted if doc.get("room_prefix") else "",
		"fields": ["hostRoomUrl", "viewerRoomUrl"],
	}
	if doc.get("streaming"):
		payload['streaming'] = {"enabled":True,"rtmpUrl": "rtmp://streaming.server.url"}
	frappe.log_error("whereby payload",payload)
	frappe.log_error("headers",headers)
	response = requests.post(url = "https://api.whereby.dev/v1/meetings",headers = headers,json=payload)
	frappe.log_error("where post",response.status_code)
	frappe.log_error("where json",response.json())
	if response.status_code != 201:
		# frappe.log_error
		frappe.throw(response.json())['error']
	if response.status_code == 201:
		return {
			"status":"success",
			"data":response.json()
		}
	

@frappe.whitelist()
def create_google_meet(doc):
	import uuid
	if type(doc) == str:
		doc = json.loads(doc)
	google_meet = frappe.get_doc("Meeting Integration",{"platform":doc['platform']})
	client_id = google_meet.client_id
	client_secret = google_meet.get_password("client_secret")
	calendar_id = google_meet.calendar_id
	meet_url = f'https://www.googleapis.com/calendar/v3/calendars/{calendar_id}/events?conferenceDataVersion=1'
	access_doc = frappe.get_doc("User Platform Credentials",{"user":"Administrator","platform":"Google Meet"})
	headers = {"Authorization": f"Bearer {access_doc.get('access_token')}","Content-Type":"application/json"}
	start_time ,end_time = convert_local_to_utc(doc['from'],doc['to'])
	participants =[]
	if doc['participants']:
		for participant in doc['participants']:
			participants.append({"email":participant['user']})
	if doc['external_participants']:
		for participant in doc['external_participants']:
			participants.append({"email":participant['email']})
	payload = {
		"summary":doc['subject'],
		"description":doc['description'] if doc.get("description") else "",
		"start": {
			"dateTime":datetime.strftime(start_time,"%Y-%m-%dT%H:%M:%SZ"),
			"timeZone":frappe.db.get_value("User",frappe.session.user,"time_zone")
		},
		"end": {
			"dateTime": datetime.strftime(end_time,"%Y-%m-%dT%H:%M:%SZ"),
			"timeZone": frappe.db.get_value("User",frappe.session.user,"time_zone")
    	},
		"attendees":participants,
		"conferenceData": {
			"createRequest": {
				"conferenceSolutionKey": {
					"type": "hangoutsMeet"
				},
				"requestId": str(uuid.uuid4())  # Unique identifier for the conference
			}
    	},
		"reminders": {
			"useDefault": False,
			"overrides": [
				{"method": "email", "minutes": 24 * 60},  # Send email reminder 1 day before
				{"method": "popup", "minutes": 10}       # Show popup reminder 10 minutes before
			]
		}
	}

	frappe.log_error("payload",payload)
	meet_resp = requests.post(url = meet_url,headers = headers,json = payload)
	frappe.log_error("meet_resp",meet_resp.json())
	if meet_resp.status_code == 200:
		return{
			"status":"success",
			"message":meet_resp.json(),
			"calendar_id":calendar_id
		}
	
# def send_notification_mail(data,receipients):
# 	frappe.sendmail()