from app import create_app, db
from modules.inventory.models import Product
from modules.inventory.models_warehouse import WarehouseProduct

def list_all_products():
    """List all products in the database and their warehouse quantities"""
    print("=" * 80)
    print("ALL PRODUCTS IN DATABASE")
    print("=" * 80)
    
    products = Product.query.all()
    
    if products:
        print(f"Found {len(products)} products")
        for product in products:
            print(f"ID: {product.id}, Name: {product.name}, SKU: {product.sku}")
            
            # Check warehouse quantities for this product
            warehouse_products = WarehouseProduct.query.filter_by(product_id=product.id).all()
            if warehouse_products:
                for wp in warehouse_products:
                    print(f"  Warehouse ID: {wp.warehouse_id}, Quantity: {wp.quantity}")
            else:
                print("  No warehouse entries found for this product")
    else:
        print("No products found in the database")
    
    print("\n" + "=" * 80)
    print("ALL WAREHOUSE PRODUCTS")
    print("=" * 80)
    
    warehouse_products = WarehouseProduct.query.all()
    
    if warehouse_products:
        print(f"Found {len(warehouse_products)} warehouse product entries")
        for wp in warehouse_products:
            product = Product.query.get(wp.product_id)
            product_name = product.name if product else "Unknown Product"
            print(f"ID: {wp.id}, Product ID: {wp.product_id} ({product_name}), Warehouse ID: {wp.warehouse_id}, Quantity: {wp.quantity}")
    else:
        print("No warehouse product entries found")

if __name__ == "__main__":
    app = create_app()
    with app.app_context():
        list_all_products()
