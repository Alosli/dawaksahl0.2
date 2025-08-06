from flask import Blueprint

# Import all route blueprints
from .auth import auth_bp
from .users import users_bp
from .pharmacies import pharmacies_bp
from .products import products_bp
from .orders import orders_bp
from .chat import chat_bp
from .reviews import reviews_bp
from .notifications import notifications_bp
from .favorites import favorites_bp

def register_blueprints(app):
    """Register all blueprints with the Flask app"""
    
    # Authentication routes
    app.register_blueprint(auth_bp, url_prefix='/api/v1/auth')
    
    # User routes
    app.register_blueprint(users_bp, url_prefix='/api/v1/users')
    
    # Pharmacy routes
    app.register_blueprint(pharmacies_bp, url_prefix='/api/v1/pharmacies')
    
    # Product routes
    app.register_blueprint(products_bp, url_prefix='/api/v1')
    
    # Order routes
    app.register_blueprint(orders_bp, url_prefix='/api/v1/orders')
    
    # Chat routes
    app.register_blueprint(chat_bp, url_prefix='/api/v1/chat')
    
    # Review routes
    app.register_blueprint(reviews_bp, url_prefix='/api/v1/reviews')
    
    # Notification routes
    app.register_blueprint(notifications_bp, url_prefix='/api/v1/notifications')
    
    # Favorites routes
    app.register_blueprint(favorites_bp, url_prefix='/api/v1/favorites')

