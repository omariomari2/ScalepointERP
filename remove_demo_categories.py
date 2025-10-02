from app import create_app, db
from modules.inventory.models import Category

def remove_demo_categories():
    app = create_app('development')
    with app.app_context():
        # Get the demo categories
        demo_categories = Category.query.filter(Category.name.in_(['Electronics', 'Furniture', 'Office Supplies', 'Raw Materials', 'Finished Goods', 'Services', 'Consumables'])).all()
        
        if not demo_categories:
            print("No demo categories found.")
            return
        
        print(f"Found {len(demo_categories)} demo categories to remove:")
        for category in demo_categories:
            print(f"- {category.name} (ID: {category.id})")
        
        # Remove the categories
        for category in demo_categories:
            db.session.delete(category)
        
        db.session.commit()
        print(f"Successfully removed {len(demo_categories)} demo categories.")

if __name__ == '__main__':
    remove_demo_categories()
