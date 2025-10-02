"""
Script to create all database tables using Flask-SQLAlchemy
"""
from app import create_app
from extensions import db
import os

# Import all models to ensure they are registered with SQLAlchemy
from modules.auth.models import User, Role, UserRole
from modules.inventory.models import Category, UnitOfMeasure, Product, Warehouse, StockLocation, StockMove, Inventory, InventoryLine
from modules.inventory.models_warehouse import WarehouseProduct, WarehouseMovement
from modules.inventory.models_scrap import ScrapItem
from modules.pos.models import Shop, ShopProduct, Order, OrderLine, Payment, Receipt, ReceiptSettings

def create_all_tables():
    """Create all tables defined in the models"""
    print("Creating application context...")
    app = create_app()
    
    with app.app_context():
        print(f"Database URI: {app.config['SQLALCHEMY_DATABASE_URI']}")
        print("Creating all tables...")
        db.create_all()
        print("All tables created successfully!")

if __name__ == '__main__':
    create_all_tables()
