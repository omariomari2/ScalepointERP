"""
Direct fix for the return quantity and subtotal issue in the ERP system.
This script provides a direct patch to the return functionality without modifying the existing code.
"""
import os
import sys
from flask import Flask, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from functools import wraps
from datetime import datetime

# Create a minimal Flask app
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'sqlite:///erp.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# Monkey patch function to fix return creation
def fixed_create_return(original_create_return):
    @wraps(original_create_return)
    def wrapper(*args, **kwargs):
        if request.method == 'POST':
            try:
                # Log all form data for debugging
                print("==== RETURN FORM SUBMISSION DEBUG ====")
                print("All form data:")
                for key, value in request.form.items():
                    print(f"  {key}: {value}")
                
                # Get product data from form
                product_ids = request.form.getlist('product_id[]')
                quantities = request.form.getlist('quantity[]')
                prices = request.form.getlist('price[]')
                
                # Debug the values
                print("Product IDs:", product_ids)
                print("Quantities:", quantities)
                print("Prices:", prices)
                
                # Call the original function to create the return
                result = original_create_return(*args, **kwargs)
                
                # After the return is created, fix any issues with the return lines
                from modules.pos.models import POSReturn, POSReturnLine
                
                # Get the latest return
                latest_return = POSReturn.query.order_by(POSReturn.id.desc()).first()
                
                if latest_return:
                    print(f"Fixing return {latest_return.name} (ID: {latest_return.id})")
                    
                    # Fix each return line
                    for line in latest_return.return_lines:
                        # Calculate the correct subtotal
                        correct_subtotal = round(line.quantity * line.unit_price, 2)
                        
                        # Check if the subtotal is incorrect
                        if abs(line.subtotal - correct_subtotal) > 0.01 or line.subtotal == 0:
                            print(f"  Fixing line {line.id}: Product {line.product_id}")
                            print(f"    Original: quantity={line.quantity}, unit_price={line.unit_price}, subtotal={line.subtotal}")
                            
                            # Fix the subtotal
                            line.subtotal = correct_subtotal
                            print(f"    Updated: quantity={line.quantity}, unit_price={line.unit_price}, subtotal={line.subtotal}")
                    
                    # Recalculate the total amount for the return
                    total_amount = sum(line.subtotal for line in latest_return.return_lines)
                    
                    # Check if the total amount is incorrect
                    if abs(latest_return.total_amount - total_amount) > 0.01 or latest_return.total_amount == 0:
                        print(f"  Fixing return total: {latest_return.total_amount} -> {total_amount}")
                        latest_return.total_amount = total_amount
                        latest_return.refund_amount = total_amount  # Update refund amount as well
                    
                    # Commit the changes
                    db.session.commit()
                    print("Fixes committed successfully")
                
                return result
            except Exception as e:
                print(f"Error in fixed_create_return: {str(e)}")
                import traceback
                traceback.print_exc()
                return original_create_return(*args, **kwargs)
        else:
            return original_create_return(*args, **kwargs)
    return wrapper

def apply_fix():
    """Apply the fix to the return functionality."""
    try:
        # Import the necessary modules
        from modules.pos.routes import partial_return, new_return
        
        # Monkey patch the return functions
        import modules.pos.routes
        modules.pos.routes.partial_return = fixed_create_return(modules.pos.routes.partial_return)
        modules.pos.routes.new_return = fixed_create_return(modules.pos.routes.new_return)
        
        print("Return functionality patched successfully")
        return True
    except Exception as e:
        print(f"Error applying fix: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

# This function will be called from app.py to apply the fix
def initialize_fix(app):
    with app.app_context():
        return apply_fix()
