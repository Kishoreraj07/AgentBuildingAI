import subprocess
import shutil
import os
import sys

def is_python_installed():
    """Check if python is available in PATH."""
    return shutil.which("python") is not None or shutil.which("python3") is not None

def install_python():
    """Run the local Python installer silently."""
    # installer_path = r"C:\DroidalAgentFlow\python-3.12.1-amd64.exe"
    installer_path = os.path.join(os.path.dirname(sys.executable), "python-3.12.1-amd64.exe")
    if not os.path.exists(installer_path):
        print(f"❌ Installer not found: {installer_path}")
        return False

    print(f"🚀 Installing Python from {installer_path} ...")
    try:
        subprocess.run(
            [
                installer_path
            ]
        )
        print("✅ Python installed successfully.")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Installation failed: {e}")
        return False

def main():
    if is_python_installed():
        print("✅ Python is already installed.")
    else:
        print("⚙️ Python not found. Starting installation...")
        install_python()

# if __name__ == "__main__":
#     main()
