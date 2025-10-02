#!/usr/bin/env python

"""
Migration script to fix the pos_returns and pos_return_lines tables
by adding missing columns and ensuring database schema matches the models
"""

import os
import sys
from app import create_app
from extensions import db
from sqlalchemy import text

# Create the app
app = create_app()

# Set up the application context
with app.app_context():
    try:
        # Check pos_returns table
        print("Checking pos_returns table...")
        result = db.session.execute(text("PRAGMA table_info(pos_returns)"))
        columns = {row[1]: row for row in result.fetchall()}
        
        if 'exchange_processed' not in columns:
            print("Adding 'exchange_processed' column to pos_returns table...")
            db.session.execute(text("ALTER TABLE pos_returns ADD COLUMN exchange_processed BOOLEAN DEFAULT 0"))
            db.session.commit()
            print("Column 'exchange_processed' added successfully!")
        else:
            print("Column 'exchange_processed' already exists in pos_returns table.")
        
        # Check pos_return_lines table
        print("\nChecking pos_return_lines table...")
        result = db.session.execute(text("PRAGMA table_info(pos_return_lines)"))
        columns = {row[1]: row for row in result.fetchall()}
        
        if 'original_order_line_id' not in columns:
            print("Adding 'original_order_line_id' column to pos_return_lines table...")
            db.session.execute(text("ALTER TABLE pos_return_lines ADD COLUMN original_order_line_id INTEGER"))
            db.session.commit()
            print("Column 'original_order_line_id' added successfully!")
        else:
            print("Column 'original_order_line_id' already exists in pos_return_lines table.")
        
        if 'product_name' not in columns:
            print("Adding 'product_name' column to pos_return_lines table...")
            db.session.execute(text("ALTER TABLE pos_return_lines ADD COLUMN product_name VARCHAR(255)"))
            db.session.commit()
            print("Column 'product_name' added successfully!")
            
            # Update product names for existing return lines
            print("Updating product names for existing return lines...")
            db.session.execute(text("""
                UPDATE pos_return_lines
                SET product_name = (
                    SELECT name FROM products 
                    WHERE products.id = pos_return_lines.product_id
                )
                WHERE product_id IS NOT NULL
            """))
            db.session.commit()
            
            # Update any remaining lines without product names
            db.session.execute(text("""
                UPDATE pos_return_lines 
                SET product_name = 'Unknown Product (ID: ' || product_id || ')'
                WHERE product_name IS NULL
            """))
            db.session.commit()
            print("Product names updated successfully!")
        else:
            print("Column 'product_name' already exists in pos_return_lines table.")
            
        print("\nDatabase schema update completed successfully!")
            
    except Exception as e:
        print(f"Error updating database schema: {str(e)}")
        db.session.rollback()
