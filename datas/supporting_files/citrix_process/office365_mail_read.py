import requests
import re
from html import unescape

def clean_html(text: str) -> str:
    # Remove HTML comments <!-- ... -->
    text = re.sub(r"<!--.*?-->", "", text, flags=re.DOTALL)
    # Remove HTML tags <...>
    text = re.sub(r"<.*?>", "", text)
    # Decode HTML entities (&nbsp; etc.)
    text = unescape(text)
    # Normalize whitespace
    text = re.sub(r"\s+", " ", text).strip()
    return text


def read_latest_mail_ms_graph(
    from_mail: str,
    tenant: str,
    client_id: str,
    client_secret: str
):
    token_url = f"https://login.microsoftonline.com/{tenant}/oauth2/v2.0/token"
    graph_url = (
        f"https://graph.microsoft.com/v1.0/users/{from_mail}/mailFolders/Inbox/messages"
        f"?$orderby=receivedDateTime desc&$top=1"
    )

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
        return None

    access_token = token_response.json()["access_token"]

    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }

    response = requests.get(graph_url, headers=headers)

    if response.status_code != 200:
        print("Mail read failed")
        print(response.status_code)
        print(response.text)
        return None

    data = response.json()
    messages = data.get("value", [])

    if not messages:
        return None

    msg = messages[0]

    raw_body = msg.get("body", {}).get("content", "")
    clean_body = clean_html(raw_body)

    # print(clean_body)
    return clean_body


# read_latest_mail_ms_graph(
#     from_mail="deepakkumar.b@droidal.com",
#     tenant="35800adc-eb69-4c43-b94c-66398463ce04",
#     client_id="5aa2a216-4c93-4f35-a308-07fb498a463d",
#     client_secret="gSk8Q~NONmI_efZCUUN2Pjof_HCIb5gMWr8fccc6"
# )
