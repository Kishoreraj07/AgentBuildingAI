import google.generativeai as genai
from selenium.webdriver.support.ui import WebDriverWait
from datas.source_files import config
import json
def main(description,driver):
    genai.configure(api_key=config.API_KEY)
    model = genai.GenerativeModel(model_name="gemini-2.5-flash-lite")
    chat = model.start_chat()
    try:
        WebDriverWait(driver, 50).until(
            lambda d: d.execute_script("return document.readyState") == "complete"
        )
        html_content = driver.execute_script("return document.documentElement.outerHTML;")
    except Exception as e:
        html_content=""


    prompt = f"""Here is the Element description : {description}
Need to find the xpath of that element from the current page of HTML Content

Here is the HTML Content : {html_content}

Return the result as this JSON format : {{"x_path":"deducted xpath"}}
Do not predict xpath as default pick refer actual HTML content and provide proper xpath
Do not need additional explaination or text"""
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
            try:
                res=json.loads(res)
            except json.JSONDecodeError:
                # Handle cases where the string is not valid JSON despite starting/ending with braces
                return None
        else:
            try:
                res=json.loads(res)
            except json.JSONDecodeError:
                # Handle cases where the string is not valid JSON
                return None

    # Check if 'x_path' key exists in the dictionary before accessing it
    if isinstance(res, dict) and "x_path" in res:
        return res["x_path"]
    else:
        # Return None or raise an error if 'x_path' is not found
        return None