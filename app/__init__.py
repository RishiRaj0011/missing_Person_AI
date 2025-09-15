from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager
from flask_bcrypt import Bcrypt
from flask_moment import Moment
from flask_wtf.csrf import CSRFProtect
from celery import Celery
from config import Config

db = SQLAlchemy()
migrate = Migrate()
login = LoginManager()
bcrypt = Bcrypt()
moment = Moment()
csrf = CSRFProtect()


def make_celery(app):
    # Validate Celery configuration
    broker_url = app.config.get("CELERY_BROKER_URL")
    result_backend = app.config.get("CELERY_RESULT_BACKEND")
    
    if not broker_url or not result_backend:
        raise ValueError("Celery configuration missing: CELERY_BROKER_URL and CELERY_RESULT_BACKEND are required")
    
    celery = Celery(
        app.import_name,
        backend=result_backend,
        broker=broker_url,
    )
    celery.conf.update(app.config)
    return celery


def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    db.init_app(app)
    migrate.init_app(app, db)
    login.init_app(app)
    login.login_view = "main.login"
    login.login_message = "Please log in to access this page"
    bcrypt.init_app(app)
    moment.init_app(app)
    csrf.init_app(app)
    
    # Add security headers
    @app.after_request
    def add_security_headers(response):
        response.headers['X-Content-Type-Options'] = 'nosniff'
        response.headers['X-Frame-Options'] = 'DENY'
        response.headers['X-XSS-Protection'] = '1; mode=block'
        response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
        response.headers['Content-Security-Policy'] = "default-src 'self'; script-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net; style-src 'self' 'unsafe-inline' https://fonts.googleapis.com https://cdnjs.cloudflare.com https://cdn.jsdelivr.net; font-src 'self' https://fonts.gstatic.com https://cdnjs.cloudflare.com; img-src 'self' data:;"
        return response

    from app.routes import bp as main_bp
    from app.admin import admin_bp

    app.register_blueprint(main_bp)
    app.register_blueprint(admin_bp)
    
    # Context processors for global data
    @app.context_processor
    def inject_global_data():
        from flask_login import current_user
        from app.models import Announcement, Notification
        from datetime import datetime
        
        # Get active announcements
        active_announcement = Announcement.query.filter(
            Announcement.is_active == True,
            db.or_(
                Announcement.expires_at.is_(None),
                Announcement.expires_at > datetime.utcnow()
            )
        ).first()
        
        # Get unread notifications count for authenticated users
        unread_count = 0
        if current_user.is_authenticated:
            unread_count = current_user.unread_notifications_count
        
        return {
            'active_announcement': active_announcement,
            'unread_notifications_count': unread_count
        }

    return app


@login.user_loader
def load_user(user_id):
    from app.models import User
    
    try:
        return User.query.get(int(user_id))
    except (ValueError, TypeError):
        return None


from app import models
