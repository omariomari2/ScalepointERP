from app import create_app
from modules.inventory.models import Product, Category, Warehouse
from modules.inventory.models_warehouse import WarehouseProduct
from flask import Flask

app = create_app()

with app.app_context():
    # Check SCREENS category
    screens_category = Category.query.filter_by(name='SCREENS').first()
    print(f'SCREENS category: {screens_category}')
    
    if screens_category:
        # Get products with SCREENS category
        products = Product.query.filter_by(category_id=screens_category.id).all()
        print(f'Products with SCREENS category: {len(products)}')
        for p in products:
            print(f'- {p.name} (ID: {p.id})')
            
            # Check if these products are in any warehouse
            warehouse_products = WarehouseProduct.query.filter_by(product_id=p.id).all()
            print(f'  In warehouses: {len(warehouse_products)}')
            for wp in warehouse_products:
                warehouse = Warehouse.query.get(wp.warehouse_id)
                print(f'  - {warehouse.name} (Qty: {wp.quantity})')
    
    # List all categories
    print("\nAll Categories:")
    categories = Category.query.all()
    for cat in categories:
        print(f"- {cat.name} (ID: {cat.id})")
        products_count = Product.query.filter_by(category_id=cat.id).count()
        print(f"  Products: {products_count}")
