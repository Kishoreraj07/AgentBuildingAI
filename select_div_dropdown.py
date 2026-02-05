import sys
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time,os
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

class ElementConfirmationDialog(QDialog):
    """Standalone element confirmation dialog with xpath highlighting"""
    
    def __init__(self, element_description,xpath, driver, parent=None):
        super().__init__(parent)
        self.element_desc=element_description
        self.xpath = xpath
        self.driver = driver
        self.result = False
        self.blinking_timer = None
        self.blink_state = False
        
        # Track current/pasted xpath and chosen return value
        self.current_xpath = self.xpath  # used for blinking/highlight
        self.user_xpath = None           # user-entered xpath via dropdown panel
        self.last_picker_xpath = None    # xpath chosen via element_picker()
        self.chosen_xpath = self.xpath   # final xpath to return on Yes
        self.main_xpath = self.xpath     # common/main xpath reflecting latest selection or input
        self.element_verify = False      # becomes True after at least one successful element_picker
        self.bound_index = None          # list-type bound index from coordinate picker
        
        self.setupUI()
        self.start_element_blinking()
        
        # Ensure dialog stays independent
        self.raise_()
        self.activateWindow()
        
    def setupUI(self):
        """Setup the confirmation dialog UI"""
        # Make dialog standalone and independent from main application
        self.setWindowFlags(
            Qt.FramelessWindowHint | 
            Qt.WindowStaysOnTopHint |
            Qt.Tool |
            Qt.X11BypassWindowManagerHint
        )
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setAttribute(Qt.WA_ShowWithoutActivating)  # Show without stealing focus from main app

        # Horizontal compact size with text and buttons
        self.setFixedSize(520, 70)
        
        # Position at bottom left corner with some margin
        screen = QApplication.desktop().screenGeometry()
        self.move(20, screen.height() - 160)  # 20px from left, 160px from bottom (moved slightly up)
        
        # Add dragging support
        self._mouse_pressed = False
        self._mouse_pos = None

        # Create main container with rounded corners
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
                font-size: 16px;
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
        no_btn = QPushButton()
        no_btn.setFixedSize(45, 45)
        no_btn.setIcon(QIcon(resource_path("styles/Icon/element_click.png")))
        no_btn.setIconSize(QSize(32, 32))
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
        no_btn.setToolTip("Pick element (X)")
        no_btn.clicked.connect(self.on_no_clicked)
        self.no_btn = no_btn
        
        # Coordinate picker button (Citrix bound-index)
        coord_btn = QPushButton()
        coord_btn.setFixedSize(45, 45)
        coord_btn.setIcon(QIcon(resource_path("styles/Icon/coordinate_click.png")))
        coord_btn.setIconSize(QSize(32, 32))
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
        coord_btn.setToolTip("Pick coordinates (Citrix)")
        coord_btn.clicked.connect(self.on_coordinate_clicked)
        self.coord_btn = coord_btn
        
        # Yes button with tick icon
        yes_btn = QPushButton()
        yes_btn.setFixedSize(45, 45)
        yes_btn.setIcon(QIcon(resource_path("styles/Icon/tick.png")))
        yes_btn.setIconSize(QSize(32, 32))
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
        yes_btn.setToolTip("Yes - Element is correct")
        yes_btn.clicked.connect(self.on_yes_clicked)
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
        button_layout.addWidget(no_btn)
        button_layout.addWidget(coord_btn)
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
        self.xpath_edit.setPlaceholderText("Enter your xpath here")
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
            self.start_element_blinking()
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
                    self.text_label.setText("<b>Unable to Find Element</b>")
            except Exception:
                pass
    
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
        self.result = True
        try:
            # If user picked coordinates via the Citrix picker, prefer returning that list
            if getattr(self, 'bound_index', None) is not None:
                self.chosen_xpath = self.bound_index  # list-type bound index
            else:
                typed = ''
                if hasattr(self, 'xpath_edit') and self.xpath_edit is not None:
                    typed = self.xpath_edit.text().strip()
                if typed:
                    # dropdown input overrides main_xpath
                    self.main_xpath = typed
                if getattr(self, 'element_verify', False):
                    # if at least once picked via X, return main_xpath
                    self.chosen_xpath = self.main_xpath
                else:
                    # no picker used; return typed if present else original
                    if typed:
                        self.chosen_xpath = self.main_xpath
                    else:
                        self.chosen_xpath = self.xpath
        except Exception:
            self.chosen_xpath = self.xpath
        self.cleanup_and_close()
    
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
                self._run_element_picker()
        except Exception as e:
            print(f"Error handling no click: {e}")
        # Do not close the dialog here

    def on_coordinate_clicked(self):
        """Pick coordinates (Citrix) and paste bound-index list into the dropdown input; do not close dialog."""
        try:
            delay = 0
            if hasattr(self, 'delay_edit') and self.delay_edit is not None:
                s = self.delay_edit.text().strip()
                delay = int(s) if s.isdigit() else 0
            if delay > 0:
                try:
                    self.countdown_overlay = CountdownOverlay(delay)
                    self.countdown_overlay.finished.connect(self._run_coordinate_picker)
                    self.countdown_overlay.show()
                except Exception as e:
                    print(f"Error starting countdown for coord picker: {e}")
                    self._run_coordinate_picker()
            else:
                self._run_coordinate_picker()
        except Exception as e:
            print(f"Error handling coordinate click: {e}")
        # Do not close the dialog here

    def _run_coordinate_picker(self):
        """Run the Citrix coordinate picker synchronously and capture bound index list."""
        try:
            # Hide dialog so overlay/picker is unobstructed
            self.hide()
            QApplication.processEvents()
            
            try:
                from datas.process_flow.Citrix_process import single_element_picker, bound_index_fix
            except Exception:
                # Fallback to capitalized package name on case-sensitive paths
                from datas.process_flow.Citrix_process import single_element_picker, bound_index_fix  # type: ignore
            
            coordinates = single_element_picker.citrix_mod_locator()
            if coordinates:
                try:
                    bound_idx = bound_index_fix.gemini_response(coordinates)
                except Exception as e:
                    print(f"Error post-processing coordinates: {e}")
                    bound_idx = None
                if bound_idx is not None:
                    # Store and reflect into input field
                    self.bound_index = bound_idx
                    try:
                        if hasattr(self, 'xpath_edit') and self.xpath_edit is not None:
                            self.xpath_edit.setText(str(bound_idx))
                            # Ensure panel is visible so user sees the pasted value
                            if hasattr(self, 'input_panel') and not self.input_panel.isVisible():
                                self.toggle_input_panel()
                    except Exception as e:
                        print(f"Error setting bound index into input: {e}")
                else:
                    QMessageBox.information(self, "Info", "Failed to extract bounding index.")
            else:
                QMessageBox.information(self, "Info", "No element selected.")
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Coordinate picker failed: {e}")
        finally:
            # Restore dialog
            self.show()
            self.raise_()
            self.activateWindow()
            QApplication.processEvents()

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
            for w in [getattr(self, 'no_btn', None), getattr(self, 'yes_btn', None),
                      getattr(self, 'dropdown_btn', None), getattr(self, 'check_btn', None),
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
                self.last_picker_xpath = picked
                self.element_verify = True
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
    
    def cleanup_and_close(self):
        """Clean up resources and close dialog"""
        # Stop animations
        if hasattr(self, 'fade_animation'):
            self.fade_animation.stop()
        
        if hasattr(self, 'glow_timer'):
            self.glow_timer.stop()
        
        # Stop element blinking
        self.stop_element_blinking()
        
        # Close dialog
        self.accept()
    
    def closeEvent(self, event):
        """Handle close event"""
        self.cleanup_and_close()
        event.accept()

def element_status(element_description,xpath, driver):
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
    # Check if we're running in a worker thread
    import threading
    current_thread = threading.current_thread()
    
    # If we're in the main thread, show dialog directly
    if current_thread.name == 'MainThread':
        # Create QApplication if it doesn't exist
        app = QApplication.instance()
        if app is None:
            app = QApplication(sys.argv)
        
        # Create and show dialog
        dialog = ElementConfirmationDialog(element_description,xpath, driver)
        dialog.exec_()
        
        return dialog.result, dialog.chosen_xpath
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