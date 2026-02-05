import os
import tempfile
import time
import speech_recognition as sr
from PyQt5.QtCore import QObject, pyqtSignal, QMutex, QWaitCondition
import google.generativeai as genai
import config

# --- API Configuration ---
try:
    genai.configure(api_key=config.API_KEY)
except Exception as e:
    print(f"FATAL ERROR: Failed to configure Google Gemini API Key. Error: {e}")

class VoiceWorker(QObject):
    """
    Handles continuous, pausable live voice-to-text transcription using the Gemini API.
    """
    partial_transcript = pyqtSignal(str) # Emits text as it's recognized
    finished_transcript = pyqtSignal(str) # Emits the final full transcript
    error = pyqtSignal(str)
    listening_status_changed = pyqtSignal(str) # States: "listening", "paused", "stopped"

    def __init__(self):
        super().__init__()
        
        self.is_running = True
        self.is_paused = False
        self._pause_mutex = QMutex()
        self._pause_condition = QWaitCondition()
        
        self.mic_available = False
        self.gemini_model = None
        self.full_transcript = ""

        try:
            self.gemini_model = genai.GenerativeModel('gemini-2.5-flash-lite')
        except Exception as e:
            print(f"Error loading Gemini model: {e}")

        try:
            self.recognizer = sr.Recognizer()
            self.microphone = sr.Microphone()
            with self.microphone as source:
                self.recognizer.adjust_for_ambient_noise(source, duration=1)
            self.mic_available = True
        except OSError as e:
            print(f"MICROPHONE ERROR: {e}")

    def stop(self):
        """Signals the worker to stop the continuous listening loop."""
        print("VoiceWorker: Stop requested.")
        self.is_running = False
        self.resume() # Wake the thread if it's paused so it can exit

    def pause(self):
        """Signals the worker to pause listening."""
        print("VoiceWorker: Pause requested.")
        self.is_paused = True

    def resume(self):
        """Signals the worker to resume listening."""
        print("VoiceWorker: Resume requested.")
        self.is_paused = False
        self._pause_condition.wakeAll()

    def run(self):
        if not self.mic_available or not self.gemini_model:
            self.error.emit("Microphone or Gemini Model not available.")
            self.listening_status_changed.emit("stopped")
            return

        temp_audio_filepath = None
        
        while self.is_running:
            # --- Pause Logic ---
            self._pause_mutex.lock()
            if self.is_paused:
                self.listening_status_changed.emit("paused")
                self._pause_condition.wait(self._pause_mutex) # Wait here until resumed
            self._pause_mutex.unlock()

            if not self.is_running:
                break # Exit loop if stopped while paused

            try:
                with self.microphone as source:
                    self.listening_status_changed.emit("listening")
                    print("Listening for a new phrase...")
                    # Use a shorter listen timeout to make it feel more responsive
                    audio_data = self.recognizer.listen(source, phrase_time_limit=10)

                with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as temp_audio_file:
                    temp_audio_filepath = temp_audio_file.name
                    temp_audio_file.write(audio_data.get_wav_data())

                audio_file = genai.upload_file(path=temp_audio_filepath)
                # (You might add the wait-for-processing loop here if needed)

                response = self.gemini_model.generate_content(["Transcript this audio.", audio_file])
                genai.delete_file(audio_file.name)

                if response.text:
                    new_text = response.text.strip()
                    print(f"Recognized chunk: {new_text}")
                    # Append new text with a space
                    self.full_transcript += f" {new_text}"
                    # Emit the updated full transcript
                    self.partial_transcript.emit(self.full_transcript.strip())

            except sr.WaitTimeoutError:
                print("No speech detected in the last interval, listening again.")
                continue # Just loop again without error
            except Exception as e:
                print(f"An error occurred during continuous listening: {e}")
                self.error.emit(str(e))
            finally:
                if temp_audio_filepath and os.path.exists(temp_audio_filepath):
                    os.remove(temp_audio_filepath)

        # Loop has ended, emit the final transcript
        print("VoiceWorker: Loop finished.")
        self.finished_transcript.emit(self.full_transcript.strip())
        self.listening_status_changed.emit("stopped")