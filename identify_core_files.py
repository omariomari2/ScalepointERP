"""
Script to identify core files needed for deployment.
This script doesn't delete anything, it just lists files that are essential.
"""
import os
import re

# Define patterns for core files
CORE_PATTERNS = [
    r'app\.py$',
    r'config\.py$',
    r'extensions\.py$',
    r'setup_database\.py$',
    r'init_db\.py$',
    r'Procfile$',
    r'requirements\.txt$',
    r'runtime\.txt$',
    r'^modules/.*\.py$',
    r'^templates/.*\.html$',
    r'^static/.*\.(css|js|png|jpg|jpeg|gif|svg)$',
    r'\.gitignore$',
    r'README\.md$',
]

# Define patterns for files to exclude
EXCLUDE_PATTERNS = [
    r'check_.*\.py$',
    r'debug_.*\.py$',
    r'inspect_.*\.py$',
    r'recreate_.*\.py$',
    r'rebuild_.*\.py$',
    r'add_.*\.py$',
    r'create_.*\.py$',
    r'direct_db_.*\.py$',
    r'force_.*\.py$',
    r'.*_DEPLOYMENT\.md$',
    r'\.git/',
    r'__pycache__/',
    r'.*\.pyc$',
]

def is_core_file(file_path):
    """Check if a file is a core file."""
    rel_path = os.path.relpath(file_path, os.path.dirname(os.path.abspath(__file__)))
    rel_path = rel_path.replace('\\', '/')
    
    # Check if file matches any core pattern
    for pattern in CORE_PATTERNS:
        if re.search(pattern, rel_path):
            return True
    
    return False

def should_exclude(file_path):
    """Check if a file should be excluded."""
    rel_path = os.path.relpath(file_path, os.path.dirname(os.path.abspath(__file__)))
    rel_path = rel_path.replace('\\', '/')
    
    # Check if file matches any exclude pattern
    for pattern in EXCLUDE_PATTERNS:
        if re.search(pattern, rel_path):
            return True
    
    return False

def scan_directory(directory):
    """Scan a directory and identify core files and files to exclude."""
    core_files = []
    exclude_files = []
    
    for root, dirs, files in os.walk(directory):
        # Skip .git directory
        if '.git' in dirs:
            dirs.remove('.git')
        
        # Skip __pycache__ directories
        if '__pycache__' in dirs:
            dirs.remove('__pycache__')
        
        for file in files:
            file_path = os.path.join(root, file)
            
            if is_core_file(file_path):
                core_files.append(file_path)
            elif should_exclude(file_path):
                exclude_files.append(file_path)
            else:
                # Files that don't match either pattern
                print(f"Unclassified: {file_path}")
    
    return core_files, exclude_files

if __name__ == "__main__":
    current_dir = os.path.dirname(os.path.abspath(__file__))
    
    print("Scanning directory for core files and files to exclude...")
    core_files, exclude_files = scan_directory(current_dir)
    
    print("\n=== CORE FILES ===")
    for file in sorted(core_files):
        print(file)
    
    print(f"\nTotal core files: {len(core_files)}")
    
    print("\n=== FILES TO EXCLUDE ===")
    for file in sorted(exclude_files):
        print(file)
    
    print(f"\nTotal files to exclude: {len(exclude_files)}")
    
    print("\nTo clean up your repository, add the patterns in EXCLUDE_PATTERNS to your .gitignore file.")
    print("Then commit only the core files to your repository.")
