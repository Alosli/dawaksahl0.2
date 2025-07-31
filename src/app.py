import os
import logging
from flask import Flask, send_from_directory, jsonify
from flask_cors import CORS
from flask_jwt_extended import JWTManager
from flask_migrate import Migrate
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

from src.config import config
from src.models import db
from src.utils.helpers import create_upload_folders
from src.utils.error_handlers import register_error_handlers

# Initialize extensions
jwt = JWTManager()
migrate = Migrate()
limiter = Limiter(
    key_func=get_remote_address,
    default_limits=["200 per day", "50 per hour"]
)

def create_app(config_name=None):
    """Application factory pattern."""
    
    if config_name is None:
        config_name = os.environ.get('FLASK_ENV', 'development')
    
    app = Flask(__name__, static_folder=os.path.join(os.path.dirname(__file__), 'static'))
    
    # Load configuration
    app.config.from_object(config[config_name])
    
    # Initialize extensions
    db.init_app(app)
    jwt.init_app(app)
    migrate.init_app(app, db)
    limiter.init_app(app)
    
    # Configure CORS
    CORS(app, origins=app.config['CORS_ORIGINS'])
    
    # Create upload folders
    create_upload_folders(app)
    
    # Configure logging
    configure_logging(app)
    
    # Register error handlers
    register_error_handlers(app)
    
    # Register JWT handlers
    register_jwt_handlers(app, jwt)
    
    # Register blueprints
    register_blueprints(app)
    
    # Health check endpoint
    @app.route('/health')
    def health_check():
        return jsonify({
            'status': 'healthy',
            'app': app.config['APP_NAME'],
            'version': app.config['APP_VERSION']
        })
    
    # Serve frontend files
    @app.route('/', defaults={'path': ''})
    @app.route('/<path:path>')
    def serve_frontend(path):
        static_folder_path = app.static_folder
        if static_folder_path is None:
            return jsonify({'error': 'Static folder not configured'}), 404

        if path != "" and os.path.exists(os.path.join(static_folder_path, path)):
            return send_from_directory(static_folder_path, path)
        else:
            index_path = os.path.join(static_folder_path, 'index.html')
            if os.path.exists(index_path):
                return send_from_directory(static_folder_path, 'index.html')
            else:
                return jsonify({'error': 'Frontend not found'}), 404
    
    return app

def configure_logging(app):
    """Configure application logging."""
    if not app.debug and not app.testing:
        if not os.path.exists('logs'):
            os.mkdir('logs')
        
        file_handler = logging.FileHandler(f'logs/{app.config["LOG_FILE"]}')
        file_handler.setFormatter(logging.Formatter(
            '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
        ))
        file_handler.setLevel(getattr(logging, app.config['LOG_LEVEL']))
        app.logger.addHandler(file_handler)
        app.logger.setLevel(getattr(logging, app.config['LOG_LEVEL']))
        app.logger.info('DawakSahl API startup')

def register_jwt_handlers(app, jwt):
    """Register JWT event handlers."""
    
    # JWT blacklist (in production, use Redis)
    blacklisted_tokens = set()
    
    @jwt.token_in_blocklist_loader
    def check_if_token_revoked(jwt_header, jwt_payload):
        return jwt_payload['jti'] in blacklisted_tokens
    
    @jwt.revoked_token_loader
    def revoked_token_callback(jwt_header, jwt_payload):
        return jsonify({
            'success': False,
            'message': 'Token has been revoked',
            'message_ar': 'تم إلغاء الرمز المميز'
        }), 401
    
    @jwt.expired_token_loader
    def expired_token_callback(jwt_header, jwt_payload):
        return jsonify({
            'success': False,
            'message': 'Token has expired',
            'message_ar': 'انتهت صلاحية الرمز المميز'
        }), 401
    
    @jwt.invalid_token_loader
    def invalid_token_callback(error):
        return jsonify({
            'success': False,
            'message': 'Invalid token',
            'message_ar': 'رمز مميز غير صحيح'
        }), 401
    
    @jwt.unauthorized_loader
    def missing_token_callback(error):
        return jsonify({
            'success': False,
            'message': 'Authorization token is required',
            'message_ar': 'رمز التفويض مطلوب'
        }), 401

def register_blueprints(app):
    """Register application blueprints."""
    
    # Import blueprints
    from src.routes.auth import auth_bp
    from src.routes.users import users_bp
    from src.routes.medications import medications_bp
    from src.routes.pharmacies import pharmacies_bp
    from src.routes.prescriptions import prescriptions_bp
    from src.routes.orders import orders_bp
    from src.routes.chat import chat_bp
    from src.routes.notifications import notifications_bp
    from src.routes.reviews import reviews_bp
    from src.routes.search import search_bp
    from src.routes.upload import upload_bp
    
    # Register blueprints with API prefix
    api_prefix = app.config['API_PREFIX']
    
    app.register_blueprint(auth_bp, url_prefix=f'{api_prefix}/auth')
    app.register_blueprint(users_bp, url_prefix=f'{api_prefix}/users')
    app.register_blueprint(medications_bp, url_prefix=f'{api_prefix}/medications')
    app.register_blueprint(pharmacies_bp, url_prefix=f'{api_prefix}/pharmacies')
    app.register_blueprint(prescriptions_bp, url_prefix=f'{api_prefix}/prescriptions')
    app.register_blueprint(orders_bp, url_prefix=f'{api_prefix}/orders')
    app.register_blueprint(chat_bp, url_prefix=f'{api_prefix}/chat')
    app.register_blueprint(notifications_bp, url_prefix=f'{api_prefix}/notifications')
    app.register_blueprint(reviews_bp, url_prefix=f'{api_prefix}/reviews')
    app.register_blueprint(search_bp, url_prefix=f'{api_prefix}/search')
    app.register_blueprint(upload_bp, url_prefix=f'{api_prefix}/upload')

