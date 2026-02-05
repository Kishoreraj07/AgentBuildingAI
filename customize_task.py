import google.generativeai as genai
import config
import ast
import os
import pandas as pd
def gemini_response(input, tasks, filepaths, task_chat_history=None):
    genai.configure(api_key=config.API_KEY)
    model = genai.GenerativeModel(model_name="gemini-2.5-flash-lite")
    
    # Initialize history if not provided (for chat continuity)
    if task_chat_history is None:
        task_chat_history = []
    
    chat = model.start_chat(history=task_chat_history)
    prompt = f"""
You are given a list of automation tasks derived from the user's earlier requirements: {tasks}.

The user may provide new instructions related to Web, Desktop, Citrix, or Hybrid automation (e.g., Web & Citrix or Desktop & Citrix).

Here is the user's latest input: {input}.

Your task:
1. If the user's input adds a **new step or task**, append it appropriately while maintaining the logical flow and sequence from the existing list.
2. If the user requests a **correction, modification, or deletion**, update the corresponding steps accordingly and return the revised list.
3. If the user specifies steps to be converted to **Citrix automation** (e.g., "change step 2, 5, and 6 as Citrix flow"), then:
   - Identify those step numbers.
   - Append the phrase **"by Citrix Automation"** to each of those steps.
     Example:  
       Original steps: ["Type Username as admin", "Click Launch button", "Extract the user name"]  
       Updated steps: ["Type Username as admin by Citrix Automation", "Click Launch button by Citrix Automation", "Extract the user name by Citrix Automation"]
4. If the user does **not** request any additions, deletions, or updates, simply return the existing list of tasks unchanged.
5. Maintain consistent capitalization, order, and phrasing for clarity.
6. Do **not** include any explanations, formatting, or extra text — return **only** the updated Python list of tasks.

================================================================================
MAIL OPERATION MODIFICATION RULES
================================================================================
When the user requests to add, modify, or update mail-related steps:

### FOR ADDING/MODIFYING SEND MAIL STEPS:
1. **Consolidate all email parameters into a single step**.
2. **Required format**:
   "Send mail from [FROM_EMAIL] to [TO_EMAIL] with subject [SUBJECT] and body [BODY] using CLIENT_ID [CLIENT_ID], CLIENT_SECRET [CLIENT_SECRET], TENANT_ID [TENANT_ID]"

3. **Subject and Body Intelligence Rules**:
   a) **If NEITHER subject NOR body provided in user's input**:
      - Use default subject: "Automated Email Notification"
      - Use default body: "This is an automated email sent via workflow automation."
   
   b) **If body PROVIDED but subject NOT provided**:
      - Generate a relevant subject based on the body content
      - Keep subject concise (5-10 words max)
      - Extract the main topic/action from the body
      - Example: If body is "Please review the attached quarterly report", subject should be "Quarterly Report Review Request"
   
   c) **If subject PROVIDED but body NOT provided**:
      - Generate a relevant body based on the subject
      - Keep body professional and contextual (1-2 sentences)
      - Expand on the subject with appropriate details
      - Example: If subject is "Meeting Reminder", body should be "This is a reminder about our upcoming meeting. Please confirm your attendance."
   
   d) **If BOTH subject AND body provided**:
      - Use exactly as provided by the user

4. **Credentials handling**: If CLIENT_ID, CLIENT_SECRET, or TENANT_ID not provided, use [NOT_PROVIDED].

### FOR ADDING/MODIFYING READ MAIL STEPS:
1. **Consolidate all email parameters into a single step**.
2. **Required format**:
   "Read mail from mailbox [MAILBOX_EMAIL] using CLIENT_ID [CLIENT_ID], CLIENT_SECRET [CLIENT_SECRET], TENANT_ID [TENANT_ID] with filter [FILTER_CRITERIA]"
3. If filter criteria is not mentioned, use "all emails".
4. **Credentials handling**: If CLIENT_ID, CLIENT_SECRET, or TENANT_ID not provided, use [NOT_PROVIDED].

### MODIFICATION EXAMPLES:
- User says: "Add a step to send email to client@example.com with body Thanks for your purchase"
  Result: Append → "Send mail from [NOT_PROVIDED] to client@example.com with subject Purchase Confirmation and body Thanks for your purchase using CLIENT_ID [NOT_PROVIDED], CLIENT_SECRET [NOT_PROVIDED], TENANT_ID [NOT_PROVIDED]"

- User says: "Change step 3 to send mail from admin@company.com to user@test.com with subject Welcome"
  Result: Update step 3 → "Send mail from admin@company.com to user@test.com with subject Welcome and body Welcome to our platform. We're glad to have you with us. using CLIENT_ID [NOT_PROVIDED], CLIENT_SECRET [NOT_PROVIDED], TENANT_ID [NOT_PROVIDED]"

- User says: "Modify step 5 - add CLIENT_ID as abc123 and subject as Invoice"
  Result: Update step 5 keeping existing params and adding new ones, generate body based on subject "Invoice"

### CITRIX WITH MAIL:
- If user requests mail steps to be converted to Citrix automation, append "by Citrix Automation" at the end:
  Example: "Send mail from admin@company.com to user@test.com with subject Welcome and body Welcome message using CLIENT_ID abc123, CLIENT_SECRET xyz789, TENANT_ID tenant456 by Citrix Automation"

### IMPORTANT:
- When modifying existing mail steps, preserve all previously provided parameters and only update/add the new ones mentioned by the user.
- Always maintain the complete format even if user only mentions partial information.
- Never split mail operations into multiple steps.
"""
    content=[prompt]
    for path in filepaths:
        try:
            # Validate file exists
            if not os.path.exists(path):
                print(f"[ERROR] File not found: {path}")
                content.append(f"\n\n--- File: {path} ---\nERROR: File not found\n")
                continue
            
            # Check file size (Gemini has limits)
            file_size = os.path.getsize(path)
            print(f"[INFO] Processing file: {path} ({file_size} bytes)")
            
            # Handle Excel/CSV as text
            if path.lower().endswith((".xlsx", ".xls", ".csv")):
                try:
                    if path.lower().endswith(".csv"):
                        df = pd.read_csv(path)
                    else:
                        df = pd.read_excel(path)
                    file_text = df.to_string(index=False)
                    content.append(f"\n\n--- File: {path} ---\n{file_text}\n")
                    print(f"[OK] Converted tabular file to text: {path}")
                except Exception as e:
                    print(f"[ERROR] Failed to read tabular file {path}: {e}")
                    content.append(f"\n\n--- File: {path} ---\nERROR: Could not read file - {str(e)}\n")
            
            # Handle text files as inline text
            elif path.lower().endswith((".txt", ".py", ".json", ".xml", ".log")):
                try:
                    with open(path, 'r', encoding='utf-8') as f:
                        file_text = f.read()
                    content.append(f"\n\n--- File: {path} ---\n{file_text}\n")
                    print(f"[OK] Read text file: {path}")
                except Exception as e:
                    print(f"[ERROR] Failed to read text file {path}: {e}")
                    content.append(f"\n\n--- File: {path} ---\nERROR: Could not read file - {str(e)}\n")
            
            # Handle binary files via upload API
            else:
                try:
                    uploaded_file = genai.upload_file(path)
                    # Wait for file to be processed
                    import time
                    time.sleep(1)  # Give API time to process
                    content.append(uploaded_file)
                    print(f"[OK] Uploaded file via API: {path}")
                except Exception as e:
                    print(f"[ERROR] Failed to upload file {path}: {e}")
                    content.append(f"\n\n--- File: {path} ---\nERROR: Upload failed - {str(e)}\n")
        
        except Exception as e:
            print(f"[ERROR] Unexpected error processing {path}: {e}")
            content.append(f"\n\n--- File: {path} ---\nERROR: {str(e)}\n")
    
    
    response = chat.send_message(content)
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
    
    # Get updated chat history from Gemini for continuity
    updated_history = chat.history
    
    # Return tuple: (tasks, updated_history)
    return (res, updated_history)

