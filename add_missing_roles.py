"""
Script to add missing roles to the database
"""
import os
from app import create_app, db
from modules.auth.models import Role

def add_missing_roles():
    """Add missing roles to the database"""
    # Create app with production config to use cloud database
    app = create_app('production')
    
    with app.app_context():
        # Check if roles already exist
        sales_worker = Role.query.filter_by(name='Sales Worker').first()
        shop_manager = Role.query.filter_by(name='Shop Manager').first()
        inventory_manager = Role.query.filter_by(name='Inventory Manager').first()
        
        roles_to_add = []
        
        if not sales_worker:
            print("Adding 'Sales Worker' role")
            roles_to_add.append(Role(name='Sales Worker', description='Sales Worker role'))
        
        if not shop_manager:
            print("Adding 'Shop Manager' role")
            roles_to_add.append(Role(name='Shop Manager', description='Approves inventory transfers and manages shop operations'))
        
        if not inventory_manager:
            print("Adding 'Inventory Manager' role")
            roles_to_add.append(Role(name='Inventory Manager', description='Manages inventory transfers and stock movements'))
        
        if roles_to_add:
            db.session.add_all(roles_to_add)
            db.session.commit()
            print(f"Added {len(roles_to_add)} new roles to the database")
        else:
            print("All required roles already exist in the database")

if __name__ == "__main__":
    add_missing_roles()
