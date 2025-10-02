"""
Script to fix the app.py file to prevent duplicate registration of the partial return blueprint.
"""
import os
import sys
import shutil
from datetime import datetime

def backup_file(file_path):
    """Create a backup of the specified file"""
    if os.path.exists(file_path):
        backup_dir = os.path.join(os.path.dirname(file_path), 'backups')
        os.makedirs(backup_dir, exist_ok=True)
        
        filename = os.path.basename(file_path)
        timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
        backup_path = os.path.join(backup_dir, f"{filename}.{timestamp}.bak")
        
        shutil.copy2(file_path, backup_path)
        print(f"Created backup: {backup_path}")
        return True
    else:
        print(f"Error: File not found at {file_path}")
        return False

def fix_app_py():
    """Fix the app.py file to move the partial return blueprint registration into the create_app function"""
    app_path = r"c:\Users\USER\erpsystem_working_backup\app.py"
    
    if not backup_file(app_path):
        return False
    
    try:
        with open(app_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Find the create_app function
        create_app_start = content.find("def create_app(")
        if create_app_start == -1:
            print("Could not find create_app function")
            return False
        
        # Find the end of the create_app function
        create_app_end = content.find("return app", create_app_start)
        if create_app_end == -1:
            print("Could not find end of create_app function")
            return False
        
        # Find the return app statement
        return_app_end = content.find("\n", create_app_end)
        if return_app_end == -1:
            print("Could not find return app statement")
            return False
        
        # Find the partial return registration in the main block
        partial_return_registration_start = content.find("# Register our new implementation of the partial return functionality", create_app_end)
        if partial_return_registration_start == -1:
            print("Could not find partial return registration")
            return False
        
        # Find the end of the partial return registration
        partial_return_registration_end = content.find("except Exception as e:", partial_return_registration_start)
        if partial_return_registration_end == -1:
            print("Could not find end of partial return registration")
            return False
        
        # Find the end of the exception handling
        exception_end = content.find("# Run the application", partial_return_registration_end)
        if exception_end == -1:
            print("Could not find end of exception handling")
            return False
        
        # Get the partial return registration code
        partial_return_registration = content[partial_return_registration_start:exception_end].strip()
        
        # Create the modified create_app function with the partial return registration
        modified_create_app = content[:return_app_end] + "\n\n    # Register our new implementation of the partial return functionality\n    try:\n        from new_partial_return import register_blueprint\n        register_blueprint(app)\n    except Exception as e:\n        print(f\"Error registering new partial return functionality: {str(e)}\")\n        import traceback\n        traceback.print_exc()\n" + content[return_app_end:partial_return_registration_start] + content[exception_end:]
        
        # Write the modified content back to the file
        with open(app_path, 'w', encoding='utf-8') as f:
            f.write(modified_create_app)
        
        print("Successfully fixed app.py to prevent duplicate registration")
        return True
    except Exception as e:
        print(f"Error fixing app.py: {str(e)}")
        return False

def main():
    """Fix the app.py file to prevent duplicate registration of the partial return blueprint"""
    print("Fixing app.py to prevent duplicate registration...")
    
    if fix_app_py():
        print("\nSuccessfully fixed app.py to prevent duplicate registration.")
        print("The partial return blueprint will now be registered only once.")
        print("\nPlease restart your application for the changes to take effect.")
        return True
    else:
        print("\nFailed to fix app.py.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
