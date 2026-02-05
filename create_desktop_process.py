import os
import shutil
import sys

def resource_path(relative_path):
    """Get absolute path to resource, works for dev and for PyInstaller"""
    if hasattr(sys, "_MEIPASS"):
        return os.path.join(sys._MEIPASS, relative_path)
    return os.path.join(os.path.abspath("."), relative_path)

def create_desktop_process_folder():
    """
    Creates the desktop_process folder and copies all necessary files
    when desktop code generation occurs.
    """
    
    # Define the desktop_process folder path
    desktop_process_dir = "desktop_process"
    
    # Create the desktop_process directory if it doesn't exist
    if not os.path.exists(desktop_process_dir):
        os.makedirs(desktop_process_dir)
        print(f"✅ Created directory: {desktop_process_dir}")
    
    # List of files that need to be copied to desktop_process folder
    files_to_copy = [
        "Desktop_code_skeleton.py",
        "Desktop_code_skeleton_backup.py", 
        "desktop_element_confirmation.py",
        "desktop_element_picker.py",
        "desktop_interact_element.py",
        "verify_desktop_attr.py",
        "Attributes_correction.py",
        "desktop_attr_find.py",
        "desktop_code_chat.py"
    ]
    
    # Copy each file to the desktop_process folder
    for file_name in files_to_copy:
        # Try to get file from bundled resources first, then from current directory
        source_file_bundled = resource_path(f"desktop_process/{file_name}")
        source_file_local = file_name
        dest_file = os.path.join(desktop_process_dir, file_name)
        
        try:
            # First try to copy from bundled resources (for .exe)
            if os.path.exists(source_file_bundled):
                shutil.copy2(source_file_bundled, dest_file)
                print(f"✅ Copied from bundle: {source_file_bundled} to {dest_file}")
            # Then try from current directory (for development)
            elif os.path.exists(source_file_local):
                shutil.copy2(source_file_local, dest_file)
                print(f"✅ Copied from local: {source_file_local} to {dest_file}")
            else:
                print(f"⚠️ Warning: Source file {file_name} not found in bundle or local directory")
        except Exception as e:
            print(f"❌ Error copying {file_name}: {str(e)}")
    
    # Create __init__.py file to make it a proper Python package
    init_file = os.path.join(desktop_process_dir, "__init__.py")
    if not os.path.exists(init_file):
        with open(init_file, 'w') as f:
            f.write('# Desktop Process Package\n')
        print(f"✅ Created {init_file}")
    
    print(f"🎉 Desktop process folder setup completed!")
    return True

def ensure_desktop_process_exists():
    """
    Ensures desktop_process folder exists and contains all required files.
    This function should be called before any desktop code generation.
    """
    desktop_process_dir = "desktop_process"
    
    # Check if desktop_process folder exists
    if not os.path.exists(desktop_process_dir):
        print("🔄 Desktop process folder not found. Creating...")
        return create_desktop_process_folder()
    
    # Check if all required files exist
    required_files = [
        "Desktop_code_skeleton.py",
        "desktop_element_confirmation.py",
        "desktop_element_picker.py", 
        "desktop_interact_element.py",
        "verify_desktop_attr.py",
        "desktop_attr_find.py",
        "desktop_code_chat.py"
    ]
    
    missing_files = []
    for file_name in required_files:
        file_path = os.path.join(desktop_process_dir, file_name)
        if not os.path.exists(file_path):
            missing_files.append(file_name)
    
    if missing_files:
        print(f"🔄 Missing files in desktop_process: {missing_files}")
        print("🔄 Recreating desktop_process folder...")
        return create_desktop_process_folder()
    
    print("✅ Desktop process folder exists with all required files")
    return True

# if __name__ == "__main__":
#     create_desktop_process_folder()
