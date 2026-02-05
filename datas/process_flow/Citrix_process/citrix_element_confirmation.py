import sys
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtSvg import QSvgRenderer
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time,os,io,json
from datetime import datetime

# Setup logging to file
LOG_FILE = "citrix_element_confirmation_log.txt"
def log_action(message):
    """Log action to both console and file"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
    log_msg = f"[{timestamp}] {message}"
    print(log_msg)
    try:
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write(log_msg + "\n")
    except Exception as e:
        print(f"Error writing to log file: {e}")
def resource_path(relative_path):
    """Get absolute path to resource, works for dev and for PyInstaller"""
    if hasattr(sys, "_MEIPASS"):
        return os.path.join(sys._MEIPASS, relative_path)
    return os.path.join(os.path.abspath("."), relative_path)

# Keep a strong reference to a single QApplication to avoid GC-related loss
_APP_SINGLETON = None

# Global reference to the last dialog instance for Ctrl+M hotkey
_LAST_DIALOG_INSTANCE = None

class GlobalHotkeyFilter(QObject):
    """Global event filter to handle Ctrl+M hotkey"""
    def eventFilter(self, obj, event):
        global _LAST_DIALOG_INSTANCE
        if event.type() == QEvent.KeyPress:
            if event.key() == Qt.Key_M and event.modifiers() == Qt.ControlModifier:
                log_action("GlobalHotkeyFilter: Ctrl+M pressed - attempting to show last dialog")
                if _LAST_DIALOG_INSTANCE is not None:
                    try:
                        log_action(f"GlobalHotkeyFilter: Dialog instance exists, showing it")
                        # Ensure dialog is visible and active
                        _LAST_DIALOG_INSTANCE.setVisible(True)
                        _LAST_DIALOG_INSTANCE.show()
                        _LAST_DIALOG_INSTANCE.raise_()
                        _LAST_DIALOG_INSTANCE.activateWindow()
                        _LAST_DIALOG_INSTANCE.setFocus()
                        # Process events to ensure UI updates
                        QApplication.processEvents()
                        log_action("GlobalHotkeyFilter: Last dialog shown via Ctrl+M, events processed")
                        return True  # Consume the event
                    except Exception as e:
                        log_action(f"GlobalHotkeyFilter: Error showing dialog: {e}")
                        import traceback
                        log_action(f"GlobalHotkeyFilter: Traceback: {traceback.format_exc()}")
                else:
                    log_action("GlobalHotkeyFilter: Ctrl+M pressed but no dialog instance available")
        return super().eventFilter(obj, event)


class SnippingTool(QWidget):
    """Snipping tool for capturing screen regions"""
    finished = pyqtSignal()  # emitted when user completes or cancels capture
    
    def __init__(self):
        super().__init__()
        log_action("SnippingTool: Initializing")
        self.start_point = QPoint()
        self.end_point = QPoint()
        self.screenshot = None
        self.captured_region = None
        self.bounds = None  # Store boundary coordinates as [left, right, top, bottom]
        self.is_dragging = False  # Track if user is currently dragging
        self.user_initiated_close = False  # Track if close was user-initiated
        self.timeout_timer = None  # 10-minute safety timeout
        
        # Make window fullscreen and transparent, keep it on top and modal
        self.setWindowFlags(
            Qt.FramelessWindowHint | 
            Qt.WindowStaysOnTopHint |
            Qt.Tool |
            Qt.X11BypassWindowManagerHint
        )
        self.setWindowModality(Qt.ApplicationModal)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setAttribute(Qt.WA_ShowWithoutActivating, False)  # Ensure it can receive focus
        self.setWindowState(Qt.WindowFullScreen)
        
        # Take screenshot of entire screen
        self.take_screenshot()
        log_action("SnippingTool: Screenshot taken")
        
        # Set cursor to crosshair
        self.setCursor(Qt.CrossCursor)
        
        # Start 10-minute timeout timer as safety measure
        self.timeout_timer = QTimer(self)
        self.timeout_timer.setSingleShot(True)
        self.timeout_timer.timeout.connect(self._on_timeout)
        self.timeout_timer.start(10 * 60 * 1000)  # 10 minutes in milliseconds
        log_action("SnippingTool: 10-minute timeout timer started")
        
    def take_screenshot(self):
        """Take screenshot of entire screen"""
        screen = QApplication.primaryScreen()
        self.screenshot = screen.grabWindow(0)
        
    def paintEvent(self, event):
        """Paint the screenshot and selection rectangle"""
        painter = QPainter(self)
        
        # Draw the screenshot
        painter.drawPixmap(0, 0, self.screenshot)
        
        # Draw semi-transparent overlay
        painter.fillRect(self.rect(), QColor(0, 0, 0, 100))
        
        # If we have a selection, draw it
        if not self.start_point.isNull() and not self.end_point.isNull():
            # Clear the selected area (remove overlay)
            selection_rect = QRect(self.start_point, self.end_point).normalized()
            painter.setCompositionMode(QPainter.CompositionMode_Clear)
            painter.fillRect(selection_rect, QColor(0, 0, 0, 0))
            
            # Draw selection border
            painter.setCompositionMode(QPainter.CompositionMode_SourceOver)
            pen = QPen(QColor(255, 0, 0), 2, Qt.SolidLine)
            painter.setPen(pen)
            painter.drawRect(selection_rect)
            
    def mousePressEvent(self, event):
        """Start selection"""
        if event.button() == Qt.LeftButton:
            self.is_dragging = True
            self.start_point = event.pos()
            self.end_point = event.pos()
            self.update()
            # Ensure window stays on top when dragging starts
            self.raise_()
            self.activateWindow()
            
    def mouseMoveEvent(self, event):
        """Update selection"""
        if not self.start_point.isNull():
            self.is_dragging = True
            self.end_point = event.pos()
            self.update()
            # Keep window on top during dragging
            if not self.isActiveWindow():
                self.raise_()
                self.activateWindow()
            
    def mouseReleaseEvent(self, event):
        """Finish selection and capture"""
        if event.button() == Qt.LeftButton and not self.start_point.isNull():
            self.is_dragging = False
            self.end_point = event.pos()
            self.capture_selection()
            # Mark as user-initiated close
            self.user_initiated_close = True
            # Stop timeout timer
            if self.timeout_timer:
                self.timeout_timer.stop()
            self.close()
            self.finished.emit()
            
    def keyPressEvent(self, event):
        """Handle escape key to cancel"""
        if event.key() == Qt.Key_Escape:
            self.is_dragging = False
            self.captured_region = None
            self.bounds = None  # Clear bounds on cancel
            # Mark as user-initiated close
            self.user_initiated_close = True
            # Stop timeout timer
            if self.timeout_timer:
                self.timeout_timer.stop()
            self.close()
            self.finished.emit()
    
    def _on_timeout(self):
        """Handle 10-minute timeout - force close if no user interaction"""
        if not self.user_initiated_close:
            print("Snipping tool timeout after 10 minutes, closing...")
            self.is_dragging = False
            self.captured_region = None
            self.bounds = None
            self.close()
            self.finished.emit()
            
    def capture_selection(self):
        """Capture the selected region and store boundary coordinates"""
        if not self.start_point.isNull() and not self.end_point.isNull():
            selection_rect = QRect(self.start_point, self.end_point).normalized()
            if selection_rect.width() > 0 and selection_rect.height() > 0:
                # Capture the region image
                self.captured_region = self.screenshot.copy(selection_rect)
                
                # Store boundary coordinates as [left, right, top, bottom]
                self.bounds = [
                    selection_rect.left(),      # left boundary
                    selection_rect.right(),     # right boundary
                    selection_rect.top(),       # top boundary
                    selection_rect.bottom()     # bottom boundary
                ]
        # Ensure listeners know we are done (even if no valid selection)
        self.finished.emit()

    def closeEvent(self, event):
        """Prevent accidental closes during dragging, only allow user-initiated or timeout closes"""
        # If user is dragging and close wasn't initiated by user, prevent close
        if self.is_dragging and not self.user_initiated_close:
            print("Preventing close during active drag operation")
            event.ignore()
            # Ensure window stays visible and on top
            self.raise_()
            self.activateWindow()
            return
        
        # Stop timeout timer if closing
        if self.timeout_timer:
            self.timeout_timer.stop()
        
        # Ensure finished signal fires
        try:
            if not self.signalsBlocked():
                self.finished.emit()
        except Exception:
            pass
        event.accept()
    
    def showEvent(self, event):
        """Ensure window stays on top when shown"""
        super().showEvent(event)
        self.raise_()
        self.activateWindow()
        # Force focus to prevent other windows from stealing it
        QApplication.processEvents()
        self.raise_()
        self.activateWindow()
    
    def changeEvent(self, event):
        """Handle window state changes to keep it on top"""
        super().changeEvent(event)
        if event.type() == QEvent.WindowStateChange:
            # If window loses fullscreen or top state, restore it
            if not self.windowState() & Qt.WindowFullScreen:
                self.setWindowState(Qt.WindowFullScreen)
            if not self.isActiveWindow():
                self.raise_()
                self.activateWindow()


class CountdownOverlay(QWidget):
    finished = pyqtSignal()

    def __init__(self, seconds: int, parent=None):
        super().__init__(parent)
        self.seconds_left = max(0, int(seconds))
        self.wave_phase = 0.0

        # Small, round, always-on-top overlay in top-left corner
        self.setWindowFlags(
            Qt.FramelessWindowHint |
            Qt.Tool |
            Qt.WindowStaysOnTopHint |
            Qt.X11BypassWindowManagerHint
        )
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setAttribute(Qt.WA_ShowWithoutActivating)
        self.resize(64, 64)
        self.move(16, 16)

        # Animation timer for wave/pulse effect
        self.anim_timer = QTimer(self)
        self.anim_timer.timeout.connect(self._tick_anim)
        self.anim_timer.start(40)  # ~25 FPS

        # Second countdown timer
        if self.seconds_left > 0:
            self.sec_timer = QTimer(self)
            self.sec_timer.timeout.connect(self._tick_sec)
            self.sec_timer.start(1000)
        else:
            QTimer.singleShot(0, self._finish)

    def _tick_anim(self):
        self.wave_phase += 0.04
        if self.wave_phase > 1.0:
            self.wave_phase -= 1.0
        self.update()

    def _tick_sec(self):
        self.seconds_left -= 1
        if self.seconds_left <= 0:
            self._finish()
        else:
            self.update()

    def _finish(self):
        try:
            if hasattr(self, 'sec_timer') and self.sec_timer.isActive():
                self.sec_timer.stop()
        except Exception:
            pass
        try:
            if self.anim_timer.isActive():
                self.anim_timer.stop()
        except Exception:
            pass
        self.hide()
        self.finished.emit()
        self.deleteLater()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHints(QPainter.Antialiasing | QPainter.TextAntialiasing)
        w, h = self.width(), self.height()
        center = QPointF(w/2, h/2)

        # Background circle
        bg_brush = QBrush(QColor(20, 20, 20, 220))
        painter.setBrush(bg_brush)
        painter.setPen(Qt.NoPen)
        radius = min(w, h)/2 - 2
        painter.drawEllipse(center, radius, radius)

        # Wave ring (expanding and fading)
        wave_r = radius - 2 + 6 * self.wave_phase
        alpha = int(160 * (1.0 - self.wave_phase))
        pen = QPen(QColor(0, 206, 209, alpha))
        pen.setWidth(3)
        painter.setPen(pen)
        painter.setBrush(Qt.NoBrush)
        painter.drawEllipse(center, wave_r, wave_r)

        # Inner border
        pen2 = QPen(QColor(0, 206, 209, 220))
        pen2.setWidth(2)
        painter.setPen(pen2)
        painter.drawEllipse(center, radius-3, radius-3)

        # Countdown text
        painter.setPen(QColor(255, 255, 255))
        font = painter.font()
        font.setBold(True)
        font.setPointSize(14)
        painter.setFont(font)
        text = str(max(0, self.seconds_left))
        painter.drawText(self.rect(), Qt.AlignCenter, text)

    def closeEvent(self, event):
        try:
            if hasattr(self, 'sec_timer') and self.sec_timer.isActive():
                self.sec_timer.stop()
            if self.anim_timer.isActive():
                self.anim_timer.stop()
        except Exception:
            pass
        event.accept()

class PickerWorker(QObject):
    finished = pyqtSignal(str)
    error = pyqtSignal(str)

    def __init__(self, driver):
        super().__init__()
        self.driver = driver

    @pyqtSlot()
    def run(self):
        try:
            from datas.source_files.verify_xpath import element_picker
            picked = element_picker(self.driver)
            if isinstance(picked, str):
                picked = picked.strip()
            self.finished.emit(picked or "")
        except Exception as e:
            self.error.emit(str(e))


class BoundsHighlightOverlay(QWidget):
    """Fullscreen overlay to highlight captured bounds region with blue box"""
    
    def __init__(self, bounds_data):
        super().__init__()
        self.bounds_data = bounds_data  # [left, right, top, bottom]
        
        # Make window fullscreen, frameless, always on top, transparent background
        self.setWindowFlags(
            Qt.FramelessWindowHint | 
            Qt.WindowStaysOnTopHint |
            Qt.Tool |
            Qt.X11BypassWindowManagerHint
        )
        self.setAttribute(Qt.WA_TranslucentBackground)
        
        # Make it fullscreen
        self.setWindowState(Qt.WindowFullScreen)
        
    def paintEvent(self, event):
        """Paint the bounds highlight"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing, True)
        
        left, right, top, bottom = self.bounds_data
        width = right - left
        height = bottom - top
        
        # Draw blue border rectangle around the bounds
        pen = QPen(QColor(0, 120, 212), 4, Qt.SolidLine)  # 4px blue border
        painter.setPen(pen)
        painter.setBrush(Qt.NoBrush)
        painter.drawRect(left, top, width, height)
        
        # Draw semi-transparent blue fill inside
        fill_brush = QBrush(QColor(0, 120, 212, 30))  # 30 alpha for transparency
        painter.setBrush(fill_brush)
        painter.setPen(Qt.NoPen)
        painter.drawRect(left, top, width, height)
        
        # Optional: Draw corner indicators
        corner_size = 15
        corner_pen = QPen(QColor(0, 120, 212), 3, Qt.SolidLine)
        painter.setPen(corner_pen)
        
        # Top-left corner
        painter.drawLine(left, top, left + corner_size, top)
        painter.drawLine(left, top, left, top + corner_size)
        
        # Top-right corner
        painter.drawLine(right, top, right - corner_size, top)
        painter.drawLine(right, top, right, top + corner_size)
        
        # Bottom-left corner
        painter.drawLine(left, bottom, left + corner_size, bottom)
        painter.drawLine(left, bottom, left, bottom - corner_size)
        
        # Bottom-right corner
        painter.drawLine(right, bottom, right - corner_size, bottom)
        painter.drawLine(right, bottom, right, bottom - corner_size)


class MousePointerOverlay(QWidget):
    """Fullscreen overlay to highlight mouse pointer position with royal blue X mark"""
    
    def __init__(self, x, y):
        super().__init__()
        self.x = x  # X coordinate
        self.y = y  # Y coordinate
        
        # Make window fullscreen, frameless, always on top, transparent background
        self.setWindowFlags(
            Qt.FramelessWindowHint | 
            Qt.WindowStaysOnTopHint |
            Qt.Tool |
            Qt.X11BypassWindowManagerHint
        )
        self.setAttribute(Qt.WA_TranslucentBackground)
        
        # Make it fullscreen
        self.setWindowState(Qt.WindowFullScreen)
        
    def paintEvent(self, event):
        """Paint the mouse pointer X mark"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing, True)
        
        # Royal blue color (#4169E1)
        royal_blue = QColor(65, 105, 225)
        
        # X mark size
        mark_size = 7
        
        # Draw royal blue X mark at pointer position
        pen = QPen(royal_blue, 3, Qt.SolidLine)
        painter.setPen(pen)
        
        # Draw X (diagonal lines)
        painter.drawLine(
            self.x - mark_size, self.y - mark_size,
            self.x + mark_size, self.y + mark_size
        )
        painter.drawLine(
            self.x + mark_size, self.y - mark_size,
            self.x - mark_size, self.y + mark_size
        )
        
        # Draw circle around the center point
        circle_radius = 8
        painter.drawEllipse(self.x - circle_radius, self.y - circle_radius, 
                           circle_radius * 2, circle_radius * 2)
        
        # Draw outer circle for emphasis
        # outer_pen = QPen(royal_blue, 2, Qt.DashLine)
        # painter.setPen(outer_pen)
        # outer_radius = 40
        # painter.drawEllipse(self.x - outer_radius, self.y - outer_radius,
        #                    outer_radius * 2, outer_radius * 2)


class ElementConfirmationDialog(QDialog):
    """Standalone element confirmation dialog with xpath highlighting"""
    
    def __init__(self, element_description,app_instance,var_name, parent=None):
        super().__init__(parent)
        log_action(f"ElementConfirmationDialog: Initializing for element '{element_description}'")
        self.element_desc=element_description
        self.app_instance = app_instance
        # self.xpath = xpath
        self.var_name=var_name
        # self.driver = driver
        self.result = False
        self.chosen_xpath = ""  # Initialize chosen_xpath to empty string
        self.bound_index_data=""
        self.coordiante_bound=""
        self.blinking_timer = None
        self.blink_state = False
        
        # Bounds blinking state
        self.bounds_blinking_timer = None
        self.bounds_blink_state = False
        self.current_bounds = None
        
        # Mouse pointer blinking state
        self.pointer_blinking_timer = None
        self.pointer_blink_state = False
        self.current_pointer_coords = None
        self.mouse_pointer_overlay = None
        
        # Track current/pasted xpath and chosen return value
        # self.current_xpath = self.xpath  # used for blinking/highlight
        self.user_xpath = None           # user-entered xpath via dropdown panel
        self.last_picker_xpath = None    # xpath chosen via element_picker()
        # self.chosen_xpath = self.xpath   # final xpath to return on Yes
        # self.main_xpath = self.xpath     # common/main xpath reflecting latest selection or input
        self.element_verify = False 
        self.image_verify=False
        self.region_verify=False
        self.proj_name=None
        self.task_name=None
        self.coordinate_verify = False     # becomes True after at least one successful element_picker
        self._coordinate_picker_running = False  # Track if coordinate picker is active
        self._image_picker_running = False  # Track if image picker is active
        self._region_picker_running = False  # Track if region picker is active
        self._force_close = False
        self._initialization_complete = False  # Flag to prevent hiding during init
        self._user_confirmed = False  # Track if user clicked Yes button
        self._subprocess_mode = False  # Flag to detect subprocess context
        
        # Build UI
        try:
            log_action("ElementConfirmationDialog: setupUI starting")
            self.setupUI()
            log_action("ElementConfirmationDialog: setupUI completed")
        except Exception as e:
            log_action(f"ElementConfirmationDialog: setupUI error: {e}")
            raise
        
        # Load project/task info early
        try:
            with open("json_info/task_info.json", "r", encoding="utf-8") as f:
                json_info = json.load(f)
            self.proj_name=json_info["Proj_file_name"]
            self.task_name=json_info["Task_file_name"]
            log_action(f"ElementConfirmationDialog: Loaded project '{self.proj_name}' and task '{self.task_name}'")
        except Exception as e:
            log_action(f"ElementConfirmationDialog: Error loading task_info.json: {e}")
        
        # Mark initialization as complete BEFORE showing dialog
        self._initialization_complete = True
        log_action("ElementConfirmationDialog: Initialization complete, preparing to show dialog")
        
        # Now show the dialog - this must happen BEFORE exec_() is called
        self.setVisible(True)
        self.show()
        self.raise_()
        self.activateWindow()
        log_action("ElementConfirmationDialog: Dialog shown, raised, and activated")
        
        # Schedule foreground ensure after dialog is shown
        # QTimer.singleShot(100, self._ensure_foreground)
        # QTimer.singleShot(300, self._ensure_foreground)

    # def _ensure_foreground(self):
    #     """Ensure the dialog is visible, on-screen and foreground."""
    #     try:
    #         # Ensure on-screen position (center-bottom of primary screen)
    #         screen_geom = QApplication.primaryScreen().availableGeometry()
    #         w = self.width() or 1020
    #         h = self.height() or 70
    #         x = (screen_geom.width() - w) // 2
    #         y = screen_geom.height() - h - 70
    #         self.move(x, y)

    #         if self.isMinimized():
    #             self.showNormal()
    #         self.setVisible(True)
    #         self.show()
    #         self.raise_()
    #         self.activateWindow()
    #         # Do NOT call processEvents here - it can trigger hide events
    #         # The dialog will be shown via exec_() which has its own event loop
    #         log_action("ElementConfirmationDialog: _ensure_foreground executed")
    #     except Exception as e:
    #         log_action(f"ElementConfirmationDialog: _ensure_foreground error: {e}")
    

    def _restore_visibility(self):
        """Restore dialog visibility after it was hidden unexpectedly"""
        try:
            log_action("ElementConfirmationDialog: _restore_visibility called")
            if not self.isVisible():
                self.setVisible(True)
                self.show()
                self.raise_()
                self.activateWindow()
                log_action("ElementConfirmationDialog: Dialog visibility restored")
        except Exception as e:
            log_action(f"ElementConfirmationDialog: _restore_visibility error: {e}")
        
    def setupUI(self):
        """Setup the confirmation dialog UI"""
        # Make dialog standalone and independent from main application
        self.setWindowFlags(
            Qt.FramelessWindowHint | 
            Qt.WindowStaysOnTopHint
        )
        self.setAttribute(Qt.WA_TranslucentBackground)
        # Do not set ApplicationModal explicitly; exec_() will manage modality safely

        # Horizontal compact size with text and buttons
        self.setFixedSize(1020, 70)
        
        # Position at bottom left corner with some margin
        screen = QApplication.desktop().screenGeometry()
        window_width = self.frameGeometry().width()
        window_height = self.frameGeometry().height()
        x = (screen.width() - window_width) // 2        # center horizontally
        y = screen.height() - window_height - 70        # 20px margin from bottom
        self.move(x, y)
        
        # Add dragging support
        self._mouse_pressed = False
        self._mouse_pos = None

        # Create main container with rounded corners
        self.container = QWidget(self)
        self.container.setGeometry(0, 0, 1020, 70)
        container = self.container
        container.setStyleSheet("""
            QWidget {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                                          stop:0 #2D2D2D, stop:1 #1A1A1A);
                border: 2px solid #00CED1;
                border-radius: 12px;
            }
        """)

        # Use vertical layout: top row (text + buttons), optional input row below
        main_layout = QVBoxLayout(container)
        main_layout.setContentsMargins(15, 12, 15, 12)
        main_layout.setSpacing(8)
        
        top_row = QHBoxLayout()
        top_row.setSpacing(15)
        top_row.setContentsMargins(0, 0, 0, 0)
        
        # Add text label on the left
        element_display_desc=self.element_desc.replace('_', ' ').replace('field', '').strip().title()
        self.text_label = QLabel(f"Confirm <b>{element_display_desc}</b> Field Highlight")
        self.text_label.setTextFormat(Qt.RichText)
        self.text_label.setStyleSheet("""
            QLabel {
                color: #FFFFFF;
                font-family: 'Asen Pro';
                font-size: 24px;
                background: transparent;
                border: none;
            }
        """)
        self.text_label.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        self.text_label.setWordWrap(True)
        top_row.addWidget(self.text_label, 1)  # Stretch factor 1 to take available space
        
        # Button container on the right
        button_layout = QHBoxLayout()
        button_layout.setSpacing(10)
        button_layout.setContentsMargins(0, 0, 0, 0)
        
        # Delay seconds input near X button
        self.delay_edit = QLineEdit()
        self.delay_edit.setValidator(QIntValidator(0, 99, self))
        self.delay_edit.setMaxLength(2)
        self.delay_edit.setFixedSize(36, 24)
        self.delay_edit.setAlignment(Qt.AlignCenter)
        self.delay_edit.setPlaceholderText("s")
        self.delay_edit.setToolTip("Delay before picker (seconds)")
        self.delay_edit.setStyleSheet("""
            QLineEdit {
                color: #FFFFFF;
                background: rgba(255,255,255,0.08);
                border: 1px solid rgba(255,255,255,0.2);
                border-radius: 6px;
                padding: 0px 4px;
                font-size: 11px;
                min-height: 0px;
            }
            QLineEdit:focus { border-color: #00CED1; }
        """)
        
        # No button with close icon
        no_svg_data = b"""
        <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24"
            viewBox="0 0 24 24" fill="none" stroke="#f8f7f7"
            stroke-width="2" stroke-linecap="round" stroke-linejoin="round"
            class="lucide lucide-mouse-pointer-click-icon lucide-mouse-pointer-click">
        <path d="M14 4.1 12 6"/>
        <path d="m5.1 8-2.9-.8"/>
        <path d="m6 12-1.9 2"/>
        <path d="M7.2 2.2 8 5.1"/>
        <path d="M9.037 9.69a.498.498 0 0 1 .653-.653l11 4.5a.5.5 0 0 1-.074.949l-4.349 1.041a1 1 0 0 0-.74.739l-1.04 4.35a.5.5 0 0 1-.95.074z"/>
        </svg>
        """

        # Render SVG into a pixmap
        no_renderer = QSvgRenderer(QByteArray(no_svg_data))
        no_pixmap = QPixmap(32, 32)
        no_pixmap.fill(Qt.transparent)
        painter = QPainter(no_pixmap)
        no_renderer.render(painter)
        painter.end()

        # ✅ Create the QPushButton with rendered icon
        no_btn = QPushButton()
        no_btn.setFixedSize(32, 32)
        no_btn.setIcon(QIcon(no_pixmap))
        no_btn.setIconSize(QSize(24, 24))
        no_btn.setStyleSheet("""
            QPushButton {
                background: transparent;
                border: none;
                border-radius: 10px;
                padding: 5px;
            }
            QPushButton:hover {
                background: rgba(255, 255, 255, 0.1);
            }
            QPushButton:pressed {
                background: rgba(255, 255, 255, 0.2);
            }
        """)
        no_btn.setCursor(Qt.PointingHandCursor)
        no_btn.setToolTip("Element Picker")
        no_btn.clicked.connect(self.on_no_clicked)
        self.no_btn = no_btn
        
        # Coordinate picker button
        coord_svg_data = b"""
        <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24"
            viewBox="0 0 24 24" fill="none" stroke="#f8f7f7"
            stroke-width="2" stroke-linecap="round" stroke-linejoin="round"
            class="lucide lucide-spline-pointer-icon lucide-spline-pointer">
        <path d="M12.034 12.681a.498.498 0 0 1 .647-.647l9 3.5a.5.5 0 0 1-.033.943l-3.444 1.068a1 1 0 0 0-.66.66l-1.067 3.443a.5.5 0 0 1-.943.033z"/>
        <path d="M5 17A12 12 0 0 1 17 5"/>
        <circle cx="19" cy="5" r="2"/>
        <circle cx="5" cy="19" r="2"/>
        </svg>
        """

        # Render SVG into QPixmap
        coord_renderer = QSvgRenderer(QByteArray(coord_svg_data))
        coord_pixmap = QPixmap(32, 32)
        coord_pixmap.fill(Qt.transparent)
        painter = QPainter(coord_pixmap)
        coord_renderer.render(painter)
        painter.end()

        # ✅ Create QPushButton with rendered SVG icon
        coord_btn = QPushButton()
        coord_btn.setFixedSize(32, 32)
        coord_btn.setIcon(QIcon(coord_pixmap))
        coord_btn.setIconSize(QSize(24, 24))
        coord_btn.setStyleSheet("""
            QPushButton {
                background: transparent;
                border: none;
                border-radius: 10px;
                padding: 5px;
            }
            QPushButton:hover {
                background: rgba(255, 255, 255, 0.1);
            }
            QPushButton:pressed {
                background: rgba(255, 255, 255, 0.2);
            }
        """)
        coord_btn.setCursor(Qt.PointingHandCursor)
        coord_btn.setToolTip("Coordinate Picker")
        coord_btn.clicked.connect(self.on_coordinate_clicked)
        self.coord_btn = coord_btn


        # Image picker button
        img_svg_data = b"""
        <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" 
             viewBox="0 0 24 24" fill="none" stroke="#f8f7f7" 
             stroke-width="2" stroke-linecap="round" stroke-linejoin="round" 
             class="lucide lucide-image-play-icon lucide-image-play">
            <path d="M15 15.003a1 1 0 0 1 1.517-.859l4.997 2.997a1 1 0 0 1 0 1.718l-4.997 2.997a1 1 0 0 1-1.517-.86z"/>
            <path d="M21 12.17V5a2 2 0 0 0-2-2H5a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h6"/>
            <path d="m6 21 5-5"/>
            <circle cx="9" cy="9" r="2"/>
        </svg>
        """
        # img_svg_bytes = img_svg_data.encode("utf-8")
        img_renderer = QSvgRenderer(QByteArray(img_svg_data))

        img_pixmap = QPixmap(32, 32)
        img_pixmap.fill(Qt.transparent)
        painter = QPainter(img_pixmap)
        img_renderer.render(painter)
        painter.end()

        img_picker = QPushButton()
        img_picker.setFixedSize(32, 32)
        img_picker.setIcon(QIcon(img_pixmap))
        img_picker.setIconSize(QSize(24, 24))
        img_picker.setStyleSheet("""
            QPushButton {
                background: transparent;
                border: none;
                border-radius: 10px;
                padding: 5px;
            }
            QPushButton:hover {
                background: rgba(255, 255, 255, 0.1);
            }
            QPushButton:pressed {
                background: rgba(255, 255, 255, 0.2);
            }
        """)
        img_picker.setCursor(Qt.PointingHandCursor)
        img_picker.setToolTip("Image Picker")
        img_picker.clicked.connect(self.on_image_clicked)
        self.img_picker = img_picker


        # Region picker button
        region_svg_data = b"""
        <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="#fcf8f8" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="lucide lucide-crop-icon lucide-crop"><path d="M6 2v14a2 2 0 0 0 2 2h14"/><path d="M18 22V8a2 2 0 0 0-2-2H2"/></svg>
        """ 
        # img_svg_bytes = img_svg_data.encode("utf-8")
        region_renderer = QSvgRenderer(QByteArray(region_svg_data))

        region_pixmap = QPixmap(32, 32)
        region_pixmap.fill(Qt.transparent)
        painter = QPainter(region_pixmap)
        region_renderer.render(painter)
        painter.end()

        region_picker = QPushButton()
        region_picker.setFixedSize(32, 32)
        region_picker.setIcon(QIcon(region_pixmap))
        region_picker.setIconSize(QSize(24, 24))
        region_picker.setStyleSheet("""
            QPushButton {
                background: transparent;
                border: none;
                border-radius: 10px;
                padding: 5px;
            }
            QPushButton:hover {
                background: rgba(255, 255, 255, 0.1);
            }
            QPushButton:pressed {
                background: rgba(255, 255, 255, 0.2);
            }
        """)
        region_picker.setCursor(Qt.PointingHandCursor)
        region_picker.setToolTip("Region Picker")
        region_picker.clicked.connect(self.on_region_clicked)
        self.region_picker = region_picker
        
        # Yes button with tick icon
        yes_svg_data = b"""
        <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24"
            viewBox="0 0 24 24" fill="none" stroke="#f8f7f7"
            stroke-width="2" stroke-linecap="round" stroke-linejoin="round"
            class="lucide lucide-check-icon lucide-check">
        <path d="M20 6 9 17l-5-5"/>
        </svg>
        """

        # Render the SVG to a QPixmap
        yes_renderer = QSvgRenderer(QByteArray(yes_svg_data))
        yes_pixmap = QPixmap(32, 32)
        yes_pixmap.fill(Qt.transparent)
        painter = QPainter(yes_pixmap)
        yes_renderer.render(painter)
        painter.end()

        # ✅ Create the QPushButton with the rendered icon
        yes_btn = QPushButton()
        yes_btn.setFixedSize(32, 32)
        yes_btn.setIcon(QIcon(yes_pixmap))
        yes_btn.setIconSize(QSize(24, 24))
        yes_btn.setStyleSheet("""
            QPushButton {
                background: transparent;
                border: none;
                border-radius: 10px;
                padding: 5px;
            }
            QPushButton:hover {
                background: rgba(255, 255, 255, 0.1);
            }
            QPushButton:pressed {
                background: rgba(255, 255, 255, 0.2);
            }
        """)
        yes_btn.setCursor(Qt.PointingHandCursor)
        yes_btn.setToolTip("Proceed")
        self._yes_in_progress = False  # prevent double-processing
        yes_btn.clicked.connect(self._handle_yes_clicked)
        self.yes_btn = yes_btn
        
        # Small dropdown-like button to toggle xpath input panel
        dropdown_btn = QPushButton("▾")
        dropdown_btn.setFixedSize(32, 32)
        dropdown_btn.setStyleSheet("""
            QPushButton {
                color: #FFFFFF;
                background: transparent;
                border: 1px solid rgba(255,255,255,0.2);
                border-radius: 6px;
                padding: 2px;
            }
            QPushButton:hover { background: rgba(255,255,255,0.08); }
            QPushButton:pressed { background: rgba(255,255,255,0.16); }
        """)
        dropdown_btn.setCursor(Qt.PointingHandCursor)
        dropdown_btn.setToolTip("Paste custom XPath and check")
        dropdown_btn.clicked.connect(self.toggle_input_panel)
        self.dropdown_btn = dropdown_btn
        
        # Add buttons to button layout (no stretch needed)
        button_layout.addWidget(self.delay_edit)
        # button_layout.addWidget(no_btn)
        button_layout.addWidget(coord_btn)
        button_layout.addWidget(img_picker)
        button_layout.addWidget(region_picker)
        button_layout.addWidget(yes_btn)
        button_layout.addWidget(dropdown_btn)
        
        # Add button layout to the top row
        top_row.addLayout(button_layout)
        main_layout.addLayout(top_row)
        
        # Input panel (hidden by default)
        self.input_panel = QWidget(container)
        input_layout = QHBoxLayout(self.input_panel)
        input_layout.setContentsMargins(0, 0, 0, 0)
        input_layout.setSpacing(8)
        
        self.xpath_edit = QLineEdit()
        self.xpath_edit.setPlaceholderText("Enter your data here")
        self.xpath_edit.setStyleSheet("""
            QLineEdit {
                color: #FFFFFF;
                background: rgba(255,255,255,0.08);
                border: 1px solid rgba(255,255,255,0.2);
                border-radius: 6px;
                padding: 6px 8px;
                font-size: 12px;
            }
            QLineEdit:focus { border-color: #00CED1; }
        """)
        self.xpath_edit.textChanged.connect(self.on_xpath_text_changed)
        
        check_btn = QPushButton("Check")
        check_btn.setFixedHeight(32)
        check_btn.setStyleSheet("""
            QPushButton {
                color: #0E0E0E;
                background: #00CED1;
                border: none;
                border-radius: 6px;
                padding: 6px 12px;
                font-weight: 600;
            }
            QPushButton:hover { background: #12dfe2; }
            QPushButton:pressed { background: #0fb8bb; }
        """)
        check_btn.setCursor(Qt.PointingHandCursor)
        check_btn.clicked.connect(self.on_check_clicked)
        self.check_btn = check_btn
        
        input_layout.addWidget(self.xpath_edit, 1)
        input_layout.addWidget(check_btn)
        self.input_panel.setVisible(False)
        main_layout.addWidget(self.input_panel)
        
        # Add fade-in animation
        self.fade_effect = QGraphicsOpacityEffect()
        container.setGraphicsEffect(self.fade_effect)
        
        self.fade_animation = QPropertyAnimation(self.fade_effect, b"opacity")
        self.fade_animation.setDuration(300)
        self.fade_animation.setStartValue(0.0)
        self.fade_animation.setEndValue(1.0)
        self.fade_animation.setEasingCurve(QEasingCurve.OutCubic)
        self.fade_animation.start()
        
        # Add pulsing glow effect
        self.glow_timer = QTimer()
        self.glow_timer.timeout.connect(self.toggle_glow)
        self.glow_timer.start(800)  # Pulse every 800ms
        self.glow_state = False
    
    def toggle_glow(self):
        """Toggle glow effect for attention"""
        try:
            container = self.findChild(QWidget)
            if container:
                if self.glow_state:
                    container.setStyleSheet("""
                        QWidget {
                            background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                                                      stop:0 #2D2D2D, stop:1 #1A1A1A);
                            border: 2px solid rgba(0, 206, 209, 0.6);
                            border-radius: 12px;
                        }
                    """)
                else:
                    container.setStyleSheet("""
                        QWidget {
                            background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                                                      stop:0 #2D2D2D, stop:1 #1A1A1A);
                            border: 2px solid rgba(0, 206, 209, 1.0);
                            border-radius: 12px;
                        }
                    """)
                self.glow_state = not self.glow_state
        except Exception as e:
            print(f"Error toggling glow: {e}")
    
    def toggle_input_panel(self):
        """Show/Hide the custom XPath input panel and adjust height"""
        try:
            if self.input_panel.isVisible():
                self.input_panel.setVisible(False)
                self.setFixedHeight(70)
                if hasattr(self, 'container'):
                    self.container.setGeometry(0, 0, self.width(), 70)
            else:
                self.input_panel.setVisible(True)
                self.setFixedHeight(120)
                if hasattr(self, 'container'):
                    self.container.setGeometry(0, 0, self.width(), 120)
        except Exception as e:
            print(f"Error toggling input panel: {e}")
    
    def on_check_clicked(self):
        """Apply user-entered XPath and start blinking that element"""
        try:
            text = self.xpath_edit.text().strip() if hasattr(self, 'xpath_edit') else ''
            if not text:
                # brief visual feedback
                self.xpath_edit.setStyleSheet(self.xpath_edit.styleSheet() + "\nQLineEdit { border-color: #ff6b6b; }")
                QTimer.singleShot(600, lambda: self.xpath_edit.setStyleSheet(self.xpath_edit.styleSheet().replace("border-color: #ff6b6b;", "border-color: #00CED1;")))
                return
            self.user_xpath = text
            self.main_xpath = text
            self.apply_new_xpath(text)
        except Exception as e:
            print(f"Error on check clicked: {e}")
    
    def on_xpath_text_changed(self, text):
        """Keep main_xpath in sync with live edits in the input field"""
        try:
            self.main_xpath = (text or '').strip()
        except Exception as e:
            print(f"Error syncing text to main_xpath: {e}")
    
    def apply_new_xpath(self, new_xpath: str):
        """Switch blinking to a new xpath"""
        try:
            self.stop_element_blinking()
            self.current_xpath = new_xpath
            if self.current_xpath.endswith(".png") and type(self.bound_index_data)==list:
                self.start_bounds_blinking(self.bound_index_data)
            elif type(self.current_xpath)==list or (self.current_xpath.startswith("[") and self.current_xpath.endswith("]")):
                x,y=self.coordiante_bound
                self.start_pointer_blinking(x,y)
            # else:
            #     self.start_element_blinking()
            
        except Exception as e:
            print(f"Error applying new xpath: {e}")
    
    def mousePressEvent(self, event):
        """Handle mouse press for dragging"""
        if event.button() == Qt.LeftButton:
            self._mouse_pressed = True
            self._mouse_pos = event.globalPos() - self.pos()
            event.accept()
    
    def mouseReleaseEvent(self, event):
        """Handle mouse release"""
        if event.button() == Qt.LeftButton:
            self._mouse_pressed = False
            event.accept()
    
    def mouseMoveEvent(self, event):
        """Handle mouse move for dragging"""
        if self._mouse_pressed and self._mouse_pos is not None:
            self.move(event.globalPos() - self._mouse_pos)
            event.accept()

    def keyPressEvent(self, event):
        # Prevent accidental close via Esc
        if event.key() == Qt.Key_Escape:
            event.ignore()
            return
        super().keyPressEvent(event)
    
    def start_element_blinking(self):
        """Start blinking the element with blue highlight"""
        try:
            # Find the element
            element = WebDriverWait(self.driver, 5).until(
                EC.presence_of_element_located((By.XPATH, self.current_xpath))
            )
            
            # Start blinking timer
            self.blinking_timer = QTimer()
            self.blinking_timer.timeout.connect(self.toggle_element_highlight)
            self.blinking_timer.start(500)  # Blink every 500ms
            
        except Exception as e:
            print(f"Error finding element for blinking: {e}")
            try:
                if hasattr(self, 'text_label') and self.text_label is not None:
                    element_display_desc=self.element_desc.replace('_', ' ').replace('field', '').strip().title()
                    self.text_label.setText(f"<b>Unable to Find {element_display_desc}. Please select the field</b>")
            except Exception:
                pass
    def stop_element_blinking_xpath(self):
        """Stop blinking the element and remove highlight"""
        try:
            # Stop the blinking timer if it's running
            if hasattr(self, 'blinking_timer') and self.blinking_timer is not None:
                self.blinking_timer.stop()
                self.blinking_timer = None

            # Ensure the element highlight is removed
            self.driver.execute_script("""
                var element = document.evaluate(arguments[0], document, null, XPathResult.FIRST_ORDERED_NODE_TYPE, null).singleNodeValue;
                if (element) {
                    element.style.border = '';
                    element.style.boxShadow = '';
                    element.style.backgroundColor = '';
                }
            """, self.current_xpath)

            # Reset blink state
            self.blink_state = False

        except Exception as e:
            print(f"Error stopping element blinking: {e}")

    def start_bounds_blinking(self, bounds_data):
        """Start blinking the bounds region with blue highlight
        
        Args:
            bounds_data: [left, right, top, bottom] coordinates
        """
        try:
            if not bounds_data or len(bounds_data) != 4:
                print("Invalid bounds data for blinking")
                return
            
            # Store bounds for blinking
            self.current_bounds = bounds_data
            
            # Start blinking timer for bounds
            self.bounds_blinking_timer = QTimer()
            self.bounds_blinking_timer.timeout.connect(self.toggle_bounds_highlight)
            self.bounds_blinking_timer.start(500)  # Blink every 500ms
            
            print(f"Started blinking for bounds: {bounds_data}")
            
        except Exception as e:
            print(f"Error starting bounds blinking: {e}")

    def toggle_bounds_highlight(self):
        """Toggle bounds region highlight overlay on screen (not in DOM)"""
        try:
            if not hasattr(self, 'current_bounds') or not self.current_bounds:
                return
            
            if self.bounds_blink_state:
                # Hide the highlight overlay
                if hasattr(self, 'bounds_highlight_overlay') and self.bounds_highlight_overlay is not None:
                    self.bounds_highlight_overlay.hide()
            else:
                # Show/create the highlight overlay
                if not hasattr(self, 'bounds_highlight_overlay') or self.bounds_highlight_overlay is None:
                    self.bounds_highlight_overlay = BoundsHighlightOverlay(self.current_bounds)
                self.bounds_highlight_overlay.show()
                self.bounds_highlight_overlay.raise_()
            
            self.bounds_blink_state = not self.bounds_blink_state
            
        except Exception as e:
            print(f"Error toggling bounds highlight: {e}")

    def stop_bounds_blinking(self):
        """Stop blinking the bounds region and remove highlight overlay"""
        try:
            # Stop the blinking timer if it's running
            if hasattr(self, 'bounds_blinking_timer') and self.bounds_blinking_timer is not None:
                self.bounds_blinking_timer.stop()
                self.bounds_blinking_timer = None

            # Hide and close the highlight overlay
            if hasattr(self, 'bounds_highlight_overlay') and self.bounds_highlight_overlay is not None:
                try:
                    self.bounds_highlight_overlay.hide()
                    self.bounds_highlight_overlay.close()
                    self.bounds_highlight_overlay.deleteLater()
                except Exception:
                    pass
                self.bounds_highlight_overlay = None

            # Reset blink state
            self.bounds_blink_state = False
            
            print("Stopped bounds blinking")

        except Exception as e:
            print(f"Error stopping bounds blinking: {e}")

    def start_pointer_blinking(self, x, y):
        """Start blinking the mouse pointer position with royal blue X mark
        
        Args:
            x: X coordinate of mouse pointer
            y: Y coordinate of mouse pointer
        """
        try:
            if x is None or y is None:
                print("Invalid coordinates for pointer blinking")
                return
            
            # Store coordinates for blinking
            self.current_pointer_coords = (x, y)
            
            # Start blinking timer for pointer
            self.pointer_blinking_timer = QTimer()
            self.pointer_blinking_timer.timeout.connect(self.toggle_pointer_highlight)
            self.pointer_blinking_timer.start(500)  # Blink every 500ms
            
            print(f"Started blinking for mouse pointer at: ({x}, {y})")
            
        except Exception as e:
            print(f"Error starting pointer blinking: {e}")

    def toggle_pointer_highlight(self):
        """Toggle mouse pointer X mark overlay on screen"""
        try:
            if not hasattr(self, 'current_pointer_coords') or not self.current_pointer_coords:
                return
            
            x, y = self.current_pointer_coords
            
            if self.pointer_blink_state:
                # Hide the pointer overlay
                if hasattr(self, 'mouse_pointer_overlay') and self.mouse_pointer_overlay is not None:
                    self.mouse_pointer_overlay.hide()
            else:
                # Show/create the pointer overlay
                if not hasattr(self, 'mouse_pointer_overlay') or self.mouse_pointer_overlay is None:
                    self.mouse_pointer_overlay = MousePointerOverlay(x, y)
                self.mouse_pointer_overlay.show()
                self.mouse_pointer_overlay.raise_()
            
            self.pointer_blink_state = not self.pointer_blink_state
            
        except Exception as e:
            print(f"Error toggling pointer highlight: {e}")

    def stop_pointer_blinking(self):
        """Stop blinking the mouse pointer and remove X mark overlay"""
        try:
            # Stop the blinking timer if it's running
            if hasattr(self, 'pointer_blinking_timer') and self.pointer_blinking_timer is not None:
                self.pointer_blinking_timer.stop()
                self.pointer_blinking_timer = None

            # Hide and close the pointer overlay
            if hasattr(self, 'mouse_pointer_overlay') and self.mouse_pointer_overlay is not None:
                try:
                    self.mouse_pointer_overlay.hide()
                    self.mouse_pointer_overlay.close()
                    self.mouse_pointer_overlay.deleteLater()
                except Exception:
                    pass
                self.mouse_pointer_overlay = None

            # Reset blink state
            self.pointer_blink_state = False
            
            print("Stopped pointer blinking")

        except Exception as e:
            print(f"Error stopping pointer blinking: {e}")


    def toggle_element_highlight(self):
        """Toggle element highlight between blue and normal"""
        try:
            if self.blink_state:
                # Remove highlight
                self.driver.execute_script("""
                    var element = document.evaluate(arguments[0], document, null, XPathResult.FIRST_ORDERED_NODE_TYPE, null).singleNodeValue;
                    if (element) {
                        element.style.border = '';
                        element.style.boxShadow = '';
                        element.style.backgroundColor = '';
                    }
                """, self.current_xpath)
            else:
                # Add blue highlight
                self.driver.execute_script("""
                    var element = document.evaluate(arguments[0], document, null, XPathResult.FIRST_ORDERED_NODE_TYPE, null).singleNodeValue;
                    if (element) {
                        element.style.border = '3px solid #0078d4';
                        element.style.boxShadow = '0 0 10px #0078d4';
                        element.style.backgroundColor = 'rgba(0, 120, 212, 0.1)';
                    }
                """, self.current_xpath)
            
            self.blink_state = not self.blink_state
            
        except Exception as e:
            print(f"Error toggling element highlight: {e}")
    
    def stop_element_blinking(self):
        """Stop blinking and remove highlight"""
        try:
            if self.blinking_timer:
                self.blinking_timer.stop()
                self.blinking_timer = None
            
            # Remove highlight
            self.driver.execute_script("""
                var element = document.evaluate(arguments[0], document, null, XPathResult.FIRST_ORDERED_NODE_TYPE, null).singleNodeValue;
                if (element) {
                    element.style.border = '';
                    element.style.boxShadow = '';
                    element.style.backgroundColor = '';
                }
            """, self.current_xpath)
            
        except Exception as e:
            print(f"Error stopping element blinking: {e}")
    
    def on_yes_clicked(self):
        """Handle Yes button click"""
        log_action("ElementConfirmationDialog: on_yes_clicked called")
        # Don't close if coordinate picker is running
        if getattr(self, '_coordinate_picker_running', False):
            log_action("ElementConfirmationDialog: on_yes_clicked - coordinate picker is running, aborting")
            return
            
        self.result = True
        log_action("ElementConfirmationDialog: on_yes_clicked - set result=True")
        try:
            typed = ''
            if hasattr(self, 'xpath_edit') and self.xpath_edit is not None:
                typed = self.xpath_edit.text().strip()
            log_action(f"ElementConfirmationDialog: on_yes_clicked - typed input: '{typed}'")
            if typed:
                # dropdown input overrides main_xpath
                self.main_xpath = typed
            if getattr(self, 'element_verify', False):
                # if at least once picked via X, return main_xpath
                self.chosen_xpath = self.main_xpath
                log_action(f"ElementConfirmationDialog: on_yes_clicked - element_verify=True, chosen_xpath='{self.chosen_xpath}'")
            elif getattr(self, 'coordinate_verify', False):
                import ast
                self.chosen_xpath = ast.literal_eval(typed)
                log_action(f"ElementConfirmationDialog: on_yes_clicked - coordinate_verify=True, chosen_xpath={self.chosen_xpath}")
            elif getattr(self, 'region_verify', False):
                import ast
                self.chosen_xpath = ast.literal_eval(typed)
                log_action(f"ElementConfirmationDialog: on_yes_clicked - region_verify=True, chosen_xpath={self.chosen_xpath}")
            elif getattr(self, 'image_verify', False):
                self.chosen_xpath = typed
                log_action(f"ElementConfirmationDialog: on_yes_clicked - image_verify=True, chosen_xpath='{self.chosen_xpath}'")
            else:
                # no picker used; return typed if present else original
                if typed:
                    self.chosen_xpath = self.main_xpath
                log_action(f"ElementConfirmationDialog: on_yes_clicked - no picker used, chosen_xpath='{self.chosen_xpath}'")
        except Exception as e:
            log_action(f"ElementConfirmationDialog: on_yes_clicked - exception: {e}")
            # self.chosen_xpath = self.xpath
            pass
        log_action(f"ElementConfirmationDialog: on_yes_clicked - calling cleanup_and_close with result={self.result}, chosen_xpath='{self.chosen_xpath}'")
        self.cleanup_and_close()

    def _handle_yes_clicked(self):
        """Wrapper to ensure Yes click always triggers processing exactly once"""
        if self._yes_in_progress:
            return
        if getattr(self, '_coordinate_picker_running', False):
            print("Coordinate picker is running, cannot close dialog yet")
            return
        self._yes_in_progress = True
        # Defer to next event loop tick to avoid focus/close race conditions
        QTimer.singleShot(0, self._run_yes_handler)

    def _run_yes_handler(self):
        try:
            self.on_yes_clicked()
        finally:
            self._yes_in_progress = False
    
    def on_no_clicked(self):
        """Delay (optional) then use element picker to select an element; do not close dialog."""
        try:
            delay = 0
            if hasattr(self, 'delay_edit') and self.delay_edit is not None:
                s = self.delay_edit.text().strip()
                delay = int(s) if s.isdigit() else 0
            if delay > 0:
                self.start_countdown(delay)
            else:
                self.stop_bounds_blinking()
                self.stop_pointer_blinking()
                self._run_element_picker()
        except Exception as e:
            print(f"Error handling no click: {e}")
        # Do not close the dialog here

    def start_countdown(self, seconds: int):
        try:
            # Create and show the overlay; pick after finish
            self.countdown_overlay = CountdownOverlay(seconds)
            self.countdown_overlay.finished.connect(self._run_element_picker)
            self.countdown_overlay.show()
        except Exception as e:
            print(f"Error starting countdown: {e}")
            self._run_element_picker()

    def _set_ui_busy(self, busy: bool):
        try:
            for w in [getattr(self, 'no_btn', None), getattr(self, 'coord_btn', None),
                      getattr(self, 'yes_btn', None), getattr(self, 'dropdown_btn', None), 
                      getattr(self, 'check_btn', None), getattr(self, 'delay_edit', None)]:
                if w is not None:
                    w.setEnabled(not busy)
            if busy:
                QApplication.setOverrideCursor(Qt.WaitCursor)
            else:
                QApplication.restoreOverrideCursor()
        except Exception:
            pass

    def _run_element_picker(self):
        try:
            # Prevent starting multiple pickers simultaneously
            if getattr(self, '_picker_thread', None):
                return
            from PyQt5.QtCore import QThread
            self._picker_thread = QThread()
            self._picker_worker = PickerWorker(self.driver)
            self._picker_worker.moveToThread(self._picker_thread)
            self._picker_thread.started.connect(self._picker_worker.run)
            self._picker_worker.finished.connect(self._on_picker_finished)
            self._picker_worker.error.connect(self._on_picker_error)
            # Cleanup
            self._picker_worker.finished.connect(self._picker_thread.quit)
            self._picker_worker.finished.connect(self._picker_worker.deleteLater)
            self._picker_thread.finished.connect(self._clear_picker_thread)
            self._picker_worker.error.connect(self._picker_thread.quit)
            self._picker_worker.error.connect(self._picker_worker.deleteLater)

            self._set_ui_busy(True)
            self._picker_thread.start()
        except Exception as e:
            print(f"Error starting picker thread: {e}")

    def _clear_picker_thread(self):
        try:
            if hasattr(self, '_picker_thread') and self._picker_thread is not None:
                self._picker_thread.deleteLater()
        except Exception:
            pass
        self._picker_thread = None
        self._picker_worker = None
        self._set_ui_busy(False)

    @pyqtSlot(str)
    def _on_picker_finished(self, picked: str):
        try:
            picked = (picked or '').strip()
            if picked:
                self.last_picker_xpath = picked
                self.element_verify = True
                self.image_verify=False
                self.region_verify=False
                self.coordinate_verify = False
                self.main_xpath = picked
                # Reflect picked xpath in the input field without forcing panel open
                try:
                    if hasattr(self, 'xpath_edit') and self.xpath_edit is not None:
                        self.xpath_edit.setText(picked)
                except Exception as e:
                    print(f"Error setting picked xpath into input: {e}")
                # Switch blinking to the picked xpath
                self.apply_new_xpath(picked)
        except Exception as e:
            print(f"Error handling picker result: {e}")

    @pyqtSlot(str)
    def _on_picker_error(self, msg: str):
        print(f"Picker error: {msg}")

    def _on_snipping_tool_finished(self, snipping_tool):
        """Handle SnippingTool completion - restore dialog and process captured image"""
        log_action("ElementConfirmationDialog: _on_snipping_tool_finished called")
        try:
            # CRITICAL: Restore dialog visibility and focus after SnippingTool closes
            log_action("ElementConfirmationDialog: Restoring dialog visibility and focus after SnippingTool")
            self.show()
            self.raise_()
            self.activateWindow()
            QApplication.processEvents()
            log_action("ElementConfirmationDialog: Dialog restored to foreground after SnippingTool")
            
            # Check if user captured something
            if snipping_tool.captured_region is not None:
                log_action("ElementConfirmationDialog: Image captured, processing region")
                # Create images directory if it doesn't exist
                images_dir = f"{self.proj_name}/{self.task_name}/images"
                if not os.path.exists(images_dir):
                    os.makedirs(images_dir)
                
                # Generate filename using desc parameter
                filename = f"{self.var_name}.png"
                filepath = os.path.join(images_dir, filename)
                
                # Save the captured image
                snipping_tool.captured_region.save(filepath)
                log_action(f"ElementConfirmationDialog: Image saved to {filepath}")
                
                # Extract and store boundary coordinates [left, right, top, bottom]
                bounds_data = snipping_tool.bounds  # [left, right, top, bottom]
                if bounds_data:
                    log_action(f"ElementConfirmationDialog: Captured bounds - Left={bounds_data[0]}, Right={bounds_data[1]}, Top={bounds_data[2]}, Bottom={bounds_data[3]}")
                    print(f"Captured bounds: Left={bounds_data[0]}, Right={bounds_data[1]}, Top={bounds_data[2]}, Bottom={bounds_data[3]}")
                    self.bound_index_data=bounds_data
                    # Start blinking the captured bounds region
                    self.start_bounds_blinking(bounds_data)
                
                # Set the image_verify flag to indicate image was captured
                self.coordinate_verify = False
                self.element_verify = False
                self.region_verify=False
                self.image_verify = True
                
                # Stop pointer blinking if active
                try:
                    self.stop_pointer_blinking()
                except:
                    pass
                
                # Update the xpath edit field with the filename
                if hasattr(self, 'xpath_edit') and self.xpath_edit is not None:
                    self.xpath_edit.setText(filename)
                
                # Update main_xpath with the filename
                self.main_xpath = filename
                
            else:
                QMessageBox.information(self, "Info", "No region selected.")
                print("No region selected")
            
            # CRITICAL: Show the dialog again and ensure it stays open
            self.show()
            self.raise_()
            self.activateWindow()
            
            # Restart glow timer if it was stopped
            if hasattr(self, 'glow_timer') and not self.glow_timer.isActive():
                self.glow_timer.start(800)
            
            # Process events to update UI
            QApplication.processEvents()
            
            # Ensure dialog gets focus and remains visible
            self.setFocus(Qt.ActiveWindowFocusReason)
            QApplication.processEvents()
            
            print("Dialog restored after image capture, waiting for user to click Yes")
            
        except Exception as e:
            import traceback
            print(f"Error in _on_snipping_tool_finished: {e}")
            traceback.print_exc()
            
            # Ensure dialog is shown even if there's an error
            try:
                self.show()
                self.raise_()
                self.activateWindow()
            except:
                pass
        finally:
            try:
                self.show()
                self.raise_()
                self.activateWindow()
            except:
                pass
            # Mark that image picker is no longer running
            self._image_picker_running = False
            log_action("ElementConfirmationDialog: _image_picker_running set to False")
    
    def _on_region_snipping_tool_finished(self, snipping_tool):
        """Handle SnippingTool completion for region picker - restore dialog and process captured region"""
        log_action("ElementConfirmationDialog: _on_region_snipping_tool_finished called")
        try:
            # CRITICAL: Restore dialog visibility and focus after SnippingTool closes
            log_action("ElementConfirmationDialog: Restoring dialog visibility and focus after region SnippingTool")
            self.show()
            self.raise_()
            self.activateWindow()
            QApplication.processEvents()
            log_action("ElementConfirmationDialog: Dialog restored to foreground after region SnippingTool")
            
            # Check if user captured something
            if snipping_tool.captured_region is not None:
                log_action("ElementConfirmationDialog: Region captured, processing bounds")
                # Create images directory if it doesn't exist
                images_dir = f"{self.proj_name}/{self.task_name}/images"
                if not os.path.exists(images_dir):
                    os.makedirs(images_dir)
                
                # Extract and store boundary coordinates [left, right, top, bottom]
                bounds_data = snipping_tool.bounds  # [left, right, top, bottom]
                if bounds_data:
                    log_action(f"ElementConfirmationDialog: Captured region bounds - Left={bounds_data[0]}, Right={bounds_data[1]}, Top={bounds_data[2]}, Bottom={bounds_data[3]}")
                    print(f"Captured bounds: Left={bounds_data[0]}, Right={bounds_data[1]}, Top={bounds_data[2]}, Bottom={bounds_data[3]}")
                    self.bound_index_data=bounds_data
                    # Start blinking the captured bounds region
                    self.start_bounds_blinking(bounds_data)
                
                # Set the region_verify flag to indicate region was captured
                self.coordinate_verify = False
                self.element_verify = False
                self.image_verify = False
                self.region_verify=True
                
                log_action(f"ElementConfirmationDialog: Region bounds stored: {self.bound_index_data}")
                print(self.bound_index_data)
                # Stop pointer blinking if active
                try:
                    self.stop_pointer_blinking()
                except:
                    pass
                
                # Update the xpath edit field with the bounds
                if hasattr(self, 'xpath_edit') and self.xpath_edit is not None:
                    self.xpath_edit.setText(str(bounds_data))
                
                # Update main_xpath with the bounds
                self.main_xpath = str(bounds_data)
                
            else:
                QMessageBox.information(self, "Info", "No region selected.")
                print("No region selected")
            
            # CRITICAL: Show the dialog again and ensure it stays open
            self.show()
            self.raise_()
            self.activateWindow()
            
            # Restart glow timer if it was stopped
            if hasattr(self, 'glow_timer') and not self.glow_timer.isActive():
                self.glow_timer.start(800)
            
            # Process events to update UI
            QApplication.processEvents()
            
            # Ensure dialog gets focus and remains visible
            self.setFocus(Qt.ActiveWindowFocusReason)
            QApplication.processEvents()
            
            print("Dialog restored after region capture, waiting for user to click Yes")
            
        except Exception as e:
            import traceback
            print(f"Error in _on_region_snipping_tool_finished: {e}")
            traceback.print_exc()
            
            # Ensure dialog is shown even if there's an error
            try:
                self.show()
                self.raise_()
                self.activateWindow()
            except:
                pass
        finally:
            try:
                self.show()
                self.raise_()
                self.activateWindow()
            except:
                pass
            # Mark that region picker is no longer running
            self._region_picker_running = False
            log_action("ElementConfirmationDialog: _region_picker_running set to False")
    
    def on_image_clicked(self):
        log_action("ElementConfirmationDialog: on_image_clicked called")
        try:
            # Mark that image picker is running to prevent dialog from being hidden
            self._image_picker_running = True
            log_action("ElementConfirmationDialog: _image_picker_running set to True")
            
            # Hide the dialog temporarily
            self.lower()
            log_action("ElementConfirmationDialog: Dialog lowered")
            QApplication.processEvents()
            
            # Wait a moment for dialog to hide
            QApplication.processEvents()
            QApplication.processEvents()
            log_action("ElementConfirmationDialog: Processing events completed")
            
            try:
                self.stop_bounds_blinking()
            except:
                pass
            try:
                self.stop_pointer_blinking()
            except:
                pass

            
            # Create and show snipping tool
            log_action("ElementConfirmationDialog: Creating SnippingTool")
            snipping_tool = SnippingTool()
            # Connect finished signal to our handler instead of using nested event loop
            try:
                snipping_tool.finished.connect(lambda: self._on_snipping_tool_finished(snipping_tool))
                log_action("ElementConfirmationDialog: SnippingTool finished signal connected successfully")
            except Exception as sig_err:
                log_action(f"ElementConfirmationDialog: WARNING - Failed to connect SnippingTool signal: {sig_err}")
            
            snipping_tool.show()
            log_action("ElementConfirmationDialog: SnippingTool shown, waiting for completion via signal")
            
            # Store reference to snipping tool so we can access it in the handler
            self._current_snipping_tool = snipping_tool
            
            # CRITICAL: Set up a timeout fallback to restore dialog if signal doesn't fire within 5 seconds
            # This ensures dialog always comes back even if SnippingTool signal fails
            log_action("ElementConfirmationDialog: Setting 5-second timeout fallback for image picker")
            QTimer.singleShot(5000, lambda: self._restore_dialog_timeout_fallback("image"))
            
            # Return immediately - the handler will restore the dialog when SnippingTool finishes
            return
            
        except Exception as e:
            import traceback
            print(f"Error in on_image_clicked: {e}")
            traceback.print_exc()
            log_action(f"ElementConfirmationDialog: Exception in on_image_clicked: {e}")
            
            # Ensure dialog is shown even if there's an error
            try:
                self.show()
                self.raise_()
                self.activateWindow()
            except:
                pass
        finally:
            try:
                self.show()
                self.raise_()
                self.activateWindow()
            except:
                pass
            # Mark that image picker is no longer running
            self._image_picker_running = False
            log_action("ElementConfirmationDialog: _image_picker_running set to False")

    def on_region_clicked(self):
        log_action("ElementConfirmationDialog: on_region_clicked called")
        try:
            # Mark that region picker is running to prevent dialog from being hidden
            self._region_picker_running = True
            log_action("ElementConfirmationDialog: _region_picker_running set to True")
            
            # Hide the dialog temporarily
            self.lower()
            log_action("ElementConfirmationDialog: Dialog lowered")
            QApplication.processEvents()
            
            # Wait a moment for dialog to hide
            QApplication.processEvents()
            QApplication.processEvents()
            log_action("ElementConfirmationDialog: Processing events completed")
            
            try:
                self.stop_element_blinking_xpath()
            except:
                pass
            
            try:
                self.stop_bounds_blinking()
            except:
                pass
            try:
                self.stop_pointer_blinking()
            except:
                pass

            
            # Create and show snipping tool
            log_action("ElementConfirmationDialog: Creating SnippingTool for region picker")
            snipping_tool = SnippingTool()
            # Connect finished signal to our handler instead of using nested event loop
            try:
                snipping_tool.finished.connect(lambda: self._on_region_snipping_tool_finished(snipping_tool))
                log_action("ElementConfirmationDialog: SnippingTool finished signal connected successfully for region picker")
            except Exception as sig_err:
                log_action(f"ElementConfirmationDialog: WARNING - Failed to connect region SnippingTool signal: {sig_err}")
            
            snipping_tool.show()
            log_action("ElementConfirmationDialog: SnippingTool shown for region picker, waiting for completion via signal")
            
            # Store reference to snipping tool so we can access it in the handler
            self._current_region_snipping_tool = snipping_tool
            
            # CRITICAL: Set up a timeout fallback to restore dialog if signal doesn't fire within 5 seconds
            # This ensures dialog always comes back even if SnippingTool signal fails
            log_action("ElementConfirmationDialog: Setting 5-second timeout fallback for region picker")
            QTimer.singleShot(5000, lambda: self._restore_dialog_timeout_fallback("region"))
            
            # Return immediately - the handler will restore the dialog when SnippingTool finishes
            return
            
        except Exception as e:
            import traceback
            print(f"Error in on_region_clicked: {e}")
            traceback.print_exc()
            log_action(f"ElementConfirmationDialog: Exception in on_region_clicked: {e}")
            
            # Ensure dialog is shown even if there's an error
            try:
                self.show()
                self.raise_()
                self.activateWindow()
            except:
                pass
        finally:
            try:
                self.show()
                self.raise_()
                self.activateWindow()
            except:
                pass
            # Mark that region picker is no longer running
            self._region_picker_running = False
            log_action("ElementConfirmationDialog: _region_picker_running set to False")
    
    def _restore_dialog_timeout_fallback(self, picker_type):
        """Fallback method to restore dialog if SnippingTool signal doesn't fire within 5 seconds"""
        log_action(f"ElementConfirmationDialog: _restore_dialog_timeout_fallback called for {picker_type} picker")
        try:
            # Only restore if the picker is still marked as running (signal handler hasn't fired)
            if picker_type == "image" and getattr(self, '_image_picker_running', False):
                log_action(f"ElementConfirmationDialog: TIMEOUT FALLBACK - Image picker signal didn't fire, restoring dialog")
                self.show()
                self.raise_()
                self.activateWindow()
                QApplication.processEvents()
                log_action("ElementConfirmationDialog: Dialog restored via timeout fallback (image picker)")
                
                # Restart glow timer if it was stopped
                if hasattr(self, 'glow_timer') and not self.glow_timer.isActive():
                    self.glow_timer.start(800)
                
                self._image_picker_running = False
                
            elif picker_type == "region" and getattr(self, '_region_picker_running', False):
                log_action(f"ElementConfirmationDialog: TIMEOUT FALLBACK - Region picker signal didn't fire, restoring dialog")
                self.show()
                self.raise_()
                self.activateWindow()
                QApplication.processEvents()
                log_action("ElementConfirmationDialog: Dialog restored via timeout fallback (region picker)")
                
                # Restart glow timer if it was stopped
                if hasattr(self, 'glow_timer') and not self.glow_timer.isActive():
                    self.glow_timer.start(800)
                
                self._region_picker_running = False
            else:
                log_action(f"ElementConfirmationDialog: Timeout fallback called but {picker_type} picker already finished (signal fired)")
                
        except Exception as e:
            log_action(f"ElementConfirmationDialog: Error in timeout fallback: {e}")
            print(f"Error in timeout fallback: {e}")
            traceback.print_exc()
            
    def on_coordinate_clicked(self):
        """Handle coordinate picker button click - runs on main thread since Qt widgets are involved"""
        log_action("ElementConfirmationDialog: on_coordinate_clicked called")
        try:
            delay = 0
            if hasattr(self, 'delay_edit') and self.delay_edit is not None:
                s = self.delay_edit.text().strip()
                delay = int(s) if s.isdigit() else 0
            log_action(f"ElementConfirmationDialog: on_coordinate_clicked - delay={delay}")
            if delay > 0:
                self.start_countdown_coordinate(delay)
            else:
                self._run_coordinate_picker()
        except Exception as e:
            log_action(f"ElementConfirmationDialog: on_coordinate_clicked - error: {e}")
            print(f"Error handling coordinate click: {e}")
        # Do not close the dialog here
    
    def _run_coordinate_picker(self):
        """Run coordinate picker - execute directly with event loop"""
        try:
            # Prevent starting multiple pickers simultaneously
            if getattr(self, '_coordinate_picker_running', False):
                return
            
            self._coordinate_picker_running = True
            
            # Stop element blinking before hiding dialog
            try:
                self.stop_element_blinking()
            except:
                pass
            try:
                self.stop_bounds_blinking()
            except:
                pass
            try:
                self.stop_pointer_blinking()
            except:
                pass
            
            # Stop glow timer to avoid interference
            if hasattr(self, 'glow_timer'):
                self.glow_timer.stop()
            
            # CRITICAL: Disable dialog to allow user to interact with screen behind it
            self.setEnabled(False)
            self.hide()
            QApplication.processEvents()
            
            # Now execute coordinate picker on the exposed screen
            self._execute_coordinate_picker()
            
        except Exception as e:
            import traceback
            print(f"Error setting up coordinate picker: {e}")
            print(traceback.format_exc())
            self._coordinate_picker_running = False
            # Restore dialog on error
            try:
                self.setEnabled(True)
                self.show()
                self.raise_()
                self.activateWindow()
            except:
                pass
    
    def start_countdown_coordinate(self, seconds: int):
        try:
            # Create and show the overlay; pick after finish
            self.countdown_overlay = CountdownOverlay(seconds)
            self.countdown_overlay.finished.connect(self._run_coordinate_picker)
            self.countdown_overlay.show()
        except Exception as e:
            print(f"Error starting countdown: {e}")
            self._run_coordinate_picker()
    
    def _execute_coordinate_picker(self):
        """Actually execute the coordinate picker - called via QTimer"""
        try:
            try:
                self.stop_element_blinking()
            except:
                pass
            try:
                self.stop_pointer_blinking()
            except:
                pass
            
            # Lower dialog so coordinate picker can appear on top
            self.lower()
            QApplication.processEvents()
            
            bound_index = None
            try:
                from coordinate_element_picker import select_element
                # This will block until user selects coordinates (uses QEventLoop internally)
                # It creates its own widgets and event loop on the main thread
                print("Starting coordinate picker...")
                bound_index = select_element()
                if hasattr(self, 'xpath_edit') and self.xpath_edit is not None:
                    self.xpath_edit.setText(str(bound_index))
                if type(bound_index) == list and len(bound_index) == 2:
                    # bound_index is [x, y] coordinates
                    x, y = bound_index
                    self.coordiante_bound=bound_index
                    # Start blinking the mouse pointer at these coordinates
                    
                    self.start_pointer_blinking(x, y)
                    self.coordinate_verify = True
                    self.element_verify = False
                    self.image_verify=False
                    self.region_verify=False
                print(f"Coordinate picker returned: {bound_index}")
            except Exception as e:
                import traceback
                print(f"Coordinate picker error: {e}")
                print(traceback.format_exc())
            
            # Process events after coordinate picker returns
            QApplication.processEvents()
            
            # Restore dialog - use QTimer to defer restoration slightly
            # This ensures coordinate picker's event loop has fully exited
            QTimer.singleShot(50, lambda: self._restore_dialog_after_picker(bound_index))
            
        except Exception as e:
            import traceback
            print(f"Error executing coordinate picker: {e}")
            print(traceback.format_exc())
            self._restore_dialog_after_picker(None)
    
    def _restore_dialog_after_picker(self, bound_index):
        """Restore dialog after coordinate picker completes"""
        log_action(f"ElementConfirmationDialog: _restore_dialog_after_picker called with bound_index={bound_index}")
        try:
            log_action("ElementConfirmationDialog: Restoring dialog after coordinate picker...")
            print("Restoring dialog after coordinate picker...")
            
            # Re-enable dialog and bring it to front
            self.setEnabled(True)
            self.raise_()
            self.activateWindow()
            log_action("ElementConfirmationDialog: Dialog enabled and raised")
            
            # Ensure dialog gets focus
            QApplication.processEvents()
            self.setFocus(Qt.ActiveWindowFocusReason)
            self.raise_()
            self.activateWindow()
            log_action("ElementConfirmationDialog: Dialog focus set")
            
            # Process events to ensure dialog is fully visible
            QApplication.processEvents()
            
            # Restart glow timer
            if hasattr(self, 'glow_timer'):
                self.glow_timer.start(800)
                log_action("ElementConfirmationDialog: Glow timer restarted")
            
            # Process the result
            if bound_index and isinstance(bound_index, list) and len(bound_index) == 2:
                log_action(f"ElementConfirmationDialog: Coordinate picker returned valid bounds: {bound_index}")
                print(f"Coordinate picker returned valid bounds: {bound_index}")
                # Auto-populate bounds in input field
                self._on_coordinate_finished(bound_index)
            else:
                log_action(f"ElementConfirmationDialog: Invalid bounds returned from coordinate picker or user cancelled: {bound_index}")
                print("Invalid bounds returned from coordinate picker or user cancelled")
                # Restart blinking with current xpath if no valid bounds
                # if self.current_xpath:
                #     try:
                #         self.start_element_blinking()
                #     except:
                #         pass  # If xpath is invalid, just continue
            
            # Process events to update UI
            QApplication.processEvents()
            
            # Verify dialog is enabled and visible
            if not self.isEnabled():
                log_action("ElementConfirmationDialog: WARNING - Dialog not enabled, restoring...")
                print("WARNING: Dialog not enabled, restoring...")
                self.setEnabled(True)
            if not self.isVisible():
                log_action("ElementConfirmationDialog: WARNING - Dialog not visible, restoring...")
                print("WARNING: Dialog not visible, restoring...")
                self.show()
                self.raise_()
                self.activateWindow()
            
            log_action("ElementConfirmationDialog: Dialog restored and waiting for user interaction (Yes button)...")
            print("Dialog restored and waiting for user interaction (Yes button)...")
            
        except Exception as e:
            import traceback
            print(f"Error restoring dialog: {e}")
            print(traceback.format_exc())
            try:
                self.setEnabled(True)
                self.raise_()
                self.activateWindow()
                if hasattr(self, 'glow_timer'):
                    self.glow_timer.start(800)
            except:
                pass
        finally:
            try:
                self.show()
                self.raise_()
                self.activateWindow()
            except:
                pass
            # Mark coordinate picker as done
            self._coordinate_picker_running = False
            self._set_ui_busy(False)
            
            # Process events one final time
            QApplication.processEvents()
            
            print("Coordinate picker cleanup complete, dialog should remain open")

    def _on_coordinate_finished(self, bounds: list):
        """Handle coordinate picker result - auto-populate input field and keep dialog open"""
        try:
            if bounds and len(bounds) == 4:
                left, right, top, bottom = bounds
                # Format as string: [left, right, top, bottom]
                bounds_str = f"[{left}, {right}, {top}, {bottom}]"
                
                # Update main_xpath with bounds
                self.main_xpath = bounds_str
                
                # Auto-populate the xpath input field
                try:
                    if hasattr(self, 'xpath_edit') and self.xpath_edit is not None:
                        # Set the text directly
                        self.xpath_edit.setText(bounds_str)
                        # Also update the user_xpath tracking variable
                        self.user_xpath = bounds_str
                        
                        # Show input panel if hidden - this expands the dialog
                        if not self.input_panel.isVisible():
                            self.toggle_input_panel()
                        
                        # Give focus to the input field so user can see it
                        self.xpath_edit.setFocus()
                        self.xpath_edit.selectAll()  # Select all text for easy editing
                        
                        # Process events to update UI immediately
                        QApplication.processEvents()
                        
                        print(f"Coordinate bounds set: {bounds_str}")
                except Exception as e:
                    print(f"Error setting coordinate bounds into input: {e}")
                    import traceback
                    print(traceback.format_exc())
        except Exception as e:
            print(f"Error handling coordinate result: {e}")
            import traceback
            print(traceback.format_exc())
    
    def cleanup_and_close(self):
        """Clean up resources and close dialog"""
        log_action("ElementConfirmationDialog: cleanup_and_close called")
        # Don't allow closing while coordinate picker is running
        if getattr(self, '_coordinate_picker_running', False):
            log_action("ElementConfirmationDialog: Cannot close - coordinate picker is running")
            return
        
        # Stop animations
        if hasattr(self, 'fade_animation'):
            self.fade_animation.stop()
            log_action("ElementConfirmationDialog: Fade animation stopped")
        
        if hasattr(self, 'glow_timer'):
            self.glow_timer.stop()
            log_action("ElementConfirmationDialog: Glow timer stopped")
        
        # Stop element blinking
        self.stop_element_blinking()
        log_action("ElementConfirmationDialog: Element blinking stopped")
        
        # Stop bounds blinking
        self.stop_bounds_blinking()
        log_action("ElementConfirmationDialog: Bounds blinking stopped")
        
        # Stop pointer blinking
        self.stop_pointer_blinking()
        log_action("ElementConfirmationDialog: Pointer blinking stopped")
        
        # Close dialog (guarded)
        log_action(f"ElementConfirmationDialog: Setting _force_close=True, result={self.result}, chosen_xpath='{self.chosen_xpath}'")
        self._force_close = True
        self.accept()
    
    def reject(self):
        # Prevent default reject (e.g., Esc) from closing the dialog
        pass
    
    def accept(self):
        """Guard accept; only allow when explicitly triggered via Yes (cleanup_and_close)."""
        if not getattr(self, '_force_close', False):
            # Block unintended accepts that would end exec_()
            return
        return super().accept()
    
    def hideEvent(self, event):
        """Prevent unintended dialog hides"""
        log_action(f"ElementConfirmationDialog: hideEvent triggered, _force_close={self._force_close}, _initialization_complete={self._initialization_complete}, _image_picker_running={self._image_picker_running}, _region_picker_running={self._region_picker_running}, _coordinate_picker_running={self._coordinate_picker_running}")
        
        # Log the stack trace to see where the hide is coming from
        import traceback
        stack_trace = ''.join(traceback.format_stack()[:-1])
        log_action(f"ElementConfirmationDialog: hideEvent stack trace: {stack_trace}")
        
        # Only allow hiding if:
        # 1. User explicitly clicked Yes (cleanup_and_close sets _force_close=True)
        # 2. Dialog is still initializing (allow hide during init)
        # 3. No picker is currently running
        if self._force_close or not self._initialization_complete:
            log_action(f"ElementConfirmationDialog: hideEvent accepted (force_close={self._force_close})")
            event.accept()
        elif self._image_picker_running or self._region_picker_running or self._coordinate_picker_running:
            log_action(f"ElementConfirmationDialog: hideEvent rejected - picker running (_image_picker_running={self._image_picker_running}, _region_picker_running={self._region_picker_running}, _coordinate_picker_running={self._coordinate_picker_running})")
            event.ignore()
            # Restore visibility immediately
            QTimer.singleShot(10, lambda: self._restore_visibility())
        else:
            log_action(f"ElementConfirmationDialog: hideEvent rejected - dialog should stay open")
            event.ignore()
            # Restore visibility immediately
            QTimer.singleShot(10, lambda: self._restore_visibility())
    
    def closeEvent(self, event):
        """Prevent accidental closing unless explicitly accepted via Yes"""
        log_action(f"ElementConfirmationDialog: closeEvent triggered, _force_close={getattr(self, '_force_close', False)}, _coordinate_picker_running={getattr(self, '_coordinate_picker_running', False)}")
        # Don't allow closing while coordinate picker is active
        if getattr(self, '_coordinate_picker_running', False):
            log_action("ElementConfirmationDialog: closeEvent ignored - coordinate picker is running")
            event.ignore()
            return
        # Only allow close if explicitly accepted
        if not getattr(self, '_force_close', False):
            log_action("ElementConfirmationDialog: closeEvent ignored - _force_close is False")
            event.ignore()
            return
        log_action("ElementConfirmationDialog: closeEvent accepted")
        event.accept()

def _clear_dialog_cache(dialog):
    """Clear all cached data created by the dialog to prevent bugs in subsequent runs"""
    try:
        log_action("element_status: Clearing dialog cache...")
        
        # Clear all picker flags
        dialog._image_picker_running = False
        dialog._region_picker_running = False
        dialog._coordinate_picker_running = False
        
        # Clear all verification flags
        dialog.element_verify = False
        dialog.image_verify = False
        dialog.region_verify = False
        dialog.coordinate_verify = False
        
        # Clear xpath data
        dialog.main_xpath = ""
        dialog.chosen_xpath = ""
        dialog.user_xpath = ""
        dialog.last_picker_xpath = ""
        
        # Clear bounds data
        dialog.bound_index_data = None
        dialog.coordiante_bound = None
        
        # Clear UI state
        if hasattr(dialog, 'xpath_edit') and dialog.xpath_edit is not None:
            dialog.xpath_edit.setText("")
        if hasattr(dialog, 'delay_edit') and dialog.delay_edit is not None:
            dialog.delay_edit.setText("")
        
        # Clear result
        dialog.result = False
        
        # Stop all animations and timers
        try:
            if hasattr(dialog, 'fade_animation'):
                dialog.fade_animation.stop()
        except:
            pass
        
        try:
            if hasattr(dialog, 'glow_timer'):
                dialog.glow_timer.stop()
        except:
            pass
        
        # Stop all blinking
        try:
            dialog.stop_element_blinking()
        except:
            pass
        
        try:
            dialog.stop_bounds_blinking()
        except:
            pass
        
        try:
            dialog.stop_pointer_blinking()
        except:
            pass
        
        # Clear snipping tool references
        dialog._current_snipping_tool = None
        dialog._current_region_snipping_tool = None
        
        # Clear picker thread references
        dialog._picker_thread = None
        dialog._picker_worker = None
        
        # Clear countdown overlay
        if hasattr(dialog, 'countdown_overlay'):
            try:
                dialog.countdown_overlay.close()
            except:
                pass
            dialog.countdown_overlay = None
        
        log_action("element_status: Dialog cache cleared successfully")
        
    except Exception as e:
        log_action(f"element_status: Error clearing dialog cache: {e}")
        import traceback
        print(f"Error clearing dialog cache: {e}")
        print(traceback.format_exc())

def element_status(element_description):
    """
    Show element confirmation dialog with xpath highlighting
    
    Args:
        xpath (str): XPath of the element to highlight
        driver: Selenium WebDriver instance
    
    Returns:
        tuple[bool, str]: (is_confirmed, xpath)
            - On Yes (tick): (True, XPATH) selection rules:
                - If element_verify is True (picked via X at least once): return main_xpath.
                - Else if dropdown input is non-empty: return main_xpath (typed value).
                - Else: return the original xpath passed to element_status.
            - X button runs element_picker(driver), switches blinking to its xpath, sets element_verify=True.
            - Closing the dialog without Yes returns (False, "").
    """
    log_action(f"element_status: Called with element_description='{element_description}'")
    # Check if we're running in a worker thread
    import threading
    current_thread = threading.current_thread()
    log_action(f"element_status: Running in thread '{current_thread.name}'")
    
    # If we're in the main thread, show dialog directly
    if current_thread.name == 'MainThread':
        log_action("element_status: Main thread detected, creating dialog")
        # Create/reuse QApplication and keep a strong reference to avoid GC
        global _APP_SINGLETON, _LAST_DIALOG_INSTANCE
        app = QApplication.instance()
        if app is None:
            if _APP_SINGLETON is None:
                _APP_SINGLETON = QApplication(sys.argv)
                log_action("element_status: Created new QApplication singleton")
            app = _APP_SINGLETON
        else:
            if _APP_SINGLETON is None:
                _APP_SINGLETON = app
            log_action("element_status: Using existing QApplication instance")
        
        # Install global hotkey filter if not already installed
        if not hasattr(app, '_hotkey_filter_installed'):
            hotkey_filter = GlobalHotkeyFilter()
            app.installEventFilter(hotkey_filter)
            app._hotkey_filter_installed = True
            log_action("element_status: Global hotkey filter installed (Ctrl+M to show dialog)")
        
        # Create and show dialog
        log_action("element_status: Creating ElementConfirmationDialog")
        dialog = ElementConfirmationDialog(element_description,app,element_description)
        _LAST_DIALOG_INSTANCE = dialog  # Store reference for Ctrl+M hotkey
        log_action("element_status: ElementConfirmationDialog created, dialog should be visible")
        
        # Process events multiple times to ensure dialog is fully rendered and responsive
        try:
            log_action("element_status: Processing events to render dialog")
            for i in range(3):
                QApplication.processEvents()
            log_action("element_status: Dialog rendered, processEvents completed")
        except Exception as e:
            log_action(f"element_status: Error processing events: {e}")
        
        log_action("element_status: Calling dialog.exec_()")
        
        # In subprocess mode, we need to run a persistent event loop
        # because dialog.exec_() may exit prematurely in subprocess context
        result_code = dialog.exec_()
        
        # Debug: Check why dialog exited
        log_action(f"element_status: Dialog exec_() returned with code: {result_code}")
        log_action(f"element_status: Dialog result: {dialog.result}")
        log_action(f"element_status: Dialog chosen_xpath: '{dialog.chosen_xpath}'")
        
        # If dialog exited but user didn't confirm, keep the event loop running
        # This handles the subprocess case where exec_() exits prematurely
        if not dialog.result and dialog.isVisible():
            log_action("element_status: Dialog still visible but exec_() returned - running persistent event loop")
            import time
            loop_count = 0
            max_loops = 3000  # ~30 seconds with 0.01s sleep
            # Run event loop until user explicitly closes dialog
            while dialog.isVisible() and not dialog.result and loop_count < max_loops:
                QApplication.processEvents()
                loop_count += 1
                # Small sleep to prevent busy-waiting
                time.sleep(0.01)
            
            if loop_count >= max_loops:
                log_action("element_status: Persistent event loop timeout after 30 seconds")
            else:
                log_action(f"element_status: Persistent event loop exited after {loop_count} iterations, dialog.result={dialog.result}, dialog.isVisible={dialog.isVisible()}")
        
        # Safety fallback: if dialog closed unexpectedly (result is False), return False and empty string
        if not dialog.result:
            log_action("element_status: Dialog result is False - clearing cache and returning (False, '')")
            _clear_dialog_cache(dialog)
            return False, ""
        
        log_action(f"element_status: Returning (True, '{dialog.chosen_xpath}')")
        result_xpath = dialog.chosen_xpath
        # Clear all dialog cache before returning
        result_return=dialog.result
        _clear_dialog_cache(dialog)
        return result_return, result_xpath
    else:
        # We're in a worker thread - need to communicate with main thread
        print(f"element_status called from worker thread: {current_thread.name}")
        print("Using signal-based communication with main thread")
        
        # Try to get the ExecuteCodeWorker instance from global reference
        try:
            # Import the global reference
            import main_process
            execute_worker = main_process._current_execute_worker
            
            print(f"Execute worker: {execute_worker}")
            print(f"Execute worker type: {type(execute_worker)}")
            
            if execute_worker and hasattr(execute_worker, 'element_confirmation_requested'):
                print("Found element_confirmation_requested signal")
                xpath=""
                driver=None
                # Emit signal to main thread
                execute_worker.element_confirmation_requested.emit(xpath, driver)
                print("Signal emitted to main thread")
                
                # Wait for response from main thread
                print("Waiting for response from main thread...")
                event_triggered = execute_worker.element_confirmation_event.wait(timeout=30)  # 30 second timeout
                
                if event_triggered:
                    # Get the result
                    result = execute_worker.element_confirmation_result
                    
                    # Reset the event for next use
                    execute_worker.element_confirmation_event.clear()
                    
                    print(f"Received response from main thread: {result}")
                    # If main thread returns a tuple, forward as-is; if it's a bool, adapt
                    if isinstance(result, tuple) and len(result) == 2:
                        return result
                    else:
                        return (bool(result), xpath if result else "")
                else:
                    print("Timeout waiting for response from main thread")
                    return False,""
            else:
                print("Execute worker not found or doesn't have element_confirmation_requested signal")
                if execute_worker:
                    print(f"Available attributes: {[attr for attr in dir(execute_worker) if 'element' in attr.lower()]}")
                return False,""
                
        except Exception as e:
            print(f"Error in signal-based element confirmation: {e}")
            import traceback
            print(f"Full traceback: {traceback.format_exc()}")
            return False, ""

# Example usage
# if __name__ == "__main__":
#     # This is just for testing - you would pass actual driver and xpath
#     print("Element confirmation module loaded successfully")