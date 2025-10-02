import os
import sys
from app import create_app, db
from modules.inventory.models import Product, Category

def remove_demo_products():
    app = create_app('development')
    with app.app_context():
        # Get the demo categories
        demo_categories = Category.query.filter(Category.name.in_(['Electronics', 'Furniture', 'Office Supplies'])).all()
        category_ids = [cat.id for cat in demo_categories]
        
        # Find products in these categories
        demo_products = Product.query.filter(Product.category_id.in_(category_ids)).all()
        
        if not demo_products:
            print("No demo products found.")
            return
        
        print(f"Found {len(demo_products)} demo products to remove:")
        for product in demo_products:
            print(f"- {product.name} (ID: {product.id}, Category: {product.category_id})")
        
        # Remove the products
        for product in demo_products:
            db.session.delete(product)
        
        db.session.commit()
        print(f"Successfully removed {len(demo_products)} demo products.")
        
        # Optionally remove the demo categories
        remove_categories = input("Do you want to remove the demo categories as well? (y/n): ").lower() == 'y'
        if remove_categories:
            for category in demo_categories:
                db.session.delete(category)
            db.session.commit()
            print(f"Successfully removed {len(demo_categories)} demo categories.")

if __name__ == '__main__':
    remove_demo_products()
