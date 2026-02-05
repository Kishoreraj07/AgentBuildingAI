import google.generativeai as genai
import config
import json
def gemini_response(current_input, previous_inputs):
    genai.configure(api_key=config.API_KEY)
    model = genai.GenerativeModel(model_name="gemini-2.5-flash-lite")
    chat = model.start_chat()
    prompt = f"""You are validating RPA tasks.  
Use the following rules to decide if a Current Task is valid.  
If Previous Tasks are empty, treat them as none.  

Current Task: {current_input}  
Previous Tasks: {previous_inputs}  

A task is considered valid only if: 

1. **Open/Start/Launch type tasks** (anything that indicates opening a website, portal, or system) must include a valid URL (https/httpss or a domain like .com, .net, .org, etc.).  
    - If the task is not about opening something, ignore this rule.   

2. **Credential type tasks** (tasks involving "username", "password", "login", "credentials") must include the exact value (e.g., "type username as admin", "type password as 1234") OR specify the field location (e.g., "type username in username field").  
    - If the value and the field location is specified, the task is valid for credentials.
    - If the task only mentions "type <value>" without specifying where to type it, it's invalid.

3. **General type tasks** (any other typing tasks not covered by rule 2) must specify both the value AND the exact location/field where it should be typed (e.g., "type welcome in chat box").  
    - This rule only applies to non-credential typing tasks. If either the value and the field location is specified, the task is valid.
    - If the task only mentions "type <value>" without specifying where to type it, it's invalid.

4. **Extract tasks** must specify exactly what to extract and provide sufficient context to locate it. Valid examples include:
    - Field extractions: "extract the email field", "extract order number"
    - Table extractions: "extract the table under Sales Data heading", "extract the pricing table"
    - Section extractions: "extract the summary section", "extract data from the reports area"
    - List extractions: "extract the list of customers", "extract all product names"
    - The task must provide enough detail to uniquely identify what and where to extract.
    
5. **Save file tasks** (e.g., "save as excel file") must specify the complete file path (e.g., "save as excel file to C:/Reports/data.xlsx").  

6. If all required details are present, the task is valid.  

Important:  
    - Always check rule 1 (URL check) first when the task intent is about opening something.  
    - Prioritize credential tasks (rule 2) over general type tasks (rule 3).
    - If the Current Task is missing required details, mark it invalid. 

Format the response strictly as JSON: 

Provide the response in the following format:
{{
    "response": "Your user-friendly and understandable response here (e.g., if invalid, explain the issue clearly like 'The task is missing a valid URL for launching the portal. Please provide one.'; if valid, confirm like 'Task is valid and ready to proceed.')",
    "valid": true/false
}}
Do not include any other information or explanation in the response.
"""

    response = chat.send_message(prompt)
    res_txt=response.text
    if '```' in res_txt:
        res=res_txt.strip("````")
        res_txt=res
    if '\n' in res_txt:
        res=res_txt.strip("\n")
        res_txt=res
    if 'json' in res_txt:
        res=res_txt.strip("json")
        res_txt=res
    if 'python' in res_txt:
        res=res_txt.strip("python")
        res_txt=res
    if '`' in res:
        res_txt=res.strip('`')
    res=res_txt
    if type(res)==str:
        if res.startswith("{") and res.endswith("}"):
            res=json.loads(res)
        else:
            try:
                res=json.loads(res)
            except:
                pass
    return res            
# current_input = "wait for 5 seconds"
# previous_inputs = []
# print(gemini_response(current_input, previous_inputs))

