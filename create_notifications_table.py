from app import create_app, db
from modules.admin.models import Notification

# Create app context
app = create_app()

with app.app_context():
    # Create the notifications table
    print("Creating notifications table...")
    # Create only the notifications table without affecting other tables
    inspector = db.inspect(db.engine)
    if 'notifications' not in inspector.get_table_names():
        Notification.__table__.create(db.engine)
        print("Notifications table created successfully!")
    else:
        print("Notifications table already exists.")
