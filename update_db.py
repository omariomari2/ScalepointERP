from app import create_app, db
from modules.inventory.models_restock import RestockRequest

app = create_app()
with app.app_context():
    db.create_all()
    print("Database schema updated successfully!")
