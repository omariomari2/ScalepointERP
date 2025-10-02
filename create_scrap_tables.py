import os
import sqlite3
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def ensure_scrap_tables_exist():
    """
    Ensure that the scrap_items table exists in the database.
    If it doesn't exist, create it.
    """
    # Check multiple possible database paths
    possible_db_paths = [
        os.path.join('instance', 'erp_system.db'),
        os.path.join('instance', 'erp.db'),
        os.path.join('instance', 'app.db'),
        os.path.join('instance', 'dev.db'),
        'erp_system.db',
        'erp.db'
    ]
    
    db_path = None
    for path in possible_db_paths:
        if os.path.exists(path):
            db_path = path
            logger.info(f"Found database at {db_path}")
            break
    
    if not db_path:
        logger.error("No database file found in any of the expected locations")
        return False
    
    try:
        # Connect to the database
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Check if the scrap_items table exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='scrap_items'")
        table_exists = cursor.fetchone()
        
        if not table_exists:
            logger.info("scrap_items table does not exist. Creating it...")
            
            # Create the scrap_items table
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS scrap_items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                product_id INTEGER NOT NULL,
                warehouse_id INTEGER NOT NULL,
                quantity INTEGER NOT NULL,
                reason TEXT NOT NULL,
                reference TEXT,
                status TEXT DEFAULT 'pending',
                created_by_id INTEGER,
                created_at TIMESTAMP,
                received_by_id INTEGER,
                received_at TIMESTAMP,
                notes TEXT,
                FOREIGN KEY (product_id) REFERENCES products (id),
                FOREIGN KEY (warehouse_id) REFERENCES warehouses (id),
                FOREIGN KEY (created_by_id) REFERENCES users (id),
                FOREIGN KEY (received_by_id) REFERENCES users (id)
            )
            ''')
            
            conn.commit()
            logger.info("scrap_items table created successfully")
            return True
        else:
            logger.info("scrap_items table already exists")
            return True
            
    except Exception as e:
        logger.error(f"Error ensuring scrap tables exist: {str(e)}")
        return False
    finally:
        if conn:
            conn.close()

if __name__ == "__main__":
    ensure_scrap_tables_exist()
