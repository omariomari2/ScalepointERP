#!/usr/bin/env python3
import os
import re

def fix_date_references(file_path):
    """Replace all instances of date.today() with datetime.date.today() in a file"""
    with open(file_path, 'r', encoding='utf-8') as file:
        content = file.read()
    
    # Replace date.today() with datetime.date.today()
    modified_content = re.sub(r'(?<!\.)date\.today\(\)', 'datetime.date.today()', content)
    
    # Replace date(year, month, day) with datetime.date(year, month, day)
    modified_content = re.sub(r'(?<!\.)date\(([^)]+)\)', r'datetime.date(\1)', modified_content)
    
    if content != modified_content:
        print(f"Fixing date references in {file_path}")
        with open(file_path, 'w', encoding='utf-8') as file:
            file.write(modified_content)
        return True
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
    modules_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'modules')
    fixed_count = process_directory(modules_dir)
    print(f"Fixed date references in {fixed_count} files")
