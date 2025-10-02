"""
Migration script to create the scrap_items table using direct SQL
"""
import sqlite3
import os

def run_migration():
    """Create the scrap_items table using direct SQL"""
    print("Creating scrap_items table...")
    
    # Connect to the database
    db_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'instance', 'erp.db')
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Create the scrap_items table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS scrap_items (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        product_id INTEGER NOT NULL,
        warehouse_id INTEGER NOT NULL,
        quantity INTEGER NOT NULL,
        reason VARCHAR(255) NOT NULL,
        reference VARCHAR(64),
        status VARCHAR(20) DEFAULT 'pending',
        created_by_id INTEGER,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        received_by_id INTEGER,
        received_at TIMESTAMP,
        notes TEXT,
        FOREIGN KEY (product_id) REFERENCES products (id),
        FOREIGN KEY (warehouse_id) REFERENCES warehouses (id),
        FOREIGN KEY (created_by_id) REFERENCES users (id),
        FOREIGN KEY (received_by_id) REFERENCES users (id)
    )
    ''')
    
    # Commit the changes and close the connection
    conn.commit()
    conn.close()
    
    print("Scrap items table created successfully!")
    return True

if __name__ == "__main__":
    run_migration()
