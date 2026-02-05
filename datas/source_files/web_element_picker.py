import time
import json
from selenium import webdriver
from selenium.webdriver.common.by import By
import sys

try:
    sys.stdout.reconfigure(encoding='utf-8')
except AttributeError:
    pass

def element_picker(driver, auto_detect_new_windows=True, is_inner=False, iframe_path=None):
    """
    iframe_path: List of iframe IDs representing the path to current iframe
    e.g., ['iframe1', 'iframe2'] means we're inside iframe2 which is inside iframe1
    """
    if iframe_path is None:
        iframe_path = []
    
    if len(driver.window_handles) > 1 and auto_detect_new_windows:
        driver.switch_to.window(driver.window_handles[-1])
        print(f"✓ Switched to: {driver.title}")

    original_window = driver.current_window_handle
    print("✓ Element Picker Initializing...")
    driver.execute_script("window.clickedResult = null; window.focus(); document.body.focus(); window.scrollTo(0,0);")

    script = """
        window.clickedResult = null;
        const isInner = arguments[0] || false;

        function getFullXPath(element) {
            if (!element || element.nodeType !== 1) return '';
            const parts = [];
            let el = element;
            while (el && el.nodeType === 1) {
                let index = 1;
                let sibling = el.previousElementSibling;
                while (sibling) {
                    if (sibling.tagName === el.tagName) index++;
                    sibling = sibling.previousElementSibling;
                }
                parts.unshift(el.tagName.toLowerCase() + '[' + index + ']');
                el = el.parentNode;
            }
            return '/' + parts.join('/');
        }

        const mask = document.createElement('div');
        mask.id = 'element-picker-mask';
        mask.style.cssText = `
            position: fixed;
            top: 0;
            left: 0;
            width: 100vw;
            height: 100vh;
            background-color: rgba(0,0,0,0.5);
            z-index: 999999;
            cursor: pointer;
        `;
        document.body.appendChild(mask);

        let highlightDiv = null;
        let labelDiv = null;
        let exitLabel = null;
        let isActive = true;

        function createExitLabel() {
            exitLabel = document.createElement('div');
            exitLabel.id = 'exit-label-iframe';
            exitLabel.innerHTML = 'Click to exit iframe';
            exitLabel.style.cssText = `
                position: fixed;
                top: 10px;
                left: 50%;
                transform: translateX(-50%);
                background-color: #ff4444;
                color: white;
                padding: 6px 12px;
                font-size: 10px;
                font-weight: bold;
                z-index: 1000002;
                pointer-events: auto;
                border-radius: 5px;
                cursor: pointer;
                box-shadow: 0 2px 5px rgba(0,0,0,0.3);
            `;
            exitLabel.onclick = (e) => {
                e.preventDefault();
                e.stopPropagation();
                window.clickedResult = 'EXIT_IFRAME';
                isActive = false;
                cleanup();
            };
            document.body.appendChild(exitLabel);
        }

        // Create exit button if inside iframe
        if (isInner) {
            createExitLabel();
        }

        function getElementAt(x, y, doc=document) {
            let maskElem = doc.getElementById('element-picker-mask');
            let oldPointer = null;
            if (maskElem) { oldPointer = maskElem.style.pointerEvents; maskElem.style.pointerEvents='none'; }
            let el = doc.elementFromPoint(x, y);
            let iframeEl = null;

            if (el && el.tagName.toUpperCase() === 'IFRAME') {
                iframeEl = el;
            }

            if (maskElem) maskElem.style.pointerEvents = oldPointer || 'auto';
            return {element: el, doc: doc, iframeEl: iframeEl};
        }

        function highlight(el, iframeEl, doc) {
            if (highlightDiv) highlightDiv.remove();
            if (!el || el.id==='element-picker-mask' || (exitLabel && el === exitLabel)) return;

            let rect;
            if (iframeEl && doc!==document) {
                const iframeRect = iframeEl.getBoundingClientRect();
                const innerRect = el.getBoundingClientRect();
                rect = { left: iframeRect.left + innerRect.left, top: iframeRect.top + innerRect.top, width: innerRect.width, height: innerRect.height };
            } else { rect = el.getBoundingClientRect(); }

            if (rect.width>0 && rect.height>0) {
                highlightDiv = document.createElement('div');
                highlightDiv.style.cssText = `
                    position: fixed;
                    left: ${rect.left}px;
                    top: ${rect.top}px;
                    width: ${rect.width}px;
                    height: ${rect.height}px;
                    border: 3px solid red;
                    background-color: rgba(255,0,0,0.1);
                    z-index: 1000000;
                    pointer-events: none;
                `;
                document.body.appendChild(highlightDiv);
            }

            if (iframeEl && doc===document) {
                if (labelDiv) labelDiv.remove();
                labelDiv = document.createElement('div');
                labelDiv.innerHTML = 'Click to enter iframe';
                labelDiv.style.cssText = `
                    position: fixed;
                    left: ${rect.left + 5}px;
                    top: ${rect.top - 20}px;
                    background-color: #ff4444;
                    color: white;
                    padding: 3px 7px;
                    font-size: 10px;
                    z-index: 1000001;
                    pointer-events: none;
                    border-radius: 3px;
                `;
                document.body.appendChild(labelDiv);
            } else if (labelDiv) {
                labelDiv.remove();
                labelDiv = null;
            }
        }

        function cleanup() {
            if (highlightDiv) highlightDiv.remove();
            if (labelDiv) labelDiv.remove();
            if (exitLabel) exitLabel.remove();
            const mask = document.getElementById('element-picker-mask');
            if (mask) mask.remove();
            document.removeEventListener('mousemove', moveHandler, true);
            document.removeEventListener('click', clickHandler, true);
            document.removeEventListener('keydown', escHandler, true);
        }

        function moveHandler(e) {
            if (!isActive) return;
            const pos = getElementAt(e.clientX, e.clientY);
            highlight(pos.element, pos.iframeEl, pos.doc);
        }

        function clickHandler(e) {
            if (!isActive) return;
            
            // Don't prevent default if clicking on exit button
            if (exitLabel && e.target === exitLabel) {
                return;
            }
            
            e.preventDefault(); e.stopPropagation();

            const pos = getElementAt(e.clientX, e.clientY);
            const el = pos.element;
            const iframeEl = pos.iframeEl;
            const doc = pos.doc;

            if (!el || el.id==='element-picker-mask') {
                if (isInner) { window.clickedResult='EXIT_IFRAME'; isActive=false; cleanup(); return; }
                else { return; }
            }

            if (iframeEl && doc===document) {
                // Enter iframe
                window.clickedResult = {iframe_id: iframeEl.id || getFullXPath(iframeEl)};
                isActive = false;
                cleanup();
                return;
            }

            let xpath_id=''; 
            if (el.id) { 
                const escapedId=CSS.escape(el.id); 
                if(doc.querySelectorAll('#'+escapedId).length===1) xpath_id="//*[@id='"+el.id+"']"; 
            }
            const xpath = getFullXPath(el);

            const result = {xpath_id:xpath_id, xpath:xpath};
            window.clickedResult = result;
            isActive=false;
            cleanup();
        }

        function escHandler(e) {
            if(e.key==='Escape'){ window.clickedResult='CANCELLED'; isActive=false; cleanup(); }
        }

        document.addEventListener('mousemove', moveHandler, true);
        document.addEventListener('click', clickHandler, true);
        document.addEventListener('keydown', escHandler, true);
    """

    cleanup_script = """
        const mask = document.getElementById('element-picker-mask');
        const highlightDiv = document.getElementById('element-picker-highlight-div');
        const labelDiv = document.getElementById('element-picker-label-div');
        const exitLabel = document.getElementById('exit-label-iframe');
        if(mask) mask.remove();
        if(highlightDiv) highlightDiv.remove();
        if(labelDiv) labelDiv.remove();
        if(exitLabel) exitLabel.remove();
    """

    result = None
    driver.execute_script(script, is_inner)
    start_time = time.time()

    while time.time()-start_time < 300:
        time.sleep(0.5)
        try:
            clicked_result = driver.execute_script("return window.clickedResult;")
        except:
            # Handle case where window is closed or context is lost
            break
            
        if clicked_result:
            # Handle iframe entry
            if isinstance(clicked_result, dict) and 'iframe_id' in clicked_result and not clicked_result.get('xpath'):
                try:
                    iframe_locator = clicked_result['iframe_id']
                    
                    if iframe_locator.startswith('//') or iframe_locator.startswith('/'):
                        iframe_elem = driver.find_element(By.XPATH, iframe_locator)
                    else:
                        iframe_elem = driver.find_element(By.ID, iframe_locator)
                    
                    driver.switch_to.frame(iframe_elem)
                    print(f"✓ Entered iframe: {iframe_locator}")
                    
                    # Build new iframe path by adding current iframe
                    new_iframe_path = iframe_path + [iframe_locator]
                    print(f"  Current iframe path: {new_iframe_path}")
                    
                    # Call recursively with updated iframe path
                    inner_result = element_picker(driver, auto_detect_new_windows=False, is_inner=True, iframe_path=new_iframe_path)
                    
                    # Always switch back to default content after exiting iframe
                    driver.switch_to.default_content()
                    print("✓ Switched back to main content")
                    
                    if inner_result and isinstance(inner_result, dict):
                        # Result already has the full iframe path from nested call
                        result = inner_result
                        break
                    else:
                        # Exit was clicked, restart element picker on main content
                        print("✓ Restarting element picker on main content...")
                        driver.execute_script("window.clickedResult = null;")
                        time.sleep(0.3)
                        # Recursively call element_picker to continue selection on main page
                        result = element_picker(driver, auto_detect_new_windows=False, is_inner=False, iframe_path=None)
                        break
                except Exception as e:
                    print(f"Error entering iframe: {e}")
                    try:
                        driver.switch_to.default_content()
                    except:
                        pass
                    result = None
                    break
            elif clicked_result == 'EXIT_IFRAME':
                print("✓ Exited iframe - continuing selection on main content")
                result = None
                break
            elif clicked_result == 'CANCELLED':
                print("✓ Selection cancelled")
                result = None
                break
            else:
                # Regular element selected
                if isinstance(clicked_result, dict):
                    # If we're inside an iframe, add the iframe path as a list
                    if is_inner and iframe_path:
                        clicked_result['iframe'] = iframe_path
                    result = clicked_result
                break

    try:
        driver.execute_script(cleanup_script)
    except:
        pass
    
    if result is None:
        result = {'xpath': ''}
        
    if driver.current_window_handle != original_window:
        try: 
            driver.switch_to.window(original_window)
        except: 
            pass

    return result


# Example usage:
# if __name__ == "__main__":
#     driver = webdriver.Chrome()
#     driver.get("https://example.com")
#     time.sleep(3)
#
#     data = element_picker(driver)
#     print("\nFinal Returned Data:", json.dumps(data, indent=2))
#     
#     # Example output for nested iframes:
#     # {
#     #   "xpath_id": "//*[@id='button']",
#     #   "xpath": "/html[1]/body[1]/div[1]/button[1]",
#     #   "iframe": ["iframe-id1", "iframe-id2", "iframe-id3"]
#     # }
#     
#     driver.quit()