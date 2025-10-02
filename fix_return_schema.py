"""
Fix the database schema for the POSReturnLine model to ensure it can properly handle quantities.
This script directly modifies the database schema without requiring a migration.
"""
import os
import sys
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import Column, Integer, Float, String, ForeignKey, DateTime, Boolean, MetaData, Table
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime

# Create a minimal Flask app to access the database
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'sqlite:///erp.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

def fix_database_schema():
    """Fix the database schema for the POSReturnLine model."""
    with app.app_context():
        try:
            # Get the database engine
            engine = db.engine
            
            # Create a connection
            connection = engine.connect()
            
            # Get the metadata
            metadata = MetaData()
            metadata.reflect(bind=engine)
            
            # Check if the pos_return_lines table exists
            if 'pos_return_lines' in metadata.tables:
                # Get the table
                pos_return_lines = metadata.tables['pos_return_lines']
                
                # Check if the quantity column exists and is an Integer
                if 'quantity' in pos_return_lines.columns:
                    # Print the current column type
                    print(f"Current quantity column type: {pos_return_lines.columns['quantity'].type}")
                    
                    # Check if the unit_price column exists
                    if 'unit_price' in pos_return_lines.columns:
                        print(f"Current unit_price column type: {pos_return_lines.columns['unit_price'].type}")
                    
                    # Check if the subtotal column exists
                    if 'subtotal' in pos_return_lines.columns:
                        print(f"Current subtotal column type: {pos_return_lines.columns['subtotal'].type}")
                    
                    # For SQLite, we can't easily change column types, so we'll use a workaround
                    # We'll create a temporary table, copy the data, drop the old table, and rename the new one
                    
                    # Create a temporary table with the correct schema
                    connection.execute("""
                    CREATE TABLE IF NOT EXISTS pos_return_lines_new (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        return_id INTEGER NOT NULL,
                        product_id INTEGER NOT NULL,
                        original_order_line_id INTEGER,
                        quantity INTEGER NOT NULL DEFAULT 0,
                        unit_price FLOAT NOT NULL DEFAULT 0.0,
                        subtotal FLOAT NOT NULL DEFAULT 0.0,
                        return_reason VARCHAR(64),
                        state VARCHAR(20) DEFAULT 'draft',
                        product_name VARCHAR(255),
                        FOREIGN KEY (return_id) REFERENCES pos_returns (id),
                        FOREIGN KEY (product_id) REFERENCES products (id),
                        FOREIGN KEY (original_order_line_id) REFERENCES pos_order_lines (id)
                    )
                    """)
                    
                    # Copy the data from the old table to the new one
                    connection.execute("""
                    INSERT INTO pos_return_lines_new
                    SELECT id, return_id, product_id, original_order_line_id, 
                           quantity, unit_price, subtotal, return_reason, state, product_name
                    FROM pos_return_lines
                    """)
                    
                    # Get the count of rows in both tables to verify
                    old_count = connection.execute("SELECT COUNT(*) FROM pos_return_lines").scalar()
                    new_count = connection.execute("SELECT COUNT(*) FROM pos_return_lines_new").scalar()
                    
                    print(f"Old table row count: {old_count}")
                    print(f"New table row count: {new_count}")
                    
                    if old_count == new_count:
                        # Drop the old table
                        connection.execute("DROP TABLE pos_return_lines")
                        
                        # Rename the new table
                        connection.execute("ALTER TABLE pos_return_lines_new RENAME TO pos_return_lines")
                        
                        print("Database schema fixed successfully")
                    else:
                        print("Row counts don't match, not proceeding with table replacement")
                else:
                    print("Quantity column not found in pos_return_lines table")
            else:
                print("pos_return_lines table not found in database")
            
            # Close the connection
            connection.close()
            
            return True
        except Exception as e:
            print(f"Error fixing database schema: {str(e)}")
            import traceback
            traceback.print_exc()
            return False

if __name__ == "__main__":
    fix_database_schema()
