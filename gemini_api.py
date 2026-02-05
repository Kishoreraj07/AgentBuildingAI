import google.generativeai as genai
import config
def gemini_response(input):
    genai.configure(api_key=config.API_KEY)
    model = genai.GenerativeModel(model_name="gemini-2.5-flash-lite")
    chat = model.start_chat()
    prompt = input
    response = chat.send_message(prompt)
    return response.text

def gemini_vision_response(prompt_text, image):
    """
    Handles multi-modal requests (text + image) to the Gemini Pro Vision model.

    Args:
        prompt_text (str): The text prompt to send along with the image.
        image (PIL.Image.Image): The image object (from pyautogui.screenshot()).

    Returns:
        str: The text response from the model.
    """
    print("--- Sending prompt and image to Gemini Vision API ---")
    try:
        # 1. Initialize the specific model for vision
        vision_model = genai.GenerativeModel('gemini-2.5-flash-lite')

        # 2. The API expects the image and prompt as a list of parts
        # The image object from pyautogui is a PIL Image, which is directly compatible.
        model_input = [prompt_text, image]
        
        # 3. Generate the content
        response = vision_model.generate_content(model_input)
        
        # 4. Return the text part of the response
        if response.parts:
            print("--- Received response from Gemini Vision ---")
            return response.text
        else:
            print(f"Warning: Gemini Vision response was empty. Prompt: {prompt_text}")
            return f"Error: No response from model for prompt: {prompt_text}"

    except Exception as e:
        print(f"An error occurred in gemini_vision_response: {e}")
        return f"Error: An exception occurred while calling the Gemini Vision API: {e}"

def restructure_prompt(user_input: str) -> str:
    """
    Advanced context-aware grammar correction for automation systems.
    Corrects human language while preserving all technical content.
    """

    if not user_input.strip():
        return ""

    prompt = f"""
You are an expert text corrector for automation systems.

Instructions for the AI:
1. Correct only natural language for spelling, grammar, capitalization, and punctuation.
2. Preserve all technical or machine-readable content exactly as it appears, including:
   - File paths (e.g., C:\\Users\\Hariprasad.k\\Desktop\\abc.txt)
   - URLs or API endpoints (https:// or http://)
   - Code snippets or programming syntax (e.g., def func():, if x == y, =, +, etc.)
   - JSON, XML, or structured data
   - File extensions (.txt, .py, .json, .pdf, etc.)
   - Command-style instructions (like "run the script execute_code.py") without adding punctuation
3. Do NOT rephrase, interpret, or modify technical content in any way.
4. Only return the corrected version. Do not add explanations, comments, or markdown formatting.

Input:
{user_input}
"""

    try:
        corrected_text = gemini_response(prompt)
        if not corrected_text:
            corrected_text = user_input
    except Exception as e:
        print(f"[⚠️ Correction skipped: {e}]")
        corrected_text = user_input

    return corrected_text.strip()

# res=gemini_response("hi")
# print(res)