import subprocess
import sys
import pkg_resources
import os

def ensure_package(package_name: str, version: str):
    package_spec = f"{package_name}=={version}"

    try:
        pkg_resources.require(package_spec)
        print(f"{package_spec} is already installed.")
        return
    except (pkg_resources.DistributionNotFound, pkg_resources.VersionConflict):
        print(f"Installing or upgrading {package_spec} ...")

    # Try to locate system Python
    possible_pythons = [
        sys._MEIPASS + "\\python.exe" if hasattr(sys, "_MEIPASS") else None,
        os.path.join(os.path.dirname(sys.executable), "python.exe"),
        "python",
        "python3"
    ]
    python_exec = next((p for p in possible_pythons if p and os.path.exists(p)), "python")

    # Hide console window (Windows only)
    startupinfo = None
    if os.name == "nt":
        startupinfo = subprocess.STARTUPINFO()
        startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW

    try:
        subprocess.Popen(
            [python_exec, "-m", "pip", "install", "--quiet", "--upgrade", package_spec],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            startupinfo=startupinfo
        )
        print(f"{package_spec} installed successfully.")
    except subprocess.CalledProcessError as e:
        print(f"Failed to install {package_spec}: {e}")

if __name__ == "__main__":
    ensure_package("google-genai", "1.44.0")
