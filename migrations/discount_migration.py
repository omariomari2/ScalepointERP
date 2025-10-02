import sqlite3
import os
import sys
from pathlib import Path

def run_migration():
    """Add discount_amount column to pos_order_lines table in all SQLite databases"""
    # Get the project root directory
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    
    # Find all SQLite database files in the project
    db_files = []
    for root, dirs, files in os.walk(project_root):
        for file in files:
            if file.endswith('.db'):
                db_files.append(os.path.join(root, file))
    
    print(f"Found {len(db_files)} database files.")
    
    # Track which databases were modified
    modified_dbs = []
    
    # Process each database
    for db_path in db_files:
        print(f"\nChecking database: {db_path}")
        
        try:
            # Connect to the database
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            # Get all tables in the database
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
            tables = [table[0] for table in cursor.fetchall()]
            
            db_modified = False
            
            # Check for pos_order_lines table
            if 'pos_order_lines' in tables:
                print(f"Found pos_order_lines table in {db_path}")
                
                # Check if discount_amount column exists
                cursor.execute("PRAGMA table_info(pos_order_lines)")
                columns = [column[1] for column in cursor.fetchall()]
                
                if 'discount_amount' not in columns:
                    print("Adding discount_amount column to pos_order_lines table...")
                    cursor.execute('''
                        ALTER TABLE pos_order_lines
                        ADD COLUMN discount_amount FLOAT DEFAULT 0.0
                    ''')
                    db_modified = True
                    modified_dbs.append(db_path)
                else:
                    print("discount_amount column already exists in pos_order_lines table.")
            
            # Commit changes if any were made
            if db_modified:
                conn.commit()
                print(f"Successfully modified {db_path}")
            
            conn.close()
            
        except Exception as e:
            print(f"Error processing {db_path}: {str(e)}")
    
    # Summary
    if modified_dbs:
        print(f"\nSuccessfully added discount_amount column to pos_order_lines table in {len(modified_dbs)} databases:")
        for db in modified_dbs:
            print(f"  - {db}")
        return True
    else:
        print("\nNo databases were modified. Either the column already exists or the table wasn't found.")
        return False

if __name__ == "__main__":
    print("Running discount migration...")
    success = run_migration()
    if success:
        print("Migration completed successfully!")
    else:
        print("Migration completed with no changes.")
