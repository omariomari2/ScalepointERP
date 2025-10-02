import os
from app import create_app, db
from modules.core.models import Activity, Event

def create_activities_table():
    """Create the activities table if it doesn't exist"""
    app = create_app('development')
    with app.app_context():
        # Check if the table exists
        if not db.engine.dialect.has_table(db.engine, 'activities'):
            print("Creating activities table...")
            # Create only the activities table
            Activity.__table__.create(db.engine)
            print("Activities table created successfully!")
        else:
            print("Activities table already exists.")
            
        # Also check for events table
        if not db.engine.dialect.has_table(db.engine, 'events'):
            print("Creating events table...")
            Event.__table__.create(db.engine)
            print("Events table created successfully!")
        else:
            print("Events table already exists.")

if __name__ == '__main__':
    create_activities_table()
