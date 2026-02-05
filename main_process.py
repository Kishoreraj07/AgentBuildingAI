#new
import sys
# import pdb
import subprocess
import scipy
import button_style
import code_skeleton
import style_loader
import aspose.words as aw
from styles.Icon import *
import threading
import matplotlib.pyplot as plt
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch
from json_auto_monitor import start_json_auto_monitor
from docx import Document
from skimage.metrics import structural_similarity as ssim
import time
# import psutil
from typing import List, Dict
from token_manager import TokenManager
from code_editor import CodeEditor
# from mermaid_cli import render_mermaid, render_mermaid_file
# from mermaid_cli import render_mermaid_file_sync
# FileTaskGenerationWorker.py
from PyQt5.QtCore import QThread, pyqtSignal
from Geminiworker import GeminiWorker_PDF
# import selenium.webdriver.support.ui
# import pandas,openpyxl,pyautogui,numpy,google.generativeai
# from selenium.webdriver.support import expected_conditions
# from selenium.common.exceptions import StaleElementReferenceException
import ctypes
from ctypes import wintypes
import signout
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import QTimer
import os
import region_img_table_extract
# import ast
# import re
# import win32gui
# import Desktop_Process
import json
import requests
from datetime import datetime
from Word_Pdf_Converter import main_word_pdf_converter
from PyQt5.QtWidgets import QFileDialog, QMessageBox, QProgressDialog
from PyQt5.QtCore import QThread, pyqtSignal, QUrl, Qt
from PyQt5.QtGui import QIcon
from PyQt5.QtCore import Qt, QEvent

# --- MODIFICATION: Import the new widget ---
from droid_overlay_gif import DroidAgentProcessingWidget
from interactive_response import GeminiSessionService
import debug_state,Debug_terminal,generated_tasks,button_style,flowchart_widget,app_monitor_widget,style_loader,task_creation_popup,automation_mode_dropdown
from python_syntax_highlighter import PythonSyntaxHighlighter
from notification_popups import show_task_generated_notification, show_detail_mode_started_notification, show_detail_mode_completed_notification
from detail_validation_popup import UnifiedValidationPopup
from functools import partial

from PyQt5.QtMultimedia import QMediaPlayer, QMediaContent
from PyQt5.QtCore import QUrl
from PyQt5.QtWidgets import QToolButton
from PyQt5.QtSvg import QSvgRenderer
from PyQt5.QtCore import *
from PyQt5.QtGui import QMovie
# import importlib.util
# import email
# import imaplib
from email.header import decode_header
from voice_integration_thread import VoiceIntegrationThread as voice_mics
# from voice_integration_thread import VoiceIntegrationThread
import config
import sys
import os
# from datas.source_files.verify_xpath import XPathModifyDialog
from moviepy import VideoFileClip
import requests
from pathlib import Path
from config import MAIN_URL

import sys
import json
import os
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QPushButton, QGraphicsView, 
    QGraphicsScene, QMessageBox, QLabel, QWidget, QTabWidget,
    QScrollArea, QProgressBar, QToolButton, QFrame, QSizePolicy
)
from PyQt5.QtGui import (
    QPen, QBrush, QColor, QFont, QIcon, QPainter, QPixmap
)
from PyQt5.QtCore import Qt, QSize, QTimer, pyqtSignal

from pdd_flowchart import FlowNode, Arrow, FlowView, FlowchartEditor

from PyQt5.QtCore import QThread, pyqtSignal

class FlowchartWorker(QThread):
    """Worker thread for generating flowchart"""
    finished = pyqtSignal()
    error = pyqtSignal(str)
    
    def __init__(self, parent):
        super().__init__()
        self.parent = parent
    
    def run(self):
        """Generate flowchart in background"""
        try:
            self.parent.generate_workflow_diagram()
            self.finished.emit()
        except Exception as e:
            self.error.emit(str(e))

import logging
logger = logging.getLogger(__name__)
logger.info("Something happened >>>")
driver = None
application_name = None
_current_execute_worker = None  # Global reference to current ExecuteCodeWorker

def svg_to_icon(svg_bytes: bytes, size=(24, 24)) -> QIcon:
    renderer = QSvgRenderer(QByteArray(svg_bytes))
    pixmap = QPixmap(size[0], size[1])
    pixmap.fill(Qt.transparent)
    painter = QPainter(pixmap)
    renderer.render(painter)
    painter.end()
    return QIcon(pixmap)

class VideoToPdfWorker(QThread):
    finished = pyqtSignal(str)
    error = pyqtSignal(str)
    show_review_dialog = pyqtSignal(object, list, str, str)
    
    def __init__(self, video_paths=None, transcript_paths=None, selected_project_id=None, 
                 selected_task_id=None, user_id=None, custom_prompt="", split_json_path=None,
                 additional_docs=None):  # NEW PARAMETER
        super().__init__()
        
        # Handle both single and multiple videos
        if isinstance(video_paths, list):
            self.video_paths = video_paths
        else:
            self.video_paths = [video_paths] if video_paths else []
        
        # Handle both single and multiple transcripts
        if isinstance(transcript_paths, list):
            self.transcript_paths = transcript_paths
        else:
            self.transcript_paths = [transcript_paths] if transcript_paths else []
        
        # Ensure transcript_paths matches video_paths length
        while len(self.transcript_paths) < len(self.video_paths):
            self.transcript_paths.append(None)
        
        self.selected_project_id = selected_project_id
        self.selected_task_id = selected_task_id
        self.userid = user_id
        self.custom_prompt = custom_prompt
        self.reviewed_steps = None
        self.review_completed = False
        self.split_json_path = split_json_path
        self.additional_docs = additional_docs if additional_docs else []  # NEW
    
    def wait_for_review(self):
        """Block and wait until the user completes the review dialog"""
        print("⏳ Worker thread waiting for review completion...")
        
        while not self.review_completed:
            QThread.msleep(100)
            QCoreApplication.processEvents()
        
        print(f"✅ Review completed. Steps: {len(self.reviewed_steps) if self.reviewed_steps else 0}")
        return self.reviewed_steps
    
    def run(self):
        try:
            proj_id = self.selected_project_id
            task_id = self.selected_task_id
            user_id = self.userid
            
            video_count = len(self.video_paths)
            print(f"🎬 Processing {video_count} video(s)...")
            
            # Process each video
            generated_transcript_paths = []
            for i, video_path in enumerate(self.video_paths):
                transcript_path = self.transcript_paths[i]
                
                # Generate transcript if not provided
                if not transcript_path:
                    print(f"📝 Generating transcript for video {i+1}/{video_count}...")
                    from Video_transcript_pdf import convert_video_transcript_to_pdf
                    
                    # Only clear output directory on first video
                    clear_dir = (i == 0)
                    transcript_path = convert_video_transcript_to_pdf(video_path, clear_output_dir=clear_dir)
                    print(f"✅ Transcript generated for video {i+1}")
                
                generated_transcript_paths.append(transcript_path)
            
            # Call the modified process function with multiple videos + additional docs
            from video_word_converter import convert_multiple_videos_to_pdf
            pdf_path = convert_multiple_videos_to_pdf(
                video_paths=self.video_paths,
                transcript_paths=generated_transcript_paths,
                project_id=proj_id,
                task_id=task_id,
                user_id=user_id,
                worker_thread=self,
                custom_prompt=self.custom_prompt,
                split_json_path=self.split_json_path,
                additional_docs=self.additional_docs  # NEW: Pass additional docs
            )
            
            self.finished.emit(pdf_path)
        except Exception as e:
            import traceback
            traceback.print_exc()
            self.error.emit(str(e))

class SkeletonCodeWorker(QThread):
    """Worker thread for generating skeleton code"""
    
    # Signals
    progress_update = pyqtSignal(str)  # Progress message
    code_generated = pyqtSignal(str, dict,str, str)  # Generated code, JSON data, automation mode
    error_occurred = pyqtSignal(str)  # Error message
    finished_processing = pyqtSignal()  # Processing completed
    
    def __init__(self, task_data, automation_mode='web', selected_project_id=None, selected_task_id=None, user_id=None):
        super().__init__()
        self.task_data = task_data
        self.automation_mode = automation_mode
        self.selected_project_id = selected_project_id
        self.selected_task_id = selected_task_id
        self.should_stop = False
        self.userid = user_id
    
    def run(self):
        """Run skeleton code generation in background thread"""
        try:
            self.progress_update.emit("[INFO] Starting skeleton code generation...")
            if self.should_stop:
                return
            
            self.progress_update.emit("[INFO] Calling DroidStudio for skeleton code generation...")
            
            # Import and call appropriate skeleton module based on automation mode
            # Use the automation mode passed during initialization
            
            self.progress_update.emit(f"[DEBUG] Using automation mode: {self.automation_mode}")
            
            if self.automation_mode == 'desktop':
                # Desktop mode - ensure desktop_process folder exists first
                try:
                    from create_desktop_process import ensure_desktop_process_exists
                    ensure_desktop_process_exists()
                except ImportError:
                    print("⚠️ Warning: create_desktop_process module not found")
                

                proj_id=self.selected_project_id
                task_id=self.selected_task_id
                proj_name=f"proj_{proj_id}"
                task_name=f"task_{task_id}"
                task_info={"Proj_file_name":proj_name,"Task_file_name":task_name}
                with open("json_info/task_info.json", "w", encoding="utf-8") as f:
                    json.dump(task_info, f, indent=4, ensure_ascii=False)
                proj_fol=str(proj_name)
                task_fol=f"{proj_name}/{task_name}"
                try:
                    if os.path.exists(task_fol):
                        os.remove(task_fol)
                except:
                    pass
                if not os.path.exists(proj_fol):
                    os.makedirs(proj_fol)
                if not os.path.exists(task_fol):
                    os.makedirs(task_fol)
                proj_init_path=f"{proj_fol}/__init__.py"
                task_init_path=f"{task_fol}/__init__.py"
                if not os.path.exists(proj_init_path):
                    open(proj_init_path, "w").close()
                if not os.path.exists(task_init_path):
                    open(task_init_path, "w").close()

                # Desktop mode - use Desktop_code_skeleton
                import code_skeleton
                from datas.process_flow.desktop_process import Desktop_code_skeleton
                if self.should_stop:
                    return
                # Call gemini_response with combined task data for Desktop mode
                code, json_data = Desktop_code_skeleton.gemini_response(self.task_data,proj_name,task_name,self.userid)
                requirements = code_skeleton.analyze_dependencies(code)
                self.progress_update.emit("[INFO] Desktop mode: Generated code and attributes")
            elif self.automation_mode == 'citrix':
                proj_id=self.selected_project_id
                task_id=self.selected_task_id
                proj_name=f"proj_{proj_id}"
                task_name=f"task_{task_id}"
                task_info={"Proj_file_name":proj_name,"Task_file_name":task_name}
                with open("json_info/task_info.json", "w", encoding="utf-8") as f:
                    json.dump(task_info, f, indent=4, ensure_ascii=False)
                proj_fol=str(proj_name)
                task_fol=f"{proj_name}/{task_name}"
                try:
                    if os.path.exists(task_fol):
                        os.remove(task_fol)
                except:
                    pass
                if not os.path.exists(proj_fol):
                    os.makedirs(proj_fol)
                if not os.path.exists(task_fol):
                    os.makedirs(task_fol)
                proj_init_path=f"{proj_fol}/__init__.py"
                task_init_path=f"{task_fol}/__init__.py"
                if not os.path.exists(proj_init_path):
                    open(proj_init_path, "w").close()
                if not os.path.exists(task_init_path):
                    open(task_init_path, "w").close()
                # Citrix mode - use citrix_code_skeleton
                import code_skeleton
                from datas.process_flow.Citrix_process import citrix_code_skeleton
                if self.should_stop:
                    return
                # Call gemini_response with combined task data for Citrix mode
                code, json_data = citrix_code_skeleton.gemini_response(self.task_data,proj_name,task_name,self.userid)
                requirements = code_skeleton.analyze_dependencies(code)
                self.progress_update.emit("[INFO] Citrix mode: Generated code and Citrix data")
            elif self.automation_mode == 'native':
                # Native mode - use native_code_skeleton (no JSON data)
                from datas.process_flow.native_process import native_code_skeleton
                import code_skeleton
                if self.should_stop:
                    return
                # Call gemini_response with task data for Native mode (no JSON data returned)
                code = native_code_skeleton.gemini_response(self.task_data)
                json_data = {}  # Native mode doesn't use JSON data
                requirements = code_skeleton.analyze_dependencies(code)
                self.progress_update.emit("[INFO] Native mode: Generated code (no JSON data)")
            else:
                # Web mode - use regular code_skeleton
                import code_skeleton
                if self.should_stop:
                    return

                # Call gemini_response with combined task data
                proj_id=self.selected_project_id
                task_id=self.selected_task_id
                proj_name=f"proj_{proj_id}"
                task_name=f"task_{task_id}"
                task_info={"Proj_file_name":proj_name,"Task_file_name":task_name}
                with open("json_info/task_info.json", "w", encoding="utf-8") as f:
                    json.dump(task_info, f, indent=4, ensure_ascii=False)
                proj_fol=str(proj_name)
                task_fol=f"{proj_name}/{task_name}"
                try:
                    if os.path.exists(task_fol):
                        os.remove(task_fol)
                except:
                    pass
                if not os.path.exists(proj_fol):
                    os.makedirs(proj_fol)
                if not os.path.exists(task_fol):
                    os.makedirs(task_fol)
                proj_init_path=f"{proj_fol}/__init__.py"
                task_init_path=f"{task_fol}/__init__.py"
                if not os.path.exists(proj_init_path):
                    open(proj_init_path, "w").close()
                if not os.path.exists(task_init_path):
                    open(task_init_path, "w").close()
                code, json_data = code_skeleton.gemini_response(self.task_data,proj_name,task_name,self.userid)
                requirements = code_skeleton.analyze_dependencies(code)
                self.progress_update.emit("[INFO] Web mode: Generated code and XPath data")
 
            if self.should_stop:
                return
            
            self.progress_update.emit("💾 Saving generated files...")
            
            # Emit the generated code and JSON data (XPath or Attributes based on mode)
            self.code_generated.emit(code, json_data, requirements, self.automation_mode)
            
            self.progress_update.emit("✅ Skeleton code generation completed!")
            self.finished_processing.emit()
            
        except Exception as e:
            if not self.should_stop:
                self.error_occurred.emit(str(e))
    
    def stop_processing(self):
        """Request thread to stop processing"""
        self.should_stop = True


class ManualTaskGenerationWorker(QThread):
    """Worker thread for generating tasks from manual input"""
    
    # Signals
    progress_update = pyqtSignal(str)  # Progress message
    tasks_generated = pyqtSignal(list, list, list, list, dict)  # req_class, task_events, app_info, full_task_info, conditional_info
    error_occurred = pyqtSignal(str)  # Error message
    finished_processing = pyqtSignal()  # Processing completed
    
    def __init__(self, manual_input):
        super().__init__()
        self.manual_input = manual_input
        self.should_stop = False
    
    def run(self):
        """Run manual task generation in background thread"""
        try:
            self.progress_update.emit("🔄 Processing manual requirement...")
            
            if self.should_stop:
                return
            
            self.progress_update.emit("🤖 Calling DroidStudio for task generation...")
            
            # Import and call task classifier
            from task_classifier import gemini_response
            
            if self.should_stop:
                return
            
            # Generate tasks
            req_class, task_events, app_info, full_task_info, conditional_info = gemini_response(self.manual_input)
            
            if self.should_stop:
                return
            
            self.progress_update.emit("💾 Saving conditional information...")
            
            # Save conditional info
            import json
            import os
            file_path = 'json_info/conditional_info.json'
            os.makedirs('json_info', exist_ok=True)
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(conditional_info, f, indent=4, ensure_ascii=False)
            
            self.progress_update.emit(f"✅ Generated {len(req_class)} steps successfully!")
            
            # Emit the generated tasks
            self.tasks_generated.emit(req_class, task_events, app_info, full_task_info, conditional_info)
            self.finished_processing.emit()
            
        except Exception as e:
            if not self.should_stop:
                self.error_occurred.emit(str(e))
    
    def stop_processing(self):
        """Request thread to stop processing"""
        self.should_stop = True


class SimpleFunctionWorker(QThread):
    """
    Minimal worker to run a Python callable off the UI thread and emit either
    the result (via `finished`) or the error string (via `error`). Useful for
    short blocking calls such as API hits or model calls.
    """
    finished = pyqtSignal(object)
    error = pyqtSignal(str)

    def __init__(self, fn, *args, **kwargs):
        super().__init__()
        self.fn = fn
        self.args = args
        self.kwargs = kwargs

    def run(self):
        try:
            result = self.fn(*self.args, **self.kwargs)
            self.finished.emit(result)
        except Exception as e:
            self.error.emit(str(e))

    
class ExecuteCodeWorker(QThread):
    """Worker thread for executing code in background"""
    
    # Signals
    progress_update = pyqtSignal(str)  # Progress message
    output_received = pyqtSignal(str)  # Stdout output
    error_received = pyqtSignal(str)   # Stderr output
    execution_finished = pyqtSignal(int)  # Return code
    error_occurred = pyqtSignal(str)   # Error message
    
    # New signals for popup communication
    element_confirmation_requested = pyqtSignal(str, object)  # xpath, driver
    xpath_modification_requested = pyqtSignal(object)  # driver
    
    # Response signals from main thread
    element_confirmation_response = pyqtSignal(bool)  # True/False response
    xpath_modification_response = pyqtSignal(str)  # XPath string response
    
    breakpoint_hit = pyqtSignal(int) 
    
    def __init__(self, code_content, breakpoints=None):
        super().__init__()
        import threading
        self.code_content = code_content
        self.should_stop = False
        self.process = None
        self.breakpoints = breakpoints or set()  # NEW: Store breakpoints
        self.is_monitoring_breakpoints = False
        
        # NEW: Breakpoint control
        self.is_paused = False
        self.continue_event = threading.Event()
        
        # Event objects for thread synchronization
        self.element_confirmation_event = threading.Event()
        self.xpath_modification_event = threading.Event()
        self.element_confirmation_result = False
        self.xpath_modification_result = ""
        
        # Set global reference for access from other modules
        global _current_execute_worker
        _current_execute_worker = self

    def pause_at_breakpoint(self, task_index):
        """Pause execution at breakpoint"""
        self.is_paused = True
        self.continue_event.clear()
        self.breakpoint_hit.emit(task_index)
        print(f"🔴 Breakpoint hit at task {task_index}, waiting for continue...")
    
    def resume_from_breakpoint(self):
        """Resume execution from breakpoint"""
        self.is_paused = False
        self.continue_event.set()
        print(f"▶️ Continuing execution from breakpoint...")
    
    def wait_if_paused(self):
        """Block until continue is signaled"""
        if self.is_paused:
            self.continue_event.wait()

    def _monitor_breakpoints(self):
        """Monitor for breakpoint signals from subprocess"""
        import time
        import json
        import os
        
        breakpoint_status_file = "json_info/breakpoint_status.json"
        last_processed_task = None  # Track last processed breakpoint
        
        while self.is_monitoring_breakpoints and not self.should_stop:
            try:
                if os.path.exists(breakpoint_status_file):
                    with open(breakpoint_status_file, "r") as f:
                        status = json.load(f)
                    
                    if status.get("status") == "paused":
                        task_index = status.get("task_index")
                        
                        # Only emit if this is a NEW breakpoint (not already processed)
                        if task_index != last_processed_task:
                            last_processed_task = task_index
                            
                            # Delete the status file IMMEDIATELY to prevent re-reading
                            try:
                                os.remove(breakpoint_status_file)
                            except:
                                pass
                            
                            # Now emit signal to main thread
                            self.breakpoint_hit.emit(task_index)
                            print(f"📢 Emitted breakpoint_hit signal for task {task_index}")
                    
            except Exception as e:
                print(f"⚠️ Error monitoring breakpoints: {e}")
            
            # Emit progress update to trigger event loop processing in main thread
            self.progress_update.emit("⏳ Execution in progress...")
            time.sleep(0.5)  # Check every 500ms
    
    def resume_from_breakpoint(self):
        """Signal subprocess to continue from breakpoint"""
        import os
        try:
            with open("json_info/breakpoint_continue.json", "w") as f:
                f.write("{}")
            print("▶️ Continue signal sent to subprocess")
        except Exception as e:
            print(f"❌ Error resuming: {e}")

    def _inject_breakpoint_support(self, code):
        """Inject breakpoint checking functionality into generated code"""
        import re
        breakpoint_code='''
    from datas.supporting_files.breakpoint_support import check_breakpoint
    '''
        
        lines = code.split('\n')
        result_lines = []
        breakpoint_injected = False
        
        # Pattern to match the aba_agent function definition
        aba_agent_pattern = re.compile(r'^def\s+aba_agent\s*\(', re.IGNORECASE)
        
        # Pattern to match step comments
        step_pattern = re.compile(r'^\s*#\s*Step\s+(\d+)\s*:', re.IGNORECASE)
        
        current_step = None
        breakpoint_added_for_step = None
        
        # Debug: Print breakpoints info
        # print(f"DEBUG: self.breakpoints = {self.breakpoints}, type = {type(self.breakpoints)}")
        
        for line in lines:
            # Check if this line is a step comment
            match = step_pattern.match(line)
            if match:
                current_step = int(match.group(1))
                breakpoint_added_for_step = None  # Reset for new step
                # print(f"DEBUG: Found Step {current_step}, checking if {current_step - 1} in breakpoints")
            
            # If we're in a step that matches our breakpoint and haven't added it yet
            if current_step is not None and breakpoint_added_for_step != current_step:
                # Check if current step matches ANY breakpoint
                should_add = False
                if isinstance(self.breakpoints, set):
                    should_add = (current_step - 1) in self.breakpoints
                elif isinstance(self.breakpoints, list):
                    should_add = (current_step - 1) in self.breakpoints
                else:
                    should_add = self.breakpoints == current_step - 1
                
                # print(f"DEBUG: Step {current_step}, should_add = {should_add}")
                
                if should_add and line.strip() and not line.strip().startswith('#'):
                    # Get the indentation of this line
                    indent = len(line) - len(line.lstrip())
                    indent_str = ' ' * indent
                    
                    # Add check_breakpoint call BEFORE this line
                    result_lines.append(f"{indent_str}check_breakpoint({current_step-1})  # Breakpoint check for Step {current_step}")
                    breakpoint_added_for_step = current_step
                    print(f"DEBUG: Added breakpoint for Step {current_step}")
            
            result_lines.append(line)
            
            # Inject breakpoint code right after "def aba_agent():"
            if not breakpoint_injected and aba_agent_pattern.match(line):
                result_lines.append(breakpoint_code)
                breakpoint_injected = True
        
        # Combine all lines
        final_code = '\n'.join(result_lines)
        
        return final_code
    
    
    def run(self):
        """Run code execution in background thread"""
        import subprocess
        import sys
        # import config
        import os
        import json
        
        try:
            # Auto-sync: Save current Code tab content to code_py/execute_code.py before execution
            if self.code_content.strip():
                # For .exe builds, write to current working directory instead of bundle
                execute_code_path = "code_py/execute_code.py"
                os.makedirs("code_py", exist_ok=True)
                modified_code = self._inject_breakpoint_support(self.code_content)
                self.code_content=modified_code
                with open(execute_code_path, "w", encoding="utf-8") as f:
                    f.write(self.code_content)
                self.progress_update.emit(" Auto-synced Code tab content to code_py/execute_code.py")
            
            # Check if code_py/execute_code.py exists (check both bundle and working directory)
            execute_code_path = "code_py/execute_code.py"
            if not os.path.exists(execute_code_path) and not os.path.exists(resource_path("code_py/execute_code.py")):
                self.error_occurred.emit("code_py/execute_code.py not found")
                return
            
            if self.should_stop:
                return
            
            self.progress_update.emit("🚀 Starting code execution...")
            
            # Clean up exception file before execution (use working directory for .exe compatibility)
            exception_file = "json_info/exception_info.json"
            if os.path.exists(exception_file):
                os.remove(exception_file)
                print(" Cleaned up previous exception file")

            breakpoint_file = "json_info/breakpoints.json"
            os.makedirs("json_info", exist_ok=True)
            # step_points = {x + 1 for x in self.breakpoints}
            with open(breakpoint_file, "w") as f:
                json.dump({"breakpoints": list(self.breakpoints)}, f)
            
            if self.breakpoints:
                self.progress_update.emit(f"🔴 {len(self.breakpoints)} breakpoint(s) active: {sorted(self.breakpoints)}")
            
            # NEW: Start breakpoint monitoring in separate thread
            self.is_monitoring_breakpoints = True
            import threading
            monitor_thread = threading.Thread(target=self._monitor_breakpoints, daemon=True)
            monitor_thread.start()
            
            
            # import runpy
            # base_path = getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(sys.executable)))
            # file_path = os.path.join(base_path, "code_py", "code_py/execute_code.py")
            # Use working directory version if available, otherwise use bundle version
            execute_code_path = "code_py/execute_code.py"
            if os.path.exists(execute_code_path) or os.path.exists(resource_path("code_py/execute_code.py")):
                # Run aba_agent in a separate thread to prevent blocking
                import threading
                import sys
                
                execution_completed = threading.Event()
                execution_result = {'success': False, 'output': '', 'error': ''}
                
                def run_aba_agent():
                    try:
                        # Import the subprocess runner
                        from subprocess_aba_runner import run_aba_agent_subprocess,install_requirements_subprocess
                        
                        # Execute using subprocess                       
                        success, output, error = run_aba_agent_subprocess()
                        
                        execution_result['success'] = success
                        execution_result['output'] = output
                        execution_result['error'] = error
                        
                        if not success:
                            # Emit error signal to main thread for popup display
                            error_message = f"Agent Flow Execution Error:\n\n{error}"
                            self.error_occurred.emit(error_message)
                        else:
                            print(" ABA Agent execution completed successfully via subprocess")
                            
                    except Exception as e:
                        print(f" Error in aba_agent execution: {e}")
                        import traceback
                        traceback.print_exc()
                        execution_result['success'] = False
                        execution_result['error'] = str(e)
                        # Emit error signal to main thread for popup display
                        error_message = f"Agent Flow Execution Error:\n\n{str(e)}\n\nFull traceback:\n{traceback.format_exc()}"
                        self.error_occurred.emit(error_message)
                    finally:
                        # Signal that execution is complete
                        execution_completed.set()
                        
                # Start aba_agent in separate thread
                agent_thread = threading.Thread(target=run_aba_agent, daemon=True)
                agent_thread.start()
                
                # Wait for thread completion with timeout (3600 seconds = 1 hour max)
                # This prevents the main thread from blocking indefinitely
                timeout_seconds = 3600
                thread_completed = execution_completed.wait(timeout=timeout_seconds)
                
                self.is_monitoring_breakpoints = False
                
                if not thread_completed:
                    print(f"[WARN] aba_agent execution timed out after {timeout_seconds} seconds")
                    self.error_occurred.emit(f"Agent execution timed out after {timeout_seconds} seconds. The process may still be running.")
                else:
                    print("[OK] aba_agent execution completed")
            
            # Check for exception file after execution
            if os.path.exists(exception_file):
                try:
                    with open(exception_file, "r", encoding="utf-8") as f:
                        exception_info = json.load(f)
                    
                    if exception_info.get("code_exception") is not None:
                        # Emit exception signal with the exception data
                        self.error_occurred.emit(f"EXCEPTION_OCCURRED:{exception_info['code_exception']}")
                        print(f"[ERROR] Exception detected: {exception_info['code_exception']}")
                except Exception as e:
                    print(f"[ERROR] Error reading exception file: {e}")
                if os.path.exists(exception_file):
                    os.remove(exception_file)
                self.execution_finished.emit(-1)
            else:
                self.execution_finished.emit(0)
            
        except Exception as e:
            if not self.should_stop:
                self.error_occurred.emit(str(e))
    
    def handle_element_confirmation_response(self, result):
        """Handle response from main thread for element confirmation"""
        self.element_confirmation_result = result
        self.element_confirmation_event.set()
    
    def handle_xpath_modification_response(self, xpath):
        """Handle response from main thread for xpath modification"""
        self.xpath_modification_result = xpath
        self.xpath_modification_event.set()
    
    def stop_execution(self):
        import subprocess
        self.should_stop = True
        self.is_monitoring_breakpoints = False
        if self.process and self.process.poll() is None:
            try:
                self.process.terminate()
                self.process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self.process.kill()
            except Exception as e:
                print(f"Error stopping execution: {e}")


class SyncCodeWorker(QThread):
    """Worker thread for syncing code changes in background"""
    
    # Signals
    progress_update = pyqtSignal(str)  # Progress message
    sync_completed = pyqtSignal()      # Sync completed successfully
    error_occurred = pyqtSignal(str)   # Error message
    
    def __init__(self, code_content):
        super().__init__()
        self.code_content = code_content
        self.should_stop = False
    
    def run(self):
        """Run code sync in background thread"""
        try:
            self.progress_update.emit(" Starting code sync...")
            
            if self.should_stop:
                return
            
            # Check if there's code to sync
            if not self.code_content.strip():
                self.error_occurred.emit("No code to sync")
                return
            
            self.progress_update.emit(" Syncing code changes...")
            
            # Simulate some processing time for better UX
            import time
            time.sleep(0.5)  # Small delay to show the syncing state
            
            if self.should_stop:
                return
            
            # Save current Code tab content to working directory for .exe compatibility
            os.makedirs("code_py", exist_ok=True)
            with open("code_py/execute_code.py", "w", encoding="utf-8") as f:
                f.write(self.code_content)
            
            self.progress_update.emit(" Code changes synced successfully!")
            
            # Small delay to show completion message
            time.sleep(0.3)
            
            if not self.should_stop:
                self.sync_completed.emit()
            
        except Exception as e:
            if not self.should_stop:
                self.error_occurred.emit(str(e))
    
    def stop_sync(self):
        """Stop the sync process"""
        self.should_stop = True


class TaskListPopulationWorker(QThread):
    """Worker thread for populating task list in background to prevent UI freezing"""
    
    # Signals
    progress_update = pyqtSignal(str)  # Progress message
    task_batch_ready = pyqtSignal(list)  # Batch of tasks ready for UI update
    population_completed = pyqtSignal()  # Population completed successfully
    error_occurred = pyqtSignal(str)   # Error message
    
    def __init__(self, req_class, app_info, conditional_info=None):
        super().__init__()
        self.req_class = req_class
        self.app_info = app_info
        self.conditional_info = conditional_info
        self.should_stop = False
        self.batch_size = 10  # Process tasks in batches to keep UI responsive
    
    def run(self):
        """Run task list population in background thread"""
        try:
            self.progress_update.emit(" Preparing step list...")
            
            if self.should_stop:
                return
            
            total_tasks = len(self.req_class)
            self.progress_update.emit(f" Processing {total_tasks} steps...")
            
            # Process tasks in batches to keep UI responsive
            for i in range(0, total_tasks, self.batch_size):
                if self.should_stop:
                    return
                
                # Create batch
                end_idx = min(i + self.batch_size, total_tasks)
                batch = []
                
                for j in range(i, end_idx):
                    if self.should_stop:
                        return
                    
                    task = self.req_class[j]
                    app_info_text = self.app_info[j] if self.app_info and j < len(self.app_info) else ""
                    
                    batch.append({
                        'task': task,
                        'index': j,
                        'app_info': app_info_text
                    })
                
                # Emit batch for UI processing
                self.task_batch_ready.emit(batch)
                
                # Small delay to prevent overwhelming the UI
                import time
                time.sleep(0.05)  # 50ms delay between batches
                
                # Update progress
                progress = min(100, int((end_idx / total_tasks) * 100))
                self.progress_update.emit(f" Processed {end_idx}/{total_tasks} steps ({progress}%)")
            
            if not self.should_stop:
                self.progress_update.emit("Steps list population completed!")
                self.population_completed.emit()
            
        except Exception as e:
            if not self.should_stop:
                self.error_occurred.emit(str(e))
    
    def stop_population(self):
        """Stop the population process"""
        self.should_stop = True


class PreProcessCompletionWorker(QThread):
    """Worker thread for handling pre-process completion tasks in background"""
    
    # Signals
    progress_update = pyqtSignal(str)  # Progress message
    completion_ready = pyqtSignal()    # Ready to show completion popup
    error_occurred = pyqtSignal(str)   # Error message
    
    def __init__(self, main_app_ref):
        super().__init__()
        self.main_app = main_app_ref
        self.should_stop = False
    
    def run(self):
        """Run pre-process completion tasks in background thread"""
        try:
            self.progress_update.emit(" Finalizing pre-processing...")
            
            if self.should_stop:
                return
            
            # Perform heavy operations that might cause UI freezing
            self.progress_update.emit(" Refreshing tasks from generated code...")
            
            # Small delay to simulate processing time
            import time
            time.sleep(0.1)
            
            if self.should_stop:
                return
            
            self.progress_update.emit(" Pre-processing finalization completed!")
            
            # Signal that completion popup can be shown
            if not self.should_stop:
                self.completion_ready.emit()
            
        except Exception as e:
            if not self.should_stop:
                self.error_occurred.emit(str(e))
    
    def stop_processing(self):
        """Stop the processing"""
        self.should_stop = True


def resource_path(relative_path):
    # When run from PyInstaller .exe, _MEIPASS is temp path to bundled files
    if hasattr(sys, "_MEIPASS"):
        return os.path.join(sys._MEIPASS, relative_path)
    return os.path.join(os.path.abspath("."), relative_path)

class TaskComboBox(QComboBox):
    def __init__(self, parent=None, get_project_id=None):
        super().__init__(parent)
        self.get_project_id = get_project_id  # function to check project id

    def showPopup(self):
        if not self.get_project_id():
            QMessageBox.warning(self, "Select Agent Flow", "Please select a Agent first!")
            return
        super().showPopup()


def retry_operation(self, operation_func, max_retries=3, delay=1000):

    self.retry_count = 0
    self.max_retries = max_retries
    self.retry_delay = delay
    self.operation_func = operation_func
    
    # Start the operation
    operation_func()

def handle_retry(self, error_message, progress_popup):
    """Handle retry logic when operation fails"""
    self.retry_count += 1
    
    if self.retry_count < self.max_retries:
        # Update popup to show retry attempt
        progress_popup.update_message(
            "Retrying", 
            f"Attempt {self.retry_count + 1} of {self.max_retries}..."
        )
        
        # Retry after delay with exponential backoff
        QTimer.singleShot(
            self.retry_delay * self.retry_count, 
            self.operation_func
        )
    else:
        # Max retries reached, show error
        progress_popup.close()
        self.show_custom_error(
            "Error", 
            f"Operation failed after {self.max_retries} attempts:\n{error_message}"
        )

class NewItemDialog_task(QDialog):
    def __init__(self, parent=None, projectid=None, refreshtoken=None, accesstoken=None):
        super().__init__(parent)
        self.project_id = projectid
        self.refreshtoken = refreshtoken
        self.accesstoken = accesstoken
        
        # Make frameless window
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.Dialog)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setFixedSize(500, 350)
        
        # Center the dialog on parent
        if parent:
            parent_rect = parent.geometry()
            x = parent_rect.x() + (parent_rect.width() - 500) // 2
            y = parent_rect.y() + (parent_rect.height() - 350) // 2
            self.move(x, y)
        
        # Main container with rounded corners and shadow effect
        main_widget = QWidget()
        main_widget.setObjectName("mainContainer")
        main_widget.setStyleSheet("""
            QWidget#mainContainer {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                                          stop:0 #2a2a2a, stop:1 #1a1a1a);
                border: 2px solid #4ECDC4;
                border-radius: 20px;
            }
        """)
        
        # Main layout
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.addWidget(main_widget)
        
        # Content layout inside main widget
        layout = QVBoxLayout(main_widget)
        layout.setContentsMargins(30, 30, 30, 30)
        layout.setSpacing(20)
        
        # Title bar with close button
        title_bar = QWidget()
        title_bar_layout = QHBoxLayout(title_bar)
        title_bar_layout.setContentsMargins(0, 0, 0, 0)
        
        # Title
        title_label = QLabel("Create New Task")
        title_label.setStyleSheet("""
            QLabel {
                color: #4ECDC4;
                font-family: 'Asen Pro';
                font-size: 20px;
                font-weight: bold;
                padding: 0;
            }
        """)
        
        # Close button
        close_btn = QPushButton()
        close_btn.setFixedSize(24, 24)
        close_btn.setStyleSheet("""
            QPushButton {
                background: transparent;
                border: none;
            }
            QPushButton:hover {
                background-color: rgba(255, 255, 255, 0.1);
                border-radius: 12px;
            }
        """)

        def paintEvent(event):
            painter = QPainter(close_btn)
            painter.setRenderHint(QPainter.Antialiasing)
            pen = QPen(QColor(255, 255, 255), 2)
            painter.setPen(pen)
            margin = 6
            painter.drawLine(margin, margin, 18, 18)
            painter.drawLine(18, margin, margin, 18)

        close_btn.paintEvent = paintEvent
        close_btn.clicked.connect(self.reject)
        
        title_bar_layout.addWidget(title_label)
        title_bar_layout.addStretch()
        title_bar_layout.addWidget(close_btn)
        layout.addWidget(title_bar)
        
        # Add some spacing
        layout.addSpacing(10)

        # Task name input
        task_name_label = QLabel("Task Name")
        task_name_label.setStyleSheet("""
            QLabel {
                color: #FFFFFF;
                font-family: 'Asen Pro';
                font-size: 14px;
                font-weight: 600;
                margin-bottom: 5px;
            }
        """)
        layout.addWidget(task_name_label)
        
        self.task_input = QLineEdit()
        self.task_input.setPlaceholderText("Enter task name...")
        self.task_input.setStyleSheet("""
            QLineEdit {
                background: rgba(255, 255, 255, 0.1);
                border: 2px solid rgba(78, 205, 196, 0.3);
                border-radius: 10px;
                padding: 8px 14px;
                color: #FFFFFF;
                font-family: 'Asen Pro';
                font-size: 13px;
                selection-background-color: #4ECDC4;
            }
            QLineEdit:focus {
                border: 2px solid #4ECDC4;
                background: rgba(255, 255, 255, 0.15);
            }
            QLineEdit::placeholder {
                color: #888;
            }
        """)
        layout.addWidget(self.task_input)

        # Task description input
        task_desc_label = QLabel("Description")
        task_desc_label.setStyleSheet("""
            QLabel {
                color: #FFFFFF;
                font-family: 'Asen Pro';
                font-size: 14px;
                font-weight: 600;
                margin-bottom: 5px;
            }
        """)
        layout.addWidget(task_desc_label)
        
        self.task_desc_input = QLineEdit()
        self.task_desc_input.setPlaceholderText("Enter task description...")
        self.task_desc_input.setStyleSheet("""
            QLineEdit {
                background: rgba(255, 255, 255, 0.1);
                border: 2px solid rgba(78, 205, 196, 0.3);
                border-radius: 10px;
                padding: 8px 14px;
                color: #FFFFFF;
                font-family: 'Asen Pro';
                font-size: 13px;
                selection-background-color: #4ECDC4;
            }
            QLineEdit:focus {
                border: 2px solid #4ECDC4;
                background: rgba(255, 255, 255, 0.15);
            }
            QLineEdit::placeholder {
                color: #888;
            }
        """)
        layout.addWidget(self.task_desc_input)
        
        # Add stretch to push button to bottom
        layout.addStretch()
        
        # Buttons layout
        buttons_layout = QHBoxLayout()
        
        # Cancel button
        cancel_button = QPushButton("Cancel")
        cancel_button.setFixedHeight(45)
        cancel_button.setStyleSheet("""
            QPushButton {
                background: rgba(255, 255, 255, 0.1);
                border: 2px solid rgba(255, 255, 255, 0.2);
                border-radius: 22px;
                color: #FFFFFF;
                font-family: 'Asen Pro';
                font-size: 14px;
                font-weight: 600;
                padding: 0 30px;
            }
            QPushButton:hover {
                background: rgba(255, 255, 255, 0.2);
                border: 2px solid rgba(255, 255, 255, 0.4);
            }
            QPushButton:pressed {
                background: rgba(255, 255, 255, 0.3);
            }
        """)
        cancel_button.clicked.connect(self.reject)
        
        # Create button
        self.create_button = QPushButton("Create Task")
        self.create_button.setFixedHeight(45)
        self.create_button.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                                          stop:0 #4ECDC4, stop:1 #45B7B8);
                border: none;
                border-radius: 22px;
                color: #FFFFFF;
                font-family: 'Asen Pro';
                font-size: 14px;
                font-weight: bold;
                padding: 0 30px;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                                          stop:0 #5DD5D6, stop:1 #4ECDC4);
            }
            QPushButton:pressed {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                                          stop:0 #45B7B8, stop:1 #3A9B9C);
            }
        """)
        self.create_button.clicked.connect(self.on_create)
        
        buttons_layout.addWidget(cancel_button)
        buttons_layout.addSpacing(10)
        buttons_layout.addWidget(self.create_button)
        layout.addLayout(buttons_layout)
        
        # Enable dragging
        self.dragging = False
        self.drag_position = QPoint()
        
        # Set focus to first input
        self.task_input.setFocus()
    
    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.dragging = True
            self.drag_position = event.globalPos() - self.frameGeometry().topLeft()
            event.accept()
    
    def mouseMoveEvent(self, event):
        if event.buttons() == Qt.LeftButton and self.dragging:
            self.move(event.globalPos() - self.drag_position)
            event.accept()
    
    def mouseReleaseEvent(self, event):
        self.dragging = False
    def show_custom_progress(self, title, message):
        """Create and show compact progress popup matching loading dialog style"""
        dialog = QDialog(self)
        dialog.setWindowFlags(Qt.Dialog | Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
        dialog.setAttribute(Qt.WA_TranslucentBackground)
        dialog.setFixedSize(250, 150)
        dialog.setModal(True)
        
        container = QWidget(dialog)
        container.setGeometry(0, 0, 250, 150)
        container.setObjectName("progressContainer")
        container.setStyleSheet("""
            QWidget#progressContainer {
                background-color: #414141;
                border-radius: 15px;
            }
        """)
        
        layout = QVBoxLayout(container)
        layout.setAlignment(Qt.AlignCenter)
        layout.setSpacing(15)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # Spinner/Icon
        dialog.spinner_label = QLabel("⟳")
        dialog.spinner_label.setStyleSheet("""
            QLabel {
                color: #4ECDC4;
                font-size: 48px;
                background: transparent;
            }
        """)
        dialog.spinner_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(dialog.spinner_label)
        
        # Message text
        dialog.text_label = QLabel(message)
        dialog.text_label.setStyleSheet("""
            QLabel {
                color: #FFFFFF;
                font-family: 'Asen Pro';
                font-size: 14px;
                background: transparent;
            }
        """)
        dialog.text_label.setAlignment(Qt.AlignCenter)
        dialog.text_label.setWordWrap(True)
        layout.addWidget(dialog.text_label)
        
        # Add update_message method to dialog
        def update_message(new_title, new_message):
            dialog.text_label.setText(new_message)
            # Change icon based on title
            if new_title.lower() == "created":
                dialog.spinner_label.setText("✓")
                dialog.spinner_label.setStyleSheet("""
                    QLabel {
                        color: #4ECDC4;
                        font-size: 48px;
                        background: transparent;
                    }
                """)
            elif new_title.lower() == "retrying":
                dialog.spinner_label.setText("⟳")
            QApplication.processEvents()
        
        dialog.update_message = update_message
        dialog.show()
        QApplication.processEvents()
        
        return dialog


    # def on_create(self):
    #     task = self.task_input.text().strip()
    #     description = self.task_desc_input.text().strip()
    
    #     if not task or not description:
    #         # Custom warning popup for missing input
    #         self.show_custom_warning("Input Error", "Please enter task and description")
    #         return
        
    #     # Show "creating" popup first
    #     progress_popup = self.show_custom_progress("Creating", f"Task '{task}' creating...")
        
    #     url = f"{MAIN_URL}/app/project/{self.project_id}/tasks/"
    #     headers = {
    #         'Content-Type': 'application/json',
    #         'Cookie': 'sessionid=wjhnaudx6uyfal7iqlok1cyt43glmr0e'
    #     }
    
    #     try:
    #         response = requests.get(url, headers=headers)
    #         response.raise_for_status()
    #         data = response.json()
    #         task_names = [t["task_name"].lower() for t in data["tasks"]]
    #         if task.lower() in task_names:
    #             progress_popup.close()  # Close the progress popup
    #             # Custom warning popup for duplicate task
    #             self.show_custom_warning("Input Error", "Task already exist.")
    #             return
                
    #         url = f"{MAIN_URL}/app/project/tasks/"
    #         payload = json.dumps({
    #             "task_name": task,
    #             "description": description,
    #             "project": self.project_id
    #         })
    #         headers = {
    #             'Content-Type': 'application/json',
    #             'Authorization': f'Bearer {self.accesstoken}',
    #         }
    
    #         response = requests.post(url, headers=headers, data=payload)
    #         print(response.text)
    #         self.created_task = response.json()
        
    #         # Update the same popup to show "created"
    #         progress_popup.update_message("Created", f"Task '{task}' created!")
            
    #         # Auto-close after 1.5 seconds and accept dialog
    #         QTimer.singleShot(1500, lambda: [progress_popup.close(), self.accept()])
            
    #     except Exception as e:
    #         progress_popup.close()  # Close the progress popup on error
    #         print("Error:", e)
    #         # Custom error popup
    #         self.show_custom_error("Error", str(e))

    def on_create(self):
        task = self.task_input.text().strip()
        description = self.task_desc_input.text().strip()

        if not task or not description:
            self.show_custom_warning("Input Error", "Please enter task and description")
            return
        
        # Initialize retry mechanism
        self.retry_count = 0
        self.max_retries = 3
        self.retry_delay = 1000
        
        # Store values for retry
        self.task_to_create = task
        self.description_to_create = description
        
        # Start creation with retry support
        self.attempt_create_task()

    def attempt_create_task(self):
        """Attempt to create task with retry support"""
        task = self.task_to_create
        description = self.description_to_create
        
        # Show/update progress popup
        if not hasattr(self, 'progress_popup') or not self.progress_popup.isVisible():
            self.progress_popup = self.show_custom_progress(
                "Creating", 
                f"Task '{task}' creating..."
            )
        else:
            self.progress_popup.update_message(
                "Retrying", 
                f"Attempt {self.retry_count + 1} of {self.max_retries}..."
            )
        
        url = f"{MAIN_URL}/app/project/{self.project_id}/tasks/"
        headers = {
            'Content-Type': 'application/json',
            'Cookie': 'sessionid=wjhnaudx6uyfal7iqlok1cyt43glmr0e'
        }

        try:
            # Check for duplicates
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()
            data = response.json()
            task_names = [t["task_name"].lower() for t in data["tasks"]]
            
            if task.lower() in task_names:
                self.progress_popup.close()
                self.show_custom_warning("Input Error", "Task already exists.")
                return
            
            # Create task
            url = f"{MAIN_URL}/app/project/tasks/"
            payload = json.dumps({
                "task_name": task,
                "description": description,
                "project": self.project_id
            })
            headers = {
                'Content-Type': 'application/json',
                'Authorization': f'Bearer {self.accesstoken}',
            }

            response = requests.post(url, headers=headers, data=payload, timeout=10)
            response.raise_for_status()
            print(response.text)
            self.created_task = response.json()
        
            # Success - update popup
            self.progress_popup.update_message("Created", f"Task '{task}' created!")
            QTimer.singleShot(1500, lambda: [self.progress_popup.close(), self.accept()])
            
        except requests.exceptions.Timeout:
            print(f"Timeout error (attempt {self.retry_count + 1})")
            self.handle_task_retry("Request timed out. Retrying...")
            
        except requests.exceptions.ConnectionError:
            print(f"Connection error (attempt {self.retry_count + 1})")
            self.handle_task_retry("Connection failed. Retrying...")
            
        except requests.exceptions.RequestException as e:
            print(f"Request error (attempt {self.retry_count + 1}): {e}")
            self.handle_task_retry(f"Network error: {str(e)}")
            
        except Exception as e:
            print(f"Unexpected error (attempt {self.retry_count + 1}): {e}")
            self.handle_task_retry(f"Unexpected error: {str(e)}")

    def handle_task_retry(self, error_message):
        """Handle retry logic for task creation"""
        self.retry_count += 1
        
        if self.retry_count < self.max_retries:
            # Update popup to show retry
            self.progress_popup.update_message(
                "Retrying", 
                f"Attempt {self.retry_count + 1} of {self.max_retries}..."
            )
            
            # Retry after delay with exponential backoff
            QTimer.singleShot(
                self.retry_delay * self.retry_count, 
                self.attempt_create_task
            )
        else:
            # Max retries reached
            self.progress_popup.close()
            self.show_custom_error(
                "Creation Failed", 
                f"Failed after {self.max_retries} attempts.\n{error_message}"
            )
    
    
    def show_custom_warning(self, title, message):
        """Show custom styled warning popup"""
        dialog = QDialog(self)
        dialog.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool | Qt.X11BypassWindowManagerHint)
        dialog.setAttribute(Qt.WA_TranslucentBackground)
        dialog.setFixedSize(500, 250)
        dialog.setModal(True)
        dialog.setStyleSheet("")
       
        container = QWidget(dialog)
        container.setGeometry(0, 0, 500, 250)
        container.setObjectName("warningContainer")
        container.setStyleSheet("QWidget#warningContainer { background-color: #414141 !important; border: none !important; border-radius: 15px !important; }")
       
        layout = QVBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 25)
        layout.setSpacing(0)
 
        # Title bar
        title_container = QWidget()
        title_container.setFixedHeight(60)
        title_container.setStyleSheet("QWidget { background: #333333 !important; border-radius: 20px 20px 0px 0px !important; border: none !important; }")
       
        title_layout = QHBoxLayout(title_container)
        title_layout.setContentsMargins(25, 15, 25, 15)
       
        title_label = QLabel(f"{title}")
        title_label.setStyleSheet("QLabel { color: #ffffff !important; font-family: 'Asen Pro' !important; font-weight: bold !important; font-size: 16px !important; background: transparent !important; border: none !important; }")
        title_label.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        title_layout.addWidget(title_label)
        title_layout.addStretch()
       
        close_btn = QPushButton()
        close_btn.setFixedSize(24, 24)
        close_btn.setStyleSheet("QPushButton { background: transparent !important; border: none !important; } QPushButton:hover { background-color: rgba(255, 255, 255, 0.1) !important; border-radius: 12px !important; }")
       
        def paintEvent(event):
            painter = QPainter(close_btn)
            painter.setRenderHint(QPainter.Antialiasing)
            pen = QPen(QColor(255, 255, 255), 2)
            painter.setPen(pen)
            margin = 6
            painter.drawLine(margin, margin, 18, 18)
            painter.drawLine(18, margin, margin, 18)
        close_btn.paintEvent = paintEvent
        close_btn.clicked.connect(dialog.accept)
        title_layout.addWidget(close_btn)
        layout.addWidget(title_container)
        layout.addSpacing(40)
       
        # Message
        msg_label = QLabel(message)
        msg_label.setStyleSheet("QLabel { color: #FFFFFF !important; font-family: 'Asen Pro' !important; font-weight: 400 !important; font-size: 16px !important; text-align: center !important; background: transparent !important; border: none !important; padding: 10px 40px !important; }")
        msg_label.setWordWrap(True)
        msg_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(msg_label)
        layout.addSpacing(40)
       
        # OK button
        btn_layout = QHBoxLayout()
        ok_btn = QPushButton("OK")
        ok_btn.setFixedSize(120, 40)
        ok_btn.setStyleSheet("QPushButton { background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1, stop: 0 #008AB3, stop: 1 #005B7F) !important; color: #FFFFFF !important; border: none !important; border-radius: 10px !important; font-family: 'Asen Pro' !important; font-weight: 600 !important; font-size: 16px !important; } QPushButton:hover { background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1, stop: 0 #0099CC, stop: 1 #006699) !important; }")
        ok_btn.clicked.connect(dialog.accept)
        btn_layout.addStretch()
        btn_layout.addWidget(ok_btn)
        btn_layout.addStretch()
        layout.addLayout(btn_layout)
       
        dialog.exec_()
 
    def show_custom_success(self, title, message):
        """Show custom styled success popup"""
        dialog = QDialog(self)
        dialog.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool | Qt.X11BypassWindowManagerHint)
        dialog.setAttribute(Qt.WA_TranslucentBackground)
        dialog.setFixedSize(500, 250)
        dialog.setModal(True)
        dialog.setStyleSheet("")
       
        container = QWidget(dialog)
        container.setGeometry(0, 0, 500, 250)
        container.setObjectName("successContainer")
        container.setStyleSheet("QWidget#successContainer { background-color: #414141 !important; border: none !important; border-radius: 15px !important; }")
       
        layout = QVBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 25)
        layout.setSpacing(0)
 
        # Title bar
        title_container = QWidget()
        title_container.setFixedHeight(60)
        title_container.setStyleSheet("QWidget { background: #333333 !important; border-radius: 20px 20px 0px 0px !important; border: none !important; }")
       
        title_layout = QHBoxLayout(title_container)
        title_layout.setContentsMargins(25, 15, 25, 15)
       
        title_label = QLabel(f"{title}")
        title_label.setStyleSheet("QLabel { color: #ffffff !important; font-family: 'Asen Pro' !important; font-weight: bold !important; font-size: 16px !important; background: transparent !important; border: none !important; }")
        title_label.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        title_layout.addWidget(title_label)
        title_layout.addStretch()
       
        close_btn = QPushButton()
        close_btn.setFixedSize(24, 24)
        close_btn.setStyleSheet("QPushButton { background: transparent !important; border: none !important; } QPushButton:hover { background-color: rgba(255, 255, 255, 0.1) !important; border-radius: 12px !important; }")
       
        def paintEvent(event):
            painter = QPainter(close_btn)
            painter.setRenderHint(QPainter.Antialiasing)
            pen = QPen(QColor(255, 255, 255), 2)
            painter.setPen(pen)
            margin = 6
            painter.drawLine(margin, margin, 18, 18)
            painter.drawLine(18, margin, margin, 18)
        close_btn.paintEvent = paintEvent
        close_btn.clicked.connect(dialog.accept)
        title_layout.addWidget(close_btn)
        layout.addWidget(title_container)
        layout.addSpacing(40)
       
        # Message
        msg_label = QLabel(message)
        msg_label.setStyleSheet("QLabel { color: #FFFFFF !important; font-family: 'Asen Pro' !important; font-weight: 400 !important; font-size: 16px !important; text-align: center !important; background: transparent !important; border: none !important; padding: 10px 40px !important; }")
        msg_label.setWordWrap(True)
        msg_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(msg_label)
        layout.addSpacing(40)
       
        # OK button
        btn_layout = QHBoxLayout()
        ok_btn = QPushButton("OK")
        ok_btn.setFixedSize(120, 40)
        ok_btn.setStyleSheet("QPushButton { background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1, stop: 0 #008AB3, stop: 1 #005B7F) !important; color: #FFFFFF !important; border: none !important; border-radius: 10px !important; font-family: 'Asen Pro' !important; font-weight: 600 !important; font-size: 16px !important; } QPushButton:hover { background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1, stop: 0 #0099CC, stop: 1 #006699) !important; }")
        ok_btn.clicked.connect(dialog.accept)
        btn_layout.addStretch()
        btn_layout.addWidget(ok_btn)
        btn_layout.addStretch()
        layout.addLayout(btn_layout)
       
        dialog.exec_()
 
    def show_custom_error(self, title, message):
        """Show custom styled error popup"""
        dialog = QDialog(self)
        dialog.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool | Qt.X11BypassWindowManagerHint)
        dialog.setAttribute(Qt.WA_TranslucentBackground)
        dialog.setFixedSize(500, 250)
        dialog.setModal(True)
        dialog.setStyleSheet("")
       
        container = QWidget(dialog)
        container.setGeometry(0, 0, 500, 250)
        container.setObjectName("errorContainer")
        container.setStyleSheet("QWidget#errorContainer { background-color: #414141 !important; border: none !important; border-radius: 15px !important; }")
       
        layout = QVBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 25)
        layout.setSpacing(0)
 
        # Title bar
        title_container = QWidget()
        title_container.setFixedHeight(60)
        title_container.setStyleSheet("QWidget { background: #333333 !important; border-radius: 20px 20px 0px 0px !important; border: none !important; }")
       
        title_layout = QHBoxLayout(title_container)
        title_layout.setContentsMargins(25, 15, 25, 15)
       
        title_label = QLabel(f"❌ {title}")
        title_label.setStyleSheet("QLabel { color: #ffffff !important; font-family: 'Asen Pro' !important; font-weight: bold !important; font-size: 16px !important; background: transparent !important; border: none !important; }")
        title_label.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        title_layout.addWidget(title_label)
        title_layout.addStretch()
       
        close_btn = QPushButton()
        close_btn.setFixedSize(24, 24)
        close_btn.setStyleSheet("QPushButton { background: transparent !important; border: none !important; } QPushButton:hover { background-color: rgba(255, 255, 255, 0.1) !important; border-radius: 12px !important; }")
       
        def paintEvent(event):
            painter = QPainter(close_btn)
            painter.setRenderHint(QPainter.Antialiasing)
            pen = QPen(QColor(255, 255, 255), 2)
            painter.setPen(pen)
            margin = 6
            painter.drawLine(margin, margin, 18, 18)
            painter.drawLine(18, margin, margin, 18)
        close_btn.paintEvent = paintEvent
        close_btn.clicked.connect(dialog.accept)
        title_layout.addWidget(close_btn)
        layout.addWidget(title_container)
        layout.addSpacing(40)
       
        # Message
        msg_label = QLabel(message)
        msg_label.setStyleSheet("QLabel { color: #FFFFFF !important; font-family: 'Asen Pro' !important; font-weight: 400 !important; font-size: 16px !important; text-align: center !important; background: transparent !important; border: none !important; padding: 10px 40px !important; }")
        msg_label.setWordWrap(True)
        msg_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(msg_label)
        layout.addSpacing(40)
       
        # OK button
        btn_layout = QHBoxLayout()
        ok_btn = QPushButton("OK")
        ok_btn.setFixedSize(120, 40)
        ok_btn.setStyleSheet("QPushButton { background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1, stop: 0 #008AB3, stop: 1 #005B7F) !important; color: #FFFFFF !important; border: none !important; border-radius: 10px !important; font-family: 'Asen Pro' !important; font-weight: 600 !important; font-size: 16px !important; } QPushButton:hover { background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1, stop: 0 #0099CC, stop: 1 #006699) !important; }")
        ok_btn.clicked.connect(dialog.accept)
        btn_layout.addStretch()
        btn_layout.addWidget(ok_btn)
        btn_layout.addStretch()
        layout.addLayout(btn_layout)
       
        dialog.exec_()


class NewItemDialog_project(QDialog):
    def __init__(self, parent=None, user_id=None, refreshtoken=None, accesstoken=None):
        super().__init__(parent)
        self.userid = user_id
        self.refreshtoken = refreshtoken
        self.accesstoken = accesstoken
        
        # Make frameless window
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.Dialog)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setFixedSize(500, 400)
        
        # Center the dialog on parent
        if parent:
            parent_rect = parent.geometry()
            x = parent_rect.x() + (parent_rect.width() - 500) // 2
            y = parent_rect.y() + (parent_rect.height() - 400) // 2
            self.move(x, y)
        
        # Main container with rounded corners and shadow effect
        main_widget = QWidget()
        main_widget.setObjectName("mainContainer")
        main_widget.setStyleSheet("""
            QWidget#mainContainer {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                                          stop:0 #2a2a2a, stop:1 #1a1a1a);
                border: 2px solid #4ECDC4;
                border-radius: 20px;
            }
        """)
        
        # Main layout
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.addWidget(main_widget)
        
        # Content layout inside main widget
        layout = QVBoxLayout(main_widget)
        layout.setContentsMargins(30, 30, 30, 30)
        layout.setSpacing(20)
        
        # Title bar with close button
        title_bar = QWidget()
        title_bar_layout = QHBoxLayout(title_bar)
        title_bar_layout.setContentsMargins(0, 0, 0, 0)
        
        # Title
        title_label = QLabel("Create New Agent Flow")
        title_label.setStyleSheet("""
            QLabel {
                color: #4ECDC4;
                font-family: 'Asen Pro';
                font-size: 20px;
                font-weight: bold;
                padding: 0;
            }
        """)
        
        # Close button
        close_btn = QPushButton()
        close_btn.setFixedSize(24, 24)
        close_btn.setStyleSheet("""
            QPushButton {
                background: transparent;
                border: none;
            }
            QPushButton:hover {
                background-color: rgba(255, 255, 255, 0.1);
                border-radius: 12px;
            }
        """)

        def paintEvent(event):
            painter = QPainter(close_btn)
            painter.setRenderHint(QPainter.Antialiasing)
            pen = QPen(QColor(255, 255, 255), 2)
            painter.setPen(pen)
            margin = 6
            painter.drawLine(margin, margin, 18, 18)
            painter.drawLine(18, margin, margin, 18)

        close_btn.paintEvent = paintEvent
        close_btn.clicked.connect(self.reject)
        
        title_bar_layout.addWidget(title_label)
        title_bar_layout.addStretch()
        title_bar_layout.addWidget(close_btn)
        layout.addWidget(title_bar)
        
        # Add some spacing
        layout.addSpacing(10)
        
        # Project name input
        project_name_label = QLabel("Agent Flow Name")
        project_name_label.setStyleSheet("""
            QLabel {
                color: #FFFFFF;
                font-family: 'Asen Pro';
                font-size: 14px;
                font-weight: 600;
                margin-bottom: 5px;
            }
        """)
        layout.addWidget(project_name_label)
        
        self.project_input = QLineEdit()
        self.project_input.setPlaceholderText("Enter Agent Flow Name...")
        self.project_input.setStyleSheet("""
            QLineEdit {
                background: rgba(255, 255, 255, 0.1);
                border: 2px solid rgba(78, 205, 196, 0.3);
                border-radius: 10px;
                padding: 12px 16px;
                color: #FFFFFF;
                font-family: 'Asen Pro';
                font-size: 14px;
                selection-background-color: #4ECDC4;
            }
            QLineEdit:focus {
                border: 2px solid #4ECDC4;
                background: rgba(255, 255, 255, 0.15);
            }
            QLineEdit::placeholder {
                color: #888;
            }
        """)
        layout.addWidget(self.project_input)
        
        # Project description input
        project_desc_label = QLabel("Description")
        project_desc_label.setStyleSheet("""
            QLabel {
                color: #FFFFFF;
                font-family: 'Asen Pro';
                font-size: 14px;
                font-weight: 600;
                margin-bottom: 5px;
            }
        """)
        layout.addWidget(project_desc_label)
        
        self.project_desc_input = QLineEdit()
        self.project_desc_input.setPlaceholderText("Enter Agent Flow description...")
        self.project_desc_input.setStyleSheet("""
            QLineEdit {
                background: rgba(255, 255, 255, 0.1);
                border: 2px solid rgba(78, 205, 196, 0.3);
                border-radius: 10px;
                padding: 12px 16px;
                color: #FFFFFF;
                font-family: 'Asen Pro';
                font-size: 14px;
                selection-background-color: #4ECDC4;
            }
            QLineEdit:focus {
                border: 2px solid #4ECDC4;
                background: rgba(255, 255, 255, 0.15);
            }
            QLineEdit::placeholder {
                color: #888;
            }
        """)
        layout.addWidget(self.project_desc_input)
        
        # Add stretch to push button to bottom
        layout.addStretch()
        
        # Buttons layout
        buttons_layout = QHBoxLayout()
        
        # Cancel button
        cancel_button = QPushButton("Cancel")
        cancel_button.setFixedHeight(45)
        cancel_button.setStyleSheet("""
            QPushButton {
                background: rgba(255, 255, 255, 0.1);
                border: 2px solid rgba(255, 255, 255, 0.2);
                border-radius: 22px;
                color: #FFFFFF;
                font-family: 'Asen Pro';
                font-size: 14px;
                font-weight: 600;
                padding: 0 30px;
            }
            QPushButton:hover {
                background: rgba(255, 255, 255, 0.2);
                border: 2px solid rgba(255, 255, 255, 0.4);
            }
            QPushButton:pressed {
                background: rgba(255, 255, 255, 0.3);
            }
        """)
        cancel_button.clicked.connect(self.reject)
        
        # Create button
        self.create_button = QPushButton("Create Agent Flow")
        self.create_button.setFixedHeight(45)
        self.create_button.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                                          stop:0 #4ECDC4, stop:1 #45B7B8);
                border: none;
                border-radius: 22px;
                color: #FFFFFF;
                font-family: 'Asen Pro';
                font-size: 14px;
                font-weight: bold;
                padding: 0 30px;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                                          stop:0 #5DD5D6, stop:1 #4ECDC4);
            }
            QPushButton:pressed {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                                          stop:0 #45B7B8, stop:1 #3A9B9C);
            }
        """)
        self.create_button.clicked.connect(self.on_create)
        
        buttons_layout.addWidget(cancel_button)
        buttons_layout.addSpacing(10)
        buttons_layout.addWidget(self.create_button)
        layout.addLayout(buttons_layout)
        
        # Enable dragging
        self.dragging = False
        self.drag_position = QPoint()
        
        # Set focus to first input
        self.project_input.setFocus()
    
    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.dragging = True
            self.drag_position = event.globalPos() - self.frameGeometry().topLeft()
            event.accept()
    
    def mouseMoveEvent(self, event):
        if event.buttons() == Qt.LeftButton and self.dragging:
            self.move(event.globalPos() - self.drag_position)
            event.accept()
    
    def mouseReleaseEvent(self, event):
        self.dragging = False
    # def on_create(self):
    #     project = self.project_input.text().strip()
    #     description = self.project_desc_input.text().strip()
    #     if not project or not description:
    #         QMessageBox.warning(self, "Input Error", "Please enter project and description")
    #         return
        
    #     # Show "creating" popup first
    #     progress_popup = self.show_custom_progress("Creating", f"Agent Flow '{project}' creating...")
        
    #     url = f"{MAIN_URL}/app/project/user/{self.userid}/projects/"
    #     headers = {
    #         'Content-Type': 'application/json',
    #         'Cookie': 'sessionid=wjhnaudx6uyfal7iqlok1cyt43glmr0e'
    #     }

    #     try:
    #         response = requests.get(url, headers=headers)
    #         response.raise_for_status()
    #         projects_output = response.json()
    #         project_names = [p["project_name"].lower() for p in projects_output["projects"]]
    #         if project.lower() in project_names:
    #             progress_popup.close()  # Close the progress popup
    #             QMessageBox.warning(self, "Input Error", "Project already exists.")
    #             return
            
    #         url = f"{MAIN_URL}/app/project/projects/"
    #         payload = json.dumps({
    #             "project_name": project,
    #             "description": description,
    #             "tenant": self.userid
    #         })
    #         headers = {
    #             'Content-Type': 'application/json',
    #             'Authorization': f'Bearer {self.accesstoken}',
    #         }

    #         response = requests.post(url, headers=headers, data=payload)
    #         print(response.text)
    #         self.created_project = response.json()

    #         # Update the same popup to show "created"
    #         progress_popup.update_message("Created", f"Agent Flow '{project}' created!")
            
    #         # Auto-close after 1.5 seconds and accept dialog
    #         QTimer.singleShot(1500, lambda: [progress_popup.close(), self.accept()])

    #     except Exception as e:
    #         progress_popup.close()  # Close the progress popup on error
    #         print("Error creating project:", e)
    #         QMessageBox.critical(self, "Error", str(e))

    def on_create(self):
        project = self.project_input.text().strip()
        description = self.project_desc_input.text().strip()
        
        if not project or not description:
            self.show_custom_warning("Input Error", "Please enter project and description")
            return
        
        # Initialize retry mechanism
        self.retry_count = 0
        self.max_retries = 3
        self.retry_delay = 1000
        
        # Store values for retry
        self.project_to_create = project
        self.description_to_create = description
        
        # Start creation with retry support
        self.attempt_create_project()

    def attempt_create_project(self):
        """Attempt to create project with retry support"""
        project = self.project_to_create
        description = self.description_to_create
        
        # Show/update progress popup
        if not hasattr(self, 'progress_popup') or not self.progress_popup.isVisible():
            self.progress_popup = self.show_custom_progress(
                "Creating", 
                f"Agent Flow '{project}' creating..."
            )
        else:
            self.progress_popup.update_message(
                "Retrying", 
                f"Attempt {self.retry_count + 1} of {self.max_retries}..."
            )
        
        url = f"{MAIN_URL}/app/project/user/{self.userid}/projects/"
        headers = {
            'Content-Type': 'application/json',
            'Cookie': 'sessionid=wjhnaudx6uyfal7iqlok1cyt43glmr0e'
        }

        try:
            # Check for duplicates
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()
            projects_output = response.json()
            project_names = [p["project_name"].lower() for p in projects_output["projects"]]
            
            if project.lower() in project_names:
                self.progress_popup.close()
                self.show_custom_warning("Input Error", "Project already exists.")
                return
            
            # Create project
            url = f"{MAIN_URL}/app/project/projects/"
            payload = json.dumps({
                "project_name": project,
                "description": description,
                "tenant": self.userid
            })
            headers = {
                'Content-Type': 'application/json',
                'Authorization': f'Bearer {self.accesstoken}',
            }

            response = requests.post(url, headers=headers, data=payload, timeout=10)
            response.raise_for_status()
            print(response.text)
            self.created_project = response.json()

            # Success - update popup
            self.progress_popup.update_message("Created", f"Agent Flow '{project}' created!")
            QTimer.singleShot(1500, lambda: [self.progress_popup.close(), self.accept()])
            
        except requests.exceptions.Timeout:
            print(f"Timeout error (attempt {self.retry_count + 1})")
            self.handle_project_retry("Request timed out. Retrying...")
            
        except requests.exceptions.ConnectionError:
            print(f"Connection error (attempt {self.retry_count + 1})")
            self.handle_project_retry("Connection failed. Retrying...")
            
        except requests.exceptions.RequestException as e:
            print(f"Request error (attempt {self.retry_count + 1}): {e}")
            self.handle_project_retry(f"Network error: {str(e)}")
            
        except Exception as e:
            print(f"Unexpected error (attempt {self.retry_count + 1}): {e}")
            self.handle_project_retry(f"Unexpected error: {str(e)}")


    def show_custom_error(self, title, message):
        """Show custom styled error popup"""
        dialog = QDialog(self)
        dialog.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool | Qt.X11BypassWindowManagerHint)
        dialog.setAttribute(Qt.WA_TranslucentBackground)
        dialog.setFixedSize(500, 250)
        dialog.setModal(True)
        dialog.setStyleSheet("")
        
        container = QWidget(dialog)
        container.setGeometry(0, 0, 500, 250)
        container.setObjectName("errorContainer")
        container.setStyleSheet("QWidget#errorContainer { background-color: #414141 !important; border: none !important; border-radius: 15px !important; }")
        
        layout = QVBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 25)
        layout.setSpacing(0)

        # Title bar
        title_container = QWidget()
        title_container.setFixedHeight(60)
        title_container.setStyleSheet("QWidget { background: #333333 !important; border-radius: 20px 20px 0px 0px !important; border: none !important; }")
        
        title_layout = QHBoxLayout(title_container)
        title_layout.setContentsMargins(25, 15, 25, 15)
        
        title_label = QLabel(f"{title}")
        title_label.setStyleSheet("QLabel { color: #ffffff !important; font-family: 'Asen Pro' !important; font-weight: bold !important; font-size: 16px !important; background: transparent !important; border: none !important; }")
        title_label.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        title_layout.addWidget(title_label)
        title_layout.addStretch()
        
        close_btn = QPushButton()
        close_btn.setFixedSize(24, 24)
        close_btn.setStyleSheet("QPushButton { background: transparent !important; border: none !important; } QPushButton:hover { background-color: rgba(255, 255, 255, 0.1) !important; border-radius: 12px !important; }")
        
        def paintEvent(event):
            painter = QPainter(close_btn)
            painter.setRenderHint(QPainter.Antialiasing)
            pen = QPen(QColor(255, 255, 255), 2)
            painter.setPen(pen)
            margin = 6
            painter.drawLine(margin, margin, 18, 18)
            painter.drawLine(18, margin, margin, 18)
        close_btn.paintEvent = paintEvent
        close_btn.clicked.connect(dialog.accept)
        title_layout.addWidget(close_btn)
        layout.addWidget(title_container)
        layout.addSpacing(40)
        
        # Message
        msg_label = QLabel(message)
        msg_label.setStyleSheet("QLabel { color: #FFFFFF !important; font-family: 'Asen Pro' !important; font-weight: 400 !important; font-size: 16px !important; text-align: center !important; background: transparent !important; border: none !important; padding: 10px 40px !important; }")
        msg_label.setWordWrap(True)
        msg_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(msg_label)
        layout.addSpacing(40)
        
        # OK button with gradient blue
        btn_layout = QHBoxLayout()
        ok_btn = QPushButton("OK")
        ok_btn.setFixedSize(120, 40)
        ok_btn.setStyleSheet("QPushButton { background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1, stop: 0 #008AB3, stop: 1 #005B7F) !important; color: #FFFFFF !important; border: none !important; border-radius: 10px !important; font-family: 'Asen Pro' !important; font-weight: 600 !important; font-size: 16px !important; } QPushButton:hover { background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1, stop: 0 #0099CC, stop: 1 #006699) !important; }")
        ok_btn.clicked.connect(dialog.accept)
        btn_layout.addStretch()
        btn_layout.addWidget(ok_btn)
        btn_layout.addStretch()
        layout.addLayout(btn_layout)
        
        dialog.exec_()

    def show_custom_warning(self, title, message):
        """Show custom styled warning popup"""
        dialog = QDialog(self)
        dialog.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool | Qt.X11BypassWindowManagerHint)
        dialog.setAttribute(Qt.WA_TranslucentBackground)
        dialog.setFixedSize(500, 250)
        dialog.setModal(True)
        dialog.setStyleSheet("")
        
        container = QWidget(dialog)
        container.setGeometry(0, 0, 500, 250)
        container.setObjectName("warningContainer")
        container.setStyleSheet("QWidget#warningContainer { background-color: #414141 !important; border: none !important; border-radius: 15px !important; }")
        
        layout = QVBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 25)
        layout.setSpacing(0)

        # Title bar
        title_container = QWidget()
        title_container.setFixedHeight(60)
        title_container.setStyleSheet("QWidget { background: #333333 !important; border-radius: 20px 20px 0px 0px !important; border: none !important; }")
        
        title_layout = QHBoxLayout(title_container)
        title_layout.setContentsMargins(25, 15, 25, 15)
        
        title_label = QLabel(f"{title}")
        title_label.setStyleSheet("QLabel { color: #ffffff !important; font-family: 'Asen Pro' !important; font-weight: bold !important; font-size: 16px !important; background: transparent !important; border: none !important; }")
        title_label.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        title_layout.addWidget(title_label)
        title_layout.addStretch()
        
        close_btn = QPushButton()
        close_btn.setFixedSize(24, 24)
        close_btn.setStyleSheet("QPushButton { background: transparent !important; border: none !important; } QPushButton:hover { background-color: rgba(255, 255, 255, 0.1) !important; border-radius: 12px !important; }")
        
        def paintEvent(event):
            painter = QPainter(close_btn)
            painter.setRenderHint(QPainter.Antialiasing)
            pen = QPen(QColor(255, 255, 255), 2)
            painter.setPen(pen)
            margin = 6
            painter.drawLine(margin, margin, 18, 18)
            painter.drawLine(18, margin, margin, 18)
        close_btn.paintEvent = paintEvent
        close_btn.clicked.connect(dialog.accept)
        title_layout.addWidget(close_btn)
        layout.addWidget(title_container)
        layout.addSpacing(40)
        
        # Message
        msg_label = QLabel(message)
        msg_label.setStyleSheet("QLabel { color: #FFFFFF !important; font-family: 'Asen Pro' !important; font-weight: 400 !important; font-size: 16px !important; text-align: center !important; background: transparent !important; border: none !important; padding: 10px 40px !important; }")
        msg_label.setWordWrap(True)
        msg_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(msg_label)
        layout.addSpacing(40)
        
        # OK button with gradient blue
        btn_layout = QHBoxLayout()
        ok_btn = QPushButton("OK")
        ok_btn.setFixedSize(120, 40)
        ok_btn.setStyleSheet("QPushButton { background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1, stop: 0 #008AB3, stop: 1 #005B7F) !important; color: #FFFFFF !important; border: none !important; border-radius: 10px !important; font-family: 'Asen Pro' !important; font-weight: 600 !important; font-size: 16px !important; } QPushButton:hover { background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1, stop: 0 #0099CC, stop: 1 #006699) !important; }")
        ok_btn.clicked.connect(dialog.accept)
        btn_layout.addStretch()
        btn_layout.addWidget(ok_btn)
        btn_layout.addStretch()
        layout.addLayout(btn_layout)
        
        dialog.exec_()

    def handle_project_retry(self, error_message):
        """Handle retry logic for project creation"""
        self.retry_count += 1
        
        if self.retry_count < self.max_retries:
            # Update popup to show retry
            self.progress_popup.update_message(
                "Retrying", 
                f"Attempt {self.retry_count + 1} of {self.max_retries}..."
            )
            
            # Retry after delay with exponential backoff
            QTimer.singleShot(
                self.retry_delay * self.retry_count, 
                self.attempt_create_project
            )
        else:
            # Max retries reached
            self.progress_popup.close()
            self.show_custom_error(
                "Creation Failed", 
                f"Failed after {self.max_retries} attempts.\n{error_message}"
            )
            

    def show_custom_success(self, title, message):
        """Show custom styled success popup"""
        dialog = QDialog(self)
        dialog.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool | Qt.X11BypassWindowManagerHint)
        dialog.setAttribute(Qt.WA_TranslucentBackground)
        dialog.setFixedSize(500, 250)
        dialog.setModal(True)
        dialog.setStyleSheet("")
        
        container = QWidget(dialog)
        container.setGeometry(0, 0, 500, 250)
        container.setObjectName("successContainer")
        container.setStyleSheet("QWidget#successContainer { background-color: #414141 !important; border: none !important; border-radius: 15px !important; }")
        
        layout = QVBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 25)
        layout.setSpacing(0)

        # Title bar
        title_container = QWidget()
        title_container.setFixedHeight(60)
        title_container.setStyleSheet("QWidget { background: #333333 !important; border-radius: 20px 20px 0px 0px !important; border: none !important; }")
        
        title_layout = QHBoxLayout(title_container)
        title_layout.setContentsMargins(25, 15, 25, 15)
        
        title_label = QLabel(f"{title}")
        title_label.setStyleSheet("QLabel { color: #ffffff !important; font-family: 'Asen Pro' !important; font-weight: bold !important; font-size: 16px !important; background: transparent !important; border: none !important; }")
        title_label.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        title_layout.addWidget(title_label)
        title_layout.addStretch()
        
        close_btn = QPushButton()
        close_btn.setFixedSize(24, 24)
        close_btn.setStyleSheet("QPushButton { background: transparent !important; border: none !important; } QPushButton:hover { background-color: rgba(255, 255, 255, 0.1) !important; border-radius: 12px !important; }")
        
        def paintEvent(event):
            painter = QPainter(close_btn)
            painter.setRenderHint(QPainter.Antialiasing)
            pen = QPen(QColor(255, 255, 255), 2)
            painter.setPen(pen)
            margin = 6
            painter.drawLine(margin, margin, 18, 18)
            painter.drawLine(18, margin, margin, 18)
        close_btn.paintEvent = paintEvent
        close_btn.clicked.connect(dialog.accept)
        title_layout.addWidget(close_btn)
        layout.addWidget(title_container)
        layout.addSpacing(40)
        
        # Message
        msg_label = QLabel(message)
        msg_label.setStyleSheet("QLabel { color: #FFFFFF !important; font-family: 'Asen Pro' !important; font-weight: 400 !important; font-size: 16px !important; text-align: center !important; background: transparent !important; border: none !important; padding: 10px 40px !important; }")
        msg_label.setWordWrap(True)
        msg_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(msg_label)
        layout.addSpacing(40)
        
        # OK button
        btn_layout = QHBoxLayout()
        ok_btn = QPushButton("OK")
        ok_btn.setFixedSize(120, 40)
        ok_btn.setStyleSheet("QPushButton { background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1, stop: 0 #008AB3, stop: 1 #005B7F) !important; color: #FFFFFF !important; border: none !important; border-radius: 10px !important; font-family: 'Asen Pro' !important; font-weight: 600 !important; font-size: 16px !important; } QPushButton:hover { background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1, stop: 0 #0099CC, stop: 1 #006699) !important; }")
        ok_btn.clicked.connect(dialog.accept)
        btn_layout.addStretch()
        btn_layout.addWidget(ok_btn)
        btn_layout.addStretch()
        layout.addLayout(btn_layout)
        
        dialog.exec_()
    def show_custom_progress(self, title, message):
        """Create and show compact progress popup matching loading dialog style"""
        dialog = QDialog(self)
        dialog.setWindowFlags(Qt.Dialog | Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
        dialog.setAttribute(Qt.WA_TranslucentBackground)
        dialog.setFixedSize(250, 150)
        dialog.setModal(True)
        
        container = QWidget(dialog)
        container.setGeometry(0, 0, 250, 150)
        container.setObjectName("progressContainer")
        container.setStyleSheet("""
            QWidget#progressContainer {
                background-color: #414141;
                border-radius: 15px;
            }
        """)
        
        layout = QVBoxLayout(container)
        layout.setAlignment(Qt.AlignCenter)
        layout.setSpacing(15)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # Spinner/Icon
        dialog.spinner_label = QLabel("⟳")
        dialog.spinner_label.setStyleSheet("""
            QLabel {
                color: #4ECDC4;
                font-size: 48px;
                background: transparent;
            }
        """)
        dialog.spinner_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(dialog.spinner_label)
        
        # Message text
        dialog.text_label = QLabel(message)
        dialog.text_label.setStyleSheet("""
            QLabel {
                color: #FFFFFF;
                font-family: 'Asen Pro';
                font-size: 14px;
                background: transparent;
            }
        """)
        dialog.text_label.setAlignment(Qt.AlignCenter)
        dialog.text_label.setWordWrap(True)
        layout.addWidget(dialog.text_label)
        
        # Add update_message method to dialog
        def update_message(new_title, new_message):
            dialog.text_label.setText(new_message)
            # Change icon based on title
            if new_title.lower() == "created":
                dialog.spinner_label.setText("✓")
                dialog.spinner_label.setStyleSheet("""
                    QLabel {
                        color: #4ECDC4;
                        font-size: 48px;
                        background: transparent;
                    }
                """)
            elif new_title.lower() == "retrying":
                dialog.spinner_label.setText("⟳")
            QApplication.processEvents()
        
        dialog.update_message = update_message
        dialog.show()
        QApplication.processEvents()
        
        return dialog


class CustomProgressPopup(QDialog):
    def __init__(self, title, message, parent=None):
        super().__init__(parent)
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool | Qt.X11BypassWindowManagerHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setFixedSize(520, 280)
        qr = self.frameGeometry()
        cp = QDesktopWidget().availableGeometry().center()
        qr.moveCenter(cp)
        self.move(qr.topLeft())
        self.setModal(True)
        
        container = QWidget(self)
        container.setGeometry(0, 0, 520, 280)
        container.setObjectName("successContainer")
        container.setStyleSheet("QWidget#successContainer { background-color: #414141 !important; border: none !important; border-radius: 15px !important; }")
        
        layout = QVBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 25)
        layout.setSpacing(0)

        # Title bar
        title_container = QWidget()
        title_container.setFixedHeight(60)
        title_container.setStyleSheet("QWidget { background: #333333 !important; border-radius: 20px 20px 0px 0px !important; border: none !important; }")
        
        title_layout = QHBoxLayout(title_container)
        title_layout.setContentsMargins(25, 15, 25, 15)
        
        # Store title label as instance variable to update later
        self.title_label = QLabel(f"⏳ {title}")
        self.title_label.setStyleSheet("QLabel { color: #ffffff !important; font-family: 'Asen Pro' !important; font-weight: bold !important; font-size: 16px !important; background: transparent !important; border: none !important; }")
        self.title_label.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        title_layout.addWidget(self.title_label)
        title_layout.addStretch()
        
        close_btn = QPushButton()
        close_btn.setFixedSize(24, 24)
        close_btn.setStyleSheet("QPushButton { background: transparent !important; border: none !important; } QPushButton:hover { background-color: rgba(255, 255, 255, 0.1) !important; border-radius: 12px !important; }")
        
        def paintEvent(event):
            painter = QPainter(close_btn)
            painter.setRenderHint(QPainter.Antialiasing)
            pen = QPen(QColor(255, 255, 255), 2)
            painter.setPen(pen)
            margin = 6
            painter.drawLine(margin, margin, 18, 18)
            painter.drawLine(18, margin, margin, 18)
        close_btn.paintEvent = paintEvent
        close_btn.clicked.connect(self.accept)
        
        title_layout.addWidget(close_btn)
        layout.addWidget(title_container)
        layout.addSpacing(40)
        
        # Message - store as instance variable to update later
        self.msg_label = QLabel(message)
        self.msg_label.setStyleSheet("QLabel { color: #FFFFFF !important; font-family: 'Asen Pro' !important; font-weight: 600 !important; font-size: 16px !important; text-align: center !important; background: transparent !important; border: none !important; padding: 10px 40px !important; }")
        self.msg_label.setAlignment(Qt.AlignCenter)
        self.msg_label.setWordWrap(True)
        layout.addWidget(self.msg_label)
        
        layout.addStretch()  # Add stretch to center the message vertically
    
    def update_message(self, title, message):
        """Update the popup with success message"""
        self.title_label.setText(f"✅ {title}")
        self.msg_label.setText(message)
        QApplication.processEvents()  # Force UI update




class NewItemDialog(QDialog):
    def __init__(self, parent=None, user_id=None, refreshtoken=None, accesstoken=None):
        super().__init__(parent)
        self.userid = user_id
        self.refreshtoken = refreshtoken
        self.accesstoken = accesstoken
        
        # Make frameless window
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.Dialog)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setFixedSize(550, 500)
        
        # Center the dialog on parent
        if parent:
            parent_rect = parent.geometry()
            x = parent_rect.x() + (parent_rect.width() - 550) // 2
            y = parent_rect.y() + (parent_rect.height() - 500) // 2
            self.move(x, y)
        
        # Main container with rounded corners and shadow effect
        main_widget = QWidget()
        main_widget.setObjectName("mainContainer")
        main_widget.setStyleSheet("""
            QWidget#mainContainer {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                                          stop:0 #2a2a2a, stop:1 #1a1a1a);
                border: 2px solid #4ECDC4;
                border-radius: 20px;
            }
        """)
        
        # Main layout
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.addWidget(main_widget)
        
        # Content layout inside main widget
        layout = QVBoxLayout(main_widget)
        layout.setContentsMargins(30, 30, 30, 30)
        layout.setSpacing(15)
        
        # Title bar with close button
        title_bar = QWidget()
        title_bar_layout = QHBoxLayout(title_bar)
        title_bar_layout.setContentsMargins(0, 0, 0, 0)
        
        # Title
        title_label = QLabel("Create New Project & Task")
        title_label.setStyleSheet("""
            QLabel {
                color: #4ECDC4;
                font-family: 'Asen Pro';
                font-size: 18px;
                font-weight: bold;
                padding: 0;
            }
        """)
        
        # Close button
        close_btn = QPushButton("✕")
        close_btn.setFixedSize(30, 30)
        close_btn.setStyleSheet("""
            QPushButton {
                background: transparent;
                color: #888;
                border: none;
                font-size: 18px;
                font-weight: bold;
                border-radius: 15px;
            }
            QPushButton:hover {
                background: #ff4444;
                color: white;
            }
        """)
        close_btn.clicked.connect(self.reject)
        
        title_bar_layout.addWidget(title_label)
        title_bar_layout.addStretch()
        title_bar_layout.addWidget(close_btn)
        layout.addWidget(title_bar)
        
        # Add some spacing
        layout.addSpacing(10)

        # Input field styling
        input_style = """
            QLineEdit {
                background: rgba(255, 255, 255, 0.1);
                border: 2px solid rgba(78, 205, 196, 0.3);
                border-radius: 10px;
                padding: 12px 16px;
                color: #FFFFFF;
                font-family: 'Asen Pro';
                font-size: 14px;
                selection-background-color: #4ECDC4;
            }
            QLineEdit:focus {
                border: 2px solid #4ECDC4;
                background: rgba(255, 255, 255, 0.15);
            }
            QLineEdit::placeholder {
                color: #888;
            }
        """
        
        label_style = """
            QLabel {
                color: #FFFFFF;
                font-family: 'Asen Pro';
                font-size: 14px;
                font-weight: 600;
                margin-bottom: 5px;
            }
        """

        # Project name input
        project_name_label = QLabel("Project Name")
        project_name_label.setStyleSheet(label_style)
        layout.addWidget(project_name_label)
        
        self.project_input = QLineEdit()
        self.project_input.setPlaceholderText("Enter project name...")
        self.project_input.setStyleSheet(input_style)
        layout.addWidget(self.project_input)

        # Project description input
        project_desc_label = QLabel("Project Description")
        project_desc_label.setStyleSheet(label_style)
        layout.addWidget(project_desc_label)
        
        self.project_desc_input = QLineEdit()
        self.project_desc_input.setPlaceholderText("Enter project description...")
        self.project_desc_input.setStyleSheet(input_style)
        layout.addWidget(self.project_desc_input)

        # Task name input
        task_name_label = QLabel("Task Name")
        task_name_label.setStyleSheet(label_style)
        layout.addWidget(task_name_label)
        
        self.task_input = QLineEdit()
        self.task_input.setPlaceholderText("Enter task name...")
        self.task_input.setStyleSheet(input_style)
        layout.addWidget(self.task_input)

        # Task description input
        task_desc_label = QLabel("Task Description")
        task_desc_label.setStyleSheet(label_style)
        layout.addWidget(task_desc_label)
        
        self.task_desc_input = QLineEdit()
        self.task_desc_input.setPlaceholderText("Enter task description...")
        self.task_desc_input.setStyleSheet(input_style)
        layout.addWidget(self.task_desc_input)
        
        # Add stretch to push button to bottom
        layout.addStretch()
        
        # Buttons layout
        buttons_layout = QHBoxLayout()
        
        # Cancel button
        cancel_button = QPushButton("Cancel")
        cancel_button.setFixedHeight(45)
        cancel_button.setStyleSheet("""
            QPushButton {
                background: rgba(255, 255, 255, 0.1);
                border: 2px solid rgba(255, 255, 255, 0.2);
                border-radius: 22px;
                color: #FFFFFF;
                font-family: 'Asen Pro';
                font-size: 14px;
                font-weight: 600;
                padding: 0 30px;
            }
            QPushButton:hover {
                background: rgba(255, 255, 255, 0.2);
                border: 2px solid rgba(255, 255, 255, 0.4);
            }
            QPushButton:pressed {
                background: rgba(255, 255, 255, 0.3);
            }
        """)
        cancel_button.clicked.connect(self.reject)

        # Create button
        self.create_button = QPushButton("Create Agent Flow & Task")
        self.create_button.setFixedHeight(45)
        self.create_button.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                                          stop:0 #4ECDC4, stop:1 #45B7B8);
                border: none;
                border-radius: 22px;
                color: #FFFFFF;
                font-family: 'Asen Pro';
                font-size: 14px;
                font-weight: bold;
                padding: 0 30px;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                                          stop:0 #5DD5D6, stop:1 #4ECDC4);
            }
            QPushButton:pressed {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                                          stop:0 #45B7B8, stop:1 #3A9B9C);
            }
        """)
        self.create_button.clicked.connect(self.on_create)
        
        buttons_layout.addWidget(cancel_button)
        buttons_layout.addSpacing(10)
        buttons_layout.addWidget(self.create_button)
        layout.addLayout(buttons_layout)
        
        # Enable dragging
        self.dragging = False
        self.drag_position = QPoint()
        
        # Set focus to first input
        self.project_input.setFocus()
    
    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.dragging = True
            self.drag_position = event.globalPos() - self.frameGeometry().topLeft()
            event.accept()
    
    def mouseMoveEvent(self, event):
        if event.buttons() == Qt.LeftButton and self.dragging:
            self.move(event.globalPos() - self.drag_position)
            event.accept()
    
    def mouseReleaseEvent(self, event):
        self.dragging = False

    def on_create(self):
        project = self.project_input.text().strip()
        project_desc = self.project_desc_input.text().strip()
        task = self.task_input.text().strip()
        task_desc = self.task_desc_input.text().strip()
        if not project or not task or not project_desc or not task_desc:
            QMessageBox.warning(self, "Input Error", "Please enter project, task, and descriptions.")
            return
        url = f"{MAIN_URL}/app/project/user/{self.userid}/projects/"
        headers = {
            'Content-Type': 'application/json',
            'Cookie': 'sessionid=wjhnaudx6uyfal7iqlok1cyt43glmr0e'
        }

        try:
            response = requests.get(url, headers=headers)
            response.raise_for_status()
            projects_output = response.json()
            project_names = [p["project_name"].lower() for p in projects_output["projects"]]
            if project.lower() in project_names:
                QMessageBox.warning(self, "Input Error", "Project already exist.")
                return

            # Create project
            url_project = f"{MAIN_URL}/app/project/projects/"
            payload_project = json.dumps({
                "project_name": project,
                "description": project_desc,
                "tenant": self.userid
            })
            headers = {
                'Content-Type': 'application/json',
                'Authorization': f'Bearer {self.accesstoken}',
            }

            response = requests.post(url_project, headers=headers, data=payload_project)
            print(response.text)
            projectdata = response.json()
            url = f"{MAIN_URL}/app/project/{projectdata['id']}/tasks/"
            headers = {
                'Content-Type': 'application/json',
                'Cookie': 'sessionid=wjhnaudx6uyfal7iqlok1cyt43glmr0e'
            }

            try:
                response = requests.get(url, headers=headers)
                response.raise_for_status()
                data = response.json()
                task_names = [t["task_name"].lower() for t in data["tasks"]]
                if task.lower() in task_names:
                    QMessageBox.warning(self, "Input Error", "Task already exist.")
                    return
                # for task_id, task_name in tasks:
                # Create task under that project
                url_task = f"{MAIN_URL}/app/project/tasks/"
                payload_task = json.dumps({
                    "task_name": task,
                    "description": task_desc,
                    "project": projectdata['id']
                })
                response = requests.post(url_task, headers=headers, data=payload_task)
                print(response.text)

                QMessageBox.information(self, "Created", f"Agent Flow '{project}' and Task '{task}' created!")
                self.accept()
            except Exception as e:
                print("Error:", e)
                QMessageBox.critical(self, "Error", str(e))
        except Exception as e:
            print("Error creating project/task:", e)
            QMessageBox.critical(self, "Error", str(e))
        


def code_convert(code_str, parent_widget=None):
    """Convert and save code with PyQt5 file dialog"""
    # First clean the code
    clean_code = code_str.strip("`").replace("python", "", 1).strip()
    
    # Return early if no parent widget
    if not parent_widget:
        return clean_code

    try:
        # Set initial directory to user's home folder
        initial_dir = os.path.expanduser("~")
        
        # Create non-modal file dialog
        dialog = QFileDialog(
            parent_widget,
            "Save Python Code",
            os.path.join(initial_dir, "automation_code.py"),
            "Python Files (*.py);;All Files (*)"
        )
        dialog.setDefaultSuffix(".py")
        dialog.setAcceptMode(QFileDialog.AcceptSave)
        dialog.setOption(QFileDialog.DontUseNativeDialog, True)
        dialog.setOption(QFileDialog.DontUseCustomDirectoryIcons, True)
        
        # Show dialog non-modally
        if dialog.exec() != QFileDialog.Accepted:
            return clean_code
            
        # Get selected file path
        file_path = dialog.selectedFiles()[0]
        
        # Add .py extension if missing
        if not file_path.lower().endswith('.py'):
            file_path += '.py'
        
        # Save the file in a try block to handle permissions/IO errors
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(clean_code)
                
            print(f"✅ Code saved successfully to: {file_path}")
            
            # Show success message
            QMessageBox.information(
                parent_widget,
                "Success", 
                f"Code saved successfully!\nLocation: {file_path}"
            )
                
        except IOError as e:
            error_msg = f"Error saving file: {str(e)}"
            print(f"❌ {error_msg}")
            QMessageBox.critical(
                parent_widget,
                "Error",
                error_msg
            )
            
    except Exception as e:
        error_msg = f"Error in file dialog: {str(e)}"
        print(f"❌ {error_msg}")
        QMessageBox.critical(
            parent_widget,
            "Error",
            error_msg
        )
        
    # Always return the cleaned code
    return clean_code

def get_windows_display_complete():
    
    user32 = ctypes.windll.user32
    shcore = ctypes.windll.shcore
    
    # Set DPI awareness
    shcore.SetProcessDpiAwareness(2)  # Per-monitor DPI aware v2
    
    # Primary monitor info
    hmonitor = user32.MonitorFromPoint(wintypes.POINT(0, 0), 1)
    
    # Get physical dimensions
    physical_width = user32.GetSystemMetrics(0)
    physical_height = user32.GetSystemMetrics(1)
    
    # Get DPI for primary monitor
    dpi_x = wintypes.UINT()
    dpi_y = wintypes.UINT()
    shcore.GetDpiForMonitor(hmonitor, 0, ctypes.byref(dpi_x), ctypes.byref(dpi_y))
    
    # Calculate scaling
    scaling = dpi_x.value / 96.0
    formatted_scaling = f"{scaling*100:.0f}%"
    
    print(f"Physical Resolution: {physical_width} x {physical_height}")
    print(f"Scaling: {formatted_scaling}")
    
    return {
        'physical': (physical_width, physical_height),
        'scaling': formatted_scaling,
    }



class PDFProcessingThread(QThread):
    """Thread for processing PDF files without blocking the main UI"""
    
    # Signals to communicate with main thread
    processing_started = pyqtSignal()
    processing_finished = pyqtSignal(list)  # Emits the processed tasks
    processing_error = pyqtSignal(str)  # Emits error message
    processing_progress = pyqtSignal(str)  # Emits progress messages
    
    def __init__(self, file_path, parent=None):
        super().__init__(parent)
        self.file_path = file_path
        self.should_stop = False
    
    def run(self):
        """Run the PDF processing in background thread"""
        try:
            self.processing_started.emit()
            self.processing_progress.emit("🔄 Loading PDF processing module...")
            
            # Import here to avoid blocking main thread during app startup
            import gemini_pdf
            
            self.processing_progress.emit("📄 Analyzing PDF content...")
            
            # Check if thread should stop
            if self.should_stop:
                return
            
            self.processing_progress.emit("🤖 Generating tasks with Gemini AI...")
            
            # Process the PDF file
            req_class = gemini_pdf.gemini_pdf_response(self.file_path)
            
            # Check if thread should stop before emitting result
            if self.should_stop:
                return
            
            self.processing_progress.emit("✅ PDF processing completed!")
            
            # Emit the result
            self.processing_finished.emit(req_class)
            
        except Exception as e:
            if not self.should_stop:
                error_msg = f"Failed to process PDF file: {str(e)}"
                self.processing_error.emit(error_msg)
    
    def stop_processing(self):
        """Request thread to stop processing"""
        self.should_stop = True
        self.quit()
        self.wait()  # Wait for thread to finish

class CustomTitleBar(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent = parent
        self.setFixedHeight(35)
        self.setProperty('class', 'CustomTitleBar')
        
        # Create layout
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # # Title label
        # self.title_label = QLabel("Agent Building Agent")
        # self.title_label.setProperty('class', 'TitleBarLabel')
        # layout.addWidget(self.title_label)
        # self.version = self.get_version_from_file()
        # self.version_label = QLabel(f"V-{self.version}")
        # self.version_label.setProperty('class', 'TitleBarVersion')
        # self.version_label.setAlignment(Qt.AlignCenter)
        # layout.addWidget(self.version_label, stretch=1)  # stretch=1 centers it
        # # Spacer
        # layout.addStretch()
        # Title label with version
        self.version = self.get_version_from_file()
        self.title_label = QLabel(f"Agent Flow (V-{self.version})")
        self.title_label.setProperty('class', 'TitleBarLabel')
        layout.addWidget(self.title_label)

        # Spacer
        layout.addStretch()
        # Window control buttons with PNG icons
        self.minimize_btn = QPushButton()
        self.minimize_btn.setIcon(QIcon(resource_path("styles/Icon/minimize.png")))
        self.minimize_btn.setIconSize(QSize(16, 16))
        self.minimize_btn.setFixedSize(30, 30)
        self.minimize_btn.setProperty('class', 'WindowControlButton')
        self.minimize_btn.setToolTip("Minimize")
        self.minimize_btn.clicked.connect(self.minimize_window)
        
        self.maximize_btn = QPushButton()
        self.maximize_btn.setIcon(QIcon(resource_path("styles/Icon/maximize.png")))
        self.maximize_btn.setIconSize(QSize(16, 16))
        self.maximize_btn.setFixedSize(30, 30)
        self.maximize_btn.setProperty('class', 'WindowControlButton')
        self.maximize_btn.setToolTip("Maximize/Restore")
        self.maximize_btn.clicked.connect(self.maximize_window)
        
        self.close_btn = QPushButton()
        self.close_btn.setIcon(QIcon(resource_path("styles/Icon/close.png")))
        self.close_btn.setIconSize(QSize(16, 16))
        self.close_btn.setFixedSize(30, 30)
        self.close_btn.setProperty('class', 'CloseWindowButton')
        self.close_btn.setToolTip("Close")
        self.close_btn.clicked.connect(self.close_window)
        
        layout.addWidget(self.minimize_btn)
        layout.addWidget(self.maximize_btn)
        layout.addWidget(self.close_btn)
        
        # Variables for window dragging
        self.drag_position = QPoint()
    def minimize_window(self):
        if self.parent:
            self.parent.showMinimized()
    
    def maximize_window(self):
        if self.parent:
            if self.parent.isMaximized():
                self.parent.showNormal()
            else:
                self.parent.showMaximized()
    def get_version_from_file(self):
        version_path = os.path.join(os.path.dirname(sys.executable), "version.txt")
        try:
            with open(version_path) as f:
                return f.read().strip()
        except FileNotFoundError:
            return "2.0.33"
        
    def close_window(self):
        if self.parent:
            # --- NEW: Stop agent via API ---
            try:
                import requests

                print("🛑 Sending stop request to agent server...")

                response = requests.post("http://127.0.0.1:5050/stop_agent", timeout=150)

                if response.status_code == 200:
                    data = response.json()
                    if data.get("success"):
                        print("✅ Agent process terminated")
                    else:
                        print(f"⚠️ Stop failed: {data.get('message')}")
                else:
                    print(f"❌ Stop API error: {response.text}")

            except Exception as e:
                print(f"❌ Error calling stop API: {e}")

            # --- EXISTING CODE (unchanged) ---
            print("Stopping Flask server...")
            subprocess.Popen(
                'cmd /c "for /f \"tokens=5\" %a in (\'netstat -ano ^| findstr :5050\') do taskkill /PID %a /F"',
                shell=True,
                creationflags=subprocess.CREATE_NEW_CONSOLE
            )

            self.parent.close()

        
    # def close_window(self):
    #     if self.parent:
    #         print("Stopping Flask server...")
    #         subprocess.Popen(
    #             'cmd /c "for /f \"tokens=5\" %a in (\'netstat -ano ^| findstr :5050\') do taskkill /PID %a /F"',
    #             shell=True,
    #             creationflags=subprocess.CREATE_NEW_CONSOLE
    #         )
    #         self.parent.close()

            
    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.drag_position = event.globalPos() - self.parent.frameGeometry().topLeft()
            event.accept()
            
    def mouseMoveEvent(self, event):
        if event.buttons() == Qt.LeftButton and self.parent:
            self.parent.move(event.globalPos() - self.drag_position)
            event.accept()

class ExceptionPopup(QDialog):
    """Frameless, draggable exception popup"""
    
    def __init__(self, display_msg, exception_text, parent=None):
        super().__init__(parent)
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.Dialog | Qt.WindowStaysOnTopHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setModal(True)
        self.setFixedSize(500, 250)
        
        # Store exception data
        self.display_msg = display_msg
        self.exception_text = exception_text
        self.result = None
        
        # For dragging
        self.drag_position = QPoint()
        
        self.setup_ui()
        self.center_on_parent()
        
    def setup_ui(self):
        """Setup the UI for the exception popup"""
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        
        # Main container with rounded corners
        container = QFrame()
        container.setStyleSheet("""
            QFrame {
                background-color: #000000;
                border: 2px solid #ff4444;
                border-radius: 12px;
            }
        """)
        container_layout = QVBoxLayout(container)
        container_layout.setContentsMargins(15, 10, 15, 15)
        container_layout.setSpacing(15)
        
        # Title bar with close and minimize buttons
        title_bar = QHBoxLayout()
        title_bar.setContentsMargins(0, 0, 0, 0)
        
        # Title label
        title_label = QLabel("⚠️ Exception Occurred")
        title_label.setStyleSheet("""
            QLabel {
                color: #ff4444;
                font-size: 14px;
                font-weight: bold;
                padding: 5px 0;
            }
        """)
        
        # Minimize button
        minimize_btn = QPushButton("−")
        minimize_btn.setFixedSize(25, 25)
        minimize_btn.setStyleSheet("""
            QPushButton {
                background-color: #FFC107;
                border: none;
                border-radius: 12px;
                color: white;
                font-size: 16px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #FFB300;
            }
        """)
        minimize_btn.clicked.connect(self.showMinimized)
        
        # Close button
        close_btn = QPushButton("✕")
        close_btn.setFixedSize(25, 25)
        close_btn.setStyleSheet("""
            QPushButton {
                background-color: #f44336;
                border: none;
                border-radius: 12px;
                color: white;
                font-size: 12px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #d32f2f;
            }
        """)
        close_btn.clicked.connect(self.reject)
        
        title_bar.addWidget(title_label)
        title_bar.addStretch()
        # title_bar.addWidget(minimize_btn)
        title_bar.addWidget(close_btn)
        container_layout.addLayout(title_bar)
        
        # Exception message
        message_label = QLabel(f"This exception occurred:\n\n{self.display_msg}")
        message_label.setAlignment(Qt.AlignCenter)
        message_label.setWordWrap(True)
        message_label.setStyleSheet("""
            QLabel {
                color: white;
                font-size: 13px;
                padding: 10px;
                background-color: transparent;
                border: none;
            }
        """)
        container_layout.addWidget(message_label)
        
        # Buttons
        button_layout = QHBoxLayout()
        button_layout.setSpacing(15)
        
        # No button
        no_btn = QPushButton("Close")
        no_btn.setFixedSize(120, 35)
        no_btn.setStyleSheet("""
            QPushButton {
                background-color: #f44336;
                border: none;
                border-radius: 8px;
                color: white;
                font-size: 12px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #d32f2f;
            }
            QPushButton:pressed {
                background-color: #b71c1c;
            }
        """)
        no_btn.clicked.connect(self.on_no_clicked)
        
        # Yes button
        yes_btn = QPushButton("✨Fix it")
        yes_btn.setFixedSize(140, 35)
        yes_btn.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                border: none;
                border-radius: 8px;
                color: white;
                font-size: 12px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
            QPushButton:pressed {
                background-color: #3d8b40;
            }
        """)
        yes_btn.clicked.connect(self.on_yes_clicked)
        yes_btn.setDefault(True)
        
        button_layout.addStretch()
        button_layout.addWidget(no_btn)
        button_layout.addStretch()
        
        container_layout.addLayout(button_layout)
        main_layout.addWidget(container)
    
    def on_yes_clicked(self):
        """Handle Yes button click"""
        self.result = "yes"
        self.accept()
    
    def on_no_clicked(self):
        """Handle No button click"""
        self.result = "no"
        self.reject()
        
    def center_on_parent(self):
        """Center the popup on parent window"""
        if self.parent():
            parent_rect = self.parent().geometry()
            popup_rect = self.geometry()
            x = parent_rect.x() + (parent_rect.width() - popup_rect.width()) // 2
            y = parent_rect.y() + (parent_rect.height() - popup_rect.height()) // 2
            self.move(x, y)
        else:
            # Center on screen if no parent
            screen = QApplication.desktop().screenGeometry()
            popup_rect = self.geometry()
            x = (screen.width() - popup_rect.width()) // 2
            y = (screen.height() - popup_rect.height()) // 2
            self.move(x, y)
    
    def mousePressEvent(self, event):
        """Handle mouse press for dragging"""
        if event.button() == Qt.LeftButton:
            self.drag_position = event.globalPos() - self.frameGeometry().topLeft()
            event.accept()
    
    def mouseMoveEvent(self, event):
        """Handle mouse move for dragging"""
        if event.buttons() == Qt.LeftButton and self.drag_position:
            self.move(event.globalPos() - self.drag_position)
            event.accept()
    
    def keyPressEvent(self, event):
        """Handle key press events"""
        if event.key() == Qt.Key_Escape:
            self.reject()
        elif event.key() == Qt.Key_Return or event.key() == Qt.Key_Enter:
            self.accept()
        else:
            super().keyPressEvent(event)

class CodeExecutionConfirmationPopup(QDialog):
    """Frameless, draggable confirmation popup for code execution"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.Dialog | Qt.WindowStaysOnTopHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setModal(True)
        self.setFixedSize(400, 200)
        
        # For dragging
        self.drag_position = QPoint()
        
        self.setup_ui()
        self.center_on_parent()
        
    def setup_ui(self):
        """Setup the UI for the confirmation popup"""
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        
        # Main container with rounded corners and shadow effect
        container = QFrame()
        container.setStyleSheet("""
            QFrame {
                background-color: #000000;
                border: 2px solid #4CAF50;
                border-radius: 12px;
            }
        """)
        container_layout = QVBoxLayout(container)
        container_layout.setContentsMargins(15, 10, 15, 15)
        container_layout.setSpacing(15)
        
        # Title bar with close and minimize buttons
        title_bar = QHBoxLayout()
        title_bar.setContentsMargins(0, 0, 0, 0)
        
        # Title label
        title_label = QLabel("Code Execution Confirmation")
        title_label.setStyleSheet("""
            QLabel {
                color: #4CAF50;
                font-size: 14px;
                font-weight: bold;
                padding: 5px 0;
            }
        """)
        
        # Minimize button
        minimize_btn = QPushButton("−")
        minimize_btn.setFixedSize(25, 25)
        minimize_btn.setStyleSheet("""
            QPushButton {
                background-color: #FFC107;
                border: none;
                border-radius: 12px;
                color: white;
                font-size: 16px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #FFB300;
            }
        """)
        minimize_btn.clicked.connect(self.showMinimized)
        
        # Close button
        close_btn = QPushButton("✕")
        close_btn.setFixedSize(25, 25)
        close_btn.setStyleSheet("""
            QPushButton {
                background-color: #f44336;
                border: none;
                border-radius: 12px;
                color: white;
                font-size: 12px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #d32f2f;
            }
        """)
        close_btn.clicked.connect(self.reject)
        
        title_bar.addWidget(title_label)
        title_bar.addStretch()
        title_bar.addWidget(minimize_btn)
        title_bar.addWidget(close_btn)
        container_layout.addLayout(title_bar)
        
        # Main message
        message_label = QLabel("Code modification completed successfully!\n\nCan I execute the code?")
        message_label.setAlignment(Qt.AlignCenter)
        message_label.setStyleSheet("""
            QLabel {
                color: white;
                font-size: 13px;
                padding: 10px;
                background-color: transparent;
                border: none;
            }
        """)
        container_layout.addWidget(message_label)
        
        # Buttons
        button_layout = QHBoxLayout()
        button_layout.setSpacing(15)
        
        # No button
        no_btn = QPushButton("No")
        no_btn.setFixedSize(80, 35)
        no_btn.setStyleSheet("""
            QPushButton {
                background-color: #757575;
                border: none;
                border-radius: 8px;
                color: white;
                font-size: 12px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #616161;
            }
            QPushButton:pressed {
                background-color: #424242;
            }
        """)
        no_btn.clicked.connect(self.reject)
        
        # Yes button
        yes_btn = QPushButton("Yes")
        yes_btn.setFixedSize(80, 35)
        yes_btn.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                border: none;
                border-radius: 8px;
                color: white;
                font-size: 12px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
            QPushButton:pressed {
                background-color: #3d8b40;
            }
        """)
        yes_btn.clicked.connect(self.accept)
        yes_btn.setDefault(True)  # Make it the default button
        
        button_layout.addStretch()
        button_layout.addWidget(no_btn)
        button_layout.addWidget(yes_btn)
        button_layout.addStretch()
        
        container_layout.addLayout(button_layout)
        main_layout.addWidget(container)
        
    def center_on_parent(self):
        """Center the popup on parent window"""
        if self.parent():
            parent_rect = self.parent().geometry()
            popup_rect = self.geometry()
            x = parent_rect.x() + (parent_rect.width() - popup_rect.width()) // 2
            y = parent_rect.y() + (parent_rect.height() - popup_rect.height()) // 2
            self.move(x, y)
        else:
            # Center on screen if no parent
            screen = QApplication.desktop().screenGeometry()
            popup_rect = self.geometry()
            x = (screen.width() - popup_rect.width()) // 2
            y = (screen.height() - popup_rect.height()) // 2
            self.move(x, y)
    
    def mousePressEvent(self, event):
        """Handle mouse press for dragging"""
        if event.button() == Qt.LeftButton:
            self.drag_position = event.globalPos() - self.frameGeometry().topLeft()
            event.accept()
    
    def mouseMoveEvent(self, event):
        """Handle mouse move for dragging"""
        if event.buttons() == Qt.LeftButton and self.drag_position:
            self.move(event.globalPos() - self.drag_position)
            event.accept()
    
    def keyPressEvent(self, event):
        """Handle key press events"""
        if event.key() == Qt.Key_Escape:
            self.reject()

# Worker classes for task generation
class ManualTaskGenerationWorker(QThread):
    """Worker thread for manual task generation"""
    
    # Signals
    progress_update = pyqtSignal(str)
    tasks_generated = pyqtSignal(list, list, dict, list, dict)  # req_class, task_events, app_info, full_task_info, conditional_info
    error_occurred = pyqtSignal(str)
    finished_processing = pyqtSignal()
    
    def __init__(self, manual_input):
        super().__init__()
        self.manual_input = manual_input
    
    def run(self):
        """Run manual task generation in background thread"""
        try:
            self.progress_update.emit("🔄 Processing manual input...")
            
            # Import and call the manual task generation function
            import task_classifier
            
            self.progress_update.emit("🤖 Generating tasks from manual input...")
            req_class= task_classifier.gemini_response(self.manual_input)
            
            # Create empty conditional_info for compatibility
            conditional_info = {}
            
            self.progress_update.emit("✅ Manual task generation completed")
            self.progress_update.emit("🤖 Generating steps from manual input...")
            # req_class= task_classifier.gemini_response(self.manual_input)
            
            # Create empty conditional_info for compatibility
            task_events = []
            app_info = {}
            full_task_info = []
            conditional_info = {}
            
            self.progress_update.emit("✅ Manual step generation completed")
            self.tasks_generated.emit(req_class, task_events, app_info, full_task_info, conditional_info)
            
        except Exception as e:
            import traceback
            error_msg = f"Manual task generation failed: {str(e)}\n\nTraceback:\n{traceback.format_exc()}"
            print(f"❌ ManualTaskGenerationWorker error: {error_msg}")
            self.error_occurred.emit(error_msg)
        finally:
            self.finished_processing.emit()


class FileTaskGenerationWorker(QThread):
    """Worker thread for file-based task generation"""
    
    progress_update = pyqtSignal(str)
    tasks_generated = pyqtSignal(list, list, dict, list, dict)  # req_class, task_events, app_info, full_task_info, conditional_info
    error_occurred = pyqtSignal(str)
    finished_processing = pyqtSignal()

    def __init__(self, file_path):
        super().__init__()
        self.file_path = file_path
        self.should_stop = False

    def run(self):
        req_class = []
        try:
            self.progress_update.emit(f"🔄 Processing file: {self.file_path}")
            if self.should_stop:
                return

            self.progress_update.emit("🤖 Generating tasks from file...")

            # --- Run GeminiWorker_PDF in its own thread ---
            self.worker = GeminiWorker_PDF(self.file_path)

            # Connect signals
            self.worker.error.connect(self.error_occurred.emit)
            
            # Start worker and wait for completion
            self.worker.start()
            self.worker.wait()

            # Check for exceptions
            if self.worker.exception:
                raise Exception(self.worker.exception)

            req_class = self.worker.result or []

        except Exception as e:
            self.error_occurred.emit(str(e))

        finally:
            # Always emit results to prevent GUI freeze
            task_events = []
            app_info = {}
            full_task_info = []
            conditional_info = {}

            self.tasks_generated.emit(req_class, task_events, app_info, full_task_info, conditional_info)
            self.finished_processing.emit()


class ProjectTaskSelectionDialog(QDialog):
    """Dialog for selecting project and task in two steps"""
    
    def __init__(self, parent=None, userid=None, refreshtoken=None, accesstoken=None):
        super().__init__(parent)
        self.userid = userid
        self.refreshtoken = refreshtoken
        self.accesstoken = accesstoken
        self.selected_project = None
        self.selected_task = None
        
        # Store loaded task data to pass back to main app
        self.loaded_req_class = []
        self.loaded_task_events = []
        self.loaded_full_task_info = []
        self.loaded_xpath_data = {}
        self.loaded_code_content = ""
        self.projects_data = []
        self.showing_projects = True  # Track which view we're showing
        
        self.setModal(True)
        self.setup_ui()
        self.load_projects()
        
    def setup_ui(self):
        """Setup the dialog UI"""
        # Make dialog frameless and always on top
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool | Qt.X11BypassWindowManagerHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setFixedSize(700, 600)
        self.move(600, 250)
        
        # Add dragging support
        self._mouse_pressed = False
        self._mouse_pos = None
        self.installEventFilter(self)
        # Create main container
        container = QWidget(self)
        container.setGeometry(0, 0, 700, 600)
        container.setObjectName("projectTaskContainer")
        container.setStyleSheet("""
            QWidget#projectTaskContainer {
                background-color: #414141 !important;
                border: none !important;
                border-radius: 15px !important;
            }
        """)
        
        layout = QVBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 25)
        layout.setSpacing(0)

        # Title bar
        title_container = QWidget()
        title_container.setFixedHeight(60)
        title_container.setStyleSheet("""
            QWidget {
                background: #333333 !important;
                border-radius: 20px 20px 0px 0px !important;
                border: none !important;
            }
        """)

        title_layout = QHBoxLayout(title_container)
        title_layout.setContentsMargins(25, 15, 25, 15)

        # Back button (initially hidden)
        self.back_btn = QPushButton("← Back")
        self.back_btn.setFixedSize(80, 30)
        self.back_btn.setVisible(False)
        self.back_btn.setStyleSheet("""
            QPushButton {
                background: transparent !important;
                color: #ffffff !important;
                border: 1px solid #555555 !important;
                border-radius: 6px !important;
                font-family: 'Asen Pro' !important;
                font-size: 13px !important;
                padding: 5px !important;
            }
            QPushButton:hover {
                background-color: rgba(255, 255, 255, 0.1) !important;
                border: 1px solid #777777 !important;
            }
        """)
        self.back_btn.clicked.connect(self.go_back_to_projects)
        title_layout.addWidget(self.back_btn)

        self.title_label = QLabel("Select Agent Flow")
        self.title_label.setStyleSheet("""
            QLabel {
                color: #ffffff !important;
                font-family: 'Asen Pro' !important;
                font-weight: bold !important;
                font-size: 16px !important;
                background: transparent !important;
                border: none !important;
            }
        """)
        self.title_label.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        title_layout.addWidget(self.title_label)
        title_layout.addStretch()
        
        # Close button
        close_btn = QPushButton()
        close_btn.setFixedSize(24, 24)
        close_btn.setStyleSheet("""
            QPushButton {
                background: transparent !important;
                border: none !important;
            }
            QPushButton:hover {
                background-color: rgba(255, 255, 255, 0.1) !important;
                border-radius: 12px !important;
            }
        """)
        
        def paintEvent(event):
            painter = QPainter(close_btn)
            painter.setRenderHint(QPainter.Antialiasing)
            pen = QPen(QColor(255, 255, 255), 2)
            painter.setPen(pen)
            margin = 6
            painter.drawLine(margin, margin, 18, 18)
            painter.drawLine(18, margin, margin, 18)
        close_btn.paintEvent = paintEvent
        close_btn.clicked.connect(self.reject)
        title_layout.addWidget(close_btn)

        layout.addWidget(title_container)
        layout.addSpacing(10)
        
        # Content area - Stacked widget to switch between projects and tasks
        self.stacked_widget = QStackedWidget()
        self.stacked_widget.setStyleSheet("background: transparent; border: none;")
        
        # Projects page
        projects_page = self.create_projects_page()
        self.stacked_widget.addWidget(projects_page)
        
        # Tasks page
        tasks_page = self.create_tasks_page()
        self.stacked_widget.addWidget(tasks_page)
        
        layout.addWidget(self.stacked_widget)
        layout.addSpacing(15)
        
        # Buttons
        button_layout = QHBoxLayout()
        button_layout.setContentsMargins(25, 0, 25, 0)
        button_layout.setSpacing(15)
        
        cancel_button = QPushButton("❌ Cancel")
        cancel_button.setFixedSize(140, 40)
        cancel_button.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1, stop: 0 #008AB3, stop: 1 #005B7F) !important;
                color: #FFFFFF !important;
                border: none !important;
                border-radius: 10px !important;
                font-family: 'Asen Pro' !important;
                font-weight: 600 !important;
                font-size: 16px !important;
            }
            QPushButton:hover {
                background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1, stop: 0 #0099CC, stop: 1 #006699) !important;
            }
        """)
        cancel_button.clicked.connect(self.reject)
        
        self.select_button = QPushButton("✅ Select")
        self.select_button.setFixedSize(120, 40)
        self.select_button.setEnabled(True)
        self.select_button.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1, stop: 0 #008AB3, stop: 1 #005B7F) !important;
                color: #FFFFFF !important;
                border: none !important;
                border-radius: 10px !important;
                font-family: 'Asen Pro' !important;
                font-weight: 600 !important;
                font-size: 16px !important;
            }
            QPushButton:hover {
                background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1, stop: 0 #0099CC, stop: 1 #006699) !important;
            }
            QPushButton:disabled {
                background-color: #555555 !important;
                color: #888888 !important;
            }
        """)
        self.select_button.clicked.connect(self.on_select_clicked)
        
        button_layout.addStretch()
        button_layout.addWidget(cancel_button)
        button_layout.addWidget(self.select_button)
        button_layout.addStretch()
        
        layout.addLayout(button_layout)

    def create_list_item_with_menu(self, name, data, item_type="project"):
        """Create a list item with three-dot menu for edit/delete"""
        # Create container widget
        item_widget = QWidget()
        item_widget.setStyleSheet("background: transparent;")
        
        item_layout = QHBoxLayout(item_widget)
        item_layout.setContentsMargins(10, 0, 10, 0)
        item_layout.setSpacing(10)
        
        # Name label - takes most space
        name_label = QLabel(name)
        name_label.setStyleSheet("""
            QLabel {
                color: #ffffff;
                font-family: 'Asen Pro';
                font-size: 15px;
                background: transparent;
            }
        """)
        item_layout.addWidget(name_label, 1)  # Stretch factor 1
        
        # Three-dot menu button
        menu_btn = QPushButton("⋮")
        menu_btn.setFixedSize(18, 18)   # fits inside the row
        menu_btn.setCursor(Qt.PointingHandCursor)
        menu_btn.setStyleSheet("""
            QPushButton {
                background: transparent;
                color: #ffffff;
                border: none;
                font-size: 18px;         /* visually big */
                font-weight: 900;
                padding: 0px;
                line-height: 18px;
            }
            QPushButton:hover {
                background-color: rgba(255, 255, 255, 0.18);
                border-radius: 4px;
                color: #ffffff;
            }
        """)

        
        # Create menu
        menu = QMenu(self)
        menu.setStyleSheet("""
            QMenu {
                background-color: #2b2b2b;
                color: #ffffff;
                border: 1px solid #555555;
                border-radius: 4px;
                padding: 5px;
            }
            QMenu::item {
                padding: 8px 25px;
                border-radius: 3px;
            }
            QMenu::item:selected {
                background-color: #008AB3;
            }
        """)
        
        # Edit action
        edit_action = menu.addAction("✏️ Edit")
        if item_type == "project":
            edit_action.triggered.connect(lambda: self.edit_project(data))
        else:
            edit_action.triggered.connect(lambda: self.edit_task(data))
        
        # Delete action
        delete_action = menu.addAction("🗑️ Delete")
        if item_type == "project":
            delete_action.triggered.connect(lambda: self.delete_project(data))
        else:
            delete_action.triggered.connect(lambda: self.delete_task(data))
        
        # Show menu on button click
        def show_menu():
            menu.exec_(menu_btn.mapToGlobal(menu_btn.rect().bottomRight()))
        
        menu_btn.clicked.connect(show_menu)
        
        item_layout.addWidget(menu_btn, 0)  # No stretch
        
        return item_widget
    
    def on_select_clicked(self):
        """Handle Select button click - navigate to tasks or accept"""
        if self.showing_projects:
            # If on projects page, navigate to tasks
            if self.selected_project:
                self.show_tasks_view()
        else:
            # If on tasks page, accept the selection
            self.accept()
    def accept(self):
        if not self.selected_task:
            QMessageBox.warning(self, "No Task Selected", "Please select a task before accepting.")
            return

        task_id = self.selected_task["id"]
        task_name = self.selected_task["task_name"]

        # Call your main task handler
        self.handle_task_selection(task_id, task_name)

        # Then close the dialog
        super().accept()

    def extract_task_zip(self, zip_file_path, project_id, task_id):
        """
        Extract zip file containing task .py files to the proper folder structure.
        If folders already exist, overwrites all .py files with new ones.
        
        Args:
            zip_file_path: Path to the downloaded zip file
            project_id: The project ID
            task_id: The task ID
            
        Returns:
            bool: True if extraction successful, False otherwise
        """
        import zipfile
        
        try:
            proj_folder_name = f"proj_{project_id}"
            task_folder_name = f"task_{task_id}"
            task_folder_path = os.path.join(proj_folder_name, task_folder_name)
            
            # Create folders if they don't exist
            os.makedirs(proj_folder_name, exist_ok=True)
            os.makedirs(task_folder_path, exist_ok=True)
            
            # Extract zip file
            with zipfile.ZipFile(zip_file_path, 'r') as zipf:
                # List all files in zip
                zip_contents = zipf.namelist()
                print(f"📦 Extracting zip file: {os.path.basename(zip_file_path)}")
                print(f"📦 Zip contains {len(zip_contents)} files")
                
                # Extract all files
                for file_name in zip_contents:
                    # Extract to current directory (zip already has proper structure)
                    zipf.extract(file_name, ".")
                    print(f"✅ Extracted: {file_name}")
                
                # Count extracted .py files (excluding __init__.py)
                py_files_count = sum(1 for f in zip_contents 
                                    if f.endswith('.py') and '__init__.py' not in f)
                
                print(f"📦 Successfully extracted {py_files_count} .py files to {task_folder_path}")
                return True
                
        except zipfile.BadZipFile:
            print(f"❌ Invalid zip file: {zip_file_path}")
            return False
        except Exception as e:
            print(f"❌ Error extracting zip file: {e}")
            import traceback
            traceback.print_exc()
            return False
        
    def handle_task_selection(self, task_id, task_name):
        """Handle task selection from menu system"""
        if not task_id:
            print("No valid task selected.")
            if hasattr(self, 'process_btn'):
                self.process_btn.setEnabled(False)
            return
        # ------------------by anu ------------------
        print("calling the parent function..")
        parent = self.parent()
        if parent:
            self.close()  
            print("parent to call..")
            parent.clear_all(popup_state = True)
        print("clear all the tasks")

        print(f"[INFO] Selected Task: {task_name} (ID: {task_id})")

        try:
            # ------------------------------
            # 1️⃣ Fetch Task Files from API
            # ------------------------------
            url = f"{MAIN_URL}/app/project/get-task-files/{task_id}/"
            response = requests.get(url, timeout=30)

            if response.status_code != 200:
                print(f"[ERROR] API {response.status_code}: {response.text}")
                QMessageBox.warning(self, "Error", f"Failed to get task files: {response.status_code}")
                return

            data = response.json()
            files = data.get("files", [])

            # ------------------------------
            # 2️⃣ Download or Create Files
            # ------------------------------
            if files:
                print(f"[INFO] Found {len(files)} files for this task.")
                for file_info in files:
                    file_name = file_info['file_name']
                    if file_name.lower().endswith(('.mp4', '.mp3')):
                        print(f"[SKIP] Skipping media file: {file_name}")
                        continue
                    file_url = file_info['file_url']
                    print(f"Downloading: {file_name} from {file_url}")

                    file_data = requests.get(file_url)
                    file_data.raise_for_status()

                    # Check if it's a zip file (task folder zip)
                    if file_name.endswith('.zip') and 'proj_' in file_name and 'task_' in file_name:
                        # Save zip file temporarily
                        temp_zip_path = os.path.join(".", file_name)
                        with open(temp_zip_path, "wb") as f:
                            f.write(file_data.content)
                        print(f"[OK] Downloaded zip file: {file_name}")
                        
                        # Extract zip file to proper folder structure
                        # Get project_id from selected_project dictionary
                        project_id = self.selected_project['id'] if self.selected_project else None
                        if project_id and task_id:
                            success = self.extract_task_zip(temp_zip_path, project_id, task_id)
                            if success:
                                print(f"[OK] Extracted and placed all .py files from zip")
                            else:
                                print(f"[WARN] Failed to extract zip file")
                        else:
                            print(f"[WARN] Project ID or Task ID not available for extraction")
                        
                        # Clean up temporary zip file
                        try:
                            os.remove(temp_zip_path)
                            print(f"[OK] Cleaned up temporary zip file")
                        except:
                            pass
                    else:
                        # Save based on file type
                        if file_name == "execute_code.py":
                            folder = "code_py"
                        elif file_name == "json_xpath.json":
                            folder = "json_info"
                        elif file_name == "citrix_data.json":
                            folder = "json_info"
                        else:
                            folder = "."

                        os.makedirs(folder, exist_ok=True)
                        file_path = os.path.join(folder, file_name)

                        with open(file_path, "wb") as f:
                            f.write(file_data.content)

                        print(f"[OK] Saved {file_name} to {file_path}")

            else:
                print("[WARN] No files found. Creating placeholders...")
                os.makedirs("code_py", exist_ok=True)
                os.makedirs("json_info", exist_ok=True)
                with open("recorded_steps.json", "w", encoding="utf-8") as f:
                    json.dump({}, f)
                open("code_py/execute_code.py", "w", encoding="utf-8").close()
                with open("json_info/json_xpath.json", "w", encoding="utf-8") as f:
                    json.dump({}, f)

            # ------------------------------
            # 3️⃣ Load Local Files
            # ------------------------------
            # recorded_steps.json
            recorded_path = "recorded_steps.json"
            try:
                with open(recorded_path, "r", encoding="utf-8") as f:
                    loaded = json.load(f)
            except (FileNotFoundError, json.JSONDecodeError):
                loaded = {}

            # execute_code.py
            execute_path = "code_py/execute_code.py"
            code_content = ""
            if os.path.exists(execute_path):
                with open(execute_path, "r", encoding="utf-8") as f:
                    code_content = f.read()
                print(f"[OK] Loaded code ({len(code_content)} chars)")
            else:
                print("[WARN] execute_code.py not found.")

            # json_xpath.json
            xpath_path = "json_info/json_xpath.json"
            try:
                with open(xpath_path, "r", encoding="utf-8") as f:
                    xpath_data = json.load(f)
            except (FileNotFoundError, json.JSONDecodeError):
                xpath_data = {}

            # ------------------------------
            # 4️⃣ Update UI Elements
            # ------------------------------
            # Code display update
            if hasattr(self, 'code_display') and self.code_display:
                self.code_display.initialize_state(code_content if code_content else "# No code available")
                print("[UI] Code display updated")

            elif hasattr(self.parent(), 'code_display'):
                # If code_display is in another parent widget
                self.parent().code_display.initialize_state(code_content)
                print("[UI] Parent code display updated")
            
            # Update code_log variable with new code content
            self.code_log = code_content if code_content else ""
            print("[UI] Updated code_log variable")
            
            # Auto-clear chat when new task is selected (web mode only)
            current_mode = getattr(self, 'current_automation_mode', 'web')
            if current_mode == 'web' and hasattr(self, 'on_new_chat_clicked'):
                try:
                    self.on_new_chat_clicked()
                    print("[UI] Chat history cleared for new task")
                except Exception as e:
                    print(f"[WARN] Failed to clear chat history: {e}")

            # Enable Execute Flow button if code is available
            if code_content and code_content.strip():
                if hasattr(self, 'execute_flow_btn'):
                    self.execute_flow_btn.setEnabled(True)
                    print("[UI] ✅ Execute Flow button ENABLED (code available)")
                elif hasattr(self.parent(), 'execute_flow_btn'):
                    self.parent().execute_flow_btn.setEnabled(True)
                    print("[UI] ✅ Parent Execute Flow button ENABLED (code available)")
            else:
                if hasattr(self, 'execute_flow_btn'):
                    self.execute_flow_btn.setEnabled(False)
                    print("[UI] ❌ Execute Flow button DISABLED (no code)")
                elif hasattr(self.parent(), 'execute_flow_btn'):
                    self.parent().execute_flow_btn.setEnabled(False)
                    print("[UI] ❌ Parent Execute Flow button DISABLED (no code)")

            # Chat panel update
            if hasattr(self, 'chat_panel') and hasattr(self.chat_panel, 'update_xpath_display'):
                self.chat_panel.update_xpath_display(xpath_data)
                print(f"[UI] Updated chat panel with {len(xpath_data)} XPath variables")
            elif hasattr(self.parent(), 'chat_panel') and hasattr(self.parent().chat_panel, 'update_xpath_display'):
                self.parent().chat_panel.update_xpath_display(xpath_data)
                print("[UI] Parent chat panel updated")

            # ------------------------------
            # 5️⃣ Update Internal Variables
            # ------------------------------
            self.req_class = loaded.get("steps", [])
            self.task_events = loaded.get("events", [])
            self.full_task_info = loaded.get("combined", [])
            self.xpath_data = xpath_data
            self.final_code_log = code_content
            
            # Store data to pass back to main app
            self.loaded_req_class = self.req_class.copy()
            self.loaded_task_events = self.task_events.copy()
            self.loaded_full_task_info = self.full_task_info.copy()
            self.loaded_xpath_data = xpath_data.copy()
            self.loaded_code_content = code_content

            # ------------------------------
            # 6️⃣ Update Application State
            # ------------------------------
            # Clear and populate task list properly
            if hasattr(self, 'task_list'):
                try:
                    # Clear existing tasks first
                    self.task_list.clear()
                    self.task_list.clear_breakpoints()
                    
                    # Set the loaded data
                    self.task_list.set_tasks_data(self.req_class, self.task_events, getattr(self, 'app_info', None))
                    
                    # Set conditional info if available
                    if hasattr(self, 'conditional_info'):
                        self.task_list.set_conditional_info(self.conditional_info)
                    
                    # Auto-select desktop tasks if task_events available
                    if self.task_events and hasattr(self.task_list, 'auto_select_desktop_tasks'):
                        self.task_list.auto_select_desktop_tasks(self.task_events)
                    
                    print(f"[UI] Successfully populated {len(self.req_class)} tasks in Generated Tasks area")
                    
                except Exception as e:
                    print(f"[ERROR] Failed to populate Generated Tasks: {e}")
                    
            # Also try parent if current object doesn't have task_list
            elif hasattr(self.parent(), 'task_list'):
                try:
                    parent = self.parent()
                    # Clear existing tasks first
                    parent.task_list.clear()
                    parent.task_list.clear_breakpoints()
                    
                    # Set the loaded data
                    parent.task_list.set_tasks_data(self.req_class, self.task_events, getattr(parent, 'app_info', None))
                    
                    # Set conditional info if available
                    if hasattr(parent, 'conditional_info'):
                        parent.task_list.set_conditional_info(parent.conditional_info)
                    
                    # Auto-select desktop tasks if task_events available
                    if self.task_events and hasattr(parent.task_list, 'auto_select_desktop_tasks'):
                        parent.task_list.auto_select_desktop_tasks(self.task_events)
                    
                    print(f"[UI] Successfully populated {len(self.req_class)} tasks in Generated Tasks area (via parent)")
                    
                except Exception as e:
                    print(f"[ERROR] Failed to populate Generated Tasks via parent: {e}")

            if hasattr(self, 'log_message'):
                self.log_message(f"[OK] Generated {len(self.req_class)} steps successfully")

            if hasattr(self, 'statusBar'):
                self.statusBar().showMessage(f"Ready - {len(self.req_class)} steps generated")

            # Enable buttons
            for btn_name in ['start_btn', 'generate_code_btn', 'save_action_btn', 'process_btn']:
                if hasattr(self, btn_name):
                    getattr(self, btn_name).setEnabled(True)

        except Exception as e:
            print(f"[EXCEPTION] {e}")
            QMessageBox.critical(self, "Error", f"Failed to process task: {str(e)}")
        
    def create_projects_page(self):
        """Create the projects selection page"""
        page = QWidget()
        page.setStyleSheet("background: transparent; border: none;")
        layout = QVBoxLayout(page)
        layout.setContentsMargins(25, 0, 25, 0)
        layout.setSpacing(15)
        
        # Projects label with icon + text
        projects_label = QLabel()
        
        # Use resource_path for the icon
        icon_path = resource_path("styles/Icon/folder.png")
        
        # Combine icon + text using setText with HTML
        # Note: For HTML img src in QLabel, you need to use the file:/// protocol
        projects_label.setText(f'<img src="file:///{icon_path}" height="20"> Agent Flow')
        
        # Styling
        projects_label.setStyleSheet("""
            QLabel {
                color: #ffffff !important;
                font-family: 'Asen Pro' !important;
                font-weight: bold !important;
                font-size: 14px !important;
                background: transparent !important;
            }
        """)
        layout.addWidget(projects_label)
        
        # Instruction label
        instruction_label = QLabel("Double-click a Agent to view its tasks")
        instruction_label.setStyleSheet("""
            QLabel {
                color: #aaaaaa !important;
                font-family: 'Asen Pro' !important;
                font-size: 12px !important;
                background: transparent !important;
                font-style: italic !important;
            }
        """)
        layout.addWidget(instruction_label)
        
        # Create Project button
        create_project_btn = QPushButton("✚ Create New Agent Flow")
        create_project_btn.setFixedHeight(35)
        create_project_btn.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1, stop: 0 #008AB3, stop: 1 #005B7F) !important;
                color: #FFFFFF !important;
                border: none !important;
                border-radius: 8px !important;
                font-family: 'Asen Pro' !important;
                font-weight: 600 !important;
                font-size: 16px !important;
                padding: 5px 10px !important;
            }
            QPushButton:hover {
                background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1, stop: 0 #0099CC, stop: 1 #006699) !important;
            }
        """)
        create_project_btn.clicked.connect(self.create_new_project)
        layout.addWidget(create_project_btn)
        
        # Projects list
        self.projects_list = QListWidget()
        self.projects_list.setMinimumHeight(350)
        self.projects_list.setStyleSheet("""
            QListWidget {
                background-color: #2b2b2b !important;
                color: #ffffff !important;
                border: 1px solid #555555 !important;
                border-radius: 8px !important;
                padding: 5px !important;
                font-family: 'Asen Pro' !important;
                font-size: 15px !important;
            }
            QListWidget::item {
                padding: 14px !important;
                border-radius: 4px !important;
                margin: 2px !important;
            }
            QListWidget::item:selected {
                background-color: #008AB3 !important;
                color: #ffffff !important;
            }
            QListWidget::item:hover {
                background-color: #404040 !important;
            }
        """)
        self.projects_list.itemClicked.connect(self.on_project_selected)
        self.projects_list.itemDoubleClicked.connect(self.on_project_double_clicked)
        self.projects_list.installEventFilter(self)
        layout.addWidget(self.projects_list)
        
        return page
    def on_project_selected(self, item):
        """Handle project single-click selection"""
        project_data = item.data(Qt.UserRole)
        if project_data:
            self.selected_project = project_data
            self.select_button.setEnabled(True)

    def on_project_double_clicked(self, item):
        """Handle project double-click - show tasks"""
        project_data = item.data(Qt.UserRole)
        if project_data:
            self.selected_project = project_data
            self.show_tasks_view()
    def create_tasks_page(self):
        """Create the tasks selection page"""
        page = QWidget()
        page.setStyleSheet("background: transparent; border: none;")
        layout = QVBoxLayout(page)
        layout.setContentsMargins(25, 0, 25, 0)
        layout.setSpacing(15)

        # Project info label with folder icon
        folder_icon_path = resource_path("styles/Icon/folder.png")
        self.project_info_label = QLabel()
        self.project_info_label.setText(
            f'<img src="file:///{folder_icon_path}" height="20"> Agent Flow:'
        )
        self.project_info_label.setStyleSheet("""
            QLabel {
                color: #ffffff !important;
                font-family: 'Asen Pro' !important;
                font-weight: bold !important;
                font-size: 14px !important;
                background: transparent !important;
            }
        """)
        layout.addWidget(self.project_info_label)

        # Tasks label with task icon
        task_icon_path = resource_path("styles/Icon/task.png")
        tasks_label = QLabel()
        tasks_label.setText(
            f'<img src="file:///{task_icon_path}" height="20"> Tasks'
        )
        tasks_label.setStyleSheet("""
            QLabel {
                color: #ffffff !important;
                font-family: 'Asen Pro' !important;
                font-weight: bold !important;
                font-size: 14px !important;
                background: transparent !important;
            }
        """)
        layout.addWidget(tasks_label)
        
        # Instruction label
        instruction_label = QLabel("Select a task to continue")
        instruction_label.setStyleSheet("""
            QLabel {
                color: #aaaaaa !important;
                font-family: 'Asen Pro' !important;
                font-size: 12px !important;
                background: transparent !important;
                font-style: italic !important;
            }
        """)
        layout.addWidget(instruction_label)
        
        # Create Task button
        self.create_task_btn = QPushButton("✚ Create New Task")
        self.create_task_btn.setFixedHeight(35)
        self.create_task_btn.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1, stop: 0 #008AB3, stop: 1 #005B7F) !important;
                color: #FFFFFF !important;
                border: none !important;
                border-radius: 8px !important;
                font-family: 'Asen Pro' !important;
                font-weight: 600 !important;
                font-size: 16px !important;
                padding: 5px 10px !important;
            }
            QPushButton:hover {
                background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1, stop: 0 #0099CC, stop: 1 #006699) !important;
            }
        """)
        self.create_task_btn.clicked.connect(self.create_new_task)
        layout.addWidget(self.create_task_btn)
        
        # Tasks list
        self.tasks_list = QListWidget()
        self.tasks_list.setMinimumHeight(350)
        self.tasks_list.setStyleSheet("""
            QListWidget {
                background-color: #2b2b2b !important;
                color: #ffffff !important;
                border: 1px solid #555555 !important;
                border-radius: 8px !important;
                padding: 5px !important;
                font-family: 'Asen Pro' !important;
                font-size: 15px !important;
            }
            QListWidget::item {
                padding: 14px !important;
                border-radius: 4px !important;
                margin: 2px !important;
            }
            QListWidget::item:selected {
                background-color: #008AB3 !important;
                color: #ffffff !important;
            }
            QListWidget::item:hover {
                background-color: #404040 !important;
            }
        """)
        self.tasks_list.itemClicked.connect(self.on_task_selected)
        self.tasks_list.itemDoubleClicked.connect(self.on_task_double_clicked)
        self.tasks_list.installEventFilter(self)
        layout.addWidget(self.tasks_list)
        
        return page
    
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

    def eventFilter(self, obj, event):
        """Handle keyboard shortcuts"""
        if event.type() == QEvent.KeyPress:
            # Handle Enter key on projects list
            if obj == self.projects_list and event.key() == Qt.Key_Return:
                current_item = self.projects_list.currentItem()
                if current_item:
                    project_data = current_item.data(Qt.UserRole)
                    if project_data:
                        self.selected_project = project_data
                        self.show_tasks_view()
                return True
            
            # Handle Enter key on tasks list
            elif obj == self.tasks_list and event.key() == Qt.Key_Return:
                current_item = self.tasks_list.currentItem()
                if current_item:
                    task_data = current_item.data(Qt.UserRole)
                    if task_data:
                        self.selected_task = task_data
                        self.accept()
                return True
            
            # Handle Backspace key globally when on tasks page
            elif event.key() == Qt.Key_Backspace and not self.showing_projects:
                self.go_back_to_projects()
                return True
        
        return super().eventFilter(obj, event)
    
    def load_projects(self):
        """Load projects from API"""
        self.projects_list.clear()
        
        url = f"{MAIN_URL}/app/project/user/{self.userid}/projects/"
        headers = {
            'Content-Type': 'application/json',
            'Cookie': 'sessionid=wjhnaudx6uyfal7iqlok1cyt43glmr0e'
        }
        
        try:
            response = requests.get(url, headers=headers)
            response.raise_for_status()
            projects_output = response.json()
            self.projects_data = projects_output.get('projects', [])
            
            if not self.projects_data:
                item = QListWidgetItem("No Agents found")
                item.setFlags(Qt.NoItemFlags)
                self.projects_list.addItem(item)
            else:
                for project in self.projects_data:
                    # Create list item
                    list_item = QListWidgetItem()
                    list_item.setData(Qt.UserRole, project)
                    
                    # Create custom widget with menu
                    item_widget = self.create_list_item_with_menu(
                        project['project_name'], 
                        project, 
                        "project"
                    )
                    
                    # Set size hint for proper display
                    list_item.setSizeHint(QSize(0, 50))
                    
                    self.projects_list.addItem(list_item)
                    self.projects_list.setItemWidget(list_item, item_widget)
                        
        except requests.RequestException as e:
            print(f"Error fetching projects: {e}")
            self.show_custom_error("Error", f"Failed to load projects: {str(e)}")
    
    def on_project_double_clicked(self, item):
        """Handle project double-click - show tasks"""
        project_data = item.data(Qt.UserRole)
        if project_data:
            self.selected_project = project_data
            self.show_tasks_view()
    
    def show_tasks_view(self):
        """Switch to tasks view"""
        if not self.selected_project:
            return

        self.showing_projects = False
        self.title_label.setText("Select Task")
        
        # Update the label with folder icon + dynamic project name
        folder_icon_path = resource_path("styles/Icon/folder.png")
        self.project_info_label.setText(
            f'<img src="file:///{folder_icon_path}" height="20"> Agent: {self.selected_project["project_name"]}'
        )

        self.back_btn.setVisible(True)
        self.stacked_widget.setCurrentIndex(1)
        self.load_tasks(self.selected_project['id'])

    
    def go_back_to_projects(self):
        """Go back to projects view"""
        self.showing_projects = True
        self.title_label.setText("Select Agent Flow")
        self.back_btn.setVisible(False)
        self.stacked_widget.setCurrentIndex(0)
        self.selected_task = None
         # Keep Select button enabled if a project is selected
        if self.selected_project:
            self.select_button.setEnabled(True)
            # Re-highlight the selected project
            for i in range(self.projects_list.count()):
                item = self.projects_list.item(i)
                project_data = item.data(Qt.UserRole)
                if project_data and project_data['id'] == self.selected_project['id']:
                    self.projects_list.setCurrentItem(item)
                    break
        else:
            self.select_button.setEnabled(False)
        
    def load_tasks(self, project_id):
        """Load tasks for selected project"""
        self.tasks_list.clear()
        self.selected_task = None
        
        url = f"{MAIN_URL}/app/project/{project_id}/tasks/"
        headers = {
            'Content-Type': 'application/json',
            'Cookie': 'sessionid=wjhnaudx6uyfal7iqlok1cyt43glmr0e'
        }
        
        try:
            response = requests.get(url, headers=headers)
            response.raise_for_status()
            tasks_output = response.json()
            tasks = tasks_output.get('tasks', [])
            
            if not tasks:
                item = QListWidgetItem("No tasks found")
                item.setFlags(Qt.NoItemFlags)
                self.tasks_list.addItem(item)
            else:
                for task in tasks:
                    # Create list item
                    list_item = QListWidgetItem()
                    list_item.setData(Qt.UserRole, task)
                    
                    # Create custom widget with menu
                    item_widget = self.create_list_item_with_menu(
                        task['task_name'], 
                        task, 
                        "task"
                    )
                    
                    # Set size hint for proper display
                    list_item.setSizeHint(QSize(0, 50))
                    
                    self.tasks_list.addItem(list_item)
                    self.tasks_list.setItemWidget(list_item, item_widget)
                        
        except requests.RequestException as e:
            print(f"Error fetching tasks: {e}")
            self.show_custom_error("Error", f"Failed to load tasks: {str(e)}")
    
    def on_task_selected(self, item):
        """Handle task selection"""
        task_data = item.data(Qt.UserRole)
        if task_data:
            self.selected_task = task_data
            self.select_button.setEnabled(True)
    
    def on_task_double_clicked(self, item):
        """Handle task double-click - auto accept"""
        task_data = item.data(Qt.UserRole)
        if task_data:
            self.selected_task = task_data
            self.accept()
    
    def show_custom_error(self, title, message):
        """Show custom styled error popup"""
        dialog = QDialog(self)
        dialog.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool)
        dialog.setAttribute(Qt.WA_TranslucentBackground)
        dialog.setFixedSize(500, 250)
        dialog.setModal(True)
        
        container = QWidget(dialog)
        container.setGeometry(0, 0, 500, 250)
        container.setStyleSheet("background-color: #414141; border-radius: 15px;")
        
        layout = QVBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 25)
        
        # Title
        title_container = QWidget()
        title_container.setFixedHeight(60)
        title_container.setStyleSheet("background: #333333; border-radius: 20px 20px 0px 0px;")
        title_layout = QHBoxLayout(title_container)
        title_layout.setContentsMargins(25, 15, 25, 15)
        title_label = QLabel(f"❌ {title}")
        title_label.setStyleSheet("color: #ffffff; font-family: 'Asen Pro'; font-weight: bold; font-size: 16px; background: transparent;")
        title_layout.addWidget(title_label)
        layout.addWidget(title_container)
        
        layout.addSpacing(40)
        
        # Message
        msg_label = QLabel(message)
        msg_label.setStyleSheet("color: #FFFFFF; font-family: 'Asen Pro'; font-size: 14px; padding: 10px 40px;")
        msg_label.setWordWrap(True)
        msg_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(msg_label)
        
        layout.addSpacing(40)
        
        # OK button
        btn_layout = QHBoxLayout()
        ok_btn = QPushButton("OK")
        ok_btn.setFixedSize(120, 40)
        ok_btn.setStyleSheet("QPushButton { background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1, stop: 0 #008AB3, stop: 1 #005B7F); color: #FFFFFF; border: none; border-radius: 10px; font-family: 'Asen Pro'; font-weight: 600; font-size: 16px; }")
        ok_btn.clicked.connect(dialog.accept)
        btn_layout.addStretch()
        btn_layout.addWidget(ok_btn)
        btn_layout.addStretch()
        layout.addLayout(btn_layout)
        
        dialog.exec_()
    
    def create_new_project(self):
        """Open dialog to create new project"""
        project_dialog = NewItemDialog_project(
            parent=self,
            user_id=self.userid,
            refreshtoken=self.refreshtoken,
            accesstoken=self.accesstoken
        )
        
        if project_dialog.exec_() == QDialog.Accepted:
            created_project = project_dialog.created_project
            self.load_projects()
            
            # Select and open the newly created project
            for i in range(self.projects_list.count()):
                item = self.projects_list.item(i)
                project_data = item.data(Qt.UserRole)
                if project_data and project_data['id'] == created_project['id']:
                    self.selected_project = project_data
                    self.show_tasks_view()
                    break
    
    def create_new_task(self):
        """Open dialog to create new task for selected project"""
        if not self.selected_project:
            self.show_custom_error("Warning", "Please select a project first")
            return
        
        task_dialog = NewItemDialog_task(
            parent=self,
            projectid=self.selected_project['id'],
            refreshtoken=self.refreshtoken,
            accesstoken=self.accesstoken
        )
        
        if task_dialog.exec_() == QDialog.Accepted:
            created_task = task_dialog.created_task
            self.load_tasks(self.selected_project['id'])
            
            # Select the newly created task
            for i in range(self.tasks_list.count()):
                item = self.tasks_list.item(i)
                task_data = item.data(Qt.UserRole)
                if task_data and task_data['id'] == created_task['id']:
                    self.tasks_list.setCurrentItem(item)
                    self.on_task_selected(item)
                    break
    
    def edit_project(self, project):
        """Edit project name"""
        from PyQt5.QtWidgets import QInputDialog
        
        new_name, ok = QInputDialog.getText(
            self,
            "Edit Agent Flow",
            "Enter new name:",
            text=project['project_name']
        )
        
        if ok and new_name.strip():
            project_id = project['id']
            url = f"{MAIN_URL}/app/project/projects/{project_id}/"
            headers = {
                "Authorization": f"Bearer {self.accesstoken}",
                "Content-Type": "application/json"
            }
            
            try:
                r = requests.patch(url, json={"project_name": new_name.strip()}, headers=headers)
                
                if r.status_code == 200:
                    self.load_projects()
                    # Re-select if this was the selected project
                    if self.selected_project and self.selected_project['id'] == project_id:
                        self.selected_project['project_name'] = new_name.strip()
                    print(f"✅ Project updated successfully")
                else:
                    print(f"❌ Failed to update project: {r.status_code} - {r.text}")
                    self.show_custom_error("Error", f"Failed to update project: {r.status_code}")
            except Exception as e:
                print(f"❌ Exception updating project: {e}")
                self.show_custom_error("Error", f"Failed to update project: {str(e)}")

    def delete_project(self, project):
        """Delete project"""
        from PyQt5.QtWidgets import QMessageBox
        
        reply = QMessageBox.question(
            self,
            "Delete Agent Flow",
            f"Are you sure you want to delete '{project['project_name']}'?\n",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            project_id = project['id']
            url = f"{MAIN_URL}/app/project/projects/{project_id}/"
            headers = {
                "Authorization": f"Bearer {self.accesstoken}",
                "Content-Type": "application/json"
            }
            
            try:
                print(f"🗑️ Attempting to delete project: {project_id}")
                print(f"🔗 URL: {url}")
                r = requests.delete(url, headers=headers)
                
                print(f"📡 Response status: {r.status_code}")
                print(f"📡 Response body: {r.text}")
                
                if r.status_code in [200, 204]:
                    # Clear selection if deleted project was selected
                    if self.selected_project and self.selected_project['id'] == project_id:
                        self.selected_project = None
                        self.select_button.setEnabled(False)
                    self.load_projects()
                    print(f"✅ Project deleted successfully")
                else:
                    print(f"❌ Failed to delete project: {r.status_code}")
                    self.show_custom_error("Error", f"Failed to delete project: {r.status_code}\n{r.text}")
            except Exception as e:
                print(f"❌ Exception deleting project: {e}")
                self.show_custom_error("Error", f"Failed to delete project: {str(e)}")

    def edit_task(self, task):
        """Edit task name"""
        from PyQt5.QtWidgets import QInputDialog

        new_name, ok = QInputDialog.getText(
            self,
            "Edit Task",
            "Enter new name:",
            text=task['task_name']
        )

        if ok and new_name.strip():
            task_id = task['id']
            project_id = self.selected_project['id']

            # ✅ UPDATED URL FORMAT
            url = f"{MAIN_URL}/app/project/tasks/{task_id}/?project_id={project_id}"

            headers = {
                "Authorization": f"Bearer {self.accesstoken}",
                "Content-Type": "application/json"
            }

            try:
                print(f"✏️ Attempting to edit task: {task_id}")
                print(f"🔗 URL: {url}")

                r = requests.patch(
                    url,
                    json={"task_name": new_name.strip()},
                    headers=headers
                )

                print(f"📡 Response status: {r.status_code}")
                print(f"📡 Response body: {r.text}")

                if r.status_code == 200:
                    self.load_tasks(project_id)

                    # Re-select if this was the selected task
                    if self.selected_task and self.selected_task['id'] == task_id:
                        self.selected_task['task_name'] = new_name.strip()

                    print(f"✅ Task updated successfully")
                else:
                    print(f"❌ Failed to update task: {r.status_code}")
                    self.show_custom_error("Error", f"Failed to update task: {r.status_code}\n{r.text}")

            except Exception as e:
                print(f"❌ Exception updating task: {e}")
                self.show_custom_error("Error", f"Failed to update task: {str(e)}")

    def delete_task(self, task):
        """Delete task"""
        from PyQt5.QtWidgets import QMessageBox

        reply = QMessageBox.question(
            self,
            "Delete Task",
            f"Are you sure you want to delete '{task['task_name']}'?\nThis action cannot be undone.",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )

        if reply == QMessageBox.Yes:
            task_id = task['id']
            project_id = self.selected_project['id']

            # ✅ UPDATED URL FORMAT
            url = f"{MAIN_URL}/app/project/tasks/{task_id}/?project_id={project_id}"

            headers = {
                "Authorization": f"Bearer {self.accesstoken}",
                "Content-Type": "application/json"
            }

            try:
                print(f"🗑️ Attempting to delete task: {task_id}")
                print(f"🔗 URL: {url}")

                r = requests.delete(url, headers=headers)

                print(f"📡 Response status: {r.status_code}")
                print(f"📡 Response body: {r.text}")

                if r.status_code in [200, 204]:
                    # Clear selection if deleted task was selected
                    if self.selected_task and self.selected_task['id'] == task_id:
                        self.selected_task = None
                        self.select_button.setEnabled(False)

                    self.load_tasks(project_id)
                    print(f"✅ Task deleted successfully")
                else:
                    print(f"❌ Failed to delete task: {r.status_code}")
                    self.show_custom_error("Error", f"Failed to delete task: {r.status_code}\n{r.text}")

            except Exception as e:
                print(f"❌ Exception deleting task: {e}")
                self.show_custom_error("Error", f"Failed to delete task: {str(e)}")


    def on_project_selected(self, item):
        """Handle project single-click selection"""
        project_data = item.data(Qt.UserRole)
        if project_data:
            self.selected_project = project_data
            self.select_button.setEnabled(True)

    def on_task_selected(self, item):
        """Handle task selection"""
        task_data = item.data(Qt.UserRole)
        if task_data:
            self.selected_task = task_data
            self.select_button.setEnabled(True)


from PyQt5.QtCore import QThread, pyqtSignal
from gemini_api import restructure_prompt

from PyQt5.QtCore import QThread, pyqtSignal
from gemini_api import restructure_prompt



def create_text_icon(text, size=32, color="#333333"):
    pixmap = QPixmap(size, size)
    pixmap.fill(Qt.transparent)
    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.Antialiasing)
    painter.setFont(QFont("Segoe UI Emoji", int(size * 0.6)))
    painter.setPen(QColor(color))
    painter.drawText(pixmap.rect(), Qt.AlignCenter, text)
    painter.end()
    return QIcon(pixmap)

class EmbeddedFlowchartEditor(QWidget):
    """Fully functional embedded flowchart editor - matches pdd_flowchart.py behavior"""
 
    def __init__(self, json_path=None, parent=None):
        super().__init__(parent)
        self.json_path = json_path
        
        # Tool state (NEW - matches main editor)
        self.current_tool = "select"  # "select", "line", "arrow"
        self.temp_line = None
        
        self.scene = QGraphicsScene()
        self.scene.setBackgroundBrush(QBrush(QColor("#F2F2F2")))
 
        # Use the same FlowView with full interaction support
        self.view = FlowView(self.scene, self)
        self.view.setRenderHints(QPainter.Antialiasing | QPainter.SmoothPixmapTransform)
        self.view.setStyleSheet("background-color: #F2F2F2;")
        self.view.setSceneRect(-5000, -5000, 10000, 10000)  # Large scene
 
        self.nodes = []
        self.first_node = None  # For connecting nodes
 
        self.init_ui()
 
        if json_path and os.path.exists(json_path):
            QTimer.singleShot(100, self.load_flowchart_from_path)
 
    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        layout.addWidget(self.view)
 
        # Create toolbars
        self.create_floating_toolbar()
        self.create_left_shape_panel()
 
    def create_floating_toolbar(self):
        toolbar_container = QWidget(self)
        toolbar_container.setStyleSheet("""
            QWidget { background-color: rgba(255, 255, 255, 0.95); border-radius: 16px;
                      border: 1px solid rgba(0, 0, 0, 0.1); }
        """)
 
        layout = QVBoxLayout()
        layout.setSpacing(8)
        layout.setContentsMargins(12, 12, 12, 12)
 
        button_style = """
            QToolButton {
                background-color: rgba(255, 255, 255, 0.7);
                border: 1px solid rgba(0, 0, 0, 0.15);
                border-radius: 12px;
                padding: 0px;
                min-width: 56px;
                max-width: 56px;
                min-height: 56px;
                max-height: 56px;
            }
            QToolButton:hover {
                background-color: rgba(227, 242, 253, 0.9);
                border-color: #2196F3;
            }
            QToolButton:pressed {
                background-color: #bbdefb;
            }
        """
        
        # Color picker button
        color_btn = QToolButton()
        color_btn.setIcon(create_text_icon("🎨", 28))
        color_btn.setIconSize(QSize(28, 28))
        color_btn.setToolTip("Change Node Color")
        color_btn.setStyleSheet(button_style)
        color_btn.clicked.connect(self.change_node_color)
        layout.addWidget(color_btn)
        
        # Delete
        delete_btn = QToolButton()
        delete_btn.setIcon(create_text_icon("🗑️", 28))
        delete_btn.setIconSize(QSize(28, 28))
        delete_btn.setToolTip("Delete Selected")
        delete_btn.setStyleSheet(button_style)
        delete_btn.clicked.connect(self.delete_selected)
        layout.addWidget(delete_btn)
 
        # Grid toggle button
        self.grid_btn = QToolButton()
        self.grid_btn.setIcon(create_text_icon("◻️", 28))
        self.grid_btn.setIconSize(QSize(28, 28))
        self.grid_btn.setToolTip("Toggle Grid")
        self.grid_btn.setStyleSheet(button_style)
        self.grid_btn.clicked.connect(self.toggle_grid)
        layout.addWidget(self.grid_btn)
 
        layout.addStretch()
        toolbar_container.setLayout(layout)
        self.toolbar_container = toolbar_container
        self.position_toolbar()
        toolbar_container.raise_()
    
    def change_node_color(self):
        """Updated to support both nodes and lines"""
        selected = [i for i in self.scene.selectedItems() if isinstance(i, FlowNode)]
        if not selected:
            QMessageBox.information(self, "No Selection", "Select nodes or lines first.")
            return
        
        # For nodes only
        border = QColorDialog.getColor(selected[0].border_color, self, "Border Color")
        if not border.isValid(): 
            return
        fill = QColorDialog.getColor(selected[0].fill_color, self, "Fill Color")
        if not fill.isValid(): 
            return
        
        for item in selected:
            if isinstance(item, FlowNode):
                item.set_colors(border.name(), fill.name())
    
    def create_left_shape_panel(self):
        """Create permanent shape panel on the left side - updated with line/arrow tools"""
        shape_container = QWidget(self)
        shape_container.setStyleSheet("""
            QWidget {
                background-color: rgba(255, 255, 255, 0.95);
                border-radius: 16px;
                border: 1px solid rgba(0, 0, 0, 0.1);
            }
        """)
       
        layout = QVBoxLayout()
        layout.setSpacing(10)
        layout.setContentsMargins(12, 12, 12, 12)
       
        # Style for shape buttons
        button_style = """
            QToolButton {
                background-color: white;
                border: 2px solid #e0e0e0;
                border-radius: 10px;
                padding: 0px;
                min-width: 56px;
                max-width: 56px;
                min-height: 56px;
                max-height: 56px;
                font-size: 32px;
                font-family: "Segoe UI Symbol", "Arial";
                color: #000000;
            }
            QToolButton:hover {
                background-color: #f0f7ff;
                border-color: #2196F3;
                color: #000000;
            }
            QToolButton:pressed {
                background-color: #e3f2fd;
                color: #000000;
            }
            QToolButton:checked {
                background-color: #bbdefb;
                border-color: #1976D2;
                border-width: 3px;
                color: #000000;
            }
        """
       
        shapes = [
            ("▭", FlowNode.Rectangle, "Rectangle", None),
            ("◇", FlowNode.Diamond, "Decision", None),
            ("⬭", FlowNode.Terminator, "Start/End", None),
            ("▱", FlowNode.Parallelogram, "I/O", None),
            ("○", FlowNode.Circle, "Circle", None),
            ("▢", FlowNode.RoundedRect, "Rounded Rect", None),
            ("─", None, "Line Tool", "line"),
            ("→", None, "Arrow Tool", "arrow"),
        ]
        
        self.tool_buttons = []
       
        for icon, node_type, tooltip, tool in shapes:
            btn = QToolButton()
            btn.setText(icon)
            btn.setToolTip(tooltip)
            btn.setStyleSheet(button_style)
            btn.setCheckable(True)
            
            if tool:
                btn.clicked.connect(lambda checked, t=tool, b=btn: self.set_tool(t, b))
                self.tool_buttons.append((tool, btn))
            else:
                btn.clicked.connect(lambda _, t=node_type, txt=tooltip: self.add_node_and_select(t, txt))
            
            layout.addWidget(btn)
       
        shape_container.setLayout(layout)
        self.shape_container = shape_container
        self.position_shape_panel()
        shape_container.raise_()
    
    def set_tool(self, tool_name, button=None):
        """Switch between select, line, and arrow tools"""
        self.current_tool = tool_name
        
        # Uncheck all tool buttons
        for tool, btn in self.tool_buttons:
            btn.setChecked(tool == tool_name)
        
        # Clear selection and reset state
        self.scene.clearSelection()
        self.first_node = None
        
        # Update cursor
        if tool_name == "select":
            self.view.setCursor(Qt.ArrowCursor)
        else:
            self.view.setCursor(Qt.CrossCursor)
    
    def add_node_and_select(self, node_type, default_text):
        """Add a node and switch to select tool"""
        self.set_tool("select")
        center = self.view.mapToScene(self.view.viewport().rect().center())
        node = FlowNode(node_type, default_text, center)
        self.scene.addItem(node)
        self.nodes.append(node)
        node.setSelected(True)
 
    def position_toolbar(self):
        if not hasattr(self, 'toolbar_container'): 
            return
        w, h = 72, 180
        self.toolbar_container.setGeometry(self.width() - w - 18, (self.height() - h) // 2, w, h)
 
    def position_shape_panel(self):
        if not hasattr(self, 'shape_container'): 
            return
        w, h = 80, 540  # Increased height for 8 buttons
        self.shape_container.setGeometry(18, (self.height() - h) // 2, w, h)
 
    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.position_toolbar()
        self.position_shape_panel()
 
    def toggle_grid(self):
        self.view.grid_mode = (self.view.grid_mode + 1) % 3
        icons = ["Grid Off", "Dot Grid", "Line Grid"]
        self.grid_btn.setIcon(create_text_icon(icons[self.view.grid_mode], 28))
        self.view.viewport().update()
    
    def add_node(self, node_type, text="Step"):
        pos = self.view.mapToScene(self.view.viewport().rect().center())
        node = FlowNode(node_type, text, pos)
        self.scene.addItem(node)
        self.nodes.append(node)
 
    def delete_selected(self):
        """Updated to support deletion of arrows and resizable lines"""
        for item in list(self.scene.selectedItems()):
            if isinstance(item, FlowNode):
                for arrow in list(item.connections):
                    self.scene.removeItem(arrow)
                self.scene.removeItem(item)
                if item in self.nodes:
                    self.nodes.remove(item)
            elif isinstance(item, Arrow):
                if item in item.start_node.connections:
                    item.start_node.connections.remove(item)
                if item in item.end_node.connections:
                    item.end_node.connections.remove(item)
                self.scene.removeItem(item)
            else:
                # Handle ResizableLine or other items (check if class exists)
                try:
                    if isinstance(item, ResizableLine):
                        self.scene.removeItem(item)
                except NameError:
                    # ResizableLine not defined, just try to remove the item
                    if hasattr(item, 'scene') and item.scene() == self.scene:
                        self.scene.removeItem(item)
    
    def auto_arrange_from_node(self, start_node):
        visited = set()
        levels = {}
       
        def dfs(node, level=0):
            if node in visited: 
                return
            visited.add(node)
            levels.setdefault(level, []).append(node)
            for arrow in node.connections:
                if arrow.start_node == node:
                    dfs(arrow.end_node, level + 1)
       
        dfs(start_node)
       
        h_space, v_space = 220, 160
        for level, nodes in levels.items():
            y = start_node.scenePos().y() + level * v_space
            total_w = (len(nodes) - 1) * h_space
            x0 = start_node.scenePos().x() - total_w / 2
            for i, n in enumerate(nodes):
                n.setPos(x0 + i * h_space, y)
        
        for node in visited:
            for arrow in node.connections:
                arrow.update_position()
 
    def load_flowchart_from_path(self):
        if not self.json_path or not os.path.exists(self.json_path):
            return
        try:
            with open(self.json_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            self.load_flowchart_data(data)
            print(f"Loaded flowchart from {self.json_path}")
        except Exception as e:
            print(f"Error loading flowchart: {e}")
            QMessageBox.critical(self, "Load Error", f"Failed to load:\n{e}")
 
    def load_flowchart_data(self, data):
        self.scene.clear()
        self.nodes.clear()
        FlowNode._next_id = 0
        id_to_node = {}
        
        for nd in data.get("nodes", []):
            node_type = nd.get("type", 0)
            text = nd.get("text", "Node")
            pos = QPointF(nd.get("x", 100), nd.get("y", 100))
            node = FlowNode(node_type, text, pos)
            node.node_id = nd["id"]
            if node.node_id >= FlowNode._next_id:
                FlowNode._next_id = node.node_id + 1
            
            # Load sizes from JSON
            node.width = nd.get("width", 400)
            node.height = nd.get("height", 100)

            # ===== NEW: Load font properties =====
            node.font_size = nd.get("font_size", 15)
            node.font_weight = nd.get("font_weight", "bold")
            node.update_text_font()  # Apply font settings
            # =====================================
 
            # Load custom colors if present
            border = nd.get("border", "#1976D2")
            fill = nd.get("fill", "#E3F2FD")
            node.set_colors(border, fill)
 
            node.update_shape()
            self.scene.addItem(node)
            self.nodes.append(node)
            id_to_node[node.node_id] = node
 
        for arr in data.get("arrows", []):
            s = id_to_node.get(arr["start_id"])
            e = id_to_node.get(arr["end_id"])
            if s and e:
                waypoints = arr.get("waypoints", [])  # NEW: Load waypoints
                label = arr.get("label", None)        # NEW: Load label
                arrow = Arrow(s, e, waypoints, label)
                self.scene.addItem(arrow)
    
    def save_flowchart_to_json(self, file_path):
        data = {"nodes": [], "arrows": []}
        for node in self.nodes:
            data["nodes"].append({
                "id": node.node_id,
                "type": node.node_type,
                "text": node.text_item.toPlainText(),
                "x": node.scenePos().x(),
                "y": node.scenePos().y(),
                "width": node.width,
                "height": node.height,
                "border": node.border_color.name(),
                "fill": node.fill_color.name(),
                # ===== NEW: Save font properties =====
                "font_size": getattr(node, 'font_size', 15),         # NEW
                "font_weight": getattr(node, 'font_weight', 'bold')  # NEW
                # =====================================
            })
        
        seen = set()
        for node in self.nodes:
            for arrow in node.connections:
                if isinstance(arrow, Arrow) and id(arrow) not in seen:
                    seen.add(id(arrow))
                    arrow_data = {
                        "start_id": arrow.start_id, 
                        "end_id": arrow.end_id
                    }
                    if arrow.waypoints:  # NEW: Save waypoints if present
                        arrow_data["waypoints"] = arrow.waypoints
                    if arrow.label:  # NEW: Save label if present
                        arrow_data["label"] = arrow.label
                    data["arrows"].append(arrow_data)
        
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=4)
            return True
        except Exception as e:
            print(f"Save error: {e}")
            return False
 
    def export_to_png(self, file_path):
        """Export flowchart as PNG"""
        try:
            if not self.scene.items():
                QMessageBox.warning(self, "Empty Diagram", "Nothing to export!")
                return False

            # Get bounding rect of all items + padding
            items_rect = self.scene.itemsBoundingRect()
            padding = 80
            source_rect = items_rect.adjusted(-padding, -padding, padding, padding)

            # Create image with correct size
            image = QPixmap(source_rect.size().toSize())
            image.fill(QColor("#F2F2F2"))

            # Create painter and render scene
            painter = QPainter()
            painter.begin(image)
            painter.setRenderHint(QPainter.Antialiasing, True)
            painter.setRenderHint(QPainter.SmoothPixmapTransform, True)

            # Render the scene into the pixmap
            self.scene.render(painter, QRectF(image.rect()), source_rect)

            # End painting before saving
            painter.end()

            # Save
            result = image.save(file_path, "PNG", quality=100)
            
            if result:
                print(f"Exported flowchart to PNG: {file_path}")
                return True
            else:
                print(f"Failed to save PNG: {file_path}")
                return False

        except Exception as e:
            print(f"PNG export error: {e}")
            import traceback
            traceback.print_exc()
            QMessageBox.critical(self, "Export Error", f"Failed to export PNG:\n{e}")
            return False



class DraggableImageLabel(QLabel):
    """Image label with drag-and-drop, copy, and zoom-on-hover functionality"""
    image_swap_requested = pyqtSignal(int, int)  # from_idx, to_idx
    image_copy_requested = pyqtSignal(int, int)  # from_idx, to_idx
    
    def __init__(self, step_idx, parent=None):
        super().__init__(parent)
        self.step_idx = step_idx
        self.setAcceptDrops(True)
        self.setScaledContents(False)
        self.setCursor(Qt.OpenHandCursor)
        
        # Zoom properties
        self.original_pixmap = None
        self.is_zoomed = False
        self.zoom_factor = 1.15  # 15% zoom
    
    def setPixmap(self, pixmap):
        """Override setPixmap to store original for zoom"""
        self.original_pixmap = pixmap
        super().setPixmap(pixmap)
    
    def enterEvent(self, event):
        """Zoom in when mouse enters"""
        if self.original_pixmap and not self.original_pixmap.isNull() and not self.is_zoomed:
            self.is_zoomed = True
            # Scale up the pixmap
            zoomed = self.original_pixmap.scaled(
                int(350 * self.zoom_factor), 
                int(275 * self.zoom_factor),
                Qt.KeepAspectRatio, 
                Qt.SmoothTransformation
            )
            super().setPixmap(zoomed)
            
            # Add glow effect
            self.setStyleSheet("""
                QLabel {
                    border: 3px solid #4ecdc4;
                    background: #1e1e1e;
                    border-radius: 8px;
                }
            """)
        super().enterEvent(event)
    
    def leaveEvent(self, event):
        """Zoom out when mouse leaves"""
        if self.original_pixmap and not self.original_pixmap.isNull() and self.is_zoomed:
            self.is_zoomed = False
            # Restore original size
            scaled = self.original_pixmap.scaled(350, 275, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            super().setPixmap(scaled)
            
            # Remove glow effect
            self.setStyleSheet("""
                QLabel {
                    border: 2px solid #404040;
                    background: #1e1e1e;
                    border-radius: 8px;
                }
            """)
        super().leaveEvent(event)
        
    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.setCursor(Qt.ClosedHandCursor)
            drag = QDrag(self)
            mime_data = QMimeData()
            
            # Store step index and whether it's a copy operation (Ctrl key)
            is_copy = event.modifiers() & Qt.ControlModifier
            mime_data.setText(f"{self.step_idx}|{'copy' if is_copy else 'swap'}")
            
            # Create drag preview
            pixmap = self.pixmap()
            if pixmap and not pixmap.isNull():
                scaled = pixmap.scaled(120, 90, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                drag.setPixmap(scaled)
                drag.setHotSpot(scaled.rect().center())
            
            drag.setMimeData(mime_data)
            drag.exec_(Qt.CopyAction | Qt.MoveAction)
            self.setCursor(Qt.OpenHandCursor)
    
    def dragEnterEvent(self, event):
        if event.mimeData().hasText():
            event.acceptProposedAction()
            self.setStyleSheet(self.styleSheet() + """
                border: 3px solid #4ecdc4 !important;
                background: #2a3a3a !important;
            """)
    
    def dragLeaveEvent(self, event):
        self.setStyleSheet("""
            QLabel {
                border: 2px solid #404040;
                background: #1e1e1e;
                border-radius: 8px;
            }
        """)
    
    def dropEvent(self, event):
        self.setStyleSheet("""
            QLabel {
                border: 2px solid #404040;
                background: #1e1e1e;
                border-radius: 8px;
            }
        """)
        
        if event.mimeData().hasText():
            data = event.mimeData().text().split('|')
            from_idx = int(data[0])
            operation = data[1] if len(data) > 1 else 'swap'
            
            if from_idx != self.step_idx:
                if operation == 'copy':
                    self.image_copy_requested.emit(from_idx, self.step_idx)
                else:
                    self.image_swap_requested.emit(from_idx, self.step_idx)
                event.acceptProposedAction()

class GeminiWorker(QThread):
    finished = pyqtSignal(str)

    def __init__(self, user_text):
        super().__init__()
        self.user_text = user_text

    def run(self):
        try:
            result = restructure_prompt(self.user_text)
            self.finished.emit(result)
        except Exception as e:
            self.finished.emit(f"[Error] {e}")


class StepOperationThread(QThread):
    """Separate thread for step edit/delete/insert operations"""
    operation_complete = pyqtSignal(dict)
    error = pyqtSignal(str)
   
    def __init__(self, operation_type, step_data=None, step_idx=None):
        super().__init__()
        self.operation_type = operation_type
        self.step_data = step_data
        self.step_idx = step_idx
   
    def run(self):
        try:
            result = {
                'operation': self.operation_type,
                'step_idx': self.step_idx,
                'step_data': self.step_data,
                'success': True
            }
            self.operation_complete.emit(result)
        except Exception as e:
            self.error.emit(f"Step operation failed: {str(e)}")



class StepReviewWidget(QWidget):
    step_changed = pyqtSignal(int, dict)
    insert_requested = pyqtSignal(int)
    delete_requested = pyqtSignal(int)
    image_swap_requested = pyqtSignal(int, int)
    image_copy_requested = pyqtSignal(int, int)

    def __init__(self, step_data: dict, step_idx: int, parent=None):
        super().__init__(parent)
        self.step_data = dict(step_data)
        self.original_idx = step_idx
        self.setup_ui()
        self.refresh_display()

    def setup_ui(self):
        main = QHBoxLayout(self)
        main.setContentsMargins(14, 14, 14, 14)
        main.setSpacing(8)

        # === IMAGE ===
        self.thumb = DraggableImageLabel(self.original_idx)
        self.thumb.setFixedSize(340, 260)
        self.thumb.setStyleSheet("background:#1e1e1e; border:2px solid #404040; border-radius:12px;")
        self.thumb.setAlignment(Qt.AlignCenter)
        self.thumb.image_swap_requested.connect(lambda f, t: self.image_swap_requested.emit(f, t))
        self.thumb.image_copy_requested.connect(lambda f, t: self.image_copy_requested.emit(f, t))

        self.update_image()

        hint = QLabel("Drag to swap • Ctrl+Drag to copy")
        hint.setStyleSheet("color:#666; font-size:11px; padding:6px 0 0 0;")
        hint.setAlignment(Qt.AlignCenter)

        img_box = QVBoxLayout()
        img_box.addWidget(self.thumb)
        img_box.addWidget(hint)
        img_box.setSpacing(6)
        main.addLayout(img_box)

        # === CONTENT AREA (Text OR Editor) ===
        content_area = QVBoxLayout()
        content_area.setSpacing(8)
        content_area.setContentsMargins(0, 0, 0, 0)

        # TEXT DISPLAY
        text_box = QVBoxLayout()
        text_box.setSpacing(8)

        self.title = QLabel()
        self.title.setStyleSheet("font-size:21px; font-weight:bold; color:#4ecdc4;")

        self.system = QLabel()
        self.system.setStyleSheet("font-size:19px; color:#bbbbbb;")

        self.actions = QLabel()
        self.actions.setWordWrap(True)
        self.actions.setStyleSheet("font-size:19px; color:#e0e0e0; line-height:1.4;")

        text_box.addWidget(self.title)
        text_box.addWidget(self.system)
        text_box.addWidget(self.actions)
        text_box.addStretch()
        content_area.addLayout(text_box)

        # === EDITOR ===
        self.editor = QTextEdit()
        self.editor.setMinimumHeight(180)
        self.editor.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.editor.setStyleSheet("""
            background:#1e1e1e; color:#e0e0e0; border:2px solid #404040; border-radius:10px;
            padding:12px; font-family:Consolas; font-size:16px;
        """)
        self.editor.setVisible(False)
        content_area.addWidget(self.editor, stretch=1)

        main.addLayout(content_area, stretch=1)

        # === BUTTONS (Right side) ===
        def btn(icon, tip, accent=False):
            b = QPushButton()
            b.setIcon(QIcon(resource_path(icon)))
            b.setToolTip(tip)
            b.setFixedSize(42, 42)
            if accent:
                b.setStyleSheet("""
                    QPushButton {background:#4ecdc4; border:none; border-radius:21px;}
                    QPushButton:hover {background:#45b7aa;}
                """)
            else:
                b.setStyleSheet("""
                    QPushButton {background:#3a3a3a; border:1px solid #555; border-radius:21px;}
                    QPushButton:hover {background:#4a4a4a; border:1px solid #4ecdc4;}
                """)
            return b

        self.edit_btn = btn("styles/Icon/edit.png", "Edit Step")
        self.delete_btn = btn("styles/Icon/delete.png", "Delete Step")
        self.insert_btn = btn("styles/Icon/add_step.png", "Insert Step After", accent=True)
        self.save_btn = btn("styles/Icon/tick.png", "Save", accent=True)
        self.cancel_btn = btn("styles/Icon/close.png", "Cancel")

        self.edit_btn.clicked.connect(self.toggle_edit)
        self.delete_btn.clicked.connect(self.delete_step)
        self.insert_btn.clicked.connect(lambda: self.insert_requested.emit(self.original_idx))
        self.save_btn.clicked.connect(self.save_edit)
        self.cancel_btn.clicked.connect(self.cancel_edit)

        self.save_btn.setVisible(False)
        self.cancel_btn.setVisible(False)

        # Button layout (vertical stack on the right)
        btn_layout = QVBoxLayout()
        btn_layout.setSpacing(12)
        btn_layout.addWidget(self.edit_btn)
        btn_layout.addWidget(self.delete_btn)
        btn_layout.addWidget(self.insert_btn)
        btn_layout.addWidget(self.save_btn)
        btn_layout.addWidget(self.cancel_btn)
        btn_layout.addStretch()

        main.addLayout(btn_layout)

        self.setStyleSheet("""
            StepReviewWidget {
                background:#2a2a2a; border:1px solid #404040; border-radius:14px; margin:6px 0;
            }
        """)

    def update_title(self):
        desc = self.step_data.get('step_description', 'New Step')
        self.title.setText(f"Step {self.original_idx + 1}: {desc}")

    def update_system(self):
        sys = self.step_data.get('system', 'Unknown')
        self.system.setText(f"System: {sys}")

    def update_actions(self):
        acts = self.step_data.get('actions', '').strip()
        if acts:
            lines = []
            for line in acts.split('\n'):
                line = line.strip()
                if line:
                    bullet = line[0] if line.startswith(('•', '>', '→', '-', '*')) else '•'
                    text = line[1:].strip() if bullet != '•' else line
                    lines.append(f"{bullet} {text}")
            self.actions.setText("\n".join(lines))
        else:
            self.actions.setText("No actions")

    def update_image(self, path=None):
        if path is None:
            path = self.step_data.get('frame_path', '')
        if path and os.path.exists(path):
            pix = QPixmap(path).scaled(340, 260, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            self.thumb.setPixmap(pix)
        else:
            self.thumb.setText("No Image\nDrag to swap\nCtrl+Drag to copy")
            self.thumb.setStyleSheet(self.thumb.styleSheet() + "color:#888; font-size:12px;")

    def refresh_display(self):
        self.update_title()
        self.update_system()
        self.update_actions()

    def format_editor_text(self):
        return f"""STEP DESCRIPTION:
{self.step_data.get('step_description', '')}

SYSTEM:
{self.step_data.get('system', '')}

ACTIONS:
{self.step_data.get('actions', '').strip()}
""".strip()

    def toggle_edit(self):
        self.editor.setPlainText(self.format_editor_text())
        self.editor.show()
        self.title.hide()
        self.system.hide()
        self.actions.hide()
        self.edit_btn.hide()
        self.delete_btn.hide()
        self.insert_btn.hide()
        self.save_btn.show()
        self.cancel_btn.show()

    def cancel_edit(self):
        self.editor.hide()
        self.title.show()
        self.system.show()
        self.actions.show()
        self.edit_btn.show()
        self.delete_btn.show()
        self.insert_btn.show()
        self.save_btn.hide()
        self.cancel_btn.hide()

    def save_edit(self):
        text = self.editor.toPlainText().strip()
        if not text:
            QMessageBox.warning(self, "Error", "Step cannot be empty")
            return

        desc = system = actions = ""
        section = None
        for line in text.split('\n'):
            l = line.strip()
            if l.upper().startswith("STEP DESCRIPTION:"):
                section = "desc"
                desc += l.split(":", 1)[1].strip() + " "
            elif l.upper().startswith("SYSTEM:"):
                section = "system"
                system = l.split(":", 1)[1].strip()
            elif l.upper().startswith("ACTIONS:"):
                section = "actions"
            elif l and section == "desc":
                desc += l + " "
            elif section == "actions" and l:
                if not l.startswith(('•', '>', '→')):
                    l = '• ' + l
                actions += l + "\n"

        desc = desc.strip()
        if not desc:
            QMessageBox.warning(self, "Error", "Step description is required!")
            return

        self.step_data.update({
            'step_description': desc,
            'system': system,
            'actions': actions.strip()
        })

        self.refresh_display()
        self.step_changed.emit(self.original_idx, self.step_data)
        self.cancel_edit()

    def delete_step(self):
        if QMessageBox.question(self, "Delete", f"Delete Step {self.original_idx + 1}?",
                                QMessageBox.Yes | QMessageBox.No) == QMessageBox.Yes:
            self.delete_requested.emit(self.original_idx)


class StepReviewDialog(QDialog):
    steps_updated = pyqtSignal(list)
   
    def __init__(self, analyzer, pdd_analyses, video_path, output_dir, parent=None):
        print("🔧 Initializing StepReviewDialog...")
        super().__init__(None)
       
        # Window flags with maximize capability
        self.setWindowFlags(
            Qt.Window |
            Qt.FramelessWindowHint |
            Qt.WindowTitleHint |
            Qt.WindowMinMaxButtonsHint |
            Qt.WindowCloseButtonHint |
            Qt.WindowStaysOnTopHint
        )
       
        self.setAttribute(Qt.WA_DeleteOnClose, False)
        self.setAttribute(Qt.WA_ShowWithoutActivating, False)
       
        # Enable dragging
        self.draggable = True
        self.mouse_pressed = False
        self.mouse_position = None
        self.is_maximized = False
        self.normal_geometry = None
       
        self.analyzer = analyzer
        self.steps = [dict(s) for s in pdd_analyses]
        self.video_path = video_path
        self.output_dir = output_dir
       
        # Thread management
        self.operation_threads = []
       
        # Workflow diagram storage
        self.current_workflow_diagram = None
       
        print(f"📊 Dialog initialized with {len(self.steps)} steps")
       
        try:
            self.init_ui()
            print("✅ Dialog UI created successfully")
           
           
        except Exception as e:
            print(f"❌ Error creating dialog UI: {e}")
            import traceback
            traceback.print_exc()
            raise
   
    def init_ui(self):
        """Setup UI with Detail Mode styling"""
        self.setFixedSize(1400, 800)
 
        self.setWindowTitle("Agent Flow")
        self.setWindowIcon(QIcon(resource_path(("styles/Icon/Header Agent.png"))))
 
        # Theme-aligned stylesheet
        self.setStyleSheet("""
            QDialog {
                background-color: #18181b;
                border: 2px solid #404040;
                border-radius: 16px;
            }
            QTabWidget::pane {
                background-color: #18181b;
                border: 1px solid #333333;
                border-radius: 8px;
                top: -1px;
            }
            QTabBar::tab {
                background-color: #2a2a2a;
                color: #e4e4e4;
                border: 1px solid #404040;
                border-bottom: none;
                border-top-left-radius: 8px;
                border-top-right-radius: 8px;
                padding: 10px 20px;
                margin-right: 4px;
                font-family: 'Segoe UI', Arial;
                font-size: 13px;
                font-weight: bold;
            }
            QTabBar::tab:selected {
                background-color: #4ecdc4;
                color: #1e1e1e;
            }
            QTabBar::tab:hover:!selected {
                background-color: #3a3a3a;
            }
            QScrollArea {
                background-color: #18181b;
                border: 1px solid #333333;
                border-radius: 8px;
            }
            QScrollBar:vertical {
                background-color: #2a2a2a;
                width: 12px;
                border-radius: 6px;
            }
            QScrollBar::handle:vertical {
                background-color: #4ecdc4;
                border-radius: 6px;
                min-height: 20px;
            }
            QScrollBar::handle:vertical:hover {
                background-color: #45b7aa;
            }
            QScrollBar:horizontal {
                background-color: #2a2a2a;
                height: 12px;
                border-radius: 6px;
            }
            QScrollBar::handle:horizontal {
                background-color: #4ecdc4;
                border-radius: 6px;
                min-width: 20px;
            }
            QScrollBar::handle:horizontal:hover {
                background-color: #45b7aa;
            }
            QWidget#scrollContent {
                background-color: #18181b;
            }
 
            QPushButton#saveBtn, QPushButton#generateBtn, QPushButton#updateFlowBtn {
                background-color: #4ecdc4;
                color: #1e1e1e;
                border: none;
                border-radius: 8px;
                padding: 12px 28px;
                font-weight: bold;
                font-size: 16px;
                min-width: 120px;
                font-family: 'Segoe UI', Arial;
            }
            QPushButton#saveBtn:hover, QPushButton#generateBtn:hover, QPushButton#updateFlowBtn:hover {
                background-color: #45b7aa;
            }
            QPushButton#saveBtn:pressed, QPushButton#generateBtn:pressed, QPushButton#updateFlowBtn:pressed {
                background-color: #3aa89d;
            }
 
            QPushButton#cancelBtn {
                background-color: #3a3a3a;
                color: #e4e4e4;
                border: 1px solid #555555;
                border-radius: 8px;
                padding: 12px 28px;
                font-weight: bold;
                font-size: 16px;
                min-width: 120px;
                font-family: 'Segoe UI', Arial;
            }
            QPushButton#cancelBtn:hover {
                background-color: #4a4a4a;
                border: 1px solid #ff6b6b;
            }
            QPushButton#cancelBtn:pressed { 
                background-color: #2a2a2a; 
            }
 
            QLabel#titleLabel {
                color: #e4e4e4;
                font-size: 20px;
                font-weight: bold;
                font-family: 'Segoe UI', Arial;
                padding: 8px 0px;
            }
           
            QLabel#noWorkflowLabel {
                color: #888888;
                font-size: 14px;
                font-family: 'Segoe UI', Arial;
                padding: 20px;
            }
 
            QWidget#titleBar {
                background-color: #2e2e2e;
                border-top-left-radius: 14px;
                border-top-right-radius: 14px;
            }
 
            QPushButton#minBtn, QPushButton#maxBtn, QPushButton#closeBtn {
                background: qlineargradient(x1:0,y1:0,x2:0,y2:1, stop:0 #3a3a3a, stop:1 #2e2e2e);
                color: #e6e6e6;
                border: 1px solid #444444;
                border-radius: 6px;
                min-width: 28px;
                min-height: 28px;
                padding: 0px;
                font-weight: bold;
                font-family: 'Segoe UI', Arial;
            }
            QPushButton#minBtn:hover, QPushButton#maxBtn:hover {
                background: qlineargradient(x1:0,y1:0,x2:0,y2:1, stop:0 #3f5350, stop:1 #344c49);
                border: 1px solid #4ecdc4;
                color: #ffffff;
            }
            QPushButton#minBtn:pressed, QPushButton#maxBtn:pressed {
                background: qlineargradient(x1:0,y1:0,x2:0,y2:1, stop:0 #2f2f2f, stop:1 #262626);
            }
 
            QPushButton#closeBtn {
                background: qlineargradient(x1:0,y1:0,x2:0,y2:1, stop:0 #4a2b2b, stop:1 #3a2121);
                color: #f2dede;
                border: 1px solid #5e2e2e;
            }
            QPushButton#closeBtn:hover {
                background: qlineargradient(x1:0,y1:0,x2:0,y2:1, stop:0 #ff6b6b, stop:1 #e95a5a);
                border: 1px solid #ff6b6b;
                color: #ffffff;
            }
            QPushButton#closeBtn:pressed {
                background: qlineargradient(x1:0,y1:0,x2:0,y2:1, stop:0 #d65a5a, stop:1 #bf4b4b);
            }
        """)
 
        # Title bar layout
        layout = QVBoxLayout(self)
        layout.setSpacing(0)
        layout.setContentsMargins(22, 18, 22, 22)
 
        # Title bar container
        title_bar = QWidget()
        title_bar.setObjectName("titleBar")
        title_layout = QHBoxLayout(title_bar)
        title_layout.setContentsMargins(8, 6, 8, 6)
        title_layout.setSpacing(12)
 
        # Icon
        icon = QLabel()
        icon.setPixmap(QIcon("styles/Icon/review.png").pixmap(28, 28))
        title_layout.addWidget(icon)
 
        # Title
        title = QLabel("")
        title.setObjectName("titleLabel")
        title_layout.addWidget(title)
        title_layout.addStretch()
 
        # Minimize Button
        self.min_btn = QPushButton("–")
        self.min_btn.setObjectName("minBtn")
        self.min_btn.setFixedSize(28, 28)
        self.min_btn.setFont(QFont("Segoe UI", 10))
        self.min_btn.setCursor(Qt.PointingHandCursor)
        self.min_btn.setFocusPolicy(Qt.NoFocus)
        self.min_btn.clicked.connect(self._force_minimize)
        title_layout.addWidget(self.min_btn)
 
        # Maximize / Restore Button
        self.max_btn = QPushButton("▢")
        self.max_btn.setObjectName("maxBtn")
        self.max_btn.setFixedSize(28, 28)
        self.max_btn.setFont(QFont("Segoe UI", 10))
        self.max_btn.setCursor(Qt.PointingHandCursor)
        self.max_btn.setFocusPolicy(Qt.NoFocus)
        self.max_btn.clicked.connect(self.toggle_maximize)
        title_layout.addWidget(self.max_btn)
 
        # Close Button
        self.close_btn = QPushButton("✕")
        self.close_btn.setObjectName("closeBtn")
        self.close_btn.setFixedSize(28, 28)
        self.close_btn.setFont(QFont("Segoe UI", 10))
        self.close_btn.setCursor(Qt.PointingHandCursor)
        self.close_btn.setFocusPolicy(Qt.NoFocus)
        self.close_btn.clicked.connect(self._force_close)
        title_layout.addWidget(self.close_btn)
 
        layout.addWidget(title_bar)
       
        # === Tab Widget ===
        self.tab_widget = QTabWidget()
       
        # ========== Tab 1: Steps Review ==========
        steps_tab = QWidget()
        steps_tab_layout = QVBoxLayout(steps_tab)
        steps_tab_layout.setContentsMargins(0, 0, 0, 0)
        steps_tab_layout.setSpacing(12)
       
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
       
        self.scroll_content = QWidget()
        self.scroll_content.setObjectName("scrollContent")
        self.steps_layout = QVBoxLayout(self.scroll_content)
        self.steps_layout.setSpacing(8)  
        self.steps_layout.addStretch()
        scroll.setWidget(self.scroll_content)
        steps_tab_layout.addWidget(scroll, stretch=1)
       
        # Bottom buttons for Steps tab
        steps_btn_layout = QHBoxLayout()
        steps_btn_layout.setSpacing(12)
        steps_btn_layout.addStretch()
       
        update_flow_btn = QPushButton("🔄 Update Flowchart")
        update_flow_btn.setObjectName("updateFlowBtn")
        update_flow_btn.clicked.connect(self.update_and_switch_to_flowchart)
        steps_btn_layout.addWidget(update_flow_btn)
       
        steps_cancel_btn = QPushButton("Cancel")
        steps_cancel_btn.setObjectName("cancelBtn")
        steps_cancel_btn.clicked.connect(self.reject)
        steps_btn_layout.addWidget(steps_cancel_btn)
       
        steps_tab_layout.addLayout(steps_btn_layout)
       
        self.tab_widget.addTab(steps_tab, "Review & Edit Process Steps")
       
        # ========== Tab 2: Workflow Diagram (INTEGRATED FLOWCHART) ==========
        workflow_tab = QWidget()
        workflow_tab_layout = QVBoxLayout(workflow_tab)
        workflow_tab_layout.setContentsMargins(0, 0, 0, 0)
        workflow_tab_layout.setSpacing(12)  # Same spacing as steps tab
       
        # Embedded flowchart editor - CRITICAL: Must be direct child without extra wrappers
        self.flowchart_editor = EmbeddedFlowchartEditor(parent=workflow_tab)
        self.flowchart_editor.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.flowchart_editor.setMinimumSize(1300, 600)  # Reduced to leave room for buttons
        
        # CRITICAL: Make sure the editor accepts mouse events
        self.flowchart_editor.setAttribute(Qt.WA_TransparentForMouseEvents, False)
        self.flowchart_editor.setMouseTracking(True)
        
        workflow_tab_layout.addWidget(self.flowchart_editor, stretch=1)
       
        # Bottom buttons for Workflow tab - SAME STYLE AS STEPS TAB
        workflow_btn_layout = QHBoxLayout()
        workflow_btn_layout.setSpacing(12)
        workflow_btn_layout.addStretch()
       
        save_btn = QPushButton("💾 Save & Generate PNG")
        save_btn.setObjectName("saveBtn")
        save_btn.clicked.connect(self.save_flowchart_and_generate_png)
        workflow_btn_layout.addWidget(save_btn)
       
        workflow_cancel_btn = QPushButton("Cancel")
        workflow_cancel_btn.setObjectName("cancelBtn")
        workflow_cancel_btn.clicked.connect(self.reject)
        workflow_btn_layout.addWidget(workflow_cancel_btn)
       
        workflow_tab_layout.addLayout(workflow_btn_layout)
               
        self.tab_widget.addTab(workflow_tab, "Process FlowDiagram")
       
        layout.addWidget(self.tab_widget, stretch=1)
       
        # Progress bar (shared across tabs)
        self.progress = QProgressBar()
        self.progress.setVisible(False)
        self.progress.setTextVisible(True)
        self.progress.setFormat("Processing... %p%")
        self.progress.setStyleSheet("""
            QProgressBar {
                background-color: #2a2a2a;
                border: 1px solid #404040;
                border-radius: 8px;
                text-align: center;
                color: #e4e4e4;
                font-family: 'Segoe UI', Arial;
            }
            QProgressBar::chunk {
                background-color: #4ecdc4;
                border-radius: 8px;
            }
        """)
        layout.addWidget(self.progress)
       
        # Add shadow effect
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(20)
        shadow.setXOffset(0)
        shadow.setYOffset(5)
        shadow.setColor(QColor(0, 0, 0, 100))
        self.setGraphicsEffect(shadow)
       
        # Load steps
        print("📥 Loading step widgets...")
        self.load_steps()
        print(f"✅ Loaded {len(self.step_widgets)} step widgets")

    def generate_detailed_workflow_from_cleaned_steps(self, retry_count=0, max_retries=3):
        """
        Generate detailed workflow diagram JSON with MULTI-COLUMN LAYOUT
        Updated with larger text size (25px) and wider rectangles
        """
        print(f"🔄 Generating multi-column workflow diagram from cleaned steps... (Attempt {retry_count + 1}/{max_retries})")
        
        if not hasattr(self, 'steps') or not self.steps:
            print("⚠️ No steps available for workflow generation")
            return None
        
        # Build detailed step descriptions for prompt
        workflow_text = self._build_workflow_text_from_steps(self.steps)
        
        prompt = f"""
            You are a workflow diagram expert. Generate a detailed flowchart JSON with MULTI-COLUMN LAYOUT and PERFECT ARROW ALIGNMENT.

            **CRITICAL LAYOUT REQUIREMENTS:**

            1. **MULTI-COLUMN LAYOUT:**
            - Main flow starts at LEFT side (Column 1): x = 250.0
            - After 5-6 nodes, continue flow in NEXT COLUMN to the right
            - Column 2: x = 700.0 (continue downward from top)
            - Column 3: x = 1150.0 (if needed)
            - Column 4: x = 1600.0 (if needed)
            - Each column flows TOP TO BOTTOM before moving right
            - Vertical spacing within column: 140px between nodes
            - Reset y position to 50 when moving to next column

            2. **STANDARD NODE DIMENSIONS (CRITICAL FOR ARROW CALCULATIONS):**
            - width: 400px (EXTRA WIDE boxes for better readability)
            - height: 100px (TALLER boxes for 30px bold font)
            - font_size: 30px (LARGER BOLD text for clarity)
            - font_weight: "bold" (BOLD text for emphasis)
            - These dimensions are used to calculate arrow entry/exit points

            3. **POSITIONING PATTERN:**
            ```
            Column 1 (x=250):     Column 2 (x=700):     Column 3 (x=1150):
            - Node 1 (y=50)       - Node 7 (y=50)       - Node 13 (y=50)
            - Node 2 (y=190)      - Node 8 (y=190)      - Node 14 (y=190)
            - Node 3 (y=330)      - Node 9 (y=330)      - Node 15 (y=330)
            - Node 4 (y=470)      - Node 10 (y=470)     - Node 16 (y=470)
            - Node 5 (y=610)      - Node 11 (y=610)     - Node 17 (y=610)
            - Node 6 (y=750)      - Node 12 (y=750)     - Node 18 (y=750)
            ```

            4. **Node Types (use correct type numbers):**
            - type 0: Process (rectangle) - **DEFAULT for ALL regular steps**
            - type 3: Decision (diamond) - ONLY for YES/NO questions, IF conditions
            - type 4: Input/Output (parallelogram) - for data entry/extraction
            - type 5: Start/End (stadium shape) - ONLY for "Start Process" and "End Process"
            - type 1: Rounded rectangle - for sub-processes or grouped actions

            5. **ARROW ALIGNMENT - EDGE CALCULATION FORMULAS:**

            **Node Edge Coordinates (width=400, height=100):**
            - **Top edge**: y_top = node.y - 50
            - **Bottom edge**: y_bottom = node.y + 50
            - **Left edge**: x_left = node.x - 200
            - **Right edge**: x_right = node.x + 200
            - **Center**: x_center = node.x, y_center = node.y

            **Entry/Exit Point Rules:**
            - Arrows entering from TOP: use y_top (y - 50)
            - Arrows exiting from BOTTOM: use y_bottom (y + 50)
            - Arrows entering from LEFT: use x_left (x - 200)
            - Arrows exiting from RIGHT: use x_right (x + 200)

            6. **ARROW ROUTING PATTERNS WITH PROPER EDGE ALIGNMENT:**

            **A. Within Same Column (straight down):**
            - No waypoints needed
            - Arrow automatically connects bottom of source to top of target
            - Example: {{"start_id": 0, "end_id": 1}}

            **B. Column Transition (last node of column to first node of next column):**
            Pattern: EXIT BOTTOM → MOVE RIGHT → MOVE UP → ENTER TOP

            Example: Node 5 (x=250, y=750) to Node 6 (x=700, y=50)
            ```json
            {{
            "start_id": 5,
            "end_id": 6,
            "waypoints": [
                {{"x": 250.0, "y": 800.0}},  // Exit bottom: y + 50
                {{"x": 475.0, "y": 800.0}},  // Move right to midpoint between columns
                {{"x": 475.0, "y": 0.0}},   // Move up above all nodes (y_top - 50)
                {{"x": 700.0, "y": 0.0}}    // Enter top: target y - 50
            ]
            }}
            ```

            **C. Decision Branch - YES Path (straight down):**
            - Usually continues in same column
            - No waypoints needed
            - Example: {{"start_id": 7, "end_id": 8, "label": "YES"}}

            **D. Decision Branch - NO Path (horizontal bypass to different column):**
            Pattern: EXIT RIGHT → MOVE RIGHT → ALIGN VERTICALLY → ENTER LEFT

            Example: Decision at (x=700, y=470) bypassing to node at (x=1150, y=50)
            ```json
            {{
            "start_id": 9,
            "end_id": 12,
            "label": "NO",
            "waypoints": [
                {{"x": 900.0, "y": 470.0}},  // Exit right: x + 200
                {{"x": 950.0, "y": 470.0}},  // Move right beyond current column
                {{"x": 950.0, "y": 50.0}},   // Align with target node y
                {{"x": 950.0, "y": 50.0}}    // Enter left: target x - 200
            ]
            }}
            ```

            7. **JSON Structure (EXACT format required):**
            ```json
            {{
            "nodes": [
                {{"id": 0, "type": 5, "text": "Start Process", "x": 250.0, "y": 50.0, "width": 400, "height": 100, "font_size": 30, "font_weight": "bold", "border": "#757575", "fill": "#F5F5F5"}},
                {{"id": 1, "type": 0, "text": "Return to Report Center tab", "x": 250.0, "y": 190.0, "width": 400, "height": 100, "font_size": 30, "font_weight": "bold", "border": "#4A90E2", "fill": "#E3F2FD"}},
                {{"id": 2, "type": 0, "text": "Identify check line item using Transaction #", "x": 250.0, "y": 330.0, "width": 400, "height": 100, "font_size": 30, "font_weight": "bold", "border": "#4A90E2", "fill": "#E3F2FD"}},
                {{"id": 3, "type": 0, "text": "Click XLSX next to Payroll Report", "x": 250.0, "y": 470.0, "width": 400, "height": 100, "font_size": 30, "font_weight": "bold", "border": "#4A90E2", "fill": "#E3F2FD"}},
                {{"id": 4, "type": 0, "text": "Download Excel file", "x": 250.0, "y": 610.0, "width": 400, "height": 100, "font_size": 30, "font_weight": "bold", "border": "#4A90E2", "fill": "#E3F2FD"}},
                {{"id": 5, "type": 5, "text": "End Process", "x": 250.0, "y": 750.0, "width": 400, "height": 100, "font_size": 30, "font_weight": "bold", "border": "#757575", "fill": "#F5F5F5"}}
            ],
            "arrows": [
                {{"start_id": 0, "end_id": 1}},
                {{"start_id": 1, "end_id": 2}},
                {{"start_id": 2, "end_id": 3}},
                {{"start_id": 3, "end_id": 4}},
                {{"start_id": 4, "end_id": 5}}
            ]
            }}
            ```

            8. **Color Coding by System/Application:**
            Add "border" and "fill" properties to each node:
            - Modmed/EMR Portal nodes: "border": "#4A90E2", "fill": "#E3F2FD" (blue)
            - Weave Portal nodes: "border": "#9C27B0", "fill": "#F3E5F5" (purple)
            - Tasking/Report nodes: "border": "#FF9800", "fill": "#FFF3E0" (orange)
            - Outlook/Email nodes: "border": "#4CAF50", "fill": "#E8F5E9" (green)
            - Generic/Other nodes: "border": "#607D8B", "fill": "#ECEFF1" (gray-blue)
            - Start/End nodes: "border": "#757575", "fill": "#F5F5F5" (gray)

            9. **Text Formatting:**
            - Keep text concise but readable with 30px BOLD font
            - Maximum 50 characters per line (boxes are much wider now)
            - Decision nodes: end with "?" (e.g., "Patient Found?", "Need Further Reporting?")
            - Remove special characters: - _ * : ; , . " '
            - Action verbs: Extract, Validate, Create, Update, Navigate, Click, Enter, Select

            10. **Arrow Label Formatting:**
            - Decision branches: "label": "YES" or "label": "NO"
            - Skip/bypass paths: "label": "SKIP" or omit label
            - Normal flow: omit label property
            - Format: {{"start_id": X, "end_id": Y, "label": "YES", "waypoints": [...]}}

            **Process Steps to Convert:**
            {workflow_text}

            **CRITICAL CHECKLIST BEFORE GENERATING:**
            ✓ All nodes have width=400, height=100, font_size=30, font_weight="bold"
            ✓ Default type is 0 (rectangle) for all regular process steps
            ✓ Nodes positioned in columns (x: 250, 700, 1150, 1600)
            ✓ Vertical spacing: 140px between nodes (y: 50, 190, 330, 470, 610, 750)
            ✓ Column transitions use waypoints with CORRECT edge calculations
            ✓ Exit bottom: node.y + 50
            ✓ Enter top: node.y - 50
            ✓ Exit right: node.x + 200
            ✓ Enter left: node.x - 200
            ✓ Decision NO branches route horizontally with proper waypoints
            ✓ All routing lines are orthogonal (horizontal/vertical only)
            ✓ Waypoints route AROUND nodes, never through them
            ✓ Color coding matches system/application
            ✓ Decision nodes marked with type 3 and end in "?"
            ✓ NO comments in JSON (no // or /* */)

            **OUTPUT FORMAT:**
            Return ONLY the JSON object starting with {{ and ending with }}. No markdown, no explanation, no comments, no extra text.
            """

        try:
            print(f"📤 Sending request to Gemini API... (Attempt {retry_count + 1}/{max_retries})")
            
            # Generate workflow JSON using Gemini
            response = self.analyzer.flowchart_model.generate_content(prompt)
            json_text = response.text.strip()
            
            print(f"📥 Received response from API (length: {len(json_text)} chars)")
            
            # Extract JSON from markdown if present
            import re
            match = re.search(r'```json\s*(.*?)```', json_text, re.DOTALL) or \
                    re.search(r'```\s*(.*?)```', json_text, re.DOTALL)
            if match:
                json_text = match.group(1).strip()
                print("✂️ Extracted JSON from markdown code block")
            
            # Remove any JSON comments
            print("🧹 Cleaning JSON comments...")
            json_text = re.sub(r'//.*?(?=\n|$)', '', json_text)
            json_text = re.sub(r'/\*.*?\*/', '', json_text, flags=re.DOTALL)
            
            print("🔍 Attempting to parse JSON...")
            # Parse and validate JSON
            workflow_json = json.loads(json_text)
            
            if "nodes" not in workflow_json or "arrows" not in workflow_json:
                raise ValueError("Invalid JSON structure: missing nodes or arrows")
            
            print(f"✅ JSON parsed successfully! Nodes: {len(workflow_json['nodes'])}, Arrows: {len(workflow_json['arrows'])}")
            
            # Post-process: ensure multi-column layout with new dimensions
            print("🔧 Enforcing multi-column layout...")
            workflow_json = self._ensure_multicolumn_layout_large(workflow_json)
            
            # Save JSON file 
            workflow_dir = os.path.abspath("workflow")
            os.makedirs(workflow_dir, exist_ok=True)
            json_file_path = os.path.join(workflow_dir, "workflow.json")

            print(f"💾 Saving workflow JSON to: {json_file_path}")
            with open(json_file_path, "w", encoding='utf-8') as f:
                json.dump(workflow_json, f, indent=4)
            print(f"✅ JSON file saved: {json_file_path}")

            # Generate Draw.io diagram AFTER JSON exists
            self.generate_drawio_from_workflow(json_file_path)
            print(f"✅ Draw.io diagram generation attempted")            
            
            print(f"   Total Nodes: {len(workflow_json['nodes'])}")
            print(f"   Decision Nodes: {sum(1 for n in workflow_json['nodes'] if n['type'] == 3)}")
            print(f"   Arrows: {len(workflow_json['arrows'])}")
            
            # Load into flowchart editor
            if hasattr(self, 'flowchart_editor'):
                print("🔄 Loading workflow into flowchart editor...")
                self.flowchart_editor.json_path = json_file_path
                self.flowchart_editor.load_flowchart_from_path()
                print("✅ Workflow loaded into flowchart editor")
                
                self.flowchart_editor.setVisible(True)
                self.flowchart_editor.setEnabled(True)
                self.flowchart_editor.raise_()
                self.flowchart_editor.activateWindow()
            
            return json_file_path
            
        except json.JSONDecodeError as e:
            print(f"❌ JSON parsing error (Attempt {retry_count + 1}/{max_retries}): {e}")
            
            if retry_count < max_retries - 1:
                print(f"🔄 Retrying workflow generation in 2 seconds...")
                import time
                time.sleep(2)
                return self.generate_detailed_workflow_from_cleaned_steps(retry_count + 1, max_retries)
            else:
                QMessageBox.warning(
                    self, 
                    "Generation Error", 
                    f"Failed to parse workflow JSON after {max_retries} attempts.\n\nError: {e}\n\nPlease try again."
                )
                return None
                
        except Exception as e:
            print(f"❌ Error generating workflow (Attempt {retry_count + 1}/{max_retries}): {e}")
            import traceback
            traceback.print_exc()
            
            if retry_count < max_retries - 1:
                print(f"🔄 Retrying workflow generation in 2 seconds...")
                import time
                time.sleep(2)
                return self.generate_detailed_workflow_from_cleaned_steps(retry_count + 1, max_retries)
            else:
                QMessageBox.warning(
                    self, 
                    "Generation Error", 
                    f"Failed to generate workflow after {max_retries} attempts.\n\nError: {e}\n\nPlease try again."
                )
                return None


    def _ensure_multicolumn_layout_large(self, workflow_json):
        """
        Post-process workflow to ensure multi-column layout with EXTRA WIDE dimensions
        width: 400px, height: 90px, font_size: 25px
        """
        nodes = workflow_json.get("nodes", [])
        
        if len(nodes) <= 6:
            # Small workflow - single column is fine
            for node in nodes:
                node["width"] = 400
                node["height"] = 90
                node["font_size"] = 25
            return workflow_json
        
        print(f"🔧 Enforcing multi-column layout with extra wide dimensions for {len(nodes)} nodes...")
        
        # Configuration for EXTRA WIDE boxes
        NODES_PER_COLUMN = 6
        COLUMN_WIDTH = 500 # Much wider spacing for extra wide boxes
        BASE_X = 250.0
        BASE_Y = 50.0
        Y_SPACING = 140.0  # More vertical space
        
        # Sort nodes by ID to maintain order
        sorted_nodes = sorted(nodes, key=lambda n: n.get("id", 0))
        
        # Redistribute nodes into columns
        for idx, node in enumerate(sorted_nodes):
            column = idx // NODES_PER_COLUMN
            row = idx % NODES_PER_COLUMN
            
            node["x"] = float(BASE_X + (column * COLUMN_WIDTH))
            node["y"] = float(BASE_Y + (row * Y_SPACING))
            
            # Ensure proper data types and EXTRA WIDE dimensions
            node["id"] = int(node["id"])
            node["type"] = int(node.get("type", 0))  # Default to rectangle
            node["width"] = 420  # EXTRA WIDE
            node["height"] = 100 # TALLER
            node["font_size"] = 13  # LARGER TEXT
            node["font_weight"] = "bold"
            
            # Clean text
            import re
            node["text"] = re.sub(r'[-_*:;,."\'$]', '', str(node["text"]))[:50]
        
        workflow_json["nodes"] = sorted_nodes
        
        print(f"✅ Layout enforced: {len(sorted_nodes)} nodes in {(len(sorted_nodes) + NODES_PER_COLUMN - 1) // NODES_PER_COLUMN} columns")
        print(f"   Node dimensions: 400x90px, Font: 25px")
        
        return workflow_json
    
    
    def generate_drawio_from_workflow(self, json_path):
        """
        Convert workflow.json into workflow/workflow.drawio
        """
        try:
            # Verify JSON file exists
            if not os.path.exists(json_path):
                print(f"❌ JSON file not found: {json_path}")
                return False
            
            from json_to_drawio import convert_json_to_drawio
            
            # Output path should be in same directory as JSON
            output_dir = os.path.dirname(json_path)
            output_path = os.path.join(output_dir, "workflow.drawio")

            print(f"🔄 Converting JSON to Draw.io: {json_path} → {output_path}")
            convert_json_to_drawio(
                json_path=json_path,
                output_path=output_path
            )

            print(f"✅ draw.io flowchart generated: {output_path}")
            return True

        except Exception as e:
            print(f"❌ Failed to generate draw.io file: {e}")
            import traceback
            traceback.print_exc()
            return False

    def _ensure_multicolumn_layout(self, workflow_json):
        """
        Post-process workflow to ensure multi-column layout
        Redistributes nodes horizontally after every 5-6 nodes
        """
        nodes = workflow_json.get("nodes", [])
        
        if len(nodes) <= 6:
            # Small workflow - single column is fine
            return workflow_json
        
        print(f"🔧 Enforcing multi-column layout for {len(nodes)} nodes...")
        
        # Configuration
        NODES_PER_COLUMN = 6
        COLUMN_WIDTH = 300  # Horizontal spacing between columns
        BASE_X = 150.0
        BASE_Y = 50.0
        Y_SPACING = 120.0
        
        # Sort nodes by ID to maintain order
        sorted_nodes = sorted(nodes, key=lambda n: n.get("id", 0))
        
        # Redistribute nodes into columns
        for idx, node in enumerate(sorted_nodes):
            column = idx // NODES_PER_COLUMN
            row = idx % NODES_PER_COLUMN
            
            node["x"] = float(BASE_X + (column * COLUMN_WIDTH))
            node["y"] = float(BASE_Y + (row * Y_SPACING))
            
            # Ensure proper data types
            node["id"] = int(node["id"])
            node["type"] = int(node.get("type", 0))
            node["width"] = int(node.get("width", 140))
            node["height"] = int(node.get("height", 60))
            
            # Clean text
            import re
            node["text"] = re.sub(r'[-_*:;,."\'$$]', '', str(node["text"]))[:30]
        
        workflow_json["nodes"] = sorted_nodes
        
        print(f"✅ Layout enforced: {len(sorted_nodes)} nodes in {(len(sorted_nodes) + NODES_PER_COLUMN - 1) // NODES_PER_COLUMN} columns")
        
        return workflow_json
    
    
    def _build_workflow_text_from_steps(self, steps):
        """
        Build detailed text description from cleaned steps
        Highlights conditional logic for workflow generation
        """
        workflow_lines = []
        
        for idx, step in enumerate(steps, 1):
            step_title = step.get('step_title', f'Step {idx}')
            system = step.get('system', 'System')
            actions = step.get('action_list', [])
            
            # Main step header
            workflow_lines.append(f"\n--- STEP {idx}: {step_title} ---")
            workflow_lines.append(f"System/Application: {system}")
            
            # Action details with conditional logic markers
            if actions:
                workflow_lines.append("Actions:")
                for action in actions:
                    action_clean = action.strip().lstrip('•➢ ')
                    
                    # Highlight conditional logic
                    if any(keyword in action_clean.upper() for keyword in 
                        ['IF', 'ELSE', 'THEN', 'CHECK', 'VERIFY', 'VALIDATE', 'YES', 'NO']):
                        workflow_lines.append(f"  [CONDITIONAL] {action_clean}")
                    else:
                        workflow_lines.append(f"  {action_clean}")
            else:
                workflow_lines.append("  No actions specified")
        
        return "\n".join(workflow_lines)


    def _validate_and_normalize_workflow(self, workflow_json):
        """
        Validate and normalize workflow JSON structure
        Ensures proper data types and positioning
        """
        nodes = workflow_json.get("nodes", [])
        arrows = workflow_json.get("arrows", [])
        
        # Validate nodes
        valid_nodes = []
        node_ids = set()
        
        for node in nodes:
            # Ensure required fields exist
            if "id" not in node or "type" not in node or "text" not in node:
                print(f"⚠️ Skipping invalid node: {node}")
                continue
            
            # Normalize node data
            node["id"] = int(node["id"])
            node["type"] = int(node.get("type", 0))
            node["x"] = float(node.get("x", 280.0))
            node["y"] = float(node.get("y", 0.0))
            node["width"] = int(node.get("width", 160))
            node["height"] = int(node.get("height", 70))
            
            # Clean text
            import re
            node["text"] = re.sub(r'[-_*:;,."\'$$]', '', str(node["text"]))[:35]
            
            node_ids.add(node["id"])
            valid_nodes.append(node)
        
        # Validate arrows (only keep arrows with valid node references)
        valid_arrows = []
        for arrow in arrows:
            start_id = arrow.get("start_id")
            end_id = arrow.get("end_id")
            
            if start_id in node_ids and end_id in node_ids:
                # Normalize arrow data
                arrow["start_id"] = int(start_id)
                arrow["end_id"] = int(end_id)
                
                # Keep label if exists
                if "label" in arrow:
                    arrow["label"] = str(arrow["label"])
                
                valid_arrows.append(arrow)
            else:
                print(f"⚠️ Skipping invalid arrow: {start_id} → {end_id}")
        
        workflow_json["nodes"] = valid_nodes
        workflow_json["arrows"] = valid_arrows
        
        print(f"✅ Validation complete: {len(valid_nodes)} nodes, {len(valid_arrows)} arrows")
        
        return workflow_json
 
    def generate_workflow_diagram(self):
        """
        NEW: Generate detailed workflow from cleaned steps instead of grouped functionalities
        """
        print("🔄 Generating detailed workflow diagram from cleaned steps...")
        
        # Use the new detailed workflow generator
        json_path = self.generate_detailed_workflow_from_cleaned_steps()
        
        if json_path:
            print(f"✅ Detailed workflow generated successfully")
        else:
            print("❌ Workflow generation failed")


    # UPDATED: Switch to flowchart tab method
    def update_and_switch_to_flowchart(self):
        """Update flowchart and switch to workflow diagram tab"""
        print("🔄 Updating flowchart and switching tabs...")
        
        # Show progress dialog
        self.progress_dialog = QProgressDialog("Generating workflow diagram...", "Cancel", 0, 0, self)
        self.progress_dialog.setWindowTitle("Processing")
        self.progress_dialog.setWindowModality(Qt.WindowModal)
        self.progress_dialog.setMinimumDuration(0)
        self.progress_dialog.setWindowFlags(Qt.Dialog | Qt.WindowMinimizeButtonHint | Qt.WindowCloseButtonHint)
        self.progress_dialog.setCancelButtonText("Cancel")
        self.progress_dialog.setRange(0, 0)  # Indeterminate - keeps animating
        self.progress_dialog.show()
        
        # Switch to workflow tab first
        self.tab_widget.setCurrentIndex(1)
        QApplication.processEvents()
        
        # Create and start worker thread
        self.flowchart_worker = FlowchartWorker(self)
        self.flowchart_worker.finished.connect(self.on_flowchart_complete)
        self.flowchart_worker.error.connect(self.on_flowchart_error)
        self.flowchart_worker.start()

    def on_flowchart_complete(self):
        """Called when flowchart generation is complete"""
        try:
            # Close progress dialog
            self.progress_dialog.close()
            
            # Force the flowchart editor to reload
            workflow_dir = os.path.abspath("workflow")
            json_file_path = os.path.join(workflow_dir, "workflow.json")
            
            if os.path.exists(json_file_path):
                # Reload the flowchart editor with the new JSON
                self.flowchart_editor.json_path = json_file_path
                self.flowchart_editor.load_flowchart_from_path()
                
                # Force a repaint
                self.flowchart_editor.update()
                self.flowchart_editor.repaint()
                QApplication.processEvents()
                
                print("✅ Flowchart generation complete and loaded!")
            else:
                print("⚠️ Workflow JSON not found after generation")
                QMessageBox.warning(self, "Warning", "Flowchart generated but file not found.")
                
        except Exception as e:
            print(f"❌ Error in flowchart completion: {e}")
            import traceback
            traceback.print_exc()

    def on_flowchart_error(self, error_msg):
        """Called when flowchart generation fails"""
        self.progress_dialog.close()
        QMessageBox.critical(self, "Generation Error", f"Failed to generate flowchart:\n{error_msg}")
        print(f"❌ Flowchart generation error: {error_msg}")


    def _normalize_workflow_positions(self, workflow_json):
        """Ensure nodes have proper sequential positioning"""
        nodes = workflow_json.get("nodes", [])
        
        # Sort by existing y position or id
        nodes_sorted = sorted(nodes, key=lambda n: (n.get("y", 0), n.get("id", 0)))
        
        base_x = 280.0
        base_y = 50.0
        y_spacing = 150.0
        
        for i, node in enumerate(nodes_sorted):
            # Set defaults if missing
            if "x" not in node:
                node["x"] = base_x
            if "y" not in node:
                node["y"] = base_y + (i * y_spacing)
            if "width" not in node:
                node["width"] = 160
            if "height" not in node:
                node["height"] = 70
            
            # Ensure proper types
            node["x"] = float(node["x"])
            node["y"] = float(node["y"])
            node["id"] = int(node["id"])
            node["type"] = int(node.get("type", 0))
            node["width"] = int(node["width"])
            node["height"] = int(node["height"])
            
            # Clean text - remove special characters
            if "text" in node:
                import re
                node["text"] = re.sub(r'[-_*:;,."\'$$$$]', '', str(node["text"]))[:25]
        
        workflow_json["nodes"] = nodes_sorted
        return workflow_json


    def save_flowchart_and_generate_png(self):
        """Save flowchart JSON + PNG → then CONTINUE with document generation"""
        workflow_dir = os.path.abspath("workflow")
        os.makedirs(workflow_dir, exist_ok=True)
        
        json_file_path = os.path.join(workflow_dir, "workflow.json")
        png_file_path = os.path.join(workflow_dir, "workflow_diagram.png")

        # Step 1: Save JSON
        if not self.flowchart_editor.save_flowchart_to_json(json_file_path):
            QMessageBox.critical(self, "Save Failed", "Could not save flowchart JSON.")
            return

        # Step 2: Export PNG
        if not self.flowchart_editor.export_to_png(png_file_path):
            QMessageBox.critical(self, "Export Failed", "Could not export PNG image.")
            return

        # SUCCESS → Show confirmation + CONTINUE to document generation
        reply = QMessageBox.information(
            self,
            "Flowchart Successfully Saved!",
            "Flowchart saved successfully. Continue with document generation?",
            QMessageBox.Ok
        )

        print(f"Flowchart saved & PNG exported → proceeding with document generation")

        # CRITICAL: Continue the original process (emit updated steps + accept dialog)
        self.save_and_regenerate()   # This triggers document generation
    def cleanup_threads(self):
        """Clean up threads on close"""
        print("🔒 Cleaning up threads...")
        
        # Clean up flowchart worker
        if hasattr(self, 'flowchart_worker') and self.flowchart_worker.isRunning():
            self.flowchart_worker.terminate()
            self.flowchart_worker.wait()
        
        for thread in self.operation_threads:
            if thread.isRunning():
                thread.terminate()
                thread.wait()
        
        print("✅ Threads cleaned up")

    def mousePressEvent(self, event):
        # Only handle mouse events on the title bar, not the whole dialog
        if hasattr(self, 'title_bar'):
            title_bar_geometry = self.title_bar.geometry()
            if not title_bar_geometry.contains(event.pos()):
                event.ignore()
                return
        
        if event.button() == Qt.LeftButton and self.draggable:
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
 
    def _force_minimize(self):
        """Minimize with Detail Mode behavior"""
        try:
            print("🔽 Forcing minimize...")
            self.setWindowState(Qt.WindowMinimized)
            if hasattr(self, 'windowHandle') and self.windowHandle():
                self.windowHandle().setWindowState(Qt.WindowMinimized)
        except Exception as e:
            print(f"Error in minimize: {e}")
            self.hide()
 
    def toggle_maximize(self):
        try:
            if not self.is_maximized:
                try:
                    self.normal_geometry = self.geometry()
                except Exception:
                    self.normal_geometry = None
 
                print("🗖 Forcing maximize...")
                self.showMaximized()
                if hasattr(self, 'windowHandle') and self.windowHandle():
                    self.windowHandle().setWindowState(Qt.WindowMaximized)
 
                self.is_maximized = True
                try:
                    self.max_btn.setText("❐")
                except Exception:
                    pass
            else:
                print("🗖 Restoring from maximize...")
                if self.normal_geometry:
                    self.showNormal()
                    self.setGeometry(self.normal_geometry)
                else:
                    self.showNormal()
                if hasattr(self, 'windowHandle') and self.windowHandle():
                    self.windowHandle().setWindowState(Qt.WindowNoState)
 
                self.is_maximized = False
                try:
                    self.max_btn.setText("▢")
                except Exception:
                    pass
        except Exception as e:
            print(f"Error in maximize toggle: {e}")
            try:
                self.showNormal()
            except Exception:
                self.hide()
 
    def _force_close(self):
        """Close with Detail Mode behavior"""
        try:
            print("❌ Force closing...")
            self.cleanup_threads()
            self.setParent(None)
            self.close()
        except Exception as e:
            print(f"Error in close: {e}")
            self.cleanup_threads()
            self.hide()

    def load_steps(self):
        for i in reversed(range(self.steps_layout.count())):
            w = self.steps_layout.itemAt(i).widget()
            if w:
                w.setParent(None)
        self.step_widgets = []
        for idx, step in enumerate(self.steps):
            widget = StepReviewWidget(step, idx)
            widget.step_changed.connect(self.on_step_changed)
            widget.insert_requested.connect(self.insert_step_after)
            widget.delete_requested.connect(self.delete_step)
            widget.image_swap_requested.connect(self.swap_images)
            widget.image_copy_requested.connect(self.copy_image)
            self.steps_layout.insertWidget(self.steps_layout.count() - 1, widget)
            self.step_widgets.append(widget)
   
    def swap_images(self, from_idx, to_idx):
        """Swap images between two steps"""
        if from_idx >= len(self.steps) or to_idx >= len(self.steps):
            return
       
        # Swap frame paths in step data
        from_path = self.steps[from_idx].get('frame_path', '')
        to_path = self.steps[to_idx].get('frame_path', '')
       
        self.steps[from_idx]['frame_path'] = to_path
        self.steps[to_idx]['frame_path'] = from_path
       
        # Update the visual thumbnails
        self.step_widgets[from_idx].step_data['frame_path'] = to_path
        self.step_widgets[to_idx].step_data['frame_path'] = from_path
       
        self.step_widgets[from_idx].update_image(to_path)
        self.step_widgets[to_idx].update_image(from_path)
       
        # Show confirmation
        QMessageBox.information(
            self,
            "Images Swapped",
            f"Successfully swapped images between Step {from_idx + 1} and Step {to_idx + 1}",
            QMessageBox.Ok
        )
   
    def copy_image(self, from_idx, to_idx):
        """Copy image from one step to another"""
        if from_idx >= len(self.steps) or to_idx >= len(self.steps):
            return
       
        # Copy frame path
        from_path = self.steps[from_idx].get('frame_path', '')
       
        self.steps[to_idx]['frame_path'] = from_path
        self.step_widgets[to_idx].step_data['frame_path'] = from_path
        self.step_widgets[to_idx].update_image(from_path)
       
        # Show confirmation
        QMessageBox.information(
            self,
            "Image Copied",
            f"Successfully copied image from Step {from_idx + 1} to Step {to_idx + 1}",
            QMessageBox.Ok
        )
   
    def on_step_changed(self, idx: int, updated_step: dict):
        self.steps[idx] = updated_step
        self.renumber_steps()
   
    def insert_step_after(self, idx: int):
        new_step = {
            "step_description": "New Step",
            "system": "System Name",
            "actions": "• The AI Agent performs action",
            "frame_path": "",
            "frame_number": 0
        }
        self.steps.insert(idx + 1, new_step)
        self.reload_steps()
   
    def delete_step(self, idx):
        """Handle step deletion in separate thread"""
        thread = StepOperationThread('delete', None, idx)
        thread.operation_complete.connect(self._handle_step_operation)
        thread.error.connect(self._handle_thread_error)
        self.operation_threads.append(thread)
        thread.start()
   
    def reload_steps(self):
        for w in self.step_widgets:
            w.setParent(None)
        self.load_steps()
   
    def renumber_steps(self):
        for i, (step, widget) in enumerate(zip(self.steps, self.step_widgets)):
            step["frame_number"] = i + 1
            widget.original_idx = i
            widget.thumb.step_idx = i
            widget.update_title()
   
    def save_and_regenerate(self):
        kept = []
        for i, w in enumerate(self.step_widgets):
            if not hasattr(w, 'deleted') or not w.deleted:
                step = self.steps[i]
                step["frame_number"] = len(kept) + 1
                kept.append(step)
       
        if not kept:
            QMessageBox.warning(self, "Empty Process", "At least one step is required.")
            return
       
        # Save cleaned steps to JSON (for reference only)
        temp_json = os.path.join(self.output_dir, "cleaned_pdd_analyses.json")
        with open(temp_json, "w", encoding="utf-8") as f:
            json.dump(kept, f, indent=2, ensure_ascii=False)
       
        # Emit the cleaned steps directly - NO API CALL
        self.steps_updated.emit(kept)
       
        QMessageBox.information(
            self,
            "Success",
            f"Successfully saved {len(kept)} steps!",
            QMessageBox.Ok
        )
        self.accept()
   
    def _handle_step_operation(self, result):
        """Handle completed step operation"""
        op_type = result['operation']
        idx = result['step_idx']
       
        if op_type == 'edit':
            self.steps[idx] = result['step_data']
            self.renumber_steps()
        elif op_type == 'insert':
            self.steps.insert(idx + 1, result['step_data'])
            self.reload_steps()
        elif op_type == 'delete':
            if idx < len(self.step_widgets):
                self.step_widgets[idx].setVisible(False)
                self.step_widgets[idx].deleted = True
   
    def _handle_thread_error(self, error_msg):
        QMessageBox.critical(self, "Operation Error", error_msg)
   
    def _update_progress_text(self, text):
        """Update progress bar text"""
        self.progress.setFormat(text)
   
    def cleanup_threads(self):
        """Clean up threads on close"""
        print("🔒 Cleaning up threads...")
        # if self.regenerate_thread and self.regenerate_thread.isRunning():
        #     self.regenerate_thread.terminate()
        #     self.regenerate_thread.wait()
       
        for thread in self.operation_threads:
            if thread.isRunning():
                thread.terminate()
                thread.wait()
       
        print("✅ Threads cleaned up")
   
    def closeEvent(self, event):
        """Clean up threads on close"""
        self.cleanup_threads()
        event.accept()



# class GeminiRegenerateThread(QThread):
#     finished = pyqtSignal(str)
#     error = pyqtSignal(str)
#     progress_update = pyqtSignal(str) # NEW
#     def __init__(self, analyzer, kept_steps, video_path, output_dir):
#         super().__init__()
#         self.analyzer = analyzer
#         self.kept_steps = kept_steps
#         self.video_path = video_path
#         self.output_dir = output_dir

#     def _regenerate_steps_from_json(self, kept_steps: List[Dict], video_path: str, output_dir: str) -> str:
#         prompt = f"""
#         You are given a list of process steps extracted from a video.
#         Renumber them starting from 1. Keep `step_description`, `actions`, and frame_path exactly.
#         Remove duplicates. Return ONLY valid JSON array with same structure.
#         Add field `new_step_number`.
#         Steps:
#         {json.dumps(kept_steps, indent=2)}
#         """
#         try:
#             response = self.model.generate_content(prompt)
#             raw = response.text or ""
#             # Save raw response for debugging
#             os.makedirs(output_dir, exist_ok=True)
#             with open(os.path.join(output_dir, "raw_model_response.txt"), "w", encoding="utf-8") as rf:
#                 rf.write(raw)

#             # Try robust extraction of the first JSON array
#             def extract_first_json_array(s: str) -> str | None:
#                 start = s.find('[')
#                 if start == -1:
#                     return None
#                 depth = 0
#                 for i in range(start, len(s)):
#                     if s[i] == '[':
#                         depth += 1
#                     elif s[i] == ']':
#                         depth -= 1
#                         if depth == 0:
#                             return s[start:i+1]
#                 return None

#             candidate = extract_first_json_array(raw)
#             if candidate is None:
#                 # remove code fences and retry
#                 cleaned = re.sub(r"```(?:json)?", "", raw, flags=re.IGNORECASE).strip()
#                 candidate = extract_first_json_array(cleaned)

#             if candidate is None:
#                 raise RuntimeError("No JSON array found in model output. See raw_model_response.txt")

#             data = json.loads(candidate)

#             # ENSURE frame_path is preserved
#             for orig, cleaned in zip(kept_steps, data):
#                 if 'frame_path' in orig:
#                     cleaned['frame_path'] = orig['frame_path']

#             cleaned_path = os.path.join(output_dir, "cleaned_pdd_analyses.json")
#             with open(cleaned_path, "w", encoding="utf-8") as f:
#                 json.dump(data, f, indent=2, ensure_ascii=False)
#             return cleaned_path
#         except Exception as e:
#             # save the raw response to help debugging
#             try:
#                 with open(os.path.join(output_dir, "raw_model_response_on_error.txt"), "w", encoding="utf-8") as rf:
#                     rf.write(raw)
#             except Exception:
#                 pass
#             raise RuntimeError(f"Gemini regeneration failed: {e}")

#     def run(self):
#         try:
#             self.progress_update.emit("Starting regeneration...")
#             cleaned_path = self.analyzer._regenerate_steps_from_json(
#                 self.kept_steps, self.video_path, self.output_dir
#             )
#             self.progress_update.emit("Regeneration complete!")
#             self.finished.emit(cleaned_path)
#         except Exception as e:
#             import traceback
#             self.error.emit(f"{str(e)}\n\n{traceback.format_exc()}")

class DropZoneLabel(QLabel):
    """Custom QLabel with drag-and-drop functionality"""
    file_dropped = pyqtSignal(str)  # Signal to emit when file is dropped
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAcceptDrops(True)
        self.allowed_extensions = ['.doc', '.docx', '.pdf', '.mp4', '.txt', '.xlsx', '.xls']
        
    def dragEnterEvent(self, event):
        """Called when a drag enters the widget"""
        if event.mimeData().hasUrls():
            # Check if any of the dragged files have valid extensions
            valid_file = False
            for url in event.mimeData().urls():
                file_path = url.toLocalFile()
                _, ext = os.path.splitext(file_path)
                if ext.lower() in self.allowed_extensions:
                    valid_file = True
                    break
            
            if valid_file:
                event.acceptProposedAction()
                # Visual feedback - change border color
                self.setStyleSheet("""
                    QLabel {
                        border: 2px dashed #0ea5e9;
                        border-radius: 8px;
                        background-color: #1a1a1a;
                    }
                """)
            else:
                event.ignore()
        else:
            event.ignore()
    
    def dragLeaveEvent(self, event):
        """Called when drag leaves the widget"""
        # Reset border color
        self.setStyleSheet("""
            QLabel {
                border: 2px dashed #575858;
                border-radius: 8px;
                background-color: #111111;
            }
        """)
    
    def dropEvent(self, event):
        """Called when file is dropped"""
        # Reset border color
        self.setStyleSheet("""
            QLabel {
                border: 2px dashed #575858;
                border-radius: 8px;
                background-color: #111111;
            }
        """)
        
        if event.mimeData().hasUrls():
            for url in event.mimeData().urls():
                file_path = url.toLocalFile()
                
                # Skip empty paths
                if not file_path:
                    continue
                
                _, ext = os.path.splitext(file_path)
                
                if ext.lower() in self.allowed_extensions:
                    # Accept the drop action first
                    event.acceptProposedAction()
                    # Then emit signal with the file path
                    self.file_dropped.emit(file_path)
                    return
            
            # If no valid file found, ignore
            event.ignore()
        else:
            event.ignore()


class CloseConfirmationDialog(QDialog):
    """Draggable, frameless confirmation dialog for closing application with save option"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.Dialog | Qt.WindowStaysOnTopHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setFixedSize(550, 280)
        
        # Center on screen
        screen_geometry = QApplication.desktop().screenGeometry()
        x = (screen_geometry.width() - self.width()) // 2
        y = (screen_geometry.height() - self.height()) // 2
        self.move(x, y)
        
        # Dragging variables
        self.drag_position = None
        
        # Result variable
        self.result_value = None
        
        self.setup_ui()
    
    def setup_ui(self):
        """Setup the UI for the close confirmation dialog"""
        # Main container
        container = QWidget(self)
        container.setGeometry(0, 0, 550, 280)
        container.setObjectName("closeContainer")
        container.setStyleSheet("""
            QWidget#closeContainer {
                background-color: #2d2d2d;
                border: 1px solid #444444;
                border-radius: 12px;
            }
        """)
        
        layout = QVBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # Title bar
        title_bar = QWidget()
        title_bar.setFixedHeight(60)
        title_bar.setStyleSheet("""
            QWidget {
                background: #333333;
                border-radius: 12px 12px 0px 0px;
                border-bottom: 1px solid #444444;
            }
        """)
        
        title_layout = QHBoxLayout(title_bar)
        title_layout.setContentsMargins(25, 15, 25, 15)
        title_layout.setSpacing(0)
        
        # Title with icon
        title_label = QLabel("Confirm Changes to Save")
        title_label.setStyleSheet("""
            QLabel {
                color: #ffffff;
                font-family: 'Asen Pro', Arial, sans-serif;
                font-weight: bold;
                font-size: 16px;
                background: transparent;
                border: none;
            }
        """)
        title_label.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        
        title_layout.addWidget(title_label)
        title_layout.addStretch()
        
        # Close button - Only closes dialog, doesn't close app
        close_btn = QPushButton()
        close_btn.setFixedSize(24, 24)
        close_btn.setCursor(Qt.PointingHandCursor)
        close_btn.setStyleSheet("""
            QPushButton {
                background: transparent;
                border: none;
            }
            QPushButton:hover {
                background-color: rgba(255, 255, 255, 0.1);
                border-radius: 12px;
            }
        """)
        close_btn.clicked.connect(self.on_close_dialog)
        
        # Custom X icon
        def paint_close_btn(event):
            painter = QPainter(close_btn)
            painter.setRenderHint(QPainter.Antialiasing)
            pen = QPen(QColor(255, 255, 255), 2)
            painter.setPen(pen)
            margin = 6
            painter.drawLine(margin, margin, 18, 18)
            painter.drawLine(18, margin, margin, 18)
        
        close_btn.paintEvent = paint_close_btn
        title_layout.addWidget(close_btn)
        
        layout.addWidget(title_bar)
        
        # Content area
        content_widget = QWidget()
        content_layout = QVBoxLayout(content_widget)
        content_layout.setContentsMargins(40, 40, 40, 40)
        content_layout.setSpacing(30)
        
        # Message
        message_label = QLabel("Do you want to save the changes?")
        message_label.setStyleSheet("""
            QLabel {
                color: #e0e0e0;
                font-family: 'Asen Pro', Arial, sans-serif;
                font-size: 14px;
                background: transparent;
                border: none;
            }
        """)
        message_label.setAlignment(Qt.AlignCenter)
        message_label.setWordWrap(True)
        message_label.setMinimumWidth(400)
        
        content_layout.addSpacing(10)
        content_layout.addWidget(message_label, 1, Qt.AlignCenter)
        content_layout.addStretch()
        
        # Buttons
        button_layout = QHBoxLayout()
        button_layout.setSpacing(20)
        button_layout.setContentsMargins(0, 0, 0, 0)
        
        # Discard button
        discard_btn = QPushButton("Discard Changes")
        discard_btn.setCursor(Qt.PointingHandCursor)
        discard_btn.setFixedSize(180, 44)
        discard_btn.setStyleSheet("""
            QPushButton {
                background-color: #c41e3a;
                color: #ffffff;
                border: none;
                border-radius: 6px;
                font-family: 'Asen Pro', Arial, sans-serif;
                font-weight: bold;
                font-size: 13px;
            }
            QPushButton:hover {
                background-color: #a01830;
            }
            QPushButton:pressed {
                background-color: #8b1729;
            }
        """)
        discard_btn.clicked.connect(self.on_discard)
        
        # Save button
        save_btn = QPushButton("Save Changes")
        save_btn.setCursor(Qt.PointingHandCursor)
        save_btn.setFixedSize(180, 44)
        save_btn.setStyleSheet("""
            QPushButton {
                background-color: #0077be;
                color: #ffffff;
                border: none;
                border-radius: 6px;
                font-family: 'Asen Pro', Arial, sans-serif;
                font-weight: bold;
                font-size: 13px;
            }
            QPushButton:hover {
                background-color: #005fa3;
            }
            QPushButton:pressed {
                background-color: #004a82;
            }
        """)
        save_btn.clicked.connect(self.on_save)
        
        button_layout.addStretch()
        button_layout.addWidget(discard_btn)
        button_layout.addWidget(save_btn)
        button_layout.addStretch()
        
        content_layout.addLayout(button_layout)
        
        layout.addWidget(content_widget, 1)
    
    def on_save(self):
        """Handle save button click"""
        self.result_value = True
        self.accept()
    
    def on_discard(self):
        """Handle discard button click"""
        self.result_value = False
        self.accept()  # Close the dialog and let closeEvent handle the app close
    
    def on_close_dialog(self):
        """Handle X button click - only closes dialog, not the app"""
        self.result_value = None  # No action, just close dialog
        self.reject()
    
    def mousePressEvent(self, event):
        """Handle mouse press for dragging"""
        if event.y() < 60:  # Title bar area
            self.drag_position = event.globalPos() - self.frameGeometry().topLeft()
            event.accept()
    
    def mouseMoveEvent(self, event):
        """Handle mouse move for dragging"""
        if self.drag_position is not None:
            self.move(event.globalPos() - self.drag_position)
            event.accept()
    
    def keyPressEvent(self, event):
        """Handle key press"""
        if event.key() == Qt.Key_Escape:
            self.on_close_dialog()  # ESC only closes dialog, doesn't close app
        else:
            super().keyPressEvent(event)


class DynamicXPathDialog(QDialog):
    """Frameless draggable dialog for dynamic XPath input"""
    
    def __init__(self, xpath_key, current_value, parent=None):
        super().__init__(parent)
        self.xpath_key = xpath_key
        self.current_value = current_value
        self.parent_app = parent
        self.drag_position = None
        
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.Dialog)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setFixedSize(520, 280)
        self.setup_ui()
        self.center_on_parent()
    
    def setup_ui(self):
        """Setup the dialog UI"""
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # Main frame - No borders
        main_frame = QFrame()
        main_frame.setStyleSheet("""
            QFrame {
                background-color: #2d2d30;
                border-radius: 12px;
                border: none;
            }
        """)
        
        frame_layout = QVBoxLayout(main_frame)
        frame_layout.setContentsMargins(24, 18, 24, 24)
        frame_layout.setSpacing(16)
        
        # ===== Title Bar =====
        title_layout = QHBoxLayout()
        title_layout.setContentsMargins(0, 0, 0, 0)
        title_layout.setSpacing(0)
        
        title_label = QLabel("Dynamic XPath Configuration")
        title_label.setStyleSheet("""
            QLabel {
                color: #ffffff;
                font-size: 16px;
                font-weight: 600;
                letter-spacing: 0.4px;
            }
        """)
        title_layout.addWidget(title_label)
        title_layout.addStretch()
        
        close_btn = QPushButton("✕")
        close_btn.setFixedSize(28, 28)
        close_btn.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                color: #888888;
                border: none;
                font-size: 20px;
                padding: 0px;
                margin: 0px;
            }
            QPushButton:hover {
                color: #ffffff;
                background-color: rgba(255, 255, 255, 0.05);
                border-radius: 4px;
            }
        """)
        close_btn.clicked.connect(self.reject)
        title_layout.addWidget(close_btn)
        
        frame_layout.addLayout(title_layout)
        
        # ===== XPath Key Info =====
        key_layout = QHBoxLayout()
        key_layout.setSpacing(12)
        key_layout.setContentsMargins(0, 5, 0, 0)
        
        key_label = QLabel("XPath Key:")
        key_label.setStyleSheet("""
            QLabel {
                color: #999999;
                font-size: 12px;
                font-weight: 500;
                letter-spacing: 0.2px;
            }
        """)
        key_layout.addWidget(key_label)
        
        key_value = QLabel(self.xpath_key)
        key_value.setStyleSheet("""
            QLabel {
                color: #4CAF50;
                font-size: 13px;
                font-weight: 600;
                font-family: 'Consolas', monospace;
                padding: 5px 10px;
                background-color: rgba(76, 175, 80, 0.12);
                border-radius: 5px;
                border: none;
            }
        """)
        key_layout.addWidget(key_value)
        key_layout.addStretch()
        
        frame_layout.addLayout(key_layout)
        
        # ===== XPath Value Input (Single Editable Field - Bigger) =====
        value_label = QLabel("XPath Value:")
        value_label.setStyleSheet("""
            QLabel {
                color: #999999;
                font-size: 12px;
                font-weight: 500;
                letter-spacing: 0.2px;
                margin-top: 2px;
            }
        """)
        frame_layout.addWidget(value_label)
        
        self.dynamic_xpath_input = QLineEdit()
        self.dynamic_xpath_input.setText(self.current_value)  # Pre-fill with current value
        self.dynamic_xpath_input.setPlaceholderText("Enter or modify XPath expression...")
        self.dynamic_xpath_input.setClearButtonEnabled(True)
        self.dynamic_xpath_input.setMinimumHeight(54)  # Increased height
        self.dynamic_xpath_input.setStyleSheet("""
            QLineEdit {
                background-color: #353538;
                color: #ffffff;
                border: none;
                border-radius: 6px;
                padding: 12px 14px;
                font-family: 'Consolas', 'Monaco', monospace;
                font-size: 13px;
                selection-background-color: #0ea5e9;
            }
            QLineEdit:focus {
                background-color: #3a3a3d;
                outline: none;
            }
            QLineEdit:hover {
                background-color: #3a3a3d;
            }
        """)
        frame_layout.addWidget(self.dynamic_xpath_input)
        
        # ===== Button Container =====
        button_layout = QHBoxLayout()
        button_layout.setSpacing(10)
        button_layout.setContentsMargins(0, 8, 0, 0)
        
        # Cancel button
        cancel_btn = QPushButton("Cancel")
        cancel_btn.setFixedHeight(38)
        cancel_btn.setStyleSheet("""
            QPushButton {
                background-color: #404040;
                color: #ffffff;
                border: none;
                border-radius: 6px;
                padding: 0px 24px;
                font-size: 12px;
                font-weight: 600;
                letter-spacing: 0.3px;
            }
            QPushButton:hover {
                background-color: #4a4a4a;
            }
            QPushButton:pressed {
                background-color: #353535;
            }
        """)
        cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(cancel_btn)
        
        # Implement button
        implement_btn = QPushButton("Implement XPath")
        implement_btn.setFixedHeight(38)
        implement_btn.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                                        stop:0 #00a8cc, stop:1 #0088aa);
                color: #ffffff;
                border: none;
                border-radius: 6px;
                padding: 0px 24px;
                font-size: 12px;
                font-weight: 600;
                letter-spacing: 0.3px;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                                        stop:0 #00b8dc, stop:1 #0098ba);
            }
            QPushButton:pressed {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                                        stop:0 #007799, stop:1 #005577);
            }
        """)
        implement_btn.clicked.connect(self.on_implement_clicked)
        button_layout.addWidget(implement_btn)
        
        frame_layout.addLayout(button_layout)
        
        main_layout.addWidget(main_frame)
    
    def on_implement_clicked(self):
        """Handle implement button click"""
        dynamic_xpath_value = self.dynamic_xpath_input.text().strip()
        
        if not dynamic_xpath_value:
            QMessageBox.warning(self, "Input Required", "Please enter a dynamic XPath expression")
            return
        
        # Close dialog first
        self.accept()
        
        # Call the parent's implement function
        if self.parent_app:
            self.parent_app.implement_dynamic_xpath(self.xpath_key, dynamic_xpath_value)
    
    def center_on_parent(self):
        """Center dialog on parent window"""
        if self.parent_app:
            parent_geom = self.parent_app.geometry()
            self.move(
                parent_geom.center().x() - self.width() // 2,
                parent_geom.center().y() - self.height() // 2
            )
        else:
            # Center on screen if no parent
            screen = QApplication.primaryScreen()
            screen_geom = screen.geometry()
            self.move(
                screen_geom.center().x() - self.width() // 2,
                screen_geom.center().y() - self.height() // 2
            )
    
    def mousePressEvent(self, event):
        """Handle mouse press for dragging"""
        if event.button() == Qt.LeftButton:
            # Check if click is on title bar area (top 30 pixels)
            if event.pos().y() < 50:
                self.drag_position = event.globalPos() - self.frameGeometry().topLeft()
                event.accept()
    
    def mouseMoveEvent(self, event):
        """Handle mouse move for dragging"""
        if self.drag_position is not None and event.buttons() == Qt.LeftButton:
            self.move(event.globalPos() - self.drag_position)
            event.accept()


class LoadingIndicatorDialog(QDialog):
    """Frameless loading indicator dialog with animated GIF only - transparent background"""
    
    def __init__(self, title, gif_path, parent=None):
        super().__init__(parent)
        self.gif_path = gif_path
        
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.Dialog | Qt.WindowStaysOnTopHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setFixedSize(120, 120)
        self.setup_ui()
        self.center_on_parent(parent)
    
    def setup_ui(self):
        """Setup the loading dialog UI - GIF only"""
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # Loading GIF container
        import os
        if os.path.exists(self.gif_path):
            self.gif_label = QLabel()
            self.gif_label.setAlignment(Qt.AlignCenter)
            movie = QMovie(self.gif_path)
            movie.setScaledSize(QSize(100, 100))
            self.gif_label.setMovie(movie)
            movie.start()
            main_layout.addWidget(self.gif_label)
        else:
            # Fallback spinner if GIF not found
            spinner_label = QLabel("⏳")
            spinner_label.setAlignment(Qt.AlignCenter)
            spinner_label.setStyleSheet("""
                QLabel {
                    color: #00a8cc;
                    font-size: 48px;
                }
            """)
            main_layout.addWidget(spinner_label)
    
    def center_on_parent(self, parent):
        """Center dialog on parent window"""
        if parent:
            parent_geom = parent.geometry()
            self.move(
                parent_geom.center().x() - self.width() // 2,
                parent_geom.center().y() - self.height() // 2
            )


class DynamicXPathSuccessNotificationGif(QDialog):
    """Frameless loading indicator dialog with GIF for success - centered on screen"""
    
    def __init__(self, xpath_key, parent=None):
        super().__init__(parent)
        self.xpath_key = xpath_key
        self.gif_path = resource_path("styles/gif/process_completed.gif")
        
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.Dialog | Qt.WindowStaysOnTopHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setFixedSize(150, 150)
        self.setup_ui()
        self.center_on_parent(parent)
        
        # Auto-close after 2.5 seconds
        QTimer.singleShot(2500, self.close_notification)
    
    def setup_ui(self):
        """Setup the success notification UI - GIF only"""
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # Success GIF container
        import os
        if os.path.exists(self.gif_path):
            self.gif_label = QLabel()
            self.gif_label.setAlignment(Qt.AlignCenter)
            movie = QMovie(self.gif_path)
            movie.setScaledSize(QSize(130, 130))
            self.gif_label.setMovie(movie)
            movie.start()
            main_layout.addWidget(self.gif_label)
            print(f"✅ Loaded success GIF from {self.gif_path}")
        else:
            # Fallback checkmark if GIF not found
            checkmark_label = QLabel("✅")
            checkmark_label.setAlignment(Qt.AlignCenter)
            checkmark_label.setStyleSheet("""
                QLabel {
                    color: #4CAF50;
                    font-size: 72px;
                }
            """)
            main_layout.addWidget(checkmark_label)
            print(f"⚠️ Success GIF not found at {self.gif_path}, using fallback checkmark")
    
    def center_on_parent(self, parent):
        """Center dialog on parent window or screen"""
        if parent:
            parent_geom = parent.geometry()
            self.move(
                parent_geom.center().x() - self.width() // 2,
                parent_geom.center().y() - self.height() // 2
            )
        else:
            # Center on screen if no parent
            screen = QApplication.primaryScreen()
            screen_geom = screen.geometry()
            self.move(
                screen_geom.center().x() - self.width() // 2,
                screen_geom.center().y() - self.height() // 2
            )
    
    def close_notification(self):
        """Close the notification"""
        self.close()
        self.deleteLater()


class DynamicXPathSuccessNotification(QWidget):
    """Auto-closing notification widget for dynamic XPath success"""
    
    def __init__(self, xpath_key, parent=None):
        super().__init__(parent)
        self.xpath_key = xpath_key
        
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setFixedSize(350, 80)
        self.setup_ui()
        self.position_top_right()
        
        # Auto-close after 3 seconds
        QTimer.singleShot(3000, self.close_notification)
    
    def setup_ui(self):
        """Setup the notification UI"""
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(15, 15, 15, 15)
        main_layout.setSpacing(0)
        
        # Main frame
        main_frame = QFrame()
        main_frame.setStyleSheet("""
            QFrame {
                background-color: #2d2d30;
                border: 1px solid #404040;
                border-radius: 8px;
            }
        """)
        
        frame_layout = QVBoxLayout(main_frame)
        frame_layout.setContentsMargins(12, 12, 12, 12)
        frame_layout.setSpacing(5)
        
        # Title
        title_layout = QHBoxLayout()
        title_label = QLabel("✅ Dynamic XPath Implemented")
        title_label.setStyleSheet("""
            QLabel {
                color: #4CAF50;
                font-size: 13px;
                font-weight: bold;
            }
        """)
        title_layout.addWidget(title_label)
        title_layout.addStretch()
        
        close_btn = QPushButton("✕")
        close_btn.setFixedSize(20, 20)
        close_btn.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                color: #ffffff;
                border: none;
                font-size: 14px;
                padding: 0px;
            }
            QPushButton:hover {
                background-color: #404040;
            }
        """)
        close_btn.clicked.connect(self.close_notification)
        title_layout.addWidget(close_btn)
        
        frame_layout.addLayout(title_layout)
        
        # Message
        message = QLabel(f"Successfully implemented dynamic XPath for: <b>{self.xpath_key}</b>")
        message.setWordWrap(True)
        message.setStyleSheet("""
            QLabel {
                color: #cccccc;
                font-size: 11px;
                padding: 2px;
            }
        """)
        frame_layout.addWidget(message)
        
        main_layout.addWidget(main_frame)
    
    def position_top_right(self):
        """Position notification at top right of screen"""
        screen = QApplication.primaryScreen()
        screen_geom = screen.geometry()
        self.move(
            screen_geom.right() - self.width() - 20,
            screen_geom.top() + 20
        )
    
    def close_notification(self):
        """Close the notification"""
        self.close()
        self.deleteLater()


class AutomationApp(QMainWindow):
    def __init__(self, username=None, userid=None, refreshtoken=None, accesstoken=None, parent=None,token_manager=None):
        # super().__init__()
        super().__init__(parent)
        self.username = username
        self.userid = userid
        self.token_manager = token_manager

        font_path = resource_path("styles\\font\\AsenPro-Regular.otf")
        font_id = QFontDatabase.addApplicationFont(font_path)
        if font_id == -1:
            print("Failed to load Asen Pro font")
        else:
            font_families = QFontDatabase.applicationFontFamilies(font_id)
            if font_families:
                asen_font_family = font_families[0]
                # This applies to the whole app
                QApplication.instance().setFont(QFont(asen_font_family, 9))
        
        self.asen_font_family = "Asen Pro"
        self.username = username
        self.xpath_header_label=None
        self.userid = userid
        self.refreshtoken = refreshtoken
        self.accesstoken = accesstoken
        self.req_class = []
        self.app_title=None
        self.task_events=[]
        self.conditional_info={}
        self.full_task_info=[]
        self.task_processor = None
        self.selected_transcript_path = None
        self.pdf_thread = None
        self.monitor_widget_instance = None
        self.current_driver = None
        self.debug_state = debug_state.DebugState()
        self.debug_signals = Debug_terminal.DebugSignals()
        # import config
        self.gemini_api_key = config.API_KEY
        self.gemini_service = GeminiSessionService(self.gemini_api_key)
        self.selected_file_path = None
        # Initialize project and task selection variables
        self.selected_project_id = None
        self.selected_project_name = None
        self.selected_task_id = None
        self.selected_task_name = None
        self.setup_debug_connections()
        self.setup_dark_theme()
        self.init_ui()
        
        # Connect to application quit event to ensure cleanup
        QApplication.instance().aboutToQuit.connect(self.cleanup_on_quit)
        
        if hasattr(self, 'tasks_status_label'):
            self.update_tasks_status("Ready", "#4CAF50")
        
        # Initialize XPath data for chat panel
        self.xpath_data = {}
        
        # Initialize automation mode
        self.current_automation_mode = "web"  # Default to web automation
        
        # self.setup_chrome()
        
    def setup_debug_connections(self):
        """Setup debug signal connections"""
        self.debug_signals.debug_started.connect(self.on_debug_started)
        self.debug_signals.line_executing.connect(self.on_line_executing)
        self.debug_signals.line_executed.connect(self.on_line_executed)
        self.debug_signals.breakpoint_hit.connect(self.on_breakpoint_hit)
        self.debug_signals.step_paused.connect(self.on_step_paused)
        self.debug_signals.execution_error.connect(self.on_execution_error)
        self.debug_signals.debug_stopped.connect(self.on_debug_stopped)
        self.debug_signals.debug_completed.connect(self.on_debug_completed)
        self.debug_signals.task_debug_completed.connect(self.on_task_debug_completed)
        self.debug_signals.pdb_waiting_for_input.connect(self.on_pdb_waiting_for_input)
        self.debug_signals.pdb_output_received.connect(self.on_pdb_output_received)
        self.debug_signals.pdb_step_executed.connect(self.on_pdb_step_executed)
        self.debug_signals.pdb_continue_executed.connect(self.on_pdb_continue_executed)
        self.debug_signals.pdb_quit_executed.connect(self.on_pdb_quit_executed)
        self.debug_signals.pdb_line_changed.connect(self.on_pdb_line_changed)
        self.debug_signals.code_display_requested.connect(self.on_code_display_requested)

    def on_pdb_quit_executed(self):
        """Handle PDB quit execution with enhanced UI feedback"""
        # Update status
        self.debug_status_label.setText("Debug Status: Debug session terminated")
        
        # Disable debug mode in terminal
        self.terminal_display.disable_debug_mode()
        
        # Reset debug state properly
        self.debug_state.stop_requested = False
        self.debug_state.execution_paused = False
        self.debug_state.debug_action = None
        self.debug_state.current_line = 0
        
        # Clear terminal and show termination message
        self.terminal_display.clear()
        
        # Add styled termination message
        termination_message = """
    🛑 DEBUG SESSION TERMINATED
    ═══════════════════════════════════════

    Debug session was stopped by user request.
    PDB execution has been terminated.

    ✅ Ready for new debugging session.
        """
        
        self.terminal_display.setPlainText(termination_message)
        
        # Also emit a signal if needed for other components
        self.debug_signals.debug_stopped.emit()
        
        # Optional: Reset any breakpoint highlighting
        if hasattr(self.terminal_display, 'highlighter'):
            self.terminal_display.highlighter.clear_current_line()


    def on_pdb_waiting_for_input(self):
        """Handle PDB waiting for user input"""
        self.terminal_display.enable_debug_mode()
        self.debug_status_label.setText("Debug Status: PDB waiting for input...")

    def on_pdb_line_changed(self, line_number, line_content):
        """Handle PDB line changes with proper UI updates"""
        print(f" GUI: Updating display for line {line_number}: {line_content}")
        
        # Update status
        self.debug_status_label.setText(f"Debug Status: Line {line_number}: {line_content}")
        
        # Update terminal highlighting
        if hasattr(self.terminal_display, 'current_code_lines'):
            # Find the line in the display and update highlighting
            for i, display_line in enumerate(self.terminal_display.current_code_lines):
                if line_content.strip() in display_line.strip():
                    self.terminal_display.display_code_with_highlighting(
                        '\n'.join(self.terminal_display.current_code_lines), 
                        i
                    )
                    break


    def on_pdb_step_executed(self):
        """Handle PDB step execution"""
        self.debug_status_label.setText("Debug Status: PDB stepped to next line")

    def on_pdb_continue_executed(self):
        """Handle PDB continue execution"""
        self.debug_status_label.setText("Debug Status: PDB continuing execution...")
        self.terminal_display.disable_debug_mode()
        
    def setup_dark_theme(self):
        """Apply modern dark theme to the application"""
        QApplication.instance().setStyle("Fusion")
        
        palette = QPalette()
        palette.setColor(QPalette.Window, QColor(45, 45, 48))
        palette.setColor(QPalette.WindowText, QColor(255, 255, 255))
        palette.setColor(QPalette.Base, QColor(30, 30, 32))
        palette.setColor(QPalette.AlternateBase, QColor(45, 45, 48))
        palette.setColor(QPalette.ToolTipBase, QColor(0, 0, 0))
        palette.setColor(QPalette.ToolTipText, QColor(255, 255, 255))
        palette.setColor(QPalette.Text, QColor(255, 255, 255))
        palette.setColor(QPalette.Button, QColor(45, 45, 48))
        palette.setColor(QPalette.ButtonText, QColor(255, 255, 255))
        palette.setColor(QPalette.BrightText, QColor(255, 0, 0))
        palette.setColor(QPalette.Link, QColor(42, 130, 218))
        palette.setColor(QPalette.Highlight, QColor(42, 130, 218))
        palette.setColor(QPalette.HighlightedText, QColor(0, 0, 0))
        
        self.setPalette(palette)
        
    def setup_chrome(self):
        import os
        chrome_profile_path = os.path.join(
            os.environ["USERPROFILE"],
            r"AppData\Local\Google\Chrome\User Data\Profile 1"
        )
        chrome_path = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
        user_data_dir = chrome_profile_path
        debug_port = "9223"
        import subprocess_cmd
        subprocess_cmd.df_subprocess_cmd(chrome_path, user_data_dir, debug_port)
        
    def init_ui(self):
        # Set frameless window
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowSystemMenuHint)
        self.setAttribute(Qt.WA_TranslucentBackground, False)
        
        self.setWindowTitle("Agent Flow")
        self.setGeometry(100, 100, 1600, 1000)
        self.setMinimumSize(1400, 900)
        self.setWindowIcon(QIcon(resource_path(("styles/Icon/Header Agent.png"))))
        screen = QApplication.primaryScreen().availableGeometry()

        screen_width = screen.width()
        screen_height = screen.height()

        # Calculate scale factor based on reference resolution (1920x1080)
        self.scale_factor = round(min(screen_width / 1920, screen_height / 1080), 2)
        
        # Create main container widget
        main_container = QWidget()
        self.setCentralWidget(main_container)
        
        # Create main container layout
        container_layout = QVBoxLayout(main_container)
        container_layout.setContentsMargins(0, 0, 0, 0)
        container_layout.setSpacing(0)
        
        # Add custom title bar
        self.title_bar = CustomTitleBar(self)
        container_layout.addWidget(self.title_bar)
        
        # Create content widget
        content_widget = QWidget()
        content_layout = QVBoxLayout(content_widget)
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(0)
        
        # Add toolbar and main content to content widget
        self.create_toolbar_in_content(content_layout)
        
        # Add content widget to main container
        container_layout.addWidget(content_widget)
        
        self.showMaximized()
        
        # Apply centralized stylesheet
        style_loader.apply_stylesheet(self)
        
        main_layout = QHBoxLayout()
        main_layout.setSpacing(0)
        main_layout.setContentsMargins(0, 0, 0, 0)
        self.create_sidebar(main_layout,screen_width)
        self.create_main_content(main_layout)
        
        # Add main layout to content layout
        content_layout.addLayout(main_layout)

    def handle_signout(self):
        # Add your custom sign-out logic here
        print("Performing custom sign-out process...")
        
        signout.delete_credentials_files()
        self.close()
    
    def closeEvent(self, event):
        """Handle application close event - clean up all threads"""
        print("[MAIN] Application closing - cleaning up threads...")
        
        try:
            # Clean up file worker thread
            if hasattr(self, 'file_worker') and self.file_worker is not None:
                print("[MAIN] Stopping file worker thread...")
                self.file_worker.should_stop = True
                if self.file_worker.isRunning():
                    self.file_worker.wait(2000)  # Wait max 2 seconds
                self.file_worker.deleteLater()
                
            # Clean up manual worker thread
            if hasattr(self, 'manual_worker') and self.manual_worker is not None:
                print("[MAIN] Stopping manual worker thread...")
                if self.manual_worker.isRunning():
                    self.manual_worker.wait(2000)
                self.manual_worker.deleteLater()
                
            # Clean up other worker threads
            for worker_attr in ['task_population_worker', 'preprocess_completion_worker']:
                if hasattr(self, worker_attr):
                    worker = getattr(self, worker_attr)
                    if worker is not None and worker.isRunning():
                        print(f"[MAIN] Stopping {worker_attr}...")
                        worker.wait(1000)
                        worker.deleteLater()
            
            print("[MAIN] All threads cleaned up successfully")
            
        except Exception as cleanup_error:
            print(f"[MAIN] Warning during application cleanup: {cleanup_error}")
        
        # Accept the close event
        event.accept()
        super().closeEvent(event)
    
    def cleanup_on_quit(self):
        """Clean up resources when application is about to quit"""
        print("[MAIN] Application about to quit. Closing all status popups and detail mode dialogs.")
        
        try:
            # Clean up any remaining threads
            self.cleanup_file_worker()
            
            # Clean up any other resources
            if hasattr(self, 'current_driver') and self.current_driver:
                try:
                    self.current_driver.quit()
                except:
                    pass
                    
        except Exception as e:
            print(f"[MAIN] Warning during quit cleanup: {e}")
    
    def on_automation_mode_changed(self, mode_key):
        """Handle automation mode change from dropdown"""
        print(f"Automation mode changed to: {mode_key}")
        
        # Store current automation mode
        self.current_automation_mode = mode_key
        
        # Update UI immediately based on mode
        self.update_ui_for_automation_mode(mode_key)
        
        # Mode-specific logic
        if mode_key == "web":
            print("Switched to Web Automation mode")
            # Add web-specific initialization if needed
        elif mode_key == "desktop":
            print("Switched to Desktop Automation mode")
            # Add desktop-specific initialization if needed
        elif mode_key == "native":
            print("Switched to Native Automation mode")
            # Add native-specific initialization if needed
        elif mode_key == "citrix":
            print("Switched to Citrix Automation mode")
            # Add citrix-specific initialization if needed
        
        # Update status or perform mode-specific actions
        self.log_message(f" Automation mode switched to: {mode_key.title()}")
        
        # You can emit signals or update other components based on the mode
        # For example, update task processing behavior based on selected mode
    
    def update_ui_for_automation_mode(self, mode_key):
        """Update UI elements based on automation mode selection"""
        print(f"🔄 Updating UI for automation mode: {mode_key}")
        
        try:
            # Update Code tab based on mode
            if hasattr(self, 'code_chat_btn') and hasattr(self, 'xpath_vars_btn'):
                if mode_key == 'native':
                    # Native mode: Hide XPath/Attributes tab, show only Code Chat
                    self.xpath_vars_btn.hide()
                    self.xpath_vars_content.hide()
                    self.code_chat_btn.setChecked(True)
                    self.code_chat_content.show()
                    print("🔧 Native mode: Hidden XPath/Attributes tab, showing only Code Chat")
                else:
                    # Desktop/Web/Citrix modes: Show both tabs
                    self.xpath_vars_btn.show()
                    
                    # Update tab text based on mode
                    if mode_key == 'desktop':
                        self.xpath_vars_btn.setText("Attributes Details")
                        print("🔧 Desktop mode: Changed tab to 'Attributes Details'")
                    elif mode_key == 'citrix':
                        self.xpath_vars_btn.setText("Citrix Data Details")
                        print("🔧 Citrix mode: Changed tab to 'Citrix Data Details'")
                    else:
                        self.xpath_vars_btn.setText("XPath Variables")
                        print("🔧 Web mode: Changed tab to 'XPath Variables'")
            
            # Refresh XPath/Attributes data display if visible
            if hasattr(self, 'refresh_code_tab_xpath_data') and mode_key != 'native':
                self.refresh_code_tab_xpath_data()
                print("🔄 Refreshed XPath/Attributes data display")
            
            # Update header text and UI elements in real-time
            if hasattr(self, 'refresh_code_tab_ui_text') and mode_key != 'native':
                self.refresh_code_tab_ui_text()
                print("🔄 Updated header and UI text in real-time")
            
            # Update draggable chat panel if it exists
            if hasattr(self, 'chat_panel') and self.chat_panel:
                if mode_key == 'native':
                    # Hide XPath section in chat panel for native mode
                    if hasattr(self.chat_panel, 'xpath_section'):
                        self.chat_panel.xpath_section.hide()
                else:
                    # Show XPath section for other modes
                    if hasattr(self.chat_panel, 'xpath_section'):
                        self.chat_panel.xpath_section.show()
                    # Refresh chat panel data
                    if hasattr(self.chat_panel, 'refresh_xpath_data'):
                        self.chat_panel.refresh_xpath_data()
            
            print(f"✅ UI updated successfully for {mode_key} mode")
            
        except Exception as e:
            print(f"❌ Error updating UI for automation mode: {e}")
            import traceback
            traceback.print_exc()
    
    def update_json_tab_name(self, automation_mode):
        """Update the JSON tab name based on automation mode"""
        try:
            if hasattr(self, 'xpath_vars_btn') and automation_mode != 'native':
                if automation_mode == 'desktop':
                    self.xpath_vars_btn.setText("Attributes Details")
                    print("🔧 Updated tab name to 'Attributes Details' for desktop mode")
                elif automation_mode == 'citrix':
                    self.xpath_vars_btn.setText("Citrix Data Details")
                    print("🔧 Updated tab name to 'Citrix Data Details' for citrix mode")
                else:
                    self.xpath_vars_btn.setText("XPath Variables")
                    print("🔧 Updated tab name to 'XPath Variables' for web mode")
        except Exception as e:
            print(f"❌ Error updating JSON tab name: {e}")
    
    def extract_task_zip(self, zip_file_path, project_id, task_id):
        """
        Extract zip file containing task .py files and images/ folder to the proper folder structure.
        If folders already exist, overwrites all .py files and images with new ones.
        
        Args:
            zip_file_path: Path to the downloaded zip file
            project_id: The project ID
            task_id: The task ID
            
        Returns:
            bool: True if extraction successful, False otherwise
        """
        import zipfile
        
        try:
            proj_folder_name = f"proj_{project_id}"
            task_folder_name = f"task_{task_id}"
            task_folder_path = os.path.join(proj_folder_name, task_folder_name)
            
            # Create folders if they don't exist
            os.makedirs(proj_folder_name, exist_ok=True)
            os.makedirs(task_folder_path, exist_ok=True)
            
            # Extract zip file
            with zipfile.ZipFile(zip_file_path, 'r') as zipf:
                # List all files in zip
                zip_contents = zipf.namelist()
                print(f"📦 Extracting zip file: {os.path.basename(zip_file_path)}")
                print(f"📦 Zip contains {len(zip_contents)} files")
                

                
                # Extract all files
                for file_name in zip_contents:
                    # Extract to current directory (zip already has proper structure)
                    zipf.extract(file_name, ".")
                    if file_name.endswith('.py'):
                        print(f"✅ Extracted .py file: {file_name}")
                    elif '/images/' in file_name:
                        print(f"🖼️ Extracted image file: {file_name}")
                
                # Count extracted .py files (excluding __init__.py)
                py_files_count = sum(1 for f in zip_contents 
                                    if f.endswith('.py') and '__init__.py' not in f)
                
                # Count extracted image files
                image_files_count = sum(1 for f in zip_contents if '/images/' in f)
                
                print(f"📦 Successfully extracted {py_files_count} .py files and {image_files_count} image files to {task_folder_path}")
                return True
                
        except zipfile.BadZipFile:
            print(f"❌ Invalid zip file: {zip_file_path}")
            return False
        except Exception as e:
            print(f"❌ Error extracting zip file: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def create_task_zip(self, project_id, task_id):
        """
        Create a zip file containing all .py files and images/ folder from the task folder
        with proper folder structure: proj_{project_id}/__init__.py and 
        proj_{project_id}/task_{task_id}/__init__.py
        
        Args:
            project_id: The project ID
            task_id: The task ID
            
        Returns:
            str: Path to the created zip file, or None if no files found
        """
        import zipfile
        import tempfile
        
        try:
            proj_folder_name = f"proj_{project_id}"
            task_folder_name = f"task_{task_id}"
            task_folder_path = os.path.join(proj_folder_name, task_folder_name)
            
            # Check if task folder exists
            if not os.path.exists(task_folder_path):
                print(f"⚠️ Task folder not found: {task_folder_path}")
                return None
            
            # Collect all .py files from task folder (excluding __init__.py)
            py_files = []
            for file in os.listdir(task_folder_path):
                if file.endswith('.py') and file != '__init__.py':
                    py_files.append(file)
            
            # Check if images folder exists
            images_folder_path = os.path.join(task_folder_path, "images")
            image_files = []
            if os.path.exists(images_folder_path) and os.path.isdir(images_folder_path):
                for file in os.listdir(images_folder_path):
                    image_files.append(file)
                    print(f"📸 Found image file: {file}")
            
            if not py_files and not image_files:
                print(f"⚠️ No .py files or images found in {task_folder_path}")
                return None
            
            # Create zip file name
            zip_filename = f"{proj_folder_name}_{task_folder_name}.zip"
            zip_path = os.path.join(tempfile.gettempdir(), zip_filename)
            
            # Create zip file
            with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                # Add proj folder __init__.py
                proj_init_content = ""  # Empty __init__.py
                zipf.writestr(f"{proj_folder_name}/__init__.py", proj_init_content)
                print(f"✅ Added {proj_folder_name}/__init__.py to zip")
                
                # Add task folder __init__.py
                task_init_content = ""  # Empty __init__.py
                zipf.writestr(f"{proj_folder_name}/{task_folder_name}/__init__.py", task_init_content)
                print(f"✅ Added {proj_folder_name}/{task_folder_name}/__init__.py to zip")
                
                # Add all .py files from task folder
                for py_file in py_files:
                    file_path = os.path.join(task_folder_path, py_file)
                    arcname = f"{proj_folder_name}/{task_folder_name}/{py_file}"
                    zipf.write(file_path, arcname)
                    print(f"✅ Added {py_file} to zip")
                
                # Add all image files from images folder if it exists
                if image_files:
                    for image_file in image_files:
                        image_path = os.path.join(images_folder_path, image_file)
                        arcname = f"{proj_folder_name}/{task_folder_name}/images/{image_file}"
                        zipf.write(image_path, arcname)
                        print(f"🖼️ Added images/{image_file} to zip")
            
            print(f"📦 Successfully created zip file: {zip_path}")
            print(f"📦 Zip contains: {len(py_files)} .py files + {len(image_files)} image files + 2 __init__.py files")
            
            # Save a copy of the zip in the project folder as well
            # local_zip_path = os.path.join(proj_folder_name, zip_filename)
            # import shutil
            # shutil.copy2(zip_path, local_zip_path)
            # print(f"📦 Saved local copy: {local_zip_path}")
            
            return zip_path
            
        except Exception as e:
            print(f"❌ Error creating task zip: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    def saveoption(self):
        try:
            # Prepare data for JSON
            data = {
                "steps": getattr(self, "req_class", []),
                "events": getattr(self, "task_events", []),
                "combined": getattr(self, "full_task_info", [])
            }

            # Save JSON file
            with open("recorded_steps.json", "w", encoding="utf-8") as f:
                json.dump(data, f, indent=4)
            self.log_message("💾 Saved JSON to recorded_steps.json")
            
            # Get current code from Code tab and save to execute_code.py
            current_code = ""
            if hasattr(self, 'code_display'):
                current_code = self.code_display.toPlainText()
            
            # Save current code to execute_code.py (both locally and for upload)
            os.makedirs("code_py", exist_ok=True)
            execute_code_path = "code_py/execute_code.py"
            with open(execute_code_path, "w", encoding="utf-8") as f:
                f.write(current_code)
            self.log_message("💾 Saved current code to code_py/execute_code.py")
            
            # Save XPath JSON file
            xpath_json_path = "json_info/json_xpath.json"
            os.makedirs("json_info", exist_ok=True)
            
            if os.path.exists(xpath_json_path):
                try:
                    with open(xpath_json_path, "r", encoding="utf-8") as f:
                        xpath_data = json.load(f)
                except:
                    xpath_data = {}
            else:
                xpath_data = {}
            
            with open(xpath_json_path, "w", encoding="utf-8") as f:
                json.dump(xpath_data, f, indent=4)
            self.log_message("💾 Saved XPath data to json_info/json_xpath.json")

            # Show custom confirmation popup
            reply = self.show_save_confirmation()
            
            if not reply:
                return
            
            # Upload to server
            url = f"{MAIN_URL}/app/project/upload-files/"

            # Check if project and task are selected
            if not hasattr(self, 'selected_project_id') or not self.selected_project_id:
                self.show_custom_warning("Warning", "Please select a project first!")
                return

            if not hasattr(self, 'selected_task_id') or not self.selected_task_id:
                self.show_custom_warning("Warning", "Please select a task first!")
                return
            
            project_id = self.selected_project_id
            taskid = self.selected_task_id
            payload = {
                "user_id": self.userid,
                "task_id": taskid,
                "project_id": project_id,
            }

            # Create zip file with all .py files from task folder
            zip_file_path = self.create_task_zip(project_id, taskid)
            
            # Upload all files including the zip
            files_to_upload = [
                ("files", ("recorded_steps.json", open("recorded_steps.json", "rb"), "application/json")),
                ("files", ("execute_code.py", open(execute_code_path, "rb"), "text/x-python")),
                ("files", ("json_xpath.json", open(xpath_json_path, "rb"), "application/json")),
            ]
            
            # Add citrix_data.json if it exists
            citrix_data_path = "json_info/citrix_data.json"
            if os.path.exists(citrix_data_path):
                files_to_upload.append(
                    ("files", ("citrix_data.json", open(citrix_data_path, "rb"), "application/json"))
                )
                self.log_message(f"📦 Added citrix_data.json to upload")
            
            # Add zip file if it was created successfully
            if zip_file_path and os.path.exists(zip_file_path):
                files_to_upload.append(
                    ("files", (os.path.basename(zip_file_path), open(zip_file_path, "rb"), "application/zip"))
                )
                self.log_message(f"📦 Created zip file: {os.path.basename(zip_file_path)}")
            
            try:
                response = requests.post(url, data=payload, files=files_to_upload)
            finally:
                # Close all file handles
                for file_tuple in files_to_upload:
                    file_tuple[1][1].close()

            # Log response
            print(response.status_code)
            print(response.text)

            self.log_message("💾 Saved all files: tasks, code, and XPath data")

            # Show success popup
            self.show_custom_success("Success", "All changes saved and uploaded successfully!")

        except Exception as e:
            self.log_message(f"❌ Save Error: {str(e)}")
            self.show_custom_error("Error", f"Failed to save data: {str(e)}")

    def saveoption_no_confirmation(self):
        """Save changes without showing the confirmation popup (used by close dialog)"""
        try:
            # Prepare data for JSON
            data = {
                "steps": getattr(self, "req_class", []),
                "events": getattr(self, "task_events", []),
                "combined": getattr(self, "full_task_info", [])
            }

            # Save JSON file
            with open("recorded_steps.json", "w", encoding="utf-8") as f:
                json.dump(data, f, indent=4)
            self.log_message("💾 Saved JSON to recorded_steps.json")
            
            # Get current code from Code tab and save to execute_code.py
            current_code = ""
            if hasattr(self, 'code_display'):
                current_code = self.code_display.toPlainText()
            
            # Save current code to execute_code.py (both locally and for upload)
            os.makedirs("code_py", exist_ok=True)
            execute_code_path = "code_py/execute_code.py"
            with open(execute_code_path, "w", encoding="utf-8") as f:
                f.write(current_code)
            self.log_message("💾 Saved current code to code_py/execute_code.py")
            
            # Save XPath JSON file
            xpath_json_path = "json_info/json_xpath.json"
            os.makedirs("json_info", exist_ok=True)
            
            if os.path.exists(xpath_json_path):
                try:
                    with open(xpath_json_path, "r", encoding="utf-8") as f:
                        xpath_data = json.load(f)
                except:
                    xpath_data = {}
            else:
                xpath_data = {}
            
            with open(xpath_json_path, "w", encoding="utf-8") as f:
                json.dump(xpath_data, f, indent=4)
            self.log_message("💾 Saved XPath data to json_info/json_xpath.json")

            # SKIP the confirmation popup - go directly to upload
            
            # Upload to server
            url = f"{MAIN_URL}/app/project/upload-files/"

            # Check if project and task are selected
            if not hasattr(self, 'selected_project_id') or not self.selected_project_id:
                self.log_message("⚠️ Warning: Please select a project first!")
                return

            if not hasattr(self, 'selected_task_id') or not self.selected_task_id:
                self.log_message("⚠️ Warning: Please select a task first!")
                return
            
            project_id = self.selected_project_id
            taskid = self.selected_task_id
            payload = {
                "user_id": self.userid,
                "task_id": taskid,
                "project_id": project_id,
            }

            # Create zip file with all .py files from task folder
            zip_file_path = self.create_task_zip(project_id, taskid)
            
            # Upload all files including the zip
            files_to_upload = [
                ("files", ("recorded_steps.json", open("recorded_steps.json", "rb"), "application/json")),
                ("files", ("execute_code.py", open(execute_code_path, "rb"), "text/x-python")),
                ("files", ("json_xpath.json", open(xpath_json_path, "rb"), "application/json")),
            ]
            
            # Add citrix_data.json if it exists
            citrix_data_path = "json_info/citrix_data.json"
            if os.path.exists(citrix_data_path):
                files_to_upload.append(
                    ("files", ("citrix_data.json", open(citrix_data_path, "rb"), "application/json"))
                )
                self.log_message(f"📦 Added citrix_data.json to upload")
            
            # Add zip file if it was created successfully
            if zip_file_path and os.path.exists(zip_file_path):
                files_to_upload.append(
                    ("files", (os.path.basename(zip_file_path), open(zip_file_path, "rb"), "application/zip"))
                )
                self.log_message(f"📦 Created zip file: {os.path.basename(zip_file_path)}")
            
            try:
                headers = {
                    'Authorization': f'Bearer {self.accesstoken}',
                }
                
                response = requests.post(url, headers=headers, data=payload, files=files_to_upload)
                
                if response.status_code == 200:
                    self.log_message("✅ All files uploaded to cloud successfully!")
                else:
                    self.log_message(f"⚠️ Upload warning: {response.status_code} - {response.text}")
                    
            except Exception as upload_error:
                self.log_message(f"⚠️ Upload Error: {str(upload_error)}")

        except Exception as e:
            self.log_message(f"❌ Save Error: {str(e)}")

    def show_save_confirmation(self):
        """Show custom confirmation dialog for save operation"""
        dialog = QDialog(self)
        dialog.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool | Qt.X11BypassWindowManagerHint)
        dialog.setAttribute(Qt.WA_TranslucentBackground)
        dialog.setFixedSize(620, 350)
        # Center the dialog on screen
        qr = dialog.frameGeometry()
        cp = QDesktopWidget().availableGeometry().center()
        qr.moveCenter(cp)
        dialog.move(qr.topLeft())
        
        dialog.setModal(True)
        dialog.setStyleSheet("")
        
        container = QWidget(dialog)
        container.setGeometry(0, 0, 620, 350)
        container.setObjectName("confirmContainer")
        container.setStyleSheet("QWidget#confirmContainer { background-color: #414141 !important; border: none !important; border-radius: 15px !important; }")
        
        layout = QVBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 25)
        layout.setSpacing(0)

        # Title bar
        title_container = QWidget()
        title_container.setFixedHeight(60)
        title_container.setStyleSheet("QWidget { background: #333333 !important; border-radius: 20px 20px 0px 0px !important; border: none !important; }")
        
        title_layout = QHBoxLayout(title_container)
        title_layout.setContentsMargins(25, 15, 25, 15)
        
        title_label = QLabel("💾 Confirm Save")
        title_label.setStyleSheet("QLabel { color: #ffffff !important; font-family: 'Asen Pro' !important; font-weight: bold !important; font-size: 16px !important; background: transparent !important; border: none !important; }")
        title_label.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        title_layout.addWidget(title_label)
        title_layout.addStretch()
        
        close_btn = QPushButton()
        close_btn.setFixedSize(24, 24)
        close_btn.setStyleSheet("QPushButton { background: transparent !important; border: none !important; } QPushButton:hover { background-color: rgba(255, 255, 255, 0.1) !important; border-radius: 12px !important; }")
        
        def paintEvent(event):
            painter = QPainter(close_btn)
            painter.setRenderHint(QPainter.Antialiasing)
            pen = QPen(QColor(255, 255, 255), 2)
            painter.setPen(pen)
            margin = 6
            painter.drawLine(margin, margin, 18, 18)
            painter.drawLine(18, margin, margin, 18)
        close_btn.paintEvent = paintEvent
        
        dialog.result_value = False
        
        def on_close():
            dialog.result_value = False
            dialog.reject()
        
        close_btn.clicked.connect(on_close)
        title_layout.addWidget(close_btn)
        layout.addWidget(title_container)
        layout.addSpacing(30)
        
        # Main message
        main_msg = QLabel("Do you want to save the current changes to cloud?")
        main_msg.setStyleSheet("QLabel { color: #FFFFFF !important; font-family: 'Asen Pro' !important; font-weight: 600 !important; font-size: 18px !important; text-align: center !important; background: transparent !important; border: none !important; padding: 10px 40px !important; }")
        main_msg.setAlignment(Qt.AlignCenter)
        main_msg.setWordWrap(True)
        layout.addWidget(main_msg)
        
        layout.addSpacing(10)
        
        # Details
        details = QLabel("This will upload:\n• Generated tasks\n• Current code from Code tab\n• XPath variables")
        details.setStyleSheet("QLabel { color: #FFFFFF !important; font-family: 'Asen Pro' !important; font-weight: 400 !important; font-size: 14px !important; text-align: center !important; background: transparent !important; border: none !important; padding: 10px 40px !important; }")
        details.setAlignment(Qt.AlignCenter)
        details.setWordWrap(True)
        layout.addWidget(details)
        
        layout.addSpacing(30)
        
        # Buttons
        button_layout = QHBoxLayout()
        button_layout.setSpacing(15)
        
        def on_no():
            dialog.result_value = False
            dialog.reject()
        
        def on_yes():
            dialog.result_value = True
            dialog.accept()
        
        no_btn = QPushButton("❌ No")
        no_btn.setFixedSize(120, 40)
        no_btn.setStyleSheet("QPushButton { background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1, stop: 0 #008AB3, stop: 1 #005B7F) !important; color: #FFFFFF !important; border: none !important; border-radius: 10px !important; font-family: 'Asen Pro' !important; font-weight: 600 !important; font-size: 16px !important; } QPushButton:hover { background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1, stop: 0 #0099CC, stop: 1 #006699) !important; }")
        no_btn.clicked.connect(on_no)
        
        yes_btn = QPushButton("✅ Yes")
        yes_btn.setFixedSize(120, 40)
        yes_btn.setStyleSheet("QPushButton { background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1, stop: 0 #008AB3, stop: 1 #005B7F) !important; color: #FFFFFF !important; border: none !important; border-radius: 10px !important; font-family: 'Asen Pro' !important; font-weight: 600 !important; font-size: 16px !important; } QPushButton:hover { background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1, stop: 0 #0099CC, stop: 1 #006699) !important; }")
        yes_btn.clicked.connect(on_yes)
        
        button_layout.addStretch()
        button_layout.addWidget(no_btn)
        button_layout.addWidget(yes_btn)
        button_layout.addStretch()
        layout.addLayout(button_layout)
        
        dialog.exec_()
        return dialog.result_value


    def show_custom_warning(self, title, message):
        """Show custom warning dialog"""
        dialog = QDialog(self)
        dialog.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool | Qt.X11BypassWindowManagerHint)
        dialog.setAttribute(Qt.WA_TranslucentBackground)
        dialog.setFixedSize(520, 280)
        # Center the dialog
        qr = dialog.frameGeometry()
        cp = QDesktopWidget().availableGeometry().center()
        qr.moveCenter(cp)
        dialog.move(qr.topLeft())
        dialog.setModal(True)
        
        container = QWidget(dialog)
        container.setGeometry(0, 0, 520, 280)
        container.setObjectName("warningContainer")
        container.setStyleSheet("QWidget#warningContainer { background-color: #414141 !important; border: none !important; border-radius: 15px !important; }")
        
        layout = QVBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 25)
        layout.setSpacing(0)

        # Title bar
        title_container = QWidget()
        title_container.setFixedHeight(60)
        title_container.setStyleSheet("QWidget { background: #333333 !important; border-radius: 20px 20px 0px 0px !important; border: none !important; }")
        
        title_layout = QHBoxLayout(title_container)
        title_layout.setContentsMargins(25, 15, 25, 15)
        
        title_label = QLabel(f"⚠️ {title}")
        title_label.setStyleSheet("QLabel { color: #ffffff !important; font-family: 'Asen Pro' !important; font-weight: bold !important; font-size: 16px !important; background: transparent !important; border: none !important; }")
        title_label.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        title_layout.addWidget(title_label)
        title_layout.addStretch()
        
        close_btn = QPushButton()
        close_btn.setFixedSize(24, 24)
        close_btn.setStyleSheet("QPushButton { background: transparent !important; border: none !important; } QPushButton:hover { background-color: rgba(255, 255, 255, 0.1) !important; border-radius: 12px !important; }")
        
        def paintEvent(event):
            painter = QPainter(close_btn)
            painter.setRenderHint(QPainter.Antialiasing)
            pen = QPen(QColor(255, 255, 255), 2)
            painter.setPen(pen)
            margin = 6
            painter.drawLine(margin, margin, 18, 18)
            painter.drawLine(18, margin, margin, 18)
        close_btn.paintEvent = paintEvent
        close_btn.clicked.connect(dialog.accept)
        
        title_layout.addWidget(close_btn)
        layout.addWidget(title_container)
        layout.addSpacing(40)
        
        # Message
        msg_label = QLabel(message)
        msg_label.setStyleSheet("QLabel { color: #FFFFFF !important; font-family: 'Asen Pro' !important; font-weight: 600 !important; font-size: 16px !important; text-align: center !important; background: transparent !important; border: none !important; padding: 10px 40px !important; }")
        msg_label.setAlignment(Qt.AlignCenter)
        msg_label.setWordWrap(True)
        layout.addWidget(msg_label)
        
        layout.addSpacing(40)
        
        # OK Button
        button_layout = QHBoxLayout()
        ok_btn = QPushButton("OK")
        ok_btn.setFixedSize(120, 40)
        ok_btn.setStyleSheet("QPushButton { background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1, stop: 0 #008AB3, stop: 1 #005B7F) !important; color: #FFFFFF !important; border: none !important; border-radius: 10px !important; font-family: 'Asen Pro' !important; font-weight: 600 !important; font-size: 16px !important; } QPushButton:hover { background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1, stop: 0 #0099CC, stop: 1 #006699) !important; }")
        ok_btn.clicked.connect(dialog.accept)
        
        button_layout.addStretch()
        button_layout.addWidget(ok_btn)
        button_layout.addStretch()
        layout.addLayout(button_layout)
        
        dialog.exec_()


    def show_custom_success(self, title, message):
        """Show custom success dialog"""
        dialog = QDialog(self)
        dialog.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool | Qt.X11BypassWindowManagerHint)
        dialog.setAttribute(Qt.WA_TranslucentBackground)
        dialog.setFixedSize(520, 280)
        qr = dialog.frameGeometry()
        cp = QDesktopWidget().availableGeometry().center()
        qr.moveCenter(cp)
        dialog.move(qr.topLeft())
        dialog.setModal(True)
        
        container = QWidget(dialog)
        container.setGeometry(0, 0, 520, 280)
        container.setObjectName("successContainer")
        container.setStyleSheet("QWidget#successContainer { background-color: #414141 !important; border: none !important; border-radius: 15px !important; }")
        
        layout = QVBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 25)
        layout.setSpacing(0)

        # Title bar
        title_container = QWidget()
        title_container.setFixedHeight(60)
        title_container.setStyleSheet("QWidget { background: #333333 !important; border-radius: 20px 20px 0px 0px !important; border: none !important; }")
        
        title_layout = QHBoxLayout(title_container)
        title_layout.setContentsMargins(25, 15, 25, 15)
        
        title_label = QLabel(f"✅ {title}")
        title_label.setStyleSheet("QLabel { color: #ffffff !important; font-family: 'Asen Pro' !important; font-weight: bold !important; font-size: 16px !important; background: transparent !important; border: none !important; }")
        title_label.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        title_layout.addWidget(title_label)
        title_layout.addStretch()
        
        close_btn = QPushButton()
        close_btn.setFixedSize(24, 24)
        close_btn.setStyleSheet("QPushButton { background: transparent !important; border: none !important; } QPushButton:hover { background-color: rgba(255, 255, 255, 0.1) !important; border-radius: 12px !important; }")
        
        def paintEvent(event):
            painter = QPainter(close_btn)
            painter.setRenderHint(QPainter.Antialiasing)
            pen = QPen(QColor(255, 255, 255), 2)
            painter.setPen(pen)
            margin = 6
            painter.drawLine(margin, margin, 18, 18)
            painter.drawLine(18, margin, margin, 18)
        close_btn.paintEvent = paintEvent
        close_btn.clicked.connect(dialog.accept)
        
        title_layout.addWidget(close_btn)
        layout.addWidget(title_container)
        layout.addSpacing(40)
        
        # Message
        msg_label = QLabel(message)
        msg_label.setStyleSheet("QLabel { color: #FFFFFF !important; font-family: 'Asen Pro' !important; font-weight: 600 !important; font-size: 16px !important; text-align: center !important; background: transparent !important; border: none !important; padding: 10px 40px !important; }")
        msg_label.setAlignment(Qt.AlignCenter)
        msg_label.setWordWrap(True)
        layout.addWidget(msg_label)
        
        layout.addSpacing(40)
        
        # OK Button
        button_layout = QHBoxLayout()
        ok_btn = QPushButton("OK")
        ok_btn.setFixedSize(120, 40)
        ok_btn.setStyleSheet("QPushButton { background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1, stop: 0 #008AB3, stop: 1 #005B7F) !important; color: #FFFFFF !important; border: none !important; border-radius: 10px !important; font-family: 'Asen Pro' !important; font-weight: 600 !important; font-size: 16px !important; } QPushButton:hover { background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1, stop: 0 #0099CC, stop: 1 #006699) !important; }")
        ok_btn.clicked.connect(dialog.accept)
        
        button_layout.addStretch()
        button_layout.addWidget(ok_btn)
        button_layout.addStretch()
        layout.addLayout(button_layout)
        
        dialog.exec_()


    def show_custom_error(self, title, message):
        """Show custom error dialog"""
        dialog = QDialog(self)
        dialog.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool | Qt.X11BypassWindowManagerHint)
        dialog.setAttribute(Qt.WA_TranslucentBackground)
        dialog.setFixedSize(520, 280)
        # Center the dialog
        qr = dialog.frameGeometry()
        cp = QDesktopWidget().availableGeometry().center()
        qr.moveCenter(cp)
        dialog.move(qr.topLeft())
        dialog.setModal(True)
        
        container = QWidget(dialog)
        container.setGeometry(0, 0, 520, 280)
        container.setObjectName("errorContainer")
        container.setStyleSheet("QWidget#errorContainer { background-color: #414141 !important; border: none !important; border-radius: 15px !important; }")
        
        layout = QVBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 25)
        layout.setSpacing(0)

        # Title bar
        title_container = QWidget()
        title_container.setFixedHeight(60)
        title_container.setStyleSheet("QWidget { background: #333333 !important; border-radius: 20px 20px 0px 0px !important; border: none !important; }")
        
        title_layout = QHBoxLayout(title_container)
        title_layout.setContentsMargins(25, 15, 25, 15)
        
        title_label = QLabel(f"❌ {title}")
        title_label.setStyleSheet("QLabel { color: #ffffff !important; font-family: 'Asen Pro' !important; font-weight: bold !important; font-size: 16px !important; background: transparent !important; border: none !important; }")
        title_label.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        title_layout.addWidget(title_label)
        title_layout.addStretch()
        
        close_btn = QPushButton()
        close_btn.setFixedSize(24, 24)
        close_btn.setStyleSheet("QPushButton { background: transparent !important; border: none !important; } QPushButton:hover { background-color: rgba(255, 255, 255, 0.1) !important; border-radius: 12px !important; }")
        
        def paintEvent(event):
            painter = QPainter(close_btn)
            painter.setRenderHint(QPainter.Antialiasing)
            pen = QPen(QColor(255, 255, 255), 2)
            painter.setPen(pen)
            margin = 6
            painter.drawLine(margin, margin, 18, 18)
            painter.drawLine(18, margin, margin, 18)
        close_btn.paintEvent = paintEvent
        close_btn.clicked.connect(dialog.accept)
        
        title_layout.addWidget(close_btn)
        layout.addWidget(title_container)
        layout.addSpacing(40)
        
        # Message
        msg_label = QLabel(message)
        msg_label.setStyleSheet("QLabel { color: #FFFFFF !important; font-family: 'Asen Pro' !important; font-weight: 600 !important; font-size: 16px !important; text-align: center !important; background: transparent !important; border: none !important; padding: 10px 40px !important; }")
        msg_label.setAlignment(Qt.AlignCenter)
        msg_label.setWordWrap(True)
        layout.addWidget(msg_label)
        
        layout.addSpacing(40)
        
        # OK Button
        button_layout = QHBoxLayout()
        ok_btn = QPushButton("OK")
        ok_btn.setFixedSize(120, 40)
        ok_btn.setStyleSheet("QPushButton { background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1, stop: 0 #008AB3, stop: 1 #005B7F) !important; color: #FFFFFF !important; border: none !important; border-radius: 10px !important; font-family: 'Asen Pro' !important; font-weight: 600 !important; font-size: 16px !important; } QPushButton:hover { background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1, stop: 0 #0099CC, stop: 1 #006699) !important; }")
        ok_btn.clicked.connect(dialog.accept)
        
        button_layout.addStretch()
        button_layout.addWidget(ok_btn)
        button_layout.addStretch()
        layout.addLayout(button_layout)
        
        dialog.exec_()

    def show_save_confirmation(self):
        """Show custom confirmation dialog for save operation"""
        dialog = QDialog(self)
        dialog.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool | Qt.X11BypassWindowManagerHint)
        dialog.setAttribute(Qt.WA_TranslucentBackground)
        dialog.setFixedSize(620, 350)
        # Center the dialog on screen
        screen_geometry = QApplication.desktop().screenGeometry()
        x = (screen_geometry.width() - dialog.width()) // 2
        y = (screen_geometry.height() - dialog.height()) // 2
        dialog.move(x, y)
        dialog.setModal(True)
        dialog.setStyleSheet("")
        
        container = QWidget(dialog)
        container.setGeometry(0, 0, 620, 350)
        container.setObjectName("confirmContainer")
        container.setStyleSheet("QWidget#confirmContainer { background-color: #414141 !important; border: none !important; border-radius: 15px !important; }")
        
        layout = QVBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 25)
        layout.setSpacing(0)

        # Title bar
        title_container = QWidget()
        title_container.setFixedHeight(60)
        title_container.setStyleSheet("QWidget { background: #333333 !important; border-radius: 20px 20px 0px 0px !important; border: none !important; }")
        
        title_layout = QHBoxLayout(title_container)
        title_layout.setContentsMargins(25, 15, 25, 15)
        
        title_label = QLabel("💾 Confirm Save")
        title_label.setStyleSheet("QLabel { color: #ffffff !important; font-family: 'Asen Pro' !important; font-weight: bold !important; font-size: 16px !important; background: transparent !important; border: none !important; }")
        title_label.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        title_layout.addWidget(title_label)
        title_layout.addStretch()
        
        close_btn = QPushButton()
        close_btn.setFixedSize(24, 24)
        close_btn.setStyleSheet("QPushButton { background: transparent !important; border: none !important; } QPushButton:hover { background-color: rgba(255, 255, 255, 0.1) !important; border-radius: 12px !important; }")
        
        def paintEvent(event):
            painter = QPainter(close_btn)
            painter.setRenderHint(QPainter.Antialiasing)
            pen = QPen(QColor(255, 255, 255), 2)
            painter.setPen(pen)
            margin = 6
            painter.drawLine(margin, margin, 18, 18)
            painter.drawLine(18, margin, margin, 18)
        close_btn.paintEvent = paintEvent
        
        dialog.result_value = False
        
        def on_close():
            dialog.result_value = False
            dialog.reject()
        
        close_btn.clicked.connect(on_close)
        title_layout.addWidget(close_btn)
        layout.addWidget(title_container)
        layout.addSpacing(30)
        
        # Main message
        main_msg = QLabel("Do you want to save the current changes to cloud?")
        main_msg.setStyleSheet("QLabel { color: #FFFFFF !important; font-family: 'Asen Pro' !important; font-weight: 600 !important; font-size: 18px !important; text-align: center !important; background: transparent !important; border: none !important; padding: 10px 40px !important; }")
        main_msg.setAlignment(Qt.AlignCenter)
        main_msg.setWordWrap(True)
        layout.addWidget(main_msg)
        
        layout.addSpacing(10)
        
        # Details
        details = QLabel("This will upload:\n• Generated tasks\n• Current code from Code tab\n• XPath variables")
        details.setStyleSheet("QLabel { color: #FFFFFF !important; font-family: 'Asen Pro' !important; font-weight: 400 !important; font-size: 14px !important; text-align: center !important; background: transparent !important; border: none !important; padding: 10px 40px !important; }")
        details.setAlignment(Qt.AlignCenter)
        details.setWordWrap(True)
        layout.addWidget(details)
        
        layout.addSpacing(30)
        
        # Buttons
        button_layout = QHBoxLayout()
        button_layout.setSpacing(15)
        
        def on_no():
            dialog.result_value = False
            dialog.reject()
        
        def on_yes():
            dialog.result_value = True
            dialog.accept()
        
        no_btn = QPushButton("❌ No")
        no_btn.setFixedSize(120, 40)
        no_btn.setStyleSheet("QPushButton { background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1, stop: 0 #008AB3, stop: 1 #005B7F) !important; color: #FFFFFF !important; border: none !important; border-radius: 10px !important; font-family: 'Asen Pro' !important; font-weight: 600 !important; font-size: 16px !important; } QPushButton:hover { background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1, stop: 0 #0099CC, stop: 1 #006699) !important; }")
        no_btn.clicked.connect(on_no)
        
        yes_btn = QPushButton("✅ Yes")
        yes_btn.setFixedSize(120, 40)
        yes_btn.setStyleSheet("QPushButton { background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1, stop: 0 #008AB3, stop: 1 #005B7F) !important; color: #FFFFFF !important; border: none !important; border-radius: 10px !important; font-family: 'Asen Pro' !important; font-weight: 600 !important; font-size: 16px !important; } QPushButton:hover { background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1, stop: 0 #0099CC, stop: 1 #006699) !important; }")
        yes_btn.clicked.connect(on_yes)
        
        button_layout.addStretch()
        button_layout.addWidget(no_btn)
        button_layout.addWidget(yes_btn)
        button_layout.addStretch()
        layout.addLayout(button_layout)
        
        dialog.exec_()
        return dialog.result_value
    def open_project_task_dialog(self):
        """Open the project and task selection dialog"""
        
        dialog = ProjectTaskSelectionDialog(
            parent=self,
            userid=self.userid,
            refreshtoken=self.refreshtoken,
            accesstoken=self.accesstoken
        )
        
        if dialog.exec_() == QDialog.Accepted:
            # User selected a project and task
            if dialog.selected_project and dialog.selected_task:
                self.selected_project_id = dialog.selected_project['id']
                self.selected_project_name = dialog.selected_project.get('project_name', 'Unknown Project')
                self.selected_task_id = dialog.selected_task['id']
                self.selected_task_name = dialog.selected_task.get('task_name', 'Unknown Task')
                
                # **CRITICAL FIX**: Transfer loaded task data from dialog to main app
                self.req_class = dialog.loaded_req_class.copy()
                self.task_events = dialog.loaded_task_events.copy()
                self.full_task_info = dialog.loaded_full_task_info.copy()
                self.xpath_data = dialog.loaded_xpath_data.copy()
                self.final_code_log = dialog.loaded_code_content
                
                print(f"[DATA TRANSFER] Transferred {len(self.req_class)} tasks to main app")
                print(f"[DATA TRANSFER] Transferred {len(self.task_events)} task events to main app")
                print(f"[DATA TRANSFER] Transferred {len(self.xpath_data)} XPath variables to main app")
                print(f"[DATA TRANSFER] Transferred {len(self.final_code_log)} chars of code to main app")
                
                # Update the display
                self.update_project_task_display()
                
                # Update UI with loaded data
                if hasattr(self, 'task_list'):
                    try:
                        # Clear existing tasks first
                        self.task_list.clear()
                        self.task_list.clear_breakpoints()
                        
                        # Set the loaded data
                        self.task_list.set_tasks_data(self.req_class, self.task_events, getattr(self, 'app_info', None))
                        
                        # Set conditional info if available
                        if hasattr(self, 'conditional_info'):
                            self.task_list.set_conditional_info(self.conditional_info)
                        
                        print(f"[MAIN APP] Successfully populated {len(self.req_class)} tasks in main app")
                        
                    except Exception as e:
                        print(f"[ERROR] Failed to populate tasks in main app: {e}")
                
                # Update code display
                if hasattr(self, 'code_display') and self.code_display:
                    self.code_display.push_state(self.final_code_log if self.final_code_log else "# No code available")
                    self.code_display.setPlainText(self.final_code_log if self.final_code_log else "# No code available")
                    print("[MAIN APP] Code display updated in main app")
                
                # Update code_log variable with new code content (web mode only)
                current_mode = getattr(self, 'current_automation_mode', 'web')
                if current_mode == 'web':
                    self.code_log = self.final_code_log if self.final_code_log else ""
                    print("[MAIN APP] Updated code_log variable with new task code")
                    
                    # Auto-clear code chat history for web mode without dialog
                    try:
                        if hasattr(self, 'chat_history'):
                            self.chat_history = []
                            print("✅ Cleared Gemini chat history for new task")
                        
                        if hasattr(self, 'ui_chat_history'):
                            self.ui_chat_history = []
                            print("✅ Cleared UI chat history for new task")
                        
                        # Clear the chat messages layout
                        if hasattr(self, 'chat_messages_layout'):
                            while self.chat_messages_layout.count() > 1:  # Keep the stretch
                                item = self.chat_messages_layout.takeAt(0)
                                if item.widget():
                                    item.widget().deleteLater()
                            print("✅ Cleared chat display widgets for new task")
                        
                        # Add system message about new task
                        self.add_chat_message("System", f"New task loaded: {self.selected_task_name}. Starting fresh chat.", is_user=False)
                        print("[MAIN APP] Code chat cleared and reset for new task")
                    except Exception as e:
                        print(f"[WARN] Failed to clear code chat for new task: {e}")
                    
                    # Auto-clear task chat history for new task as well
                    try:
                        if hasattr(self, 'task_chat_history'):
                            self.task_chat_history = []
                            print("✅ Cleared Gemini task_chat_history for new task")
                        
                        if hasattr(self, 'ui_task_chat_history'):
                            self.ui_task_chat_history = []
                            print("✅ Cleared UI task_chat_history for new task")
                        
                        # Clear the task chat messages layout
                        if hasattr(self, 'task_chat_layout'):
                            while self.task_chat_layout.count() > 1:  # Keep the stretch
                                item = self.task_chat_layout.takeAt(0)
                                if item.widget():
                                    item.widget().deleteLater()
                            print("✅ Cleared task chat display widgets for new task")
                        
                        print("[MAIN APP] Task chat cleared and reset for new task")
                    except Exception as e:
                        print(f"[WARN] Failed to clear task chat for new task: {e}")
                
                # Update XPath display in chat panel
                if hasattr(self, 'chat_panel') and hasattr(self.chat_panel, 'update_xpath_display'):
                    self.chat_panel.update_xpath_display(self.xpath_data)
                    print(f"[MAIN APP] Updated chat panel with {len(self.xpath_data)} XPath variables in main app")
                
                # Enable save button if needed
                if hasattr(self, 'save_action_btn'):
                    self.save_action_btn.setEnabled(True)
                
                # Enable start processing button
                if hasattr(self, 'start_btn'):
                    self.start_btn.setEnabled(True)
                    print("[MAIN APP] Start Processing button enabled")
                
                print(f"Selected Project: {self.selected_project_name} (ID: {self.selected_project_id})")
                print(f"Selected Task: {self.selected_task_name} (ID: {self.selected_task_id})")
                print(f"[MAIN APP] Main app now has {len(self.req_class)} tasks ready for processing!")

    def create_toolbar_in_content(self, content_layout):
        """Create toolbar within content area instead of as QMainWindow toolbar"""
        toolbar_widget = QWidget()
        toolbar_widget.setStyleSheet("""
            QWidget {
                background-color: #000;
                border: none;
                padding: 5px;
            }
            QToolButton {
                background-color: #1b1b1b;
                color: #aaa;
                padding: 8px 12px;
                border-radius: 6px;
                margin: 2px;
                border: none;
                min-width: 32px;
                min-height: 32px;
            }
            QToolButton:selected {
                border: 1px solid #17a2b8;
                color: white;
                background-color: #1b1b1b;
            }
            QToolButton:hover {
                color: #17a2b8;
                background-color: #000000;
                border: 1px solid #17a2b8;
            }
            QToolButton:disabled {
                color: #555;
                background-color: #1b1b1b;
            }
            QToolButton:disabled:hover {
                background-color: #1b1b1b;
                border: none;
            }
        """)
        
        toolbar_layout = QHBoxLayout(toolbar_widget)
        toolbar_layout.setContentsMargins(10, 5, 10, 5)
        
        # Create QToolButton
        # In create_toolbar_in_content method, modify the file_button section:

        file_button = QToolButton()
        file_button.setText("")
        file_button.setIcon(QIcon(resource_path("styles/Icon/open.png")))
        file_button.setPopupMode(QToolButton.InstantPopup)
        file_button.setToolButtonStyle(Qt.ToolButtonIconOnly)
        file_button.setIconSize(QSize(20, 20))
        file_button.setToolTip("Open Project")
        file_button.setCursor(Qt.PointingHandCursor)
        file_button.clicked.connect(lambda: self.open_project_with_loading())

        toolbar_layout.addWidget(file_button)

        
        # Add separator
        separator = QFrame()
        separator.setFrameShape(QFrame.VLine)
        separator.setFrameShadow(QFrame.Sunken)
        separator.setStyleSheet("color: #404040;")
        toolbar_layout.addWidget(separator)
        
        # Save button
        self.save_action_btn = QToolButton()
        self.save_action_btn.setText("")
        self.save_action_btn.setIcon(QIcon(resource_path("styles/Icon/save.png")))
        self.save_action_btn.setIconSize(QSize(20, 20))
        self.save_action_btn.setToolTip("Save Project")
        self.save_action_btn.setCursor(Qt.PointingHandCursor)
        self.save_action_btn.setEnabled(False)
        self.save_action_btn.clicked.connect(lambda: (self.player_click.stop(), self.player_click.play(), self.saveoption()))
        toolbar_layout.addWidget(self.save_action_btn)
        
        # Add separator
        separator2 = QFrame()
        separator2.setFrameShape(QFrame.VLine)
        separator2.setFrameShadow(QFrame.Sunken)
        separator2.setStyleSheet("color: #404040;")
        toolbar_layout.addWidget(separator2)
        
        # Add spacer
        spacer = QWidget()
        spacer.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        toolbar_layout.addWidget(spacer)
        
        # Project & Task display widget with icons
        self.project_task_widget = QWidget()
        self.project_task_layout = QHBoxLayout(self.project_task_widget)
        self.project_task_layout.setContentsMargins(0, 0, 0, 0)
        self.project_task_layout.setSpacing(4)
        
        # Create individual components
        self.project_icon_label = QLabel()
        self.project_icon_label.setFixedSize(40, 40)
        self.project_icon_label.setScaledContents(True)
        
        self.project_text_label = QLabel("No Agent Flow Selected")
        self.project_text_label.setStyleSheet("color: #ffffff; padding: 2px;")
        
        self.task_icon_label = QLabel()
        self.task_icon_label.setFixedSize(40, 40)
        self.task_icon_label.setScaledContents(True)
        self.task_icon_label.hide()  # Initially hidden
        
        self.task_text_label = QLabel()
        self.task_text_label.setStyleSheet("color: #ffffff; padding: 2px;")
        self.task_text_label.hide()  # Initially hidden
        
        # Add to layout
        self.project_task_layout.addStretch()
        self.project_task_layout.addWidget(self.project_icon_label)
        self.project_task_layout.addWidget(self.project_text_label)
        self.project_task_layout.addWidget(self.task_icon_label)
        self.project_task_layout.addWidget(self.task_text_label)
        
        self.project_task_widget.setMinimumWidth(200)
        toolbar_layout.addWidget(self.project_task_widget)
        
        # Initialize tracking variables
        self.selected_project_id = None
        self.selected_project_name = None
        self.selected_task_id = None
        self.selected_task_name = None
        
        # Add another spacer
        spacer2 = QWidget()
        spacer2.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        toolbar_layout.addWidget(spacer2)
        
        # Add separator before automation mode dropdown
        separator3 = QFrame()
        separator3.setFrameShape(QFrame.VLine)
        separator3.setFrameShadow(QFrame.Sunken)
        separator3.setStyleSheet("color: #404040;")
        toolbar_layout.addWidget(separator3)

        # Automation Mode Dropdown (moved before resolution info)
        self.automation_mode_widget = automation_mode_dropdown.SwitchModeButton()
        self.automation_mode_widget.mode_changed.connect(self.on_automation_mode_changed)
        self.automation_mode_widget.setToolTip("Switch automation mode")
        toolbar_layout.addWidget(self.automation_mode_widget)

        # Add separator after automation mode dropdown
        separator4 = QFrame()
        separator4.setFrameShape(QFrame.VLine)
        separator4.setFrameShadow(QFrame.Sunken)
        separator4.setStyleSheet("color: #404040;")
        toolbar_layout.addWidget(separator4)

       # Resolution info (moved after automation mode dropdown)
        try:
            from desktop_boundindex_find import get_windows_display_complete
            resolutions = get_windows_display_complete()
            if resolutions and isinstance(resolutions, dict):
                physical_res = f"{resolutions['physical']}"
                scaling = f"{resolutions['scaling']}"
            else:
                physical_res = ""
                scaling = ""
        except ImportError:
            # Fallback if function doesn't exist
            physical_res = "1920x1080"
            scaling = "100%"

        res_label = QLabel(f"{physical_res}  |  {scaling}")
        res_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        res_label.setStyleSheet("color: #ffffff; padding: 6px;")
        toolbar_layout.addWidget(res_label)

        # Add separator after resolution info
        separator5 = QFrame()
        separator5.setFrameShape(QFrame.VLine)
        separator5.setFrameShadow(QFrame.Sunken)
        separator5.setStyleSheet("color: #404040;")
        toolbar_layout.addWidget(separator5)

        # # Sign out button (added after automation mode dropdown)
        # signout_button = QToolButton()
        # signout_button.setText("")
        # signout_button.setIcon(QIcon(resource_path("styles/Icon/log-out.png")))
        # signout_button.setIconSize(QSize(20, 20))
        # signout_button.setToolTip("Log out and close application")
        # signout_button.setCursor(Qt.PointingHandCursor)
        # signout_button.setProperty('class', 'SignOutButton')
        # signout_button.clicked.connect(self.handle_signout)
        # toolbar_layout.addWidget(signout_button)
        # content_layout.addWidget(toolbar_widget)
        # Sign out button (added after automation mode dropdown)


        signout_button = QToolButton()
        signout_button.setText("")
        signout_button.setIcon(QIcon(resource_path("styles/Icon/log-out.png")))
        signout_button.setIconSize(QSize(20, 20))
        signout_button.setToolTip("Log out and close application")
        signout_button.setCursor(Qt.PointingHandCursor)
        signout_button.setProperty('class', 'SignOutButton')
        signout_button.clicked.connect(self.confirm_signout)
        toolbar_layout.addWidget(signout_button)
        content_layout.addWidget(toolbar_widget)
    # def confirm_signout(self):
    #     """Show confirmation dialog before signing out"""
    #     reply = QMessageBox.question(
    #         self,
    #         'Confirm Sign Out',
    #         'Do you want to sign out?',
    #         QMessageBox.Yes | QMessageBox.No,
    #         QMessageBox.No
    #     )
        
    #     if reply == QMessageBox.Yes:
    #         self.handle_signout()

    def open_project_with_loading(self):
        """Show loading dialog before opening project dialog"""
        # Play click sound
        self.player_click.stop()
        self.player_click.play()
        
        # Create and show loading dialog
        self.loading_dialog = QDialog(self)
        self.loading_dialog.setWindowFlags(Qt.Dialog | Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
        self.loading_dialog.setAttribute(Qt.WA_TranslucentBackground)
        self.loading_dialog.setFixedSize(250, 150)
        self.loading_dialog.setModal(True)
        
        container = QWidget(self.loading_dialog)
        container.setGeometry(0, 0, 250, 150)
        container.setStyleSheet("""
            QWidget {
                background-color: #414141;
                border-radius: 15px;
            }
        """)
        
        layout = QVBoxLayout(container)
        layout.setAlignment(Qt.AlignCenter)
        layout.setSpacing(15)
        
        # Spinner
        spinner_label = QLabel("⟳")
        spinner_label.setStyleSheet("""
            QLabel {
                color: #17a2b8;
                font-size: 48px;
                background: transparent;
            }
        """)
        spinner_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(spinner_label)
        
        # Loading text
        text_label = QLabel("Loading Projects...")
        text_label.setStyleSheet("""
            QLabel {
                color: #FFFFFF;
                font-family: 'Asen Pro';
                font-size: 14px;
                background: transparent;
            }
        """)
        text_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(text_label)
        
        self.loading_dialog.show()
        QApplication.processEvents()
        
        # Delay before opening project dialog
        QTimer.singleShot(800, self.open_project_dialog_after_loading)
    def open_project_dialog_after_loading(self):
        """Open project dialog after loading animation"""
        try:
            self.loading_dialog.close()
            self.open_project_task_dialog()
        except Exception as e:
            if hasattr(self, 'loading_dialog'):
                self.loading_dialog.close()
            print(f"Error opening project dialog: {e}")
    def confirm_signout(self):
        """Show confirmation dialog before signing out"""
        reply = self.show_signout_confirmation()
        
        if reply:
            # User clicked Yes - proceed with sign out
            self.handle_signout()
            return True
        else:
            # User clicked No - cancel sign out
            return False

    def show_signout_confirmation(self):
        """Show custom styled sign out confirmation dialog"""
        dialog = QDialog(self)  # Make sure 'self' is the main window
        dialog.setWindowFlags(Qt.Dialog | Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
        dialog.setAttribute(Qt.WA_TranslucentBackground)
        dialog.setFixedSize(500, 300)
        dialog.setModal(True)
        
        container = QWidget(dialog)
        container.setGeometry(0, 0, 500, 300)
        container.setObjectName("signoutContainer")
        container.setStyleSheet("""
            QWidget#signoutContainer {
                background-color: #414141;
                border: none;
                border-radius: 15px;
            }
        """)
    
    # ... rest of your code remains the same ...
        
        layout = QVBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 30)
        layout.setSpacing(0)

        # Title bar
        title_container = QWidget()
        title_container.setFixedHeight(60)
        title_container.setStyleSheet("""
            QWidget {
                background: #333333;
                border-radius: 20px 20px 0px 0px;
                border: none;
            }
        """)
        
        title_layout = QHBoxLayout(title_container)
        title_layout.setContentsMargins(25, 15, 25, 15)
        
        title_label = QLabel("Confirm Sign Out")
        title_label.setStyleSheet("""
            QLabel {
                color: #ffffff;
                font-family: 'Asen Pro';
                font-weight: bold;
                font-size: 16px;
                background: transparent;
                border: none;
            }
        """)
        title_label.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        title_layout.addWidget(title_label)
        title_layout.addStretch()
        
        close_btn = QPushButton()
        close_btn.setFixedSize(24, 24)
        close_btn.setStyleSheet("""
            QPushButton {
                background: transparent;
                border: none;
            }
            QPushButton:hover {
                background-color: rgba(255, 255, 255, 0.1);
                border-radius: 12px;
            }
        """)
        
        def paintEvent(event):
            painter = QPainter(close_btn)
            painter.setRenderHint(QPainter.Antialiasing)
            pen = QPen(QColor(255, 255, 255), 2)
            painter.setPen(pen)
            margin = 6
            painter.drawLine(margin, margin, 18, 18)
            painter.drawLine(18, margin, margin, 18)
        close_btn.paintEvent = paintEvent
        
        dialog.result_value = False
        
        def on_close():
            dialog.result_value = False
            dialog.reject()
        
        close_btn.clicked.connect(on_close)
        title_layout.addWidget(close_btn)
        
        layout.addWidget(title_container)
        layout.addSpacing(50)
        
        # Message
        msg_label = QLabel("Do you want to sign out?")
        msg_label.setStyleSheet("""
            QLabel {
                color: #FFFFFF;
                font-family: 'Asen Pro';
                font-weight: 400;
                font-size: 16px;
                text-align: center;
                background: transparent;
                border: none;
                padding: 10px 40px;
            }
        """)
        msg_label.setWordWrap(True)
        msg_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(msg_label)
        
        layout.addSpacing(50)
        
        # Buttons
        button_layout = QHBoxLayout()
        button_layout.setSpacing(15)
        
        def on_no():
            dialog.result_value = False
            dialog.reject()
        
        def on_yes():
            dialog.result_value = True
            dialog.accept()
        
        no_btn = QPushButton("❌ No")
        no_btn.setFixedSize(120, 40)
        no_btn.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1, stop: 0 #008AB3, stop: 1 #005B7F);
                color: #FFFFFF;
                border: none;
                border-radius: 10px;
                font-family: 'Asen Pro';
                font-weight: 600;
                font-size: 16px;
            }
            QPushButton:hover {
                background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1, stop: 0 #0099CC, stop: 1 #006699);
            }
            QPushButton:pressed {
                background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1, stop: 0 #007799, stop: 1 #004455);
            }
        """)
        no_btn.clicked.connect(on_no)
        
        yes_btn = QPushButton("✅ Yes")
        yes_btn.setFixedSize(120, 40)
        yes_btn.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1, stop: 0 #008AB3, stop: 1 #005B7F);
                color: #FFFFFF;
                border: none;
                border-radius: 10px;
                font-family: 'Asen Pro';
                font-weight: 600;
                font-size: 16px;
            }
            QPushButton:hover {
                background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1, stop: 0 #0099CC, stop: 1 #006699);
            }
            QPushButton:pressed {
                background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1, stop: 0 #007799, stop: 1 #004455);
            }
        """)
        yes_btn.clicked.connect(on_yes)
        
        button_layout.addStretch()
        button_layout.addWidget(no_btn)
        button_layout.addWidget(yes_btn)
        button_layout.addStretch()
        
        layout.addLayout(button_layout)
        
        # Add dragging support
        dialog._mouse_pressed = False
        dialog._mouse_pos = None
        
        def mousePressEvent(event):
            if event.button() == Qt.LeftButton:
                dialog._mouse_pressed = True
                dialog._mouse_pos = event.globalPos() - dialog.pos()
                event.accept()
        
        def mouseReleaseEvent(event):
            if event.button() == Qt.LeftButton:
                dialog._mouse_pressed = False
                event.accept()
        
        def mouseMoveEvent(event):
            if dialog._mouse_pressed and dialog._mouse_pos is not None:
                dialog.move(event.globalPos() - dialog._mouse_pos)
                event.accept()
        
        dialog.mousePressEvent = mousePressEvent
        dialog.mouseReleaseEvent = mouseReleaseEvent
        dialog.mouseMoveEvent = mouseMoveEvent
        
        dialog.exec_()
        return dialog.result_value

    def create_toolbar(self):
        toolbar = QToolBar("Main Toolbar")
        toolbar.setMovable(False)
        toolbar.setStyleSheet("""
            QToolBar {
                background-color: #000;
                border: none;
                spacing: 10px;
                padding: 5px;
            }
            QToolButton {
                background-color: #1b1b1b;
                color: #aaa;
                padding: 6px 14px;
                border-top-left-radius: 6px;
                border-top-right-radius: 6px;
                margin-right: 2px;
                border: none;
            }
            QToolButton:selected {
                border: 1px solid #17a2b8;
                border-bottom: none;
                color: white;
                background-color: #1b1b1b;
            }
            QToolButton:hover {
                color: #17a2b8;
                background-color: #404040;
            }
        """)
        # Toolbar styling handled by external stylesheet
        
        # Create QToolButton
        file_button = QToolButton()
        file_button.setText("Open")
        file_button.setPopupMode(QToolButton.InstantPopup)  # Menu pops up immediately

        # Make it look like a normal push button (text only, no arrow icon)
        file_button.setToolButtonStyle(Qt.ToolButtonTextOnly)

        # Create dropdown menu
        menu = QMenu()

        self.projects_menu = QMenu("Projects", self)
        self.projects_menu.aboutToShow.connect(self.populate_projects_menu)
        
        menu.addMenu(self.projects_menu)

        # Assign menu to button
        file_button.setMenu(menu)

        toolbar.addWidget(file_button)

        toolbar.addSeparator()

        self.save_action = QAction("Save", self)
        # save_action.setIcon(QIcon("./styles/Icon/save.png"))
        self.save_action.setStatusTip("Save current automation")
        toolbar.addAction(self.save_action)
        self.save_action.setEnabled(False)
        self.save_action.triggered.connect(self.saveoption)
        
        # Update save button state when save_action state changes
        if hasattr(self, 'save_action_btn'):
            self.save_action_btn.setEnabled(self.save_action.isEnabled())

        toolbar.addSeparator()
        
        # help_action = QAction("Help", self)
        # # help_action.setIcon(QIcon("./styles/Icon/help.png"))
        # help_action.setStatusTip("Show help documentation")
        # toolbar.addAction(help_action)
        # Add a stretch spacer so the label stays right-aligned

        spacer = QWidget()
        spacer.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        toolbar.addWidget(spacer)
        
        # Add Project & Task display label
        self.project_task_label = QLabel("No Agent Selected")
        self.project_task_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        self.project_task_label.setMinimumWidth(200)
        toolbar.addWidget(self.project_task_label)
        
        # Initialize tracking variables
        self.selected_project_id = None
        self.selected_project_name = None
        self.selected_task_id = None
        self.selected_task_name = None

        spacer = QWidget()

        spacer.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)

        toolbar.addWidget(spacer)

        # Red Sign Out button
        signout_button = QToolButton()
        signout_button.setText("Sign Out")
        signout_button.setToolTip("Log out and close application")
        signout_button.setProperty('class', 'SignOutButton')
        signout_button.clicked.connect(self.handle_signout)
        toolbar.addWidget(signout_button)

        self.addToolBar(Qt.TopToolBarArea, toolbar)


        # Right-aligned label for resolution/scaling info

        resolutions = get_windows_display_complete()

        if resolutions and isinstance(resolutions,dict):

            physical_res = f"{resolutions['physical']}"

            scaling = f"{resolutions['scaling']}"

        else:

            physical_res=""

            scaling=""



        res_label = QLabel(f"{physical_res}  |  {scaling}")

        res_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)

        toolbar.addWidget(res_label)
        self.addToolBar(toolbar)
       
    def task_selected(self, project_id, taskid):
        """Legacy method - task selection now handled by menu system"""
        print(f"Task selection for project {project_id}, step {taskid} handled by menu system")

    def project_create(self):
        print("create project function : ", self.userid)

        # --- Create Project Dialog ---
        project_dialog = NewItemDialog_project(
            parent=self,
            user_id=self.userid,
            refreshtoken=self.refreshtoken,
            accesstoken=self.accesstoken
        )

        if project_dialog.exec_() == QDialog.Accepted:
            # Refresh project list
            self.populate_projects_menu()
            created_project = project_dialog.created_project

            # Reload projects for this user
            self.load_projects(self.userid)

            # Store the created project info for selection
            self.selected_project_id = created_project['id']
            self.selected_project_name = created_project.get('project_name', 'New Project')

            # --- Create Task Dialog for this project ---
            task_dialog = NewItemDialog_task(
                parent=self,
                projectid=created_project['id'],
                refreshtoken=self.refreshtoken,
                accesstoken=self.accesstoken
            )

            if task_dialog.exec_() == QDialog.Accepted:
                created_task = task_dialog.created_task

                # Store the created task info for selection
                self.selected_task_id = created_task['id']
                self.selected_task_name = created_task.get('task_name', 'New Task')
                
                # Update the display
                self.update_project_task_display()

        
            

    def task_create(self, projectid):
        task_dialog = NewItemDialog_task(
            parent=self,
            projectid=projectid,
            refreshtoken=self.refreshtoken,
            accesstoken=self.accesstoken
        )

        if task_dialog.exec_() == QDialog.Accepted:
            created_task = getattr(task_dialog, "created_task", None)

            if created_task:
                # Store the created task info for selection
                self.selected_task_id = created_task['id']
                self.selected_task_name = created_task.get('task_name', 'New Task')
                
                # Update the display
                self.update_project_task_display()

    def populate_task_menu(self, project_menu, project_id):
        """Populate tasks directly under the project submenu."""
        project_menu.clear()
        
        # Store project name for later use
        self.current_project_name = project_menu.title()  # Get the menu title
        
        url = f"{MAIN_URL}/app/project/{project_id}/tasks/"
        headers = {
            'Content-Type': 'application/json',
            'Cookie': 'sessionid=wjhnaudx6uyfal7iqlok1cyt43glmr0e'
        }

        try:
            response = requests.get(url, headers=headers)
            response.raise_for_status()
            data = response.json()
            tasks = [(task["id"], task["task_name"]) for task in data.get("tasks", [])]

            if not tasks:
                project_menu.addAction("(No tasks found)").setEnabled(False)

            action = QAction("➕ Create Task", self)
            action.setData(project_id)
            action.triggered.connect(partial(self.task_create, project_id))
            project_menu.addAction(action)
            
            for task_id, task_name in tasks:
                action = QAction(task_name, self)
                action.setData((project_id, task_id, task_name))  # Include task name
                action.triggered.connect(partial(self.task_selected_with_names, project_id, task_id, task_name))
                project_menu.addAction(action)

        except requests.RequestException as e:
            print("Error fetching tasks:", e)
            project_menu.addAction("(Error loading tasks)").setEnabled(False)

    def task_selected_with_names(self, project_id, task_id, task_name):
        """Handle task selection with names already available"""
        print("Task selected:", project_id, task_id, task_name)
        
        # Store selections
        self.selected_project_id = project_id
        self.selected_task_id = task_id
        self.selected_project_name = self.current_project_name
        self.selected_task_name = task_name
        
        # Update display
        self.update_project_task_display()
        
        # Load task files and data
        self.handle_task_selection(task_id, task_name)

    def update_project_task_display(self):
        """Update the project and task display in the toolbar"""
        if not hasattr(self, 'selected_project_name') or not self.selected_project_name:
            # No Agent selected
            self.project_icon_label.hide()
            self.project_text_label.setText("No Agent Selected")
            self.task_icon_label.hide()
            self.task_text_label.hide()
            # Disable clear button when no task is selected
            if hasattr(self, 'clear_btn'):
                self.clear_btn.setEnabled(False)
        elif not hasattr(self, 'selected_task_name') or not self.selected_task_name:
            # Project selected but no task
            project_display = self.selected_project_name[:20] + "..." if len(self.selected_project_name) > 20 else self.selected_project_name
            
            # Show project icon and text
            self.project_icon_label.setPixmap(QIcon(resource_path("styles/Icon/folder.png")).pixmap(40, 40))
            self.project_icon_label.show()
            self.project_text_label.setText(f"Project: {project_display}")
            
            # Hide task elements
            self.task_icon_label.hide()
            self.task_text_label.hide()
            # Disable clear button when no task is selected
            if hasattr(self, 'clear_btn'):
                self.clear_btn.setEnabled(False)
        else:
            # Both project and task selected
            project_display = self.selected_project_name[:15] + "..." if len(self.selected_project_name) > 15 else self.selected_project_name
            task_display = self.selected_task_name[:15] + "..." if len(self.selected_task_name) > 15 else self.selected_task_name
            
            # Show project icon and text
            self.project_icon_label.setPixmap(QIcon(resource_path("styles/Icon/folder.png")).pixmap(40, 40))
            self.project_icon_label.show()
            self.project_text_label.setText(f"Agent: {project_display} →")
            
            # Show task icon and text
            self.task_icon_label.setPixmap(QIcon(resource_path("styles/Icon/task.png")).pixmap(40, 40))
            self.task_icon_label.show()
            self.task_text_label.setText(f"Task: {task_display}")
            self.task_text_label.show()
            # Enable clear button when a task is selected
            if hasattr(self, 'clear_btn'):
                self.clear_btn.setEnabled(True)
        
        # Check if process button should be enabled
        self.check_process_button_state()
            
    def populate_projects_menu(self):
        """Populate projects menu with a 'Create Project' option and project submenus."""
        self.projects_menu.clear()

        # Add "Create Project" option at the top
        create_action = QAction("➕ Create Agent Flow", self)
        create_action.triggered.connect(self.project_create)  # define project_create()
        self.projects_menu.addAction(create_action)

        # Divider for clarity
        self.projects_menu.addSeparator()

        url = f"{MAIN_URL}/app/project/user/{self.userid}/projects/"
        headers = {
            'Content-Type': 'application/json',
            'Cookie': 'sessionid=wjhnaudx6uyfal7iqlok1cyt43glmr0e'
        }

        try:
            response = requests.get(url, headers=headers)
            response.raise_for_status()
            projects_output = response.json()
            projects = projects_output['projects']

            if not projects:
                self.projects_menu.addAction("(No Agents found)").setEnabled(False)

            for project in projects:
                # Create submenu for each project
                project_menu = QMenu(project['project_name'], self)

                # Populate tasks when hovering over project
                project_menu.aboutToShow.connect(
                    partial(self.populate_task_menu, project_menu, project['id'])
                )

                self.projects_menu.addMenu(project_menu)

        except requests.RequestException as e:
            print(f"Error fetching projects: {e}")
            self.projects_menu.addAction("(Error loading projects)").setEnabled(False)




    def project_selected(self):
        """When a project is clicked."""
        print("dropdown select : ")
        action = self.sender()
        project_id = action.data()  # hidden id
        project_name = action.text()  # visible value
        QMessageBox.information(self, "Project Selected", f"ID: {project_id}\nName: {project_name}")


    def new_project(self):
        dialog = NewItemDialog(
            parent=self, 
            user_id=self.userid, 
            refreshtoken=self.refreshtoken, 
            accesstoken=self.accesstoken
        )
        
        if dialog.exec_() == QDialog.Accepted:
            # Refresh your project/task menu after creation
            self.populate_projects_menu()

    def create_status_bar_old(self):
        """Create modern status bar"""
        status_bar = QStatusBar()
        # Status bar styling handled by external stylesheet
        status_bar.showMessage("Ready - Welcome to Advanced Web Automation Studio")
        self.setStatusBar(status_bar)

    def load_projects(self, userid):
        """Load projects for the user - now handled by menu system"""
        # This method is called after project creation to refresh the menu
        # The actual project loading is handled by populate_projects_menu()
        print(f"Projects loaded for user {userid} - menu will refresh on next open")

    def on_project_change(self, index):
        """Legacy method - now handled by menu system"""
        print("Project change handled by menu system")

    def project_selected(self, index):
        """Legacy method - now handled by menu system"""
        print("Project selection handled by menu system")
        
    def check_project_selected(self):
        """Legacy method - now handled by menu system"""
        print("Project selection check handled by menu system")

    def load_tasks_for_project(self, project_id):
        """Legacy method - task loading now handled by menu system"""
        print(f"Task loading for project {project_id} handled by menu system")

    def on_task_change(self, index):
        """Legacy method - task change now handled by menu system"""
        print("Task change handled by menu system")
        
    def handle_task_selection(self, task_id, task_name):
        """Handle task selection from menu system"""
        if task_id:
            print(f"Selected Task: {task_name}, ID: {task_id}")
            # You can now pass task_id to your next API call or logic
            try:
                # task_id = 123   # Replace with your task_id
                url = f"{MAIN_URL}/app/project/get-task-files/{task_id}/"

                try:
                    response = requests.get(url)

                    if response.status_code == 200:
                        data = response.json()
                        print("Files List:")
                        if data['files']!=[]:
                            for file_info in data.get("files", []):
                                file_name = file_info['file_name']
                                file_url = file_info['file_url']
                                print(f"Downloading: {file_name} from {file_url}")
                                # Download file
                                response = requests.get(file_url)
                                response.raise_for_status()  # raise error if download fails

                                # Check if it's a zip file (task folder zip)
                                if file_name.endswith('.zip') and 'proj_' in file_name and 'task_' in file_name:
                                    # Save zip file temporarily
                                    temp_zip_path = os.path.join(".", file_name)
                                    with open(temp_zip_path, "wb") as f:
                                        f.write(response.content)
                                    print(f"[OK] Downloaded zip file: {file_name}")
                                    
                                    # Extract zip file to proper folder structure
                                    if hasattr(self, 'selected_project_id') and hasattr(self, 'selected_task_id'):
                                        success = self.extract_task_zip(temp_zip_path, self.selected_project_id, self.selected_task_id)
                                        if success:
                                            print(f"[OK] Extracted and placed all .py files and images from zip")
                                        else:
                                            print(f"[WARN] Failed to extract zip file")
                                    
                                    # Clean up temporary zip file
                                    try:
                                        os.remove(temp_zip_path)
                                        print(f"[OK] Cleaned up temporary zip file")
                                    except:
                                        pass
                                else:
                                    # Save file to appropriate location
                                    if file_name == "execute_code.py":
                                        # Save to code_py directory
                                        os.makedirs("code_py", exist_ok=True)
                                        file_path = os.path.join("code_py", file_name)
                                    elif file_name == "json_xpath.json":
                                        # Save to json_info directory
                                        os.makedirs("json_info", exist_ok=True)
                                        file_path = os.path.join("json_info", file_name)
                                    elif file_name == "citrix_data.json":
                                        # Save to json_info directory
                                        os.makedirs("json_info", exist_ok=True)
                                        file_path = os.path.join("json_info", file_name)
                                    else:
                                        # Save to current directory (recorded_steps.json)
                                        file_path = file_name
                                    with open(file_path, "wb") as f:
                                        f.write(response.content)

                                    print(f"Saved: {file_name}\n")
                        else:
                            # Create empty files if no files exist
                            with open("recorded_steps.json", "w", encoding="utf-8") as fr:
                                json.dump({}, fr)
                            os.makedirs("code_py", exist_ok=True)
                            with open("code_py/execute_code.py", "w", encoding="utf-8") as fr:
                                pass
                            os.makedirs("json_info", exist_ok=True)
                            with open("json_info/json_xpath.json", "w", encoding="utf-8") as fr:
                                json.dump({}, fr)
                    else:
                        print(f"Error: {response.status_code} - {response.text}")

                except requests.exceptions.RequestException as e:
                    print(f"Request failed: {e}")
                
                # from task_classifier import gemini_response
                # self.req_class,self.task_events,self.full_task_info = gemini_response(initial_input)
                file_path = "recorded_steps.json"

                if os.path.exists(file_path) and os.path.getsize(file_path) > 0:
                    with open(file_path, "r", encoding="utf-8") as f:
                        try:
                            loaded = json.load(f)
                        except json.JSONDecodeError:
                            loaded = {}  # fallback
                else:
                    loaded = {}  # fallback

                print(loaded)

                # Load code from execute_code.py and update Code tab
                execute_code_path = "code_py/execute_code.py"
                if os.path.exists(execute_code_path):
                    with open(execute_code_path, "r", encoding="utf-8") as f:
                        code_content = f.read()
                        self.final_code_log = code_content
                        self.code_log = code_content  # Update code_log variable
                        print("[UI] Updated code_log variable")
                        
                        # Update Code tab display
                        if hasattr(self, 'code_display'):
                            self.code_display.initialize_state(code_content)
                            print(f"[OK] Updated Code tab with {len(code_content)} characters")
                        
                        # Auto-clear chat when new task is selected (web mode only)
                        current_mode = getattr(self, 'current_automation_mode', 'web')
                        if current_mode == 'web' and hasattr(self, 'on_new_chat_clicked'):
                            try:
                                self.on_new_chat_clicked()
                                print("[UI] Chat history cleared for new task")
                            except Exception as e:
                                print(f"[WARN] Failed to clear chat history: {e}")
                        
                        # Enable Execute Flow button if code is available
                        if code_content and code_content.strip():
                            if hasattr(self, 'execute_flow_btn'):
                                self.execute_flow_btn.setEnabled(True)
                                print("[UI] ✅ Execute Flow button ENABLED (code available)")
                else:
                    self.final_code_log = ""
                    self.code_log = ""  # Clear code_log if no code available
                    print("[UI] Cleared code_log variable")
                    
                    if hasattr(self, 'code_display'):
                        self.code_display.initialize_state("# No code available")
                    
                    # Auto-clear chat when new task is selected (web mode only)
                    current_mode = getattr(self, 'current_automation_mode', 'web')
                    if current_mode == 'web' and hasattr(self, 'on_new_chat_clicked'):
                        try:
                            self.on_new_chat_clicked()
                            print("[UI] Chat history cleared for new task")
                        except Exception as e:
                            print(f"[WARN] Failed to clear chat history: {e}")
                    
                    # Disable Execute Flow button if no code
                    if hasattr(self, 'execute_flow_btn'):
                        self.execute_flow_btn.setEnabled(False)
                        print("[UI] ❌ Execute Flow button DISABLED (no code)")
                
                # Load XPath data and update XPath Variables tab
                xpath_json_path = "json_info/json_xpath.json"
                if os.path.exists(xpath_json_path):
                    try:
                        with open(xpath_json_path, "r", encoding="utf-8") as f:
                            xpath_data = json.load(f)
                            self.xpath_data = xpath_data
                            # Update XPath Variables tab if it exists
                            if hasattr(self, 'chat_panel') and hasattr(self.chat_panel, 'update_xpath_display'):
                                self.chat_panel.update_xpath_display(xpath_data)
                                print(f"[OK] Updated XPath Variables tab with {len(xpath_data)} variables")
                    except json.JSONDecodeError:
                        self.xpath_data = {}
                        print("[WARN] Invalid XPath JSON file, using empty data")
                else:
                    self.xpath_data = {}
                    print("[INFO] No XPath file found, using empty data")

                steps = loaded.get("steps", [])
                events = loaded.get("events", [])
                combined = loaded.get("combined", [])

                if steps and events and combined:
                    self.req_class = steps
                    self.task_events = events
                    self.full_task_info = combined
                else:
                    self.req_class = []
                    self.task_events = []
                    self.full_task_info = []

                self.update_task_list()

                if hasattr(self, 'task_events') and self.task_events:
                    print(f"[INFO] UI: Auto-selecting Desktop tasks from {len(self.task_events)} steps events")
                    self.task_list.auto_select_desktop_tasks(self.task_events)
                
                self.log_message(f"[OK] Generated {len(self.req_class)} steps successfully")
                self.start_btn.setEnabled(True)
                self.statusBar().showMessage(f"Ready - {len(self.req_class)} steps generated")
                self.generate_code_btn.setEnabled(True)
                # Enable save button after tasks are generated
                if hasattr(self, 'save_action_btn'):
                    self.save_action_btn.setEnabled(True)
            except Exception as e:
                pass
                # QMessageBox.critical(self, "❌ Error", f"Failed to process requirement: {str(e)}")
                # self.log_message(f"❌ Error: {str(e)}")
                # self.statusBar().showMessage("Error occurred during processing")
            finally:
                if hasattr(self, 'process_btn'):
                    self.process_btn.setEnabled(True)
                if hasattr(self, 'save_action_btn'):
                    self.save_action_btn.setEnabled(True)
        else:
            print("No valid task selected.")
            if hasattr(self, 'process_btn'):
                self.process_btn.setEnabled(False)
    # def create_sidebar(self, main_layout,screen_width):
    #     """Create modern sidebar navigation with breakpoint support"""
    #     sidebar = QFrame()
    #     sidebar.setFixedWidth(600)
    #     # sidebar.setFixedWidth(600)

    #     sidebar.setFixedWidth(int(600 * self.scale_factor))

    #     sidebar.setStyleSheet(f"""

    #         QFrame {{

    #             background-color: #252526;

    #             border-right: {int(2 * self.scale_factor)}px solid #555555;

    #             border-radius: 0px;

    #         }}

    #     """)
        
    #     sidebar_layout = QVBoxLayout(sidebar)
    #     sidebar_layout.setSpacing(int(15 * self.scale_factor))

    #     sidebar_layout.setContentsMargins(int(15 * self.scale_factor), int(20 * self.scale_factor), int(15 * self.scale_factor), int(20 * self.scale_factor))
        
    #     # App title
    #     # title_label = QLabel("Droid Studio")
    #     # title_label.setFont(QFont("Arial", int(16 * self.scale_factor), QFont.Bold))

    #     # title_label.setProperty('class', 'TitleLabel')
    #     # style_loader.apply_stylesheet(title_label)
    #     # sidebar_layout.addWidget(title_label)
    #     title_label = QLabel()
    #     title_label.setObjectName("TitleLabel")   # link to QSS
 
    #     from PyQt5.QtGui import QPixmap
    #     pixmap = QPixmap(resource_path("styles/Icon/logos 1.png"))
    #     scaled_pixmap = pixmap.scaled(
    #         int(250 * self.scale_factor),
    #         int(100 * self.scale_factor),
    #         Qt.KeepAspectRatio,
    #         Qt.SmoothTransformation
    #     )
    #     title_label.setPixmap(scaled_pixmap)
 
    #     sidebar_layout.addWidget(title_label)
    #     # Input section
    #     # Input section
    #     input_group = QGroupBox()
    #     input_group.setObjectName("req_input")
    #     input_layout = QVBoxLayout(input_group)
    #     dropdowns_layout = QHBoxLayout()

    #     # First dropdown with label
    #     # Dropdown
    #     layout = QVBoxLayout()

    #     # Label
    #     project_dropdown_label = QLabel("Project:")
    #     project_dropdown_label.setProperty('class', 'DropdownLabel')
    #     layout.addWidget(project_dropdown_label)
    #     self.project_dropdown = QComboBox()
    #     self.project_dropdown.setProperty('class', 'ProjectDropdown')
    #     style_loader.apply_stylesheet(self.project_dropdown)
    #     self.project_dropdown.setStyleSheet(f"""
    #     QComboBox {{
    #         background-color: white;
    #         color: black;
    #         padding: {int(3 * self.scale_factor)}px {int(18 * self.scale_factor)}px {int(3 * self.scale_factor)}px {int(3 * self.scale_factor)}px;
    #         border: {int(1 * self.scale_factor)}px solid gray;
    #         border-radius: {int(3 * self.scale_factor)}px;
    #         min-width: {int(120 * self.scale_factor)}px;
    #     }}
    #     QComboBox::drop-down {{
    #         subcontrol-origin: padding;
    #         subcontrol-position: top right;
    #         width: {int(15 * self.scale_factor)}px;
    #         border-left: {int(1 * self.scale_factor)}px solid gray;
    #         background-color: white;
    #     }}
    #     QAbstractItemView {{
    #         background-color: white;
    #         color: black;
    #         selection-background-color: #0078d4;
    #         selection-color: white;
    #     }}
    # """)
    #     self.project_dropdown.addItem("-- Select Agent Flow --", None)  # placeholder
    #     layout.addWidget(self.project_dropdown)

    #     self.setLayout(layout)

    #     self.project_dropdown.currentIndexChanged.connect(self.on_project_change)
    #     # Second dropdown with label
    #     task_label = QLabel("Task:")
    #     task_label.setProperty('class', 'DropdownLabel')
    #     self.task_dropdown = QComboBox()        
    #     self.task_dropdown.setStyleSheet(f"""
    #     QComboBox {{
    #         background-color: white;
    #         color: black;
    #         padding: {int(3 * self.scale_factor)}px {int(18 * self.scale_factor)}px {int(3 * self.scale_factor)}px {int(3 * self.scale_factor)}px;
    #         border: {int(1 * self.scale_factor)}px solid gray;
    #         border-radius: {int(3 * self.scale_factor)}px;
    #         min-width: {int(120 * self.scale_factor)}px;
    #     }}
    #     QComboBox::drop-down {{
    #         subcontrol-origin: padding;
    #         subcontrol-position: top right;
    #         width: {int(15 * self.scale_factor)}px;
    #         border-left: {int(1 * self.scale_factor)}px solid gray;
    #         background-color: white;
    #     }}
    #     QAbstractItemView {{
    #         background-color: white;
    #         color: black;
    #         selection-background-color: #0078d4;
    #         selection-color: white;
    #     }}
    # """)
    #     self.load_projects(self.userid)  # <- inside create_sidebar()
    #     self.task_dropdown = TaskComboBox(get_project_id=lambda: self.project_dropdown.currentData())
    #     self.task_dropdown.setStyleSheet(f"""
    #     QComboBox {{
    #         background-color: white;
    #         color: black;
    #         padding: {int(3 * self.scale_factor)}px {int(18 * self.scale_factor)}px {int(3 * self.scale_factor)}px {int(3 * self.scale_factor)}px;
    #         border: {int(1 * self.scale_factor)}px solid gray;
    #         border-radius: {int(3 * self.scale_factor)}px;
    #         min-width: {int(120 * self.scale_factor)}px;
    #     }}
    #     QComboBox::drop-down {{
    #         subcontrol-origin: padding;
    #         subcontrol-position: top right;
    #         width: {int(15 * self.scale_factor)}px;
    #         border-left: {int(1 * self.scale_factor)}px solid gray;
    #         background-color: white;
    #     }}
    #     QAbstractItemView {{
    #         background-color: white;
    #         color: black;
    #         selection-background-color: #0078d4;
    #         selection-color: white;
    #     }}
    # """)
    #     self.task_dropdown.addItem("-- Select Task --", None)  # placeholder
    #     self.task_dropdown.currentIndexChanged.connect(self.on_task_change)
    #     # Add labels and combos to the horizontal layout
    #     dropdowns_layout.addWidget(project_dropdown_label)
    #     dropdowns_layout.addWidget(self.project_dropdown)
    #     dropdowns_layout.addSpacing(20)  # optional space between dropdowns
    #     dropdowns_layout.addWidget(task_label)
    #     dropdowns_layout.addWidget(self.task_dropdown)

    #     # Add this horizontal layout to your main input layout
    #     input_layout.addLayout(dropdowns_layout)
    #     project_dropdown_label.hide()
    #     self.project_dropdown.hide()
    #     task_label.hide()
    #     self.task_dropdown.hide()
    #     # Input method selection
    #     method_layout = QHBoxLayout()
    #     self.manual_radio = QRadioButton("📝 Manual Input")
    #     self.file_radio = QRadioButton("📁 File Upload (.pdf/.txt/.mp4/.doc/.docx)")
    #     self.manual_radio.setChecked(True)  # Default to manual input
    #     # Radio button styling handled by external stylesheet
        
    #     # Connect radio button signals
    #     self.manual_radio.toggled.connect(self.on_input_method_changed)
    #     self.file_radio.toggled.connect(self.on_input_method_changed)
        
    #     method_layout.addWidget(self.manual_radio)
    #     method_layout.addWidget(self.file_radio)
    #     input_layout.addLayout(method_layout)
        
    #     # Manual input section
    #     self.requirement_input = QTextEdit()
    #     self.requirement_input.setPlaceholderText(" Say something i can get it done for you")
    #     self.requirement_input.setMaximumHeight(int(120 * self.scale_factor))

    #     self.requirement_input.setFont(QFont("Segoe UI", int(13 * self.scale_factor)))
    #     input_layout.addWidget(self.requirement_input)
        
    #     # File upload section
    #     self.file_upload_layout = QHBoxLayout()
    #     self.file_path_label = QLabel("No file selected")
    #     self.file_path_label.setProperty('class', 'FilePathDefault')
    #     style_loader.apply_stylesheet(self.file_path_label)
    #     self.browse_btn = button_style.ModernButton("📁 Browse File", "#9C27B0", "#7B1FA2")
    #     self.browse_btn.clicked.connect(self.browse_file)
    #     self.browse_btn.setVisible(False)
        
    #     self.file_upload_layout.addWidget(self.file_path_label)
    #     self.file_upload_layout.addWidget(self.browse_btn)
    #     input_layout.addLayout(self.file_upload_layout)
        
    #     # Hide file upload components initially
    #     self.file_path_label.setVisible(False)
        
    #     self.process_btn = button_style.ModernButton("🔄 Process Requirements", "#4CAF50", "#45a049")
    #     self.process_btn.clicked.connect(self.process_requirement)
    #     self.process_btn.setEnabled(False)
    #     input_layout.addWidget(self.process_btn)
        
    #     sidebar_layout.addWidget(input_group)
        
    #     # Agent GIF Display section
    #     agent_group = QGroupBox("🤖 Droid Agent")
    #     agent_layout = QVBoxLayout(agent_group)

    #     # Create QLabel for GIF display
    #     self.agent_gif_label = QLabel()
    #     self.agent_gif_label.setAlignment(Qt.AlignCenter)  # Center the content
    #     self.agent_gif_label.setFixedHeight(int(200 * self.scale_factor))

    #     self.agent_gif_label.setScaledContents(True)

    #     self.agent_gif_label.setProperty('class', 'AgentGifLabel')
    #     style_loader.apply_stylesheet(self.agent_gif_label)
    #     # Load and display the GIF/image
    #     try:
    #         from PyQt5.QtGui import QMovie, QPixmap
    #         self.agent_movie = QMovie(resource_path("styles/Icon/Agent_2.png"))
    #         if self.agent_movie.isValid():
    #             # Scale the movie to desired size
    #             self.agent_movie.setScaledSize(QSize(int(180 * self.scale_factor), int(150 * self.scale_factor)))
    #             self.agent_gif_label.setMovie(self.agent_movie)
    #             self.agent_movie.start()
    #         else:
    #             # Fallback to static image
    #             pixmap = QPixmap(resource_path("styles/Icon/Agent_2.png"))
    #             if not pixmap.isNull():
    #                 scaled_pixmap = pixmap.scaled(int(180 * self.scale_factor), int(150 * self.scale_factor), Qt.KeepAspectRatio, Qt.SmoothTransformation)
    #                 self.agent_gif_label.setPixmap(scaled_pixmap)
    #     except Exception as e:
    #         self.agent_gif_label.setText("🤖\n\nDroid Agent\n\n(Loading error)")

    #     # Add the label to layout with center alignment
    #     agent_layout.addWidget(self.agent_gif_label, 0, Qt.AlignCenter)
        
    #     # Control buttons
    #     control_layout = QHBoxLayout()
        
    #     self.verify_mode_btn = verify_mode_widget.VerifyModeButton()
    #     self.verify_mode_btn.setToolTip("Enable to verify each task execution")
    #     self.verify_mode_btn.clicked.connect(self.toggle_verify_mode)
    #     control_layout.addWidget(self.verify_mode_btn)
        
    #     self.start_btn = button_style.ModernButton("▶️ Start Processing", "#2196F3", "#1976D2")
    #     self.start_btn.clicked.connect(self.start_processing)
    #     self.start_btn.setEnabled(False)
    #     control_layout.addWidget(self.start_btn)
        
    #     agent_layout.addLayout(control_layout)
        
    #     # Progress bar
    #     self.progress_bar = QProgressBar()
    #     self.progress_bar.setVisible(False)
    #     self.progress_bar.setProperty('class', 'MainProgressBar')
    #     style_loader.apply_stylesheet(self.progress_bar)
    #     agent_layout.addWidget(self.progress_bar)
        
    #     sidebar_layout.addWidget(agent_group)
        
    #     # Actions section
    #     actions_group = QGroupBox("⚡ Actions")
    #     actions_layout = QVBoxLayout(actions_group)
        
    #     self.generate_code_btn = button_style.ModernButton("🔧 Generate Final Code", "#FF9800", "#F57C00")
    #     self.generate_code_btn.clicked.connect(self.generate_final_code)
    #     self.generate_code_btn.setEnabled(False)
    #     actions_layout.addWidget(self.generate_code_btn)
        
    #     clear_btn = button_style.ModernButton("🗑️ Clear All", "#f44336", "#d32f2f")
    #     clear_btn.clicked.connect(self.clear_all)
    #     actions_layout.addWidget(clear_btn)
        
    #     sidebar_layout.addWidget(actions_group)
    #     sidebar_layout.addStretch()
        
    #     main_layout.addWidget(sidebar)

    def check_process_button_state(self):
        """Enable process button only when both project and task are selected"""
        has_project = hasattr(self, 'selected_project_name') and self.selected_project_name
        has_task = hasattr(self, 'selected_task_name') and self.selected_task_name

        is_enabled = bool(has_project and has_task)    
        self.process_btn.setEnabled(is_enabled)

    def create_agent_section_with_processing(self, sidebar_layout):
        """
        Create agent section that can switch between normal and processing states.
        Title/buttons stay the same – only the GIF and progress bar change.
        """

        # === Container ===
        self.agent_container = QFrame()
        self.agent_container.setFixedHeight(int(350 * self.scale_factor))
        container_layout = QVBoxLayout(self.agent_container)
        container_layout.setContentsMargins(0, 0, 0, 0)
        container_layout.setSpacing(0)

        # === PROCESSING WIDGET (replaces the old agent group) ===
        self.processing_widget = DroidAgentProcessingWidget(self.scale_factor)
        
        # Connect the close button signal
        # self.processing_widget.processing_stopped.connect(self.closeEvent)
        
        # Add the processing widget to container
        container_layout.addWidget(self.processing_widget)

        # === Control buttons (verify + start) - positioned below the widget ===
        control_frame = QFrame()
        control_frame.setFixedHeight(int(60 * self.scale_factor))
        control_frame.setStyleSheet("background: transparent;")
        
        control_layout = QHBoxLayout(control_frame)
        control_layout.setContentsMargins(
            int(10 * self.scale_factor), int(10 * self.scale_factor),
            int(10 * self.scale_factor), int(10 * self.scale_factor)
        )

        # Verify mode removed - no longer needed

        # ===== Generate Code Button (renamed from Start Processing) =====
        self.start_btn = QPushButton("⚙️ Generate Code")
        
        self.start_btn.setStyleSheet(f"""
            QPushButton {{
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #008AB3, stop:1 #005B7F);
                color: white;
                font-family:{self.asen_font_family};
                font-weight: bold;
                border-radius: {int(10 * self.scale_factor)}px;
                font-size: {int(16 * self.scale_factor)}px;
                border: none;
                padding: {int(10 * self.scale_factor)}px;
            }}
            QPushButton:hover {{
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #22C4FF, stop:1 #0077A6);
            }}
            QPushButton:disabled {{
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #606060, stop:1 #404040);
                color: #CCCCCC;
            }}
        """)
        
        # Initialize media player for sound
        self.click_sound_player = QMediaPlayer()
        sound_path = resource_path("styles\\sound\\ipad_click-99325.mp3")
        self.click_sound_player.setMedia(QMediaContent(QUrl.fromLocalFile(sound_path)))
        
        # Connect button click to both sound and processing
        self.start_btn.clicked.connect(self.play_click_sound)
        self.start_btn.clicked.connect(self.delete_existing_task_files)
        self.start_btn.clicked.connect(self.start_processing)
        
        # 🔹 Fix alignment by setting equal height
        button_height = int(46 * self.scale_factor)
        self.start_btn.setFixedHeight(button_height)
        
        # ===== Execute Flow Button =====
        self.execute_flow_btn = QPushButton("▶️ Execute Flow")
        
        self.execute_flow_btn.setStyleSheet(f"""
            QPushButton {{
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #4CAF50, stop:1 #388E3C);
                color: white;
                font-family:{self.asen_font_family};
                font-weight: bold;
                border-radius: {int(10 * self.scale_factor)}px;
                font-size: {int(16 * self.scale_factor)}px;
                border: none;
                padding: {int(10 * self.scale_factor)}px;
            }}
            QPushButton:hover {{
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #66BB6A, stop:1 #43A047);
            }}
            QPushButton:disabled {{
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #606060, stop:1 #404040);
                color: #CCCCCC;
            }}
        """)
        
        # Connect button click to execute code
        self.execute_flow_btn.clicked.connect(self.play_click_sound)
        self.execute_flow_btn.clicked.connect(self.execute_code)
        self.execute_flow_btn.setFixedHeight(button_height)
        self.execute_flow_btn.setEnabled(False)

        # ===== STOP Button (sidebar) =====
        self.stop_flow_btn = QPushButton(" STOP")
        self.stop_flow_btn.setStyleSheet(f"""
            QPushButton {{
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #C62828, stop:1 #B71C1C);
                color: white;
                font-family:{self.asen_font_family};
                font-weight: bold;
                border-radius: {int(10 * self.scale_factor)}px;
                font-size: {int(16 * self.scale_factor)}px;
                border: none;
                padding: {int(10 * self.scale_factor)}px;
            }}
            QPushButton:hover {{
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #E53935, stop:1 #D32F2F);
            }}
            QPushButton:disabled {{
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #606060, stop:1 #404040);
                color: #CCCCCC;
            }}
        """)
        self.stop_flow_btn.clicked.connect(self.stop_execution)
        self.stop_flow_btn.setFixedHeight(button_height)
        self.stop_flow_btn.setEnabled(False)

        # Add both buttons horizontally
        control_layout.addWidget(self.start_btn)
        control_layout.addSpacing(int(10 * self.scale_factor))
        control_layout.addWidget(self.execute_flow_btn)
        control_layout.addSpacing(int(10 * self.scale_factor))
        control_layout.addWidget(self.stop_flow_btn)
        control_layout.addStretch()
        
        # Add control frame to container
        container_layout.addWidget(control_frame)

        # Add to sidebar
        sidebar_layout.addWidget(self.agent_container)

        return self.agent_container


    def play_click_sound(self):
        """Play the click sound when button is clicked."""
        self.click_sound_player.setVolume(100)  # Set volume to 100%
        self.click_sound_player.play()
    def create_sidebar(self, main_layout, screen_width):
        sidebar = QFrame()
        sidebar.setFixedWidth(int(500 * self.scale_factor))
        sidebar.setStyleSheet(f"""
            QFrame {{
                background-color: #1a1a1a;
                border-right: {int(2 * self.scale_factor)}px solid #333333;
                border-radius: 0px;
            }}
        """)
        
        sidebar_layout = QVBoxLayout(sidebar)
        sidebar_layout.setSpacing(int(15 * self.scale_factor))
        sidebar_layout.setContentsMargins(int(15 * self.scale_factor), int(20 * self.scale_factor), int(15 * self.scale_factor), int(20 * self.scale_factor))
        
        # ===== Logo =====
        title_label = QLabel()
        pixmap = QPixmap(resource_path("styles/Icon/logos.png"))
        scaled_pixmap = pixmap.scaled(
            int(250 * self.scale_factor),
            int(100 * self.scale_factor),
            Qt.KeepAspectRatio,
            Qt.SmoothTransformation
        )
        title_label.setPixmap(scaled_pixmap)
        sidebar_layout.addWidget(title_label)

        # ===== Input container =====
        input_container = QFrame()
        input_container.setObjectName("InputContainer")
        input_layout = QVBoxLayout(input_container)
        input_layout.setSpacing(0)
        input_layout.setContentsMargins(0, 0, 0, 0)

        # ===== Tabs (Manual / File Upload) =====
        method_layout = QHBoxLayout()
        method_layout.setSpacing(0)
        method_layout.setContentsMargins(0, 0, 0, 0)

        self.manual_radio = QPushButton("Manual input")
        self.manual_radio.setObjectName("ManualRadio")
        self.manual_radio.setCheckable(True)
        self.manual_radio.setChecked(True)
        self.manual_radio.setFixedHeight(int(40 * self.scale_factor))

        self.file_radio = QPushButton("File upload")
        self.file_radio.setObjectName("FileRadio")
        self.file_radio.setCheckable(True)
        self.file_radio.setFixedHeight(int(40 * self.scale_factor))

        method_layout.addWidget(self.manual_radio)
        method_layout.addWidget(self.file_radio)

        # ===== Manual Input Section with Voice Integration =====
        input_with_mic_container = QFrame()
        input_with_mic_container.setFixedHeight(int(205 * self.scale_factor))
        
        # Text input with padding for microphone button
        self.requirement_input = QTextEdit(input_with_mic_container)
        self.requirement_input.setPlaceholderText(" Say something i can get it done for you (or click mic to speak)")
        self.requirement_input.setGeometry(0, int(5 * self.scale_factor), input_with_mic_container.width(), int(200 * self.scale_factor))
        self.requirement_input.setStyleSheet(f"""
            QTextEdit {{
                background-color: #2a2a2a;
                color: #cccccc;
                border: {int(1 * self.scale_factor)}px solid #404040;
                border-radius: {int(6 * self.scale_factor)}px;
                padding: {int(12 * self.scale_factor)}px {int(50 * self.scale_factor)}px {int(12 * self.scale_factor)}px {int(12 * self.scale_factor)}px;
                font-family: {self.asen_font_family}; 
                font-size: {int(18 * self.scale_factor)}px;
            }}
            QTextEdit:focus {{
                border-color: #0ea5e9;
            }}
            QScrollBar:vertical {{
                background: #1e1e1e;
                width: 10px;
                margin: 0px;
                border-radius: 5px;
            }}
            QScrollBar::handle:vertical {{
                background: #474747;
                border-radius: 5px;
                min-height: 20px;
            }}
            QScrollBar::add-line:vertical,
            QScrollBar::sub-line:vertical {{
                background: none;
                border: none;
                height: 0px;
            }}
        """)

        # Create microphone button positioned inside the text input
        self.mic_button = QPushButton(input_with_mic_container)
        mic_size = int(32 * self.scale_factor)
        self.mic_button.setFixedSize(mic_size, mic_size)
        self.mic_button.setToolTip("Click to record voice input")
        
        # Try to set microphone icon, fallback to emoji
        try:
            self.mic_button.setIcon(QIcon(resource_path("styles/Icon/microphone.png")))
            self.mic_button.setIconSize(QSize(int(18 * self.scale_factor), int(18 * self.scale_factor)))
        except:
            self.mic_button.setText("🎤")
            self.mic_button.setStyleSheet(f"""
                QPushButton {{
                    font-size: {int(16 * self.scale_factor)}px;
                }}
            """)
        
        # Position microphone button at bottom right inside text input
        def position_mic_button():
            input_rect = self.requirement_input.geometry()
            button_x = input_rect.width() - mic_size - int(8 * self.scale_factor)
            button_y = input_rect.height() - mic_size - int(8 * self.scale_factor) + int(5 * self.scale_factor)
            self.mic_button.move(button_x, button_y)
        
        # Connect resize event to reposition button
        original_resize = self.requirement_input.resizeEvent
        def resize_with_mic_positioning(event):
            original_resize(event)
            position_mic_button()
        self.requirement_input.resizeEvent = resize_with_mic_positioning
        
        # Initial positioning
        def setup_mic_position():
            input_with_mic_container.setFixedWidth(int(470 * self.scale_factor))
            self.requirement_input.setGeometry(0, int(5 * self.scale_factor), int(470 * self.scale_factor), int(200 * self.scale_factor))
            position_mic_button()
        
        # Use QTimer to position after layout is complete
        from PyQt5.QtCore import QTimer
        QTimer.singleShot(0, setup_mic_position)
        
        # Microphone button styling - floating inside text input
        self.mic_button.setStyleSheet(f"""
            QPushButton {{
                background-color: rgba(42, 42, 42, 220);
                border: {int(1 * self.scale_factor)}px solid #404040;
                border-radius: {int(16 * self.scale_factor)}px;
                padding: {int(4 * self.scale_factor)}px;
            }}
            QPushButton:hover {{
                background-color: rgba(58, 58, 58, 240);
                border-color: #0ea5e9;
            }}
            QPushButton:pressed {{
                background-color: rgba(74, 74, 74, 240);
            }}
            QPushButton[recording="true"] {{
                background-color: rgba(220, 38, 38, 240);
                border-color: #ef4444;
            }}
            QPushButton[recording="true"]:hover {{
                background-color: rgba(185, 28, 28, 240);
            }}
        """)

        # Voice status label
        self.voice_status_label = QLabel("")
        self.voice_status_label.setStyleSheet(f"""
            QLabel {{
                color: #888888;
                font-size: {int(12 * self.scale_factor)}px;
                padding: {int(2 * self.scale_factor)}px {int(5 * self.scale_factor)}px;
                margin-left: {int(12 * self.scale_factor)}px;
            }}
        """)
        self.voice_status_label.hide()

        # ===== File Upload Section =====
        self.file_upload_frame = QFrame()
        upload_layout = QVBoxLayout(self.file_upload_frame)
        upload_layout.setSpacing(10)

        # Drop Zone
        self.drop_zone = DropZoneLabel() 
        self.drop_zone.setAlignment(Qt.AlignCenter)
        self.drop_zone.setFixedSize(100, 100)
        self.drop_zone.setText("""
            <div style="text-align: center; color: #575858;">
                <img src="styles/Icon/image (5).png" width="24" height="24"><br>
                <span style="font-size:17px; font-weight:500;">Drop</span>
            </div>
        """)
        self.drop_zone.setStyleSheet("""
            QLabel {
                border: 2px dashed #575858;
                border-radius: 8px;
                background-color: #111111;
            }
        """)
        self.drop_zone.file_dropped.connect(self.handle_file_drop)

        # Browse button
        self.browse_btn = QPushButton(" Browse")
        self.browse_btn.setObjectName("BrowseButton")
        self.browse_btn.setIcon(QIcon(resource_path("styles/Icon/image (3).png")))
        self.browse_btn.setIconSize(QSize(24, 24))
        self.browse_btn.setFixedSize(140, 45)
        self.browse_btn.clicked.connect(self.browse_file)

        # File name label with remove button
        file_label_layout = QHBoxLayout()
        self.file_path_label = QLabel()
        self.file_path_label.setStyleSheet("""
            QLabel {
                color: white;
                font-size: 13px;
                padding: 5px;
            }
        """)
        self.file_path_label.setWordWrap(True)
        self.file_path_label.setText("")
        
        # Remove file button
        self.file_remove_btn = QPushButton("✕")
        self.file_remove_btn.setFixedSize(24, 24)
        self.file_remove_btn.setToolTip("Remove attached file")
        self.file_remove_btn.setStyleSheet("""
            QPushButton {
                background: rgba(220, 53, 69, 0.8);
                color: white;
                border: none;
                border-radius: 12px;
                font-size: 13px;
                font-weight: bold;
                padding: 0px;
            }
            QPushButton:hover {
                background: rgba(220, 53, 69, 1.0);
            }
            QPushButton:pressed {
                background: rgba(200, 35, 51, 1.0);
            }
        """)
        self.file_remove_btn.clicked.connect(self.remove_selected_file)
        self.file_remove_btn.hide()  # Initially hidden
        
        file_label_layout.addWidget(self.file_path_label)
        file_label_layout.addWidget(self.file_remove_btn)
        file_label_layout.addStretch()
        
        # Label for displaying accepted file types (.DOC / .PDF / .MP4)
        self.file_types_label = QLabel(".DOC / .PDF / .MP4")
        self.file_types_label.setStyleSheet("color: #575858; font-size: 13px;")
        # The doc_type.png image label
        self.file_types_label = QLabel(".DOC / .PDF / .MP4")
        self.file_types_label.setStyleSheet("""
            QLabel {
                font-family: 'Asen Pro'; /* Ensure this font is available on the system */
                font-weight: 600;
                font-size: 14px;
                line-height: 17px; /* Line height is usually tied to font-size in Qt, but can be influenced by padding */
                color: #575858;
                /* Absolute positioning is generally avoided in Qt layouts.
                We'll achieve the position using spacers and alignment within the layout. */
            }
        """)
        # We'll set the alignment for this label directly
        self.file_types_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)

        # Arrange drop + browse horizontally
        drop_browse_layout = QHBoxLayout()
        drop_browse_layout.addWidget(self.drop_zone)
        drop_browse_layout.addWidget(self.browse_btn)

        file_info_layout = QHBoxLayout()
        file_info_layout.addStretch() # Push content to the right
        # Add the file types label directly
        file_info_layout.addWidget(self.file_types_label)

        upload_layout.addLayout(drop_browse_layout)
        upload_layout.addSpacing(15) # Add some space between drop/browse and the file info
        upload_layout.addLayout(file_info_layout) # Add the layout with file types text
        upload_layout.addLayout(file_label_layout)

        # ===== Toggle functions =====
        def toggle_to_file():
            self.file_radio.setChecked(True)
            self.manual_radio.setChecked(False)
            input_with_mic_container.setVisible(False)
            self.voice_status_label.setVisible(False)
            self.file_upload_frame.setVisible(True)
            self.process_btn.setText("  Upload && Process")
            self.process_btn.setIcon(QIcon(resource_path("styles/Icon/Process.png")))
            self.process_btn.setCursor(Qt.PointingHandCursor)

        def toggle_to_manual():
            self.manual_radio.setChecked(True)
            self.file_radio.setChecked(False)
            input_with_mic_container.setVisible(True)
            self.file_upload_frame.setVisible(False)
            self.process_btn.setText("  Enter && process")
            self.process_btn.setIcon(QIcon(resource_path("styles/Icon/Process.png")))
            self.process_btn.setCursor(Qt.PointingHandCursor)

        self.manual_radio.clicked.connect(toggle_to_manual)
        self.file_radio.clicked.connect(toggle_to_file)

        # Add all to input container
        input_layout.addLayout(method_layout)
        input_layout.addWidget(input_with_mic_container)
        input_layout.addWidget(self.voice_status_label)
        input_layout.addWidget(self.file_upload_frame)

        # ===== Initialize Voice Integration =====
        self._initialize_voice_integration()

        # ===== Process Button =====
        # ===== Process Button =====
        self.process_btn = QPushButton(" Enter && process")
        self.process_btn.setObjectName("ProcessButton")
        self.process_btn.setFixedSize(130, 35)   # same size as refresh button
        self.process_btn.setIcon(QIcon(resource_path("styles/Icon/Process.png")))  # dummy path for process icon
        self.process_btn.clicked.connect(lambda: (self.player_click.play(), self.process_requirement()))

        self.process_btn.setEnabled(False)  # True keep enabled initially

        # Apply same style as refresh button
        self.process_btn.setStyleSheet("""
    QPushButton {
        background: qlineargradient(x1:0, y1:1, x2:0, y2:0,
                                    stop:0 #005B7F, stop:1 #008AB3);
        border-radius: 10px;
        color: #FFFFFF;
        font-family: 'Asen Pro', sans-serif;
        font-weight: 600;
        font-size: 16px;
        letter-spacing: 0.05em;
        text-align: center;   /* ✅ center text */
        border: none;
    }
    QPushButton:hover {
        background: qlineargradient(x1:0, y1:1, x2:0, y2:0,
                                    stop:0 #006B8F, stop:1 #009AC3);
    }
    QPushButton:pressed {
        background: qlineargradient(x1:0, y1:1, x2:0, y2:0,
                                    stop:0 #004B6F, stop:1 #007A93);
    }
""")

        
        sidebar_layout.addWidget(input_container)
        
        # Create button container for process button
        button_container = QHBoxLayout()
        
        button_container.addWidget(self.process_btn)
        
        # Create a widget to hold the button layout
        button_widget = QWidget()
        button_widget.setLayout(button_container)
        
        sidebar_layout.addWidget(button_widget, alignment=Qt.AlignRight)
        
        # Now call toggle_to_manual after skeleton button is created
        toggle_to_manual()
    

        # Create a plain container (no title text)
        self.create_agent_section_with_processing(sidebar_layout)
        self.processing_widget.start_processing()
        
        # Actions section
        actions_group = QGroupBox("Actions")
        actions_group.setFixedHeight(int(160 * self.scale_factor))
        actions_group.setStyleSheet(f"""
            QGroupBox {{
                background-color: #000000;
                border: none;
                border-radius: {int(20 * self.scale_factor)}px;
                margin: {int(10 * self.scale_factor)}px 0px;
                font-family: {self.asen_font_family};
                font-weight: 600;
                font-size: {int(16 * self.scale_factor)}px;
                color: white;
                padding-top: {int(20 * self.scale_factor)}px;
            }}
            QGroupBox::title {{
                subcontrol-origin: margin;
                left: {int(20 * self.scale_factor)}px;
                top: {int(20 * self.scale_factor)}px;
            }}
        """)

        actions_layout = QHBoxLayout(actions_group)
        actions_layout.setContentsMargins(
            int(25 * self.scale_factor),
            int(50 * self.scale_factor),
            int(25 * self.scale_factor),
            int(30 * self.scale_factor)
        )
        actions_layout.setSpacing(int(30 * self.scale_factor))

        self.player_click = QMediaPlayer()
        self.player_click.setMedia(QMediaContent(
            QUrl.fromLocalFile(resource_path("styles/sound/ipad_click-99325.mp3"))
        ))

        self.player_confirm = QMediaPlayer()
        self.player_confirm.setMedia(QMediaContent(
            QUrl.fromLocalFile(resource_path("styles\\sound\\fh_paper_swipe_surface2_short_01wav-14432.mp3"))
        ))
    
        self.clear_btn = button_style.ModernButton("Clear all", "#f44336", "#d32f2f")
        self.clear_btn.setFixedSize(155, 35)

        # Add subtle shadow for depth
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(20)
        shadow.setColor(QColor(255, 70, 70, 140))
        shadow.setOffset(0, 3)
        self.clear_btn.setGraphicsEffect(shadow)

        # Enhanced red gradient + hover glow + pressed tone
        self.clear_btn.setStyleSheet("""
        QPushButton {
            background-color: qlineargradient(
                x1:0, y1:0, x2:0, y2:1,
                stop:0 #FF4B4B, stop:1 #B62026
            );
            border: none;
            border-radius: 10px;
            color: white;
            font-size: 16px;
            font-weight: 600;
            letter-spacing: 0.05em;
            padding: 6px 12px;
            text-align: center;
            transition: all 0.2s ease-in-out;
        }
        QPushButton:hover {
            background-color: qlineargradient(
                x1:0, y1:0, x2:0, y2:1,
                stop:0 #FF7070, stop:1 #E42222
            );
            box-shadow: 0px 0px 10px rgba(255, 80, 80, 0.6);
            transform: scale(1.05);
        }
        QPushButton:pressed {
            background-color: qlineargradient(
                x1:0, y1:0, x2:0, y2:1,
                stop:0 #B71C1C, stop:1 #7F0000
            );
            transform: scale(0.97);
        }
        QPushButton:disabled {
            background-color: qlineargradient(
                x1:0, y1:0, x2:0, y2:1,
                stop:0 #f44336, stop:1 #d32f2f
            );
            color: white;
            opacity: 0.6;
        }
    """)

        # clear_btn.setCursor(Qt.PointingHandCursor)
        self.clear_btn.setIcon(QIcon(resource_path("Icon\\image (9).png")))
        self.clear_btn.setIconSize(QSize(24, 24))
        # when clicking the button, play click sound first
        
        self.clear_btn.clicked.connect(self.on_clear_click)
        # Initially disable the clear all button until a task is selected
        self.clear_btn.setEnabled(False)
        actions_layout.addWidget(self.clear_btn)
    

        self.generate_code_btn = button_style.ModernButton("Publish code", "#4CAF50", "#388E3C")
        self.generate_code_btn.setFixedSize(154, 35)
        self.generate_code_btn.setStyleSheet("""
            QPushButton {
                background-color: qlineargradient(
                    x1:0, y1:0, x2:0, y2:1,
                    stop:0 #5A9310, stop:1 #94F219
                );
                border: none;
                border-radius: 10px;
                color: white;
                font-size: 16px;
                font-weight: 600;
                letter-spacing: 0.05em;
                padding: 6px 12px;
                text-align: center;
            }
            QPushButton:hover {
                background-color: qlineargradient(
                    x1:0, y1:0, x2:0, y2:1,
                    stop:0 #6FBF13, stop:1 #A8FF3A
                );
            }
            QPushButton:disabled {
                background-color: qlineargradient(
                    x1:0, y1:0, x2:0, y2:1,
                    stop:0 #5A9310, stop:1 #94F219
                );
                color: white;
            }
        """)
   
        # self.generate_code_btn.setCursor(Qt.PointingHandCursor)
        self.generate_code_btn.setIcon(QIcon(resource_path("styles/Icon/image (8).png")))
        self.generate_code_btn.setIconSize(QSize(24, 24))
        self.generate_code_btn.clicked.connect(lambda: (self.player_click.stop(), self.player_click.play(), self.generate_final_code()))

        self.generate_code_btn.setEnabled(True)
        
        actions_layout.addWidget(self.generate_code_btn)

        sidebar_layout.addWidget(actions_group)
        sidebar_layout.addStretch()

        main_layout.addWidget(sidebar)

        #==================================gemini button==========================================

        self.gemini_btn = QPushButton(input_with_mic_container)  # parent = input container
        self.gemini_btn.setFixedSize(int(28 * self.scale_factor), int(28 * self.scale_factor))
        self.gemini_btn.setToolTip("Restructure prompt")

        # Set golden star icon or fallback to emoji
        try:
            self.gemini_btn.setIcon(QIcon(resource_path("styles/Icon/gemini_icon.png")))  # golden star
            self.gemini_btn.setIconSize(QSize(int(82 * self.scale_factor), int(82 * self.scale_factor)))
        except:
            self.gemini_btn.setText("✨")
            self.gemini_btn.setStyleSheet(f"font-size: {int(16 * self.scale_factor)}px; color: gold;")

        # Button style
        self.gemini_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: rgba(42, 42, 42, 220);
                border: {int(1 * self.scale_factor)}px solid #404040;
                border-radius: {int(14 * self.scale_factor)}px;
                padding: {int(4 * self.scale_factor)}px;
                color: gold;
            }}
            QPushButton:hover {{
                background-color: rgba(250, 204, 21, 0.2);
            }}
            QPushButton:pressed {{
                background-color: rgba(250, 204, 21, 0.3);
            }}
        """)



        # Function to position the Gemini button at bottom-left inside text input
        def position_gemini_btn():
            input_rect = self.requirement_input.geometry()
            x = int(8 * self.scale_factor)  # left padding
            y = input_rect.height() - self.gemini_btn.height() - int(8 * self.scale_factor) + int(5 * self.scale_factor)
            self.gemini_btn.move(x, y)

        # Connect resize event to reposition Gemini button
        original_resize_input = self.requirement_input.resizeEvent
        def resize_with_gemini(event):
            if original_resize_input:
                original_resize_input(event)
            position_gemini_btn()
        self.requirement_input.resizeEvent = resize_with_gemini
        self.gemini_btn.clicked.connect(self.handle_gemini_click)
    
    def handle_file_drop(self, file_path):
        """Handle the dropped file"""
        if not os.path.exists(file_path):
            return
        
        # Get file name and extension
        file_name = os.path.basename(file_path)
        _, ext = os.path.splitext(file_path)
        
        # Validate file type
        allowed_extensions = ['.doc', '.docx', '.pdf', '.mp4', '.txt', '.xlsx', '.xls']
        if ext.lower() not in allowed_extensions:
            # Show error message
            from PyQt5.QtWidgets import QMessageBox
            QMessageBox.warning(
                self, 
                "Invalid File Type", 
                f"Please drop only .DOC, .DOCX, .PDF, .MP4, .TXT, .XLSX or .XLS files.\nYou dropped: {ext}"
            )
            return
        
        # Store the file path
        self.selected_file_path = file_path
        
        # Update the file label to show selected file
        self.file_path_label.setText(f"📎 {file_name}")
        self.file_path_label.setStyleSheet("""
            QLabel {
                color: #0ea5e9;
                font-size: 13px;
                padding: 5px;
            }
        """)
        
        # Show the remove button
        self.file_remove_btn.show()
        
        # Enable the process button
        self.process_btn.setEnabled(True)
        
        # Optional: Play a sound effect
        if hasattr(self, 'player_confirm'):
            self.player_confirm.play()


    def remove_selected_file(self):
        """Remove the selected file"""
        self.selected_file_path = None
        self.file_path_label.setText("")
        self.file_remove_btn.hide()
        
        # Disable process button if no file
        if self.file_radio.isChecked():
            self.process_btn.setEnabled(False)
    # gemini responds function
    def handle_gemini_click(self):
        user_text = self.requirement_input.toPlainText().strip()
        if not user_text:
            self.voice_status_label.setText("Please enter some text first")
            self.voice_status_label.show()
            return

        self.voice_status_label.setText("Prompt tunning...")
        self.voice_status_label.show()

        # Start worker thread
        self.gemini_worker = GeminiWorker(user_text)
        self.gemini_worker.finished.connect(self.update_prompt_after_gemini)
        self.gemini_worker.start()

    def update_prompt_after_gemini(self, structured_prompt):
        self.requirement_input.setPlainText(structured_prompt)
        self.voice_status_label.setText("Prompt tunned ✅")


            #==========================================
    def on_clear_click(self):
        """Play click sound first, then open confirmation."""
        self.player_click.stop()
        self.player_click.play()
        self.clear_all()
    
    def _initialize_voice_integration(self):
        """Initialize voice integration with Gemini API."""
        try:
                    
            # Get API key
            GEMINI_API_KEY = getattr(config, 'API_KEY', None)
            
            if not GEMINI_API_KEY:
                print("[WARN] Warning: No Gemini API key found in config")
                return
            
            # Create voice thread
            self.voice_thread = voice_mics(GEMINI_API_KEY)
            
            # Connect voice thread signals
            self.voice_thread.recording_started.connect(self._on_recording_started)
            self.voice_thread.recording_stopped.connect(self._on_recording_stopped)
            self.voice_thread.transcription_ready.connect(self._on_transcription_ready)
            self.voice_thread.error_occurred.connect(self._on_voice_error)
            self.voice_thread.processing_started.connect(self._on_processing_started)
            self.voice_thread.processing_finished.connect(self._on_processing_finished)
            
            # Connect microphone button
            self.mic_button.clicked.connect(self._toggle_voice_recording)
            
            # Initialize state
            self.is_recording = False
            
            print("[OK] Voice integration initialized successfully")
            
        except Exception as e:
            print(f"[ERROR] Voice integration failed: {e}")
            # Disable mic button if voice fails
            self.mic_button.setEnabled(False)
            self.mic_button.setToolTip("Voice integration unavailable")

    def _toggle_voice_recording(self):
        """Toggle voice recording on/off."""
        if not hasattr(self, 'voice_thread'):
            return
        
        if self.is_recording:
            # Stop recording
            self.voice_thread.stop_recording()
        else:
            # Start recording
            # Set context for the conversation
            context = {
                'generate_response': False,  # Just transcribe, don't generate responses
                'chat_history': getattr(self, 'chat_history', []),
                'current_tasks': getattr(self, 'current_tasks', []),
            }
            self.voice_thread.set_context(context)
            self.voice_thread.start_recording()

    def _on_recording_started(self):
        """Handle recording started event."""
        self.is_recording = True
        self.mic_button.setProperty("recording", True)
        self.mic_button.style().unpolish(self.mic_button)
        self.mic_button.style().polish(self.mic_button)
        self.mic_button.setToolTip("Recording... Click to stop")
        
        self.voice_status_label.setText("🔴 Recording... Click mic to stop")
        self.voice_status_label.show()

    def _on_recording_stopped(self):
        """Handle recording stopped event."""
        self.is_recording = False
        self.mic_button.setProperty("recording", False)
        self.mic_button.style().unpolish(self.mic_button)
        self.mic_button.style().polish(self.mic_button)
        self.mic_button.setToolTip("Click to record voice input")
        
        self.voice_status_label.setText("⏳ Processing audio...")

    def _on_processing_started(self):
        """Handle processing started event."""
        self.voice_status_label.setText("🤖 Transcribing...")

    def _on_processing_finished(self):
        """Handle processing finished event."""
        from PyQt5.QtCore import QTimer
        QTimer.singleShot(2000, self.voice_status_label.hide)

    def _on_transcription_ready(self, text):
        """Handle transcription ready event."""
        # Add transcribed text to the input field
        current_text = self.requirement_input.toPlainText().strip()
        if current_text:
            # Append to existing text
            self.requirement_input.setPlainText(current_text + " " + text)
        else:
            # Set as new text
            self.requirement_input.setPlainText(text)
        
        # Move cursor to end
        cursor = self.requirement_input.textCursor()
        cursor.movePosition(cursor.End)
        self.requirement_input.setTextCursor(cursor)
        
        self.voice_status_label.setText("✅ Transcription complete")
        
        # Auto-hide status after 2 seconds
        from PyQt5.QtCore import QTimer
        QTimer.singleShot(2000, self.voice_status_label.hide)

    def _on_voice_error(self, error_msg):
        """Handle voice error event."""
        self.is_recording = False
        self.mic_button.setProperty("recording", False)
        self.mic_button.style().unpolish(self.mic_button)
        self.mic_button.style().polish(self.mic_button)
        
        self.voice_status_label.setText(f"❌ {error_msg}")
        self.voice_status_label.show()
        
        # Auto-hide error after 4 seconds
        from PyQt5.QtCore import QTimer
        QTimer.singleShot(4000, self.voice_status_label.hide)

    def cleanup_voice(self):
        """Clean up voice resources when closing."""
        if hasattr(self, 'voice_thread'):
            self.voice_thread.cleanup()
            print("[INFO] Voice resources cleaned up")

    def create_main_content(self, main_layout):
        """Create main content area with tab group system"""
        # Create content container with drag toggle
        content_container = QWidget()
        content_container_layout = QVBoxLayout(content_container)
        content_container_layout.setContentsMargins(0, 0, 0, 0)
        content_container_layout.setSpacing(0)
        
        # Drag controls removed - chat panel functionality disabled
        # self.drag_controls_widget = QWidget()  # Removed
        # self.drag_controls_widget.setParent(self)  # Removed
        # drag_layout = QHBoxLayout(self.drag_controls_widget)  # Removed
        # drag_layout.setContentsMargins(0, 0, 0, 0)  # Removed
        # drag_layout.setSpacing(5)  # Removed
        
        # Main drag toggle button (smaller size) - REMOVED
        # self.drag_toggle_btn = QPushButton()  # Removed
        # self.drag_toggle_btn.setFixedSize(30, 30)  # Removed
        # self.drag_toggle_btn.setIcon(QIcon(resource_path("styles/Icon/drag_1.png")))  # Removed
        # self.drag_toggle_btn.setIconSize(QSize(20, 20))  # Removed
        # self.drag_toggle_btn.setProperty('class', 'DragToggleButton')  # Removed
        # self.drag_toggle_btn.setToolTip("Switch to secondary tabs")  # Removed
        # style_loader.apply_stylesheet(self.drag_toggle_btn)  # Removed
        
        # Drag left button - REMOVED
        # self.drag_left_btn = QPushButton()  # Removed
        # self.drag_left_btn.setFixedSize(25, 25)  # Removed
        # self.drag_left_btn.setIcon(QIcon(resource_path("styles/Icon/drag_left.png")))  # Removed
        # self.drag_left_btn.setIconSize(QSize(16, 16))  # Removed
        # self.drag_left_btn.setProperty('class', 'DragToggleButton')  # Removed
        # self.drag_left_btn.setToolTip("Move left")  # Removed
        # style_loader.apply_stylesheet(self.drag_left_btn)  # Removed
        
        # Drag right button - REMOVED
        # self.drag_right_btn = QPushButton()  # Removed
        # self.drag_right_btn.setFixedSize(25, 25)  # Removed
        # self.drag_right_btn.setIcon(QIcon(resource_path("styles/Icon/drag_right.png")))  # Removed
        # self.drag_right_btn.setIconSize(QSize(16, 16))  # Removed
        # self.drag_right_btn.setProperty('class', 'DragToggleButton')  # Removed
        # self.drag_right_btn.setToolTip("Move right")  # Removed
        # style_loader.apply_stylesheet(self.drag_right_btn)  # Removed
        
        # Add buttons to layout with spacing - REMOVED
        # drag_layout.addWidget(self.drag_toggle_btn)  # Removed
        # drag_layout.addSpacing(10)  # Removed
        
        # Show both buttons - they both toggle chat visibility - REMOVED
        # self.drag_left_btn.show()  # Removed
        # self.drag_right_btn.show()  # Removed
        # drag_layout.addWidget(self.drag_left_btn)  # Removed
        # drag_layout.addWidget(self.drag_right_btn)  # Removed
        
        # Set widget size to fit all buttons with spacing - REMOVED
        # self.drag_controls_widget.setFixedSize(85, 30)  # Removed
        
        # Track chat panel state - REMOVED
        # self.chat_dragged_left = False  # Removed
        
        # Connect drag toggle - REMOVED
        # self.drag_toggle_btn.clicked.connect(self.toggle_tab_groups)  # Removed
        # self.drag_left_btn.clicked.connect(self.move_drag_left)  # Removed
        # self.drag_right_btn.clicked.connect(self.move_drag_right)  # Removed
        # self.showing_primary_tabs = True  # Removed - was only used for drag toggle
        
        # Create primary tab widget (default visible)
        self.primary_tabs = QTabWidget()
        self.primary_tabs.setTabPosition(QTabWidget.North)
        self.primary_tabs.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.primary_tabs.setProperty('class', 'ContentTabs')
        style_loader.apply_stylesheet(self.primary_tabs)
        
        # Create secondary tab widget (initially hidden)
        self.secondary_tabs = QTabWidget()
        self.secondary_tabs.setTabPosition(QTabWidget.North)
        self.secondary_tabs.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.secondary_tabs.setProperty('class', 'ContentTabs')
        self.secondary_tabs.hide()
        style_loader.apply_stylesheet(self.secondary_tabs)
        
        content_container_layout.addWidget(self.primary_tabs)
        content_container_layout.addWidget(self.secondary_tabs)
        
        # Add toggle button for switching between tab groups
        # Create toggle button for switching between tab groups
        self.tab_toggle_btn = QPushButton()
        self.tab_toggle_btn.setIcon(QIcon(resource_path("styles/Icon/switch_tabs.png")))
        self.tab_toggle_btn.setFixedSize(32, 28)
        self.tab_toggle_btn.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                border: None;
                padding: 8px;
            }
            QPushButton:hover {
                background-color: transparent;
            }
            QPushButton:pressed {
                background-color: #45B7B8;
            }
        """)
        self.tab_toggle_btn.setCursor(Qt.PointingHandCursor)
        self.tab_toggle_btn.clicked.connect(self.toggle_tab_groups)
        self.tab_toggle_btn.setToolTip("Toggle between Main tabs and Debug Tools")

        # Add toggle button as corner widget to primary tabs (top-right)
        self.primary_tabs.setCornerWidget(self.tab_toggle_btn, Qt.TopRightCorner)

        # Also add the same button to secondary tabs
        self.tab_toggle_btn_secondary = QPushButton()
        self.tab_toggle_btn_secondary.setIcon(QIcon(resource_path("styles/Icon/switch_tabs.png")))
        self.tab_toggle_btn_secondary.setFixedSize(32, 28)
        self.tab_toggle_btn_secondary.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                border: None;
                padding: 8px;
            }
            QPushButton:hover {
                background-color: transparent;
            }
            QPushButton:pressed {
                background-color: #45B7B8;
            }
        """)
        self.tab_toggle_btn_secondary.setCursor(Qt.PointingHandCursor)
        self.tab_toggle_btn_secondary.clicked.connect(self.toggle_tab_groups)
        self.tab_toggle_btn_secondary.setToolTip("Toggle between Main tabs and Debug Tools")
        self.secondary_tabs.setCornerWidget(self.tab_toggle_btn_secondary, Qt.TopRightCorner)

        # Track which tab group is currently showing
        self.showing_primary_tabs = True
        # Store content container reference for positioning
        self.content_container = content_container
        
        # Position drag controls after tabs are added - REMOVED
        # QTimer.singleShot(100, self.position_drag_button)  # Removed
        
        # Use primary_tabs as content_area for backward compatibility
        content_area = self.primary_tabs
        
        # Generated Tasks Tab with split-screen layout (tasks left, chat right)
        tasks_widget = QWidget()
        tasks_layout = QVBoxLayout(tasks_widget)

        # Create horizontal splitter for tasks and chat
        self.tasks_chat_splitter = QSplitter(Qt.Horizontal)
        self.tasks_chat_splitter.setChildrenCollapsible(False)

        # Left side - Tasks display area
        tasks_area_widget = QWidget()
        tasks_area_layout = QVBoxLayout(tasks_area_widget)
        tasks_area_layout.setContentsMargins(10, 10, 5, 10)
        tasks_area_layout.setSpacing(10)

        # Create the task list widget for the tab (extended height)
        self.task_list = generated_tasks.EditableTaskListWidget()
        
        # Connect task updates signal
        self.task_list.tasks_updated.connect(self.on_tasks_updated)
        self.task_list.setMinimumHeight(int(500 * self.scale_factor))
        tasks_area_layout.addWidget(self.task_list)
        
        # Task actions section
        task_actions = QHBoxLayout()

        # --- Setup for click sound ---
        self.player = QMediaPlayer()
        self.click_sound_path = resource_path("styles/sound/ipad_click-99325.mp3")

        def play_click_sound():
            try:
                url = QUrl.fromLocalFile(self.click_sound_path)
                self.player.setMedia(QMediaContent(url))
                self.player.setVolume(100)
                self.player.play()
            except Exception as e:
                print(f"[ERROR] Failed to play sound: {e}")

        refresh_tasks_btn = QPushButton(" Refresh Steps")
        refresh_tasks_btn.setFixedSize(200, 40)
        refresh_tasks_btn.setIcon(QIcon(resource_path("styles/Icon/Refresh.png")))
        refresh_tasks_btn.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:1, x2:0, y2:0,
                                        stop:0 #005B7F, stop:1 #008AB3);
                border-radius: 10px;
                color: #FFFFFF;
                font-family: 'Asen Pro', sans-serif;
                font-weight: 600;
                font-size: 16px;
                letter-spacing: 0.05em;
                text-align: left;
                padding-left: 20px;
                border: none;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:1, x2:0, y2:0,
                                        stop:0 #006B8F, stop:1 #009AC3);
            }
            QPushButton:pressed {
                background: qlineargradient(x1:0, y1:1, x2:0, y2:0,
                                        stop:0 #004B6F, stop:1 #007A93);
            }
        """)
        # refresh_tasks_btn.clicked.connect(lambda: (play_click_sound(), self.update_task_list()))

        clear_breakpoints_btn = QPushButton(" Clear breakpoints")
        clear_breakpoints_btn.setFixedSize(235, 40)
        clear_breakpoints_btn.setIcon(QIcon(resource_path("styles/Icon/clear.png")))
        clear_breakpoints_btn.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:1, x2:0, y2:0,
                                        stop:0 #005B7F, stop:1 #008AB3);
                border-radius: 10px;
                color: #FFFFFF;
                font-family: 'Asen Pro', sans-serif;
                font-weight: 600;
                font-size: 16px;
                letter-spacing: 0.05em;
                text-align: left;
                padding-left: 20px;
                border: none;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:1, x2:0, y2:0,
                                        stop:0 #006B8F, stop:1 #009AC3);
            }
            QPushButton:pressed {
                background: qlineargradient(x1:0, y1:1, x2:0, y2:0,
                                        stop:0 #004B6F, stop:1 #007A93);
            }
        """)
        clear_breakpoints_btn.clicked.connect(lambda: (play_click_sound(), self.task_list.clear_breakpoints()))

        task_actions.addWidget(refresh_tasks_btn)
        task_actions.addWidget(clear_breakpoints_btn)
        task_actions.addStretch()
        tasks_area_layout.addLayout(task_actions)


        # Right side - Task Chat area
        task_chat_area_widget = QWidget()
        task_chat_area_layout = QVBoxLayout(task_chat_area_widget)
        task_chat_area_layout.setContentsMargins(5, 10, 10, 10)
        task_chat_area_layout.setSpacing(10)

        # New Chat button for task chat (top of chat area)
        task_new_chat_svg = "<svg xmlns=\"http://www.w3.org/2000/svg\" width=\"24\" height=\"24\" viewBox=\"0 0 24 24\" fill=\"none\" stroke=\"#fbf9f9\" stroke-width=\"2\" stroke-linecap=\"round\" stroke-linejoin=\"round\" class=\"lucide lucide-square-pen-icon lucide-square-pen\"><path d=\"M12 3H5a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7\"/><path d=\"M18.375 2.625a1 1 0 0 1 3 3l-9.013 9.014a2 2 0 0 1-.853.505l-2.873.84a.5.5 0 0 1-.62-.62l.84-2.873a2 2 0 0 1 .506-.852z\"/></svg>"
        
        self.task_new_chat_btn = QPushButton()
        self.task_new_chat_btn.setFixedHeight(40)
        self.task_new_chat_btn.setText("  New Chat")
        self.task_new_chat_btn.setToolTip("Start a new task chat session")
        
        # Create pixmap from SVG for task new chat button
        try:
            from PyQt5.QtSvg import QSvgRenderer
            task_new_chat_renderer = QSvgRenderer()
            task_new_chat_renderer.load(task_new_chat_svg.encode())
            task_new_chat_pixmap = QPixmap(24, 24)
            task_new_chat_pixmap.fill(Qt.transparent)
            task_new_chat_painter = QPainter(task_new_chat_pixmap)
            task_new_chat_renderer.render(task_new_chat_painter)
            task_new_chat_painter.end()
            self.task_new_chat_btn.setIcon(QIcon(task_new_chat_pixmap))
        except:
            self.task_new_chat_btn.setText("✎ New Chat")
        
        self.task_new_chat_btn.setIconSize(QSize(20, 20))
        self.task_new_chat_btn.setStyleSheet("""
            QPushButton {
                background: rgba(78, 205, 196, 0.1);
                border: 1px solid rgba(78, 205, 196, 0.3);
                border-radius: 6px;
                padding: 8px 12px;
                color: #fbf9f9;
                font-size: 14px;
                font-weight: 500;
                text-align: center;
            }
            QPushButton:hover {
                background: rgba(78, 205, 196, 0.2);
                border-color: rgba(78, 205, 196, 0.5);
            }
            QPushButton:pressed {
                background: rgba(78, 205, 196, 0.3);
            }
        """)
        self.task_new_chat_btn.clicked.connect(self.on_task_new_chat_clicked)
        task_chat_area_layout.addWidget(self.task_new_chat_btn)

        # Task Chat header removed as requested

        # Attached files display for task chat - will be moved to input area
        
        # Task Chat history display - using widget-based approach like code chat
        self.task_chat_display = QScrollArea()
        self.task_chat_display.setWidgetResizable(True)
        self.task_chat_display.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.task_chat_display.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.task_chat_display.setStyleSheet("""
            QScrollArea {
                background: rgba(20, 25, 30, 0.9);
                border: 1px solid rgba(78, 205, 196, 0.2);
                border-radius: 8px;
                padding: 5px;
            }
            QScrollBar:vertical {
                background: rgba(255, 255, 255, 0.1);
                width: 8px;
                border-radius: 4px;
            }
            QScrollBar::handle:vertical {
                background: rgba(78, 205, 196, 0.6);
                border-radius: 4px;
                min-height: 20px;
            }
            QScrollBar::handle:vertical:hover {
                background: rgba(78, 205, 196, 0.8);
            }
            QScrollBar:horizontal {
                background: rgba(255, 255, 255, 0.1);
                height: 8px;
                border-radius: 4px;
            }
            QScrollBar::handle:horizontal {
                background: rgba(78, 205, 196, 0.6);
                border-radius: 4px;
                min-width: 20px;
            }
            QScrollBar::handle:horizontal:hover {
                background: rgba(78, 205, 196, 0.8);
            }
        """)
        
        # Create container widget for task chat messages
        self.task_chat_container = QWidget()
        self.task_chat_layout = QVBoxLayout(self.task_chat_container)
        self.task_chat_layout.setContentsMargins(10, 10, 10, 10)
        self.task_chat_layout.setSpacing(10)
        self.task_chat_layout.addStretch()  # Push messages to bottom initially
        
        self.task_chat_display.setWidget(self.task_chat_container)
        task_chat_area_layout.addWidget(self.task_chat_display, 1)  # Takes most space

        # Task Chat input area - with files info and proper border
        task_chat_input_main_container = QWidget()
        task_chat_input_main_layout = QVBoxLayout(task_chat_input_main_container)
        task_chat_input_main_layout.setSpacing(4)
        task_chat_input_main_layout.setContentsMargins(2, 2, 2, 4)
        
        # Attached files display with remove option (top of input area)
        task_files_container = QWidget()
        task_files_layout = QHBoxLayout(task_files_container)
        task_files_layout.setContentsMargins(0, 0, 0, 0)
        task_files_layout.setSpacing(8)
        
        self.task_attached_files_label = QLabel("No files attached")
        self.task_attached_files_label.setStyleSheet("""
            QLabel {
                color: #888;
                font-size: 11px;
                padding: 4px 8px;
                background: rgba(255, 255, 255, 0.05);
                border-radius: 4px;
            }
        """)
        task_files_layout.addWidget(self.task_attached_files_label)
        
        # Remove attachments button (initially hidden)
        self.task_remove_attachments_btn = QPushButton("✕")
        self.task_remove_attachments_btn.setFixedSize(20, 20)
        self.task_remove_attachments_btn.setToolTip("Remove all attachments")
        self.task_remove_attachments_btn.setStyleSheet("""
            QPushButton {
                background: rgba(220, 53, 69, 0.8);
                color: white;
                border: none;
                border-radius: 10px;
                font-size: 12px;
                font-weight: bold;
                padding: 0px;
            }
            QPushButton:hover {
                background: rgba(220, 53, 69, 1.0);
            }
            QPushButton:pressed {
                background: rgba(200, 35, 51, 1.0);
            }
        """)
        self.task_remove_attachments_btn.clicked.connect(self.remove_task_attachments)
        self.task_remove_attachments_btn.hide()  # Initially hidden
        task_files_layout.addWidget(self.task_remove_attachments_btn)
        
        task_files_layout.addStretch()  # Push everything to the left
        task_chat_input_main_layout.addWidget(task_files_container)
        
        # Input container with proper border
        task_chat_input_container = QFrame()
        task_chat_input_container.setStyleSheet("""
            QFrame {
                background: #000000;
                border: 2px solid rgba(78, 205, 196, 0.6);
                border-radius: 8px;
                padding: 6px;
                min-height: 60px;
                margin: 2px;
            }
        """)
        task_chat_input_layout = QHBoxLayout(task_chat_input_container)
        task_chat_input_layout.setSpacing(6)
        task_chat_input_layout.setContentsMargins(8, 8, 8, 8)
        
        # Left side buttons container - vertical layout (top/bottom)
        left_buttons_layout = QVBoxLayout()
        left_buttons_layout.setSpacing(2)
        left_buttons_layout.setContentsMargins(0, 0, 0, 0)
        
        # Attach button (left edge inside box - smaller, no background)
        self.task_attach_btn = QPushButton()
        self.task_attach_btn.setFixedSize(28, 28)
        self.task_attach_btn.setIcon(QIcon(resource_path("styles/Icon/attach.png")))
        self.task_attach_btn.setIconSize(QSize(20, 20))
        self.task_attach_btn.setStyleSheet("""
            QPushButton {
                background: transparent;
                border: none;
                padding: 4px;
            }
            QPushButton:hover {
                background: rgba(78, 205, 196, 0.15);
                border-radius: 14px;
            }
        """)
        self.task_attach_btn.clicked.connect(self.attach_task_files)
        left_buttons_layout.addWidget(self.task_attach_btn)
        
        # Speak button (left edge inside box - smaller, no background)
        self.task_speak_btn = QPushButton()
        self.task_speak_btn.setIcon(QIcon(resource_path("styles/Icon/speak.png")))
        self.task_speak_btn.setFixedSize(28, 28)
        self.task_speak_btn.setIconSize(QSize(20, 20))
        self.task_speak_btn.setStyleSheet("""
            QPushButton {
                background: transparent;
                border: none;
                padding: 4px;
            }
            QPushButton:hover {
                background: rgba(78, 205, 196, 0.15);
                border-radius: 14px;
            }
        """)
        left_buttons_layout.addWidget(self.task_speak_btn)
 
        # --- Initialize Voice Integration Thread ---
        # --- Initialize Voice Integration Thread ---
        # from voice_integration_thread import VoiceIntegrationThread
        import config
 
        GEMINI_API_KEY = getattr(config, 'API_KEY', None)
        self.voice_thread_mic2 = voice_mics(api_key=GEMINI_API_KEY)
 
        # --- Connect signals ---
 
        def on_transcription_ready(text):
            """Handle Gemini text response and paste it into the input box."""
            current_text = self.task_chat_input.toPlainText().strip()
            if current_text in ["🤖 Listening...", "🤖 Transcribing..."]:
                current_text = ""
           
            # Stop voice playback immediately if any
            if hasattr(self, "voice_thread_mic2"):
                try:
                    self.voice_thread_mic2.stop_playback()
                except Exception:
                    pass
 
            # Paste final response
            self.task_chat_input.setPlainText(text.strip())
 
        self.voice_thread_mic2.transcription_ready.connect(on_transcription_ready)
 
        # --- Handle errors ---
        def on_voice_error(error_msg):
            """Display error in the input box."""
            self.task_chat_input.setPlainText(f"❌ Error occurred: {error_msg}")
 
        self.voice_thread_mic2.error_occurred.connect(on_voice_error)
 
        # --- Button UI feedback ---
        self.voice_thread_mic2.recording_started.connect(lambda: [
            self.task_speak_btn.setStyleSheet("""
                QPushButton {
                    background: red;
                    border: none;
                    padding: 4px;
                    border-radius: 14px;
                }
            """),
            self.task_chat_input.setPlainText("🤖 Listening...")
        ])
 
        self.voice_thread_mic2.recording_stopped.connect(lambda: [
            self.task_speak_btn.setStyleSheet("""
                QPushButton {
                    background: transparent;
                    border: none;
                    padding: 4px;
                }
                QPushButton:hover {
                    background: rgba(78, 205, 196, 0.15);
                    border-radius: 14px;
                }
            """),
            self.task_chat_input.setPlainText("🤖 Transcribing...")
        ])
 
        # --- Mic toggle function ---
        def toggle_voice_recording_mic2():
            """Toggle voice recording on/off."""
            if not hasattr(self, 'voice_thread_mic2'):
                return
 
            if self.voice_thread_mic2.is_recording:
                self.voice_thread_mic2.stop_recording()
            else:
                context = {
                    'generate_response': True,  # Ask Gemini for text response
                }
                self.voice_thread_mic2.set_context(context)
                self.voice_thread_mic2.start_recording()
 
        # --- Connect mic button ---
        self.task_speak_btn.clicked.connect(toggle_voice_recording_mic2)
        
        task_chat_input_layout.addLayout(left_buttons_layout)
        
        # Input text area (center, expanding - no inner border, fixed viewport)
        self.task_chat_input = QTextEdit()
        self.task_chat_input.setFixedHeight(45)
        self.task_chat_input.setPlaceholderText("Type your message about steps restructuring...")
        self.task_chat_input.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.task_chat_input.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.task_chat_input.setFrameStyle(0)  # Remove frame
        self.task_chat_input.setStyleSheet("""
            QTextEdit {
                background: transparent;
                border: none;
                color: white;
                font-size: 14px;
                padding: 8px 20px;
                border-radius: 0px;
                line-height: 1.4;
                margin: 0px;
            }
            QTextEdit:focus {
                border: none;
                background: transparent;
                outline: none;
            }
            QTextEdit QScrollBar {
                width: 0px;
                height: 0px;
            }
        """)
        
        # Install event filter for Enter key functionality
        self.task_chat_input.installEventFilter(self)
        
        task_chat_input_layout.addWidget(self.task_chat_input, 1)  # Expanding to full width
        
        # Send button (right edge inside box - larger size and icon)
        self.send_task_chat_btn = QPushButton()
        self.send_task_chat_btn.setIcon(QIcon(resource_path("styles/Icon/sent_task.png")))
        self.send_task_chat_btn.setFixedSize(50, 50)
        self.send_task_chat_btn.setIconSize(QSize(35, 35))
        self.send_task_chat_btn.setStyleSheet("""
            QPushButton {
                background: transparent;
                border: none;
                padding: 6px;
            }
            QPushButton:hover {
                background: rgba(78, 205, 196, 0.15);
                border-radius: 20px;
            }
            QPushButton:pressed {
                background: rgba(78, 205, 196, 0.25);
                border-radius: 20px;
            }
        """)
        self.send_task_chat_btn.clicked.connect(self.send_task_chat_message)
        task_chat_input_layout.addWidget(self.send_task_chat_btn)
        
        # Add input container to main container
        task_chat_input_main_layout.addWidget(task_chat_input_container)
        
        # Add the main input container to the layout
        task_chat_area_layout.addWidget(task_chat_input_main_container)
        
        # Add both areas to splitter
        self.tasks_chat_splitter.addWidget(tasks_area_widget)
        self.tasks_chat_splitter.addWidget(task_chat_area_widget)
        # Set initial sizes (60% tasks, 40% chat)
        self.tasks_chat_splitter.setSizes([600, 400])
        
        # Initialize task chat variables
        self.task_attached_files = []
        self.task_chat_history = []  # Gemini format for history
        self.ui_task_chat_history = []  # UI display format
        
        tasks_layout.addWidget(self.tasks_chat_splitter)

        # Create text input for compatibility with existing restructure_tasks method
        self.task_restructure_input = QTextEdit()
        self.task_restructure_input.hide()  # Hidden since we use task chat now
        
        # Create send button for compatibility
        self.restructure_send_btn = QPushButton()
        self.restructure_send_btn.hide()
        
        content_area.addTab(tasks_widget, "Generated Steps")
        
        # Processing Log Tab
        log_widget = QWidget()
        log_layout = QVBoxLayout(log_widget)
        
        # Removed inner log header for a cleaner unified look
        
        self.log_display = QTextEdit()
        self.log_display.setReadOnly(True)
        self.log_display.setFont(QFont("Consolas", int(10 * self.scale_factor)))

        # self.log_display.setProperty('class', 'LogDisplay')
        style_loader.apply_stylesheet(self.log_display)
        log_layout.addWidget(self.log_display)
        
        content_area.addTab(log_widget, "Processing Log")
        # Generated Code Tab with Chat Window
        code_widget = QWidget()
        code_layout = QVBoxLayout(code_widget)

        # Create horizontal splitter for code and chat
        self.code_chat_splitter = QSplitter(Qt.Horizontal)
        self.code_chat_splitter.setChildrenCollapsible(False)

        # Left side - Code display area
        code_area_widget = QWidget()
        code_area_layout = QVBoxLayout(code_area_widget)
        
        self.code_display = CodeEditor()
        self.code_display.setReadOnly(False)
        self.code_display.setFont(QFont("Consolas", int(10 * self.scale_factor)))
        
        # Apply enhanced VS Code-like dark theme styling
        self.code_display.setStyleSheet("""
    QTextEdit {
        background-color: #1e1e1e;
        color: #d4d4d4;
        border: 1px solid #3c3c3c;
        border-radius: 6px;
        padding: 12px;
        line-height: 1.5;
        selection-background-color: #264f78;
        selection-color: #ffffff;
    }
    QScrollBar:vertical {
        background-color: #252526;
        width: 14px;
        border-radius: 7px;
        margin: 0px;
    }
    QScrollBar::handle:vertical {
        background-color: #424242;
        border-radius: 7px;
        min-height: 30px;
        margin: 2px;
    }
    QScrollBar::handle:vertical:hover {
        background-color: #4f4f4f;
    }
    QScrollBar::handle:vertical:pressed {
        background-color: #555555;
    }
    QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
        border: none;
        background: none;
        height: 0px;
    }
    QScrollBar:horizontal {
        background-color: #252526;
        height: 14px;
        border-radius: 7px;
        margin: 0px;
    }
    QScrollBar::handle:horizontal {
        background-color: #424242;
        border-radius: 7px;
        min-width: 30px;
        margin: 2px;
    }
    QScrollBar::handle:horizontal:hover {
        background-color: #4f4f4f;
    }
    QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {
        border: none;
        background: none;
        width: 0px;
    }
""")
        
        # Apply Python syntax highlighting to the code display
        self.python_highlighter = PythonSyntaxHighlighter(self.code_display.document())
        
        code_area_layout.addWidget(self.code_display)
        
         # Code actions
        code_actions = QHBoxLayout()

        # --- Setup for click sound ---
        self.player = QMediaPlayer()
        self.click_sound_path = resource_path("styles/sound/ipad_click-99325.mp3")

        def play_click_sound():
            try:
                url = QUrl.fromLocalFile(self.click_sound_path)
                self.player.setMedia(QMediaContent(url))
                self.player.setVolume(100)
                self.player.play()
            except Exception as e:
                print(f"[ERROR] Failed to play sound: {e}")

        # Undo button with SVG icon
        undo_svg = "<svg xmlns=\"http://www.w3.org/2000/svg\" width=\"24\" height=\"24\" viewBox=\"0 0 24 24\" fill=\"none\" stroke=\"#f3f1f1\" stroke-width=\"2\" stroke-linecap=\"round\" stroke-linejoin=\"round\" class=\"lucide lucide-undo-icon lucide-undo\"><path d=\"M3 7v6h6\"/><path d=\"M21 17a9 9 0 0 0-9-9 9 9 0 0 0-6 2.3L3 13\"/></svg>"
        
        self.undo_btn = QPushButton()
        self.undo_btn.setFixedSize(40, 40)
        self.undo_btn.setToolTip("Undo (Ctrl+Z)")
        self.undo_btn.setSvgIcon(undo_svg) if hasattr(self.undo_btn, 'setSvgIcon') else None
        
        # Create pixmap from SVG for undo button
        try:
            from PyQt5.QtSvg import QSvgRenderer
            undo_renderer = QSvgRenderer()
            undo_renderer.load(undo_svg.encode())
            undo_pixmap = QPixmap(24, 24)
            undo_pixmap.fill(Qt.transparent)
            undo_painter = QPainter(undo_pixmap)
            undo_renderer.render(undo_painter)
            undo_painter.end()
            self.undo_btn.setIcon(QIcon(undo_pixmap))
        except:
            # Fallback to text if SVG fails
            self.undo_btn.setText("↶")
        
        self.undo_btn.setIconSize(QSize(20, 20))
        self.undo_btn.setStyleSheet("""
            QPushButton {
                background: transparent;
                border: none;
                border-radius: 6px;
                padding: 4px;
            }
            QPushButton:hover {
                background: rgba(78, 205, 196, 0.2);
            }
            QPushButton:pressed {
                background: rgba(78, 205, 196, 0.3);
            }
            QPushButton:disabled {
                opacity: 0.4;
            }
        """)
        self.undo_btn.setEnabled(False)
        self.undo_btn.clicked.connect(self.on_undo_clicked)
        
        # Redo button with SVG icon
        redo_svg = "<svg xmlns=\"http://www.w3.org/2000/svg\" width=\"24\" height=\"24\" viewBox=\"0 0 24 24\" fill=\"none\" stroke=\"#f3f1f1\" stroke-width=\"2\" stroke-linecap=\"round\" stroke-linejoin=\"round\" class=\"lucide lucide-redo-icon lucide-redo\"><path d=\"M21 7v6h-6\"/><path d=\"M3 17a9 9 0 0 1 9-9 9 9 0 0 1 6 2.3l3 2.7\"/></svg>"
        
        self.redo_btn = QPushButton()
        self.redo_btn.setFixedSize(40, 40)
        self.redo_btn.setToolTip("Redo (Ctrl+Y)")
        
        # Create pixmap from SVG for redo button
        try:
            redo_renderer = QSvgRenderer()
            redo_renderer.load(redo_svg.encode())
            redo_pixmap = QPixmap(24, 24)
            redo_pixmap.fill(Qt.transparent)
            redo_painter = QPainter(redo_pixmap)
            redo_renderer.render(redo_painter)
            redo_painter.end()
            self.redo_btn.setIcon(QIcon(redo_pixmap))
        except:
            # Fallback to text if SVG fails
            self.redo_btn.setText("↷")
        
        self.redo_btn.setIconSize(QSize(20, 20))
        self.redo_btn.setStyleSheet("""
            QPushButton {
                background: transparent;
                border: none;
                border-radius: 6px;
                padding: 4px;
            }
            QPushButton:hover {
                background: rgba(78, 205, 196, 0.2);
            }
            QPushButton:pressed {
                background: rgba(78, 205, 196, 0.3);
            }
            QPushButton:disabled {
                opacity: 0.4;
            }
        """)
        self.redo_btn.setEnabled(False)
        self.redo_btn.clicked.connect(self.on_redo_clicked)
        
        # Connect code editor's undo/redo state signal to update buttons
        self.code_display.undo_redo_state_changed.connect(self.update_undo_redo_buttons)

        execute_btn = QPushButton(" Execute Code")
        execute_btn.setFixedSize(190, 50)
        execute_btn.setIcon(QIcon(resource_path("styles/Icon/play.png")))
        execute_btn.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:1, x2:0, y2:0,
                                            stop:0 #005B7F, stop:1 #008AB3);
                border-radius: 10px;
                color: #FFFFFF;
                font-family: 'Asen Pro', sans-serif;
                font-weight: 600;
                font-size: 16px;
                letter-spacing: 0.05em;
                text-align: left;
                padding-left: 20px;
                border: none;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:1, x2:0, y2:0,
                                            stop:0 #006B8F, stop:1 #009AC3);
            }
            QPushButton:pressed {
                background: qlineargradient(x1:0, y1:1, x2:0, y2:0,
                                            stop:0 #004B6F, stop:1 #007A93);
            }
            QPushButton:disabled {
                background: qlineargradient(x1:0, y1:1, x2:0, y2:0,
                                            stop:0 #666666, stop:1 #888888);
                color: #AAAAAA;
                border: 1px solid #555555;
            }
        """)
        execute_btn.clicked.connect(lambda: (play_click_sound(), self.execute_code()))
        execute_btn.hide()  # Hide the Execute Code button
        self.execute_btn = execute_btn  # Store reference for enabling/disabling

        # Sync Changes button (optional, currently commented out)
        sync_btn = QPushButton(" Sync Changes")
        sync_btn.setFixedSize(190, 50)
        sync_btn.setIcon(QIcon(resource_path("styles/Icon/refresh.png")))  # Using refresh icon for sync
        sync_btn.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:1, x2:0, y2:0,
                                            stop:0 #1976D2, stop:1 #2196F3);
                border-radius: 10px;
                color: #FFFFFF;
                font-family: 'Asen Pro', sans-serif;
                font-weight: 600;
                font-size: 16px;
                letter-spacing: 0.05em;
                text-align: left;
                padding-left: 20px;
                border: none;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:1, x2:0, y2:0,
                                            stop:0 #1565C0, stop:1 #1E88E5);
            }
            QPushButton:pressed {
                background: qlineargradient(x1:0, y1:1, x2:0, y2:0,
                                            stop:0 #0D47A1, stop:1 #1565C0);
            }
        """)
        sync_btn.clicked.connect(lambda: (play_click_sound(), self.sync_code_changes()))
        self.sync_btn = sync_btn  # Store reference

        stop_btn = QPushButton(" Stop Execution")
        stop_btn.setFixedSize(190, 50)
        stop_btn.setIcon(QIcon(resource_path("styles/Icon/stop.png")))
        stop_btn.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:1, x2:0, y2:0,
                                            stop:0 #005B7F, stop:1 #008AB3); /* Blue gradient */
                border-radius: 10px;
                color: #FFFFFF;
                font-family: 'Asen Pro', sans-serif;
                font-weight: 600;
                font-size: 16px;
                letter-spacing: 0.05em;
                text-align: left;
                padding-left: 20px;
                border: none;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:1, x2:0, y2:0,
                                            stop:0 #006B8F, stop:1 #009AC3); /* Lighter blue */
            }
            QPushButton:pressed {
                background: qlineargradient(x1:0, y1:1, x2:0, y2:0,
                                            stop:0 #C62828, stop:1 #F44336); /* Red on press */
            }
        """)
        stop_btn.clicked.connect(lambda: (play_click_sound(), self.stop_execution()))
        stop_btn.setEnabled(False)  # Initially disabled
        self.stop_btn = stop_btn

        # Add undo/redo buttons to the left of other buttons
        code_actions.addWidget(self.undo_btn)
        code_actions.addWidget(self.redo_btn)
        code_actions.addWidget(execute_btn)
        # code_actions.addWidget(sync_btn)
        # code_actions.addWidget(stop_btn)
        code_actions.addStretch()
        code_area_layout.addLayout(code_actions)

        
        # Right side - Chat window
        chat_area_widget = QWidget()
        chat_area_layout = QVBoxLayout(chat_area_widget)
        
        # Switchable header for Code Chat / XPath Variables
        header_container = QWidget()
        header_layout = QHBoxLayout(header_container)
        header_layout.setContentsMargins(0, 0, 0, 0)
        header_layout.setSpacing(0)
        
        # Code Chat button
        self.code_chat_btn = QPushButton("Code Chat")
        self.code_chat_btn.setProperty('class', 'CodeTabHeaderButton')
        self.code_chat_btn.setCheckable(True)
        self.code_chat_btn.setChecked(True)  # Code Chat is active by default
        self.code_chat_btn.clicked.connect(self.show_code_chat_view)
        
        # XPath Variables button
        self.xpath_vars_btn = QPushButton("XPath Variables")
        self.xpath_vars_btn.setProperty('class', 'CodeTabHeaderButton')
        self.xpath_vars_btn.setCheckable(True)
        self.xpath_vars_btn.setChecked(False)
        self.xpath_vars_btn.clicked.connect(self.show_xpath_vars_view)
        
        # Header button styling
        header_button_style = """
            QPushButton {
                background-color: #000000;
                color: #ffffff;
                border: 2px solid #666666;
                border-radius: 8px;
                border-bottom-left-radius: 0px;
                border-bottom-right-radius: 0px;
                border-bottom: none;
                padding: 8px 12px;
                font-size: 14px;
                font-weight: normal;
                outline: none;
                margin: 0px;
            }
            QPushButton:checked {
                background-color: #000000;
                color: #ffffff;
                border: 2px solid #17a2b8;
                border-radius: 8px;
                border-bottom-left-radius: 0px;
                border-bottom-right-radius: 0px;
                border-bottom: none;
            }
            QPushButton:hover {
                background-color: #000000;
                border-color: #888888;
            }
            QPushButton:checked:hover {
                background-color: #000000;
                border: 2px solid #17a2b8;
                border-bottom: none;
            }
        """
        
        self.code_chat_btn.setStyleSheet(header_button_style)
        self.xpath_vars_btn.setStyleSheet(header_button_style)
        header_layout.addWidget(self.code_chat_btn)
        header_layout.addWidget(self.xpath_vars_btn)
        header_layout.addStretch()
        
        chat_area_layout.addWidget(header_container)
        
        # Create switchable content container
        self.code_tab_content_container = QWidget()
        content_container_layout = QVBoxLayout(self.code_tab_content_container)
        content_container_layout.setContentsMargins(0, 0, 0, 0)
        content_container_layout.setSpacing(0)
        
        # Code Chat content area (initially visible)
        self.code_chat_content = QWidget()
        code_chat_layout = QVBoxLayout(self.code_chat_content)
        code_chat_layout.setContentsMargins(0, 0, 0, 0)
        code_chat_layout.setSpacing(8)
        
        # New Chat button with SVG icon and text (top of chat area)
        new_chat_svg = "<svg xmlns=\"http://www.w3.org/2000/svg\" width=\"24\" height=\"24\" viewBox=\"0 0 24 24\" fill=\"none\" stroke=\"#fbf9f9\" stroke-width=\"2\" stroke-linecap=\"round\" stroke-linejoin=\"round\" class=\"lucide lucide-square-pen-icon lucide-square-pen\"><path d=\"M12 3H5a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7\"/><path d=\"M18.375 2.625a1 1 0 0 1 3 3l-9.013 9.014a2 2 0 0 1-.853.505l-2.873.84a.5.5 0 0 1-.62-.62l.84-2.873a2 2 0 0 1 .506-.852z\"/></svg>"
        
        self.new_chat_btn_top = QPushButton()
        self.new_chat_btn_top.setFixedHeight(40)
        self.new_chat_btn_top.setText("  New Chat")
        self.new_chat_btn_top.setToolTip("Start a new chat session")
        
        # Create pixmap from SVG for new chat button
        try:
            from PyQt5.QtSvg import QSvgRenderer
            new_chat_renderer = QSvgRenderer()
            new_chat_renderer.load(new_chat_svg.encode())
            new_chat_pixmap = QPixmap(24, 24)
            new_chat_pixmap.fill(Qt.transparent)
            new_chat_painter = QPainter(new_chat_pixmap)
            new_chat_renderer.render(new_chat_painter)
            new_chat_painter.end()
            self.new_chat_btn_top.setIcon(QIcon(new_chat_pixmap))
        except:
            self.new_chat_btn_top.setText("✎ New Chat")
        
        self.new_chat_btn_top.setIconSize(QSize(20, 20))
        self.new_chat_btn_top.setStyleSheet("""
            QPushButton {
                background: rgba(78, 205, 196, 0.1);
                border: 1px solid rgba(78, 205, 196, 0.3);
                border-radius: 6px;
                padding: 8px 12px;
                color: #fbf9f9;
                font-size: 14px;
                font-weight: 500;
                text-align: center;
            }
            QPushButton:hover {
                background: rgba(78, 205, 196, 0.2);
                border-color: rgba(78, 205, 196, 0.5);
            }
            QPushButton:pressed {
                background: rgba(78, 205, 196, 0.3);
            }
        """)
        self.new_chat_btn_top.clicked.connect(self.on_new_chat_clicked)
        code_chat_layout.addWidget(self.new_chat_btn_top)
        
        # Chat history display - using widget-based approach like draggable_chat_panel
        self.chat_display = QScrollArea()
        self.chat_display.setWidgetResizable(True)
        self.chat_display.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.chat_display.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.chat_display.setStyleSheet("""
            QScrollArea {
                background: rgba(20, 25, 30, 0.8);
                border: 1px solid rgba(128, 128, 128, 0.2);
                border-radius: 8px;
            }
            QScrollBar:vertical {
                background: rgba(40, 45, 50, 0.5);
                width: 8px;
                border-radius: 4px;
            }
            QScrollBar::handle:vertical {
                background: rgba(128, 128, 128, 0.6);
                border-radius: 4px;
                min-height: 20px;
            }
            QScrollBar::handle:vertical:hover {
                background: rgba(160, 160, 160, 0.8);
            }
        """)
        
        # Chat messages container
        self.chat_messages_widget = QWidget()
        self.chat_messages_layout = QVBoxLayout(self.chat_messages_widget)
        self.chat_messages_layout.setContentsMargins(10, 10, 10, 10)
        self.chat_messages_layout.setSpacing(10)
        self.chat_messages_layout.addStretch()  # Push messages to top
        
        self.chat_display.setWidget(self.chat_messages_widget)
        self.chat_history_display = self.chat_display  # Keep reference for compatibility
        
        # Remove click event handler since we're using widget-based approach now
        
        code_chat_layout.addWidget(self.chat_display)
        
        # Attached files display with remove option
        code_files_container = QWidget()
        code_files_layout = QHBoxLayout(code_files_container)
        code_files_layout.setContentsMargins(0, 0, 0, 0)
        code_files_layout.setSpacing(8)
        
        self.attached_files_label = QLabel("📎 No files attached")
        self.attached_files_label.setStyleSheet("""
            QLabel {
                color: #888888;
                font-size: 12px;
                padding: 5px;
                background: rgba(40, 45, 50, 0.6);
                border-radius: 4px;
                margin: 5px 0;
            }
        """)
        code_files_layout.addWidget(self.attached_files_label)
        
        # Remove attachments button for code chat (initially hidden)
        self.code_remove_attachments_btn = QPushButton("✕")
        self.code_remove_attachments_btn.setFixedSize(20, 20)
        self.code_remove_attachments_btn.setToolTip("Remove all attachments")
        self.code_remove_attachments_btn.setStyleSheet("""
            QPushButton {
                background: rgba(220, 53, 69, 0.8);
                color: white;
                border: none;
                border-radius: 10px;
                font-size: 12px;
                font-weight: bold;
                padding: 0px;
            }
            QPushButton:hover {
                background: rgba(220, 53, 69, 1.0);
            }
            QPushButton:pressed {
                background: rgba(200, 35, 51, 1.0);
            }
        """)
        self.code_remove_attachments_btn.clicked.connect(self.remove_code_attachments)
        self.code_remove_attachments_btn.hide()  # Initially hidden
        code_files_layout.addWidget(self.code_remove_attachments_btn)
        
        code_files_layout.addStretch()  # Push everything to the left
        code_chat_layout.addWidget(code_files_container)
        
        # Chat input area with proper layout matching reference design
        chat_input_container = QFrame()
        chat_input_container.setStyleSheet("""
            QFrame {
                background: rgba(30, 35, 40, 0.9);
                border: 1px solid rgba(78, 205, 196, 0.3);
                border-radius: 12px;
                padding: 4px;
                max-height: 60px;
                min-height: 60px;
            }
        """)
        chat_input_layout = QHBoxLayout(chat_input_container)
        chat_input_layout.setSpacing(6)
        chat_input_layout.setContentsMargins(6, 6, 6, 6)
        
        # Attach button (left side)
        self.attach_btn = QPushButton()
        self.attach_btn.setFixedSize(28, 28)
        self.attach_btn.setIcon(QIcon(resource_path("styles/Icon/attach.png")))
        self.attach_btn.setIconSize(QSize(16, 16))
        self.attach_btn.setToolTip("Attach files")
        self.attach_btn.setStyleSheet("""
            QPushButton {
                background: transparent;
                border: none;
                border-radius: 14px;
                padding: 6px;
            }
            QPushButton:hover {
                background: rgba(78, 205, 196, 0.2);
            }
            QPushButton:pressed {
                background: rgba(78, 205, 196, 0.3);
            }
        """)
        self.attach_btn.clicked.connect(self.attach_files)
        chat_input_layout.addWidget(self.attach_btn)
        
        # Input text area (center, expanding)
        self.chat_input = QTextEdit()
        self.chat_input.setFixedHeight(80)
        self.chat_input.setPlaceholderText("Type your message about the code...")
        self.chat_input.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.chat_input.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.chat_input.setFrameStyle(0)  # Remove frame
        self.chat_input.setStyleSheet("""
            QTextEdit {
                background: transparent;
                border: none;
                color: white;
                font-size: 13px;
                font-family: 'Segoe UI';
                padding: 4px 8px;
            }
            QTextEdit:focus {
                background: transparent;
                border: none;
                outline: none;
            }
        """)
        
        # Install event filter for Enter key functionality
        self.chat_input.installEventFilter(self)
        
        chat_input_layout.addWidget(self.chat_input, 1)  # Expanding
        
        # Speak button (right side)
        self.speak_btn = QPushButton()
        self.speak_btn.setFixedSize(28, 28)
        self.speak_btn.setIcon(QIcon(resource_path("styles/Icon/speak.png")))
        self.speak_btn.setIconSize(QSize(16, 16))
        self.speak_btn.setToolTip("Voice input")
        self.speak_btn.setStyleSheet("""
            QPushButton {
                background: transparent;
                border: none;
                border-radius: 14px;
                padding: 6px;
            }
            QPushButton:hover {
                background: rgba(78, 205, 196, 0.2);
            }
            QPushButton:pressed {
                background: rgba(78, 205, 196, 0.3);
            }
        """)
        chat_input_layout.addWidget(self.speak_btn)
 
        GEMINI_API_KEY = getattr(config, 'API_KEY', None)
        self.voice_thread_btn = voice_mics(api_key=GEMINI_API_KEY)
 
        # --- Connect signals ---
        def on_transcription_ready_btn(text):
            """Handle Gemini text response and paste it into the input box."""
            current_text = self.chat_input.toPlainText().strip()
            if current_text in ["🤖 Listening...", "🤖 Transcribing..."]:
                current_text = ""
 
            # Stop voice playback immediately if any
            if hasattr(self, "voice_thread_btn"):
                try:
                    self.voice_thread_btn.stop_playback()
                except Exception:
                    pass
 
            # Paste final response
            self.chat_input.setPlainText(text.strip())
 
        self.voice_thread_btn.transcription_ready.connect(on_transcription_ready_btn)
 
        # --- Handle errors ---
        def on_voice_error_btn(error_msg):
            """Display error in the input box."""
            self.chat_input.setPlainText(f"❌ Error occurred: {error_msg}")
 
        self.voice_thread_btn.error_occurred.connect(on_voice_error_btn)
 
        # --- Button UI feedback ---
        self.voice_thread_btn.recording_started.connect(lambda: [
            self.speak_btn.setStyleSheet("""
                QPushButton {
                    background: red;
                    border: none;
                    border-radius: 14px;
                    padding: 6px;
                }
            """),
            self.chat_input.setPlainText("🤖 Listening...")
        ])
 
        self.voice_thread_btn.recording_stopped.connect(lambda: [
            self.speak_btn.setStyleSheet("""
                QPushButton {
                    background: transparent;
                    border: none;
                    border-radius: 14px;
                    padding: 6px;
                }
                QPushButton:hover {
                    background: rgba(78, 205, 196, 0.2);
                }
                QPushButton:pressed {
                    background: rgba(78, 205, 196, 0.3);
                }
            """),
            self.chat_input.setPlainText("🤖 Transcribing...")
        ])
 
        # --- Mic toggle function ---
        def toggle_voice_recording_btn():
            """Toggle voice recording on/off."""
            if not hasattr(self, 'voice_thread_btn'):
                return
 
            if self.voice_thread_btn.is_recording:
                self.voice_thread_btn.stop_recording()
            else:
                context = {
                    'generate_response': True,  # Ask Gemini for text response
                }
                self.voice_thread_btn.set_context(context)
                self.voice_thread_btn.start_recording()
 
        # --- Connect mic button ---
        self.speak_btn.clicked.connect(toggle_voice_recording_btn)
        
        # Note: New Chat button with text is now at top of Code Chat area (self.new_chat_btn_top)
        # Keeping self.new_chat_btn reference for backward compatibility
        self.new_chat_btn = self.new_chat_btn_top
        
        # Send button (far right, separate from container - larger size)
        self.send_chat_btn = QPushButton()
        self.send_chat_btn.setFixedSize(80, 80)
        self.send_chat_btn.setIcon(QIcon(resource_path("styles/Icon/sent_task.png")))
        self.send_chat_btn.setIconSize(QSize(60, 60))
        self.send_chat_btn.setToolTip("Send message")
        self.send_chat_btn.setStyleSheet("""
            QPushButton {
                background: transparent;
                border: none;
                border-radius: 16px;
                padding: 6px;
            }
            QPushButton:hover {
                background: rgba(78, 205, 196, 0.2);
            }
            QPushButton:pressed {
                background: rgba(78, 205, 196, 0.3);
            }
        """)
        self.send_chat_btn.clicked.connect(self.send_chat_message)
        
        # Layout for input container and send button (new chat button moved to top)
        input_row_layout = QHBoxLayout()
        input_row_layout.setSpacing(8)
        input_row_layout.addWidget(chat_input_container, 1)  # Expanding
        input_row_layout.addWidget(self.send_chat_btn)
        
        code_chat_layout.addLayout(input_row_layout)
        
        # Add Code Chat content to container
        content_container_layout.addWidget(self.code_chat_content)
        
        # XPath Variables content area (initially hidden)
        self.xpath_vars_content = QWidget()
        xpath_vars_layout = QVBoxLayout(self.xpath_vars_content)
        xpath_vars_layout.setContentsMargins(10, 10, 10, 5)
        xpath_vars_layout.setSpacing(8)
        
        # XPath header with controls (same as draggable_chat_panel)
        xpath_header_layout = QVBoxLayout()
        
        # ===== Title and Buttons Row =====
        title_row = QHBoxLayout()

        # Detect mode and set header text
        current_mode = getattr(self, 'current_automation_mode', 'web')
        if current_mode == 'desktop':
            header_text = "Attributes Configuration"
        elif current_mode == 'citrix':
            header_text = "Citrix Configuration"
        else:
            header_text = "XPath Configuration"
        self.xpath_header_label = QLabel(header_text)
        self.xpath_header_label.setStyleSheet("""
            QLabel {
                color: white;
                font-size: 16px;
                font-weight: bold;
                padding: 5px;
            }
        """)

        # ===== Clear All Button =====
        self.code_tab_clearall_xpath_btn = QPushButton()
        self.code_tab_clearall_xpath_btn.setFixedSize(32, 32)
        self.code_tab_clearall_xpath_btn.setToolTip("Clear all XPath entries")
        self.code_tab_clearall_xpath_btn.setIcon(QIcon(resource_path("styles/Icon/clearall.png")))
        self.code_tab_clearall_xpath_btn.setIconSize(QSize(20, 20))
        self.code_tab_clearall_xpath_btn.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                border: 1px solid #555555;
                border-radius: 16px;
                padding: 4px;
            }
            QPushButton:hover {
                background-color: rgba(255, 255, 255, 0.1);
                border-color: #ff5252;
            }
            QPushButton:pressed {
                background-color: rgba(255, 255, 255, 0.2);
                border-color: #e53935;
            }
        """)
        self.code_tab_clearall_xpath_btn.clicked.connect(self.clear_all_xpath_data)

        # ===== Save / Refresh Button =====
        self.code_tab_refresh_xpath_btn = QPushButton()
        self.code_tab_refresh_xpath_btn.setFixedSize(32, 32)
        tooltip_text = "Refresh attributes data" if current_mode == 'desktop' else "Refresh XPath data"
        self.code_tab_refresh_xpath_btn.setToolTip(tooltip_text)
        self.code_tab_refresh_xpath_btn.setIcon(QIcon(resource_path("styles/Icon/save_1.png")))
        self.code_tab_refresh_xpath_btn.setIconSize(QSize(20, 20))
        self.code_tab_refresh_xpath_btn.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                border: 1px solid #555555;
                border-radius: 16px;
                padding: 4px;
            }
            QPushButton:hover {
                background-color: rgba(255, 255, 255, 0.1);
                border-color: #17a2b8;
            }
            QPushButton:pressed {
                background-color: rgba(255, 255, 255, 0.2);
                border-color: #4CAF50;
            }
        """)
        self.code_tab_refresh_xpath_btn.clicked.connect(self.refresh_code_tab_xpath_data)
        # start_json_auto_monitor(self)

        # ===== Layout Order =====
        title_row.addWidget(self.xpath_header_label)
        title_row.addStretch()
        title_row.addWidget(self.code_tab_clearall_xpath_btn)  # ⬅ ClearAll on the left
        title_row.addWidget(self.code_tab_refresh_xpath_btn)   # ⬅ Save_1 on the right

        xpath_header_layout.addLayout(title_row)
        
        # Search bar
        self.code_tab_xpath_search = QLineEdit()
        # Make search placeholder mode-aware
        current_mode = getattr(self, 'current_automation_mode', 'web')
        if current_mode == 'desktop':
            placeholder_text = "🔍 Search attributes keys or values..."
        elif current_mode == 'citrix':
            placeholder_text = "🔍 Search citrix keys or values..."
        else:
            placeholder_text = "🔍 Search XPath keys or values..."
        self.code_tab_xpath_search.setPlaceholderText(placeholder_text)
        self.code_tab_xpath_search.setStyleSheet("""
            QLineEdit {
                background-color: #2d2d30;
                border: 2px solid #404040;
                border-radius: 6px;
                padding: 8px 12px;
                color: white;
                font-size: 13px;
                margin: 2px 0;
            }
            QLineEdit:focus {
                border-color: #17a2b8;
            }
            QLineEdit::placeholder {
                color: #888888;
            }
        """)
        self.code_tab_xpath_search.textChanged.connect(self.filter_code_tab_xpath_entries)
        xpath_header_layout.addWidget(self.code_tab_xpath_search)
        
        # Sort and filter controls
        controls_row = QHBoxLayout()
        
        # Sort dropdown
        self.code_tab_sort_combo = QComboBox()
        self.code_tab_sort_combo.addItems([
            "Sort by Keys A-Z",
            "Sort by Keys Z-A", 
            "Sort by Values A-Z",
            "Sort by Values Z-A"
        ])
        dropdown_style = """
            QComboBox {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #4a4a4a, stop:1 #3a3a3a);
                border: 1px solid #666666;
                border-radius: 8px;
                padding: 8px 16px 8px 12px;
                color: white;
                font-size: 12px;
                font-weight: 500;
                min-width: 120px;
                min-height: 16px;
            }
            QComboBox:hover {
                border-color: #17a2b8;
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #5a5a5a, stop:1 #4a4a4a);
            }
            QComboBox::drop-down {
                subcontrol-origin: padding;
                subcontrol-position: top right;
                width: 20px;
                border-left: 1px solid #666666;
                border-top-right-radius: 8px;
                border-bottom-right-radius: 8px;
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #5a5a5a, stop:1 #4a4a4a);
            }
            QComboBox::down-arrow {
                image: none;
                border-left: 4px solid transparent;
                border-right: 4px solid transparent;
                border-top: 5px solid #cccccc;
                margin: 0px 2px;
            }
            QComboBox QAbstractItemView {
                background-color: #404040;
                border: 1px solid #666666;
                border-radius: 6px;
                selection-background-color: #17a2b8;
                selection-color: white;
                color: white;
                font-size: 12px;
                padding: 2px;
                outline: none;
            }
            QComboBox QAbstractItemView::item {
                padding: 10px 12px;
                border-bottom: 1px solid #555555;
                min-height: 18px;
            }
            QComboBox QAbstractItemView::item:hover {
                background-color: #17a2b8;
                color: white;
            }
        """
        self.code_tab_sort_combo.setStyleSheet(dropdown_style)
        self.code_tab_sort_combo.currentTextChanged.connect(self.sort_code_tab_xpath_entries)
        
        # Filter dropdown
        self.code_tab_filter_combo = QComboBox()
        self.code_tab_filter_combo.addItems([
            "Show All",
            "Show Not_assigned Only",
            "Show Assigned Only"
        ])
        self.code_tab_filter_combo.setStyleSheet(dropdown_style)
        self.code_tab_filter_combo.currentTextChanged.connect(self.filter_code_tab_xpath_entries)
        
        controls_row.addWidget(QLabel("Sort:"))
        controls_row.addWidget(self.code_tab_sort_combo)
        controls_row.addWidget(QLabel("Filter:"))
        controls_row.addWidget(self.code_tab_filter_combo)
        controls_row.addStretch()
        
        # Style the labels
        for i in range(controls_row.count()):
            widget = controls_row.itemAt(i).widget()
            if isinstance(widget, QLabel):
                widget.setStyleSheet("color: #888888; font-size: 11px; font-weight: bold;")
        
        xpath_header_layout.addLayout(controls_row)
        xpath_vars_layout.addLayout(xpath_header_layout)
        
        # XPath display scroll area
        self.code_tab_xpath_display = QScrollArea()
        self.code_tab_xpath_display.setProperty('class', 'ChatDisplay')
        self.code_tab_xpath_display.setWidgetResizable(True)
        self.code_tab_xpath_display.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.code_tab_xpath_display.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        
        # XPath list widget
        self.code_tab_xpath_list_widget = QWidget()
        self.code_tab_xpath_list_layout = QVBoxLayout(self.code_tab_xpath_list_widget)
        self.code_tab_xpath_list_layout.setContentsMargins(5, 5, 5, 5)
        self.code_tab_xpath_list_layout.setSpacing(8)
        self.code_tab_xpath_list_layout.addStretch()
        
        self.code_tab_xpath_display.setWidget(self.code_tab_xpath_list_widget)
        xpath_vars_layout.addWidget(self.code_tab_xpath_display, 1)
        
        # XPath status label
        self.code_tab_xpath_status_label = QLabel("No XPath data available")
        self.code_tab_xpath_status_label.setStyleSheet("""
            QLabel {
                color: #888888;
                font-size: 12px;
                padding: 5px;
                text-align: center;
            }
        """)
        xpath_vars_layout.addWidget(self.code_tab_xpath_status_label)
        
        # Initially hide XPath Variables content
        self.xpath_vars_content.hide()
        content_container_layout.addWidget(self.xpath_vars_content)
        
        # Add content container to main chat area layout
        chat_area_layout.addWidget(self.code_tab_content_container)
        
        # Initialize XPath data for Code tab
        self.code_tab_xpath_data = {}
        self.code_tab_original_xpath_data = {}
        self.code_tab_filtered_xpath_data = {}
        
        # Add both areas to splitter
        self.code_chat_splitter.addWidget(code_area_widget)
        self.code_chat_splitter.addWidget(chat_area_widget)
        
        # Set initial sizes (60% code, 40% chat)
        self.code_chat_splitter.setSizes([600, 400])
        
        # Initialize chat variables
        self.attached_files = []
        self.chat_history = []
        
        code_layout.addWidget(self.code_chat_splitter)

        content_area.addTab(code_widget, "Code")
        
        # XPath Tab moved to draggable chat panel area
        
        # FlowChart Tab
        flowchart_tab_widget = QWidget()
        flowchart_tab_layout = QVBoxLayout(flowchart_tab_widget)
        
        # Create the comprehensive flowchart widget
        self.flowchart_widget = flowchart_widget.ComprehensiveFlowchartIDE()
        flowchart_tab_layout.addWidget(self.flowchart_widget)
        
        # Add controls for PDF export
        flowchart_controls = QHBoxLayout()
        # save_pdf_btn = QPushButton("💾 Save as PDF")
        # save_pdf_btn.clicked.connect(self.save_flowchart_as_pdf)
        # flowchart_controls.addWidget(save_pdf_btn)
        flowchart_controls.addStretch()
        flowchart_tab_layout.addLayout(flowchart_controls)
        
        content_area.addTab(flowchart_tab_widget, "FlowChart")
        # Code Builder Tab - Add this after the FlowChart tab section
        # from code_builder_widget import CodeBuilderWidget  # Import the widget
        # code_builder_widget = CodeBuilderWidget()

        # content_area.addTab(code_builder_widget, "Code Builder")
        
        # Enhanced Debug Terminal Tab
        terminal_widget = QWidget()
        terminal_layout = QVBoxLayout(terminal_widget)
        
        # Removed inner header for Debug Terminal to match unified tab look
        
        # Create enhanced debug terminal
        self.terminal_display = Debug_terminal.DebugTerminalWidget()
        terminal_layout.addWidget(self.terminal_display)
        
        # Connect debug control buttons
        self.terminal_display.step_btn.clicked.connect(self.step_into)
        self.terminal_display.continue_btn.clicked.connect(self.continue_execution)
        self.terminal_display.stop_btn.clicked.connect(self.stop_execution)
        
        # Debug info panel
        debug_info = QLabel("Debug Status: Ready")
        # debug_info.setProperty('class', 'DebugStatusLabel')
        style_loader.apply_stylesheet(debug_info)
        self.debug_status_label = debug_info
        terminal_layout.addWidget(debug_info)
        
        self.secondary_tabs.addTab(terminal_widget, "Debug Terminal")
        
        # =========================
        # Statistics Tab (cards UI) - Fixed Gradient Text
        # =========================
        stats_widget = QWidget()
        outer = QVBoxLayout(stats_widget)
        outer.setContentsMargins(16, 16, 16, 16)
        outer.setSpacing(16)
 
        grid = QGridLayout()
        grid.setHorizontalSpacing(20)
        grid.setVerticalSpacing(20)
        grid.setContentsMargins(0, 0, 0, 0)
 
        class GradientLabel(QLabel):
            def __init__(self, text="", gradient_colors=None, parent=None):
                super().__init__(text, parent)
                self.gradient_colors = gradient_colors or []
               
                # ✅ Use ultra-thin font weight for even thinner text
                font = QFont("Arial", 30)
                font.setWeight(10)  # Even thinner than QFont.Thin (100)
                self.setFont(font)
                self.setStyleSheet("background-color: transparent;")
 
            def setGradientColors(self, colors):
                self.gradient_colors = colors
                self.update()
 
            def paintEvent(self, event):
                if self.gradient_colors and len(self.gradient_colors) >= 2:
                    painter = QPainter(self)
                    painter.setRenderHint(QPainter.Antialiasing)
                    painter.setRenderHint(QPainter.TextAntialiasing)
 
                    # Create vertical gradient
                    gradient = QLinearGradient(0, 0, 0, self.height())
                    for i, color in enumerate(self.gradient_colors):
                        position = i / (len(self.gradient_colors) - 1)
                        gradient.setColorAt(position, QColor(color))
 
                    # ✅ Use gradient directly as pen (no brush, no border)
                    painter.setPen(QPen(QBrush(gradient), 0))
                    painter.setFont(self.font())
 
                    # Draw text normally (thin & clean)
                    painter.drawText(self.rect(), Qt.AlignLeft | Qt.AlignBottom, self.text())
                else:
                    super().paintEvent(event)
 
        def create_stat_card(icon_path: str, title: str, value_colors: list = None):
            card = QWidget()
            card.setObjectName("StatCard")
            card.setFixedSize(296, 150)
            card.setStyleSheet("""
                QWidget#StatCard {
                    background-color: #2a2a2a;
                    border-radius: 12px;
                    border: 1px solid #404040;
                }
                QLabel.StatTitle {
                    color: #ffffff;
                    font-size: 18px;
                    font-weight: 600;
                    background-color: transparent;
                }
            """)
 
            layout = QVBoxLayout(card)
            layout.setContentsMargins(16, 14, 16, 14)
            layout.setSpacing(0)
 
            # --- Title ---
            title_lbl = QLabel(title)
            title_lbl.setProperty("class", "StatTitle")
            layout.addWidget(title_lbl, alignment=Qt.AlignTop | Qt.AlignLeft)
 
            layout.addStretch(1)
 
            # --- Bottom row ---
            bottom = QHBoxLayout()
            bottom.setContentsMargins(0, 0, 0, 0)
 
            # Value with gradient text
            # Always use GradientLabel for consistent sizing
            value_lbl = GradientLabel("0", value_colors)
            if not value_colors or len(value_colors) == 1:
                # fallback: solid color (white or given) using same gradient logic
                color = value_colors[0] if value_colors else "#E4E4E4"
                value_lbl.setGradientColors([color, color])
 
 
            bottom.addWidget(value_lbl, alignment=Qt.AlignLeft | Qt.AlignBottom)
 
            # Icon with grey background
            icon_lbl = QLabel()
            icon_lbl.setStyleSheet("""
                background-color: transparent;
                border-radius: 8px;
                padding: 8px;
            """)
            icon_lbl.setFixedSize(56, 56)
            icon_lbl.setAlignment(Qt.AlignCenter)
 
            try:
                if os.path.exists(icon_path):
                    pixmap = QPixmap(icon_path).scaled(32, 32, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                    icon_lbl.setPixmap(pixmap)
                else:
                    # Fallback with better styling
                    icon_lbl.setText("□")
                    icon_lbl.setStyleSheet("""
                        background-color: transparent;
                        border-radius: 8px;
                        color: #888888;
                        font-size: 24px;
                        font-weight: bold;
                    """)
            except Exception:
                icon_lbl.setText("□")
                icon_lbl.setStyleSheet("""
                    background-color: transparent;
                    border-radius: 8px;
                    color: #888888;
                    font-size: 24px;
                    font-weight: bold;
                """)
 
            bottom.addWidget(icon_lbl, alignment=Qt.AlignRight | Qt.AlignBottom)
 
            layout.addLayout(bottom)
 
            return card, value_lbl
 
 
        # Create cards with gradient text colors
        card_tasks,   self.stat_tasks_val   = create_stat_card("styles/Icon/generated task.png",   "Total tasks processed", ["#5FCCF5", "#00BBF2", "#005B7F"])
 
        card_success, self.stat_success_val = create_stat_card("styles/Icon/success.png", "Success rate", ["#94F219", "#5A9310"])
 
        card_time,    self.stat_time_val    = create_stat_card("styles/Icon/time.png",    "Average process time", ["#5FCCF5", "#00BBF2", "#005B7F"])
 
        card_code,    self.stat_code_val    = create_stat_card("styles/Icon/code.png",    "Code lines generated", ["#E4E4E4"])
 
        card_debug,   self.stat_debug_val   = create_stat_card("styles/Icon/debug.png",   "Debug sessions", ["#5FCCF5", "#00BBF2", "#005B7F"])
 
        card_break,   self.stat_break_val   = create_stat_card("styles/Icon/break.png",   "Breakpoint hits", ["#E4E4E4"])
 
        # Arrange in 2-column grid
        grid.addWidget(card_tasks,   0, 0)
        grid.addWidget(card_success, 0, 1)
        grid.addWidget(card_time,    1, 0)
        grid.addWidget(card_code,    1, 1)
        grid.addWidget(card_debug,   2, 0)
        grid.addWidget(card_break,   2, 1)
 
        outer.addLayout(grid)
        outer.addStretch(1)
 
 
        # =========================
        # Refresh helper (keeps functionality same)
        # =========================
        def refresh_statistics_from_state():
            tasks       = getattr(self, "tasks_processed",        25.0)
            success     = getattr(self, "success_rate",           99.8)    # percent
            avg_time    = getattr(self, "avg_process_time",       32.0)  # seconds
            code_lines  = getattr(self, "code_lines_generated",   3400)
            debug_cnt   = getattr(self, "debug_sessions",         5)
            break_cnt   = getattr(self, "breakpoints_hit",        14)
 
            self.stat_tasks_val.setText(str(tasks))
            self.stat_success_val.setText(f"{success}%")
            try:
                self.stat_time_val.setText(f"{float(avg_time):.1f}s")
            except Exception:
                self.stat_time_val.setText(f"{avg_time}s")
            self.stat_code_val.setText(str(code_lines))
            self.stat_debug_val.setText(str(debug_cnt))
            self.stat_break_val.setText(str(break_cnt))
 
        refresh_statistics_from_state()
 
        self.secondary_tabs.addTab(stats_widget, "Stats")
 

        # --- MODIFICATION: Embed the AppMonitorWidget directly ---
        self.monitor_widget_instance = app_monitor_widget.AppMonitorWidget(self)
        self.secondary_tabs.addTab(self.monitor_widget_instance, "PIP")
        
        # Create horizontal layout for content area and chat panel
        content_chat_layout = QHBoxLayout()
        content_chat_layout.setContentsMargins(0, 0, 0, 0)
        content_chat_layout.setSpacing(0)
        
        # Add content container to layout
        content_chat_layout.addWidget(content_container, 1)  # Takes remaining space

        # Add chat panel to layout - REMOVED
        # content_chat_layout.addWidget(self.chat_panel, 0)  # Removed
        
        # Create container widget for the layout
        content_container = QWidget()
        content_container.setLayout(content_chat_layout)
        main_layout.addWidget(content_container)
    
    def attach_files(self):
        """Handle file attachment for code chat using proper file dialog"""
        dialog = QFileDialog(self)
        dialog.setWindowTitle("Select Files for Code Chat")
        dialog.setAcceptMode(QFileDialog.AcceptOpen)
        dialog.setFileMode(QFileDialog.ExistingFiles)
        
        # Set file filters for supported formats
        dialog.setNameFilters([
            "All Supported Files (*.pdf *.txt *.xlsx *.csv *.py *.doc *.docx)",
            "PDF Files (*.pdf)",
            "Text Files (*.txt)",
            "Excel Files (*.xlsx)",
            "CSV Files (*.csv)",
            "Python Files (*.py)",
            "Word Documents (*.doc *.docx)",
            "All Files (*)"
        ])
        
        if dialog.exec_() == QFileDialog.Accepted:
            selected_files = dialog.selectedFiles()
            if selected_files:
                self.attached_files = selected_files
                
                # Update attached files display
                file_names = [os.path.basename(f) for f in selected_files]
                if len(file_names) == 1:
                    display_text = f"📎 {file_names[0]}"
                else:
                    display_text = f"📎 {len(file_names)} files attached"
                
                self.attached_files_label.setText(display_text)
                self.attached_files_label.setStyleSheet("""
                    QLabel {
                        color: #4ECDC4;
                        font-size: 11px;
                        padding: 4px 8px;
                        background: rgba(78, 205, 196, 0.2);
                        border-radius: 4px;
                        margin-bottom: 8px;
                    }
                """)
                
                # Show remove button when files are attached
                self.code_remove_attachments_btn.show()

    def attach_task_files(self):
        """Handle file attachment for task chat using proper file dialog"""
        dialog = QFileDialog(self)
        dialog.setWindowTitle("Select Files for Task Chat")
        dialog.setAcceptMode(QFileDialog.AcceptOpen)
        dialog.setFileMode(QFileDialog.ExistingFiles)
        
        # Set file filters for supported formats
        dialog.setNameFilters([
            "All Supported Files (*.pdf *.txt *.xlsx *.csv *.py *.doc *.docx)",
            "PDF Files (*.pdf)",
            "Text Files (*.txt)",
            "Excel Files (*.xlsx)",
            "CSV Files (*.csv)",
            "Python Files (*.py)",
            "Word Documents (*.doc *.docx)",
            "All Files (*)"
        ])
        
        if dialog.exec_() == QFileDialog.Accepted:
            selected_files = dialog.selectedFiles()
            if selected_files:
                self.task_attached_files = selected_files
                
                # Update attached files display
                file_names = [os.path.basename(f) for f in selected_files]
                if len(file_names) == 1:
                    display_text = f"📎 {file_names[0]}"
                else:
                    display_text = f"📎 {len(file_names)} files attached"
                
                self.task_attached_files_label.setText(display_text)
                self.task_attached_files_label.setStyleSheet("""
                    QLabel {
                        color: #4ECDC4;
                        font-size: 11px;
                        padding: 4px 8px;
                        background: rgba(78, 205, 196, 0.2);
                        border-radius: 4px;
                    }
                """)
                
                # Show remove button when files are attached
                self.task_remove_attachments_btn.show()
    
    def remove_code_attachments(self):
        """Remove all attached files from code chat"""
        self.attached_files = []
        self.attached_files_label.setText("📎 No files attached")
        self.attached_files_label.setStyleSheet("""
            QLabel {
                color: #888888;
                font-size: 12px;
                padding: 5px;
                background: rgba(40, 45, 50, 0.6);
                border-radius: 4px;
                margin: 5px 0;
            }
        """)
        
        # Hide remove button when no files are attached
        self.code_remove_attachments_btn.hide()
    
    def remove_task_attachments(self):
        """Remove all attached files from task chat"""
        self.task_attached_files = []
        self.task_attached_files_label.setText("No files attached")
        self.task_attached_files_label.setStyleSheet("""
            QLabel {
                color: #888;
                font-size: 11px;
                padding: 4px 8px;
                background: rgba(255, 255, 255, 0.05);
                border-radius: 4px;
            }
        """)
        
        # Hide remove button when no files are attached
        self.task_remove_attachments_btn.hide()
    
    def send_chat_message(self):
        """Send chat message and get response from code_chat module - now threaded"""
        user_message = self.chat_input.toPlainText().strip()
        
        if not user_message:
            return
        
        # Check if chat thread is already running
        if hasattr(self, 'chat_thread') and self.chat_thread is not None and self.chat_thread.isRunning():
            print("[WARN] Chat thread already running, ignoring new request")
            self.add_chat_message("System", "Please wait for the current request to complete before sending another message.", is_user=False, is_error=True)
            return
        
        # Initialize both histories if they don't exist (for web mode only)
        if not hasattr(self, 'chat_history'):
            self.chat_history = []
        if not hasattr(self, 'ui_chat_history'):
            self.ui_chat_history = []
        
        # Get current code_log - ALWAYS fetch from UI code display to get latest code
        # This ensures we always have the most up-to-date code from the code tab
        if hasattr(self, 'code_display'):
            code_log = self.code_display.toPlainText()
            self.code_log = code_log  # Update self.code_log with current UI code
            print("[INFO] send_chat_message: Updated self.code_log from UI code display")
        else:
            code_log = getattr(self, 'code_log', getattr(self, 'final_code_log', ''))
        
        # Add user message to chat history
        self.add_chat_message("You", user_message, is_user=True)
        
        # Clear input
        self.chat_input.clear()
        
        # Set droid overlay to MODIFYING CODE state
        if hasattr(self, 'processing_widget') and self.processing_widget:
            self.processing_widget.set_modifying_code_state()
            print("[INFO] Set droid overlay to MODIFYING CODE state")
        
        # Store attached files for thread
        attached_files_copy = self.attached_files.copy()
        
        # Clear attached files immediately
        self.attached_files = []
        self.attached_files_label.setText("📎 No files attached")
        self.attached_files_label.setStyleSheet("""
            QLabel {
                color: #888888;
                font-size: 12px;
                padding: 5px;
                background: rgba(40, 45, 50, 0.6);
                border-radius: 4px;
                margin: 5px 0;
            }
        """)
        
        # Hide remove button when files are cleared
        self.code_remove_attachments_btn.hide()
        
        # Start threaded processing
        from PyQt5.QtCore import QThread, pyqtSignal
        class ChatProcessingThread(QThread):
            response_ready = pyqtSignal(str, str, str, object, object)  # response, res_msg, old_code, tasks, chat_history
            error_occurred = pyqtSignal(str)
            
            def __init__(self, code_log, user_message, attached_files, req_class, automation_mode='web', chat_history=None, parent=None):
                super().__init__()
                self.code_log = code_log
                self.user_message = user_message
                self.attached_files = attached_files
                self.req_class = req_class
                self.automation_mode = automation_mode
                self.chat_history = chat_history if chat_history is not None else []
                self.parent = parent  # Reference to parent AutomationApp instance for accessing UI
            
            def run(self):
                try:
                    print("[INFO] ChatProcessingThread: Starting chat processing...")
                    
                    # Import and call code_chat with error handling - mode-aware
                    try:
                        if self.automation_mode == 'desktop':
                            from datas.process_flow.desktop_process import desktop_code_chat
                            print("[INFO] ChatProcessingThread: Calling desktop_code_chat.chat_request...")
                            response, res_msg = desktop_code_chat.chat_request(self.code_log, self.user_message, self.attached_files)
                            updated_history = self.chat_history
                            print("[OK] ChatProcessingThread: Got response from desktop_code_chat")
                        elif self.automation_mode == 'citrix':
                            from datas.process_flow.Citrix_process import citrix_code_chat
                            print("[INFO] ChatProcessingThread: Calling citrix_code_chat.chat_request...")
                            response, res_msg = citrix_code_chat.chat_request(self.code_log, self.user_message, self.attached_files)
                            updated_history = self.chat_history
                            print("[OK] ChatProcessingThread: Got response from citrix_code_chat")
                        elif self.automation_mode == 'native':
                            from datas.process_flow.native_process import native_code_chat
                            print("[INFO] ChatProcessingThread: Calling native_code_chat.chat_request...")
                            response, res_msg = native_code_chat.chat_request(self.code_log, self.user_message, self.attached_files)
                            updated_history = self.chat_history
                            print("[OK] ChatProcessingThread: Got response from native_code_chat")
                        else:
                            # Web mode - use code_chat with history support
                            # IMPORTANT: Get fresh code from UI right before calling chat_request
                            if self.parent and hasattr(self.parent, 'code_display'):
                                self.code_log = self.parent.code_display.toPlainText()
                                print("[INFO] ChatProcessingThread: Refreshed code_log from UI code display before calling code_chat")
                            
                            import code_chat
                            print("[INFO] ChatProcessingThread: Calling code_chat.chat_request with chat history...")
                            result = code_chat.chat_request(self.code_log, self.user_message, self.attached_files, self.chat_history)
                            if len(result) == 3:
                                response, res_msg, updated_history = result
                            else:
                                response, res_msg = result
                                updated_history = self.chat_history
                            print("[OK] ChatProcessingThread: Got response from code_chat")
                        
                        old_code = self.code_log
                        
                        # Import and call task_modifier with error handling
                        try:
                            import task_modifier
                            print("[INFO] ChatProcessingThread: Calling task_modifier.gemini_response...")
                            tasks = task_modifier.gemini_response(self.req_class, old_code, response)
                            print("[OK] ChatProcessingThread: Got tasks from task_modifier")
                        except Exception as e:
                            print(f"[ERROR] ChatProcessingThread: Error in task_modifier: {e}")
                            # Continue without task modification if this fails
                            tasks = self.req_class
                        
                        print("[OK] ChatProcessingThread: Emitting response_ready signal with chat history")
                        self.response_ready.emit(response, res_msg, old_code, tasks, updated_history)
                        
                    except Exception as e:
                        print(f"[ERROR] ChatProcessingThread: Unexpected error: {e}")
                        import traceback
                        traceback.print_exc()
                        self.error_occurred.emit(f"Unexpected error: {str(e)}")
                except Exception as e:
                    print(f"[ERROR] ChatProcessingThread: Unexpected error: {e}")
                    import traceback
                    traceback.print_exc()
                    self.error_occurred.emit(f"Unexpected error: {str(e)}")
        
        # Create and start thread with current automation mode
        current_mode = getattr(self, 'current_automation_mode', 'web')
        self.chat_thread = ChatProcessingThread(code_log, user_message, attached_files_copy, self.req_class, current_mode, self.chat_history, parent=self)
        self.chat_thread.response_ready.connect(self.on_chat_response_ready)
        self.chat_thread.error_occurred.connect(self.on_chat_error)
        
        # Add timeout mechanism (60 seconds)
        self.chat_timeout_timer = QTimer()
        self.chat_timeout_timer.setSingleShot(True)
        self.chat_timeout_timer.timeout.connect(self.on_chat_timeout)
        self.chat_timeout_timer.start(300000)  # 5 minutes

        
        self.chat_thread.start()
        print("[INFO] Chat thread started with 60-second timeout")

    def attach_task_files(self):
        """Handle file attachment for task chat using proper file dialog"""
        dialog = QFileDialog(self)
        dialog.setWindowTitle("Select Files for Task Chat")
        dialog.setAcceptMode(QFileDialog.AcceptOpen)
        dialog.setFileMode(QFileDialog.ExistingFiles)
            
        # Set file filters for supported formats
        dialog.setNameFilters([
            "All Supported Files (*.pdf *.txt *.xlsx *.csv *.py *.doc *.docx)",
            "PDF Files (*.pdf)",
            "Text Files (*.txt)",
            "Excel Files (*.xlsx)",
            "CSV Files (*.csv)",
            "Python Files (*.py)",
            "Word Documents (*.doc *.docx)",
            "All Files (*)"
        ])
            
        if dialog.exec_() == QFileDialog.Accepted:
            selected_files = dialog.selectedFiles()
            if selected_files:
                self.task_attached_files = selected_files
                    
                # Update attached files display
                file_names = [os.path.basename(f) for f in selected_files]
                if len(file_names) == 1:
                    display_text = f" {file_names[0]}"
                else:
                    display_text = f" {len(file_names)} files attached"
                
                self.task_attached_files_label.setText(display_text)
                self.task_attached_files_label.setStyleSheet("""
                    QLabel {
                        color: #4ECDC4;
                        font-size: 11px;
                        padding: 4px 8px;
                        background: rgba(78, 205, 196, 0.2);
                        border-radius: 4px;
                    }
                """)
                
                # Show remove button when files are attached
                self.task_remove_attachments_btn.show()
        
    def remove_code_attachments(self):
        """Remove all attached files from code chat"""
        self.attached_files = []
        self.attached_files_label.setText(" No files attached")
        self.attached_files_label.setStyleSheet("""
            QLabel {
                color: #888888;
                font-size: 12px;
                padding: 5px;
                background: rgba(40, 45, 50, 0.6);
                border-radius: 4px;
                margin: 5px 0;
            }
        """)
            
        # Hide remove button when no files are attached
        self.code_remove_attachments_btn.hide()
        
    def remove_task_attachments(self):
        """Remove all attached files from task chat"""
        self.task_attached_files = []
        self.task_attached_files_label.setText("No files attached")
        self.task_attached_files_label.setStyleSheet("""
            QLabel {
                color: #888;
                font-size: 11px;
                padding: 4px 8px;
                background: rgba(255, 255, 255, 0.05);
                border-radius: 4px;
            }
        """)
            
        # Hide remove button when no files are attached
        self.task_remove_attachments_btn.hide()
        
        
    def on_chat_response_ready(self, response, res_msg, old_code, tasks, chat_history=None):
        """Handle successful chat response in main thread"""
        try:
            print("🔄 on_chat_response_ready: Processing chat response...")
            
            # Update chat history
            if chat_history is not None:
                self.chat_history = chat_history
                print(f"✅ Chat history updated with {len(self.chat_history)} messages")
            
            # Update self.code_log with the AI response
            self.code_log = response
            self.req_class = tasks
            
            # Update self.final_code_log with the AI response
            self.final_code_log = response
            
            # Update the Code tab display with AI response - with error handling
            try:
                # For QPlainTextEdit (CodeEditor), use setPlainText instead of append
                header = "#===User Modified Generated Code ===\n\n"
                full_text = header + response
                
                # Use push_state to add this to undo history
                self.code_display.push_state(full_text)
                self.code_display.setPlainText(full_text)
                
                # Move cursor to start so user sees the beginning
                cursor = self.code_display.textCursor()
                cursor.movePosition(cursor.Start)
                self.code_display.setTextCursor(cursor)
                
                print("✅ Code display updated successfully")
                
            except Exception as e:
                print(f"❌ Error updating code display: {e}")
                import traceback
                traceback.print_exc()
            
            # Call XPath correction to extract and update XPath variables from modified code
            try:
                self.update_xpath_from_modified_code(response)
                print("✅ XPath correction completed successfully")
            except Exception as e:
                print(f"❌ Error in XPath correction: {e}")
            
            # Add AI response to chat history
            try:
                self.add_chat_message("AI Assistant", res_msg, is_user=False)
                print("✅ AI response added to chat history")
            except Exception as e:
                print(f"❌ Error adding AI response to chat: {e}")

            # Update the Generated Tasks UI with modified tasks
            try:
                if hasattr(self, 'task_list') and self.task_list:
                    if type(tasks)==str:
                        import ast
                        tasks=ast.literal_eval(tasks)
                    print(f"🔄 TASK_MODIFIER: Updating Generated Tasks UI with {len(tasks)} modified tasks")
                    
                    # Reset all task colors to default white before updating
                    self.task_list.task_status.clear()
                    print("🔄 TASK_MODIFIER: Reset all task colors to default white")
                    
                    self.task_list.set_tasks_data(tasks)
                    print("✅ Generated Tasks UI updated successfully")
            except Exception as e:
                print(f"❌ Error updating Generated Tasks UI: {e}")
            
            # Set droid overlay back to PROCESS PENDING state
            try:
                if hasattr(self, 'processing_widget') and self.processing_widget:
                    self.processing_widget.set_process_pending_state()
                    print("✅ Set droid overlay back to PROCESS PENDING state")
            except Exception as e:
                print(f"❌ Error setting droid overlay state: {e}")
            
            # Enable Execute Flow button
            try:
                if hasattr(self, 'execute_flow_btn'):
                    self.execute_flow_btn.setEnabled(True)
                if hasattr(self, 'stop_flow_btn'):
                    self.stop_flow_btn.setEnabled(False)
            except Exception:
                pass
            
            # Clean up thread and timer
            try:
                if hasattr(self, 'chat_timeout_timer') and self.chat_timeout_timer is not None:
                    self.chat_timeout_timer.stop()
                    self.chat_timeout_timer = None
                    print("✅ Chat timeout timer stopped")
                
                if hasattr(self, 'chat_thread') and self.chat_thread is not None:
                    self.chat_thread.deleteLater()
                    self.chat_thread = None
                    print("✅ Chat thread cleaned up successfully")
            except Exception as e:
                print(f"❌ Error cleaning up chat thread: {e}")
            
            # Show code execution confirmation popup
            try:
                self.show_code_execution_confirmation()
                print("✅ Code execution confirmation popup shown")
            except Exception as e:
                print(f"❌ Error showing code execution confirmation: {e}")
                
        except Exception as e:
            print(f"❌ Critical error in on_chat_response_ready: {e}")
            import traceback
            traceback.print_exc()
            self.on_chat_error(f"Critical error processing response: {str(e)}")
            
    def on_chat_error(self, error_msg):
        """Handle chat processing error"""
        try:
            print(f"🔄 on_chat_error: Handling error: {error_msg}")
            
            # Format error message
            formatted_error = f"Error: {error_msg}"
            
            # Try to add error message to chat
            try:
                self.add_chat_message("System", formatted_error, is_user=False, is_error=True)
                print("✅ Error message added to chat")
            except Exception as e:
                print(f"❌ Failed to add error message to chat: {e}")
                # Show error in console if chat fails
                print(f"CHAT ERROR: {formatted_error}")
            
            # Set droid overlay back to PROCESS PENDING state on error
            try:
                if hasattr(self, 'processing_widget') and self.processing_widget:
                    self.processing_widget.set_process_pending_state()
                    print("❌ Set droid overlay back to PROCESS PENDING state after error")
            except Exception as e:
                print(f"❌ Failed to set droid overlay state: {e}")
            
            # Clean up thread and timer on error
            try:
                # Stop timeout timer
                if hasattr(self, 'chat_timeout_timer') and self.chat_timeout_timer is not None:
                    self.chat_timeout_timer.stop()
                    self.chat_timeout_timer = None
                    print("✅ Chat timeout timer stopped after error")
                
                # Clean up thread
                if hasattr(self, 'chat_thread') and self.chat_thread is not None:
                    self.chat_thread.deleteLater()
                    self.chat_thread = None
                    print("✅ Chat thread cleaned up after error")
            except Exception as e:
                print(f"❌ Error cleaning up chat thread after error: {e}")
                
        except Exception as e:
            print(f"❌ Critical error in on_chat_error: {e}")
            import traceback
            traceback.print_exc()
            # Last resort: show message box if everything else fails
            try:
                from PyQt5.QtWidgets import QMessageBox
                QMessageBox.critical(self, "Chat Error", f"Chat processing failed: {error_msg}")
            except:
                pass  # If even message box fails, just log to console
    
    def show_code_execution_confirmation(self):
        """Show confirmation popup for code execution after chat modification"""
        try:
            # Create and show the confirmation popup
            popup = CodeExecutionConfirmationPopup(self)
            result = popup.exec_()
            
            if result == QDialog.Accepted:
                # User clicked Yes - directly call execute_code method instead of clicking button
                print("✅ User confirmed code execution - triggering execute_code method")
                self.execute_code()
                print("✅ Execute code method called automatically")
            else:
                # User clicked No or closed popup - reset button and overlay states
                print("❌ User declined code execution or closed popup")
                
                # Reset execute button to normal state
                self.set_execute_button_normal_state()
                self.stop_btn.setEnabled(False)
                
                # Reset droid overlay to waiting state
                if hasattr(self, 'processing_widget') and self.processing_widget:
                    self.processing_widget.set_waiting_state()
                    print("⏳ Reset droid overlay to WAITING state after popup cancellation")
                
        except Exception as e:
            print(f"❌ Error in show_code_execution_confirmation: {e}")
            import traceback
            traceback.print_exc()
            
            # Reset states on error
            self.set_execute_button_normal_state()
            self.stop_btn.setEnabled(False)
            if hasattr(self, 'processing_widget') and self.processing_widget:
                self.processing_widget.set_waiting_state()

    def on_chat_timeout(self):
        """Handle chat processing timeout"""
        try:
            print("⏰ Chat processing timeout - terminating thread")
            
            # Terminate the thread if it's still running
            if hasattr(self, 'chat_thread') and self.chat_thread is not None:
                if self.chat_thread.isRunning():
                    self.chat_thread.terminate()
                    self.chat_thread.wait(5000)  # Wait up to 5 seconds for termination
                self.chat_thread.deleteLater()
                self.chat_thread = None
            
            # Stop the timer
            if hasattr(self, 'chat_timeout_timer') and self.chat_timeout_timer is not None:
                self.chat_timeout_timer.stop()
                self.chat_timeout_timer = None
            
            # Show timeout error
            self.add_chat_message("System", "Chat request timed out after 5 Minutes. Please try again with a shorter message.", is_user=False, is_error=True)
            
            # Reset droid overlay
            if hasattr(self, 'processing_widget') and self.processing_widget:
                self.processing_widget.set_process_pending_state()
                print("⏰ Set droid overlay back to PROCESS PENDING state after timeout")
                
        except Exception as e:
            print(f"❌ Error handling chat timeout: {e}")

    def add_chat_message(self, sender, message, is_user=False, is_error=False):
        """Add a message to the chat history using widget-based approach like draggable_chat_panel"""
        from datetime import datetime
        timestamp = datetime.now().strftime("%H:%M")
        
        # Process message to split long continuous words
        message = self._split_long_words(message, max_word_length=20)
        
        # Create message widget
        msg_widget = QWidget()
        msg_layout = QHBoxLayout(msg_widget)
        msg_layout.setContentsMargins(0, 0, 0, 0)
        
        # Just show the message content without sender labels or timestamps
        display_text = message
        
        # Message bubble
        bubble = QLabel(display_text)
        bubble.setWordWrap(True)
        bubble.setTextInteractionFlags(Qt.TextSelectableByMouse)
        
        if is_user:
            # User message styling - right aligned with cyan gradient (matching draggable_chat_panel)
            bubble.setStyleSheet(f"""
                QLabel {{
                    background: qlineargradient(x1:0, y1:1, x2:0, y2:0,
                                                stop:0 #5FCCF5,
                                                stop:0.2855 #00BBF2,
                                                stop:0.993 #005B7F);
                    color: #FFFFFF;
                    border-radius: {20 if len(message) > 5 else 15}px;
                    padding: 8px 16px;
                    font-family: 'Asen Pro';
                    font-weight: 600;
                    font-size: 14px;
                    letter-spacing: 0.05em;
                    word-break: break-word;
                    white-space: pre-wrap;
                    overflow-wrap: break-word;
                }}
            """)
            bubble.setMaximumWidth(800)  # Increased from 500 to 800 for much wider user messages
            msg_layout.addStretch()
            msg_layout.addWidget(bubble)
        else:
            # AI message styling - left aligned with transparent background (matching draggable_chat_panel)
            bg_color = "transparent" if not is_error else "#d32f2f"
            bubble.setStyleSheet(f"""
                QLabel {{
                    background: {bg_color};
                    color: #FFFFFF;
                    font-family: 'Asen Pro';
                    font-style: normal;
                    font-weight: 600;
                    font-size: 14px;
                    line-height: 21px;
                    letter-spacing: 0.02em;
                    padding: 4px 0;
                    border-radius: {"8px" if is_error else "0px"};
                    word-break: break-word;
                    white-space: pre-wrap;
                    overflow-wrap: break-word;
                }}
            """)
            bubble.setMaximumWidth(1000)  # Increased from 700 to 1000 for much wider AI messages
            msg_layout.addWidget(bubble)
            msg_layout.addStretch()
        
        # Insert before stretch (at the end of messages)
        self.chat_messages_layout.insertWidget(
            self.chat_messages_layout.count() - 1, msg_widget
        )
        
        # Scroll to bottom
        QTimer.singleShot(100, self.scroll_chat_to_bottom)
        
        # Store in UI chat history list (for display purposes only)
        if not hasattr(self, 'ui_chat_history'):
            self.ui_chat_history = []
        
        self.ui_chat_history.append({
            'sender': sender,
            'message': message,
            'timestamp': timestamp,
            'is_user': is_user,
            'is_error': is_error
        })
        
        # Store in Gemini-formatted history (for API purposes only)
        if not hasattr(self, 'chat_history'):
            self.chat_history = []
        
        # Only add actual message exchanges to Gemini history (not system messages or errors)
        if not is_error and sender != "System":
            role = "user" if is_user else "model"
            # Store in Gemini-compatible format as a dictionary
            self.chat_history.append({
                "role": role,
                "parts": [{"text": message}]
            })
    
    def scroll_chat_to_bottom(self):
        """Scroll chat to bottom"""
        scrollbar = self.chat_display.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())
        
        # QTimer.singleShot(200, self.position_drag_button)  # Removed
        # QTimer.singleShot(300, lambda: self.drag_controls_widget.raise_())  # Removed
    
    def handle_chat_click(self, event):
        """Handle clicks on chat messages - no longer needed with widget approach"""
        pass
    
    def show_expanded_message(self, sender, message):
        """Show expanded message in popup dialog"""
        try:
            from message_popup import MessagePopup
            popup = MessagePopup(f"{sender} - Full Response", message, self)
            popup.exec_()
        except Exception as e:
            print(f"❌ Error showing expanded message: {e}")
            import traceback
            traceback.print_exc()

    def eventFilter(self, obj, event):
        """Handle key events for chat inputs - Enter to send"""
        if event.type() == event.KeyPress:
            if event.key() == Qt.Key_Return or event.key() == Qt.Key_Enter:
                # Check if Shift is pressed - if so, allow new line
                if event.modifiers() & Qt.ShiftModifier:
                    return False  # Let the default behavior handle it (new line)
                else:
                    # Send message on Enter without Shift
                    if obj == self.task_chat_input:
                        self.send_task_chat_message() #send_task_chat_message()
                        return True  # Event handled
                    elif obj == self.chat_input:
                        self.send_chat_message()
                        return True  # Event handled
        return super().eventFilter(obj, event)

    def send_task_chat_message(self):
        """Send task chat message and restructure tasks - now threaded"""
        user_message = self.task_chat_input.toPlainText().strip()
        
        if not user_message:
            return
        
        # Check if task restructure thread is already running
        if hasattr(self, 'task_restructure_thread') and self.task_restructure_thread is not None and self.task_restructure_thread.isRunning():
            print("⚠️ Task restructure thread already running, ignoring new request")
            self.add_task_chat_message("System", "Please wait for the current task restructuring to complete before sending another message.", is_user=False, is_error=True)
            return
        
        # Add user message to task chat history
        self.add_task_chat_message("You", user_message, is_user=True)
        
        # Clear input
        self.task_chat_input.clear()
        
        # Set droid overlay to OUTPUTTING state
        if hasattr(self, 'processing_widget') and self.processing_widget:
            self.processing_widget.set_outputting_state()
            print("🔄 Set droid overlay to OUTPUTTING state for task restructuring")
        
        # Store attached files for processing
        attached_files_copy = self.task_attached_files.copy()
        
        # Clear attached files immediately
        self.task_attached_files = []
        self.task_attached_files_label.setText("No files attached")
        self.task_attached_files_label.setStyleSheet("""
            QLabel {
                color: #888;
                font-size: 11px;
                padding: 4px 8px;
                background: rgba(255, 255, 255, 0.05);
                border-radius: 4px;
            }
        """)
        
        # Hide remove button when files are cleared
        self.task_remove_attachments_btn.hide()
        
        # Start threaded task restructuring
        from PyQt5.QtCore import QThread, pyqtSignal
        
        class TaskRestructureThread(QThread):
            restructure_completed = pyqtSignal(str, str, object)  # chat_message, validation_message, updated_history
            error_occurred = pyqtSignal(str)
            
            def __init__(self, user_message, attached_files, req_class, gemini_service, task_chat_history=None):
                super().__init__()
                self.user_message = user_message
                self.attached_files = attached_files
                self.req_class = req_class
                self.gemini_service = gemini_service
                self.task_chat_history = task_chat_history if task_chat_history is not None else []
            
            def run(self):
                try:
                    print("🔄 TaskRestructureThread: Starting task restructuring...")
                    
                    # Call task restructuring with error handling
                    try:
                        from customize_task import gemini_response
                        print("🔄 TaskRestructureThread: Calling customize_task.gemini_response with chat history...")
                        
                        # Prepare file paths list - empty if no files attached
                        file_paths = self.attached_files if self.attached_files else []
                        print(f"🔄 TaskRestructureThread: Attached files: {file_paths}")
                        
                        # Call with history for continuity
                        result = gemini_response(self.user_message, self.req_class, file_paths, self.task_chat_history)
                        
                        # Handle both old (just tasks) and new (tasks, history) return formats
                        if isinstance(result, tuple) and len(result) == 2:
                            new_tasks, updated_history = result
                            print("✅ TaskRestructureThread: Got new tasks and updated history from customize_task")
                        else:
                            new_tasks = result
                            updated_history = self.task_chat_history
                            print("✅ TaskRestructureThread: Got new tasks from customize_task (no history)")
                    except Exception as e:
                        print(f"❌ TaskRestructureThread: Error in task restructuring: {e}")
                        self.error_occurred.emit(f"Task restructuring error: {str(e)}")
                        return
                    
                    # Get friendly response from Gemini
                    try:
                        from task_response_msg import friendly_response
                        chat_window_message = friendly_response(self.user_message)
                        print(f"🤖 TaskRestructureThread: Gemini validation message: {chat_window_message}")
                    except Exception as e:
                        print(f"❌ TaskRestructureThread: Error getting Gemini message: {e}")
                        chat_window_message = "Hey there! Let me quickly validate these tasks for you. This won't take long!"
                    
                    print("✅ TaskRestructureThread: Emitting restructure_completed signal with updated history")
                    self.restructure_completed.emit(str(new_tasks), chat_window_message, updated_history)
                    
                except Exception as e:
                    print(f"❌ TaskRestructureThread: Unexpected error: {e}")
                    import traceback
                    traceback.print_exc()
                    self.error_occurred.emit(f"Unexpected error: {str(e)}")
        
        # Create and start thread with chat history
        self.task_restructure_thread = TaskRestructureThread(user_message, attached_files_copy, self.req_class, self.gemini_service, self.task_chat_history)
        self.task_restructure_thread.restructure_completed.connect(self.on_task_restructure_completed)
        self.task_restructure_thread.error_occurred.connect(self.on_task_restructure_error)
        
        # Add timeout mechanism (10 minutes)
        self.task_restructure_timeout_timer = QTimer()
        self.task_restructure_timeout_timer.setSingleShot(True)
        self.task_restructure_timeout_timer.timeout.connect(self.on_task_restructure_timeout)
        self.task_restructure_timeout_timer.start(600000)  # 10 minutes
        
        self.task_restructure_thread.start()
        print("🔄 Task restructure thread started with 10-minute timeout")
    
    def on_task_restructure_completed(self, new_tasks_str, chat_window_message, updated_history=None):
        """Handle successful task restructuring in main thread"""
        try:
            print("🔄 on_task_restructure_completed: Processing task restructuring response...")
            
            # Update chat history from thread
            if updated_history is not None:
                self.task_chat_history = updated_history
                print(f"✅ Updated task_chat_history with {len(updated_history)} entries from Gemini")
            
            # Parse new tasks
            try:
                no_steps_flag=False
                import ast
                if isinstance(new_tasks_str, str):
                    try:
                        new_tasks = ast.literal_eval(new_tasks_str)
                    except Exception as e:
                        import re
                        match = re.search(r"(\[.*\])", new_tasks_str, re.DOTALL)
                        tasks_only = match.group(1) if match else ""
                        new_tasks_str=tasks_only
                        new_tasks = ast.literal_eval(new_tasks_str)

                else:
                    new_tasks = new_tasks_str
                    
                # Validate response is a list
                if isinstance(new_tasks, list) and len(new_tasks) > 0:
                    # Update self.req_class with new tasks
                    old_task_count = len(self.req_class)
                    self.req_class = new_tasks
                    
                    # Update the task list UI
                    if hasattr(self, 'task_list') and self.task_list:
                        self.task_list.set_tasks_data(self.req_class)
                        print(f"✅ Task list UI updated with {len(new_tasks)} steps")
                    
                    print(f"✅ Tasks restructured successfully! {old_task_count} → {len(new_tasks)} steps")
                else:
                    raise ValueError("No Steps Found")
                    no_steps_flag=True
                    
            except Exception as e:
                import traceback
                print(f"❌ Error parsing new tasks: {e}")
                if no_steps_flag:
                    self.on_task_restructure_error(f"{str(e)}")
                else:
                    self.on_task_restructure_error(f"{str(traceback.format_exc())}")
                return
            
            # Speak the validation message first (if unified popup exists)
            try:
                if hasattr(self, 'unified_popup') and self.unified_popup:
                    self.unified_popup.speak_validation_message(chat_window_message)
            except Exception as e:
                print(f"❌ Error speaking validation message: {e}")

            # Add AI response to task chat
            try:
                self.add_task_chat_message("AI Assistant", chat_window_message, is_user=False)
                print("✅ AI response added to task chat history")
            except Exception as e:
                print(f"❌ Error adding AI response to task chat: {e}")
            
            # Set droid overlay back to OFF state
            try:
                if hasattr(self, 'processing_widget') and self.processing_widget:
                    self.processing_widget.set_off_state()
                    print("✅ Set droid overlay back to OFF state after task restructuring")
            except Exception as e:
                print(f"❌ Error setting droid overlay state: {e}")
            
            # Clean up thread and timer
            try:
                # Stop timeout timer
                if hasattr(self, 'task_restructure_timeout_timer') and self.task_restructure_timeout_timer is not None:
                    self.task_restructure_timeout_timer.stop()
                    self.task_restructure_timeout_timer = None
                    print("✅ Task restructure timeout timer stopped")
                
                # Clean up thread
                if hasattr(self, 'task_restructure_thread') and self.task_restructure_thread is not None:
                    self.task_restructure_thread.deleteLater()
                    self.task_restructure_thread = None
                    print("✅ Task restructure thread cleaned up successfully")
            except Exception as e:
                print(f"❌ Error cleaning up task restructure thread: {e}")
                
        except Exception as e:
            print(f"❌ Critical error in on_task_restructure_completed: {e}")
            import traceback
            traceback.print_exc()
            self.on_task_restructure_error(f"Critical error processing response: {str(traceback.format_exc())}")
    
    def on_task_restructure_error(self, error_msg):
        """Handle task restructuring error"""
        try:
            print(f"🔄 on_task_restructure_error: Handling error: {error_msg}")
            
            # Format error message
            formatted_error = f"Error Occured During Steps Restructuring : {error_msg}"
            
            # Try to add error message to task chat
            try:
                self.add_task_chat_message("System", formatted_error, is_user=False, is_error=True)
                print("✅ Error message added to task chat")
            except Exception as e:
                print(f"❌ Failed to add error message to task chat: {e}")
                # Show error in console if chat fails
                print(f"TASK CHAT ERROR: {formatted_error}")
            
            # Set droid overlay back to OFF state on error
            try:
                if hasattr(self, 'processing_widget') and self.processing_widget:
                    self.processing_widget.set_off_state()
                    print("❌ Set droid overlay back to OFF state after task restructuring error")
            except Exception as e:
                print(f"❌ Failed to set droid overlay state: {e}")
            
            # Clean up thread and timer on error
            try:
                # Stop timeout timer
                if hasattr(self, 'task_restructure_timeout_timer') and self.task_restructure_timeout_timer is not None:
                    self.task_restructure_timeout_timer.stop()
                    self.task_restructure_timeout_timer = None
                    print("✅ Task restructure timeout timer stopped after error")
                
                # Clean up thread
                if hasattr(self, 'task_restructure_thread') and self.task_restructure_thread is not None:
                    self.task_restructure_thread.deleteLater()
                    self.task_restructure_thread = None
                    print("✅ Task restructure thread cleaned up after error")
            except Exception as e:
                print(f"❌ Error cleaning up task restructure thread after error: {e}")
                
        except Exception as e:
            print(f"❌ Critical error in on_task_restructure_error: {e}")
            import traceback
            traceback.print_exc()
            # Last resort: show message box if everything else fails
            try:
                from PyQt5.QtWidgets import QMessageBox
                QMessageBox.critical(self, "Task Restructure Error", f"Task restructuring failed: {error_msg}")
            except Exception:
                pass
    
    def on_task_restructure_timeout(self):
        """Handle task restructuring timeout"""
        try:
            print("⏰ Task restructuring timeout - terminating thread")
            
            # Terminate the thread if it's still running
            if hasattr(self, 'task_restructure_thread') and self.task_restructure_thread is not None:
                if self.task_restructure_thread.isRunning():
                    self.task_restructure_thread.terminate()
                    self.task_restructure_thread.wait(5000)  # Wait up to 5 seconds for termination
                self.task_restructure_thread.deleteLater()
                self.task_restructure_thread = None
            
            # Stop the timer
            if hasattr(self, 'task_restructure_timeout_timer') and self.task_restructure_timeout_timer is not None:
                self.task_restructure_timeout_timer.stop()
                self.task_restructure_timeout_timer = None
            
            # Show timeout error
            self.add_task_chat_message("System", "Task restructuring timed out after 10 minutes. Please try again with a shorter message or check your connection.", is_user=False, is_error=True)
            
            # Reset droid overlay
            if hasattr(self, 'processing_widget') and self.processing_widget:
                self.processing_widget.set_off_state()
                print("⏰ Set droid overlay back to OFF state after task restructuring timeout")
                
        except Exception as e:
            print(f"❌ Error handling task restructuring timeout: {e}")

    def _split_long_words(self, text, max_word_length=20):
        """Split long continuous words by inserting spaces"""
        words = text.split(' ')
        result = []
        
        for word in words:
            if len(word) > max_word_length:
                # Split the word into chunks and rejoin with spaces
                chunks = []
                for i in range(0, len(word), max_word_length):
                    chunks.append(word[i:i + max_word_length])
                result.append(' '.join(chunks))
            else:
                result.append(word)
        
        return ' '.join(result)

    def add_task_chat_message(self, sender, message, is_user=False, is_error=False):
        """Add a message to the task chat history (both UI and Gemini format)"""
        from datetime import datetime
        timestamp = datetime.now().strftime("%H:%M")
        
        # Process message to split long continuous words
        message = self._split_long_words(message, max_word_length=35)
        
        # Create message widget
        msg_widget = QWidget()
        msg_layout = QHBoxLayout(msg_widget)
        msg_layout.setContentsMargins(0, 0, 0, 0)
        
        # Just show the message content without sender labels or timestamps
        display_text = message
        
        # Message bubble
        bubble = QLabel(display_text)
        bubble.setWordWrap(True)
        bubble.setTextInteractionFlags(Qt.TextSelectableByMouse)
        
        if is_user:
            # User message styling - right aligned with cyan gradient (matching code chat)
            bubble.setStyleSheet(f"""
                QLabel {{
                    background: qlineargradient(x1:0, y1:1, x2:0, y2:0,
                                                stop:0 #5FCCF5,
                                                stop:0.2855 #00BBF2,
                                                stop:0.993 #005B7F);
                    color: #FFFFFF;
                    border-radius: 20px;
                    padding: 8px 16px;
                    font-family: 'Asen Pro';
                    font-weight: 600;
                    font-size: 14px;
                    letter-spacing: 0.05em;
                    word-break: break-word;
                    white-space: normal;
                    overflow-wrap: break-word;
                }}
            """)
            bubble.setMaximumWidth(600)
            msg_layout.addStretch()
            msg_layout.addWidget(bubble)
        else:
            # AI message styling - left aligned with transparent background (matching code chat)
            bg_color = "transparent" if not is_error else "#d32f2f"
            border_radius = "8px" if is_error else "0px"
            bubble.setStyleSheet(f"""
                QLabel {{
                    background: {bg_color};
                    color: #FFFFFF;
                    font-family: 'Asen Pro';
                    font-style: normal;
                    font-weight: 600;
                    font-size: 14px;
                    line-height: 21px;
                    letter-spacing: 0.02em;
                    padding: 4px 0;
                    border-radius: {border_radius};
                    word-break: break-word;
                    white-space: normal;
                    overflow-wrap: break-word;
                }}
            """)
            bubble.setMaximumWidth(700)
            msg_layout.addWidget(bubble)
            msg_layout.addStretch()
        
        # Insert before stretch (at the end of messages)
        self.task_chat_layout.insertWidget(
            self.task_chat_layout.count() - 1, msg_widget
        )
        
        # Scroll to bottom
        QTimer.singleShot(100, self.scroll_task_chat_to_bottom)
        
        # Store in UI task chat history list
        self.ui_task_chat_history.append({
            'sender': sender,
            'message': message,
            'timestamp': timestamp,
            'is_user': is_user,
            'is_error': is_error
        })
        
        # Store in Gemini-compatible format for chat continuity (skip system/error messages)
        if is_user or (sender and sender not in ["System", "Error"]):
            role = "user" if is_user else "model"
            self.task_chat_history.append({
                "role": role,
                "parts": [{"text": message}]
            })
    
    def scroll_task_chat_to_bottom(self):
        """Scroll task chat to bottom"""
        scrollbar = self.task_chat_display.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())

    # def position_drag_button(self):  # REMOVED - drag functionality disabled
    #     """Position drag controls widget based on chat panel state and position"""
    #     # Method removed as part of drag controls cleanup
 
                
            
    # def move_drag_left(self):  # REMOVED - drag functionality disabled
    #     """Handle drag left button click - toggle chat panel visibility"""
    #     # Method removed as part of drag controls cleanup
        
    # def move_drag_right(self):  # REMOVED - drag functionality disabled
    #     """Handle drag right button click - toggle chat panel visibility"""
    #     # Method removed as part of drag controls cleanup
        
    # def _reposition_after_toggle(self):  # REMOVED - drag functionality disabled
    #     """Reposition drag button after tab group toggle"""
    #     # Method removed as part of drag controls cleanup
        
    def handle_chat_message(self, message):
        """Handle chat message sent from the draggable panel - now for general chat only"""
        try:
            # Note: Task restructuring functionality has been moved to Generated Tasks tab
            # This draggable chat panel is now for general conversation only
            
            # Add user message to draggable chat - REMOVED
            # self.chat_panel.add_message(message, is_user=True)  # Removed
            
            # Add a simple response indicating the chat functionality change
            response_message = (
                "Hi! For task restructuring, please use the chat in the Generated Tasks tab. "
                "This chat panel is now for general conversation and XPath management."
            )
            
            # Add AI response to draggable chat - REMOVED
            # QTimer.singleShot(1000, lambda: self.chat_panel.add_message(response_message, is_user=False))  # Removed
            
        except Exception as e:
            # self.chat_panel.add_message(f"Error processing request: {str(e)}", is_user=False)  # Removed
            print(f"❌ Error in handle_chat_message: {e}")
            
    def on_chat_panel_shown(self):
        """Handle when chat panel is shown"""
        # QTimer.singleShot(50, self.position_drag_button)  # Removed
            
    def on_chat_panel_hidden(self):
        """Handle when chat panel is hidden"""
        # Reposition drag button when chat panel is hidden - REMOVED
        # QTimer.singleShot(50, self.position_drag_button)  # Removed
        # Also reposition when width changes - REMOVED
        # QTimer.singleShot(50, self.position_drag_button)  # Removed
        
    def on_chat_width_changed(self, new_width):
        """Handle when chat panel width is changed by dragging"""
        # Reposition drag button immediately when chat panel moves - REMOVED
        # self.position_drag_button()  # Removed
        print(f"Chat panel width changed to: {new_width}px")
    
    def on_chat_position_changed(self):
        """Handle when chat panel position changes during dragging"""
        # Reposition drag button immediately for synchronous movement - REMOVED
        # self.position_drag_button()  # Removed
            
    def restructure_tasks_from_chat(self, message):
        """Process task restructuring from chat message"""
        # Use the existing restructure_tasks method but with chat message
        self.task_restructure_input.setPlainText(message)
        self.restructure_tasks()
        
        try:
            friendly_response = self.gemini_service.get_chat_window_message(message)
            chat_window_message = friendly_response["message"]
            print(f"🤖 Gemini validation message: {chat_window_message}")
        except Exception as e:
            print(f"Error getting Gemini message: {e}")
            chat_window_message = "Hey there! Let me quickly validate these tasks for you. This won't take long!"
        
        # Speak the validation message first
        self.unified_popup.speak_validation_message(chat_window_message)

        # self.chat_panel.add_message(chat_window_message, is_user=False)  # Removed
        
        # Set to OFF state when chat response is received
        if hasattr(self, 'processing_widget'):
            self.processing_widget.set_off_state()
        
    def position_chat_button(self):
        """Position chat toggle button on right edge - REMOVED"""
        # Chat toggle button functionality moved to drag buttons
        pass
            
    def _delayed_position_button(self):
        """Delayed positioning after layout is ready"""
        if hasattr(self, 'chat_toggle_btn') and hasattr(self, 'content_area'):
            # Get content area geometry
            content_width = self.content_area.width()
            content_height = self.content_area.height()
            
            # Position at right edge of content area
            x = content_width - 30  # 30px from right edge
            y = (content_height - 80) // 2  # Vertically centered
            
            self.chat_toggle_btn.move(x, y)
            self.chat_toggle_btn.raise_()
            self.chat_toggle_btn.show()
            print(f"Chat button positioned at ({x}, {y})")
        
    def resizeEvent(self, event):
        """Handle window resize to reposition buttons"""
        super().resizeEvent(event)
        if hasattr(self, 'chat_toggle_btn'):
            # Reposition chat toggle button on right edge
            self.chat_toggle_btn.position_on_edge()
        # if hasattr(self, 'drag_toggle_btn'):  # REMOVED
        #     # Reposition drag button when window resizes
        #     QTimer.singleShot(50, self.position_drag_button)  # Removed


    # --- MODIFICATION: Remove the launch function ---
    # def launch_app_monitor(self): ... (This function is no longer needed)

    # --- MODIFICATION: Update closeEvent to clean up the widget ---
    def closeEvent(self, event):
        """Handle close event with save confirmation dialog (only if project & task selected)"""
        print("🔄 Main window close event triggered...")
        
        # Check if project and task are selected
        has_project = hasattr(self, 'selected_project_id') and self.selected_project_id
        has_task = hasattr(self, 'selected_task_id') and self.selected_task_id
        
        # If neither project nor task is selected, close directly without confirmation
        if not has_project or not has_task:
            print("⚠️ No project or task selected - closing directly without confirmation...")
            self._perform_cleanup_and_close(event)
            return
        
        # Show close confirmation dialog only if project and task are selected
        close_dialog = CloseConfirmationDialog(self)
        result = close_dialog.exec_()
        
        # Check user's choice through result_value
        if close_dialog.result_value is True:
            # User wants to save changes
            print("💾 User chose to save changes before closing...")
            try:
                # Call the save functionality WITHOUT showing confirmation popup
                self.saveoption_no_confirmation()
                print("✅ Changes saved successfully")
            except Exception as e:
                print(f"❌ Error saving changes: {e}")
                import traceback
                traceback.print_exc()
            
            # Proceed with cleanup and close
            self._perform_cleanup_and_close(event)
        
        elif close_dialog.result_value is False:
            # User wants to discard changes
            print("🚫 User chose to discard changes and close...")
            # Proceed with cleanup and close without saving
            self._perform_cleanup_and_close(event)
        
        else:
            # Dialog was closed with X button or ESC - don't close app, keep it open
            print("🔙 User cancelled - app remains open...")
            event.ignore()
    
    def _perform_cleanup_and_close(self, event):
        """Perform cleanup operations and close the application"""
        print("🔄 Performing cleanup before closing...")
        
        # Stop PDF processing thread if running
        if hasattr(self, 'pdf_thread') and self.pdf_thread and self.pdf_thread.isRunning():
            self.pdf_thread.stop_processing()
        
        # Stop execution worker thread if running
        if hasattr(self, 'execute_worker') and self.execute_worker is not None:
            print("🔄 Stopping execution worker thread...")
            self.execute_worker.stop_execution()
            if self.execute_worker.isRunning():
                if not self.execute_worker.wait(3000):  # Wait 3 seconds
                    print("⚠️ Force terminating execution worker...")
                    self.execute_worker.terminate()
                    self.execute_worker.wait(1000)  # Wait 1 more second
            self.execute_worker = None
        
        # Stop sync worker thread if running
        if hasattr(self, 'sync_worker') and self.sync_worker is not None:
            print("🔄 Stopping sync worker thread...")
            self.sync_worker.stop_sync()
            if self.sync_worker.isRunning():
                if not self.sync_worker.wait(2000):  # Wait 2 seconds
                    print("⚠️ Force terminating sync worker...")
                    self.sync_worker.terminate()
                    self.sync_worker.wait(1000)  # Wait 1 more second
            self.sync_worker = None
        
        # Close all status popups when main app closes
        # Status popup removed - no cleanup needed
        
        # Close ALL child windows and dialogs
        try:
            from PyQt5.QtWidgets import QApplication
            for widget in QApplication.topLevelWidgets():
                try:
                    # Skip the main window itself
                    if widget == self:
                        continue
                        
                    if widget and widget.isVisible():
                        widget_class = widget.__class__.__name__
                        widget_title = getattr(widget, 'windowTitle', lambda: 'Unknown')()
                        
                        print(f"🔄 Closing child window: {widget_class} - {widget_title}")
                        
                        # Force close the widget
                        widget.close()
                        widget.deleteLater()
                        
                except Exception as e:
                    print(f"⚠️ Error closing child widget: {e}")
        except Exception as e:
            print(f"⚠️ Error finding child widgets: {e}")
        
        # Existing cleanup code
        if self.monitor_widget_instance:
            self.monitor_widget_instance.cleanup_on_close()
        
        # Ensure application quits completely
        QApplication.instance().quit()
        
        super().closeEvent(event)
    
    def cleanup_on_quit(self):
        """Cleanup method called when application is about to quit"""
        print("🔄 Application quitting - cleaning up all popups and dialogs...")
        
        # Status popup removed - no cleanup needed
        
        # Close all remaining child windows
        try:
            from PyQt5.QtWidgets import QApplication
            for widget in QApplication.topLevelWidgets():
                try:
                    if widget != self and widget.isVisible():
                        print(f"🔄 Force closing remaining widget: {widget.__class__.__name__}")
                        widget.close()
                        widget.deleteLater()
                except Exception as e:
                    print(f"⚠️ Error closing remaining widget: {e}")
        except Exception as e:
            print(f"⚠️ Error during final cleanup: {e}")
        
        # Close all detail mode dialogs
        try:
            from PyQt5.QtWidgets import QApplication
            for widget in QApplication.topLevelWidgets():
                try:
                    if widget and hasattr(widget, 'windowTitle'):
                        title = widget.windowTitle()
                        if "Detail Mode" in title or "Validation Logs" in title:
                            print(f"🔄 Closing detail mode dialog during quit: {title}")
                            widget.close()
                            widget.deleteLater()
                except Exception as e:
                    print(f"⚠️ Error closing detail mode dialog during quit: {e}")
        except Exception as e:
            print(f"⚠️ Error finding detail mode dialogs during quit: {e}")
        
        print("✅ Cleanup completed")
        
    def copy_code(self):
        """Copy code to clipboard"""
        clipboard = QApplication.clipboard()
        clipboard.setText(self.code_display.toPlainText())
        self.log_message("📋 Code copied to clipboard")
        
    def clear_all(self,popup_state=False):
        """Clear all data and reset the application"""
        if not popup_state:
            reply = QMessageBox.question(self, 'Clear All',
                                    'Are you sure you want to clear all data?',
                                    QMessageBox.Yes | QMessageBox.No,
                                    QMessageBox.No)
           
            if reply == QMessageBox.Yes:
                popup_state = True
       
        if popup_state:
            self.player_confirm.stop()
            self.player_confirm.play()
 
            self.stop_execution()  
            if hasattr(self, 'task_processor') and self.task_processor is not None and self.task_processor.isRunning():
                stop_thread = threading.Thread(target=self._stop_execution_thread)
                stop_thread.start()
                stop_thread.join()
                
            self.requirement_input.clear()
            self.flowchart_widget.canvas.set_flowchart_data([])
            self.flowchart_widget.off_download_button()
            self.task_list.clear()
            self.task_list.add_bottom_add_step_button()
            self.task_list.clear_breakpoints()
            self.debug_state.task_applications.clear()
            self.log_display.clear()
            self.code_display.clear()
            self.terminal_display.clear()
            self.file_path_label.clear()
            self.selected_file_path = None
            self.terminal_display.clear_highlights()
            self.req_class = []
            self.task_events=[]
            self.tasks_data = []
            self.full_task_info=[]
            self.debug_state.reset()
            self.start_btn.setEnabled(False)
            self.generate_code_btn.setEnabled(False)
            self.clear_btn.setEnabled(False)  # Disable clear button after clearing
            self.update_tasks_status("Ready", "#4CAF50")
            
            # Reset selected project and task to clear the display
            self.selected_project_name = None
            self.selected_task_name = None
            self.selected_project_id = None
            self.selected_task_id = None
            
            # Update the display to reflect the cleared state
            self.update_project_task_display()
           
            # Clear task chat input and data
            self.task_chat_input.clear()
            self.task_attached_files.clear()
            self.task_chat_history.clear()
     
            import json
            import os
               
            json_files = [
                "json_info/json_xpath.json",
                "json_info/json_attr.json"
            ]
               
            for json_file in json_files:
                try:
                    # Ensure directory exists
                    os.makedirs(os.path.dirname(json_file), exist_ok=True)
                       
                    # Write empty JSON object
                    with open(json_file, 'w', encoding='utf-8') as f:
                        json.dump({}, f, indent=4)
                           
                    print(f"Cleared {json_file}")
                except Exception as e:
                    print(f"Error clearing {json_file}: {e}")                  
               
            self.refresh_code_tab_xpath_data()
     
            # Clear task chat messages layout
            if hasattr(self, 'task_chat_layout'):
                while self.task_chat_layout.count() > 0:
                    item = self.task_chat_layout.takeAt(0)
                    if item:
                        widget = item.widget()
                        if widget:
                            widget.deleteLater()
     
                self.task_chat_layout.addStretch()
     
            # Reset task chat attached files label and button
            if hasattr(self, 'task_attached_files_label'):
                self.task_attached_files_label.setText("No files attached")
           
        if hasattr(self, 'task_remove_attachments_btn'):
            self.task_remove_attachments_btn.hide()
 
        # Clear code chat input
        self.chat_input.clear()
       
        # Clear code chat messages widget
        if hasattr(self, 'chat_messages_layout'):
            while self.chat_messages_layout.count() > 0:
                item = self.chat_messages_layout.takeAt(0)
                if item:
                    widget = item.widget()
                    if widget:
                        widget.deleteLater()
            self.chat_messages_layout.addStretch()
           
        # Clear attached files for code chat
        if hasattr(self, 'code_attached_files'):
            self.code_attached_files.clear()
           
        # Reset code chat attached files label
        if hasattr(self, 'attached_files_label'):
            self.attached_files_label.setText("📎 No files attached")
           
        # Hide code chat remove attachments button
        if hasattr(self, 'code_remove_attachments_btn'):
            self.code_remove_attachments_btn.hide()
                   
        self.log_message("✓ Application reset successfully")
 
    def on_code_display_requested(self, code_str):
        """Handle code display request"""
        self.terminal_display.display_code_with_highlighting(code_str, 0)
        self.terminal_display.enable_debug_mode()

    def on_pdb_waiting_for_input(self):
        """Handle PDB waiting for user input"""
        self.terminal_display.enable_debug_controls()
        self.debug_status_label.setText("Debug Status: PDB waiting for input...")

    def on_pdb_output_received(self, output):
        """Handle PDB output"""
        self.terminal_display.append_pdb_output(output)

    def step_into(self):
        """Handle step into button - sends 's' command to PDB"""
        if self.terminal_display.is_pdb_active:
            print(" DEBUG: Step Into clicked - sending 's' command to PDB")
            
            self.debug_state.debug_action = "stepinto"
            self.debug_state.execution_paused = False
            
            # Wake up PDB
            self.debug_state.mutex.lock()
            self.debug_state.wait_condition.wakeAll()
            self.debug_state.mutex.unlock()
            
            self.debug_status_label.setText("Debug Status: Stepping...")

    def continue_execution(self):
        """Handle continue button - sends 'c' command to PDB"""
        if self.terminal_display.is_pdb_active:
            print(" DEBUG: Continue clicked - sending 'c' command to PDB")
            
            self.debug_state.debug_action = "continue"
            self.debug_state.execution_paused = False
            
            # Wake up PDB
            self.debug_state.mutex.lock()
            self.debug_state.wait_condition.wakeAll()
            self.debug_state.mutex.unlock()
            
            self.debug_status_label.setText("Debug Status: Continuing...")

    def pause_execution(self):
        if self.task_processor.isRunning():
            self.task_processor.should_pause = True
            self.pause_btn.setText("▶️ RESUME")
            self.pause_btn.clicked.disconnect()
            self.pause_btn.clicked.connect(self.resume_execution)

    def resume_execution(self):
        if self.task_processor.isRunning():
            self.task_processor.should_pause = False
            
            self.task_processor._pause_condition.wakeAll()
            self.pause_btn.setText("⏸️ PAUSE")
            self.pause_btn.clicked.disconnect()
            self.pause_btn.clicked.connect(self.pause_execution)

    # def stop_execution(self):
    #     """Handle stop button click in a separate thread"""

    #     if hasattr(self, 'task_processor') and self.task_processor is not None and self.task_processor.isRunning():

    #         # Create a new thread for stopping execution

    #         stop_thread = threading.Thread(target=self._stop_execution_thread)

    #         stop_thread.start()
    def _stop_execution_thread(self):

        """Helper method to stop execution in a separate thread"""

        try:

            if hasattr(self, 'task_processor') and self.task_processor is not None and self.task_processor.isRunning():

                # Set stop flag

                self.task_processor.request_stop()

                self.task_processor.should_pause = False

                # Wait for the processor to finish

                self.task_processor.wait()

                print("🛑 Execution stopped")



                # Update UI in the main thread

                def update_ui():

                    # self.progress_bar.setVisible(False)

                    # Reset button states

                    self.pause_btn.setText("⏸️ PAUSE")

                    self.pause_btn.clicked.disconnect()

                    self.pause_btn.clicked.connect(self.pause_execution)

                    self.debug_status_label.setText("Debug Status: Stopped")

                    self.terminal_display.append("[STOP] ⏹️ Execution stopped by user")

                    self.task_processor = None  # Reset task_processor after stopping



                # Schedule UI update in the main thread

                QApplication.instance().postEvent(self, QEvent(QEvent.User))

                self.customEvent = lambda event: update_ui()

        except Exception as e:

            print(f"❌ Error stopping execution: {str(e)}")

            # Ensure task_processor is reset even if an error occurs

            def update_ui():

                self.task_processor = None

                # self.progress_bar.setVisible(False)

                self.debug_status_label.setText("Debug Status: Stopped")

                self.terminal_display.append("[STOP] ⏹️ Execution stopped due to error")

            QApplication.instance().postEvent(self, QEvent(QEvent.User))

            self.customEvent = lambda event: update_ui()

    def start_pdf_processing(self):
        """Start PDF processing in a separate thread"""
        
        # Disable UI elements during processing
        self.process_btn.setEnabled(False)
        self.process_btn.setText("🔄 Processing...")
        
        # Show progress bar
        # if hasattr(self, 'progress_bar'):
        #     self.progress_bar.setVisible(True)
        #     self.progress_bar.setRange(0, 0)  # Indeterminate progress
        
        # Create and start the PDF processing thread
        self.pdf_thread = PDFProcessingThread(self.selected_file_path, self)
        
        # Connect thread signals to UI update methods
        self.pdf_thread.processing_started.connect(self.on_pdf_processing_started)
        self.pdf_thread.processing_finished.connect(self.on_pdf_processing_finished)
        self.pdf_thread.processing_error.connect(self.on_pdf_processing_error)
        self.pdf_thread.processing_progress.connect(self.on_pdf_processing_progress)
        
        # Start the thread
        self.pdf_thread.start()

    def on_pdf_processing_started(self):
        """Handle PDF processing start"""
        self.log_message(f"🔄 Processing file: {self.selected_file_path}")
        self.statusBar().showMessage("Processing file requirements...")

    def on_pdf_processing_progress(self, message):
        """Handle PDF processing progress updates"""
        self.log_message(message)
        # Status message removed - no status bar in frameless window

    def on_pdf_processing_finished(self, req_class):
        """Handle successful PDF processing completion"""
        try:
            # Update the requirements class
            self.req_class = req_class
            
            # Update task list display
            self.update_task_list()
            
            self.log_message(f"✅ Generated {len(self.req_class)} steps successfully from file")
            self.start_btn.setEnabled(True)
            self.statusBar().showMessage(f"Ready - {len(self.req_class)} steps generated from file")
            
            # Show success message
            QMessageBox.information(
                self, 
                "✅ Success", 
                f"PDF processed successfully!\nGenerated {len(self.req_class)} steps."
            )
            
        except Exception as e:
            self.on_pdf_processing_error(f"Error handling PDF results: {str(e)}")
        finally:
            self.cleanup_pdf_processing()

    def on_pdf_processing_error(self, error_message):
        """Handle PDF processing errors"""
        QMessageBox.critical(self, "❌ Error", error_message)
        self.log_message(f"❌ Error: {error_message}")
        self.statusBar().showMessage("Error occurred during file processing")
        self.cleanup_pdf_processing()

    def cleanup_pdf_processing(self):
        """Clean up after PDF processing is complete"""
        # Re-enable UI elements
        self.process_btn.setEnabled(True)
        # self.process_btn.setText("🔄 Process Requirements")
        
        # Hide progress bar
        # if hasattr(self, 'progress_bar'):
        #     self.progress_bar.setVisible(False)
        
        # Clean up thread reference
        if hasattr(self, 'pdf_thread') and self.pdf_thread:
            self.pdf_thread.deleteLater()
            self.pdf_thread = None
        
    def create_xpath_tab(self, content_area):
        """Create XPath tab with editable JSON data"""
        xpath_widget = QWidget()
        xpath_layout = QVBoxLayout(xpath_widget)
        
        # Header with refresh button
        header_layout = QHBoxLayout()
        header_label = QLabel("XPath Configuration")
        header_label.setStyleSheet("""
            QLabel {
                color: white;
                font-size: 18px;
                font-weight: bold;
                padding: 10px;
            }
        """)
        
        refresh_xpath_btn = QPushButton(" Refresh XPath")
        refresh_xpath_btn.setFixedSize(130, 35)
        refresh_xpath_btn.setIcon(QIcon(resource_path("styles/Icon/Refresh.png")))
        refresh_xpath_btn.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:1, x2:0, y2:0,
                                        stop:0 #005B7F, stop:1 #008AB3);
                border-radius: 10px;
                color: #FFFFFF;
                font-family: 'Asen Pro', sans-serif;
                font-weight: 600;
                font-size: 12px;
                letter-spacing: 0.05em;
                text-align: center;
                border: none;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:1, x2:0, y2:0,
                                        stop:0 #006B8F, stop:1 #009AC3);
            }
            QPushButton:pressed {
                background: qlineargradient(x1:0, y1:1, x2:0, y2:0,
                                        stop:0 #004B6F, stop:1 #007A93);
            }
        """)
        refresh_xpath_btn.clicked.connect(self.refresh_xpath_tab)
        
        header_layout.addWidget(header_label)
        header_layout.addStretch()
        header_layout.addWidget(refresh_xpath_btn)
        xpath_layout.addLayout(header_layout)
        
        # Scroll area for XPath entries
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll_area.setStyleSheet("""
            QScrollArea {
                background-color: #1e1e1e;
                border: 1px solid #3c3c3c;
                border-radius: 6px;
            }
        """)
        
        # Container for XPath entries
        self.xpath_container = QWidget()
        self.xpath_entries_layout = QVBoxLayout(self.xpath_container)
        self.xpath_entries_layout.setSpacing(10)
        self.xpath_entries_layout.setContentsMargins(15, 15, 15, 15)
        
        scroll_area.setWidget(self.xpath_container)
        xpath_layout.addWidget(scroll_area)
        
        # Store reference for refreshing
        self.xpath_tab_widget = xpath_widget
        
        # Load initial data
        self.refresh_xpath_tab()
        
        content_area.addTab(xpath_widget, "XPath/Attributes")
    
    def refresh_xpath_tab(self):
        """Refresh XPath/Attributes tab with current JSON data based on automation mode"""
        import json
        import os
        
        # Clear existing entries
        for i in reversed(range(self.xpath_entries_layout.count())):
            child = self.xpath_entries_layout.itemAt(i).widget()
            if child:
                child.setParent(None)
        
        # Determine which JSON file to load based on current automation mode
        current_mode = getattr(self, 'current_automation_mode', 'web')
        
        if current_mode == 'desktop':
            # Desktop mode - load attributes JSON
            json_path = "json_info/json_attr.json"
            data_type = "Attributes"
        elif current_mode == 'citrix':
            # Citrix mode - load citrix data JSON
            json_path = "json_info/citrix_data.json"
            data_type = "Citrix"
        else:
            # Web/Native modes - load XPath JSON
            json_path = "json_info/json_xpath.json"
            data_type = "XPath"
        
        json_data = {}
        
        if os.path.exists(json_path):
            try:
                with open(json_path, "r", encoding="utf-8") as f:
                    json_data = json.load(f)
            except Exception as e:
                print(f"Error loading {data_type} JSON: {e}")
        
        if not json_data:
            # Show message when no data available
            no_data_label = QLabel(f"No {data_type} data available.\nProcess a requirement to generate {data_type} configuration.")
            no_data_label.setAlignment(Qt.AlignCenter)
            no_data_label.setStyleSheet("""
                QLabel {
                    color: #888888;
                    font-size: 14px;
                    padding: 50px;
                    background-color: #2a2a2a;
                    border-radius: 8px;
                    border: 2px dashed #404040;
                }
            """)
            self.xpath_entries_layout.addWidget(no_data_label)
            return
        
        # Create editable entries for each key-value pair
        for key, value in json_data.items():
            self.create_xpath_entry(key, value)
        
        # Add stretch to push entries to top
        self.xpath_entries_layout.addStretch()
    
    def create_xpath_entry(self, key, value):
        """Create an editable XPath entry"""
        entry_frame = QFrame()
        entry_frame.setStyleSheet("""
            QFrame {
                background-color: #2a2a2a;
                border: 1px solid #404040;
                border-radius: 8px;
                padding: 10px;
                margin: 5px 0;
            }
        """)
        
        entry_layout = QVBoxLayout(entry_frame)
        entry_layout.setSpacing(8)
        
        # Key label (non-editable)
        key_label = QLabel(f"🔑 {key}")
        key_label.setStyleSheet("""
            QLabel {
                color: #4CAF50;
                font-weight: bold;
                font-size: 14px;
                padding: 5px;
            }
        """)
        entry_layout.addWidget(key_label)
        
        # Value input with button container
        value_container = QHBoxLayout()
        value_container.setSpacing(5)
        value_container.setContentsMargins(0, 0, 0, 0)
        
        # Value input (editable)
        value_input = QLineEdit(value)
        value_input.setStyleSheet("""
            QLineEdit {
                background-color: #1e1e1e;
                color: #ffffff;
                border: 1px solid #555555;
                border-radius: 4px;
                padding: 8px;
                font-family: 'Consolas', monospace;
                font-size: 12px;
            }
            QLineEdit:focus {
                border-color: #0ea5e9;
            }
        """)
        
        # Set mode-aware placeholder text
        current_mode = getattr(self, 'current_automation_mode', 'web')
        if current_mode == 'desktop':
            value_input.setPlaceholderText("Enter attribute value...")
        elif current_mode == 'citrix':
            value_input.setPlaceholderText("Enter citrix data value...")
        else:
            value_input.setPlaceholderText("Enter XPath value...")
        
        # Ensure field is editable (explicitly set)
        value_input.setReadOnly(False)
        
        # Connect to update function for real-time saving
        value_input.textChanged.connect(lambda text, k=key: self.update_xpath_value(k, text))
        value_input.editingFinished.connect(lambda k=key: self.update_xpath_value(k, value_input.text()))
        
        value_container.addWidget(value_input, 1)
        
        # Dynamic XPath button (only for web mode)
        current_mode = getattr(self, 'current_automation_mode', 'web')
        if current_mode == 'web':
            dynamic_xpath_btn = QPushButton()
            dynamic_xpath_btn.setFixedSize(32, 32)
            dynamic_xpath_btn.setCursor(Qt.PointingHandCursor)
            
            # SVG Icon for dynamic XPath
            svg_data = b'''<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="#fbf9f9" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="lucide lucide-trending-up-down-icon lucide-trending-up-down"><path d="M14.828 14.828 21 21"/><path d="M21 16v5h-5"/><path d="m21 3-9 9-4-4-6 6"/><path d="M21 8V3h-5"/></svg>'''
            from PyQt5.QtSvg import QSvgRenderer
            from PyQt5.QtCore import QByteArray
            
            renderer = QSvgRenderer(QByteArray(svg_data))
            pixmap = QPixmap(24, 24)
            pixmap.fill(Qt.transparent)
            painter = QPainter(pixmap)
            renderer.render(painter)
            painter.end()
            
            dynamic_xpath_btn.setIcon(QIcon(pixmap))
            dynamic_xpath_btn.setStyleSheet("""
                QPushButton {
                    background-color: transparent;
                    border: 1px solid #555555;
                    border-radius: 4px;
                    padding: 4px;
                }
                QPushButton:hover {
                    background-color: #363636;
                    border-color: #4a9eff;
                }
                QPushButton:pressed {
                    background-color: #2a2a2a;
                }
            """)
            
            # Connect button to dynamic XPath dialog
            dynamic_xpath_btn.clicked.connect(lambda checked, k=key, v=value: self.show_dynamic_xpath_dialog(k, v))
            value_container.addWidget(dynamic_xpath_btn)
        
        entry_layout.addLayout(value_container)
        
        # Status indicator
        status_label = QLabel("✅ Saved" if value != "Not_assigned" else "⚠️ Not assigned")
        status_label.setStyleSheet("""
            QLabel {
                color: #888888;
                font-size: 11px;
                padding: 2px 5px;
            }
        """)
        entry_layout.addWidget(status_label)
        
        self.xpath_entries_layout.addWidget(entry_frame)
    
    def update_xpath_value(self, key, value):
        """Update XPath/Attributes value in JSON file based on current automation mode"""
        import json
        import os
        
        # Determine which JSON file to update based on current automation mode
        current_mode = getattr(self, 'current_automation_mode', 'web')
        
        if current_mode == 'desktop':
            # Desktop mode - update attributes JSON
            json_path = "json_info/json_attr.json"
            data_type = "Attributes"
        elif current_mode == 'citrix':
            # Citrix mode - update citrix data JSON
            json_path = "json_info/citrix_data.json"
            data_type = "Citrix"
        else:
            # Web/Native modes - update XPath JSON
            json_path = "json_info/json_xpath.json"
            data_type = "XPath"
        
        try:
            # Load current data
            json_data = {}
            if os.path.exists(json_path):
                with open(json_path, "r", encoding="utf-8") as f:
                    json_data = json.load(f)
            
            # Update value
            json_data[key] = value
            
            # Save back to file
            os.makedirs("json_info", exist_ok=True)
            with open(json_path, "w", encoding="utf-8") as f:
                json.dump(json_data, f, indent=4)
            
            print(f"✅ Updated {data_type} {key}: {value}")
            
        except Exception as e:
            print(f"❌ Error updating {data_type} value: {e}")

    def show_dynamic_xpath_dialog(self, xpath_key, current_value):
        """Show a frameless draggable dialog for dynamic XPath input"""
        dialog = DynamicXPathDialog(xpath_key, current_value, self)
        dialog.exec_()
    
    def implement_dynamic_xpath(self, xpath_key, dynamic_xpath_value):
        """
        Implement dynamic XPath by:
        1. Calling append_after_keyword function
        2. Loading updated code from execute_code.py
        3. Updating the code tab in real-time
        4. Showing success notification with GIF
        """
        loading_dialog = None
        try:
            from datas.source_files.dynamic_xpath_code_correction import append_after_keyword
            import os
            
            # Show loading indicator with buffer GIF - GIF only, no text
            loading_dialog = LoadingIndicatorDialog("Processing Dynamic XPath...", resource_path("styles/gif/Trail loading.gif"), self)
            loading_dialog.show()
            QApplication.processEvents()  # Allow UI to update
            
            # Call the append_after_keyword function
            updated_code = append_after_keyword(xpath_key, dynamic_xpath_value,self.userid)
            import os
            org_path=os.getcwd()
            Task_file=os.path.join(org_path,"json_info/task_info.json")
            with open(Task_file, "r", encoding="utf-8") as f:
                task_info = json.load(f)
            proj_name=task_info["Proj_file_name"]
            task_name=task_info["Task_file_name"]

            file_path = f"{proj_name}/{task_name}/{xpath_key}.py"
            import os
            if os.path.exists(file_path):
                os.remove(file_path)
            # Save the updated code to execute_code.py
            code_py_path = "code_py/execute_code.py"
            os.makedirs("code_py", exist_ok=True)
            with open(code_py_path, "w", encoding="utf-8") as f:
                f.write(updated_code)
            
            print(f"💾 Saved updated code to {code_py_path}")
            
            # Update the code tab with the new content in real-time
            if hasattr(self, 'code_display') and self.code_display:
                self.code_display.push_state(updated_code)
                self.code_display.setPlainText(updated_code)
                self.code_display.ensureCursorVisible()
                print(f"✅ Code display updated with {len(updated_code)} characters")
                QApplication.processEvents()  # Refresh UI immediately
            else:
                print("⚠️ code_display widget not found")
            
            import ast
            try:
                temp_data=ast.literal_eval(dynamic_xpath_value)
                if "xpath" in temp_data and "iframe" in temp_data:
                    dynamic_xpath_value=temp_data
            except:
                pass
            # Update the XPath Variables tab with the new dynamic value
            if hasattr(self, 'code_tab_xpath_data') and self.code_tab_xpath_data is not None:
                self.code_tab_xpath_data[xpath_key] = dynamic_xpath_value
                self.code_tab_original_xpath_data[xpath_key] = dynamic_xpath_value
                # Save to JSON
                self.save_code_tab_xpath_data()
                # Refresh the display
                self.filter_code_tab_xpath_entries()
                print(f"✅ XPath Variables tab updated for {xpath_key}")
            
            # Close loading dialog
            if loading_dialog:
                loading_dialog.close()
                loading_dialog.deleteLater()
                QApplication.processEvents()
            
            # Show success notification with GIF
            self.show_dynamic_xpath_success(xpath_key)
            
            print(f"✅ Dynamic XPath implementation completed for {xpath_key}")
            
        except Exception as e:
            print(f"❌ Error implementing dynamic XPath: {e}")
            import traceback
            traceback.print_exc()
            
            # Close loading dialog on error
            if loading_dialog:
                try:
                    loading_dialog.close()
                    loading_dialog.deleteLater()
                except:
                    pass
            
            QMessageBox.critical(self, "Error", f"Failed to implement dynamic XPath:\n\n{str(e)}")
    
    def show_dynamic_xpath_success(self, xpath_key):
        """Show a temporary success notification with GIF for dynamic XPath"""
        notification = DynamicXPathSuccessNotificationGif(xpath_key, self)
        notification.show()

    def process_requirement(self):
        # Check which input method is selected
        try:
            print("Button Click Function gets called")
            
            if self.manual_radio.isChecked():
                # Manual input processing - NOW IN SEPARATE THREAD
                initial_input = self.requirement_input.toPlainText().strip()
                if not initial_input:
                    self.show_custom_warning("Warning", "Please enter a requirement first!")
                    return
                    
                self.log_message("🔄 Starting manual task generation...")
                self.process_btn.setEnabled(False)
                # Set task generating state when Enter & Process is clicked
                if hasattr(self, 'processing_widget'):
                    self.processing_widget.set_task_generating_state()
                
                # Start manual task generation in separate thread
                self.start_threaded_manual_generation(initial_input)
                    
            elif self.file_radio.isChecked():
                print("File Upload Button Checked")
                
                # File upload processing - NOW IN SEPARATE THREAD
                if not self.selected_file_path:
                    self.show_custom_warning("Warning", "Please select a file first!")
                    return
                self.log_message(f"🔄 Starting file task generation...")
                self.process_btn.setEnabled(False)
                # Set task generating state when Upload & Progress is clicked
                if hasattr(self, 'processing_widget'):
                    self.processing_widget.set_task_generating_state()
                
                # Start file task generation in separate thread
                self.start_threaded_file_generation(self.selected_file_path)
        except Exception as e:
            import traceback
            error_msg = f"Button processing failed: {str(e)}\n\nTraceback:\n{traceback.format_exc()}"
            print(f"❌ Exception on Processing: {error_msg}")
            
            # Show user-friendly error message with custom popup
            self.show_custom_error("Processing Error", 
                            f"Failed to process your request:\n\n{str(e)}\n\nPlease try again or contact support if the issue persists.")
            
            # Reset UI state
            self.process_btn.setEnabled(True)
            if hasattr(self, 'processing_widget'):
                self.processing_widget.set_off_state()
    def start_threaded_manual_generation(self, manual_input):
        """Start manual task generation in a separate thread"""
        try:
            # Create and configure worker thread
            self.manual_worker = ManualTaskGenerationWorker(manual_input)
            
            # Connect signals
            self.manual_worker.progress_update.connect(self.on_task_generation_progress)
            self.manual_worker.tasks_generated.connect(self.on_manual_tasks_generated)
            self.manual_worker.error_occurred.connect(self.on_task_generation_error)
            self.manual_worker.finished_processing.connect(self.on_manual_generation_finished)
            
            # Start the worker thread
            self.manual_worker.start()
            
        except Exception as e:
            self.log_message(f"❌ Error starting manual task generation: {str(e)}")
            QMessageBox.critical(self, "❌ Error", f"Failed to start task generation:\n{str(e)}")
            if hasattr(self, 'processing_widget'):
                self.processing_widget.set_off_state()
            self.process_btn.setEnabled(True)
    
    def start_threaded_file_generation(self, file_path):
        print("start_threaded_file_generation function called")
        
        """Start file task generation in a separate thread"""
        try:
            # Create and configure worker thread
            self.file_worker = FileTaskGenerationWorker(file_path)
            
            # Connect signals
            self.file_worker.progress_update.connect(self.on_task_generation_progress)
            self.file_worker.tasks_generated.connect(self.on_file_tasks_generated)
            self.file_worker.error_occurred.connect(self.on_task_generation_error)
            self.file_worker.finished_processing.connect(self.on_file_generation_finished)
            
            # Start the worker thread
            self.file_worker.start()
            
        except Exception as e:
            self.log_message(f"❌ Error starting file task generation: {str(e)}")
            QMessageBox.critical(self, "❌ Error", f"Failed to start task generation:\n{str(e)}")
            if hasattr(self, 'processing_widget'):
                self.processing_widget.set_off_state()
            self.process_btn.setEnabled(True)
    
    def on_task_generation_progress(self, message):
        """Handle progress updates from task generation workers"""
        self.log_message(message)
    
    def on_manual_tasks_generated(self, req_class, task_events, app_info, full_task_info, conditional_info):
        """Handle generated tasks from manual worker"""
        try:
            # Store the generated data
            self.req_class = req_class
            self.task_events = task_events
            self.app_info = app_info
            self.full_task_info = full_task_info
            self.conditional_info = conditional_info
            
            # Clear task list immediately (fast operation)
            self.task_list.clear()
            self.task_list.clear_breakpoints()
            
            # Always set conditional info in task list (even if empty to clear previous)
            self.task_list.set_conditional_info(self.conditional_info)
            print(f" UI: Set conditional info: {self.conditional_info}")
            
            # Start background task list population to prevent UI freezing
            self.start_task_list_population()
            
            self.log_message(f"✅ Generated {len(self.req_class)} tasks successfully")
            self.log_message(f"✅ Generated {len(self.req_class)} steps successfully")
            self.start_btn.setEnabled(True)
            
        except Exception as e:
            self.log_message(f"❌ Error processing manual tasks: {str(e)}")
            QMessageBox.critical(self, "❌ Error", f"Failed to process generated tasks:\n{str(e)}")
    
    def on_file_tasks_generated(self, req_class, task_events, app_info, full_task_info, conditional_info):
        """Handle generated tasks from file worker"""
        try:
            # Store the generated data
            self.req_class = req_class
            self.task_events = task_events
            self.app_info = app_info
            self.full_task_info = full_task_info
            self.conditional_info = conditional_info
            
            # Clear task list immediately (fast operation)
            self.task_list.clear()
            self.task_list.clear_breakpoints()
            
            # Always set conditional info in task list (even if empty to clear previous)
            self.task_list.set_conditional_info(self.conditional_info)
            print(f"📱 UI: Set conditional info: {self.conditional_info}")
            
            # Start background task list population to prevent UI freezing
            self.start_task_list_population()
            
            self.log_message(f"✅ Generated {len(self.req_class)} tasks successfully from file")
            self.log_message(f"✅ Generated {len(self.req_class)} steps successfully from file")
            self.start_btn.setEnabled(True)
            
        except Exception as e:
            self.log_message(f"❌ Error processing file tasks: {str(e)}")
            QMessageBox.critical(self, "❌ Error", f"Failed to process generated tasks:\n{str(e)}")
    
    def on_task_generation_error(self, error_message):
        """Handle errors from task generation workers"""
        self.log_message(f"❌ Error generating tasks: {error_message}")
        QMessageBox.critical(self, "❌ Error", f"Failed to generate tasks:\n{error_message}")
        if hasattr(self, 'processing_widget'):
            self.processing_widget.set_off_state()
    
    def on_manual_generation_finished(self):
        """Handle completion of manual task generation"""
        # Set to detail mode state after processing completes
        if hasattr(self, 'processing_widget'):
            self.processing_widget.set_detail_mode_state()
        
        # Show task creation popup and wait for user decision
        try:
            task_count = len(self.req_class)
            self.show_task_creation_popup(task_count)
            print(f"✅ Showed task creation popup: {task_count} steps")
        except Exception as e:
            print(f"Error showing task creation popup: {e}")
            # If popup fails, show fallback message
            QMessageBox.information(self, "✅ Success", f"{len(self.req_class)} steps created successfully!")
        
        # Re-enable process button
        self.process_btn.setEnabled(True)
        
        # Clean up worker thread
        if hasattr(self, 'manual_worker'):
            self.manual_worker.deleteLater()
            self.manual_worker = None
    
    def on_file_generation_finished(self):
        """Handle completion of file task generation"""
        print("[MAIN] File generation finished - starting cleanup")
        
        # Set to detail mode state after file processing completes
        if hasattr(self, 'processing_widget'):
            self.processing_widget.set_detail_mode_state()
        
        # Show task creation popup and wait for user decision
        try:
            task_count = len(self.req_class)
            self.show_task_creation_popup(task_count)
            print(f"✅ Showed task creation popup: {task_count} steps")
        except Exception as e:
            print(f"Error showing task creation popup: {e}")
            # If popup fails, show fallback message
            QMessageBox.information(self, "✅ Success", f"{len(self.req_class)} steps created successfully!")
        
        # Re-enable process button
        self.process_btn.setEnabled(True)
        
        # Clean up worker thread properly
        self.cleanup_file_worker()
    
    def cleanup_file_worker(self):
        """Properly clean up the file worker thread"""
        if hasattr(self, 'file_worker') and self.file_worker is not None:
            print("[MAIN] Cleaning up file worker thread")
            try:
                # Disconnect all signals to prevent issues
                self.file_worker.progress_update.disconnect()
                self.file_worker.tasks_generated.disconnect()
                self.file_worker.error_occurred.disconnect()
                self.file_worker.finished_processing.disconnect()
                
                # Wait for thread to finish if still running
                if self.file_worker.isRunning():
                    print("[MAIN] Waiting for file worker thread to finish...")
                    self.file_worker.wait(3000)  # Wait max 3 seconds
                    
                # Delete the worker
                self.file_worker.deleteLater()
                self.file_worker = None
                print("[MAIN] File worker thread cleaned up successfully")
                
            except Exception as cleanup_error:
                print(f"[MAIN] Warning during file worker cleanup: {cleanup_error}")
                # Force cleanup even if there's an error
                self.file_worker = None
    
    def show_task_creation_popup(self, task_count):
        """Show custom task creation popup and handle user choice"""
        popup = task_creation_popup.TaskCreationPopup(task_count=task_count, parent=self)
        
        # Connect signals
        popup.start_detail_mode.connect(self.start_detail_mode_validation)
        popup.cancelled.connect(self.on_task_creation_cancelled)
        
        # Show popup and wait for result
        result = popup.exec_()
        
        print(f"🔔 Task creation popup result: {popup.result}")
        
        # Handle result
        if popup.result == "start_detail":
            print("✅ User chose to start detail mode")
        elif popup.result in ["cancel", "close"]:
            print("❌ User cancelled or closed popup - detail mode will not start")
        else:
            print("⚠️ Unknown popup result")
    
    def on_task_creation_cancelled(self):
        """Handle when user cancels task creation popup"""
        print("❌ Task creation popup cancelled - detail mode will not start")
        # Set to Ready to Process state when detail mode is skipped
        if hasattr(self, 'processing_widget'):
            self.processing_widget.set_ready_to_process_state()
    
    def start_task_list_population(self):
        """Start task list population in background thread to prevent UI freezing"""
        try:
            # Create and configure worker thread
            self.task_population_worker = TaskListPopulationWorker(
                self.req_class, 
                self.app_info, 
                getattr(self, 'conditional_info', None)
            )
            
            # Connect signals
            self.task_population_worker.progress_update.connect(self.on_task_population_progress)
            self.task_population_worker.task_batch_ready.connect(self.on_task_batch_ready)
            self.task_population_worker.population_completed.connect(self.on_task_population_completed)
            self.task_population_worker.error_occurred.connect(self.on_task_population_error)
            
            # Start the worker thread
            self.task_population_worker.start()
            
        except Exception as e:
            self.log_message(f"❌ Error starting steps list population: {str(e)}")
            print(f"Error starting steps list population: {e}")
    
    def on_task_population_progress(self, message):
        """Handle progress updates from task population worker"""
        self.log_message(message)
    
    def on_task_batch_ready(self, batch):
        """Handle batch of tasks ready for UI update"""
        try:
            # Add tasks from batch to UI (small batches keep UI responsive)
            for task_data in batch:
                self.task_list.add_task_with_breakpoint(
                    task_data['task'], 
                    task_data['index'], 
                    len(batch),
                    task_data['app_info']
                )
            
            # Process events to keep UI responsive
            QApplication.processEvents()
            
        except Exception as e:
            print(f"❌ Error processing task batch: {e}")
    
    def on_task_population_completed(self):
        """Handle completion of task list population"""
        try:
            # Set app_info in task list after all tasks are added
            if hasattr(self, 'app_info') and self.app_info:
                self.task_list.set_app_info(self.app_info)
                print(f"📱 UI: Set app info for {len(self.app_info)} steps")
            
            # Ensure add button is at the end after all tasks are loaded
            self.task_list.ensure_add_button_at_end()
            
            self.log_message("✅ Step list population completed!")
            print("✅ Step list population completed successfully")
            
            # Clean up worker thread
            if hasattr(self, 'task_population_worker'):
                self.task_population_worker.deleteLater()
                self.task_population_worker = None
            
        except Exception as e:
            print(f"❌ Error completing task population: {e}")
    
    def on_task_population_error(self, error_message):
        """Handle errors from task population worker"""
        self.log_message(f"❌ Error populating task list: {error_message}")
        print(f"❌ Error populating task list: {error_message}")
        
        # Clean up worker thread
        if hasattr(self, 'task_population_worker'):
            self.task_population_worker.deleteLater()
            self.task_population_worker = None
    
    def start_preprocess_completion(self):
        """Start pre-process completion in background thread to prevent UI freezing"""
        try:
            # Create and configure worker thread
            self.preprocess_completion_worker = PreProcessCompletionWorker(self)
            
            # Connect signals
            self.preprocess_completion_worker.progress_update.connect(self.on_preprocess_completion_progress)
            self.preprocess_completion_worker.completion_ready.connect(self.on_preprocess_completion_ready)
            self.preprocess_completion_worker.error_occurred.connect(self.on_preprocess_completion_error)
            
            # Start the worker thread
            self.preprocess_completion_worker.start()
            
        except Exception as e:
            self.log_message(f"❌ Error starting pre-process completion: {str(e)}")
            print(f"Error starting pre-process completion: {e}")
            # Fallback to direct completion
            self.show_preprocess_completion_popup()
    
    def on_preprocess_completion_progress(self, message):
        """Handle progress updates from pre-process completion worker"""
        self.log_message(message)
    
    def on_preprocess_completion_ready(self):
        """Handle when pre-process completion is ready to show popup"""
        try:
            # Call task refreshing to update tasks based on generated code
            self.refresh_tasks_from_code()
            
            # Show completion popup
            self.show_preprocess_completion_popup()
            
            # Clean up worker thread
            if hasattr(self, 'preprocess_completion_worker'):
                self.preprocess_completion_worker.deleteLater()
                self.preprocess_completion_worker = None
            
        except Exception as e:
            print(f"❌ Error in pre-process completion ready: {e}")
            self.show_preprocess_completion_popup()  # Fallback
    
    def on_preprocess_completion_error(self, error_message):
        """Handle errors from pre-process completion worker"""
        self.log_message(f"❌ Error in pre-process completion: {error_message}")
        print(f"❌ Error in pre-process completion: {error_message}")
        
        # Clean up worker thread
        if hasattr(self, 'preprocess_completion_worker'):
            self.preprocess_completion_worker.deleteLater()
            self.preprocess_completion_worker = None
        
        # Fallback to direct completion
        self.show_preprocess_completion_popup()
    
    def show_preprocess_completion_popup(self):
        """Show the pre-process completion popup"""
        try:
            # Create custom styled dialog instead of QMessageBox
            dialog = QDialog(self)
            dialog.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool | Qt.X11BypassWindowManagerHint)
            dialog.setAttribute(Qt.WA_TranslucentBackground)
            dialog.setFixedSize(620, 400)
            # ✅ Center the dialog dynamically
            screen_geometry = QApplication.primaryScreen().geometry()
            x = (screen_geometry.width() - dialog.width()) // 2
            y = (screen_geometry.height() - dialog.height()) // 2
            dialog.move(x, y)
            dialog.setModal(True)
            dialog.setStyleSheet("")
            
            container = QWidget(dialog)
            container.setGeometry(0, 0, 620, 400)
            container.setObjectName("dialogContainer")
            container.setStyleSheet("QWidget#dialogContainer { background-color: #414141 !important; border: none !important; border-radius: 15px !important; }")
            
            layout = QVBoxLayout(container)
            layout.setContentsMargins(0, 0, 0, 25)
            layout.setSpacing(0)

            # Title bar
            title_container = QWidget()
            title_container.setFixedHeight(60)
            title_container.setStyleSheet("QWidget { background: #333333 !important; border-radius: 20px 20px 0px 0px !important; border: none !important; }")
            
            title_layout = QHBoxLayout(title_container)
            title_layout.setContentsMargins(25, 15, 25, 15)
            
            title_label = QLabel("Pre Processing Completed")
            title_label.setStyleSheet("QLabel { color: #ffffff !important; font-family: 'Asen Pro' !important; font-weight: bold !important; font-size: 16px !important; background: transparent !important; border: none !important; }")
            title_label.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
            title_layout.addWidget(title_label)
            title_layout.addStretch()
            
            close_btn = QPushButton()
            close_btn.setFixedSize(24, 24)
            close_btn.setStyleSheet("QPushButton { background: transparent !important; border: none !important; } QPushButton:hover { background-color: rgba(255, 255, 255, 0.1) !important; border-radius: 12px !important; }")
            
            def paintEvent(event):
                painter = QPainter(close_btn)
                painter.setRenderHint(QPainter.Antialiasing)
                pen = QPen(QColor(255, 255, 255), 2)
                painter.setPen(pen)
                margin = 6
                painter.drawLine(margin, margin, 18, 18)
                painter.drawLine(18, margin, margin, 18)
            close_btn.paintEvent = paintEvent
            close_btn.clicked.connect(dialog.accept)
            title_layout.addWidget(close_btn)
            layout.addWidget(title_container)
            layout.addSpacing(30)
            
            # Success message with icon
            msg_container = QWidget()
            msg_container.setStyleSheet("background: transparent !important; border: none !important;")
            msg_layout = QHBoxLayout(msg_container)
            msg_layout.setContentsMargins(40, 0, 40, 0)
            msg_layout.setSpacing(15)

            # Success icon using same approach as Task Creation popup
            icon_button = QPushButton()
            icon_button.setFixedSize(40, 40)
            
            # Try to set success icon, fallback to emoji
            try:
                icon = QIcon(resource_path("styles/Icon/success_image.png"))
                icon_button.setIcon(icon)
                icon_button.setIconSize(QSize(40, 40))
                icon_button.setStyleSheet("""
                    QPushButton {
                        background: transparent !important;
                        border: none !important;
                        padding: 0px !important;
                    }
                    QPushButton:hover {
                        background: transparent !important;
                    }
                    QPushButton:pressed {
                        background: transparent !important;
                    }
                """)
            except:
                icon_button.setText("✅")
                icon_button.setStyleSheet("""
                    QPushButton {
                        background: transparent !important;
                        border: none !important;
                        font-size: 28px !important;
                    }
                """)
            
            main_msg = QLabel("Pre Processing completed successfully!")
            main_msg.setStyleSheet("QLabel { color: #FFFFFF !important; font-family: 'Asen Pro' !important; font-weight: 600 !important; font-size: 20px !important; background: transparent !important; border: none !important; }")
            main_msg.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
            
            msg_layout.addWidget(icon_button)
            msg_layout.addWidget(main_msg)
            msg_layout.addStretch()
            layout.addWidget(msg_container)
            layout.addSpacing(20)
            
            # Details text
            details = QLabel("• Code saved to: Code Tab\n• Element data saved to: Element Tab\n• Tasks refreshed based on generated code\n\nCheck the Code tab to view the generated code and Generated Tasks tab for updated tasks.")
            details.setStyleSheet("QLabel { color: #FFFFFF !important; font-family: 'Asen Pro' !important; font-size: 14px !important; line-height: 18px !important; background: transparent !important; border: none !important; padding: 10px 40px !important; }")
            details.setWordWrap(True)
            layout.addWidget(details)
            
            layout.addSpacing(30)
            
            # OK button
            btn_layout = QHBoxLayout()
            ok_btn = QPushButton("OK")
            ok_btn.setFixedSize(120, 40)
            ok_btn.setStyleSheet("QPushButton { background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1, stop: 0 #008AB3, stop: 1 #005B7F) !important; color: #FFFFFF !important; border: none !important; border-radius: 10px !important; font-family: 'Asen Pro' !important; font-weight: 600 !important; font-size: 16px !important; } QPushButton:hover { background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1, stop: 0 #0099CC, stop: 1 #006699) !important; }")
            ok_btn.clicked.connect(dialog.accept)
            btn_layout.addStretch()
            btn_layout.addWidget(ok_btn)
            btn_layout.addStretch()
            layout.addLayout(btn_layout)
            
            dialog.exec_()
            
            self.update_tasks_status("Pre Processing completed", "#4CAF50")
            
            # Re-enable start button
            self.start_btn.setEnabled(True)
            self.start_btn.setText("⚙️ Generate Code")
            
        except Exception as e:
            print(f"❌ Error showing pre-process completion popup: {e}")

    def on_input_method_changed(self):
        """Handle input method selection changes"""
        try:
            # Play click sound when switching modes
            self.player_click.stop()
            self.player_click.play()
        except Exception as e:
            print(f"[ERROR] Failed to play click sound: {e}")

        if self.manual_radio.isChecked():
            # Show manual input, hide file upload
            self.requirement_input.setVisible(True)
            self.file_path_label.setVisible(False)
            self.browse_btn.setVisible(False)
            self.file_radio.setChecked(False)
            self.process_btn.setText("🔄 Enter && Process")
        elif self.file_radio.isChecked():
            # Show file upload, hide manual input
            self.requirement_input.setVisible(False)
            self.file_path_label.setVisible(True)
            self.browse_btn.setVisible(True)
            self.manual_radio.setChecked(False)
            self.process_btn.setText("🔄 Upload && Process")

    
    def _show_step_review_dialog(self, analyzer, pdd_analyses, video_path, output_dir):

        print("🔍 Main thread: Creating independent review dialog...")
        
        # Create dialog with NO parent (truly independent)
        dialog = StepReviewDialog(analyzer, pdd_analyses, video_path, output_dir, parent=None)
        
        # Store reference
        self._active_review_dialog = dialog
        
        final_steps = pdd_analyses
        
        def on_steps_updated(steps):
            nonlocal final_steps
            final_steps = steps
        
        dialog.steps_updated.connect(on_steps_updated)
        
        # Show dialog (will be independent from main window now)
        result = dialog.exec_()
        
        # Send results back to worker thread
        if result == QDialog.Accepted:
            self.worker.reviewed_steps = final_steps
            self.worker.review_completed = True
            print(f"Review accepted: {len(final_steps)} steps")
        else:
            self.worker.reviewed_steps = []
            self.worker.review_completed = True
            print("Review cancelled")


    def browse_file(self):
        dialog = QFileDialog(self)
        dialog.setWindowTitle("Select Requirements Document(s)")
        dialog.setAcceptMode(QFileDialog.AcceptOpen)
        
        # Enable multiple file selection
        dialog.setFileMode(QFileDialog.ExistingFiles)
        
        dialog.setNameFilter("Document Files (*.pdf *.txt *.doc *.docx *.mp4);;PDF Files (*.pdf);;Text Files (*.txt);;Word Documents (*.doc *.docx);;Video Files (*.mp4);;All Files (*)")
        
        initial_dir = os.path.expanduser("~")
        dialog.setDirectory(initial_dir)
        
        dialog.setOption(QFileDialog.DontUseNativeDialog, True)
        dialog.setProperty('class', 'CustomFileDialog')
        style_loader.apply_stylesheet(dialog)
        
        urls = []
        paths = [
            os.path.expanduser("~/Desktop"),
            os.path.expanduser("~/Downloads"),
            os.path.expanduser("~/Documents"),
            os.path.expanduser("~")
        ]
        for path in paths:
            if os.path.exists(path):
                urls.append(QUrl.fromLocalFile(path))
        dialog.setSidebarUrls(urls)
        
        if dialog.exec_():
            selected_files = dialog.selectedFiles()
            if selected_files:
                # Check if all selected files are MP4 or mixed types
                mp4_files = [f for f in selected_files if f.lower().endswith('.mp4')]
                non_mp4_files = [f for f in selected_files if not f.lower().endswith('.mp4')]
                
                # Case 1: Only non-MP4 files selected
                if not mp4_files and non_mp4_files:
                    if len(non_mp4_files) > 1:
                        QMessageBox.warning(self, "Multiple Files", "Please select only one non-video file at a time.")
                        return
                    
                    # Single non-MP4 file - existing logic
                    self.selected_file_path = non_mp4_files[0]
                    file_name = os.path.basename(self.selected_file_path)
                    
                    # Convert .doc/.docx to PDF if needed
                    if self.selected_file_path.lower().endswith(('.doc', '.docx')):
                        try:
                            self.log_message(f"📄 Converting {file_name} to PDF...")
                            
                            self.file_path_label.setText(f"{file_name} (Converting...)")
                            self.file_path_label.setStyleSheet("""
                                QLabel {
                                    background-color: #FFA500;
                                    color: #ffffff;
                                    font-size: 13px;
                                    padding: 6px;
                                    border-radius: 4px;
                                }
                            """)
                            
                            from Word_Pdf_Converter import docx_to_pdf
                            pdf_path = docx_to_pdf(self.selected_file_path)
                            self.selected_file_path = pdf_path
                            file_name = os.path.basename(self.selected_file_path)
                            self.log_message(f"✅ Converted to PDF: {file_name}")
                            
                        except Exception as e:
                            self.log_message(f"❌ Error converting {file_name} to PDF: {str(e)}")
                            QMessageBox.critical(self, "❌ Error", f"Failed to convert {file_name} to PDF: {str(e)}")
                            self.selected_file_path = None
                            self.file_path_label.setText("No file selected")
                            self.file_path_label.setProperty('class', 'FilePathDefault')
                            style_loader.apply_stylesheet(self.file_path_label)
                            return
                    
                    # Update UI
                    self.file_path_label.setText(f"{file_name}")
                    self.file_path_label.setStyleSheet("""
                        QLabel {
                            background-color: #000000;
                            color: #ffffff;
                            font-size: 13px;
                            padding: 6px;
                            border-radius: 4px;
                        }
                    """)
                    self.file_path_label.setProperty('class', 'FilePathSelected')
                    self.file_remove_btn.show()  # Show remove button when file is selected
                    self.log_message(f"📁 File selected: {file_name}")
                    return
                
                # Case 2: MP4 files selected (single or multiple)
                if mp4_files:
                    if non_mp4_files:
                        QMessageBox.warning(self, "Mixed Selection", "Please select only MP4 videos or only documents, not both.")
                        return
                    
                    # Store multiple video paths
                    self.selected_video_paths = mp4_files
                    video_count = len(mp4_files)
                    
                    self.log_message(f"📹 {video_count} video(s) selected")
                    
                    # ============================================================
                    # LAUNCH VIDEO TRIMMER - ONE AT A TIME
                    # ============================================================
                    trimmer_result = QMessageBox.question(
                        self,
                        "Trim Videos?",
                        f"Would you like to trim the {video_count} video(s) before processing?",
                        QMessageBox.Yes | QMessageBox.No,
                        QMessageBox.Yes
                    )
                    
                    split_json_path = None
                    
                    if trimmer_result == QMessageBox.Yes:
                        from Mp4_trimmer import VideoTrimmer
                        
                        # Clear existing JSON before processing multiple videos
                        if os.path.exists("split_timestamps.json"):
                            os.remove("split_timestamps.json")
                            self.log_message("🗑️ Cleared previous split data")
                        
                        # Launch trimmer for each video sequentially
                        for video_idx, video_path in enumerate(self.selected_video_paths):
                            self.log_message(f"🎬 Opening trimmer for video {video_idx+1}/{video_count}...")
                            
                            # Create trimmer window
                            trimmer = VideoTrimmer()
                            trimmer.setWindowModality(Qt.ApplicationModal)
                            trimmer.upload_video_programmatic(video_path)
                            
                            # Wait for trimmer to close
                            result = trimmer.exec_()
                            
                            # Check if JSON was saved
                            if os.path.exists("split_timestamps.json"):
                                split_json_path = "split_timestamps.json"
                                self.log_message(f"✅ Video {video_idx+1} trimmed - splits saved")
                            else:
                                self.log_message(f"⚠️ No splits saved for video {video_idx+1}")
                    
                    # NOW show transcript upload dialog (after trimmer closes)
                    from transcript_upload_dialog import TranscriptUploadDialog
                    
                    # Show custom dialog with video count
                    upload_dialog = TranscriptUploadDialog(self, video_count=video_count)
                    
                    if upload_dialog.exec_() == QDialog.Accepted:
                        # Get results from dialog (list of transcript paths + additional docs)
                        transcript_paths, additional_docs, custom_prompt = upload_dialog.get_results()
                        self.selected_transcript_paths = transcript_paths
                        self.additional_docs = additional_docs  # NEW
                        self.custom_prompt = custom_prompt
                        self.split_json_path = split_json_path
                        
                        # Check how many transcripts were uploaded
                        uploaded_count = sum(1 for t in transcript_paths if t is not None)
                        additional_docs_count = len(additional_docs)
                        
                        # Build status message
                        status_parts = [f"{video_count} video(s)"]
                        if uploaded_count > 0:
                            status_parts.append(f"{uploaded_count} transcript(s)")
                        if additional_docs_count > 0:
                            status_parts.append(f"{additional_docs_count} additional doc(s)")
                        
                        status_message = " with ".join(status_parts)
                        
                        if uploaded_count > 0:
                            # Some transcripts uploaded
                            self.file_path_label.setText(status_message)
                            self.file_path_label.setStyleSheet("""
                                QLabel {
                                    background-color: #000000;
                                    color: #ffffff;
                                    font-size: 13px;
                                    padding: 6px;
                                    border-radius: 4px;
                                }
                            """)
                            self.file_path_label.setProperty('class', 'FilePathSelected')
                            self.file_remove_btn.show()
                            self.log_message(f"📄 {uploaded_count}/{video_count} transcript(s) uploaded")
                        else:
                            # No transcripts - auto-generate
                            self.file_path_label.setText(f"{video_count} video(s) (Processing...)")
                            self.file_path_label.setStyleSheet("""
                                QLabel {
                                    background-color: #FFA500;
                                    color: #ffffff;
                                    font-size: 13px;
                                    padding: 6px;
                                    border-radius: 4px;
                                }
                            """)
                            self.file_remove_btn.show()
                            self.log_message(f"📄 No transcripts uploaded - will be generated automatically for {video_count} video(s)")
                        
                        if additional_docs_count > 0:
                            self.log_message(f"📎 {additional_docs_count} additional document(s) attached")
                        
                        if custom_prompt:
                            self.log_message(f"📝 Custom prompt added: {custom_prompt[:50]}...")
                        
                        # Show progress dialog
                        progress = QProgressDialog(f"Processing {video_count} MP4 video(s)...", "Cancel", 0, 0, self)
                        progress.setWindowTitle("Processing")
                        progress.setWindowModality(Qt.WindowModal)
                        progress.setMinimumDuration(0)
                        progress.setWindowFlags(Qt.Dialog | Qt.WindowMinimizeButtonHint | Qt.WindowCloseButtonHint)
                        progress.setCancelButtonText("Cancel")
                        progress.setRange(0, 0)
                        progress.show()
                        
                        # Connect cancel button
                        def on_cancel():
                            if hasattr(self, 'worker') and self.worker.isRunning():
                                self.worker.terminate()
                                self.worker.wait()
                                self.log_message("⚠️ Video processing cancelled by user")
                                progress.close()
                                self.selected_video_paths = []
                                self.selected_transcript_paths = []
                                self.additional_docs = []
                                self.custom_prompt = ""
                                self.split_json_path = None
                                self.file_path_label.setText("No file selected")
                                self.file_path_label.setProperty('class', 'FilePathDefault')
                                style_loader.apply_stylesheet(self.file_path_label)
                                QMessageBox.information(self, "Cancelled", "Video processing was cancelled.")
                        
                        progress.canceled.connect(on_cancel)
                        
                        # Run conversion in worker thread with multiple videos
                        self.worker = VideoToPdfWorker(
                            video_paths=self.selected_video_paths,
                            transcript_paths=self.selected_transcript_paths,
                            selected_project_id=self.selected_project_id, 
                            selected_task_id=self.selected_task_id, 
                            user_id=self.userid,
                            custom_prompt=self.custom_prompt,
                            split_json_path=self.split_json_path,
                            additional_docs=self.additional_docs  # NEW
                        )
                        self.worker.show_review_dialog.connect(self._show_step_review_dialog)
                        self.worker.finished.connect(lambda pdf_path: self._on_conversion_finished(pdf_path, progress, f"{video_count} video(s)"))
                        self.worker.error.connect(lambda error_msg: self._on_conversion_error(error_msg, progress))
                        self.worker.start()
                        
                    else:
                        # Dialog cancelled
                        self.selected_video_paths = []
                        self.selected_transcript_paths = []
                        self.additional_docs = []
                        self.custom_prompt = ""
                        self.split_json_path = None
                        self.file_path_label.setText("No file selected")
                        self.file_path_label.setProperty('class', 'FilePathDefault')
                        self.file_remove_btn.hide()
                        style_loader.apply_stylesheet(self.file_path_label)
                        self.log_message("⚠️ Upload cancelled")
                        
                        
    # Helper methods that need to be integrated (from previous code)
    
    def remove_selected_file(self):
        """Remove the selected file and reset the file upload UI"""
        self.selected_file_path = None
        self.selected_video_paths = []
        self.selected_transcript_paths = []
        self.additional_docs = []
        self.custom_prompt = ""
        self.split_json_path = None
        
        # Reset file path label
        self.file_path_label.setText("")
        self.file_path_label.setStyleSheet("""
            QLabel {
                color: white;
                font-size: 13px;
                padding: 5px;
            }
        """)
        self.file_path_label.setProperty('class', 'FilePathDefault')
        
        # Hide the remove button
        self.file_remove_btn.hide()
        
        self.log_message("🗑️ File removed from upload queue")
    def _on_conversion_finished(self, pdf_path, progress, original_file_name):
        """Handle successful video to PDF conversion"""
        progress.close()
        if pdf_path and os.path.exists(pdf_path):
            self.selected_file_path = pdf_path
            converted_file_name = os.path.basename(pdf_path)
           
            # Update UI with successful conversion (using new code's styling)
            self.file_path_label.setText(f"{original_file_name} → PDF")
            self.file_path_label.setStyleSheet("""
                QLabel {
                    background-color: #000000;
                    color: #ffffff;
                    font-size: 13px;
                    padding: 6px;
                    border-radius: 4px;
                }
            """)
            self.file_path_label.setProperty('class', 'FilePathSelected')
           
            self.log_message(f"✅ Video successfully converted to PDF: {converted_file_name}")
            QMessageBox.information(self, "✅ Success", f"Video successfully processed and converted to PDF:\n{converted_file_name}")
        else:
            self.log_message("❌ Video conversion failed - no PDF generated")
            self.selected_file_path = None
            self.file_path_label.setText("No file selected")
            self.file_path_label.setProperty('class', 'FilePathDefault')
            style_loader.apply_stylesheet(self.file_path_label)
            QMessageBox.critical(self, "❌ Error", "Video conversion failed. No PDF was generated.")
            
    def _on_conversion_finished(self, pdf_path, progress, original_file_name):
        """Handle successful video-to-PDF conversion"""
        progress.close()
        self.selected_file_path = pdf_path
        file_name = os.path.basename(pdf_path)
        self.log_message(f"✅ Generated requirements summary PDF: {file_name}")
        self.file_path_label.setText("Video Processed Successfully to PDD")
        self.file_path_label.setProperty('class', 'FilePathSelected')
        style_loader.apply_stylesheet(self.file_path_label)


    def _on_conversion_error(self, error_msg, progress):
        """Handle errors during video-to-PDF conversion"""
        progress.close()
        self.log_message(f"❌ Error processing MP4 and transcript: {error_msg}")
        QMessageBox.critical(self, "❌ Error", f"Failed to process MP4 and transcript: {error_msg}")
        self.selected_file_path = None
        self.selected_transcript_path = None
        self.file_path_label.setText("No file selected")
        self.file_path_label.setProperty('class', 'FilePathDefault')
        style_loader.apply_stylesheet(self.file_path_label)


    def delete_existing_task_files(self):
        """
        Deletes all .py files in the current task folder except __init__.py.
        Triggered before starting processing.
        """
        try:
            proj_id = self.selected_project_id
            task_id = self.selected_task_id
            fol_path = f"proj_{proj_id}/task_{task_id}"
            if not os.path.exists(fol_path):
                print(f"⚠️ Folder does not exist: {fol_path}")
                return
            py_files = [f for f in os.listdir(fol_path) if f.endswith(".py")]
            for py_file in py_files:
                if py_file != "__init__.py":
                    file_path = os.path.join(fol_path, py_file)
                    try:
                        os.remove(file_path)
                    except Exception as e:
                        print(f" Error deleting {file_path}: {e}")
        except Exception as e:
            print(f"Error during cleanup: {e}")

    def start_processing(self):
        if not self.req_class:
            self.show_custom_warning("Warning", "No tasks to process!")
            return
        
        if hasattr(self, 'refresh_code_tab_xpath_data'):
            # refresh and update display immediately
            self.refresh_code_tab_xpath_data()  
            if hasattr(self, 'update_code_tab_xpath_display'):
                self.update_code_tab_xpath_display()  # ensure UI shows refreshed data
            print("🔄 Code Tab XPath/Attribute data refreshed automatically before processing.")
        
        # Update status to show processing is starting
        self.update_tasks_status("Pre Processing...", "#2196F3")
        # Set processing state when Start Process is clicked
        if hasattr(self, 'processing_widget'):
            self.processing_widget.set_processing_state()
        # Gate Execute Flow until preprocessing completes
        try:
            if hasattr(self, 'execute_flow_btn'):
                self.execute_flow_btn.setEnabled(False)
            if hasattr(self, 'stop_flow_btn'):
                self.stop_flow_btn.setEnabled(False)
        except Exception:
            pass
        
        # Start skeleton code generation in separate thread
        self.start_threaded_skeleton_generation()

    def show_custom_warning(self, title, message):
        """Show custom styled warning popup"""
        dialog = QDialog(self)
        dialog.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool | Qt.X11BypassWindowManagerHint)
        dialog.setAttribute(Qt.WA_TranslucentBackground)
        dialog.setFixedSize(500, 250)
        dialog.setModal(True)
        dialog.setStyleSheet("")
        
        container = QWidget(dialog)
        container.setGeometry(0, 0, 500, 250)
        container.setObjectName("warningContainer")
        container.setStyleSheet("QWidget#warningContainer { background-color: #414141 !important; border: none !important; border-radius: 15px !important; }")
        
        layout = QVBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 25)
        layout.setSpacing(0)

        # Title bar
        title_container = QWidget()
        title_container.setFixedHeight(60)
        title_container.setStyleSheet("QWidget { background: #333333 !important; border-radius: 20px 20px 0px 0px !important; border: none !important; }")
        
        title_layout = QHBoxLayout(title_container)
        title_layout.setContentsMargins(25, 15, 25, 15)
        
        title_label = QLabel(f"⚠️ {title}")
        title_label.setStyleSheet("QLabel { color: #ffffff !important; font-family: 'Asen Pro' !important; font-weight: bold !important; font-size: 16px !important; background: transparent !important; border: none !important; }")
        title_label.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        title_layout.addWidget(title_label)
        title_layout.addStretch()
        
        close_btn = QPushButton()
        close_btn.setFixedSize(24, 24)
        close_btn.setStyleSheet("QPushButton { background: transparent !important; border: none !important; } QPushButton:hover { background-color: rgba(255, 255, 255, 0.1) !important; border-radius: 12px !important; }")
        
        def paintEvent(event):
            painter = QPainter(close_btn)
            painter.setRenderHint(QPainter.Antialiasing)
            pen = QPen(QColor(255, 255, 255), 2)
            painter.setPen(pen)
            margin = 6
            painter.drawLine(margin, margin, 18, 18)
            painter.drawLine(18, margin, margin, 18)
        close_btn.paintEvent = paintEvent
        close_btn.clicked.connect(dialog.accept)
        title_layout.addWidget(close_btn)
        layout.addWidget(title_container)
        layout.addSpacing(40)
        
        # Message
        msg_label = QLabel(message)
        msg_label.setStyleSheet("QLabel { color: #FFFFFF !important; font-family: 'Asen Pro' !important; font-weight: 400 !important; font-size: 16px !important; text-align: center !important; background: transparent !important; border: none !important; padding: 10px 40px !important; }")
        msg_label.setWordWrap(True)
        msg_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(msg_label)
        layout.addSpacing(40)
        
        # OK button
        btn_layout = QHBoxLayout()
        ok_btn = QPushButton("OK")
        ok_btn.setFixedSize(120, 40)
        ok_btn.setStyleSheet("QPushButton { background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1, stop: 0 #008AB3, stop: 1 #005B7F) !important; color: #FFFFFF !important; border: none !important; border-radius: 10px !important; font-family: 'Asen Pro' !important; font-weight: 600 !important; font-size: 16px !important; } QPushButton:hover { background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1, stop: 0 #0099CC, stop: 1 #006699) !important; }")
        ok_btn.clicked.connect(dialog.accept)
        btn_layout.addStretch()
        btn_layout.addWidget(ok_btn)
        btn_layout.addStretch()
        layout.addLayout(btn_layout)
        
        dialog.exec_()
    def start_threaded_skeleton_generation(self):
        """Start skeleton code generation in a separate thread"""
        xpath_json_path="json_info/json_xpath.json"
        if os.path.exists(xpath_json_path):
            os.remove(xpath_json_path)
        code_skeleton_path="code_py/execute_code.py"
        if os.path.exists(code_skeleton_path):
            os.remove(code_skeleton_path)
        requirements_path="code_py/requirements.txt"
        if os.path.exists(requirements_path):
            os.remove(requirements_path)
        try:
            # Prepare task data
            manual_typed_data = "\n".join(self.req_class) if self.req_class else ""
            
            if not manual_typed_data.strip():
                QMessageBox.warning(self, "⚠️ Warning", "No task data available for skeleton generation!")
                if hasattr(self, 'processing_widget'):
                    self.processing_widget.set_off_state()
                return
            
            # Disable start button and update text
            self.start_btn.setEnabled(False)
            self.start_btn.setText("🔄 Generating...")
            
            # Create and configure worker thread with current automation mode
            current_mode = getattr(self, 'current_automation_mode', 'web')
            self.log_message(f"🔧 Creating skeleton worker with automation mode: {current_mode}")
            self.skeleton_worker = SkeletonCodeWorker(
                manual_typed_data, 
                current_mode,
                self.selected_project_id,
                self.selected_task_id,
                self.userid
            )
            
            # Connect signals
            self.skeleton_worker.progress_update.connect(self.on_skeleton_progress)
            self.skeleton_worker.code_generated.connect(self.on_skeleton_code_generated)
            self.skeleton_worker.error_occurred.connect(self.on_skeleton_error)
            self.skeleton_worker.finished_processing.connect(self.on_skeleton_finished)
            
            # Start the worker thread
            self.skeleton_worker.start()
            
        except Exception as e:
            self.log_message(f"❌ Error starting skeleton generation: {str(e)}")
            QMessageBox.critical(self, "❌ Error", f"Failed to start skeleton generation:\n{str(e)}")
            if hasattr(self, 'processing_widget'):
                self.processing_widget.set_off_state()
            self.start_btn.setEnabled(True)
            self.start_btn.setText("⚙️ Generate Code")
    def on_skeleton_progress(self, message):
        """Handle progress updates from skeleton worker"""
        self.log_message(message)
    
    def on_skeleton_code_generated(self, code, json_data,requirements,automation_mode=None):
        """Handle generated code from skeleton worker"""
        try:
            import os
            import json
            packages = [
                line.strip() 
                for line in requirements.strip().split('\n') 
                if line.strip() and not line.strip().startswith('#')
            ]
            
            # If no packages found
            if not packages:
                packages = ["No packages to install"]
            
            pip_command = f"#!pip install {' '.join(packages)}"
            code=f"{pip_command}\n{code}"

            # Write code to working directory for .exe compatibility
            os.makedirs("code_py", exist_ok=True)

            with open("code_py/requirements.txt", "w", encoding="utf-8") as f:
                f.write(requirements)
            
            with open("code_py/execute_code.py", "w", encoding="utf-8") as f:
                f.write(code)

            
            # Ensure json_info directory exists
            os.makedirs("json_info", exist_ok=True)
            
            # Write JSON data to appropriate file based on automation mode
            if isinstance(json_data, dict) and automation_mode != 'native':
                if automation_mode == 'desktop':
                    # Desktop mode - save as json_attr.json
                    with open("json_info/json_attr.json", "w", encoding="utf-8") as f:
                        json.dump(json_data, f, indent=4)
                    self.log_message("📄 Attributes JSON written to: Attributes Details Tab")
                elif automation_mode == 'citrix':
                    # Citrix mode - save as citrix_data.json
                    with open("json_info/citrix_data.json", "w", encoding="utf-8") as f:
                        json.dump(json_data, f, indent=4)
                    self.log_message("📄 Citrix JSON written to: Citrix Data Details Tab")
                else:
                    # Web mode - save as json_xpath.json
                    with open("json_info/json_xpath.json", "w", encoding="utf-8") as f:
                        json.dump(json_data, f, indent=4)
                    self.log_message("📄 XPath JSON written to: XPath Tab")
            elif automation_mode == 'native':
                # Native mode - no JSON data needed
                self.log_message("📄 Native mode: No JSON data required")
            
            self.log_message("Pre Processing completed successfully!")
            self.log_message(f"📄 Code written to: Code Tab")
            
            # Update Code tab with skeleton code
            self.update_code_display_with_skeleton(code)

            try:
                # After code generation and json creation
                import flowchart_widget
                flowchart_widget.SAMPLE_CODE = code  # 🔥 Update the global variable in flowchart_widget.py

                # If your flowchart widget instance is available
                if hasattr(self, 'flowchart_widget'):
                    self.flowchart_widget.code_input.setPlainText(code)
                    self.flowchart_widget.generate_flowchart()

                self.log_message("🧩 Flowchart updated with generated skeleton code.")

            except Exception as e:
                self.log_message(f"⚠️ Could not update SAMPLE_CODE: {str(e)}")
                
            # ------------------- Auto-refresh XPath/Attributes tab -------------------
            if hasattr(self, 'refresh_code_tab_xpath_data'):
                self.refresh_code_tab_xpath_data()
                if hasattr(self, 'update_code_tab_xpath_display'):
                    self.update_code_tab_xpath_display()
                self.log_message("🔄 Code Tab XPath/Attribute data refreshed automatically after code generation.")

            # Optionally refresh tasks from code
            self.refresh_tasks_from_code()
            
            # Update tab name based on automation mode
            self.update_json_tab_name(automation_mode)
            
            # Enable Execute Flow in sidebar now that skeleton code exists
            try:
                if hasattr(self, 'execute_flow_btn'):
                    self.execute_flow_btn.setEnabled(True)
                if hasattr(self, 'stop_flow_btn'):
                    self.stop_flow_btn.setEnabled(False)
            except Exception:
                pass
            
        except Exception as e:
            self.log_message(f"❌ Error saving generated files: {str(e)}")
            QMessageBox.critical(self, "❌ Error", f"Failed to save generated files:\n{str(e)}")
    def on_skeleton_error(self, error_message):
        """Handle errors from skeleton worker"""
        self.log_message(f"❌ Error generating skeleton code: {error_message}")
        QMessageBox.critical(self, "❌ Error", f"Failed to generate skeleton code:\n{error_message}")
        if hasattr(self, 'processing_widget'):
            self.processing_widget.set_off_state()
        self.update_tasks_status("Skeleton generation failed", "#F44336")
        
        # Re-enable start button
        self.start_btn.setEnabled(True)
        self.start_btn.setText("⚙️ Generate Code")
        
        # Clean up worker thread
        if hasattr(self, 'skeleton_worker') and self.skeleton_worker is not None:
            self.skeleton_worker.deleteLater()
            self.skeleton_worker = None
    
    def on_skeleton_finished(self):
        """Handle completion of skeleton generation"""
        # Update processing widget to ready for execution state
        if hasattr(self, 'processing_widget'):
            self.processing_widget.set_ready_for_execution_state()
        
        # Start background completion processing to prevent UI freezing
        self.start_preprocess_completion()
        
        # Clean up skeleton worker thread
        if hasattr(self, 'skeleton_worker') and self.skeleton_worker is not None:
            self.skeleton_worker.deleteLater()
            self.skeleton_worker = None
    
    def refresh_tasks_from_code(self):
        """Refresh tasks based on generated code using task_refreshing module"""
        try:
            # Get the generated code from the code display
            displaying_code = self.code_display.toPlainText()
            
            if not displaying_code or not displaying_code.strip():
                self.log_message("⚠️ No generated code found to refresh tasks")
                return
            
            if not self.req_class:
                self.log_message("⚠️ No existing tasks found to refresh")
                return
            
            self.log_message("🔄 Refreshing tasks based on generated code...")
            
            # import task_refreshing
            
            # updated_req_class = task_refreshing.gemini_response(displaying_code, self.req_class)
            
            # if isinstance(updated_req_class, list) and updated_req_class:
            #     old_count = len(self.req_class)
            #     self.req_class = updated_req_class
            #     new_count = len(self.req_class)
                
            #     self.update_generated_tasks_display()
                
            #     self.log_message(f"✅ Tasks refreshed successfully! Updated from {old_count} to {new_count} steps")
                
            #     self.update_tasks_status(f"Tasks refreshed: {new_count} steps", "#4CAF50")
                
            # else:
            #     self.log_message("⚠️ Task refreshing returned invalid data, keeping original tasks")
                
        except Exception as e:
            self.log_message(f"❌ Error refreshing tasks: {str(e)}")
            print(f"Error in refresh_tasks_from_code: {e}")
    
    def update_generated_tasks_display(self):
        """Update the generated tasks display with refreshed tasks"""
        try:
            # Check if task_list exists and has the necessary methods
            if hasattr(self, 'task_list') and self.task_list:
                # Update the task list with new data
                self.task_list.set_tasks_data(self.req_class)
                
                # If we have app_info, set it as well
                if hasattr(self, 'app_info') and self.app_info:
                    self.task_list.set_app_info(self.app_info)
                
                # If we have conditional_info, set it as well
                if hasattr(self, 'conditional_info') and self.conditional_info:
                    self.task_list.set_conditional_info(self.conditional_info)
                
                self.log_message("✅ Generated tasks display updated successfully")
            if hasattr(self.parent(), 'task_list') and self.parent().task_list:
                # Update the task list with new data
                self.parent().task_list.set_tasks_data(self.req_class)
                
                # If we have app_info, set it as well
                if hasattr(self.parent(), 'app_info') and self.parent().app_info:
                    self.parent().task_list.set_app_info(self.parent().app_info)
                
                # If we have conditional_info, set it as well
                if hasattr(self.parent(), 'conditional_info') and self.parent().conditional_info:
                    self.parent().task_list.set_conditional_info(self.parent().conditional_info)
                
                self.parent().log_message("✅ Generated tasks display updated successfully")
            else:
                self.log_message("⚠️ Task list widget not found, cannot update display")
                
        except Exception as e:
            self.log_message(f"❌ Error updating generated tasks display: {str(e)}")
            print(f"Error in update_generated_tasks_display: {e}")
    
    def update_xpath_from_modified_code(self, modified_code):
        """Extract XPath variables from modified code and update XPath JSON and tab"""
        try:
            # Determine current automation mode
            current_mode = getattr(self, 'current_automation_mode', 'web')
            
            if current_mode == 'desktop':
                self.log_message("🔄 Extracting Attributes variables from modified code...")
                
                # Import and call desktop_attr_find.analyze_code_for_attributes()
                from datas.process_flow.desktop_process import desktop_attr_find
                import os
                import json
                
                # Call desktop_attr_find to extract attribute variables
                xpaths_json = desktop_attr_find.analyze_code_for_attributes(modified_code)
            elif current_mode == 'citrix':
                self.log_message("🔄 Extracting Citrix variables from modified code...")
                
                # Import and call citrix xpath_correction equivalent
                from datas.process_flow.Citrix_process import citrix_json_correction  # Use same xpath_correction for citrix
                import os
                import json
                
                # Call xpath_correction to extract Citrix variables
                xpaths_json = citrix_json_correction.gemini_response(modified_code)
            else:
                self.log_message("🔄 Extracting XPath variables from modified code...")
                
                # Import and call xpath_correction.gemini_response()
                import xpath_correction
                import os
                import json
                
                # Call xpath_correction to extract XPath variables
                xpaths_json = xpath_correction.gemini_response(modified_code)
            # Check if we got a valid dictionary back
            if isinstance(xpaths_json, dict):
                # Ensure json_info directory exists
                os.makedirs("json_info", exist_ok=True)
                
                 # Determine which JSON file to save based on current automation mode
                current_mode = getattr(self, 'current_automation_mode', 'web')
                
                if current_mode == 'desktop':
                    json_path = "json_info/json_attr.json"
                    data_type = "Attributes"
                elif current_mode == 'citrix':
                    json_path = "json_info/citrix_data.json"
                    data_type = "Citrix"
                else:
                    json_path = "json_info/json_xpath.json"
                    data_type = "XPath"
                
                # Write the entire JSON data to appropriate file
                with open(json_path, "w", encoding="utf-8") as f:
                    json.dump(xpaths_json, f, indent=4, ensure_ascii=False)
                
                self.log_message(f"✅ {data_type} JSON updated with {len(xpaths_json)} variables")
                self.log_message(f"📄 {data_type} data written to: {json_path}")
                # Update the XPath tab if it exists
                self.update_xpath_tab_display(xpaths_json)
                
            else:
                self.log_message("⚠️ XPath extraction returned invalid data, skipping update")
                
        except Exception as e:
            data_type = "Attributes" if getattr(self, 'current_automation_mode', 'web') == 'desktop' else "XPath"
            self.log_message(f"❌ Error extracting {data_type} variables: {str(e)}")
            print(f"Error in update_xpath_from_modified_code: {e}")
    
    def update_xpath_tab_display(self, xpaths_json):
        """Update the XPath tab display with new XPath data"""
        try:
            # Check if chat panel exists and has XPath functionality - REMOVED
            # if hasattr(self, 'chat_panel') and self.chat_panel:
            #     # Refresh the XPath data in chat panel
            #     self.chat_panel.refresh_xpath_data()  # Removed
            #     self.log_message("✅ XPath tab display updated successfully")
            # else:
            #     self.log_message("⚠️ XPath tab not found, cannot update display")  # Removed
            self.log_message("✅ XPath functionality removed with chat panel")
                
        except Exception as e:
            self.log_message(f"❌ Error updating XPath tab display: {str(e)}")
            print(f"Error in update_xpath_tab_display: {e}")
    

    def refresh_code_tab_ui_text(self):
        """Refresh Code tab UI text based on current automation mode"""
        try:
            current_mode = getattr(self, 'current_automation_mode', 'web')
            
            # Update header label
            if hasattr(self, 'xpath_header_label'):
                if current_mode == 'desktop':
                    header_text = "Attributes Configuration"
                elif current_mode == 'citrix':
                    header_text = "Citrix Configuration"
                else:
                    header_text = "XPath Configuration"
                self.xpath_header_label.setText(header_text)
            
            # Update search placeholder
            if hasattr(self, 'code_tab_xpath_search'):
                if current_mode == 'desktop':
                    placeholder_text = "🔍 Search attributes keys or values..."
                elif current_mode == 'citrix':
                    placeholder_text = "🔍 Search citrix keys or values..."
                else:
                    placeholder_text = "🔍 Search XPath keys or values..."
                self.code_tab_xpath_search.setPlaceholderText(placeholder_text)
            
            # Update refresh button tooltip
            if hasattr(self, 'code_tab_refresh_xpath_btn'):
                if current_mode == 'desktop':
                    tooltip_text = "Refresh attributes data"
                elif current_mode == 'citrix':
                    tooltip_text = "Refresh citrix data"
                else:
                    tooltip_text = "Refresh XPath data"
                self.code_tab_refresh_xpath_btn.setToolTip(tooltip_text)
            
            # Refresh the display to update status text
            if hasattr(self, 'update_code_tab_xpath_display'):
                self.update_code_tab_xpath_display()
                
        except Exception as e:
            print(f"Error refreshing Code tab UI text: {e}")
            
    def update_json_tab_name(self, automation_mode):
        """Update the JSON tab name based on automation mode"""
        try:
            # Update main content tabs (XPath tab)
            if hasattr(self, 'content_tabs'):
                tab_widget = self.content_tabs
                
                # Find the tab index by checking tab text
                for i in range(tab_widget.count()):
                    tab_text = tab_widget.tabText(i)
                    if tab_text in ["XPath", "Attributes Details", "XPath/Attributes", "Citrix Data Details"]:
                        # Update tab name based on automation mode
                        if automation_mode == 'desktop':
                            tab_widget.setTabText(i, "Attributes Details")
                            self.log_message("📝 Main tab renamed to: Attributes Details")
                        elif automation_mode == 'citrix':
                            tab_widget.setTabText(i, "Citrix Data Details")
                            self.log_message("📝 Main tab renamed to: Citrix Data Details")
                        else:
                            tab_widget.setTabText(i, "XPath")
                            self.log_message("📝 Main tab renamed to: XPath")
                        break
            
            # Update Code Tab XPath Variables button
            if hasattr(self, 'xpath_vars_btn'):
                if automation_mode == 'desktop':
                    self.xpath_vars_btn.setText("Attributes Details")
                    self.log_message("📝 Code tab button renamed to: Attributes Details")
                elif automation_mode == 'citrix':
                    self.xpath_vars_btn.setText("Citrix Data Details")
                    self.log_message("📝 Code tab button renamed to: Citrix Data Details")
                else:
                    self.xpath_vars_btn.setText("XPath Variables")
                    self.log_message("📝 Code tab button renamed to: XPath Variables")
            # Also refresh the Code tab UI text to match the new mode
            if hasattr(self, 'refresh_code_tab_ui_text'):
                self.refresh_code_tab_ui_text()
                        
        except Exception as e:
            print(f"Error updating JSON tab name: {e}")
            self.log_message(f"❌ Error updating tab names: {str(e)}")
    
    def on_undo_clicked(self):
        """Handle undo button click"""
        if self.code_display.undo():
            # Get the current code after undo
            current_code = self.code_display.toPlainText()
            
            # Update code_log variable
            self.code_log = current_code
            
            # Update the execute_code.py file in real-time
            try:
                import os
                code_file_path = "code_py/execute_code.py"
                os.makedirs("code_py", exist_ok=True)
                with open(code_file_path, "w", encoding="utf-8") as f:
                    f.write(current_code)
                print("✅ Undo successful - code_log and execute_code.py updated")
            except Exception as e:
                print(f"⚠️ Undo successful but failed to update file: {e}")
        else:
            print("⚠️ No undo history available")
    
    def on_redo_clicked(self):
        """Handle redo button click"""
        if self.code_display.redo():
            # Get the current code after redo
            current_code = self.code_display.toPlainText()
            
            # Update code_log variable
            self.code_log = current_code
            
            # Update the execute_code.py file in real-time
            try:
                import os
                code_file_path = "code_py/execute_code.py"
                os.makedirs("code_py", exist_ok=True)
                with open(code_file_path, "w", encoding="utf-8") as f:
                    f.write(current_code)
                print("✅ Redo successful - code_log and execute_code.py updated")
            except Exception as e:
                print(f"⚠️ Redo successful but failed to update file: {e}")
        else:
            print("⚠️ No redo history available")
    
    def update_undo_redo_buttons(self, can_undo, can_redo):
        """Update undo/redo button enabled states"""
        self.undo_btn.setEnabled(can_undo)
        self.redo_btn.setEnabled(can_redo)
    
    def on_new_chat_clicked(self):
        """Handle New Chat button click - clear chat history and start fresh"""
        if not hasattr(self, 'ui_chat_history') or len(self.ui_chat_history) == 0:
            print("ℹ️ No chat history to clear - starting fresh")
            # Clear the chat messages layout
            if hasattr(self, 'chat_messages_layout'):
                while self.chat_messages_layout.count() > 1:  # Keep the stretch
                    item = self.chat_messages_layout.takeAt(0)
                    if item.widget():
                        item.widget().deleteLater()
            self.chat_history = []
            self.ui_chat_history = []
            return
        
        # Display current chat history before clearing
        try:
            print(f"📋 Current chat history has {len(self.ui_chat_history)} messages")
            history_text = "=== Chat History ===\n\n"
            
            for msg in self.ui_chat_history:
                try:
                    sender = msg.get('sender', 'Unknown')
                    message = msg.get('message', '')
                    timestamp = msg.get('timestamp', '')
                    history_text += f"[{sender}] {timestamp}:\n{message}\n\n"
                except Exception as e:
                    print(f"[WARN] Error processing history message: {e}")
                    history_text += f"{str(msg)}\n\n"
            
            # Show history in a message box
            msg_box = QMessageBox(self)
            msg_box.setWindowTitle("Current Chat History")
            msg_box.setText("Chat history will be cleared after closing this dialog.")
            msg_box.setDetailedText(history_text)
            msg_box.setStandardButtons(QMessageBox.Ok | QMessageBox.Cancel)
            msg_box.setStyleSheet("""
                QMessageBox {
                    background-color: #1e1e1e;
                }
                QMessageBox QLabel {
                    color: #d4d4d4;
                }
                QMessageBox QTextEdit {
                    background-color: #252526;
                    color: #d4d4d4;
                    border: 1px solid #3c3c3c;
                }
                QPushButton {
                    background-color: #0066cc;
                    color: white;
                    border: none;
                    border-radius: 4px;
                    padding: 6px 16px;
                    min-width: 60px;
                }
                QPushButton:hover {
                    background-color: #0078d7;
                }
                QPushButton:pressed {
                    background-color: #005a9e;
                }
            """)
            
            result = msg_box.exec_()
            
            if result == QMessageBox.Ok:
                # Clear chat history and UI
                self.chat_history = []
                self.ui_chat_history = []
                
                # Clear the chat messages layout
                if hasattr(self, 'chat_messages_layout'):
                    while self.chat_messages_layout.count() > 1:  # Keep the stretch
                        item = self.chat_messages_layout.takeAt(0)
                        if item.widget():
                            item.widget().deleteLater()
                
                print("✅ New Chat started - history cleared")
                self.add_chat_message("System", "New chat started. Chat history has been cleared.", is_user=False)
            else:
                print("⚠️ Chat history was not cleared")
        
        except Exception as e:
            print(f"❌ Error handling New Chat: {e}")
            import traceback
            traceback.print_exc()
            # Still clear the history even if there's an error
            self.chat_history = []
            self.ui_chat_history = []
            if hasattr(self, 'chat_messages_layout'):
                while self.chat_messages_layout.count() > 1:  # Keep the stretch
                    item = self.chat_messages_layout.takeAt(0)
                    if item.widget():
                        item.widget().deleteLater()
    
    def on_task_new_chat_clicked(self):
        """Handle New Chat button click for task chat - clear history silently"""
        try:
            if hasattr(self, 'task_chat_history'):
                self.task_chat_history = []
                print("✅ Cleared Gemini task_chat_history for new task chat")
            
            if hasattr(self, 'ui_task_chat_history'):
                self.ui_task_chat_history = []
                print("✅ Cleared UI task_chat_history for new task chat")
            
            # Clear the task chat messages layout
            if hasattr(self, 'task_chat_layout'):
                while self.task_chat_layout.count() > 1:  # Keep the stretch
                    item = self.task_chat_layout.takeAt(0)
                    if item.widget():
                        item.widget().deleteLater()
                print("✅ Cleared task chat display widgets")
            
            # Add system message
            self.add_task_chat_message("System", "New task chat started. History cleared.", is_user=False)
            print("[TASK CHAT] New Chat started - history cleared")
            
        except Exception as e:
            print(f"❌ Error handling task new chat: {e}")
            import traceback
            traceback.print_exc()
            # Still try to clear the history even if there's an error
            if hasattr(self, 'task_chat_history'):
                self.task_chat_history = []
            if hasattr(self, 'ui_task_chat_history'):
                self.ui_task_chat_history = []
            if hasattr(self, 'task_chat_layout'):
                while self.task_chat_layout.count() > 1:
                    item = self.task_chat_layout.takeAt(0)
                    if item.widget():
                        item.widget().deleteLater()
    
    def sync_code_changes(self):
        """Manually sync Code tab content to code_py/execute_code.py using worker thread"""
        try:
            # Get current code from Code tab display
            current_code = self.code_display.toPlainText()
            
            if not current_code.strip():
                self.log_display.append(f"[{datetime.now().strftime('%H:%M:%S')}] ⚠️ No code to sync")
                return
            
            # Set droid overlay to SYNCING CHANGES state
            if hasattr(self, 'processing_widget') and self.processing_widget:
                self.processing_widget.set_syncing_changes_state()
                print("🔄 Set droid overlay to SYNCING CHANGES state")
            
            # Log sync start
            self.log_display.append(f"[{datetime.now().strftime('%H:%M:%S')}] 🔄 Starting code sync...")
            
            # Create and start sync worker thread
            self.sync_worker = SyncCodeWorker(current_code)
            
            # Connect signals
            self.sync_worker.progress_update.connect(self.on_sync_progress)
            self.sync_worker.sync_completed.connect(self.on_sync_completed)
            self.sync_worker.error_occurred.connect(self.on_sync_error)
            
            # Start the worker thread
            self.sync_worker.start()
            
        except Exception as e:
            self.log_display.append(f"[{datetime.now().strftime('%H:%M:%S')}] ❌ Error starting code sync: {str(e)}")
            print(f"Error starting code sync: {e}")
            
            # Set droid overlay back to previous state on error
            if hasattr(self, 'processing_widget') and self.processing_widget:
                self.processing_widget.set_ready_for_execution_state()
                print("❌ Set droid overlay back to READY FOR EXECUTION state after error")
    
    def on_sync_progress(self, message):
        """Handle progress updates from sync worker"""
        self.log_display.append(f"[{datetime.now().strftime('%H:%M:%S')}] {message}")
        print(message)
    
    def on_sync_completed(self):
        """Handle completion of sync worker"""
        self.log_display.append(f"[{datetime.now().strftime('%H:%M:%S')}] ✅ Code changes synced successfully!")
        print("✅ Code sync completed successfully")
        
        # Set droid overlay back to READY FOR EXECUTION state
        if hasattr(self, 'processing_widget') and self.processing_widget:
            self.processing_widget.set_ready_for_execution_state()
            print("✅ Set droid overlay back to READY FOR EXECUTION state after sync")
        
        # Clean up worker thread
        if hasattr(self, 'sync_worker') and self.sync_worker is not None:
            self.sync_worker.deleteLater()
            self.sync_worker = None
    
    def on_sync_error(self, error_message):
        """Handle errors from sync worker"""
        self.log_display.append(f"[{datetime.now().strftime('%H:%M:%S')}] ❌ Error during code sync: {error_message}")
        print(f"❌ Error during code sync: {error_message}")
        
        # Set droid overlay back to READY FOR EXECUTION state on error
        if hasattr(self, 'processing_widget') and self.processing_widget:
            self.processing_widget.set_ready_for_execution_state()
            print("❌ Set droid overlay back to READY FOR EXECUTION state after sync error")
        
        # Show error message to user
        QMessageBox.warning(self, "⚠️ Sync Error", f"Code sync failed:\n{error_message}")
        
        # Clean up worker thread
        if hasattr(self, 'sync_worker') and self.sync_worker is not None:
            self.sync_worker.deleteLater()
            self.sync_worker = None
    
    # def stop_execution(self):
    #     """Stop the currently running code execution"""
    #     try:
    #         if hasattr(self, 'execute_worker') and self.execute_worker is not None:
    #             self.log_display.append(f"[{datetime.now().strftime('%H:%M:%S')}] 🛑 Stopping code execution...")
    #             print("🛑 Stopping code execution...")
                
    #             # Stop the worker thread
    #             self.execute_worker.stop_execution()
                
    #             # Reset button states and appearance immediately
    #             self.set_execute_button_normal_state()
    #             self.stop_btn.setEnabled(False)
                
    #             # Set droid overlay back to PROCESS PENDING state
    #             if hasattr(self, 'processing_widget') and self.processing_widget:
    #                 self.processing_widget.set_process_pending_state()
    #                 print("🛑 Set droid overlay back to PROCESS PENDING state after stop")
                
    #             # Properly clean up worker thread
    #             if self.execute_worker.isRunning():
    #                 print("⏳ Waiting for execution thread to finish...")
    #                 # Wait for thread to finish with timeout
    #                 if not self.execute_worker.wait(5000):  # Wait up to 5 seconds
    #                     print("⚠️ Thread did not finish gracefully, terminating...")
    #                     self.execute_worker.terminate()
    #                     if not self.execute_worker.wait(2000):  # Wait 2 more seconds after terminate
    #                         print("❌ Thread failed to terminate, forcing cleanup...")
                
    #             # Schedule deletion safely
    #             self.execute_worker.finished.connect(self.execute_worker.deleteLater)
    #             self.execute_worker = None
                
    #             self.log_display.append(f"[{datetime.now().strftime('%H:%M:%S')}] ✅ Code execution stopped successfully")
    #             print("✅ Code execution stopped successfully")

    #             # Revert sidebar buttons: enable Execute if code exists, disable STOP
    #             try:
    #                 if hasattr(self, 'execute_flow_btn'):
    #                     has_code = bool(self.code_display.toPlainText().strip())
    #                     self.execute_flow_btn.setEnabled(has_code)
    #                 if hasattr(self, 'stop_flow_btn'):
    #                     self.stop_flow_btn.setEnabled(False)
    #             except Exception:
    #                 pass
                
    #         else:
    #             self.log_display.append(f"[{datetime.now().strftime('%H:%M:%S')}] ⚠️ No running execution to stop")
    #             # Ensure sidebar STOP is disabled when nothing is running
    #             try:
    #                 if hasattr(self, 'stop_flow_btn'):
    #                     self.stop_flow_btn.setEnabled(False)
    #             except Exception:
    #                 pass
                
    #     except Exception as e:
    #         self.log_display.append(f"[{datetime.now().strftime('%H:%M:%S')}] ❌ Error stopping execution: {str(e)}")
    #         print(f"Error stopping execution: {e}")
            
    #         # Ensure cleanup even on error
    #         if hasattr(self, 'execute_worker') and self.execute_worker is not None:
    #             try:
    #                 self.execute_worker.finished.connect(self.execute_worker.deleteLater)
    #                 self.execute_worker = None
    #             except:
    #                 pass

    def stop_execution(self):
        """Stop the currently running code execution"""
        try:
            if hasattr(self, 'execute_worker') and self.execute_worker is not None:
                self.log_display.append(f"[{datetime.now().strftime('%H:%M:%S')}] 🛑 Stopping code execution...")
                print("🛑 Stopping code execution...")
                
                # First, terminate the subprocess if it's running
                from subprocess_aba_runner import terminate_running_process
                subprocess_terminated = terminate_running_process()
                if subprocess_terminated:
                    self.log_display.append(f"[{datetime.now().strftime('%H:%M:%S')}] ✅ Subprocess terminated")
                    print("✅ Subprocess terminated")
                
                # Stop the worker thread
                self.execute_worker.stop_execution()
                
                # Reset button states and appearance immediately
                self.set_execute_button_normal_state()
                self.stop_btn.setEnabled(False)
                
                # Set droid overlay back to PROCESS PENDING state
                if hasattr(self, 'processing_widget') and self.processing_widget:
                    self.processing_widget.set_process_pending_state()
                    print("🛑 Set droid overlay back to PROCESS PENDING state after stop")
                
                # Properly clean up worker thread
                if self.execute_worker.isRunning():
                    print("⏳ Waiting for execution thread to finish...")
                    # Wait for thread to finish with timeout
                    if not self.execute_worker.wait(5000):  # Wait up to 5 seconds
                        print("⚠️ Thread did not finish gracefully, terminating...")
                        self.execute_worker.terminate()
                        if not self.execute_worker.wait(2000):  # Wait 2 more seconds after terminate
                            print("❌ Thread failed to terminate, forcing cleanup...")
                
                # Schedule deletion safely
                self.execute_worker.finished.connect(self.execute_worker.deleteLater)
                self.execute_worker = None
                
                self.log_display.append(f"[{datetime.now().strftime('%H:%M:%S')}] ✅ Code execution stopped successfully")
                print("✅ Code execution stopped successfully")

                # Revert sidebar buttons: enable Execute if code exists, disable STOP
                try:
                    if hasattr(self, 'execute_flow_btn'):
                        has_code = bool(self.code_display.toPlainText().strip())
                        self.execute_flow_btn.setEnabled(has_code)
                    if hasattr(self, 'stop_flow_btn'):
                        self.stop_flow_btn.setEnabled(False)
                except Exception:
                    pass
                
            else:
                self.log_display.append(f"[{datetime.now().strftime('%H:%M:%S')}] ⚠️ No running execution to stop")
                # Ensure sidebar STOP is disabled when nothing is running
                try:
                    if hasattr(self, 'stop_flow_btn'):
                        self.stop_flow_btn.setEnabled(False)
                except Exception:
                    pass
                
        except Exception as e:
            self.log_display.append(f"[{datetime.now().strftime('%H:%M:%S')}] ❌ Error stopping execution: {str(e)}")
            print(f"Error stopping execution: {e}")
            
            # Ensure cleanup even on error
            if hasattr(self, 'execute_worker') and self.execute_worker is not None:
                try:
                    self.execute_worker.finished.connect(self.execute_worker.deleteLater)
                    self.execute_worker = None
                except:
                    pass
            
            # Try to terminate subprocess even on error
            try:
                from subprocess_aba_runner import terminate_running_process
                terminate_running_process()
            except:
                pass


    def set_execute_button_processing_state(self):
        """Set execute button to processing state - grey and disabled appearance"""
        self.execute_btn.setEnabled(False)
        self.execute_btn.setText(" Processing...")
        self.execute_btn.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:1, x2:0, y2:0,
                                            stop:0 #666666, stop:1 #888888);
                border-radius: 10px;
                color: #AAAAAA;
                font-family: 'Asen Pro', sans-serif;
                font-weight: 600;
                font-size: 16px;
                letter-spacing: 0.05em;
                text-align: left;
                padding-left: 20px;
                border: 1px solid #555555;
            }
            QPushButton:disabled {
                background: qlineargradient(x1:0, y1:1, x2:0, y2:0,
                                            stop:0 #666666, stop:1 #888888);
                color: #AAAAAA;
                border: 1px solid #555555;
            }
        """)
        print("🔧 Execute button set to processing state (grey)")
    
    def set_execute_button_normal_state(self):
        """Restore execute button to normal state - blue and enabled"""
        self.execute_btn.setEnabled(True)
        self.execute_btn.setText(" Execute Code")
        self.execute_btn.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:1, x2:0, y2:0,
                                            stop:0 #005B7F, stop:1 #008AB3);
                border-radius: 10px;
                color: #FFFFFF;
                font-family: 'Asen Pro', sans-serif;
                font-weight: 600;
                font-size: 16px;
                letter-spacing: 0.05em;
                text-align: left;
                padding-left: 20px;
                border: none;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:1, x2:0, y2:0,
                                            stop:0 #006B8F, stop:1 #009AC3);
            }
            QPushButton:pressed {
                background: qlineargradient(x1:0, y1:1, x2:0, y2:0,
                                            stop:0 #004B6F, stop:1 #007A93);
            }
            QPushButton:disabled {
                background: qlineargradient(x1:0, y1:1, x2:0, y2:0,
                                            stop:0 #666666, stop:1 #888888);
                color: #AAAAAA;
                border: 1px solid #555555;
            }
        """)
        print("🔧 Execute button restored to normal state (blue)")

    def on_breakpoint_hit(self, task_index):
        """Handle when a breakpoint is hit during execution"""
        timestamp = datetime.now().strftime('%H:%M:%S')
        self.log_display.append(f"[{timestamp}] 🔴 BREAKPOINT HIT at Task {task_index}")
        self.log_display.append(f"[{timestamp}] ⏸️ Execution paused. Click 'Continue' to resume...")
        
        # Store current task index for resume
        self.current_breakpoint_task = task_index
        
        # Highlight the breakpoint line in code display
        self.highlight_breakpoint_line(task_index)
        
        # Change Execute button to Continue button
        self.set_continue_button_state()

    def set_continue_button_state(self):
        """Change Execute button to Continue button during breakpoint"""
        if hasattr(self, 'execute_flow_btn'):
            self.execute_flow_btn.setText("▶️ Continue")
            self.execute_flow_btn.setIcon(QIcon(resource_path("styles/Icon/play.png")))
            self.execute_flow_btn.setEnabled(True)
            self.execute_flow_btn.show()

            if hasattr(self, 'processing_widget') and self.processing_widget:
                self.processing_widget.set_waiting_state()
                print("⏳ Set droid overlay to WAITING state")
            
            # Disconnect old signal and connect to continue handler
            try:
                self.execute_flow_btn.clicked.disconnect()
            except:
                pass
            self.execute_flow_btn.clicked.connect(lambda: (self.play_click_sound(), self.on_continue_from_breakpoint()))

    def set_execute_button_normal_state(self):
        """Reset Execute button to normal state"""
        if hasattr(self, 'execute_flow_btn'):
            self.execute_flow_btn.setText("▶️ Execute Flow")
            self.execute_flow_btn.setIcon(QIcon(resource_path("styles/Icon/play.png")))
            self.execute_flow_btn.setEnabled(True)
            
            # Reconnect to execute_code
            try:
                self.execute_flow_btn.clicked.disconnect()
            except:
                pass
            self.execute_flow_btn.clicked.connect(lambda: (self.play_click_sound(), self.execute_code()))

    def on_continue_from_breakpoint(self):
        """Handle continue button click during breakpoint"""
        timestamp = datetime.now().strftime('%H:%M:%S')
        self.log_display.append(f"[{timestamp}] ▶️ Continuing execution from Task {self.current_breakpoint_task}...")
        
        # Clear highlight
        self.clear_breakpoint_highlight()
        
        if hasattr(self, 'execute_flow_btn'):
            self.execute_flow_btn.setText("▶️ Execute Flow")
            self.execute_flow_btn.setIcon(QIcon(resource_path("styles/Icon/play.png")))
            self.execute_flow_btn.setEnabled(False)

            if hasattr(self, 'processing_widget') and self.processing_widget:
                self.processing_widget.set_process_executing_state()
                print("🚀 Set droid overlay to PROCESS EXECUTING state")
            
            # Reconnect to execute_code for next run
            try:
                self.execute_flow_btn.clicked.disconnect()
            except:
                pass
            self.execute_flow_btn.clicked.connect(lambda: (self.play_click_sound(), self.execute_code()))
        
        
        # Write continue signal file to resume execution
        try:
            import os
            import json
            os.makedirs("json_info", exist_ok=True)
            continue_file = "json_info/breakpoint_continue.json"
            with open(continue_file, "w") as f:
                json.dump({"continue": True, "task_index": self.current_breakpoint_task}, f)
            print(f"✅ Written continue signal for task {self.current_breakpoint_task}")
        except Exception as e:
            print(f"Error writing continue signal: {e}")
            self.log_display.append(f"[{timestamp}] ❌ Error resuming execution: {str(e)}")

    def highlight_breakpoint_line(self, task_index):
        """Highlight the line where breakpoint was hit"""
        try:
            cursor = self.code_display.textCursor()
            code_text = self.code_display.toPlainText()
            lines = code_text.split('\n')
            
            # Find the line with the task (assuming task comments like "# Step X:" or checking breakpoint)
            target_line = -1
            for i, line in enumerate(lines):
                if f"check_breakpoint({task_index})" in line or f"# Step {task_index + 1}:" in line:
                    target_line = i
                    break
            
            if target_line >= 0:
                # Store original format before highlighting
                if not hasattr(self, 'original_text_format'):
                    self.original_text_format = {}
                
                # Move cursor to the start of the target line
                cursor.movePosition(cursor.MoveOperation.Start)
                for _ in range(target_line):
                    cursor.movePosition(cursor.MoveOperation.Down)
                
                # Select the entire line
                cursor.movePosition(cursor.MoveOperation.StartOfLine)
                cursor.movePosition(cursor.MoveOperation.EndOfLine, cursor.MoveMode.KeepAnchor)
                
                # Store original background
                self.original_text_format[target_line] = cursor.charFormat().background()
                
                # Apply highlight format
                highlight_format = cursor.charFormat()
                highlight_format.setBackground(QColor(255, 200, 200))  # Light red background
                cursor.mergeCharFormat(highlight_format)
                
                # Store the line number for later clearing
                self.highlighted_line = target_line
                
                # Scroll to the highlighted line
                self.code_display.setTextCursor(cursor)
                self.code_display.ensureCursorVisible()
                
        except Exception as e:
            print(f"Error highlighting breakpoint line: {e}")

    def clear_breakpoint_highlight(self):
        """Remove breakpoint highlighting from code display"""
        try:
            if not hasattr(self, 'highlighted_line'):
                return
                
            cursor = self.code_display.textCursor()
            
            # Move to the highlighted line
            cursor.movePosition(cursor.MoveOperation.Start)
            for _ in range(self.highlighted_line):
                cursor.movePosition(cursor.MoveOperation.Down)
            
            # Select the entire line
            cursor.movePosition(cursor.MoveOperation.StartOfLine)
            cursor.movePosition(cursor.MoveOperation.EndOfLine, cursor.MoveMode.KeepAnchor)
            
            # Restore original format
            if hasattr(self, 'original_text_format') and self.highlighted_line in self.original_text_format:
                restore_format = cursor.charFormat()
                restore_format.setBackground(self.original_text_format[self.highlighted_line])
                cursor.mergeCharFormat(restore_format)
            
            # Move cursor to start to deselect
            cursor.movePosition(cursor.MoveOperation.Start)
            self.code_display.setTextCursor(cursor)
            
            # Clean up
            delattr(self, 'highlighted_line')
            
        except Exception as e:
            print(f"Error clearing breakpoint highlight: {e}")
    

    def execute_code(self):
        """Execute the code from code_py/execute_code.py file using worker thread"""
        try:
            # Check if execution is already running
            if hasattr(self, 'execute_worker') and self.execute_worker is not None:
                self.log_display.append(f"[{datetime.now().strftime('%H:%M:%S')}] ⚠️ Code execution already in progress")
                return
            
            # Get current code from Code tab display
            current_code = self.code_display.toPlainText()
            
            if not current_code.strip():
                self.log_display.append(f"[{datetime.now().strftime('%H:%M:%S')}] ⚠️ No code to execute")
                return
            
            # Update button states and appearance
            self.set_execute_button_processing_state()
            self.stop_btn.setEnabled(True)
            
            # Set droid overlay to PROCESS EXECUTING state
            if hasattr(self, 'processing_widget') and self.processing_widget:
                self.processing_widget.set_process_executing_state()
                print("🚀 Set droid overlay to PROCESS EXECUTING state")
            
            # Log execution start
            self.log_display.append(f"[{datetime.now().strftime('%H:%M:%S')}] 🚀 Starting code execution...")
            
            # Create and start execute worker thread
            print(f"Breakpoints : {self.task_list.breakpoints}")
            self.execute_worker = ExecuteCodeWorker(current_code,self.task_list.breakpoints)
            
            
            # Connect signals
            self.execute_worker.progress_update.connect(self.on_execute_progress)
            self.execute_worker.output_received.connect(self.on_execute_output)
            self.execute_worker.error_received.connect(self.on_execute_error_output)
            self.execute_worker.execution_finished.connect(self.on_execute_finished)
            self.execute_worker.error_occurred.connect(self.on_execute_exception_handler)
            
            # Connect new popup signals
            # self.execute_worker.element_confirmation_requested.connect(self.show_element_confirmation_popup)
            # self.execute_worker.xpath_modification_requested.connect(self.show_xpath_modification_popup)
            
            # Connect response signals
            self.execute_worker.element_confirmation_response.connect(self.execute_worker.handle_element_confirmation_response)
            self.execute_worker.xpath_modification_response.connect(self.execute_worker.handle_xpath_modification_response)
            
            try:
                self.execute_worker.breakpoint_hit.disconnect()
            except:
                pass

            # Now connect
            self.execute_worker.breakpoint_hit.connect(self.on_breakpoint_hit)
            
            # Start the worker thread
            self.execute_worker.start()
            
            # Disable Execute Flow and enable STOP in sidebar
            try:
                if hasattr(self, 'execute_flow_btn'):
                    self.execute_flow_btn.setEnabled(False)
                if hasattr(self, 'stop_flow_btn'):
                    self.stop_flow_btn.setEnabled(True)
            except Exception:
                pass
            
        except Exception as e:
            # Reset button states and appearance on error
            self.set_execute_button_normal_state()
            self.stop_btn.setEnabled(False)
            
            self.log_display.append(f"[{datetime.now().strftime('%H:%M:%S')}] ❌ Error starting code execution: {str(e)}")
            print(f"Error starting code execution: {e}")
            
            # Set droid overlay back to PROCESS PENDING state on error
            if hasattr(self, 'processing_widget') and self.processing_widget:
                self.processing_widget.set_process_pending_state()
                print("❌ Set droid overlay back to PROCESS PENDING state after error")

            # Revert sidebar buttons on error: enable Execute if code exists, disable STOP
            try:
                if hasattr(self, 'execute_flow_btn'):
                    has_code = bool(self.code_display.toPlainText().strip())
                    self.execute_flow_btn.setEnabled(has_code)
                if hasattr(self, 'stop_flow_btn'):
                    self.stop_flow_btn.setEnabled(False)
            except Exception:
                pass
    
    def on_execute_progress(self, message):
        """Handle progress updates from execute worker"""
        self.log_display.append(f"[{datetime.now().strftime('%H:%M:%S')}] {message}")
        print(message)
        
        # Process Qt events to keep UI responsive
        QApplication.processEvents()
    
    def on_execute_output(self, output):
        """Handle stdout output from execute worker"""
        self.log_display.append(f"[{datetime.now().strftime('%H:%M:%S')}] 📄 Output:\n{output}")
        print(f"Execution output: {output}")
    
    def on_execute_error_output(self, error_output):
        """Handle stderr output from execute worker"""
        self.log_display.append(f"[{datetime.now().strftime('%H:%M:%S')}] ❌ Error Output:\n{error_output}")
        print(f"Execution error output: {error_output}")
    
    def on_execute_finished(self, return_code):
        """Handle completion of execute worker"""
        # Reset button states and appearance after execution
        self.set_execute_button_normal_state()
        self.stop_btn.setEnabled(False)
        # Log completion status
        if return_code == 0:
            self.log_display.append(f"[{datetime.now().strftime('%H:%M:%S')}] ✅ Code execution completed successfully")
            self.generate_code_btn.setEnabled(True)
            print("✅ Code execution completed successfully")
        else:
            self.log_display.append(f"[{datetime.now().strftime('%H:%M:%S')}] ❌ Code execution failed with return code {return_code}")
            print(f"❌ Code execution failed with return code {return_code}")
            
            # Check for exception file when execution failed
            import os
            import json
            exception_file = "json_info/exception_info.json"
            if os.path.exists(exception_file):
                try:
                    with open(exception_file, "r", encoding="utf-8") as f:
                        exception_info = json.load(f)
                    
                    if exception_info.get("code_exception") is not None:
                        # Handle the exception by calling the exception handler directly
                        self.handle_code_exception(exception_info['code_exception'])
                        print(f"[ERROR] Exception detected in failed execution: {exception_info['code_exception']}")
                except Exception as e:
                    print(f"[ERROR] Error reading exception file: {e}")
            if os.path.exists(exception_file):
                os.remove(exception_file)
            
        # Set droid overlay to WAITING state
        if hasattr(self, 'processing_widget') and self.processing_widget:
            self.processing_widget.set_waiting_state()
            print("⏳ Set droid overlay to WAITING state")
        
        # Clean up worker thread safely
        if hasattr(self, 'execute_worker') and self.execute_worker is not None:
            # Schedule safe deletion
            self.execute_worker.finished.connect(self.execute_worker.deleteLater)
            self.execute_worker = None
            
            # Revert Execute Flow and STOP buttons in sidebar
            try:
                if hasattr(self, 'execute_flow_btn'):
                    self.execute_flow_btn.setEnabled(True)
                if hasattr(self, 'stop_flow_btn'):
                    self.stop_flow_btn.setEnabled(False)
            except Exception:
                pass
        
        # Ensure window is still visible and active
        self.ensure_window_stability()
    
    def ensure_window_stability(self):
        """Ensure the application window stays stable and responsive after execution"""
        try:
            # Check if window is minimized or hidden
            if self.isMinimized():
                self.showNormal()
                print("✅ Window was minimized, restored to normal state")
            
            # Ensure window is visible
            if not self.isVisible():
                self.show()
                print("✅ Window was hidden, made visible again")
            
            # Bring window to foreground
            self.activateWindow()
            self.raise_()
            
            # Process any pending Qt events to keep UI responsive
            QApplication.processEvents()
            
            print("✅ Window stability check completed")
        except Exception as e:
            print(f"⚠️ Error during window stability check: {e}")
    
    def process_event_loop(self):
        """Process Qt event loop to keep UI responsive during long operations"""
        QApplication.processEvents()
    
    def on_execute_error(self, error_message):
        """Handle errors from execute worker"""
        # Reset button states on error
        self.execute_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)
        
        self.log_display.append(f"[{datetime.now().strftime('%H:%M:%S')}] ❌ Error during code execution: {error_message}")
        print(f"❌ Error during code execution: {error_message}")
        
        # Set droid overlay back to PROCESS PENDING state on error
        if hasattr(self, 'processing_widget') and self.processing_widget:
            self.processing_widget.set_process_pending_state()
            print("❌ Set droid overlay back to PROCESS PENDING state after error")
        
        # Show error message to user
        QMessageBox.critical(self, "❌ Execution Error", f"Code execution failed:\n{error_message}")
        
        # Clean up worker thread safely
        if hasattr(self, 'execute_worker') and self.execute_worker is not None:
            # Schedule safe deletion
            self.execute_worker.finished.connect(self.execute_worker.deleteLater)
            self.execute_worker = None
            
            # Revert Execute Flow and STOP buttons in sidebar
            try:
                if hasattr(self, 'execute_flow_btn'):
                    self.execute_flow_btn.setEnabled(True)
                if hasattr(self, 'stop_flow_btn'):
                    self.stop_flow_btn.setEnabled(False)
            except Exception:
                pass
    
    def on_execute_exception_handler(self, error_message):
        """Handle exceptions from execute worker with special exception processing"""
        # Check if this is a special exception message
        if error_message.startswith("EXCEPTION_OCCURRED:"):
            exception_text = error_message.replace("EXCEPTION_OCCURRED:", "")
            self.handle_code_exception(exception_text)
        elif error_message.startswith("Agent Flow Execution Error:"):
            # Handle ABA Agent specific errors with custom popup
            self.show_aba_agent_error_popup(error_message)
        else:
            # Handle as regular error
            self.on_execute_error(error_message)
    
    def show_aba_agent_error_popup(self, error_message):
        """Show ABA Agent execution error popup with close button"""
        try:
            # Don't reset button states here - wait until popup is closed
            # Reset stop button only
            if hasattr(self, 'stop_btn'):
                self.stop_btn.setEnabled(False)
            
            # Set droid overlay back to PROCESS PENDING state on error
            if hasattr(self, 'processing_widget') and self.processing_widget:
                self.processing_widget.set_process_pending_state()
                print("❌ Set droid overlay back to PROCESS PENDING state after AGENT FLOW error")
            # Revert sidebar buttons on error: enable Execute if code exists, disable STOP
            try:
                if hasattr(self, 'execute_flow_btn'):
                    has_code = bool(self.code_display.toPlainText().strip())
                    self.execute_flow_btn.setEnabled(has_code)
                if hasattr(self, 'stop_flow_btn'):
                    self.stop_flow_btn.setEnabled(False)
            except Exception:
                pass
            # Log the error
            self.log_display.append(f"[{datetime.now().strftime('%H:%M:%S')}] ❌ AGENT FLOW Error: {error_message}")
            print(f"❌ AGENT FLOW Error: {error_message}")
            
            # Create frameless custom error dialog
            dialog = QDialog(self)
            dialog.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
            dialog.setAttribute(Qt.WA_TranslucentBackground)
            dialog.setFixedSize(600, 400)
            dialog.setModal(True)
            
            # Main container widget for frameless design
            container = QWidget(dialog)
            container.setGeometry(0, 0, 600, 400)
            container.setStyleSheet("""
                QWidget {
                    background-color: #2d2d30;
                    color: #ffffff;
                    border: none;
                    border-radius: 15px;
                }
                QLabel {
                    color: #ffffff;
                    background: transparent;
                    border: none;
                }
                QPushButton {
                    background-color: #0078d4;
                    color: white;
                    border: none;
                    padding: 10px 20px;
                    border-radius: 5px;
                    font-weight: bold;
                    font-size: 14px;
                    min-width: 100px;
                }
                QPushButton:hover {
                    background-color: #106ebe;
                }
                QPushButton:pressed {
                    background-color: #005a9e;
                }
                QTextEdit {
                    background-color: #1e1e1e;
                    color: #ffffff;
                    border: none;
                    border-radius: 5px;
                    padding: 10px;
                    font-family: 'Consolas', 'Courier New', monospace;
                    font-size: 12px;
                }
                QScrollBar:vertical {
                    background-color: #3d3d3d;
                    width: 12px;
                    border: none;
                    border-radius: 6px;
                }
                QScrollBar::handle:vertical {
                    background-color: #666666;
                    border-radius: 6px;
                    min-height: 20px;
                }
                QScrollBar::handle:vertical:hover {
                    background-color: #888888;
                }
                QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                    border: none;
                    background: none;
                }
            """)
            
            # Create layout for container
            layout = QVBoxLayout(container)
            layout.setContentsMargins(15, 10, 15, 20)
            layout.setSpacing(10)
            
            # Make dialog draggable
            def mousePressEvent(event):
                if event.button() == Qt.LeftButton:
                    dialog.drag_position = event.globalPos() - dialog.frameGeometry().topLeft()
                    event.accept()
            
            def mouseMoveEvent(event):
                if event.buttons() == Qt.LeftButton and hasattr(dialog, 'drag_position'):
                    dialog.move(event.globalPos() - dialog.drag_position)
                    event.accept()
            
            container.mousePressEvent = mousePressEvent
            container.mouseMoveEvent = mouseMoveEvent
            
            # Add title bar with minimize and close buttons for frameless window
            title_bar = QHBoxLayout()
            title_bar.setContentsMargins(0, 5, 5, 0)
            title_spacer = QWidget()
            title_spacer.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)

            # Minimize button

            # self.minimize_btn = QPushButton()
            # self.minimize_btn.setIcon(QIcon(resource_path("styles/Icon/minimize.png")))
            # self.minimize_btn.setIconSize(QSize(16, 16))
            # self.minimize_btn.setFixedSize(30, 30)
            # self.minimize_btn.setProperty('class', 'WindowControlButton')
            # self.minimize_btn.setToolTip("Minimize")
            # self.minimize_btn.setStyleSheet("""
            # QPushButton {
            #     background: transparent;
            #     border: none;
            # }
            # QPushButton:hover {
            #     background: rgba(255, 255, 255, 30);
            #     border-radius: 4px;
            # }
            # """)
            # self.minimize_btn.clicked.connect(self.showMinimized)  

            # title_bar.addWidget(title_spacer)
            # title_bar.addWidget(self.minimize_btn)
            # layout.addLayout(title_bar)

            
            # Title label - positioned higher
            title_label = QLabel("🤖 Agent Flow Execution Error")
            title_label.setStyleSheet("""
                QLabel {
                    color: #ff4444;
                    font-weight: bold;
                    font-size: 20px;
                    padding: 5px 0 0 0;
                    margin-top: -5px;
                }
            """)
            title_label.setAlignment(Qt.AlignCenter)
            layout.addWidget(title_label)
            
            # Description label
            desc_label = QLabel("An error occurred while executing the Agent Flow. Please review the details below:")
            desc_label.setStyleSheet("""
                QLabel {
                    color: #cccccc;
                    font-size: 14px;
                    padding: 5px 0;
                }
            """)
            desc_label.setWordWrap(True)
            layout.addWidget(desc_label)
            
            # Error message display (scrollable text area)
            error_display = QTextEdit()
            error_display.setPlainText(error_message)
            error_display.setReadOnly(True)
            error_display.setMaximumHeight(200)
            layout.addWidget(error_display)
            
            # Button layout
            button_layout = QHBoxLayout()
            button_layout.addStretch()
            
            # Close button
            close_btn = QPushButton("✕ Close")
            
            def on_close_clicked():
                # Restore Execute Code button to normal blue state
                self.set_execute_button_normal_state()
                dialog.accept()
            
            close_btn.clicked.connect(on_close_clicked)
            close_btn.setStyleSheet("""
                QPushButton {
                    background-color: #dc3545;
                    color: white;
                    border: none;
                    padding: 12px 25px;
                    border-radius: 6px;
                    font-weight: bold;
                    font-size: 14px;
                    min-width: 120px;
                }
                QPushButton:hover {
                    background-color: #c82333;
                }
                QPushButton:pressed {
                    background-color: #bd2130;
                }
            """)
            
            button_layout.addWidget(close_btn)
            layout.addLayout(button_layout)
            
            # Center the dialog on the main window
            if self.parent():
                dialog.move(
                    self.x() + (self.width() - dialog.width()) // 2,
                    self.y() + (self.height() - dialog.height()) // 2
                )
            
            # Connect dialog finished signal to ensure Execute Code button is restored
            def on_dialog_finished():
                # Restore Execute Code button to normal blue state when dialog closes
                self.set_execute_button_normal_state()
            
            dialog.finished.connect(on_dialog_finished)
            
            # Show the dialog
            dialog.exec_()
            
            # Clean up worker thread safely after dialog closes
            if hasattr(self, 'execute_worker') and self.execute_worker is not None:
                try:
                    self.execute_worker.finished.connect(self.execute_worker.deleteLater)
                    self.execute_worker = None
                except:
                    pass
            
        except Exception as e:
            print(f"❌ Error showing AGENT FLOW error popup: {e}")
            # Fallback to standard message box
            QMessageBox.critical(self, "Agent Flow Error", f"Agent Flow execution failed:\n\n{error_message}")
    
    def handle_code_exception(self, exception_text):
        """Handle code exceptions with friendly error display and chat integration"""
        try:
            # Import exception handling module
            from exception_handling import friendly_error_msg
            
            # Get friendly error message
            display_msg = friendly_error_msg(exception_text)
            
            # Show frameless popup with the exception (includes Yes/No buttons)
            self.show_exception_popup(display_msg, exception_text)
            
        except Exception as e:
            print(f"❌ Error handling exception: {e}")
            # Fallback to regular error handling
            self.on_execute_error(f"Exception occurred: {exception_text}")
    
    def show_exception_popup(self, display_msg, exception_text):
        """Show frameless popup with exception message"""
        try:
            # Create frameless popup dialog
            popup = QDialog(self)
            popup.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
            popup.setAttribute(Qt.WA_TranslucentBackground)
            popup.setFixedSize(500, 200)
            
            # Main container with rounded corners
            container = QWidget(popup)
            container.setGeometry(0, 0, 500, 200)
            container.setStyleSheet("""
                QWidget {
                    background-color: #2d2d2d;
                    border: 2px solid #ff4444;
                    border-radius: 15px;
                }
            """)
            
            layout = QVBoxLayout(container)
            layout.setContentsMargins(20, 15, 20, 15)
            
            # Title bar with minimize and close buttons
            title_bar = QHBoxLayout()
            title_label = QLabel("⚠️ Exception Occurred")
            title_label.setStyleSheet("""
                QLabel {
                    color: #ff4444;
                    font-weight: bold;
                    font-size: 16px;
                    background: transparent;
                    border: none;
                }
            """)
            
            # Minimize button
            minimize_btn = QPushButton("−")
            minimize_btn.setFixedSize(30, 30)
            minimize_btn.setStyleSheet("""
                QPushButton {
                    background-color: #ffaa00;
                    color: white;
                    border: none;
                    border-radius: 15px;
                    font-weight: bold;
                    font-size: 16px;
                }
                QPushButton:hover {
                    background-color: #ff8800;
                }
            """)
            minimize_btn.clicked.connect(popup.showMinimized)
            
            # Close button
            close_btn = QPushButton("×")
            close_btn.setFixedSize(30, 30)
            close_btn.setStyleSheet("""
                QPushButton {
                    background-color: #ff4444;
                    color: white;
                    border: none;
                    border-radius: 15px;
                    font-weight: bold;
                    font-size: 16px;
                }
                QPushButton:hover {
                    background-color: #ff2222;
                }
            """)
            close_btn.clicked.connect(popup.close)
            
            title_bar.addWidget(title_label)
            title_bar.addStretch()
            # title_bar.addWidget(minimize_btn)
            title_bar.addWidget(close_btn)
            layout.addLayout(title_bar)
            
            # Exception message
            msg_label = QLabel(f"This exception occurred:\n\n{display_msg}")
            msg_label.setStyleSheet("""
                QLabel {
                    color: #ffffff;
                    font-size: 14px;
                    background: transparent;
                    border: none;
                    padding: 10px;
                }
            """)
            msg_label.setWordWrap(True)
            msg_label.setAlignment(Qt.AlignCenter)
            layout.addWidget(msg_label)
            
            # Add Yes/No buttons
            button_layout = QHBoxLayout()
            
            # Yes button
            yes_btn = QPushButton("✨ Fix it")
            yes_btn.setFixedSize(140, 35)
            yes_btn.setStyleSheet("""
                QPushButton {
                    background-color: #4CAF50;
                    color: white;
                    border: none;
                    border-radius: 17px;
                    font-weight: bold;
                    font-size: 12px;
                }
                QPushButton:hover {
                    background-color: #45a049;
                }
            """)
            
            # No button
            no_btn = QPushButton("Close")
            no_btn.setFixedSize(120, 35)
            no_btn.setStyleSheet("""
                QPushButton {
                    background-color: #f44336;
                    color: white;
                    border: none;
                    border-radius: 17px;
                    font-weight: bold;
                    font-size: 12px;
                }
                QPushButton:hover {
                    background-color: #da190b;
                }
            """)
            
            # Store the result
            popup.result = None
            
            def on_yes_clicked():
                popup.result = "yes"
                popup.close()
            
            def on_no_clicked():
                popup.result = "no"
                popup.close()
            
            yes_btn.clicked.connect(on_yes_clicked)
            no_btn.clicked.connect(on_no_clicked)
            
            button_layout.addWidget(no_btn)
            layout.addLayout(button_layout)
            
            # Resize popup to accommodate buttons
            popup.setFixedSize(500, 250)
            container.setGeometry(0, 0, 500, 250)
            
            # Center the popup on screen
            popup.move(
                self.x() + (self.width() - popup.width()) // 2,
                self.y() + (self.height() - popup.height()) // 2
            )
            
            # Show popup and get result
            popup.exec_()
            
            # Handle the result
            if popup.result == "yes":
                self.send_exception_to_chat_direct(exception_text)
                print("✅ User chose to send exception to chat")
            elif popup.result == "no":
                print("❌ User chose not to send exception to chat")
            
        except Exception as e:
            print(f"❌ Error showing exception popup: {e}")
    
    def show_element_confirmation_popup(self, xpath, driver):
        """Show element confirmation popup in main thread"""
        try:
            from datas.source_files.element_confirmation import ElementConfirmationDialog
            
            # Create dialog without parent to make it truly standalone
            dialog = ElementConfirmationDialog(xpath, driver, parent=None)
            result = dialog.exec_()
            
            # Send response back to worker thread
            if hasattr(self, 'execute_worker') and self.execute_worker:
                self.execute_worker.element_confirmation_response.emit(dialog.result)
                
        except Exception as e:
            print(f"❌ Error showing element confirmation popup: {e}")
            # Send False response on error
            if hasattr(self, 'execute_worker') and self.execute_worker:
                self.execute_worker.element_confirmation_response.emit(False)
    
    def show_xpath_modification_popup(self, driver):
        """Show xpath modification popup in main thread"""
        try:
            from datas.source_files.verify_xpath import XPathModifyDialog
            
            # Create dialog without parent to make it truly standalone
            dialog = XPathModifyDialog(driver, parent=None)
            result = dialog.exec_()
            
            # Send response back to worker thread
            if hasattr(self, 'execute_worker') and self.execute_worker:
                if result == QDialog.Accepted and dialog.result:
                    xpath = dialog.xpath_display.toPlainText().strip()
                    self.execute_worker.xpath_modification_response.emit(xpath)
                else:
                    self.execute_worker.xpath_modification_response.emit("")
                    
        except Exception as e:
            print(f"❌ Error showing xpath modification popup: {e}")
            # Send empty response on error
            if hasattr(self, 'execute_worker') and self.execute_worker:
                self.execute_worker.xpath_modification_response.emit("")
        
    # def send_exception_to_chat(self, exception_text):  # REMOVED - chat panel functionality disabled
    #     """Send exception message to code chat automatically"""
    #     # Method removed as part of drag controls cleanup
    
    def send_exception_to_chat_direct(self, exception_text):
        """Send exception message directly to Code Chat without confirmation"""
        try:
            # html_file_path = os.path.join(os.getcwd(), "page_html", "html_file_content.html")
            
            # if os.path.exists(html_file_path):
            #     with open(html_file_path, "r", encoding="utf-8") as f:
            #         html_content = f.read()
            # else:
            #     html_content = ""
            #     print("⚠️ HTML file not found at", html_file_path)
                
            # Check if Code Chat components exist
            if hasattr(self, 'chat_input') and hasattr(self, 'send_chat_btn'):
                # Prepare the message
                # if html_content.strip():
                #     message = (
                #         f"Here is the html content of the current active page use this page to resolve this issue\n\n HTML Content : {html_content} \n\n which caused this Exception : {exception_text} \n\n Analyze with Current Code and use the html content  to resolve this issue and fix the error"
                #     )
                # else:
                #     message = f"I got this error:\n{exception_text}\nNeed to fix that."
                message = f"I got this error:\n{exception_text}\nNeed to fix that."
                
                # Switch to Code tab to show the chat
                if hasattr(self, 'content_area'):
                    # Find the Code tab index
                    for i in range(self.content_area.count()):
                        if self.content_area.tabText(i) == "Code":
                            self.content_area.setCurrentIndex(i)
                            print("📱 Switched to Code tab for exception handling")
                            break
                
                # Set the message in Code Chat input
                self.chat_input.setPlainText(message)
                print("✅ Exception + HTML content set in Code Chat input")
                
                # Automatically click the send button
                self.send_chat_btn.click()
                print("✅ Exception message sent to Code Chat automatically")
                
            else:
                print("❌ Code Chat components not found")
                print(f"❌ chat_input exists: {hasattr(self, 'chat_input')}")
                print(f"❌ send_chat_btn exists: {hasattr(self, 'send_chat_btn')}")
                
        except Exception as e:
            print(f"❌ Error sending exception to Code Chat directly: {e}")
    
    def generate_skeleton_code(self):
        """Generate skeleton code using code_skeleton.gemini_response()"""
        try:
            self.log_message("🔄 Starting skeleton code generation...")
            self.start_btn.setEnabled(False)
            self.start_btn.setText("🔄 Generating...")
            
            # Get manual input text - combine all tasks into one string
            manual_typed_data = "\n".join(self.req_class) if self.req_class else ""
            
            if not manual_typed_data.strip():
                QMessageBox.warning(self, "⚠️ Warning", "No task data available for skeleton generation!")
                return
            
            # Import and call code_skeleton.gemini_response()
            import code_skeleton
            import os
            
            self.log_message("🤖 Calling DroidStudio for skeleton code generation...")
            
            # Call gemini_response with combined task data

            proj_id=self.selected_project_id
            task_id=self.selected_task_id
            proj_name=f"proj_{proj_id}"
            task_name=f"task_{task_id}"
            proj_fol=str(proj_name)
            if os.path.exists(proj_fol):
                os.remove(proj_fol)
            task_fol=f"{proj_name}/{task_name}"
            if os.path.exists(task_fol):
                os.remove(task_fol)
            if not os.path.exists(proj_fol):
                os.makedirs(proj_fol)
            if not os.path.exists(task_fol):
                os.makedirs(task_fol)
            proj_init_path=f"{proj_fol}/__init__.py"
            task_init_path=f"{proj_fol}/{task_fol}/__init__.py"
            if not os.path.exists(proj_init_path):
                open(proj_init_path, "w").close()
            if not os.path.exists(task_init_path):
                open(task_init_path, "w").close()
            
            code, json_xpath = code_skeleton.gemini_response(manual_typed_data,proj_name,task_name,self.userid)
            requirements = code_skeleton.analyze_dependencies(code)

            # Write code to working directory for .exe compatibility
            os.makedirs("code_py", exist_ok=True)
            with open("code_py/execute_code.py", "w", encoding="utf-8") as f:
                f.write(code)

            with open("code_py/requirements.txt", "w", encoding="utf-8") as f:
                f.write(requirements)

            # Ensure json_info directory exists
            os.makedirs("json_info", exist_ok=True)
            
            # Write json_xpath to json_info/json_xpath.json
            import json
            if isinstance(json_xpath, dict):
                with open("json_info/json_xpath.json", "w", encoding="utf-8") as f:
                    json.dump(json_xpath, f, indent=4)
            
            self.log_message("✅ Skeleton   code generated successfully!")
            self.log_message(f"📄 Requirements written to: code_py/requirements.txt as {requirements}")
            self.log_message(f"📄 Code written to: code_py/execute_code.py")
            self.log_message(f"📄 XPath JSON written to: json_info/json_xpath.json")
            
            # Update Code tab with skeleton code
            self.update_code_display_with_skeleton(code)

            try:
                # After code generation and json creation
                import flowchart_widget
                flowchart_widget.SAMPLE_CODE = code  # 🔥 Update the global variable in flowchart_widget.py

                # If your flowchart widget instance is available
                if hasattr(self, 'flowchart_widget'):
                    self.flowchart_widget.code_input.setPlainText(code)
                    self.flowchart_widget.generate_flowchart()

                self.log_message("🧩 Flowchart updated with generated skeleton code.")

            except Exception as e:
                self.log_message(f"⚠️ Could not update SAMPLE_CODE: {str(e)}")
            
            # Call task refreshing to update tasks based on generated code
            self.refresh_tasks_from_code()
            
            # Refresh the XPath tab if it exists
            if hasattr(self, 'xpath_tab_widget'):
                self.refresh_xpath_tab()
            
            # Update processing widget to completed state
            if hasattr(self, 'processing_widget'):
                self.processing_widget.set_off_state()
            
            # Start background completion processing to prevent UI freezing
            self.start_preprocess_completion()
            
        except Exception as e:
            self.log_message(f"❌ Error generating skeleton code: {str(e)}")
            QMessageBox.critical(self, "❌ Error", f"Failed to generate skeleton code:\n{str(e)}")
            if hasattr(self, 'processing_widget'):
                self.processing_widget.set_off_state()
            self.update_tasks_status("Skeleton generation failed", "#F44336")
        finally:
            self.start_btn.setEnabled(True)
            self.start_btn.setText("⚙️ Generate Code")
    
    def start_processing_with_apps(self):
        """Start processing with application selections"""
        # Variable manager removed - no longer needed
        
        self.start_btn.setEnabled(False)
        # self.progress_bar.setVisible(True)
        # self.progress_bar.setRange(0, 0)
        # Status message removed - no status bar in frameless window
        
        if self.debug_state.breakpoints:
            self.log_message(f"🔴 Debug mode enabled with {len(self.debug_state.breakpoints)} breakpoints")
            self.terminal_display.append(f"[DEBUG] Starting execution with breakpoints at tasks: {sorted(self.debug_state.breakpoints)}")
        
        
        
        

        initial_input = self.requirement_input.toPlainText().strip()
        verify_mode_enabled = False
        self.task_processor = task_processor.TaskProcessor(self.req_class, initial_input, self.debug_state, self.debug_signals, verify_mode_enabled, task_events=self.task_events, full_task_info=self.full_task_info,gemini_service=self.gemini_service,conditional_info=self.conditional_info)
        
        # Variable manager removed - no longer needed
        
        # Connect code_log_updated signal to update Code tab in real-time (deprecated)
        self.task_processor.code_log_updated.connect(self.update_code_display)
        print("🔧 TaskProcessor connections established")
        
        print(f"🚀 NEW TASKPROCESSOR: should_stop = {self.task_processor.should_stop}")
        print(f"🚀 NEW TASKPROCESSOR: thread ID = {self.task_processor.currentThreadId()}")
        self.task_processor.should_stop=False
        self.task_processor.task_started.connect(self.on_task_started)
        # self.task_processor.verification_requested.connect(self.show_detail_mode_dialog)
        self.task_processor.task_completed.connect(self.on_task_completed)
        self.task_processor.exception_occurred.connect(self.on_exception_occurred)
        self.task_processor.task_extended.connect(self.on_task_extension_needed)
        self.task_processor.processing_finished.connect(self.on_processing_finished)
        self.task_processor.task_status_changed.connect(self.on_task_status_changed)
        self.task_processor.breakpoint_hit_signal.connect(self.on_breakpoint_hit_inline)
        self.task_processor.task_transition_signal.connect(self.on_task_transition)
        self.task_processor.tasks_restructured.connect(self.on_tasks_restructured)
        self.task_processor.verification_requested.connect(self.on_verification_requested)
        self.task_processor.exception_dialog_requested.connect(self.on_exception_dialog_requested)
        # self.task_processor.instruction_dialog_requested.connect(instruction_mode_widget.on_instruction_dialog_requested)
        self.task_processor.detail_mode_requested.connect(self.show_detail_mode_dialog)
        self.task_processor.element_confirmation_requested.connect(self.on_element_confirmation_requested)
        
        # Store reference to task processor for driver access
        self.task_processor.driver_updated.connect(self.on_driver_updated)
        
        self.task_processor.start()
    #Stop processing

    def stop_overall_processing(self):
        print(f"In stop process")
        if self.task_processor:
            print(f"Stopping task processor...")
            self.task_stop = True
            self.task_processor.quit()
        self.start_btn.setEnabled(True)
        # self.progress_bar.setVisible(False)
        # Status message removed - no status bar in frameless window

    # Debug event handlers
    def on_debug_started(self, code_lines):
        self.terminal_display.append(f"[DEBUG]  Starting debug execution of {len(code_lines)} lines")
        self.terminal_display.display_code_with_line_numbers(code_lines)
        self.debug_status_label.setText("Debug Status: ⏸️ Waiting for user input")
        self.terminal_display.enable_debug_controls()

    def on_line_executing(self, line_idx, line_code):
        """Handle line execution with visual feedback"""
        self.terminal_display.display_code_with_highlighting(
            '\n'.join(self.terminal_display.current_code_lines), 
            line_idx
        )
        self.debug_status_label.setText(f"Debug Status: Executing line {line_idx + 1}")

    def on_line_executed(self, line_idx, line_code):
        """Handle line execution completion"""
        self.debug_status_label.setText(f"Debug Status: Completed line {line_idx + 1}")

    def on_task_debug_completed(self):
        """Handle individual task debug completion - FIXED"""
        self.terminal_display.append("[TASK COMPLETE] ✅ Debug task completed - continuing to next task")
        self.terminal_display.clear_highlights()
        self.debug_status_label.setText("Debug Status: Task completed - continuing...")
        # ✅ CRITICAL: Keep debug controls enabled for future breakpoint tasks
        # Do NOT disable debug controls here

    def on_debug_completed(self):
        """Handle complete debug session completion - ONLY called when ALL tasks done"""
        self.terminal_display.append("[SESSION COMPLETE] ✅ All debug execution completed")
        self.terminal_display.clear_highlights()
        self.debug_status_label.setText("Debug Status: ✅ Session Completed")
        # ✅ NOW disable debug controls since entire session is done
        self.terminal_display.disable_debug_controls()
    
    
    def on_step_paused(self, line_num, line_code):
        self.terminal_display.append(f"[STEP] ⏸️ Paused after line {line_num + 1}")
        self.debug_status_label.setText(f"Debug Status: ⏸️ Step paused (line {line_num + 1})")
    
    def on_execution_error(self, line_num, line_code, error):
        self.terminal_display.append(f"[ERROR] ❌ Line {line_num + 1}: {error}")
        self.debug_status_label.setText(f"Debug Status: ❌ Error at line {line_num + 1}")
        self.log_message(f"❌ Execution error at line {line_num + 1}: {error}")
    
    def on_debug_stopped(self):
        self.terminal_display.append("[STOP] ⏹️ Execution stopped by user")
        self.terminal_display.clear_highlights()
        self.debug_status_label.setText("Debug Status: ⏹️ Stopped")
        self.terminal_display.disable_debug_controls()
    
    
    def on_task_started(self, message):
        self.log_message(f"🔃 Started: {message}")
        
        # Update status to show current task processing
        if "Task" in message and ":" in message:
            task_info = message.split(":")
            if len(task_info) > 1:
                task_desc = task_info[1].strip()
                self.update_tasks_status(f"Processing: {task_desc}", "#FF9800")
    
    def on_task_completed(self, message, code):
        self.log_message(message)
        
        # Update flowchart with individual task code if available
        if hasattr(self, 'flowchart_widget') and code and len(str(code).strip()) > 10:
            try:
                self.flowchart_widget.update_flowchart(str(code))
            except Exception as e:
                print(f"Error updating flowchart with task code: {e}")
        self.log_message(f"✅ Completed: {message}")
        self.code_display.append(f"--- Task Code ---\n{code}\n")
    
    def on_task_status_changed(self, task_index, status):
        """Handle task status changes and update UI colors"""
        if hasattr(self, 'task_list'):
            self.task_list.update_task_status(task_index, status)
            print(f"🎨 UI: Updated step {task_index} status to {status}")
            
            # Update status label based on task status
            if status == 'processing':
                self.update_tasks_status(f"Step {task_index + 1} processing...", "#FF9800")
            elif status == 'completed':
                self.update_tasks_status(f"Step {task_index + 1} completed", "#4CAF50")
            elif status == 'exception':
                self.update_tasks_status(f"Step {task_index + 1} failed", "#F44336")
    
    def on_breakpoint_hit_inline(self, task_index):
        """Handle breakpoint hit - show inline continue button"""
        if hasattr(self, 'task_list'):
            self.task_list.show_continue_button(task_index)
            print(f"🎮 BREAKPOINT HIT: Showing inline continue button for step {task_index}")
    
    def on_task_transition(self, task_index):
        """Handle task transition - hide all continue buttons"""
        if hasattr(self, 'task_list'):
            self.task_list.hide_all_continue_buttons()
            print(f"🎮 TASK TRANSITION: Hiding all continue buttons after step {task_index}")
    
    def on_exception_occurred(self, task_num, modified_tasks, initial_input, status):
        self.log_message(f"⚠️ Exception in step {task_num}: {status}")
        self.req_class = modified_tasks
        self.update_task_list()
    
   
    #     """Helper to unblock task processor thread safely"""
    #     try:
    #         self.task_processor.instruction_pending = False
    #         self.task_processor.instruction_mutex.lock()
    #         self.task_processor.instruction_condition.wakeAll()
    #         self.task_processor.instruction_mutex.unlock()
    #     except Exception as e:
    #         print(f"❌ Error unblocking task processor: {str(e)}")
    #         print(f"❌ Error in instruction dialog: {str(e)}")
    #         # Ensure thread is unblocked even if there's an error
    #         self.task_processor.instruction_pending = False
    #         self.task_processor.instruction_mutex.lock()
    #         self.task_processor.instruction_condition.wakeAll()
    #         self.task_processor.instruction_mutex.unlock()
    
    def on_task_extension_needed(self, current_tasks):
        self.log_message("🔄 Task extension needed...")
        
        additional_req, ok = self.get_additional_requirements()
        
        if ok and additional_req.strip():
            try:
                import task_extender
                old_task_count = len(self.req_class)  # Store original task count
                extended_tasks,self.task_events,self.full_task_info = task_extender.task_extender(self.full_task_info,additional_req)
                self.req_class = extended_tasks
                
                # Check for new Desktop tasks in the extended list
                new_desktop_tasks = []
                for i in range(old_task_count, len(extended_tasks)):
                    if i < len(self.task_events) and self.task_events[i] == "Event :Desktop":
                        new_desktop_tasks.append(i)
                        print(f"🔵 NEW DESKTOP TASK: Task {i} is Desktop - {extended_tasks[i]}")
                
                # Update the task list UI
                self.update_task_list()
                
                # Auto-select radio buttons for all Desktop tasks (including new ones)
                if hasattr(self, 'task_events') and self.task_events:
                    print(f"🔵 UI: Auto-selecting Desktop tasks from {len(self.task_events)} step events after extension")
                    self.task_list.auto_select_desktop_tasks(self.task_events)
                
                # If there are new Desktop tasks, skip dialog and use auto-detection
                if new_desktop_tasks:
                    print(f"🔵 NEW DESKTOP TASKS DETECTED: {new_desktop_tasks}")
                    print(f"🔵 SKIPPING APPLICATION SELECTION DIALOG - Using auto-detection")
                    self.log_message(f"🔵 Detected {len(new_desktop_tasks)} new Desktop tasks. Using automatic app detection.")
                    
                    # Skip dialog - applications will be auto-detected during task processing
                    # Add new Desktop tasks to radio selections
                    self.debug_state.radio_selections.update(new_desktop_tasks)
                    self.task_list.radio_selections.update(new_desktop_tasks)
                    
                    print(f"🔵 NEW DESKTOP TASKS ADDED TO RADIO SELECTIONS: {new_desktop_tasks}")
                    self.log_message(f"✅ {len(new_desktop_tasks)} new Desktop tasks will use automatic app detection")
                    
                    # Update UI to reflect radio selections for new Desktop tasks
                    for task_idx in new_desktop_tasks:
                        if task_idx in self.task_list.task_widgets:
                            widget_refs = self.task_list.task_widgets[task_idx]
                            radio_btn = widget_refs.get('radio_btn')
                            label = widget_refs['label']
                            
                            if radio_btn:
                                radio_btn.setChecked(True)
                                radio_btn.setProperty('class', 'SelectedRadioButton')
                                style_loader.apply_stylesheet(radio_btn)
                                
                                label.setProperty('class', 'SelectedLabel')
                                style_loader.apply_stylesheet(label)
                
                self.log_message(f"✅ Tasks extended. New total: {len(extended_tasks)}")
                
                if self.task_processor:
                    self.task_processor.continue_processing(extended_tasks,self.task_events,self.full_task_info)
                    
            except Exception as e:
                self.log_message(f"❌ Error extending tasks: {str(e)}")
        else:
            if self.task_processor:
                self.task_processor.continue_processing(current_tasks,self.task_events,self.full_task_info)
    
    # def extend_tasks_with_input(self, current_tasks, additional_input):
    #     """Modified version of task_extender that uses our input instead of console input"""
    #     import google.generativeai as genai
    #     import config
    #     import ast
        
    #     genai.configure(api_key=config.API_KEY)
    #     model = genai.GenerativeModel(model_name="gemini-2.5-flash-lite")
    #     chat = model.start_chat()
        
    #     prompt = f"""
    #     The following is a list of tasks generated based on the user's original requirements: {current_tasks}.
    #     Here is the user's latest input: {additional_input}.
    #     If the user intends to add additional tasks, please extend the existing list accordingly. If no changes are required, simply return the current task list as a valid Python list. Do not include any explanation, formatting, or extra text—return only the list.
    #     """
        
    #     response = chat.send_message(prompt)
    #     res_txt = response.text
        
    #     res_txt = res_txt.strip("`").strip("``").strip("```")
    #     res_txt = res_txt.replace("json", "").replace("python", "").strip()
        
    #     try:
    #         if res_txt.startswith("[") and res_txt.endswith("]"):
    #             return ast.literal_eval(res_txt)
    #         else:
    #             return ast.literal_eval(res_txt)
    #     except:
    #         return current_tasks
    
    def get_additional_requirements(self):
        
        """
        Simpler approach using QWidget with specific window attributes
        """
        from PyQt5.QtCore import QEventLoop
        
        dialog = QWidget()
        dialog.setWindowTitle("➕ Additional Requirements")
        
        # The key attributes for independence
        dialog.setAttribute(Qt.WA_DeleteOnClose)
        dialog.setAttribute(Qt.WA_QuitOnClose, False)  # Don't quit main app when this closes
        
        dialog.setWindowFlags(
            Qt.Window |
            Qt.WindowStaysOnTopHint | 
            Qt.WindowCloseButtonHint |
            Qt.WindowMinimizeButtonHint |
            Qt.WindowMaximizeButtonHint |
            Qt.WindowTitleHint |
            Qt.WindowSystemMenuHint
        )
        
        # Remove any parent relationship
        dialog.setParent(None)
        
        dialog.setFixedSize(500, 300)
        dialog.setStyleSheet("""
            QWidget {
                background-color: #2d2d30;
                color: #ffffff;
                border: 2px solid #555555;
                border-radius: 10px;
            }
            QLabel {
                color: #ffffff;
                font-weight: bold;
                font-size: 14px;
                padding: 15px;
                background-color: transparent;
            }
            QTextEdit {
                background-color: #1e1e1e;
                color: #ffffff;
                border: 2px solid #0078d4;
                border-radius: 8px;
                padding: 15px;
                font-family: 'Segoe UI', Arial, sans-serif;
                font-size: 14px;
                line-height: 1.5;
                selection-background-color: #264f78;
            }
            QTextEdit:focus {
                border: 2px solid #4ecdc4;
                box-shadow: 0 0 5px rgba(78, 205, 196, 0.3);
            }
            QPushButton {
                background-color: #0078d4;
                color: white;
                border: none;
                padding: 12px 25px;
                border-radius: 8px;
                font-weight: bold;
                font-size: 14px;
                min-width: 100px;
            }
            QPushButton:hover {
                background-color: #106ebe;
            }
            QPushButton:pressed {
                background-color: #0a5a94;
            }
            QPushButton#cancelBtn {
                background-color: #6c757d;
            }
            QPushButton#cancelBtn:hover {
                background-color: #5a6268;
            }
        """)
        
        layout = QVBoxLayout(dialog)
        layout.setSpacing(15)
        
        # Title label
        title_label = QLabel(" Enter additional requirements:")
        title_label.setProperty('class', 'TitleLabel')
        style_loader.apply_stylesheet(title_label)
        
        layout.addWidget(title_label)
        
        # Subtitle label
        subtitle_label = QLabel("(Leave empty to continue with current tasks)")
        subtitle_label.setStyleSheet("""
            QLabel {
                color: #888888;
                font-weight: normal;
                font-size: 12px;
                padding: 5px 10px;
                background-color: transparent;
            }
        """)
        layout.addWidget(subtitle_label)
        
        # Text input area
        text_input = QTextEdit()
        text_input.setPlaceholderText("Type your additional requirements here...")
        text_input.setMinimumHeight(150)
        layout.addWidget(text_input)
        
        # Button layout
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        # Variables to store results
        result_text = ""
        dialog_accepted = False
        
        def on_ok():
            nonlocal result_text, dialog_accepted
            result_text = text_input.toPlainText().strip()
            dialog_accepted = True
            dialog.close()
        
        def on_cancel():
            nonlocal dialog_accepted
            dialog_accepted = False
            dialog.close()
        
        cancel_btn = QPushButton("Cancel")
        cancel_btn.setObjectName("cancelBtn")
        cancel_btn.clicked.connect(on_cancel)
        
        ok_btn = QPushButton("OK")
        ok_btn.clicked.connect(on_ok)
        
        button_layout.addWidget(cancel_btn)
        button_layout.addWidget(ok_btn)
        layout.addLayout(button_layout)
        
        # Set focus to text input
        text_input.setFocus()
        
        # Show the dialog
        dialog.show()
        dialog.raise_()
        dialog.activateWindow()
        
        # Use a custom event loop to wait for user interaction
        loop = QEventLoop()
        dialog.destroyed.connect(loop.quit)
        
        # Keep reference to prevent garbage collection
        self._simple_dialog_ref = dialog
        
        # Wait for dialog to close
        loop.exec_()
        
        # Clean up reference
        self._simple_dialog_ref = None
        
        return result_text, dialog_accepted
    
    def on_processing_finished(self, code_log):
        # self.progress_bar.setVisible(False)
        self.log_message("🎉 Processing completed successfully!")
        self.update_tasks_status("All tasks completed! 🎉", "#4CAF50")
        self.generate_code_btn.setEnabled(True)
        self.start_btn.setEnabled(True)
        self.final_code_log = code_log
        # Enable save button after processing completion
        if hasattr(self, 'save_action_btn'):
            self.save_action_btn.setEnabled(True)
        # Set to OFF state when all task processing completes
        if hasattr(self, 'processing_widget'):
            self.processing_widget.set_off_state()
        # Status message removed - no status bar in frameless window
        # Enable save button after processing completion
        if hasattr(self, 'save_code_btn'):
            self.save_code_btn.setEnabled(True)
        # Update flowchart with the generated code log
        if hasattr(self, 'flowchart_widget') and code_log:
            try:
                self.flowchart_widget.update_flowchart(code_log)
                self.log_message("📊 Flowchart updated with generated code")
            except Exception as e:
                print(f"Error updating flowchart: {e}")
    
    
    def generate_final_code(self):
        # if not hasattr(self, 'final_code_log'):
        #     QMessageBox.warning(self, "⚠️ Warning", "No code to generate. Please process tasks first!")
        #     return
        if not os.path.exists("code_py/execute_code.py") and not os.path.exists("json_info/json_xpath.json"):
            print(f"\n✗ Error: Input file not found: code_py/execute_code.py")
            print("Please check the file path and try again.")  
            QMessageBox.critical(self, "❌ Final Code Error", f"Final Code Generation failed:\n Please check if initial the code is generated")         
            return
        try:
            execute_code_empty = os.path.getsize("code_py/execute_code.py") == 0
            json_xpath_empty = os.path.getsize("json_info/json_xpath.json") == 0
            
            if execute_code_empty or json_xpath_empty:
                empty_files = []
                if execute_code_empty:
                    empty_files.append("code_py/execute_code.py")
                if json_xpath_empty:
                    empty_files.append("json_info/json_xpath.json")
                
                print(f"\n✗ Error: The following file(s) are empty: {', '.join(empty_files)}")
                print("Please ensure the files contain valid content.")
                QMessageBox.critical(self, "❌ Final Code Error", f"Final Code Generation failed:\n Please check if initial the code is generated")
                return
        except OSError as e:
            print(f"\n✗ Error: Unable to read file size: {e}")
            QMessageBox.critical(self, "❌ Final Code Error", f"Final Code Generation failed:\n Please check if initial the code is generated")
            return
            
        try:
            with open("code_py/execute_code.py", "r", encoding="utf-8") as f:
                self.final_code_log = f.read()
            with open("json_info/json_xpath.json", "r", encoding="utf-8") as f:
                import json
                self.xpath_json = json.load(f)
                
            from gen_final_code import gen_code
            result = gen_code(self.final_code_log, self.req_class,self.xpath_json)
            
            flowchart_widget.SAMPLE_CODE=result
            
            resolutions = get_windows_display_complete()
            res_comment="#No Resolution Detected"
            physical_res=0
            scaling=0

            if resolutions and isinstance(resolutions,dict):
                physical_res = resolutions['physical']
                scaling = resolutions['scaling']
                res_comment = f"# Resolution Detected\n"
                res_comment += f"# Physical Resolution: {physical_res}\n"
                res_comment += f"# Scaling: {scaling}\n"

            resolution_check_code = """
def get_windows_display_complete(resolution_to_check, scaling_to_check):
    import tkinter as tk
    from tkinter import messagebox
    from ctypes import wintypes
    import sys
    import ctypes

    def show_popup(title, message):
        root = tk.Tk()
        root.withdraw()  # Hide the main window
        messagebox.showinfo(title, message)
        root.destroy()

    user32 = ctypes.windll.user32
    shcore = ctypes.windll.shcore

    # Set DPI awareness
    shcore.SetProcessDpiAwareness(2)

    # Primary monitor info
    hmonitor = user32.MonitorFromPoint(wintypes.POINT(0, 0), 1)

    # Get physical dimensions
    physical_width = user32.GetSystemMetrics(0)
    physical_height = user32.GetSystemMetrics(1)

    # Get DPI for primary monitor
    dpi_x = wintypes.UINT()
    dpi_y = wintypes.UINT()
    shcore.GetDpiForMonitor(hmonitor, 0, ctypes.byref(dpi_x), ctypes.byref(dpi_y))

    # Calculate scaling
    scaling = dpi_x.value / 96.0
    physical_res = (physical_width, physical_height)
    formatted_scaling = f"{scaling*100:.0f}%"

    print(f"Physical Resolution: {physical_width} x {physical_height}")
    print(f"Scaling: {formatted_scaling}")

    # Check and stop script if mismatch
    if resolution_to_check != physical_res and scaling_to_check != formatted_scaling:
        show_popup("Resolution and Scaling Check", "False - Resolution and Scaling do not match")
        sys.exit()
    elif resolution_to_check != physical_res:
        show_popup("Resolution and Scaling Check", "False - Resolution does not match")
        sys.exit()
    elif scaling_to_check != formatted_scaling:
        show_popup("Resolution and Scaling Check", "False - Scaling does not match")
        sys.exit()
    else:
        show_popup("Resolution and Scaling Check", "True - Resolution and Scaling matched")
                """
            calling_resolution_check = f"get_windows_display_complete({physical_res}, f'{scaling}')"

            clean_code = result.strip("`").replace("python", "", 1).strip()
            
            clean_code = res_comment + resolution_check_code + "\n"+ calling_resolution_check + "\n\n" + clean_code
            
            # Create custom file dialog with improved UI
            dialog = QFileDialog(self)
            dialog.setWindowTitle("Save Python Code")
            dialog.setAcceptMode(QFileDialog.AcceptSave)
            dialog.setNameFilter("Python Files (*.py);;All Files (*)")
            dialog.setDefaultSuffix("py")
            
            # Set initial directory and filename
            initial_dir = os.path.expanduser("~")
            dialog.setDirectory(initial_dir)
            dialog.selectFile("automation_code.py")
            
            # Configure dialog appearance
            dialog.setOption(QFileDialog.DontUseNativeDialog, True)
            dialog.setStyleSheet("""
                QFileDialog {
                    background-color: white;
                }
                QWidget {
                    background-color: white;
                    color: black;
                }
                QTreeView {
                    background-color: white;
                    color: black;
                }
                QLineEdit {
                    background-color: white;
                    color: black;
                    border: 1px solid #ccc;
                    padding: 5px;
                }
            """)
            
            # Add quick access shortcuts for common folders
            urls = []
            paths = [
                os.path.expanduser("~/Desktop"),
                os.path.expanduser("~/Downloads"),
                os.path.expanduser("~/Documents"),
                os.path.expanduser("~")  # Home directory
            ]
            
            # Create QUrls for each existing path
            for path in paths:
                if os.path.exists(path):
                    urls.append(QUrl.fromLocalFile(path))
            
            # if urls:
            dialog.setSidebarUrls(urls)
            
            if dialog.exec_() == QDialog.Accepted:
                file_path = dialog.selectedFiles()[0]
                
                # Ensure .py extension
                if not file_path.lower().endswith('.py'):
                    file_path += '.py'
                
                # Save the code
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(clean_code)
                    
                print(f"✅ Code saved successfully to: {file_path}")
                QMessageBox.information(
                    self,
                    "Success",
                    f"Code saved successfully!\nLocation: {file_path}")
                
                # Update self.code_log with the final generated code (only after successful save)
                self.code_log = clean_code
                
                # Update the Code tab display (only after successful save)
                self.code_display.clear()
                self.code_display.append("=== 🔧 FINAL GENERATED CODE ===\n")
                self.code_display.append(clean_code)
                self.log_message("🎉 Final code generated and saved successfully!")
            
            # Update flowchart with the final generated code
            if hasattr(self, 'flowchart_widget') and clean_code:
                try:
                    # Set the code in the flowchart IDE
                    self.flowchart_widget.code_input.setPlainText(clean_code)
                    # Generate the flowchart
                    self.flowchart_widget.generate_flowchart()
                    self.log_message("📊 Flowchart updated with final code")
                    
                    # Switch to FlowChart tab to show the result
                    if hasattr(self, 'content_area'):
                        flowchart_tab_index = -1
                        for i in range(self.content_area.count()):
                            if "FlowChart" in self.content_area.tabText(i):
                                flowchart_tab_index = i
                                break
                        if flowchart_tab_index >= 0:
                            self.content_area.setCurrentIndex(flowchart_tab_index)
                            self.log_message("📊 Switched to FlowChart tab")
                except Exception as e:
                    print(f"Error updating flowchart with final code: {e}")
            
        except Exception as e:
            QMessageBox.critical(self, "❌ Error", f"Failed to generate final code: {str(e)}")
            self.log_message(f"❌ Error generating final code: {str(e)}")
    
    def update_task_list(self):
        # Store current task status before clearing

        old_task_status = {}

        if hasattr(self.task_list, 'task_status'):

            old_task_status = self.task_list.task_status.copy()

        

        # Store current breakpoints and radio selections

        old_breakpoints = self.task_list.breakpoints.copy() if hasattr(self.task_list, 'breakpoints') else set()

        old_radio_selections = self.task_list.radio_selections.copy() if hasattr(self.task_list, 'radio_selections') else set()

        

        print(f"🔄 UPDATE_TASK_LIST: Preserving status for {len(old_task_status)} steps")

        print(f"🔄 UPDATE_TASK_LIST: Preserving {len(old_breakpoints)} breakpoints and {len(old_radio_selections)} radio selections")

        

        # Clear and rebuild task list

        self.task_list.clear()

        self.task_list.clear_breakpoints()

        for i, task in enumerate(self.req_class):

            self.task_list.add_task_with_breakpoint(task, i)

        
        # Ensure add button is at the end after loading all tasks
        self.task_list.ensure_add_button_at_end()

        # Restore breakpoints and radio selections

        self.task_list.breakpoints = old_breakpoints

        self.task_list.radio_selections = old_radio_selections

        

        # Restore task status and update UI colors

        for task_idx, status in old_task_status.items():

            if task_idx < len(self.req_class):  # Only restore if task still exists

                self.task_list.task_status[task_idx] = status

                self.task_list.update_task_status(task_idx, status)

                print(f"🔄 RESTORED: Task {task_idx} status = {status}")

        

        # Update UI to reflect restored breakpoints and radio selections

        self.task_list.rebuild_task_list()
    
    def log_message(self, message):
        timestamp = self.get_timestamp()
        self.log_display.append(f"<span style='color: #888;'>[{timestamp}]</span> {message}")
        cursor = self.log_display.textCursor()
        cursor.movePosition(QTextCursor.End)
        self.log_display.setTextCursor(cursor)
    
    def get_timestamp(self):
        from datetime import datetime
        return datetime.now().strftime("%H:%M:%S")
        
    def update_code_display(self, code_log):
        """Update the Code tab display with real-time code_log updates - DEPRECATED"""
        # This method is now deprecated - skeleton code is displayed instead
        pass
    
    def update_code_display_with_skeleton(self, skeleton_code):
        """Update the Code tab display with generated skeleton code"""
        if skeleton_code and skeleton_code.strip():
            # Update the Code tab with skeleton code
            self.code_display.initialize_state(skeleton_code)
            
            # CRITICAL FIX: Update self.code_log to match the displayed code
            self.code_log = skeleton_code
            print(f"✅ FIXED: self.code_log updated with skeleton code ({len(skeleton_code)} chars)")
            
            # Reset any special styling
            self.code_display.setStyleSheet("""
                QTextEdit {
                    background-color: #1e1e1e;
                    color: #d4d4d4;
                    border: 1px solid #3c3c3c;
                    border-radius: 6px;
                    padding: 12px;
                    font-family: 'Consolas', 'Monaco', 'Courier New', monospace;
                    font-size: 14px;
                    line-height: 1.5;
                    selection-background-color: #264f78;
                    selection-color: #ffffff;
                }
            """)
            # Scroll to the top to show the beginning of the code
            cursor = self.code_display.textCursor()
            cursor.movePosition(cursor.Start)
            self.code_display.setTextCursor(cursor)
            # Enable Execute Flow in sidebar now that skeleton code exists
            try:
                if hasattr(self, 'execute_flow_btn'):
                    self.execute_flow_btn.setEnabled(True)
                if hasattr(self, 'stop_flow_btn'):
                    self.stop_flow_btn.setEnabled(False)
            except Exception:
                pass
        else:
            # Show placeholder when no skeleton code is available
            self.code_display.initialize_state("# Generated skeleton code will appear here after processing...")
            self.code_display.setStyleSheet("color: #888888; font-style: italic;")
            
            # Clear code_log when no skeleton code
            self.code_log = ""
            print("✅ FIXED: self.code_log cleared (no skeleton code available)")
            # Disable Execute Flow when no code displayed
            try:
                if hasattr(self, 'execute_flow_btn'):
                    self.execute_flow_btn.setEnabled(False)
                if hasattr(self, 'stop_flow_btn'):
                    self.stop_flow_btn.setEnabled(False)
            except Exception:
                pass
            
    def save_flowchart_as_pdf(self):
        """Save the current flowchart as PDF"""
        if not hasattr(self, 'flowchart_widget'):
            return
            
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Save Flowchart as PDF",
            os.path.expanduser("~/flowchart.pdf"),
            "PDF Files (*.pdf);;All Files (*)"
        )
        
        if file_path:
            try:
                # Ensure .pdf extension
                if not file_path.lower().endswith('.pdf'):
                    file_path += '.pdf'
                
                # Call the flowchart widget's PDF export function
                if hasattr(self.flowchart_widget, 'export_pdf'):
                    self.flowchart_widget.export_pdf(file_path)
                    self.log_message(f"✅ Flowchart saved as PDF: {file_path}")
                    QMessageBox.information(
                        self,
                        "Success",
                        f"Flowchart saved successfully as PDF!\nLocation: {file_path}"
                    )
            except Exception as e:
                error_msg = f"Error saving PDF: {str(e)}"
                print(f"❌ {error_msg}")
                QMessageBox.critical(
                    self,
                    "Error",
                    error_msg
                )
    
    def on_tasks_updated(self, updated_tasks):
        """Handle task updates from the editable task list"""
        self.req_class = updated_tasks
        self.log_message(f"📝 Tasks updated - {len(updated_tasks)} steps in list")
        print(f"📝 TASKS UPDATED: {len(updated_tasks)} steps")
        for i, task in enumerate(updated_tasks):
            print(f"  Step {i+1}: {task[:50]}..." if len(task) > 50 else f"  Step {i+1}: {task}")

    def on_tasks_restructured(self, new_tasks):
        """Handle task restructuring from TaskProcessor"""
        self.req_class = new_tasks
        self.update_task_list()
        self.log_message(f"🔄 Tasks restructured - new total: {len(new_tasks)}")
        print(f"🔄 TASKS RESTRUCTURED: {len(new_tasks)} steps")
        for i, task in enumerate(new_tasks):
            print(f"  Step {i+1}: {task[:50]}..." if len(task) > 50 else f"  Step {i+1}: {task}")
    
    def restructure_tasks(self):
        """Handle task restructuring using Gemini API"""
        user_input = self.task_restructure_input.toPlainText().strip()
        
        if not user_input:
            self.show_custom_warning("Warning", "Please enter instructions for task restructuring!")
            return
        
        if not self.req_class:
            self.show_custom_warning("Warning", "No tasks available to restructure!")
            return
        
        # Disable the send button during processing
        self.restructure_send_btn.setEnabled(False)
        self.log_message(f"🔄 Restructuring tasks based on: {user_input}")

        # Run Gemini call off the UI thread
        def _run_restructure():
            from customize_task import gemini_response
            return gemini_response(user_input, self.req_class)

        self.restructure_worker = SimpleFunctionWorker(_run_restructure)
        self.restructure_worker.finished.connect(self._on_restructure_finished)
        self.restructure_worker.error.connect(self._on_restructure_error)
        self.restructure_worker.start()

    def _on_restructure_finished(self, response):
        try:
            if isinstance(response, list) and len(response) > 0:
                old_task_count = len(self.req_class)
                self.req_class = response

                # Use threaded population to keep UI smooth
                self.task_list.set_tasks_data(self.req_class)
                self.start_task_list_population()

                self.task_restructure_input.clear()
                self.log_message(f"✅ Tasks restructured successfully! {old_task_count} → {len(self.req_class)} steps")

                if self.task_processor and self.task_processor.isRunning():
                    self.log_message("🔄 Resuming task processing with new tasks...")
                    self.task_processor.req_class = self.req_class

                self.show_custom_success(
                    "Success",
                    f"Tasks restructured successfully!\n"
                    f"Old tasks: {old_task_count}\n"
                    f"New tasks: {len(self.req_class)}"
                )
            else:
                self.log_message("❌ Error: Invalid response from Gemini API")
                self.show_custom_error("Error", "Failed to restructure tasks. Invalid response from API.")
        finally:
            self.restructure_send_btn.setEnabled(True)
            self.restructure_worker = None

    def _on_restructure_error(self, error_message):
        self.log_message(f"❌ Error restructuring tasks: {error_message}")
        self.show_custom_error("Error", f"Failed to restructure tasks:\n{error_message}")
        self.restructure_send_btn.setEnabled(True)
        self.restructure_worker = None
    # Verify mode functionality removed

    def on_detail_mode_requested(self, task_idx, response_text):
        """Handle detail mode request from TaskProcessor"""
        try:
            # Show detail mode dialog in main thread
            if self.show_detail_mode_dialog(task_idx, response_text,self.req_class[task_idx]):
                # Unlock task processor
                if hasattr(self, 'task_processor'):
                    self.task_processor.verification_mutex.lock()
                    self.task_processor.verification_result = True
                    self.task_processor.verification_pending = False
                    self.task_processor.verification_condition.wakeAll()
                    self.task_processor.verification_mutex.unlock()
            else:
                # Cancelled or failed
                if hasattr(self, 'task_processor'):
                    self.task_processor.verification_mutex.lock()
                    self.task_processor.verification_result = False
                    self.task_processor.verification_pending = False
                    self.task_processor.verification_condition.wakeAll()
                    self.task_processor.verification_mutex.unlock()
        except Exception as e:
            print(f"Error in detail mode dialog: {str(e)}")
            # Ensure thread is unblocked even if there's an error
            if hasattr(self, 'task_processor'):
                self.task_processor.verification_mutex.lock()
                self.task_processor.verification_result = False
                self.task_processor.verification_pending = False
                self.task_processor.verification_condition.wakeAll()
                self.task_processor.verification_mutex.unlock()

    # def on_detail_mode_requested(self, task_idx, response_text):
    #     """Handle detail mode request from TaskProcessor"""
    #     from detailing_mode_dialog import DetailModeDialog
    #     dialog = DetailModeDialog(self.req_class[task_idx], response_text, self)
        
    #     if dialog.exec_() == QDialog.Accepted:
    #         user_input = dialog.get_user_input()
    #         if user_input.strip():
    #             # Process user input through detail_mode_correction
    #             import detail_mode_correction
    #             corrected_task = detail_mode_correction.gemini_response(user_input)
                
    #             # Update task in req_class and UI
    #             self.req_class[task_idx] = corrected_task
                
    #             # Force UI refresh
    #             if hasattr(self, 'task_list') and hasattr(self.task_list, 'update_task'):
    #                 self.task_list.update_task(task_idx, corrected_task)
    #                 self.update_task_list()  # Refresh entire task list UI
                    
    #             # Unlock task processor with success
    #             if hasattr(self, 'task_processor'):
    #                 self.task_processor.verification_mutex.lock()
    #                 self.task_processor.verification_result = True
    #                 self.task_processor.verification_pending = False
    #                 self.task_processor.verification_condition.wakeAll()
    #                 self.task_processor.verification_mutex.unlock()
    #         else:
    #             # Cancel detail mode if no input
    #             if hasattr(self, 'task_processor'):
    #                 self.task_processor.verification_mutex.lock()
    #                 self.task_processor.verification_result = False
    #                 self.task_processor.verification_pending = False
    #                 self.task_processor.verification_condition.wakeAll()
    #                 self.task_processor.verification_mutex.unlock()
    #     else:
    #         # Dialog cancelled
    #         if hasattr(self, 'task_processor'):
    #             self.task_processor.verification_mutex.lock()
    #             self.task_processor.verification_result = False
    #             self.task_processor.verification_pending = False
    #             self.task_processor.verification_condition.wakeAll()
    #             self.task_processor.verification_mutex.unlock()
    
    def show_detail_mode_dialog(self, task_idx, response_text, task_name):

        from detail_mode_dialog import DetailModeMainWindow        
        from PyQt5.QtCore import QTimer, QEventLoop
        from PyQt5.QtWidgets import QApplication
        import time
        import gc
        
        print(f"📢 Preparing Detail Mode window for Step {task_idx + 1}")
        print(f"📢 Response text to speak: {response_text[:50]}...")
        
        # Set detail mode state when detail mode starts
        if hasattr(self, 'processing_widget'):
            print(" About to set processing widget to DETAIL MODE state")
            # Force UI update before setting state
            from PyQt5.QtWidgets import QApplication
            QApplication.processEvents()
            self.processing_widget.set_detail_mode_state()
            print(" Processing widget set to DETAIL MODE state")
            # Additional UI update after setting state
            QApplication.processEvents()
            # Small delay to ensure state is properly applied
            import time
            time.sleep(0.1)
        
        gc.collect()
        QApplication.processEvents()
        time.sleep(0.3)  

        dialog = DetailModeMainWindow(response_text)
        
        print(f"📢 Detail Mode dialog created, preparing to show...")
        
        loop = QEventLoop()
        dialog.destroyed.connect(loop.quit)  
        

        result = [None]
        
        def set_result(res):
            result[0] = res
            print(f"📢 Dialog result captured: {res[:50] if res else 'None'}...")
        
        dialog.accepted_signal.connect(set_result)
        
        # Show dialog and ensure it's properly displayed with multiple speech triggers
        dialog.show()
        dialog.raise_()
        dialog.activateWindow()
        
        # Process events multiple times to ensure dialog is fully rendered
        for _ in range(3):
            QApplication.processEvents()
            time.sleep(0.1)
        
        # Trigger speech multiple times with delays to ensure it works
        print(f"📢 Detail Mode dialog shown, triggering speech...")
        dialog.speak_text_advanced(response_text)  # Immediate attempt
        
        print(f"📢 Detail Mode dialog fully initialized, entering event loop...")
        
        # Block until window is closed
        loop.exec_()
        
        print(f"📢 Event loop exited, processing result...")
        
        # Now check the captured result without accessing the deleted dialog
        if result[0] is not None:
            user_input = result[0]
            if user_input and user_input.strip():
                print(f"📢 User provided input: {user_input[:50]}...")
                
                from detailing_mode_correction import gemini_response
                
                response = gemini_response(user_input, task_name)
                print(f"Detail correction on task: {task_name} : {response}")

                self.req_class[task_idx] = response
                
                if hasattr(self, 'task_list') and hasattr(self.task_list, 'set_tasks_data'):
                    print(f"📢 Updating task list UI for step {task_idx + 1}")
                    self.task_list.set_tasks_data(self.req_class)
                    QTimer.singleShot(100, self.update_task_list)  # Small delay to ensure UI updates
                    
                if hasattr(self.task_processor, 'verification_result'):
                    self.task_processor.verification_result = response
                    
                print(f"✅ Detail mode updated step {task_idx + 1} with user input")
                # Set to OFF state when detail mode completes
                if hasattr(self, 'processing_widget'):
                    self.processing_widget.set_off_state()
                return True  # Success
            else:
                print("⚠️ No input provided by user")
                if hasattr(self.task_processor, 'verification_result'):
                    self.task_processor.verification_result = None
                return False  # No input provided
        else:
            print("⚠️ Dialog closed without accepting")
            if hasattr(self.task_processor, 'verification_result'):
                self.task_processor.verification_result = None
            # Set to OFF state when detail mode is cancelled
            if hasattr(self, 'processing_widget'):
                self.processing_widget.set_off_state()
            return False  # Window closed without accept

        # Cleanup any remaining task processor states
        if hasattr(self.task_processor, 'verification_pending') and \
        hasattr(self.task_processor, 'verification_mutex') and \
        hasattr(self.task_processor, 'verification_condition'):
            print(f"📢 Unlocking task processor for step {task_idx + 1}")
            self.task_processor.verification_pending = False
            self.task_processor.verification_mutex.lock()
            self.task_processor.verification_condition.wakeAll()
            self.task_processor.verification_mutex.unlock()
            
    def toggle_verify_mode(self):
        """Toggle verify mode state"""
        self.verify_mode = self.verify_mode_btn.is_enabled
        if self.verify_mode:
            print(" Verify Mode enabled - tasks will require confirmation")
            # Safely append to terminal if it exists
            if hasattr(self, 'terminal_display') and self.terminal_display is not None:
                try:
                    self.terminal_display.append("[INFO] ✅ Verify Mode enabled - each task will require confirmation")
                except RuntimeError:
                    pass  # Terminal widget has been deleted, ignore
        else:
            print(" Verify Mode disabled - tasks will execute normally")
            # Safely append to terminal if it exists
            if hasattr(self, 'terminal_display') and self.terminal_display is not None:
                try:
                    self.terminal_display.append("[INFO]  Verify Mode disabled - tasks will execute normally")
                except RuntimeError:
                    pass  # Terminal widget has been deleted, ignore
    def toggle_tab_groups(self):
        """Toggle between primary tabs (main) and secondary tabs (debug tools)"""
        if self.showing_primary_tabs:
            # Switch to secondary tabs (Debug Tools)
            self.primary_tabs.hide()
            self.secondary_tabs.show()
            # Keep the icon, don't change text
            self.tab_toggle_btn.setToolTip("Switch back to Main tabs")
            self.showing_primary_tabs = False
            print("🔧 Switched to Debug Tools tabs")
        else:
            # Switch to primary tabs (Main)
            self.secondary_tabs.hide()
            self.primary_tabs.show()
            # Keep the icon, don't change text
            self.tab_toggle_btn.setToolTip("Toggle between Main tabs and Debug Tools")
            self.showing_primary_tabs = True
            print("📋 Switched to Main tabs")
    def on_verification_requested(self, task_idx, task_description):
        """Handle verification request from TaskProcessor"""
        try:
            verification_dialog = task_processor.VerificationDialog(task_description, parent=self,gemini_service=self.gemini_service)
            
            if verification_dialog.exec_() == QDialog.Accepted:
                if verification_dialog.result == "modify":
                    if self.task_events[task_idx]=="Event :Desktop":
                        self.task_processor.desktop_modify_info=verification_dialog.user_instruction
                    else:
                        # User wants to modify the task
                        print("verification_dialog.user_instruction", verification_dialog.user_instruction)
                        import verify_mode
                        new_task = verify_mode.gemini_response(verification_dialog.user_instruction)
                        new_task=new_task.strip("\n")
                        print("new_task", new_task)
                        # Update the task in TaskProcessor
                        self.task_processor.req_class[task_idx] = new_task
                        
                        # Update UI task display immediately
                        if hasattr(self, 'task_list'):
                            # Update the task data in the task list
                            if task_idx < len(self.task_list.tasks_data):
                                self.task_list.tasks_data[task_idx] = new_task
                            
                            # Update the UI display for this specific task
                            if task_idx in self.task_list.task_widgets:
                                widget_refs = self.task_list.task_widgets[task_idx]
                                radio_btn = widget_refs.get('radio_btn')
                                label = widget_refs['label']
                                
                                if radio_btn:
                                    radio_btn.setChecked(True)
                                    radio_btn.setStyleSheet("""
                                        QPushButton {
                                            background-color: #0078d4;
                                            border: 1px solid #0078d4;
                                            border-radius: 6px;
                                        }
                                        QPushButton:hover {
                                            border: 1px solid #cccccc;
                                            background-color: rgba(255, 255, 255, 0.1);
                                        }
                                        QPushButton:checked {
                                            background-color: #0078d4;
                                            border: 1px solid #0078d4;
                                        }
                                    """)
                                    
                                    label.setStyleSheet("""
                                        QLabel {
                                            color: #0078d4;
                                            font-size: 14px;
                                            font-weight: 600;
                                            padding: 8px 10px;
                                            background-color: transparent;
                                            border: none;
                                            line-height: 1.5;
                                        }
                                    """)
                
                    # Signal TaskProcessor that task was modified
                    self.task_processor.verification_result = "modify"
                elif verification_dialog.result == "continue":
                    self.task_processor.verification_result = "continue"
                
            else:
                # User cancelled
                self.task_processor.verification_result = "cancel"
            
            # Wake up the waiting TaskProcessor thread
            self.task_processor.verification_mutex.lock()
            self.task_processor.verification_pending = False
            self.task_processor.verification_condition.wakeAll()
            self.task_processor.verification_mutex.unlock()
            
        except Exception as e:
            print(f"Error in verification dialog: {e}")
            # In case of error, continue normally
            self.task_processor.verification_result = "continue"
            self.task_processor.verification_mutex.lock()
            self.task_processor.verification_pending = False
            self.task_processor.verification_condition.wakeAll()
            self.task_processor.verification_mutex.unlock()
    
    def on_exception_dialog_requested(self, task_idx, status, task_description):
        """Handle exception dialog request from TaskProcessor - THREAD SAFE"""
        try:
            print(f"🚨 MAIN THREAD: Showing exception dialog for step {task_idx}")
            
            # Create exception dialog on main thread
            dialog = QDialog(self)
            dialog.setWindowTitle("Exception Handling")
            dialog.setModal(True)
            dialog.setFixedSize(500, 300)
            dialog.setProperty('class', 'CustomDialog')
            style_loader.apply_stylesheet(dialog)
            
            # Exception message
            exception_label = QLabel(f"Exception occurred: {status}\nDuring task: {task_description}\n\nPlease provide instructions to overcome this exception:")
            exception_label.setWordWrap(True)
            layout.addWidget(exception_label)
            
            # User instruction input
            instruction_input = QTextEdit()
            instruction_input.setPlaceholderText("Enter your instructions here...")
            layout.addWidget(instruction_input)
            
            # Buttons
            button_layout = QHBoxLayout()
            ok_button = QPushButton("OK")
            cancel_button = QPushButton("Cancel")
            
            button_layout.addWidget(cancel_button)
            button_layout.addWidget(ok_button)
            layout.addLayout(button_layout)
            
            # Button connections
            ok_button.clicked.connect(dialog.accept)
            cancel_button.clicked.connect(dialog.reject)
            
            # Show dialog and get result
            if dialog.exec_() == QDialog.Accepted:
                user_instruction = instruction_input.toPlainText().strip()
                self.task_processor.exception_dialog_result = user_instruction if user_instruction else None
                print(f"📝 MAIN THREAD: User provided instruction: {user_instruction}")
            else:
                self.task_processor.exception_dialog_result = None
                print("⏭️ MAIN THREAD: User cancelled exception dialog")
            
            # Wake up the waiting TaskProcessor thread
            self.task_processor.exception_dialog_mutex.lock()
            self.task_processor.exception_dialog_pending = False
            self.task_processor.exception_dialog_condition.wakeAll()
            self.task_processor.exception_dialog_mutex.unlock()
            
        except Exception as e:
            print(f"❌ ERROR in exception dialog: {e}")
            # In case of error, set result to None and wake up thread
            self.task_processor.exception_dialog_result = None
            self.task_processor.exception_dialog_mutex.lock()
            self.task_processor.exception_dialog_pending = False
            self.task_processor.exception_dialog_condition.wakeAll()
            self.task_processor.exception_dialog_mutex.unlock()
    
    def on_element_confirmation_requested(self, task_idx, xpath):
        """Handle element confirmation request from TaskProcessor - THREAD SAFE"""
        try:
            print(f" MAIN THREAD: Showing element confirmation popup for step {task_idx}")
            
            # Start element blinking in the background
            self.start_element_blinking(task_idx, xpath)
            
            # Create frameless confirmation popup on main thread
            popup = QWidget()
            popup.setWindowFlags(
                Qt.FramelessWindowHint | 
                Qt.WindowStaysOnTopHint | 
                Qt.Tool |  # Prevents interference with focus
                Qt.X11BypassWindowManagerHint  # For Linux compatibility
            )
            popup.setAttribute(Qt.WA_TranslucentBackground)
            popup.setAttribute(Qt.WA_ShowWithoutActivating)  # Prevents focus stealing
            popup.setFixedSize(400, 200)
            
            # Store popup reference to prevent premature garbage collection
            self._current_popup = popup
            
            # Center the popup on screen
            screen = QApplication.primaryScreen().geometry()
            popup.move(
                (screen.width() - popup.width()) // 2,
                (screen.height() - popup.height()) // 2
            )
            
            # Add dragging support to the popup
            popup._mouse_pressed = False
            popup._mouse_pos = None
            
            def popup_mousePressEvent(event):
                if event.button() == Qt.LeftButton:
                    popup._mouse_pressed = True
                    popup._mouse_pos = event.globalPos() - popup.pos()
                    event.accept()
            
            def popup_mouseReleaseEvent(event):
                if event.button() == Qt.LeftButton:
                    popup._mouse_pressed = False
                    event.accept()
            
            def popup_mouseMoveEvent(event):
                if popup._mouse_pressed and popup._mouse_pos is not None:
                    popup.move(event.globalPos() - popup._mouse_pos)
                    event.accept()
            
            # Override close event to prevent accidental closing
            original_close_event = popup.closeEvent
            def safe_close_event(event):
                # Only allow programmatic closing, not external close events
                if hasattr(popup, '_allow_close') and popup._allow_close:
                    original_close_event(event)
                else:
                    event.ignore()
            
            popup.closeEvent = safe_close_event
            popup._allow_close = False
            
            # Connect mouse events for dragging
            popup.mousePressEvent = popup_mousePressEvent
            popup.mouseReleaseEvent = popup_mouseReleaseEvent
            popup.mouseMoveEvent = popup_mouseMoveEvent
            
            # Create main container with rounded corners and shadow
            container = QWidget(popup)
            container.setGeometry(0, 0, 400, 200)
            container.setStyleSheet("""
                QWidget {
                    background-color: #2d2d30;
                    border: 2px solid #0078d4;
                    border-radius: 15px;
                }
            """)
            
            layout = QVBoxLayout(container)
            layout.setContentsMargins(25, 25, 25, 25)
            layout.setSpacing(20)
            
            # Title with pulsing animation to show it's active
            title_label = QLabel(" Element Confirmation")
            title_label.setStyleSheet("""
                QLabel {
                    color: #0078d4;
                    font-weight: bold;
                    font-size: 16px;
                    text-align: center;
                }
            """)
            title_label.setAlignment(Qt.AlignCenter)
            layout.addWidget(title_label)
            
            # Add pulsing animation to title to show activity
            title_effect = QGraphicsOpacityEffect()
            title_label.setGraphicsEffect(title_effect)
            
            title_animation = QPropertyAnimation(title_effect, b"opacity")
            title_animation.setDuration(1000)
            title_animation.setStartValue(0.5)
            title_animation.setEndValue(1.0)
            title_animation.setLoopCount(-1)
            title_animation.setEasingCurve(QEasingCurve.InOutQuad)
            title_animation.start()
            
            # Store animation reference
            popup._title_animation = title_animation
            
            # Message
            message_label = QLabel(f"Is this the correct element for step {task_idx + 1}?\n\nXPath: {xpath}")
            message_label.setStyleSheet("""
                QLabel {
                    color: #ffffff;
                    font-size: 12px;
                    text-align: center;
                    background-color: rgba(0, 120, 212, 0.1);
                    border: 1px solid rgba(0, 120, 212, 0.3);
                    border-radius: 8px;
                    padding: 10px;
                }
            """)
            message_label.setAlignment(Qt.AlignCenter)
            message_label.setWordWrap(True)
            layout.addWidget(message_label)
            
            # Buttons
            button_layout = QHBoxLayout()
            button_layout.setSpacing(15)
            
            no_btn = QPushButton("❌ No")
            no_btn.setFixedSize(80, 35)
            no_btn.setStyleSheet("""
                QPushButton {
                    background-color: #dc3545;
                    color: white;
                    border: none;
                    border-radius: 8px;
                    font-weight: bold;
                    font-size: 12px;
                }
                QPushButton:hover {
                    background-color: #c82333;
                    transform: scale(1.05);
                }
                QPushButton:pressed {
                    background-color: #bd2130;
                }
            """)
            
            yes_btn = QPushButton("✅ Yes")
            yes_btn.setFixedSize(80, 35)
            yes_btn.setStyleSheet("""
                QPushButton {
                    background-color: #28a745;
                    color: white;
                    border: none;
                    border-radius: 8px;
                    font-weight: bold;
                    font-size: 12px;
                }
                QPushButton:hover {
                    background-color: #218838;
                    transform: scale(1.05);
                }
                QPushButton:pressed {
                    background-color: #1e7e34;
                }
            """)
            
            button_layout.addStretch()
            button_layout.addWidget(no_btn)
            button_layout.addWidget(yes_btn)
            button_layout.addStretch()
            
            layout.addLayout(button_layout)
            
            # Create cleanup function
            def cleanup_popup():
                try:
                    # Stop animations
                    if hasattr(popup, '_title_animation'):
                        popup._title_animation.stop()
                    
                    # Stop element blinking
                    self.stop_element_blinking(task_idx, xpath)
                    
                    # Allow popup to close
                    popup._allow_close = True
                    
                    # Remove reference
                    if hasattr(self, '_current_popup'):
                        delattr(self, '_current_popup')
                        
                    # Close popup safely
                    if popup and popup.isVisible():
                        popup.close()
                        
                except Exception as e:
                    print(f"Error during popup cleanup: {e}")
            
            # Button connections with improved thread safety
            def on_yes():
                try:
                    print("✅ Element confirmation: Yes clicked")
                    
                    # Set verification result in thread-safe manner
                    with QMutexLocker(self.task_processor.verification_mutex):
                        self.task_processor.verification_result = "yes"
                        self.task_processor.verification_pending = False
                        self.task_processor.verification_condition.wakeAll()
                    
                    # Use QTimer.singleShot for safe cleanup
                    QTimer.singleShot(100, cleanup_popup)
                    
                except Exception as e:
                    print(f"Error in yes button handler: {e}")
            
            def on_no():
                try:
                    print("❌ Element confirmation: No clicked")
                    
                    # Set verification result in thread-safe manner
                    with QMutexLocker(self.task_processor.verification_mutex):
                        self.task_processor.verification_result = "no"
                        self.task_processor.verification_pending = False
                        self.task_processor.verification_condition.wakeAll()
                    
                    # Use QTimer.singleShot for safe cleanup
                    QTimer.singleShot(100, cleanup_popup)
                    
                except Exception as e:
                    print(f"Error in no button handler: {e}")
            
            # Connect buttons
            yes_btn.clicked.connect(on_yes)
            no_btn.clicked.connect(on_no)
            
            # Add keyboard shortcuts for accessibility
            yes_shortcut = QShortcut(QKeySequence("Return"), popup)
            yes_shortcut.activated.connect(on_yes)
            
            no_shortcut = QShortcut(QKeySequence("Escape"), popup)
            no_shortcut.activated.connect(on_no)
            
            # Show popup with non-blocking approach
            popup.show()
            popup.raise_()
            
            # Don't call activateWindow() to prevent focus conflicts with TTS
            # popup.activateWindow()  # Commented out to prevent TTS interference
            
            # Ensure popup stays visible even if focus changes
            popup.setWindowState(popup.windowState() & ~Qt.WindowMinimized | Qt.WindowActive)
            
            print(f"🎤 Popup shown for step {task_idx}, TTS can now run simultaneously")
            
        except Exception as e:
            print(f"❌ ERROR in element confirmation popup: {e}")
            # In case of error, set result to "yes" and wake up thread to continue
            try:
                with QMutexLocker(self.task_processor.verification_mutex):
                    self.task_processor.verification_result = "yes"
                    self.task_processor.verification_pending = False
                    self.task_processor.verification_condition.wakeAll()
            except:
                pass
            
    def start_detail_mode_validation(self):
        """Start Detail Mode validation with unified popup"""
        try:
            print(" Starting Detail Mode validation phase...")
            
            if not self.req_class:
                print("❌ No tasks to validate in Detail Mode")
                return
            
            self.update_tasks_status("Detail Mode in progress...", "#FF9800")
            
            # Initialize speech tracking variables
            self._validation_speech_active = False
            self._pending_validation_message = None
            
            # Show detail mode started notification
            # try:
            #     show_detail_mode_started_notification(parent=self)
            #     print(" Showed detail mode started notification")
            # except Exception as e:
            #     print(f"Error showing detail mode started popup: {e}")
            
            # Import the detail mode checker
            try:
                import detailing_mode_checker
                print("✅ Successfully imported detailing_mode_checker")
            except Exception as e:
                print(f"❌ Error importing detailing_mode_checker: {e}")
                QMessageBox.critical(self, "❌ Import Error", f"Failed to import detailing_mode_checker:\n{str(e)}")
                return
            
            # Validation state tracking
            self.current_validation_index = 0
            self.validation_waiting = False
            
            # Create unified validation popup
            try:
                print("🔄 Creating UnifiedValidationPopup...")
                self.unified_popup = UnifiedValidationPopup(parent=self, gemini_service=self.gemini_service)
                print("✅ UnifiedValidationPopup created successfully")
                
                total_tasks = len(self.req_class)
                self.unified_popup.set_total_tasks(total_tasks)
                
                # Connect signals
                self.unified_popup.detail_mode_response.connect(self.on_unified_detail_response)
                self.unified_popup.validation_completed.connect(self.on_detail_mode_popup_closed)
                
                # Show the unified popup
                self.unified_popup.show()
                self.unified_popup.center_on_screen()
                
                # Process events with minimal interference
                QApplication.processEvents()
                
                print("📑 Unified validation popup created and displayed")
                print("💡 Starting validation process...")

                try:
                    friendly_response = self.gemini_service.get_validation_start_message(total_tasks)
                    validation_message = friendly_response["message"]
                    print(f"🤖 Gemini validation message: {validation_message}")
                except Exception as e:
                    print(f"Error getting Gemini validation message: {e}")
                    validation_message = "Starting validation of your tasks..."

                # Speak the validation message first
                self.unified_popup.speak_validation_message(validation_message)
                
                # Wait a bit before starting actual validation to let the message play
                QTimer.singleShot(500, lambda: self._start_actual_validation(total_tasks))
                
            except Exception as popup_error:
                print(f"❌ Error creating UnifiedValidationPopup: {popup_error}")
                print("🔄 Falling back to simple validation...")
                
                # Fallback: Show simple message and skip detail mode
                QMessageBox.information(self, "✅ Tasks Generated", 
                                      f"{len(self.req_class)} steps have been generated successfully!\n\n"
                                      "Detail mode validation was skipped due to an error.\n"
                                      "You can proceed with task execution.")
                
                # Set to ready state
                if hasattr(self, 'processing_widget'):
                    self.processing_widget.set_ready_to_process_state()
                
                self.update_tasks_status("Tasks ready for execution", "#4CAF50")
                return

        except Exception as e:
            print(f"❌ Error in detail mode validation: {e}")
            self.update_tasks_status("Detail Mode error", "#F44336")
            
            # Fallback: Show error message and set ready state
            try:
                QMessageBox.warning(self, "⚠️ Validation Error", 
                                  f"Detail mode validation failed:\n{str(e)}\n\n"
                                  "Tasks have been generated but validation was skipped.\n"
                                  "You can still proceed with task execution.")
                
                # Set to ready state even on error
                if hasattr(self, 'processing_widget'):
                    self.processing_widget.set_ready_to_process_state()
                
                self.update_tasks_status("Tasks ready (validation skipped)", "#FF9800")
                
            except Exception as fallback_error:
                print(f"❌ Even fallback failed: {fallback_error}")
                # Last resort: just print and continue
                print("🔄 Application will continue without detail mode validation")

    def _start_actual_validation(self, total_tasks):
        """Start the actual validation process after initial message"""
        try:
            import detailing_mode_checker
            completed = 0
            
            # Process each task
            for index, single_task in enumerate(self.req_class):
                task_preview = single_task[:80] + "..." if len(single_task) > 80 else single_task
                print(f" Validating step {index + 1}: {task_preview}")
                
                # Update unified popup
                self.unified_popup.add_log(f" Validating step {index + 1}: {task_preview}...", "info")
                QApplication.processEvents()
                
                try:
                    # Validate task
                    ins_res = detailing_mode_checker.gemini_response(self.req_class[index], self.req_class[:index])
                    print(f"Validation response : {ins_res}")
                    
                    if ins_res["valid"] == False:
                        print(f" Step {index + 1} needs detail mode correction")
                        
                        # Update status
                        self.update_tasks_status(f"Step {index + 1} needs correction", "#FF5722")
                        
                        # Show detail mode in unified popup with proper speech sequencing
                        print(f"🔧 DEBUG: Calling show_detail_mode_for_task({index}, response, task)")
                        self.unified_popup.show_detail_mode_for_task(index, ins_res["response"], self.req_class[index])
                        
                        # Wait for user response
                        self.current_validation_index = index
                        self.validation_waiting = True
                        print(f"🔧 DEBUG: Set validation_waiting=True, current_validation_index={index}")
                        
                        # Force UI update
                        QApplication.processEvents()
                        
                        return  # Exit validation loop, will resume after user input
                        
                    else:
                        print(f"✅ Step {index + 1} is valid")
                        self.unified_popup.add_log(f"✅ Step {index + 1} is valid", "success")
                        completed += 1
                        self.unified_popup.set_progress(completed)
                        
                except Exception as task_error:
                    print(f"❌ Error validating step {index + 1}: {task_error}")
                    self.unified_popup.add_log(f"❌ Error: {str(task_error)}", "error")
                    continue
                
                QApplication.processEvents()
            
            # Completion
            validation_message = "All tasks validated successfully! Please proceed to executing the tasks"
            try:   
                friendly_response = self.gemini_service.get_validation_success_message()
                completion_message = friendly_response["message"]
                print(f"🤖 Gemini completion message: {completion_message}")
            except Exception as e:
                print(f"Error getting Gemini completion message: {e}")
                completion_message = "Amazing! All tasks are validated and ready to go!"

            # Then use the message
            self.unified_popup.speak_validation_message(completion_message)
            
            self.update_tasks_status("Detail Mode completed", "#4CAF50")
            self.unified_popup.add_log("🎉 All tasks validated!", "success")
            print("✅ Detail Mode validation completed")
            
            # Show detail mode completion notification (3 seconds)
            # try:
            #     show_detail_mode_completed_notification(parent=self)
            #     print("✅ Showed detail mode completion notification")
            # except Exception as e:
            #     print(f"Error showing detail mode completion popup: {e}")
            
            # Don't auto-close - let user manage the dialog
            print("📑 Detail Mode validation dialog remains open for user control")
            
        except Exception as e:
            print(f"❌ Error in actual validation: {e}")
            self.update_tasks_status("Detail Mode error", "#F44336")

    def on_unified_detail_response(self, task_index, user_input):
        """Handle detail mode response from unified popup"""
        try:
            print(f"📝 Processing detail mode response for step {task_index + 1}")
            
            # Import correction module
            import detailing_mode_correction
            
            # Get corrected task
            corrected_task = detailing_mode_correction.gemini_response(user_input, self.req_class[task_index])
            print(f"✅ Step {task_index + 1} corrected: {corrected_task[:100]}...")
            
            # Update task in the list
            self.req_class[task_index] = corrected_task
            
            # Update the Generated Tasks tab
            self.update_task_list()
            
            # Log the correction
            self.unified_popup.add_log(f"✅ Step {task_index + 1} corrected successfully", "success")
            
            # Reset validation state
            self.validation_waiting = False
            self.current_validation_index = -1
            
            # Resume validation from the next task
            self.resume_validation_from_index(task_index + 1)
            
        except Exception as e:
            print(f"❌ Error processing detail mode response: {e}")
            self.unified_popup.add_log(f"❌ Error: {str(e)}", "error")
            # Reset validation state on error too
            self.validation_waiting = False
            self.current_validation_index = -1
    
    def resume_validation_from_index(self, start_index):
        """Resume validation from a specific task index"""
        try:
            import detailing_mode_checker
            
            total_tasks = len(self.req_class)
            completed = start_index  # Tasks before this index are already processed
            
            # Continue validation from start_index
            for index in range(start_index, total_tasks):
                single_task = self.req_class[index]
                task_preview = single_task[:80] + "..." if len(single_task) > 80 else single_task
                print(f" Validating step {index + 1}: {task_preview}")
                
                # Update unified popup
                self.unified_popup.add_log(f" Validating step {index + 1}: {task_preview}...", "info")
                QApplication.processEvents()
                
                # Update main status
                self.update_tasks_status(f"Validating step {index + 1}...", "#FF9800")
                QApplication.processEvents()
                
                try:
                    # Validate task
                    ins_res = detailing_mode_checker.gemini_response(self.req_class[index], self.req_class[:index])
                    print(f"Validation response : {ins_res}")
                    
                    if ins_res["valid"] == False:
                        print(f" Step {index + 1} needs detail mode correction")
                        
                        # Update status
                        self.update_tasks_status(f"Step {index + 1} needs correction", "#FF5722")
                        
                        # Show detail mode in unified popup
                        print(f"🔧 DEBUG: Calling show_detail_mode_for_task({index}, response, task)")
                        self.unified_popup.show_detail_mode_for_task(index, ins_res["response"], self.req_class[index])
                        
                        # Wait for user response
                        self.current_validation_index = index
                        self.validation_waiting = True
                        print(f"🔧 DEBUG: Set validation_waiting=True, current_validation_index={index}")
                        
                        # Force UI update
                        QApplication.processEvents()
                        
                        return  # Exit validation loop, will resume after user input
                        
                    else:
                        print(f"✅ Step {index + 1} is valid")
                        self.unified_popup.add_log(f"✅ Step {index + 1} is valid", "success")
                        completed += 1
                        self.unified_popup.set_progress(completed)
                        
                except Exception as task_error:
                    print(f"❌ Error validating step {index + 1}: {task_error}")
                    self.unified_popup.add_log(f"❌ Error: {str(task_error)}", "error")
                    continue
                
                QApplication.processEvents()
            
            # All tasks completed
            self.update_tasks_status("Detail Mode completed", "#4CAF50")
            self.unified_popup.add_log("🎉 All tasks validated!", "success")
            print("✅ Detail Mode validation completed")
            
            # Show detail mode completion notification (3 seconds)
            try:
                show_detail_mode_completed_notification(parent=self)
                print("✅ Showed detail mode completion notification")
            except Exception as e:
                print(f"Error showing detail mode completion popup: {e}")
        except Exception as e:
            print(f"❌ Error resuming validation: {e}")
            self.unified_popup.add_log(f"❌ Error: {str(e)}", "error")

    def on_detail_mode_popup_closed(self):
        """Handle when detail mode popup is closed - set ready to process state"""
        try:
            print("🔄 Detail mode popup closed, setting ready to process state")
            if hasattr(self, 'processing_widget') and self.processing_widget:
                self.processing_widget.set_ready_to_process_state()
                print("✅ Set droid agent to READY TO PROCESS state")
        except Exception as e:
            print(f"❌ Error setting ready to process state: {e}")

    def on_driver_updated(self, driver):
        """Handle driver updates from TaskProcessor"""
        self.current_driver = driver
        print(f"🚗 MAIN THREAD: Driver updated - {type(driver).__name__}")

    
    def update_tasks_status(self, status, color="#4CAF50"):
        """Update status - popup removed"""
        # Just print the status, popup removed
        print(f"📊 STATUS UPDATED: {status}")

    def show_task_error(self, task_index: int, details: str = ""):
        """Display task failure - popup removed"""
        # Just print the error, popup removed
        print(f"❌ Error occurred at task no. {task_index} {details}")
    
    def _get_rgb_from_hex(self, hex_color):
        """Convert hex color to RGB string for CSS rgba"""
        hex_color = hex_color.lstrip('#')
        if len(hex_color) == 6:
            r = int(hex_color[0:2], 16)
            g = int(hex_color[2:4], 16)
            b = int(hex_color[4:6], 16)
            return f"{r}, {g}, {b}"
        return "76, 175, 80"  # Default green
    
    def start_element_blinking(self, task_idx, xpath):
        """Start blinking the element with yellow border - called from main thread"""
        try:
            # Store the current element info for this task
            if not hasattr(self, 'blinking_elements'):
                self.blinking_elements = {}
            
            self.blinking_elements[task_idx] = {
                'xpath': xpath,
                'timer': None
            }
            
            # Create a timer to blink the element
            from PyQt5.QtCore import QTimer
            
            def blink_element():
                try:
                    # Get the current driver from main app
                    if hasattr(self, 'current_driver') and self.current_driver:
                        driver = self.current_driver
                        # Inject JavaScript to blink the element with darker royal blue
                        script = """
                        function blinkElement(xpath) {
                            var element = document.evaluate(xpath, document, null, XPathResult.FIRST_ORDERED_NODE_TYPE, null).singleNodeValue;
                            if (element) {
                                // Define darker royal blue colors
                                var darkRoyalBlue = '#1e3a8a';  // Much darker royal blue
                                var accentBlue = '#1d4ed8';     // Slightly lighter accent
                                
                                // Check current state and toggle
                                if (element.style.border && element.style.border.includes(darkRoyalBlue)) {
                                    // Remove border and effects
                                    element.style.border = '';
                                    element.style.boxShadow = '';
                                    element.style.animation = '';
                                } else {
                                    // Apply darker royal blue border with enhanced effects
                                    element.style.border = '4px solid ' + darkRoyalBlue;
                                    element.style.boxShadow = '0 0 15px ' + accentBlue + ', inset 0 0 10px rgba(30, 58, 138, 0.3)';
                                    element.style.animation = 'darkRoyalBlink 1s infinite ease-in-out';
                                    element.style.borderRadius = '6px';
                                    element.style.position = 'relative';
                                    element.style.zIndex = '9999';
                                    
                                    // Add enhanced blinking animation with darker royal blue theme
                                    if (!document.getElementById('dark-royal-blink-style')) {
                                        var style = document.createElement('style');
                                        style.id = 'dark-royal-blink-style';
                                        style.innerHTML = `
                                            @keyframes darkRoyalBlink {
                                                0% { 
                                                    opacity: 1; 
                                                    border-color: #1e3a8a;
                                                    box-shadow: 0 0 15px #1d4ed8, inset 0 0 10px rgba(30, 58, 138, 0.3);
                                                    transform: scale(1);
                                                }
                                                25% {
                                                    opacity: 0.8;
                                                    border-color: #1d4ed8;
                                                    box-shadow: 0 0 25px #2563eb, inset 0 0 15px rgba(30, 58, 138, 0.5);
                                                    transform: scale(1.02);
                                                }
                                                50% { 
                                                    opacity: 0.4; 
                                                    border-color: #2563eb;
                                                    box-shadow: 0 0 35px #3b82f6, inset 0 0 20px rgba(30, 58, 138, 0.7);
                                                    transform: scale(1.04);
                                                }
                                                75% {
                                                    opacity: 0.8;
                                                    border-color: #1d4ed8;
                                                    box-shadow: 0 0 25px #2563eb, inset 0 0 15px rgba(30, 58, 138, 0.5);
                                                    transform: scale(1.02);
                                                }
                                                100% { 
                                                    opacity: 1; 
                                                    border-color: #1e3a8a;
                                                    box-shadow: 0 0 15px #1d4ed8, inset 0 0 10px rgba(30, 58, 138, 0.3);
                                                    transform: scale(1);
                                                }
                                            }
                                            
                                            /* Additional pulsing effect for extra visibility */
                                            @keyframes darkRoyalPulse {
                                                0% { box-shadow: 0 0 15px #1d4ed8; }
                                                50% { box-shadow: 0 0 30px #3b82f6, 0 0 40px #60a5fa; }
                                                100% { box-shadow: 0 0 15px #1d4ed8; }
                                            }
                                        `;
                                        document.head.appendChild(style);
                                    }
                                }
                            }
                        }
                        blinkElement(arguments[0]);
                        """
                        driver.execute_script(script, xpath)
                except Exception as e:
                    print(f"⚠️ Error in element blinking: {e}")
            
            # Create timer that blinks every 500ms
            timer = QTimer()
            timer.timeout.connect(blink_element)
            timer.start(500)
            
            # Store the timer
            self.blinking_elements[task_idx]['timer'] = timer
            
            # Start first blink immediately
            blink_element()
            
            print(f"🌟 Started element blinking for task {task_idx}, XPath: {xpath}")
            
        except Exception as e:
            print(f"❌ Error starting element blinking: {e}")
    
    def stop_element_blinking(self, task_idx, xpath):
        """Stop blinking the element and remove the border - called from main thread"""
        try:
            if hasattr(self, 'blinking_elements') and task_idx in self.blinking_elements:
                # Stop the timer
                timer = self.blinking_elements[task_idx].get('timer')
                if timer:
                    timer.stop()
                    timer.deleteLater()
                
                # Remove the blinking effect from the element
                if hasattr(self, 'current_driver') and self.current_driver:
                    driver = self.current_driver
                    script = """
                    function stopBlinking(xpath) {
                        var element = document.evaluate(xpath, document, null, XPathResult.FIRST_ORDERED_NODE_TYPE, null).singleNodeValue;
                        if (element) {
                            element.style.border = '';
                            element.style.animation = '';
                        }
                    }
                    stopBlinking(arguments[0]);
                    """
                    driver.execute_script(script, xpath)
                
                # Remove from tracking
                del self.blinking_elements[task_idx]
                
                print(f"🛑 Stopped element blinking for task {task_idx}, XPath: {xpath}")
                
        except Exception as e:
            print(f"❌ Error stopping element blinking: {e}")
 
    # ========================================
    # Code Tab Switching Methods
    # ========================================
    
    def show_code_chat_view(self):
        """Show Code Chat view and hide XPath Variables view"""
        self.code_chat_btn.setChecked(True)
        self.xpath_vars_btn.setChecked(False)
        self.code_chat_content.show()
        self.xpath_vars_content.hide()
        print("🔧 Switched to Code Chat view")
    
    def show_xpath_vars_view(self):
        """Show XPath Variables view and hide Code Chat view"""
        self.xpath_vars_btn.setChecked(True)
        self.code_chat_btn.setChecked(False)
        self.xpath_vars_content.show()
        self.code_chat_content.hide()
        print("🔧 Switched to XPath Variables view")
        
        # Refresh XPath display when switching to XPath view
        self.refresh_code_tab_xpath_data()
    
    # ========================================
    # Code Tab XPath Variables Methods
    # ========================================
    
    def clear_all_xpath_data(self):
        """
        Clears all XPath values in json_info/json_xpath.json by replacing them with 'Not_assigned'.
        """
        try:
            json_file_path = os.path.join(os.getcwd(), "json_info", "json_xpath.json")
            if not os.path.exists(json_file_path):
                self.show_custom_warning("File Not Found", f"File not found:\n{json_file_path}")
                return
            with open(json_file_path, "r", encoding="utf-8") as f:
                data = json.load(f)

            for key in data.keys():
                data[key] = "Not_assigned"

            # Write updated JSON back to file
            with open(json_file_path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=4)

            # Inform user with custom popup
            self.show_custom_success("Cleared", "All XPath values have been replaced with 'Not_assigned'!")

            # Refresh UI if supported
            if hasattr(self, "refresh_code_tab_xpath_data"):
                self.refresh_code_tab_xpath_data()

        except Exception as e:
            self.show_custom_error("Error", f"Failed to clear XPath data:\n{str(e)}")
        
    def refresh_code_tab_xpath_data(self):
        """Refresh XPath data from JSON file for Code tab"""
        import json
        import os
        
        current_mode = getattr(self, 'current_automation_mode', 'web')

        if current_mode == 'desktop':
            json_path = "json_info/json_attr.json"
            data_type = "Attributes"
        elif current_mode=='citrix':
            json_path = "json_info/citrix_data.json"
            data_type = "Citrix Data"
        else:
            json_path = "json_info/json_xpath.json"
            data_type = "XPath"
        self.code_tab_xpath_data = {}
        
        if os.path.exists(json_path):
            try:
                with open(json_path, "r", encoding="utf-8") as f:
                    self.code_tab_xpath_data = json.load(f)
                print(f"🔧 Code Tab: Loaded {len(self.code_tab_xpath_data)} {data_type} entries")
            except Exception as e:
                import traceback
                traceback.print_exc()
                print(f"❌ Code Tab: Error loading {data_type} JSON: {e}")
                self.code_tab_xpath_data = {}
        
        # Store original data for filtering/sorting
        self.code_tab_original_xpath_data = self.code_tab_xpath_data.copy()
        self.code_tab_filtered_xpath_data = self.code_tab_xpath_data.copy()
        
        self.update_code_tab_xpath_display()
    
    def save_code_tab_xpath_data(self):
        """Save XPath data to JSON file in real-time for Code tab"""
        import json
        import os
        
        # Determine which JSON file to save based on current automation mode
        current_mode = getattr(self, 'current_automation_mode', 'web')

        if current_mode == 'desktop':
            json_path = "json_info/json_attr.json"
            data_type = "Attributes"
        elif current_mode == 'citrix':
            json_path = "json_info/citrix_data.json"
            data_type = "Citrix Data"
        else:
            json_path = "json_info/json_xpath.json"
            data_type = "XPath"
        
        try:
            # Ensure directory exists
            os.makedirs("json_info", exist_ok=True)
            
            # Save the data
            with open(json_path, "w", encoding="utf-8") as f:
                json.dump(self.code_tab_xpath_data, f, indent=4, ensure_ascii=False)
            print(f"💾 Code Tab: Saved {data_type} data to {json_path}")
            
            # Also update the draggable chat panel if it exists
            if hasattr(self, 'chat_panel') and self.chat_panel:
                self.chat_panel.refresh_xpath_data()
            
        except Exception as e:
            print(f"❌ Code Tab: Error saving {data_type} JSON: {e}")
    
    def filter_code_tab_xpath_entries(self):
        """Filter XPath entries based on search text and filter combo for Code tab"""
        search_text = self.code_tab_xpath_search.text().lower()
        filter_option = self.code_tab_filter_combo.currentText()
        
        # Start with original data
        filtered_data = {}
        
        for key, value in self.code_tab_original_xpath_data.items():
            # Apply search filter
            if search_text:
                if (search_text not in key.lower() and 
                    search_text not in str(value).lower()):
                    continue
            
            # Apply dropdown filter
            if filter_option == "Show Not_assigned Only":
                if str(value).lower() != "not_assigned":
                    continue
            elif filter_option == "Show Assigned Only":
                if str(value).lower() == "not_assigned":
                    continue
            # "Show All" - no additional filtering
            
            filtered_data[key] = value
        
        self.code_tab_filtered_xpath_data = filtered_data
        self.sort_code_tab_xpath_entries()
    
    def sort_code_tab_xpath_entries(self):
        """Sort XPath entries based on sort combo selection for Code tab"""
        sort_option = self.code_tab_sort_combo.currentText()
        
        if sort_option == "Sort by Keys A-Z":
            sorted_items = sorted(self.code_tab_filtered_xpath_data.items(), key=lambda x: x[0].lower())
        elif sort_option == "Sort by Keys Z-A":
            sorted_items = sorted(self.code_tab_filtered_xpath_data.items(), key=lambda x: x[0].lower(), reverse=True)
        elif sort_option == "Sort by Values A-Z":
            sorted_items = sorted(self.code_tab_filtered_xpath_data.items(), key=lambda x: str(x[1]).lower())
        elif sort_option == "Sort by Values Z-A":
            sorted_items = sorted(self.code_tab_filtered_xpath_data.items(), key=lambda x: str(x[1]).lower(), reverse=True)
        else:
            sorted_items = list(self.code_tab_filtered_xpath_data.items())
        
        # Convert back to dict maintaining order
        self.code_tab_filtered_xpath_data = dict(sorted_items)
        self.update_code_tab_xpath_display()
    
    def update_code_tab_xpath_display(self):
        """Update the XPath display with filtered and sorted data for Code tab"""
        data_to_display = getattr(self, 'code_tab_filtered_xpath_data', self.code_tab_xpath_data)
        print(f"🔄 Code Tab: update_xpath_display called with {len(data_to_display)} filtered XPath entries")
 
        # ✅ Properly clear only existing XPath widgets (keep the bottom spacer/stretch)
        count_before = self.code_tab_xpath_list_layout.count()
        for i in reversed(range(count_before - 1)):  # keep last spacer
            item = self.code_tab_xpath_list_layout.itemAt(i)
            widget = item.widget()
            if widget:
                widget.deleteLater()  # safely delete from memory
            else:
                self.code_tab_xpath_list_layout.removeItem(item)
       
        # === Handle no data case ===
        if not data_to_display:
            total_count = len(getattr(self, 'code_tab_original_xpath_data', {}))
            if total_count > 0:
                self.code_tab_xpath_status_label.setText(f"No entries match current filter (Total: {total_count})")
            else:
                self.code_tab_xpath_status_label.setText("No XPath data available")
            return
       
        # Update count label
        count = len(data_to_display)
        total_count = len(getattr(self, 'code_tab_original_xpath_data', data_to_display))
        # if count == total_count:
        #     self.code_tab_xpath_status_label.setText(f"{count} XPath entry{'ies' if count != 1 else ''} available")
        # else:
        #     self.code_tab_xpath_status_label.setText(f"Showing {count} of {total_count} XPath entries")
        # Make status text mode-aware
        current_mode = getattr(self, 'current_automation_mode', 'web')
        if current_mode == 'desktop':
            data_type = "attributes"
        elif current_mode == 'citrix':
            data_type = "citrix data"
        else:
            data_type = "XPath"
 
        if count == total_count:
            self.code_tab_xpath_status_label.setText(f"{count} {data_type} entr{'y' if count == 1 else 'ies'} available")
        else:
            self.code_tab_xpath_status_label.setText(f"Showing {count} of {total_count} {data_type} entries")
        # === Recreate XPath entry widgets (keep original layout structure) ===
        for xpath, info in data_to_display.items():
            xpath_widget = self.create_code_tab_editable_xpath_widget(xpath, info)
            # 🔸 Insert before final stretch item (preserves spacing)
            self.code_tab_xpath_list_layout.insertWidget(
                self.code_tab_xpath_list_layout.count() - 1,
                xpath_widget
            )
       
        print(f"📊 Code Tab: Updated XPath display with {count} entries")
    
    def create_code_tab_editable_xpath_widget(self, xpath, info):
        """Create an editable widget for a single XPath entry in Code tab"""
        widget = QWidget()
        # widget = QWidget(self)  # Set parent to prevent separate windows
        main_layout = QHBoxLayout(widget)
        main_layout.setContentsMargins(12, 6, 12, 6)
        main_layout.setSpacing(8)
        
        
        # ----- Clear Button (left of XPath label) -----
        clear_btn = QPushButton()
        clear_btn.setFixedSize(32, 32)
        clear_btn.setToolTip("Clear this XPath entry")

        # Load icon safely with fallback to a drawn 'X' icon
        icon_path = resource_path("styles/Icon/clear_1.png")
        icon = None
        if os.path.exists(icon_path):
            pixmap = QPixmap(icon_path)
            if not pixmap.isNull():
                icon = QIcon(pixmap)
            else:
                print(f"⚠️ Image found but invalid: {icon_path}")
        else:
            print(f"⚠️ Icon not found at: {icon_path}")

        if not icon:
            # Create a fallback "X" pixmap icon manually
            pixmap = QPixmap(32, 32)
            pixmap.fill(Qt.transparent)
            painter = QPainter(pixmap)
            pen = QPen(QColor("#b04242"))
            pen.setWidth(3)
            painter.setPen(pen)
            painter.drawLine(8, 8, 24, 24)
            painter.drawLine(8, 24, 24, 8)
            painter.end()
            icon = QIcon(pixmap)

        clear_btn.setIcon(icon)
        clear_btn.setIconSize(QSize(20, 20))

        # --- Style ---
        clear_btn.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                border: 1px solid #555555;
                border-radius: 16px;
                padding: 4px;
            }
            QPushButton:hover {
                background-color: rgba(255, 255, 255, 0.1);
                border-color: #17a2b8;
            }
            QPushButton:pressed {
                background-color: rgba(255, 255, 255, 0.2);
                border-color: #4CAF50;
            }
        """)

        # --- Connect clear action ---
        clear_btn.clicked.connect(lambda: self.clear_xpath_value(xpath, info, widget))
        main_layout.addWidget(clear_btn)


            
        # Left side - XPath key label (non-editable) with fixed width for alignment
        xpath_label = QLabel(f"{xpath}:")
        xpath_label.setStyleSheet("""
            QLabel {
                color: #ffffff;
                font-weight: 600;
                font-size: 13px;
                padding: 6px 8px;
                background-color: rgba(255, 255, 255, 0.05);
                border-radius: 4px;
                border-left: 3px solid #17a2b8;
            }
        """)
        xpath_label.setWordWrap(True)
        xpath_label.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        xpath_label.setFixedWidth(180)  # Fixed width for alignment
        main_layout.addWidget(xpath_label)
        
        # Right side - Editable value field
        value_edit = QLineEdit(str(info))
        value_edit.setStyleSheet("""
            QLineEdit {
                background-color: #2d2d30;
                border: 1px solid #555555;
                border-radius: 6px;
                padding: 8px 12px;
                color: white;
                font-size: 12px;
                font-family: 'Consolas', 'Monaco', monospace;
                min-height: 18px;
            }
            QLineEdit:focus {
                border-color: #4CAF50;
                background-color: #353538;
            }
            QLineEdit:hover {
                border-color: #17a2b8;
                background-color: #353538;
            }
        """)
        
        # Add context menu for delete option
        value_edit.setContextMenuPolicy(Qt.CustomContextMenu)
        value_edit.customContextMenuRequested.connect(lambda pos: self.show_code_tab_xpath_context_menu(pos, xpath, value_edit))
        
        # Set placeholder and styling based on value
        if str(info).lower() == "not_assigned":
            value_edit.setPlaceholderText("Enter XPath value...")
            value_edit.setStyleSheet(value_edit.styleSheet() + """
                QLineEdit {
                    border-color: #ff6b6b;
                    background-color: rgba(255, 107, 107, 0.1);
                }
            """)
        
        # Connect real-time saving
        def on_value_changed():
            new_value = value_edit.text().strip()
            if new_value != str(info):
                # Update the data
                self.code_tab_xpath_data[xpath] = new_value
                self.code_tab_original_xpath_data[xpath] = new_value
                
                # Save to JSON file immediately
                self.save_code_tab_xpath_data()
                
                print(f"💾 Code Tab: Updated XPath '{xpath}' = '{new_value}'")
        
        value_edit.textChanged.connect(on_value_changed)
        value_edit.editingFinished.connect(on_value_changed)
        
        main_layout.addWidget(value_edit, 1)  # Give value field more space
        
        # ===== ADD DYNAMIC XPATH BUTTON (Web mode only) =====
        current_mode = getattr(self, 'current_automation_mode', 'web')
        if current_mode == 'web':
            dynamic_xpath_btn = QPushButton()
            dynamic_xpath_btn.setFixedSize(32, 32)
            dynamic_xpath_btn.setToolTip("Apply dynamic XPath pattern")
            dynamic_xpath_btn.setCursor(Qt.PointingHandCursor)
            
            # SVG Icon for dynamic XPath
            svg_data = b'''<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="#fbf9f9" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="lucide lucide-trending-up-down-icon lucide-trending-up-down"><path d="M14.828 14.828 21 21"/><path d="M21 16v5h-5"/><path d="m21 3-9 9-4-4-6 6"/><path d="M21 8V3h-5"/></svg>'''
            from PyQt5.QtSvg import QSvgRenderer
            from PyQt5.QtCore import QByteArray
            
            renderer = QSvgRenderer(QByteArray(svg_data))
            pixmap = QPixmap(24, 24)
            pixmap.fill(Qt.transparent)
            painter = QPainter(pixmap)
            renderer.render(painter)
            painter.end()
            
            dynamic_xpath_btn.setIcon(QIcon(pixmap))
            dynamic_xpath_btn.setIconSize(QSize(18, 18))
            dynamic_xpath_btn.setStyleSheet("""
                QPushButton {
                    background-color: transparent;
                    border: 1px solid #555555;
                    border-radius: 16px;
                    padding: 4px;
                }
                QPushButton:hover {
                    background-color: rgba(255, 255, 255, 0.1);
                    border-color: #17a2b8;
                }
                QPushButton:pressed {
                    background-color: rgba(255, 255, 255, 0.2);
                    border-color: #4CAF50;
                }
            """)
            
            # Connect button to dynamic XPath dialog
            dynamic_xpath_btn.clicked.connect(lambda checked, k=xpath, v=str(info): self.show_dynamic_xpath_dialog(k, v))
            main_layout.addWidget(dynamic_xpath_btn)
        
        # Add bottom border to widget for separation
        widget.setStyleSheet("""
            QWidget {
                border-bottom: 1px solid #333333;
                margin-bottom: 4px;
                padding-bottom: 4px;
            }
        """)
        
        return widget
    
    def clear_xpath_value(self, xpath, info, widget):
        """
        Ask confirmation before clearing the XPath value.
        If user confirms, clear it and show info message.
        If user cancels, do nothing.
        """
       
        # --- Step 1: Ask for confirmation ---
        reply = QMessageBox.question(
            self,
            "Confirm Clear",
            f"Are you sure you want to clear the value for '{xpath}'?\n\n"
            "This will reset it to 'Not_Assigned'.",
            QMessageBox.Ok | QMessageBox.Cancel,
            QMessageBox.Cancel
        )
 
        # If user clicks Cancel, exit function
        if reply != QMessageBox.Ok:
            print(f"❎ Clear action cancelled for '{xpath}'")
            return
 
        # --- Step 2: Proceed with clearing ---
        self.code_tab_xpath_data[xpath] = "Not_assigned"
        self.code_tab_original_xpath_data[xpath] = "Not_assigned"
 
        # Save immediately
        self.save_code_tab_xpath_data()
        print(f"🗑️ Cleared XPath value for '{xpath}', set to 'Not_assigned'")
       
        proj_id = self.selected_project_id
        task_id=self.selected_task_id
        fol_path=f"proj_{proj_id}/task_{task_id}"
        try:
            py_file_path = os.path.join(fol_path, f"{xpath}.py")
            if os.path.exists(py_file_path):
                os.remove(py_file_path)        
        except Exception as e:
            print(f"Error deleting file for '{xpath}': {e}")
 
        # Update the QLineEdit in the widget
        for i in range(widget.layout().count()):
            child = widget.layout().itemAt(i).widget()
            if isinstance(child, QLineEdit):
                child.setText("Not_assigned")
                child.setPlaceholderText("Enter XPath value...")
                child.setStyleSheet(child.styleSheet() + """
                    QLineEdit {
                        border-color: #ff6b6b;
                        background-color: rgba(255, 107, 107, 0.1);
                    }
                """)
                break
 
        # # --- Step 3: Show info popup after clearing ---
        # QMessageBox.information(
        #     self,
        #     "XPath Cleared",
        #     f"XPath '{xpath}' has been cleared successfully."
        # )
    
    def show_code_tab_xpath_context_menu(self, pos, xpath, value_edit):
        """Show context menu for XPath entry with delete option in Code tab"""
        context_menu = QMenu(self)
        context_menu.setStyleSheet("""
            QMenu {
                background-color: #404040;
                border: 1px solid #666666;
                border-radius: 6px;
                padding: 4px;
            }
            QMenu::item {
                background-color: transparent;
                color: white;
                padding: 8px 16px;
                border-radius: 4px;
            }
            QMenu::item:selected {
                background-color: #f44336;
                color: white;
            }
        """)
        
        # Delete action
        delete_action = context_menu.addAction("🗑️ Delete XPath Entry")
        delete_action.triggered.connect(lambda: self.delete_code_tab_xpath_entry(xpath))
        
        # Show context menu at cursor position
        global_pos = value_edit.mapToGlobal(pos)
        context_menu.exec_(global_pos)
    
    def delete_code_tab_xpath_entry(self, xpath):
        """Delete XPath entry from data and refresh display in Code tab"""
        if xpath in self.code_tab_xpath_data:
            del self.code_tab_xpath_data[xpath]
            if hasattr(self, 'code_tab_original_xpath_data') and xpath in self.code_tab_original_xpath_data:
                del self.code_tab_original_xpath_data[xpath]
            self.save_code_tab_xpath_data()
            self.filter_code_tab_xpath_entries()  # Refresh display
            print(f"🗑️ Code Tab: Deleted XPath entry: {xpath}")

def create_web_automation_app():
    """Create and return AutomationApp instance for embedding"""
    return AutomationApp()

def main():
    """Main function for standalone execution"""
   
    os.environ["QT_ENABLE_HIGHDPI_SCALING"] = "0"
    os.environ["QT_AUTO_SCREEN_SCALE_FACTOR"] = "0" 
    os.environ["QT_DEVICE_PIXEL_RATIO"] = "1"
    os.environ["QT_SCALE_FACTOR"] = "1"
    os.environ["QT_SCREEN_SCALE_FACTORS"] = "1"
    os.environ["QT_DPI_OVERRIDE"] = "96"

    app = QApplication(sys.argv)  
    # Force disable all DPI-related features
    app.setAttribute(Qt.AA_EnableHighDpiScaling, False)
    app.setAttribute(Qt.AA_UseHighDpiPixmaps, False)
    app.setAttribute(Qt.AA_DisableHighDpiScaling, True)
    
    # Force application DPI to 96 (100% scaling)
    app.setProperty("AA_Use96Dpi", True)
    
    app.setApplicationName("Advanced Web Automation Studio")
    app.setApplicationVersion("3.0")
    app.setOrganizationName("Automation Solutions") 
    app.setApplicationName("Advanced Web Automation Studio")
    app.setApplicationVersion("3.0")
    app.setOrganizationName("Automation Solutions")
    
def main_login_page(username, userid, refreshtoken, accesstoken):
    print(username, userid)
    json_path=resource_path("json_info/json_xpath.json")
    chat_path=resource_path("json_info/chat_history.json")
    exception_path=resource_path("json_info/exception_info.json")
    execute_code_path=resource_path("code_py/execute_code.py")
    files_to_remove = [json_path, chat_path, exception_path, execute_code_path]
    for file_path in files_to_remove:
        if os.path.exists(file_path):
            os.remove(file_path)
            print(f"Removed: {file_path}")
        else:
            print(f"Not found: {file_path}")
    os.environ["QT_ENABLE_HIGHDPI_SCALING"] = "0"
    os.environ["QT_AUTO_SCREEN_SCALE_FACTOR"] = "0" 
    os.environ["QT_DEVICE_PIXEL_RATIO"] = "1"
    os.environ["QT_SCALE_FACTOR"] = "1"
    os.environ["QT_SCREEN_SCALE_FACTORS"] = "1"
    os.environ["QT_DPI_OVERRIDE"] = "96"
    window = AutomationApp(username=username, userid=userid, refreshtoken=refreshtoken, accesstoken= accesstoken)
    window.show()

# username='kishore'
# userid=6
# access='eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ0b2tlbl90eXBlIjoiYWNjZXNzIiwiZXhwIjoxNzU3NjQxNDg3LCJpYXQiOjE3NTc2Mzc4ODcsImp0aSI6IjM2ZjE1OWExY2I2NjRjMzg5YjA2NzQ3ZmJiMDFiNmY2IiwidXNlcl9pZCI6IjYifQ.t_v-wMOsZ3Psw8hpRSfiMPIRah3_PgqoZDeyznSRDOQ'
# refreshtoken='eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ0b2tlbl90eXBlIjoicmVmcmVzaCIsImV4cCI6MTc1NzcyNDI4NywiaWF0IjoxNzU3NjM3ODg3LCJqdGkiOiJmY2IzMzcwNmIzZDQ0M2MzOTIyYjVkYjg2NThlODkyMSIsInVzZXJfaWQiOiI2In0.yuivHS-PXBj0beigo1qJatvtzNym5sdf8AXpiNgXulA'
    """Refresh XPath data from JSON file for Code tab"""
    import json
    import os
    
    json_path = "json_info/json_xpath.json"
    self.code_tab_xpath_data = {}
    
    if os.path.exists(json_path):
        try:
            with open(json_path, "r", encoding="utf-8") as f:
                self.code_tab_xpath_data = json.load(f)
            # print(f"🔧 Code Tab: Loaded {len(self.code_tab_xpath_data)} {data_type} entries")
        except Exception as e:
            print(f"❌ Code Tab: Error loading JSON: {e}")
            self.code_tab_xpath_data = {}
    
    # Store original data for filtering/sorting
    self.code_tab_original_xpath_data = self.code_tab_xpath_data.copy()
    self.code_tab_filtered_xpath_data = self.code_tab_xpath_data.copy()
    
    self.update_code_tab_xpath_display()
    
    def save_code_tab_xpath_data(self):
        """Save XPath data to JSON file in real-time for Code tab"""
        import json
        import os
        
        # Determine which JSON file to save based on current automation mode
        current_mode = getattr(self, 'current_automation_mode', 'web')

        if current_mode == 'desktop':
            json_path = "json_info/json_attr.json"
            data_type = "Attributes"
        elif current_mode == 'citrix':
            json_path = "json_info/citrix_data.json"
            data_type = "Citrix Data"
        else:
            json_path = "json_info/json_xpath.json"
            data_type = "XPath"
        
        try:
            # Ensure directory exists
            os.makedirs("json_info", exist_ok=True)
            
            # Save the data
            with open(json_path, "w", encoding="utf-8") as f:
                json.dump(self.code_tab_xpath_data, f, indent=4, ensure_ascii=False)
            print(f"💾 Code Tab: Saved {data_type} data to {json_path}")
            
            # Also update the draggable chat panel if it exists
            if hasattr(self, 'chat_panel') and self.chat_panel:
                self.chat_panel.refresh_xpath_data()
            
        except Exception as e:
            print(f"❌ Code Tab: Error saving {data_type} JSON: {e}")
    
    def filter_code_tab_xpath_entries(self):
        """Filter XPath entries based on search text and filter combo for Code tab"""
        search_text = self.code_tab_xpath_search.text().lower()
        filter_option = self.code_tab_filter_combo.currentText()
        
        # Start with original data
        filtered_data = {}
        
        for key, value in self.code_tab_original_xpath_data.items():
            # Apply search filter
            if search_text:
                if (search_text not in key.lower() and 
                    search_text not in str(value).lower()):
                    continue
            
            # Apply dropdown filter
            if filter_option == "Show Not_assigned Only":
                if str(value).lower() != "not_assigned":
                    continue
            elif filter_option == "Show Assigned Only":
                if str(value).lower() == "not_assigned":
                    continue
            # "Show All" - no additional filtering
            
            filtered_data[key] = value
        
        self.code_tab_filtered_xpath_data = filtered_data
        self.sort_code_tab_xpath_entries()
    
    def sort_code_tab_xpath_entries(self):
        """Sort XPath entries based on sort combo selection for Code tab"""
        sort_option = self.code_tab_sort_combo.currentText()
        
        if sort_option == "Sort by Keys A-Z":
            sorted_items = sorted(self.code_tab_filtered_xpath_data.items(), key=lambda x: x[0].lower())
        elif sort_option == "Sort by Keys Z-A":
            sorted_items = sorted(self.code_tab_filtered_xpath_data.items(), key=lambda x: x[0].lower(), reverse=True)
        elif sort_option == "Sort by Values A-Z":
            sorted_items = sorted(self.code_tab_filtered_xpath_data.items(), key=lambda x: str(x[1]).lower())
        elif sort_option == "Sort by Values Z-A":
            sorted_items = sorted(self.code_tab_filtered_xpath_data.items(), key=lambda x: str(x[1]).lower(), reverse=True)
        else:
            sorted_items = list(self.code_tab_filtered_xpath_data.items())
        
        # Convert back to dict maintaining order
        self.code_tab_filtered_xpath_data = dict(sorted_items)
        self.update_code_tab_xpath_display()
    
    def update_code_tab_xpath_display(self):
        """Update the XPath display with filtered and sorted data for Code tab"""
        data_to_display = getattr(self, 'code_tab_filtered_xpath_data', self.code_tab_xpath_data)
        print(f"🔄 Code Tab: update_xpath_display called with {len(data_to_display)} filtered XPath entries")
 
        # ✅ Properly clear only existing XPath widgets (keep the bottom spacer/stretch)
        count_before = self.code_tab_xpath_list_layout.count()
        for i in reversed(range(count_before - 1)):  # keep last spacer
            item = self.code_tab_xpath_list_layout.itemAt(i)
            widget = item.widget()
            if widget:
                widget.deleteLater()  # safely delete from memory
            else:
                self.code_tab_xpath_list_layout.removeItem(item)
 
        # === Handle no data case ===
        if not data_to_display:
            total_count = len(getattr(self, 'code_tab_original_xpath_data', {}))
            if total_count > 0:
                self.code_tab_xpath_status_label.setText(f"No entries match current filter (Total: {total_count})")
            else:
                self.code_tab_xpath_status_label.setText("No XPath data available")
            return
 
        # === Update count label ===
        count = len(data_to_display)
        total_count = len(getattr(self, 'code_tab_original_xpath_data', data_to_display))
        current_mode = getattr(self, 'current_automation_mode', 'web')
        data_type = "Attributes" if current_mode == 'desktop' else "XPath"

        if count == total_count:
            self.code_tab_xpath_status_label.setText(f"{count} {data_type} entry{'ies' if count != 1 else ''} available")
        else:
            self.code_tab_xpath_status_label.setText(f"Showing {count} of {total_count} {data_type} entries")
 
        # === Recreate XPath entry widgets (keep original layout structure) ===
        for xpath, info in data_to_display.items():
            xpath_widget = self.create_code_tab_editable_xpath_widget(xpath, info)
            # 🔸 Insert before final stretch item (preserves spacing)
            self.code_tab_xpath_list_layout.insertWidget(
                self.code_tab_xpath_list_layout.count() - 1,
                xpath_widget
            )
 
        print(f"📊 Code Tab: Updated XPath display with {count} entries")
    
    def create_code_tab_editable_xpath_widget(self, xpath, info):
        """Create an editable widget for a single XPath entry in Code tab"""
        widget = QWidget()
        main_layout = QHBoxLayout(widget)
        main_layout.setContentsMargins(12, 6, 12, 6)
        main_layout.setSpacing(8)
        
        # Left side - XPath key label (non-editable) with fixed width for alignment
        xpath_label = QLabel(f"{xpath}:")
        xpath_label.setStyleSheet("""
            QLabel {
                color: #ffffff;
                font-weight: 600;
                font-size: 13px;
                padding: 6px 8px;
                background-color: rgba(255, 255, 255, 0.05);
                border-radius: 4px;
                border-left: 3px solid #17a2b8;
            }
        """)
        xpath_label.setWordWrap(True)
        xpath_label.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        xpath_label.setFixedWidth(180)  # Fixed width for alignment
        main_layout.addWidget(xpath_label)
        
        # Right side - Editable value field
        value_edit = QLineEdit(str(info))
        value_edit.setStyleSheet("""
            QLineEdit {
                background-color: #2d2d30;
                border: 1px solid #555555;
                border-radius: 6px;
                padding: 8px 12px;
                color: white;
                font-size: 12px;
                font-family: 'Consolas', 'Monaco', monospace;
                min-height: 18px;
            }
            QLineEdit:focus {
                border-color: #4CAF50;
                background-color: #353538;
            }
            QLineEdit:hover {
                border-color: #17a2b8;
                background-color: #353538;
            }
        """)
        
        # Add context menu for delete option
        value_edit.setContextMenuPolicy(Qt.CustomContextMenu)
        value_edit.customContextMenuRequested.connect(lambda pos: self.show_code_tab_xpath_context_menu(pos, xpath, value_edit))
        
        # Set placeholder and styling based on value
        if str(info).lower() == "not_assigned":
            value_edit.setPlaceholderText("Enter XPath value...")
            value_edit.setStyleSheet(value_edit.styleSheet() + """
                QLineEdit {
                    border-color: #ff6b6b;
                    background-color: rgba(255, 107, 107, 0.1);
                }
            """)
        
        # Connect real-time saving
        def on_value_changed():
            new_value = value_edit.text().strip()
            if new_value != str(info):
                # Update the data
                self.code_tab_xpath_data[xpath] = new_value
                self.code_tab_original_xpath_data[xpath] = new_value
                
                # Save to JSON file immediately
                self.save_code_tab_xpath_data()
                
                # Update styling based on new value
                if new_value.lower() == "not_assigned" or not new_value:
                    value_edit.setStyleSheet("""
                        QLineEdit {
                            background-color: #2d2d30;
                            border: 1px solid #ff6b6b;
                            border-radius: 6px;
                            padding: 8px 12px;
                            color: white;
                            font-size: 12px;
                            font-family: 'Consolas', 'Monaco', monospace;
                            background-color: rgba(255, 107, 107, 0.1);
                            min-height: 18px;
                        }
                        QLineEdit:focus {
                            border-color: #ff6b6b;
                            background-color: rgba(255, 107, 107, 0.15);
                        }
                    """)
                else:
                    value_edit.setStyleSheet("""
                        QLineEdit {
                            background-color: #2d2d30;
                            border: 1px solid #4CAF50;
                            border-radius: 6px;
                            padding: 8px 12px;
                            color: white;
                            font-size: 12px;
                            font-family: 'Consolas', 'Monaco', monospace;
                            background-color: rgba(76, 175, 80, 0.1);
                            min-height: 18px;
                        }
                        QLineEdit:focus {
                            border-color: #4CAF50;
                            background-color: rgba(76, 175, 80, 0.15);
                        }
                    """)
                
                print(f"💾 Code Tab: Updated XPath '{xpath}' = '{new_value}'")
        
        value_edit.textChanged.connect(on_value_changed)
        value_edit.editingFinished.connect(on_value_changed)
        
        main_layout.addWidget(value_edit, 1)  # Give value field more space
        
        # Add bottom border to widget for separation
        widget.setStyleSheet("""
            QWidget {
                border-bottom: 1px solid #333333;
                margin-bottom: 4px;
                padding-bottom: 4px;
            }
        """)
        
        return widget
    
    def show_code_tab_xpath_context_menu(self, pos, xpath, value_edit):
        """Show context menu for XPath entry with delete option in Code tab"""
        context_menu = QMenu(self)
        context_menu.setStyleSheet("""
            QMenu {
                background-color: #404040;
                border: 1px solid #666666;
                border-radius: 6px;
                padding: 4px;
            }
            QMenu::item {
                background-color: transparent;
                color: white;
                padding: 8px 16px;
                border-radius: 4px;
            }
            QMenu::item:selected {
                background-color: #f44336;
                color: white;
            }
        """)
        
        # Delete action
        delete_action = context_menu.addAction("🗑️ Delete XPath Entry")
        delete_action.triggered.connect(lambda: self.delete_code_tab_xpath_entry(xpath))
        
        # Show context menu at cursor position
        global_pos = value_edit.mapToGlobal(pos)
        context_menu.exec_(global_pos)
    
    def delete_code_tab_xpath_entry(self, xpath):
        """Delete XPath entry from data and refresh display in Code tab"""
        if xpath in self.code_tab_xpath_data:
            del self.code_tab_xpath_data[xpath]
            if hasattr(self, 'code_tab_original_xpath_data') and xpath in self.code_tab_original_xpath_data:
                del self.code_tab_original_xpath_data[xpath]
            self.save_code_tab_xpath_data()
            self.filter_code_tab_xpath_entries()  # Refresh display
            print(f"🗑️ Code Tab: Deleted XPath entry: {xpath}")

def delete_files():
    import shutil
    if getattr(sys, 'frozen', False):
        # Running in normal Python (DEV mode)
        base_dir = r"C:\DroidalAgentFlow"

        # 1️⃣ Delete all .py files
        for file in os.listdir(base_dir):
            if file.endswith(".py"):
                try:
                    os.remove(os.path.join(base_dir, file))
                except Exception as e:
                    print(f"Failed to delete {file}: {e}")

        # 2️⃣ Delete folders
        folders_to_delete = ["Icon", "sound","font","gif","supporting_files","Citrix_process","desktop_process","native_process"]

        for folder in folders_to_delete:
            folder_path = os.path.join(base_dir, folder)
            if os.path.exists(folder_path):
                try:
                    shutil.rmtree(folder_path)
                except Exception as e:
                    print(f"Failed to delete {folder}: {e}")

def main_login_page(username, userid, refreshtoken, accesstoken):
    print(username, userid)
    delete_files()
    import subprocess, sys, threading
    
    print("Starting Flask server...")
    subprocess.Popen(
        [r"C:\DroidalAgentFlow\venv\Scripts\python.exe", "C:\\DroidalAgentFlow\\datas\\source_files\\agent_runner_api.py"],
        creationflags=subprocess.CREATE_NO_WINDOW,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL

        
    )
    json_path=resource_path("json_info/json_xpath.json")
    chat_path=resource_path("json_info/chat_history.json")
    exception_path=resource_path("json_info/exception_info.json")
    execute_code_path=resource_path("code_py/execute_code.py")
    desktop_json_path=resource_path("json_info/json_attr.json")
    citrix_json_path=resource_path("json_info/citrix_data.json")
    files_to_remove = [json_path, chat_path, exception_path, execute_code_path,desktop_json_path,citrix_json_path]
    for file_path in files_to_remove:
        if os.path.exists(file_path):
            os.remove(file_path)
            print(f"Removed: {file_path}")
        else:
            print(f"Not found: {file_path}")
    os.environ["QT_ENABLE_HIGHDPI_SCALING"] = "0"
    os.environ["QT_AUTO_SCREEN_SCALE_FACTOR"] = "0" 
    os.environ["QT_DEVICE_PIXEL_RATIO"] = "1"
    os.environ["QT_SCALE_FACTOR"] = "1"
    os.environ["QT_SCREEN_SCALE_FACTORS"] = "1"
    os.environ["QT_DPI_OVERRIDE"] = "96"
    window = AutomationApp(username=username, userid=userid, refreshtoken=refreshtoken, accesstoken= accesstoken)
    window.show()

# username='kishore'
# userid=6
# access='eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ0b2tlbl90eXBlIjoiYWNjZXNzIiwiZXhwIjoxNzU3NjQxNDg3LCJpYXQiOjE3NTc2Mzc4ODcsImp0aSI6IjM2ZjE1OWExY2I2NjRjMzg5YjA2NzQ3ZmJiMDFiNmY2IiwidXNlcl9pZCI6IjYifQ.t_v-wMOsZ3Psw8hpRSfiMPIRah3_PgqoZDeyznSRDOQ'
# refreshtoken='eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ0b2tlbl90eXBlIjoicmVmcmVzaCIsImV4cCI6MTc1NzcyNDI4NywiaWF0IjoxNzU3NjM3ODg3LCJqdGkiOiJmY2IzMzcwNmIzZDQ0M2MzOTIyYjVkYjg2NThlODkyMSIsInVzZXJfaWQiOiI2In0.yuivHS-PXBj0beigo1qJatvtzNym5sdf8AXpiNgXulA'

# test(username,userid,refreshtoken,access)zcyNDI4NywiaWF0IjoxNzU3NjM3ODg3LCJqdGkiOiJmY2IzMzcwNmIzZDQ0M2MzOTIyYjVkYjg2NThlODkyMSIsInVzZXJfaWQiOiI2In0.yuivHS-PXBj0beigo1qJatvtzNym5sdf8AXpiNgXulA'

# test(username,userid,refreshtoken,access)