from app import create_app
from extensions import db
from modules.pos.models import POSReturnLine
from sqlalchemy import text

def add_product_name_column():
    """Add product_name column to pos_return_lines table and populate it from products"""
    print("Adding product_name column to pos_return_lines table...")
    
    # Check if the column already exists
    with db.engine.connect() as conn:
        result = conn.execute(text("PRAGMA table_info(pos_return_lines)"))
        columns = [row[1] for row in result.fetchall()]
        
        if 'product_name' in columns:
            print("Column product_name already exists in pos_return_lines table.")
            return
    
    # Add the column
    with db.engine.connect() as conn:
        conn.execute(text("ALTER TABLE pos_return_lines ADD COLUMN product_name VARCHAR(255)"))
        print("Column product_name added to pos_return_lines table.")
    
    # Populate the column with product names from the products table
    print("Populating product_name column from products table...")
    
    # Get all return lines
    return_lines = POSReturnLine.query.all()
    updated_count = 0
    
    for line in return_lines:
        if line.product:
            line.product_name = line.product.name
            updated_count += 1
    
    db.session.commit()
    print(f"Updated {updated_count} return lines with product names.")
    
    # Update any remaining lines that don't have a product reference
    with db.engine.connect() as conn:
        conn.execute(text("""
            UPDATE pos_return_lines 
            SET product_name = 'Unknown Product (ID: ' || product_id || ')'
            WHERE product_name IS NULL
        """))
        
    print("Migration completed successfully.")

if __name__ == '__main__':
    app = create_app()
    with app.app_context():
        add_product_name_column()
