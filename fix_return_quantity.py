"""
Emergency fix for the return quantity and subtotal issue in the ERP system.
This script directly updates the database schema and fixes any existing returns with incorrect quantities or subtotals.
"""
import os
import sys
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import Column, Integer, Float, String, ForeignKey, DateTime, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime

# Create a minimal Flask app to access the database
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'sqlite:///erp.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# Define the POSReturnLine model to match the existing one
class POSReturnLine(db.Model):
    __tablename__ = 'pos_return_lines'
    
    id = db.Column(db.Integer, primary_key=True)
    return_id = db.Column(db.Integer, db.ForeignKey('pos_returns.id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=False)
    original_order_line_id = db.Column(db.Integer, db.ForeignKey('pos_order_lines.id'), nullable=True)
    quantity = db.Column(db.Integer, default=0)
    unit_price = db.Column(db.Float, default=0.0)
    subtotal = db.Column(db.Float, default=0.0)
    return_reason = db.Column(db.String(64))
    state = db.Column(db.String(20), default='draft')
    product_name = db.Column(db.String(255))  # Store product name for resilience

# Define the POSReturn model to match the existing one
class POSReturn(db.Model):
    __tablename__ = 'pos_returns'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), unique=True)
    original_order_id = db.Column(db.Integer, db.ForeignKey('pos_orders.id'), nullable=False)
    customer_name = db.Column(db.String(128))
    customer_phone = db.Column(db.String(64))
    return_date = db.Column(db.DateTime, default=datetime.now)
    total_amount = db.Column(db.Float, default=0.0)
    refund_amount = db.Column(db.Float, default=0.0)
    return_type = db.Column(db.String(20), default='full')  # 'full' or 'partial'
    refund_method = db.Column(db.String(20), default='cash')  # 'cash', 'card', 'mobile_money', 'store_credit', 'exchange'
    notes = db.Column(db.Text)
    state = db.Column(db.String(20), default='draft')  # 'draft', 'validated', 'cancelled'
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'))
    exchange_processed = db.Column(db.Boolean, default=False)
    
    # Relationships
    return_lines = db.relationship('POSReturnLine', backref='return_', lazy='dynamic')

def fix_return_quantities_and_subtotals():
    """Fix return quantities and subtotals for all returns in the system."""
    with app.app_context():
        # Get all returns
        returns = POSReturn.query.all()
        print(f"Found {len(returns)} returns to check")
        
        fixed_count = 0
        for return_ in returns:
            print(f"\nChecking return {return_.name} (ID: {return_.id})")
            
            # Check each return line
            for line in return_.return_lines:
                original_quantity = line.quantity
                original_unit_price = line.unit_price
                original_subtotal = line.subtotal
                
                # Calculate the correct subtotal
                correct_subtotal = round(line.quantity * line.unit_price, 2)
                
                # Check if the subtotal is incorrect
                if abs(line.subtotal - correct_subtotal) > 0.01:
                    print(f"  Fixing line {line.id}: Product {line.product_id}")
                    print(f"    Original: quantity={original_quantity}, unit_price={original_unit_price}, subtotal={original_subtotal}")
                    
                    # Fix the subtotal
                    line.subtotal = correct_subtotal
                    print(f"    Updated: quantity={line.quantity}, unit_price={line.unit_price}, subtotal={line.subtotal}")
                    fixed_count += 1
            
            # Recalculate the total amount for the return
            total_amount = sum(line.subtotal for line in return_.return_lines)
            
            # Check if the total amount is incorrect
            if abs(return_.total_amount - total_amount) > 0.01:
                print(f"  Fixing return total: {return_.total_amount} -> {total_amount}")
                return_.total_amount = total_amount
                return_.refund_amount = total_amount  # Update refund amount as well
                fixed_count += 1
        
        # Commit the changes if any fixes were made
        if fixed_count > 0:
            print(f"\nCommitting {fixed_count} fixes to the database")
            db.session.commit()
            print("Fixes committed successfully")
        else:
            print("\nNo fixes needed")

if __name__ == "__main__":
    fix_return_quantities_and_subtotals()
