"""
Script to apply the clean app.py file that removes automatic partial return fixes.
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

def apply_clean_app():
    """Apply the clean app.py file"""
    app_path = r"c:\Users\USER\erpsystem_working_backup\app.py"
    clean_app_path = r"c:\Users\USER\erpsystem_working_backup\clean_app.py"
    
    if not os.path.exists(clean_app_path):
        print(f"Error: Clean app file not found at {clean_app_path}")
        return False
    
    # Backup the original app.py file
    if not backup_file(app_path):
        return False
    
    try:
        # Copy the clean app.py file to app.py
        shutil.copy2(clean_app_path, app_path)
        print(f"Successfully applied clean app.py file")
        return True
    except Exception as e:
        print(f"Error applying clean app.py file: {str(e)}")
        return False

def main():
    """Apply the clean app.py file"""
    print("Applying clean app.py file...")
    
    if apply_clean_app():
        print("\nClean app.py file applied successfully!")
        print("The automatic partial return fixes have been removed.")
        print("Only your latest fixes will be active when the app starts.")
        print("\nPlease restart your application for the changes to take effect.")
        return True
    else:
        print("\nFailed to apply clean app.py file.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
