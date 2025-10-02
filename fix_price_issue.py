"""
Fix for the price issue in the partial return functionality.
This script ensures that the correct price is used when creating return lines.
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

def fix_new_partial_return():
    """Fix the price handling in new_partial_return.py"""
    file_path = r"c:\Users\USER\erpsystem_working_backup\new_partial_return.py"
    
    if not backup_file(file_path):
        return False
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Find the section where the price is processed
        price_section_start = content.find("# Process price with proper validation")
        if price_section_start == -1:
            print("Could not find price processing section")
            return False
        
        # Find the end of the price processing section
        price_section_end = content.find("# Get return reason and note", price_section_start)
        if price_section_end == -1:
            print("Could not find end of price processing section")
            return False
        
        # Get the current price processing code
        current_price_code = content[price_section_start:price_section_end]
        
        # Create the updated price processing code
        updated_price_code = """# Process price with proper validation
                price = 0.0  # Default to 0 if invalid
                if i < len(prices):
                    price_str = prices[i]
                    if price_str and price_str != 'undefined':
                        try:
                            price = float(price_str)
                        except (ValueError, TypeError):
                            print(f"Invalid price: {price_str}, using default of 0.0")
                
                # If price is still 0, try to get it from the original order line
                if price <= 0 and original_line_id:
                    original_line = POSOrderLine.query.get(original_line_id)
                    if original_line:
                        price = original_line.unit_price
                        print(f"Using price {price} from original order line {original_line_id}")
                
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
                
"""
        
        # Replace the price processing code
        updated_content = content.replace(current_price_code, updated_price_code)
        
        # Update the line that logs the return line creation
        if "print(f\"Creating return line for product {product_id} with quantity {quantity}\")" in updated_content:
            updated_content = updated_content.replace(
                "print(f\"Creating return line for product {product_id} with quantity {quantity}\")",
                "print(f\"Creating return line for product {product_id} with quantity {quantity}, price {price}, subtotal {line_subtotal}\")"
            )
        
        # Write the updated content back to the file
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(updated_content)
        
        print("Successfully updated new_partial_return.py")
        return True
    except Exception as e:
        print(f"Error fixing new_partial_return.py: {str(e)}")
        return False

def fix_return_detail_template():
    """Fix the return_detail.html template to correctly display values"""
    template_path = r"c:\Users\USER\erpsystem_working_backup\templates\pos\return_detail.html"
    
    if not backup_file(template_path):
        return False
    
    try:
        with open(template_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Find the table row that displays the return line values
        table_row_start = content.find("<tbody>")
        if table_row_start == -1:
            print("Could not find table body in template")
            return False
        
        table_row_end = content.find("</tbody>", table_row_start)
        if table_row_end == -1:
            print("Could not find end of table body in template")
            return False
        
        # Get the table body content
        table_body = content[table_row_start:table_row_end + 8]
        
        # Check if the template already uses the correct format
        if "{{ line.quantity }}" in table_body and "{{ line.unit_price }}" in table_body:
            # Update the template to use the correct format
            updated_table_body = table_body.replace(
                "{{ line.quantity }}",
                "{{ '%.1f'|format(line.quantity|float) }}"
            )
            
            updated_table_body = updated_table_body.replace(
                "{{ line.unit_price }}",
                "{{ '%.2f'|format(line.unit_price|float) }}"
            )
            
            # Check if the subtotal is calculated or displayed directly
            if "{{ line.quantity * line.unit_price }}" in updated_table_body:
                updated_table_body = updated_table_body.replace(
                    "{{ line.quantity * line.unit_price }}",
                    "{{ '%.2f'|format(line.subtotal|float) }}"
                )
            elif "{{ line.subtotal }}" in updated_table_body:
                updated_table_body = updated_table_body.replace(
                    "{{ line.subtotal }}",
                    "{{ '%.2f'|format(line.subtotal|float) }}"
                )
            
            # Replace the table body in the content
            updated_content = content.replace(table_body, updated_table_body)
            
            # Write the updated content back to the file
            with open(template_path, 'w', encoding='utf-8') as f:
                f.write(updated_content)
            
            print("Successfully updated return_detail.html template")
        else:
            print("Template does not use the expected format, manual inspection required")
        
        return True
    except Exception as e:
        print(f"Error fixing return_detail.html template: {str(e)}")
        return False

def create_fix_existing_returns_script():
    """Create a script to fix existing returns in the database"""
    script_path = r"c:\Users\USER\erpsystem_working_backup\fix_existing_returns.py"
    
    try:
        script_content = """\"\"\"
Fix existing returns in the database to ensure correct prices and subtotals.
\"\"\"
from flask import Flask
from app import create_app
from modules.pos.models import POSReturn, POSReturnLine, POSOrderLine
from extensions import db

def fix_existing_returns():
    \"\"\"Fix existing returns in the database\"\"\"
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
                
                # If unit price is still 0, try to get it from the product
                if (line.unit_price is None or line.unit_price <= 0) and line.product:
                    if hasattr(line.product, 'list_price') and line.product.list_price > 0:
                        line.unit_price = float(line.product.list_price)
                        needs_update = True
                        print(f"Updated line {line.id} unit price to {line.unit_price} from product list price")
                    elif hasattr(line.product, 'standard_price') and line.product.standard_price > 0:
                        line.unit_price = float(line.product.standard_price)
                        needs_update = True
                        print(f"Updated line {line.id} unit price to {line.unit_price} from product standard price")
            
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
        print(f"Error fixing existing returns: {str(e)}")
        db.session.rollback()
        import traceback
        traceback.print_exc()
        return False

if __name__ == \"__main__\":
    # Create the application context
    app = create_app()
    
    # Run the fix within the application context
    with app.app_context():
        if fix_existing_returns():
            print("Successfully fixed existing returns")
        else:
            print("Failed to fix existing returns")
"""
        
        with open(script_path, 'w', encoding='utf-8') as f:
            f.write(script_content)
        
        print(f"Successfully created {script_path}")
        return True
    except Exception as e:
        print(f"Error creating fix_existing_returns.py: {str(e)}")
        return False

def main():
    """Apply all fixes"""
    print("Starting fix for price issue in partial return functionality...")
    
    # Fix the new_partial_return.py file
    if not fix_new_partial_return():
        print("Failed to fix new_partial_return.py")
        return False
    
    # Fix the return_detail.html template
    if not fix_return_detail_template():
        print("Failed to fix return_detail.html template")
        return False
    
    # Create the script to fix existing returns
    if not create_fix_existing_returns_script():
        print("Failed to create fix_existing_returns.py")
        return False
    
    print("\nAll fixes applied successfully!")
    print("Next steps:")
    print("1. Run 'python fix_existing_returns.py' to fix existing returns")
    print("2. Restart your application for the changes to take effect")
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
