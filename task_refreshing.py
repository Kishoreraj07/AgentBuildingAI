import google.generativeai as genai
import config
import ast
def gemini_response(code,tasks):
    genai.configure(api_key=config.API_KEY)
    model = genai.GenerativeModel(model_name="gemini-2.5-flash-lite")
    chat = model.start_chat()
    prompt = f"""Here is the list of tasks : {tasks}
    Here is the code generated for the list of tasks : {code}
    
    Here if the code is have much more tasks than the list of tasks, then the list of tasks need to get updateed by adding the missing tasks into it
    And sent the finalized full updated task as list of python string
    
    Do not sent any additional explaination or text"""
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