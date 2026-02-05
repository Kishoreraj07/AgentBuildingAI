from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
from xpath_find import main
from element_confirmation import element_status
from verify_xpath import mod_xpath
import json
import os
import openpyxl

def automate_aetna():
    # Initialize WebDriver (replace with your preferred browser)
    driver = webdriver.Chrome()  # or Firefox(), Edge()

    # 4. Navigate to URL
    driver.get("https://www.aetna.com/provweb/index.html")

    # Load JSON for XPaths
    with open("json_info/json_xpath.json", "r") as f:
        json_xpath = json.load(f)

    # 7. Highlight Username Input Field (Log In tab), Enter username and password
    username_xpath = main("username field in login tab", driver)
    username_result = element_status(username_xpath, driver)

    if username_result:
        username_element = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, username_xpath))
        )
    else:
        username_xpath = mod_xpath(driver)
        username_element = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, username_xpath))
        )

    # Highlight the element
    driver.execute_script("arguments[0].style.border='3px solid red'", username_element)
    json_xpath["username_xpath"] = username_xpath
    with open("json_info/json_xpath.json", "w") as f:
        json.dump(json_xpath, f, indent=4)
        
    username_element.send_keys("drsofteeth6825")


    password_xpath = main("password field in login tab", driver)
    password_result = element_status(password_xpath, driver)

    if password_result:
        password_element = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, password_xpath))
        )
    else:
        password_xpath = mod_xpath(driver)
        password_element = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, password_xpath))
        )

    # Highlight the element
    driver.execute_script("arguments[0].style.border='3px solid red'", password_element)
    json_xpath["password_xpath"] = password_xpath
    with open("json_info/json_xpath.json", "w") as f:
        json.dump(json_xpath, f, indent=4)
        
    password_element.send_keys("01toothbrush")

    # 8. Click "Log In" button
    login_button_xpath = main("Log In button", driver)
    login_button_result = element_status(login_button_xpath, driver)

    if login_button_result:
        login_button_element = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, login_button_xpath))
        )
    else:
        login_button_xpath = mod_xpath(driver)
        login_button_element = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, login_button_xpath))
        )

    json_xpath["login_button_xpath"] = login_button_xpath
    with open("json_info/json_xpath.json", "w") as f:
        json.dump(json_xpath, f, indent=4)
    login_button_element.click()


    # 10. Click "Continue" button
    continue_button_xpath = main("Continue button after login", driver)
    continue_button_result = element_status(continue_button_xpath, driver)

    if continue_button_result:
        continue_button_element = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, continue_button_xpath))
        )
    else:
        continue_button_xpath = mod_xpath(driver)
        continue_button_element = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, continue_button_xpath))
        )

    json_xpath["continue_button_xpath"] = continue_button_xpath
    with open("json_info/json_xpath.json", "w") as f:
        json.dump(json_xpath, f, indent=4)
    continue_button_element.click()

    # 12. Click 'eligibility & benefits' hyperlink button.
    eligibility_benefits_xpath = main("eligibility & benefits hyperlink", driver)
    eligibility_benefits_result = element_status(eligibility_benefits_xpath, driver)

    if eligibility_benefits_result:
        eligibility_benefits_element = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, eligibility_benefits_xpath))
        )
    else:
        eligibility_benefits_xpath = mod_xpath(driver)
        eligibility_benefits_element = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, eligibility_benefits_xpath))
        )

    json_xpath["eligibility_benefits_xpath"] = eligibility_benefits_xpath
    with open("json_info/json_xpath.json", "w") as f:
        json.dump(json_xpath, f, indent=4)
    eligibility_benefits_element.click()


    # 13. Click 'continue' hyperlink button.
    continue_hyperlink_xpath = main("continue hyperlink after eligibility & benefits", driver)
    continue_hyperlink_result = element_status(continue_hyperlink_xpath, driver)

    if continue_hyperlink_result:
        continue_hyperlink_element = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, continue_hyperlink_xpath))
        )
    else:
        continue_hyperlink_xpath = mod_xpath(driver)
        continue_hyperlink_element = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, continue_hyperlink_xpath))
        )

    json_xpath["continue_hyperlink_xpath"] = continue_hyperlink_xpath
    with open("json_info/json_xpath.json", "w") as f:
        json.dump(json_xpath, f, indent=4)
    continue_hyperlink_element.click()

    # 16. Wait for the dental xchange fully load in the screen.
    WebDriverWait(driver, 30).until(
        EC.presence_of_element_located((By.ID, "dentalXChangeFrame"))
    )

    # Switch to the iframe
    driver.switch_to.frame("dentalXChangeFrame")

    # 17. Click the Provider field
    provider_field_xpath = main("provider field", driver)
    provider_field_result = element_status(provider_field_xpath, driver)

    if provider_field_result:
        provider_field_element = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, provider_field_xpath))
        )
    else:
        provider_field_xpath = mod_xpath(driver)
        provider_field_element = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, provider_field_xpath))
        )
    json_xpath["provider_field_xpath"] = provider_field_xpath
    with open("json_info/json_xpath.json", "w") as f:
        json.dump(json_xpath, f, indent=4)
    provider_field_element.click()


    # 17. Select the provider from the dropdown menu given as'zie Kelley - 1590 LITTLE RAVEN ST SUITE 180, 1356703847, 273182175, 204285'
    provider_option_xpath = main("provider option 'zie Kelley - 1590 LITTLE RAVEN ST SUITE 180, 1356703847, 273182175, 204285'", driver)
    provider_option_result = element_status(provider_option_xpath, driver)

    if provider_option_result:
        provider_option_element = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, provider_option_xpath))
        )
    else:
        provider_option_xpath = mod_xpath(driver)
        provider_option_element = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, provider_option_xpath))
        )

    json_xpath["provider_option_xpath"] = provider_option_xpath
    with open("json_info/json_xpath.json", "w") as f:
        json.dump(json_xpath, f, indent=4)
    provider_option_element.click()

    # 18. Click the payer name field.
    payer_name_field_xpath = main("payer name field", driver)
    payer_name_field_result = element_status(payer_name_field_xpath, driver)

    if payer_name_field_result:
        payer_name_field_element = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, payer_name_field_xpath))
        )
    else:
        payer_name_field_xpath = mod_xpath(driver)
        payer_name_field_element = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, payer_name_field_xpath))
        )

    json_xpath["payer_name_field_xpath"] = payer_name_field_xpath
    with open("json_info/json_xpath.json", "w") as f:
        json.dump(json_xpath, f, indent=4)
    payer_name_field_element.click()

    # 18. Select 'Aetna Dental Plans - 60054' from the dropdown menu.
    payer_name_option_xpath = main("payer name option 'Aetna Dental Plans - 60054'", driver)
    payer_name_option_result = element_status(payer_name_option_xpath, driver)

    if payer_name_option_result:
        payer_name_option_element = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, payer_name_option_xpath))
        )
    else:
        payer_name_option_xpath = mod_xpath(driver)
        payer_name_option_element = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, payer_name_option_xpath))
        )

    json_xpath["payer_name_option_xpath"] = payer_name_option_xpath
    with open("json_info/json_xpath.json", "w") as f:
        json.dump(json_xpath, f, indent=4)
    payer_name_option_element.click()

    # 19. Type 'W483087700' in the Member ID or SSN field
    member_id_xpath = main("member id field", driver)
    member_id_result = element_status(member_id_xpath, driver)

    if member_id_result:
        member_id_element = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, member_id_xpath))
        )
    else:
        member_id_xpath = mod_xpath(driver)
        member_id_element = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, member_id_xpath))
        )

    json_xpath["member_id_xpath"] = member_id_xpath
    with open("json_info/json_xpath.json", "w") as f:
        json.dump(json_xpath, f, indent=4)
    member_id_element.send_keys("W483087700")

    # 20. Type 'Chrisman' in the lastname field
    last_name_xpath = main("last name field", driver)
    last_name_result = element_status(last_name_xpath, driver)

    if last_name_result:
        last_name_element = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, last_name_xpath))
        )
    else:
        last_name_xpath = mod_xpath(driver)
        last_name_element = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, last_name_xpath))
        )

    json_xpath["last_name_xpath"] = last_name_xpath
    with open("json_info/json_xpath.json", "w") as f:
        json.dump(json_xpath, f, indent=4)
    last_name_element.send_keys("Chrisman")

    # 21. Type 'Jonah' in the firstname field
    first_name_xpath = main("first name field", driver)
    first_name_result = element_status(first_name_xpath, driver)

    if first_name_result:
        first_name_element = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, first_name_xpath))
        )
    else:
        first_name_xpath = mod_xpath(driver)
        first_name_element = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, first_name_xpath))
        )

    json_xpath["first_name_xpath"] = first_name_xpath
    with open("json_info/json_xpath.json", "w") as f:
        json.dump(json_xpath, f, indent=4)
    first_name_element.send_keys("Jonah")

    # 22. Type '5/16/1999' in the Date of Birth field
    date_of_birth_xpath = main("date of birth field", driver)
    date_of_birth_result = element_status(date_of_birth_xpath, driver)

    if date_of_birth_result:
        date_of_birth_element = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, date_of_birth_xpath))
        )
    else:
        date_of_birth_xpath = mod_xpath(driver)
        date_of_birth_element = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, date_of_birth_xpath))
        )

    json_xpath["date_of_birth_xpath"] = date_of_birth_xpath
    with open("json_info/json_xpath.json", "w") as f:
        json.dump(json_xpath, f, indent=4)
    date_of_birth_element.send_keys("5/16/1999")

    # 23. Click 'Continue' button to proceed further.
    continue_button2_xpath = main("Continue button after DOB", driver)
    continue_button2_result = element_status(continue_button2_xpath, driver)

    if continue_button2_result:
        continue_button2_element = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, continue_button2_xpath))
        )
    else:
        continue_button2_xpath = mod_xpath(driver)
        continue_button2_element = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, continue_button2_xpath))
        )

    json_xpath["continue_button2_xpath"] = continue_button2_xpath
    with open("json_info/json_xpath.json", "w") as f:
        json.dump(json_xpath, f, indent=4)
    continue_button2_element.click()

    # 24. Wait until patient details & benefits search tab appears on the screen.
    WebDriverWait(driver, 30).until(
        EC.presence_of_element_located((By.ID, "patientInformation"))
    )

    # 25. After page fully loaded- extract the patient information in the patient information tab.
    patient_info_xpath = main("patient information tab content", driver)
    patient_info_result = element_status(patient_info_xpath, driver)

    if patient_info_result:
        patient_info_element = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, patient_info_xpath))
        )
    else:
        patient_info_xpath = mod_xpath(driver)
        patient_info_element = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, patient_info_xpath))
        )

    json_xpath["patient_info_xpath"] = patient_info_xpath
    with open("json_info/json_xpath.json", "w") as f:
        json.dump(json_xpath, f, indent=4)
    patient_info = patient_info_element.text
    print(f"Extracted Patient Information: {patient_info}")

    # 26. Extract the Status of the patient.
    status_xpath = main("patient status", driver)
    status_result = element_status(status_xpath, driver)

    if status_result:
        status_element = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, status_xpath))
        )
    else:
        status_xpath = mod_xpath(driver)
        status_element = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, status_xpath))
        )

    json_xpath["status_xpath"] = status_xpath
    with open("json_info/json_xpath.json", "w") as f:
        json.dump(json_xpath, f, indent=4)
    status = status_element.text
    print(f"Extracted Patient Status: {status}")

    # 27. create a json file in the downloads folder as "C:\Users\Ranganathan.m.DROIDAL\Downloads\patient_data.json" and if already created, then don't create it, please proceed further in that json file.
    downloads_path = os.path.join(os.path.expanduser('~'), 'Downloads')
    json_file_path = os.path.join(downloads_path, "patient_data.json")

    patient_data = {}
    if os.path.exists(json_file_path):
        with open(json_file_path, "r") as f:
            try:
                patient_data = json.load(f)
            except json.JSONDecodeError:
                patient_data = {} # Handle empty or corrupted JSON file
    else:
        patient_data = {}

    patient_data["status"] = status

    with open(json_file_path, "w") as f:
        json.dump(patient_data, f, indent=4)

    # 28. Create the patient_data.xlsx file
    excel_file_path = os.path.join(downloads_path, "patient_data.xlsx")
    if not os.path.exists(excel_file_path):
        workbook = openpyxl.Workbook()
        sheet = workbook.active
        sheet['A1'] = 'Status'  # Header
        sheet['A2'] = status     # Value
        workbook.save(excel_file_path)
    else:
        workbook = openpyxl.load_workbook(excel_file_path)
        sheet = workbook.active
        sheet['A2'] = status
        workbook.save(excel_file_path)

    # 27. Display the extracted 'Status' field text.
    print(f"Patient Status: {status}")

    # 28.Click the General Benefits Checkbox
    general_benefits_xpath = main("General Benefits Checkbox", driver)
    general_benefits_result = element_status(general_benefits_xpath, driver)

    if general_benefits_result:
        general_benefits_element = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, general_benefits_xpath))
        )
    else:
        general_benefits_xpath = mod_xpath(driver)
        general_benefits_element = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, general_benefits_xpath))
        )

    json_xpath["general_benefits_xpath"] = general_benefits_xpath
    with open("json_info/json_xpath.json", "w") as f:
        json.dump(json_xpath, f, indent=4)
    general_benefits_element.click()

    # 29.Click 'View Benefits' button
    view_benefits_xpath = main("View Benefits button", driver)
    view_benefits_result = element_status(view_benefits_xpath, driver)

    if view_benefits_result:
        view_benefits_element = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, view_benefits_xpath))
        )
    else:
        view_benefits_xpath = mod_xpath(driver)
        view_benefits_element = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, view_benefits_xpath))
        )

    json_xpath["view_benefits_xpath"] = view_benefits_xpath
    with open("json_info/json_xpath.json", "w") as f:
        json.dump(json_xpath, f, indent=4)
    view_benefits_element.click()

    # 30. Extract the value of patient name.
    patient_name_xpath = main("patient name in benefits section", driver)
    patient_name_result = element_status(patient_name_xpath, driver)

    if patient_name_result:
        patient_name_element = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, patient_name_xpath))
        )
    else:
        patient_name_xpath = mod_xpath(driver)
        patient_name_element = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, patient_name_xpath))
        )

    json_xpath["patient_name_xpath"] = patient_name_xpath
    with open("json_info/json_xpath.json", "w") as f:
        json.dump(json_xpath, f, indent=4)
    patient_name = patient_name_element.text

    # 31.Update the extracted value of patient name only , no other data like member id / dob etc,.. in the patient_data.json file
    with open(json_file_path, "r") as f:
        patient_data = json.load(f)
    patient_data["patient_name"] = patient_name
    with open(json_file_path, "w") as f:
        json.dump(patient_data, f, indent=4)

    # 32. Extract the Payer Group Name.
    payer_group_name_xpath = main("Payer Group Name", driver)
    payer_group_name_result = element_status(payer_group_name_xpath, driver)

    if payer_group_name_result:
        payer_group_name_element = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, payer_group_name_xpath))
        )
    else:
        payer_group_name_xpath = mod_xpath(driver)
        payer_group_name_element = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, payer_group_name_xpath))
        )

    json_xpath["payer_group_name_xpath"] = payer_group_name_xpath
    with open("json_info/json_xpath.json", "w") as f:
        json.dump(json_xpath, f, indent=4)
    payer_group_name = payer_group_name_element.text

    # 33. Update the extracted value of the extracted Group Name in the patient_data.json file.
    with open(json_file_path, "r") as f:
        patient_data = json.load(f)
    patient_data["payer_group_name"] = payer_group_name
    with open(json_file_path, "w") as f:
        json.dump(patient_data, f, indent=4)

    # Switch back to the default content
    driver.switch_to.default_content()

    # Close the browser
    driver.quit()

if __name__ == "__main__":
    automate_aetna()
```

**Explanation and Important Notes:**

*   **Dependencies:**  Make sure you have the required libraries installed:
    ```bash
    pip install selenium openpyxl
    ```
    You'll also need to download the appropriate WebDriver for your browser (e.g., ChromeDriver for Chrome) and place it in a directory included in your system's PATH or specify its location directly in the `webdriver.Chrome()` constructor.

*   **`xpath_find.py`, `element_confirmation.py`, `verify_xpath.py`:** These files are assumed to be in the same directory as your main script.  You *must* create these files and implement the logic described in the rules.  These are critical for the XPath handling mechanism.
    *   `xpath_find.py`: Should contain a `main()` function that takes a description of an element and the driver as input, and returns an XPath string. This is your initial attempt to find the element's XPath.
    *   `element_confirmation.py`: Should contain an `element_status()` function that takes an XPath string and the driver as input, and returns `True` if the element exists on the page and is interactable, and `False` otherwise.
    *   `verify_xpath.py`:  Should contain a `mod_xpath()` function that takes the driver as input and allows the user to interactively identify the correct XPath for an element on the page (e.g., using browser developer tools).  It should then return the corrected XPath string. This is your fallback when the initial XPath from `xpath_find.py` fails.

*   **`json_info/json_xpath.json`:**  Create this file (and the `json_info` directory) and initialize it with the XPath keys and default values:
    ```json
    {
      "username_xpath": "Not_assigned",
      "password_xpath": "Not_assigned",
      "login_button_xpath": "Not_assigned",
      "continue_button_xpath": "Not_assigned",
      "eligibility_benefits_xpath": "Not_assigned",
      "continue_hyperlink_xpath": "Not_assigned",
      "provider_field_xpath": "Not_assigned",
      "provider_option_xpath": "Not_assigned",
      "payer_name_field_xpath": "Not_assigned",
      "payer_name_option_xpath": "Not_assigned",
      "member_id_xpath": "Not_assigned",
      "last_name_xpath": "Not_assigned",
      "first_name_xpath": "Not_assigned",
      "date_of_birth_xpath": "Not_assigned",
      "continue_button2_xpath": "Not_assigned",
      "patient_info_xpath": "Not_assigned",
      "status_xpath": "Not_assigned",
      "general_benefits_xpath": "Not_assigned",
      "view_benefits_xpath": "Not_assigned",
      "patient_name_xpath": "Not_assigned",
      "payer_group_name_xpath": "Not_assigned"
    }
    ```

*   **Error Handling:** This code lacks comprehensive error handling (e.g., `try...except` blocks).  You should add error handling to make the script more robust.

*   **Dynamic Waits:**  Consider using more dynamic `WebDriverWait` conditions that wait for specific elements to become visible, clickable, or present, rather than just waiting for presence.  This can make the script more reliable.

*   **Iframe Switching:** The code includes switching to and from the `dentalXChangeFrame` iframe.  Ensure that the iframe ID is correct and that you switch back to the default content after you're done interacting with elements within the iframe.

*   **File Paths:**  The code uses `os.path.join(os.path.expanduser('~'), 'Downloads')` to construct the file paths for the JSON and Excel files.  This should work on most systems, but you might need to adjust the paths if your Downloads folder is in a different location.

*   **JSON Handling:** The code includes logic to check if the `patient_data.json` file already exists and to load its contents if it does. It also handles potential `JSONDecodeError` exceptions that can occur if the file is empty or corrupted.

*   **Excel Handling:**  The code creates or updates an Excel file using `openpyxl`.  Make sure you have `openpyxl` installed.

*   **Highlighting:** The `driver.execute_script()` calls are used to highlight elements in the browser. This can be helpful for debugging.

*   **Element Descriptions:**  Provide clear and descriptive strings to the `main()` function in `xpath_find.py`. These descriptions will help you identify the elements later if you need to modify the XPaths.

*   **Maintainability:**  The code is structured to be relatively easy to maintain.  The use of functions, descriptive variable names, and comments helps to improve readability.

*   **Security:** Be extremely careful when handling passwords or sensitive information.  Do not store passwords directly in the code or in easily accessible files.  Consider using environment variables or a secure configuration management system.
