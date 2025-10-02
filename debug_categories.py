from app import create_app
from modules.inventory.models import Product, Category
from modules.inventory.models_warehouse import WarehouseProduct
from flask import Flask
import pandas as pd

app = create_app()

with app.app_context():
    # Check all categories
    print("=== ALL CATEGORIES ===")
    categories = Category.query.all()
    for cat in categories:
        print(f"- {cat.name} (ID: {cat.id})")
        # Check if any products have this category
        products_count = Product.query.filter_by(category_id=cat.id).count()
        print(f"  Products with this category: {products_count}")
    
    print("\n=== ALL PRODUCTS ===")
    products = Product.query.all()
    print(f"Total products: {len(products)}")
    for p in products:
        category_name = p.category.name if p.category else "None"
        print(f"- {p.name} (SKU: {p.sku}, Category ID: {p.category_id}, Category: {category_name})")
        
    print("\n=== CHECKING CASE SENSITIVITY ===")
    # Check for case sensitivity issues with category names
    test_categories = ["SCREENS", "screens", "Screens"]
    for test_name in test_categories:
        cat = Category.query.filter(Category.name.ilike(f"%{test_name}%")).all()
        print(f"Search for '{test_name}': {cat}")
        
    print("\n=== WAREHOUSE PRODUCTS ===")
    warehouse_products = WarehouseProduct.query.limit(5).all()
    for wp in warehouse_products:
        product = Product.query.get(wp.product_id)
        category_name = product.category.name if product.category else "None"
        print(f"- WP ID: {wp.id}, Product: {product.name}, Category: {category_name}")
