import google.generativeai as genai
import config
def gemini_response(input):
    genai.configure(api_key=config.API_KEY)
    model = genai.GenerativeModel(model_name="gemini-2.5-flash-lite")
    chat = model.start_chat()
    prompt = f"""Convert the following user input {input} into a clear, grammatically correct sentence, simplified and limited to a maximum of three lines.
              Do not provide any additional explanation—just return the corrected sentence"""
    response = chat.send_message(prompt)
    return response.text

