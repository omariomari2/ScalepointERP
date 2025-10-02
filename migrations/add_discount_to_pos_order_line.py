import os
import sys
import sqlite3

# Add the parent directory to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

def get_db_path():
    """Get the path to the SQLite database file"""
    # Look for the database file in the instance folder
    instance_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'instance')
    db_path = os.path.join(instance_path, 'erp.db')
    
    # If not found, look in the root directory
    if not os.path.exists(db_path):
        db_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'erp.db')
    
    # If still not found, search for any .db file
    if not os.path.exists(db_path):
        for root, dirs, files in os.walk(os.path.dirname(os.path.dirname(__file__))):
            for file in files:
                if file.endswith('.db'):
                    db_path = os.path.join(root, file)
                    print(f"Found database at: {db_path}")
                    return db_path
    
    return db_path

def upgrade():
    """Add discount_amount column to pos_order_lines table"""
    db_path = get_db_path()
    print(f"Using database at: {db_path}")
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Check if the column already exists
    cursor.execute("PRAGMA table_info(pos_order_lines)")
    columns = [column[1] for column in cursor.fetchall()]
    
    if 'discount_amount' not in columns:
        # Add the column
        cursor.execute('ALTER TABLE pos_order_lines ADD COLUMN discount_amount FLOAT DEFAULT 0.0')
        conn.commit()
        print("Added discount_amount column to pos_order_lines table")
    else:
        print("discount_amount column already exists in pos_order_lines table")
    
    conn.close()

def downgrade():
    """Remove discount_amount column from pos_order_lines table"""
    db_path = get_db_path()
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Check if the column exists
    cursor.execute("PRAGMA table_info(pos_order_lines)")
    columns = [column[1] for column in cursor.fetchall()]
    
    if 'discount_amount' in columns:
        # SQLite doesn't support dropping columns directly
        # We would need to create a new table without the column and copy data
        print("SQLite doesn't support dropping columns directly. Please use a full migration tool for downgrade.")
    else:
        print("discount_amount column does not exist in pos_order_lines table")
    
    conn.close()

if __name__ == '__main__':
    # Run the upgrade function when script is executed
    upgrade()
