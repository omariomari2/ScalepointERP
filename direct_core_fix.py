"""
Direct core fix for the partial return functionality in the ERP system.
This script directly modifies the core functionality to ensure return lines are correctly saved and displayed.
"""
import os
import sys
import shutil
from datetime import datetime
import re

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

def fix_return_model():
    """Fix the POSReturnLine model to ensure correct data types and calculations"""
    model_path = r"c:\Users\USER\erpsystem_working_backup\modules\pos\models.py"
    
    if not backup_file(model_path):
        return False
    
    try:
        with open(model_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Find the POSReturnLine class definition
        pos_return_line_class = re.search(r'class POSReturnLine\(.*?\):.*?(?=class|$)', content, re.DOTALL)
        
        if not pos_return_line_class:
            print("Error: Could not find POSReturnLine class in models.py")
            return False
        
        pos_return_line_def = pos_return_line_class.group(0)
        
        # Check if the model already has the correct field definitions
        if 'quantity = db.Column(db.Float, default=1.0, nullable=False)' in pos_return_line_def and \
           'unit_price = db.Column(db.Float, default=0.0, nullable=False)' in pos_return_line_def and \
           'subtotal = db.Column(db.Float, default=0.0, nullable=False)' in pos_return_line_def:
            print("POSReturnLine model already has correct field definitions")
        else:
            # Update the field definitions to ensure correct data types
            updated_def = pos_return_line_def
            
            # Update quantity field
            updated_def = re.sub(
                r'quantity\s*=\s*db\.Column\(.*?\)',
                'quantity = db.Column(db.Float, default=1.0, nullable=False)',
                updated_def
            )
            
            # Update unit_price field
            updated_def = re.sub(
                r'unit_price\s*=\s*db\.Column\(.*?\)',
                'unit_price = db.Column(db.Float, default=0.0, nullable=False)',
                updated_def
            )
            
            # Update subtotal field
            updated_def = re.sub(
                r'subtotal\s*=\s*db\.Column\(.*?\)',
                'subtotal = db.Column(db.Float, default=0.0, nullable=False)',
                updated_def
            )
            
            # Add __init__ method to ensure subtotal is calculated correctly
            if '__init__' not in updated_def:
                init_method = """
    def __init__(self, **kwargs):
        super(POSReturnLine, self).__init__(**kwargs)
        # Ensure subtotal is calculated correctly
        if hasattr(self, 'quantity') and hasattr(self, 'unit_price'):
            if self.quantity and self.unit_price:
                self.subtotal = float(self.quantity) * float(self.unit_price)
                print(f"POSReturnLine.__init__: Set subtotal={self.subtotal} (quantity={self.quantity}, unit_price={self.unit_price})")
"""
                # Find the last line of the class definition
                last_line = updated_def.rstrip().split('\n')[-1]
                # Insert the __init__ method before the last line
                updated_def = updated_def.replace(last_line, init_method + last_line)
            
            # Update the content with the modified class definition
            updated_content = content.replace(pos_return_line_def, updated_def)
            
            with open(model_path, 'w', encoding='utf-8') as f:
                f.write(updated_content)
            
            print("Successfully updated POSReturnLine model")
        
        return True
    except Exception as e:
        print(f"Error fixing POSReturnLine model: {str(e)}")
        return False

def fix_partial_return_route():
    """Fix the partial_return route to ensure correct values are saved"""
    routes_path = r"c:\Users\USER\erpsystem_working_backup\modules\pos\routes.py"
    
    if not backup_file(routes_path):
        return False
    
    try:
        with open(routes_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Find the partial_return function
        partial_return_func = re.search(r'@pos\.route\(\'/returns/partial\'.*?def partial_return\(\).*?(?=@pos\.route|\Z)', content, re.DOTALL)
        
        if not partial_return_func:
            print("Error: Could not find partial_return function in routes.py")
            return False
        
        partial_return_def = partial_return_func.group(0)
        
        # Check if the function already has the correct implementation for creating return lines
        if 'line_subtotal = price * quantity' in partial_return_def and \
           'subtotal=line_subtotal' in partial_return_def:
            print("partial_return function already has correct implementation")
        else:
            # Update the function to ensure correct values are saved
            updated_def = partial_return_def
            
            # Find the section where return lines are created
            return_line_creation = re.search(r'# Create a return line.*?return_line = POSReturnLine\(.*?\)', updated_def, re.DOTALL)
            
            if return_line_creation:
                return_line_code = return_line_creation.group(0)
                
                # Update the return line creation to ensure subtotal is calculated correctly
                if 'line_subtotal = price * quantity' not in return_line_code:
                    # Add the subtotal calculation before the return line creation
                    updated_line_code = return_line_code.replace(
                        'return_line = POSReturnLine(',
                        '# Calculate subtotal\n                line_subtotal = price * quantity\n                print(f"Creating return line with quantity={quantity}, price={price}, subtotal={line_subtotal}")\n                \n                return_line = POSReturnLine('
                    )
                    
                    # Update the return line creation to include subtotal
                    if 'subtotal=' not in updated_line_code:
                        updated_line_code = updated_line_code.replace(
                            'unit_price=price,',
                            'unit_price=price,\n                    subtotal=line_subtotal,'
                        )
                    
                    # Update the function with the modified return line creation
                    updated_def = updated_def.replace(return_line_code, updated_line_code)
                    
                    # Update the content with the modified function
                    updated_content = content.replace(partial_return_def, updated_def)
                    
                    with open(routes_path, 'w', encoding='utf-8') as f:
                        f.write(updated_content)
                    
                    print("Successfully updated partial_return function")
                else:
                    print("Return line creation already has correct implementation")
            else:
                print("Error: Could not find return line creation in partial_return function")
                return False
        
        return True
    except Exception as e:
        print(f"Error fixing partial_return route: {str(e)}")
        return False

def fix_return_detail_route():
    """Fix the return_detail route to ensure correct values are displayed"""
    routes_path = r"c:\Users\USER\erpsystem_working_backup\modules\pos\routes.py"
    
    try:
        with open(routes_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Find the return_detail function
        return_detail_func = re.search(r'@pos\.route\(\'/returns/(?P<return_id>\w+)\'.*?def return_detail\(return_id\).*?(?=@pos\.route|\Z)', content, re.DOTALL)
        
        if not return_detail_func:
            print("Error: Could not find return_detail function in routes.py")
            return False
        
        return_detail_def = return_detail_func.group(0)
        
        # Add debug logging to the return_detail function
        if 'print(f"Return line values:")' not in return_detail_def:
            # Find the line where the template is rendered
            render_template_line = re.search(r'return render_template\(.*?\)', return_detail_def)
            
            if render_template_line:
                render_line = render_template_line.group(0)
                
                # Add debug logging before the template is rendered
                debug_logging = """
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
        
"""
                
                # Insert the debug logging before the template rendering
                updated_def = return_detail_def.replace(render_line, debug_logging + render_line)
                
                # Update the content with the modified function
                updated_content = content.replace(return_detail_def, updated_def)
                
                with open(routes_path, 'w', encoding='utf-8') as f:
                    f.write(updated_content)
                
                print("Successfully updated return_detail function")
            else:
                print("Error: Could not find render_template line in return_detail function")
                return False
        else:
            print("return_detail function already has debug logging")
        
        return True
    except Exception as e:
        print(f"Error fixing return_detail route: {str(e)}")
        return False

def fix_return_detail_template():
    """Fix the return_detail.html template to correctly display values"""
    template_path = r"c:\Users\USER\erpsystem_working_backup\templates\pos\return_detail.html"
    
    if not backup_file(template_path):
        return False
    
    try:
        with open(template_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Find the table row that displays return line values
        table_row = re.search(r'<tr>.*?<td.*?>.*?</td>.*?<td class="text-end">.*?</td>.*?<td class="text-end">.*?</td>.*?<td class="text-end">.*?</td>.*?</tr>', content, re.DOTALL)
        
        if not table_row:
            print("Error: Could not find table row in return_detail.html")
            return False
        
        table_row_html = table_row.group(0)
        
        # Find the quantity, unit price, and subtotal cells
        quantity_cell = re.search(r'<td class="text-end">.*?</td>', table_row_html)
        unit_price_cell = re.search(r'<td class="text-end">.*?</td>', table_row_html[quantity_cell.end():])
        subtotal_cell = re.search(r'<td class="text-end">.*?</td>', table_row_html[quantity_cell.end() + unit_price_cell.end():])
        
        if not quantity_cell or not unit_price_cell or not subtotal_cell:
            print("Error: Could not find all cells in table row")
            return False
        
        # Update the cells to correctly display values
        updated_row = table_row_html
        
        # Update quantity cell
        updated_row = updated_row.replace(
            quantity_cell.group(0),
            '<td class="text-end">{{ "%.1f"|format(line.quantity|float) }}</td>'
        )
        
        # Update unit price cell
        updated_row = updated_row.replace(
            unit_price_cell.group(0),
            '<td class="text-end">GH₵{{ "%.2f"|format(line.unit_price|float) }}</td>'
        )
        
        # Update subtotal cell
        updated_row = updated_row.replace(
            subtotal_cell.group(0),
            '<td class="text-end">GH₵{{ "%.2f"|format(line.subtotal|float) }}</td>'
        )
        
        # Update the content with the modified table row
        updated_content = content.replace(table_row_html, updated_row)
        
        with open(template_path, 'w', encoding='utf-8') as f:
            f.write(updated_content)
        
        print("Successfully updated return_detail.html template")
        return True
    except Exception as e:
        print(f"Error fixing return_detail template: {str(e)}")
        return False

def create_direct_db_fix():
    """Create a script to directly fix the database values"""
    script_path = r"c:\Users\USER\erpsystem_working_backup\fix_return_db_values.py"
    
    try:
        script_content = """\"\"\"
Direct fix for the database values in the pos_return_lines table.
This script should be run within the application context.
\"\"\"
from flask import Flask
from app import create_app
from modules.pos.models import POSReturn, POSReturnLine, POSOrderLine
from extensions import db

def fix_return_db_values():
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
                    else:
                        print(f"Could not find valid unit price for line {line.id} from original order line")
                # If we still don't have a valid unit price, try to get it from the product
                if line.unit_price is None or line.unit_price <= 0:
                    if line.product and hasattr(line.product, 'list_price') and line.product.list_price > 0:
                        line.unit_price = float(line.product.list_price)
                        needs_update = True
                        print(f"Updated line {line.id} unit price to {line.unit_price} from product")
                    else:
                        print(f"Could not find valid unit price for line {line.id} from product")
            
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
        else:
            print("No returns needed total_amount updates")
        
        return True
    except Exception as e:
        print(f"Error fixing return DB values: {str(e)}")
        db.session.rollback()
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    # Create the application context
    app = create_app()
    
    # Run the fix within the application context
    with app.app_context():
        if fix_return_db_values():
            print("Successfully fixed return DB values")
        else:
            print("Failed to fix return DB values")
"""
        
        with open(script_path, 'w', encoding='utf-8') as f:
            f.write(script_content)
        
        print(f"Successfully created {script_path}")
        return True
    except Exception as e:
        print(f"Error creating direct DB fix script: {str(e)}")
        return False

def create_startup_script():
    """Create a startup script that applies all fixes and starts the application"""
    script_path = r"c:\Users\USER\erpsystem_working_backup\start_fixed_app.py"
    
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
    print("Fixing return DB values...")
    result = subprocess.run([sys.executable, "fix_return_db_values.py"], capture_output=True, text=True)
    if result.returncode != 0:
        print(f"Error fixing return DB values: {result.stderr}")
        return False
    
    print(result.stdout)
    
    # Start the application
    print("Starting the application...")
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

def main():
    """Apply all fixes"""
    print("Starting direct core fix for partial return functionality...")
    
    # Fix the POSReturnLine model
    if not fix_return_model():
        print("Failed to fix POSReturnLine model")
        return False
    
    # Fix the partial_return route
    if not fix_partial_return_route():
        print("Failed to fix partial_return route")
        return False
    
    # Fix the return_detail route
    if not fix_return_detail_route():
        print("Failed to fix return_detail route")
        return False
    
    # Fix the return_detail.html template
    if not fix_return_detail_template():
        print("Failed to fix return_detail template")
        return False
    
    # Create the direct DB fix script
    if not create_direct_db_fix():
        print("Failed to create direct DB fix script")
        return False
    
    # Create the startup script
    if not create_startup_script():
        print("Failed to create startup script")
        return False
    
    print("\nAll fixes applied successfully!")
    print("To start the application with the fixes, run:")
    print("python start_fixed_app.py")
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
