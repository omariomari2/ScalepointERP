#!/usr/bin/env python

"""
Migration script to add the product_name column to the pos_return_lines table
"""

import os
import sys

# Add the current directory to the path so we can import the app
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Import the app and models
from app import create_app
from extensions import db
from sqlalchemy import text

# Create the app
app = create_app()

# Set up the application context
with app.app_context():
    try:
        # Check if the column already exists
        result = db.session.execute(text("PRAGMA table_info(pos_return_lines)"))
        columns = [row[1] for row in result.fetchall()]
        
        if 'product_name' not in columns:
            print("Adding 'product_name' column to pos_return_lines table...")
            # Add the product_name column
            db.session.execute(text("ALTER TABLE pos_return_lines ADD COLUMN product_name TEXT"))
            db.session.commit()
            print("Column 'product_name' added successfully!")
        else:
            print("Column 'product_name' already exists in pos_return_lines table.")
            
    except Exception as e:
        print(f"Error adding column: {str(e)}")
        db.session.rollback()
