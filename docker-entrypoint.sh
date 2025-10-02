#!/bin/bash
set -e

echo "Initializing database connection..."
# Check if DATABASE_URL is set - used for Cloud SQL connection in GCP
if [ -z "$DATABASE_URL" ]; then
  echo "WARNING: DATABASE_URL environment variable not set. Using default SQLite connection."
  # We will rely on the application's default configuration
else
  echo "Using provided DATABASE_URL for database connection"
fi

# Initialize the database with more robust error handling
python -c "
from app import create_app, db
from modules.auth.models import User, Role, UserRole
from modules.inventory.models import Category, UnitOfMeasure, Product, Warehouse, StockLocation, StockMove, Inventory, InventoryLine
from modules.sales.models import Customer, SalesOrder, SalesOrderLine, Invoice, InvoiceLine, Payment
from modules.pos.models import POSSession, POSCashRegister, POSOrder, POSOrderLine, POSCategory, POSPaymentMethod, POSReturn, POSReturnLine, QualityCheck
from modules.purchase.models import Supplier, PurchaseOrder, PurchaseOrderLine, PurchaseReceipt, PurchaseReceiptLine, PurchaseInvoice, PurchaseInvoiceLine, PurchasePayment
from modules.employees.models import Department, JobPosition, Employee, LeaveType, LeaveAllocation, Attendance
from sqlalchemy import text
import sys

try:
    app = create_app('production')
    with app.app_context():
        print('Creating all tables if they do not exist...')
        db.create_all()
        
        print('Checking if database needs initialization...')
        try:
            user_count = User.query.count()
            if user_count == 0:
                print('Initializing database with minimal data...')
                from init_db import init_db_minimal
                init_db_minimal()
                print('Database initialized with minimal data (users and roles only)')
            else:
                print(f'Database already contains {user_count} users, skipping initialization')
        except Exception as e:
            print(f'Error checking users: {e}')
            print('Forcing database initialization with minimal data...')
            try:
                from init_db import init_db_minimal
                init_db_minimal()
                print('Database initialized with minimal data (users and roles only)')
            except Exception as e:
                print(f'Failed to initialize database: {e}')
        
        # Apply all migrations to ensure schema is up to date
        print('Applying migrations...')
        
        # PostgreSQL uses ALTER TABLE ADD COLUMN IF NOT EXISTS
        try:
            # Check if we're using PostgreSQL
            if 'postgresql' in db.engine.url.drivername:
                print('Detected PostgreSQL database, applying PostgreSQL-specific migrations')
                # Add exchange_processed column to pos_returns if it doesn't exist
                db.session.execute(text(\"\"\"
                    DO $$
                    BEGIN
                        IF NOT EXISTS (
                            SELECT FROM information_schema.columns 
                            WHERE table_name = 'pos_returns' AND column_name = 'exchange_processed'
                        ) THEN
                            ALTER TABLE pos_returns ADD COLUMN exchange_processed BOOLEAN DEFAULT FALSE;
                            RAISE NOTICE 'Added exchange_processed column';
                        END IF;
                    END $$;
                \"\"\"))
                db.session.commit()
                
                # Add original_order_line_id column to pos_return_lines if it doesn't exist
                db.session.execute(text(\"\"\"
                    DO $$
                    BEGIN
                        IF NOT EXISTS (
                            SELECT FROM information_schema.columns 
                            WHERE table_name = 'pos_return_lines' AND column_name = 'original_order_line_id'
                        ) THEN
                            ALTER TABLE pos_return_lines ADD COLUMN original_order_line_id INTEGER;
                            RAISE NOTICE 'Added original_order_line_id column';
                        END IF;
                    END $$;
                \"\"\"))
                db.session.commit()
                
                # Add product_name column to pos_return_lines if it doesn't exist
                db.session.execute(text(\"\"\"
                    DO $$
                    BEGIN
                        IF NOT EXISTS (
                            SELECT FROM information_schema.columns 
                            WHERE table_name = 'pos_return_lines' AND column_name = 'product_name'
                        ) THEN
                            ALTER TABLE pos_return_lines ADD COLUMN product_name TEXT;
                            RAISE NOTICE 'Added product_name column';
                        END IF;
                    END $$;
                \"\"\"))
                db.session.commit()
                
                # Add quantity column to quality_checks if it doesn't exist
                db.session.execute(text(\"\"\"
                    DO $$
                    BEGIN
                        IF NOT EXISTS (
                            SELECT FROM information_schema.columns 
                            WHERE table_name = 'quality_checks' AND column_name = 'quantity'
                        ) THEN
                            ALTER TABLE quality_checks ADD COLUMN quantity INTEGER DEFAULT 0;
                            RAISE NOTICE 'Added quantity column';
                        END IF;
                    END $$;
                \"\"\"))
                db.session.commit()
                
                # Note: Attendance migrations moved to a separate script
                # Run migrations/attendance_migration.py after deployment
                print('PostgreSQL migrations applied successfully')
            else:
                print('Detected SQLite database, applying SQLite-specific migrations')
                # SQLite migrations (as before)
                result = db.session.execute(text(\"PRAGMA table_info(pos_returns)\"))
                columns = [row[1] for row in result.fetchall()]
                if 'exchange_processed' not in columns:
                    print(\"Adding 'exchange_processed' column to pos_returns table...\")
                    db.session.execute(text(\"ALTER TABLE pos_returns ADD COLUMN exchange_processed BOOLEAN DEFAULT 0\"))
                    db.session.commit()
                    print(\"Column 'exchange_processed' added successfully!\")
                
                # Add original_order_line_id column to pos_return_lines if it doesn't exist
                result = db.session.execute(text(\"PRAGMA table_info(pos_return_lines)\"))
                columns = [row[1] for row in result.fetchall()]
                if 'original_order_line_id' not in columns:
                    print(\"Adding 'original_order_line_id' column to pos_return_lines table...\")
                    db.session.execute(text(\"ALTER TABLE pos_return_lines ADD COLUMN original_order_line_id INTEGER\"))
                    db.session.commit()
                    print(\"Column 'original_order_line_id' added successfully!\")
                
                # Add product_name column to pos_return_lines if it doesn't exist
                if 'product_name' not in columns:
                    print(\"Adding 'product_name' column to pos_return_lines table...\")
                    db.session.execute(text(\"ALTER TABLE pos_return_lines ADD COLUMN product_name TEXT\"))
                    db.session.commit()
                    print(\"Column 'product_name' added successfully!\")
                
                # Add quantity column to quality_checks if it doesn't exist
                result = db.session.execute(text(\"PRAGMA table_info(quality_checks)\"))
                columns = [row[1] for row in result.fetchall()]
                if 'quantity' not in columns:
                    print(\"Adding 'quantity' column to quality_checks table...\")
                    db.session.execute(text(\"ALTER TABLE quality_checks ADD COLUMN quantity INTEGER DEFAULT 0\"))
                    db.session.commit()
                    print(\"Column 'quantity' added successfully!\")
                
                print('SQLite migrations applied successfully')
        except Exception as e:
            print(f\"Error applying migrations: {e}\")
            # Continue despite migration errors - tables should still work
except Exception as e:
    print(f\"ERROR setting up database: {e}\")
    # Don't exit - container should still start
"

# Run the role fix script - use the new improved script
echo "Running inventory manager role fix script..."
python fix_inventory_manager_role.py || echo "WARNING: Role fix script failed, but continuing startup"

# Add Raph user with Inventory Manager role
echo "Adding Raph user with Inventory Manager role..."
python add_raph_user.py || echo "WARNING: Failed to add Raph user, but continuing startup"

# Fix return subtotals for existing returns
echo "Fixing return subtotals..."
python fix_return_subtotals.py || echo "WARNING: Failed to fix return subtotals, but continuing startup"

# List all users and their roles for debugging
echo "Listing all users and their roles for reference..."
python -c "
try:
    from fix_inventory_manager_role import list_all_users
    list_all_users()
except Exception as e:
    print(f'Error listing users: {e}')
"

echo "Startup completed successfully, launching application..."
# Execute the command passed to docker-entrypoint
exec "$@"
