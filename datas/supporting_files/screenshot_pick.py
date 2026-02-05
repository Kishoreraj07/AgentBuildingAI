import pyautogui
import os

def take_screenshot(image_path):
    # Create folder if not exists
    folder = os.path.dirname(image_path)
    if folder and not os.path.exists(folder):
        os.makedirs(folder)

    screenshot = pyautogui.screenshot()
    screenshot.save(image_path)
    return image_path


# Example usage
# take_screenshot(r"C:\Users\Administrator\Desktop\screenshot.png")
