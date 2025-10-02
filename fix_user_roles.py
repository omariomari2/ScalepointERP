"""
Script to fix the role assignment issue in the ERP system.
This script ensures that the Inventory Manager and Shop Manager roles exist
and can be properly assigned to users.
"""

from app import create_app, db
from modules.auth.models import User, Role, UserRole
import sys

def fix_roles():
    """Fix the roles in the database to ensure inventory_manager and shop_manager roles exist."""
    app = create_app('production')
    with app.app_context():
        print("Checking and fixing roles in the database...")
        
        # Check if roles exist
        inventory_manager_role = Role.query.filter(Role.name.ilike('Inventory Manager')).first()
        shop_manager_role = Role.query.filter(Role.name.ilike('Shop Manager')).first()
        
        # Create the roles if they don't exist
        if not inventory_manager_role:
            print("Creating Inventory Manager role...")
            inventory_manager_role = Role(
                name='Inventory Manager',
                description='Manages inventory transfers and stock movements'
            )
            db.session.add(inventory_manager_role)
            db.session.commit()
            print("Inventory Manager role created successfully!")
        else:
            print(f"Inventory Manager role already exists with ID: {inventory_manager_role.id}")
        
        if not shop_manager_role:
            print("Creating Shop Manager role...")
            shop_manager_role = Role(
                name='Shop Manager',
                description='Approves inventory transfers and manages shop operations'
            )
            db.session.add(shop_manager_role)
            db.session.commit()
            print("Shop Manager role created successfully!")
        else:
            print(f"Shop Manager role already exists with ID: {shop_manager_role.id}")
        
        # List all roles for verification
        print("\nAll roles in the system:")
        all_roles = Role.query.all()
        for role in all_roles:
            print(f"ID: {role.id}, Name: {role.name}")
        
        # Check user role assignment function
        print("\nVerifying role assignment functionality...")
        test_user = User.query.filter_by(username='admin').first()
        if test_user:
            # Check if admin has the roles
            has_inventory_role = test_user.has_role('Inventory Manager')
            has_shop_role = test_user.has_role('Shop Manager')
            
            print(f"Admin user has Inventory Manager role: {has_inventory_role}")
            print(f"Admin user has Shop Manager role: {has_shop_role}")
            
            # Assign roles if not present
            if not has_inventory_role and inventory_manager_role:
                print("Assigning Inventory Manager role to admin...")
                user_role = UserRole(user_id=test_user.id, role_id=inventory_manager_role.id)
                db.session.add(user_role)
                db.session.commit()
            
            if not has_shop_role and shop_manager_role:
                print("Assigning Shop Manager role to admin...")
                user_role = UserRole(user_id=test_user.id, role_id=shop_manager_role.id)
                db.session.add(user_role)
                db.session.commit()
            
            # Verify again
            db.session.refresh(test_user)
            print(f"After assignment - Admin has Inventory Manager role: {test_user.has_role('Inventory Manager')}")
            print(f"After assignment - Admin has Shop Manager role: {test_user.has_role('Shop Manager')}")
        
        print("\nRole verification and fix completed!")

if __name__ == "__main__":
    fix_roles()
