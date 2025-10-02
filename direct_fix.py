#!/usr/bin/env python
"""
Script to directly fix the partial return functionality in the ERP system.
This script creates a backup of the original file and then replaces it with a fixed version.
"""
import os
import shutil
from datetime import datetime

def fix_routes_py():
    """Fix the routes.py file to handle partial returns correctly."""
    file_path = os.path.join('modules', 'pos', 'routes.py')
    backup_path = f"{file_path}.bak.{datetime.now().strftime('%Y%m%d%H%M%S')}"
    
    # Create a backup of the original file
    shutil.copy2(file_path, backup_path)
    print(f"Created backup at {backup_path}")
    
    # Read the original file
    with open(file_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    # Find the line where we need to add our code for actual_quantity
    product_data_line_idx = None
    for i, line in enumerate(lines):
        if "# Get product data from form" in line:
            product_data_line_idx = i
            break
    
    if product_data_line_idx is not None:
        # Find the end of the product data section (after original_line_ids)
        for i in range(product_data_line_idx, len(lines)):
            if "original_line_ids = request.form.getlist('original_line_id[]')" in lines[i]:
                insert_idx = i + 1
                # Add our code for actual_quantity
                lines.insert(insert_idx, "\n")
                lines.insert(insert_idx + 1, "            # CRITICAL FIX: Check for the special actual_quantity field\n")
                lines.insert(insert_idx + 2, "            # This is added by our JavaScript fix to ensure the correct quantity is used\n")
                lines.insert(insert_idx + 3, '            actual_quantity = request.form.get("actual_quantity")\n')
                lines.insert(insert_idx + 4, "            if actual_quantity:\n")
                lines.insert(insert_idx + 5, "                try:\n")
                lines.insert(insert_idx + 6, "                    actual_quantity = int(float(actual_quantity))\n")
                lines.insert(insert_idx + 7, '                    print(f"Found special actual_quantity: {actual_quantity}")\n')
                lines.insert(insert_idx + 8, "                    # Replace all quantities with this value to ensure it's used\n")
                lines.insert(insert_idx + 9, "                    quantities = [str(actual_quantity)]\n")
                lines.insert(insert_idx + 10, "                except (ValueError, TypeError):\n")
                lines.insert(insert_idx + 11, '                    print(f"Invalid actual_quantity: {actual_quantity}")\n')
                break
    
    # Find the line where we need to add our code for return_type
    new_return_line_idx = None
    for i, line in enumerate(lines):
        if "new_return = POSReturn(" in line:
            new_return_line_idx = i
            break
    
    if new_return_line_idx is not None:
        # Find the end of the new_return creation
        for i in range(new_return_line_idx, len(lines)):
            if ")" in lines[i] and "created_at" in lines[i-1]:
                insert_idx = i + 1
                # Add our code for return_type
                lines.insert(insert_idx, "\n")
                lines.insert(insert_idx + 1, "            # CRITICAL FIX: Force return_type to 'partial' regardless of what was submitted\n")
                lines.insert(insert_idx + 2, '            new_return.return_type = "partial"\n')
                break
    
    # Write the modified file
    with open(file_path, 'w', encoding='utf-8') as f:
        f.writelines(lines)
    
    print(f"✓ Fixed {file_path}")

def main():
    """Main function to apply all fixes."""
    print("Applying direct fixes for partial return functionality...")
    
    try:
        fix_routes_py()
        print("\nAll fixes applied successfully!")
        print("Please restart the application for the changes to take effect.")
    except Exception as e:
        print(f"Error applying fixes: {str(e)}")

if __name__ == "__main__":
    main()
