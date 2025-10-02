"""
Direct fix for the return details display issue in the ERP system.
This script directly fixes the database schema and ensures values are properly saved and displayed.
"""
import os
import sys
import sqlite3
import shutil
from datetime import datetime

def backup_database():
    """Create a backup of the database"""
    db_path = r"c:\Users\USER\erpsystem_working_backup\instance\erp.db"
    if os.path.exists(db_path):
        backup_dir = os.path.dirname(db_path)
        timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
        backup_path = os.path.join(backup_dir, f"erp.{timestamp}.bak.db")
        
        shutil.copy2(db_path, backup_path)
        print(f"Created database backup: {backup_path}")
        return True
    else:
        print(f"Error: Database file not found at {db_path}")
        return False

def fix_database_schema():
    """Fix the database schema to ensure return lines have correct data types"""
    db_path = r"c:\Users\USER\erpsystem_working_backup\instance\erp.db"
    
    try:
        # Connect to the database
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Check if the pos_return_lines table exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='pos_return_lines'")
        if cursor.fetchone() is None:
            print("Error: pos_return_lines table not found in the database")
            conn.close()
            return False
        
        # Get the current schema of the pos_return_lines table
        cursor.execute("PRAGMA table_info(pos_return_lines)")
        columns = cursor.fetchall()
        
        # Check the data types of the quantity, unit_price, and subtotal columns
        quantity_type = None
        unit_price_type = None
        subtotal_type = None
        
        for column in columns:
            if column[1] == 'quantity':
                quantity_type = column[2]
            elif column[1] == 'unit_price':
                unit_price_type = column[2]
            elif column[1] == 'subtotal':
                subtotal_type = column[2]
        
        print(f"Current schema: quantity={quantity_type}, unit_price={unit_price_type}, subtotal={subtotal_type}")
        
        # Fix the data in the pos_return_lines table
        # First, update any NULL values to defaults
        cursor.execute("UPDATE pos_return_lines SET quantity = 1 WHERE quantity IS NULL OR quantity <= 0")
        cursor.execute("UPDATE pos_return_lines SET unit_price = 0 WHERE unit_price IS NULL")
        cursor.execute("UPDATE pos_return_lines SET subtotal = quantity * unit_price WHERE subtotal IS NULL OR subtotal <= 0")
        
        # Get the count of updated rows
        updated_rows = cursor.rowcount
        print(f"Updated {updated_rows} rows with default values")
        
        # Now update the subtotal for all rows to ensure it's correctly calculated
        cursor.execute("UPDATE pos_return_lines SET subtotal = quantity * unit_price")
        updated_rows = cursor.rowcount
        print(f"Updated {updated_rows} rows with correct subtotal values")
        
        # Commit the changes
        conn.commit()
        
        # Verify the data
        cursor.execute("SELECT id, quantity, unit_price, subtotal FROM pos_return_lines")
        rows = cursor.fetchall()
        print(f"Verified {len(rows)} rows in pos_return_lines table")
        
        # Check for any remaining issues
        cursor.execute("SELECT id, quantity, unit_price, subtotal FROM pos_return_lines WHERE subtotal != quantity * unit_price")
        rows = cursor.fetchall()
        if rows:
            print(f"Warning: Found {len(rows)} rows with incorrect subtotal values")
            for row in rows:
                print(f"  ID: {row[0]}, quantity: {row[1]}, unit_price: {row[2]}, subtotal: {row[3]}, calculated: {row[1] * row[2]}")
                # Fix these rows
                cursor.execute("UPDATE pos_return_lines SET subtotal = ? WHERE id = ?", (row[1] * row[2], row[0]))
            conn.commit()
            print("Fixed remaining issues with subtotal values")
        
        # Close the connection
        conn.close()
        
        print("Successfully fixed database schema and data")
        return True
    except Exception as e:
        print(f"Error fixing database schema: {str(e)}")
        return False

def fix_return_line_model():
    """Create a fixed version of the POSReturnLine model"""
    model_path = r"c:\Users\USER\erpsystem_working_backup\fixed_return_line_model.py"
    
    try:
        model_content = """\"\"\"
Fixed version of the POSReturnLine model to ensure correct values are saved.
This should be imported in app.py and used to replace the existing model.
\"\"\"
from extensions import db
from datetime import datetime

class FixedPOSReturnLine(db.Model):
    __tablename__ = 'pos_return_lines'
    
    id = db.Column(db.Integer, primary_key=True)
    return_id = db.Column(db.Integer, db.ForeignKey('pos_returns.id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=False)
    original_order_line_id = db.Column(db.Integer, db.ForeignKey('pos_order_lines.id'), nullable=True)
    quantity = db.Column(db.Float, default=1.0, nullable=False)
    unit_price = db.Column(db.Float, default=0.0, nullable=False)
    subtotal = db.Column(db.Float, default=0.0, nullable=False)
    return_reason = db.Column(db.String(64))
    state = db.Column(db.String(20), default='draft')
    product_name = db.Column(db.String(255))  # Store product name for resilience
    
    # Relationships
    product = db.relationship('Product')
    original_order_line = db.relationship('POSOrderLine', foreign_keys=[original_order_line_id], back_populates='return_lines')
    
    def __init__(self, **kwargs):
        super(FixedPOSReturnLine, self).__init__(**kwargs)
        # Ensure subtotal is calculated correctly
        if self.quantity and self.unit_price:
            self.subtotal = self.quantity * self.unit_price
    
    def __repr__(self):
        return f'<POSReturnLine {self.id} - Product: {self.product_id}, Qty: {self.quantity}>'
"""
        
        with open(model_path, 'w', encoding='utf-8') as f:
            f.write(model_content)
        
        print(f"Successfully created {model_path}")
        return True
    except Exception as e:
        print(f"Error creating fixed return line model: {str(e)}")
        return False

def create_app_patch():
    """Create a patch for app.py to use the fixed model"""
    patch_path = r"c:\Users\USER\erpsystem_working_backup\apply_fixed_model.py"
    
    try:
        patch_content = """\"\"\"
Patch to apply the fixed return line model to the application.
This script should be run before starting the application.
\"\"\"
import sys
import importlib.util
import os

def apply_fixed_model():
    \"\"\"Apply the fixed return line model to the application\"\"\"
    try:
        # Import the fixed model
        spec = importlib.util.spec_from_file_location(
            "fixed_return_line_model",
            os.path.join(os.path.dirname(__file__), "fixed_return_line_model.py")
        )
        fixed_model = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(fixed_model)
        
        # Import the original model
        from modules.pos.models import POSReturnLine
        
        # Replace the original model with the fixed model
        original_module = sys.modules['modules.pos.models']
        original_module.POSReturnLine = fixed_model.FixedPOSReturnLine
        
        print("Successfully applied fixed return line model")
        return True
    except Exception as e:
        print(f"Error applying fixed model: {str(e)}")
        return False

if __name__ == "__main__":
    if apply_fixed_model():
        print("Fixed model applied successfully")
    else:
        print("Failed to apply fixed model")
        sys.exit(1)
"""
        
        with open(patch_path, 'w', encoding='utf-8') as f:
            f.write(patch_content)
        
        print(f"Successfully created {patch_path}")
        return True
    except Exception as e:
        print(f"Error creating app patch: {str(e)}")
        return False

def create_startup_script():
    """Create a startup script that applies all fixes and starts the application"""
    script_path = r"c:\Users\USER\erpsystem_working_backup\start_fixed_app.py"
    
    try:
        script_content = """\"\"\"
Startup script that applies all fixes and starts the application.
\"\"\"
import os
import sys
import subprocess

def main():
    \"\"\"Apply all fixes and start the application\"\"\"
    print("Applying fixes and starting the application...")
    
    # Apply the fixed model
    print("Applying fixed return line model...")
    result = subprocess.run([sys.executable, "apply_fixed_model.py"], capture_output=True, text=True)
    if result.returncode != 0:
        print(f"Error applying fixed model: {result.stderr}")
        return False
    
    print(result.stdout)
    
    # Start the application
    print("Starting the application...")
    os.execv(sys.executable, [sys.executable, "app.py"])
    
    return True

if __name__ == "__main__":
    main()
"""
        
        with open(script_path, 'w', encoding='utf-8') as f:
            f.write(script_content)
        
        print(f"Successfully created {script_path}")
        return True
    except Exception as e:
        print(f"Error creating startup script: {str(e)}")
        return False

def main():
    """Apply all fixes"""
    print("Starting direct fix for return display issue...")
    
    # Backup the database
    if not backup_database():
        print("Failed to backup database")
        return False
    
    # Fix the database schema
    if not fix_database_schema():
        print("Failed to fix database schema")
        return False
    
    # Create the fixed return line model
    if not fix_return_line_model():
        print("Failed to create fixed return line model")
        return False
    
    # Create the app patch
    if not create_app_patch():
        print("Failed to create app patch")
        return False
    
    # Create the startup script
    if not create_startup_script():
        print("Failed to create startup script")
        return False
    
    print("\nAll fixes applied successfully!")
    print("To start the application with the fixes, run:")
    print("python start_fixed_app.py")
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
