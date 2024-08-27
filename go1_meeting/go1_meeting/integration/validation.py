import frappe,msal,requests,json
@frappe.whitelist()
def validate_user(doc):
    doc = json.loads(doc)
    if not frappe.db.exists("User Platform Credentials",{"user":frappe.session.user,"platform":doc['platform']}):
        return "invalid Credentials"
    

@frappe.whitelist()
def fetch_users():
    headers = {"Authorization": "Bearer " + frappe.session.data.get("access_token")}
    user_directory = requests.get(
			url ="https://graph.microsoft.com/v1.0/users",
			headers=headers
		)
@frappe.whitelist()
def create_access_token(doc,usr,pwd):
    doc = json.loads(doc)
    # frappe.log_error("doc",doc['platform'])
    # frappe.log_error("doc type",type(doc['platform']))
    if doc['platform'] == "Teams":
        if not frappe.db.exists("User Platform Credentials",{"user":frappe.session.user,"platform":"Teams"}):
            teams_credential = frappe.get_doc("Meeting Integration",{"platform":"Teams"})
            client_id = teams_credential.client_id
            client_secret = teams_credential.client_secret
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
    client_secret = teams_credential.client_secret
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