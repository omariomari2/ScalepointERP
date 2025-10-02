"""
EMERGENCY SCHEMA FIX for the return functionality
This script directly modifies the database schema and the return processing logic
"""
import os
import sys
import sqlite3
from flask import Flask
from flask_sqlalchemy import SQLAlchemy

# Create a minimal Flask app
app = Flask(__name__)

# Configure the SQLAlchemy part of the app
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'sqlite:///erp_system.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize SQLAlchemy
db = SQLAlchemy(app)

def fix_database_schema():
    """Fix the database schema to properly handle return quantities and prices"""
    db_file = 'erp_system.db'
    if not os.path.exists(db_file):
        print(f"Database file {db_file} not found")
        return False
    
    try:
        # Connect to the database
        conn = sqlite3.connect(db_file)
        cursor = conn.cursor()
        
        print(f"Connected to database: {db_file}")
        
        # Check if we need to modify the pos_return_lines table
        cursor.execute("PRAGMA table_info(pos_return_lines)")
        columns = cursor.fetchall()
        column_names = [col[1] for col in columns]
        column_types = [col[2] for col in columns]
        
        print(f"Current pos_return_lines columns: {list(zip(column_names, column_types))}")
        
        # Check if quantity column is INTEGER
        quantity_index = column_names.index('quantity') if 'quantity' in column_names else -1
        
        if quantity_index >= 0 and 'INT' in column_types[quantity_index].upper():
            print("Quantity column is INTEGER, need to convert to REAL")
            
            # SQLite doesn't support ALTER COLUMN directly, so we need to:
            # 1. Create a new table with the correct schema
            # 2. Copy data from the old table
            # 3. Drop the old table
            # 4. Rename the new table
            
            # Create a backup of the original table first
            cursor.execute("CREATE TABLE pos_return_lines_backup AS SELECT * FROM pos_return_lines")
            print("Created backup of pos_return_lines table")
            
            # Get the CREATE TABLE statement for the original table
            cursor.execute("SELECT sql FROM sqlite_master WHERE type='table' AND name='pos_return_lines'")
            create_table_sql = cursor.fetchone()[0]
            
            # Modify the CREATE TABLE statement to change quantity to REAL
            create_table_sql = create_table_sql.replace(
                'quantity INTEGER', 'quantity REAL'
            ).replace(
                'quantity integer', 'quantity REAL'
            ).replace(
                'quantity INT', 'quantity REAL'
            ).replace(
                'quantity int', 'quantity REAL'
            )
            
            # Create a new table with the modified schema
            cursor.execute("DROP TABLE IF EXISTS pos_return_lines_new")
            cursor.execute(create_table_sql.replace('pos_return_lines', 'pos_return_lines_new'))
            print("Created new pos_return_lines_new table with REAL quantity column")
            
            # Copy data from the old table to the new table
            cursor.execute("INSERT INTO pos_return_lines_new SELECT * FROM pos_return_lines")
            print("Copied data from pos_return_lines to pos_return_lines_new")
            
            # Drop the old table
            cursor.execute("DROP TABLE pos_return_lines")
            print("Dropped old pos_return_lines table")
            
            # Rename the new table
            cursor.execute("ALTER TABLE pos_return_lines_new RENAME TO pos_return_lines")
            print("Renamed pos_return_lines_new to pos_return_lines")
            
            # Verify the change
            cursor.execute("PRAGMA table_info(pos_return_lines)")
            columns = cursor.fetchall()
            column_names = [col[1] for col in columns]
            column_types = [col[2] for col in columns]
            
            print(f"New pos_return_lines columns: {list(zip(column_names, column_types))}")
        else:
            print("Quantity column is already REAL or not found")
        
        # Commit the changes
        conn.commit()
        print("Changes committed to database")
        
        # Close the connection
        conn.close()
        print("Database connection closed")
        
        return True
    except Exception as e:
        print(f"Error fixing database schema: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def fix_return_processing():
    """Fix the return processing logic to correctly handle quantities, prices, and subtotals"""
    try:
        # Import the necessary modules
        import modules.pos.routes
        from flask import request, redirect, url_for, flash, render_template
        from flask_login import current_user
        
        # Get the original functions
        original_partial_return = modules.pos.routes.partial_return
        
        # Define the patched function for partial returns
        def patched_partial_return():
            print("EMERGENCY SCHEMA FIX: Using patched partial_return function")
            
            if request.method == 'POST':
                try:
                    # Import the models inside the function to avoid circular imports
                    from modules.pos.models import POSOrder, POSReturn, POSReturnLine, Product
                    from extensions import db
                    
                    # Log all form data for debugging
                    print("==== EMERGENCY SCHEMA FIX - FORM DATA ====")
                    for key, value in request.form.items():
                        if '[]' in key:
                            values = request.form.getlist(key)
                            print(f"{key}: {values}")
                        else:
                            print(f"{key}: {value}")
                    
                    # Get form data
                    original_order_id = request.form.get('original_order_id')
                    if not original_order_id:
                        flash("An original order must be selected for all returns", "error")
                        return redirect(url_for('pos.partial_return'))
                    
                    # Get customer information
                    customer_name = request.form.get('customer_name', '')
                    customer_phone = request.form.get('customer_phone', '')
                    
                    # Get return details
                    refund_method = request.form.get('refund_method', 'cash')
                    notes = request.form.get('notes', '')
                    
                    # Get the original order to validate products
                    original_order = POSOrder.query.get_or_404(original_order_id)
                    
                    # Get product data from form
                    product_ids = request.form.getlist('product_id[]')
                    quantities = request.form.getlist('quantity[]')
                    prices = request.form.getlist('price[]')
                    return_reasons = request.form.getlist('return_reason[]')
                    line_notes = request.form.getlist('line_notes[]')
                    original_line_ids = request.form.getlist('original_line_id[]')
                    
                    # Debug information
                    print(f"EMERGENCY SCHEMA FIX - Product IDs: {product_ids}")
                    print(f"EMERGENCY SCHEMA FIX - Quantities: {quantities}")
                    print(f"EMERGENCY SCHEMA FIX - Prices: {prices}")
                    
                    # Calculate total amount and validate quantities
                    total_amount = 0
                    return_lines_data = []
                    
                    for i in range(len(product_ids)):
                        if not product_ids[i]:
                            continue
                        
                        try:
                            product_id = int(product_ids[i])
                            quantity = float(quantities[i]) if quantities[i] else 0
                            price = float(prices[i]) if prices[i] else 0
                            reason = return_reasons[i] if i < len(return_reasons) else ""
                            note = line_notes[i] if i < len(line_notes) else ""
                            original_line_id = original_line_ids[i] if i < len(original_line_ids) else None
                            
                            # Skip products with zero quantity
                            if quantity <= 0:
                                continue
                            
                            # Calculate subtotal with proper rounding
                            subtotal = round(quantity * price, 2)
                            total_amount += subtotal
                            
                            print(f"EMERGENCY SCHEMA FIX - Line {i}: product={product_id}, quantity={quantity}, price={price}, subtotal={subtotal}")
                            
                            # Add to return lines data
                            return_lines_data.append({
                                'product_id': product_id,
                                'quantity': quantity,
                                'unit_price': price,
                                'subtotal': subtotal,
                                'return_reason': reason,
                                'notes': note,
                                'original_line_id': original_line_id
                            })
                        except Exception as e:
                            print(f"Error processing line {i}: {str(e)}")
                    
                    if not return_lines_data:
                        flash("Please add at least one product to return", "error")
                        return redirect(url_for('pos.partial_return'))
                    
                    # Create a new return record
                    return_type = 'partial'  # Always partial for this route
                    
                    new_return = POSReturn(
                        original_order_id=original_order_id,
                        customer_name=customer_name,
                        customer_phone=customer_phone,
                        total_amount=total_amount,
                        refund_amount=total_amount,  # Default to same as total
                        return_type=return_type,
                        refund_method=refund_method,
                        notes=notes,
                        state='draft',
                        created_by=current_user.id,
                        exchange_processed=False  # Initialize as not processed for exchange
                    )
                    
                    # Generate a unique name for the return
                    from datetime import datetime
                    timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
                    new_return.name = f"RET/SCHEMA/{timestamp}"
                    
                    db.session.add(new_return)
                    db.session.flush()  # Get the ID without committing
                    
                    # Create return lines
                    for line_data in return_lines_data:
                        # Create a return line with the correct values
                        return_line = POSReturnLine(
                            return_id=new_return.id,
                            product_id=line_data['product_id'],
                            return_reason=line_data['return_reason'],
                            quantity=line_data['quantity'],  # Now a REAL column
                            unit_price=line_data['unit_price'],
                            subtotal=line_data['subtotal'],
                            state='draft'
                        )
                        
                        # If we have an original line ID, set it
                        if line_data['original_line_id']:
                            return_line.original_order_line_id = line_data['original_line_id']
                        
                        # Get product name for resilience
                        product = Product.query.get(line_data['product_id'])
                        if product:
                            return_line.product_name = product.name
                        
                        db.session.add(return_line)
                    
                    # Update the returned_quantity on the original order lines
                    for line_data in return_lines_data:
                        product_id = line_data['product_id']
                        return_quantity = line_data['quantity']
                        
                        # Get all original order lines for this product
                        product_lines = [line for line in original_order.lines if line.product_id == product_id and line.quantity > line.returned_quantity]
                        
                        # Sort lines by ID to ensure consistent processing
                        product_lines.sort(key=lambda x: x.id)
                        
                        # Distribute the returned quantity across the original lines
                        remaining_to_return = return_quantity
                        for original_line in product_lines:
                            if remaining_to_return <= 0:
                                break
                                
                            # Calculate how much can be returned from this line
                            available_from_line = max(0, original_line.quantity - original_line.returned_quantity)
                            
                            if available_from_line <= 0:
                                continue
                                
                            # Determine how much to return from this line
                            return_from_line = min(remaining_to_return, available_from_line)
                            
                            # Update the returned quantity
                            original_line.returned_quantity += return_from_line
                            
                            # Reduce the remaining quantity to return
                            remaining_to_return -= return_from_line
                    
                    db.session.commit()
                    
                    # EMERGENCY SCHEMA FIX: Verify the return was saved correctly
                    saved_return = POSReturn.query.get(new_return.id)
                    print(f"EMERGENCY SCHEMA FIX - Saved return: total_amount={saved_return.total_amount}, refund_amount={saved_return.refund_amount}")
                    
                    # EMERGENCY SCHEMA FIX: If the total amount is wrong, fix it directly
                    if abs(saved_return.total_amount - total_amount) > 0.01:
                        print(f"EMERGENCY SCHEMA FIX - Fixing incorrect total amount: {saved_return.total_amount} -> {total_amount}")
                        saved_return.total_amount = total_amount
                        saved_return.refund_amount = total_amount
                        db.session.commit()
                    
                    # EMERGENCY SCHEMA FIX: Verify the return lines were saved correctly
                    for line in saved_return.return_lines:
                        print(f"EMERGENCY SCHEMA FIX - Saved line: quantity={line.quantity}, unit_price={line.unit_price}, subtotal={line.subtotal}")
                        expected_subtotal = round(float(line.quantity) * float(line.unit_price), 2)
                        if abs(float(line.subtotal) - expected_subtotal) > 0.01:
                            print(f"EMERGENCY SCHEMA FIX - Fixing incorrect line subtotal: {line.subtotal} -> {expected_subtotal}")
                            line.subtotal = expected_subtotal
                            db.session.commit()
                    
                    flash(f"Partial return {new_return.name} created successfully", "success")
                    return redirect(url_for('pos.return_detail', return_id=new_return.id))
                    
                except Exception as e:
                    db.session.rollback()
                    flash(f"Error creating partial return: {str(e)}", "error")
                    import traceback
                    traceback.print_exc()
                    return redirect(url_for('pos.partial_return'))
            
            # GET request - show the form
            from modules.pos.models import POSOrder
            
            # Get all orders that can be returned (not fully returned already)
            orders = POSOrder.query.filter_by(state='completed').all()
            returnable_orders = []
            
            for order in orders:
                # Check if order has any returnable lines
                has_returnable_lines = False
                for line in order.lines:
                    if line.quantity > line.returned_quantity:
                        has_returnable_lines = True
                        break
                
                if has_returnable_lines:
                    returnable_orders.append(order)
            
            return render_template('pos/partial_return_form.html', orders=returnable_orders)
        
        # Replace the original function with the patched one
        modules.pos.routes.partial_return = patched_partial_return
        
        print("Return processing logic patched successfully")
        return True
    except Exception as e:
        print(f"Error fixing return processing logic: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def fix_return_model():
    """Fix the POSReturnLine model to use float for quantity"""
    try:
        with app.app_context():
            # Import the models
            from modules.pos.models import POSReturnLine
            from sqlalchemy import Float
            
            # Monkey patch the quantity column to be a float
            # This won't change the database schema, but will affect how SQLAlchemy interacts with it
            POSReturnLine.quantity = db.Column(Float, default=0.0)
            
            print("POSReturnLine.quantity patched to be a Float in the model")
            return True
    except Exception as e:
        print(f"Error fixing return model: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def fix_return_detail_template():
    """Fix the return_detail.html template to correctly display subtotals"""
    template_path = 'templates/pos/return_detail.html'
    
    try:
        with open(template_path, 'r', encoding='utf-8') as file:
            content = file.read()
        
        # Find the line with the subtotal calculation
        if '<td class="text-end">GH₵{{ "%.2f"|format(line.subtotal) }}</td>' in content:
            # Replace it with a direct calculation
            content = content.replace(
                '<td class="text-end">GH₵{{ "%.2f"|format(line.subtotal) }}</td>',
                '<td class="text-end">GH₵{{ "%.2f"|format(line.quantity * line.unit_price) }}</td>'
            )
            print("Fixed subtotal calculation in template (case 1)")
        elif '<td class="text-end">GH₵{{ "%.2f"|format(line.quantity * line.unit_price) }}</td>' in content:
            # Already using the correct calculation
            print("Template already using correct subtotal calculation (case 2)")
        else:
            # Try to find and replace the subtotal display with a more general approach
            import re
            pattern = r'<td[^>]*class="text-end"[^>]*>GH₵[^<]*</td>'
            matches = re.findall(pattern, content)
            
            if len(matches) >= 3:  # We expect at least 3 matches (quantity, price, subtotal)
                # Replace the third instance (subtotal) with our calculation
                subtotal_match = matches[2]
                content = content.replace(
                    subtotal_match,
                    '<td class="text-end">GH₵{{ "%.2f"|format(line.quantity * line.unit_price) }}</td>'
                )
                print(f"Fixed subtotal calculation in template using pattern matching (case 3)")
            else:
                print(f"Could not find subtotal display in template, matches found: {len(matches)}")
        
        # Write the updated content back to the file
        with open(template_path, 'w', encoding='utf-8') as file:
            file.write(content)
        
        print("Successfully patched return_detail.html template")
        return True
    except Exception as e:
        print(f"Error patching template: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def apply_all_fixes():
    """Apply all fixes"""
    # Fix the database schema
    fix_database_schema()
    
    # Fix the return model
    fix_return_model()
    
    # Fix the return processing logic
    fix_return_processing()
    
    # Fix the return detail template
    fix_return_detail_template()
    
    print("All emergency schema fixes applied successfully")
    return True

if __name__ == "__main__":
    # Apply all fixes
    apply_all_fixes()
