import sys
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtSvg import QSvgRenderer
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from datas.process_flow.desktop_process.verify_desktop_attr import main_desktop_element_picker
import time,os,io,json,threading,traceback,ast

class BlinkingWorker(QObject):
    """Worker thread for element blinking operations (non-blocking)"""
    finished = pyqtSignal()
    error = pyqtSignal(str)
    
    def __init__(self, element, blink_duration=None):
        super().__init__()
        self.element = element
        self.blink_duration = blink_duration  # None = infinite blinking
        self.is_running = False
        self.blink_state = False
        self.stop_requested = False
    
    @pyqtSlot()
    def start_blinking(self):
        """Start blinking the element (runs in worker thread)"""
        try:
            self.is_running = True
            self.stop_requested = False
            start_time = time.time()
            
            while self.is_running and not self.stop_requested:
                try:
                    # Alternate between RED and BLUE
                    color = 0xFF0000 if not self.blink_state else 0x0000FF
                    self._safe_draw_outline(color, 3)
                    self.blink_state = not self.blink_state
                    
                    # Check if duration exceeded
                    if self.blink_duration and (time.time() - start_time) > self.blink_duration:
                        break
                    
                    time.sleep(0.5)  # 500ms blink interval
                except Exception as e:
                    print(f"Error in blink loop: {e}")
                    time.sleep(0.5)
            
            self.is_running = False
            self.finished.emit()
        except Exception as e:
            print(f"Error starting blinking: {e}")
            self.error.emit(str(e))
    
    @pyqtSlot()
    def stop_blinking(self):
        """Stop blinking and clear outline (runs in worker thread)"""
        try:
            self.stop_requested = True
            time.sleep(0.1)  # Let current blink cycle finish
            
            # Clear the outline
            self._safe_draw_outline(0x000000, 0)
            self.is_running = False
            self.finished.emit()
        except Exception as e:
            print(f"Error stopping blinking: {e}")
            self.error.emit(str(e))
    
    def _safe_draw_outline(self, color, thickness):
        """Safely call draw_outline with fallbacks"""
        try:
            if self.element:
                self.element.draw_outline(color, thickness)
        except TypeError:
            try:
                if self.element:
                    self.element.draw_outline(thickness, color)
            except Exception as e:
                print(f"draw_outline failed: {e}")

def resource_path(relative_path):
    """Get absolute path to resource, works for dev and for PyInstaller"""
    if hasattr(sys, "_MEIPASS"):
        return os.path.join(sys._MEIPASS, relative_path)
    return os.path.join(os.path.abspath("."), relative_path)


class SnippingTool(QWidget):
    """Snipping tool for capturing screen regions"""
    
    def __init__(self):
        super().__init__()
        self.start_point = QPoint()
        self.end_point = QPoint()
        self.screenshot = None
        self.captured_region = None
        self.bounds = None  # Store boundary coordinates as [left, right, top, bottom]
        
        # Make window fullscreen and transparent
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setWindowState(Qt.WindowFullScreen)
        
        # Take screenshot of entire screen
        self.take_screenshot()
        
        # Set cursor to crosshair
        self.setCursor(Qt.CrossCursor)
        
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
            self.start_point = event.pos()
            self.end_point = event.pos()
            self.update()
            
    def mouseMoveEvent(self, event):
        """Update selection"""
        if not self.start_point.isNull():
            self.end_point = event.pos()
            self.update()
            
    def mouseReleaseEvent(self, event):
        """Finish selection and capture"""
        if event.button() == Qt.LeftButton and not self.start_point.isNull():
            self.end_point = event.pos()
            self.capture_selection()
            self.close()
            
    def keyPressEvent(self, event):
        """Handle escape key to cancel"""
        if event.key() == Qt.Key_Escape:
            self.captured_region = None
            self.bounds = None  # Clear bounds on cancel
            self.close()
            
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

class DesktopPickerWorker(QObject):
    """Worker thread for desktop element picker."""
    finished = pyqtSignal(object)  # Emits dict or string
    error = pyqtSignal(str)
    
    def __init__(self,target_title,proj_name,task_name,var_name,parent=None):
        super().__init__(parent)
        self.title = target_title
        self.proj_name = proj_name
        self.task_name = task_name
        self.var_name = var_name

    
    @pyqtSlot()
    def run(self):
        """Run the desktop element picker and emit result."""
        try:
            import time
            # QThread.sleep(2) 
            # QApplication.processEvents()
            output_attr = main_desktop_element_picker(self.title,self.proj_name,self.task_name,self.var_name)
            QApplication.processEvents()
            picked = output_attr
            # Handle different return types
            if isinstance(picked, dict):
                # Direct dictionary response
                self.finished.emit(picked)
            elif isinstance(picked, str):
                # String response - try to parse as JSON
                try:
                    import json
                    parsed = json.loads(picked)
                    self.finished.emit(parsed)
                except json.JSONDecodeError:
                    # Not JSON, emit as string
                    self.finished.emit(picked.strip() if picked else "")
            else:
                # Unknown type, convert to string
                self.finished.emit(str(picked) if picked else "")
        except Exception as e:
            import traceback
            error_msg = f"Desktop picker error: {str(e)}\n{traceback.format_exc()}"
            print(error_msg)
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


class DesktopElementConfirmationDialog(QDialog):
    """Standalone element confirmation dialog with safe blinking and enhanced features."""

    def __init__(self, target_title,element, element_name,proj_name,task_name,var_name,app_instance=None, parent=None):
        super().__init__(parent)
        self.element = element
        self.element_name = element_name
        self.title = target_title
        self.app_instance = app_instance
        self.var_name = var_name
        self.result = False
        self.blink_state = False
        self.blinking_timer = None
        self._mouse_pressed = False
        self._mouse_pos = None
        self.proj_name = proj_name
        self.task_name = task_name
        
        # Blinking worker thread
        self.blinking_thread = None
        self.blinking_worker = None
        
        # Bounds blinking state
        self.bounds_blinking_timer = None
        self.bounds_blink_state = False
        self.current_bounds = None
        
        # Mouse pointer blinking state
        self.pointer_blinking_timer = None
        self.pointer_blink_state = False
        self.current_pointer_coords = None
        self.mouse_pointer_overlay = None
        
        # Track verification states
        self.element_verify = False
        self.image_verify = False
        self.coordinate_verify = False
        self._coordinate_picker_running = False
        
        # Track xpaths/data
        self.bound_index_data = ""
        self.coordinate_bound = ""
        self.chosen_data = None
        
        # Project/task info
        self.proj_name = None
        self.task_name = None
        
        self.setupUI()
        
        try:
            self.start_element_blinking_pywinauto()
        except Exception as e:
            print(f"Could not start pywinauto blinking: {e}")
            self.stop_element_blinking_pywinauto()

        self.raise_()
        self.activateWindow()
        
        # Load project info
        try:
            with open("json_info/task_info.json", "r", encoding="utf-8") as f:
                json_info = json.load(f)
            self.proj_name = json_info["Proj_file_name"]
            self.task_name = json_info["Task_file_name"]
        except Exception as e:
            print(f"Could not load task info: {e}")

    def setupUI(self):
        """Setup the confirmation dialog UI with enhanced features."""
        self.setWindowFlags(
            Qt.FramelessWindowHint |
            Qt.WindowStaysOnTopHint |
            Qt.Tool |
            Qt.X11BypassWindowManagerHint
        )
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setAttribute(Qt.WA_ShowWithoutActivating)
        
        # Compact horizontal size
        self.setFixedSize(520, 70)
        
        # Position at bottom left corner
        screen = QApplication.desktop().screenGeometry()
        self.move(20, screen.height() - 160)
        
        # Create main container
        self.container = QWidget(self)
        self.container.setGeometry(0, 0, 520, 70)
        container = self.container
        container.setStyleSheet("""
            QWidget {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                                          stop:0 #2D2D2D, stop:1 #1A1A1A);
                border: 2px solid #00CED1;
                border-radius: 12px;
            }
        """)

        # Main layout
        main_layout = QVBoxLayout(container)
        main_layout.setContentsMargins(15, 12, 15, 12)
        main_layout.setSpacing(8)
        
        # Top row with text and buttons
        top_row = QHBoxLayout()
        top_row.setSpacing(15)
        top_row.setContentsMargins(0, 0, 0, 0)
        
        # Text label
        element_display_desc = self.element_name.replace('_', ' ').replace('field', '').strip().title()
        self.text_label = QLabel(f"Confirm <b>{element_display_desc}</b> Field Highlight")
        self.text_label.setTextFormat(Qt.RichText)
        self.text_label.setStyleSheet("""
            QLabel {
                color: #FFFFFF;
                font-family: 'Segoe UI';
                font-size: 16px;
                background: transparent;
                border: none;
            }
        """)
        self.text_label.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        self.text_label.setWordWrap(True)
        top_row.addWidget(self.text_label, 1)
        
        # Button container
        button_layout = QHBoxLayout()
        button_layout.setSpacing(10)
        button_layout.setContentsMargins(0, 0, 0, 0)
        
        # Delay input
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
        
        # Element picker button (X)
        no_svg_data = b"""
        <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24"
            viewBox="0 0 24 24" fill="none" stroke="#f8f7f7"
            stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
        <path d="M14 4.1 12 6"/>
        <path d="m5.1 8-2.9-.8"/>
        <path d="m6 12-1.9 2"/>
        <path d="M7.2 2.2 8 5.1"/>
        <path d="M9.037 9.69a.498.498 0 0 1 .653-.653l11 4.5a.5.5 0 0 1-.074.949l-4.349 1.041a1 1 0 0 0-.74.739l-1.04 4.35a.5.5 0 0 1-.95.074z"/>
        </svg>
        """
        no_renderer = QSvgRenderer(QByteArray(no_svg_data))
        no_pixmap = QPixmap(32, 32)
        no_pixmap.fill(Qt.transparent)
        painter = QPainter(no_pixmap)
        no_renderer.render(painter)
        painter.end()

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
            QPushButton:hover { background: rgba(255, 255, 255, 0.1); }
            QPushButton:pressed { background: rgba(255, 255, 255, 0.2); }
        """)
        no_btn.setCursor(Qt.PointingHandCursor)
        no_btn.setToolTip("Pick element (X)")
        no_btn.clicked.connect(self.on_element_picker_clicked)
        self.no_btn = no_btn
        
        # Coordinate picker button
        coord_svg_data = b"""
        <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24"
            viewBox="0 0 24 24" fill="none" stroke="#f8f7f7"
            stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
        <path d="M12.034 12.681a.498.498 0 0 1 .647-.647l9 3.5a.5.5 0 0 1-.033.943l-3.444 1.068a1 1 0 0 0-.66.66l-1.067 3.443a.5.5 0 0 1-.943.033z"/>
        <path d="M5 17A12 12 0 0 1 17 5"/>
        <circle cx="19" cy="5" r="2"/>
        <circle cx="5" cy="19" r="2"/>
        </svg>
        """
        coord_renderer = QSvgRenderer(QByteArray(coord_svg_data))
        coord_pixmap = QPixmap(32, 32)
        coord_pixmap.fill(Qt.transparent)
        painter = QPainter(coord_pixmap)
        coord_renderer.render(painter)
        painter.end()

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
            QPushButton:hover { background: rgba(255, 255, 255, 0.1); }
            QPushButton:pressed { background: rgba(255, 255, 255, 0.2); }
        """)
        coord_btn.setCursor(Qt.PointingHandCursor)
        coord_btn.setToolTip("Pick coordinates")
        coord_btn.clicked.connect(self.on_coordinate_clicked)
        self.coord_btn = coord_btn

        # Image picker button
        img_svg_data = b"""
        <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" 
             viewBox="0 0 24 24" fill="none" stroke="#f8f7f7" 
             stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <path d="M15 15.003a1 1 0 0 1 1.517-.859l4.997 2.997a1 1 0 0 1 0 1.718l-4.997 2.997a1 1 0 0 1-1.517-.86z"/>
            <path d="M21 12.17V5a2 2 0 0 0-2-2H5a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h6"/>
            <path d="m6 21 5-5"/>
            <circle cx="9" cy="9" r="2"/>
        </svg>
        """
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
            QPushButton:hover { background: rgba(255, 255, 255, 0.1); }
            QPushButton:pressed { background: rgba(255, 255, 255, 0.2); }
        """)
        img_picker.setCursor(Qt.PointingHandCursor)
        img_picker.setToolTip("Image Picker")
        img_picker.clicked.connect(self.on_image_clicked)
        self.img_picker = img_picker
        
        # Yes button
        yes_svg_data = b"""
        <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24"
            viewBox="0 0 24 24" fill="none" stroke="#f8f7f7"
            stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
        <path d="M20 6 9 17l-5-5"/>
        </svg>
        """
        yes_renderer = QSvgRenderer(QByteArray(yes_svg_data))
        yes_pixmap = QPixmap(32, 32)
        yes_pixmap.fill(Qt.transparent)
        painter = QPainter(yes_pixmap)
        yes_renderer.render(painter)
        painter.end()

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
            QPushButton:hover { background: rgba(255, 255, 255, 0.1); }
            QPushButton:pressed { background: rgba(255, 255, 255, 0.2); }
        """)
        yes_btn.setCursor(Qt.PointingHandCursor)
        yes_btn.setToolTip("Yes - Element is correct")
        yes_btn.clicked.connect(self.on_yes_clicked)
        self.yes_btn = yes_btn
        
        # Dropdown button for custom input
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
        dropdown_btn.setToolTip("Paste custom data and check")
        dropdown_btn.clicked.connect(self.toggle_input_panel)
        self.dropdown_btn = dropdown_btn
        
        # Add buttons to layout
        button_layout.addWidget(self.delay_edit)
        button_layout.addWidget(no_btn)
        button_layout.addWidget(coord_btn)
        button_layout.addWidget(img_picker)
        button_layout.addWidget(yes_btn)
        button_layout.addWidget(dropdown_btn)
        
        top_row.addLayout(button_layout)
        main_layout.addLayout(top_row)
        
        # Input panel (hidden by default)
        self.input_panel = QWidget(container)
        input_layout = QHBoxLayout(self.input_panel)
        input_layout.setContentsMargins(0, 0, 0, 0)
        input_layout.setSpacing(8)
        
        self.data_edit = QLineEdit()
        self.data_edit.setPlaceholderText("Enter your data here")
        self.data_edit.setStyleSheet("""
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
        
        input_layout.addWidget(self.data_edit, 1)
        input_layout.addWidget(check_btn)
        self.input_panel.setVisible(False)
        main_layout.addWidget(self.input_panel)
        
        # Fade-in animation
        self.fade_effect = QGraphicsOpacityEffect()
        container.setGraphicsEffect(self.fade_effect)
        
        self.fade_animation = QPropertyAnimation(self.fade_effect, b"opacity")
        self.fade_animation.setDuration(300)
        self.fade_animation.setStartValue(0.0)
        self.fade_animation.setEndValue(1.0)
        self.fade_animation.setEasingCurve(QEasingCurve.OutCubic)
        self.fade_animation.start()
        
        # Pulsing glow effect
        self.glow_timer = QTimer()
        self.glow_timer.timeout.connect(self.toggle_glow)
        self.glow_timer.start(800)
        self.glow_state = False
    
    def toggle_glow(self):
        """Toggle glow effect for attention."""
        try:
            container = self.container
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
        """Show/Hide the custom input panel and adjust height."""
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
        """Apply user-entered data."""
        try:
            text = self.data_edit.text().strip() if hasattr(self, 'data_edit') else ''
            if not text:
                self.data_edit.setStyleSheet(self.data_edit.styleSheet() + "\nQLineEdit { border-color: #ff6b6b; }")
                QTimer.singleShot(600, lambda: self.data_edit.setStyleSheet(self.data_edit.styleSheet().replace("border-color: #ff6b6b;", "border-color: #00CED1;")))
                return
            # Store the custom data
            self.chosen_data = text
        except Exception as e:
            print(f"Error on check clicked: {e}")

    def mousePressEvent(self, event):
        """Handle mouse press for dragging."""
        if event.button() == Qt.LeftButton:
            self._mouse_pressed = True
            self._mouse_pos = event.globalPos() - self.pos()
            event.accept()

    def mouseMoveEvent(self, event):
        """Handle mouse move for dragging."""
        if self._mouse_pressed and self._mouse_pos:
            self.move(event.globalPos() - self._mouse_pos)
            event.accept()

    def mouseReleaseEvent(self, event):
        """Handle mouse release."""
        if event.button() == Qt.LeftButton:
            self._mouse_pressed = False
            event.accept()

    def start_element_blinking_pywinauto(self):
        """Start blinking using worker thread (non-blocking)."""
        try:
            # Stop any existing blinking thread
            self.stop_element_blinking_pywinauto()
            
            # Create and start blinking worker thread
            self.blinking_thread = QThread()
            self.blinking_worker = BlinkingWorker(self.element)
            self.blinking_worker.moveToThread(self.blinking_thread)
            
            # Connect signals
            self.blinking_thread.started.connect(self.blinking_worker.start_blinking)
            self.blinking_worker.finished.connect(self.blinking_thread.quit)
            self.blinking_worker.error.connect(self._on_blinking_error)
            
            # Cleanup when thread finishes
            self.blinking_thread.finished.connect(self.blinking_thread.deleteLater)
            self.blinking_worker.finished.connect(self.blinking_worker.deleteLater)
            
            # Start the thread
            self.blinking_thread.start()
            print(f"[BLINKING] Started element blinking worker thread for {self.element_name}")
        except Exception as e:
            print(f"Error starting pywinauto blinking: {e}")
            traceback.print_exc()

    def toggle_element_highlight_pywinauto(self):
        """Deprecated - Now handled by worker thread"""
        pass

    @pyqtSlot(str)
    def _on_blinking_error(self, error_msg):
        """Handle blinking worker error"""
        try:
            element_display_desc = self.element_name.replace('_', ' ').replace('field', '').strip().title()
            self.text_label.setText(f"</b>Unable to Find <b>{element_display_desc}</b>. Please select the field</b>")
            print(f"Blinking error: {error_msg}")
        except Exception as e:
            print(f"Error handling blinking error: {e}")

    def stop_element_blinking_pywinauto(self):
        """Stop blinking and clear the outline (worker thread safe)."""
        try:
            # Stop the worker thread if running
            if self.blinking_worker and self.blinking_thread:
                # Request worker to stop blinking
                if self.blinking_thread.isRunning():
                    # Signal worker to stop
                    QTimer.singleShot(0, self.blinking_worker.stop_blinking)
                    # Wait for thread to finish (max 2 seconds)
                    if not self.blinking_thread.wait(2000):
                        print("[BLINKING] Warning: Blinking thread did not stop gracefully")
                        self.blinking_thread.terminate()
                        self.blinking_thread.wait()
                
                self.blinking_thread = None
                self.blinking_worker = None
            
            print(f"[BLINKING] Stopped element blinking for {self.element_name}")
        except Exception as e:
            print(f"Error stopping pywinauto blinking: {e}")
            traceback.print_exc()

    def _safe_draw_outline(self, color, thickness):
        """Safely call draw_outline with multiple fallbacks (pywinauto version)."""
        try:
            self.element.draw_outline(color, thickness)
        except TypeError:
            try:
                self.element.draw_outline(thickness, color)
            except Exception as e:
                print(f"draw_outline failed: {e}")

    def start_bounds_blinking(self, bounds_data):
        """Start blinking the bounds region with blue highlight."""
        try:
            if not bounds_data or len(bounds_data) != 4:
                print("Invalid bounds data for blinking")
                return
            
            self.current_bounds = bounds_data
            self.bounds_blinking_timer = QTimer()
            self.bounds_blinking_timer.timeout.connect(self.toggle_bounds_highlight)
            self.bounds_blinking_timer.start(500)
            print(f"Started blinking for bounds: {bounds_data}")
        except Exception as e:
            print(f"Error starting bounds blinking: {e}")

    def toggle_bounds_highlight(self):
        """Toggle bounds region highlight overlay on screen."""
        try:
            if not hasattr(self, 'current_bounds') or not self.current_bounds:
                return
            
            if self.bounds_blink_state:
                if hasattr(self, 'bounds_highlight_overlay') and self.bounds_highlight_overlay is not None:
                    self.bounds_highlight_overlay.hide()
            else:
                if not hasattr(self, 'bounds_highlight_overlay') or self.bounds_highlight_overlay is None:
                    self.bounds_highlight_overlay = BoundsHighlightOverlay(self.current_bounds)
                self.bounds_highlight_overlay.show()
                self.bounds_highlight_overlay.raise_()
            
            self.bounds_blink_state = not self.bounds_blink_state
        except Exception as e:
            print(f"Error toggling bounds highlight: {e}")

    def stop_bounds_blinking(self):
        """Stop blinking the bounds region and remove highlight overlay."""
        try:
            if hasattr(self, 'bounds_blinking_timer') and self.bounds_blinking_timer is not None:
                self.bounds_blinking_timer.stop()
                self.bounds_blinking_timer = None

            if hasattr(self, 'bounds_highlight_overlay') and self.bounds_highlight_overlay is not None:
                try:
                    self.bounds_highlight_overlay.hide()
                    self.bounds_highlight_overlay.close()
                    self.bounds_highlight_overlay.deleteLater()
                except Exception:
                    pass
                self.bounds_highlight_overlay = None

            self.bounds_blink_state = False
            print("Stopped bounds blinking")
        except Exception as e:
            print(f"Error stopping bounds blinking: {e}")

    def start_pointer_blinking(self, x, y):
        """Start blinking the mouse pointer position with royal blue X mark."""
        try:
            if x is None or y is None:
                print("Invalid coordinates for pointer blinking")
                return
            
            self.current_pointer_coords = (x, y)
            self.pointer_blinking_timer = QTimer()
            self.pointer_blinking_timer.timeout.connect(self.toggle_pointer_highlight)
            self.pointer_blinking_timer.start(500)
            print(f"Started blinking for mouse pointer at: ({x}, {y})")
        except Exception as e:
            print(f"Error starting pointer blinking: {e}")

    def toggle_pointer_highlight(self):
        """Toggle mouse pointer X mark overlay on screen."""
        try:
            if not hasattr(self, 'current_pointer_coords') or not self.current_pointer_coords:
                return
            
            x, y = self.current_pointer_coords
            
            if self.pointer_blink_state:
                if hasattr(self, 'mouse_pointer_overlay') and self.mouse_pointer_overlay is not None:
                    self.mouse_pointer_overlay.hide()
            else:
                if not hasattr(self, 'mouse_pointer_overlay') or self.mouse_pointer_overlay is None:
                    self.mouse_pointer_overlay = MousePointerOverlay(x, y)
                self.mouse_pointer_overlay.show()
                self.mouse_pointer_overlay.raise_()
            
            self.pointer_blink_state = not self.pointer_blink_state
        except Exception as e:
            print(f"Error toggling pointer highlight: {e}")

    def stop_pointer_blinking(self):
        """Stop blinking the mouse pointer and remove X mark overlay."""
        try:
            if hasattr(self, 'pointer_blinking_timer') and self.pointer_blinking_timer is not None:
                self.pointer_blinking_timer.stop()
                self.pointer_blinking_timer = None

            if hasattr(self, 'mouse_pointer_overlay') and self.mouse_pointer_overlay is not None:
                try:
                    self.mouse_pointer_overlay.hide()
                    self.mouse_pointer_overlay.close()
                    self.mouse_pointer_overlay.deleteLater()
                except Exception:
                    pass
                self.mouse_pointer_overlay = None

            self.pointer_blink_state = False
            print("Stopped pointer blinking")
        except Exception as e:
            print(f"Error stopping pointer blinking: {e}")

    def on_element_picker_clicked(self):
        """Handle element picker button click."""
        try:
            delay = 0
            if hasattr(self, 'delay_edit') and self.delay_edit is not None:
                s = self.delay_edit.text().strip()
                if s !="":
                    delay = int(s) if s.isdigit() else 0
            if delay > 0:
                self.start_countdown(delay, self._run_element_picker)
            else:
                self.stop_bounds_blinking()
                self.stop_pointer_blinking()
                self._run_element_picker()
        except Exception as e:
            print(f"Error handling element picker click: {e}")

    def on_coordinate_clicked(self):
        """Handle coordinate picker button click."""
        try:
            delay = 0
            if hasattr(self, 'delay_edit') and self.delay_edit is not None:
                s = self.delay_edit.text().strip()
                delay = int(s) if s.isdigit() else 0
            if delay > 0:
                self.start_countdown_coordinate(delay)
            else:
                self._run_coordinate_picker()
        except Exception as e:
            print(f"Error handling coordinate click: {e}")
    
    def start_countdown(self, seconds, callback):
        """Start countdown overlay before action."""
        try:
            self.countdown_overlay = CountdownOverlay(seconds)
            self.countdown_overlay.finished.connect(callback)
            self.countdown_overlay.show()
        except Exception as e:
            print(f"Error starting countdown: {e}")
            callback()
    
    def start_countdown_coordinate(self, seconds):
        """Start countdown for coordinate picker."""
        self.start_countdown(seconds, self._run_coordinate_picker)

    def _run_element_picker(self):
        """Run desktop element picker using threaded worker."""
        try:
            # Prevent starting multiple pickers simultaneously
            if getattr(self, '_picker_thread', None):
                return
            from PyQt5.QtCore import QThread
            self._picker_thread = QThread()
            self._picker_worker = DesktopPickerWorker(self.title, self.proj_name, self.task_name, self.var_name)
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

            # self._set_ui_busy(True)
            self._picker_thread.start()
        except Exception as e:
            print(f"Error starting picker thread: {e}")

    def _clear_picker_thread(self):
        """Clear picker thread references."""
        try:
            if hasattr(self, '_picker_thread') and self._picker_thread is not None:
                self._picker_thread.deleteLater()
        except Exception:
            pass
        self._picker_thread = None
        self._picker_worker = None
        # self._set_ui_busy(False)

    @pyqtSlot(object)
    def _on_picker_finished(self, picked_data):
        """Handle desktop element picker result."""
        try:
            # Check if it's a valid element dictionary or error message
            if isinstance(picked_data, dict):
                if picked_data.get("status") == "No element clicked.":
                    print("No element was clicked")
                    return
                # Valid element data received
                self.element_verify = True
                self.image_verify = False
                self.coordinate_verify = False
                self.chosen_data = picked_data
                
                # Display element info in input field if available
                try:
                    if hasattr(self, 'data_edit') and self.data_edit is not None:
                        # Show a summary of the picked element
                        element_info = picked_data.get('control_type', 'Unknown')
                        if 'name' in picked_data and picked_data['name']:
                            element_info = f"{picked_data['name']} ({element_info})"
                        self.data_edit.setText(str(picked_data))
                        
                        # Update label to show success
                        # if hasattr(self, 'text_label'):
                            # self.text_label.setText(f"<b>Selected:</b> {element_info}")
                except Exception as e:
                    print(f"Error updating UI with picked element: {e}")
            
            elif isinstance(picked_data, str):
                import ast
                picked_data=ast.literal_eval(picked_data)
                # Check if it's a valid element dictionary or error message
                # if picked_data.get("status") == "No element clicked.":
                #     print("No element was clicked")
                #     return
                # Valid element data received
                self.element_verify = True
                self.image_verify = False
                self.coordinate_verify = False
                self.chosen_data = picked_data
                
                # Display element info in input field if available
                try:
                    # if hasattr(self, 'data_edit') and self.data_edit is not None:
                    #     # Show a summary of the picked element
                    #     element_info = picked_data.get('control_type', 'Unknown')
                    #     if 'name' in picked_data and picked_data['name']:
                    #         element_info = f"{picked_data['name']} ({element_info})"
                    self.data_edit.setText(str(picked_data))
                        
                        # Update label to show success
                        # if hasattr(self, 'text_label'):
                            # self.text_label.setText(f"<b>Selected:</b> {element_info}")
                except Exception as e:
                    print(f"Error updating UI with picked element: {e}")
        except Exception as e:
            print(f"Error handling picker result: {e}")

    @pyqtSlot(str)
    def _on_picker_error(self, msg: str):
        """Handle picker error."""
        print(f"Desktop picker error: {msg}")

    def _run_coordinate_picker(self):
        """Run coordinate picker using QTimer to avoid blocking dialog's exec_()."""
        try:
            if getattr(self, '_coordinate_picker_running', False):
                return
            
            self._coordinate_picker_running = True
            # self._set_ui_busy(True)
            
            # Stop element blinking
            self.stop_element_blinking_pywinauto()
            try:
                self.stop_bounds_blinking()
            except:
                pass
            try:
                self.stop_pointer_blinking()
            except:
                pass
            
            # Stop glow timer
            if hasattr(self, 'glow_timer'):
                self.glow_timer.stop()
            
            # Lower dialog so picker appears on top
            self.lower()
            QApplication.processEvents()
            QApplication.processEvents()
            
            # Use QTimer to defer coordinate picker execution
            QTimer.singleShot(200, self._execute_coordinate_picker)
        except Exception as e:
            import traceback
            print(f"Error setting up coordinate picker: {e}")
            print(traceback.format_exc())
            self._coordinate_picker_running = False
            # self._set_ui_busy(False)
            self.show()
            self.raise_()
    
    def _execute_coordinate_picker(self):
        """Actually execute the coordinate picker - called via QTimer."""
        try:
            try:
                self.stop_element_blinking_pywinauto()
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
            
            bound_index = None
            try:
                from coordinate_element_picker import select_element
                print("Starting coordinate picker...")
                bound_index = select_element()
                if hasattr(self, 'data_edit') and self.data_edit is not None:
                    self.data_edit.setText(str(bound_index))
                if type(bound_index) == list and len(bound_index) == 2:
                    x, y = bound_index
                    self.coordinate_bound = bound_index
                    self.start_pointer_blinking(x, y)
                    self.coordinate_verify = True
                    self.element_verify = False
                    self.image_verify = False
                print(f"Coordinate picker returned: {bound_index}")
            except Exception as e:
                import traceback
                print(f"Coordinate picker error: {e}")
                print(traceback.format_exc())
            
            QApplication.processEvents()
            QTimer.singleShot(50, lambda: self._restore_dialog_after_picker(bound_index))
        except Exception as e:
            import traceback
            print(f"Error executing coordinate picker: {e}")
            print(traceback.format_exc())
            self._restore_dialog_after_picker(None)
    
    def _restore_dialog_after_picker(self, bound_index):
        """Restore dialog after coordinate picker completes."""
        try:
            print("Restoring dialog after coordinate picker...")
            
            self.setEnabled(True)
            self.raise_()
            self.activateWindow()
            
            QApplication.processEvents()
            self.setFocus(Qt.ActiveWindowFocusReason)
            self.raise_()
            self.activateWindow()
            QApplication.processEvents()
            
            if hasattr(self, 'glow_timer'):
                self.glow_timer.start(800)
            
            if bound_index and isinstance(bound_index, list) and len(bound_index) == 2:
                print(f"Coordinate picker returned valid bounds: {bound_index}")
                self._on_coordinate_finished(bound_index)
            else:
                print("Invalid bounds returned from coordinate picker or user cancelled")
            
            QApplication.processEvents()
            
            if not self.isEnabled():
                print("WARNING: Dialog not enabled, restoring...")
                self.setEnabled(True)
            if not self.isVisible():
                print("WARNING: Dialog not visible, restoring...")
                self.show()
                self.raise_()
                self.activateWindow()
            
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
            self._coordinate_picker_running = False
            # self._set_ui_busy(False)
            QApplication.processEvents()
            print("Coordinate picker cleanup complete, dialog should remain open")

    def _on_coordinate_finished(self, bounds: list):
        """Handle coordinate picker result - auto-populate input field and keep dialog open."""
        try:
            if bounds and len(bounds) == 2:
                x, y = bounds
                bounds_str = f"[{x}, {y}]"
                
                self.chosen_data = bounds_str
                
                try:
                    if hasattr(self, 'data_edit') and self.data_edit is not None:
                        self.data_edit.setText(bounds_str)
                        
                        if not self.input_panel.isVisible():
                            self.toggle_input_panel()
                        
                        self.data_edit.setFocus()
                        self.data_edit.selectAll()
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

    def on_image_clicked(self):
        """Handle image picker button click."""
        try:
            self.hide()
            QApplication.processEvents()
            time.sleep(0.5)
            
            try:
                self.stop_element_blinking_pywinauto()
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
            snipping_tool = SnippingTool()
            snipping_tool.show()
            
            while snipping_tool.isVisible():
                QApplication.processEvents()
            
            if snipping_tool.captured_region is not None:
                images_dir = f"{self.proj_name}/{self.task_name}/images"
                if not os.path.exists(images_dir):
                    os.makedirs(images_dir)
                
                filename = f"{self.var_name}.png"
                filepath = os.path.join(images_dir, filename)
                snipping_tool.captured_region.save(filepath)
                
                bounds_data = snipping_tool.bounds
                if bounds_data:
                    print(f"Captured bounds: Left={bounds_data[0]}, Right={bounds_data[1]}, Top={bounds_data[2]}, Bottom={bounds_data[3]}")
                    self.bound_index_data = bounds_data
                    self.start_bounds_blinking(bounds_data)
                    
                    import json
                    metadata = {
                        "filename": filename,
                        "bounds": {
                            "left": bounds_data[0],
                            "right": bounds_data[1],
                            "top": bounds_data[2],
                            "bottom": bounds_data[3],
                            "width": bounds_data[1] - bounds_data[0],
                            "height": bounds_data[3] - bounds_data[2]
                        }
                    }
                
                self.coordinate_verify = False
                self.element_verify = False
                self.image_verify = True
                
                try:
                    self.stop_pointer_blinking()
                except:
                    pass
                
                if hasattr(self, 'data_edit') and self.data_edit is not None:
                    self.data_edit.setText(filename)
                
                self.chosen_data = filename
            else:
                from PyQt5.QtWidgets import QMessageBox
                QMessageBox.information(self, "Info", "No region selected.")
                print("No region selected")
            
            self.show()
            self.raise_()
            self.activateWindow()
            
            if hasattr(self, 'glow_timer') and not self.glow_timer.isActive():
                self.glow_timer.start(800)
            
            QApplication.processEvents()
            self.setFocus(Qt.ActiveWindowFocusReason)
            self.wait_for_user_confirmation()
            
            print("Dialog restored after image capture, waiting for user to click Yes")
        except Exception as e:
            import traceback
            print(f"Error in on_image_clicked: {e}")
            traceback.print_exc()
            try:
                self.show()
                self.raise_()
                self.activateWindow()
            except:
                pass

    def _set_ui_busy(self, busy: bool):
        """Enable/disable UI elements during operations."""
        try:
            for w in [getattr(self, 'no_btn', None), getattr(self, 'coord_btn', None),
                      getattr(self, 'yes_btn', None), getattr(self, 'dropdown_btn', None), 
                      getattr(self, 'check_btn', None), getattr(self, 'delay_edit', None),
                      getattr(self, 'img_picker', None)]:
                if w is not None:
                    w.setEnabled(not busy)
            if busy:
                QApplication.setOverrideCursor(Qt.WaitCursor)
            else:
                QApplication.restoreOverrideCursor()
        except Exception:
            pass

    def wait_for_user_confirmation(self):
        """Wait for user to click Yes button before returning."""
        try:
            from PyQt5.QtCore import QEventLoop
            loop = QEventLoop()
            self.accepted.connect(loop.quit)
            self.rejected.connect(loop.quit)
            print("Waiting for user to confirm (click Yes button)...")
            loop.exec_()
            print("User confirmation received, continuing...")
        except Exception as e:
            import traceback
            print(f"Error in wait_for_user_confirmation: {e}")
            traceback.print_exc()

    def on_yes_clicked(self):
        """Handle Yes button click."""
        if getattr(self, '_coordinate_picker_running', False):
            print("Coordinate picker is running, cannot close dialog yet")
            return
            
        self.result = True
        try:
            typed = ''
            if hasattr(self, 'data_edit') and self.data_edit is not None:
                typed = self.data_edit.text().strip()
            
            if getattr(self, 'element_verify', False):
                # Element picker was used
                self.chosen_data = typed or self.element
            elif getattr(self, 'coordinate_verify', False):
                # Coordinate picker was used
                import ast
                self.chosen_data = ast.literal_eval(typed) if typed else None
            elif getattr(self, 'image_verify', False):
                # Image picker was used
                self.chosen_data = typed
            else:
                # No picker used; return typed if present else original element
                self.chosen_data = typed if typed else self.element
        except Exception as e:
            print(f"Error processing chosen data: {e}")
            self.chosen_data = self.element
        try:
            if getattr(self, '_coordinate_picker_running', False):
                print("Cannot close dialog while coordinate picker is running")
                return
            
            if hasattr(self, 'fade_animation'):
                self.fade_animation.stop()
            
            if hasattr(self, 'glow_timer'):
                self.glow_timer.stop()
            
            self.stop_element_blinking_pywinauto()
            self.stop_bounds_blinking()
            self.stop_pointer_blinking()
            
            self.accept()
        except:
            import traceback
            traceback.print_exc()

        # self.cleanup_and_close()

    def cleanup_and_close(self):
        """Clean up resources and close dialog."""
        if getattr(self, '_coordinate_picker_running', False):
            print("Cannot close dialog while coordinate picker is running")
            return
        
        if hasattr(self, 'fade_animation'):
            self.fade_animation.stop()
        
        if hasattr(self, 'glow_timer'):
            self.glow_timer.stop()
        
        self.stop_element_blinking_pywinauto()
        self.stop_bounds_blinking()
        self.stop_pointer_blinking()
        
        self.accept()

    def closeEvent(self, event):
        """Handle close event - prevent closing while coordinate picker is running."""
        if getattr(self, '_coordinate_picker_running', False):
            print("Preventing dialog close while coordinate picker is running")
            event.ignore()
            return
        self.cleanup_and_close()
        event.accept()
        
def desktop_element_status(dlg,element_attr,var_name):
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
    with open("json_info/task_info.json", "r", encoding="utf-8") as f:
            json_info = json.load(f)
    proj_name=json_info["Proj_file_name"]
    task_name=json_info["Task_file_name"]
    element_name=var_name
    # Check if we're running in a worker thread
    import threading
    current_thread = threading.current_thread()
    
    # If we're in the main thread, show dialog directly
    if current_thread.name == 'MainThread':
        
        app = QApplication.instance()
        if app is None:
            app = QApplication(sys.argv)

        loop = QEventLoop()
        result = {}
        target_title = dlg.window_text()
        def show_dialog():
            # NOTE: This part assumes 'dlg' can find the element without full ancestor path
            element_wrapper = dlg.child_window(**element_attr)
            dialog = DesktopElementConfirmationDialog(target_title,element_wrapper, element_name,proj_name,task_name,var_name)
            
            dialog.exec_()
            result["value"] = dialog.result
            result["attrs_json"] = dialog.chosen_data
            print(result["attrs_json"])
            if dialog.result and dialog.chosen_data is not None:
                result["attrs_json"] = dialog.chosen_data
            else:
                result["attrs_json"] = element_attr
            loop.quit()

        QTimer.singleShot(0, show_dialog)
        loop.exec_()
        # data="{'current_element': {'name': 'Host:', 'control_type': 'Edit', 'class_name': 'Edit', 'auto_id': '-31832', 'value': 'Host:', 'handle': '3541830', 'process_id': '37776', 'rectangle': {'left': 57, 'top': 109, 'right': 215, 'bottom': 142, 'width': 158, 'height': 33}}, 'ancestors': [{'name': 'Desktop 1', 'control_type': 'Pane', 'class_name': '#32769', 'auto_id': '', 'value': 'Desktop 1', 'handle': '65548', 'process_id': '1116', 'rectangle': {'left': 0, 'top': 0, 'right': 1920, 'bottom': 1080, 'width': 1920, 'height': 1080}}, {'name': 'FileZilla', 'control_type': 'Window', 'class_name': 'wxWindowNR', 'auto_id': '', 'value': 'FileZilla', 'handle': '3474634', 'process_id': '37776', 'rectangle': {'left': -11, 'top': -11, 'right': 1931, 'bottom': 1019, 'width': 1942, 'height': 1030}}, {'name': 'panel', 'control_type': 'Pane', 'class_name': 'wxWindowNR', 'auto_id': '-31834', 'value': 'panel', 'handle': '2558452', 'process_id': '37776', 'rectangle': {'left': 0, 'top': 102, 'right': 1920, 'bottom': 148, 'width': 1920, 'height': 46}}], 'siblings': {'previous_sibling': {'name': 'Host:', 'control_type': 'Text', 'class_name': 'Static', 'auto_id': '5999', 'value': 'Host:', 'handle': '9898784', 'process_id': '37776', 'rectangle': {'left': 5, 'top': 113, 'right': 48, 'bottom': 139, 'width': 43, 'height': 26}}, 'next_sibling': {'name': 'Username:', 'control_type': 'Text', 'class_name': 'Static', 'auto_id': '5999', 'value': 'Username:', 'handle': '920398', 'process_id': '37776', 'rectangle': {'left': 229, 'top': 113, 'right': 313, 'bottom': 139, 'width': 84, 'height': 26}}}, 'screenshot': 'proj_51\\\\task_80\\\\desktop\\\\images\\\\host_name.png', 'timestamp': '20251121_190216'}"
        return result.get("value", False),result["attrs_json"]

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
                
                # Emit signal to main thread
                execute_worker.element_confirmation_requested.emit(element_attr, dlg)
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
                        return (bool(result), element_attr if result else "")
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