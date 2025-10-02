# fix_returns_schema.py
# Script to ensure 'exchange_processed' column exists in the 'pos_returns' table for all likely SQLite databases in this ERP system.

import os
from sqlalchemy import create_engine, text, inspect

# List all likely database files
possible_dbs = [
    'instance/app.db',
    'instance/erp.db',
    'instance/erp_system.db',
    'erp.db',
    'erp_system.db',
    'odoo.db',
    'instance/dev.db',
]

for db_path in possible_dbs:
    if not os.path.exists(db_path):
        continue
    print(f"Checking {db_path}...")
    engine = create_engine(f'sqlite:///{db_path}')
    with engine.connect() as conn:
        inspector = inspect(engine)
        if 'pos_returns' not in inspector.get_table_names():
            print(f"Table 'pos_returns' does not exist in {db_path}.")
            continue
        columns = [col['name'] for col in inspector.get_columns('pos_returns')]
        if 'exchange_processed' not in columns:
            print("Adding 'exchange_processed' column to pos_returns table...")
            conn.execute(text("ALTER TABLE pos_returns ADD COLUMN exchange_processed BOOLEAN DEFAULT 0"))
            print("Column 'exchange_processed' added successfully!")
        else:
            print("Column 'exchange_processed' already exists in pos_returns table.")
print("Schema fix complete.")
