"""
Script to check the erp_system.db database for POS-related tables.
"""
import sqlite3
import os

def check_database():
    """Check the erp_system.db database for POS-related tables"""
    db_path = os.path.join(os.path.dirname(__file__), 'instance', 'erp_system.db')
    
    try:
        # Connect to the database
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Get all tables
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = cursor.fetchall()
        
        print(f"Found {len(tables)} tables in {db_path}:")
        for table in tables:
            print(f"- {table[0]}")
        
        # Check for POS-related tables
        pos_tables = [table[0] for table in tables if table[0].startswith('pos_')]
        if pos_tables:
            print(f"\nFound {len(pos_tables)} POS-related tables:")
            for table in pos_tables:
                print(f"- {table}")
                
                # Get the schema for POS return-related tables
                if table in ['pos_returns', 'pos_return_line']:
                    print(f"\nSchema for {table}:")
                    cursor.execute(f"PRAGMA table_info({table})")
                    columns = cursor.fetchall()
                    for column in columns:
                        print(f"  - {column[1]} ({column[2]})")
        else:
            print("\nNo POS-related tables found")
        
        # Close the connection
        conn.close()
        
        return True
    except Exception as e:
        print(f"Error checking database: {str(e)}")
        return False

if __name__ == "__main__":
    check_database()
