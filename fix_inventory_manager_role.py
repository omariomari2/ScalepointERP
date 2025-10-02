"""
Script to fix the Inventory Manager role assignment issue
This script ensures the Inventory Manager role exists and can be assigned to users
It can be run locally or in the cloud environment
"""

from app import create_app
from extensions import db
from modules.auth.models import User, Role, UserRole
import sys
import traceback

def fix_inventory_manager_role(username=None):
    """
    Fix the Inventory Manager role and assign it to a specified user if provided
    
    Args:
        username: Optional username to assign the role to
    
    Returns:
        bool: True if successful, False otherwise
    """
    app = create_app()
    with app.app_context():
        try:
            print("=== CHECKING INVENTORY MANAGER ROLE ===")
            
            # 1. Check if Inventory Manager role exists
            inventory_manager_role = Role.query.filter(Role.name.ilike('Inventory Manager')).first()
            
            # 2. Create the role if it doesn't exist
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
                print(f"Inventory Manager role exists with ID: {inventory_manager_role.id}")
            
            # 3. If username provided, assign role to that user
            if username:
                user = User.query.filter_by(username=username).first()
                if not user:
                    print(f"Error: User '{username}' not found")
                    return False
                
                # Check if user already has the role
                has_role = False
                for role in user.roles:
                    if role.name.lower() == 'inventory manager':
                        has_role = True
                        break
                
                # Alternative check using UserRole directly
                user_role = UserRole.query.filter_by(
                    user_id=user.id, 
                    role_id=inventory_manager_role.id
                ).first()
                
                if user_role or has_role:
                    print(f"User '{username}' already has the Inventory Manager role")
                else:
                    print(f"Assigning Inventory Manager role to user '{username}'...")
                    new_user_role = UserRole(user_id=user.id, role_id=inventory_manager_role.id)
                    db.session.add(new_user_role)
                    db.session.commit()
                    print(f"Role assigned successfully!")
            
            # 4. List all roles for verification
            print("\nAll roles in the system:")
            all_roles = Role.query.all()
            for role in all_roles:
                print(f"- ID: {role.id}, Name: {role.name}")
            
            # 5. If username provided, verify their roles
            if username:
                user = User.query.filter_by(username=username).first()
                print(f"\nRoles for user '{username}':")
                for role in user.roles:
                    print(f"- {role.name}")
            
            print("\n=== INVENTORY MANAGER ROLE FIX COMPLETED ===")
            return True
            
        except Exception as e:
            print(f"ERROR: {str(e)}")
            print(traceback.format_exc())
            return False

def list_all_users():
    """List all users in the system and their roles"""
    app = create_app()
    with app.app_context():
        try:
            users = User.query.all()
            print(f"\nFound {len(users)} users in the system:")
            for user in users:
                role_names = [role.name for role in user.roles]
                print(f"- {user.username} (ID: {user.id}): Roles: {', '.join(role_names) if role_names else 'None'}")
            return True
        except Exception as e:
            print(f"ERROR listing users: {str(e)}")
            return False

if __name__ == "__main__":
    try:
        # Check command line arguments
        if len(sys.argv) > 1:
            username = sys.argv[1]
            success = fix_inventory_manager_role(username)
        elif len(sys.argv) == 1:
            # If no arguments, just check and create the role if needed
            success = fix_inventory_manager_role()
            print("\nTo assign the role to a user, run:")
            print("python fix_inventory_manager_role.py <username>")
            print("\nListing all users in the system...")
            list_all_users()
        
        if success:
            print("Inventory Manager role fix completed successfully")
            sys.exit(0)
        else:
            print("Inventory Manager role fix failed")
            sys.exit(1)
    except Exception as e:
        print(f"Unhandled error: {e}")
        print(traceback.format_exc())
        sys.exit(1) 