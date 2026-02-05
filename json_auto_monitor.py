import os
import time
import threading
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

class JSONFileChangeHandler(FileSystemEventHandler):
    def __init__(self, json_path, refresh_button):
        super().__init__()
        self.json_path = os.path.abspath(json_path)
        self.refresh_button = refresh_button

    def on_modified(self, event):
        """Called when the JSON file is modified"""
        if os.path.abspath(event.src_path) == self.json_path:
            print(f"🔄 Detected change in {os.path.basename(self.json_path)}")
            try:
                # Simulate a button click safely from main thread
                self.refresh_button.click()
                print("✅ Auto-refreshed XPath data via Refresh button.")
            except Exception as e:
                print(f"❌ Failed to trigger refresh: {e}")

def start_json_auto_monitor(app_instance):
    """
    Monitors json_xpath.json or json_attr.json depending on current automation mode.
    Automatically clicks the refresh (save_1) button when file changes.
    """
    try:
        current_mode = getattr(app_instance, 'current_automation_mode', 'web')

        if current_mode == 'desktop':
            json_path = "json_info/json_attr.json"
        elif current_mode == 'citrix':
            json_path="json_info/citrix_data.json"
        else:
            json_path = "json_info/json_xpath.json"

        if not hasattr(app_instance, 'code_tab_refresh_xpath_btn'):
            print("❌ No refresh button found in app instance.")
            return

        if not os.path.exists(json_path):
            print(f"⚠️ File not found: {json_path}. Creating empty file.")
            os.makedirs("json_info", exist_ok=True)
            open(json_path, "w", encoding="utf-8").write("{}")

        handler = JSONFileChangeHandler(json_path, app_instance.code_tab_refresh_xpath_btn)
        observer = Observer()
        observer.schedule(handler, os.path.dirname(json_path), recursive=False)
        observer.start()

        print(f"👀 JSON Auto-monitor started for: {json_path}")

        # Run observer in background thread
        thread = threading.Thread(target=_keep_observer_alive, args=(observer,), daemon=True)
        thread.start()

    except Exception as e:
        print(f"❌ Error starting JSON monitor: {e}")

def _keep_observer_alive(observer):
    """Keep watchdog observer running indefinitely"""
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()
