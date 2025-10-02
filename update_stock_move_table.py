from extensions import db
from app import create_app
from sqlalchemy import text

# Create the app
app = create_app()

# Add the missing columns to the stock_moves table
with app.app_context():
    # Check if the columns already exist
    with db.engine.connect() as conn:
        # Get the table info
        result = conn.execute(text("PRAGMA table_info(stock_moves)"))
        columns = [row[1] for row in result.fetchall()]
        
        # Add created_by_id column if it doesn't exist
        if 'created_by_id' not in columns:
            print("Adding created_by_id column to stock_moves table...")
            conn.execute(text("ALTER TABLE stock_moves ADD COLUMN created_by_id INTEGER REFERENCES users(id)"))
        else:
            print("created_by_id column already exists")
        
        # Add approved_by_id column if it doesn't exist
        if 'approved_by_id' not in columns:
            print("Adding approved_by_id column to stock_moves table...")
            conn.execute(text("ALTER TABLE stock_moves ADD COLUMN approved_by_id INTEGER REFERENCES users(id)"))
        else:
            print("approved_by_id column already exists")
        
        # Add approved_at column if it doesn't exist
        if 'approved_at' not in columns:
            print("Adding approved_at column to stock_moves table...")
            conn.execute(text("ALTER TABLE stock_moves ADD COLUMN approved_at DATETIME"))
        else:
            print("approved_at column already exists")
        
        # Add notes column if it doesn't exist
        if 'notes' not in columns:
            print("Adding notes column to stock_moves table...")
            conn.execute(text("ALTER TABLE stock_moves ADD COLUMN notes TEXT"))
        else:
            print("notes column already exists")
        
        # Add approval_notes column if it doesn't exist
        if 'approval_notes' not in columns:
            print("Adding approval_notes column to stock_moves table...")
            conn.execute(text("ALTER TABLE stock_moves ADD COLUMN approval_notes TEXT"))
        else:
            print("approval_notes column already exists")
        
        print("\nDatabase migration completed successfully!")
