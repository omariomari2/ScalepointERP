from app import create_app, db
from modules.inventory.models import Product
from modules.inventory.models_warehouse import WarehouseProduct

app = create_app()
with app.app_context():
    # Check for product by name or SKU
    product = Product.query.filter((Product.name == '559') | (Product.sku == '100**')).first()
    
    if product:
        print(f"Product found:")
        print(f"ID: {product.id}")
        print(f"Name: {product.name}")
        print(f"SKU: {product.sku}")
        print(f"Description: {product.description}")
        print(f"Active: {product.is_active}")
        
        # Check warehouse quantities
        warehouse_entries = WarehouseProduct.query.filter_by(product_id=product.id).all()
        if warehouse_entries:
            print("\nWarehouse quantities:")
            for entry in warehouse_entries:
                print(f"Warehouse ID: {entry.warehouse_id}, Quantity: {entry.quantity}")
        else:
            print("\nNo warehouse entries found for this product.")
    else:
        print("No product found with name '559' or SKU '100**'")
        
        # Try partial match
        partial_matches = Product.query.filter(
            (Product.name.like('%559%')) | 
            (Product.sku.like('%100%'))
        ).all()
        
        if partial_matches:
            print("\nFound similar products:")
            for p in partial_matches:
                print(f"ID: {p.id}, Name: {p.name}, SKU: {p.sku}")
