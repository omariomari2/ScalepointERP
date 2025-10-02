from app import create_app, db
from modules.auth.models import User, Role, UserRole

def fix_roles():
    app = create_app()
    with app.app_context():
        # Find the user 'bright'
        bright_user = User.query.filter_by(username='bright').first()
        if not bright_user:
            print("User 'bright' not found")
            return
            
        # Find the Shop Manager role
        shop_manager_role = Role.query.filter_by(name='Shop Manager').first()
        if not shop_manager_role:
            print("Role 'Shop Manager' not found")
            return
            
        # Check if the user already has this role
        existing_role = UserRole.query.filter_by(user_id=bright_user.id, role_id=shop_manager_role.id).first()
        if existing_role:
            print(f"User '{bright_user.username}' already has the role '{shop_manager_role.name}'")
        else:
            # Assign the role to the user
            new_user_role = UserRole(user_id=bright_user.id, role_id=shop_manager_role.id)
            db.session.add(new_user_role)
            db.session.commit()
            print(f"Successfully assigned role '{shop_manager_role.name}' to user '{bright_user.username}'")
            
        # Print all users and their roles for verification
        print("\nAll users and their roles:")
        users = User.query.all()
        for user in users:
            roles = [role.name for role in user.roles]
            print(f"User: {user.username}, Roles: {roles if roles else 'No roles'}")

if __name__ == "__main__":
    fix_roles()
