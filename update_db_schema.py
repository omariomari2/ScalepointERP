from app import create_app, db
from sqlalchemy import text

app = create_app()

def update_warehouse_product_quantity_type():
    with app.app_context():
        # Create a backup of the current data
        print("Creating backup of warehouse_products data...")
        result = db.session.execute(text("SELECT id, product_id, warehouse_id, quantity, location_code, created_at, updated_at FROM warehouse_products"))
        products_data = result.fetchall()
        
        # Alter the table to change the quantity column type from FLOAT to INTEGER
        print("Updating quantity column type from FLOAT to INTEGER...")
        
        # SQLite doesn't support ALTER COLUMN directly, so we need to:
        # 1. Create a new table with the correct schema
        # 2. Copy the data
        # 3. Drop the old table
        # 4. Rename the new table
        
        # Create new table with correct schema
        db.session.execute(text("""
        CREATE TABLE warehouse_products_new (
            id INTEGER NOT NULL PRIMARY KEY,
            product_id INTEGER NOT NULL,
            warehouse_id INTEGER NOT NULL,
            quantity INTEGER NOT NULL DEFAULT 0,
            location_code VARCHAR(64),
            created_at DATETIME,
            updated_at DATETIME,
            FOREIGN KEY(product_id) REFERENCES products(id),
            FOREIGN KEY(warehouse_id) REFERENCES warehouses(id)
        )
        """))
        
        # Copy data, converting quantity to INTEGER
        for product in products_data:
            # Convert float quantity to integer
            quantity_int = int(product[3])
            db.session.execute(text(f"""
            INSERT INTO warehouse_products_new (id, product_id, warehouse_id, quantity, location_code, created_at, updated_at)
            VALUES ({product[0]}, {product[1]}, {product[2]}, {quantity_int}, '{product[4] or ''}', '{product[5] or ''}', '{product[6] or ''}')
            """))
        
        # Drop old table and rename new table
        db.session.execute(text("DROP TABLE warehouse_products"))
        db.session.execute(text("ALTER TABLE warehouse_products_new RENAME TO warehouse_products"))
        
        # Commit the changes
        db.session.commit()
        print("Database schema updated successfully!")

if __name__ == "__main__":
    update_warehouse_product_quantity_type()
