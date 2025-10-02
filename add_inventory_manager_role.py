from modules.auth.models import Role
from extensions import db
from app import create_app

if __name__ == '__main__':
    app = create_app()
    with app.app_context():
        role_name = 'Inventory Manager'
        existing = Role.query.filter_by(name=role_name).first()
        if not existing:
            role = Role(name=role_name, description='Manages inventory operations')
            db.session.add(role)
            db.session.commit()
            print(f'Role "{role_name}" added.')
        else:
            print(f'Role "{role_name}" already exists.')
