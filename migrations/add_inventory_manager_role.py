from extensions import db
from modules.auth.models import Role
from sqlalchemy import text

def run_migration():
    # Check if Inventory Manager role already exists
    inventory_manager_role = Role.query.filter_by(name='Inventory Manager').first()
    if not inventory_manager_role:
        # Create the Inventory Manager role
        inventory_manager_role = Role(name='Inventory Manager', description='Manages inventory and stock movements')
        db.session.add(inventory_manager_role)
        print("Created Inventory Manager role")
    
    # Check if Shop Manager role already exists
    shop_manager_role = Role.query.filter_by(name='Shop Manager').first()
    if not shop_manager_role:
        # Create the Shop Manager role
        shop_manager_role = Role(name='Shop Manager', description='Manages shop operations and approves inventory transfers')
        db.session.add(shop_manager_role)
        print("Created Shop Manager role")
    
    # Add the new columns to the stock_moves table if they don't exist
    try:
        # Check if columns exist
        db.session.execute(text("SELECT created_by_id FROM stock_moves LIMIT 1"))
        print("Column created_by_id already exists")
    except Exception:
        # Add the columns
        db.session.execute(text("""
        ALTER TABLE stock_moves 
        ADD COLUMN created_by_id INTEGER REFERENCES users(id),
        ADD COLUMN approved_by_id INTEGER REFERENCES users(id),
        ADD COLUMN approved_at DATETIME,
        ADD COLUMN notes TEXT,
        ADD COLUMN approval_notes TEXT
        """))
        print("Added approval workflow columns to stock_moves table")
    
    db.session.commit()
    print("Migration completed successfully")

if __name__ == "__main__":
    # This allows the script to be run directly for testing
    from app import create_app
    app = create_app()
    with app.app_context():
        run_migration()
