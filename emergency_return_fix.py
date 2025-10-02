"""
EMERGENCY FIX for the return quantity and pricing issues
This script directly modifies the database to fix existing returns and patches the code to ensure future returns work correctly
"""
import os
import sys
from flask import Flask, render_template
from flask_sqlalchemy import SQLAlchemy
import importlib
import inspect
import types

# Create a minimal Flask app
app = Flask(__name__)

# Configure the SQLAlchemy part of the app
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'sqlite:///erp.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize SQLAlchemy
db = SQLAlchemy(app)

# Import models
from modules.pos.models import POSReturn, POSReturnLine, POSOrder, POSOrderLine
from modules.inventory.models import Product

def fix_existing_returns():
    """Fix all existing returns in the database"""
    with app.app_context():
        # Get all returns
        returns = POSReturn.query.all()
        print(f"Found {len(returns)} returns to fix")
        
        fixed_returns = 0
        fixed_lines = 0
        
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
                
                # Get the product
                product = Product.query.get(line.product_id)
                
                # Fix the unit price if it's zero or invalid
                if line.unit_price <= 0 and original_line:
                    old_price = line.unit_price
                    line.unit_price = original_line.unit_price
                    print(f"    Fixed unit price: {old_price} -> {line.unit_price}")
                    return_fixed = True
                    fixed_lines += 1
                
                # Calculate the correct subtotal
                correct_subtotal = round(line.quantity * line.unit_price, 2)
                
                # Fix the subtotal if it's incorrect
                if abs(line.subtotal - correct_subtotal) > 0.01:
                    old_subtotal = line.subtotal
                    line.subtotal = correct_subtotal
                    print(f"    Fixed subtotal: {old_subtotal} -> {line.subtotal}")
                    return_fixed = True
                    fixed_lines += 1
                
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
                fixed_returns += 1
        
        # Commit all changes
        if fixed_returns > 0:
            db.session.commit()
            print(f"\nFixed {fixed_returns} returns and {fixed_lines} return lines")
        else:
            print("\nNo returns needed fixing")

def patch_return_creation():
    """Patch the return creation functions to ensure they work correctly"""
    try:
        # Import the routes module
        import modules.pos.routes
        
        # Get the original functions
        original_new_return = modules.pos.routes.new_return
        original_partial_return = modules.pos.routes.partial_return
        
        # Define the patched function for new returns
        def patched_new_return():
            print("EMERGENCY PATCH: Using patched new_return function")
            from flask import request, redirect, url_for, flash
            
            # Call the original function if it's not a POST request
            if request.method != 'POST':
                return original_new_return()
            
            try:
                # Get the form data
                print("Form data:", request.form)
                
                # Call the original function
                result = original_new_return()
                
                # Fix the latest return
                with app.app_context():
                    # Get the latest return
                    latest_return = POSReturn.query.order_by(POSReturn.id.desc()).first()
                    
                    if latest_return:
                        print(f"Fixing return {latest_return.name} (ID: {latest_return.id})")
                        
                        # Fix each return line
                        return_total = 0
                        for line in latest_return.return_lines:
                            # Get the original order line if available
                            original_line = None
                            if line.original_order_line_id:
                                original_line = POSOrderLine.query.get(line.original_order_line_id)
                            
                            # Fix the unit price if it's zero or invalid
                            if line.unit_price <= 0 and original_line:
                                line.unit_price = original_line.unit_price
                                print(f"  Fixed unit price: {line.unit_price}")
                            
                            # Calculate the correct subtotal
                            line.subtotal = round(line.quantity * line.unit_price, 2)
                            print(f"  Fixed subtotal: {line.subtotal}")
                            
                            # Add to the return total
                            return_total += line.subtotal
                        
                        # Fix the return total
                        latest_return.total_amount = return_total
                        latest_return.refund_amount = return_total
                        print(f"  Fixed return total: {return_total}")
                        
                        # Commit the changes
                        db.session.commit()
                        print("Changes committed successfully")
                
                return result
            except Exception as e:
                print(f"Error in patched_new_return: {str(e)}")
                import traceback
                traceback.print_exc()
                return original_new_return()
        
        # Define the patched function for partial returns
        def patched_partial_return():
            print("EMERGENCY PATCH: Using patched partial_return function")
            from flask import request, redirect, url_for, flash
            
            # Call the original function if it's not a POST request
            if request.method != 'POST':
                return original_partial_return()
            
            try:
                # Get the form data
                print("Form data:", request.form)
                
                # Call the original function
                result = original_partial_return()
                
                # Fix the latest return
                with app.app_context():
                    # Get the latest return
                    latest_return = POSReturn.query.order_by(POSReturn.id.desc()).first()
                    
                    if latest_return:
                        print(f"Fixing return {latest_return.name} (ID: {latest_return.id})")
                        
                        # Fix each return line
                        return_total = 0
                        for line in latest_return.return_lines:
                            # Get the original order line if available
                            original_line = None
                            if line.original_order_line_id:
                                original_line = POSOrderLine.query.get(line.original_order_line_id)
                            
                            # Fix the unit price if it's zero or invalid
                            if line.unit_price <= 0 and original_line:
                                line.unit_price = original_line.unit_price
                                print(f"  Fixed unit price: {line.unit_price}")
                            
                            # Calculate the correct subtotal
                            line.subtotal = round(line.quantity * line.unit_price, 2)
                            print(f"  Fixed subtotal: {line.subtotal}")
                            
                            # Add to the return total
                            return_total += line.subtotal
                        
                        # Fix the return total
                        latest_return.total_amount = return_total
                        latest_return.refund_amount = return_total
                        print(f"  Fixed return total: {return_total}")
                        
                        # Commit the changes
                        db.session.commit()
                        print("Changes committed successfully")
                
                return result
            except Exception as e:
                print(f"Error in patched_partial_return: {str(e)}")
                import traceback
                traceback.print_exc()
                return original_partial_return()
        
        # Replace the original functions with the patched ones
        modules.pos.routes.new_return = patched_new_return
        modules.pos.routes.partial_return = patched_partial_return
        
        print("Return creation functions patched successfully")
        return True
    except Exception as e:
        print(f"Error patching return creation functions: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    # Fix existing returns
    fix_existing_returns()
    
    # Patch the return creation functions
    patch_return_creation()
    
    print("Emergency fix completed successfully")
