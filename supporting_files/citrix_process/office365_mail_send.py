import requests
import base64
import os

def send_mail_ms_graph(
    from_mail: str,
    to_mail: str,
    tenant: str,
    client_id: str,
    client_secret: str,
    subject: str,
    body: str,
    attachments: list = None  
):

    token_url = f"https://login.microsoftonline.com/{tenant}/oauth2/v2.0/token"
    graph_url = f"https://graph.microsoft.com/v1.0/users/{from_mail}/sendMail"

    token_payload = {
        "client_id": client_id,
        "client_secret": client_secret,
        "scope": "https://graph.microsoft.com/.default",
        "grant_type": "client_credentials"
    }

    token_response = requests.post(token_url, data=token_payload)

    if token_response.status_code != 200:
        print("Token Error")
        print(token_response.status_code)
        print(token_response.text)
        return

    access_token = token_response.json()["access_token"]

    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }

    mail_payload = {
        "message": {
            "subject": subject,
            "body": {
                "contentType": "HTML",
                "content": body
            },
            "toRecipients": [
                {"emailAddress": {"address": to_mail}}
            ]
        },
        "saveToSentItems": True
    }

    # 📎 Handle attachments if provided
    if attachments:
        attachment_list = []

        for file_path in attachments:
            if not os.path.exists(file_path):
                print(f"Attachment not found: {file_path}")
                continue

            with open(file_path, "rb") as f:
                encoded_content = base64.b64encode(f.read()).decode("utf-8")

            attachment_list.append({
                "@odata.type": "#microsoft.graph.fileAttachment",
                "name": os.path.basename(file_path),
                "contentBytes": encoded_content
            })

        if attachment_list:
            mail_payload["message"]["attachments"] = attachment_list

    response = requests.post(graph_url, headers=headers, json=mail_payload)

    if response.status_code == 202:
        print("Mail sent successfully")
    else:
        print("Mail send failed")
        print(response.status_code)
        print(response.text)


# send_mail_ms_graph(
#     from_mail="deepakkumar.b@droidal.com",
#     to_mail="deepakkumar.b@droidal.com",
#     tenant = "35800adc-eb69-4c43-b94c-66398463ce04",
#     client_id="5aa2a216-4c93-4f35-a308-07fb498a463d",
#     client_secret="gSk8Q~NONmI_efZCUUN2Pjof_HCIb5gMWr8fccc6",
#     subject="Test mail",
#     body="This is a test mail"
# )