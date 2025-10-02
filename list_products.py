from app import create_app, db
from modules.inventory.models import Product, Category

def list_products():
    app = create_app('development')
    with app.app_context():
        products = Product.query.all()
        categories = Category.query.all()
        
        print(f"Found {len(products)} products:")
        for product in products:
            category_name = next((c.name for c in categories if c.id == product.category_id), "Unknown")
            print(f"- {product.name} (ID: {product.id}, Category: {category_name})")
        
        print("\nCategories:")
        for category in categories:
            print(f"- {category.name} (ID: {category.id})")

if __name__ == '__main__':
    list_products()
