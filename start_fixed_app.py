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
    print("Fixing return DB values...")
    result = subprocess.run([sys.executable, "fix_return_db_values.py"], capture_output=True, text=True)
    if result.returncode != 0:
        print(f"Error fixing return DB values: {result.stderr}")
        return False
    
    print(result.stdout)
    
    # Start the application
    print("Starting the application...")
    os.execv(sys.executable, [sys.executable, "app.py"])
    
    return True

if __name__ == "__main__":
    main()
