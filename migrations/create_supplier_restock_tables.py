import sys
import os

# Add the parent directory to the path so we can import modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from extensions import db
from app import create_app
from modules.inventory.models_supplier_restock import SupplierRestock, SupplierRestockItem

def create_tables():
    """Create the supplier restock tables in the database"""
    print("Creating supplier restock tables...")
    
    # Create the tables
    db.create_all()
    
    # Check if tables were created
    engine = db.engine
    inspector = db.inspect(engine)
    
    tables_created = []
    if 'supplier_restocks' in inspector.get_table_names():
        tables_created.append('supplier_restocks')
    if 'supplier_restock_items' in inspector.get_table_names():
        tables_created.append('supplier_restock_items')
    
    if len(tables_created) == 2:
        print("Supplier restock tables created successfully!")
    else:
        print(f"Warning: Only some tables were created: {tables_created}")
        
    return True

if __name__ == '__main__':
    app = create_app()
    with app.app_context():
        create_tables()
