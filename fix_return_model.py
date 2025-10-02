"""
Direct fix for the return model and data handling in the ERP system.
This script modifies the POSReturnLine model to ensure quantity is stored as a float instead of an integer.
"""
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
import os
import sys
import decimal

# Create a minimal Flask app
app = Flask(__name__)

# Configure the SQLAlchemy part of the app
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'sqlite:///erp.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize SQLAlchemy
db = SQLAlchemy(app)

def fix_return_model():
    """
    Apply the fix to the return model by modifying the column type for quantity.
    """
    with app.app_context():
        # Import the models
        from modules.pos.models import POSReturnLine
        
        # Get the inspector to check the current column type
        from sqlalchemy import inspect
        inspector = inspect(db.engine)
        
        # Check if we need to modify the column
        columns = inspector.get_columns('pos_return_lines')
        quantity_column = next((col for col in columns if col['name'] == 'quantity'), None)
        
        if quantity_column:
            print(f"Current quantity column type: {quantity_column['type']}")
            
            # If the column is an integer, we need to modify it to be a float
            if 'INTEGER' in str(quantity_column['type']).upper():
                print("Converting quantity column from INTEGER to FLOAT...")
                
                # Execute the ALTER TABLE statement
                with db.engine.connect() as conn:
                    # For SQLite, we need to create a new table and copy the data
                    if 'sqlite' in str(db.engine.url):
                        # SQLite doesn't support ALTER COLUMN, so we need to:
                        # 1. Create a new table with the correct schema
                        # 2. Copy data from the old table
                        # 3. Drop the old table
                        # 4. Rename the new table
                        
                        # Create a temporary table with the correct schema
                        conn.execute("""
                        CREATE TABLE pos_return_lines_new (
                            id INTEGER PRIMARY KEY,
                            return_id INTEGER NOT NULL,
                            product_id INTEGER NOT NULL,
                            original_order_line_id INTEGER,
                            quantity FLOAT DEFAULT 0.0,
                            unit_price FLOAT DEFAULT 0.0,
                            subtotal FLOAT DEFAULT 0.0,
                            return_reason VARCHAR(64),
                            state VARCHAR(20) DEFAULT 'draft',
                            product_name VARCHAR(255),
                            FOREIGN KEY (return_id) REFERENCES pos_returns (id),
                            FOREIGN KEY (product_id) REFERENCES products (id),
                            FOREIGN KEY (original_order_line_id) REFERENCES pos_order_lines (id)
                        )
                        """)
                        
                        # Copy data from the old table, converting quantity to float
                        conn.execute("""
                        INSERT INTO pos_return_lines_new
                        SELECT id, return_id, product_id, original_order_line_id, 
                               CAST(quantity AS FLOAT), unit_price, subtotal, 
                               return_reason, state, product_name
                        FROM pos_return_lines
                        """)
                        
                        # Drop the old table
                        conn.execute("DROP TABLE pos_return_lines")
                        
                        # Rename the new table
                        conn.execute("ALTER TABLE pos_return_lines_new RENAME TO pos_return_lines")
                        
                        print("Successfully converted quantity column to FLOAT in SQLite")
                    else:
                        # For PostgreSQL or other databases that support ALTER COLUMN
                        conn.execute("ALTER TABLE pos_return_lines ALTER COLUMN quantity TYPE FLOAT")
                        print("Successfully converted quantity column to FLOAT")
            else:
                print("Quantity column is already a FLOAT, no need to modify")
        else:
            print("Could not find quantity column in pos_return_lines table")

def fix_existing_returns():
    """
    Fix existing returns in the database to ensure quantities, prices, and subtotals are correct.
    """
    with app.app_context():
        # Import the models
        from modules.pos.models import POSReturn, POSReturnLine, POSOrder, POSOrderLine
        
        # Get all returns
        returns = POSReturn.query.all()
        print(f"Found {len(returns)} returns to fix")
        
        fixed_count = 0
        
        for return_ in returns:
            print(f"\nProcessing return {return_.name} (ID: {return_.id})")
            
            # Track if this return needs fixing
            return_fixed = False
            return_total = 0
            
            # Process each return line
            for line in return_.return_lines:
                print(f"  Processing line {line.id} for product {line.product_id}")
                
                # Get the original order line if available
                original_line = None
                if line.original_order_line_id:
                    original_line = POSOrderLine.query.get(line.original_order_line_id)
                
                # Fix the unit price if it's zero or invalid
                if line.unit_price <= 0 and original_line:
                    old_price = line.unit_price
                    line.unit_price = original_line.unit_price
                    print(f"    Fixed unit price: {old_price} -> {line.unit_price}")
                    return_fixed = True
                    fixed_count += 1
                
                # Calculate the correct subtotal
                correct_subtotal = round(float(line.quantity) * float(line.unit_price), 2)
                
                # Fix the subtotal if it's incorrect
                if abs(line.subtotal - correct_subtotal) > 0.01:
                    old_subtotal = line.subtotal
                    line.subtotal = correct_subtotal
                    print(f"    Fixed subtotal: {old_subtotal} -> {line.subtotal}")
                    return_fixed = True
                    fixed_count += 1
                
                # Add to the return total
                return_total += line.subtotal
            
            # Fix the return total if needed
            if abs(return_.total_amount - return_total) > 0.01:
                old_total = return_.total_amount
                return_.total_amount = return_total
                return_.refund_amount = return_total  # Also fix the refund amount
                print(f"  Fixed return total: {old_total} -> {return_total}")
                return_fixed = True
            
            if return_fixed:
                fixed_count += 1
        
        # Commit all changes
        if fixed_count > 0:
            db.session.commit()
            print(f"\nFixed {fixed_count} returns and return lines")
        else:
            print("\nNo returns needed fixing")

def monkey_patch_model():
    """
    Monkey patch the POSReturnLine model to ensure quantity is handled as a float.
    """
    with app.app_context():
        # Import the models
        from modules.pos.models import POSReturnLine
        from sqlalchemy import Float
        
        # Monkey patch the quantity column to be a float
        POSReturnLine.quantity = db.Column(Float, default=0.0)
        
        print("Monkey patched POSReturnLine.quantity to be a Float")

def monkey_patch_routes():
    """
    Monkey patch the routes to ensure quantities are handled correctly.
    """
    try:
        # Import the routes module
        import modules.pos.routes
        
        # Get the original functions
        original_partial_return = modules.pos.routes.partial_return
        
        # Define the patched function
        def patched_partial_return():
            print("DIRECT FIX: Using patched partial_return function")
            from flask import request, redirect, url_for, flash
            from flask_login import current_user
            from modules.pos.models import POSOrder, POSReturn, POSReturnLine, Product
            from extensions import db
            
            # Call the original function if it's not a POST request
            if request.method != 'POST':
                return original_partial_return()
            
            try:
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
                print(f"DIRECT FIX - Received partial return data: {len(product_ids)} products")
                print(f"Product IDs: {product_ids}")
                print(f"Quantities: {quantities}")
                print(f"Prices: {prices}")
                
                # Calculate total amount and validate quantities
                total_amount = 0
                return_lines_data = []
                
                for i in range(len(product_ids)):
                    if not product_ids[i]:
                        continue
                    
                    product_id = int(product_ids[i])
                    quantity = float(quantities[i]) if quantities[i] else 0
                    price = float(prices[i]) if prices[i] else 0
                    reason = return_reasons[i] if i < len(return_reasons) else ""
                    note = line_notes[i] if i < len(line_notes) else ""
                    
                    # Skip products with zero quantity
                    if quantity <= 0:
                        continue
                    
                    # Calculate subtotal with proper rounding
                    subtotal = round(quantity * price, 2)
                    total_amount += subtotal
                    
                    # Add to return lines data
                    return_lines_data.append({
                        'product_id': product_id,
                        'quantity': quantity,
                        'unit_price': price,
                        'subtotal': subtotal,
                        'return_reason': reason,
                        'notes': note,
                        'original_line_id': original_line_ids[i] if i < len(original_line_ids) else None
                    })
                
                # Create a new return record
                return_type = request.form.get('return_type', 'partial')
                
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
                new_return.name = f"RET/FIX/{timestamp}"
                
                db.session.add(new_return)
                db.session.flush()  # Get the ID without committing
                
                # Create return lines
                for line_data in return_lines_data:
                    # Ensure we have valid numeric values
                    quantity = float(line_data['quantity'])
                    unit_price = float(line_data['unit_price'])
                    subtotal = round(quantity * unit_price, 2)
                    
                    print(f"DIRECT FIX - Creating return line with: quantity={quantity}, unit_price={unit_price}, subtotal={subtotal}")
                    
                    # Create a return line with the correct values
                    return_line = POSReturnLine(
                        return_id=new_return.id,
                        product_id=line_data['product_id'],
                        return_reason=line_data['return_reason'],
                        quantity=quantity,
                        unit_price=unit_price,
                        subtotal=subtotal,
                        state='draft'
                    )
                    
                    # If we have an original line ID, set it
                    if 'original_line_id' in line_data and line_data['original_line_id']:
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
                flash(f"Partial return {new_return.name} created successfully", "success")
                return redirect(url_for('pos.return_detail', return_id=new_return.id))
                
            except Exception as e:
                db.session.rollback()
                flash(f"Error creating partial return: {str(e)}", "error")
                import traceback
                traceback.print_exc()
                return redirect(url_for('pos.partial_return'))
        
        # Replace the original function with the patched one
        modules.pos.routes.partial_return = patched_partial_return
        
        print("Monkey patched partial_return function successfully")
        return True
    except Exception as e:
        print(f"Error monkey patching routes: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    # Fix the return model
    fix_return_model()
    
    # Fix existing returns
    fix_existing_returns()
    
    # Monkey patch the model
    monkey_patch_model()
    
    # Monkey patch the routes
    monkey_patch_routes()
    
    print("Return model and data fix completed successfully")
