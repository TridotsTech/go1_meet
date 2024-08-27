# Copyright (c) 2024, Tridots Tech and contributors
# For license information, please see license.txt

import frappe,requests,msal,json,pytz
from datetime import datetime
from frappe.model.document import Document
from go1_meeting.go1_meeting.integration.validation import create_access_token_from_refresh_token

class MeetingIntegration(Document):
	pass

@frappe.whitelist()
def create_meeting_link(attendees,from_time,to_time,subject):
	# data = {'@odata.context': "https://graph.microsoft.com/v1.0/$metadata#users('9a63aebd-8549-4659-9cd7-f72d40ae569d')/onlineMeetings/$entity", 'id': 'MSo5YTYzYWViZC04NTQ5LTQ2NTktOWNkNy1mNzJkNDBhZTU2OWQqMCoqMTk6bWVldGluZ19NV0l5TldRd01XTXRZelF6TlMwME56STBMV0UzTlRNdFltUTJOVFE1TVdabE9UQXpAdGhyZWFkLnYy', 'creationDateTime': '2024-08-26T07:09:19.9294211Z', 'startDateTime': '2024-08-26T07:09:05Z', 'endDateTime': '2024-08-26T07:30:00Z', 'joinUrl': f'https://teams.microsoft.com/l/meetup-join/19%3ameeting_MWIyNWQwMWMtYzQzNS00NzI0LWE3NTMtYmQ2NTQ5MWZlOTAz%40thread.v2/0?context=%7b%22Tid%22%3a%229dddf813-4fcd-4ab3-b0a8-8566773cb0df%22%2c%22Oid%22%3a%229a63aebd-8549-4659-9cd7-f72d40ae569d%22%7d', 'meetingCode': '416803604020', 'isBroadcast': False, 'autoAdmittedUsers': 'everyoneInCompany', 'outerMeetingAutoAdmittedUsers': None, 'capabilities': [], 'externalId': None, 'iCalUid': None, 'meetingType': None, 'meetingsMigrationMode': None, 'joinWebUrl': f'https://teams.microsoft.com/l/meetup-join/19%3ameeting_MWIyNWQwMWMtYzQzNS00NzI0LWE3NTMtYmQ2NTQ5MWZlOTAz%40thread.v2/0?context=%7b%22Tid%22%3a%229dddf813-4fcd-4ab3-b0a8-8566773cb0df%22%2c%22Oid%22%3a%229a63aebd-8549-4659-9cd7-f72d40ae569d%22%7d', 'subject': 'Test Internal Meeting', 'videoTeleconferenceId': None, 'isEntryExitAnnounced': True, 'allowedPresenters': 'everyone', 'allowAttendeeToEnableMic': True, 'allowAttendeeToEnableCamera': True, 'allowMeetingChat': 'enabled', 'shareMeetingChatHistoryDefault': 'none', 'allowTeamworkReactions': True, 'anonymizeIdentityForRoles': [], 'recordAutomatically': False, 'allowParticipantsToChangeName': False, 'allowTranscription': True, 'allowRecording': True, 'allowWhiteboard': True, 'allowBreakoutRooms': True, 'allowLiveShare': 'enabled', 'allowPowerpointSharing': True, 'meetingTemplateId': None, 'broadcastSettings': None, 'meetingInfo': None, 'audioConferencing': None, 'watermarkProtection': None, 'chatRestrictions': None, 'participants': {'organizer': {'upn': 'jaffarsherif@tridotstech.com', 'role': 'presenter', 'identity': {'application': None, 'device': None, 'user': {'id': '9a63aebd-8549-4659-9cd7-f72d40ae569d', 'displayName': None, 'tenantId': '9dddf813-4fcd-4ab3-b0a8-8566773cb0df', 'identityProvider': 'AAD'}}}, 'attendees': [{'upn': None, 'role': 'attendee', 'identity': {'application': None, 'device': None, 'user': {'id': '0f1422ce-9a60-45a0-94fb-e18bbf0c812d', 'displayName': None, 'tenantId': None, 'identityProvider': 'MSA'}}}]}, 'chatInfo': {'threadId': '19:meeting_MWIyNWQwMWMtYzQzNS00NzI0LWE3NTMtYmQ2NTQ5MWZlOTAz@thread.v2', 'messageId': '0', 'replyChainMessageId': None}, 'joinInformation': {'content': f'data:text/html,%3cdiv+style%3d%22max-width%3a+520px%3b+color%3a+%23242424%3b+font-family%3a%27Segoe+UI%27%2c%27Helvetica+Neue%27%2cHelvetica%2cArial%2csans-serif%22+class%3d%22me-email-text%22%3e%0d%0a++%3cdiv+style%3d%22margin-bottom%3a24px%3boverflow%3ahidden%3bwhite-space%3anowrap%3b%22%3e________________________________________________________________________________%3c%2fdiv%3e%0d%0a%0d%0a++%3cdiv+style%3d%22margin-bottom%3a+12px%3b%22%3e%0d%0a++++%3cspan+class%3d%22me-email-text%22+style%3d%22font-size%3a+24px%3bfont-weight%3a+700%3b+margin-right%3a12px%3b%22%3eMicrosoft+Teams%3c%2fspan%3e%0d%0a++++%3ca+id%3d%22meet_invite_block.action.help%22+class%3d%22me-email-link%22+style%3d%22font-size%3a14px%3b+text-decoration%3aunderline%3b+color%3a+%235B5FC7%3b%22+href%3d%22https%3a%2f%2faka.ms%2fJoinTeamsMeeting%3fomkt%3den-US%22%3eNeed+help%3f%3c%2fa%3e%0d%0a++%3c%2fdiv%3e%0d%0a%0d%0a++%3cdiv+style%3d%22margin-bottom%3a+6px%3b%22%3e%0d%0a++++%3ca+id%3d%22meet_invite_block.action.join_link%22+title%3d%22Meeting+join+link%22+class%3d%22me-email-headline%22+style%3d%22font-size%3a+20px%3b+font-weight%3a600%3b+text-decoration%3a+underline%3b+color%3a+%235B5FC7%3b%22+href%3d%22https%3a%2f%2fteams.microsoft.com%2fl%2fmeetup-join%2f19%253ameeting_MWIyNWQwMWMtYzQzNS00NzI0LWE3NTMtYmQ2NTQ5MWZlOTAz%2540thread.v2%2f0%3fcontext%3d%257b%2522Tid%2522%253a%25229dddf813-4fcd-4ab3-b0a8-8566773cb0df%2522%252c%2522Oid%2522%253a%25229a63aebd-8549-4659-9cd7-f72d40ae569d%2522%257d%22+target%3d%22_blank%22+rel%3d%22noreferrer+noopener%22%3eJoin+the+meeting+now%3c%2fa%3e%0d%0a++%3c%2fdiv%3e%0d%0a%0d%0a++%3cdiv+style%3d%22margin-bottom%3a+6px%3b%22%3e%0d%0a++++%3cspan+class%3d%22me-email-text-secondary%22+style%3d%22font-size%3a+14px%3b+color%3a+%23616161%3b%22%3eMeeting+ID%3a+%3c%2fspan%3e%0d%0a++++%3cspan+class%3d%22me-email-text%22+style%3d%22font-size%3a+14px%3b+color%3a+%23242424%3b%22%3e416+803+604+020%3c%2fspan%3e%0d%0a++%3c%2fdiv%3e%0d%0a%0d%0a%0d%0a%0d%0a++%3cdiv+style%3d%22margin-bottom%3a+24px%3b+max-width%3a+532px%3b%22%3e%0d%0a++++%3chr+style%3d%22border%3a+0%3b+background%3a+%23D1D1D1%3b+height%3a+1px%3b%22%3e%3c%2fhr%3e%0d%0a++%3c%2fdiv%3e%0d%0a%0d%0a%0d%0a%0d%0a%0d%0a%0d%0a++%3cdiv%3e%0d%0a++++%3cspan+class%3d%22me-email-text-secondary%22+style%3d%22font-size%3a+14px%3b+color%3a+%23616161%3b%22%3eFor+organizers%3a+%3c%2fspan%3e%0d%0a++++%3ca+id%3d%22meet_invite_block.action.organizer_meet_options%22+class%3d%22me-email-link%22+style%3d%22font-size%3a+14px%3b+text-decoration%3a+underline%3b+color%3a+%235B5FC7%3b%22+target%3d%22_blank%22+href%3d%22https%3a%2f%2fteams.microsoft.com%2fmeetingOptions%2f%3forganizerId%3d9a63aebd-8549-4659-9cd7-f72d40ae569d%26tenantId%3d9dddf813-4fcd-4ab3-b0a8-8566773cb0df%26threadId%3d19_meeting_MWIyNWQwMWMtYzQzNS00NzI0LWE3NTMtYmQ2NTQ5MWZlOTAz%40thread.v2%26messageId%3d0%26language%3den-US%22+rel%3d%22noreferrer+noopener%22%3eMeeting+options%3c%2fa%3e%0d%0a++%3c%2fdiv%3e%0d%0a%0d%0a++%3cdiv+style%3d%22margin-top%3a+24px%3b+margin-bottom%3a+6px%3b%22%3e%0d%0a++++%0d%0a++++%0d%0a++%3c%2fdiv%3e%0d%0a%0d%0a++%3cdiv+style%3d%22margin-bottom%3a+24px%3b%22%3e%0d%0a++++%0d%0a++%3c%2fdiv%3e%0d%0a%0d%0a++%3cdiv+style%3d%22margin-bottom%3a24px%3boverflow%3ahidden%3bwhite-space%3anowrap%3b%22%3e________________________________________________________________________________%3c%2fdiv%3e%0d%0a%0d%0a%3c%2fdiv%3e', 'contentType': 'html'}, 'joinMeetingIdSettings': {'isPasscodeRequired': False, 'joinMeetingId': '416803604020', 'passcode': None}, 'lobbyBypassSettings': {'scope': 'organization', 'isDialInBypassEnabled': False}}
	headers = get_headers()
	# frappe.log_error("headers in link fn",headers)
	validate = validate_user_credentials(headers = headers)
	# frappe.log_error("validate meet link fn",validate)
	if validate.get("directory"):
		if validate.get("is_updated"):
			headers = get_headers()
		user_directory = validate.get("directory")
		# frappe.log_error("user type directory",type(user_directory))
		# frappe.log_error("user directory", user_directory)
		meeting_users = []
		attendees = json.loads(attendees)
	# for i in attendees:
	# 	meeting_users.
	# user_directory = validate_user_credentials(headers)['value']
		# frappe.log_error("user type directory",type(user_directory))
		# frappe.log_error("user directory", user_directory)

		for i in attendees:
			for j in user_directory:
				if j['mail'] == i['user']:
					meeting_users.append({"identity": {"user": {"id": j['id']}}})
		# frappe.log_error("meeting user",meeting_users)

		from_time , to_time = convert_local_to_utc(from_time,to_time)
		from_time = datetime.strftime(from_time,"%Y-%m-%dT%H:%M:%SZ")
		to_time = datetime.strftime(to_time,"%Y-%m-%dT%H:%M:%SZ")
		# frappe.log_error("meet link utc",[from_time,to_time])
		meeting_data = {
			"subject": subject,
			"startDateTime": from_time,
			"endDateTime": to_time,
			"participants": {
				"attendees": meeting_users
				}
			}
		# frappe.log_error("meeting_data",meeting_data)
		response = requests.post(
			url="https://graph.microsoft.com/v1.0/me/onlineMeetings",
			headers=headers,
			json=meeting_data
		)
		# frappe.log_error("meet response",response)
		# frappe.log_error("meet response code",response.status_code)
		if response.status_code == 201:
			meeting_response = response.json()
			# frappe.log_error("meeting_response json",meeting_response)
			join_url = meeting_response['joinUrl']
			# frappe.log_error("join_url",join_url)
			create_calender_event(meeting_response , headers , attendees,user_directory,subject = subject )

def create_calender_event(data,headers,attendees,user_directory,subject = None):
	people = []
	for i in attendees:
		for j in user_directory:
			if j['mail'] == i['user']:
				people.append({
					"emailAddress": {
						"address": j['mail'],
						"name": j['displayName']
					},
					"type": "required"
					})	
	join_url = data['joinUrl']
	calendar_api_url = 'https://graph.microsoft.com/v1.0/me/events'
	event = {
			"subject": subject,
			"body": {
				"contentType": "HTML",
				"content": f"Please join the meeting using the following link: <a href='{join_url}'>Join the Meeting</a>"
			},
			"start": {
				"dateTime": data['startDateTime'],
				"timeZone": "UTC"
			},
			"end": {
				"dateTime": data["endDateTime"],
				"timeZone": "UTC"
			},
			"location": {
				"displayName": "Test Meeting - Internal"
			},
			"attendees": people,
			"allowNewTimeProposals": True,
			"isOnlineMeeting": True,
			"onlineMeeting": {
				"joinUrl": f"{join_url}"
			}
		}
	cal_response = requests.post(calendar_api_url, headers=headers, json = event)
	# frappe.log_error("cal_response json",cal_response.json())
	# frappe.log_error("cal_response",cal_response.status_code)


def convert_local_to_utc(from_time_str,to_time_str):
	dt_format = "%Y-%m-%d %H:%M:%S"
	from_time_obj  = datetime.strptime(from_time_str, dt_format)
	to_time_obj = datetime.strptime(to_time_str, dt_format)
	user_time_zone = frappe.db.get_value("User",frappe.session.user,"time_zone")
	local_from_time = pytz.timezone(user_time_zone).localize(from_time_obj)
	local_to_time = pytz.timezone(user_time_zone).localize(to_time_obj)
	utc_from_time = local_from_time.astimezone(pytz.timezone("UTC"))
	utc_to_time = local_to_time.astimezone(pytz.timezone("UTC"))
	# frappe.log_error("utc_from_time",utc_from_time)
	# frappe.log_error("utc_to_time",utc_to_time)
	return utc_from_time,utc_to_time

def get_headers():
	access_token = frappe.db.get_value("User Platform Credentials",{"user":frappe.session.user,"platform":"Teams"},['access_token'])
	headers = {"Authorization": "Bearer " + access_token}
	return headers
def validate_user_credentials(headers, is_updated = None):
	user_directory = get_users(headers)
	# frappe.log_error("user_directory_if",user_directory.status_code)

	if user_directory.status_code != 200:
		# frappe.log_error("user_directory if js",user_directory.json())
		refresh_token = frappe.db.get_value("User Platform Credentials",
				{"user":frappe.session.user,"platform":"Teams"},['refresh_token'])
		token_response = create_access_token_from_refresh_token(refresh_token)
		# frappe.log_error("token_response",token_response)
		# frappe.log_error("token_response",type(token_response))

		# frappe.log_error("token_response sts code",token_response.status_code)
		if "access_token" in token_response:
			exist = frappe.db.exists("User Platform Credentials",{"user":frappe.session.user,"platform":"Teams"})
			if exist:
				frappe.db.set_value("User Platform Credentials",exist,{
					"access_token":token_response['access_token'],
					"refresh_token":token_response['refresh_token']
				})
				frappe.db.commit()
			# frappe.log_error("acc token set",exist)
			access_token = token_response['access_token']
			headers = {"Authorization": "Bearer " + access_token}
			is_updated = 1
			updated_directory = get_users(headers)
		if is_updated:
			# frappe.log_error("is updated",is_updated)
			return {'directory':updated_directory.json()['value'],"is_updated":1}
	return {'directory':user_directory.json()['value']}

def get_users(headers):
	user_directory = requests.get(
			url ="https://graph.microsoft.com/v1.0/users",
			headers=headers
		)
	return user_directory