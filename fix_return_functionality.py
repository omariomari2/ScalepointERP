"""
Script to fix the return functionality in the ERP system.
This script applies all necessary fixes to make partial returns work correctly.
"""
import os
import sys
import shutil
from datetime import datetime

# Backup original files before modifying
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
    return False

# Apply the fix to the routes.py file
def fix_routes_file():
    """Apply fixes to the routes.py file"""
    routes_file = r"c:\Users\USER\erpsystem_working_backup\modules\pos\routes.py"
    
    # Backup the original file
    if not backup_file(routes_file):
        print(f"Error: Could not find {routes_file}")
        return False
    
    # Import the fixed partial return function
    sys.path.insert(0, r"c:\Users\USER\erpsystem_working_backup")
    try:
        from partial_return_fix_new import apply_partial_return_fix
        from modules.pos.routes import pos
        
        # Apply the fix
        apply_partial_return_fix(pos)
        print("Successfully applied fix to POS routes")
        return True
    except Exception as e:
        print(f"Error applying fix to routes: {str(e)}")
        return False

def main():
    """Main function to apply all fixes"""
    print("Starting return functionality fix...")
    
    # Fix the routes file
    if fix_routes_file():
        print("Routes file fixed successfully")
    else:
        print("Failed to fix routes file")
        return False
    
    print("\nAll fixes applied successfully!")
    print("Please restart your application for the changes to take effect.")
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
