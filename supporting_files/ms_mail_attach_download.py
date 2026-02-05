import os
import requests
import msal
import base64


def download_outlook_attachments(
    from_mail: str,
    tenant: str,
    client_id: str,
    client_secret: str,
    download_path: str
):
    mail_id=from_mail
    tenant_id=tenant
    os.makedirs(download_path, exist_ok=True)

    authority = f"https://login.microsoftonline.com/{tenant}"
    scope = ["https://graph.microsoft.com/.default"]
    graph_api = "https://graph.microsoft.com/v1.0"

    app = msal.ConfidentialClientApplication(
        client_id=client_id,
        authority=authority,
        client_credential=client_secret
    )

    token_result = app.acquire_token_for_client(scopes=scope)
    if "access_token" not in token_result:
        raise Exception(f"Token acquisition failed: {token_result}")

    headers = {
        "Authorization": f"Bearer {token_result['access_token']}"
    }

    messages_url = (
        f"{graph_api}/users/{from_mail}/messages"
        f"?$orderby=receivedDateTime desc"
        f"&$top=10"
        f"&$select=id,hasAttachments"
    )

    messages_resp = requests.get(messages_url, headers=headers)
    messages_resp.raise_for_status()

    messages = messages_resp.json().get("value", [])

    if not messages:
        print("No emails found.")
        return

    for msg in messages:
        if not msg.get("hasAttachments"):
            continue 

        msg_id = msg["id"]

        attachments_url = f"{graph_api}/users/{from_mail}/messages/{msg_id}/attachments"
        attach_resp = requests.get(attachments_url, headers=headers)
        attach_resp.raise_for_status()

        attachments = attach_resp.json().get("value", [])

        if not attachments:
            continue

        for att in attachments:
            if att.get("isInline"):
                continue

            if att["@odata.type"] == "#microsoft.graph.fileAttachment":
                file_name = att["name"]
                file_bytes = base64.b64decode(att["contentBytes"])

                file_path = os.path.join(download_path, file_name)
                with open(file_path, "wb") as f:
                    f.write(file_bytes)

                print(f"Downloaded: {file_path}")

        break
    else:
        print("No attachment mail found.")
