import google.generativeai as genai
import config
import pandas as pd

def response_msg(input):
    genai.configure(api_key=config.API_KEY)
    model = genai.GenerativeModel(model_name="gemini-2.5-flash-lite")
    chat = model.start_chat()
    prompt = f"""You are a Chatbot Agent.  
    Here is the User Query: {input}  

    Generate a direct and positive response to the user’s query and Respond like the task has been successfully completed
    Do not include additional explanations or extra text—just provide the response in clear, natural human language."""

    response = chat.send_message(prompt)
    return response.text
def convert_xlsx_to_text(xlsx_path):
    """Convert Excel to a plain text table for Gemini"""
    df = pd.read_excel(xlsx_path)
    return df.to_string(index=False)

def chat_request(code,input,filepaths):
    genai.configure(api_key=config.API_KEY)
    model = genai.GenerativeModel(model_name="gemini-2.5-flash-lite")
    chat = model.start_chat()
    modified_prompt=f"""Here is the User Query: {input}
    User request is related to modify the existing code with their query
    Here is the existing code: {code}

    If the query is related to any of the files, the attached files and their full paths are: {filepaths}

    Based on the provided input, update or modify the code as needed and return it as Python code.

    - If the User Query doesn't require any code changes, return the existing code as-is.
    - If the User Query asks to add the process of MFA OTP from a mobile authenticator, 
      update the code to include the MFA/OTP handling logic means always use this code snippet to generate OTP from the token:

            import time
            from pyotp import TOTP
            def mfa_token(tokens):
                time.sleep(1)
                totp = TOTP(tokens)
                token = totp.now()
                return token

         Use mfa_token(<secret_token>) wherever OTP input is required.

    - Do not change the existing function name (e.g., aba_agent()) in the code.
    - Do not call the function; only define it.
    - No additional explanation or text, just provide the code."""


    content=[modified_prompt]
    for path in filepaths:
        if path.endswith((".xlsx", ".csv")):
            file_text = convert_xlsx_to_text(path)
            content.append(f"\n\n--- File: {path} ---\n{file_text}\n")
        else:
            content.append(genai.upload_file(path))
    prompt = content
    response = chat.send_message(prompt)
    final_code=response.text
    if final_code.startswith("```"):
        final_code = "\n".join(final_code.strip().split("\n")[1:-1])
    res_msg=response_msg(input)
    return final_code,res_msg

# filepaths=[r"C:\Users\Kishore.k\Documents\automation_code.py",
# r"C:\Users\Kishore.k\Downloads\pdf_highlighter.py",
# r"C:\Users\Kishore.k\Downloads\claims_sample.xlsx"]
# code=""
# input="Analyze the attached files and summarize the context"
# response=chat_request(code,input,filepaths)
# print(response)
