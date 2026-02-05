import sys
import time
from PyQt5.QtWidgets import (
    QApplication, QDialog, QWidget, QLabel, QPushButton, QVBoxLayout, QHBoxLayout
)
from PyQt5.QtCore import Qt, QTimer, QEventLoop, QThread, QRect
from PyQt5.QtGui import QPainter, QColor, QPen
import pywinauto
from pywinauto import Desktop
from pywinauto.keyboard import send_keys
from pywinauto import Application
import traceback # Added for better debugging

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

        # Optional: Click on a safe area to ensure focus is back on the main app
        if app_window:
             try:
                 rect = app_window.rectangle()
                 # Click near the title bar, assuming it's a safe spot
                 safe_x = rect.left + 50
                 safe_y = rect.top + 10
                 app_window.click_input(coords=(safe_x, safe_y))
                 time.sleep(0.2)
             except Exception:
                 pass

    except Exception as e:
        print(f"Failed to reset menu state: {e}")


class DesktopElementConfirmationDialog(QDialog):
    """Standalone element confirmation dialog with safe blinking."""

    def __init__(self, element, element_name="Unknown Element", parent=None):
        super().__init__(parent)
        self.element = element
        self.element_name = element_name
        self.result = False
        self.blink_state = False
        self.blinking_timer = None
        self._mouse_pressed = False
        self._mouse_pos = None

        self.setupUI()
        # NOTE: Original code here calls start_element_blinking, 
        # but since 'element' is a pywinauto element wrapper, we need 
        # to ensure it can still highlight itself using draw_outline
        try:
             self.start_element_blinking_pywinauto()
        except Exception as e:
             print(f"Could not start pywinauto blinking: {e}")
             self.stop_element_blinking_pywinauto() # ensure cleanup if any partial draw happens

        self.raise_()
        self.activateWindow()

    def setupUI(self):
        # ... (setupUI implementation is unchanged)
        self.setWindowFlags(
            Qt.FramelessWindowHint |
            Qt.WindowStaysOnTopHint |
            Qt.Tool |
            Qt.X11BypassWindowManagerHint
        )
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setFixedSize(620, 249)
        self.move(842, 363)

        container = QWidget(self)
        container.setGeometry(0, 0, 620, 249)
        container.setStyleSheet("background-color: #414141; border-radius: 15px;")
        layout = QVBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 25)
        layout.setSpacing(0)

        # Title bar
        title_container = QWidget()
        title_container.setFixedHeight(60)
        title_container.setStyleSheet("background: #333; border-radius: 20px 20px 0 0;")
        title_layout = QHBoxLayout(title_container)
        title_layout.setContentsMargins(25, 15, 25, 15)

        title_label = QLabel(" Element Confirmation")
        title_label.setStyleSheet("color: white; font-weight: bold; font-size: 16px;")
        title_layout.addWidget(title_label)
        title_layout.addStretch()

        # Close button (X)
        close_btn = QPushButton()
        close_btn.setFixedSize(24, 24)
        close_btn.setStyleSheet("background: transparent; border: none;")
        close_btn.paintEvent = lambda event: self.paint_close_icon(event, close_btn)
        close_btn.clicked.connect(self.on_no_clicked)
        title_layout.addWidget(close_btn)
        layout.addWidget(title_container)
        layout.addSpacing(20)

        # Message
        message_label = QLabel(f"Is this the correct element?\n\nName: {self.element_name}")
        message_label.setStyleSheet("color: white; font-size: 16px; text-align: center;")
        message_label.setAlignment(Qt.AlignCenter)
        message_label.setWordWrap(True)
        layout.addWidget(message_label)

        # Buttons
        button_layout = QHBoxLayout()
        button_layout.setSpacing(15)

        no_btn = QPushButton("No")
        yes_btn = QPushButton("Yes")
        for btn in [no_btn, yes_btn]:
            btn.setFixedSize(80, 45)
            btn.setStyleSheet("""
                QPushButton {
                    background: qlineargradient(x1:0,y1:0,x2:0,y2:1, stop:0 #008AB3, stop:1 #005B7F);
                    color: white; border: none; border-radius: 10px;
                    font-weight: 600; font-size: 14px;
                }
                QPushButton:hover { background: #0099CC; }
                QPushButton:pressed { background: #004455; }
            """)
        no_btn.clicked.connect(self.on_no_clicked)
        yes_btn.clicked.connect(self.on_yes_clicked)
        button_layout.addStretch()
        button_layout.addWidget(no_btn)
        button_layout.addWidget(yes_btn)
        button_layout.addStretch()
        layout.addLayout(button_layout)


    def paint_close_icon(self, event, btn):
        # ... (paint_close_icon implementation is unchanged)
        painter = QPainter(btn)
        painter.setRenderHint(QPainter.Antialiasing)
        pen = QPen(QColor(255, 255, 255), 2)
        painter.setPen(pen)
        margin = 6
        painter.drawLine(margin, margin, 24 - margin, 24 - margin)
        painter.drawLine(24 - margin, margin, margin, 24 - margin)

    def mousePressEvent(self, event):
        # ... (mousePressEvent implementation is unchanged)
        if event.button() == Qt.LeftButton:
            self._mouse_pressed = True
            self._mouse_pos = event.globalPos() - self.pos()
            event.accept()

    def mouseMoveEvent(self, event):
        # ... (mouseMoveEvent implementation is unchanged)
        if self._mouse_pressed and self._mouse_pos:
            self.move(event.globalPos() - self._mouse_pos)
            event.accept()

    def mouseReleaseEvent(self, event):
        # ... (mouseReleaseEvent implementation is unchanged)
        if event.button() == Qt.LeftButton:
            self._mouse_pressed = False
            event.accept()

    def start_element_blinking_pywinauto(self):
        """Start blinking using pywinauto's draw_outline."""
        try:
            self.toggle_element_highlight_pywinauto()
            self.blinking_timer = QTimer(self)
            self.blinking_timer.timeout.connect(self.toggle_element_highlight_pywinauto)
            self.blinking_timer.start(500)

        except Exception as e:
            print(f"Error starting pywinauto blinking: {e}")

    def toggle_element_highlight_pywinauto(self):
        """Toggle outline color between red and blue (pywinauto version)."""
        try:
            color = 0xFF0000 if not self.blink_state else 0x0000FF
            self._safe_draw_outline(color, 3)
            self.blink_state = not self.blink_state
        except Exception as e:
            print(f"Blink toggle error (pywinauto): {e}")

    def stop_element_blinking_pywinauto(self):
        """Stop blinking and clear the outline (pywinauto version)."""
        try:
            if self.blinking_timer:
                self.blinking_timer.stop()
                self.blinking_timer = None
            self._safe_draw_outline(0x000000, 0)  # clear outline
        except Exception as e:
            print(f"Error stopping pywinauto blinking: {e}")

    def _safe_draw_outline(self, color, thickness):
        """Safely call draw_outline with multiple fallbacks (pywinauto version)."""
        try:
            # Most modern pywinauto builds
            self.element.draw_outline(color, thickness)
        except TypeError:
            try:
                # Some older builds require reversed order
                self.element.draw_outline(thickness, color)
            except Exception as e:
                print(f"draw_outline failed: {e}")


    def on_yes_clicked(self):
        self.result = True
        self.cleanup_and_close()

    def on_no_clicked(self):
        self.result = False
        self.cleanup_and_close()

    def cleanup_and_close(self):
        self.stop_element_blinking_pywinauto() # Use the pywinauto version for this class
        self.accept()

    def closeEvent(self, event):
        self.cleanup_and_close()
        event.accept()


class HighlightOverlay(QWidget):
    """Transparent overlay window for highlighting elements."""
    
    # ... (HighlightOverlay implementation is unchanged)
    def __init__(self, rect, parent=None):
        super().__init__(parent)
        self.highlight_rect = rect
        self.blink_color = QColor(255, 0, 0, 150)
        
        self.setWindowFlags(
            Qt.FramelessWindowHint | 
            Qt.WindowStaysOnTopHint | 
            Qt.Tool |
            Qt.WindowTransparentForInput
        )
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setAttribute(Qt.WA_TransparentForMouseEvents)
        
        self.setGeometry(rect.x(), rect.y(), rect.width(), rect.height())
        
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        pen = QPen(self.blink_color, 5)
        painter.setPen(pen)
        painter.setBrush(Qt.NoBrush)
        
        rect = QRect(0, 0, self.width(), self.height())
        painter.drawRect(rect)
        
        fill_color = QColor(self.blink_color)
        fill_color.setAlpha(30)
        painter.fillRect(rect, fill_color)
        
    def set_color(self, color):
        self.blink_color = color
        self.update()


class DesktopElementConfirmationDialog_ancestor(QDialog):
    """Element confirmation dialog with automatic menu navigation."""

    def __init__(self, element_attr, parent=None):
        super().__init__(parent)
        self.element_attr = element_attr
        self.element_name = element_attr.get('title', 'Unknown Element')
        self.result = False
        self.blink_state = False
        self.blinking_timer = None
        self.highlight_overlay = None
        self.opened_elements = []  # Track which elements we opened
        self._mouse_pressed = False
        self._mouse_pos = None

        self.setupUI()
        self.navigate_and_highlight()

        self.raise_()
        self.activateWindow()

    def setupUI(self):
        # ... (setupUI implementation is unchanged)
        self.setWindowFlags(
            Qt.FramelessWindowHint |
            Qt.WindowStaysOnTopHint |
            Qt.Tool
        )
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setFixedSize(620, 300)
        
        screen = QApplication.desktop().screenGeometry()
        self.move((screen.width() - self.width()) // 2, 
                  (screen.height() - self.height()) // 2)

        container = QWidget(self)
        container.setGeometry(0, 0, 620, 300)
        container.setStyleSheet("background-color: #414141; border-radius: 15px;")
        layout = QVBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 25)
        layout.setSpacing(0)

        # Title bar
        title_container = QWidget()
        title_container.setFixedHeight(60)
        title_container.setStyleSheet("background: #333; border-radius: 20px 20px 0 0;")
        title_layout = QHBoxLayout(title_container)
        title_layout.setContentsMargins(25, 15, 25, 15)

        title_label = QLabel("Element Confirmation")
        title_label.setStyleSheet("color: white; font-weight: bold; font-size: 16px;")
        title_layout.addWidget(title_label)
        title_layout.addStretch()

        close_btn = QPushButton()
        close_btn.setFixedSize(24, 24)
        close_btn.setStyleSheet("background: transparent; border: none;")
        close_btn.paintEvent = lambda event: self.paint_close_icon(event, close_btn)
        close_btn.clicked.connect(self.on_no_clicked)
        title_layout.addWidget(close_btn)
        layout.addWidget(title_container)
        layout.addSpacing(20)

        # Message with element details
        details = self.format_element_details()
        message_label = QLabel(f"Is this the correct element?\n\n{details}")
        message_label.setStyleSheet("color: white; font-size: 14px;")
        message_label.setAlignment(Qt.AlignCenter)
        message_label.setWordWrap(True)
        layout.addWidget(message_label)
        layout.addSpacing(20)

        # Buttons
        button_layout = QHBoxLayout()
        button_layout.setSpacing(15)

        no_btn = QPushButton("No")
        yes_btn = QPushButton("Yes")
        for btn in [no_btn, yes_btn]:
            btn.setFixedSize(100, 45)
            btn.setStyleSheet("""
                QPushButton {
                    background: qlineargradient(x1:0,y1:0,x2:0,y2:1, stop:0 #008AB3, stop:1 #005B7F);
                    color: white; border: none; border-radius: 10px;
                    font-weight: 600; font-size: 14px;
                }
                QPushButton:hover { background: #0099CC; }
                QPushButton:pressed { background: #004455; }
            """)
        no_btn.clicked.connect(self.on_no_clicked)
        yes_btn.clicked.connect(self.on_yes_clicked)
        button_layout.addStretch()
        button_layout.addWidget(no_btn)
        button_layout.addWidget(yes_btn)
        button_layout.addStretch()
        layout.addLayout(button_layout)

    def format_element_details(self):
        # ... (format_element_details implementation is unchanged)
        title = self.element_attr.get('title', 'N/A')
        control_type = self.element_attr.get('control_type', 'N/A')
        
        # Show ancestor path
        ancestors = self.element_attr.get('ancestors', [])
        if ancestors and len(ancestors) > 0:
            path = " → ".join([a.get('name', 'Unknown') for a in ancestors[-2:]])  # Last 2 ancestors
            return f"Title: {title}\nType: {control_type}\nPath: {path} → {title}"
        
        return f"Title: {title}\nType: {control_type}"

    def paint_close_icon(self, event, btn):
        # ... (paint_close_icon implementation is unchanged)
        painter = QPainter(btn)
        painter.setRenderHint(QPainter.Antialiasing)
        pen = QPen(QColor(255, 255, 255), 2)
        painter.setPen(pen)
        margin = 6
        painter.drawLine(margin, margin, 24 - margin, 24 - margin)
        painter.drawLine(24 - margin, margin, margin, 24 - margin)

    def mousePressEvent(self, event):
        # ... (mousePressEvent implementation is unchanged)
        if event.button() == Qt.LeftButton:
            self._mouse_pressed = True
            self._mouse_pos = event.globalPos() - self.pos()
            event.accept()

    def mouseMoveEvent(self, event):
        # ... (mouseMoveEvent implementation is unchanged)
        if self._mouse_pressed and self._mouse_pos:
            self.move(event.globalPos() - self._mouse_pos)
            event.accept()

    def mouseReleaseEvent(self, event):
        # ... (mouseReleaseEvent implementation is unchanged)
        if event.button() == Qt.LeftButton:
            self._mouse_pressed = False
            event.accept()

    def find_element_by_attributes(self, parent_element, attrs):
        # ... (find_element_by_attributes implementation is unchanged)
        """Find a child element matching the given attributes."""
        try:
            name = attrs.get('name', '')
            control_type = attrs.get('control_type', '')
            
            # Search for element
            children = parent_element.children()
            
            for child in children:
                try:
                    # Check if properties match
                    if control_type and control_type in str(type(child)):
                        if name and child.window_text() == name:
                            return child
                        elif not name:
                            return child
                except:
                    continue
                    
            # If not found in direct children, try descendants
            try:
                if control_type == 'MenuControl':
                    menu = parent_element.child_window(title=name, control_type="Menu")
                    return menu
            except:
                pass
                
        except Exception as e:
            print(f"Error finding element: {e}")
        
        return None

    def navigate_through_ancestors(self):
        """Navigate through ancestor hierarchy and click the target element (handles popup menus)."""
        ancestors = self.element_attr.get('ancestors', [])
        if not ancestors or len(ancestors) < 2:
            print("No ancestors to navigate through")
            return None

        try:
            desktop = Desktop(backend="uia")
            app_ancestor = ancestors[1]  # Usually the main app window
            app_name = app_ancestor.get('name', '')
            class_name = app_ancestor.get('class_name', '')

            print(f"🔍 Looking for application: {app_name or class_name}")

            # --- Locate main application window ---
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

            # --- Focus the application window ---
            try:
                app_window.set_focus()
                # app_window.set_keyboard_focus()
                print("Application window focused successfully.")
            except Exception as e:
                print(f"Could not focus application window: {e}")

            time.sleep(0.8)
            current_element = app_window
            last_popup = None

            # --- Traverse ancestor chain ---
            for i in range(2, len(ancestors)):
                ancestor = ancestors[i]
                ancestor_name = ancestor.get('name', '')
                ancestor_type = ancestor.get('control_type', '')
                print(f"Navigating to: {ancestor_name or '[Unnamed ancestor]'}")

                try:
                    # Locate ancestor element
                    if ancestor_name:
                        possible_elem = current_element.child_window(title=ancestor_name)
                    else:
                        possible_elem = current_element.child_window(control_type=ancestor_type)

                    if possible_elem.exists():
                        print(f"Found ancestor: {ancestor_name or ancestor_type}")
                        possible_elem.click_input()
                        time.sleep(0.5)

                        # Wait for popup menu (#32768)
                        for _ in range(10):
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

            # # --- Locate and click target element ---
            # target_title = self.element_attr.get("title", "")
            # target_type = self.element_attr.get("control_type", "")
            # print(f"Searching for target element: {target_title or target_type}")

            # try:
            #     time.sleep(0.6)
            #     target_elem = current_element.child_window(title=target_title, control_type=target_type)
            #     if target_elem.exists():
            #         # target_elem.click_input()
            #         print(f"Found target element: {target_title}")
            #         return target_elem
            #     else:
            #         print(f"Target element not found inside popup: {target_title}")
            #         children = current_element.children()
            #         print("Popup contains:")
            #         for idx, c in enumerate(children):
            #             print(f"  [{idx}] {c.window_text()} - {c.element_info.control_type}")
            # except Exception as e:
            #     print(f"Error clicking target element: {e}")

            return current_element

        except Exception as e:
            print(f"Error navigating ancestors: {e}")
            import traceback
            traceback.print_exc()
            return None


    def navigate_and_highlight(self):
        """Navigate through menu hierarchy and highlight target element."""
        try:
            # First, navigate through ancestors to open menus
            print("Starting navigation...")
            last_element = self.navigate_through_ancestors()
            
            # Now highlight the target element using bounding_rectangle
            rect_str = self.element_attr.get('bounding_rectangle')
            if rect_str:
                rect = self.parse_bounding_rect(rect_str)
                if rect:
                    self.start_element_blinking(rect)
            else:
                print("No bounding_rectangle found, skipping highlight")
                
        except Exception as e:
            print(f"Error in navigate_and_highlight: {e}")
            import traceback
            traceback.print_exc()

    def toggle_blink(self):
        """Toggle highlight color (red ↔ blue)."""
        if not self.highlight_overlay:
            return
        color = QColor(255, 0, 0, 180) if not self.blink_state else QColor(0, 128, 255, 180)
        self.highlight_overlay.set_color(color)
        self.blink_state = not self.blink_state


    def parse_bounding_rect(self, rect_str):
        # ... (parse_bounding_rect implementation is unchanged)
        """Parse bounding rectangle string like '(138,171,552,197)[414x26]'"""
        try:
            dims_part = rect_str.split('[')[1].strip(']')
            width, height = map(int, dims_part.split('x'))
            
            coords_part = rect_str.split('[')[0].strip('()')
            x, y, right, bottom = map(int, coords_part.split(','))
            
            rect = QRect(x, y, width, height)
            print(f"Parsed rectangle: x={x}, y={y}, width={width}, height={height}")
            return rect
        except Exception as e:
            print(f"Error parsing bounding_rectangle: {e}")
            return None

    def start_element_blinking(self, rect):
        # ... (start_element_blinking implementation is unchanged)
        """Start blinking the element at the given rectangle."""
        try:
            print(f"Creating highlight overlay at: {rect}")
            
            self.highlight_overlay = HighlightOverlay(rect)
            self.highlight_overlay.show()
            self.highlight_overlay.raise_()

            self.blinking_timer = QTimer(self)
            self.blinking_timer.timeout.connect(self.toggle_element_highlight)
            self.blinking_timer.start(500)

        except Exception as e:
            print(f"Error starting blinking: {e}")

    def toggle_element_highlight(self):
        # ... (toggle_element_highlight implementation is unchanged)
        """Toggle outline color between red and blue."""
        try:
            if self.highlight_overlay:
                if self.blink_state:
                    color = QColor(255, 0, 0, 150)  # Red
                else:
                    color = QColor(0, 0, 255, 150)  # Blue
                
                self.highlight_overlay.set_color(color)
                self.blink_state = not self.blink_state
        except Exception as e:
            print(f"Blink toggle error: {e}")

    def stop_element_blinking(self):
        # ... (stop_element_blinking implementation is unchanged)
        """Stop blinking and remove overlay."""
        try:
            if self.blinking_timer:
                self.blinking_timer.stop()
                self.blinking_timer = None
            
            if self.highlight_overlay:
                self.highlight_overlay.close()
                self.highlight_overlay = None
        except Exception as e:
            print(f"Error stopping blinking: {e}")

    def cleanup_and_close(self):
        """Clean up and close menus that were opened."""
        self.stop_element_blinking()
        
        # Reset the menu state by sending ESC keys
        reset_menu_state()
        
        self.accept()
        
    def on_yes_clicked(self):
        self.result = True
        self.cleanup_and_close()

    def on_no_clicked(self):
        self.result = False
        self.cleanup_and_close()

    def closeEvent(self, event):
        self.cleanup_and_close()
        event.accept()


def desktop_element_status(dlg,element_attr, element_name):
    # ... (desktop_element_status implementation is unchanged)
    """
    Thread-safe confirmation dialog with automatic menu navigation.
    
    Args:
        element_attr (dict): Dictionary containing element attributes including:
            - title: Element title/name
            - control_type: Type of control
            - bounding_rectangle: Position string
            - ancestors: List of parent elements in hierarchy
    
    Returns:
        bool: True if user confirms, False otherwise
    """
    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)

    loop = QEventLoop()
    result = {}

    def show_dialog():
        if 'ancestors' in element_attr and element_attr['ancestors']:
            dialog = DesktopElementConfirmationDialog_ancestor(element_attr)
        else:
            # NOTE: This part assumes 'dlg' can find the element without full ancestor path
            element_wrapper = dlg.child_window(**element_attr)
            dialog = DesktopElementConfirmationDialog(element_wrapper, element_name)
        
        dialog.exec_()
        result["value"] = dialog.result
        loop.quit()

    QTimer.singleShot(0, show_dialog)
    loop.exec_()

    return result.get("value", False)


if __name__ == "__main__":
#     # Test with Compare filesize menu item (FileZilla example)
    element_attr = {
        "title": "Compare filesize",
        "control_type": "MenuItem",
        "class_name": "",
        "auto_id": "33577",
        "framework_id": "",
        "process_id": 22400,
        "bounding_rectangle": "(391,156,726,182)[335x26]",
        "ancestors": [
            {
                "name": "Desktop 1",
                "control_type": "PaneControl",
                "class_name": "#32769",
                "automation_id": "",
                "framework_id": "Win32"
            },
            {
                "name": "FileZilla",
                "control_type": "WindowControl",
                "class_name": "wxWindowNR",
                "automation_id": "",
                "framework_id": "Win32"
            },
            {
                "name": "View",
                "control_type": "MenuControl",
                "class_name": "#32768",
                "automation_id": "",
                "framework_id": "Win32"
            },
            {
                "name": "Directory comparison",
                "control_type": "MenuControl",
                "class_name": "#32768",
                "automation_id": "",
                "framework_id": "Win32"
            }
        ]
    }
    
    # IMPORTANT: Ensure FileZilla is running before running this script, 
    # or change .start() to .connect() if you prefer manual startup.
    # .start() is fine if you're comfortable with it restarting FileZilla every test.
    try:
        app = Application(backend="uia").connect(title_re="FileZilla", timeout=5)
    except pywinauto.findbestmatch.MatchError:
        print("FileZilla not found. Starting it...")
        app = Application(backend="uia").start(r"C:\Program Files\FileZilla FTP Client\filezilla.exe")

    # Get the main window
    dlg = app.window(title_re="FileZilla")
    dlg.maximize()
    dlg.set_focus()
    print("Testing menu navigation and confirmation...")
    # NOTE: The element_attr has two duplicated cleanup_and_close methods in the original code. 
    # I removed the second one and simplified the first one in the final version above.
    confirmed = desktop_element_status(dlg,element_attr,"Compare filesize")
    print(f"User confirmed: {confirmed}")      # Final testing code