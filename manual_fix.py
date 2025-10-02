#!/usr/bin/env python
"""
Script to manually fix the syntax errors in routes.py
"""
import os

def fix_file():
    file_path = 'modules/pos/routes.py'
    
    # Read the file content
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Replace the problematic lines with correct syntax
    content = content.replace("actual_quantity = request.form.get(\\'actual_quantity\\')", 
                             'actual_quantity = request.form.get("actual_quantity")')
    
    content = content.replace("# Replace all quantities with this value to ensure it\\'s used", 
                             "# Replace all quantities with this value to ensure it's used")
    
    content = content.replace('new_return.return_type = \\'partial\\'', 
                             'new_return.return_type = "partial"')
    
    # Write the fixed content back to the file
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print(f"✓ Fixed {file_path}")

if __name__ == "__main__":
    fix_file()
