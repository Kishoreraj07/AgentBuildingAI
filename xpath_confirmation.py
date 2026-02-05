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

LOG_FILE = "xpath_element_confirmation.txt"

def log_action(message):
    """Log action to both console and file with timestamp"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
    log_message = f"[{timestamp}] {message}"
    print(log_message)
    try:
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write(log_message + "\n")
    except Exception as e:
        print(f"Error writing to log file: {e}")

# Keep a strong reference to a single QApplication to avoid GC-related loss
_APP_SINGLETON = None

def resource_path(relative_path):
    """Get absolute path to resource, works for dev and for PyInstaller"""
    if hasattr(sys, "_MEIPASS"):
        return os.path.join(sys._MEIPASS, relative_path)
    return os.path.join(os.path.abspath("."), relative_path)


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


class XPathConfirmationDialog(QDialog):
    """Standalone XPath confirmation dialog with element picker only"""
    
    def __init__(self, label_text, driver, app_instance, parent=None):
        super().__init__(parent)
        log_action(f"XPathConfirmationDialog: Initializing with label_text='{label_text}'")
        self.label_text = label_text
        self.app_instance = app_instance
        self.driver = driver
        self.result = False
        self.chosen_xpath = ""
        self.blinking_timer = None
        self.blink_state = False
        self._force_close = False
        
        # Track current xpath and chosen return value
        self.current_xpath = None
        self.main_xpath = None
        self.element_verify = False
        self._initialization_complete = False
        
        # Build UI
        try:
            log_action("XPathConfirmationDialog: setupUI starting")
            self.setupUI()
            log_action("XPathConfirmationDialog: setupUI completed")
        except Exception as e:
            log_action(f"XPathConfirmationDialog: setupUI error: {e}")
            raise
        
        # Show the dialog immediately after setupUI
        self.setVisible(True)
        self.show()
        log_action("XPathConfirmationDialog: Dialog shown")
        
        # Process events to ensure dialog is rendered
        QApplication.processEvents()
        
        # Ensure dialog stays independent
        self.raise_()
        self.activateWindow()
        QApplication.processEvents()
        log_action("XPathConfirmationDialog: Dialog raised and activated")
        
        # Mark initialization as complete
        self._initialization_complete = True
        log_action("XPathConfirmationDialog: Initialization complete, dialog ready for user interaction")
        
        # Re-assert visibility/foreground shortly after init
        try:
            QTimer.singleShot(0, self._ensure_foreground)
            QTimer.singleShot(250, self._ensure_foreground)
        except Exception as e:
            log_action(f"XPathConfirmationDialog: Error scheduling foreground ensure: {e}")

    def _ensure_foreground(self):
        """Ensure the dialog is visible, on-screen and foreground."""
        try:
            screen_geom = QApplication.primaryScreen().availableGeometry()
            w = self.width() or 600
            h = self.height() or 70
            x = (screen_geom.width() - w) // 2
            y = screen_geom.height() - h - 70
            self.move(x, y)

            if self.isMinimized():
                self.showNormal()
            self.setVisible(True)
            self.show()
            self.raise_()
            self.activateWindow()
            log_action("XPathConfirmationDialog: _ensure_foreground executed")
        except Exception as e:
            log_action(f"XPathConfirmationDialog: _ensure_foreground error: {e}")
        
    def setupUI(self):
        """Setup the confirmation dialog UI with only element picker and proceed buttons"""
        # Make dialog standalone and independent
        self.setWindowFlags(
            Qt.FramelessWindowHint | 
            Qt.WindowStaysOnTopHint |
            Qt.Tool |
            Qt.X11BypassWindowManagerHint
        )
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setAttribute(Qt.WA_ShowWithoutActivating)

        # Compact size with text and buttons
        self.setFixedSize(600, 70)
        
        # Position at bottom center
        screen = QApplication.desktop().screenGeometry()
        window_width = self.frameGeometry().width()
        window_height = self.frameGeometry().height()
        x = (screen.width() - window_width) // 2
        y = screen.height() - window_height - 70
        self.move(x, y)
        
        # Add dragging support
        self._mouse_pressed = False
        self._mouse_pos = None

        # Create main container with rounded corners
        self.container = QWidget(self)
        self.container.setGeometry(0, 0, 600, 70)
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
        
        top_row = QHBoxLayout()
        top_row.setSpacing(15)
        top_row.setContentsMargins(0, 0, 0, 0)
        
        # Add text label with the provided label_text
        self.text_label = QLabel(self.label_text)
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
        top_row.addWidget(self.text_label, 1)
        
        # Button container on the right - ONLY element picker and proceed buttons
        button_layout = QHBoxLayout()
        button_layout.setSpacing(10)
        button_layout.setContentsMargins(0, 0, 0, 0)
        
        # Delay seconds input near picker button
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
        
        # Element picker button (only button besides proceed)
        picker_svg_data = b"""
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

        picker_renderer = QSvgRenderer(QByteArray(picker_svg_data))
        picker_pixmap = QPixmap(32, 32)
        picker_pixmap.fill(Qt.transparent)
        painter = QPainter(picker_pixmap)
        picker_renderer.render(painter)
        painter.end()

        picker_btn = QPushButton()
        picker_btn.setFixedSize(32, 32)
        picker_btn.setIcon(QIcon(picker_pixmap))
        picker_btn.setIconSize(QSize(24, 24))
        picker_btn.setStyleSheet("""
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
        picker_btn.setCursor(Qt.PointingHandCursor)
        picker_btn.setToolTip("Element Picker")
        picker_btn.clicked.connect(self.on_picker_clicked)
        self.picker_btn = picker_btn
        
        # Proceed button (Yes/Tick)
        proceed_svg_data = b"""
        <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24"
            viewBox="0 0 24 24" fill="none" stroke="#f8f7f7"
            stroke-width="2" stroke-linecap="round" stroke-linejoin="round"
            class="lucide lucide-check-icon lucide-check">
        <path d="M20 6 9 17l-5-5"/>
        </svg>
        """

        proceed_renderer = QSvgRenderer(QByteArray(proceed_svg_data))
        proceed_pixmap = QPixmap(32, 32)
        proceed_pixmap.fill(Qt.transparent)
        painter = QPainter(proceed_pixmap)
        proceed_renderer.render(painter)
        painter.end()

        proceed_btn = QPushButton()
        proceed_btn.setFixedSize(32, 32)
        proceed_btn.setIcon(QIcon(proceed_pixmap))
        proceed_btn.setIconSize(QSize(24, 24))
        proceed_btn.setStyleSheet("""
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
        proceed_btn.setCursor(Qt.PointingHandCursor)
        proceed_btn.setToolTip("Proceed")
        proceed_btn.clicked.connect(self.on_proceed_clicked)
        self.proceed_btn = proceed_btn
        
        # Add buttons to button layout
        button_layout.addWidget(self.delay_edit)
        button_layout.addWidget(picker_btn)
        button_layout.addWidget(proceed_btn)
        
        # Add button layout to the top row
        top_row.addLayout(button_layout)
        main_layout.addLayout(top_row)
        
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
        self.glow_timer.start(800)
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
    
    def start_element_blinking(self):
        """Start blinking the element with blue highlight"""
        try:
            if not self.current_xpath:
                print("No XPath set for blinking")
                return
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
    
    def on_proceed_clicked(self):
        """Handle Proceed button click"""
        log_action("XPathConfirmationDialog: on_proceed_clicked called")
        self.result = True
        self.chosen_xpath = self.main_xpath
        log_action(f"XPathConfirmationDialog: on_proceed_clicked - result=True, chosen_xpath='{self.chosen_xpath}'")
        self.cleanup_and_close()
    
    def on_picker_clicked(self):
        """Delay (optional) then use element picker to select an element; do not close dialog."""
        try:
            delay = 0
            if hasattr(self, 'delay_edit') and self.delay_edit is not None:
                s = self.delay_edit.text().strip()
                delay = int(s) if s.isdigit() else 0
            if delay > 0:
                self.start_countdown(delay)
            else:
                self._run_element_picker()
        except Exception as e:
            print(f"Error handling picker click: {e}")

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
            for w in [getattr(self, 'picker_btn', None), getattr(self, 'proceed_btn', None), 
                      getattr(self, 'delay_edit', None)]:
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
                self.element_verify = True
                self.main_xpath = picked
                self.current_xpath = picked
                # Switch blinking to the picked xpath
                self.stop_element_blinking()
                self.start_element_blinking()
        except Exception as e:
            print(f"Error handling picker result: {e}")

    @pyqtSlot(str)
    def _on_picker_error(self, msg: str):
        print(f"Picker error: {msg}")

    def cleanup_and_close(self):
        """Clean up resources and close dialog"""
        log_action("XPathConfirmationDialog: cleanup_and_close called")
        
        # Stop animations
        if hasattr(self, 'fade_animation'):
            self.fade_animation.stop()
            log_action("XPathConfirmationDialog: Fade animation stopped")
        
        if hasattr(self, 'glow_timer'):
            self.glow_timer.stop()
            log_action("XPathConfirmationDialog: Glow timer stopped")
        
        # Stop element blinking
        self.stop_element_blinking()
        log_action("XPathConfirmationDialog: Element blinking stopped")
        
        # Set force close flag before accepting
        self._force_close = True
        log_action(f"XPathConfirmationDialog: Setting _force_close=True, result={self.result}, chosen_xpath='{self.chosen_xpath}'")
        
        # Close dialog
        self.accept()
    
    def hideEvent(self, event):
        """Prevent unintended hides during exec_(). Keep dialog visible unless closing explicitly."""
        log_action(f"XPathConfirmationDialog: hideEvent triggered, _force_close={getattr(self, '_force_close', False)}, _initialization_complete={getattr(self, '_initialization_complete', False)}")
        
        # If initialization is not complete, block the hide event
        if not getattr(self, '_initialization_complete', False):
            log_action("XPathConfirmationDialog: hideEvent ignored during initialization")
            event.ignore()
            return
        
        if getattr(self, '_force_close', False):
            log_action("XPathConfirmationDialog: hideEvent accepted (force_close=True)")
            return super().hideEvent(event)
        log_action("XPathConfirmationDialog: hideEvent ignored, re-showing dialog")
        event.ignore()
        try:
            self.show()
            self.raise_()
            self.activateWindow()
        except Exception:
            pass
    
    def closeEvent(self, event):
        """Handle close event"""
        log_action(f"XPathConfirmationDialog: closeEvent triggered, _force_close={getattr(self, '_force_close', False)}")
        if not getattr(self, '_force_close', False):
            log_action("XPathConfirmationDialog: closeEvent - force_close not set, ignoring close")
            event.ignore()
            return
        log_action("XPathConfirmationDialog: closeEvent accepted")
        event.accept()
    
    def keyPressEvent(self, event):
        """Handle escape key to prevent closing via Esc"""
        if event.key() == Qt.Key_Escape:
            log_action("XPathConfirmationDialog: Escape key pressed, ignoring")
            event.ignore()
            return
        super().keyPressEvent(event)
    
    def reject(self):
        """Prevent default reject (e.g., Esc) from closing the dialog"""
        log_action("XPathConfirmationDialog: reject() called, ignoring")
        pass
    
    def accept(self):
        """Guard accept; only allow when explicitly triggered via Proceed."""
        if not getattr(self, '_force_close', False):
            log_action("XPathConfirmationDialog: accept() called but _force_close not set, blocking")
            return
        log_action("XPathConfirmationDialog: accept() called with _force_close=True, accepting")
        return super().accept()


def xpath_status(label_text, driver):
    """
    Show XPath confirmation dialog with element picker button and blinking
    
    Args:
        label_text (str): Text label to display on the dialog
        driver: Selenium WebDriver instance
    
    Returns:
        tuple[bool, str]: (is_confirmed, xpath)
            - On Proceed (tick): (True, selected_xpath)
            - On picker click: switches to picked xpath
            - Closing the dialog returns (False, "")
    """
    import threading
    current_thread = threading.current_thread()
    log_action(f"element_status: Called with label_text='{label_text}'")
    log_action(f"element_status: Running in thread '{current_thread.name}'")
    
    # If we're in the main thread, show dialog directly
    if current_thread.name == 'MainThread':
        log_action("element_status: Main thread detected, creating dialog")
        # Create/reuse QApplication
        global _APP_SINGLETON
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
        
        # Create and show dialog
        log_action("element_status: Creating XPathConfirmationDialog")
        dialog = XPathConfirmationDialog(label_text, driver, app)
        try:
            log_action("element_status: Ensuring dialog visibility before exec_()")
            dialog.setVisible(True)
            dialog.show()
        except Exception as e:
            log_action(f"element_status: Error ensuring visibility: {e}")
        
        log_action("element_status: Calling dialog.exec_()")
        result_code = dialog.exec_()
        
        log_action(f"element_status: Dialog exec_() returned with code: {result_code}")
        log_action(f"element_status: Dialog result: {dialog.result}")
        log_action(f"element_status: Dialog chosen_xpath: '{dialog.chosen_xpath}'")
        
        if not dialog.result:
            log_action("element_status: Dialog result is False, returning (False, '')")
            return False, ""
        
        log_action(f"element_status: Returning ({dialog.result}, '{dialog.chosen_xpath}')")
        return dialog.result, dialog.chosen_xpath
    else:
        print(f"element_status called from worker thread: {current_thread.name}")
        print("Using signal-based communication with main thread")
        return False, ""
