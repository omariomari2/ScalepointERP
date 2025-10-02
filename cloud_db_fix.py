import os
import sys
import psycopg2
from psycopg2 import sql

def fix_cloud_database():
    """Add missing discount_amount column to pos_order_lines table if it doesn't exist"""
    
    # Get database connection info from environment variables
    db_user = os.environ.get('DB_USER', 'erpuser')
    db_pass = os.environ.get('DB_PASS', 'ERPuser2025!')
    db_name = os.environ.get('DB_NAME', 'erpsystem')
    db_host = os.environ.get('DB_HOST', '/cloudsql/erp-system-445701:us-central1:erp-database')
    
    # For local testing with direct connection
    db_direct_host = os.environ.get('DB_DIRECT_HOST', '')
    db_port = os.environ.get('DB_PORT', '5432')
    
    try:
        # Connect to the database - if unix socket is provided, use it
        if db_direct_host:
            # Connect via TCP/IP for local testing
            print(f"Connecting to database {db_name} on {db_direct_host}:{db_port}")
            conn = psycopg2.connect(
                dbname=db_name,
                user=db_user,
                password=db_pass,
                host=db_direct_host,
                port=db_port
            )
        else:
            # Connect via Unix socket for Cloud SQL
            print(f"Connecting to database {db_name} via Unix socket {db_host}")
            conn = psycopg2.connect(
                dbname=db_name,
                user=db_user,
                password=db_pass,
                host=db_host
            )
        
        # Create a cursor
        cursor = conn.cursor()
        
        # Check if pos_order_lines table exists
        cursor.execute("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_schema = 'public'
                AND table_name = 'pos_order_lines'
            );
        """)
        
        table_exists = cursor.fetchone()[0]
        
        if not table_exists:
            print("Warning: pos_order_lines table doesn't exist. The database schema may need initialization.")
            return False
        
        # Check if discount_amount column exists
        cursor.execute("""
            SELECT EXISTS (
                SELECT FROM information_schema.columns 
                WHERE table_schema = 'public'
                AND table_name = 'pos_order_lines'
                AND column_name = 'discount_amount'
            );
        """)
        
        column_exists = cursor.fetchone()[0]
        
        if not column_exists:
            print("Adding discount_amount column to pos_order_lines table...")
            cursor.execute("""
                ALTER TABLE pos_order_lines
                ADD COLUMN discount_amount FLOAT DEFAULT 0.0;
            """)
            conn.commit()
            print("Successfully added discount_amount column to pos_order_lines table.")
        else:
            print("discount_amount column already exists in pos_order_lines table.")
            
        # Close cursor and connection
        cursor.close()
        conn.close()
        
        return True
        
    except Exception as e:
        print(f"Error connecting to database: {str(e)}")
        return False

if __name__ == "__main__":
    print("Running cloud database fix...")
    success = fix_cloud_database()
    if success:
        print("Database update completed successfully!")
    else:
        print("Database update failed. Please check the error messages above.") 