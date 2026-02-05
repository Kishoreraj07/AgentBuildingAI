from google import genai
import google.generativeai as genai1
from datas.source_files import config
import json
import time


def text_extract(img_file_path,description):
    desc=description
    print(img_file_path)
    # genai.configure(api_key=config.API_KEY)
    # try:
    client = genai.Client(api_key=config.API_KEY)
    if img_file_path.lower().endswith(('.png', '.jpg', '.jpeg', '.bmp')):
        # Upload the PDF file
        img_file = client.files.upload(file=img_file_path)
        
        # Wait for the file to be processed
        import time
        while img_file.state.name == "PROCESSING":
            print("Processing PDF file...")
            time.sleep(2)
            img_file = client.files.get(img_file.name)
        
        if img_file.state.name == "FAILED":
            raise ValueError("Image file processing failed")
        
        # Create model and send message with the uploaded file
        # model = genai.GenerativeModel(model_name="gemini-2.5-flash-lite",client=client)
        
        prompt=f"""
        ===============================================================================
        🎯 USER ACTION REQUIREMENT
        ===============================================================================
        {desc}

        ===============================================================================
        📎 PROVIDED INPUT
        ===============================================================================
        An image has been attached containing text content to be extracted.

        ===============================================================================
        🔍 TASK ANALYSIS & EXECUTION
        ===============================================================================
        Analyze the attached image and the user's request to determine what text to extract:

        **EXTRACTION TYPES:**

        1. **FULL TEXT EXTRACTION**
           - User asks: "extract text", "get all text", "OCR the image", "read the content"
           - Action: Extract ALL visible text from the entire image

        2. **TARGETED TEXT EXTRACTION**
           - User asks: "extract text after [keyword]", "get text from [section]", "extract [specific field]"
           - Action: Extract ONLY the requested text portion or field value

        3. **SPECIFIC FIELD EXTRACTION**
           - User asks: "extract subscriber name", "get invoice number", "find the date"
           - Action: Locate and extract ONLY the value of that specific field

        ===============================================================================
        📤 OUTPUT FORMAT (MANDATORY)
        ===============================================================================

        **Return JSON in this EXACT format:**
```json
        {{
            "result": "extracted text content here"
        }}
```

        ===============================================================================
        📋 DETAILED EXAMPLES
        ===============================================================================

        **Example 1 - Full Text Extraction:**
        User Request: "Extract all text from this image"
        Image contains: "Invoice #12345\nDate: 2024-01-15\nSubscriber: John Doe\nTotal: $599.99"

        Response:
        {{
            "result": "Invoice #12345\nDate: 2024-01-15\nSubscriber: John Doe\nTotal: $599.99"
        }}

        **Example 2 - Targeted Text Extraction:**
        User Request: "Extract text after 'Date:'"
        Image contains: "Invoice #12345\nDate: 2024-01-15\nSubscriber: John Doe\nTotal: $599.99"

        Response:
        {{
            "result": "2024-01-15\nSubscriber: John Doe\nTotal: $599.99"
        }}

        **Example 3 - Specific Field Extraction:**
        User Request: "Extract the subscriber name"
        Image contains: "Invoice #12345\nDate: 2024-01-15\nSubscriber: John Doe\nTotal: $599.99"

        Response:
        {{
            "result": "John Doe"
        }}

        **Example 4 - Field Value Extraction:**
        User Request: "Get the invoice number value"
        Image contains: "Invoice #12345\nDate: 2024-01-15\nSubscriber: John Doe"

        Response:
        {{
            "result": "12345"
        }}

        **Example 5 - Section Extraction:**
        User Request: "Extract text from the payment section"
        Image contains multiple sections with payment details in one section

        Response:
        {{
            "result": "Payment Method: Credit Card\nCard ending: 1234\nAmount: $599.99"
        }}

        ===============================================================================
        ⚠️ CRITICAL REQUIREMENTS
        ===============================================================================
        1. **Response Format**: ONLY return valid JSON - no explanations, no markdown, no extra text
        2. **No Markdown**: Do not wrap response in ```json``` code blocks
        3. **Exact Structure**: Follow the exact JSON structure: {{"result": "text"}}
        4. **Data Type**: result must always be a string
        5. **Clean Data**: Remove unnecessary whitespace, preserve meaningful line breaks
        6. **Empty Data Handling**: If no text found: {{"result": ""}}
        7. **Error Handling**: If image cannot be processed: {{"result": null, "error": "brief description"}}
        8. **Context Awareness**: Understand the user's intent and extract accordingly

        ===============================================================================
        🎨 PROCESSING GUIDELINES
        ===============================================================================

        **For Full Text Extraction:**
        - Extract all visible text from the image
        - Maintain natural reading order (left-to-right, top-to-bottom)
        - Preserve line breaks between paragraphs or sections
        - Include all labels, values, headers, and body text

        **For Targeted Text Extraction:**
        - Locate the specified keyword/section/position
        - Extract text from that point forward or in that area
        - Maintain context and formatting of the extracted portion

        **For Specific Field Extraction:**
        - Identify the field label (e.g., "Subscriber:", "Name:", "Invoice #")
        - Extract ONLY the value associated with that field
        - Remove the label itself unless specifically requested
        - Return just the clean value

        **General Rules:**
        - Keep text as-is (don't translate or modify unless requested)
        - Preserve meaningful formatting (line breaks, spacing)
        - Remove excessive whitespace
        - Handle field separators (colons, equals, etc.) intelligently
        - If field not found, return empty string: {{"result": ""}}

        ===============================================================================
        ✅ FINAL CHECKLIST
        ===============================================================================
        Before returning your response, verify:
        - [ ] Output is valid JSON (can be parsed)
        - [ ] No markdown formatting or code blocks
        - [ ] No explanatory text before or after JSON
        - [ ] Structure is: {{"result": "string value"}}
        - [ ] Extracted the correct portion based on user request
        - [ ] Text is clean and properly formatted
        - [ ] Only JSON response, nothing else

        ===============================================================================
        🚀 NOW PROCESS THE IMAGE AND RETURN ONLY THE JSON RESPONSE
        ===============================================================================
        """
        
        response = client.models.generate_content(
            model='gemini-2.5-flash-lite',
            contents=[prompt, img_file]
        )
        
        # Clean up - delete the uploaded file
        client.files.delete(name=img_file.name)

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
    if isinstance(res, dict) and "result" in res:
        return res["result"]
    else:
        # Return None or raise an error if 'x_path' is not found
        return None

    
    # return res

# Usage
# pdf_file = r"C:\Users\Kishore.k\Downloads\captcha1.png"
# desc="Need to extract the captcha content from the image"
# response = gemini_image_response(pdf_file,desc)
# print(response)
