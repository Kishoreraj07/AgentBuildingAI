import google.generativeai as genai1
from google import genai
import os,time,json
from datas.source_files import config
def get_xpath(driver,description,html_content):
    client = genai.Client(api_key=config.API_KEY)
    os.makedirs("images", exist_ok=True)
    screenshot_path = "images/xpath.png"
    driver.save_screenshot(screenshot_path)
    img_file = client.files.upload(file=screenshot_path)
    while img_file.state.name == "PROCESSING":
        print("Processing Image file...")
        time.sleep(2)
        img_file = client.files.get(img_file.name)
    
    if img_file.state.name == "FAILED":
        raise ValueError("Image file processing failed")
    prompt = f"""
Here is the element description: {description}
Here is the HTML content: {html_content}
Also attached is the current active page screenshot.

Using all three sources (HTML content, element description, and screenshot), identify the most accurate Full XPath of the target element.

Return the result strictly in JSON format as:
{{"xpath": <extracted_xpath>}}

Ensure the XPath is valid and functional for use in Python Selenium operations such as clicking, typing, or extracting element data.

Return only the JSON object — no explanation or additional text.
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
    return json.loads(res_txt)
