#!/usr/bin/env python
"""
Script to fix partial return functionality in the ERP system.
This script modifies the necessary files to ensure partial returns work correctly.
"""
import os
import re

def fix_routes_py():
    """Fix the routes.py file to handle partial returns correctly."""
    file_path = os.path.join('modules', 'pos', 'routes.py')
    
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Add code to check for and use the special actual_quantity field
    pattern = r'(# Get product data from form\s+product_ids = request\.form\.getlist\(\'product_id\[\]\'\)\s+quantities = request\.form\.getlist\(\'quantity\[\]\'\)\s+prices = request\.form\.getlist\(\'price\[\]\'\)\s+return_reasons = request\.form\.getlist\(\'return_reason\[\]\'\)\s+line_notes = request\.form\.getlist\(\'line_notes\[\]\'\)\s+original_line_ids = request\.form\.getlist\(\'original_line_id\[\]\'\))'
    replacement = r'\1\n\n            # CRITICAL FIX: Check for the special actual_quantity field\n            # This is added by our JavaScript fix to ensure the correct quantity is used\n            actual_quantity = request.form.get("actual_quantity")\n            if actual_quantity:\n                try:\n                    actual_quantity = int(float(actual_quantity))\n                    print(f"Found special actual_quantity: {actual_quantity}")\n                    # Replace all quantities with this value to ensure it\'s used\n                    quantities = [str(actual_quantity)]\n                except (ValueError, TypeError):\n                    print(f"Invalid actual_quantity: {actual_quantity}")'
    
    content = re.sub(pattern, replacement, content)
    
    # Force return_type to 'partial' after creating the new_return object
    pattern = r'(new_return = POSReturn\([^)]+\)\s+\n\s+# Add detailed logging before saving return header)'
    replacement = r'\1\n\n            # CRITICAL FIX: Force return_type to "partial" regardless of what was submitted\n            new_return.return_type = "partial"'
    
    content = re.sub(pattern, replacement, content)
    
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print(f"✓ Fixed {file_path}")

def main():
    """Main function to apply all fixes."""
    print("Applying fixes for partial return functionality...")
    
    try:
        fix_routes_py()
        print("\nAll fixes applied successfully!")
        print("Please restart the application for the changes to take effect.")
    except Exception as e:
        print(f"Error applying fixes: {str(e)}")

if __name__ == "__main__":
    main()
