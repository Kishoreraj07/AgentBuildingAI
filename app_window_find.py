from pywinauto import Application
import os

def open_app(app_path):
    app_path = os.path.normpath(app_path)
    try:
        app = Application(backend='uia4').start(app_path)
    except:
        app = Application(backend='uia').start(app_path)
    try:
        # Wait and connect to the Calculator window, retry a few times
        calc_window = app.window()
        calc_window.wait('exists enabled visible ready', timeout=30)

        return "No_Issue",calc_window.window_text()
    except Exception as e:
        print("Error:", e)
        return "Issue Occured","No Window Found"