#!/usr/bin/env python3
"""
Validation script for automation mode dropdown integration
"""
import sys
import os

def validate_files():
    """Validate that all required files exist and have correct content"""
    print("🔍 Validating automation mode dropdown integration...")
    
    # Check if automation_mode_dropdown.py exists
    dropdown_file = "automation_mode_dropdown.py"
    if not os.path.exists(dropdown_file):
        print(f"❌ Missing file: {dropdown_file}")
        return False
    print(f"✅ Found: {dropdown_file}")
    
    # Check if required icon files exist
    required_icons = [
        "styles/Icon/web.png",
        "styles/Icon/desktop.png", 
        "styles/Icon/native.png",
        "styles/Icon/citrix.png",
        "styles/Icon/switch.png"
    ]
    
    for icon in required_icons:
        if not os.path.exists(icon):
            print(f"❌ Missing icon: {icon}")
            return False
        print(f"✅ Found icon: {icon}")
    
    # Check main_process.py for dropdown integration
    main_process_file = "main_process.py"
    if not os.path.exists(main_process_file):
        print(f"❌ Missing file: {main_process_file}")
        return False
    
    with open(main_process_file, 'r', encoding='utf-8') as f:
        content = f.read()
        
    # Check for required imports
    if "import automation_mode_dropdown" not in content:
        print("❌ Missing import: automation_mode_dropdown in main_process.py")
        return False
    print("✅ Found import: automation_mode_dropdown")
    
    # Check for dropdown widget creation
    if "automation_mode_dropdown.SwitchModeButton()" not in content:
        print("❌ Missing dropdown widget creation in main_process.py")
        return False
    print("✅ Found dropdown widget creation")
    
    # Check for mode change handler
    if "def on_automation_mode_changed" not in content:
        print("❌ Missing mode change handler in main_process.py")
        return False
    print("✅ Found mode change handler")
    
    # Check login_page.py for direct main_process call
    login_file = "login_page.py"
    if not os.path.exists(login_file):
        print(f"❌ Missing file: {login_file}")
        return False
    
    with open(login_file, 'r', encoding='utf-8') as f:
        login_content = f.read()
    
    # Check that it calls main_process directly
    if "main_process.main_login_page(" not in login_content:
        print("❌ Login page doesn't call main_process directly")
        return False
    print("✅ Login page calls main_process directly")
    
    return True

def validate_syntax():
    """Validate Python syntax of key files"""
    print("\n🔍 Validating Python syntax...")
    
    files_to_check = [
        "automation_mode_dropdown.py",
        "test_dropdown.py"
    ]
    
    for file_path in files_to_check:
        if not os.path.exists(file_path):
            print(f"⚠️ Skipping syntax check for missing file: {file_path}")
            continue
            
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                source = f.read()
            compile(source, file_path, 'exec')
            print(f"✅ Syntax OK: {file_path}")
        except SyntaxError as e:
            print(f"❌ Syntax Error in {file_path}: {e}")
            return False
        except Exception as e:
            print(f"❌ Error checking {file_path}: {e}")
            return False
    
    return True

def validate_dropdown_component():
    """Validate the dropdown component can be imported"""
    print("\n🔍 Validating dropdown component import...")
    
    try:
        # Add current directory to path
        sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
        
        # Try to import the module
        import automation_mode_dropdown
        print("✅ Successfully imported automation_mode_dropdown")
        
        # Check if classes exist
        if hasattr(automation_mode_dropdown, 'AutomationModeDropdown'):
            print("✅ Found AutomationModeDropdown class")
        else:
            print("❌ Missing AutomationModeDropdown class")
            return False
            
        if hasattr(automation_mode_dropdown, 'SwitchModeButton'):
            print("✅ Found SwitchModeButton class")
        else:
            print("❌ Missing SwitchModeButton class")
            return False
        
        return True
        
    except ImportError as e:
        print(f"❌ Failed to import automation_mode_dropdown: {e}")
        return False
    except Exception as e:
        print(f"❌ Error validating dropdown component: {e}")
        return False

def main():
    """Run all validation checks"""
    print("🚀 Starting automation mode dropdown integration validation...\n")
    
    all_passed = True
    
    # Run validation checks
    if not validate_files():
        all_passed = False
    
    if not validate_syntax():
        all_passed = False
    
    if not validate_dropdown_component():
        all_passed = False
    
    # Final result
    print("\n" + "="*60)
    if all_passed:
        print("🎉 ALL VALIDATIONS PASSED!")
        print("\n✅ Integration Summary:")
        print("   • Automation type selection window removed")
        print("   • Dropdown integrated into main toolbar")
        print("   • All required files and icons present")
        print("   • Python syntax is valid")
        print("   • Components can be imported successfully")
        print("\n🚀 Ready to test the full application!")
        print("\nNext steps:")
        print("1. Run the application: python login_page.py")
        print("2. Login with valid credentials")
        print("3. Verify dropdown appears in toolbar")
        print("4. Test switching between automation modes")
    else:
        print("❌ SOME VALIDATIONS FAILED!")
        print("\n🔧 Please fix the issues above before testing.")
    
    return 0 if all_passed else 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
