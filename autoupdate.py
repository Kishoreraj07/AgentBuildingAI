import os
import sys
import requests
import subprocess
import zipfile
import shutil
import logging
from pathlib import Path
from datetime import datetime
from packaging import version
from PyQt5.QtWidgets import (QApplication, QDialog, QVBoxLayout, QHBoxLayout, 
                             QLabel, QPushButton, QWidget)
from PyQt5.QtCore import Qt, QThread, pyqtSignal, QTimer
from PyQt5.QtGui import QIcon

# Configuration
MAIN_URL = "https://dev-cloud.droidal.com"
REMOTE_VERSION_URL = f"{MAIN_URL}/app/version/droidal/ABA/"
API_FILES_URL = f"{MAIN_URL}/app/version/list_file"
ICON_PATH = "icon_3.ico"
INSTALL_DIR = Path(r"C:\DroidalAgentFlow")
VENV_PYTHON = INSTALL_DIR / "venv" / "Scripts" / "python.exe"
LOG_DIR = INSTALL_DIR / "logs"
LOG_FILE = LOG_DIR / f"updater_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"

# Setup logging
def setup_logging():
    """Initialize logging system"""
    try:
        LOG_DIR.mkdir(parents=True, exist_ok=True)
        
        # Configure logging
        logging.basicConfig(
            level=logging.DEBUG,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(LOG_FILE, encoding='utf-8'),
                logging.StreamHandler(sys.stdout)
            ]
        )
        
        # Clean old logs (keep last 10)
        log_files = sorted(LOG_DIR.glob("updater_*.log"))
        if len(log_files) > 10:
            for old_log in log_files[:-10]:
                try:
                    old_log.unlink()
                except:
                    pass
        
        logging.info("="*70)
        logging.info("Agent Flow Updater Started")
        logging.info(f"Log file: {LOG_FILE}")
        logging.info(f"Python version: {sys.version}")
        logging.info(f"Install directory: {INSTALL_DIR}")
        logging.info("="*70)
        
    except Exception as e:
        print(f"Failed to setup logging: {e}")

# Initialize logging
setup_logging()


class UpdateWorker(QThread):
    """Background worker for update process"""
    progress_changed = pyqtSignal(int, str)  # progress, message
    stage_changed = pyqtSignal(str)  # stage name
    error_occurred = pyqtSignal(str)  # error message
    completed = pyqtSignal()
    
    def __init__(self, download_urls, latest_version):
        super().__init__()
        self.download_urls = download_urls if isinstance(download_urls, list) else [download_urls]
        self.latest_version = latest_version
        self.should_cancel = False
        
    def run(self):
        try:
            logging.info("Update worker started")
            logging.info(f"Download URLs: {self.download_urls}")
            logging.info(f"Target version: {self.latest_version}")
            
            total_files = len([url for url in self.download_urls 
                             if not os.path.basename(url).lower() == "update202.exe"])
            logging.info(f"Total files to download: {total_files}")
            current_file = 0
            
            # Stage 1: Download files
            logging.info("Stage 1: Starting file downloads")
            self.stage_changed.emit("Downloading updates...")
            for download_url in self.download_urls:
                if self.should_cancel:
                    logging.warning("Update canceled by user")
                    return
                    
                file_name = os.path.basename(download_url)
                if file_name.lower() == "update202.exe":
                    logging.info(f"Skipping {file_name}")
                    continue
                
                current_file += 1
                base_progress = int((current_file - 1) / total_files * 40)
                
                logging.info(f"Downloading file {current_file}/{total_files}: {file_name}")
                if not self._download_file(download_url, file_name, base_progress):
                    logging.error(f"Failed to download {file_name}")
                    return
                logging.info(f"Successfully downloaded {file_name}")
            
            # Stage 2: Extract archives
            logging.info("Stage 2: Starting archive extraction")
            self.stage_changed.emit("Extracting files...")
            self.progress_changed.emit(40, "Extracting downloaded files...")
            if not self._extract_archives():
                logging.error("Archive extraction failed")
                return
            self.progress_changed.emit(60, "Extraction complete")
            logging.info("Archive extraction completed successfully")
            
            # Stage 3: Install dependencies
            logging.info("Stage 3: Starting dependency installation")
            self.stage_changed.emit("Installing dependencies...")
            self.progress_changed.emit(65, "Checking Python packages...")
            if not self._install_dependencies():
                logging.error("Dependency installation failed")
                return
            self.progress_changed.emit(85, "Dependencies installed")
            logging.info("Dependency installation completed")
            
            # Stage 4: Run installer
            logging.info("Stage 4: Starting installer")
            self.stage_changed.emit("Finalizing installation...")
            self.progress_changed.emit(90, "Running installer...")
            if not self._run_installer():
                logging.error("Installer execution failed")
                return
            logging.info("Installer executed successfully")
            
            # Stage 5: Update version file
            logging.info("Stage 5: Updating version file")
            self.progress_changed.emit(95, "Updating version info...")
            self._update_version_file()
            
            self.progress_changed.emit(100, "Update complete!")
            logging.info("="*70)
            logging.info("UPDATE COMPLETED SUCCESSFULLY")
            logging.info("="*70)
            QThread.msleep(500)
            self.completed.emit()
            
        except Exception as e:
            logging.exception(f"Critical error in update process: {str(e)}")
            self.error_occurred.emit(f"Update failed: {str(e)}")
    
    def _download_file(self, url, file_name, base_progress):
        try:
            logging.info(f"Starting download: {url}")

            temp_file = INSTALL_DIR / file_name

            # ✅ FIX: do NOT stream small text files
            if file_name.lower().endswith(".txt"):
                logging.info("Detected text file, downloading without streaming")

                r = requests.get(url, timeout=10)
                r.raise_for_status()

                temp_file.write_bytes(r.content)

                self.progress_changed.emit(
                    base_progress + 40,
                    f"Downloaded {file_name}"
                )

                logging.info(f"Downloaded text file: {file_name}")
                return True

            # ⬇️ EXISTING streaming logic for big files
            with requests.get(url, stream=True, timeout=30) as r:
                r.raise_for_status()

                total_length = int(r.headers.get('content-length', 0))
                downloaded = 0

                with open(temp_file, "wb") as f:
                    for chunk in r.iter_content(chunk_size=8192):
                        if self.should_cancel:
                            return False
                        if chunk:
                            f.write(chunk)
                            downloaded += len(chunk)

                return True

        except Exception as e:
            logging.exception(f"Download failed: {file_name}")
            self.error_occurred.emit(str(e))
            return False
    
    def _extract_archives(self):
        """Extract all ZIP files"""
        try:
            zip_files = list(INSTALL_DIR.glob("*.zip"))
            logging.info(f"Found {len(zip_files)} ZIP files to extract")
            
            if not zip_files:
                logging.info("No ZIP files to extract")
                return True
                
            for i, zip_file in enumerate(zip_files):
                if self.should_cancel:
                    logging.warning("Extraction canceled by user")
                    return False
                    
                progress = 40 + int((i / len(zip_files)) * 20)
                self.progress_changed.emit(progress, f"Extracting {zip_file.name}...")
                logging.info(f"Extracting {zip_file.name} to {INSTALL_DIR}")
                
                try:
                    with zipfile.ZipFile(zip_file, 'r') as zip_ref:
                        # Log contents
                        file_list = zip_ref.namelist()
                        logging.info(f"ZIP contains {len(file_list)} files")
                        
                        zip_ref.extractall(INSTALL_DIR)
                    
                    logging.info(f"Successfully extracted {zip_file.name}")
                    zip_file.unlink()
                    logging.info(f"Deleted ZIP file: {zip_file.name}")
                    
                except zipfile.BadZipFile as e:
                    logging.error(f"Corrupt ZIP file {zip_file.name}: {e}")
                    self.error_occurred.emit(f"Corrupt ZIP file: {zip_file.name}")
                    return False
            
            logging.info("All archives extracted successfully")
            return True
            
        except Exception as e:
            logging.exception(f"Extraction failed")
            self.error_occurred.emit(f"Extraction failed: {str(e)}")
            return False
    
    def _install_dependencies(self):
        """Install Python requirements"""
        requirements_path = INSTALL_DIR / "requirements.txt"
        
        logging.info(f"Checking requirements file: {requirements_path}")
        
        if not requirements_path.exists():
            logging.info("No requirements.txt found, skipping dependency installation")
            self.progress_changed.emit(85, "No requirements file found, skipping...")
            return True
        
        logging.info(f"Checking virtual environment: {VENV_PYTHON}")
        if not VENV_PYTHON.exists():
            logging.error(f"Virtual environment Python not found at {VENV_PYTHON}")
            self.error_occurred.emit(f"Virtual environment missing: {VENV_PYTHON}")
            return False
        
        try:
            # Log requirements content
            with open(requirements_path, 'r') as f:
                req_content = f.read()
                logging.info(f"Requirements content:\n{req_content}")
            
            self.progress_changed.emit(70, "Upgrading pip...")
            logging.info("Attempting to upgrade pip")
            
            # First, upgrade pip itself (don't fail if this doesn't work)
            try:
                pip_upgrade_cmd = [str(VENV_PYTHON), "-m", "pip", "install", "--upgrade", "pip", "--no-warn-script-location"]
                logging.info(f"Running command: {' '.join(pip_upgrade_cmd)}")
                
                result = subprocess.run(
                    pip_upgrade_cmd, 
                    cwd=str(INSTALL_DIR),
                    creationflags=subprocess.CREATE_NO_WINDOW,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    timeout=60,
                    check=False,
                    universal_newlines=True
                )
                
                logging.info(f"Pip upgrade return code: {result.returncode}")
                if result.stdout:
                    logging.info(f"Pip upgrade stdout:\n{result.stdout}")
                if result.stderr:
                    logging.warning(f"Pip upgrade stderr:\n{result.stderr}")
                    
            except Exception as e:
                logging.warning(f"Pip upgrade failed (continuing anyway): {e}")
            
            self.progress_changed.emit(75, "Installing Python packages...")
            logging.info("Starting requirements installation")
            
            # Install requirements with detailed output
            cmd = [
                str(VENV_PYTHON), 
                "-m", "pip", "install", 
                "-r", str(requirements_path),
                "--upgrade",
                "--no-cache-dir",
                "--no-warn-script-location"
            ]
            
            logging.info(f"Running command: {' '.join(cmd)}")
            
            process = subprocess.Popen(
                cmd,
                cwd=str(INSTALL_DIR),
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                creationflags=subprocess.CREATE_NO_WINDOW,
                universal_newlines=True,
                bufsize=1
            )
            
            # Read output line by line for progress updates
            output_lines = []
            package_name = ""
            
            for line in process.stdout:
                if self.should_cancel:
                    logging.warning("Installation canceled by user")
                    process.terminate()
                    return False
                
                output_lines.append(line)
                logging.debug(f"Pip output: {line.strip()}")
                line_lower = line.lower()
                
                # Extract package name from various pip output formats
                if "collecting" in line_lower or "downloading" in line_lower:
                    parts = line.strip().split()
                    if len(parts) > 1:
                        package_name = parts[1].split("==")[0].split(">")[0].split("<")[0]
                        self.progress_changed.emit(78, f"Downloading {package_name}...")
                        logging.info(f"Downloading package: {package_name}")
                elif "installing collected packages:" in line_lower:
                    packages = line.split(":")[-1].strip()
                    self.progress_changed.emit(82, f"Installing {packages}...")
                    logging.info(f"Installing packages: {packages}")
                elif "successfully installed" in line_lower:
                    self.progress_changed.emit(84, "Installation completed")
                    logging.info(f"Successfully installed: {line.strip()}")
            
            return_code = process.wait(timeout=300)  # 5 minute timeout
            
            logging.info(f"Pip install return code: {return_code}")
            
            # Log full output
            full_output = "".join(output_lines)
            logging.info(f"Full pip output:\n{full_output}")
            
            if return_code == 0:
                self.progress_changed.emit(85, "All packages installed successfully")
                logging.info("All packages installed successfully")
                return True
            else:
                # Log error details
                logging.warning(f"Pip install returned non-zero code: {return_code}")
                logging.warning(f"Last 20 lines of output:\n{''.join(output_lines[-20:])}")
                
                # Continue anyway - partial installation is better than nothing
                self.progress_changed.emit(85, "Installation completed with warnings")
                logging.warning("Continuing despite installation warnings")
                return True
            
        except subprocess.TimeoutExpired:
            logging.error("Pip installation timeout (300 seconds)")
            self.progress_changed.emit(85, "Installation timeout, continuing...")
            return True
        except FileNotFoundError:
            logging.error(f"Python executable not found: {VENV_PYTHON}")
            self.error_occurred.emit(f"Python executable not found: {VENV_PYTHON}")
            return False
        except Exception as e:
            # Log error but continue - don't let dependency issues block the update
            logging.exception(f"Dependency installation error")
            self.progress_changed.emit(85, "Continuing despite installation issues...")
            return True
    
    def _run_installer(self):
        """Run the installer executable"""
        try:
            installer = INSTALL_DIR / "AgentFlow.exe"
            logging.info(f"Looking for installer at: {installer}")
            
            if installer.exists():
                logging.info(f"Installer found, size: {installer.stat().st_size} bytes")
                cmd = [str(installer), "/VERYSILENT", "/NORESTART"]
                logging.info(f"Running installer: {' '.join(cmd)}")
                
                process = subprocess.Popen(
                    cmd,
                    creationflags=subprocess.CREATE_NO_WINDOW,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE
                )
                
                logging.info(f"Installer process started with PID: {process.pid}")
            else:
                logging.warning(f"Installer not found at {installer}, skipping")
            
            return True
            
        except Exception as e:
            logging.exception("Failed to run installer")
            self.error_occurred.emit(f"Installer failed: {str(e)}")
            return False
    
    def _update_version_file(self):
        """Update the version file"""
        try:
            version_path = Path(sys.executable).parent / "version.txt"
            logging.info(f"Updating version file at: {version_path}")
            logging.info(f"New version: {self.latest_version}")
            
            version_path.write_text(self.latest_version)
            
            # Verify write
            written_version = version_path.read_text().strip()
            logging.info(f"Version file updated and verified: {written_version}")
            
        except Exception as e:
            logging.warning(f"Failed to update version.txt: {e}")
            # Don't fail the update for this
    
    def cancel(self):
        """Cancel the update process"""
        self.should_cancel = True


class CustomMessageBox(QDialog):
    """Custom styled message box"""
    
    def __init__(self, parent=None, title="", message="", buttons=None, icon_type="info"):
        super().__init__(parent)
        if buttons is None:
            buttons = ["OK"]
        self.result_value = None
        self.setup_ui(title, message, buttons, icon_type)
        
    def setup_ui(self, title, message, buttons, icon_type):
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setFixedSize(500, 250)
        self.setModal(True)
        
        container = QWidget(self)
        container.setGeometry(0, 0, 500, 250)
        container.setStyleSheet("""
            QWidget {
                background-color: #414141;
                border-radius: 15px;
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
                background: #333333;
                border-radius: 20px 20px 0px 0px;
            }
        """)
        
        title_layout = QHBoxLayout(title_container)
        title_layout.setContentsMargins(25, 15, 25, 15)
        
        icon_map = {"info": "ℹ️", "question": "❓", "warning": "⚠️", "error": "❌"}
        icon_prefix = icon_map.get(icon_type, "")
        
        title_label = QLabel(f"{icon_prefix} {title}")
        title_label.setStyleSheet("""
            QLabel {
                color: #ffffff;
                font-family: 'Segoe UI', Arial;
                font-weight: bold;
                font-size: 16px;
                background: transparent;
            }
        """)
        title_layout.addWidget(title_label)
        title_layout.addStretch()
        
        close_btn = QPushButton("✕")
        close_btn.setFixedSize(30, 30)
        close_btn.setStyleSheet("""
            QPushButton {
                background: transparent;
                border: none;
                color: #ffffff;
                font-size: 20px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: rgba(255, 255, 255, 0.1);
                border-radius: 15px;
            }
        """)
        close_btn.clicked.connect(self.reject)
        title_layout.addWidget(close_btn)
        
        layout.addWidget(title_container)
        layout.addSpacing(40)
        
        # Message
        msg_label = QLabel(message)
        msg_label.setStyleSheet("""
            QLabel {
                color: #FFFFFF;
                font-family: 'Segoe UI', Arial;
                font-size: 14px;
                padding: 10px 40px;
            }
        """)
        msg_label.setWordWrap(True)
        msg_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(msg_label)
        
        layout.addSpacing(40)
        
        # Buttons
        btn_layout = QHBoxLayout()
        btn_layout.setContentsMargins(25, 0, 25, 0)
        btn_layout.setSpacing(15)
        btn_layout.addStretch()
        
        for btn_text in buttons:
            btn = QPushButton(btn_text)
            btn.setFixedSize(120, 40)
            
            if btn_text in ["Yes", "OK", "Update"]:
                btn.setStyleSheet("""
                    QPushButton {
                        background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1, 
                                                   stop: 0 #008AB3, stop: 1 #005B7F);
                        color: #FFFFFF;
                        border: none;
                        border-radius: 10px;
                        font-family: 'Segoe UI', Arial;
                        font-weight: 600;
                        font-size: 16px;
                    }
                    QPushButton:hover {
                        background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1, 
                                                   stop: 0 #0099CC, stop: 1 #006699);
                    }
                """)
            else:
                btn.setStyleSheet("""
                    QPushButton {
                        background: #555555;
                        color: #ffffff;
                        border: none;
                        border-radius: 10px;
                        font-family: 'Segoe UI', Arial;
                        font-weight: 600;
                        font-size: 16px;
                    }
                    QPushButton:hover {
                        background: #666666;
                    }
                """)
            
            btn.clicked.connect(lambda checked, text=btn_text: self.button_clicked(text))
            btn_layout.addWidget(btn)
        
        btn_layout.addStretch()
        layout.addLayout(btn_layout)
    
    def button_clicked(self, button_text):
        self.result_value = button_text
        self.accept()
    
    @staticmethod
    def show_info(parent=None, title="Information", message="", buttons=None):
        if buttons is None:
            buttons = ["OK"]
        dialog = CustomMessageBox(parent, title, message, buttons, "info")
        dialog.exec_()
        return dialog.result_value
    
    @staticmethod
    def show_question(parent=None, title="Question", message="", buttons=None):
        if buttons is None:
            buttons = ["Yes", "No"]
        dialog = CustomMessageBox(parent, title, message, buttons, "question")
        dialog.exec_()
        return dialog.result_value
    
    @staticmethod
    def show_warning(parent=None, title="Warning", message="", buttons=None):
        if buttons is None:
            buttons = ["OK"]
        dialog = CustomMessageBox(parent, title, message, buttons, "warning")
        dialog.exec_()
        return dialog.result_value
    
    @staticmethod
    def show_error(parent=None, title="Error", message="", buttons=None):
        if buttons is None:
            buttons = ["OK"]
        dialog = CustomMessageBox(parent, title, message, buttons, "error")
        dialog.exec_()
        return dialog.result_value


class UpdateProgressDialog(QDialog):
    """Enhanced progress dialog for complete update process"""
    
    def __init__(self, parent=None, download_urls=None, latest_version=None):
        super().__init__(parent)
        self.download_urls = download_urls
        self.latest_version = latest_version
        self.worker = None
        self.setup_ui()
        
    def setup_ui(self):
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setFixedSize(550, 280)
        self.setModal(True)
        
        container = QWidget(self)
        container.setGeometry(0, 0, 550, 280)
        container.setStyleSheet("""
            QWidget {
                background-color: #414141;
                border-radius: 15px;
            }
        """)
        
        layout = QVBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 25)
        
        # Title bar
        title_container = QWidget()
        title_container.setFixedHeight(60)
        title_container.setStyleSheet("""
            QWidget {
                background: #333333;
                border-radius: 20px 20px 0px 0px;
            }
        """)
        
        title_layout = QHBoxLayout(title_container)
        title_layout.setContentsMargins(25, 15, 25, 15)
        
        self.title_label = QLabel("🔄 Agent Flow Updater")
        self.title_label.setStyleSheet("""
            QLabel {
                color: #ffffff;
                font-family: 'Segoe UI', Arial;
                font-weight: bold;
                font-size: 16px;
                background: transparent;
            }
        """)
        title_layout.addWidget(self.title_label)
        
        layout.addWidget(title_container)
        layout.addSpacing(25)
        
        # Stage label
        self.stage_label = QLabel("Preparing update...")
        self.stage_label.setStyleSheet("""
            QLabel {
                color: #00D4FF;
                font-family: 'Segoe UI', Arial;
                font-size: 13px;
                font-weight: 600;
                padding: 0px 40px;
            }
        """)
        layout.addWidget(self.stage_label)
        
        layout.addSpacing(10)
        
        # Message
        self.message_label = QLabel("Initializing...")
        self.message_label.setStyleSheet("""
            QLabel {
                color: #CCCCCC;
                font-family: 'Segoe UI', Arial;
                font-size: 13px;
                padding: 0px 40px;
            }
        """)
        layout.addWidget(self.message_label)
        
        layout.addSpacing(15)
        
        # Progress bar container
        progress_container = QWidget()
        progress_container.setFixedHeight(30)
        progress_layout = QHBoxLayout(progress_container)
        progress_layout.setContentsMargins(40, 0, 40, 0)
        
        self.progress_widget = QWidget()
        self.progress_widget.setFixedHeight(24)
        self.progress_widget.setStyleSheet("""
            QWidget {
                background-color: #2b2b2b;
                border: 2px solid #555555;
                border-radius: 12px;
            }
        """)
        
        self.progress_bar = QWidget(self.progress_widget)
        self.progress_bar.setGeometry(2, 2, 0, 20)
        self.progress_bar.setStyleSheet("""
            QWidget {
                background: qlineargradient(x1: 0, y1: 0, x2: 1, y2: 0,
                                           stop: 0 #008AB3, stop: 1 #00D4FF);
                border-radius: 10px;
            }
        """)
        
        progress_layout.addWidget(self.progress_widget)
        layout.addWidget(progress_container)
        
        layout.addSpacing(5)
        
        # Percentage label
        self.percent_label = QLabel("0%")
        self.percent_label.setStyleSheet("""
            QLabel {
                color: #00D4FF;
                font-family: 'Segoe UI', Arial;
                font-size: 16px;
                font-weight: bold;
            }
        """)
        self.percent_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.percent_label)
        
        layout.addSpacing(15)
        
        # Cancel button
        btn_layout = QHBoxLayout()
        self.cancel_btn = QPushButton("Cancel")
        self.cancel_btn.setFixedSize(110, 38)
        self.cancel_btn.setStyleSheet("""
            QPushButton {
                background: #555555;
                color: #ffffff;
                border: none;
                border-radius: 10px;
                font-family: 'Segoe UI', Arial;
                font-size: 14px;
                font-weight: 600;
            }
            QPushButton:hover {
                background: #666666;
            }
            QPushButton:disabled {
                background: #3a3a3a;
                color: #666666;
            }
        """)
        self.cancel_btn.clicked.connect(self.cancel_update)
        btn_layout.addStretch()
        btn_layout.addWidget(self.cancel_btn)
        btn_layout.addStretch()
        layout.addLayout(btn_layout)
    
    def start_update(self):
        """Start the update process in background thread"""
        self.worker = UpdateWorker(self.download_urls, self.latest_version)
        self.worker.progress_changed.connect(self.update_progress)
        self.worker.stage_changed.connect(self.update_stage)
        self.worker.error_occurred.connect(self.handle_error)
        self.worker.completed.connect(self.handle_completion)
        self.worker.start()
    
    def update_progress(self, value, message):
        """Update progress bar and message"""
        width = int((self.progress_widget.width() - 4) * value / 100)
        self.progress_bar.setGeometry(2, 2, width, 20)
        self.percent_label.setText(f"{value}%")
        self.message_label.setText(message)
        QApplication.processEvents()
    
    def update_stage(self, stage):
        """Update current stage label"""
        self.stage_label.setText(stage)
    
    def handle_error(self, error_message):
        """Handle errors during update"""
        self.close()
        CustomMessageBox.show_error(None, "Update Failed", error_message)
    
    def handle_completion(self):
        """Handle successful completion"""
        self.cancel_btn.setEnabled(False)
        self.cancel_btn.setText("Closing...")
        QTimer.singleShot(1000, self.close_and_exit)
    
    def close_and_exit(self):
        """Close dialog and exit application"""
        self.close()
        CustomMessageBox.show_info(None, "Update Complete", 
                                   "Agent Flow has been updated successfully!")
        os._exit(0)
    
    def cancel_update(self):
        """Cancel the update process"""
        if self.worker and self.worker.isRunning():
            self.worker.cancel()
            self.worker.wait()
        CustomMessageBox.show_info(None, "Update Canceled", 
                                  "The update process has been canceled.")
        self.close()


def get_local_version():
    """Get the current installed version"""
    version_path = Path(sys.executable).parent / "version.txt"
    logging.info(f"Reading local version from: {version_path}")
    try:
        local_ver = version_path.read_text().strip()
        logging.info(f"Local version: {local_ver}")
        return local_ver
    except FileNotFoundError:
        logging.warning("version.txt not found, using default version 2.0.23")
        return "2.0.23"
    except Exception as e:
        logging.error(f"Error reading version file: {e}")
        return "2.0.23"


def get_remote_info():
    """Fetch remote version information"""
    logging.info(f"Checking for updates at: {REMOTE_VERSION_URL}")
    try:
        resp = requests.get(REMOTE_VERSION_URL, timeout=10)
        resp.raise_for_status()
        data = resp.json()
        logging.info(f"Remote version info: {data}")
        return data
    except requests.exceptions.RequestException as e:
        logging.error(f"Failed to fetch remote version: {e}")
        return None
    except Exception as e:
        logging.exception("Unexpected error fetching remote version")
        return None


def get_download_urls():
    """Fetch list of files to download"""
    logging.info(f"Fetching file list from: {API_FILES_URL}")
    try:
        response = requests.get(API_FILES_URL, timeout=10)
        response.raise_for_status()
        data = response.json()
        urls = [file_info["url"] for file_info in data.get("files", [])]
        logging.info(f"Found {len(urls)} files to download")
        for url in urls:
            logging.info(f"  - {url}")
        return urls
    except requests.exceptions.RequestException as e:
        logging.error(f"Failed to fetch file list: {e}")
        return None
    except Exception as e:
        logging.exception("Unexpected error fetching file list")
        return None


def check_for_update():
    """Main update check function"""
    logging.info("Starting update check")
    
    app = QApplication.instance() or QApplication(sys.argv)
    
    if os.path.exists(ICON_PATH):
        app.setWindowIcon(QIcon(ICON_PATH))
        logging.info(f"Application icon loaded: {ICON_PATH}")
    else:
        logging.warning(f"Application icon not found: {ICON_PATH}")
    
    # Clean up _internal folder if frozen
    if getattr(sys, 'frozen', False):
        internal_dir = Path(getattr(sys, '_MEIPASS', Path(sys.executable).parent)) / '_internal'
        logging.info(f"Running as frozen executable, checking for _internal: {internal_dir}")
        try:
            if internal_dir.exists():
                logging.info(f"Removing _internal directory: {internal_dir}")
                shutil.rmtree(internal_dir)
                logging.info("_internal directory removed")
        except Exception as e:
            logging.warning(f"Failed to remove _internal directory: {e}")
    
    # Check for updates
    local = get_local_version()
    remote = get_remote_info()
    
    if not remote:
        logging.error("Failed to get remote version info")
        CustomMessageBox.show_error(None, "Update Check Failed",
                                   "Unable to check for updates.\nPlease try again later.")
        return
    
    latest = remote["version_number"]
    logging.info(f"Version comparison - Local: {local}, Remote: {latest}")
    
    if version.parse(latest) > version.parse(local):
        logging.info(f"Update available: {local} -> {latest}")
        
        result = CustomMessageBox.show_question(
            None,
            "Update Available",
            f"A new version is available!\n\n"
            f"Current version: {local}\n"
            f"Latest version: {latest}\n\n"
            f"Would you like to update now?",
            ["Yes", "No"]
        )
        
        logging.info(f"User response to update prompt: {result}")
        
        if result == "Yes":
            urls = get_download_urls()
            if not urls:
                logging.error("Failed to get download URLs")
                CustomMessageBox.show_error(None, "Update Failed",
                                          "Failed to fetch update files.")
                return
            
            # Show progress dialog and start update
            logging.info("Starting update process")
            progress = UpdateProgressDialog(None, urls, latest)
            progress.show()
            progress.start_update()
            app.exec_()
        else:
            logging.info("User declined update")
            # CustomMessageBox.show_info(None, "Update Skipped",
            #                           "You can update later from the Help menu.")
    else:
        logging.info(f"No update needed. Current version {local} is up to date")
        # CustomMessageBox.show_info(None, "No Updates Available",
        #                           f"You are running the latest version ({local}).")


if __name__ == "__main__":
    try:
        check_for_update()
    except Exception as e:
        logging.exception("Fatal error in main")
        try:
            CustomMessageBox.show_error(None, "Critical Error",
                                       f"Updater crashed:\n{str(e)}\n\nCheck logs at:\n{LOG_FILE}")
        except:
            pass
    finally:
        logging.info("Updater exiting")