#!/usr/bin/env python

"""
Migration script to add the quantity column to the quality_checks table
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
        result = db.session.execute(text("PRAGMA table_info(quality_checks)"))
        columns = [row[1] for row in result.fetchall()]
        
        if 'quantity' not in columns:
            print("Adding 'quantity' column to quality_checks table...")
            # Add the quantity column with default value of 0
            db.session.execute(text("ALTER TABLE quality_checks ADD COLUMN quantity INTEGER DEFAULT 0"))
            db.session.commit()
            print("Column 'quantity' added successfully!")
        else:
            print("Column 'quantity' already exists in quality_checks table.")
            
    except Exception as e:
        print(f"Error adding column: {str(e)}")
        db.session.rollback()
