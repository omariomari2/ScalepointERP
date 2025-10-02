# This file contains the fixed partial_return function for the ERP system
# Replace the existing partial_return function in modules/pos/routes.py with this code

@pos.route('/returns/partial', methods=['GET', 'POST'])
@login_required
def partial_return():
    """Create a new partial return"""
    if request.method == 'POST':
        try:
            # Log all form data for debugging
            print("==== PARTIAL RETURN FORM SUBMISSION DEBUG ====")
            print("All form data:")
            for key, value in request.form.items():
                print(f"  {key}: {value}")
            
            # Get form data
            original_order_id = request.form.get('original_order_id')
            if not original_order_id:
                raise ValueError("An original order must be selected for all returns")
            
            # Get customer information
            customer_name = request.form.get('customer_name', '')
            customer_phone = request.form.get('customer_phone', '')
            
            # Get return details
            refund_method = request.form.get('refund_method', 'cash')
            notes = request.form.get('notes', '')
            
            # Get the original order to validate products
            original_order = POSOrder.query.get_or_404(original_order_id)
            
            # Create a dictionary of returnable products from the original order
            valid_products = {}
            for line in original_order.lines:
                # Use integer returnable_quantity since products are sold as whole pieces
                returnable_quantity = max(0, int(line.quantity - line.returned_quantity))
                if returnable_quantity > 0:
                    if line.product_id not in valid_products:
                        valid_products[line.product_id] = {
                            'returnable_quantity': returnable_quantity,
                            'lines': []
                        }
                    else:
                        valid_products[line.product_id]['returnable_quantity'] += returnable_quantity
                        
                    valid_products[line.product_id]['lines'].append({
                        'line_id': line.id,
                        'returnable_quantity': returnable_quantity,
                        'unit_price': line.unit_price
                    })
            
            # Get product data from form
            product_ids = request.form.getlist('product_id[]')
            quantities = request.form.getlist('quantity[]')
            prices = request.form.getlist('price[]')
            return_reasons = request.form.getlist('return_reason[]')
            line_notes = request.form.getlist('line_notes[]')
            original_line_ids = request.form.getlist('original_line_id[]')
            
            # Debug information
            print(f"Received partial return data: {len(product_ids)} products")
            print(f"Product IDs: {product_ids}")
            print(f"Quantities: {quantities}")
            print(f"Prices: {prices}")
            print(f"Original line IDs: {original_line_ids}")
            
            # Validate the return data
            if not product_ids or not any(pid for pid in product_ids if pid):
                flash("Please add at least one product to return", "error")
                return redirect(url_for('pos.partial_return'))
            
            # Calculate total amount and validate quantities
            total_amount = 0
            return_lines_data = []
            
            for i in range(len(product_ids)):
                if not product_ids[i]:
                    continue
                
                product_id = int(product_ids[i])
                quantity = int(quantities[i]) if quantities[i] else 0
                price = float(prices[i]) if prices[i] else 0
                reason = return_reasons[i] if i < len(return_reasons) else ""
                note = line_notes[i] if i < len(line_notes) else ""
                original_line_id = original_line_ids[i] if i < len(original_line_ids) and original_line_ids[i] else None
                
                # Skip products with zero quantity
                if quantity <= 0:
                    continue
                
                # Validate product is returnable
                if product_id not in valid_products:
                    flash(f"Product ID {product_id} is not valid for this order", "error")
                    return redirect(url_for('pos.partial_return'))
                
                # Validate quantity is within returnable limit
                if quantity > valid_products[product_id]['returnable_quantity']:
                    flash(f"Return quantity exceeds available quantity for product ID {product_id}", "error")
                    return redirect(url_for('pos.partial_return'))
                
                # Ensure price is valid - FIXED: Get price directly from original order line
                if price <= 0:
                    # Get price from the original order line
                    for line in original_order.lines:
                        if line.product_id == product_id:
                            price = line.unit_price
                            print(f"Setting price from original order line: {price} for product {product_id}")
                            break
                
                # Calculate subtotal
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
                    'original_line_id': original_line_id
                })
            
            # Create a new return record
            new_return = POSReturn(
                original_order_id=original_order_id,
                customer_name=customer_name,
                customer_phone=customer_phone,
                total_amount=total_amount,
                refund_amount=total_amount,  # Default to same as total
                return_type='partial',  # Always partial for this route
                refund_method=refund_method,
                notes=notes,
                state='draft',
                created_by=current_user.id,
                exchange_processed=False  # Initialize as not processed for exchange
            )
            
            # Generate a unique name for the return
            from datetime import datetime
            timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
            new_return.name = f"RET/PART/{timestamp}"
            
            db.session.add(new_return)
            db.session.flush()  # Get the ID without committing
            
            # Create return lines - FIXED: Ensure price is set correctly
            for line_data in return_lines_data:
                # Get the original order line to ensure we have the correct price
                original_line = None
                for line in original_order.lines:
                    if line.product_id == line_data['product_id']:
                        original_line = line
                        break
                
                # Use the price from the original order line if available
                unit_price = line_data['unit_price']
                if original_line and unit_price <= 0:
                    unit_price = original_line.unit_price
                
                return_line = POSReturnLine(
                    return_id=new_return.id,
                    product_id=line_data['product_id'],
                    return_reason=line_data['return_reason'],
                    quantity=line_data['quantity'],
                    unit_price=unit_price,
                    subtotal=line_data['subtotal'],
                    state='draft'
                )
                
                # Set the original line ID if available
                if 'original_line_id' in line_data and line_data['original_line_id']:
                    return_line.original_order_line_id = line_data['original_line_id']
                elif original_line:
                    return_line.original_order_line_id = original_line.id
                
                # Get product name for resilience
                product = Product.query.get(line_data['product_id'])
                if product:
                    return_line.product_name = product.name
                
                db.session.add(return_line)
            
            # Update the returned_quantity on the original order lines
            for line in original_order.lines:
                for line_data in return_lines_data:
                    if line.product_id == line_data['product_id']:
                        # Add the returned quantity to the line's returned_quantity field
                        line.returned_quantity += line_data['quantity']
            
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
