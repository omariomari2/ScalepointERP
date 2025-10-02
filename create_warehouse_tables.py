from app import create_app
from extensions import db
from modules.inventory.models_warehouse import WarehouseProduct, WarehouseMovement

app = create_app()

with app.app_context():
    # Create the warehouse tables
    db.create_all()
    print("Warehouse tables created successfully.")
