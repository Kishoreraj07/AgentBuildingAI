from google import genai
import google.generativeai as genai1
import config
import ast

def gemini_pdf_response(pdf_file_path):
    print(pdf_file_path)
    # genai.configure(api_key=config.API_KEY)
    try:
        client = genai.Client(api_key=config.API_KEY)
        if pdf_file_path.endswith('.pdf'):
            # Upload the PDF file
            pdf_file = client.files.upload(file=pdf_file_path)
            
            # Wait for the file to be processed
            import time
            while pdf_file.state.name == "PROCESSING":
                print("Processing PDF file...")
                time.sleep(2)
                pdf_file = client.files.get(pdf_file.name)
            
            if pdf_file.state.name == "FAILED":
                raise ValueError("PDF file processing failed")
            
            # Create model and send message with the uploaded file
            # model = genai.GenerativeModel(model_name="gemini-2.5-flash-lite",client=client)
            
            sample_requirement = """
            Open the website httpss://app.taskmanagerpro.io/, then enter the email address as 'user@example.com' and password as 'securepass123', and click the 'Sign In' button.
            After logging in, navigate to the 'Tasks' section from the sidebar.
            Click on 'New Task' button, enter the task title as 'Submit Report', set the due date to '2025-07-15', and add a description saying 'Monthly financial report submission'.
            Finally, click the 'Create Task' button to save it.
            Then open the Filezilla Application "C:\\Program Files\\FileZilla FTP Client\\filezilla.exe"
            Then Type Username as ubuntu
            Type Password as 12345
            Then on web portal click the Run button
            """

            sample_response = '["Open the URL httpss://app.taskmanagerpro.io/  Event : Web| App : Chrome","Type email as user@example.com Event : Web | App : Chrome","Type password as securepass123 Event : Web | App : Chrome","Click Sign In button Event : Web | App : Chrome","Click Tasks section from sidebar Event : Web | App : Chrome","Click New Task button Event : Web | App : Chrome","Type Submit Report in task title field Event : Web | App : Chrome","Set due date as 2025-07-15 Event : Web | App : Chrome","Type Monthly financial report submission in task description field Event : Web | App : Chrome","Click Create Task button Event : Web | App : Chrome","Open the Filezilla Application `C:\\Program Files\\FileZilla FTP Client\\filezilla.exe` Event : Desktop | App : Filezilla","Type Username as Ubuntu Event : Desktop | App : Filezilla", "Type Password as 12345 Event : Desktop | App : Filezilla","Click Run Button Event : Desktop | App : Filezilla"]'


            prompt = f"""Please analyze the attached PDF document thoroughly. It is a PDD (Process Definition Document) containing requirement specifications. Based on the analysis, extract and classify the requirements into a structured list of actionable tasks.

            Return the output as a Python list of strings, where each string represents an individual task.

            Example List of task generation from PDD:
            {sample_requirement}

            ##Event Classification:
            Then From the list of generated tasks each task may come from Web Automation or Desktop Automation or Combinely Both
            Based on that it should identify each task referring to Web or Portal by mentioning each as Event : Web or Event : Desktop like below output

            The Final out list of tasks with event should be like below:
            {sample_response}

            Like wise need to analyze the attached PDD and return the Final output list of tasks
            NOTE: 
            - Need to return only as a list of strings, not as a dictionary or any other data structure or any explaination 
            - Automations involving Excel, text files, PDFs, etc., should be categorized as **Web** events, not Desktop.
            - Ensure each step is precise, well-structured, and corresponds exactly to a user action.
            - Ensure do not return the python code just returns the list of python string as explained

            ## Application Classification:
            For Application classification, For all Web tasks, the application should be mentioned as "App : Chrome"
            For Desktop tasks , it should find from user requirement and mention the launch application name with name or path , then Application Name name should be found from that and and apply like App : [Application Name] same for all upcoming Desktop tasks until new application is mentioned in the user requirement.

            ### NOTE :
            - Do not seperate event and App on the final list by , symbol use | symbol as the given structure on : {sample_response}
            - The keywors like back to portal,back to web, back to desktop, back to application, back to browser, switch to portal, switch to web, switch to desktop, switch to application, switch to browser are the keyowrds to differenetiate the tasks from Web and Desktop do not consider these keywords as the task from Web or Desktop
            - For the file path details always use double slash like this \\ do not use single slash to avoid `unicodeescape` error
            """
            
            response = client.models.generate_content(
                model='gemini-2.5-flash-lite',
                contents=[prompt, pdf_file]
            )
            
            # Clean up - delete the uploaded file
            client.files.delete(name=pdf_file.name)
        
        elif pdf_file_path.endswith('.txt'):
            # Read the text file
            with open(pdf_file_path, 'r') as file:
                txt_pdd = file.read()
            genai1.configure(api_key=config.API_KEY)
            model = genai1.GenerativeModel(model_name="gemini-2.5-flash-lite")
            chat = model.start_chat()
            sample_requirement = """
            Open the website httpss://app.taskmanagerpro.io/, then enter the email address as 'user@example.com' and password as 'securepass123', and click the 'Sign In' button.
            After logging in, navigate to the 'Tasks' section from the sidebar.
            Click on 'New Task' button, enter the task title as 'Submit Report', set the due date to '2025-07-15', and add a description saying 'Monthly financial report submission'.
            Finally, click the 'Create Task' button to save it.
            Then open the Filezilla Application r"C:\\Program Files\\FileZilla FTP Client\\filezilla.exe"
            Then Type Username as ubuntu
            Type Password as 12345
            Then on web portal click the Run button
            """

            sample_response = '["Open the URL httpss://app.taskmanagerpro.io/  Event : Web| App : Chrome","Type email as user@example.com Event : Web | App : Chrome","Type password as securepass123 Event : Web | App : Chrome","Click Sign In button Event : Web | App : Chrome","Click Tasks section from sidebar Event : Web | App : Chrome","Click New Task button Event : Web | App : Chrome","Type Submit Report in task title field Event : Web | App : Chrome","Set due date as 2025-07-15 Event : Web | App : Chrome","Type Monthly financial report submission in task description field Event : Web | App : Chrome","Click Create Task button Event : Web | App : Chrome","Open the Filezilla Application r`C:\Program Files\FileZilla FTP Client\filezilla.exe` Event : Desktop | App : Filezilla","Type Username as Ubuntu Event : Desktop | App : Filezilla", "Type Password as 12345 Event : Desktop | App : Filezilla","Click Run Button Event : Desktop | App : Filezilla"]'



            prompt = f"""
            You are given a user's detailed natural language requirement describing a sequence of UI actions. 

            Your task is to break down the request into clear, concise step-by-step instructions also referring to previous instructions, each as a separate string in a list.

            ### CRITICAL REQUIREMENTS FOR TABLE EXTRACTION TASKS:

            **When the user mentions extracting table data:**
            1. **ALWAYS specify which table** by referencing the heading/section it's under
            2. **ALWAYS use format**: "Extract the table under [SPECIFIC_HEADING] heading" or "Extract the table below [SPECIFIC_SECTION] section"
            3. **NEVER use generic terms** like "extract table contents" or "get table data"
            4. **BE SPECIFIC** about the contextual reference (heading, section name, etc.)


            ### Example Input:
            {sample_requirement}

            ### Example Output:
            {sample_response}

            Now classify the following user requirement in the same format:

            {txt_pdd}

            ##Event Classification:
            Then From the list of generated tasks each task may come from Web Automation or Desktop Automation or Combinely Both
            Based on that it should identify each task referring to Web or Portal by mentioning each as Event : Web or Event : Desktop like below output

            The Final out list of tasks with event should be like below:
            {sample_response}

            Like wise need to analyze the attached PDD and return the Final output list of tasks
            NOTE: 
            - Need to return only as a list of strings, not as a dictionary or any other data structure or any explaination 
            - Automations involving Excel, text files, PDFs, etc., should be categorized as **Web** events, not Desktop.
            - Ensure each step is precise, well-structured, and corresponds exactly to a user action.
            - Ensure do not return the python code just returns the list of python string as explained

            ## Application Classification:
            For Application classification, For all Web tasks, the application should be mentioned as "App : Chrome"
            For Desktop tasks , it should find from user requirement and mention the launch application name with name or path , then Application Name name should be found from that and and apply like App : [Application Name] same for all upcoming Desktop tasks until new application is mentioned in the user requirement.

            ### NOTE :
            - Do not seperate event and App on the final list by , symbol use | symbol as the given structure on : {sample_response}
            - The keywors like back to portal,back to web, back to desktop, back to application, back to browser, switch to portal, switch to web, switch to desktop, switch to application, switch to browser are the keyowrds to differenetiate the tasks from Web and Desktop do not consider these keywords as the task from Web or Desktop
            - Return only a valid Python list literal as the final output. Do not include any explanation, intro text, or markdown formatting. The response must start with '[' and end with ']'.
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
        full_info=res
        descriptions = []
        events = []
        apps = []
        # res="Here is the detailed analysis \n"+res
        if type(res)!=list:
            import re
            match = re.search(r"\[.*\]", res, re.DOTALL)
            if match:
                res = match.group(0)
            if res.startswith("[") and res.endswith("]"):
                res=ast.literal_eval(res)
            else:
                try:
                    res=ast.literal_eval(res)
                except:
                    pass

        for item in res:
            # Split by 'Event :'
            if "Event :" in item:
                desc, rest = item.split("Event :", 1)
                descriptions.append(desc.strip())
                
                # Split remaining part by '| App :'
                if "| App :" in rest:
                    event_part, app_part = rest.split("| App :", 1)
                    events.append("Event :" + event_part.strip())
                    apps.append("App :" + app_part.strip())
                else:
                    events.append("Event :" + rest.strip())
                    apps.append("")
            else:
                descriptions.append(item.strip())
                events.append("")
                apps.append("")

        result = [descriptions, events, apps]

        return result[0]
    except Exception as e:
        print(f"Error in gemini_pdf_response: {str(e)}")
        raise Exception(f"File processing failed: {str(e)}")

    
    # return res

# Usage
# pdf_file = r"C:\Users\Kishore.k\Documents\req_new.txt"
# response = gemini_pdf_response(pdf_file)
# print(response)
