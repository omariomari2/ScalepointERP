#!/usr/bin/env python3
import os
import re

def fix_clock_file():
    file_path = 'modules/employees/clock.py'
    
    with open(file_path, 'r', encoding='utf-8') as file:
        content = file.read()
    
    # Replace datetime.date.today() with date.today()
    modified_content = content.replace('datetime.date.today()', 'date.today()')
    
    if content != modified_content:
        print(f"Fixing date references in {file_path}")
        with open(file_path, 'w', encoding='utf-8') as file:
            file.write(modified_content)
        return True
    return False

if __name__ == "__main__":
    # Change to the root directory of the project
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    
    # Fix the clock.py file
    if fix_clock_file():
        print("Successfully fixed date references in clock.py")
    else:
        print("No changes needed in clock.py")
