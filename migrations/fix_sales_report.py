"""
Migration script to fix sales report issues in production.
This script:
1. Adds the discount_amount field to the pos_orders and pos_order_lines tables if missing
2. Makes the discount_amount field nullable with a default of 0
3. Updates any NULL values to 0 to prevent errors
"""
import os
import sys
import psycopg2
from psycopg2 import sql

def run_migration(database_url):
    """Run the migration to fix sales report issues"""
    print("Starting migration to fix sales report issues...")
    
    try:
        # Connect to the database
        conn = psycopg2.connect(database_url)
        cursor = conn.cursor()
        
        # 1. Check if the column exists in pos_orders
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
            
            # Make sure the column is not nullable and has a default value
            cursor.execute("""
                ALTER TABLE pos_orders 
                ALTER COLUMN discount_amount SET DEFAULT 0.0,
                ALTER COLUMN discount_amount SET NOT NULL;
            """)
            print("Updated discount_amount column in pos_orders table.")
        
        # 2. Check if the column exists in pos_order_lines
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
            
            # Make sure the column is not nullable and has a default value
            cursor.execute("""
                ALTER TABLE pos_order_lines 
                ALTER COLUMN discount_amount SET DEFAULT 0.0,
                ALTER COLUMN discount_amount SET NOT NULL;
            """)
            print("Updated discount_amount column in pos_order_lines table.")
        
        # 3. Update any NULL values to 0
        cursor.execute("""
            UPDATE pos_orders 
            SET discount_amount = 0.0 
            WHERE discount_amount IS NULL;
        """)
        
        cursor.execute("""
            UPDATE pos_order_lines 
            SET discount_amount = 0.0 
            WHERE discount_amount IS NULL;
        """)
        print("Updated NULL discount values to 0.")
        
        # Commit the changes
        conn.commit()
        print("Migration completed successfully!")
        
    except Exception as e:
        print(f"Error during migration: {e}")
        if 'conn' in locals():
            conn.rollback()
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
