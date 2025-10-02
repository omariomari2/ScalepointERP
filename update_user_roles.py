from extensions import db
from modules.auth.models import Role, UserRole, User
from app import create_app

# Create the app
app = create_app()

# Define the roles to ensure they exist
roles_to_ensure = [
    {
        'name': 'Inventory Manager',
        'description': 'Manages inventory transfers and stock movements'
    },
    {
        'name': 'Shop Manager',
        'description': 'Approves inventory transfers and manages shop operations'
    }
]

# Function to assign a role to a user
def assign_role_to_user(username, role_name):
    with app.app_context():
        user = User.query.filter_by(username=username).first()
        if not user:
            print(f"User '{username}' not found")
            return False
        
        role = Role.query.filter_by(name=role_name).first()
        if not role:
            print(f"Role '{role_name}' not found")
            return False
        
        # Check if user already has this role
        existing_role = UserRole.query.filter_by(user_id=user.id, role_id=role.id).first()
        if existing_role:
            print(f"User '{username}' already has role '{role_name}'")
            return True
        
        # Assign role to user
        user_role = UserRole(user_id=user.id, role_id=role.id)
        db.session.add(user_role)
        db.session.commit()
        print(f"Assigned role '{role_name}' to user '{username}'")
        return True

# Main execution
with app.app_context():
    # Ensure roles exist
    for role_data in roles_to_ensure:
        role = Role.query.filter_by(name=role_data['name']).first()
        if not role:
            print(f"Creating role: {role_data['name']}")
            role = Role(name=role_data['name'], description=role_data['description'])
            db.session.add(role)
            db.session.commit()
        else:
            print(f"Role already exists: {role_data['name']}")
    
    # List all available roles
    all_roles = Role.query.all()
    print("\nAvailable roles:")
    for role in all_roles:
        print(f"- {role.name}: {role.description}")
    
    # List all users
    all_users = User.query.all()
    print("\nAvailable users:")
    for user in all_users:
        print(f"- {user.username} (ID: {user.id})")
        print(f"  Roles: {', '.join([role.name for role in user.roles])}")
    
    # Prompt to assign roles
    print("\nTo assign a role to a user, enter the username and role name below.")
    print("Leave blank and press Enter to skip.")
    
    username = input("\nUsername: ")
    if username:
        role_name = input("Role name: ")
        if role_name:
            assign_role_to_user(username, role_name)
