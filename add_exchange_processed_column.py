#!/usr/bin/env python

"""
Migration script to add the exchange_processed column to the pos_returns table
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
        result = db.session.execute(text("PRAGMA table_info(pos_returns)"))
        columns = [row[1] for row in result.fetchall()]
        
        if 'exchange_processed' not in columns:
            print("Adding 'exchange_processed' column to pos_returns table...")
            # Add the exchange_processed column with default value of 0 (False)
            db.session.execute(text("ALTER TABLE pos_returns ADD COLUMN exchange_processed BOOLEAN DEFAULT 0"))
            db.session.commit()
            print("Column 'exchange_processed' added successfully!")
        else:
            print("Column 'exchange_processed' already exists in pos_returns table.")
            
    except Exception as e:
        print(f"Error adding column: {str(e)}")
        db.session.rollback()
