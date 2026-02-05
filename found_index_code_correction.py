import google.generativeai as genai
import config
def gemini_response(index,code):
    genai.configure(api_key=config.API_KEY)
    model = genai.GenerativeModel(model_name="gemini-2.5-flash-lite")
    chat = model.start_chat()
    prompt = f"""On this Code :
    {code}
    Need to modify like use this Found Index : {index} and return the modified code
    
    Note: Do not need additional explaination just return the modified code
    Just return the modified code"""
    response = chat.send_message(prompt)
    return response.text

