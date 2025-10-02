"""
Fix for the data in existing returns to ensure correct values are displayed.
This script should be run within the application context.
"""
from flask import Flask
from app import create_app
from modules.pos.models import POSReturn, POSReturnLine
from extensions import db

def fix_return_data():
    """Fix the data in existing returns to ensure correct values are displayed"""
    try:
        # Get all returns with potential issues
        returns = POSReturn.query.all()
        fixed_count = 0
        
        for return_ in returns:
            for line in return_.return_lines:
                # Check if the line has valid data
                if line.quantity > 0 and line.unit_price <= 0:
                    # Try to get the correct price from the original order line
                    if line.original_order_line and line.original_order_line.unit_price > 0:
                        line.unit_price = line.original_order_line.unit_price
                        line.subtotal = line.quantity * line.unit_price
                        fixed_count += 1
                    # If we can't get the price from the original order line, try to get it from the product
                    elif line.product and hasattr(line.product, 'list_price') and line.product.list_price > 0:
                        line.unit_price = line.product.list_price
                        line.subtotal = line.quantity * line.unit_price
                        fixed_count += 1
                
                # Ensure subtotal is correctly calculated
                if line.subtotal <= 0 and line.quantity > 0 and line.unit_price > 0:
                    line.subtotal = line.quantity * line.unit_price
                    fixed_count += 1
        
        if fixed_count > 0:
            db.session.commit()
            print(f"Fixed {fixed_count} return lines with incorrect data")
        else:
            print("No data issues found in existing returns")
        
        return True
    except Exception as e:
        print(f"Error fixing return data: {str(e)}")
        db.session.rollback()
        return False

if __name__ == "__main__":
    # Create the application context
    app = create_app()
    
    # Run the fix within the application context
    with app.app_context():
        if fix_return_data():
            print("Successfully fixed return data")
        else:
            print("Failed to fix return data")
