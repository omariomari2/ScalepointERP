#!/usr/bin/env python

"""
Migration script to add the quantity column to the quality_checks table
"""

from app import create_app
from extensions import db
from sqlalchemy import text

# Create the app
app = create_app()

# Set up the application context
with app.app_context():
    try:
        # Check if the column already exists
        print("Checking quality_checks table...")
        result = db.session.execute(text("PRAGMA table_info(quality_checks)"))
        columns = {row[1]: row for row in result.fetchall()}
        
        if 'quantity' not in columns:
            print("Adding 'quantity' column to quality_checks table...")
            db.session.execute(text("ALTER TABLE quality_checks ADD COLUMN quantity INTEGER DEFAULT 0"))
            db.session.commit()
            print("Column 'quantity' added successfully!")
            
            # Update existing quality checks to use the full return line quantity
            print("Updating existing quality checks to use return line quantities...")
            db.session.execute(text("""
                UPDATE quality_checks
                SET quantity = (
                    SELECT quantity FROM pos_return_lines 
                    WHERE pos_return_lines.id = quality_checks.return_line_id
                )
                WHERE return_line_id IS NOT NULL
            """))
            db.session.commit()
            print("Existing quality checks updated successfully!")
        else:
            print("Column 'quantity' already exists in quality_checks table.")
            
        print("\nQuality checks table update completed successfully!")
            
    except Exception as e:
        print(f"Error updating quality_checks table: {str(e)}")
        db.session.rollback()
