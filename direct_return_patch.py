
# Direct patch for return functionality
from flask import Flask, request, redirect, url_for, flash, render_template
from flask_login import current_user
import os
import sys
import decimal

def patch_return_functionality(app):
    """
    Patch the return functionality to ensure quantities, prices, and subtotals are correct
    """
    with app.app_context():
        # Import the models
        from modules.pos.models import POSReturn, POSReturnLine, POSOrder, POSOrderLine, Product
        from extensions import db
        
        # Define the patched function
        def patched_partial_return():
            print("DIRECT PATCH: Using patched partial_return function")
            
            if request.method == 'POST':
                try:
                    # Log all form data for debugging
                    print("==== DIRECT PATCH - FORM DATA ====")
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
                    print(f"DIRECT PATCH - Product IDs: {product_ids}")
                    print(f"DIRECT PATCH - Quantities: {quantities}")
                    print(f"DIRECT PATCH - Prices: {prices}")
                    
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
                            
                            print(f"DIRECT PATCH - Line {i}: product={product_id}, quantity={quantity}, price={price}, subtotal={subtotal}")
                            
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
                    new_return.name = f"RET/PATCH/{timestamp}"
                    
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
                    
                    # Double-check that the return was created correctly
                    saved_return = POSReturn.query.get(new_return.id)
                    if saved_return.total_amount != total_amount:
                        print(f"DIRECT PATCH - Return total amount is incorrect: {saved_return.total_amount} != {total_amount}")
                        saved_return.total_amount = total_amount
                        saved_return.refund_amount = total_amount
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
        import modules.pos.routes
        modules.pos.routes.partial_return = patched_partial_return
        
        print("Return functionality patched successfully")
        return True

# Function to be called from app.py
def initialize_fix(app):
    return patch_return_functionality(app)
