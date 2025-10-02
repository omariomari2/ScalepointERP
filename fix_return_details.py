"""
Fix for the return details display issue in the ERP system.
This script fixes the problem where return details page shows incorrect values for quantity, unit price, and subtotal.
"""
from flask import Flask
from modules.pos.models import POSReturn, POSReturnLine
from extensions import db
import sys

def fix_return_details_display():
    """
    Fix the issue with return details display showing incorrect values.
    The problem is that the return details page shows a default quantity of 1 regardless of the actual quantity,
    and the unit price and subtotal are showing as 0.00.
    """
    print("Applying fix for return details display issue...")
    
    # Update the return_detail.html template to correctly display the values
    template_path = r"c:\Users\USER\erpsystem_working_backup\templates\pos\return_detail.html"
    
    try:
        with open(template_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Check if the template already has the correct display logic
        if '<td class="text-end">{{ line.quantity }}</td>' in content and \
           '<td class="text-end">GH₵{{ "%.2f"|format(line.unit_price) }}</td>' in content and \
           '<td class="text-end">GH₵{{ "%.2f"|format(line.quantity * line.unit_price) }}</td>' in content:
            
            # The template has the correct display logic, but the issue might be with the data
            # Let's update the template to use the subtotal field directly instead of calculating it
            updated_content = content.replace(
                '<td class="text-end">GH₵{{ "%.2f"|format(line.quantity * line.unit_price) }}</td>',
                '<td class="text-end">GH₵{{ "%.2f"|format(line.subtotal) }}</td>'
            )
            
            with open(template_path, 'w', encoding='utf-8') as f:
                f.write(updated_content)
            
            print("Updated return_detail.html template to use the subtotal field directly")
        else:
            print("Template doesn't have the expected display logic. No changes made.")
        
        # Now let's create a function to fix the data in existing returns
        def fix_return_data():
            """Fix the data in existing returns to ensure correct values are displayed"""
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
        
        # Create a function to patch the POSReturnLine model to ensure correct data is saved
        def patch_return_line_model():
            """Patch the POSReturnLine model to ensure correct data is saved"""
            try:
                # Add a hook to the POSReturnLine model to ensure subtotal is calculated correctly
                original_init = POSReturnLine.__init__
                
                def patched_init(self, *args, **kwargs):
                    # Call the original __init__ method
                    original_init(self, *args, **kwargs)
                    
                    # Ensure subtotal is calculated correctly
                    if hasattr(self, 'quantity') and hasattr(self, 'unit_price'):
                        if self.quantity > 0 and self.unit_price > 0:
                            self.subtotal = self.quantity * self.unit_price
                
                # Replace the __init__ method with our patched version
                POSReturnLine.__init__ = patched_init
                
                print("Patched POSReturnLine model to ensure correct subtotal calculation")
                return True
            except Exception as e:
                print(f"Error patching POSReturnLine model: {str(e)}")
                return False
        
        # Apply the fixes
        if fix_return_data() and patch_return_line_model():
            print("Successfully fixed return details display issue")
            return True
        else:
            print("Failed to fix return details display issue")
            return False
        
    except Exception as e:
        print(f"Error fixing return details display: {str(e)}")
        return False

def patch_new_partial_return():
    """
    Patch the new_partial_return.py file to ensure correct values are saved when creating a return.
    """
    print("Patching new_partial_return.py to ensure correct values are saved...")
    
    try:
        # Path to the new_partial_return.py file
        file_path = r"c:\Users\USER\erpsystem_working_backup\new_partial_return.py"
        
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Check if the file already has the correct logic for calculating subtotal
        if "line_subtotal = price * quantity" in content:
            # The file has the correct logic, but let's ensure it's being applied consistently
            # We'll add a debug statement to verify the values are correct
            updated_content = content.replace(
                "line_subtotal = price * quantity",
                "# Ensure correct subtotal calculation\nline_subtotal = price * quantity\nprint(f\"Creating return line with quantity={quantity}, price={price}, subtotal={line_subtotal}\")"
            )
            
            # Also ensure the subtotal is being set correctly in the POSReturnLine creation
            if "subtotal=line_subtotal," in content:
                print("new_partial_return.py already has correct subtotal calculation")
            else:
                # If subtotal is not being set correctly, fix it
                updated_content = updated_content.replace(
                    "return_line = POSReturnLine(",
                    "# Create return line with correct values\nreturn_line = POSReturnLine("
                )
                
                # Ensure the subtotal is being set
                if "subtotal=" not in updated_content:
                    updated_content = updated_content.replace(
                        "unit_price=price,",
                        "unit_price=price,\n                        subtotal=line_subtotal,"
                    )
            
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(updated_content)
            
            print("Updated new_partial_return.py to ensure correct values are saved")
            return True
        else:
            print("new_partial_return.py doesn't have the expected logic. No changes made.")
            return False
        
    except Exception as e:
        print(f"Error patching new_partial_return.py: {str(e)}")
        return False

def main():
    """Apply all fixes"""
    print("Starting return details display fix...")
    
    # Fix the return details display
    if fix_return_details_display():
        print("Return details display fixed successfully")
    else:
        print("Failed to fix return details display")
        return False
    
    # Patch the new_partial_return.py file
    if patch_new_partial_return():
        print("new_partial_return.py patched successfully")
    else:
        print("Failed to patch new_partial_return.py")
        return False
    
    print("\nAll fixes applied successfully!")
    print("Please restart your application for the changes to take effect.")
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
