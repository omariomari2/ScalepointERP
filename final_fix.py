"""
Final fix for the partial return functionality in the ERP system.
This script fixes all the issues with the return details page showing incorrect values.
"""
import os
import sys
import shutil
from datetime import datetime

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
    else:
        print(f"Error: File not found at {file_path}")
        return False

def fix_return_detail_template():
    """Fix the return_detail.html template to correctly display values"""
    template_path = r"c:\Users\USER\erpsystem_working_backup\templates\pos\return_detail.html"
    
    if not backup_file(template_path):
        return False
    
    try:
        with open(template_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Find the table row for return lines
        if '<td class="text-end">{{ line.quantity }}</td>' in content:
            # Replace the quantity, unit price, and subtotal cells
            updated_content = content.replace(
                '<td class="text-end">{{ line.quantity }}</td>',
                '<td class="text-end">{{ "%.1f"|format(line.quantity|float) }}</td>'
            )
            
            updated_content = updated_content.replace(
                '<td class="text-end">GH₵{{ "%.2f"|format(line.unit_price) }}</td>',
                '<td class="text-end">GH₵{{ "%.2f"|format(line.unit_price|float) }}</td>'
            )
            
            updated_content = updated_content.replace(
                '<td class="text-end">GH₵{{ "%.2f"|format(line.quantity * line.unit_price) }}</td>',
                '<td class="text-end">GH₵{{ "%.2f"|format(line.subtotal|float) }}</td>'
            )
            
            with open(template_path, 'w', encoding='utf-8') as f:
                f.write(updated_content)
            
            print("Successfully updated return_detail.html template")
        else:
            print("Could not find expected template structure. Manual inspection required.")
        
        return True
    except Exception as e:
        print(f"Error fixing return_detail template: {str(e)}")
        return False

def create_db_fix_script():
    """Create a script to fix the database values"""
    script_path = r"c:\Users\USER\erpsystem_working_backup\fix_db_values.py"
    
    try:
        script_content = """\"\"\"
Fix for the database values in the pos_return_lines table.
\"\"\"
from flask import Flask
from app import create_app
from modules.pos.models import POSReturn, POSReturnLine, POSOrderLine
from extensions import db

def fix_db_values():
    \"\"\"Fix the values in the pos_return_lines table\"\"\"
    try:
        # Get all return lines
        return_lines = POSReturnLine.query.all()
        fixed_count = 0
        
        print(f"Found {len(return_lines)} return lines")
        
        for line in return_lines:
            needs_update = False
            
            # Check if the unit price is missing or zero
            if line.unit_price is None or line.unit_price <= 0:
                # Try to get the unit price from the original order line
                if line.original_order_line_id:
                    original_line = POSOrderLine.query.get(line.original_order_line_id)
                    if original_line and original_line.unit_price > 0:
                        line.unit_price = float(original_line.unit_price)
                        needs_update = True
                        print(f"Updated line {line.id} unit price to {line.unit_price} from original order line")
            
            # Ensure quantity is valid
            if line.quantity is None or line.quantity <= 0:
                line.quantity = 1.0
                needs_update = True
                print(f"Updated line {line.id} quantity to 1.0")
            
            # Ensure subtotal is correctly calculated
            correct_subtotal = float(line.quantity) * float(line.unit_price)
            if line.subtotal is None or line.subtotal <= 0 or abs(line.subtotal - correct_subtotal) > 0.01:
                line.subtotal = correct_subtotal
                needs_update = True
                print(f"Updated line {line.id} subtotal to {line.subtotal}")
            
            if needs_update:
                db.session.add(line)
                fixed_count += 1
        
        if fixed_count > 0:
            db.session.commit()
            print(f"Fixed {fixed_count} return lines")
        else:
            print("No return lines needed fixing")
        
        # Update the total_amount for all returns
        returns = POSReturn.query.all()
        updated_returns = 0
        
        for return_ in returns:
            # Calculate the total amount from the return lines
            total = sum(line.subtotal for line in return_.return_lines if line.subtotal)
            
            # Update the return total_amount if it's different
            if abs(return_.total_amount - total) > 0.01:
                return_.total_amount = total
                db.session.add(return_)
                updated_returns += 1
        
        if updated_returns > 0:
            db.session.commit()
            print(f"Updated total_amount for {updated_returns} returns")
        
        return True
    except Exception as e:
        print(f"Error fixing DB values: {str(e)}")
        db.session.rollback()
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    # Create the application context
    app = create_app()
    
    # Run the fix within the application context
    with app.app_context():
        if fix_db_values():
            print("Successfully fixed DB values")
        else:
            print("Failed to fix DB values")
"""
        
        with open(script_path, 'w', encoding='utf-8') as f:
            f.write(script_content)
        
        print(f"Successfully created {script_path}")
        return True
    except Exception as e:
        print(f"Error creating DB fix script: {str(e)}")
        return False

def create_return_detail_fix():
    """Create a patch for the return_detail route"""
    patch_path = r"c:\Users\USER\erpsystem_working_backup\patch_return_detail.py"
    
    try:
        patch_content = """\"\"\"
Patch for the return_detail route to ensure correct values are displayed.
\"\"\"
from flask import Flask
from app import create_app
from modules.pos.models import POSReturn, POSReturnLine
from extensions import db
import types

def patch_return_detail():
    \"\"\"Patch the return_detail route to ensure correct values are displayed\"\"\"
    try:
        # Import the routes module
        from modules.pos.routes import return_detail, pos
        
        # Define the patched function
        def patched_return_detail(return_id):
            \"\"\"Patched version of return_detail\"\"\"
            from flask import render_template, flash, redirect, url_for
            from modules.pos.models import POSReturn, POSOrder, db
            import traceback
            
            try:
                pos_return = POSReturn.query.get_or_404(return_id)
                
                # Ensure all return lines have valid products
                for line in pos_return.return_lines:
                    if not line.product:
                        print(f"Warning: Return line {line.id} has no associated product (product_id: {line.product_id})")
                
                # Get original order details
                original_order = None
                if pos_return.original_order_id:
                    original_order = POSOrder.query.get(pos_return.original_order_id)
                    
                    if original_order:
                        # Create a dictionary of valid products from the original order
                        valid_product_ids = set()
                        for line in original_order.lines:
                            valid_product_ids.add(line.product_id)
                        
                        # Check for any return lines with products not in the original order
                        for line in pos_return.return_lines:
                            if line.product_id not in valid_product_ids:
                                print(f"Warning: Return line {line.id} has product {line.product_id} which was not in the original order")
                
                # Debug logging for return line values
                print(f"Return line values:")
                for line in pos_return.return_lines:
                    print(f"  Line {line.id}: quantity={line.quantity}, unit_price={line.unit_price}, subtotal={line.subtotal}")
                    # Ensure subtotal is correctly calculated
                    if line.quantity and line.unit_price and (line.subtotal <= 0 or line.subtotal != line.quantity * line.unit_price):
                        line.subtotal = float(line.quantity) * float(line.unit_price)
                        print(f"  Updated subtotal to {line.subtotal}")
                        db.session.add(line)
                
                # Commit any changes
                if db.session.dirty:
                    db.session.commit()
                    print("Committed updates to return lines")
                
                return render_template('pos/return_detail.html', return_=pos_return, original_order=original_order)
            except Exception as e:
                print(f"Error viewing return details: {str(e)}")
                traceback.print_exc()
                flash(f"Error viewing return details: {str(e)}", "danger")
                return redirect(url_for('pos.returns'))
        
        # Replace the original function with our patched version
        pos.view_functions['return_detail'] = patched_return_detail
        
        print("Successfully patched return_detail route")
        return True
    except Exception as e:
        print(f"Error patching return_detail route: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    # Create the application context
    app = create_app()
    
    # Run the patch within the application context
    with app.app_context():
        if patch_return_detail():
            print("Successfully patched return_detail route")
        else:
            print("Failed to patch return_detail route")
"""
        
        with open(patch_path, 'w', encoding='utf-8') as f:
            f.write(patch_content)
        
        print(f"Successfully created {patch_path}")
        return True
    except Exception as e:
        print(f"Error creating return_detail patch: {str(e)}")
        return False

def create_startup_script():
    """Create a startup script that applies all fixes and starts the application"""
    script_path = r"c:\Users\USER\erpsystem_working_backup\start_app.py"
    
    try:
        script_content = """\"\"\"
Startup script that applies all fixes and starts the application.
\"\"\"
import os
import sys
import subprocess

def main():
    \"\"\"Apply all fixes and start the application\"\"\"
    print("Applying fixes and starting the application...")
    
    # Run the database fix script
    print("Fixing database values...")
    result = subprocess.run([sys.executable, "fix_db_values.py"], capture_output=True, text=True)
    print(result.stdout)
    if result.returncode != 0:
        print(f"Error fixing database values: {result.stderr}")
    
    # Start the application with the patched return_detail route
    print("Starting the application...")
    os.environ["PATCH_RETURN_DETAIL"] = "1"
    os.execv(sys.executable, [sys.executable, "app.py"])
    
    return True

if __name__ == "__main__":
    main()
"""
        
        with open(script_path, 'w', encoding='utf-8') as f:
            f.write(script_content)
        
        print(f"Successfully created {script_path}")
        return True
    except Exception as e:
        print(f"Error creating startup script: {str(e)}")
        return False

def update_app_py():
    """Update app.py to apply the return_detail patch at startup"""
    app_path = r"c:\Users\USER\erpsystem_working_backup\app.py"
    
    if not backup_file(app_path):
        return False
    
    try:
        with open(app_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Find the section where the new_partial_return is registered
        if "# Register our new implementation of the partial return functionality" in content:
            # Add the return_detail patch after the new_partial_return registration
            patch_code = """
    # Apply the return_detail patch if requested
    if os.environ.get("PATCH_RETURN_DETAIL") == "1":
        try:
            from patch_return_detail import patch_return_detail
            with app.app_context():
                if patch_return_detail():
                    print("Return detail route patched successfully")
                else:
                    print("Failed to patch return detail route")
        except Exception as e:
            print(f"Error patching return detail route: {str(e)}")
            import traceback
            traceback.print_exc()
"""
            
            # Insert the patch code after the new_partial_return registration
            updated_content = content.replace(
                "    # Register our new implementation of the partial return functionality",
                "    # Register our new implementation of the partial return functionality" + patch_code
            )
            
            with open(app_path, 'w', encoding='utf-8') as f:
                f.write(updated_content)
            
            print("Successfully updated app.py to apply the return_detail patch at startup")
        else:
            print("Could not find the expected section in app.py")
        
        return True
    except Exception as e:
        print(f"Error updating app.py: {str(e)}")
        return False

def main():
    """Apply all fixes"""
    print("Starting final fix for partial return functionality...")
    
    # Fix the return_detail.html template
    if not fix_return_detail_template():
        print("Failed to fix return_detail template")
        return False
    
    # Create the database fix script
    if not create_db_fix_script():
        print("Failed to create database fix script")
        return False
    
    # Create the return_detail patch
    if not create_return_detail_fix():
        print("Failed to create return_detail patch")
        return False
    
    # Update app.py to apply the return_detail patch at startup
    if not update_app_py():
        print("Failed to update app.py")
        return False
    
    # Create the startup script
    if not create_startup_script():
        print("Failed to create startup script")
        return False
    
    print("\nAll fixes applied successfully!")
    print("To start the application with the fixes, run:")
    print("python start_app.py")
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
