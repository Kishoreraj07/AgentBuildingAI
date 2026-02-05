from google import genai
import google.generativeai as genai1
from datas.source_files import config
import json
from PIL import ImageGrab
import time

def gemini_pdf_response(pdf_file_path,desc):
    print(pdf_file_path)
    # genai.configure(api_key=config.API_KEY)
    # try:
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
        
        prompt=f"""
===============================================================================
🎯 USER ACTION REQUIREMENT
===============================================================================
{desc}

===============================================================================
📎 PROVIDED INPUT
===============================================================================
A PDF has been attached containing either:
- Text content to be extracted (from image/scanned PDFs or rich text PDFs)
- Table/tabular data to be extracted (from image/scanned PDFs or rich text PDFs)

The PDF may be:
- **Image-based/Scanned PDF**: Requires OCR for text extraction
- **Rich Text PDF**: Contains selectable/searchable text

User may specify specific pages to process:
- Single page: "page 1", "page 5"
- Multiple specific pages: "page 1, 3, 5"
- Page range: "page 1 to 5", "page 2-7"
- Multiple pages for single table: "page 1 and 2" (treat as one continuous table)

===============================================================================
🔍 TASK ANALYSIS & EXECUTION
===============================================================================
Analyze the attached PDF file and the user's action requirement to determine the extraction type:

**TYPE 1: TEXT EXTRACTION**
If the action is about extracting text (e.g., "extract text", "get text from image", "read text", "OCR the content"):
- Extract all visible text from specified page(s)
- For image-based/scanned PDFs: Use OCR to extract text
- For rich text PDFs: Extract selectable text directly
- Return the extracted text as a clean string
- Preserve line breaks and formatting where meaningful
- If multiple pages specified, concatenate text in page order

**TYPE 2: TABLE EXTRACTION**
If the action is about extracting table data (e.g., "extract table", "get table data", "scrape table", "parse table"):
- Identify and extract the table structure (headers and rows) from specified page(s)
- For image-based/scanned PDFs: Use OCR to detect and extract table
- For rich text PDFs: Parse table structure directly
- **IMPORTANT**: If user specifies multiple pages (e.g., "page 1 and 2", "page 1 to 3", "page 1, 2, 5"), treat them as ONE CONTINUOUS TABLE
- Combine all rows from specified pages into a single table structure
- Parse the data into structured format
- Each column should be represented as a dictionary with column name as key and list of values

===============================================================================
📄 PAGE SPECIFICATION HANDLING
===============================================================================

**Single Page:**
- "page 1" → Extract only from page 1
- "page 5" → Extract only from page 5

**Multiple Specific Pages (as one table):**
- "page 1, 3, 5" → Extract from pages 1, 3, and 5, combine into single result
- "page 1 and 2" → Extract from pages 1 and 2, combine into single result

**Page Range (as one table):**
- "page 1 to 5" → Extract from pages 1, 2, 3, 4, 5, combine into single result
- "page 2-7" → Extract from pages 2 through 7, combine into single result

**No Page Specified:**
- Process all pages in the PDF

**Table Extraction Across Pages:**
- When extracting tables from multiple pages, assume they are continuations of the same table
- Use headers from the first page (or most complete header row)
- Combine all data rows sequentially
- Maintain column alignment across pages

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
- Preserve column order as they appear in the source
- When combining multiple pages, append rows sequentially

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

**Example 2 - Table Extraction (Single Page):**
User Action: "Extract the product table from page 1"
Page 1 contains table:
| Product | Price | Quantity |
|---------|-------|----------|
| Apple   | $2.50 | 10       |
| Banana  | $1.20 | 15       |

Response:
```json
{{
  "result": [
    {{
      "Product": ["Apple", "Banana"],
      "Price": ["$2.50", "$1.20"],
      "Quantity": ["10", "15"]
    }}
  ]
}}
```

**Example 3 - Table Extraction (Multiple Pages as One Table):**
User Action: "Extract table from page 1 and 2"

Page 1 contains:
| Product | Price | Quantity |
|---------|-------|----------|
| Apple   | $2.50 | 10       |
| Banana  | $1.20 | 15       |

Page 2 contains (continuation):
| Product | Price | Quantity |
|---------|-------|----------|
| Orange  | $3.00 | 8        |
| Grape   | $4.50 | 12       |

Response:
```json
{{
  "result": [
    {{
      "Product": ["Apple", "Banana", "Orange", "Grape"],
      "Price": ["$2.50", "$1.20", "$3.00", "$4.50"],
      "Quantity": ["10", "15", "8", "12"]
    }}
  ]
}}
```

**Example 4 - Table Extraction (Page Range):**
User Action: "Extract table from page 1 to 3"

Combined table from pages 1, 2, and 3:

Response:
```json
{{
  "result": [
    {{
      "Name": ["John", "Emma", "Mike", "Sarah", "Tom", "Lisa"],
      "Age": ["25", "30", "28", "35", "22", "29"],
      "City": ["NYC", "London", "Paris", "Tokyo", "Berlin", "Madrid"]
    }}
  ]
}}
```

**Example 5 - Table Extraction (Specific Non-Sequential Pages):**
User Action: "Extract table from page 1, 5, 7"

Combined table from pages 1, 5, and 7:

Response:
```json
{{
  "result": [
    {{
      "ID": ["001", "002", "005", "006", "009", "010"],
      "Status": ["Active", "Pending", "Active", "Closed", "Active", "Pending"]
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
6. **Multi-Page Tables**: 
   - Always combine specified pages into ONE table
   - Do not create separate tables per page
   - Maintain sequential row order
7. **PDF Type Handling**:
   - Detect if PDF is image-based/scanned (use OCR) or rich text (direct extraction)
   - Apply appropriate extraction method automatically
8. **Clean Data**: Remove unnecessary whitespace, preserve meaningful formatting
9. **Empty Data Handling**: 
   - If no text found: `{{"result": ""}}`
   - If no table found: `{{"result": [{{}}]}}`
10. **Error Handling**: If PDF cannot be processed, return: `{{"result": null, "error": "brief error description"}}`
11. **Response Format**: Ensure that the returned JSON data contains the same number of elements for all columns, so that no errors occur—specifically the error "All arrays must be of the same length"—when converting the list of dictionaries into a DataFrame.

===============================================================================
🎨 PROCESSING GUIDELINES
===============================================================================
**For Text Extraction:**
- Detect PDF type (image-based/scanned vs rich text)
- For scanned PDFs: Use OCR to extract all visible text
- For rich text PDFs: Extract text programmatically
- Maintain natural reading order (left-to-right, top-to-bottom)
- Preserve line breaks between paragraphs or sections
- Remove excessive whitespace
- Keep text as-is (don't translate or modify)
- If multiple pages: concatenate text in specified page order

**For Table Extraction:**
- Detect PDF type (image-based/scanned vs rich text)
- For scanned PDFs: Use OCR to detect and extract table structure
- For rich text PDFs: Parse table structure programmatically
- Identify table boundaries and structure on each specified page
- Detect column headers (usually first row or bold text on first page)
- **For multiple pages: treat as ONE continuous table**
- Extract headers once (from first occurrence)
- Combine all data rows from all specified pages sequentially
- Align data correctly with column headers
- Handle merged cells appropriately
- Preserve data types as strings (don't convert numbers)
- If no clear headers, use generic names: "Column1", "Column2", etc.
- Skip repeated headers on continuation pages

**Page Processing Logic:**
- Parse page specifications from user action requirement
- Extract only from specified pages
- If no pages specified, process entire PDF
- Maintain page order when combining results
- For ranges (e.g., "1 to 5"), process all pages inclusively

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
- [ ] For multi-page tables: all pages combined into ONE table
- [ ] Data is clean and properly formatted
- [ ] Correct pages processed based on user specification
- [ ] PDF type (scanned vs rich text) handled appropriately

===============================================================================
🚀 NOW PROCESS THE PDF AND RETURN ONLY THE JSON RESPONSE
===============================================================================
"""
        
        response = client.models.generate_content(
            model='gemini-2.5-flash-lite',
            contents=[prompt, pdf_file]
        )
        
        # Clean up - delete the uploaded file
        client.files.delete(name=pdf_file.name)

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
