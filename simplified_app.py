"""
Simplified version of the app.py file that keeps only the new_partial_return functionality
and removes the other automatic fixes.
"""
import os
import sys
from flask import Flask, render_template, redirect, url_for, flash, request, jsonify, session, g
from flask_login import current_user, login_required
from config import config
from extensions import db, migrate, jwt, login_manager
from datetime import datetime
import traceback

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
    
    # Set up before request handler to prepare greeting data
    @app.before_request
    def before_request():
        g.start_time = datetime.utcnow()
        
        hour = datetime.now().hour
        if hour < 12:
            g.greeting = "Good morning"
        elif hour < 18:
            g.greeting = "Good afternoon"
        else:
            g.greeting = "Good evening"
    
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
    
    # Set up error handlers
    @app.errorhandler(404)
    def page_not_found(e):
        return render_template('404.html'), 404
    
    @app.errorhandler(500)
    def internal_server_error(e):
        return render_template('500.html'), 500
    
    # Set up template filters
    @app.template_filter('currency')
    def currency_filter(value):
        if value is None:
            return "GH₵0.00"
        return f"GH₵{float(value):.2f}"
    
    @app.template_filter('date')
    def date_filter(value):
        if value is None:
            return ""
        return value.strftime('%d/%m/%Y')
    
    @app.template_filter('datetime')
    def datetime_filter(value):
        if value is None:
            return ""
        return value.strftime('%d/%m/%Y %H:%M')
    
    # Set up context processors
    @app.context_processor
    def utility_processor():
        def format_price(amount, currency="GH₵"):
            if amount is None:
                return f"{currency}0.00"
            return f"{currency}{amount:.2f}"
        
        def format_date(date):
            if date is None:
                return ""
            return date.strftime('%d/%m/%Y')
        
        def format_datetime(date):
            if date is None:
                return ""
            return date.strftime('%d/%m/%Y %H:%M')
        
        return dict(
            format_price=format_price,
            format_date=format_date,
            format_datetime=format_datetime
        )
    
    # Event routes
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
    
    # Register our new implementation of the partial return functionality
    try:
        from new_partial_return import register_blueprint
        if register_blueprint(app):
            print("New partial return functionality registered successfully")
        else:
            print("Failed to register new partial return functionality")
    except Exception as e:
        print(f"Error registering new partial return functionality: {str(e)}")
        traceback.print_exc()
    
    # Run the application
    app.run(debug=True)
