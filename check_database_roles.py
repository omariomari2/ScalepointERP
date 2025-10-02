"""
Script to check the roles in the database
"""
import os
from app import create_app, db
from modules.auth.models import Role, User, UserRole

def check_roles():
    """Check the roles in the database"""
    # Create app with development config to use local database
    app = create_app('development')
    
    with app.app_context():
        # Get all roles
        roles = Role.query.all()
        print("=== Roles in Database ===")
        for role in roles:
            print(f"ID: {role.id}, Name: '{role.name}', Description: {role.description}")
        
        # Get a sample user with roles
        admin_user = User.query.filter_by(username='admin').first()
        if admin_user:
            print("\n=== Admin User Roles ===")
            for role in admin_user.roles:
                print(f"Role: '{role.name}'")
        
        # Check for specific roles
        shop_manager = Role.query.filter(Role.name.ilike('%shop%manager%')).first()
        if shop_manager:
            print(f"\nFound Shop Manager role: '{shop_manager.name}'")
        else:
            print("\nNo Shop Manager role found")
        
        sales_worker = Role.query.filter(Role.name.ilike('%sales%worker%')).first()
        if sales_worker:
            print(f"Found Sales Worker role: '{sales_worker.name}'")
        else:
            print("No Sales Worker role found")
        
        # Check similar roles
        manager = Role.query.filter(Role.name.ilike('%manager%')).all()
        print("\n=== Manager-like Roles ===")
        for role in manager:
            print(f"Role: '{role.name}'")
        
        sales = Role.query.filter(Role.name.ilike('%sales%')).all()
        print("\n=== Sales-like Roles ===")
        for role in sales:
            print(f"Role: '{role.name}'")

if __name__ == "__main__":
    check_roles()
