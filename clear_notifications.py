from app import create_app
from extensions import db
from modules.admin.models import Notification

def clear_all_notifications():
    """Clear all notifications from the database"""
    app = create_app()
    
    with app.app_context():
        try:
            # Count notifications before deletion
            count = Notification.query.count()
            
            # Delete all notifications
            Notification.query.delete()
            db.session.commit()
            
            print(f"Successfully deleted {count} notifications")
        except Exception as e:
            db.session.rollback()
            print(f"Error clearing notifications: {str(e)}")

if __name__ == "__main__":
    clear_all_notifications()
