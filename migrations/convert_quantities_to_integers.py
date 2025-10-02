"""
Migration script to convert quantity fields from FLOAT to INTEGER in the POS system.
This ensures that all quantities are stored as whole numbers throughout the system.
"""
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
import os
import sys
import sqlite3

# Add the parent directory to sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import Config
from extensions import db
from modules.pos.models import POSOrderLine, POSReturnLine, QualityCheck

def run_migration():
    """Run the migration to convert quantity fields from FLOAT to INTEGER"""
    print("Starting migration: Converting quantity fields from FLOAT to INTEGER")
    
    try:
        # Create connection to SQLite database
        db_path = Config.SQLALCHEMY_DATABASE_URI.replace('sqlite:///', '')
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # 1. Update pos_order_lines table
        print("Updating pos_order_lines table...")
        
        # Check if the table exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='pos_order_lines'")
        if not cursor.fetchone():
            print("Table pos_order_lines does not exist, skipping")
        else:
            # Round all existing quantities to integers
            cursor.execute("UPDATE pos_order_lines SET quantity = ROUND(quantity)")
            print(f"Updated {cursor.rowcount} rows in pos_order_lines.quantity to whole numbers")
            
            # Round all existing returned quantities to integers
            cursor.execute("UPDATE pos_order_lines SET returned_quantity = ROUND(returned_quantity)")
            print(f"Updated {cursor.rowcount} rows in pos_order_lines.returned_quantity to whole numbers")
        
        # 2. Update pos_return_lines table
        print("Updating pos_return_lines table...")
        
        # Check if the table exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='pos_return_lines'")
        if not cursor.fetchone():
            print("Table pos_return_lines does not exist, skipping")
        else:
            # Round all existing quantities to integers
            cursor.execute("UPDATE pos_return_lines SET quantity = ROUND(quantity)")
            print(f"Updated {cursor.rowcount} rows in pos_return_lines.quantity to whole numbers")
        
        # 3. Update quality_checks table
        print("Updating quality_checks table...")
        
        # Check if the table exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='quality_checks'")
        if not cursor.fetchone():
            print("Table quality_checks does not exist, skipping")
        else:
            # Round all existing quantities to integers
            cursor.execute("UPDATE quality_checks SET quantity = ROUND(quantity)")
            print(f"Updated {cursor.rowcount} rows in quality_checks.quantity to whole numbers")
        
        # Commit the changes
        conn.commit()
        print("Migration completed successfully!")
        
        # Note: SQLite doesn't support ALTER COLUMN TYPE, so we can't change the column type directly.
        # The model changes will take effect when the application creates new records.
        print("Note: SQLite doesn't support changing column types. The model changes will take effect for new records.")
        print("Existing data has been rounded to whole numbers to match the INTEGER model fields.")
        
    except Exception as e:
        print(f"Error during migration: {str(e)}")
        if 'conn' in locals():
            conn.rollback()
        raise
    finally:
        if 'conn' in locals():
            conn.close()

if __name__ == "__main__":
    run_migration()
