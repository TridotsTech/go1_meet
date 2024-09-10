import frappe,msal,requests,json,base64,urllib.parse
# from go1_meeting.go1_meeting.doctype.meeting_integration.meeting_integration import create_meeting_link
@frappe.whitelist()
def validate_user(doc):
    doc = json.loads(doc)
    if not frappe.db.exists("User Platform Credentials",{"user":frappe.session.user,"platform":doc['platform']}):
        return "invalid Credentials"
    

@frappe.whitelist()
def fetch_users(access_token):
    headers = {"Authorization": "Bearer " + access_token}
    user_directory = requests.get(
			url ="https://graph.microsoft.com/v1.0/users",
			headers=headers
		)
    return user_directory.json()
#Create access token from username and password
@frappe.whitelist()
def create_access_token(doc,usr,pwd):
    doc = json.loads(doc)
    # frappe.log_error("doc",doc['platform'])
    # frappe.log_error("doc type",type(doc['platform']))
    if doc['platform'] == "Teams":
        if not frappe.db.exists("User Platform Credentials",{"user":frappe.session.user,"platform":"Teams"}):
            teams_credential = frappe.get_doc("Meeting Integration",{"platform":"Teams"})
            client_id = teams_credential.client_id
            client_secret = teams_credential.get_password("client_secret")
            tenant_id = teams_credential.tenant_id
            authority = f"https://login.microsoftonline.com/{tenant_id}"
            scopes = ['User.Read','User.Read.All', 'OnlineMeetings.ReadWrite']
            # frappe.log_error("args",(usr,pwd))
            msal_app = msal.ConfidentialClientApplication(
            client_id,
            authority=authority,
            client_credential=client_secret
            )

            token_response = msal_app.acquire_token_by_username_password(
                username=usr,
                password=pwd,
                scopes = scopes
            )
            # frappe.log_error("token_response",token_response)
            if 'access_token' in token_response:
                cred = frappe.get_doc({
                    "doctype": "User Platform Credentials",
                    "user":frappe.session.user,
                    "platform":doc.get("platform"),
                    "access_token":token_response['access_token'],
                    "refresh_token":token_response['refresh_token']
                })
                cred.insert()
                # cred.user = frappe.session.user
                # cred.platform = doc['platform'],
                # cred.access_token = token_response['access_token']
                # cred.refresh_token = token_response['refresh_token']
                # cred.save()
                # frappe.db.commit()

def create_access_token_from_refresh_token(refresh_token):
    teams_credential = frappe.get_doc("Meeting Integration",{"platform":"Teams"})
    client_id = teams_credential.client_id
    client_secret = teams_credential.get_password("client_secret")
    tenant_id = teams_credential.tenant_id
    authority = f"https://login.microsoftonline.com/{tenant_id}"
    scopes = ['User.Read','User.Read.All', 'OnlineMeetings.ReadWrite']
    msal_app = msal.ConfidentialClientApplication(
    client_id,
    authority=authority,
    client_credential=client_secret
    )

    token_response = msal_app.acquire_token_by_refresh_token(refresh_token, scopes=scopes)
    return token_response

@frappe.whitelist()
def _redirect_uri(doc):
    if doc['platform'] == "Teams":
        client_id , client_secret , tenant_id , scopes = get_teams_credentials()
        authority = f"https://login.microsoftonline.com/{tenant_id}"
        msal_app = msal.ClientApplication(client_id, authority=authority, client_credential=client_secret)
        redirect_uri = frappe.utils.get_url('/api/method/go1_meeting.go1_meeting.integration.validation.teams_oauth_callback')
        frappe.log_error("redirect_uri",redirect_uri)
        # Generate authorization URL
        auth_url = msal_app.get_authorization_request_url(scopes, redirect_uri=redirect_uri)
        frappe.log_error("auth_url",auth_url)
    elif doc['platform'] == "Zoom":
        client_id = frappe.db.get_value("Meeting Integration",{'platform':doc['platform']},['client_id'])
        redirect_uri = frappe.utils.get_url('/api/method/go1_meeting.go1_meeting.integration.validation.zoom_oauth_callback')
        encoded_state = urllib.parse.urlencode({"name":doc['name']})
        auth_url = f"https://zoom.us/oauth/authorize?response_type=code&client_id={client_id}&redirect_uri={redirect_uri}&state={encoded_state}"
        frappe.log_error("auth_url",auth_url)
    return auth_url

@frappe.whitelist(allow_guest = True)
def teams_oauth_calback(code = None):
    if not code:
        frappe.throw("Authorization code not found")
    client_id , client_secret , tenant_id , scopes = get_teams_credentials()
    redirect_uri = frappe.utils.get_url('/api/method/go1_meeting.go1_meeting.integration.validation.teams_oauth_calback')
    authority = f"https://login.microsoftonline.com/{tenant_id}"
    frappe.log_error("code",code)
    msal_app = msal.ConfidentialClientApplication(
        client_id,
        authority=authority,
        client_credential=client_secret
    )
    token_response = msal_app.acquire_token_by_authorization_code(
        code=code,
        scopes=scopes,
        redirect_uri=redirect_uri
    )
    latest_doc = frappe.get_last_doc("Meeting Integration",{"platform":"Teams","owner":frappe.session.user})
    frappe.log_error("last doc",latest_doc )
    frappe.log_error("last d name",latest_doc.name)
    set_token_response(token_response)
    # redirect_uri = frappe.utils.get_url('/api/method/go1_meeting.go1_meeting.integration.validation.teams_oauth_calback')
    frappe.log_error("token resp from microsoft",token_response)
    frappe.local.response["type"] = "redirect"
    frappe.local.response["location"] = f"/app/meeting-integration"

@frappe.whitelist(allow_guest = True) 
def zoom_oauth_callback():
    code = frappe.form_dict.get("code")
    state = frappe.form_dict.get("state")
    if state:
        query_state = urllib.parse.parse_qs(state)
        doc_name = query_state.get("name")[0]
    zoom_credentials = frappe.get_doc("Meeting Integration",{"platform":"Zoom"})
    client_id = zoom_credentials.client_id
    client_secret = zoom_credentials.get_password("client_secret")
    token_url = "https://zoom.us/oauth/token"
    redirect_uri = frappe.utils.get_url('/api/method/go1_meeting.go1_meeting.integration.validation.zoom_oauth_callback')
    headers = {
        "Authorization":"Basic "+base64.b64encode(f"{client_id}:{client_secret}".encode()).decode(),
        "Content-Type": "application/x-www-form-urlencoded"
    }
    data = {
        "grant_type":"authorization_code",
        "code":code,
        "redirect_uri":redirect_uri
    }
    response = requests.post(token_url, headers=headers, data=data)
    if response.status_code == 200:
        token_data = response.json()
        frappe.log_error("zoom access token",token_data)
        access_token = token_data.get("access_token")
        refresh_token = token_data.get("refresh_token")
        frappe.local.response["type"] = "redirect"
        frappe.local.response["location"] = f"/app/app/go1-meet/{doc_name}"
@frappe.whitelist()
def authorize_user_access_token(doc):
    doc = json.loads(doc)
    #Checks for zoom
    if doc['platform'] == "Zoom":
        admin_auth = frappe.db.get_value("Meeting Integration",{'platform':doc['platform']},['admin_auth'])
    user = "Administrator" if doc['platform'] == "Zoom" and admin_auth else frappe.session.user
    if not frappe.db.exists("User Platform Credentials",{"user":user,"platform":doc['platform']}):
        auth_url = _redirect_uri(doc)
        return {"status":"not_authorized","message":auth_url}
    else:
        return {"status":"authorized"}
        

def get_teams_credentials():
    cred_doc = frappe.get_doc("Meeting Integration",{"platform":"Teams"})
    client_id = cred_doc.client_id
    client_secret = cred_doc.get_password("client_secret")
    tenant_id = cred_doc.tenant_id
    scopes = ['User.Read', 'OnlineMeetings.ReadWrite']
    return client_id,client_secret,tenant_id,scopes

def set_token_response(token_response):
    frappe.log_error("token_response set tokens",token_response)
    cred = frappe.get_doc({
            "doctype": "User Platform Credentials",
            "user":frappe.session.user,
            "platform":"Teams",
            "access_token":token_response['access_token'],
            "refresh_token":token_response['refresh_token']
        })
    cred.insert()
    frappe.db.commit()