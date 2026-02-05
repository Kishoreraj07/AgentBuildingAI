import google.generativeai as genai
import json
from datas.source_files import config
def gemini_response(flow,keyname,value,conditional_info,task_end_index):
    genai.configure(api_key=config.API_KEY)
    model = genai.GenerativeModel(model_name="gemini-2.5-flash-lite")
    chat = model.start_chat()
    prompt = f"""Using the flow : {flow} and value : {keyname}-{value} and end index : {task_end_index}
    And need to search on this Conditional Info Json : {conditional_info}
    And return the start index of the task from the Conditional Info Json

    like json format of {{"start_task_index":"value"}}
    Just return as Valid Json Format
    Do not return with additional text or explaination
    
    """
    response = chat.send_message(prompt)
    res_txt=response.text
    if '`' in res_txt:
        res=res_txt.strip("`")
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
        if res.startswith("{") and res.endswith("}"):
            res=json.loads(res)
        else:
            try:
                res=json.loads(res)
            except:
                pass
    return res
def get_start_index(flow, keyname, value, conditional_info, task_end_index):
    # Ensure the flow exists
    if flow not in conditional_info:
        return {}

    for item in conditional_info[flow]:
        # Match the condition and task_end_index
        if keyname in item and str(item[keyname]) == str(value) and item["task_end_index"] == task_end_index:
            return {"start_task_index": str(item["task_start_index"])}

    # If not found, return empty
    return {}