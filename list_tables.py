"""
Script to list all tables in the database.
"""
import sqlite3
import os

def list_tables():
    """List all tables in the database"""
    db_path = os.path.join(os.path.dirname(__file__), 'instance', 'erp.db')
    
    try:
        # Connect to the database
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Get all tables
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = cursor.fetchall()
        
        print(f"Found {len(tables)} tables in the database:")
        for table in tables:
            print(f"- {table[0]}")
        
        # Close the connection
        conn.close()
        
        return True
    except Exception as e:
        print(f"Error listing tables: {str(e)}")
        return False

if __name__ == "__main__":
    list_tables()
