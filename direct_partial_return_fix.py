"""
Direct fix for the partial return functionality in the ERP system.
This script directly modifies the partial_return function in the routes.py file.
"""
import os
import sys
import re
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

def fix_partial_return():
    """Fix the partial_return function in the routes.py file"""
    routes_file = r"c:\Users\USER\erpsystem_working_backup\modules\pos\routes.py"
    
    # Backup the original file
    if not backup_file(routes_file):
        print(f"Error: Could not find {routes_file}")
        return False
    
    # Read the file content
    with open(routes_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Find the start and end of the partial_return function
    pattern = r'@pos\.route\(\'/returns/partial\', methods=\[\'GET\', \'POST\'\]\)\s*@login_required\s*def partial_return\(\):(.*?)(?=\n\S)'
    match = re.search(pattern, content, re.DOTALL)
    
    if not match:
        print("Error: Could not find the partial_return function in the routes.py file")
        return False
    
    # Get the indentation level of the function
    indentation_match = re.search(r'(\s*)def partial_return\(\):', match.group(0))
    if not indentation_match:
        print("Error: Could not determine indentation level")
        return False
    
    indentation = indentation_match.group(1)
    
    # Create the fixed function with the correct indentation
    fixed_function = f"""@pos.route('/returns/partial', methods=['GET', 'POST'])
@login_required
def partial_return():
    \"\"\"Create a new partial return\"\"\"
    if request.method == 'POST':
        try:
            # Log all form data for debugging
            print("==== PARTIAL RETURN FORM SUBMISSION DEBUG ====")
            print("All form data:")
            for key, value in request.form.items():
                print(f"  {{key}}: {{value}}")
            
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
            valid_products = {{}}
            for line in original_order.lines:
                # Use integer returnable_quantity since products are sold as whole pieces
                returnable_quantity = max(0, int(line.quantity - line.returned_quantity))
                if returnable_quantity > 0:
                    if line.product_id not in valid_products:
                        valid_products[line.product_id] = {{
                            'returnable_quantity': returnable_quantity,
                            'lines': []
                        }}
                    else:
                        valid_products[line.product_id]['returnable_quantity'] += returnable_quantity
                        
                    valid_products[line.product_id]['lines'].append({{
                        'line_id': line.id,
                        'returnable_quantity': returnable_quantity,
                        'unit_price': line.unit_price
                    }})
            
            # Get product data from form
            product_ids = request.form.getlist('product_id[]')
            quantities = request.form.getlist('quantity[]')
            prices = request.form.getlist('price[]')
            return_reasons = request.form.getlist('return_reason[]')
            line_notes = request.form.getlist('line_notes[]')
            original_line_ids = request.form.getlist('original_line_id[]')
            
            # Process the special actual_quantity field (only once)
            actual_quantity = None
            if "actual_quantity" in request.form:
                try:
                    actual_quantity = int(float(request.form.get("actual_quantity")))
                    print(f"Found special actual_quantity: {{actual_quantity}}")
                except (ValueError, TypeError):
                    print(f"Invalid actual_quantity: {{request.form.get('actual_quantity')}}")
            
            # Debug information
            print(f"Received return data: {{len(product_ids)}} products")
            print(f"Product IDs: {{product_ids}}")
            print(f"Quantities: {{quantities}}")
            print(f"Original line IDs: {{original_line_ids}}")
            
            # Validate the return data
            if not product_ids or not any(pid for pid in product_ids if pid):
                flash("Please add at least one product to return", "error")
                return redirect(url_for('pos.partial_return'))
            
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
                    print(f"Invalid product ID at index {{i}}: {{product_ids[i]}}")
                    continue
                
                # Skip products that weren't in the original order or have no returnable quantity
                if product_id not in valid_products:
                    print(f"Product ID {{product_id}} not in valid products list")
                    continue
                
                # Handle quantity correctly
                quantity = 1  # Default to 1 if invalid
                
                # If this is the first product and we have an actual_quantity, use that
                if i == 0 and actual_quantity is not None:
                    quantity = actual_quantity
                    print(f"Using special actual_quantity for product {{product_id}}: {{quantity}}")
                # Otherwise use the standard approach
                elif i < len(quantities):
                    quantity_str = quantities[i]
                    if quantity_str and quantity_str != 'undefined':
                        try:
                            quantity = int(float(quantity_str))
                            quantity = max(1, quantity)  # Ensure minimum quantity is 1
                            print(f"Processing quantity for product {{product_id}}: {{quantity}}")
                        except (ValueError, TypeError):
                            print(f"Invalid quantity at index {{i}}: {{quantity_str}}, using default of 1")
                
                # Process price with proper validation
                price = 0.0  # Default to 0 if invalid
                if i < len(prices):
                    price_str = prices[i]
                    if price_str and price_str != 'undefined':
                        try:
                            price = float(price_str)
                        except (ValueError, TypeError):
                            print(f"Invalid price: {{price_str}}, using default of 0.0")
                
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
                            print(f"Invalid original line ID at index {{i}}: {{line_id_str}}")
                
                # Verify the product exists
                product = Product.query.get(product_id)
                if not product:
                    print(f"Product with ID {{product_id}} not found in database")
                    continue
                
                # Cap the quantity to what's returnable
                max_returnable = valid_products[product_id]['returnable_quantity']
                if quantity > max_returnable:
                    print(f"Reducing quantity for product {{product_id}} from {{quantity}} to {{max_returnable}} (max returnable)")
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
                    print(f"Original order line {{original_line_id}} not found, skipping")
                    continue
                
                # Calculate subtotal
                line_subtotal = price * quantity
                total_amount += line_subtotal
                
                print(f"Creating return line for product {{product_id}} with quantity {{quantity}}")
                
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
                print(f"  Product ID: {{product_id}}")
                print(f"  Quantity: {{quantity}} (Type: {{type(quantity)}})")
                print(f"  Unit Price: {{price}} (Type: {{type(price)}})")
                print(f"  Subtotal: {{line_subtotal}} (Type: {{type(line_subtotal)}})")
                print(f"  Original Line ID: {{original_line_id}}")
                
                return_lines_data.append(return_line)
            
            # If no valid lines were processed
            if not return_lines_data:
                flash("No valid products or quantities provided for return.", "error")
                return redirect(url_for('pos.partial_return'))
                
            print(f"Final calculated total_amount before creating return object: {{total_amount}}")
            
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
            from datetime import datetime
            timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
            new_return.name = f"RET/PART/{{timestamp}}"
            
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
                    
                    print(f"Updated line {{original_line.id}}: returned {{return_from_line}} of {{original_line.quantity}}, new returned_quantity={{original_line.returned_quantity}}")
                    
                    # Add detailed logging for original line update
                    print(f"--- Updating Original Order Line ---")
                    print(f"  Original Line ID: {{original_line.id}}")
                    print(f"  Added Quantity: {{return_from_line}}")
                    print(f"  New Returned Quantity: {{original_line.returned_quantity}}")
                    
                    db.session.add(original_line) # Ensure the change is staged
            
            db.session.commit()
            
            flash(f"Partial return {{new_return.name}} created successfully", "success")
            return redirect(url_for('pos.return_detail', return_id=new_return.id))
            
        except ValueError as ve:
            print(f"ValueError during form processing: {{str(ve)}}")
            flash(str(ve), "error")
            return redirect(url_for('pos.partial_return'))
            
        except Exception as e:
            db.session.rollback()
            flash(f"Error creating partial return: {{str(e)}}", "error")
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
    
    print(f"Found {{len(returnable_orders)}} returnable orders")
    print(f"--- Loading Partial Return Form: Found {{len(returnable_orders)}} returnable orders ---")
    return render_template('pos/partial_return_form.html', orders=returnable_orders)"""
    
    # Replace the function in the file content
    new_content = re.sub(pattern, fixed_function, content, flags=re.DOTALL)
    
    # Write the modified content back to the file
    with open(routes_file, 'w', encoding='utf-8') as f:
        f.write(new_content)
    
    print("Successfully replaced the partial_return function in the routes.py file")
    return True

def fix_app_py():
    """Remove all existing fixes from app.py"""
    app_file = r"c:\Users\USER\erpsystem_working_backup\app.py"
    
    # Backup the original file
    if not backup_file(app_file):
        print(f"Error: Could not find {app_file}")
        return False
    
    # Read the file content
    with open(app_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Find the start and end of the fix code
    pattern = r'if __name__ == \'__main__\':\s*app = create_app\(os\.getenv\(\'FLASK_CONFIG\'\) or \'default\'\)(.*?)app\.run\(debug=True\)'
    match = re.search(pattern, content, re.DOTALL)
    
    if not match:
        print("Error: Could not find the fix code in app.py")
        return False
    
    # Replace the fix code with a clean version
    clean_code = """
if __name__ == '__main__':
    app = create_app(os.getenv('FLASK_CONFIG') or 'default')
    
    # Run the application
    app.run(debug=True)"""
    
    new_content = content.replace(match.group(0), clean_code)
    
    # Write the modified content back to the file
    with open(app_file, 'w', encoding='utf-8') as f:
        f.write(new_content)
    
    print("Successfully removed all existing fixes from app.py")
    return True

def main():
    """Apply all fixes"""
    print("Starting direct partial return fix...")
    
    # Fix the partial_return function
    if fix_partial_return():
        print("Partial return function fixed successfully")
    else:
        print("Failed to fix partial return function")
        return False
    
    # Fix app.py
    if fix_app_py():
        print("app.py fixed successfully")
    else:
        print("Failed to fix app.py")
        return False
    
    print("\nAll fixes applied successfully!")
    print("Please restart your application for the changes to take effect.")
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
