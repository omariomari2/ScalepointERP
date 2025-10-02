"""
Fix for the return details display issue in the ERP system.
This script fixes the problem where return details page shows incorrect values for quantity, unit price, and subtotal.
"""
import os
import sys
from datetime import datetime
import shutil

def backup_file(file_path):
    """Create a backup of the specified file"""
    if os.path.exists(file_path):
        backup_dir = os.path.join(os.path.dirname(file_path), 'backups')
        os.makedirs(backup_dir, exist_ok=True)
        
        filename = os.path.basename(file_path)
        timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
        backup_path = os.path.join(backup_dir, f"{filename}.{timestamp}.bak")
        
        shutil.copy2(file_path, backup_path)
        print(f"Created backup: {backup_path}")
        return True
    return False

def fix_return_detail_template():
    """Fix the return_detail.html template to correctly display the values"""
    template_path = r"c:\Users\USER\erpsystem_working_backup\templates\pos\return_detail.html"
    
    # Backup the template file
    if not backup_file(template_path):
        print(f"Error: Could not find {template_path}")
        return False
    
    try:
        with open(template_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Update the template to correctly display the subtotal
        updated_content = content.replace(
            '<td class="text-end">GH₵{{ "%.2f"|format(line.quantity * line.unit_price) }}</td>',
            '<td class="text-end">GH₵{{ "%.2f"|format(line.subtotal) }}</td>'
        )
        
        with open(template_path, 'w', encoding='utf-8') as f:
            f.write(updated_content)
        
        print("Successfully updated return_detail.html template to use the subtotal field directly")
        return True
    except Exception as e:
        print(f"Error updating return_detail.html template: {str(e)}")
        return False

def fix_new_partial_return():
    """Fix the new_partial_return.py file to ensure correct values are saved"""
    file_path = r"c:\Users\USER\erpsystem_working_backup\new_partial_return.py"
    
    # Backup the file
    if not backup_file(file_path):
        print(f"Error: Could not find {file_path}")
        return False
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Find the section where the return line is created
        return_line_section = """                # Create a single return line with the full quantity
                return_line = POSReturnLine(
                    return_id=None,
                    product_id=product_id,
                    quantity=quantity,
                    unit_price=price,
                    subtotal=line_subtotal,
                    return_reason=return_reason,
                    state='draft',
                    original_order_line_id=original_line_id,
                    product_name=product.name  # Store the product name for resilience
                )"""
        
        # Check if the subtotal is already being set correctly
        if "subtotal=line_subtotal," in content:
            print("new_partial_return.py already has correct subtotal calculation")
        else:
            # If subtotal is not being set correctly, fix it
            updated_content = content.replace(
                """                # Create a single return line with the full quantity
                return_line = POSReturnLine(
                    return_id=None,
                    product_id=product_id,
                    quantity=quantity,
                    unit_price=price,""",
                """                # Create a single return line with the full quantity
                return_line = POSReturnLine(
                    return_id=None,
                    product_id=product_id,
                    quantity=quantity,
                    unit_price=price,
                    subtotal=line_subtotal,"""
            )
            
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(updated_content)
            
            print("Successfully updated new_partial_return.py to set the subtotal field correctly")
        
        return True
    except Exception as e:
        print(f"Error updating new_partial_return.py: {str(e)}")
        return False

def create_data_fix_script():
    """Create a script to fix the data in existing returns"""
    script_path = r"c:\Users\USER\erpsystem_working_backup\fix_return_data.py"
    
    try:
        script_content = """\"\"\"
Fix for the data in existing returns to ensure correct values are displayed.
This script should be run within the application context.
\"\"\"
from flask import Flask
from app import create_app
from modules.pos.models import POSReturn, POSReturnLine
from extensions import db

def fix_return_data():
    \"\"\"Fix the data in existing returns to ensure correct values are displayed\"\"\"
    try:
        # Get all returns with potential issues
        returns = POSReturn.query.all()
        fixed_count = 0
        
        for return_ in returns:
            for line in return_.return_lines:
                # Check if the line has valid data
                if line.quantity > 0 and line.unit_price <= 0:
                    # Try to get the correct price from the original order line
                    if line.original_order_line and line.original_order_line.unit_price > 0:
                        line.unit_price = line.original_order_line.unit_price
                        line.subtotal = line.quantity * line.unit_price
                        fixed_count += 1
                    # If we can't get the price from the original order line, try to get it from the product
                    elif line.product and hasattr(line.product, 'list_price') and line.product.list_price > 0:
                        line.unit_price = line.product.list_price
                        line.subtotal = line.quantity * line.unit_price
                        fixed_count += 1
                
                # Ensure subtotal is correctly calculated
                if line.subtotal <= 0 and line.quantity > 0 and line.unit_price > 0:
                    line.subtotal = line.quantity * line.unit_price
                    fixed_count += 1
        
        if fixed_count > 0:
            db.session.commit()
            print(f"Fixed {fixed_count} return lines with incorrect data")
        else:
            print("No data issues found in existing returns")
        
        return True
    except Exception as e:
        print(f"Error fixing return data: {str(e)}")
        db.session.rollback()
        return False

if __name__ == "__main__":
    # Create the application context
    app = create_app()
    
    # Run the fix within the application context
    with app.app_context():
        if fix_return_data():
            print("Successfully fixed return data")
        else:
            print("Failed to fix return data")
"""
        
        with open(script_path, 'w', encoding='utf-8') as f:
            f.write(script_content)
        
        print(f"Successfully created {script_path}")
        return True
    except Exception as e:
        print(f"Error creating fix_return_data.py: {str(e)}")
        return False

def create_model_patch_script():
    """Create a script to patch the POSReturnLine model"""
    script_path = r"c:\Users\USER\erpsystem_working_backup\patch_return_line_model.py"
    
    try:
        script_content = """\"\"\"
Patch for the POSReturnLine model to ensure correct values are saved.
This script should be added to app.py to be executed at startup.
\"\"\"
from modules.pos.models import POSReturnLine

def patch_return_line_model():
    \"\"\"Patch the POSReturnLine model to ensure correct values are saved\"\"\"
    try:
        # Store the original __init__ method
        original_init = POSReturnLine.__init__
        
        def patched_init(self, *args, **kwargs):
            # Call the original __init__ method
            original_init(self, *args, **kwargs)
            
            # Ensure subtotal is calculated correctly
            if hasattr(self, 'quantity') and hasattr(self, 'unit_price'):
                if self.quantity > 0 and self.unit_price > 0:
                    self.subtotal = self.quantity * self.unit_price
                    print(f"POSReturnLine: Set subtotal={self.subtotal} (quantity={self.quantity}, unit_price={self.unit_price})")
        
        # Replace the __init__ method with our patched version
        POSReturnLine.__init__ = patched_init
        
        print("Successfully patched POSReturnLine model")
        return True
    except Exception as e:
        print(f"Error patching POSReturnLine model: {str(e)}")
        return False
"""
        
        with open(script_path, 'w', encoding='utf-8') as f:
            f.write(script_content)
        
        print(f"Successfully created {script_path}")
        return True
    except Exception as e:
        print(f"Error creating patch_return_line_model.py: {str(e)}")
        return False

def update_app_py():
    """Update app.py to include the model patch"""
    app_path = r"c:\Users\USER\erpsystem_working_backup\app.py"
    
    # Backup the file
    if not backup_file(app_path):
        print(f"Error: Could not find {app_path}")
        return False
    
    try:
        with open(app_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Find the section where the new_partial_return is registered
        register_section = """    # Register our new implementation of the partial return functionality
    try:
        from new_partial_return import register_blueprint
        if register_blueprint(app):
            print("New partial return functionality registered successfully")
        else:
            print("Failed to register new partial return functionality")
    except Exception as e:
        print(f"Error registering new partial return functionality: {str(e)}")
        import traceback
        traceback.print_exc()"""
        
        # Add the model patch after the new_partial_return registration
        updated_content = content.replace(
            register_section,
            register_section + """
    
    # Patch the POSReturnLine model to ensure correct values are saved
    try:
        from patch_return_line_model import patch_return_line_model
        if patch_return_line_model():
            print("POSReturnLine model patched successfully")
        else:
            print("Failed to patch POSReturnLine model")
    except Exception as e:
        print(f"Error patching POSReturnLine model: {str(e)}")
        import traceback
        traceback.print_exc()"""
        )
        
        with open(app_path, 'w', encoding='utf-8') as f:
            f.write(updated_content)
        
        print("Successfully updated app.py to include the model patch")
        return True
    except Exception as e:
        print(f"Error updating app.py: {str(e)}")
        return False

def main():
    """Apply all fixes"""
    print("Starting return details display fix...")
    
    # Fix the return_detail.html template
    if fix_return_detail_template():
        print("Return detail template fixed successfully")
    else:
        print("Failed to fix return detail template")
        return False
    
    # Fix the new_partial_return.py file
    if fix_new_partial_return():
        print("new_partial_return.py fixed successfully")
    else:
        print("Failed to fix new_partial_return.py")
        return False
    
    # Create the data fix script
    if create_data_fix_script():
        print("Data fix script created successfully")
    else:
        print("Failed to create data fix script")
        return False
    
    # Create the model patch script
    if create_model_patch_script():
        print("Model patch script created successfully")
    else:
        print("Failed to create model patch script")
        return False
    
    # Update app.py to include the model patch
    if update_app_py():
        print("app.py updated successfully")
    else:
        print("Failed to update app.py")
        return False
    
    print("\nAll fixes applied successfully!")
    print("Next steps:")
    print("1. Run 'python fix_return_data.py' to fix the data in existing returns")
    print("2. Restart your application for the changes to take effect")
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
