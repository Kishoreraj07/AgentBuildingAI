import pyaudio
import wave
import threading
import queue
import time
import tempfile
import os
import pyttsx3
from PyQt5.QtCore import QThread, pyqtSignal, QObject, QTimer
from PyQt5.QtWidgets import QPushButton, QHBoxLayout, QLabel
from PyQt5.QtGui import QIcon
from PyQt5.QtCore import QSize, Qt
import numpy as np
from google import genai  # Updated Gemini import
from typing import Optional, Dict, Any
import threading as th_lock

class VoiceIntegrationThread(QObject):
    """Self-contained voice integration thread with built-in Gemini service."""
    
    # Signals
    transcription_ready = pyqtSignal(str)
    recording_started = pyqtSignal()
    recording_stopped = pyqtSignal()
    speaking_started = pyqtSignal()
    speaking_finished = pyqtSignal()
    error_occurred = pyqtSignal(str)
    processing_started = pyqtSignal()
    processing_finished = pyqtSignal()
    
    def __init__(self, api_key=None, parent=None):
        super().__init__(parent)
        
        # Initialize Gemini
        self.api_key = api_key
        self.gemini_client = None
        self.gemini_model_name = None
        self._init_gemini()
        
        # Audio components
        self.is_recording = False
        self.is_speaking = False
        self.audio_thread = None
        self.p = None
        self.stream = None
        self.frames = []
        self.recording_lock = th_lock.Lock()  # FIX: Add lock for thread safety
        self.recording_started_flag = False  # FIX: Track if recording actually started
        
        # Audio settings
        self.CHUNK = 1024
        self.FORMAT = pyaudio.paInt16
        self.CHANNELS = 1
        self.RATE = 16000
        
        # Initialize TTS
        self.tts_engine = None
        self._init_tts()
        
        # Context for conversation
        self.context = {}
    
    def _init_gemini(self):
        """Initialize Gemini AI service."""
        try:
            if self.api_key:
                self.gemini_client = genai.Client(api_key=self.api_key)
                self.gemini_model_name = "gemini-2.0-flash-exp"  # Updated model
            else:
                self.error_occurred.emit("Gemini API key not provided")
        except Exception as e:
            self.error_occurred.emit(f"Failed to initialize Gemini: {str(e)}")
    
    def _init_tts(self):
        """Initialize Text-to-Speech engine."""
        try:
            self.tts_engine = pyttsx3.init()
            voices = self.tts_engine.getProperty('voices')
            if voices:
                for voice in voices:
                    if 'female' in voice.name.lower() or 'zira' in voice.name.lower():
                        self.tts_engine.setProperty('voice', voice.id)
                        break
            
            self.tts_engine.setProperty('rate', 180)
            self.tts_engine.setProperty('volume', 0.9)
            
        except Exception as e:
            self.error_occurred.emit(f"TTS initialization failed: {str(e)}")
    
    def set_context(self, context):
        """Set conversation context."""
        self.context = context or {}
    
    def start_recording(self):
        """Start audio recording."""
        with self.recording_lock:  # FIX: Lock to prevent concurrent calls
            if self.is_recording or self.is_speaking:
                return
            
            self.is_recording = True
            self.recording_started_flag = False
            self.frames = []
        
        try:
            self.p = pyaudio.PyAudio()
            self.stream = self.p.open(
                format=self.FORMAT,
                channels=self.CHANNELS,
                rate=self.RATE,
                input=True,
                frames_per_buffer=self.CHUNK
            )
            
            with self.recording_lock:  # FIX: Set flag only after stream is ready
                self.recording_started_flag = True
            
            self.recording_started.emit()  # FIX: Emit signal AFTER stream is ready
            
            self.audio_thread = threading.Thread(target=self._record_audio)
            self.audio_thread.daemon = True
            self.audio_thread.start()
            
        except Exception as e:
            with self.recording_lock:
                self.is_recording = False
                self.recording_started_flag = False
            self.error_occurred.emit(f"Failed to start recording: {str(e)}")
    
    def stop_recording(self):
        """Stop recording and process audio."""
        with self.recording_lock:  # FIX: Lock to prevent concurrent calls
            if not self.is_recording:
                return
            
            self.is_recording = False
        
        try:
            if self.audio_thread and self.audio_thread.is_alive():
                self.audio_thread.join(timeout=2.0)
            
            if self.stream:
                self.stream.stop_stream()
                self.stream.close()
                self.stream = None
            if self.p:
                self.p.terminate()
                self.p = None
            
            self.recording_stopped.emit()
            
            if self.frames:
                self._process_audio()
            else:
                self.error_occurred.emit("No audio recorded")
                
        except Exception as e:
            self.error_occurred.emit(f"Failed to stop recording: {str(e)}")
    
    def _record_audio(self):
        """Record audio in background thread."""
        try:
            while self.is_recording and self.stream:
                try:
                    data = self.stream.read(self.CHUNK, exception_on_overflow=False)
                    self.frames.append(data)
                except Exception:
                    break
        except Exception as e:
            self.error_occurred.emit(f"Recording error: {str(e)}")
    
    def _process_audio(self):
        """Process recorded audio with Gemini."""
        if not self.frames:
            return
        
        self.processing_started.emit()
        
        def process_worker():
            try:
                wav_path = self._create_wav_file()
                if not wav_path:
                    self.error_occurred.emit("Failed to create audio file")
                    return
                
                if self.gemini_client:
                    transcription = self._transcribe_with_gemini(wav_path)
                    if transcription and not transcription.startswith("Error"):
                        self.transcription_ready.emit(transcription)
                        
                        if self.context.get('generate_response', True):
                            response = self._generate_response(transcription)
                            if response:
                                self.speak_text(response)
                    else:
                        self.error_occurred.emit(transcription or "Transcription failed")
                else:
                    self.error_occurred.emit("Gemini not available")
                
                try:
                    if os.path.exists(wav_path):
                        os.unlink(wav_path)
                except Exception:
                    pass
                    
            except Exception as e:
                self.error_occurred.emit(f"Processing error: {str(e)}")
            finally:
                self.processing_finished.emit()
        
        thread = threading.Thread(target=process_worker)
        thread.daemon = True
        thread.start()
    
    def _create_wav_file(self):
        """Create WAV file from recorded frames."""
        try:
            temp_file = tempfile.NamedTemporaryFile(suffix='.wav', delete=False)
            temp_filename = temp_file.name
            temp_file.close()
            
            with wave.open(temp_filename, 'wb') as wf:
                wf.setnchannels(self.CHANNELS)
                wf.setsampwidth(2)
                wf.setframerate(self.RATE)
                wf.writeframes(b''.join(self.frames))
            
            return temp_filename
        except Exception:
            return None
    
    def _transcribe_with_gemini(self, wav_path):
        """Transcribe audio using Gemini with updated SDK, always translating to English."""
        try:
            audio_file = self.gemini_client.files.upload(file=wav_path)

            prompt = """Transcribe ONLY the actual spoken words from this audio with these rules:
    1. If you hear clear speech, transcribe it exactly as spoken.
    2. If the audio contains speech in any language other than English, translate it to English.
    3. If the audio contains only silence, background noise, beeps, or no intelligible speech, return exactly: "EMPTY".
    4. Ignore timestamps, time codes, or duration markers.
    5. Be concise and accurate — only transcribe what was actually said.
    6. Do NOT include any extra commentary, labels, or quotes.

    Transcription (in English):"""

            response = self.gemini_client.models.generate_content(
                model=self.gemini_model_name,
                contents=[prompt, audio_file]
            )

            result = response.text.strip() if response.text else "EMPTY"

            # Handle empty or noise responses
            if result == "EMPTY" or len(result) < 2 or result.lower() in ["no speech", "silence", "noise"]:
                return " "
            
            return result

        except Exception as e:
            return f"Error: {str(e)}"

    
    def _generate_response(self, user_input):
        """Generate AI response using Gemini."""
        try:
            context_prompt = "You are an AI assistant helping with task automation. "
            if self.context.get('chat_history'):
                context_prompt += "Previous conversation: " + str(self.context['chat_history'][-3:])
            if self.context.get('current_tasks'):
                context_prompt += f" Current tasks: {self.context['current_tasks']}"
            prompt = f"{context_prompt}\n\nUser said: {user_input}\n\nProvide a helpful, concise response:"
            response = self.gemini_client.models.generate_content(
                model=self.gemini_model_name,
                contents=[prompt]
            )
            if response.text:
                return response.text.strip()
        except Exception as e:
            return f"Sorry, I couldn't process that: {str(e)}"
        return None
    
    def speak_text(self, text):
        """Convert text to speech."""
        pass

class MicrophoneButton(QPushButton):
    """Enhanced microphone button with visual feedback."""
    
    def __init__(self, scale_factor=1.0, parent=None):
        super().__init__(parent)
        self.scale_factor = scale_factor
        self.is_recording = False
        
        # Set button size
        button_size = int(36 * scale_factor)
        self.setFixedSize(button_size, button_size)
        
        # Set icon or text
        try:
            self.setIcon(QIcon("styles/Icon/microphone.png"))
            self.setIconSize(QSize(int(20 * scale_factor), int(20 * scale_factor)))
        except:
            self.setText("🎤")
        
        self.setToolTip("Click to record voice input")
        self._update_style()
    
    def _update_style(self):
        """Update button styling."""
        self.setStyleSheet(f"""
            QPushButton {{
                background-color: #2a2a2a;
                border: {int(1 * self.scale_factor)}px solid #404040;
                border-radius: {int(18 * self.scale_factor)}px;
                padding: {int(5 * self.scale_factor)}px;
            }}
            QPushButton:hover {{
                background-color: #3a3a3a;
                border-color: #0ea5e9;
            }}
            QPushButton:pressed {{
                background-color: #4a4a4a;
            }}
            QPushButton[recording="true"] {{
                background-color: #dc2626;
                border-color: #ef4444;
            }}
            QPushButton[recording="true"]:hover {{
                background-color: #b91c1c;
            }}
        """)
    
    def set_recording_state(self, recording):
        """Update visual state for recording."""
        self.is_recording = recording
        self.setProperty("recording", recording)
        self.style().unpolish(self)
        self.style().polish(self)
        
        if recording:
            self.setToolTip("Recording... Click to stop")
        else:
            self.setToolTip("Click to record voice input")


def add_voice_to_sidebar(sidebar_instance, gemini_api_key=None):
    """
    Add voice integration to existing sidebar.
    Call this after creating your sidebar instance.
    
    Args:
        sidebar_instance: Your sidebar class instance
        gemini_api_key: Google AI API key for Gemini
    """
    
    # Create voice thread
    sidebar_instance.voice_thread = VoiceIntegrationThread(gemini_api_key)
    
    # Create microphone button
    scale_factor = getattr(sidebar_instance, 'scale_factor', 1.0)
    sidebar_instance.mic_button = MicrophoneButton(scale_factor)
    
    # Find the requirement input and modify its layout
    if hasattr(sidebar_instance, 'requirement_input'):
        input_widget = sidebar_instance.requirement_input
        input_parent = input_widget.parent()
        
        if input_parent and input_parent.layout():
            layout = input_parent.layout()
            
            # Find input widget index
            input_index = -1
            for i in range(layout.count()):
                item = layout.itemAt(i)
                if item and item.widget() == input_widget:
                    input_index = i
                    break
            
            if input_index >= 0:
                # Remove input from layout
                layout.removeWidget(input_widget)
                
                # Create new container with input + mic button
                from PyQt5.QtWidgets import QFrame, QHBoxLayout
                
                input_container = QFrame()
                input_layout = QHBoxLayout(input_container)
                input_layout.setContentsMargins(0, 0, 0, 0)
                input_layout.setSpacing(int(8 * scale_factor))
                
                # Add input and mic button
                input_layout.addWidget(input_widget)
                input_layout.addWidget(sidebar_instance.mic_button, 0, Qt.AlignTop)
                
                # Add container back to original position
                layout.insertWidget(input_index, input_container)
                
                # Update placeholder text
                current_placeholder = input_widget.placeholderText()
    
    # Create status label
    sidebar_instance.voice_status_label = QLabel("")
    sidebar_instance.voice_status_label.setStyleSheet(f"""
        QLabel {{
            color: #888888;
            font-size: {int(12 * scale_factor)}px;
            padding: {int(2 * scale_factor)}px {int(5 * scale_factor)}px;
        }}
    """)
    sidebar_instance.voice_status_label.hide()
    
    # Add status label to sidebar (find a good spot)
    if hasattr(sidebar_instance, 'requirement_input') and sidebar_instance.requirement_input.parent():
        parent_layout = sidebar_instance.requirement_input.parent().parent().layout()
        if parent_layout:
            # Add after the input container
            for i in range(parent_layout.count()):
                item = parent_layout.itemAt(i)
                if item and item.widget() and hasattr(item.widget(), 'layout'):
                    child_layout = item.widget().layout()
                    if child_layout:
                        for j in range(child_layout.count()):
                            child_item = child_layout.itemAt(j)
                            if (child_item and child_item.widget() and 
                                hasattr(child_item.widget(), 'layout')):
                                # Found input container, add status after it
                                parent_layout.insertWidget(i + 1, sidebar_instance.voice_status_label)
                                break
    
    # Connect voice thread signals
    def on_recording_started():
        sidebar_instance.mic_button.set_recording_state(True)
        sidebar_instance.voice_status_label.setText("🔴 Recording... Click mic to stop")
        sidebar_instance.voice_status_label.show()
    
    def on_recording_stopped():
        sidebar_instance.mic_button.set_recording_state(False)
        sidebar_instance.voice_status_label.setText("⏳ Processing audio...")
    
    def on_processing_finished():
        if not sidebar_instance.voice_thread.is_speaking:
            QTimer.singleShot(2000, sidebar_instance.voice_status_label.hide)
    
    def on_transcription_ready(text):
        current_text = sidebar_instance.requirement_input.toPlainText().strip()
        if current_text:
            sidebar_instance.requirement_input.setPlainText(current_text + " " + text)
        else:
            sidebar_instance.requirement_input.setPlainText(text)
        
        sidebar_instance.voice_status_label.setText("✅ Transcription complete")
    
    def on_speaking_started():
        sidebar_instance.voice_status_label.setText("🔊 Speaking response...")
        sidebar_instance.voice_status_label.show()
    
    def on_speaking_finished():
        QTimer.singleShot(1000, sidebar_instance.voice_status_label.hide)
    
    def on_error_occurred(error_msg):
        sidebar_instance.voice_status_label.setText(f"❌ {error_msg}")
        sidebar_instance.voice_status_label.show()
        QTimer.singleShot(4000, sidebar_instance.voice_status_label.hide)
    
    # Connect all signals
    sidebar_instance.voice_thread.recording_started.connect(on_recording_started)
    sidebar_instance.voice_thread.recording_stopped.connect(on_recording_stopped)
    sidebar_instance.voice_thread.processing_finished.connect(on_processing_finished)
    sidebar_instance.voice_thread.transcription_ready.connect(on_transcription_ready)
    sidebar_instance.voice_thread.speaking_started.connect(on_speaking_started)
    sidebar_instance.voice_thread.speaking_finished.connect(on_speaking_finished)
    sidebar_instance.voice_thread.error_occurred.connect(on_error_occurred)
    
    # Connect mic button click - FIX: Improved toggle logic
    def toggle_recording():
        if sidebar_instance.voice_thread.is_recording:
            sidebar_instance.voice_thread.stop_recording()
        else:
            # Set context before recording
            context = {
                'generate_response': True,  # Enable AI responses
                'chat_history': getattr(sidebar_instance, 'chat_history', []),
                'current_tasks': getattr(sidebar_instance, 'current_tasks', []),
                'selected_task': getattr(sidebar_instance, 'selected_task', None)
            }
            sidebar_instance.voice_thread.set_context(context)
            sidebar_instance.voice_thread.start_recording()
    
    sidebar_instance.mic_button.clicked.connect(toggle_recording)
    
    # Add cleanup method to sidebar
    original_cleanup = getattr(sidebar_instance, 'cleanup', lambda: None)
    def enhanced_cleanup():
        if hasattr(sidebar_instance, 'voice_thread'):
            if sidebar_instance.voice_thread.is_recording:
                sidebar_instance.voice_thread.stop_recording()
        original_cleanup()
    
    sidebar_instance.cleanup = enhanced_cleanup
    
    return sidebar_instance.voice_thread, sidebar_instance.mic_button