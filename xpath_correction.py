import google.generativeai as genai
import json
from datas.source_files import config
def gemini_response(code):
    # Try to load existing JSON, create empty dict if file doesn't exist
    try:
        with open("json_info/json_xpath.json", "r", encoding="utf-8") as f:
            json_xpath = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        json_xpath = {}
    genai.configure(api_key=config.API_KEY)
    model = genai.GenerativeModel(model_name="gemini-2.5-flash-lite")
    chat = model.start_chat()
    prompt = f"""Here is the code of a process: {code}

Analyze the given code and identify all variables or keys being used from the 'json_xpath' dictionary.
(Not all keys necessarily end with '_xpath', so consider all key usages dynamically.)

Compare the identified keys with the keys of the given JSON: {json_xpath}.

Apply the following update rules to produce the final JSON:
1. Keep all existing keys and values exactly as they are — do not overwrite or modify their values.
2. If any new keys are found in the code but missing in the given JSON, add them with the value "Not_assigned".
3. If any keys exist in the given JSON but are not referenced in the uncommented lines of the code, remove those keys.
   (Completely ignore commented-out code when checking for usage.)
4. Preserve JSON key order as much as possible.
5. First check whether a variable name used in the code already exists in the JSON. If it exists, do not modify the key name or its XPath value. 
6. Only add keys for newly introduced variable names in the code, and assign them the value "Not_assigned".
7. If a new step must be inserted between existing steps, insert it at the correct numeric position and shift all following steps forward.
8. Do not overwrite or duplicate existing steps when shifting; move them forward while preserving their keys and values.
9. If the code explicitly deletes, removes, disables, or drops a variable or step, remove the corresponding XPath key from the JSON.
10. If a variable is missing from the code or explicitly removed there, its XPath key must also be removed from the JSON.
11. Do not change the value of any existing XPath key that is not being removed.
12. Do not modify any other keys or values beyond what is required by these rules.
13. Apply add/remove/delete actions only to the explicitly specified step.
14. Do not modify, reorder, rename, or update any other steps or XPath keys.
15. Only the user-specified step may be changed; all others must remain exactly as they are.

Return only the final updated JSON. No explanations or extra text.
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

# code="""
# #===User Modified Generated Code ===

# from selenium import webdriver
# from selenium.webdriver.chrome.service import Service
# from selenium.webdriver.chrome.options import Options
# from selenium.webdriver.common.by import By
# from selenium.webdriver.support.ui import WebDriverWait
# from selenium.webdriver.support import expected_conditions as EC
# from xpath_find import main
# from element_confirmation import element_status
# from verify_xpath import mod_xpath
# import json
# import traceback
# import time

# def aba_agent():
#     try:
#         # Configure Chrome options
#         chrome_options = Options()
#         chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
#         chrome_options.add_experimental_option('useAutomationExtension', False)
#         chrome_options.add_argument("--start-maximized")  # open in full width

#         # Create driver
#         driver = webdriver.Chrome(options=chrome_options)

#         # Load XPath mappings
#         try:
#             with open("json_info/json_xpath.json", "r") as f:
#                 json_xpath = json.load(f)
#         except FileNotFoundError:
#             json_xpath = {
#                 "username_xpath": "Not_assigned",
#                 "password_xpath": "Not_assigned",
#                 "login_button_xpath": "Not_assigned"
#             }
#             import os
#             os.makedirs("json_info", exist_ok=True)
#             with open("json_info/json_xpath.json", "w") as f:
#                 json.dump(json_xpath, f, indent=4)
#         except json.JSONDecodeError:
#             json_xpath = {
#                 "username_xpath": "Not_assigned",
#                 "password_xpath": "Not_assigned",
#                 "login_button_xpath": "Not_assigned"
#             }
#             import os
#             os.makedirs("json_info", exist_ok=True)
#             with open("json_info/json_xpath.json", "w") as f:
#                 json.dump(json_xpath, f, indent=4)


#         # Launch URL
#         url = "https://cloud-droidal.com"
#         driver.get(url)
#         time.sleep(2) # Allow page to load

#         # Type username
#         username_key = "username_xpath"
#         if json_xpath[username_key] == "Not_assigned":
#             element_xpath = main("type on the username field", driver)
#             element_result = element_status("type on the username field", element_xpath, driver)
#             if not element_result:
#                 element_xpath = mod_xpath(driver)
#             json_xpath[username_key] = element_xpath
#             with open("json_info/json_xpath.json", "w") as f:
#                 json.dump(json_xpath, f, indent=4)
#         else:
#             element_xpath = json_xpath[username_key]

#         WebDriverWait(driver, 60).until(
#             EC.presence_of_element_located((By.XPATH, element_xpath))
#         ).send_keys("admin")
        
#         json_xpath[username_key] = element_xpath
#         with open("json_info/json_xpath.json", "w") as f:
#             json.dump(json_xpath, f, indent=4)

#         # Type password
#         password_key = "password_xpath"
#         if json_xpath[password_key] == "Not_assigned":
#             element_xpath = main("type on the password field", driver)
#             element_result = element_status("type on the password field", element_xpath, driver)
#             if not element_result:
#                 element_xpath = mod_xpath(driver)
#             json_xpath[password_key] = element_xpath
#             with open("json_info/json_xpath.json", "w") as f:
#                 json.dump(json_xpath, f, indent=4)
#         else:
#             element_xpath = json_xpath[password_key]

#         WebDriverWait(driver, 60).until(
#             EC.presence_of_element_located((By.XPATH, element_xpath))
#         ).send_keys("1234")

#         json_xpath[password_key] = element_xpath
#         with open("json_info/json_xpath.json", "w") as f:
#             json.dump(json_xpath, f, indent=4)

#         # Removed the click login button step as per the user query.
            
#         time.sleep(5) # Allow for page navigation after login

#     except Exception:
#         import os
#         os.makedirs("json_info", exist_ok=True)
#         with open("json_info/exception_info.json", "w") as f:
#             json.dump({"code_exception": traceback.format_exc()}, f, indent=4)
#     finally:
#         if 'driver' in locals() and driver:
#             driver.quit()
# """
# res=gemini_response(code)
# print(res)