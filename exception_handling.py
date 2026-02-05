import google.generativeai as genai
import config
def friendly_error_msg(exception):
    genai.configure(api_key=config.API_KEY)
    model = genai.GenerativeModel(model_name="gemini-2.5-flash-lite")
    chat = model.start_chat()
    prompt = f"""This is the python error message : {exception}

Just return this as User Understandable error message

Just return the error friendly message only Do not return any explaination or additional text"""
    response = chat.send_message(prompt)
    return response.text
def helper_function(exception):
    display_msg=friendly_error_msg (exception)
    