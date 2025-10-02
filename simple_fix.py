#!/usr/bin/env python
"""
Script to fix the syntax errors in routes.py using a simpler approach
"""
import os

def fix_file():
    file_path = 'modules/pos/routes.py'
    
    # Read the file line by line
    with open(file_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    # Fix the problematic lines
    for i in range(len(lines)):
        if "actual_quantity = request.form.get(" in lines[i] and "\\" in lines[i]:
            lines[i] = '            actual_quantity = request.form.get("actual_quantity")\n'
        
        if "# Replace all quantities with this value to ensure it" in lines[i] and "\\" in lines[i]:
            lines[i] = "            # Replace all quantities with this value to ensure it's used\n"
        
        if "new_return.return_type = " in lines[i] and "\\" in lines[i]:
            lines[i] = '            new_return.return_type = "partial"\n'
    
    # Write the fixed content back to the file
    with open(file_path, 'w', encoding='utf-8') as f:
        f.writelines(lines)
    
    print(f"✓ Fixed {file_path}")

if __name__ == "__main__":
    fix_file()
