
import uiautomation as auto
import time
import re
import google.generativeai as genai
import config
import json
import io
import sys
from pywinauto import Application


def print_tree(control, depth=0, max_depth=3):
    """Recursive UI tree dumper for debugging."""
    indent = "  " * depth
    print(f"{indent}ControlType: {control.ControlTypeName} | ClassName: {control.ClassName} | "
          f"Name: '{control.Name}' | AutomationId: '{control.AutomationId}'")
    if depth < max_depth:
        try:
            for child in control.GetChildren():
                print_tree(child, depth + 1, max_depth)
        except Exception as e:
            print(f"{indent}  (Error getting children: {e})")


def _get_descendants(control, depth=0, max_depth=3):
    """Generator that yields all descendants up to max_depth."""
    if depth > max_depth:
        return
    try:
        for child in control.GetChildren():
            yield child
            yield from _get_descendants(child, depth + 1, max_depth)
    except Exception:
        pass


def _normalize_name(name):
    """Remove common special characters and extra spaces for comparison."""
    if not name:
        return ""
    return re.sub(r"[:;,]", "", name).strip().lower()


def _is_visible(elem):
    """Safe bounding rectangle check to filter out invisible or tiny controls."""
    try:
        rect = elem.BoundingRectangle
        rect = rect() if callable(rect) else rect
        if not rect or getattr(rect, "width", 0) < 2 or getattr(rect, "height", 0) < 2:
            return False
        return True
    except Exception:
        return False


def safe_json_loads(res_txt):
    try:
        # Remove surrounding single quotes if present
        txt = res_txt.strip()
        if txt.startswith("'") and txt.endswith("'"):
            txt = txt[1:-1]

        # Extract only the {...} part if mixed with text
        match = re.search(r"\{.*\}", txt, re.DOTALL)
        if match:
            txt = match.group()

        # Try normal load
        return json.loads(txt)
    except json.JSONDecodeError:
        # Try double-decoding if it was a stringified JSON
        try:
            return json.loads(json.loads(txt))
        except Exception:
            return {"error": "Invalid JSON from Gemini", "raw": res_txt}


def get_ancestors(element, max_ancestors=5):
    """Return a list of ancestor controls."""
    ancestors = []
    current = element
    for _ in range(max_ancestors):
        parent = current.GetParentControl()
        if not parent or parent == current:
            break
        ancestors.append({
            'name': parent.Name,
            'control_type': parent.ControlTypeName,
            'class_name': parent.ClassName,
            'automation_id': parent.AutomationId,
            'framework_id': parent.FrameworkId,
        })
        current = parent
    ancestors.reverse()
    return ancestors


def describe_control(control):
    """Return a dictionary with useful UIA properties."""
    return {
        "title": control.Name,
        "control_type": control.ControlTypeName.replace("Control", ""),
        "class_name": control.ClassName,
        "auto_id": control.AutomationId,
        "framework_id": control.FrameworkId,
        "process_id": control.ProcessId,
        "bounding_rectangle": str(control.BoundingRectangle),
        "ancestors": get_ancestors(control)
    }


def print_control_info(control, level):
    """Nicely print info for a single control."""
    info = describe_control(control)
    print(f"\n🔹 Level {level} Menu Item: '{info['title']}'")
    print("-" * 60)
    for k, v in info.items():
        if k == "ancestors":
            print("  ancestors:")
            for i, anc in enumerate(v):
                print(f"    {i+1}. {anc}")
        else:
            print(f"  {k}: {v}")


def traverse_menu(window, menu_path, debug=False):
    """
    Multi-level menu traversal with correct MenuControl ancestor chain.
    """
    if not menu_path:
        raise ValueError("menu_path must be a list of menu names")

    try:
        window.SetFocus()
        if debug:
            print(f"✅ Focused window: '{window.Name}'")

        current_parent = window
        last_item = None
        menu_controls = []  # Track only MenuControl popups

        for i, menu_name in enumerate(menu_path):
            regex = re.compile(rf"^{menu_name}$", re.IGNORECASE)

            menu_item = auto.MenuItemControl(RegexName=regex, parent=current_parent, searchDepth=5)
            if not menu_item.Exists(maxSearchSeconds=2):
                menu_item = auto.MenuItemControl(RegexName=regex, searchDepth=10)

            if not menu_item.Exists():
                if debug:
                    print(f"Menu item '{menu_name}' not found at level {i+1}.")
                current_parent = auto.MenuControl(searchDepth=1)
                continue

            if debug:
                print_control_info(menu_item, i + 1)

            # Click only intermediate menu items
            if i < len(menu_path) - 1:
                try:
                    menu_item.Click()
                    time.sleep(0.4)
                    if debug:
                        print(f"Clicked '{menu_item.Name}' successfully.")
                    
                    # Capture the opened MenuControl popup
                    popup_menu = auto.MenuControl(searchDepth=2)
                    if popup_menu.Exists(maxSearchSeconds=1):
                        menu_controls.append({
                            'name': popup_menu.Name,
                            'control_type': popup_menu.ControlTypeName,
                            'class_name': popup_menu.ClassName,
                            'automation_id': popup_menu.AutomationId,
                            'framework_id': popup_menu.FrameworkId,
                        })
                        if debug:
                            print(f"   📦 Captured MenuControl: '{popup_menu.Name}' class='{popup_menu.ClassName}'")
                    
                except Exception as e:
                    if debug:
                        print(f"Error: {e}")

            current_parent = auto.MenuControl(searchDepth=1)
            last_item = menu_item

        if last_item:
            # Get window ancestors
            all_ancestors = get_ancestors(last_item, max_ancestors=10)
            window_ancestors = []
            for anc in all_ancestors:
                if 'Menu' in anc.get('control_type', ''):
                    break
                window_ancestors.append(anc)
            
            # Combine
            combined_ancestors = window_ancestors + menu_controls
            
            result = describe_control(last_item)
            result['ancestors'] = combined_ancestors
            
            return result
        
        return {"error": "No menu item found"}

    except Exception as e:
        if debug:
            print(f"\nFailed: {e}")
        return {"error": str(e)}
    

def find_element_from_dump(window, description, window_dump, debug=False):
    """
    Use Gemini to find a single element from window dump.
    Returns element attributes dictionary.
    """
    genai.configure(api_key=config.API_KEY)
    model = genai.GenerativeModel(model_name="gemini-2.5-flash-lite")
    chat = model.start_chat()

    prompt = f"""
Here is the element description: {description}

Here are the window's visible UI elements:
{window_dump}

Find the correct element and return only JSON in this format:
{{"title": "xxx", "auto_id": "xxx", "control_type": "xxx", "class_name": "xxx"}}

Rules(strict):
- Match element name exactly (case-insensitive). 'Quickconnect' ≠ 'Connect'.
- 'title' field must be the **actual Name** of the matched element from the window dump, not the description.
- Use only visible elements.
- No guessing. Only return if a clear match exists.
- Return valid JSON only, no extra text.
"""
    
    response = chat.send_message(prompt)
    res_txt = response.text.strip().replace("```json", "").replace("```", "")
    res = safe_json_loads(res_txt)

    if "error" in res:
        return res

    # Final cleanup
    if res.get("control_type", "").endswith("Control"):
        res["control_type"] = res["control_type"].replace("Control", "")

    if debug:
        print(f"\n✅ Matched Element for '{description}':")
        for k, v in res.items():
            print(f"  {k}: {v}")

    return res


def main(description, dlg, expected_title_pattern, expected_pid=None, debug=False):
    """
    Main logic with conditional path:
    - If description is a list with length 1: Use direct window dump search
    - If description is a list with length > 1: Use menu traversal
    - If description is a string: Convert to list and use direct search
    
    Args:
        description: Either a string or a list of strings representing the path to the element
        dlg: pywinauto dialog object
        expected_title_pattern: Regex pattern for window title matching
        expected_pid: Process ID (optional)
        debug: Enable debug output
    
    Returns:
        Dictionary with element attributes
    """
    try:
        # Normalize description to list
        if isinstance(description, str):
            path = [description]
        elif isinstance(description, list):
            path = description
        else:
            return {"error": "description must be a string or list"}

        if not path:
            return {"error": "description cannot be empty"}

        pywinauto_hwnd = dlg.handle
        pywinauto_title = dlg.window_text()
        pywinauto_pid = dlg.process_id() if expected_pid is None else expected_pid

        if debug:
            print(f"=== Pywinauto Details ===")
            print(f"HWND: {pywinauto_hwnd}, PID: {pywinauto_pid}, Title: '{pywinauto_title}'")

        # --- Attach UIA window ---
        window = auto.WindowControl(hwnd=pywinauto_hwnd)
        time.sleep(0.5)  # stabilize UI

        if not window.Exists():
            raise Exception("UIA window not found or inaccessible.")

        # --- Fallback for PID mismatch ---
        if window.ProcessId != pywinauto_pid:
            if debug:
                print("PID mismatch — fallback to PID/title search...")
            root = auto.GetRootControl()
            candidates = [w for w in root.GetChildren()
                          if w.ProcessId == pywinauto_pid and
                          re.search(expected_title_pattern, w.Name or "", re.IGNORECASE)]
            if not candidates:
                raise Exception("No matching window found after fallback.")
            window = candidates[0]

        if debug:
            print(f"=== UIA Connected === Title: '{window.Name}', PID: {window.ProcessId}")
        window.SetFocus()
        time.sleep(0.2)

        # ===== CONDITIONAL LOGIC =====
        if len(path) == 1:
            # Single element - use direct window dump search
            if debug:
                print(f"\n🔍 Single element path detected: '{path[0]}'")
                print("📋 Using direct window dump search...")

            # Dump window tree for Gemini
            buffer = io.StringIO()
            sys_stdout = sys.stdout
            sys.stdout = buffer
            try:
                print_tree(window, max_depth=3)
            finally:
                sys.stdout = sys_stdout
            window_dump = buffer.getvalue()

            result = find_element_from_dump(window, path[0], window_dump, debug)
            return result

        else:
            # Multi-level path - use menu traversal
            if debug:
                print(f"\n🔍 Multi-level path detected: {path}")
                print("Using menu traversal...")

            result = traverse_menu(window, path, debug=debug)
            return result

    except Exception as e:
        return {"error": str(e)}
