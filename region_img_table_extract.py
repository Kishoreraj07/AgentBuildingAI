from google import genai
import google.generativeai as genai1
from datas.source_files import config
import json
from PIL import ImageGrab
import time

def capture_region(bound_index):
    time.sleep(3)
    save_path="temp_image.png"
    if len(bound_index) != 4:
        raise ValueError("bound_index must be [left, right, top, bottom]")

    left, right, top, bottom = bound_index

    try:
        img = ImageGrab.grab(bbox=(left, top, right, bottom))
        img.save(save_path)
        print(f"Screenshot saved to {save_path}")
        return save_path
    except Exception as e:
        print(f"Error capturing screenshot: {e}")
        return save_path

def gemini_image_response(img_file_path,desc):
    print(img_file_path)
    # genai.configure(api_key=config.API_KEY)
    # try:
    client = genai.Client(api_key=config.API_KEY)
    if img_file_path.endswith('.png'):
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
        An image has been attached containing either:
        - Text content to be extracted
        - Table/tabular data to be extracted

        ===============================================================================
        🔍 TASK ANALYSIS & EXECUTION
        ===============================================================================
        Analyze the attached image and the user's action requirement to determine the extraction type:

        **TYPE 1: TEXT EXTRACTION**
        If the action is about extracting text (e.g., "extract text", "get text from image", "read text", "OCR the content"):
        - Extract all visible text from the image
        - Return the extracted text as a clean string
        - Preserve line breaks and formatting where meaningful

        **TYPE 2: TABLE EXTRACTION**
        If the action is about extracting table data (e.g., "extract table", "get table data", "scrape table", "parse table"):
        - Identify and extract the table structure (headers and rows)
        - Parse the data into structured format
        - Each column should be represented as a dictionary with column name as key and list of values

        ===============================================================================
        📤 OUTPUT FORMAT (MANDATORY)
        ===============================================================================

        **For TEXT EXTRACTION - Return JSON in this EXACT format:**
        ```json
        {{
        "result": "extracted text content here"
        }}
        ```

        **For TABLE EXTRACTION - Return JSON in this EXACT format:**
        ```json
        {{
        "result": [
            {{
            "Column1": ["value1_row1", "value1_row2", "value1_row3"],
            "Column2": ["value2_row1", "value2_row2", "value2_row3"],
            "Column3": ["value3_row1", "value3_row2", "value3_row3"]
            }}
        ]
        }}
        ```

        **Table Format Explanation:**
        - The `result` field contains a list with ONE dictionary
        - Each key in the dictionary is a column name (string)
        - Each value is a list containing all values from that column in order
        - All column value lists must have the same length (number of rows)
        - Preserve column order as they appear in the image

        ===============================================================================
        📋 DETAILED EXAMPLES
        ===============================================================================

        **Example 1 - Text Extraction:**
        User Action: "Extract text from this invoice image"
        Image contains: "Invoice #12345\nDate: 2024-01-15\nTotal: $599.99"

        Response:
        ```json
        {{
        "result": "Invoice #12345\nDate: 2024-01-15\nTotal: $599.99"
        }}
        ```

        **Example 2 - Table Extraction:**
        User Action: "Extract the product table from this image"
        Image contains table:
        | Product | Price | Quantity |
        |---------|-------|----------|
        | Apple   | $2.50 | 10       |
        | Banana  | $1.20 | 15       |
        | Orange  | $3.00 | 8        |

        Response:
        ```json
        {{
        "result": [
            {{
            "Product": ["Apple", "Banana", "Orange"],
            "Price": ["$2.50", "$1.20", "$3.00"],
            "Quantity": ["10", "15", "8"]
            }}
        ]
        }}
        ```

        **Example 3 - Table Extraction (Multi-column):**
        User Action: "Get table data"
        Image contains table:
        | Name | Age | City | Country |
        |------|-----|------|---------|
        | John | 25  | NYC  | USA     |
        | Emma | 30  | London | UK    |

        Response:
        ```json
        {{
        "result": [
            {{
            "Name": ["John", "Emma"],
            "Age": ["25", "30"],
            "City": ["NYC", "London"],
            "Country": ["USA", "UK"]
            }}
        ]
        }}
        ```

        ===============================================================================
        ⚠️ CRITICAL REQUIREMENTS
        ===============================================================================
        1. **Response Format**: ONLY return valid JSON - no explanations, no markdown, no extra text
        2. **No Markdown**: Do not wrap response in ```json``` code blocks
        3. **Exact Structure**: Follow the exact JSON structure specified above
        4. **Data Types**: 
        - Text extraction: result is a string
        - Table extraction: result is a list containing one dictionary
        5. **Table Structure**: 
        - Keys = column names (strings)
        - Values = lists of all values in that column
        - All value lists must have equal length
        6. **Clean Data**: Remove unnecessary whitespace, preserve meaningful formatting
        7. **Empty Data Handling**: 
        - If no text found: `{{"result": ""}}`
        - If no table found: `{{"result": [{{}}]}}`
        8. **Error Handling**: If image cannot be processed, return: `{{"result": null, "error": "brief error description"}}`

        ===============================================================================
        🎨 PROCESSING GUIDELINES
        ===============================================================================
        **For Text Extraction:**
        - Use OCR to extract all visible text
        - Maintain natural reading order (left-to-right, top-to-bottom)
        - Preserve line breaks between paragraphs or sections
        - Remove excessive whitespace
        - Keep text as-is (don't translate or modify)

        **For Table Extraction:**
        - Identify table boundaries and structure
        - Detect column headers (usually first row or bold text)
        - Extract all rows systematically
        - Align data correctly with column headers
        - Handle merged cells appropriately
        - Preserve data types as strings (don't convert numbers)
        - If no clear headers, use generic names: "Column1", "Column2", etc.

        ===============================================================================
        ✅ FINAL CHECKLIST
        ===============================================================================
        Before returning your response, verify:
        - [ ] Output is valid JSON (can be parsed)
        - [ ] No markdown formatting or code blocks
        - [ ] No explanatory text before or after JSON
        - [ ] Correct structure based on extraction type
        - [ ] For tables: all column lists have equal length
        - [ ] For tables: result is a list containing one dictionary
        - [ ] Data is clean and properly formatted

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
# pdf_file = r"C:\Users\Kishore.k\Documents\req_new.txt"
# response = gemini_pdf_response(pdf_file)
# print(response)
