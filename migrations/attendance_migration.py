"""
Standalone migration script for attendance features.
This can be run manually after deployment to add the necessary tables and columns.
"""

import sys
import os
import argparse

# Add the parent directory to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

# Create a minimal Flask application for migration
app = Flask(__name__)

# Parse command line arguments
parser = argparse.ArgumentParser(description='Run attendance migrations')
parser.add_argument('--db-url', dest='db_url', required=True,
                    help='Database URL (e.g., postgresql://user:pass@host/dbname)')
args = parser.parse_args()

# Configure the database
app.config['SQLALCHEMY_DATABASE_URI'] = args.db_url
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize the database
db = SQLAlchemy(app)

def run_postgres_migrations():
    """Run migrations for PostgreSQL database"""
    from sqlalchemy import text
    
    print("Running PostgreSQL migrations for attendance features...")
    
    with app.app_context():
        # Add last_edited_by column to attendances if it doesn't exist
        try:
            db.session.execute(text("""
                DO $$
                BEGIN
                    IF NOT EXISTS (
                        SELECT FROM information_schema.columns 
                        WHERE table_name = 'attendances' AND column_name = 'last_edited_by'
                    ) THEN
                        ALTER TABLE attendances ADD COLUMN last_edited_by INTEGER REFERENCES users(id);
                        RAISE NOTICE 'Added last_edited_by column to attendances';
                    END IF;
                END $$;
            """))
            db.session.commit()
            print("✅ Added last_edited_by column to attendances table (if needed)")
        except Exception as e:
            print(f"❌ Error adding last_edited_by column: {e}")
        
        # Create attendance_edits table if it doesn't exist
        try:
            db.session.execute(text("""
                DO $$
                BEGIN
                    CREATE TABLE IF NOT EXISTS attendance_edits (
                        id SERIAL PRIMARY KEY,
                        attendance_id INTEGER NOT NULL REFERENCES attendances(id),
                        editor_id INTEGER NOT NULL REFERENCES users(id),
                        edit_time TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                        previous_check_in TIMESTAMP,
                        previous_check_out TIMESTAMP,
                        previous_state VARCHAR(20),
                        previous_notes TEXT,
                        new_check_in TIMESTAMP,
                        new_check_out TIMESTAMP,
                        new_state VARCHAR(20),
                        new_notes TEXT,
                        edit_reason TEXT NOT NULL
                    );
                EXCEPTION WHEN duplicate_table THEN
                    NULL;
                END $$;
            """))
            db.session.commit()
            print("✅ Created attendance_edits table (if needed)")
        except Exception as e:
            print(f"❌ Error creating attendance_edits table: {e}")

def run_sqlite_migrations():
    """Run migrations for SQLite database"""
    from sqlalchemy import text
    
    print("Running SQLite migrations for attendance features...")
    
    with app.app_context():
        # Add last_edited_by column to attendances if it doesn't exist
        try:
            result = db.session.execute(text("PRAGMA table_info(attendances)"))
            columns = [row[1] for row in result.fetchall()]
            if 'last_edited_by' not in columns:
                db.session.execute(text("ALTER TABLE attendances ADD COLUMN last_edited_by INTEGER REFERENCES users(id)"))
                db.session.commit()
                print("✅ Added last_edited_by column to attendances table")
            else:
                print("✅ last_edited_by column already exists in attendances table")
        except Exception as e:
            print(f"❌ Error adding last_edited_by column: {e}")
        
        # Create attendance_edits table if it doesn't exist
        try:
            result = db.session.execute(text("SELECT name FROM sqlite_master WHERE type='table' AND name='attendance_edits'"))
            if not result.fetchone():
                db.session.execute(text("""
                CREATE TABLE attendance_edits (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    attendance_id INTEGER NOT NULL,
                    editor_id INTEGER NOT NULL,
                    edit_time TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    previous_check_in TIMESTAMP,
                    previous_check_out TIMESTAMP,
                    previous_state VARCHAR(20),
                    previous_notes TEXT,
                    new_check_in TIMESTAMP,
                    new_check_out TIMESTAMP,
                    new_state VARCHAR(20),
                    new_notes TEXT,
                    edit_reason TEXT NOT NULL,
                    FOREIGN KEY (attendance_id) REFERENCES attendances(id),
                    FOREIGN KEY (editor_id) REFERENCES users(id)
                );
                """))
                db.session.commit()
                print("✅ Created attendance_edits table")
            else:
                print("✅ attendance_edits table already exists")
        except Exception as e:
            print(f"❌ Error creating attendance_edits table: {e}")

if __name__ == '__main__':
    # Detect database type from URL
    if 'postgresql' in args.db_url.lower():
        run_postgres_migrations()
    else:
        run_sqlite_migrations()
    
    print("Migration completed!")
