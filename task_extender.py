import google.generativeai as genai
import config
import ast
def task_extender(list_of_task,user_req):
    genai.configure(api_key=config.API_KEY)
    model = genai.GenerativeModel(model_name="gemini-2.5-flash-lite")
    chat = model.start_chat()
    prompt = f"""
You are given a list of automation tasks derived from the user's earlier requirements: {list_of_task}.

The user may provide new instructions related to Web, Desktop, Citrix, or Hybrid automation (e.g., Web & Citrix or Desktop & Citrix).

Here is the user's latest input: {user_req}.

Your task:
1. If the user’s input adds a **new step or task**, append it appropriately while maintaining the logical flow and sequence from the existing list.
2. If the user requests a **correction, modification, or deletion**, update the corresponding steps accordingly and return the revised list.
3. If the user specifies steps to be converted to **Citrix automation** (e.g., “change step 2, 5, and 6 as Citrix flow”), then:
   - Identify those step numbers.
   - Append the phrase **“by Citrix Automation”** to each of those steps.
     Example:  
       Original steps: ["Type Username as admin", "Click Launch button", "Extract the user name"]  
       Updated steps: ["Type Username as admin by Citrix Automation", "Click Launch button by Citrix Automation", "Extract the user name by Citrix Automation"]
4. If the user does **not** request any additions, deletions, or updates, simply return the existing list of tasks unchanged.
5. Maintain consistent capitalization, order, and phrasing for clarity.
6. Do **not** include any explanations, formatting, or extra text — return **only** the updated Python list of tasks.
"""

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
    full_info=res
    descriptions = []
    events = []
    for item in res:
        if "Event :" in item:
            parts = item.split("Event :")
            descriptions.append(parts[0].strip())
            events.append("Event :" + parts[1].strip())
        else:
            descriptions.append(item.strip())
            events.append("")
    res=[descriptions,events]

    return res[0],res[1],full_info
    # return res