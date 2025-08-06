from flask import Flask, jsonify
from flask_cors import CORS
from flask_jwt_extended import JWTManager
from datetime import timedelta
import os

from src.config import Config
from src.config import ProductionConfig as Config

def create_app(config_class=Config):
    """Application factory pattern"""
    app = Flask(__name__)
    app.config.from_object(config_class)
    
    # Initialize extensions
    db.init_app(app)
    migrate.init_app(app, db)
    
    # Configure CORS
    CORS(app, 
         origins=app.config['CORS_ORIGINS'],
         allow_headers=["Content-Type", "Authorization"],
         methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
         supports_credentials=True)
    
    # Configure JWT
    jwt = JWTManager(app)
    app.config['JWT_SECRET_KEY'] = app.config['SECRET_KEY']
    app.config['JWT_ACCESS_TOKEN_EXPIRES'] = timedelta(hours=24)
    app.config['JWT_REFRESH_TOKEN_EXPIRES'] = timedelta(days=30)
    
    # JWT error handlers
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
    
    # Register blueprints
    from src.routes.auth import auth_bp
    from src.routes.products import products_bp
    from src.routes.orders import orders_bp
    from src.routes.chat import chat_bp
    from src.routes.reviews import reviews_bp
    from src.routes.notifications import notifications_bp
    from src.routes.favorites import favorites_bp
    from src.routes.users import users_bp
    from src.routes.pharmacies import pharmacies_bp
    
    # API v1 routes
    app.register_blueprint(auth_bp, url_prefix='/api/v1/auth')
    app.register_blueprint(products_bp, url_prefix='/api/v1/products')
    app.register_blueprint(orders_bp, url_prefix='/api/v1/orders')
    app.register_blueprint(chat_bp, url_prefix='/api/v1/chat')
    app.register_blueprint(reviews_bp, url_prefix='/api/v1/reviews')
    app.register_blueprint(notifications_bp, url_prefix='/api/v1/notifications')
    app.register_blueprint(favorites_bp, url_prefix='/api/v1/favorites')
    app.register_blueprint(users_bp, url_prefix='/api/v1/users')
    app.register_blueprint(pharmacies_bp, url_prefix='/api/v1/pharmacies')
    
    # Health check endpoint
    @app.route('/health')
    def health_check():
        return jsonify({
            'status': 'healthy',
            'message': 'Dawaksahl API is running',
            'message_ar': 'واجهة برمجة تطبيقات دواكسهل تعمل',
            'version': '2.0.0'
        }), 200
    
    # API info endpoint
    @app.route('/api/v1')
    def api_info():
        return jsonify({
            'success': True,
            'message': 'Dawaksahl API v1',
            'message_ar': 'واجهة برمجة تطبيقات دواكسهل الإصدار 1',
            'version': '1.0.0',
            'endpoints': {
                'auth': '/api/v1/auth',
                'products': '/api/v1/products',
                'orders': '/api/v1/orders',
                'chat': '/api/v1/chat',
                'reviews': '/api/v1/reviews',
                'notifications': '/api/v1/notifications',
                'favorites': '/api/v1/favorites',
                'users': '/api/v1/users',
                'pharmacies': '/api/v1/pharmacies'
            }
        }), 200
    
    # Error handlers
    @app.errorhandler(404)
    def not_found(error):
        return jsonify({
            'success': False,
            'message': 'Endpoint not found',
            'message_ar': 'النقطة غير موجودة'
        }), 404
    
    @app.errorhandler(405)
    def method_not_allowed(error):
        return jsonify({
            'success': False,
            'message': 'Method not allowed',
            'message_ar': 'الطريقة غير مسموحة'
        }), 405
    
    @app.errorhandler(500)
    def internal_error(error):
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': 'Internal server error',
            'message_ar': 'خطأ داخلي في الخادم'
        }), 500
    
    # Create database tables
    with app.app_context():
        try:
            db.create_all()
            app.logger.info("Database tables created successfully")
        except Exception as e:
            app.logger.error(f"Failed to create database tables: {str(e)}")
    
    return app

# Create app instance
app = create_app()

if __name__ == '__main__':
    # Development server
    app.run(
        host='0.0.0.0',
        port=int(os.environ.get('PORT', 5000)),
        debug=app.config['DEBUG']
    )
