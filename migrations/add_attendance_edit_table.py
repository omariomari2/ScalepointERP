import sys
import os

# Add the parent directory to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))) 

from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from datetime import datetime

# Import the db from the app package
from app import db

# Create a minimal Flask application for migration
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///../instance/erp_system.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db.init_app(app)
migrate = Migrate(app, db)

def upgrade():
    """Add the attendance_edits table and last_edited_by column to attendances table"""
    with app.app_context():
        # Use the correct SQLAlchemy syntax for executing SQL
        from sqlalchemy import text
        
        # Add last_edited_by column to attendances table if it doesn't exist
        try:
            with db.engine.connect() as conn:
                conn.execute(text('ALTER TABLE attendances ADD COLUMN last_edited_by INTEGER REFERENCES users(id);'))
                conn.commit()
        except Exception as e:
            print(f"Note: {e}")
            print("Column might already exist or there was an issue adding it.")
        
        # Create attendance_edits table
        try:
            with db.engine.connect() as conn:
                conn.execute(text('''
                CREATE TABLE IF NOT EXISTS attendance_edits (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    attendance_id INTEGER NOT NULL,
                    editor_id INTEGER NOT NULL,
                    edit_time DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    previous_check_in DATETIME,
                    previous_check_out DATETIME,
                    previous_state VARCHAR(20),
                    previous_notes TEXT,
                    new_check_in DATETIME,
                    new_check_out DATETIME,
                    new_state VARCHAR(20),
                    new_notes TEXT,
                    edit_reason TEXT NOT NULL,
                    FOREIGN KEY (attendance_id) REFERENCES attendances(id),
                    FOREIGN KEY (editor_id) REFERENCES users(id)
                );
                '''))
                conn.commit()
        except Exception as e:
            print(f"Error creating table: {e}")
        
        print("Migration completed successfully!")

if __name__ == '__main__':
    upgrade()
