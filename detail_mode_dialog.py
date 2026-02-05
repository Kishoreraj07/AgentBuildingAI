import os
import sys
import subprocess
import threading
import time
from queue import Queue, Empty
import speech_recognition as sr
from PyQt5.QtWidgets import QMainWindow, QWidget, QVBoxLayout, QLabel, QTextEdit, QPushButton, QHBoxLayout, QApplication, QProgressBar, QFrame, QSizePolicy
from PyQt5.QtCore import Qt, QTimer, QThread, pyqtSignal, QDateTime, QSize, QProcess
from PyQt5.QtGui import QTextCursor, QIcon
from PyQt5.QtWidgets import QGraphicsDropShadowEffect
from PyQt5.QtGui import QColor
import style_loader
from detail_mode_thread import detail_mode_manager

class IsolatedSpeechManager:
    """Isolated speech manager for each dialog instance"""
    
    def __init__(self, dialog_id):
        self.dialog_id = dialog_id
        self.is_speaking = False
        self.speech_queue = Queue()
        self.speech_thread = None
        self.stop_speaking = False
        self.has_spoken = False  # Track if we've already spoken for this dialog
        print(f"🎤 Created isolated speech manager for dialog {dialog_id}")
    
    def speak_async(self, text, callback=None, force=False):
        """Queue text for speech in this specific dialog instance"""
        if not text or not text.strip():
            print(f"⚠️ Dialog {self.dialog_id}: Empty text provided for speech")
            return
        
        # Prevent multiple speeches unless forced (manual trigger)
        if self.has_spoken and not force:
            print(f"🔇 Dialog {self.dialog_id}: Already spoken, skipping automatic speech")
            return
        
        # Clear any existing items in queue first
        self._clear_queue()
        
        print(f"🎤 Dialog {self.dialog_id}: Queueing new text: {text[:50]}...")
        self.speech_queue.put((text.strip(), callback))
        self._start_speech_processor()
    
    def _clear_queue(self):
        """Clear the speech queue"""
        while not self.speech_queue.empty():
            try:
                self.speech_queue.get_nowait()
            except Empty:
                break
    
    def _start_speech_processor(self):
        """Start the speech processing thread for this dialog"""
        if self.speech_thread and self.speech_thread.is_alive():
            print(f"🎤 Dialog {self.dialog_id}: Speech thread already running, stopping it first...")
            self.stop_speaking = True
            time.sleep(0.2)
            self.stop_speaking = False
        
        self.speech_thread = threading.Thread(target=self._speech_processor, daemon=True)
        self.speech_thread.start()
        print(f"🎤 Dialog {self.dialog_id}: Started new speech processor thread")
    
    def _speech_processor(self):
        """Main speech processing loop for this dialog"""
        while True:
            try:
                # Get speech request with timeout
                speech_data = self.speech_queue.get(timeout=1.0)
                if speech_data is None:  # Poison pill to stop
                    break
                
                text, callback = speech_data
                print(f"🎤 Dialog {self.dialog_id}: Processing speech: {text[:50]}...")
                success = self._execute_speech(text, callback)
                
                # Mark as spoken if successful
                if success:
                    self.has_spoken = True
                
                # Only process one item then exit (no continuous loop)
                break
                
            except Empty:
                break
            except Exception as e:
                print(f"❌ Dialog {self.dialog_id}: Speech processor error: {e}")
                break
    
    def _execute_speech(self, text, callback=None):
        """Execute speech using multiple fallback methods"""
        self.is_speaking = True
        success = False
        
        print(f"🎤 Dialog {self.dialog_id}: Attempting to speak: {text[:50]}...")
        
        # Method 1: Try pyttsx3 in isolated process
        if not success and not self.stop_speaking:
            success = self._try_pyttsx3_isolated(text)
        
        # Method 2: Try Windows SAPI directly
        if not success and not self.stop_speaking and sys.platform == "win32":
            success = self._try_windows_sapi(text)
        
        # Method 3: Try system TTS commands
        if not success and not self.stop_speaking:
            success = self._try_system_tts(text)
        
        self.is_speaking = False
        
        if callback:
            callback(success)
        
        if success:
            print(f"✅ Dialog {self.dialog_id}: Successfully spoke text")
        else:
            print(f"❌ Dialog {self.dialog_id}: Failed to speak text")
        
        return success
    
    def _try_pyttsx3_isolated(self, text):
        """Try pyttsx3 in completely isolated way"""
        try:
            # Create unique script for this dialog instance
            script_content = f"""
import sys
import os
sys.path.insert(0, os.getcwd())

try:
    import pyttsx3
    engine = pyttsx3.init()
    
    # Set properties
    voices = engine.getProperty('voices')
    if voices:
        for voice in voices:
            if 'zira' in voice.name.lower() or 'female' in voice.name.lower():
                engine.setProperty('voice', voice.id)
                break
        else:
            engine.setProperty('voice', voices[0].id)
    
    engine.setProperty('rate', 180)
    engine.setProperty('volume', 1.0)
    
    # Speak text
    engine.say({repr(text)})
    engine.runAndWait()
    engine.stop()
    
    print("SUCCESS")
except Exception as e:
    print(f"ERROR: {{e}}")
    sys.exit(1)
"""
            
            # Write script to unique temp file for this dialog
            script_path = f"temp_speech_script_{self.dialog_id}_{int(time.time())}.py"
            with open(script_path, 'w', encoding='utf-8') as f:
                f.write(script_content)
            
            print(f"🎤 Dialog {self.dialog_id}: Executing isolated pyttsx3 script: {script_path}")
            
            # Execute in separate process
            result = subprocess.run([sys.executable, script_path], 
                                  capture_output=True, text=True, timeout=15)
            
            # Cleanup
            try:
                os.remove(script_path)
            except:
                pass
            
            success = "SUCCESS" in result.stdout
            if success:
                print(f"✅ Dialog {self.dialog_id}: pyttsx3 isolated method succeeded")
            else:
                print(f"❌ Dialog {self.dialog_id}: pyttsx3 isolated method failed: {result.stderr}")
            
            return success
            
        except Exception as e:
            print(f"❌ Dialog {self.dialog_id}: pyttsx3 isolated method failed: {e}")
            return False
    
    def _try_windows_sapi(self, text):
        """Try Windows SAPI directly via PowerShell"""
        if sys.platform != "win32":
            return False
        
        try:
            # Escape text for PowerShell
            escaped_text = text.replace('"', '`"').replace("'", "''")
            
            # PowerShell command to use SAPI
            ps_command = f'''
Add-Type -AssemblyName System.Speech
$synth = New-Object System.Speech.Synthesis.SpeechSynthesizer
$synth.Rate = 2
$synth.Volume = 100
$voices = $synth.GetInstalledVoices()
foreach ($voice in $voices) {{
    if ($voice.VoiceInfo.Name -like "*Zira*" -or $voice.VoiceInfo.Gender -eq "Female") {{
        $synth.SelectVoice($voice.VoiceInfo.Name)
        break
    }}
}}
$synth.Speak("{escaped_text}")
$synth.Dispose()
'''
            
            print(f"🎤 Dialog {self.dialog_id}: Trying Windows SAPI...")
            result = subprocess.run(
                ["powershell", "-Command", ps_command],
                capture_output=True, text=True, timeout=15
            )
            
            success = result.returncode == 0
            if success:
                print(f"✅ Dialog {self.dialog_id}: Windows SAPI method succeeded")
            else:
                print(f"❌ Dialog {self.dialog_id}: Windows SAPI method failed: {result.stderr}")
            
            return success
            
        except Exception as e:
            print(f"❌ Dialog {self.dialog_id}: Windows SAPI method failed: {e}")
            return False
    
    def _try_system_tts(self, text):
        """Try system-specific TTS commands"""
        try:
            if sys.platform == "win32":
                # Windows: Use built-in narrator or PowerShell
                command = ["powershell", "-Command", f'(New-Object -ComObject SAPI.SpVoice).Speak("{text}")']
            elif sys.platform == "darwin":
                # macOS: Use say command
                command = ["say", text]
            else:
                # Linux: Try espeak or festival
                if subprocess.run(["which", "espeak"], capture_output=True).returncode == 0:
                    command = ["espeak", text]
                elif subprocess.run(["which", "festival"], capture_output=True).returncode == 0:
                    command = ["echo", text, "|", "festival", "--tts"]
                else:
                    return False
            
            print(f"🎤 Dialog {self.dialog_id}: Trying system TTS...")
            result = subprocess.run(command, capture_output=True, timeout=12)
            
            success = result.returncode == 0
            if success:
                print(f"✅ Dialog {self.dialog_id}: System TTS method succeeded")
            else:
                print(f"❌ Dialog {self.dialog_id}: System TTS method failed")
            
            return success
            
        except Exception as e:
            print(f"❌ Dialog {self.dialog_id}: System TTS method failed: {e}")
            return False
    
    def stop_all_speech(self):
        """Stop all speech for this dialog"""
        print(f"🛑 Dialog {self.dialog_id}: Stopping all speech...")
        self.stop_speaking = True
        self._clear_queue()
        time.sleep(0.1)
        self.stop_speaking = False
    
    def reset_speech_flag(self):
        """Reset the has_spoken flag - for manual triggers"""
        self.has_spoken = False


class SpeechWorker(QThread):
    """Qt-based speech worker for better integration"""
    finished = pyqtSignal()
    error = pyqtSignal(str)
    success = pyqtSignal()

    def __init__(self, text, dialog_id, force=False):
        super().__init__()
        self.text = text
        self.dialog_id = dialog_id
        self.force = force
        self.speech_manager = IsolatedSpeechManager(f"worker_{dialog_id}")

    def run(self):
        try:
            success = [False]
            
            def callback(result):
                success[0] = result
            
            print(f"🎤 SpeechWorker {self.dialog_id}: Starting speech for: {self.text[:30]}...")
            self.speech_manager.speak_async(self.text, callback, self.force)
            
            # Wait for completion
            start_time = time.time()
            while self.speech_manager.is_speaking and (time.time() - start_time) < 30:
                time.sleep(0.1)
            
            # Wait a bit more for the callback
            time.sleep(0.5)
            
            if success[0]:
                self.success.emit()
            else:
                self.error.emit("Speech failed")
                
        except Exception as e:
            self.error.emit(str(e))
        finally:
            self.finished.emit()


class DetailModeMainWindow(QMainWindow):
    accepted_signal = pyqtSignal(str)  # Signal to emit result when accepted
    
    # Class variable to track dialog instances
    _dialog_counter = 0
    
    def __init__(self, response_text, parent=None):
        super().__init__(None)   # No parent - completely independent
        
        # Assign unique ID to this dialog instance
        DetailModeMainWindow._dialog_counter += 1
        self.dialog_id = DetailModeMainWindow._dialog_counter
        
        self.response_text = response_text
        self.result = None
        self.initial_speech_completed = False  # Track initial speech
        
        print(f"🆔 Creating DetailModeMainWindow instance #{self.dialog_id}")
        print(f"📢 Response text for dialog {self.dialog_id}: {response_text[:50]}...")
        
        # Initialize threaded processing
        self.worker_id = None
        self.detail_worker = None
        
        # Window setup - Make it completely independent
        self.setWindowFlags(
            Qt.Window |
            Qt.FramelessWindowHint |
            Qt.WindowStaysOnTopHint |
            Qt.X11BypassWindowManagerHint
        )
        
        # Set attributes for complete independence
        self.setAttribute(Qt.WA_DeleteOnClose, True)
        self.setAttribute(Qt.WA_QuitOnClose, False)
        self.setAttribute(Qt.WA_ShowWithoutActivating, False)
        self.setAttribute(Qt.WA_X11NetWmWindowTypeDialog, False)
        self.setAttribute(Qt.WA_GroupLeader, True)
        
        self.setFixedSize(800, 600)
        self.draggable = True
        self.mouse_pressed = False
        self.mouse_position = None
        
        # Setup UI
        self.setup_ui()
        
        # Initialize voice integration
        self._initialize_voice_integration()
        
        # Start threaded processing for this dialog
        print(f"📢 Dialog {self.dialog_id}: Starting threaded processing...")
        self._start_threaded_processing()

    def _start_threaded_processing(self):
        """Start detail mode processing in separate thread"""
        try:
            self.worker_id, self.detail_worker = detail_mode_manager.start_detail_mode_processing(self.response_text)
            
            # Connect worker signals
            self.detail_worker.speech_started.connect(self._on_speech_started)
            self.detail_worker.speech_completed.connect(self._on_speech_completed)
            self.detail_worker.speech_error.connect(self._on_speech_error)
            self.detail_worker.force_terminated.connect(self._on_force_terminated)
            
            print(f"✅ Dialog {self.dialog_id}: Threaded processing started with worker ID {self.worker_id}")
            
        except Exception as e:
            print(f"❌ Dialog {self.dialog_id}: Failed to start threaded processing: {e}")
    
    def _on_speech_started(self):
        """Handle speech started signal"""
        print(f"🎤 Dialog {self.dialog_id}: Speech started")
        self.initial_speech_completed = True
    
    def _on_speech_completed(self):
        """Handle speech completed signal"""
        print(f"✅ Dialog {self.dialog_id}: Speech completed successfully")
    
    def _on_speech_error(self, error_msg):
        """Handle speech error signal"""
        print(f"❌ Dialog {self.dialog_id}: Speech error: {error_msg}")
    
    def _on_force_terminated(self):
        """Handle force termination signal"""
        print(f"🛑 Dialog {self.dialog_id}: Processing was force terminated")
        self.worker_id = None
        self.detail_worker = None

    def showEvent(self, event):
        super().showEvent(event)
        self.setParent(None)
        self.raise_()
        print(f"⚠️ Dialog {self.dialog_id}: Window shown with full independence")
        
        # NO additional speech attempt when window is shown - removed this line

    def closeEvent(self, event):
        print(f"⚠️ Dialog {self.dialog_id}: Window closing independently")
        self.cleanup_all_processing()
        super().closeEvent(event)

    def cleanup_all_processing(self):
        """Clean up all processing resources for this dialog"""
        print(f"🔧 Dialog {self.dialog_id}: Cleaning up all processing resources...")
        
        # Terminate threaded processing
        if self.worker_id is not None:
            print(f"🛑 Dialog {self.dialog_id}: Terminating worker {self.worker_id}")
            detail_mode_manager.terminate_detail_mode_processing(self.worker_id)
            self.worker_id = None
            self.detail_worker = None
        
        # Clean up voice integration if exists
        if hasattr(self, 'voice_thread'):
            try:
                self.voice_thread.cleanup()
            except Exception as e:
                print(f"Error cleaning up voice thread: {e}")
                
        print(f"🔧 Dialog {self.dialog_id}: All processing resources cleaned up")

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.mouse_pressed = True
            self.mouse_position = event.globalPos() - self.pos()
            event.accept()

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.mouse_pressed = False
            event.accept()

    def mouseMoveEvent(self, event):
        if self.draggable and self.mouse_pressed:
            self.move(event.globalPos() - self.mouse_position)
            event.accept()

    def setup_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        self.setProperty('class', 'DetailModeDialog')
        central_widget.setProperty('class', 'DetailModeDialog')
        
        # Apply styles BEFORE loading external stylesheet
        self.setStyleSheet("""
            QMainWindow[class="DetailModeDialog"] {
                background-color: #18181b;
                border: 1px solid #404040;
                border-radius: 16px;
            }
            QWidget[class="DetailModeDialog"] {
                background-color: #18181b;
                color: #e4e4e4;
            }
            
            /* Container Styles */
            QWidget#systemContainer {
                background-color: #2a2a2a;
                border: 1px solid #404040;
                border-radius: 12px;
                padding: 16px;
                margin: 8px 0px;
            }
            
            QWidget#userContainer {
                background-color: #2a2a2a;
                border: 1px solid #404040;
                border-radius: 12px;
                padding: 16px;
                margin: 8px 0px;
            }
            
            QLabel#containerHeader {
                color: #4ecdc4;
                font-weight: bold;
                font-size: 14px;
                padding: 4px 0px;
                border-bottom: 1px solid #404040;
                margin-bottom: 8px;
                font-family: 'Asen Pro';
                background-color: transparent;
            }
            
            QLabel#taskInfoLabel {
                color: #4ecdc4;
                font-size: 11px;
                padding: 2px 8px;
                background-color: #1a4a47;
                border-radius: 4px;
                border: 1px solid #4ecdc4;
                font-family: 'Asen Pro';
            }
            
            QTextEdit#responseText {
                background-color: #1e1e1e;
                border: 1px solid #333333;
                border-radius: 6px;
                color: #e4e4e4;
                padding: 8px;
                font-size: 12px;
                font-family: 'Asen Pro';
            }
            
            QTextEdit#inputArea {
                background-color: #1e1e1e;
                border: 1px solid #333333;
                border-radius: 6px;
                color: #e4e4e4;
                padding: 8px;
                font-size: 12px;
                font-family: 'Asen Pro';
            }
            
            QTextEdit#inputArea:focus {
                border: 2px solid #4ecdc4;
            }
            
            QPushButton#micButton {
                background-color: #3a3a3a;
                border: 1px solid #555555;
                border-radius: 20px;
                color: #e4e4e4;
            }
            
            QPushButton#micButton:hover {
                background-color: #4a4a4a;
                border: 1px solid #4ecdc4;
            }
            
            QPushButton#submitBtn {
                background-color: #4ecdc4;
                color: #1e1e1e;
                border: none;
                border-radius: 6px;
                padding: 8px 20px;
                font-weight: bold;
                font-size: 12px;
                min-width: 80px;
                font-family: 'Asen Pro';
            }
            
            QPushButton#submitBtn:hover {
                background-color: #45b7aa;
            }
            
            QLabel#voiceStatus {
                color: #4ecdc4;
                font-size: 11px;
                padding: 2px 0px;
                font-family: 'Asen Pro';
                background-color: transparent;
            }
        """)

        main_layout = QHBoxLayout(central_widget)
        main_layout.setSpacing(0)
        main_layout.setContentsMargins(22, 18, 22, 22)

        left_layout = QVBoxLayout()
        left_layout.setSpacing(0)

        # Title bar
        title_layout = QHBoxLayout()
        icon = QLabel()
        icon.setPixmap(QIcon("styles/Icon/detail_mode.png").pixmap(32, 32))
        title_layout.addWidget(icon)

        title = QLabel(f"Detail Mode #{self.dialog_id}")  # Show dialog ID
        title.setObjectName("titleLabel")
        title_layout.addWidget(title)
        title_layout.addStretch()

        min_btn = QPushButton("–")
        min_btn.setObjectName("minBtn")
        min_btn.setProperty('class', 'DetailDialogMinButton')
        style_loader.apply_stylesheet(min_btn)
        min_btn.clicked.connect(self._force_minimize)
        title_layout.addWidget(min_btn)

        close_btn = QPushButton("✕")
        close_btn.setObjectName("closeBtn")
        close_btn.setProperty('class', 'DetailDialogCloseButton')
        style_loader.apply_stylesheet(close_btn)
        close_btn.clicked.connect(self._force_close)
        title_layout.addWidget(close_btn)

        left_layout.addLayout(title_layout)

        # Separator
        separator = QFrame()
        separator.setObjectName("separatorLine")
        separator.setFrameShape(QFrame.HLine)
        left_layout.addWidget(separator)

        # Container 1: System Information (Detail Mode, Droid Response, Task Number, Message)
        system_container = QWidget()
        system_container.setObjectName("systemContainer")
        system_layout = QVBoxLayout(system_container)
        system_layout.setSpacing(12)
        system_layout.setContentsMargins(16, 16, 16, 16)

        # Detail Mode header
        detail_mode_label = QLabel(" Detail Mode")
        detail_mode_label.setObjectName("containerHeader")
        system_layout.addWidget(detail_mode_label)

        # Droid Response header
        response_label = QLabel("🤖 Droid Response")
        response_label.setObjectName("sectionLabel")
        system_layout.addWidget(response_label)

        # Task number info
        task_info_label = QLabel(f"Task number: Type username")
        task_info_label.setObjectName("taskInfoLabel")
        system_layout.addWidget(task_info_label)

        # System response text
        self.response_text_widget = QTextEdit(self.response_text)
        self.response_text_widget.setObjectName("responseText")
        self.response_text_widget.setReadOnly(True)
        self.response_text_widget.setMaximumHeight(110)
        system_layout.addWidget(self.response_text_widget)

        left_layout.addWidget(system_container)

        # Container 2: User Response Section (Your Detailed Response, Input Area, Buttons)
        user_container = QWidget()
        user_container.setObjectName("userContainer")
        user_layout = QVBoxLayout(user_container)
        user_layout.setSpacing(12)
        user_layout.setContentsMargins(16, 16, 16, 16)

        # Your response header
        input_label = QLabel("💬 Your Detailed Response")
        input_label.setObjectName("containerHeader")
        user_layout.addWidget(input_label)

        # Input area
        self.input_area = QTextEdit()
        self.input_area.setObjectName("inputArea")
        self.input_area.setPlaceholderText("Type your detailed response or use the microphone...")
        self.input_area.setMinimumHeight(120)
        user_layout.addWidget(self.input_area)

        # Voice status label
        self.voice_status_label = QLabel("")
        self.voice_status_label.setObjectName("voiceStatus")
        self.voice_status_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.voice_status_label.setFixedHeight(20)
        user_layout.addWidget(self.voice_status_label)

        # Buttons row (mic + send)
        buttons_layout = QHBoxLayout()
        buttons_layout.setSpacing(12)
        buttons_layout.addStretch()

        self.mic_button = QPushButton()
        self.mic_button.setObjectName("micButton")
        self.mic_button.setFixedSize(40, 40)
        self.mic_button.setToolTip("Click to record voice input")
        self.mic_button.setIcon(QIcon("styles/Icon/microphone.png"))
        self.mic_button.setIconSize(QSize(24, 24))
        buttons_layout.addWidget(self.mic_button)

        submit_btn = QPushButton("Send")
        submit_btn.setObjectName("submitBtn")
        submit_btn.clicked.connect(self.accept)
        buttons_layout.addWidget(submit_btn)

        user_layout.addLayout(buttons_layout)
        left_layout.addWidget(user_container)
        main_layout.addLayout(left_layout)

        self.setGraphicsEffect(self.create_shadow_effect())
        
        # Force apply our container styles with maximum specificity
        self.setStyleSheet(self.styleSheet() + """
            /* Force container styles with highest priority */
            QWidget#systemContainer {
                background-color: #2a2a2a !important;
                border: 2px solid #404040 !important;
                border-radius: 12px !important;
                margin: 8px 0px !important;
            }
            
            QWidget#userContainer {
                background-color: #2a2a2a !important;
                border: 2px solid #404040 !important;
                border-radius: 12px !important;
                margin: 8px 0px !important;
            }
            
            QLabel#containerHeader {
                color: #4ecdc4 !important;
                font-weight: bold !important;
                font-size: 14px !important;
                padding: 8px 0px !important;
                border-bottom: 1px solid #404040 !important;
                margin-bottom: 8px !important;
                background-color: transparent !important;
            }
            
            QLabel#taskInfoLabel {
                color: #4ecdc4 !important;
                font-size: 11px !important;
                padding: 4px 8px !important;
                background-color: #1a4a47 !important;
                border-radius: 4px !important;
                border: 1px solid #4ecdc4 !important;
                margin: 4px 0px !important;
            }
        """)

    def _initialize_voice_integration(self):
        try:
            from voice_integration_thread import VoiceIntegrationThread
            import config
            GEMINI_API_KEY = getattr(config, 'API_KEY', None)
            if not GEMINI_API_KEY:
                print("⚠️ Warning: No Gemini API key found in config")
                return
            self.voice_thread = VoiceIntegrationThread(GEMINI_API_KEY)
            self.voice_thread.recording_started.connect(self._on_recording_started)
            self.voice_thread.recording_stopped.connect(self._on_recording_stopped)
            self.voice_thread.transcription_ready.connect(self._on_transcription_ready)
            self.voice_thread.error_occurred.connect(self._on_voice_error)
            self.voice_thread.processing_started.connect(self._on_processing_started)
            self.voice_thread.processing_finished.connect(self._on_processing_finished)
            self.mic_button.clicked.connect(self._toggle_voice_recording)
            self.is_recording = False
            print(f"✅ Dialog {self.dialog_id}: Voice integration initialized successfully")
        except Exception as e:
            print(f"❌ Dialog {self.dialog_id}: Voice integration failed: {e}")
            self.mic_button.setEnabled(False)
            self.mic_button.setToolTip("Voice integration unavailable")

    def _toggle_voice_recording(self):
        if not hasattr(self, 'voice_thread'):
            return
        if self.is_recording:
            self.voice_thread.stop_recording()
        else:
            context = {
                'generate_response': False,
                'chat_history': getattr(self, 'chat_history', []),
                'current_tasks': getattr(self, 'current_tasks', []),
            }
            self.voice_thread.set_context(context)
            self.voice_thread.start_recording()

    def _on_recording_started(self):
        self.is_recording = True
        self.mic_button.setProperty("recording", True)
        self.mic_button.style().unpolish(self.mic_button)
        self.mic_button.style().polish(self.mic_button)
        self.mic_button.setToolTip("Recording... Click to stop")
        self.voice_status_label.setText("🔴 Recording... Click mic to stop")
        self.voice_status_label.show()

    def _on_recording_stopped(self):
        self.is_recording = False
        self.mic_button.setProperty("recording", False)
        self.mic_button.style().unpolish(self.mic_button)
        self.mic_button.style().polish(self.mic_button)
        self.mic_button.setToolTip("Click to record voice input")
        self.voice_status_label.setText("⏳ Processing audio...")

    def _on_processing_started(self):
        self.voice_status_label.setText("🤖 Sending to Agent...")

    def _on_processing_finished(self):
        self.voice_status_label.setText("")

    def _on_transcription_ready(self, text):
        current_text = self.input_area.toPlainText().strip()
        if current_text:
            self.input_area.setPlainText(current_text + " " + text)
        else:
            self.input_area.setPlainText(text)
        cursor = self.input_area.textCursor()
        cursor.movePosition(cursor.End)
        self.input_area.setTextCursor(cursor)
        self.voice_status_label.setText("✅ Transcription complete")
        QTimer.singleShot(2000, self.voice_status_label.hide)

    def _on_voice_error(self, error_msg):
        self.is_recording = False
        self.mic_button.setProperty("recording", False)
        self.mic_button.style().unpolish(self.mic_button)
        self.mic_button.style().polish(self.mic_button)
        self.voice_status_label.setText(f"❌ {error_msg}")
        self.voice_status_label.show()
        QTimer.singleShot(4000, self.voice_status_label.hide)

    def _force_minimize(self):
        try:
            print(f"🔽 Dialog {self.dialog_id}: Forcing minimize...")
            self.setWindowState(Qt.WindowMinimized)
            if hasattr(self, 'windowHandle') and self.windowHandle():
                self.windowHandle().setWindowState(Qt.WindowMinimized)
            QTimer.singleShot(50, self._force_minimize_fallback)
        except Exception as e:
            print(f"Error in force minimize: {e}")
            self._emergency_minimize()

    def _force_minimize_fallback(self):
        try:
            if self.windowState() != Qt.WindowMinimized:
                print("Standard minimize blocked, using fallback...")
                self.lower()
                self.setWindowState(Qt.WindowMinimized)
                QTimer.singleShot(100, self._emergency_minimize)
        except Exception as e:
            print(f"Fallback minimize failed: {e}")
            self._emergency_minimize()

    def _emergency_minimize(self):
        if self.windowState() != Qt.WindowMinimized:
            print("All minimize attempts failed, hiding window as emergency measure")
            self.hide()

    def _force_close(self):
        try:
            print(f"❌ Dialog {self.dialog_id}: Force closing...")
            # Immediately terminate all background processing
            self.cleanup_all_processing()
            self.setParent(None)
            self.close()
        except Exception as e:
            print(f"Error in force close: {e}")
            # Ensure cleanup even if close fails
            self.cleanup_all_processing()
            self.hide()

    def create_shadow_effect(self):
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(20)
        shadow.setXOffset(0)
        shadow.setYOffset(5)
        shadow.setColor(QColor(0, 0, 0, 100))
        return shadow

    # Legacy methods for compatibility
    def speak_text(self, text):
        """Legacy method - redirects to advanced method"""
        self.speak_text_advanced(text)

    def start_speaking_response(self, response_text):
        """Legacy method - use advanced method"""
        self.response_text_widget.setPlainText(response_text)
        self.speak_text_advanced(response_text)

    def accept(self):
        self.result = self.input_area.toPlainText()
        self.accepted_signal.emit(self.result)
        self.close()