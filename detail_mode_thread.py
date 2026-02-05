import sys
import threading
import time
from queue import Queue, Empty
from PyQt5.QtCore import QThread, pyqtSignal, QTimer, QMutex, QWaitCondition
from PyQt5.QtWidgets import QApplication
import subprocess
import os


class DetailModeWorker(QThread):
    """Threaded worker for detail mode processing with proper termination"""
    
    # Signals for communication with main thread
    speech_started = pyqtSignal()
    speech_completed = pyqtSignal()
    speech_error = pyqtSignal(str)
    processing_completed = pyqtSignal(str)  # Emits user input result
    force_terminated = pyqtSignal()
    
    def __init__(self, response_text, dialog_id):
        super().__init__()
        self.response_text = response_text
        self.dialog_id = dialog_id
        self.should_terminate = False
        self.is_speaking = False
        self.speech_process = None
        self.speech_queue = Queue()
        
        # Thread synchronization
        self.termination_mutex = QMutex()
        self.termination_condition = QWaitCondition()
        
        print(f"🧵 DetailModeWorker {dialog_id} initialized")
    
    def run(self):
        """Main thread execution"""
        try:
            print(f"🧵 DetailModeWorker {dialog_id} starting...")
            
            # Start TTS in separate thread
            self.start_speech_processing()
            
            # Wait for termination or completion
            self.termination_mutex.lock()
            try:
                while not self.should_terminate:
                    # Wait for termination signal or timeout
                    if not self.termination_condition.wait(self.termination_mutex, 1000):  # 1 second timeout
                        # Check if we should continue processing
                        if self.should_terminate:
                            break
            finally:
                self.termination_mutex.unlock()
            
            if self.should_terminate:
                print(f"🛑 DetailModeWorker {self.dialog_id} terminated by user")
                self.cleanup_all_processes()
                self.force_terminated.emit()
            else:
                print(f"✅ DetailModeWorker {self.dialog_id} completed normally")
                
        except Exception as e:
            print(f"❌ DetailModeWorker {self.dialog_id} error: {e}")
            self.cleanup_all_processes()
    
    def start_speech_processing(self):
        """Start TTS processing in separate thread"""
        if not self.response_text or self.should_terminate:
            return
        
        print(f"🎤 Starting speech processing for dialog {self.dialog_id}")
        self.speech_started.emit()
        
        # Start speech in daemon thread
        speech_thread = threading.Thread(
            target=self._execute_speech_process,
            args=(self.response_text,),
            daemon=True
        )
        speech_thread.start()
    
    def _execute_speech_process(self, text):
        """Execute TTS in separate process for isolation"""
        try:
            if self.should_terminate:
                return
            
            self.is_speaking = True
            
            # Create isolated TTS script
            script_content = f"""
import sys
import os
import subprocess
import time

def speak_with_edge_tts(text):
    try:
        # Try Edge TTS first (best quality)
        import edge_tts
        import asyncio
        import pygame
        
        async def speak():
            communicate = edge_tts.Communicate(text, "en-US-JennyNeural")
            temp_file = f"temp_speech_{{int(time.time())}}.mp3"
            
            await communicate.save(temp_file)
            
            # Play with pygame
            pygame.mixer.init()
            pygame.mixer.music.load(temp_file)
            pygame.mixer.music.play()
            
            while pygame.mixer.music.get_busy():
                time.sleep(0.1)
            
            pygame.mixer.quit()
            os.remove(temp_file)
            return True
        
        return asyncio.run(speak())
    except Exception as e:
        print(f"Edge TTS failed: {{e}}")
        return False

def speak_with_pyttsx3(text):
    try:
        import pyttsx3
        engine = pyttsx3.init()
        engine.setProperty('rate', 180)
        engine.setProperty('volume', 1.0)
        
        voices = engine.getProperty('voices')
        if voices:
            for voice in voices:
                if 'zira' in voice.name.lower() or 'female' in voice.name.lower():
                    engine.setProperty('voice', voice.id)
                    break
        
        engine.say(text)
        engine.runAndWait()
        engine.stop()
        return True
    except Exception as e:
        print(f"pyttsx3 failed: {{e}}")
        return False

def speak_with_system(text):
    try:
        if sys.platform == "win32":
            escaped_text = text.replace('"', '`"').replace("'", "''")
            ps_command = f'''
Add-Type -AssemblyName System.Speech
$synth = New-Object System.Speech.Synthesis.SpeechSynthesizer
$synth.Rate = 2
$synth.Volume = 100
$synth.Speak("{escaped_text}")
$synth.Dispose()
'''
            result = subprocess.run(["powershell", "-Command", ps_command], 
                                  capture_output=True, timeout=15)
            return result.returncode == 0
        return False
    except Exception as e:
        print(f"System TTS failed: {{e}}")
        return False

# Main execution
text = {repr(text)}
success = False

# Try methods in order of preference
if not success:
    success = speak_with_edge_tts(text)
if not success:
    success = speak_with_pyttsx3(text)
if not success:
    success = speak_with_system(text)

if success:
    print("SPEECH_SUCCESS")
else:
    print("SPEECH_FAILED")
"""
            
            # Write and execute script
            script_path = f"temp_detail_speech_{self.dialog_id}_{int(time.time())}.py"
            
            with open(script_path, 'w', encoding='utf-8') as f:
                f.write(script_content)
            
            print(f"🎤 Executing TTS script: {script_path}")
            
            # Execute in separate process with termination capability
            self.speech_process = subprocess.Popen(
                [sys.executable, script_path],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            
            # Wait for completion or termination
            try:
                stdout, stderr = self.speech_process.communicate(timeout=30)
                
                if not self.should_terminate:
                    if "SPEECH_SUCCESS" in stdout:
                        print(f"✅ TTS completed successfully for dialog {self.dialog_id}")
                        self.speech_completed.emit()
                    else:
                        print(f"❌ TTS failed for dialog {self.dialog_id}: {stderr}")
                        self.speech_error.emit(f"TTS failed: {stderr}")
                
            except subprocess.TimeoutExpired:
                if not self.should_terminate:
                    print(f"⏰ TTS timeout for dialog {self.dialog_id}")
                    self.speech_error.emit("TTS timeout")
                self.speech_process.kill()
            
            # Cleanup
            try:
                os.remove(script_path)
            except:
                pass
                
        except Exception as e:
            print(f"❌ TTS execution error for dialog {self.dialog_id}: {e}")
            self.speech_error.emit(str(e))
        finally:
            self.is_speaking = False
            self.speech_process = None
    
    def terminate_processing(self):
        """Terminate all processing immediately"""
        print(f"🛑 Terminating DetailModeWorker {self.dialog_id}")
        
        self.termination_mutex.lock()
        try:
            self.should_terminate = True
            self.termination_condition.wakeAll()
        finally:
            self.termination_mutex.unlock()
        
        # Force terminate speech process
        self.cleanup_all_processes()
        
        # Terminate thread
        self.quit()
        self.wait(2000)  # Wait up to 2 seconds for clean shutdown
        
        if self.isRunning():
            print(f"⚠️ Force terminating thread for dialog {self.dialog_id}")
            self.terminate()
    
    def cleanup_all_processes(self):
        """Clean up all running processes"""
        print(f"🔧 Cleaning up processes for dialog {self.dialog_id}")
        
        # Kill speech process
        if self.speech_process and self.speech_process.poll() is None:
            try:
                print(f"🛑 Killing TTS process for dialog {self.dialog_id}")
                self.speech_process.kill()
                self.speech_process.wait(timeout=2)
            except Exception as e:
                print(f"Error killing TTS process: {e}")
        
        # Clear speech queue
        while not self.speech_queue.empty():
            try:
                self.speech_queue.get_nowait()
            except Empty:
                break
        
        # Kill any remaining TTS processes (system-wide cleanup)
        try:
            if sys.platform == "win32":
                # Kill any remaining PowerShell TTS processes
                subprocess.run(["taskkill", "/f", "/im", "powershell.exe"], 
                             capture_output=True, timeout=5)
        except Exception as e:
            print(f"Error in system TTS cleanup: {e}")
        
        self.is_speaking = False
        print(f"🔧 Cleanup completed for dialog {self.dialog_id}")


class ThreadedDetailModeManager:
    """Manager for threaded detail mode processing"""
    
    def __init__(self):
        self.active_workers = {}  # dialog_id -> worker
        self.worker_counter = 0
    
    def start_detail_mode_processing(self, response_text):
        """Start detail mode processing in separate thread"""
        self.worker_counter += 1
        dialog_id = self.worker_counter
        
        print(f"🚀 Starting threaded detail mode processing #{dialog_id}")
        
        # Create and start worker
        worker = DetailModeWorker(response_text, dialog_id)
        self.active_workers[dialog_id] = worker
        
        # Connect cleanup signal
        worker.force_terminated.connect(lambda: self._cleanup_worker(dialog_id))
        worker.finished.connect(lambda: self._cleanup_worker(dialog_id))
        
        worker.start()
        return dialog_id, worker
    
    def terminate_detail_mode_processing(self, dialog_id):
        """Terminate specific detail mode processing"""
        if dialog_id in self.active_workers:
            worker = self.active_workers[dialog_id]
            print(f"🛑 Terminating detail mode processing #{dialog_id}")
            worker.terminate_processing()
            self._cleanup_worker(dialog_id)
    
    def terminate_all_processing(self):
        """Terminate all active detail mode processing"""
        print(f"🛑 Terminating all detail mode processing ({len(self.active_workers)} active)")
        
        for dialog_id in list(self.active_workers.keys()):
            self.terminate_detail_mode_processing(dialog_id)
    
    def _cleanup_worker(self, dialog_id):
        """Clean up worker reference"""
        if dialog_id in self.active_workers:
            print(f"🔧 Cleaning up worker #{dialog_id}")
            del self.active_workers[dialog_id]
    
    def get_active_count(self):
        """Get number of active workers"""
        return len(self.active_workers)


# Global manager instance
detail_mode_manager = ThreadedDetailModeManager()
