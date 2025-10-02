"""
Script to fix role assignments in the cloud database
This script will be included in the Docker image and run during startup
"""
from app import create_app, db
from modules.auth.models import Role, User, UserRole
from sqlalchemy import text
import sys
import traceback

def fix_cloud_roles():
    """Fix roles in the cloud database"""
    try:
        # Create app with production config
        app = create_app('production')
        
        with app.app_context():
            print("=== FIXING CLOUD ROLES ===")
            
            # Check existing roles
            existing_roles = Role.query.all()
            print(f"Found {len(existing_roles)} existing roles:")
            for role in existing_roles:
                print(f"- ID: {role.id}, Name: '{role.name}'")
            
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
            
            # Fix any role assignment issues
            print("\nChecking for role assignment issues...")
            
            # Get all user roles
            user_roles = UserRole.query.all()
            print(f"Found {len(user_roles)} user role assignments")
            
            # Check if there are any orphaned role assignments (role_id doesn't exist)
            orphaned_roles = []
            for user_role in user_roles:
                role = Role.query.get(user_role.role_id)
                if not role:
                    print(f"Found orphaned role assignment: User ID {user_role.user_id}, Role ID {user_role.role_id}")
                    orphaned_roles.append(user_role)
            
            if orphaned_roles:
                print(f"Removing {len(orphaned_roles)} orphaned role assignments")
                for orphaned_role in orphaned_roles:
                    db.session.delete(orphaned_role)
                db.session.commit()
            
            # Direct SQL query to check user roles
            result = db.session.execute(text("""
                SELECT u.id, u.username, r.id, r.name 
                FROM "user" u
                LEFT JOIN user_role ur ON u.id = ur.user_id
                LEFT JOIN role r ON ur.role_id = r.id
                ORDER BY u.username
            """))
            
            print("\nUser roles from direct SQL query:")
            for row in result:
                user_id, username, role_id, role_name = row
                print(f"- User: {username} (ID: {user_id}), Role: {role_name if role_name else 'None'} (ID: {role_id if role_id else 'None'})")
            
            print("\n=== ROLE FIX COMPLETED ===")
            return True
    except Exception as e:
        print(f"ERROR in fix_cloud_roles: {str(e)}")
        print(traceback.format_exc())
        return False

if __name__ == "__main__":
    try:
        success = fix_cloud_roles()
        if success:
            print("Cloud roles fix completed successfully")
            sys.exit(0)
        else:
            print("Cloud roles fix failed")
            sys.exit(1)
    except Exception as e:
        print(f"Unhandled error in cloud_role_fix.py: {e}")
        print(traceback.format_exc())
        sys.exit(1)
