"""
Subprocess-based AGENT FLOW Agent Runner
This module provides a function to run AGENT FLOW Agent using local Python environment
instead of importing modules directly, solving PyInstaller module limitations.
"""

import subprocess
import shutil
import os
import sys

def install_requirements_subprocess():
    """
    Install required packages from requirements.txt using subprocess.
    This ensures all dependencies are installed before running the agent.
    
    Returns:
        tuple: (success: bool, output: str, error: str)
    """
    try:
        current_dir = os.getcwd()
        
        # Check if the requirements.txt file exists
        requirements_file = os.path.join(current_dir, "code_py", "requirements.txt")
        if not os.path.exists(requirements_file):
            error_msg = f"Requirements file not found: {requirements_file}"
            print(f"⚠️ {error_msg}")
            return False, "", error_msg
        
        print(f"✓ Found requirements file: {requirements_file}")
        
        # Find Python executable
        python_executable = None
        
        # Try to find Python in common locations
        # possible_python_paths = [
        #     "python",  # Try system PATH first
        #     "python3",
        #     r"C:\Program Files\Python312\python.exe",
        #     r"C:\Program Files\Python311\python.exe", 
        #     r"C:\Program Files\Python310\python.exe",
        #     r"C:\Program Files (x86)\Python312\python.exe",
        #     r"C:\Program Files (x86)\Python311\python.exe",
        #     r"C:\Program Files (x86)\Python310\python.exe",
        #     r"C:\Users\{}\AppData\Local\Programs\Python\Python312\python.exe".format(os.getenv('USERNAME', '')),
        #     r"C:\Users\{}\AppData\Local\Programs\Python\Python311\python.exe".format(os.getenv('USERNAME', '')),
        #     r"C:\Users\{}\AppData\Local\Programs\Python\Python310\python.exe".format(os.getenv('USERNAME', ''))
        # ]
        
        # for python_path in possible_python_paths:
        #     try:
        #         if python_path in ["python", "python3"]:
        #             # Check if python is in PATH
        #             if shutil.which(python_path):
        #                 python_executable = python_path
        #                 print(f"✓ Found Python in PATH: {python_path}")
        #                 break
        #         else:
        #             # Check if specific path exists
        #             if os.path.exists(python_path):
        #                 python_executable = python_path
        #                 print(f"✓ Found Python at: {python_path}")
        #                 break
        #     except Exception as e:
        #         continue
        python_executable=find_python_executable()
        
        if not python_executable:
            error_msg = "Could not find local Python installation. Please ensure Python is installed and accessible."
            print(f"❌ {error_msg}")
            return False, "", error_msg
        
        print(f"📦 Installing packages from requirements.txt...")
        print(f"   Using Python: {python_executable}")
        
        # Execute pip install command
        result = subprocess.run(
            [python_executable, "-m", "pip", "install", "-r", requirements_file],
            cwd=current_dir,
            capture_output=True,
            text=True,
            timeout=300,  # 5 minute timeout
            creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0  # Hide console window on Windows
        )
        
        # Print output for debugging
        output_text = ""
        error_text = ""
        
        if result.stdout:
            output_text = result.stdout
            print("📄 Pip Install Output:")
            print(result.stdout)
        
        if result.stderr:
            error_text = result.stderr
            # Pip often sends non-error messages to stderr, so don't treat all stderr as errors
            print("ℹ️ Pip Install Messages:")
            print(result.stderr)
        
        # Check return code
        if result.returncode != 0:
            error_msg = f"Package installation failed with return code {result.returncode}"
            if result.stderr:
                error_msg += f"\n\nError Output:\n{result.stderr}"
            if result.stdout:
                error_msg += f"\n\nStandard Output:\n{result.stdout}"
            print(f"❌ {error_msg}")
            return False, output_text, error_msg
        
        print("✅ Package installation completed successfully")
        return True, output_text, error_text
            
    except subprocess.TimeoutExpired:
        error_message = "Package installation timed out after 5 minutes"
        print(f"⏱️ {error_message}")
        return False, "", error_message
    except Exception as e:
        error_message = f"Error during package installation: {str(e)}"
        print(f"❌ {error_message}")
        import traceback
        traceback.print_exc()
        return False, "", error_message

def find_python_executable():
    """
    Always use the venv Python installed by the installer.
    """

    # Use raw string or double backslashes
    venv_python = r"C:\DroidalAgentFlow\venv\Scripts\python.exe"

    if os.path.exists(venv_python):
        print(f"✓ Found venv Python at: {venv_python}")
        return venv_python

    print("❌ venv Python not found. Expected:", venv_python)
    return None

def run_aba_agent_subprocess():
    """
    Execute AGENT FLOW Agent using bundled Python environment via subprocess.
    This solves the PyInstaller limitation where new modules in execute_code.py
    are not available in the built .exe file.
    
    Returns:
        tuple: (success: bool, output: str, error: str)
    """
    try:
        current_dir = os.getcwd()
        try:
            install_requirements_subprocess()
        except Exception as e:
            pass

        # Check if the execute_code.py file exists
        execute_code_file = os.path.join(current_dir, "code_py", "execute_code.py")
        if not os.path.exists(execute_code_file):
            error_msg = f"Execute code file not found: {execute_code_file}"
            print(f" {error_msg}")
            return False, "", error_msg
        
        print(f" Found execute code file: {execute_code_file}")
        
        # Determine if we're running from PyInstaller bundle
        if hasattr(sys, '_MEIPASS'):
            # Running from PyInstaller bundle - find local Python instead of using bundled
            bundle_dir = sys._MEIPASS
            exe_dir = os.path.dirname(sys.executable)
            
            print(f" Running from PyInstaller bundle: {bundle_dir}")
            print(f" Executable directory: {exe_dir}")
            
            # Find local Python executable (don't use sys.executable as it's the .exe)
            python_executable = None
            
            # Try to find Python in common locations
            # possible_python_paths = [
            #     "python",  # Try system PATH first
            #     "python3",
            #     r"C:\Program Files\Python312\python.exe",
            #     r"C:\Program Files\Python311\python.exe", 
            #     r"C:\Program Files\Python310\python.exe",
            #     r"C:\Program Files (x86)\Python312\python.exe",
            #     r"C:\Program Files (x86)\Python311\python.exe",
            #     r"C:\Program Files (x86)\Python310\python.exe",
            #     r"C:\Users\{}\AppData\Local\Programs\Python\Python312\python.exe".format(os.getenv('USERNAME', '')),
            #     r"C:\Users\{}\AppData\Local\Programs\Python\Python311\python.exe".format(os.getenv('USERNAME', '')),
            #     r"C:\Users\{}\AppData\Local\Programs\Python\Python310\python.exe".format(os.getenv('USERNAME', ''))
            # ]
            
            # for python_path in possible_python_paths:
            #     try:
            #         if python_path in ["python", "python3"]:
            #             # Check if python is in PATH
            #             if shutil.which(python_path):
            #                 python_executable = python_path
            #                 print(f" Found Python in PATH: {python_path}")
            #                 break
            #         else:
            #             # Check if specific path exists
            #             if os.path.exists(python_path):
            #                 python_executable = python_path
            #                 print(f" Found Python at: {python_path}")
            #                 break
            #     except Exception as e:
            #         continue
            
            python_executable=find_python_executable()
            
            if not python_executable:
                error_msg = "Could not find local Python installation. Please ensure Python is installed and accessible."
                return False, "", error_msg
            
            # Copy required modules from bundle to current directory for local Python access
            required_modules = ['xpath_find.py', 'element_confirmation.py', 'verify_xpath.py', 'config.py', 'web_element_picker.py', 'style_loader.py']
            
            print(" Copying required modules from bundle to current directory...")
            for module_file in required_modules:
                bundle_module_path = os.path.join(bundle_dir, module_file)
                current_module_path = os.path.join(current_dir, module_file)
                
                if os.path.exists(bundle_module_path):
                    try:
                        import shutil
                        shutil.copy2(bundle_module_path, current_module_path)
                        print(f" [OK] Copied {module_file} from bundle")
                    except Exception as e:
                        print(f" [WARN] Could not copy {module_file}: {e}")
                else:
                    print(f" [WARN] {module_file} not found in bundle")
            
            # Set up Python code for local execution (no emoji characters to avoid encoding issues)
            python_code = f"""
import sys
import os

# Add current directory to Python path
current_dir = r'{current_dir}'
sys.path.insert(0, current_dir)
os.chdir(current_dir)

print(f"Working directory: {{os.getcwd()}}")
print(f"Python path includes current dir: {{current_dir in sys.path}}")

try:
    # Import required modules to verify they're available
    import xpath_find
    import element_confirmation
    import web_element_picker
    import verify_xpath
    import config
    import style_loader
    print("[OK] All required modules imported successfully")
    
    # Now import and execute aba_agent
    from code_py.execute_code import aba_agent
    print("[START] Starting AGENT FLOW Agent execution...")
    aba_agent()
    print("[DONE] AGENT FLOW Agent execution completed successfully")
except ImportError as e:
    print(f"[ERROR] Import error: {{e}}")
    print(f"Available .py files in current dir: {{[f for f in os.listdir('.') if f.endswith('.py')]}}")
    raise
except Exception as e:
    print(f"[ERROR] Error in AGENT FLOW Agent execution: {{e}}")
    import traceback
    traceback.print_exc()
    raise
"""
        else:
            # Running from source - use local Python
            print(" Running from source code")
            
            # Find local Python executable
            python_executable = None
            
            # # Try to find Python in common locations
            # possible_python_paths = [
            #     "python",  # Try system PATH first
            #     "python3",
            #     r"C:\Program Files\Python312\python.exe",
            #     r"C:\Program Files\Python311\python.exe", 
            #     r"C:\Program Files\Python310\python.exe",
            #     r"C:\Program Files (x86)\Python312\python.exe",
            #     r"C:\Program Files (x86)\Python311\python.exe",
            #     r"C:\Program Files (x86)\Python310\python.exe",
            #     r"C:\Users\{}\AppData\Local\Programs\Python\Python312\python.exe".format(os.getenv('USERNAME', '')),
            #     r"C:\Users\{}\AppData\Local\Programs\Python\Python311\python.exe".format(os.getenv('USERNAME', '')),
            #     r"C:\Users\{}\AppData\Local\Programs\Python\Python310\python.exe".format(os.getenv('USERNAME', ''))
            # ]
            
            # for python_path in possible_python_paths:
            #     try:
            #         if python_path in ["python", "python3"]:
            #             # Check if python is in PATH
            #             if shutil.which(python_path):
            #                 python_executable = python_path
            #                 print(f" Found Python in PATH: {python_path}")
            #                 break
            #         else:
            #             # Check if specific path exists
            #             if os.path.exists(python_path):
            #                 python_executable = python_path
            #                 print(f" Found Python at: {python_path}")
            #                 break
            #     except Exception as e:
            #         continue

            python_executable=find_python_executable()
            
            if not python_executable:
                error_msg = "Could not find local Python installation. Please ensure Python is installed and accessible."
                return False, "", error_msg
            
            # Create the command for source execution
            python_code = f"""
import sys
import os
sys.path.insert(0, r'{current_dir}')
os.chdir(r'{current_dir}')
try:
    from code_py.execute_code import aba_agent
    print("[START] Starting AGENT FLOW Agent execution...")
    aba_agent()
    print("[DONE] AGENT FLOW Agent execution completed successfully")
except Exception as e:
    print(f"[ERROR] Error in AGENT FLOW Agent execution: {{e}}")
    import traceback
    traceback.print_exc()
    raise
"""
        
        print(f" Using Python executable: {python_executable}")
        print(" Executing AGENT FLOW Agent using subprocess...")
        print(f" Working directory: {current_dir}")
        
        # Execute using subprocess with proper error handling
        result = subprocess.run(
            [python_executable, "-c", python_code],
            cwd=current_dir,
            capture_output=True,
            text=True,
            timeout=300,  # 5 minute timeout
            creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0  # Hide console window on Windows
        )
        
        # Print output for debugging
        output_text = ""
        error_text = ""
        
        if result.stdout:
            output_text = result.stdout
            print(" AGENT FLOW Agent Output:")
            print(result.stdout)
        
        if result.stderr:
            error_text = result.stderr
            print(" AGENT FLOW Agent Errors/Warnings:")
            print(result.stderr)
        
        # Check return code
        if result.returncode != 0:
            error_msg = f"AGENT FLOW Agent process failed with return code {result.returncode}"
            if result.stderr:
                error_msg += f"\n\nError Output:\n{result.stderr}"
            if result.stdout:
                error_msg += f"\n\nStandard Output:\n{result.stdout}"
            return False, output_text, error_msg
        
        print(" AGENT FLOW Agent subprocess execution completed successfully")
        return True, output_text, error_text
            
    except subprocess.TimeoutExpired:
        error_message = "AGENT FLOW Agent execution timed out after 5 minutes"
        print(f" {error_message}")
        return False, "", error_message
    except Exception as e:
        error_message = f"Error in AGENT FLOW execution: {str(e)}"
        print(f" {error_message}")
        import traceback
        traceback.print_exc()
        return False, "", error_message


# if __name__ == "__main__":
#     # Test the function
#     success, output, error = run_aba_agent_subprocess()
#     if success:
#         print("✅ AGENT FLOW Agent executed successfully!")
#     else:
#         print(f"❌ AGENT FLOW Agent execution failed: {error}")
