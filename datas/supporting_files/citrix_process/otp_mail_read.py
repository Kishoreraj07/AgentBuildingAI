from google import genai
import json
from datas.source_files import config

def gemini_extract_otp_from_mail(body_content: str):


    if not body_content:
        return None

    client = genai.Client(api_key=config.API_KEY)

    prompt = f"""
You are an OTP extraction engine.

TASK:
Extract ONLY the OTP value from the email content below.

RULES:
- OTP is a numeric verification code (usually 4 to 8 digits).
- Return ONLY the OTP digits.
- No explanation.
- No formatting.
- No markdown.
- If no OTP exists, return null.

EMAIL CONTENT:
{body_content}

OUTPUT FORMAT:
Return only the number like:
095424

If not found:
null
"""

    response = client.models.generate_content(
        model="gemini-2.5-flash-lite",
        contents=[prompt]
    )

    res_txt = response.text.strip()

    # Clean possible formatting noise
    if '`' in res_txt:
        res_txt = res_txt.replace('`', '').strip()
    if res_txt.lower() == "null":
        return None

    return res_txt


# mail_body = """
# Ref ID: 994233
# Transaction OTP -> 556677
# Amount: ₹5,000
# Merchant: Flipkart
# """

# otp = gemini_extract_otp_from_mail(mail_body)
# print(otp)