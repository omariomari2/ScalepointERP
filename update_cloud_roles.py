"""
Script to update roles in the cloud database
This script will add the missing roles needed for proper role-based access control
"""
import os
from app import create_app, db
from modules.auth.models import Role, User, UserRole
import sys

def update_cloud_roles():
    """Add missing roles to the cloud database"""
    # Create app with production config to use cloud database via environment variable
    os.environ['DATABASE_URL'] = "postgresql://erpuser:ERPuser2025!@/erpsystem?host=/cloudsql/erp-system-445701:us-central1:erp-database"
    app = create_app('production')
    
    with app.app_context():
        print("Connecting to cloud database...")
        
        # Check existing roles
        existing_roles = Role.query.all()
        print(f"Found {len(existing_roles)} existing roles:")
        for role in existing_roles:
            print(f"- {role.name}")
        
        # Define required roles
        required_roles = [
            ('Shop Manager', 'Approves inventory transfers and manages shop operations'),
            ('Sales Worker', 'Sales Worker role'),
            ('Inventory Manager', 'Manages inventory transfers and stock movements')
        ]
        
        # Add missing roles
        roles_added = 0
        for role_name, role_desc in required_roles:
            # Check if role already exists (case insensitive)
            existing_role = Role.query.filter(Role.name.ilike(role_name)).first()
            
            if not existing_role:
                print(f"Adding missing role: {role_name}")
                new_role = Role(name=role_name, description=role_desc)
                db.session.add(new_role)
                roles_added += 1
            else:
                print(f"Role already exists: {existing_role.name}")
        
        if roles_added > 0:
            db.session.commit()
            print(f"Successfully added {roles_added} missing roles to the database")
        else:
            print("No new roles needed to be added")
        
        # Verify roles after update
        updated_roles = Role.query.all()
        print("\nCurrent roles in database:")
        for role in updated_roles:
            print(f"- {role.name}")

if __name__ == "__main__":
    try:
        update_cloud_roles()
        print("Cloud roles update completed successfully")
    except Exception as e:
        print(f"Error updating cloud roles: {e}")
        sys.exit(1)
