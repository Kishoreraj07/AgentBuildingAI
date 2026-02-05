import time
import pyperclip
from selenium import webdriver

def element_picker_original(driver):
    # Inject JavaScript: add mask overlay, highlight elements on hover, capture XPath on click
    driver.execute_script("""
        // === Create mask overlay ===
        const mask = document.createElement('div');
        mask.id = 'element-picker-mask';
        mask.style.cssText = `
            position: fixed;
            top: 0;
            left: 0;
            width: 100vw;
            height: 100vh;
            background-color: rgba(0, 0, 0, 0.5);
            z-index: 999999;
            cursor: crosshair;
            pointer-events: auto;
        `;
        document.body.appendChild(mask);

        // === Add hover style to highlight elements ===
        const style = document.createElement('style');
        style.id = 'element-picker-style';
        style.innerHTML = `
            .element-picker-highlight {
                outline: 3px solid #ff0000 !important;
                outline-offset: 2px !important;
                background-color: rgba(255, 0, 0, 0.1) !important;
                position: relative !important;
                z-index: 1000000 !important;
            }
            #element-picker-mask {
                pointer-events: none !important;
            }
        `;
        document.head.appendChild(style);

        // === XPath generator function ===
        function getXPath(element) {
            if (element.id !== '' && element.id !== 'element-picker-mask')
                return 'id("' + element.id + '")';
            if (element === document.body)
                return element.tagName.toLowerCase();
            
            let ix = 0;
            const siblings = element.parentNode.childNodes;
            for (let i = 0; i < siblings.length; i++) {
                const sibling = siblings[i];
                if (sibling === element)
                    return getXPath(element.parentNode) + '/' + element.tagName.toLowerCase() + '[' + (ix + 1) + ']';
                if (sibling.nodeType === 1 && sibling.tagName === element.tagName)
                    ix++;
            }
        }

        // === Variables to track state ===
        let currentHighlighted = null;
        let isPickerActive = true;

        // === Mouse move handler for highlighting ===
        function mouseMoveHandler(event) {
            if (!isPickerActive) return;
            
            // Temporarily disable mask to get element underneath
            mask.style.pointerEvents = 'none';
            const elementBelow = document.elementFromPoint(event.clientX, event.clientY);
            mask.style.pointerEvents = 'auto';
            
            if (elementBelow && elementBelow !== mask && elementBelow !== currentHighlighted) {
                // Remove previous highlight
                if (currentHighlighted) {
                    currentHighlighted.classList.remove('element-picker-highlight');
                }
                
                // Add highlight to new element
                if (elementBelow.id !== 'element-picker-mask') {
                    elementBelow.classList.add('element-picker-highlight');
                    currentHighlighted = elementBelow;
                }
            }
        }

        // === Click handler ===
        function clickHandler(event) {
            if (!isPickerActive) return;
            
            event.preventDefault();
            event.stopPropagation();
            
            // Get the element underneath the mask
            mask.style.pointerEvents = 'none';
            const targetElement = document.elementFromPoint(event.clientX, event.clientY);
            
            if (targetElement && targetElement.id !== 'element-picker-mask') {
                const xpath = getXPath(targetElement);
                console.log("Clicked XPath:", xpath);
                window.clickedXPath = xpath;
                
                // Cleanup and deactivate picker
                isPickerActive = false;
                cleanup();
            }
        }

        // === Cleanup function ===
        function cleanup() {
            // Remove highlight from current element
            if (currentHighlighted) {
                currentHighlighted.classList.remove('element-picker-highlight');
            }
            
            // Remove event listeners
            document.removeEventListener("mousemove", mouseMoveHandler, true);
            document.removeEventListener("click", clickHandler, true);
            
            // Remove mask and style
            const maskElement = document.getElementById('element-picker-mask');
            const styleElement = document.getElementById('element-picker-style');
            
            if (maskElement) maskElement.remove();
            if (styleElement) styleElement.remove();
        }

        // === Add event listeners ===
        document.addEventListener("mousemove", mouseMoveHandler, true);
        document.addEventListener("click", clickHandler, true);
        
        // === ESC key to cancel ===
        function escHandler(event) {
            if (event.key === 'Escape') {
                console.log("Element picker cancelled");
                window.clickedXPath = 'CANCELLED';
                cleanup();
                document.removeEventListener("keydown", escHandler, true);
            }
        }
        document.addEventListener("keydown", escHandler, true);
    """)

    print("🎯 Element Picker Activated!")
    print("🖱️  Move mouse to highlight elements")
    print("🖱️  Click on any element to select it")
    print("⌨️  Press ESC to cancel")
    print("⌛ Waiting up to 30 seconds...")

    # Poll for XPath after click
    clicked_xpath = None
    for _ in range(30):
        time.sleep(1)
        clicked_xpath = driver.execute_script("return window.clickedXPath || null;")
        if clicked_xpath:
            time.sleep(5)
            break

    # Clean up any remaining elements (safety net)
    driver.execute_script("""
        const mask = document.getElementById('element-picker-mask');
        const style = document.getElementById('element-picker-style');
        if (mask) mask.remove();
        if (style) style.remove();
        
        // Remove any remaining highlights
        document.querySelectorAll('.element-picker-highlight').forEach(el => {
            el.classList.remove('element-picker-highlight');
        });
    """)

    if clicked_xpath:
        if clicked_xpath == 'CANCELLED':
            return None
        else:
            pyperclip.copy(clicked_xpath)
            print(f"\n✅ XPath copied to clipboard:\n{clicked_xpath}")
            return clicked_xpath
    else:
        print("\n⏰ Timeout: No element was selected.")
        return None

def element_picker(driver):
    """
    Element picker function that runs in a separate thread
    
    Args:
        driver: Selenium WebDriver instance
    
    Returns:
        str: Selected XPath if element was clicked, None if cancelled or timeout
    """
    import threading
    import time
    
    result_container = {'xpath': None, 'completed': False}
    
    def run_element_picker():
        try:
            result_container['xpath'] = element_picker_original(driver)
            result_container['completed'] = True
        except Exception as e:
            print(f"❌ Error in element_picker thread: {e}")
            result_container['xpath'] = None
            result_container['completed'] = True
    
    # Start element picker in separate thread
    picker_thread = threading.Thread(target=run_element_picker, daemon=True)
    picker_thread.start()
    
    # Wait for thread completion with timeout
    timeout = 60  # 60 second timeout
    start_time = time.time()
    
    while not result_container['completed'] and (time.time() - start_time) < timeout:
        time.sleep(0.1)  # Small delay to prevent busy waiting
    
    if not result_container['completed']:
        print("⚠️ element_picker timed out after 60 seconds")
        return None
    
    print(f"✅ element_picker completed with result: {result_container['xpath']}")
    return result_container['xpath']