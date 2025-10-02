"""
Fix existing returns in the database to ensure correct prices and subtotals.
"""
from flask import Flask
from app import create_app
from modules.pos.models import POSReturn, POSReturnLine, POSOrderLine
from extensions import db

def fix_existing_returns():
    """Fix existing returns in the database"""
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

if __name__ == "__main__":
    # Create the application context
    app = create_app()
    
    # Run the fix within the application context
    with app.app_context():
        if fix_existing_returns():
            print("Successfully fixed existing returns")
        else:
            print("Failed to fix existing returns")
