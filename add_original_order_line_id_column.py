#!/usr/bin/env python

"""
Migration script to add the original_order_line_id column to the pos_return_lines table
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
        
        if 'original_order_line_id' not in columns:
            print("Adding 'original_order_line_id' column to pos_return_lines table...")
            # Add the original_order_line_id column as nullable
            db.session.execute(text("ALTER TABLE pos_return_lines ADD COLUMN original_order_line_id INTEGER"))
            db.session.commit()
            print("Column 'original_order_line_id' added successfully!")
        else:
            print("Column 'original_order_line_id' already exists in pos_return_lines table.")
            
    except Exception as e:
        print(f"Error adding column: {str(e)}")
        db.session.rollback()
