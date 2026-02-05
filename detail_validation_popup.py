import sys
import os
import time
import threading
import tempfile
import asyncio
import edge_tts
import pygame
from queue import Queue, Empty
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *
import subprocess
from interactive_response import GeminiSessionService
def resource_path(relative_path):
    """Get absolute path to resource, works for dev and for PyInstaller"""
    if hasattr(sys, "_MEIPASS"):
        return os.path.join(sys._MEIPASS, relative_path)
    return os.path.join(os.path.abspath("."), relative_path)
class IsolatedSpeechManager:
    """Isolated speech manager for each dialog instance using Edge TTS Jenny voice"""
    
    def __init__(self, dialog_id):
        self.dialog_id = dialog_id
        self.is_speaking = False
        self.speech_queue = Queue()
        self.speech_thread = None
        self.stop_speaking = False
        self.has_spoken = False
        
        # Initialize pygame mixer for audio playback
        try:
            pygame.mixer.init(frequency=22050, size=-16, channels=2, buffer=1024)
            print(f"🎤 Created isolated speech manager for dialog {dialog_id} with Edge TTS Jenny")
        except Exception as e:
            print(f"❌ Dialog {dialog_id}: Failed to initialize pygame mixer: {e}")
    
    def speak_async(self, text, callback=None, force=False):
        if not text or not text.strip():
            print(f"⚠️ Dialog {self.dialog_id}: Empty text provided for speech")
            return
        
        if self.has_spoken and not force:
            print(f"🔇 Dialog {self.dialog_id}: Already spoken, skipping automatic speech")
            return
        
        self._clear_queue()
        print(f"🎤 Dialog {self.dialog_id}: Queueing new text: {text[:50]}...")
        self.speech_queue.put((text.strip(), callback))
        self._start_speech_processor()
    
    def _clear_queue(self):
        while not self.speech_queue.empty():
            try:
                self.speech_queue.get_nowait()
            except Empty:
                break
    
    def _start_speech_processor(self):
        if self.speech_thread and self.speech_thread.is_alive():
            print(f"🎤 Dialog {self.dialog_id}: Speech thread already running, stopping it first...")
            self.stop_speaking = True
            time.sleep(0.2)
            self.stop_speaking = False
        
        self.speech_thread = threading.Thread(target=self._speech_processor, daemon=True)
        self.speech_thread.start()
        print(f"🎤 Dialog {self.dialog_id}: Started new speech processor thread")
    
    def _speech_processor(self):
        while True:
            try:
                speech_data = self.speech_queue.get(timeout=1.0)
                if speech_data is None:
                    break
                
                text, callback = speech_data
                print(f"🎤 Dialog {self.dialog_id}: Processing speech: {text[:50]}...")
                success = self._execute_speech(text, callback)
                
                if success:
                    self.has_spoken = True
                
                break
                
            except Empty:
                break
            except Exception as e:
                print(f"❌ Dialog {self.dialog_id}: Speech processor error: {e}")
                break
    
    def _execute_speech(self, text, callback=None):
        self.is_speaking = True
        success = False
        
        print(f"🎤 Dialog {self.dialog_id}: Attempting to speak with Edge TTS Jenny: {text[:50]}...")
        
        if not self.stop_speaking:
            success = self._try_edge_tts(text)
        
        # Fallback methods if Edge TTS fails
        if not success and not self.stop_speaking:
            success = self._try_pyttsx3_isolated(text)
        
        if not success and not self.stop_speaking and sys.platform == "win32":
            success = self._try_windows_sapi(text)
        
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
    
    def _try_edge_tts(self, text):
        """Use Microsoft Edge TTS with Jenny voice"""
        try:
            # Create a temporary file for the audio
            with tempfile.NamedTemporaryFile(delete=False, suffix='.mp3') as temp_file:
                temp_path = temp_file.name
            
            async def generate_speech():
                # Use Jenny voice (US English female voice)
                voice = "en-US-JennyNeural"
                communicate = edge_tts.Communicate(text, voice)
                await communicate.save(temp_path)
            
            # Run the async function
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            loop.run_until_complete(generate_speech())
            loop.close()
            
            # Play the generated audio file
            if os.path.exists(temp_path) and os.path.getsize(temp_path) > 0:
                pygame.mixer.music.load(temp_path)
                pygame.mixer.music.play()
                
                # Wait for playback to complete
                while pygame.mixer.music.get_busy():
                    if self.stop_speaking:
                        pygame.mixer.music.stop()
                        break
                    time.sleep(0.1)
                
                # Clean up
                try:
                    os.unlink(temp_path)
                except:
                    pass
                
                if not self.stop_speaking:
                    print(f"✅ Dialog {self.dialog_id}: Edge TTS Jenny method succeeded")
                    return True
                else:
                    print(f"🛑 Dialog {self.dialog_id}: Edge TTS playback stopped")
                    return False
            else:
                print(f"❌ Dialog {self.dialog_id}: Edge TTS failed to generate audio file")
                return False
                
        except Exception as e:
            print(f"❌ Dialog {self.dialog_id}: Edge TTS method failed: {e}")
            # Clean up temp file if it exists
            try:
                if 'temp_path' in locals():
                    os.unlink(temp_path)
            except:
                pass
            return False
    
    def _try_pyttsx3_isolated(self, text):
        try:
            script_content = f"""
import sys
import os
sys.path.insert(0, os.getcwd())

try:
    import pyttsx3
    engine = pyttsx3.init()
    
    voices = engine.getProperty('voices')
    if voices:
        for voice in voices:
            if 'jenny' in voice.name.lower() or 'female' in voice.name.lower():
                engine.setProperty('voice', voice.id)
                break
        else:
            engine.setProperty('voice', voices[0].id)
    
    engine.setProperty('rate', 180)
    engine.setProperty('volume', 1.0)
    
    engine.say({repr(text)})
    engine.runAndWait()
    engine.stop()
    
    print("SUCCESS")
except Exception as e:
    print(f"ERROR: {{e}}")
    sys.exit(1)
"""
            script_path = f"temp_speech_script_{self.dialog_id}_{int(time.time())}.py"
            with open(script_path, 'w', encoding='utf-8') as f:
                f.write(script_content)
            
            print(f"🎤 Dialog {self.dialog_id}: Executing isolated pyttsx3 script: {script_path}")
            
            result = subprocess.run([sys.executable, script_path], 
                                  capture_output=True, text=True, timeout=15)
            
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
        if sys.platform != "win32":
            return False
        
        try:
            escaped_text = text.replace('"', '`"').replace("'", "''")
            ps_command = f'''
Add-Type -AssemblyName System.Speech
$synth = New-Object System.Speech.Synthesis.SpeechSynthesizer
$synth.Rate = 2
$synth.Volume = 100
$voices = $synth.GetInstalledVoices()
foreach ($voice in $voices) {{
    if ($voice.VoiceInfo.Name -like "*Jenny*" -or $voice.VoiceInfo.Gender -eq "Female") {{
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
        try:
            if sys.platform == "win32":
                command = ["powershell", "-Command", f'(New-Object -ComObject SAPI.SpVoice).Speak("{text}")']
            elif sys.platform == "darwin":
                command = ["say", text]
            else:
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
        print(f"🛑 Dialog {self.dialog_id}: Stopping all speech...")
        self.stop_speaking = True
        self._clear_queue()
        
        # Stop pygame mixer if it's playing
        try:
            if pygame.mixer.music.get_busy():
                pygame.mixer.music.stop()
        except:
            pass
            
        time.sleep(0.1)
        self.stop_speaking = False
    
    def reset_speech_flag(self):
        self.has_spoken = False

class SpeechWorker(QThread):
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
            
            print(f"🎤 SpeechWorker {self.dialog_id}: Starting Edge TTS Jenny speech for: {self.text[:30]}...")
            self.speech_manager.speak_async(self.text, callback, self.force)
            
            start_time = time.time()
            while self.speech_manager.is_speaking and (time.time() - start_time) < 30:
                time.sleep(0.1)
            
            time.sleep(0.5)
            
            if success[0]:
                self.success.emit()
            else:
                self.error.emit("Speech failed")
                
        except Exception as e:
            self.error.emit(str(e))
        finally:
            self.finished.emit()

class UnifiedValidationPopup(QMainWindow):
    """Unified popup combining validation logs and detail mode"""
    
    detail_mode_response = pyqtSignal(int, str)
    validation_completed = pyqtSignal()
    
    def __init__(self, parent=None, gemini_service=None):
        super().__init__(parent)
        self.gemini_service = gemini_service or getattr(parent, 'gemini_service', None)
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setFixedSize(1200, 700)
        
        self.dialog_id = id(self)  # Unique ID for this instance
        self.speech_manager = IsolatedSpeechManager(self.dialog_id)
        self.current_speech_worker = None
        self.initial_speech_completed = False
        
        self.load_popup_styles()
        
        screen = QApplication.primaryScreen().availableGeometry()
        x = (screen.width() - self.width()) // 2
        y = (screen.height() - self.height()) // 2
        self.move(x, y)
        
        self.setup_ui()
        self.current_task_index = -1
        self.current_task_name = ""
        self._detail_mode_lock = False
        self._detail_mode_active = False
        self._first_detail_mode = True
        self._initialize_voice_integration()
        
    def setup_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        main_container = QFrame()
        main_container.setObjectName("mainContainer")

        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.addWidget(main_container)

        main_container.setStyleSheet("""
            QFrame#mainContainer {
                background: #000000;
                border: 2px solid rgba(128, 128, 128, 0.08); 
                border-radius: 20px;
                margin: 10px;
            }
        """)
        main_container.update()

        container_layout = QVBoxLayout(main_container)
        container_layout.setContentsMargins(15, 10, 15, 15)
        container_layout.setSpacing(10)

        self.setup_header(container_layout)

        content_layout = QHBoxLayout()
        content_layout.setSpacing(15)

        self.setup_detail_mode_area(content_layout)
        self.setup_validation_logs_area(content_layout)

        container_layout.addLayout(content_layout)
    def setup_header(self, parent_layout):
        header_layout = QHBoxLayout()
        header_layout.setContentsMargins(0, 0, 0, 0)
        
        title_label = QLabel(" Validation & Detail Mode")
        title_label.setObjectName("popupTitle")
        title_label.setStyleSheet("color: white;")
        header_layout.addWidget(title_label)
        
        header_layout.addStretch()
        
        self.minimize_btn = QPushButton("−")
        self.minimize_btn.setFixedSize(35, 35)
        self.minimize_btn.setObjectName("minimizeBtn")
        self.minimize_btn.clicked.connect(self.showMinimized)
        self.minimize_btn.setStyleSheet("""
            QPushButton#minimizeBtn {
                background: transparent !important;
                border: none !important;
                color: white !important;
                font-weight: bold !important;
                font-size: 18px !important;
            }
            QPushButton#minimizeBtn:hover {
                background: red !important;
                border-radius: 17px !important;
            }
            QPushButton#minimizeBtn:pressed {
                background: red !important;
                border-radius: 17px !important;
            }
        """)

        self.close_btn = QPushButton("×")
        self.close_btn.setFixedSize(35, 35)
        self.close_btn.setObjectName("closeBtn")
        self.close_btn.clicked.connect(self._force_close)
        self.close_btn.setStyleSheet("""
            QPushButton#closeBtn {
                background: transparent !important;
                border: none !important;
                color: white !important;
                font-weight: bold !important;
                font-size: 18px !important;
            }
            QPushButton#closeBtn:hover {
                background: red !important;
                border-radius: 17px !important;
            }
            QPushButton#closeBtn:pressed {
                background: red !important;
                border-radius: 17px !important;
            }
        """)

        header_layout.addWidget(self.minimize_btn)
        header_layout.addWidget(self.close_btn)
        parent_layout.addLayout(header_layout)
        
    def load_popup_styles(self):
        try:
            current_dir = os.path.dirname(os.path.abspath(__file__))
            # qss_path = os.path.join(current_dir, "popup_styles.qss")
            qss_path = resource_path("styles/popup_styles.qss")
            if os.path.exists(qss_path):
                with open(qss_path, 'r', encoding='utf-8') as f:
                    stylesheet = f.read()
                self.setStyleSheet(stylesheet)
            else:
                print(f"Warning: popup_styles.qss not found at {qss_path}")
        except Exception as e:
            print(f"Error loading popup styles: {e}")
        
    def setup_detail_mode_area(self, parent_layout):
        detail_container = QFrame()
        detail_container.setFixedWidth(580)
        detail_container.setObjectName("detailContainer")
        
        detail_layout = QVBoxLayout(detail_container)
        detail_layout.setContentsMargins(15, 15, 15, 15)
        detail_layout.setSpacing(10)
        
        detail_header = QLabel("Detail Mode")
        detail_header.setObjectName("detailHeader")
        detail_header.setAlignment(Qt.AlignCenter) 
        detail_layout.addWidget(detail_header)
        detail_header.setStyleSheet("""
        QLabel#detailHeader {
            background: black;
            
        }
    """)

        
        
        self.detail_placeholder = QLabel(" Detailing Mode")
        self.detail_placeholder.setAlignment(Qt.AlignCenter)
        self.detail_placeholder.setObjectName("detailPlaceholder")
        self.detail_placeholder.setStyleSheet("""
        QLabel#detailPlaceholder {
            background-color: black;
            color: white;
            border-radius: 6px;
            padding: 5px;
        }
    """)
        detail_layout.addWidget(self.detail_placeholder)
        
        self.detail_form_widget = QWidget() 
        self.detail_form_widget.setVisible(False)
        self.setup_detail_form(self.detail_form_widget)
        detail_layout.addWidget(self.detail_form_widget)
        
        parent_layout.addWidget(detail_container)
        
    def setup_detail_form(self, parent_widget):
        form_layout = QVBoxLayout(parent_widget)
        form_layout.setContentsMargins(0, 0, 0, 0)
        form_layout.setSpacing(15)
        
        # Container 1: System Information (Droid Response, Task Number, Message Area)
        system_container = QFrame()
        system_container.setObjectName("systemInfoContainer")
        system_container.setStyleSheet("""
            QFrame#systemInfoContainer {
                background: black !important;
                border: 3px solid rgba(78, 205, 196, 0.6) !important;
                border-radius: 15px !important;
                margin: 10px 0 !important;
                padding: 5px !important;
            }
        """)
        system_layout = QVBoxLayout(system_container)
        system_layout.setContentsMargins(15, 15, 15, 15)
        system_layout.setSpacing(10)

        self.system_label = QLabel("Droid Response")
        self.system_label.setObjectName("systemLabel")
        self.system_label.setStyleSheet("""
            QLabel#systemLabel {
                background: transparent !important;
                border: none !important;
                padding: 8px 0 !important;
                margin: 0 !important;
                color: white !important;
                font-family: 'Asen Pro', 'Segoe UI', Arial, sans-serif !important;
                font-size: 16px !important;
                font-weight: 600 !important;
            }
        """)
        system_layout.addWidget(self.system_label)

        self.task_num_box = QLabel("Task: –")
        self.task_num_box.setObjectName("taskNumBox")
        self.task_num_box.setStyleSheet("""
            QLabel#taskNumBox {
                background: transparent;
                border: none;
                padding: 4px 0;
                color: white;
                font-family: 'Asen Pro'; 
                font-weight: bold;
                font-size: 14px;
            }
        """)
        system_layout.addWidget(self.task_num_box)

        self.system_response_text = QTextEdit()
        self.system_response_text.setFixedHeight(100)
        self.system_response_text.setReadOnly(True)
        self.system_response_text.setObjectName("systemResponse")
        self.system_response_text.setStyleSheet("""
            QTextEdit#systemResponse {
                background: grey !important; /* Changed to grey */
                border: 1px solid rgba(78, 205, 196, 0.2);
                border-radius: 8px;
                color: white;
                font-family: 'Asen Pro', 'Segoe UI', Arial, sans-serif;
                font-size: 13px;
                padding: 10px;
                selection-background-color: rgba(78, 205, 196, 0.3);
                line-height: 1.4;
            }
            QTextEdit#systemResponse:focus {
                border: 1px solid rgba(78, 205, 196, 0.4);
                background: rgba(20, 25, 30, 0.8);
            }
        """)
        system_layout.addWidget(self.system_response_text)

        form_layout.addWidget(system_container)
        
        # Container 2: User Response (Header, Text Area, Voice Status, Buttons)
        user_container = QFrame()
        user_container.setObjectName("userResponseContainer")
        user_container.setStyleSheet("""
            QFrame#userResponseContainer {
                background: black !important; /* Changed to black */
                border: 3px solid rgba(78, 205, 196, 0.6) !important;
                border-radius: 15px !important;
                margin: 10px 0 !important;
                padding: 5px !important;
            }
        """)
        user_layout = QVBoxLayout(user_container)
        user_layout.setContentsMargins(15, 15, 15, 15)
        user_layout.setSpacing(10)
        
        user_label = QLabel("Your Detailed Response")
        user_label.setObjectName("userLabel")
        user_label.setStyleSheet("""
            QLabel#userLabel {
                background: transparent !important;
                border: none !important;
                padding: 8px 0 !important;
                margin: 0 !important;
                color: white !important; /* Changed to white */
                font-family: 'Asen Pro', 'Segoe UI', Arial, sans-serif !important;
                font-size: 16px !important;
                font-weight: 600 !important;
            }
        """)
        user_layout.addWidget(user_label)
        
        self.user_response_text = QTextEdit()
        self.user_response_text.setFixedHeight(110)
        self.user_response_text.setPlaceholderText(" Type your detailed response or use the microphone...")
        self.user_response_text.setObjectName("userResponse")
        self.user_response_text.setStyleSheet("""
            QTextEdit#userResponse {
            background: grey !important;
            border: 1px solid rgba(78, 205, 196, 0.2);
            border-radius: 8px;
            color: white; /* For entered text */
            font-family: 'Asen Pro', 'Segoe UI', Arial, sans-serif;
            font-size: 13px;
            padding: 10px;
            selection-background-color: rgba(78, 205, 196, 0.3);
            line-height: 1.4;
        }
        QTextEdit#userResponse::placeholder {
            color: white !important; /* Explicitly set placeholder text to white */
        }
        QTextEdit#userResponse:focus {
            border: 1px solid rgba(78, 205, 196, 0.4);
            background: rgba(20, 25, 30, 0.8);
        }
    """)
        user_layout.addWidget(self.user_response_text)
        
        # Voice status label
        status_container = QWidget()
        status_layout = QVBoxLayout(status_container)
        status_layout.setContentsMargins(0, 0, 0, 0)
        status_layout.setSpacing(0)
        
        self.voice_status_label = QLabel("")
        self.voice_status_label.setProperty('class', 'ChatVoiceStatus')
        self.voice_status_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.voice_status_label.setFixedHeight(20)
        self.voice_status_label.setStyleSheet("""
            QLabel {
                color: #888888;
                font-family: 'Asen Pro'; 
                font-size: 12px;
                padding: 2px 5px;
                margin-left: 12px;
            }
        """)
        status_layout.addWidget(self.voice_status_label)
        user_layout.addWidget(status_container)
        
        button_layout = QHBoxLayout()
        
        self.mic_btn = QPushButton()
        self.mic_btn.setFixedSize(45, 45)
        self.mic_btn.setToolTip("Click to record voice input")
        self.mic_btn.setIcon(QIcon("styles/Icon/microphone.png"))
        self.mic_btn.setIconSize(QSize(24, 24))
        self.mic_btn.setStyleSheet("""
            QPushButton {
                background-color: rgba(42,42,42,220);
                border: 1px solid #404040;
                border-radius: 20px;
                font-family: 'Asen Pro'; 
                padding: 4px;
            }
            QPushButton:hover {
                background-color: rgba(58,58,58,240);
                border-color: #0ea5e9;
            }
            QPushButton:pressed {
                background-color: rgba(74,74,74,240);
            }
            QPushButton[recording="true"] {
                background-color: rgba(220,38,38,240);
                border-color: #ef4444;
            }
            QPushButton[recording="true"]:hover {
                background-color: rgba(185,28,28,240);
            }
        """)
        self.mic_btn.clicked.connect(self._toggle_voice_recording)
        button_layout.addWidget(self.mic_btn)
        
        button_layout.addStretch()
        
        self.send_btn = QPushButton("Send")
        self.send_btn.setFixedSize(50, 40)
        self.send_btn.setObjectName("sendBtn")
        self.send_btn.clicked.connect(self.on_send_clicked)
        
        button_layout.addWidget(self.send_btn)
        
        user_layout.addLayout(button_layout)
        form_layout.addWidget(user_container)
        
    def setup_validation_logs_area(self, parent_layout):
        logs_container = QFrame()
        logs_container.setObjectName("logsContainer")
        
        logs_layout = QVBoxLayout(logs_container)
        logs_layout.setContentsMargins(15, 15, 15, 15)
        logs_layout.setSpacing(10)
        
        header_layout = QHBoxLayout()
        
        logs_header = QLabel("Validation Logs")
        logs_header.setObjectName("logsHeader")
        header_layout.addWidget(logs_header)
        
        header_layout.addStretch()
        
        self.progress_label = QLabel("0/0")
        self.progress_label.setObjectName("progressLabel")
        self.progress_label.setStyleSheet("""
            QLabel#progressLabel {
                background: transparent !important;
                color: white !important; /* Ensure text is readable against black background */
                border: none !important;
                padding: 0 !important;
                margin: 0 !important;
            }
        """)
        header_layout.addWidget(self.progress_label)
        
        logs_layout.addLayout(header_layout)
        
        self.progress_bar = QProgressBar()
        self.progress_bar.setFixedHeight(12)
        self.progress_bar.setObjectName("validationProgress")
        self.progress_bar.setStyleSheet("""
            QProgressBar#validationProgress {
                border: none;
                border-radius: 6px;  /* Rounded edges */
                background-color: rgba(0, 0, 0, 0.8);
                height: 12px;
                min-height: 12px;
                max-height: 12px;
            }
            QProgressBar#validationProgress::chunk {
                border-radius: 6px;  /* Match with parent radius */
                background: qlineargradient(
                    spread:pad, x1:0, y1:0, x2:1, y2:0,
                    stop:0 #004361,
                    stop:0.39 #00BAF1,
                    stop:0.55 #5ECBF4
                );
                margin: 0px;
                box-shadow: 0px 0px 6px #57C8E8; /* Glow effect */
            }
        """)
        logs_layout.addWidget(self.progress_bar)
        
        self.logs_display = QTextEdit()
        self.logs_display.setReadOnly(True)
        self.logs_display.setObjectName("logsDisplay")
        self.logs_display.setStyleSheet("""
    QTextEdit#logsDisplay {
        background: black !important;
        border: 2px solid rgba(78, 205, 196, 0.2);
        border-radius: 8px;
        color: white;
        font-family: 'Asen Pro', 'Segoe UI', Arial, sans-serif;
        font-size: 13px;
        padding: 15px;
    }
    QTextEdit#logsDisplay QScrollBar:vertical {
        background: #1e1e1e;
        width: 10px;
        margin: 0px;
        border-radius: 5px;
    }
    QTextEdit#logsDisplay QScrollBar::handle:vertical {
        background: #474747;   /* scrollbar handle color */
        border-radius: 5px;
        min-height: 20px;
    }
    QTextEdit#logsDisplay QScrollBar::add-line:vertical,
    QTextEdit#logsDisplay QScrollBar::sub-line:vertical {
        background: none;
        border: none;
        height: 0px;
    }
""")

        logs_layout.addWidget(self.logs_display)
        
        parent_layout.addWidget(logs_container)
        
    def _initialize_voice_integration(self):
        try:
            from voice_integration_thread import VoiceIntegrationThread
            import config
            GEMINI_API_KEY = getattr(config, 'API_KEY', None)
            if not GEMINI_API_KEY:
                print(f"⚠️ Dialog {self.dialog_id}: No Gemini API key found in config")
                return
            self.voice_thread = VoiceIntegrationThread(GEMINI_API_KEY)
            self.voice_thread.recording_started.connect(self._on_recording_started)
            self.voice_thread.recording_stopped.connect(self._on_recording_stopped)
            self.voice_thread.transcription_ready.connect(self._on_transcription_ready)
            self.voice_thread.error_occurred.connect(self._on_voice_error)
            self.voice_thread.processing_started.connect(self._on_processing_started)
            self.voice_thread.processing_finished.connect(self._on_processing_finished)
            self.is_recording = False
            print(f"✅ Dialog {self.dialog_id}: Voice integration initialized successfully")
        except Exception as e:
            print(f"❌ Dialog {self.dialog_id}: Voice integration failed: {e}")
            self.mic_btn.setEnabled(False)
            self.mic_btn.setToolTip("Voice integration unavailable")
    
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
        self.mic_btn.setProperty("recording", True)
        self.mic_btn.style().unpolish(self.mic_btn)
        self.mic_btn.style().polish(self.mic_btn)
        self.mic_btn.setToolTip("Recording... Click to stop")
        self.voice_status_label.setText("🔴 Recording... Click mic to stop")
        self.voice_status_label.show()
    
    def _on_recording_stopped(self):
        self.is_recording = False
        self.mic_btn.setProperty("recording", False)
        self.mic_btn.style().unpolish(self.mic_btn)
        self.mic_btn.style().polish(self.mic_btn)
        self.mic_btn.setToolTip("Click to record voice input")
        self.voice_status_label.setText("⏳ Processing audio...")
    
    def _on_processing_started(self):
        self.voice_status_label.setText("🤖 Sending to Agent...")
    
    def _on_processing_finished(self):
        self.voice_status_label.setText("")
    
    def _on_transcription_ready(self, text):
        current_text = self.user_response_text.toPlainText().strip()
        if current_text:
            self.user_response_text.setPlainText(current_text + " " + text)
        else:
            self.user_response_text.setPlainText(text)
        cursor = self.user_response_text.textCursor()
        cursor.movePosition(cursor.End)
        self.user_response_text.setTextCursor(cursor)
        self.voice_status_label.setText("✅ Transcription complete")
        QTimer.singleShot(2000, self.voice_status_label.hide)
    
    def _on_voice_error(self, error_msg):
        self.is_recording = False
        self.mic_btn.setProperty("recording", False)
        self.mic_btn.style().unpolish(self.mic_btn)
        self.mic_btn.style().polish(self.mic_btn)
        self.voice_status_label.setText(f"❌ {error_msg}")
        self.voice_status_label.show()
        QTimer.singleShot(4000, self.voice_status_label.hide)
    
    def speak_text_advanced(self, text, force=False):
        if not text or not text.strip():
            print(f"⚠️ Dialog {self.dialog_id}: No text provided for speech")
            return
        
        if self.initial_speech_completed and not force:
            print(f"🔇 Dialog {self.dialog_id}: Initial speech already completed, use manual trigger")
            return
        
        print(f"🎤 Dialog {self.dialog_id}: Starting advanced speech for: {text[:50]}...")
        
        if self.current_speech_worker and self.current_speech_worker.isRunning():
            print(f"🛑 Dialog {self.dialog_id}: Stopping previous speech worker...")
            self.current_speech_worker.terminate()
            self.current_speech_worker.wait(1000)
        
        self.current_speech_worker = SpeechWorker(text, self.dialog_id, force)
        self.current_speech_worker.success.connect(lambda: print(f"✅ Dialog {self.dialog_id}: Speech completed successfully"))
        self.current_speech_worker.error.connect(lambda err: print(f"❌ Dialog {self.dialog_id}: Speech error: {err}"))
        self.current_speech_worker.finished.connect(lambda: print(f"📢 Dialog {self.dialog_id}: Speech worker finished"))
        
        self.current_speech_worker.start()
    
    def cleanup_speech(self):
        print(f"🔧 Dialog {self.dialog_id}: Cleaning up speech resources...")
        
        if self.current_speech_worker and self.current_speech_worker.isRunning():
            self.current_speech_worker.terminate()
            self.current_speech_worker.wait(2000)
        
        self.speech_manager.stop_all_speech()
        
        if hasattr(self, 'voice_thread'):
            try:
                self.voice_thread.cleanup()
            except Exception as e:
                print(f"Error cleaning up voice thread: {e}")
                
        print(f"🔧 Dialog {self.dialog_id}: Speech resources cleaned up")
    
    def set_total_tasks(self, total):
        self.total_tasks = total
        self.completed_tasks = 0
        self.progress_bar.setRange(0, total)
        self.progress_bar.setValue(0)
        self.progress_label.setText(f"0/{total}")
        
    def add_log(self, message, log_type="info"):
        timestamp = QTime.currentTime().toString("hh:mm:ss")
        colors = {
            "info": "#81A1C1",
            "success": "#A3BE8C", 
            "warning": "#EBCB8B",
            "error": "#BF616A",
            "debug": "#B48EAD"
        }
        color = colors.get(log_type, "#D8DEE9")
        formatted_message = f'<span style="color: #4C566A;">[{timestamp}]</span> <span style="color: {color};">{message}</span>'
        self.logs_display.append(formatted_message)
        scrollbar = self.logs_display.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())
        print(f"LOG [{timestamp}] {log_type.upper()}: {message}")
        
    def set_progress(self, completed):
        self.completed_tasks = completed
        self.progress_bar.setValue(completed)
        self.progress_label.setText(f"{completed}/{self.total_tasks}")

    def speak_validation_message(self, text, force=False):
        """
        Speak a message when starting or updating validation logs,
        with proper sequencing to avoid conflicts.
        """
        # Add it visually to the logs
        self.add_log(text, "info")
        QApplication.processEvents()

        # Reset speech state so we don't get blocked
        if hasattr(self, 'speech_manager'):
            self.speech_manager.reset_speech_flag()
            self.initial_speech_completed = False

        # Store the validation message for later sequential speaking
        self._pending_validation_message = text
        
        # Speak immediately with a unique identifier
        QTimer.singleShot(
            300,  # Reduced delay for faster response
            lambda: self._speak_validation_message_now(text, force=force)
        )

    def _speak_validation_message_now(self, text, force=False):
        """Internal method to handle validation message speech"""
        try:
            print(f"🎤 VALIDATION: Speaking validation message: {text[:50]}...")
            self.speak_text_advanced(text, force=force)
            
            # Mark that validation speech is in progress
            self._validation_speech_active = True
            
            # Set a timer to mark speech as completed
            QTimer.singleShot(
                len(text) * 100 + 1000,  # Estimate speech duration + buffer
                self._mark_validation_speech_complete
            )
            
        except Exception as e:
            print(f"❌ Error speaking validation message: {e}")
            self._validation_speech_active = False

    def _mark_validation_speech_complete(self):
        """Mark validation speech as completed"""
        self._validation_speech_active = False
        print("✅ VALIDATION: Validation message speech completed")

    def show_detail_mode_for_task(self, task_index, system_response, task_name):
        print(f"🔧 DEBUG: *** SHOW_DETAIL_MODE_FOR_TASK CALLED FOR TASK {task_index + 1} ***")
        print(f"🔧 DEBUG: Detail mode active: {self._detail_mode_active}, First detail mode: {self._first_detail_mode}")
        
        self.set_progress(task_index + 1)
        
        if self._detail_mode_active:
            print(f"🔧 DEBUG: Detail mode already active, just updating content for task {task_index + 1}")
            self.current_task_index = task_index
            self.current_task_name = task_name

            task_num = task_index + 1
            print("DEBUG TaskNumBox setting:", task_num)
            self.task_num_box.setText(f"Task : {task_name}")
            self.task_num_box.adjustSize()
            self.task_num_box.repaint()

            self.system_response_text.setPlainText(system_response)
            self.user_response_text.clear()
            self.user_response_text.setFocus()
            
            task_preview = task_name[:50] + "..." if len(task_name) > 50 else task_name
            self.add_log(f"⚠️ Task {task_index + 1} needs correction: {task_preview}", "warning")
            
            # Wait for any pending validation speech to complete before speaking system response
            self._schedule_system_response_speech(system_response,self.gemini_service)
            return
        
        retry_count = 0
        while self._detail_mode_lock and retry_count < 10:
            print(f"🔧 DEBUG: Detail mode locked, waiting... (attempt {retry_count + 1})")
            QApplication.processEvents()
            time.sleep(0.1)
            retry_count += 1
            
        if self._detail_mode_lock:
            print(f"🔧 DEBUG: Detail mode still locked after waiting, forcing unlock")
            self._detail_mode_lock = False
            
        self._detail_mode_lock = True
        print(f"🔧 DEBUG: First time showing detail mode for task {task_index + 1} (LOCKED)")
        print(f"🔧 DEBUG: Current widget states - placeholder visible: {self.detail_placeholder.isVisible()}, form visible: {self.detail_form_widget.isVisible()}")
        
        self.current_task_index = task_index
        self.current_task_name = task_name

        task_num = task_index + 1
        print("DEBUG TaskNumBox setting:", task_num)
        self.task_num_box.setText(f"Task number: {task_name}")
        self.task_num_box.adjustSize()
        self.task_num_box.repaint()

        print(f"🔧 DEBUG: Setting form visibility - hiding placeholder, showing form")
        self.detail_placeholder.hide()
        self.detail_form_widget.show()
        
        self._detail_mode_active = True
        self._first_detail_mode = False
        
        print(f"🔧 DEBUG: After state change - placeholder visible: {self.detail_placeholder.isVisible()}, form visible: {self.detail_form_widget.isVisible()}")
        
        self.system_response_text.setPlainText(system_response)
        print(f"🔧 DEBUG: Set system response text: {system_response[:100]}...")
        
        self.user_response_text.clear()
        self.user_response_text.setFocus()
        
        task_preview = task_name[:50] + "..." if len(task_name) > 50 else task_name
        self.add_log(f"⚠️ Task {task_index + 1} needs correction: {task_preview}", "warning")
        
        self.detail_form_widget.update()
        self.detail_form_widget.repaint()
        self.update()
        self.repaint()
        
        QApplication.processEvents()
        
        self._detail_mode_lock = False
        
        # Wait for any pending validation speech to complete before speaking system response
        self._schedule_system_response_speech(system_response,self.gemini_service)
        
        print(f"🔧 DEBUG: Detail mode form now visible for task {task_index + 1} (UNLOCKED)")
        print(f"🔧 DEBUG: Final widget states - placeholder visible: {self.detail_placeholder.isVisible()}, form visible: {self.detail_form_widget.isVisible()}")
        print(f"🔧 DEBUG: Detail mode will stay active for subsequent tasks (no more hide operations)")
        print(f"🔧 DEBUG: *** SHOW_DETAIL_MODE_FOR_TASK COMPLETED FOR TASK {task_index + 1} ***")

    def _schedule_system_response_speech(self, system_response, gemini_service=None):
        """Schedule system response speech after validation speech completes"""
        def check_and_speak():
            if hasattr(self, '_validation_speech_active') and self._validation_speech_active:
                print("🎤 SYSTEM: Waiting for validation speech to complete...")
                QTimer.singleShot(500, check_and_speak)
            else:
                print(f"🎤 SYSTEM: Preparing friendly system response for: {system_response[:50]}...")
                try:
                    friendly_response = gemini_service.get_task_correction_message(
                        self.current_task_index, 
                        self.current_task_name, 
                        system_response
                    )
                    friendly_message = friendly_response["message"]
                    print(f"🤖 Gemini system message: {friendly_message}")
                except Exception as e:
                    print(f"Error getting Gemini system message: {e}")
                    # Fallback to a friendlier version of the original message
                    friendly_message = f"Task {self.current_task_index + 1} needs a small adjustment: {system_response}"
                
                print(f"🎤 SYSTEM: Speaking friendly message: {friendly_message[:50]}...")
                self.speech_manager.reset_speech_flag()
                self.initial_speech_completed = False
                self.speak_text_advanced(friendly_message, force=False)
        
        # Start checking after a short delay
        QTimer.singleShot(500, check_and_speak)
           
    def hide_detail_mode(self):
        print(f"🔧 DEBUG: *** HIDE_DETAIL_MODE CALLED ***")
        print(f"🔧 DEBUG: Detail mode active: {self._detail_mode_active}")
        
        if self._detail_mode_active:
            print(f"🔧 DEBUG: Detail mode already active - hide operation disabled")
            print(f"🔧 DEBUG: Hide functionality only available at initial launch")
            return
        
        if self._detail_mode_lock:
            print(f"🔧 DEBUG: Detail mode locked, skipping hide operation")
            return
            
        self._detail_mode_lock = True
        import traceback
        print(f"🔧 DEBUG: Initial launch - hiding detail mode form (LOCKED)")
        print(f"🔧 DEBUG: Call stack:")
        for line in traceback.format_stack():
            print(f"  {line.strip()}")
        
        self.detail_form_widget.setVisible(False)
        self.detail_placeholder.setVisible(True)
        self.user_response_text.clear()
        self.system_response_text.clear()
        
        self.current_task_index = -1
        self.current_task_name = ""
        
        self.update()
        self.repaint()
        
        QApplication.processEvents()
        
        self._detail_mode_lock = False
        print(f"🔧 DEBUG: Initial hide completed - placeholder shown (UNLOCKED)")
        print(f"🔧 DEBUG: Detail mode active: {self._detail_mode_active}")
        print(f"🔧 DEBUG: Hide functionality will be disabled after first task validation")
        print(f"🔧 DEBUG: *** HIDE_DETAIL_MODE COMPLETED ***")
        
    def on_send_clicked(self):
        import traceback
        print(f"🔧 DEBUG: on_send_clicked called!")
        print(f"🔧 DEBUG: Call stack for on_send_clicked:")
        for line in traceback.format_stack():
            print(f"  {line.strip()}")
            
        user_input = self.user_response_text.toPlainText().strip()
        print(f"🔧 DEBUG: Send clicked, user_input length: {len(user_input)}, current_task_index: {getattr(self, 'current_task_index', 'None')}")
        
        if not user_input:
            print(f"🔧 DEBUG: No user input - ignoring automatic send trigger")
            self.add_log("⚠️ Please provide a response before sending", "warning")
            return
            
        if not hasattr(self, 'current_task_index') or self.current_task_index < 0:
            print(f"🔧 DEBUG: Invalid task index - ignoring send")
            return
            
        print(f"🔧 DEBUG: Emitting detail_mode_response signal for task {self.current_task_index + 1}")
        
        self.add_log(f"✅ User provided correction for Task {self.current_task_index + 1}", "success")
        
        self.detail_mode_response.emit(self.current_task_index, user_input)
        
        self.hide_detail_mode()
    
    def center_on_screen(self):
        from PyQt5.QtWidgets import QApplication
        screen = QApplication.desktop().screenGeometry()
        size = self.geometry()
        self.move(
            (screen.width() - size.width()) // 2,
            (screen.height() - size.height()) // 2
        )
        
    def _force_close(self):
        self.cleanup_speech()
        self.validation_completed.emit()
        self.close()
        
    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.drag_position = event.globalPos() - self.frameGeometry().topLeft()
            event.accept()
            
    def mouseMoveEvent(self, event):
        if event.buttons() == Qt.LeftButton and hasattr(self, 'drag_position'):
            self.move(event.globalPos() - self.drag_position)
            event.accept()

    def closeEvent(self, event):
        self.cleanup_speech()
        super().closeEvent(event)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    
    popup = UnifiedValidationPopup()
    popup.show()
    
    popup.set_total_tasks(5)
    popup.add_log(" Starting validation...", "info")
    popup.add_log("✅ Task 1 is valid", "success")
    popup.add_log("⚠️ Task 2 needs correction", "warning")
    
    popup.show_detail_mode_for_task(1, "The task is missing the field location for the username. Please specify where to type the username.", "Type username as admin")
    
    sys.exit(app.exec_())