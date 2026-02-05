import google.generativeai as genai
import config
def gemini_response(input,exp,code_log,user_request):

    genai.configure(api_key=config.API_KEY)
    model = genai.GenerativeModel(model_name="gemini-2.5-flash-lite")
    chat = model.start_chat()
    prompt =f"""
        This is the agent-generated code:  
        {input}

        An exception was encountered during execution:  
        {exp}

        ### Current Task:
        Please correct the code only for the following user request:  
        {user_request}

        ### Generated Code Log:
        - The following is a log of all previously generated code from earlier tasks.
        - This is provided only for reference to help structure your response and maintain continuity (e.g., consistent variable naming and logic flow).
        - Do not reuse or return any of the previous code in your response.
        {code_log}

        ### Instructions:
        - Ensure the corrected code includes all necessary import statements and is syntactically valid.
        - Apply any fixes needed to resolve the reported exception.
        - Maintain consistency with the previous code where applicable (e.g., variable names, flow).
        - Return only the updated and corrected code for this current request : {user_request}.

        **Note:** Return only the Python code. Do not include any explanations, comments, or additional content.
        """




    response = chat.send_message(prompt)
    return response.text
