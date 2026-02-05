import google.generativeai as genai
import config,json
def gemini_response(code):
    # Try to load existing JSON, create empty dict if file doesn't exist
    try:
        with open("json_info/json_attr.json", "r", encoding="utf-8") as f:
            json_attr = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        json_attr = {}
    genai.configure(api_key=config.API_KEY)
    model = genai.GenerativeModel(model_name="gemini-2.5-flash-lite")
    chat = model.start_chat()
    prompt = f"""Here is the code of a process : {code}
    
    On that code there are so many variables assigned with Attributes as values like username_attributes,password_ttributes like need to list out all as a JSON format like
    Need to compare all with the keys of this JSON : {json_attr}

    If anything missing there means add only the missing keys with values "Not_assigned"
    
    Return only the JSON no need additional explaination or text
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
    if '```' in res_txt:
        res=res_txt.strip("```")
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