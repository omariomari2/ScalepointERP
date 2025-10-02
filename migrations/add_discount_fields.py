"""
Migration script to add discount fields to the database.
This script adds the discount_amount field to the pos_orders and pos_order_lines tables.
"""
import os
import sys
import psycopg2
from psycopg2 import sql

def run_migration(database_url):
    """Run the migration to add discount fields"""
    print("Starting migration to add discount fields...")
    
    try:
        # Connect to the database
        conn = psycopg2.connect(database_url)
        cursor = conn.cursor()
        
        # Check if the column already exists in pos_orders
        cursor.execute("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name='pos_orders' AND column_name='discount_amount';
        """)
        
        if cursor.fetchone() is None:
            print("Adding discount_amount column to pos_orders table...")
            cursor.execute("""
                ALTER TABLE pos_orders 
                ADD COLUMN discount_amount FLOAT DEFAULT 0.0;
            """)
            print("Added discount_amount column to pos_orders table.")
        else:
            print("discount_amount column already exists in pos_orders table.")
        
        # Check if the column already exists in pos_order_lines
        cursor.execute("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name='pos_order_lines' AND column_name='discount_amount';
        """)
        
        if cursor.fetchone() is None:
            print("Adding discount_amount column to pos_order_lines table...")
            cursor.execute("""
                ALTER TABLE pos_order_lines 
                ADD COLUMN discount_amount FLOAT DEFAULT 0.0;
            """)
            print("Added discount_amount column to pos_order_lines table.")
        else:
            print("discount_amount column already exists in pos_order_lines table.")
        
        # Commit the changes
        conn.commit()
        print("Migration completed successfully!")
        
    except Exception as e:
        print(f"Error during migration: {e}")
        conn.rollback() if 'conn' in locals() else None
        return False
    finally:
        if 'conn' in locals():
            cursor.close()
            conn.close()
    
    return True

if __name__ == "__main__":
    # Get database URL from command line or environment
    database_url = sys.argv[1] if len(sys.argv) > 1 else os.environ.get("DATABASE_URL")
    
    if not database_url:
        print("Error: DATABASE_URL not provided. Please provide it as an argument or set it as an environment variable.")
        sys.exit(1)
    
    success = run_migration(database_url)
    sys.exit(0 if success else 1)
