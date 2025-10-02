"""
WSGI configuration for deployment
"""

import sys
import os

# Add the app directory to the Python path
path = os.path.dirname(os.path.abspath(__file__))
if path not in sys.path:
    sys.path.append(path)

# Import the Flask app using the factory function
from app import create_app

# Create the application instance using production config
application = create_app('production')

# This is what gunicorn will use
if __name__ == "__main__":
    application.run()
