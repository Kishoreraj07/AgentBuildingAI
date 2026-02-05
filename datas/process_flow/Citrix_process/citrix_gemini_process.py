from google import genai
import google.generativeai as genai1
import config
import json
def gemini_response(desc,all_data):
    try:
        annoted_image=r"Citrix_process\annotated.png"
        client = genai.Client(api_key=config.API_KEY)
        if annoted_image.endswith(('.png','.jpg')):
            img_file = client.files.upload(file=annoted_image)
            import time
            while img_file.state.name == "PROCESSING":
                print("Processing PDF file...")
                time.sleep(2)
                img_file = client.files.get(img_file.name)
            
            if img_file.state.name == "FAILED":
                raise ValueError("PDF file processing failed")
        prompt = f"""
    The JSON data likely contains OCR/visual-detection metadata — element types, coordinates, centroid positions, etc.
    The image represents the visual overlay of those detected elements (red = text blocks, blue = icons).

    Here is the JSON data: {all_data}

    An image file is also attached for reference — please analyze it as well.

    Here is the Current Needed Element Description: {desc}

    First, analyze the attached image to identify all elements visually.
    Then, compare the detected elements in the image with the provided JSON data to find the correct element that matches the given Description.
    For example, if the Description is "Username field", locate the Username field by cross-referencing both the image and the JSON data, and return its bounding coordinates.

    The corresponding visual reference image with highlighted elements is attached here: annotated.png

    Using the provided Description, analyze and compare both the JSON data and the attached image to accurately identify the correct element.

    Return only the bounding coordinates of that element in the following JSON format:
    {{"Bounding-Index": [top_left_x, top_left_y, bottom_right_x, bottom_right_y]}}

    Example:
    {{"Bounding-Index": [912, 23, 45, 67]}}

    Do not include any additional explanation, reasoning, or text — only return the JSON data exactly in the specified format.
    """


        response = client.models.generate_content(
            model='gemini-2.5-flash-lite',
            contents=[prompt, img_file]
        )
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
    except:
        return [947,470,1294,768]

# desc="Username Field"
# json_path=r"Citrix_process\pixel_click_log.json"
# with open(json_path, "r", encoding="utf-8") as f:
#     json_data = json.load(f)
# img_path=r"Citrix_process\annotated.png"
# res=gemini_response(desc,json_data,img_path)
# print(res)