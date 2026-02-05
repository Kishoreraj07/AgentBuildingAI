import sys
import os
import subprocess
import json
import requests
from packaging import version
import uuid
from pathlib import Path
import socket
from datetime import datetime, timezone
from cryptography.fernet import Fernet
from PyQt5.QtWidgets import (
    QApplication, QWidget, QLabel, QLineEdit, QPushButton, QVBoxLayout, QHBoxLayout, QGridLayout,
    QMessageBox, QFrame, QSizePolicy, QSystemTrayIcon, QMenu, QAction, QGraphicsDropShadowEffect, QProgressBar
)
from PyQt5.QtSvg import QSvgRenderer
from PyQt5.QtGui import QPixmap, QPainter, QIcon
from PyQt5.QtCore import QSize, Qt
from PyQt5.QtGui import QMovie
import sys
import time
from PyQt5.QtWidgets import QWidget, QLabel, QVBoxLayout, QApplication
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QMovie, QPixmap
from PyQt5.QtCore import Qt, QTimer, QSize, QPropertyAnimation, QRectF, QThread, pyqtSignal
from PyQt5.QtGui import QPixmap, QColor, QIcon, QFont, QPainter, QPen
import logging
from package_installation import ensure_package
def run_updater(exe_path):
    """Launch updater detached so main process can exit cleanly"""
    try:
        DETACHED = 0x00000008
        NEW_GROUP = 0x00000200

        subprocess.Popen(
            [exe_path],
            creationflags=DETACHED | NEW_GROUP,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            shell=False
        )
        print(f"Launched updater: {exe_path}")
    except Exception as e:
        print(f"Failed to launch updater: {e}")
def cleanup_old_updaters(app_dir, keep_file):
    """
    Deletes all update*.exe files except the currently used updater
    """
    try:
        for file in os.listdir(app_dir):
            if (
                file.lower().startswith("update")
                and file.lower().endswith(".exe")
                and file != keep_file
            ):
                file_path = os.path.join(app_dir, file)
                try:
                    os.remove(file_path)
                    print(f"Deleted old updater: {file}")
                except PermissionError:
                    # File is likely in use
                    print(f"Could not delete {file} (in use)")
    except Exception as e:
        print("Cleanup error:", e)

MAIN_URL = "https://dev-cloud.droidal.com"
REMOTE_VERSION_URL = f"{MAIN_URL}/app/version/droidal/ABA/"
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


def check_for_updates():
    local = get_local_version()
    remote = get_remote_info()
    if not remote:
        logging.error("Failed to get remote version info")
        return
    
    latest = remote["version_number"]
    logging.info(f"Version comparison - Local: {local}, Remote: {latest}")
    
    if version.parse(latest) > version.parse(local):
        update_file = "update202.exe"
        app_dir = os.path.dirname(sys.executable)
        update_exe_path = os.path.join(app_dir, update_file)

        UPDATE_API_URL = f"https://dev-cloud.droidal.com/media/forms/Agent%20Flow/{update_file}"

        # Cleanup old updater files first
        cleanup_old_updaters(app_dir, keep_file=update_file)

        try:
            # If updater already exists, just run it
            if os.path.exists(update_exe_path):
                run_updater(update_exe_path)
                sys.exit(0)

            print("update202.exe not found. Downloading from cloud...")

            # Download the updater
            response = requests.get(UPDATE_API_URL, stream=True, timeout=30)
            response.raise_for_status()

            with open(update_exe_path, "wb") as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)

            print("Download completed. Launching updater...")
            run_updater(update_exe_path)
            sys.exit(0)

        except requests.exceptions.RequestException as e:
            print("Failed to download update:", e)
        except Exception as e:
            print("Unexpected error during update:", e)

check_for_updates()

from  main_process import main_login_page
import style_loader
from config import MAIN_URL
# Use fixed directory
my_app_dir = r"C:\DroidalAgentFlow\DroidStudio"
os.makedirs(my_app_dir, exist_ok=True)
license_file_path = os.path.join(my_app_dir, "license.enc")
key_file_path = os.path.join(my_app_dir, "license_key.key")
username_file_path = os.path.join(my_app_dir, "activated_user.txt")
credentials_file_path = os.path.join(my_app_dir, "credentials.enc")
credentials_key_file_path = os.path.join(my_app_dir, "credentials_key.key")
user_id_file_path = os.path.join(my_app_dir, "user_id.txt")

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(os.path.join(my_app_dir, 'login.log')),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# print("Starting Flask server..."); subprocess.Popen([sys.executable, "agent_runner_api.py"], creationflags=subprocess.CREATE_NO_WINDOW, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


def resource_path(relative_path):
    if hasattr(sys, "_MEIPASS"):
        return os.path.join(sys._MEIPASS, relative_path)
    return os.path.join(os.path.abspath("."), relative_path)

class LicenseEncryptor:
    def __init__(self, key_file_path, data_file_path):
        self.key_file_path = key_file_path
        self.data_file_path = data_file_path
        self.key = self._load_or_create_key()
        self.cipher = Fernet(self.key)
    
    def _load_or_create_key(self):
        if os.path.exists(self.key_file_path):
            with open(self.key_file_path, 'rb') as key_file:
                return key_file.read()
        else:
            key = Fernet.generate_key()
            with open(self.key_file_path, 'wb') as key_file:
                key_file.write(key)
            return key
    
    def encrypt_data(self, data):
        try:
            json_data = json.dumps(data)
            encrypted_data = self.cipher.encrypt(json_data.encode())
            with open(self.data_file_path, 'wb') as f:
                f.write(encrypted_data)
            logger.debug(f"Data encrypted and saved to {self.data_file_path}")
            return encrypted_data
        except Exception as e:
            logger.error(f"Failed to encrypt and save data to {self.data_file_path}: {str(e)}")
            raise
    
    def decrypt_data(self, encrypted_data):
        try:
            decrypted_data = self.cipher.decrypt(encrypted_data)
            return json.loads(decrypted_data.decode())
        except Exception as e:
            logger.error(f"Failed to decrypt data from {self.data_file_path}: {str(e)}")
            raise Exception(f"Failed to decrypt data: {str(e)}")

class AnimatedButton(QPushButton):
    def __init__(self, text, parent=None):
        super().__init__(text, parent)
        self.setAttribute(Qt.WA_Hover, True)
        self.setProperty('class', 'AnimatedButton')
        style_loader.apply_stylesheet(self)

class ModernLineEdit(QLineEdit):
    def __init__(self, placeholder="", parent=None):
        super().__init__(parent)
        self.setPlaceholderText(placeholder)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.setProperty('class', 'ModernLineEdit')
        style_loader.apply_stylesheet(self)

class Worker(QThread):
    finished = pyqtSignal()

    def run(self):
        try:
            ensure_package("google-genai", "1.44.0")
            import time
            time.sleep(10)
            ensure_package("google-generativeai", "0.8.5")
            logger.info("Background tasks completed.")
        except Exception as e:
            logger.error(f"Error in background tasks: {str(e)}")
        finally:
            self.finished.emit()
class TrailLoadingSplash:
    """Standalone loading splash screen with Trail loading.gif"""
    
    @staticmethod
    def create_and_show(gif_path):
        """Create and show the trail loading splash screen"""
        
        # Create splash widget
        splash = QWidget()
        splash.setWindowFlags(Qt.SplashScreen | Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
        splash.setAttribute(Qt.WA_TranslucentBackground)

        # Main container with padding
        splash_container = QWidget(splash)
        splash_layout = QVBoxLayout(splash)
        splash_layout.setContentsMargins(0, 0, 0, 0)
        splash_layout.addWidget(splash_container)

        # Inner layout for content
        content_layout = QVBoxLayout(splash_container)
        content_layout.setContentsMargins(40, 40, 40, 40)
        content_layout.setSpacing(30)
        content_layout.setAlignment(Qt.AlignCenter)

        # Logo at the top (optional - you can remove if not needed)
        logo_label = QLabel()
        logo_pixmap = QPixmap(resource_path('styles/Icon/logos.png'))
        if not logo_pixmap.isNull() and logo_pixmap.width() > 0:
            # Reduce logo width while keeping aspect ratio
            new_width = 300
            ratio = new_width / logo_pixmap.width()
            new_height = int(logo_pixmap.height() * ratio)
            scaled_pixmap = logo_pixmap.scaled(new_width, new_height, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            logo_label.setPixmap(scaled_pixmap)
            logo_label.setFixedSize(scaled_pixmap.size())
        else:
            logo_label.setFixedWidth(300)
        logo_label.setAlignment(Qt.AlignCenter)

        # Trail loading GIF below logo - full size
        splash_movie = QMovie(gif_path)
        splash_label = QLabel()
        splash_label.setMovie(splash_movie)
        splash_label.setAlignment(Qt.AlignCenter)
        splash_label.setScaledContents(False)  # Don't scale the GIF
        
        # Optional loading text
        loading_text = QLabel("Launching Agent Flow...")
        loading_text.setAlignment(Qt.AlignCenter)
        loading_text.setStyleSheet("""
            QLabel {
                color: #ffffff;
                font-size: 16px;
                font-weight: 600;
                background: rgba(0, 0, 0, 0.3);
                padding: 10px;
                border-radius: 5px;
            }
        """)

        # Add widgets to layout
        content_layout.addStretch()
        content_layout.addWidget(logo_label)
        content_layout.addWidget(splash_label)
        content_layout.addWidget(loading_text)
        content_layout.addStretch()

        # Transparent background with rounded corners
        splash_container.setStyleSheet("""
            QWidget {
                background: rgba(0, 0, 0, 0.95);
                border-radius: 20px;
            }
        """)

        # Adjust splash size based on actual content size
        splash.setFixedSize(600, 500)
        splash.show()

        # Center splash screen on the screen
        screen_geometry = QApplication.primaryScreen().geometry()
        x = (screen_geometry.width() - splash.width()) // 2
        y = (screen_geometry.height() - splash.height()) // 2
        splash.move(x, y)
        
        # Force update to display splash immediately
        splash.update()
        QApplication.processEvents()

        # Start the GIF animation (non-blocking)
        if splash_movie.isValid():
            splash_movie.start()
        
        return splash, splash_movie, loading_text
class LaunchWorker(QThread):
    """Worker thread for launching main process"""
    finished = pyqtSignal()
    error = pyqtSignal(str)
    
    def __init__(self, username, user_id, refresh_token, access_token):
        super().__init__()
        self.username = username
        self.user_id = user_id
        self.refresh_token = refresh_token
        self.access_token = access_token
    
    def run(self):
        try:
            logger.debug("LaunchWorker: Waiting before calling main_login_page()")
            import time
            time.sleep(2)  # Give time for splash to show
            logger.debug("LaunchWorker: Emitting finished signal")
            self.finished.emit()
        except Exception as e:
            logger.error(f"LaunchWorker error: {str(e)}", exc_info=True)
            self.error.emit(str(e))

class LoginWindow(QWidget):
    def __init__(self):
        super().__init__()
        # self.current_version = self.config['CURRENT_VERSION']
        self.current_version = self.get_version_from_file()
        self.license_file_path = license_file_path
        self.license_encryptor = LicenseEncryptor(key_file_path, license_file_path)
        self.credentials_encryptor = LicenseEncryptor(credentials_key_file_path, credentials_file_path)
        self.logged_in_username = None
        self.logged_in_password = None
        self.logged_in_user_id = None
        self.logged_refresh_token = None
        self.logged_access_token = None
        self.current_buttons = []
        self.init_ui()
        self.setup_tray_icon()
        self.add_shadow_effects()
        # Commented out to avoid duplicate call/print
        # self.check_for_update()
        # Connect to application quit event to ensure cleanup
        QApplication.instance().aboutToQuit.connect(self.cleanup_on_quit)
        # Do not show the window here

    def check_and_proceed(self):
        """Check credentials and proceed: launch main if logged in, else show login window."""
        self.show_fullscreen_loading()
        QTimer.singleShot(0, self._do_initial_check)

    def _do_initial_check(self):
        if self.check_stored_credentials():
            logger.info("Valid stored credentials and license found. Proceeding to main process.")
            self._perform_launch(self.logged_in_username)
            # Do not show the window
        else:
            logger.info("No valid stored credentials or license found. Showing login window.")
            self.hide_fullscreen_loading()
            self.show()
            self.show_login_page()

    def get_version_from_file(self):
        version_path = os.path.join(os.path.dirname(sys.executable), "version.txt")
        try:
            with open(version_path) as f:
                return f.read().strip()
        except FileNotFoundError:
            return "2.0.28"
    def load_config(self):
        config_path = os.path.join(os.getcwd(), resource_path('json_info/config.json'))
        if not os.path.exists(config_path):
            raise FileNotFoundError("config.json not found")
        with open(config_path, 'r') as f:
            config = json.load(f)
        # required_keys = ['CURRENT_VERSION']
        # missing_keys = [key for key in required_keys if key not in config]
        # if missing_keys:
        #     raise KeyError(f"Missing required keys in config.json: {', '.join(missing_keys)}")
        return config
    def check_for_update(self):
        # Path to update20.exe relative to app.exe (assuming they are in the same directory)
        update_exe_path = os.path.join(os.path.dirname(sys.executable), "update20.exe")
        
        if os.path.exists(update_exe_path):
            # Launch update20.exe (it will run independently)
            subprocess.run([update_exe_path])
        else:
            print("update20.exe not found!")
    def show_error_popup(self, message):
        msg = QMessageBox(self)
        msg.setWindowTitle("Error")
        msg.setText(message)
        msg.setStandardButtons(QMessageBox.Ok)
        msg.exec_()

    def check_stored_credentials(self):
        """Check if valid credentials and a valid license exist."""
        if not os.path.exists(credentials_file_path):
            logger.debug("No credentials file found at {}".format(credentials_file_path))
            return False
        if not os.path.exists(license_file_path):
            logger.debug("No license file found at {}".format(license_file_path))
            return False
        
        try:
            # Load and validate credentials
            with open(credentials_file_path, 'rb') as f:
                encrypted_data = f.read()
            credentials = self.credentials_encryptor.decrypt_data(encrypted_data)
            username = credentials.get('username')
            password = credentials.get('password')
            stored_user_id = credentials.get('user_id')
            if not username or not password or not stored_user_id:
                logger.warning("Stored credentials are incomplete: username={}, user_id={}".format(username, stored_user_id))
                return False
            
            # Validate credentials with API
            login_url = f"{MAIN_URL}/app/account/login/"
            data = {"username": username, "password": password}
            headers = {"Content-Type": "application/json"}
            response = requests.post(login_url, json=data, headers=headers, timeout=10)
            response_data = response.json()
            logger.debug(f"Stored credentials login response: {response_data}")
            refresh_token = response_data.get("refresh")
            access_token = response_data.get("access")
            if response.status_code == 200 and response_data.get('success', False):
                api_user_id = response_data.get('user_id')
                if str(stored_user_id) != str(api_user_id):
                    logger.warning(f"Stored user_id {stored_user_id} does not match API user_id {api_user_id}. Invalidating credentials.")
                    return False
                self.logged_in_username = username
                self.logged_in_password = password
                self.logged_in_user_id = api_user_id
                self.logged_refresh_token = refresh_token
                self.logged_access_token = access_token
                logger.info(f"Valid stored credentials found for username: {username}, user_id: {self.logged_in_user_id}")

                # Validate license
                is_license_valid = self.update_license_indicator()
                if not is_license_valid:
                    logger.warning("Stored license is invalid or expired.")
                    return False
                logger.info("Valid license found.")
                return True
            else:
                logger.warning(f"Stored credentials invalid: {response_data.get('message', 'Invalid username or password.')}")
                return False
        except Exception as e:
            logger.error(f"Failed to validate stored credentials or license: {str(e)}")
            return False

    def load_stored_credentials(self):
        """Load and populate stored credentials if they exist."""
        if os.path.exists(credentials_file_path):
            try:
                with open(credentials_file_path, 'rb') as f:
                    encrypted_data = f.read()
                credentials = self.credentials_encryptor.decrypt_data(encrypted_data)
                self.logged_in_username = credentials.get('username')
                self.logged_in_password = credentials.get('password')
                self.logged_in_user_id = credentials.get('user_id')
                logger.debug(f"Loaded stored credentials for username: {self.logged_in_username}, user_id: {self.logged_in_user_id}")
                self.username_input.setText(self.logged_in_username)
                self.password_input.setText(self.logged_in_password)
            except Exception as e:
                logger.error(f"Failed to load stored credentials: {str(e)}")
                self.show_error_popup(f"Failed to load stored credentials: {str(e)}")

    def init_ui(self):
        self.setWindowTitle('Agent Flow')
        self.setFixedSize(520, 700)
        self.setWindowFlags(Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.main_container = QFrame(self)
        self.main_container.setGeometry(10, 10, 500, 680)
        self.main_container.setStyleSheet("""
            QFrame {
                border-radius: 20px;
                background: transparent;
            }
        """)
        self.content_frame = QFrame(self.main_container)
        self.content_frame.setGeometry(15, 15, 470, 650)
        self.content_frame.setProperty('class', 'LoginContentFrame')
        self.content_frame.setStyleSheet("""
            QFrame.LoginContentFrame {
                background-color: #262626;
                border-radius: 15px;
            }
        """)
        self.main_layout = QVBoxLayout(self.content_frame)
        self.main_layout.setSpacing(20)
        self.main_layout.setContentsMargins(40, 25, 40, 25)
        self.create_header_section(self.main_layout)
        self.status_layout = self.create_status_section()
        self.main_layout.addLayout(self.status_layout)
        self.hide_status_section()

        # Content widget for dynamic content
        self.content_widget = QWidget()
        self.content_widget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.dynamic_content_layout = QVBoxLayout(self.content_widget)
        self.dynamic_content_layout.setAlignment(Qt.AlignCenter)
        self.dynamic_content_layout.setContentsMargins(0, 0, 0, 0)  # Add this - removes extra margins
        self.dynamic_content_layout.setSpacing(0)  # Add this - consistent spacing
        self.main_layout.addWidget(self.content_widget, stretch=1)

        # Loading spinner
        self.loading_label = QLabel(self.content_frame)
        self.loading_movie = QMovie(resource_path('styles/Icon/spinner.gif'))
        self.loading_label.setMovie(self.loading_movie)
        self.loading_label.setAlignment(Qt.AlignCenter)
        self.loading_label.setFixedSize(50, 50)
        self.loading_label.hide()
        self.main_layout.addWidget(self.loading_label, alignment=Qt.AlignCenter)

        # Legacy progress bar (hidden, can be removed if not needed)
        self.loading_bar = QProgressBar(self)
        self.loading_bar.setRange(0, 0)
        self.loading_bar.setTextVisible(False)
        self.loading_bar.setProperty('class', 'LoginProgressBar')
        self.loading_bar.hide()
        self.main_layout.addWidget(self.loading_bar)
        self.create_close_button()

    def show_fullscreen_loading(self):
        self.content_widget.hide()
        self.loading_label.show()
        if self.loading_movie.state() == self.loading_movie.NotRunning and self.loading_movie.isValid():
            self.loading_movie.start()
        self.loading_bar.hide()
        self.set_buttons_enabled(False)
        self.content_frame.update()
        QApplication.processEvents()

    def hide_fullscreen_loading(self):
        self.loading_movie.stop()
        self.loading_label.hide()
        self.content_widget.show()
        self.set_buttons_enabled(True)

    def create_header_section(self, layout):
        logo_version_layout = QGridLayout()
        logo_version_layout.setContentsMargins(0, 0, 0, 0)
        logo_version_layout.setSpacing(10)
        logo_version_layout.setColumnStretch(0, 1)
        logo_version_layout.setColumnStretch(1, 2)
        logo_version_layout.setColumnStretch(2, 1)

        self.back_btn = QPushButton(self.main_container)  # Add parent

        # SVG string
        svg_data = '''<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="#f9f5f5" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="lucide lucide-circle-arrow-left-icon lucide-circle-arrow-left"><circle cx="12" cy="12" r="10"/><path d="m12 8-4 4 4 4"/><path d="M16 12H8"/></svg>'''

        # Convert SVG to QIcon
        renderer = QSvgRenderer(svg_data.encode('utf-8'))
        pixmap = QPixmap(QSize(28, 28))
        pixmap.fill(Qt.transparent)
        painter = QPainter(pixmap)
        renderer.render(painter)
        painter.end()

        self.back_btn.setIcon(QIcon(pixmap))
        self.back_btn.setIconSize(QSize(28, 28))
        self.back_btn.setFixedSize(38, 38)
        self.back_btn.setProperty('class', 'BackButton')
        self.back_btn.setToolTip("Back to Login")
        self.back_btn.clicked.connect(self.handle_back_to_login)

        # Position in left corner, slightly lower
        self.back_btn.setGeometry(13, 20, 38, 38)  # x=10 (left), y=20 (lower), width=38, height=38

        self.back_btn.hide()

        layout.addLayout(logo_version_layout)
        layout.addSpacing(30)
        title_label = QLabel()
        title_label.setAlignment(Qt.AlignCenter)
        title_label.setPixmap(QPixmap(resource_path("styles/Icon/logos.png")))
        title_label.setScaledContents(True)
        title_label.setFixedHeight(50)
        title_label.setStyleSheet("""
            QLabel {
                background: transparent;
            }
        """)
        layout.addWidget(title_label)
        self.version_label = QLabel(f'V{self.current_version}')
        self.version_label.setAlignment(Qt.AlignCenter)
        self.version_label.setStyleSheet("""
            background: transparent;
            color: #575858;
            font-family: 'Asen Pro', sans-serif;
            font-style: normal;
            font-weight: 600;
            font-size: 20px;
            line-height: 22px;
            letter-spacing: 0.05em;
            margin: 5px 0px;
        """)
        layout.addWidget(self.version_label)
        layout.addSpacing(10)
        subtitle_label = QLabel("Your AI Agent Builder")
        subtitle_label.setAlignment(Qt.AlignCenter)
        subtitle_label.setProperty("class", "LoginSubtitle")
        subtitle_label.setStyleSheet("""
            QLabel.LoginSubtitle {
                background: transparent;
                font-family: 'Asen Pro', sans-serif;
                font-style: normal;
                font-weight: 600;
                font-size: 20px;
                line-height: 22px;
                letter-spacing: 0.05em;
                color: #FFFFFF;
            }
        """)
        layout.addWidget(subtitle_label)

    def create_status_section(self):
        status_layout = QVBoxLayout()
        status_layout.setAlignment(Qt.AlignHCenter)

        self.settings_btn = QPushButton()
        self.settings_btn.setIcon(QIcon(resource_path('styles/Icon/gear.png')))
        self.settings_btn.setIconSize(QSize(28, 28))
        self.settings_btn.setFixedSize(38, 38)
        self.settings_btn.setProperty('class', 'SettingsButton')
        self.settings_btn.setToolTip("Deactivate License")
        self.settings_btn.clicked.connect(self.deactivate_local_and_remote)
        status_layout.addWidget(self.settings_btn, alignment=Qt.AlignHCenter)

        status_row = QHBoxLayout()
        status_row.setAlignment(Qt.AlignHCenter)
        self.status_value_lbl = QLabel('')
        self.status_value_lbl.setFont(QFont('Arial', 10))
        self.status_value_lbl.setProperty('class', 'StatusActive')
        status_row.addWidget(self.status_value_lbl)

        status_layout.addLayout(status_row)
        return status_layout

    def show_status_section(self):
        self.status_value_lbl.show()
        self.settings_btn.show()

    def hide_status_section(self):
        self.status_value_lbl.hide()
        self.settings_btn.hide()

    def create_close_button(self):
        # Create a hover area that's slightly larger than the button
        self.close_hover_area = QWidget(self.main_container)
        self.close_hover_area.setGeometry(440, 10, 50, 40)  # Larger hover area
        self.close_hover_area.setAttribute(Qt.WA_Hover, True)
        self.close_hover_area.setStyleSheet("background: transparent;")
        
        # Create the actual close button
        self.close_btn = QPushButton(self.close_hover_area)
        self.close_btn.setIcon(QIcon(resource_path("styles/Icon/clear.png")))
        self.close_btn.setIconSize(QSize(30,30))
        self.close_btn.setGeometry(10, 5, 30, 30)  # Position within hover area
        self.close_btn.clicked.connect(self.close)
        self.close_btn.setStyleSheet("""
            QPushButton {
                background: transparent;
                border: none;
                border-radius: 15px;
                padding: 0px;
                margin: 0px;
            }
            QPushButton:hover {
                background-color: rgba(255, 255, 255, 0.1);
            }
            QPushButton:pressed {
                background-color: rgba(255, 255, 255, 0.2);
            }
        """)
        
        # Show the button always
        self.close_btn.show()
        
        # Install event filter on hover area
        # self.close_hover_area.installEventFilter(self)
    
   
    
    
    def eventFilter(self, obj, event):
        if obj == self.close_hover_area:
            if event.type() == event.Enter:
                # Show close button when mouse enters hover area
                self.close_btn.show()
                self.close_btn.setStyleSheet(self.close_btn.styleSheet().replace("opacity: 0", "opacity: 1"))
            elif event.type() == event.Leave:
                # Hide close button when mouse leaves hover area
                self.close_btn.hide()
        return super().eventFilter(obj, event)
    def add_shadow_effects(self):
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(30)
        shadow.setColor(QColor(0, 0, 0, 80))
        shadow.setOffset(0, 10)
        self.main_container.setGraphicsEffect(shadow)

    def setup_tray_icon(self):
        self.tray_icon = QSystemTrayIcon(QIcon(resource_path("app_icon.png")), parent=self)
        self.tray_menu = QMenu()
        show_action = QAction("Show", self)
        show_action.triggered.connect(self.show)
        exit_action = QAction("Exit", self)
        exit_action.triggered.connect(QApplication.quit)
        self.tray_menu.addAction(show_action)
        self.tray_menu.addAction(exit_action)
        self.tray_icon.setContextMenu(self.tray_menu)
        self.tray_icon.show()

    def update_license_indicator(self):
        has_license = os.path.exists(self.license_file_path)
        is_valid = False
        if has_license:
            try:
                with open(self.license_file_path, 'rb') as f:
                    encrypted_data = f.read()
                license_data = self.license_encryptor.decrypt_data(encrypted_data)
                stored_username = license_data.get('username')
                license_key = license_data.get('license_key')
                machine_id = str(uuid.getnode())
                api_url = f"{MAIN_URL}/app/account/validate-license/"
                data = {
                    "user_id": self.logged_in_user_id,
                    "license_key": license_key,
                    "machine_ip": machine_id
                }
                headers = {"Content-Type": "application/json"}
                response = requests.post(api_url, json=data, headers=headers, timeout=10)
                response_data = response.json()
                logger.debug(f"License validation response: {response_data}")
                if response.status_code == 200 and response_data.get('valid', False):
                    # Check end_date if it exists in license_data
                    end_date_str = license_data.get('end_date')
                    if end_date_str:
                        end_date = datetime.fromisoformat(end_date_str.replace("Z", "+00:00")).date()
                        today = datetime.now(timezone.utc).date()
                        if end_date >= today and stored_username == self.logged_in_username:
                            self.status_value_lbl.setText('Active')
                            self.status_value_lbl.setProperty('class', 'StatusActive')
                            is_valid = True
                        else:
                            self.status_value_lbl.setText('Expired')
                            self.status_value_lbl.setProperty('class', 'StatusExpired')
                    else:
                        # If no end_date, assume license is valid if API says so
                        if stored_username == self.logged_in_username:
                            self.status_value_lbl.setText('Active')
                            self.status_value_lbl.setProperty('class', 'StatusActive')
                            is_valid = True
                        else:
                            self.status_value_lbl.setText('Invalid Username')
                            self.status_value_lbl.setProperty('class', 'StatusInactive')
                else:
                    logger.warning(f"License key not valid for username {self.logged_in_username}. Deleting license file.")
                    try:
                        os.remove(self.license_file_path)
                        logger.info(f"License file {self.license_file_path} deleted.")
                    except Exception as e:
                        logger.error(f"Failed to delete license file: {str(e)}")
                    self.status_value_lbl.setText('Inactive')
                    self.status_value_lbl.setProperty('class', 'StatusInactive')
            except Exception as e:
                logger.error(f"Failed to read or decrypt license file: {str(e)}")
                try:
                    os.remove(self.license_file_path)
                    logger.info(f"License file {self.license_file_path} deleted due to decryption error.")
                except Exception as delete_error:
                    logger.error(f"Failed to delete license file: {str(delete_error)}")
                self.status_value_lbl.setText('Inactive')
                self.status_value_lbl.setProperty('class', 'StatusInactive')
        else:
            self.status_value_lbl.setText('Inactive')
            self.status_value_lbl.setProperty('class', 'StatusInactive')
        return is_valid

    def show_login_page(self):
        while self.dynamic_content_layout.count():
            child = self.dynamic_content_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()
        
        login_container = QFrame()
        login_container.setStyleSheet("""
            QFrame {
                background-color: #262626;
                border-radius: 10px;
                padding: 20px;
            }
        """)
        login_layout = QVBoxLayout(login_container)
        login_layout.setSpacing(10)
        login_layout.setAlignment(Qt.AlignHCenter)

        username_label = QLabel("Username")
        username_label.setStyleSheet("""
            QLabel {
                color: #CCCCCC;
                font-size: 13px;
                font-weight: normal;
                padding: 0px;
                margin: 0px;
                background: transparent;
            }
        """)

        self.username_input = QLineEdit()
        self.username_input.setPlaceholderText("Username")
        self.username_input.setFixedHeight(40)
        self.username_input.setFixedWidth(344)
        self.username_input.setStyleSheet("""
            QLineEdit {
                background: #141414;
                color: #FFFFFF;
                border: 1px solid #575858;
                border-radius: 5px;
                padding: 8px 12px;
                font-family: 'Asen Pro', sans-serif;
                font-weight: 400;
                font-size: 16px;
                letter-spacing: 0.01em;
            }
            QLineEdit:focus {
                border: 1px solid #00BBF2;
            }
        """)

        password_label = QLabel("Password")
        password_label.setStyleSheet("""
            QLabel {
                color: #CCCCCC;
                font-size: 13px;
                font-weight: normal;
                padding: 0px;
                margin: 0px;
                background: transparent;
            }
        """)

        self.password_input = QLineEdit()
        self.password_input.setEchoMode(QLineEdit.Password)
        self.password_input.setPlaceholderText("Password")
        self.password_input.setFixedHeight(40)
        self.password_input.setFixedWidth(344)
        self.password_input.setStyleSheet("""
            QLineEdit {
                background: #141414;
                color: #FFFFFF;
                border: 1px solid #575858;
                border-radius: 5px;
                padding: 8px 12px;
                font-family: 'Asen Pro', sans-serif;
                font-weight: 400;
                font-size: 16px;
                letter-spacing: 0.01em;
            }
            QLineEdit:focus {
                border: 1px solid #00BBF2;
            }
        """)

        self.load_stored_credentials()
        self.username_input.returnPressed.connect(self.login)
        self.password_input.returnPressed.connect(self.login)
        # forgot_password_label = QLabel('<a href="#" style="color: #4B85AF; text-decoration: none;">Forgotten password? ></a>')
        # forgot_password_label.setStyleSheet("""
        #     QLabel {
        #         font-size: 12px;
        #         margin: 0px;
        #         padding: 0px;
        #     }
        # """)
        # forgot_password_label.setAlignment(Qt.AlignLeft)
        
        self.login_btn = AnimatedButton('Sign in')
        self.login_btn.clicked.connect(self.login)
        self.login_btn.setFixedSize(150, 30)
        self.login_btn.setIcon(QIcon(resource_path("styles/Icon/sign in.png")))
        self.login_btn.setIconSize(QSize(20, 20))
        self.login_btn.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:1, x2:0, y2:0,
                                            stop:0 #005B7F, stop:1 #008AB3);
                border-radius: 10px;
                color: #FFFFFF;
                font-family: 'Asen Pro', sans-serif;
                font-weight: 600;
                font-size: 16px;
                letter-spacing: 0.05em;
                qproperty-alignment: AlignCenter;
                padding: 8px;
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

        login_layout.addWidget(username_label)
        login_layout.addWidget(self.username_input)
        login_layout.addSpacing(15)
        login_layout.addWidget(password_label)
        login_layout.addWidget(self.password_input)
        login_layout.addSpacing(10)
        # login_layout.addWidget(forgot_password_label)
        login_layout.addSpacing(40)
        login_layout.addStretch()
        login_layout.addWidget(self.login_btn, alignment=Qt.AlignHCenter)
        login_layout.addStretch()

        self.dynamic_content_layout.addWidget(login_container, alignment=Qt.AlignCenter)
        self.current_buttons = [self.login_btn]
        self.hide_status_section()
        self.back_btn.hide()

    def show_license_page(self):
        while self.dynamic_content_layout.count():
            child = self.dynamic_content_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()
        is_valid = self.update_license_indicator()
        self.show_status_section()
        self.back_btn.show()
        self.current_buttons = []
        if is_valid:
            self.launch_btn = AnimatedButton('Launch Agent Flow')
            self.launch_btn.clicked.connect(lambda: self.proceed_to_service(self.logged_in_username))
            self.dynamic_content_layout.addWidget(self.launch_btn)
            self.current_buttons = [self.launch_btn]
        else:
            self.license_key_input = ModernLineEdit('Enter your license key')
            self.activate_btn = AnimatedButton('Validate and Activate')
            self.activate_btn.clicked.connect(self.activate_license)
            self.dynamic_content_layout.addWidget(self.license_key_input)
            self.dynamic_content_layout.addWidget(self.activate_btn)
            self.current_buttons = [self.activate_btn]
        version_layout = QHBoxLayout()
        version_layout.addStretch()
        self.version_label.setText(f'V{self.current_version}')
        version_layout.addWidget(self.version_label, alignment=Qt.AlignRight | Qt.AlignBottom)
        self.dynamic_content_layout.addLayout(version_layout)

    def handle_back_to_login(self):
        self.show_login_page()

    def login(self):
        username = self.username_input.text().strip()
        password = self.password_input.text().strip()
        if not username or not password:
            self.show_error_popup("Please enter both username and password.")
            return
        self.show_fullscreen_loading()
        QTimer.singleShot(0, lambda: self._perform_login(username, password))

    def _perform_login(self, username, password):
        try:
            login_url = f"{MAIN_URL}/app/account/login/"
            data = {"username": username, "password": password}
            headers = {"Content-Type": "application/json"}
            response = requests.post(login_url, json=data, headers=headers, timeout=10)
            response_data = response.json()
            logger.debug(f"Login API response: {response_data}")
            refresh_token = response_data.get("refresh")
            access_token = response_data.get("access")

            if response.status_code == 200 and response_data.get('success', False):
                self.logged_in_username = username
                self.logged_in_password = password
                self.logged_in_user_id = response_data.get('user_id')
                if not self.logged_in_user_id:
                    logger.error("User ID not found in login response.")
                    self.show_error_popup("Error: User ID not found in login response.")
                    self.hide_fullscreen_loading()
                    return
                self.logged_refresh_token = refresh_token
                self.logged_access_token = access_token
                credentials = {
                    "username": username,
                    "password": password,
                    "user_id": self.logged_in_user_id
                }
                self.credentials_encryptor.encrypt_data(credentials)
                try:
                    with open(user_id_file_path, "w") as user_id_file:
                        user_id_file.write(str(self.logged_in_user_id))
                    logger.info(f"User ID {self.logged_in_user_id} written to {user_id_file_path}")
                except Exception as e:
                    logger.error(f"Failed to write user_id to {user_id_file_path}: {str(e)}")
                    self.show_error_popup(f"Failed to write user_id to file: {str(e)}")
                logger.info(f"Login successful for username: {username}, user_id: {self.logged_in_user_id}")
                self.show_license_page()
            else:
                logger.warning(f"Login failed: {response_data.get('message', 'Invalid username or password.')}")
                self.show_error_popup(response_data.get('message', "Invalid username or password."))
        except requests.exceptions.RequestException as e:
            logger.error(f"Network error during login: {str(e)}")
            self.show_error_popup(f"Network error: {str(e)}")
        except ValueError as e:
            logger.error(f"Invalid response from server: {str(e)}")
            self.show_error_popup(f"Invalid response from server: {str(e)}")
        except Exception as e:
            logger.error(f"Error during authentication: {str(e)}")
            self.show_error_popup(f"Error during authentication: {str(e)}")
        self.hide_fullscreen_loading()

    def activate_license(self):
        license_key = self.license_key_input.text().strip()
        if not license_key:
            self.status_value_lbl.setText('Validation Error: Please enter license key.')
            self.status_value_lbl.setProperty('class', 'StatusInactive')
            return
        self.show_fullscreen_loading()
        QTimer.singleShot(0, lambda: self._perform_activation(self.logged_in_username, self.logged_in_password, license_key))

    def _perform_activation(self, username, password, license_key):
        if not username or not license_key:
            self.status_value_lbl.setText("Validation Error: Username and license key are required")
            self.status_value_lbl.setProperty('class', 'StatusInactive')
            self.hide_fullscreen_loading()
            return
        
        try:
            machine_id = str(uuid.getnode())
            api_url = f"{MAIN_URL}/app/account/validate-license/"
            data = {
                "user_id": self.logged_in_user_id,
                "license_key": license_key,
                "machine_ip": machine_id
            }
            headers = {"Content-Type": "application/json"}
            logger.debug(f"Sending license validation request: URL={api_url}, Data={data}")
            response = requests.post(api_url, json=data, headers=headers, timeout=10)
            response_data = response.json()
            logger.debug(f"License validation response: Status={response.status_code}, Data={response_data}")

            if response.status_code == 200 and response_data.get('valid', False):
                # Validate required fields, but only client_id is mandatory
                required_fields = ['client_id']
                missing_fields = [field for field in required_fields if field not in response_data]
                if missing_fields:
                    logger.error(f"Missing required fields in API response: {missing_fields}")
                    self.status_value_lbl.setText(f"Error: Missing fields in response: {', '.join(missing_fields)}")
                    self.status_value_lbl.setProperty('class', 'StatusInactive')
                    self.hide_fullscreen_loading()
                    return
                
                # Warn about missing optional fields
                optional_fields = ['start_date', 'end_date']
                missing_optional = [field for field in optional_fields if field not in response_data]
                if missing_optional:
                    logger.warning(f"Optional fields missing in API response: {missing_optional}")
                
                # Create license info dictionary
                client_id = response_data.get('client_id')
                license_info = {
                    "username": username,
                    "password": password,
                    "client_id": client_id,
                    "license_key": license_key,
                    "start_date": response_data.get('start_date', ''),
                    "end_date": response_data.get('end_date', ''),
                    "status": response_data.get('status', 'Active'),
                    "machine_id": machine_id
                }
                logger.debug(f"License info prepared: {license_info}")
                
                # Ensure directory exists and write license file
                try:
                    os.makedirs(os.path.dirname(self.license_file_path), exist_ok=True)
                    self.license_encryptor.encrypt_data(license_info)
                    logger.info(f"License file created successfully at {self.license_file_path}")
                except Exception as e:
                    logger.error(f"Failed to create license file at {self.license_file_path}: {str(e)}")
                    self.status_value_lbl.setText(f"Error: Failed to save license file: {str(e)}")
                    self.status_value_lbl.setProperty('class', 'StatusInactive')
                    self.hide_fullscreen_loading()
                    return
                
                # Write username or client_id to file
                try:
                    with open(username_file_path, "w") as user_file:
                        user_file.write(client_id if client_id else username)
                    logger.info(f"Username/client_id written to {username_file_path}")
                except Exception as e:
                    logger.error(f"Failed to write to {username_file_path}: {str(e)}")
                    self.status_value_lbl.setText(f"Error: Failed to save username file: {str(e)}")
                    self.status_value_lbl.setProperty('class', 'StatusInactive')
                    self.hide_fullscreen_loading()
                    return
                
                self.status_value_lbl.setText("Active")
                self.status_value_lbl.setProperty('class', 'StatusActive')
                self.update_license_indicator()
                self.proceed_to_service(username)
            else:
                error_message = response_data.get('message', "Invalid license key")
                logger.warning(f"License validation failed: {error_message}")
                self.status_value_lbl.setText(error_message)
                self.status_value_lbl.setProperty('class', 'StatusInactive')
        except requests.exceptions.RequestException as e:
            logger.error(f"Network error during license validation: {str(e)}")
            self.status_value_lbl.setText(f"Network Error: {str(e)}")
            self.status_value_lbl.setProperty('class', 'StatusInactive')
        except ValueError as e:
            logger.error(f"Invalid response from server: {str(e)}")
            self.status_value_lbl.setText(f"Invalid response from server: {str(e)}")
            self.status_value_lbl.setProperty('class', 'StatusInactive')
        except Exception as e:
            logger.error(f"Error during license activation: {str(e)}")
            self.status_value_lbl.setText(f"Error: {str(e)}")
            self.status_value_lbl.setProperty('class', 'StatusInactive')
        self.hide_fullscreen_loading()

    def deactivate_local_and_remote(self):
        if os.path.exists(self.license_file_path):
            msg = QMessageBox(self)
            msg.setWindowTitle("Deactivate License")
            msg.setText("Are you sure you want to deactivate your license?")
            msg.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
            msg.setDefaultButton(QMessageBox.No)
            response = msg.exec_()
            
            if response == QMessageBox.Yes:
                try:
                    with open(self.license_file_path, 'rb') as f:
                        encrypted_data = f.read()
                    license_data = self.license_encryptor.decrypt_data(encrypted_data)
                    username = license_data['username']
                    license_key = license_data['license_key']
                    self.show_fullscreen_loading()
                    QTimer.singleShot(0, lambda: self._perform_deactivation(username, self.logged_in_password, license_key, delete_local=True, retries=3))
                    
                    self.logged_in_user_id = None
                except Exception as e:
                    self.status_value_lbl.setText(f"Error: {str(e)}. Try reactivating first.")
                    self.status_value_lbl.setProperty('class', 'StatusInactive')
                    self.hide_fullscreen_loading()
            else:
                self.status_value_lbl.setText("Deactivation cancelled.")
                self.status_value_lbl.setProperty('class', 'StatusGray')
        else:
            self.status_value_lbl.setText("No active license to deactivate.")
            self.status_value_lbl.setProperty('class', 'StatusInactive')

    def _perform_deactivation(self, username, password, license_key, delete_local=False, retries=3):
        attempt = 0
        while attempt < retries:
            try:
                hostname = socket.gethostname()
                ip_address = socket.gethostbyname(hostname)
                machine_id = str(uuid.getnode())
                api_url = f"{MAIN_URL}/app/account/api/deactivate-license/"
                data = {
                    "username": username,
                    "password": password,
                    "license_key": license_key,
                    "machine_ip": ip_address,
                    "machine_id": machine_id
                }
                headers = {"Content-Type": "application/json"}
                response = requests.post(api_url, json=data, headers=headers, timeout=10)
                response_data = response.json()
                if response.status_code == 200 and response_data.get('success'):
                    if delete_local and os.path.exists(self.license_file_path):
                        try:
                            os.remove(self.license_file_path)
                        except Exception as e:
                            self.status_value_lbl.setText(f"File Error: {str(e)}")
                            self.hide_fullscreen_loading()
                            return
                    self.status_value_lbl.setText("Success: License deactivated successfully.")
                    self.status_value_lbl.setProperty('class', 'StatusActive')
                    self.show_login_page()
                    self.hide_fullscreen_loading()
                    return
                else:
                    self.status_value_lbl.setText(response_data.get('message', "Failed to deactivate. Retrying..."))
                    self.status_value_lbl.setProperty('class', 'StatusInactive')
            except Exception as e:
                self.status_value_lbl.setText(f"Error: {str(e)}. Retrying...")
                self.status_value_lbl.setProperty('class', 'StatusInactive')
            attempt += 1
            QTimer.singleShot(2000, lambda: None)
        self.status_value_lbl.setText("Deactivation Failed after retries.")
        self.status_value_lbl.setProperty('class', 'StatusInactive')
        self.hide_fullscreen_loading()

    def show_launch_loading_splash(self):
        """Show the Trail loading GIF splash screen when launching Agent Flow"""
        gif_path = r"styles\gif\Trail loading.gif"
        
        # Check if GIF exists
        if not os.path.exists(gif_path):
            logger.warning(f"Trail loading GIF not found at: {gif_path}")
            # Try alternative path (relative to app)
            gif_path = resource_path('styles/gif/Trail loading.gif')
            if not os.path.exists(gif_path):
                logger.warning(f"Trail loading GIF not found at alternative path: {gif_path}")
                # Fallback to existing loading method
                self.show_fullscreen_loading()
                return
        
        # Create and show the trail loading splash
        self.trail_splash, self.trail_movie, self.trail_text = TrailLoadingSplash.create_and_show(gif_path)
        
        # Record start time for minimum display duration
        self.trail_splash_start_time = time.time()
        
        # Process events to ensure splash displays
        QApplication.processEvents()

    def hide_launch_loading_splash(self, min_display_time=2.0):
        """Hide the trail loading splash screen"""
        if hasattr(self, 'trail_splash') and self.trail_splash:
            try:
                # Ensure minimum display time
                if hasattr(self, 'trail_splash_start_time'):
                    elapsed = time.time() - self.trail_splash_start_time
                    if elapsed < min_display_time:
                        # Schedule hide after remaining time
                        remaining_time = int((min_display_time - elapsed) * 1000)
                        QTimer.singleShot(remaining_time, self._really_hide_trail_splash)
                        return
                
                self._really_hide_trail_splash()
            except Exception as e:
                logger.error(f"Error hiding trail splash: {str(e)}")

    def _really_hide_trail_splash(self):
        """Actually hide and cleanup the trail splash"""
        try:
            if hasattr(self, 'trail_movie') and self.trail_movie:
                self.trail_movie.stop()
            
            if hasattr(self, 'trail_splash') and self.trail_splash:
                self.trail_splash.hide()
                self.trail_splash.close()
                self.trail_splash.deleteLater()
                self.trail_splash = None
                
            self.trail_movie = None
            self.trail_text = None
        except Exception as e:
            logger.error(f"Error in _really_hide_trail_splash: {str(e)}")

    def proceed_to_service(self, username):
        """Modified proceed_to_service with Trail loading splash"""
        # Hide the fullscreen loading first
        self.hide_fullscreen_loading()
        
        # Show the Trail loading splash
        self.show_launch_loading_splash()
        
        # Force the splash to render completely
        QApplication.processEvents()
        
        # Small delay to ensure GIF starts animating
        QTimer.singleShot(300, lambda: self._perform_launch(username))
    def _perform_launch(self, username):
        """Modified _perform_launch with background thread"""
        logger.debug(f"Starting _perform_launch with username: {username}, user_id: {self.logged_in_user_id}")
        
        # Hide the login window
        self.hide()
        
        # Create and start worker thread
        self.launch_worker = LaunchWorker(
            username, 
            self.logged_in_user_id, 
            self.logged_refresh_token, 
            self.logged_access_token
        )
        
        # Connect signals
        self.launch_worker.finished.connect(self._on_launch_success)
        self.launch_worker.error.connect(self._on_launch_error)
        
        # Start the worker
        self.launch_worker.start()

    def _on_launch_success(self):
        """Called when launch completes successfully"""
        logger.debug("Launch completed successfully")
        
        # Hide trail loading splash after successful launch
        self.hide_launch_loading_splash(min_display_time=2.0)
        
        try:
            # Call main_login_page in the main thread (Qt GUI thread)
            logger.debug("Calling main_login_page() in main thread")
            main_login_page(self.logged_in_username, self.logged_in_user_id, 
                        self.logged_refresh_token, self.logged_access_token)
            logger.debug("main_login_page executed successfully")
            
            self.tray_icon.showMessage("Droidal Service", "AGENT FLOW launched successfully.", QSystemTrayIcon.Information)
            self.status_value_lbl.setText(f"Welcome {self.logged_in_username}! AGENT FLOW launched successfully.")
            self.status_value_lbl.setProperty('class', 'LoginStatusSuccess')
            style_loader.apply_stylesheet(self.status_value_lbl)
        except Exception as e:
            logger.error(f"Error calling main_login_page: {str(e)}", exc_info=True)
            self._on_launch_error(str(e))
    def _on_launch_error(self, error_message):
        """Called when launch fails"""
        logger.error(f"Launch error: {error_message}")
        
        # Hide trail loading splash on error
        self.hide_launch_loading_splash(min_display_time=0)
        
        self.status_value_lbl.setText(f"Execution Error: {error_message}")
        self.status_value_lbl.setProperty('class', 'LoginStatusError')
        style_loader.apply_stylesheet(self.status_value_lbl)
        
        # Show the login window again on error
        self.show()
    def closeEvent(self, event):
        """Modified closeEvent with trail splash cleanup"""
        # Hide trail loading splash if visible
        if hasattr(self, 'trail_splash') and self.trail_splash:
            self._really_hide_trail_splash()
        
        # Close detail mode dialogs
        try:
            from PyQt5.QtWidgets import QApplication
            for widget in QApplication.topLevelWidgets():
                try:
                    if widget and hasattr(widget, 'windowTitle'):
                        title = widget.windowTitle()
                        if "Detail Mode" in title or "Validation Logs" in title:
                            print(f"Closing detail mode dialog: {title}")
                            widget.close()
                            widget.deleteLater()
                except Exception as e:
                    print(f"Error closing detail mode dialog: {e}")
        except Exception as e:
            print(f"Error finding detail mode dialogs: {e}")
        
        super().closeEvent(event)

    def cleanup_on_quit(self):
        """Modified cleanup_on_quit with trail splash cleanup"""
        logger.info("Application about to quit. Closing trail splash and detail mode dialogs.")
        
        # Hide trail loading splash if visible
        if hasattr(self, 'trail_splash') and self.trail_splash:
            self._really_hide_trail_splash()
        
        # Close detail mode dialogs
        try:
            from PyQt5.QtWidgets import QApplication
            for widget in QApplication.topLevelWidgets():
                try:
                    if widget and hasattr(widget, 'windowTitle'):
                        title = widget.windowTitle()
                        if "Detail Mode" in title or "Validation Logs" in title:
                            print(f"Closing detail mode dialog on quit: {title}")
                            widget.close()
                            widget.deleteLater()
                except Exception as e:
                    print(f"Error closing detail mode dialog on quit: {e}")
        except Exception as e:
            print(f"Error finding detail mode dialogs on quit: {e}")
    def set_buttons_enabled(self, enabled):
        for button in self.current_buttons:
            try:
                button.setEnabled(enabled)
            except RuntimeError:
                pass

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.drag_position = event.globalPos() - self.frameGeometry().topLeft()
            event.accept()

    def mouseMoveEvent(self, event):
        if hasattr(self, 'drag_position') and event.buttons() == Qt.LeftButton:
            self.move(event.globalPos() - self.drag_position)
            event.accept()

    def closeEvent(self, event):
        # Status popup removed - no cleanup needed
        
        try:
            from PyQt5.QtWidgets import QApplication
            for widget in QApplication.topLevelWidgets():
                try:
                    if widget and hasattr(widget, 'windowTitle'):
                        title = widget.windowTitle()
                        if "Detail Mode" in title or "Validation Logs" in title:
                            print(f"Closing detail mode dialog: {title}")
                            widget.close()
                            widget.deleteLater()
                except Exception as e:
                    print(f"Error closing detail mode dialog: {e}")
        except Exception as e:
            print(f"Error finding detail mode dialogs: {e}")
        
        super().closeEvent(event)

    def cleanup_on_quit(self):
        logger.info("Application about to quit. Closing all status popups and detail mode dialogs.")
        # Status popup removed - no cleanup needed
        
        try:
            from PyQt5.QtWidgets import QApplication
            for widget in QApplication.topLevelWidgets():
                try:
                    if widget and hasattr(widget, 'windowTitle'):
                        title = widget.windowTitle()
                        if "Detail Mode" in title or "Validation Logs" in title:
                            print(f"Closing detail mode dialog on quit: {title}")
                            widget.close()
                            widget.deleteLater()
                except Exception as e:
                    print(f"Error closing detail mode dialog on quit: {e}")
        except Exception as e:
            print(f"Error finding detail mode dialogs on quit: {e}")

if __name__ == '__main__':
    app = QApplication(sys.argv)
    app.setStyle('Fusion')
    style_loader.apply_stylesheet(app)
    app.setWindowIcon(QIcon())

    # Create splash screen with spinner to show immediately
    splash = QWidget()
    splash.setWindowFlags(Qt.SplashScreen | Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
    splash.setAttribute(Qt.WA_TranslucentBackground)

    # Main container with padding
    splash_container = QWidget(splash)
    splash_layout = QVBoxLayout(splash)
    splash_layout.setContentsMargins(0, 0, 0, 0)
    splash_layout.addWidget(splash_container)

    # Inner layout for content
    content_layout = QVBoxLayout(splash_container)
    content_layout.setContentsMargins(40, 40, 40, 40)
    content_layout.setSpacing(30)
    content_layout.setAlignment(Qt.AlignCenter)

    # Logo at the top - full size
    logo_label = QLabel()
    logo_pixmap = QPixmap(resource_path('styles/Icon/logos.png'))
    logo_label.setPixmap(logo_pixmap)  # No scaling - full original size
    logo_label.setAlignment(Qt.AlignCenter)
    # Reduce logo width while keeping aspect ratio
    new_width = 300  # reduced width in pixels
    if not logo_pixmap.isNull() and logo_pixmap.width() > 0:
        ratio = new_width / logo_pixmap.width()
        new_height = int(logo_pixmap.height() * ratio)
        scaled_pixmap = logo_pixmap.scaled(new_width, new_height, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        logo_label.setPixmap(scaled_pixmap)
        logo_label.setFixedSize(scaled_pixmap.size())
    else:
        logo_label.setFixedWidth(new_width)

    # Spinner below logo - full size
    splash_movie = QMovie(resource_path('styles/Icon/spinner.gif'))
    splash_label = QLabel()
    splash_label.setMovie(splash_movie)
    splash_label.setAlignment(Qt.AlignCenter)
    splash_label.setScaledContents(False)
    splash_label.setStyleSheet("background: transparent;")  # Add this line to remove black background # Don't scale the GIF
    # Optional loading text (fixed stylesheet without text-shadow)
    loading_text = QLabel("Loading...")
    loading_text.setAlignment(Qt.AlignCenter)
    loading_text.setStyleSheet("""
        QLabel {
            color: #ffffff;
            font-size: 14px;
            font-weight: 600;
            background: rgba(0, 0, 0, 0.3);  /* Semi-transparent black bg */
        }
    """)

    # Add widgets to layout
    content_layout.addStretch()
    content_layout.addWidget(logo_label)
    content_layout.addWidget(splash_label)
    content_layout.addWidget(loading_text)
    content_layout.addStretch()

    # Transparent background
    splash_container.setStyleSheet("""
        QWidget {
            background: rgba(0, 0, 0, 1.0);
            border-radius: 20px;
        }
    """)

    # Adjust splash size based on actual content size
    # You may need to increase this based on your logo/spinner dimensions
    splash.setFixedSize(600, 500)  # Increased size to accommodate full-size assets
    splash.show()

    # Center splash screen on the screen
    screen_geometry = QApplication.primaryScreen().geometry()
    x = (screen_geometry.width() - splash.width()) // 2
    y = (screen_geometry.height() - splash.height()) // 2
    splash.move(x, y)
    import time
    # Force update to display splash immediately
    splash.update()
    app.processEvents()

    # Start the GIF animation (non-blocking)
    splash_movie.start()

    # Record start time for minimum 5 second display
    start_time = time.time()

    # Initialize the main window (non-blocking)
    window = LoginWindow()

    # Start background thread for heavy tasks
    worker = Worker()
    worker.finished.connect(lambda: hide_splash_and_proceed())
    worker.start()

    def hide_splash_and_proceed():
        # Ensure minimum 5 seconds display
        import time
        elapsed = time.time() - start_time
        if elapsed < 5:
            QTimer.singleShot(int((5 - elapsed) * 1000), lambda: _really_hide_splash())
        else:
            _really_hide_splash()

    def _really_hide_splash():
        splash_movie.stop()
        splash.hide()
        splash.close()
        splash.deleteLater()
        window.check_and_proceed()

    sys.exit(app.exec_())