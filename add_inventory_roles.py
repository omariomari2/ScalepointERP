from extensions import db
from modules.auth.models import Role

# Initialize the database connection
from app import create_app

# Define the roles to add
roles_to_add = [
    {
        'name': 'Inventory Manager',
        'description': 'Manages inventory transfers and stock movements'
    },
    {
        'name': 'Shop Manager',
        'description': 'Approves inventory transfers and manages shop operations'
    }
]

# Create the app
app = create_app()

# Add the roles if they don't exist
with app.app_context():
    for role_data in roles_to_add:
        role = Role.query.filter_by(name=role_data['name']).first()
        if not role:
            print(f"Creating new role: {role_data['name']}")
            role = Role(name=role_data['name'], description=role_data['description'])
            db.session.add(role)
        else:
            print(f"Role already exists: {role_data['name']}")
    
    # Commit the changes
    db.session.commit()
    
    # Verify all roles in the database
    all_roles = Role.query.all()
    print("\nAll roles in the database:")
    for role in all_roles:
        print(f"- {role.name}: {role.description}")
