#!/usr/bin/env python3
import os
import re

def fix_date_references(file_path):
    """Replace all instances of date.today() with datetime.date.today() in a file"""
    try:
        # Try UTF-8 first
        with open(file_path, 'r', encoding='utf-8') as file:
            content = file.read()
    except UnicodeDecodeError:
        try:
            # Try Latin-1 if UTF-8 fails
            with open(file_path, 'r', encoding='latin-1') as file:
                content = file.read()
        except Exception as e:
            print(f"Could not read {file_path}: {e}")
            return False
    
    # Replace date.today() with datetime.date.today()
    modified_content = re.sub(r'(?<!\.)date\.today\(\)', 'datetime.date.today()', content)
    
    # Replace date(year, month, day) with datetime.date(year, month, day)
    modified_content = re.sub(r'(?<!\.)date\(([^)]+)\)', r'datetime.date(\1)', modified_content)
    
    if content != modified_content:
        print(f"Fixing date references in {file_path}")
        try:
            with open(file_path, 'w', encoding='utf-8') as file:
                file.write(modified_content)
            return True
        except Exception as e:
            print(f"Could not write to {file_path}: {e}")
            return False
    return False

def process_directory(directory):
    """Process all Python files in a directory recursively"""
    fixed_files = 0
    for root, _, files in os.walk(directory):
        for file in files:
            if file.endswith('.py'):
                file_path = os.path.join(root, file)
                if fix_date_references(file_path):
                    fixed_files += 1
    return fixed_files

if __name__ == "__main__":
    # Process the modules directory
    app_dir = os.path.dirname(os.path.abspath(__file__))
    modules_dir = os.path.join(app_dir, 'modules')
    fixed_count = process_directory(modules_dir)
    
    # Also check the app.py and other root files
    for root_file in ['app.py', 'config.py', 'extensions.py']:
        root_path = os.path.join(app_dir, root_file)
        if os.path.exists(root_path) and fix_date_references(root_path):
            fixed_count += 1
    
    print(f"Fixed date references in {fixed_count} files")
