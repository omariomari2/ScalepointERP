"""
Startup script that applies all fixes and starts the application.
"""
import os
import sys
import subprocess

def main():
    """Apply all fixes and start the application"""
    print("Applying fixes and starting the application...")
    
    # Run the database fix script
    print("Fixing database values...")
    result = subprocess.run([sys.executable, "fix_db_values.py"], capture_output=True, text=True)
    print(result.stdout)
    if result.returncode != 0:
        print(f"Error fixing database values: {result.stderr}")
    
    # Start the application with the patched return_detail route
    print("Starting the application...")
    os.environ["PATCH_RETURN_DETAIL"] = "1"
    os.execv(sys.executable, [sys.executable, "app.py"])
    
    return True

if __name__ == "__main__":
    main()
