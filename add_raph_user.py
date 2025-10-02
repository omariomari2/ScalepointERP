"""
Script to add the Raph user with Inventory Manager role to the database
This script is called from the docker-entrypoint.sh script
"""
import os
import sys
import bcrypt
from app import create_app, db
from modules.auth.models import User, Role, UserRole
from sqlalchemy import text

def add_raph_user():
    """Add Raph user with Inventory Manager role to the database"""
    print("Running add_raph_user script...")
    
    try:
        # Create app with production config to use cloud database
        app = create_app('production')
        
        with app.app_context():
            # Check if Raph user already exists
            raph_user = User.query.filter_by(username='Raph').first()
            
            if raph_user:
                print(f"User 'Raph' already exists (ID: {raph_user.id})")
            else:
                # Create Raph user with password 000000
                hashed_password = bcrypt.hashpw('000000'.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
                raph_user = User(
                    username='Raph',
                    first_name='Raphaelina',
                    last_name='Anie',
                    email='ralph@example.com',
                    password_hash=hashed_password,
                    is_active=True
                )
                db.session.add(raph_user)
                db.session.commit()
                print(f"Created user 'Raph' with ID: {raph_user.id}")
            
            # Check if Inventory Manager role exists (use case insensitive query)
            inventory_manager_role = Role.query.filter(Role.name.ilike('Inventory Manager')).first()
            
            if not inventory_manager_role:
                # Create Inventory Manager role
                inventory_manager_role = Role(
                    name='Inventory Manager',
                    description='Manages inventory transfers and stock movements'
                )
                db.session.add(inventory_manager_role)
                db.session.commit()
                print(f"Created 'Inventory Manager' role with ID: {inventory_manager_role.id}")
            else:
                print(f"'Inventory Manager' role already exists (ID: {inventory_manager_role.id})")
            
            # Check if Raph already has Inventory Manager role
            has_role = UserRole.query.filter_by(
                user_id=raph_user.id, 
                role_id=inventory_manager_role.id
            ).first()
            
            if has_role:
                print("User 'Raph' already has the Inventory Manager role")
            else:
                try:
                    # Assign Inventory Manager role to Raph
                    user_role = UserRole(user_id=raph_user.id, role_id=inventory_manager_role.id)
                    db.session.add(user_role)
                    db.session.commit()
                    print("Successfully assigned Inventory Manager role to user 'Raph'")
                except Exception as e:
                    print(f"Error adding role via ORM: {e}")
                    db.session.rollback()
                    
                    # Try direct SQL as fallback
                    try:
                        insert_sql = text("INSERT INTO user_role (user_id, role_id) VALUES (:user_id, :role_id)")
                        db.session.execute(insert_sql, {"user_id": raph_user.id, "role_id": inventory_manager_role.id})
                        db.session.commit()
                        print("Successfully assigned role using direct SQL")
                    except Exception as e2:
                        print(f"Error with direct SQL: {e2}")
                        db.session.rollback()
            
            # List all users and their roles
            print("\nVerifying all users and their roles:")
            result = db.session.execute(text("""
                SELECT u.username, r.name 
                FROM "user" u
                LEFT JOIN user_role ur ON u.id = ur.user_id
                LEFT JOIN role r ON ur.role_id = r.id
                ORDER BY u.username, r.name
            """))
            
            users = {}
            for username, role_name in result:
                if username not in users:
                    users[username] = []
                if role_name:
                    users[username].append(role_name)
            
            for username, roles in users.items():
                print(f"- {username}: {', '.join(roles) if roles else 'No roles'}")
            
            print("Add Raph user script completed successfully")
            
    except Exception as e:
        print(f"Error in add_raph_user script: {e}")
        sys.exit(1)

if __name__ == "__main__":
    add_raph_user() 