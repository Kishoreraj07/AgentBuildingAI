import google.generativeai as genai
import ast
import config,json

def condition_statement_info(tasks,input):
    genai.configure(api_key=config.API_KEY)
    model = genai.GenerativeModel(model_name="gemini-2.5-flash-lite")
    chat = model.start_chat()
    sample_response = {
        "if": [
            {"task_no": "2 to 3", "condition": "group number greater than 10", "order": 1,"task_start_index":2,"task_end_index":3},
            {"task_no": "14 to 18", "condition": "age greater than 18", "order": 1,"task_start_index":14,"task_end_index":18}
        ],
        "else": [
            {"task_no": "7 to 8", "native_if_elif_task_no": ["3 to 8", "8 to 10"], "order": 3,"task_start_index":7,"task_end_index":8}
        ],
        "elif": [
            {"task_no": "14","condition":"price equals to 30" ,"native_if_elif_task_no": ["2 to 3", "4 to 6"], "order": 2,"task_start_index":14,"task_end_index":14}
        ],
        "while": [
            {"task_no": "18 to 25", "condition": "Group name is Aetna", "order": 1,"task_start_index":18,"task_end_index":25}
        ],
        "for": [
            {"task_no": "28 to 31", "iteration_range": "list data of roll number", "order": 2,"task_start_index":28,"task_end_index":31},
            {"task_no": "34 to 37", "iteration_range": "range of 0 to 7", "order": 1,"task_start_index":34,"task_end_index":37}
        ]
    }

    prompt = f"""
    User Input: {input}
    Generated Tasks: {tasks}

    The user input may contain:
    - Conditional statements: if, else, elif
    - Looping statements: for, while
    - Exception handling: try, except, finally

    Your job is to map these user instructions to the Generated Tasks and return structured JSON.

    STRICT RULES:

    1. Respect Start/End Markers
    - Use the "start" and "end" words from the user input or tasks to determine exact block boundaries.
    - If user says "start ... end the nested if/for/while", then include every task in between.
    - If no explicit "end" is given, then:
        - The block must still include at least one flow operation (e.g., print, set variable).
        - If the immediate next task is not a flow, extend the block's end_index forward until you reach a flow operation.
        - Stop extending once another block begins (if, elif, else, for, while, try, except, finally).

    2. Nested Conditions and Loops
    - A parent block must always cover its entire nested scope.
    - Nested if/elif/else/for/while/try/except blocks must remain fully inside their parent range.
    - Example:
        Outer if (task 4) → "4 to 7"
        Nested if (task 6) → "6 to 7"
    - Do NOT collapse nested blocks into the parent, but ensure parent extends until the nested end.

    3. If–Elif–Else Chains
    - An `if` block must end before the first `elif` or `else`.
    - Orders: if=1, elif=2, else=3.

    4. Loops and Exceptions
    - Apply the same rules for for/while/try/except/finally blocks.
    - Each must include at least one flow task inside.
    - Extend end_index until next block or explicit end marker.

    5. Each Block Must Include:
    - "task_no": a single number or a range, e.g. "4 to 8"
    - "condition" (or "iteration_range" for loops, or "exception" for try/except): exactly as written in the user input
    - "order": sequence number (if=1, elif=2, else=3, loops = based on appearance order)
    - "task_start_index": first task number of the block
    - "task_end_index": last task number of the block
    - For elif/else blocks, also include "native_if_elif_task_no": list of linked parent if/elif task ranges
    
    6.Start and End Index Range Calculation:
    - The Start Index can be determined directly from the current task index.
    - Before finalizing the End Index, verify whether any nested block related to the current task appears afterward
    - If a nested block related to current task exists, extend the End Index to cover that block completely, ensuring the entire condition flow is included
    - If the user input explicitly specifies an end of a nested condition, assign the End Index immediately at that point.
    
    7. Do NOT shift or guess indexes.
    - task_start_index and task_end_index must map exactly to tasks in the Generated Tasks list.
    - If a block has no body task, extend forward until you find a body or next block marker.

    8. Output
    - Return ONLY a JSON object with blocks grouped under "if", "elif", "else", "for", "while", "try", "except", "finally".
    - If no conditions, loops, or exceptions exist, return {{}}.
    - Do not add explanations or extra text.

    Format Example:
    {sample_response}

    
    
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

def gemini_response(input):
    # Set your API key here
    genai.configure(api_key=config.API_KEY)
    model = genai.GenerativeModel(model_name="gemini-2.5-flash-lite")
    chat = model.start_chat()
    sample_requirement = """
    Open the website https://app.taskmanagerpro.io/, then enter the email address as 'user@example.com' and password as 'securepass123' by citrix flow, and click the 'Sign In' button.
    After logging in, navigate to the 'Tasks' section from the sidebar by citrix flow.
    Click on 'New Task' button, enter the task title as 'Submit Report', set the due date to '2025-07-15', and add a description saying 'Monthly financial report submission'.
    Finally, click the 'Create Task' button to save it.
    Click the Run button.
    """

    sample_response = '["Open the URL https://app.taskmanagerpro.io/","Type email as user@example.com","Type password as securepass123 by Citrix Automation","Click Sign In button Event","Click Tasks section from sidebar by Citrix Automation","Click New Task button","Type Submit Report in task title field","Set due date as 2025-07-15","Type Monthly financial report submission in task description field","Click Create Task button","Click Run Button"]'

    prompt = f"""
    You are an expert instruction breakdown agent for automation flows.  
    Your task is to read a user's natural language requirement describing a sequence of UI or system actions and convert it into a **clear, structured list of step-by-step instructions**.  
    Each step must be represented as a **single string** in a **Python list format**.

    ================================================================================
    CRITICAL BEHAVIOR RULES
    ================================================================================
    1. **No Python code**, explanations, or text — only return a valid Python list of strings.
    2. Each list item must describe exactly one clear, actionable step.
    3. Maintain the **original sequence** of the user's instructions.
    4. Be context-aware — if a step depends on a previous one, phrase it naturally (e.g., "After logging in…").
    5. Keep capitalization consistent and verbs clear (e.g., "Click", "Type", "Open", "Set", "Extract").
    6. When referring to elements, use natural language (e.g., "Click Sign In button", "Type email as …").
    7. If the user mentions "extracting table data", follow the Table Extraction Rules below.
    8. If the user mentions "sending mail" or "reading mail", follow the Mail Operation Rules below.

    ================================================================================
    TABLE EXTRACTION RULES
    ================================================================================
    When the user mentions extracting table data:
    1. **Always specify which table** by referencing the heading or section it is under.
    2. **Use format**:
       - "Extract the table under [SPECIFIC_HEADING] heading", or
       - "Extract the table below [SPECIFIC_SECTION] section."
    3. **Never use** generic phrases like "extract table data" or "get table contents."
    4. **Be specific** and contextual based on the surrounding description.

    ================================================================================
    MAIL OPERATION RULES
    ================================================================================
    When the user mentions sending or reading emails:
    
    ### FOR SENDING MAIL:
    1. **Consolidate all email parameters into a single step**.
    2. **Required format**:
       "Send mail from [FROM_EMAIL] to [TO_EMAIL] with subject [SUBJECT] and body [BODY] using CLIENT_ID [CLIENT_ID], CLIENT_SECRET [CLIENT_SECRET], TENANT_ID [TENANT_ID]"
    3. **Always include all parameters** mentioned by the user in this exact order:
       - from (sender email)
       - to (recipient email)
       - subject
       - body
       - CLIENT_ID
       - CLIENT_SECRET
       - TENANT_ID
    4. **Subject and Body Intelligence Rules**:
       a) **If NEITHER subject NOR body provided**:
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
    
    5. **Never split** mail sending into multiple steps.
    6. **Credentials handling**: If CLIENT_ID, CLIENT_SECRET, or TENANT_ID not provided, use [NOT_PROVIDED].

    ### FOR READING MAIL:
    1. **Consolidate all email parameters into a single step**.
    2. **Required format**:
       "Read mail from mailbox [MAILBOX_EMAIL] using CLIENT_ID [CLIENT_ID], CLIENT_SECRET [CLIENT_SECRET], TENANT_ID [TENANT_ID] with filter [FILTER_CRITERIA]"
    3. **Always include**:
       - mailbox (email account to read from)
       - CLIENT_ID
       - CLIENT_SECRET
       - TENANT_ID
       - filter criteria (if specified, e.g., "unread only", "from specific sender", "subject contains")
    4. If filter criteria is not mentioned, use "all emails".
    5. **Never split** mail reading into multiple steps.
    6. **Credentials handling**: If CLIENT_ID, CLIENT_SECRET, or TENANT_ID not provided, use [NOT_PROVIDED].

    ### EXAMPLES:
    - Send Mail (all provided): "Send mail from sales@company.com to client@example.com with subject Invoice for April and body Please find the attached invoice for your review using CLIENT_ID abc123, CLIENT_SECRET xyz789, TENANT_ID tenant456"
    
    - Send Mail (only body provided): "Send mail from sales@company.com to client@example.com with subject Invoice Review Request and body Please find the attached invoice for your review using CLIENT_ID abc123, CLIENT_SECRET xyz789, TENANT_ID tenant456"
    
    - Send Mail (only subject provided): "Send mail from sales@company.com to client@example.com with subject Meeting Reminder and body This is a reminder about our scheduled meeting. Please confirm your availability. using CLIENT_ID abc123, CLIENT_SECRET xyz789, TENANT_ID tenant456"
    
    - Send Mail (neither provided): "Send mail from sales@company.com to client@example.com with subject Automated Email Notification and body This is an automated email sent via workflow automation. using CLIENT_ID abc123, CLIENT_SECRET xyz789, TENANT_ID tenant456"
    
    - Read Mail: "Read mail from support@company.com using CLIENT_ID abc123, CLIENT_SECRET xyz789, TENANT_ID tenant456 with filter unread only"

    ================================================================================
    EXAMPLE
    ================================================================================
    Example Input:
    {sample_requirement}

    Example Output:
    {sample_response}

    ================================================================================
    FINAL TASK
    ================================================================================
    Now, analyze and classify the following user requirement:
    {input}

    ### OUTPUT RULES:
    - Return only the Python list of strings.
    - No explanations, comments, or extra formatting.
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
        if res.startswith("[") and res.endswith("]"):
            res=ast.literal_eval(res)
        else:
            try:
                res=ast.literal_eval(res)
            except:
                pass
    

    return res

# input="""
# open this url https://droidal.ai/login
# type username as admin as citrix
# type password as 2610
# click login button by citrix flow"""
# res=gemini_response(input)
# print(res)