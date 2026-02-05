import time
import pywinauto
from pywinauto import Desktop
import win32api
import win32con
import tkinter as tk
from tkinter import Toplevel
import json
import win32process


class ElementSelector:
    def __init__(self, hover_overlay, click_overlay, clicked_attributes_list, target_window_title=None):
        self.hover_overlay = hover_overlay
        self.click_overlay = click_overlay
        self.clicked_attributes_list = clicked_attributes_list
        self.target_window_title = target_window_title
        self.target_handle = None
        self.target_pid = None
        self.click_successful = False

        # Cache for optimization
        self.last_rect = None
        self.last_element_hash = None
        self.overlay_visible = False

        if target_window_title:
            self.target_handle, self.target_pid = self.find_window_by_title(target_window_title)

        # Initialize overlays
        self.hover_canvas = tk.Canvas(hover_overlay, bg="white", highlightthickness=0)
        self.hover_canvas.pack(fill="both", expand=True)
        hover_overlay.attributes('-topmost', True)
        hover_overlay.overrideredirect(True)
        hover_overlay.attributes('-transparentcolor', 'white')
        hover_overlay.withdraw()

        self.click_canvas = tk.Canvas(click_overlay, bg="white", highlightthickness=0)
        self.click_canvas.pack(fill="both", expand=True)
        click_overlay.attributes('-topmost', True)
        click_overlay.overrideredirect(True)
        click_overlay.attributes('-transparentcolor', 'white')
        click_overlay.withdraw()

        self.last_hovered_element_info = None
        self.is_processing_click = False

        if self.target_window_title:
            print(f"Targeting Window: \"{self.target_window_title}\"")
        else:
            print("Targeting: Any application")
        print("Waiting for double-clicks...")

    def find_window_by_title(self, title):
        """Finds a window by its title and returns its handle and process ID."""
        try:
            windows = pywinauto.findwindows.find_windows(title_re=f".*{title}.*", backend="uia")
            if windows:
                handle = windows[0]
                app = pywinauto.Application(backend="uia").connect(handle=handle)
                window = app.window(handle=handle)
                window.set_focus()
                _, pid = win32process.GetWindowThreadProcessId(handle)
                return handle, pid
        except Exception as e:
            print(f"Could not find window with title containing: '{title}'. Error: {e}")
        return None, None

    def draw_rectangle(self, overlay, canvas, rect, color="red", width=5):
        """Draws a highlighted rectangle on an overlay window."""
        try:
            if rect.width() <= 0 or rect.height() <= 0:
                overlay.withdraw()
                return False

            current_rect = (rect.left, rect.top, rect.width(), rect.height())
            if self.last_rect == current_rect and self.overlay_visible:
                return True

            self.last_rect = current_rect
            overlay.geometry(f"{rect.width()}x{rect.height()}+{rect.left}+{rect.top}")
            canvas.delete("highlight")
            canvas.create_rectangle(
                0, 0, rect.width(), rect.height(),
                outline=color, width=width, tags="highlight"
            )
            return True
        except Exception as e:
            print(f"Draw rectangle failed: {e}")
            overlay.withdraw()
            return False

    def find_most_specific_element(self, element):
        """Find the most specific/smallest element at the cursor position."""
        try:
            children = element.children()
            cursor_pos = win32api.GetCursorPos()
            for child in children:
                try:
                    child_rect = child.rectangle()
                    if (child_rect.left <= cursor_pos[0] <= child_rect.right and
                        child_rect.top <= cursor_pos[1] <= child_rect.bottom):
                        more_specific = self.find_most_specific_element(child)
                        if more_specific:
                            return more_specific
                        return child
                except:
                    continue
            return element
        except:
            return element

    def hover_highlight(self, pos):
        """Highlights the element under the cursor with optimizations."""
        if self.is_processing_click or self.click_successful:
            if self.overlay_visible:
                self.hover_overlay.withdraw()
                self.overlay_visible = False
            self.last_hovered_element_info = None
            return

        try:
            element = Desktop(backend="uia").from_point(*pos)
            is_internal_window = element and element.handle in [
                self.hover_overlay.winfo_id(), self.click_overlay.winfo_id()
            ]
            target_app_match = (
                element and
                (not self.target_pid or element.element_info.process_id == self.target_pid)
            )

            if element and not is_internal_window and target_app_match:
                specific_element = self.find_most_specific_element(element)
                if specific_element:
                    element = specific_element

                element_hash = (
                    element.handle,
                    element.element_info.control_id,
                    element.element_info.name,
                    element.element_info.class_name,
                    str(element.rectangle())
                )

                if self.last_element_hash != element_hash:
                    rect = element.rectangle()
                    self.last_hovered_element_info = (element, rect, element.element_info.process_id)
                    self.last_element_hash = element_hash

                    if self.draw_rectangle(self.hover_overlay, self.hover_canvas, rect, color="red", width=5):
                        if not self.overlay_visible:
                            self.hover_overlay.deiconify()
                            self.overlay_visible = True
                elif not self.overlay_visible and self.last_rect:
                    self.hover_overlay.deiconify()
                    self.overlay_visible = True
            else:
                if self.overlay_visible:
                    self.hover_overlay.withdraw()
                    self.overlay_visible = False
                self.last_hovered_element_info = None
                self.last_element_hash = None
                self.last_rect = None
        except:
            if self.overlay_visible:
                self.hover_overlay.withdraw()
                self.overlay_visible = False
            self.last_hovered_element_info = None
            self.last_element_hash = None
            self.last_rect = None

    def click_extract(self, pos):
        """Extracts and returns the essential attributes of the clicked element, including ancestors."""
        self.is_processing_click = True
        if self.overlay_visible:
            self.hover_overlay.withdraw()
            self.overlay_visible = False
        self.click_overlay.withdraw()
        time.sleep(0.05)

        try:
            element = Desktop(backend="uia").from_point(*pos)

            is_internal_window = element and element.handle in [
                self.hover_overlay.winfo_id(), self.click_overlay.winfo_id()
            ]
            target_app_match = (
                element and
                (not self.target_pid or element.element_info.process_id == self.target_pid)
            )

            if element and not is_internal_window and target_app_match:
                specific_element = self.find_most_specific_element(element)
                if specific_element:
                    element = specific_element

                rect = element.rectangle()

                # Highlight clicked region
                self.click_canvas.delete("all")
                self.click_canvas.create_rectangle(
                    2, 2, rect.width()-2, rect.height()-2,
                    outline="lime", width=2, tags="highlight"
                )
                self.click_canvas.create_rectangle(
                    1, 1, rect.width()-1, rect.height()-1,
                    outline="red", width=6, tags="highlight"
                )

                self.click_overlay.geometry(f"{rect.width()}x{rect.height()}+{rect.left}+{rect.top}")
                self.click_overlay.attributes('-topmost', True)
                self.click_overlay.deiconify()
                self.click_overlay.lift()

                info = element.element_info

                # --- NEW: Extract ancestor hierarchy ---
                ancestors = []
                try:
                    ancestor = element.parent()
                    while ancestor:
                        ancestors.append({
                            "name": str(getattr(ancestor.element_info, "name", "")),
                            "control_type": str(getattr(ancestor.element_info, "control_type", "")),
                            "class_name": str(getattr(ancestor.element_info, "class_name", "")),
                            "auto_id": str(getattr(ancestor.element_info, "automation_id", "")),
                        })
                        ancestor = ancestor.parent()
                except Exception:
                    pass

                attrs = {
                    "name": str(getattr(info, "name", "")),
                    "control_type": str(getattr(info, "control_type", "")),
                    "class_name": str(getattr(info, "class_name", "")),
                    "auto_id": str(getattr(info, "automation_id", "")),
                    "rectangle": {
                        "left": rect.left,
                        "top": rect.top,
                        "right": rect.right,
                        "bottom": rect.bottom,
                        "width": rect.width(),
                        "height": rect.height()
                    },
                    "click_point": {
                        "x": rect.left + rect.width() // 2,
                        "y": rect.top + rect.height() // 2
                    },
                    "ancestors": ancestors[::-1]  # Reverse so topmost parent comes first
                }

                try:
                    attrs["value"] = element.get_value()
                except Exception:
                    attrs["value"] = None

                json_string = json.dumps(attrs, indent=2)
                self.clicked_attributes_list.append(json_string)
                self.click_successful = True
                self.click_overlay.after(2000, self.click_overlay.withdraw)
            else:
                self.click_overlay.withdraw()
        except Exception as e:
            print(f"Error during click extraction: {e}")
        finally:
            self.is_processing_click = False

def mouse_event_loop(selector_instance, root_window):
    """
    Mouse event loop: trigger element extraction only on Ctrl + Left Click.
    Useful for submenus or sensitive UI elements.
    """
    pos = win32api.GetCursorPos()
    selector_instance.hover_highlight(pos)

    # Detect Ctrl + Left Click
    ctrl_pressed = win32api.GetAsyncKeyState(win32con.VK_CONTROL)
    left_click = win32api.GetAsyncKeyState(win32con.VK_LBUTTON) & 0x8000

    if ctrl_pressed and left_click:
        print("Ctrl + Click detected for element extraction.")
        selector_instance.click_extract(pos)

    if not selector_instance.click_successful:
        root_window.after(30, lambda: mouse_event_loop(selector_instance, root_window))
    else:
        root_window.after(30, root_window.destroy)


def main_desktop_element_picker(target_window_title):
    root = tk.Tk()
    root.withdraw()
    hover_overlay = Toplevel(root)
    click_overlay = Toplevel(root)

    clicked_attributes_list = []
    selector = ElementSelector(hover_overlay, click_overlay, clicked_attributes_list, target_window_title)

    def on_close():
        print("Stopping monitoring and exiting...")
        root.destroy()

    root.protocol("WM_DELETE_WINDOW", on_close)
    mouse_event_loop(selector, root)

    root.mainloop()
    if clicked_attributes_list:
        print("clicked_attributes_list : ", clicked_attributes_list[-1])
        return clicked_attributes_list[-1]
    else:
        return json.dumps({"status": "No element clicked."}, indent=2)


# # Example usage:
# application_name = "FileZilla"
# attributes = main_desktop_element_picker(application_name)
# print(attributes)
