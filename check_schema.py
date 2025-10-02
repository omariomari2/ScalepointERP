from app import create_app, db
from modules.inventory.models_warehouse import WarehouseProduct

app = create_app()

with app.app_context():
    # Get the column type for the quantity column
    inspector = db.inspect(db.engine)
    columns = inspector.get_columns('warehouse_products')
    
    print("Warehouse Products Table Schema:")
    for column in columns:
        print(f"Column: {column['name']}, Type: {column['type']}")
