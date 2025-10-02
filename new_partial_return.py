"""
New implementation of the partial return functionality for the ERP system.
This script creates a new route that correctly handles partial returns.
"""
from flask import Flask, Blueprint, render_template, redirect, url_for, flash, request, jsonify
from flask_login import current_user, login_required
from modules.pos.models import POSOrder, POSOrderLine, POSReturn, POSReturnLine, Product
from extensions import db
from datetime import datetime
import traceback

# Create a blueprint for the new partial return functionality
partial_return_bp = Blueprint('partial_return', __name__, url_prefix='/pos/returns')

@partial_return_bp.route('/partial', methods=['GET', 'POST'])
@login_required
def partial_return():
    """New implementation of the partial return functionality"""
    if request.method == 'POST':
        try:
            # Log all form data for debugging
            print("==== NEW PARTIAL RETURN FORM SUBMISSION DEBUG ====")
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
            
            # Process the special actual_quantity field
            actual_quantity = None
            if "actual_quantity" in request.form:
                try:
                    actual_quantity = int(float(request.form.get("actual_quantity")))
                    print(f"Found special actual_quantity: {actual_quantity}")
                except (ValueError, TypeError):
                    print(f"Invalid actual_quantity: {request.form.get('actual_quantity')}")
            
            # Debug information
            print(f"Received return data: {len(product_ids)} products")
            print(f"Product IDs: {product_ids}")
            print(f"Quantities: {quantities}")
            print(f"Original line IDs: {original_line_ids}")
            
            # Validate the return data
            if not product_ids or not any(pid for pid in product_ids if pid):
                flash("Please add at least one product to return", "error")
                return redirect(url_for('partial_return.partial_return'))
            
            # Calculate total amount and validate quantities
            total_amount = 0
            return_lines_data = []
            
            for i in range(len(product_ids)):
                # Skip empty product IDs
                if not product_ids[i]:
                    continue
                
                try:
                    product_id = int(product_ids[i])
                except (ValueError, TypeError):
                    print(f"Invalid product ID at index {i}: {product_ids[i]}")
                    continue
                
                # Skip products that weren't in the original order or have no returnable quantity
                if product_id not in valid_products:
                    print(f"Product ID {product_id} not in valid products list")
                    continue
                
                # Handle quantity correctly
                quantity = 1  # Default to 1 if invalid
                
                # If this is the first product and we have an actual_quantity, use that
                if i == 0 and actual_quantity is not None:
                    quantity = actual_quantity
                    print(f"Using special actual_quantity for product {product_id}: {quantity}")
                # Otherwise use the standard approach
                elif i < len(quantities):
                    quantity_str = quantities[i]
                    if quantity_str and quantity_str != 'undefined':
                        try:
                            quantity = int(float(quantity_str))
                            quantity = max(1, quantity)  # Ensure minimum quantity is 1
                            print(f"Processing quantity for product {product_id}: {quantity}")
                        except (ValueError, TypeError):
                            print(f"Invalid quantity at index {i}: {quantity_str}, using default of 1")
                
                # Process price with proper validation
                price = 0.0  # Default to 0 if invalid
                if i < len(prices):
                    price_str = prices[i]
                    if price_str and price_str != 'undefined':
                        try:
                            price = float(price_str)
                            print(f"Successfully parsed price from form: {price}")
                        except (ValueError, TypeError):
                            print(f"Invalid price: {price_str}, using default of 0.0")
                    else:
                        print(f"Empty or undefined price at index {i}")
                else:
                    print(f"No price found at index {i}")
                # If price is still 0, try to get it from the original order line
                if price <= 0 and original_line_id:
                    try:
                        original_line = POSOrderLine.query.get(original_line_id)
                        if original_line and original_line.unit_price > 0:
                            price = original_line.unit_price
                            print(f"Using price {price} from original order line {original_line_id}")
                        else:
                            print(f"Original order line {original_line_id} not found or has zero price")
                    except Exception as e:
                        print(f"Error getting price from original order line: {str(e)}")
                # If price is still 0, try to get it from the valid_products dictionary
                if price <= 0 and product_id in valid_products and valid_products[product_id]['lines']:
                    price = valid_products[product_id]['lines'][0]['unit_price']
                    print(f"Using price {price} from valid_products dictionary for product {product_id}")
                
                # If price is still 0, try to get it from the product
                if price <= 0:
                    try:
                        if hasattr(product, 'list_price') and product.list_price > 0:
                            price = product.list_price
                            print(f"Using list_price {price} from product {product_id}")
                        elif hasattr(product, 'standard_price') and product.standard_price > 0:
                            price = product.standard_price
                            print(f"Using standard_price {price} from product {product_id}")
                    except Exception as e:
                        print(f"Error getting price from product: {str(e)}")
                
# Get return reason and note
                return_reason = return_reasons[i] if i < len(return_reasons) else "defective"
                note = line_notes[i] if i < len(line_notes) else ""
                
                # Process original line ID with proper validation
                original_line_id = None
                if i < len(original_line_ids):
                    line_id_str = original_line_ids[i]
                    if line_id_str and line_id_str != 'undefined':
                        try:
                            original_line_id = int(line_id_str)
                        except (ValueError, TypeError):
                            print(f"Invalid original line ID at index {i}: {line_id_str}")
                
                # Verify the product exists
                product = Product.query.get(product_id)
                if not product:
                    print(f"Product with ID {product_id} not found in database")
                    continue
                
                # Cap the quantity to what's returnable
                max_returnable = valid_products[product_id]['returnable_quantity']
                if quantity > max_returnable:
                    print(f"Reducing quantity for product {product_id} from {quantity} to {max_returnable} (max returnable)")
                    quantity = max_returnable
                
                # Skip if no quantity to return
                if quantity <= 0:
                    continue
                
                # Get the first original line ID for this product if not specified
                if not original_line_id and valid_products[product_id]['lines']:
                    original_line_id = valid_products[product_id]['lines'][0]['line_id']
                
                # Get the original order line
                original_line = POSOrderLine.query.get(original_line_id) if original_line_id else None
                if not original_line:
                    print(f"Original order line {original_line_id} not found, skipping")
                    continue
                
                # Calculate subtotal
                line_subtotal = price * quantity
                total_amount += line_subtotal
                
                print(f"Creating return line for product {product_id} with quantity {quantity}, price {price}, subtotal {line_subtotal}")
                
                # Create a single return line with the full quantity
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
                )
                
                # Add detailed logging before saving return line
                print(f"--- Pre-Save Return Line ---")
                print(f"  Product ID: {product_id}")
                print(f"  Quantity: {quantity} (Type: {type(quantity)})")
                print(f"  Unit Price: {price} (Type: {type(price)})")
                print(f"  Subtotal: {line_subtotal} (Type: {type(line_subtotal)})")
                print(f"  Original Line ID: {original_line_id}")
                
                return_lines_data.append(return_line)
            
            # If no valid lines were processed
            if not return_lines_data:
                flash("No valid products or quantities provided for return.", "error")
                return redirect(url_for('partial_return.partial_return'))
                
            print(f"Final calculated total_amount before creating return object: {total_amount}")
            
            # Create the main return record
            new_return = POSReturn(
                original_order_id=original_order_id,
                customer_name=customer_name,
                customer_phone=customer_phone,
                total_amount=total_amount,
                refund_amount=total_amount,
                return_type='partial',  # Ensure this is always partial
                refund_method=refund_method,
                notes=notes,
                state='draft',
                created_by=current_user.id,
                exchange_processed=False  # Initialize as not processed for exchange
            )
            
            # Force return_type to "partial" regardless of what was submitted
            new_return.return_type = "partial"
            
            # Add to session to get an ID
            db.session.add(new_return)
            db.session.flush()
            
            # Generate a unique name for the return
            timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
            new_return.name = f"RET/PART/{timestamp}"
            
            # Add return lines
            for line_data in return_lines_data:
                line_data.return_id = new_return.id
                db.session.add(line_data)
            
            # Update the returned_quantity on the original order lines
            for line_data in return_lines_data:
                product_id = line_data.product_id
                return_quantity = line_data.quantity
                
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
                    
                    print(f"Updated line {original_line.id}: returned {return_from_line} of {original_line.quantity}, new returned_quantity={original_line.returned_quantity}")
                    
                    # Add detailed logging for original line update
                    print(f"--- Updating Original Order Line ---")
                    print(f"  Original Line ID: {original_line.id}")
                    print(f"  Added Quantity: {return_from_line}")
                    print(f"  New Returned Quantity: {original_line.returned_quantity}")
                    
                    db.session.add(original_line) # Ensure the change is staged
            
            db.session.commit()
            
            flash(f"Partial return {new_return.name} created successfully", "success")
            return redirect(url_for('pos.return_detail', return_id=new_return.id))
            
        except ValueError as ve:
            print(f"ValueError during form processing: {str(ve)}")
            flash(str(ve), "error")
            return redirect(url_for('partial_return.partial_return'))
            
        except Exception as e:
            db.session.rollback()
            flash(f"Error creating partial return: {str(e)}")
            traceback.print_exc()
            return redirect(url_for('partial_return.partial_return'))
    
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
    
    print(f"Found {len(returnable_orders)} returnable orders")
    return render_template('pos/partial_return_form.html', orders=returnable_orders)

# Flag to track if the blueprint has been registered
_blueprint_registered = False

def register_blueprint(app):
    """Register the partial return blueprint with the Flask app"""
    global _blueprint_registered
    
    # Check if the blueprint has already been registered
    if _blueprint_registered:
        print("Partial return blueprint already registered, skipping")
        return True
    
    # Register the blueprint
    app.register_blueprint(partial_return_bp)
    
    # Create a redirect from the old URL to the new one
    @app.route('/pos/returns/partial')
    def redirect_to_new_partial_return():
        return redirect(url_for('partial_return.partial_return'))
    
    # Set the flag to indicate the blueprint has been registered
    _blueprint_registered = True
    
    print("New partial return functionality registered successfully")
    return True

@partial_return_bp.route('/api/order_line/<int:line_id>', methods=['GET'])
@login_required
def get_order_line(line_id):
    """API endpoint to get order line details"""
    try:
        # Get the order line
        order_line = POSOrderLine.query.get_or_404(line_id)
        
        # Return the order line details
        return jsonify({
            'success': True,
            'line': {
                'id': order_line.id,
                'product_id': order_line.product_id,
                'quantity': order_line.quantity,
                'unit_price': order_line.unit_price,
                'subtotal': order_line.subtotal,
                'returned_quantity': order_line.returned_quantity
            }
        })
    except Exception as e:
        print(f"Error getting order line details: {str(e)}")
        return jsonify({
            'success': False,
            'message': f"Error getting order line details: {str(e)}"
        })
