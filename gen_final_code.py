import google.generativeai as genai
import config
import json
# def gen_code(full_code_log,task_classify):
#     genai.configure(api_key=config.API_KEY)
#     model = genai.GenerativeModel(model_name="gemini-2.5-flash-lite")
#     chat = model.start_chat()
#     prompt = f"""
#     The user provided a complete requirement to build a bot, which was then broken down into the following list of tasks: {task_classify}.

#     Based on each task in the list, the agent generated the corresponding Python code step by step. Below is the complete code generation log:
#     {full_code_log}

#     ###Important Requirement:
#     - When generating code, ensure that all control flow structures (e.g., If–Else conditions, For/While loops, and Try–Except blocks) are clearly defined and properly encapsulated.
#     - Each flow block must be marked with standardized command comments to indicate where the flow starts and ends. Use the following format:

#         ***If–Else Condition Block***
#             # Start Flow of Task 3 If Condition
#             ...
#             # End Flow of Task 3 If Condition

#         ***For Loop Block***
#             # Start Flow of Task 4 For Loop
#             ...
#             # End Flow of Task 4 For Loop

#         ***While Loop Block***
#             # Start Flow of Task 7 While Loop
#             ...
#             # End Flow of Task 7 While Loop

#         ***Try Block***
#             # Start Flow of Task 1 Try Block
#             ...
#             # End Flow of Task 1 Try Block

#         ***Except Block***
#             # Start Flow of Task 12 Except Block
#             ...
#             # End Flow of Task 12 Except Block



#     Combine all steps into a single Python script that performs the entire requirement. Return only the final Python code without any explanation or additional text.
#     """


#     response = chat.send_message(prompt)
#     return response.text

def gen_code(full_code_log,task_classify,xpath_values):
    genai.configure(api_key=config.API_KEY)
    model = genai.GenerativeModel(model_name="gemini-2.5-flash-lite")
    chat = model.start_chat()
    prompt = f"""
You are given a Python code file and a JSON file containing XPath values.

**Task:**
1. Remove these three import statements from the code:
   - from xpath_find import main
   - from element_confirmation import element_status
   - from verify_xpath import mod_xpath

2. Remove any code blocks that load JSON from file:
   - with open("json_info/json_xpath.json", "r") as f:
       json_xpath = json.load(f)

3. Replace all xpath variable assignments that use json_xpath.get() with direct string assignments using values from the provided JSON.
   - Find patterns like: variable_xpath = json_xpath.get("key_name", "Not_assigned")
   - Replace with: variable_xpath = "actual_xpath_value_from_json"
   - If the JSON value is empty, use: variable_xpath = ""  # TODO: Add key_name XPath

4. Remove any if blocks that check for "Not_assigned" and the code inside them (like element_xpath assignments).

5. Remove any code blocks that write back to the JSON file:
   - json_xpath["key"] = variable_xpath
   - with open("json_info/json_xpath.json", "w") as f:
       json.dump(json_xpath, f, indent=4)

6. Fix any indented import statements - move all import statements to the top of the file with no indentation.

7. Never load or read XPath values from a JSON file. Always assign XPath values directly in the code as string literals, using the exact corresponding value (whether it is a valid XPath or "Not_assigned") from the JSON XPath Values.

**USER Tasks:**
{task_classify}

**Original Code:**

{full_code_log}


**JSON XPath Values:**

{json.dumps(xpath_values, indent=2)}



Return only the converted Python code without any explanation, markdown formatting, or additional text.
"""

    response = chat.send_message(prompt)
    return response.text