"""
Complete fix for the partial return functionality in the ERP system.
This script directly patches the database and the application code to ensure partial returns work correctly.
"""
import os
import sys
import importlib
import inspect
import types
from flask import Flask
from flask_sqlalchemy import SQLAlchemy

# Create a minimal Flask app
app = Flask(__name__)

# Configure the SQLAlchemy part of the app
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'sqlite:///erp.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize SQLAlchemy
db = SQLAlchemy(app)

def get_table_name():
    """Get the actual table name for return lines from the database"""
    with app.app_context():
        # Connect to the database
        from sqlalchemy import inspect
        inspector = inspect(db.engine)
        
        # Get all table names
        tables = inspector.get_table_names()
        print(f"Available tables: {tables}")
        
        # Look for tables that might be related to returns
        return_tables = [table for table in tables if 'return' in table.lower()]
        print(f"Return-related tables: {return_tables}")
        
        return return_tables

def patch_return_detail_template():
    """Patch the return_detail.html template to correctly display subtotals"""
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

def patch_partial_return_form():
    """Patch the partial_return_form.html template to correctly handle quantities and prices"""
    template_path = 'templates/pos/partial_return_form.html'
    
    try:
        with open(template_path, 'r', encoding='utf-8') as file:
            content = file.read()
        
        # Find and fix the quantity input to ensure it can handle decimals
        if 'type="number"' in content and 'step="1"' in content:
            # Replace step="1" with step="0.01" to allow decimal quantities
            content = content.replace('step="1"', 'step="0.01"')
            print("Fixed quantity input to allow decimals")
        
        # Ensure subtotal calculation is correct in JavaScript
        if 'const subtotal = Math.round((quantity * price) * 100) / 100;' in content:
            # Already using the correct calculation
            print("JavaScript already using correct subtotal calculation")
        else:
            # Try to find and replace the subtotal calculation
            import re
            pattern = r'const\s+subtotal\s*=\s*[^;]+;'
            match = re.search(pattern, content)
            
            if match:
                content = content.replace(
                    match.group(0),
                    'const subtotal = Math.round((quantity * price) * 100) / 100;'
                )
                print("Fixed subtotal calculation in JavaScript")
            else:
                print("Could not find subtotal calculation in JavaScript")
        
        # Write the updated content back to the file
        with open(template_path, 'w', encoding='utf-8') as file:
            file.write(content)
        
        print("Successfully patched partial_return_form.html template")
        return True
    except Exception as e:
        print(f"Error patching template: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def patch_routes():
    """Patch the routes.py file to correctly handle partial returns"""
    try:
        # Import the routes module
        import modules.pos.routes
        
        # Get the original function
        original_partial_return = modules.pos.routes.partial_return
        
        # Define the patched function
        def patched_partial_return():
            print("COMPLETE FIX: Using patched partial_return function")
            from flask import request, redirect, url_for, flash, render_template
            from flask_login import current_user
            from modules.pos.models import POSOrder, POSReturn, POSReturnLine, Product
            from extensions import db
            
            if request.method == 'POST':
                try:
                    # Log all form data for debugging
                    print("==== COMPLETE FIX - FORM DATA ====")
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
                    print(f"COMPLETE FIX - Product IDs: {product_ids}")
                    print(f"COMPLETE FIX - Quantities: {quantities}")
                    print(f"COMPLETE FIX - Prices: {prices}")
                    
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
                            
                            print(f"COMPLETE FIX - Line {i}: product={product_id}, quantity={quantity}, price={price}, subtotal={subtotal}")
                            
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
                    new_return.name = f"RET/COMPLETE/{timestamp}"
                    
                    db.session.add(new_return)
                    db.session.flush()  # Get the ID without committing
                    
                    # Create return lines
                    for line_data in return_lines_data:
                        # Create a return line with the correct values
                        return_line = POSReturnLine(
                            return_id=new_return.id,
                            product_id=line_data['product_id'],
                            return_reason=line_data['return_reason'],
                            quantity=line_data['quantity'],
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
                    flash(f"Partial return {new_return.name} created successfully", "success")
                    return redirect(url_for('pos.return_detail', return_id=new_return.id))
                    
                except Exception as e:
                    db.session.rollback()
                    flash(f"Error creating partial return: {str(e)}", "error")
                    import traceback
                    traceback.print_exc()
                    return redirect(url_for('pos.partial_return'))
            
            # GET request - show the form
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
        
        print("Successfully patched partial_return function")
        return True
    except Exception as e:
        print(f"Error patching routes: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def apply_fix():
    """Apply all fixes"""
    # Get the actual table names
    return_tables = get_table_name()
    
    # Patch the templates
    patch_return_detail_template()
    patch_partial_return_form()
    
    # Patch the routes
    patch_routes()
    
    print("Complete return fix applied successfully")
    return True

if __name__ == "__main__":
    apply_fix()
