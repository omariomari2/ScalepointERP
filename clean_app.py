"""
Clean version of the app.py file with only the necessary partial return functionality.
This removes all the automatic fixes that start when the app opens.
"""
import os
import sys
from flask import Flask, render_template, session, redirect, url_for, flash, request, jsonify, g
from flask_login import current_user, login_required
from config import config
from extensions import db, migrate, jwt, login_manager
from datetime import datetime, timedelta
import logging
from logging.handlers import RotatingFileHandler
import json

def create_app(config_name='default'):
    # Create and configure the app
    app = Flask(__name__)
    app.config.from_object(config[config_name])
    config[config_name].init_app(app)
    
    # Initialize extensions with app
    db.init_app(app)
    migrate.init_app(app, db)
    jwt.init_app(app)
    login_manager.init_app(app)
    
    # Set up logging
    if not app.debug and not app.testing:
        if not os.path.exists('logs'):
            os.mkdir('logs')
        file_handler = RotatingFileHandler('logs/erp.log', maxBytes=10240, backupCount=10)
        file_handler.setFormatter(logging.Formatter(
            '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'))
        file_handler.setLevel(logging.INFO)
        app.logger.addHandler(file_handler)
        app.logger.setLevel(logging.INFO)
        app.logger.info('ERP startup')
    
    # Register blueprints
    from modules.main import main as main_blueprint
    app.register_blueprint(main_blueprint)
    
    from modules.auth import auth as auth_blueprint
    app.register_blueprint(auth_blueprint, url_prefix='/auth')
    
    from modules.admin import admin as admin_blueprint
    app.register_blueprint(admin_blueprint, url_prefix='/admin')
    
    from modules.inventory import inventory as inventory_blueprint
    app.register_blueprint(inventory_blueprint, url_prefix='/inventory')
    
    from modules.pos import pos as pos_blueprint
    app.register_blueprint(pos_blueprint, url_prefix='/pos')
    
    from modules.sales import sales as sales_blueprint
    app.register_blueprint(sales_blueprint, url_prefix='/sales')
    
    from modules.purchases import purchases as purchases_blueprint
    app.register_blueprint(purchases_blueprint, url_prefix='/purchases')
    
    from modules.hr import hr as hr_blueprint
    app.register_blueprint(hr_blueprint, url_prefix='/hr')
    
    from modules.reports import reports as reports_blueprint
    app.register_blueprint(reports_blueprint, url_prefix='/reports')
    
    from modules.api import api as api_blueprint
    app.register_blueprint(api_blueprint, url_prefix='/api')
    
    # Register our new implementation of the partial return functionality
    try:
        from new_partial_return import register_blueprint
        if register_blueprint(app):
            print("New partial return functionality registered successfully")
        else:
            print("Failed to register new partial return functionality")
    except Exception as e:
        print(f"Error registering new partial return functionality: {str(e)}")
        import traceback
        traceback.print_exc()
    
    # Set up context processors
    @app.context_processor
    def inject_now():
        return {'now': datetime.utcnow()}
    
    @app.context_processor
    def inject_user_roles():
        if current_user.is_authenticated:
            return {'user_roles': [role.name for role in current_user.roles]}
        return {'user_roles': []}
    
    @app.context_processor
    def inject_notifications():
        if current_user.is_authenticated:
            from modules.main.models import Notification
            notifications = Notification.query.filter_by(user_id=current_user.id, read=False).order_by(Notification.created_at.desc()).limit(5).all()
            return {'notifications': notifications, 'notification_count': len(notifications)}
        return {'notifications': [], 'notification_count': 0}
    
    # Set up error handlers
    @app.errorhandler(404)
    def page_not_found(e):
        return render_template('404.html'), 404
    
    @app.errorhandler(500)
    def internal_server_error(e):
        return render_template('500.html'), 500
    
    # Set up before request handlers
    @app.before_request
    def before_request():
        g.start_time = datetime.utcnow()
        if current_user.is_authenticated:
            current_user.last_seen = datetime.utcnow()
            db.session.commit()
    
    # Set up after request handlers
    @app.after_request
    def after_request(response):
        if hasattr(g, 'start_time'):
            elapsed = datetime.utcnow() - g.start_time
            app.logger.debug(f"Request for {request.path} took {elapsed.total_seconds():.2f}s")
        return response
    
    # Set up jinja filters
    @app.template_filter('datetimeformat')
    def datetimeformat(value, format='%d/%m/%Y %H:%M'):
        if value:
            return value.strftime(format)
        return ""
    
    @app.template_filter('currency')
    def currency(value):
        if value:
            return f"GH₵{value:.2f}"
        return "GH₵0.00"
    
    # Set up routes
    @app.route('/events')
    def all_events():
        from modules.main.models import Event
        page = request.args.get('page', 1, type=int)
        pagination = Event.query.order_by(Event.timestamp.desc()).paginate(
            page=page, per_page=10, error_out=False)
        events = pagination.items
        return render_template('events.html', events=events, pagination=pagination)
    
    @app.route('/clear-events')
    def clear_events():
        if current_user.is_authenticated and current_user.has_role('Admin'):
            from modules.main.models import Event
            Event.query.delete()
            db.session.commit()
            flash('All events have been cleared.', 'success')
            
        return redirect(url_for('all_events'))
    
    return app

if __name__ == '__main__':
    app = create_app(os.getenv('FLASK_CONFIG') or 'default')
    
    # Run the application
    app.run(debug=True)
