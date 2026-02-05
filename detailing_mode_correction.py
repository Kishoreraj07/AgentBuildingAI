import google.generativeai as genai
import config
def gemini_response(instruction,task_name):
    genai.configure(api_key=config.API_KEY)
    model = genai.GenerativeModel(model_name="gemini-2.5-flash-lite")
    chat = model.start_chat()
    xpath_senerio="""User : Click on the xpath : //div[@class='class_name'] 
    Agent : Click on the xpath : //div[@class='class_name'] 
    
    User : Type on the xpath : //div[@class='class_name']
    Agent : Type on the xpath : //div[@class='class_name']
    just return the Agent response like below :
    Click on the xpath : //div[@class='class_name']"""
    prompt = f"""You are an RPA assistant that rewrites user-supplied task instructions.

INPUTS
• task_name – the invalid task previously generated.  
• instruction – the user’s correction or clarification.  
• xpath_scenario – the fixed example below (do **not** modify it).

STRICT RULES
1. **Use only the information the user supplies.**  
   • If the user does **not** specify the value to type, the element to click, the exact URL, file path, or field name.
2. If the xpath is not provided but the field name is specified , we can simply use it.
3. When all required details are present, return **one** clear, grammatically correct sentence (max 2 lines).  
4. If the user request is already of the form
   • “Click on the xpath : …”  
   • “Type on the xpath : …”  
   return it **unchanged**.  
5. Give **no** explanations or extra text—return **only** the sentence or the follow-up question.
6. **Do not ask questions, Just generate the task**

EXAMPLE
User → “Click on the xpath : //div[@class='class_name']”  
Assistant → “Click on the xpath : //div[@class='class_name']”


This is the invalid task generated: {task_name}.  
Convert the following user input into a clear, grammatically correct sentence (max 2 lines), following the STRICT RULES.  
User input: {instruction}

Example scenario:  
{xpath_senerio}
"""
    response = chat.send_message(prompt)
    return response.text