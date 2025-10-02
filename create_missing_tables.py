import os
from app import create_app, db
from modules.core.models import Activity, Event
from sqlalchemy import inspect

def create_missing_tables():
    """Create any missing tables in the database"""
    app = create_app('development')
    with app.app_context():
        # Create all tables - this will create tables that don't exist yet
        # but won't modify existing tables
        print("Creating missing tables...")
        db.create_all()
        
        # Verify if the tables were created
        inspector = inspect(db.engine)
        all_tables = inspector.get_table_names()
        
        if 'activities' in all_tables:
            print("Activities table exists!")
        else:
            print("Warning: Activities table was not created!")
            
        if 'events' in all_tables:
            print("Events table exists!")
        else:
            print("Warning: Events table was not created!")
            
        print("All tables in database:", all_tables)

if __name__ == '__main__':
    create_missing_tables()
