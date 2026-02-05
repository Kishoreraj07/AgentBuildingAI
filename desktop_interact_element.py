import time
from pywinauto import Desktop
from pywinauto.keyboard import send_keys

def reset_menu_state(app_window=None):
    """
    Close any open menus or dropdowns before navigation.
    """
    try:
        # Press ESC twice to close transient/persistent menus
        send_keys("{ESC}")
        time.sleep(0.2)
        send_keys("{ESC}")
        time.sleep(0.2)

        # # Click on a safe area of the app window to reset focus
        # if app_window:
        #     try:
        #         rect = app_window.rectangle()
        #         safe_x = rect.left + 20
        #         safe_y = rect.top + 10
        #         app_window.click_input(coords=(safe_x, safe_y))
        #         time.sleep(0.2)
        #     except Exception:
        #         pass

    except Exception as e:
        print(f"Failed to reset menu state: {e}")

def interact_with_element(dlg, element_attr, text=None, extract_text=False):
    """
    Interact with a desktop element:
    1. Try attribute-based interaction.
    2. If fails, navigate through ancestor hierarchy to reveal submenus.
    3. If still fails, fallback to coordinate click.
    4. Optionally extract element text.
    """
    allowed_keys = {"title", "control_type", "class_name"}
    search_attr = {k: v for k, v in element_attr.items() if k in allowed_keys and v}

    def navigate_through_ancestors(element_attr):
        """Navigate through ancestor hierarchy and click the target element (handles popup menus)."""
        ancestors = element_attr.get('ancestors', [])
        if not ancestors or len(ancestors) < 2:
            print("No ancestors to navigate through")
            return None

        try:
            desktop = Desktop(backend="uia")
            app_ancestor = ancestors[1]  # Usually the main app window
            app_name = app_ancestor.get('name', '')
            class_name = app_ancestor.get('class_name', '')

            print(f"🔍 Looking for application: {app_name or class_name}")

            # Try to locate main application window
            app_window = None
            try:
                if app_name:
                    app_window = desktop.window(title=app_name)
                if not app_window and class_name:
                    app_window = desktop.window(class_name=class_name)
            except Exception:
                pass

            if not app_window:
                print(f"Could not find application window: {app_name or class_name}")
                return None

            print(f"Found application: {app_name or class_name}")

            # Focus and activate the application window
            try:
                app_window.set_focus()
                app_window.set_focus()  # Double call for reliability
                app_window.set_keyboard_focus()
                app_window.restore()  # Restore if minimized
                app_window.set_focus()
                print("Application window focused successfully.")
            except Exception as e:
                print(f"Could not focus application window: {e}")

            time.sleep(1)
            current_element = app_window
            last_popup = None

            # Start from index 2 (skip Desktop and app window)
            for i in range(2, len(ancestors)):
                ancestor = ancestors[i]
                ancestor_name = ancestor.get('name', '')
                ancestor_type = ancestor.get('control_type', '')
                print(f"Navigating to: {ancestor_name or '[Unnamed ancestor]'}")

                try:
                    # Try to find ancestor element
                    if ancestor_name:
                        possible_elem = current_element.child_window(title=ancestor_name)
                    else:
                        possible_elem = current_element.child_window(control_type=ancestor_type)

                    if possible_elem.exists():
                        print(f"Found ancestor: {ancestor_name or ancestor_type}")
                        possible_elem.click_input()
                        time.sleep(0.6)

                        # Wait for a NEW popup to appear
                        for _ in range(10):  # retry up to 10 times
                            popups = [w for w in desktop.windows(class_name="#32768") if w.is_visible()]
                            if last_popup:
                                popups = [p for p in popups if p.handle != last_popup.handle]
                            if popups:
                                last_popup = popups[-1]
                                current_element = last_popup
                                print(f"Switched to popup: {current_element.window_text() or '[Unnamed popup]'}")
                                break
                            time.sleep(0.1)
                    else:
                        print(f"Ancestor not found: {ancestor_name or ancestor_type}")
                except Exception as e:
                    print(f"Error navigating to ancestor {ancestor_name}: {e}")
                    continue

            # After navigating all ancestors, try to find and click the target menu item
            target_title = element_attr.get("title", "")
            target_type = element_attr.get("control_type", "")
            print(f"Searching for target element: {target_title or target_type}")

            try:
                time.sleep(0.8)
                target_elem = current_element.child_window(title=target_title, control_type=target_type)
                if target_elem.exists():
                    target_elem.click_input()
                    print(f"Clicked target element: {target_title}")
                    return target_elem
                else:
                    print(f"Target element not found inside popup: {target_title}")
                    # Optional debug: list available items
                    children = current_element.children()
                    print("Popup contains:")
                    for idx, c in enumerate(children):
                        print(f"  [{idx}] {c.window_text()} - {c.element_info.control_type}")
            except Exception as e:
                print(f"Error clicking target element: {e}")

            return current_element

        except Exception as e:
            print(f"Error navigating ancestors: {e}")
            return None

    # --- Direct search in dlg ---
    try:
        elem = dlg.child_window(**search_attr).wrapper_object()
        print(f"Found element directly in main window: {search_attr}")
    except Exception:
        elem = None
        print(f"Direct search failed for {search_attr}, trying ancestor navigation...")

    # --- Try navigating through ancestors ---
    if not elem and "ancestors" in element_attr:
        nav_parent = navigate_through_ancestors(element_attr)
        if nav_parent:
            try:
                # elem = nav_parent.child_window(**search_attr).wrapper_object()
                print(f"Found target after navigating ancestors: {search_attr}")
                return
            except Exception as e:
                print(f"Still couldn’t find target element after navigation: {e}")

    # --- Coordinate fallback ---
    if not elem:
        try:
            rect_str = element_attr.get("bounding_rectangle", "")
            rect_nums = [int(n) for n in rect_str.replace("(", "").replace(")", "")
                         .replace("[", ",").replace("]", "").replace("x", ",").split(",")
                         if n.strip().isdigit()]
            if len(rect_nums) >= 4:
                left, top, right, bottom = rect_nums[:4]
                x = left + (right - left) // 2
                y = top + (bottom - top) // 2
                dlg.click_input(coords=(x, y))
                print(f"Fallback: clicked at ({x}, {y})")
                if text:
                    dlg.type_keys(text, with_spaces=True, set_foreground=True)
                if extract_text:
                    return None
                return
            else:
                raise RuntimeError("Invalid bounding_rectangle format.")
        except Exception as e:
            raise RuntimeError(f"Fallback click failed: {e}")

    # --- Final interaction ---
    if elem:
        try:
            dlg.set_focus()
            time.sleep(0.6)
            elem.set_focus()
            elem.click_input()
            if text:
                elem.type_keys(text, with_spaces=True, set_foreground=True)
            if extract_text:
                return elem.window_text()
        except Exception as e:
            raise RuntimeError(f"Element interaction failed: {e}")
