import google.generativeai as genai
import config,json
def gemini_response(element_data):
    genai.configure(api_key=config.API_KEY)
    model = genai.GenerativeModel(model_name="gemini-2.5-flash-lite")
    chat = model.start_chat()
    prompt = f"""The JSON data likely contains OCR/visual-detection metadata — element types, coordinates, centroid positions, etc.
    
    Here is the Json Data : {element_data}

    Return only the bounding coordinates of that element in the following JSON format:
    {{"Bounding-Index": [top_left_x, top_left_y, bottom_right_x, bottom_right_y]}}

    Example:
    {{"Bounding-Index": [912, 23, 45, 67]}}

    Do not include any additional explanation, reasoning, or text — only return the JSON data exactly in the specified format.
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
    return res["Bounding-Index"]