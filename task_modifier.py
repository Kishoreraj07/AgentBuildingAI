import google.generativeai as genai
import config
import ast
def gemini_response(tasks,old_code,new_code):
    genai.configure(api_key=config.API_KEY)
    model = genai.GenerativeModel(model_name="gemini-2.5-flash-lite")
    chat = model.start_chat()
    prompt = f"""Here is the List of Tasks : {tasks}
    Here is the code created based on above listed tasks : {old_code}
    
    Now User modified the code as this one : {new_code}
    
    Based on the above modified code need to update the tasks as per the modified code and returns the updated list of tasks as same as python string of list format
    
    No need additional explaination or text just provide the list of tasks"""
    response = chat.send_message(prompt)
    res_txt=response.text
    if '`' in res_txt:
        res=res_txt.strip("`")
        res_txt=res
    if '``' in res_txt:
        res=res_txt.strip("``")
        res_txt=res
    if '```' in res_txt:
        res=res_txt.strip("```")
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
    res=res_txt
    if type(res)==str:
        res = res.replace("```", "").strip()
        if res.startswith("[") and res.endswith("]"):
            res=ast.literal_eval(res)
        else:
            try:
                res=ast.literal_eval(res)
            except:
                pass
    return res