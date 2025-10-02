"""
Script to create the scrap_items table using Flask-SQLAlchemy
"""
from app import create_app
from extensions import db
import os

# Import only the ScrapItem model
from modules.inventory.models_scrap import ScrapItem

def create_scrap_table():
    """Create the scrap_items table"""
    print("Creating application context...")
    app = create_app()
    
    with app.app_context():
        print(f"Database URI: {app.config['SQLALCHEMY_DATABASE_URI']}")
        print("Creating scrap_items table...")
        
        # Check if the table exists
        inspector = db.inspect(db.engine)
        if 'scrap_items' not in inspector.get_table_names():
            # Create just the scrap_items table
            ScrapItem.__table__.create(db.engine)
            print("Scrap items table created successfully!")
        else:
            print("Scrap items table already exists.")

if __name__ == '__main__':
    create_scrap_table()
