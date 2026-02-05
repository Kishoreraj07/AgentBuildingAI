from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException, TimeoutException

def run(driver: WebDriver):
    main_dropdown_xpath = "/html/body/div[2]/div/div[1]/div[2]/div[1]/div/div/div/form/div[2]/div[3]"
    user_requirements = ['Offer Approved', 'Offer Accepted', 'Cleared to Start/Hire']

    wait = WebDriverWait(driver, 10)

    try:
        main_dropdown_container = wait.until(EC.presence_of_element_located((By.XPATH, main_dropdown_xpath)))

        # Click to expand the filter if it's collapsed
        header_element = main_dropdown_container.find_element(By.XPATH, ".//div[contains(@class, 'pointer')]")
        if 'triangle-collapsed' in header_element.find_element(By.TAG_NAME, 'i').get_attribute('class'):
            header_element.click()

        # Find the multi-select input field
        select2_container = wait.until(EC.presence_of_element_located((By.XPATH, ".//div[contains(@class, 'select2-container-multi')]")))
        search_input = select2_container.find_element(By.XPATH, ".//input[contains(@class, 'select2-input')]")

        # Iterate through the required options and select them
        for option_text in user_requirements:
            # Type the option into the search box to make it visible
            search_input.send_keys(option_text)

            # Wait for the dropdown results to appear and find the specific option
            try:
                option_xpath = f".//li[contains(@class, 'select2-result-selectable') and .//div[text()='{option_text}']]"
                option_element = wait.until(EC.element_to_be_clickable((By.XPATH, option_xpath)))
                option_element.click()
            except (NoSuchElementException, TimeoutException):
                # If not found, clear the search and try again with the next option
                search_input.clear()
                continue
            finally:
                # Clear the search input after trying to select an option
                search_input.clear()

    except (NoSuchElementException, TimeoutException) as e:
        print(f"Error interacting with the dropdown: {e}")
        # Handle the error as needed, e.g., re-raise or log

if __name__ == '__main__':
    # This block is for testing purposes and would not be part of the final delivered code.
    # You would typically initialize your driver and call the run function.
    # from selenium import webdriver
    # driver = webdriver.Chrome()
    # driver.get("your_application_url")
    # run(driver)
    # driver.quit()
    pass