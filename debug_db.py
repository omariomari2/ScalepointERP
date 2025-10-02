from app import create_app, db
from modules.inventory.models_warehouse import WarehouseProduct, WarehouseMovement
from modules.inventory.models import Product, StockMove
import sys

def inspect_database():
    """Inspect the database tables to diagnose issues with warehouse product quantities"""
    print("=" * 80)
    print("DATABASE INSPECTION")
    print("=" * 80)
    
    # Check database engine and connection
    print(f"Database URL: {db.engine.url}")
    print(f"Database dialect: {db.engine.dialect.name}")
    
    # Inspect warehouse_products table schema
    print("\n" + "=" * 80)
    print("WAREHOUSE PRODUCTS TABLE SCHEMA")
    print("=" * 80)
    
    # Get table info directly from database
    inspector = db.inspect(db.engine)
    columns = inspector.get_columns('warehouse_products')
    
    for column in columns:
        print(f"Column: {column['name']}, Type: {column['type']}, Nullable: {column.get('nullable', True)}")
    
    # Check for specific product
    product_id = 557  # The product ID you mentioned
    print("\n" + "=" * 80)
    print(f"PRODUCT {product_id} DETAILS")
    print("=" * 80)
    
    product = Product.query.filter_by(id=product_id).first()
    if product:
        print(f"Product: {product.name} (ID: {product.id}, SKU: {product.sku})")
    else:
        print(f"Product with ID {product_id} not found")
    
    # Check warehouse products for this product
    print("\n" + "=" * 80)
    print(f"WAREHOUSE PRODUCTS FOR PRODUCT {product_id}")
    print("=" * 80)
    
    warehouse_products = WarehouseProduct.query.filter_by(product_id=product_id).all()
    
    if warehouse_products:
        for wp in warehouse_products:
            print(f"Warehouse ID: {wp.warehouse_id}, Quantity: {wp.quantity}, Updated: {wp.updated_at}")
            
            # Get raw data using SQL to verify
            result = db.session.execute(
                "SELECT quantity, updated_at FROM warehouse_products WHERE id = :id", 
                {"id": wp.id}
            ).fetchone()
            
            if result:
                print(f"  Raw SQL quantity: {result[0]}, Updated: {result[1]}")
                print(f"  Data type of quantity: {type(result[0])}")
    else:
        print(f"No warehouse products found for product {product_id}")
    
    # Check recent warehouse movements
    print("\n" + "=" * 80)
    print("RECENT WAREHOUSE MOVEMENTS")
    print("=" * 80)
    
    movements = WarehouseMovement.query.filter_by(product_id=product_id).order_by(WarehouseMovement.created_at.desc()).limit(10).all()
    
    if movements:
        for m in movements:
            print(f"ID: {m.id}, Type: {m.movement_type}, Quantity: {m.quantity}, Reference: {m.reference}, Created: {m.created_at}")
    else:
        print(f"No movements found for product {product_id}")
    
    # Check recent transfers
    print("\n" + "=" * 80)
    print("RECENT TRANSFERS")
    print("=" * 80)
    
    transfers = StockMove.query.filter_by(product_id=product_id).order_by(StockMove.created_at.desc()).limit(10).all()
    
    if transfers:
        for t in transfers:
            print(f"ID: {t.id}, State: {t.state}, Quantity: {t.quantity}, Created: {t.created_at}")
    else:
        print(f"No transfers found for product {product_id}")

if __name__ == "__main__":
    app = create_app()
    with app.app_context():
        inspect_database()
