"""
Script to assign the Inventory Manager role to the Raph user in the cloud database
"""
import os
import sys
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

def assign_inventory_manager_role():
    # Cloud SQL PostgreSQL connection string
    db_url = "postgresql://erpuser:ERPuser2025!@/erpsystem?host=/cloudsql/erp-system-445701:us-central1:erp-database"
    
    try:
        # Create engine and session
        engine = create_engine(db_url)
        Session = sessionmaker(bind=engine)
        session = Session()
        
        print("Connected to cloud database")
        
        # First, check if the Inventory Manager role exists
        role_query = text("SELECT id, name FROM role WHERE name ILIKE 'Inventory Manager'")
        result = session.execute(role_query).fetchone()
        
        if not result:
            print("Inventory Manager role not found, creating it...")
            insert_role = text("INSERT INTO role (name, description) VALUES ('Inventory Manager', 'Manages inventory transfers and stock movements') RETURNING id")
            result = session.execute(insert_role).fetchone()
            session.commit()
            role_id = result[0]
            print(f"Created Inventory Manager role with ID: {role_id}")
        else:
            role_id = result[0]
            print(f"Found existing Inventory Manager role with ID: {role_id}")
        
        # Find the user ID for 'Raph'
        user_query = text("SELECT id, username FROM \"user\" WHERE username = 'Raph'")
        user_result = session.execute(user_query).fetchone()
        
        if not user_result:
            print("User 'Raph' not found in the database")
            return
        
        user_id = user_result[0]
        print(f"Found user 'Raph' with ID: {user_id}")
        
        # Check if the role is already assigned
        check_role = text("SELECT * FROM user_role WHERE user_id = :user_id AND role_id = :role_id")
        has_role = session.execute(check_role, {"user_id": user_id, "role_id": role_id}).fetchone()
        
        if has_role:
            print("User 'Raph' already has the Inventory Manager role")
        else:
            # Assign the Inventory Manager role to the user
            assign_role = text("INSERT INTO user_role (user_id, role_id) VALUES (:user_id, :role_id)")
            session.execute(assign_role, {"user_id": user_id, "role_id": role_id})
            session.commit()
            print("Successfully assigned Inventory Manager role to user 'Raph'")
        
        # List all users and their roles for verification
        print("\nListing all users and their roles:")
        users_roles_query = text("""
            SELECT u.username, r.name as role_name
            FROM "user" u
            LEFT JOIN user_role ur ON u.id = ur.user_id
            LEFT JOIN role r ON ur.role_id = r.id
            ORDER BY u.username, r.name
        """)
        
        results = session.execute(users_roles_query).fetchall()
        current_user = None
        for username, role_name in results:
            if current_user != username:
                print(f"\nUser: {username}")
                current_user = username
            print(f"  - Role: {role_name if role_name else 'No role'}")
        
        session.close()
        print("\nRole assignment complete")
    
    except Exception as e:
        print(f"Error assigning role: {e}")
        sys.exit(1)

if __name__ == "__main__":
    assign_inventory_manager_role() 