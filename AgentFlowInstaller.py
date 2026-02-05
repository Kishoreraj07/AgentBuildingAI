"""
Agent Flow - Production-ready Windows installer (Patched)
Version: 1.0 (Production-grade)

Features:
- Admin elevation with --elevated flag
- Prevent EXE re-entry when pip spawns helper processes
- Private venv inside INSTALL_PATH (avoids WinError 5)
- Robust pip install logic (uses venv python)
- Rollback on failure (removes partially created files)
- Non-blocking CustomTkinter UI (threaded)
- Detailed logging to C:\Logs\agentflow_installer.log
"""

from __future__ import annotations

import ctypes
import logging
import os
import shutil
import subprocess
import sys
import threading
import time
import zipfile
import venv
from pathlib import Path
from typing import Optional, List, Dict, Any

# ---------------------------
# CRITICAL STARTUP GUARDS
# ---------------------------
# 1) If running as a pip helper process (pip sets PIP_REQ_TRACKER or PYTHONUSERBASE), exit immediately.
#    This prevents PyInstaller-built EXE from being triggered by pip and causing duplicate installers.
if hasattr(sys, "_MEIPASS"):
    if os.environ.get("PIP_REQ_TRACKER") or os.environ.get("PYTHONUSERBASE"):
        # This is a pip helper process — do not run installer logic
        os._exit(0)

# 2) Minimal safe import for requests/ui libs — installer can create venv and install missing libs into it.
try:
    import requests
except Exception:
    requests = None  # we'll use venv python to install requests if needed later

# Optional UI imports (wrapped, installer will still run in CLI if missing)
try:
    import customtkinter as ctk  # type: ignore
    from tkinter import messagebox  # type: ignore
    from PIL import Image  # type: ignore
except Exception:
    ctk = None
    messagebox = None
    Image = None

# ---------------------------
# Configuration
# ---------------------------
APP_NAME = "Agent Flow"
INSTALL_PATH = Path(r"C:\DroidalAgentFlow")
LOG_DIR = Path(r"C:\Logs")
LOG_FILE = LOG_DIR / "agentflow_installer.log"
MANIFEST_URL = "https://dev-cloud.droidal.com/app/version/list_file"
PYTHON_MIN_VERSION = (3, 10)
PYTHON_ENV_FILE = INSTALL_PATH / "python_env.txt"
DOWNLOAD_TIMEOUT = 60
DOWNLOAD_RETRIES = 3
ELEVATION_FLAG = "--elevated"
VENV_DIR = INSTALL_PATH / "venv"
VENV_PY = VENV_DIR / "Scripts" / "python.exe"  # Windows path

# Configure logging (ensure folder)
LOG_DIR.mkdir(parents=True, exist_ok=True)
logging.basicConfig(
    filename=str(LOG_FILE),
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)

# Console fallback logging for debug runs
console = logging.StreamHandler()
console.setLevel(logging.INFO)
logging.getLogger().addHandler(console)

# ---------------------------
# Elevation helpers
# ---------------------------
def is_admin() -> bool:
    try:
        return ctypes.windll.shell32.IsUserAnAdmin() != 0
    except Exception:
        return False


def relaunch_as_admin():
    """Relaunch current script as admin using ShellExecute 'runas', pass ELEVATION_FLAG, then exit."""
    params = f'"{sys.argv[0]}" {ELEVATION_FLAG}'
    try:
        ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.executable, params, None, 1)
        logging.info("Requested elevation via ShellExecuteW")
    except Exception as e:
        logging.exception("Failed to relaunch as admin: %s", e)
    # Ensure original process stops immediately
    os._exit(0)


# ---------------------------
# Registry & Python detection
# ---------------------------
import winreg

def python_path_from_registry() -> Optional[str]:
    roots = [(winreg.HKEY_LOCAL_MACHINE, "HKLM"), (winreg.HKEY_CURRENT_USER, "HKCU")]
    sub_keys = [
        r"SOFTWARE\Python\PythonCore",
        r"SOFTWARE\Wow6432Node\Python\PythonCore",
    ]
    for root, _ in roots:
        for sk in sub_keys:
            try:
                with winreg.OpenKey(root, sk) as base:
                    i = 0
                    while True:
                        try:
                            ver = winreg.EnumKey(base, i)
                            i += 1
                            install_key = f"{sk}\\{ver}\\InstallPath"
                            try:
                                with winreg.OpenKey(root, install_key) as ip:
                                    install_path, _ = winreg.QueryValueEx(ip, None)
                                    candidate = Path(install_path) / "python.exe"
                                    if candidate.exists():
                                        logging.info(f"Found Python via registry: {candidate}")
                                        return str(candidate)
                            except Exception:
                                continue
                        except OSError:
                            break
            except Exception:
                continue
    return None

# =================================================================
# PYTHON VERSION DETECTION
# =================================================================
def is_python_installed(min_version=(3, 10)):
    commands = [
        ["python", "--version"],
        ["python3", "--version"]
    ]
 
    for cmd in commands:
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, shell=False)
            output = result.stdout.strip() or result.stderr.strip()
 
            if output.startswith("Python"):
                version_str = output.split()[1]
                major, minor, *_ = map(int, version_str.split("."))
                logging.info(f"Detected Python version: {version_str}")
 
                if (major, minor) >= min_version:
                    logging.info("Python satisfies minimum requirement.")
                    return True
        except Exception as e:
            logging.warning(f"Python detection failed for {cmd}: {e}")
 
    logging.info("Python version below minimum or not installed.")
    return False

 
 
# =================================================================
# FILE DOWNLOADS
# =================================================================
def download_python_installer(download_url, save_path):
    try:
        if os.path.exists(save_path):
            logging.info("Installer already exists at: %s", save_path)
            return True
        logging.info("Downloading Python from %s", download_url)
        response = requests.get(download_url, stream=True)
        if response.status_code == 200:
            with open(save_path, 'wb') as f:
                for chunk in response.iter_content(1024):
                    f.write(chunk)
            logging.info("Download completed: %s", save_path)
            return True
        else:
            logging.error("Failed to download Python installer: HTTP %s", response.status_code)
            return False
    except Exception as e:
        logging.error("Download error: %s", str(e))
        return False
 
 
def install_python_silently(installer_path):
    try:
        command = [
            str(installer_path),          # str() ensures Path → string
            "/quiet",
            "InstallAllUsers=1",
            "PrependPath=1",
            "Include_test=0",
            "Include_pip=1"
        ]

        logging.info("Running installer: %s", " ".join(command))

        result = subprocess.run(
            command,
            shell=False,                  # ← IMPORTANT: shell=False
            capture_output=True,
            text=True,
            creationflags=subprocess.CREATE_NO_WINDOW
        )

        logging.info("Return code: %s | stderr: %s", result.returncode, result.stderr.strip())
        return result.returncode == 0

    except FileNotFoundError:
        logging.error("Installer executable not found: %s", installer_path)
        return False
    except Exception as e:
        logging.error("Installation exception: %s", e)
        return False


COMMON_PYTHON_LOCATIONS = [
    Path(r"C:\Program Files\Python312\python.exe"),
    Path(r"C:\Program Files\Python311\python.exe"),
    Path(r"C:\Program Files\Python310\python.exe"),
    Path(r"C:\Python312\python.exe"),
    Path(r"C:\Python311\python.exe"),
    Path(r"C:\Python310\python.exe"),
]


def find_python_path() -> str:
    """
    Find a usable python executable.
    PyInstaller EXE must NOT treat sys.executable as python.
    """

    running_frozen = hasattr(sys, "_MEIPASS")

    # 1. Prefer private venv
    try:
        if VENV_PY.exists():
            logging.info(f"Using venv python: {VENV_PY}")
            return str(VENV_PY)
    except Exception:
        pass

    # 2. sys.executable ONLY if NOT frozen
    if not running_frozen:
        try:
            cur = Path(sys.executable)
            if cur.exists():
                logging.info(f"sys.executable = {cur}")
                return str(cur)
        except Exception:
            pass
    else:
        logging.info("Skipping sys.executable because running from PyInstaller EXE")

    # 3. Registry
    try:
        reg = python_path_from_registry()
        if reg:
            logging.info(f"Found python via registry: {reg}")
            return reg
    except Exception:
        pass

    # 4. Common Python locations
    for p in COMMON_PYTHON_LOCATIONS:
        if p.exists():
            logging.info(f"Found python in common location: {p}")
            return str(p)

    # 5. PATH lookup
    try:
        r = subprocess.run(["where", "python"], capture_output=True, text=True)
        if r.returncode == 0:
            path = r.stdout.splitlines()[0].strip()
            logging.info(f"Found python via PATH: {path}")
            return path
    except Exception:
        pass

    logging.warning("Falling back to default 'python'")
    return "python"



def save_python_path(path: str) -> None:
    try:
        INSTALL_PATH.mkdir(parents=True, exist_ok=True)
        PYTHON_ENV_FILE.write_text(f"PYTHON_PATH={path}", encoding="utf-8")
        logging.info(f"Wrote python path to {PYTHON_ENV_FILE}")
    except Exception:
        logging.exception("Failed to save python path")


def load_saved_python_path() -> Optional[str]:
    try:
        if PYTHON_ENV_FILE.exists():
            content = PYTHON_ENV_FILE.read_text(encoding="utf-8").strip()
            if content.startswith("PYTHON_PATH="):
                return content.split("=", 1)[1].strip()
    except Exception:
        logging.debug("Failed to load saved python path")
    return None

CREATE_NO_WINDOW = 0x08000000
# ---------------------------
# Virtualenv helpers (use stdlib venv)
# ---------------------------
def create_private_venv() -> str:
    """
    Create a venv using REAL system Python, not the PyInstaller runtime.
    """
    venv_python = VENV_PY
    venv_dir = VENV_DIR

    if venv_python.exists():
        logging.info(f"Private venv already exists: {venv_python}")
        return str(venv_python)

    # Get real python installation
    real_python = find_python_path()
    logging.info(f"Using real system python to create venv: {real_python}")

    try:
        # Run: python -m venv <path>
        cmd = [
            real_python,
            "-m",
            "venv",
            str(venv_dir)
        ]
        logging.info("Creating venv via subprocess: " + " ".join(cmd))

        env = os.environ.copy()
        # Clear dangerous env variables
        env.pop("PYTHONHOME", None)
        env.pop("PYTHONPATH", None)

        result = subprocess.run(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            creationflags=CREATE_NO_WINDOW,
            text=True,
            check=True,
        )

        logging.info("venv creation exit code: %s, stderr: %s",
                     result.returncode,
                     result.stderr.strip())

        if result.returncode != 0:
            raise RuntimeError("python -m venv failed")

        # Now verify python.exe exists
        if not venv_python.exists():
            alt = venv_dir / "bin" / "python"
            if alt.exists():
                logging.info("Using alternate venv python: %s", alt)
                return str(alt)
            raise RuntimeError("venv python not found after create")

        logging.info("Private venv created successfully")
        return str(venv_python)

    except Exception as e:
        logging.exception("Failed to create venv: %s", e)
        raise RuntimeError(f"Failed to create venv: {e}")


# ---------------------------
# Download helpers (simple, reliable)
# ---------------------------
def download_file(url: str, dest: Path, timeout: int = DOWNLOAD_TIMEOUT, retries: int = DOWNLOAD_RETRIES) -> bool:
    """Download a file with streaming and retry logic."""
    try:
        # ensure requests is available in this runtime; if not, attempt a simple fallback using urllib
        import requests as _requests
    except Exception:
        _requests = None

    for attempt in range(1, retries + 1):
        try:
            dest.parent.mkdir(parents=True, exist_ok=True)
            if _requests:
                with _requests.get(url, stream=True, timeout=timeout) as r:
                    r.raise_for_status()
                    content_type = r.headers.get("content-type", "")
                    if "text/html" in content_type.lower():
                        logging.error("Download returned HTML (probably error page)")
                        return False
                    with open(dest, "wb") as f:
                        for chunk in r.iter_content(chunk_size=8192):
                            if chunk:
                                f.write(chunk)
            else:
                # fallback: urllib
                from urllib.request import urlopen
                with urlopen(url, timeout=timeout) as r:
                    data = r.read()
                    with open(dest, "wb") as f:
                        f.write(data)
            logging.info(f"Downloaded {url} → {dest}")
            return True
        except Exception as e:
            logging.warning(f"Download attempt {attempt} failed for {url}: {e}")
            time.sleep(1 * attempt)
    logging.error(f"All downloads failed for {url}")
    return False

# ---------------------------
# Installer actions
# ---------------------------
def extract_zip(zip_path: Path, dest_dir: Path) -> bool:
    try:
        with zipfile.ZipFile(str(zip_path), "r") as z:
            z.extractall(str(dest_dir))
        logging.info(f"Extracted ZIP: {zip_path}")
        return True
    except Exception:
        logging.exception("ZIP extraction failed")
        return False


def _clean_env_for_pip(child_env: Optional[Dict[str, str]] = None) -> Dict[str, str]:
    """
    Return a copy of the current environment safe for launching pip/python subprocesses.
    Remove PIP_REQ_TRACKER and other potentially confusing variables so child python doesn't trigger EXE re-entry.
    """
    env = dict(os.environ)
    for key in ("PIP_REQ_TRACKER", "PYTHONUSERBASE", "PYTHONPATH", "PYTHONHOME"):
        env.pop(key, None)
    # Allow override
    if child_env:
        env.update(child_env)
    return env


def pip_install_requirements(python_exe: str, requirements_file: Path, timeout: int = None) -> bool:
    """
    Run: <python_exe> -m pip install -r requirements.txt
    Silent execution (NO cmd popup).
    """
    if not requirements_file.exists():
        logging.error("requirements.txt missing")
        return False

    cmd = [
        str(python_exe), "-m", "pip", "install",
        "--disable-pip-version-check",
        "-r", str(requirements_file)
    ]
    logging.info(f"Running pip: {' '.join(cmd)}")

    env = _clean_env_for_pip()

    try:
        proc = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            env=env,
            creationflags=CREATE_NO_WINDOW  # << Hides CMD window
        )
    except Exception:
        logging.exception("Failed to spawn pip process")
        return False

    try:
        for line in proc.stdout:
            logging.info(f"pip: {line.strip()}")
        proc.wait()
        logging.info(f"pip exit code {proc.returncode}")
        return proc.returncode == 0

    except Exception:
        logging.exception("Error while running pip")
        try:
            proc.kill()
        except Exception:
            pass
        return False


# ---------------------------
# Rollback helpers
# ---------------------------
class RollbackTracker:
    def __init__(self):
        self.created_paths: List[Path] = []

    def note(self, p: Path):
        try:
            self.created_paths.append(p)
        except Exception:
            pass

    def rollback(self):
        # Attempt to remove created files/folders (best effort)
        for p in reversed(self.created_paths):
            try:
                if p.is_file():
                    p.unlink(missing_ok=True)
                elif p.is_dir():
                    shutil.rmtree(p, ignore_errors=True)
                logging.info(f"Rolled back {p}")
            except Exception:
                logging.exception(f"Failed to rollback {p}")


# ---------------------------
# Desktop shortcut helper
# ---------------------------
def create_desktop_shortcut(target: Path, name: str = "AgentFlow"):
    try:
        desktop = Path(os.path.join(os.environ["USERPROFILE"], "Desktop"))
        shortcut_path = desktop / f"{name}.lnk"
        import win32com.client  # requires pywin32
        wscript = win32com.client.Dispatch("WScript.Shell")
        shortcut = wscript.CreateShortcut(str(shortcut_path))
        shortcut.TargetPath = str(target)
        shortcut.WorkingDirectory = str(target.parent)
        shortcut.IconLocation = str(target)
        shortcut.Save()
        logging.info(f"Desktop shortcut created: {shortcut_path}")
        return True
    except Exception:
        logging.exception("Failed to create desktop shortcut")
        return False


# ---------------------------
# UI: CustomTkinter installer (non-blocking)
# ---------------------------
def resource_path(relative_path):
    # When run from PyInstaller .exe, _MEIPASS is temp path to bundled files
    if hasattr(sys, "_MEIPASS"):
        return os.path.join(sys._MEIPASS, relative_path)
    return os.path.join(os.path.abspath("."), relative_path)

if ctk is not None:
    class InstallerUI(ctk.CTk):
        def __init__(self):
            super().__init__()
            self.title(f"{APP_NAME} Installer")
            self.geometry("900x600")
            self.animating = False
            self.anim_phase = 0.0
            # Basic icon
            try:
                logo = resource_path("styles/Icon/app_icon.png") if 'resource_path' in globals() else "styles/Icon/app_icon.png"
                if Path(logo).exists():
                    Image.open(logo).save("logo.ico", format="ICO", sizes=[(32, 32)])
                    self.iconbitmap("logo.ico")
            except Exception:
                pass

            self.main_frame = ctk.CTkFrame(self, corner_radius=12)
            self.main_frame.pack(fill="both", expand=True, padx=20, pady=20)

            header = ctk.CTkLabel(self.main_frame, text=f"{APP_NAME} Setup", font=("Segoe UI", 22, "bold"))
            header.pack(pady=(8, 16))

            body = ctk.CTkFrame(self.main_frame)
            body.pack(fill="both", expand=True, padx=10)

            left = ctk.CTkFrame(body, width=320)
            left.pack(side="left", fill="y", padx=(0, 12))

            ctk.CTkLabel(left, text="Install location:", font=("Segoe UI", 12, "bold")).pack(anchor="w")
            ctk.CTkLabel(left, text=str(INSTALL_PATH), font=("Consolas", 10), wraplength=300).pack(anchor="w", pady=(4, 12))

            ctk.CTkLabel(left, text="System Requirements", font=("Segoe UI", 12, "bold")).pack(anchor="w")
            for r in ["Windows 10/11", "500 MB free disk", "Internet connection"]:
                ctk.CTkLabel(left, text=f"✓ {r}", font=("Segoe UI", 11)).pack(anchor="w")

            right = ctk.CTkFrame(body)
            right.pack(side="left", fill="both", expand=True)

            self.status = ctk.CTkLabel(right, text="Ready", font=("Segoe UI", 12))
            self.status.pack(anchor="w")

            self.progress = ctk.CTkProgressBar(right)
            self.progress.set(0)
            self.progress.pack(fill="x", pady=(8, 10))

            self.progress_pct = ctk.CTkLabel(right, text="0%", font=("Segoe UI", 11, "bold"))
            self.progress_pct.pack(anchor="e")

            self.steps_frame = ctk.CTkFrame(right)
            self.steps_frame.pack(fill="both", expand=True, pady=(10, 0))

            self.step_labels = []
            steps = [
                "Check / Download AgentFlow Dependencies",
                "Install Droidal package",
                "Create folders",
                "Download app files",
                "Download requirements",
                "Install dependencies",
                "Finalize"
            ]
            for s in steps:
                lbl = ctk.CTkLabel(self.steps_frame, text=s, anchor="w")
                lbl.pack(fill="x", padx=6, pady=3)
                self.step_labels.append(lbl)

            btn_frame = ctk.CTkFrame(self.main_frame)
            btn_frame.pack(fill="x", pady=(12, 6))

            self.cancel_btn = ctk.CTkButton(btn_frame, text="Cancel", width=120, command=self._on_cancel)
            self.cancel_btn.pack(side="left", padx=(0, 8))

            self.install_btn = ctk.CTkButton(btn_frame, text="Install", width=140, command=self.start_install)
            self.install_btn.pack(side="left")

            self.finish_btn = ctk.CTkButton(btn_frame, text="Finish", width=120, state="disabled", command=self.destroy)

            self.installation_failed = False
            self._thread: Optional[threading.Thread] = None
            self.rollback = RollbackTracker()

        # basic helpers
        def update_status(self, text: str):
            self.after(0, lambda: self.status.configure(text=text))

        def start_progress_animation(self):
            """Start smooth looping animation for the progress bar."""
            if not self.animating:
                self.animating = True
                self._animate_progress()

        def stop_progress_animation(self):
            """Stop animation when real progress is set."""
            self.animating = False

        def _animate_progress(self):
            """Internal smooth animation loop."""
            if not self.animating:
                return

            # Cosine bounce animation (smooth)
            import math
            self.anim_phase += 0.08
            val = (math.sin(self.anim_phase) + 1) / 2  # 0 → 1 → 0 loop
            self.progress.set(val)
            self.progress_pct.configure(text="...")  # Animated indicator

            # Schedule next frame (every 30ms = 33 FPS)
            self.after(30, self._animate_progress)


        def set_step_ok(self, idx: int, ok: bool = True):
            if 0 <= idx < len(self.step_labels):
                label = self.step_labels[idx]
                prefix = "✓ " if ok else "✗ "
                self.after(0, lambda: label.configure(text=prefix + label.cget("text").lstrip("✓ ✗ ")))

        def set_progress(self, fraction: float):
            self.stop_progress_animation()  # stop animation before setting real progress
            frac = max(0.0, min(1.0, fraction))
            self.after(0, lambda: self.progress.set(frac))
            self.after(0, lambda: self.progress_pct.configure(text=f"{int(frac*100)}%"))

        def _on_cancel(self):
            if self._thread and self._thread.is_alive():
                if messagebox.askyesno("Cancel", "Installation is in progress. Are you sure?"):
                    logging.info("User cancelled - exiting")
                    os._exit(1)
            else:
                self.destroy()

        def start_install(self):
            self.install_btn.configure(state="disabled")
            self.cancel_btn.configure(state="disabled")
            self.update_status("Starting installation...")
            self._thread = threading.Thread(target=self._install_sequence, daemon=True)
            self._thread.start()

        # ---------------------------
        # Core install sequence (threaded)
        # ---------------------------
        def _install_sequence(self):
            try:
                self.update_status("Preparing installation folder...")
                self.set_progress(0.02)
                INSTALL_PATH.mkdir(parents=True, exist_ok=True)
                self.rollback.note(INSTALL_PATH)

                # Step 1: Ensure or create venv BEFORE installing packages
                self.update_status("Setting up private Python environment...")
                self.set_progress(0.07)
                # system_python = ensure_python_available()
                installer_url = "https://www.python.org/ftp/python/3.12.1/python-3.12.1-amd64.exe"
                # installer_path = Path(r"C:\Temp\python-3.12.8-amd64.exe")
                import tempfile
                installer_path = Path(tempfile.gettempdir()) / "python-3.12.1-amd64.exe"
                self.start_progress_animation()
                download_python_installer(installer_url,installer_path)
                def install_python():
                    if is_python_installed((3, 10)):
                        logging.info("Python ready after fresh check")
                        return True

                    # installer_path = Path(r"C:\Temp\python-3.12.1-amd64.exe")
                    if not installer_path.exists():
                        logging.error("Python installer missing!")
                        self.installation_failed = True
                        return False

                    self.after(0, lambda: self.status_text.configure(text="Installing Python (silent)..."))
                    return install_python_silently(str(installer_path))
                install_python()
                try:
                    python_exec = create_private_venv()
                except Exception as e:
                    raise RuntimeError(f"Failed to create private venv: {e}")

                save_python_path(python_exec)
                self.start_progress_animation()
                self.set_step_ok(0, True)

                # Step 2: Create folders & secure
                self.update_status("Creating application folders...")
                self.set_progress(0.2)
                (INSTALL_PATH / "data").mkdir(exist_ok=True)
                (INSTALL_PATH / "logs").mkdir(exist_ok=True)
                self.rollback.note(INSTALL_PATH / "data")
                self.rollback.note(INSTALL_PATH / "logs")
                try:
                    make_folder_full_access(INSTALL_PATH)
                except Exception:
                    logging.debug("Failed to set ACLs (non-fatal)")
                self.set_step_ok(2, True)

                # Step 3: Fetch manifest + files
                self.update_status("Downloading application files...")
                self.set_progress(0.35)
                try:
                    manifest = requests.get(MANIFEST_URL, timeout=30).json()
                except Exception:
                    logging.exception("Failed to fetch manifest")
                    manifest = {}
                files = manifest.get("files", [])
                total_files = len(files)
                downloaded_files = 0
                self.start_progress_animation()
                for idx, f in enumerate(files, start=1):
                    name = f.get("name")
                    url = f.get("url")
                    if not name or not url:
                        continue
                    target = INSTALL_PATH / name
                    self.update_status(f"Downloading {name} ({idx}/{total_files})")
                    if not download_file(url, target):
                        raise RuntimeError(f"Failed to download {name}")
                    self.rollback.note(target)
                    if name.lower().endswith(".zip"):
                        self.update_status(f"Extracting {name}...")
                        if not extract_zip(target, INSTALL_PATH):
                            raise RuntimeError(f"Failed to extract {name}")
                        try:
                            target.unlink()
                        except:
                            pass
                    downloaded_files += 1
                    self.set_progress(0.35 + 0.20 * (downloaded_files / max(1, total_files)))

                self.set_step_ok(3, True)

                # Step 4: requirements
                self.update_status("Preparing requirements...")
                self.set_progress(0.6)
                req_dest = INSTALL_PATH / "requirements.txt"
                requirements_url = None
                for f in files:
                    if f.get("name", "").lower() == "requirements.txt":
                        requirements_url = f.get("url")
                        break
                if requirements_url:
                    if not download_file(requirements_url, req_dest):
                        logging.warning("Failed to download requirements.txt from manifest; using fallback")
                else:
                    logging.warning("requirements.txt not present in manifest; using fallback")
                if not req_dest.exists():
                    req_dest.write_text("requests>=2.25.0\ncustomtkinter>=5.0.0\nPillow>=9.0.0", encoding="utf-8")
                self.rollback.note(req_dest)
                self.set_step_ok(4, True)

                # Step 5: Install dependencies into venv
                self.update_status("Installing AgentFlow packages (in private venv)...")
                self.set_progress(0.75)
                python_exec = load_saved_python_path() or str(VENV_PY)
                self.start_progress_animation()
                ok = pip_install_requirements(python_exec, req_dest)
                if not ok:
                    raise RuntimeError("Dependency installation failed")
                self.start_progress_animation()
                self.set_step_ok(5, True)

                # Step 6: Write config, finalize
                self.update_status("Finalizing installation...")
                self.set_progress(0.92)
                self.start_progress_animation()

                cfg = INSTALL_PATH / "config.ini"
                cfg.write_text("[Application]\nname=AgentFlow\nversion=1.0.0\ninstalled=true", encoding="utf-8")
                self.rollback.note(cfg)
                self.set_step_ok(6, True)

                (INSTALL_PATH / "logs").mkdir(exist_ok=True)
                (INSTALL_PATH / "logs" / "install_finished.txt").write_text(time.strftime("%Y-%m-%d %H:%M:%S"))
                

                self.update_status("Installation complete — launching (if available)...")
                try:
                    messagebox.showinfo("Installed", f"{APP_NAME} installed at {INSTALL_PATH}")
                except Exception:
                    pass

                exe = INSTALL_PATH / "AgentFlow.exe"
                if exe.exists():
                    try:
                        subprocess.Popen([str(exe)], cwd=str(INSTALL_PATH), shell=False)
                    except Exception:
                        try:
                            subprocess.Popen(f'start "" "{exe}"', shell=True, cwd=str(INSTALL_PATH))
                        except Exception:
                            logging.warning("Could not launch installed exe")

                create_desktop_shortcut(exe, "AgentFlow")
                self.set_progress(1.0)
                self.after(0, lambda: self.finish_btn.pack(side="left", padx=8))
                self.after(0, lambda: self.finish_btn.configure(state="normal"))
                logging.info("Installation finished successfully")

            except Exception as e:
                logging.exception("Installation failed: %s", e)
                self.installation_failed = True
                self.update_status("Installation failed — performing rollback")
                try:
                    self.rollback.rollback()
                except Exception:
                    logging.exception("Rollback encountered errors")
                try:
                    messagebox.showerror("Installation Failed", f"{e}\nSee log: {LOG_FILE}")
                except Exception:
                    pass
                self.after(0, lambda: self.cancel_btn.configure(state="normal"))


else:
    InstallerUI = None  # UI not available; CLI will be used


# ---------------------------
# CLI helpers (non-UI mode)
# ---------------------------
def is_python_installed(min_version=PYTHON_MIN_VERSION) -> bool:
    candidates = ["python", "python3"]
    for c in candidates:
        try:
            r = subprocess.run([c, "--version"], capture_output=True, text=True)
            out = (r.stdout or r.stderr or "").strip()
            if out.lower().startswith("python"):
                ver = out.split()[1]
                major, minor = map(int, ver.split(".")[:2])
                if (major, minor) >= min_version:
                    logging.info(f"Detected system python {ver} via {c}")
                    return True
        except Exception:
            continue
    return False


def make_folder_full_access(path: Path):
    # Best effort; non-fatal if fails
    try:
        import win32security
        import ntsecuritycon as con

        sd = win32security.GetFileSecurity(str(path), win32security.DACL_SECURITY_INFORMATION)
        dacl = win32security.ACL()
        everyone, _, _ = win32security.LookupAccountName("", "Everyone")
        dacl.AddAccessAllowedAce(win32security.ACL_REVISION, con.FILE_ALL_ACCESS, everyone)
        sd.SetSecurityDescriptorDacl(1, dacl, 0)
        win32security.SetFileSecurity(str(path), win32security.DACL_SECURITY_INFORMATION, sd)
        logging.info(f"Granted full access to {path}")
    except Exception:
        logging.debug("make_folder_full_access not applied")


# ---------------------------
# Main entry
# ---------------------------
def main():
    # Elevation guard: relaunch if not elevated (only once)
    if os.name == "nt" and not is_admin() and ELEVATION_FLAG not in sys.argv:
        relaunch_as_admin()

    # If running under non-admin but with --elevated flag, still check is_admin() to avoid double
    if InstallerUI is not None:
        try:
            app = InstallerUI()
            app.mainloop()
            return
        except Exception:
            logging.exception("GUI launch failed — falling back to CLI")

    # CLI fallback sequence (simplified mirror of UI steps)
    logging.info("Running in CLI fallback mode")
    rb = RollbackTracker()
    try:
        INSTALL_PATH.mkdir(parents=True, exist_ok=True)
        rb.note(INSTALL_PATH)
        # Create venv
        python_exec = create_private_venv()
        save_python_path(python_exec)
        # Download manifest
        try:
            import requests as _r
            manifest = _r.get(MANIFEST_URL, timeout=30).json()
        except Exception:
            manifest = {}
        files = manifest.get("files", [])
        for f in files:
            name = f.get("name"); url = f.get("url")
            if not name or not url:
                continue
            target = INSTALL_PATH / name
            if not download_file(url, target):
                raise RuntimeError(f"Failed to download {name}")
            rb.note(target)
            if name.lower().endswith(".zip"):
                if not extract_zip(target, INSTALL_PATH):
                    raise RuntimeError(f"Zip extract failed: {name}")
                try:
                    target.unlink()
                except Exception:
                    pass
        # requirements
        req_dest = INSTALL_PATH / "requirements.txt"
        if not req_dest.exists():
            req_dest.write_text("requests>=2.25.0\ncustomtkinter>=5.0.0\nPillow>=9.0.0", encoding="utf-8")
            rb.note(req_dest)
        # pip install
        if not pip_install_requirements(python_exec, req_dest):
            raise RuntimeError("Dependency installation failed")
        # finalize
        cfg = INSTALL_PATH / "config.ini"
        cfg.write_text("[Application]\nname=AgentFlow\nversion=1.0.0\ninstalled=true", encoding="utf-8")
        rb.note(cfg)
        (INSTALL_PATH / "logs").mkdir(exist_ok=True)
        (INSTALL_PATH / "logs" / "install_finished.txt").write_text(time.strftime("%Y-%m-%d %H:%M:%S"))
        logging.info("CLI installation completed successfully")
    except Exception as e:
        logging.exception("CLI installation failed: %s", e)
        try:
            rb.rollback()
        except Exception:
            logging.exception("Rollback failed")
        print(f"Installation failed: {e}. See log: {LOG_FILE}")


if __name__ == "__main__":
    main()
