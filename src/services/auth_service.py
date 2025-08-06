from functools import wraps
from flask import jsonify, current_app
from flask_jwt_extended import get_jwt_identity, verify_jwt_in_request
from src.models.user import User
from src.models.pharmacy import Pharmacy

class AuthService:
    """Authentication and authorization service"""
    
    @staticmethod
    def get_current_user():
        """Get current authenticated user"""
        try:
            verify_jwt_in_request()
            current_identity = get_jwt_identity()
            
            if not current_identity:
                return None
            
            user_id = current_identity.get('id')
            user_type = current_identity.get('type')
            
            if user_type == 'user':
                return User.query.get(user_id)
            elif user_type == 'pharmacy':
                return Pharmacy.query.get(user_id)
            
            return None
        except:
            return None
    
    @staticmethod
    def get_current_identity():
        """Get current JWT identity"""
        try:
            verify_jwt_in_request()
            return get_jwt_identity()
        except:
            return None
    
    @staticmethod
    def require_auth(user_types=None):
        """Decorator to require authentication"""
        def decorator(f):
            @wraps(f)
            def decorated_function(*args, **kwargs):
                try:
                    verify_jwt_in_request()
                    current_identity = get_jwt_identity()
                    
                    if not current_identity:
                        return jsonify({
                            'success': False,
                            'message': 'Authentication required',
                            'message_ar': 'المصادقة مطلوبة'
                        }), 401
                    
                    user_type = current_identity.get('type')
                    
                    # Check user type if specified
                    if user_types and user_type not in user_types:
                        return jsonify({
                            'success': False,
                            'message': 'Access denied',
                            'message_ar': 'الوصول مرفوض'
                        }), 403
                    
                    return f(*args, **kwargs)
                    
                except Exception as e:
                    current_app.logger.error(f"Auth error: {str(e)}")
                    return jsonify({
                        'success': False,
                        'message': 'Authentication failed',
                        'message_ar': 'فشل في المصادقة'
                    }), 401
            
            return decorated_function
        return decorator
    
    @staticmethod
    def require_pharmacy():
        """Decorator to require pharmacy authentication"""
        return AuthService.require_auth(['pharmacy'])
    
    @staticmethod
    def require_user():
        """Decorator to require user authentication"""
        return AuthService.require_auth(['user'])
    
    @staticmethod
    def require_admin():
        """Decorator to require admin authentication"""
        return AuthService.require_auth(['admin'])
    
    @staticmethod
    def check_pharmacy_ownership(pharmacy_id):
        """Check if current user owns the pharmacy"""
        current_identity = AuthService.get_current_identity()
        
        if not current_identity or current_identity.get('type') != 'pharmacy':
            return False
        
        return current_identity.get('id') == pharmacy_id
    
    @staticmethod
    def check_user_ownership(user_id):
        """Check if current user is the same user"""
        current_identity = AuthService.get_current_identity()
        
        if not current_identity or current_identity.get('type') != 'user':
            return False
        
        return current_identity.get('id') == user_id
    
    @staticmethod
    def check_resource_access(resource_type, resource_id, user_id=None, pharmacy_id=None):
        """Check if current user can access a resource"""
        current_identity = AuthService.get_current_identity()
        
        if not current_identity:
            return False
        
        current_user_type = current_identity.get('type')
        current_user_id = current_identity.get('id')
        
        # Admin can access everything
        if current_user_type == 'admin':
            return True
        
        # Check specific resource access
        if resource_type == 'product':
            # Users can view all products
            if current_user_type == 'user':
                return True
            # Pharmacies can only access their own products
            elif current_user_type == 'pharmacy':
                return pharmacy_id == current_user_id
        
        elif resource_type == 'order':
            # Users can only access their own orders
            if current_user_type == 'user':
                return user_id == current_user_id
            # Pharmacies can access orders for their products
            elif current_user_type == 'pharmacy':
                return pharmacy_id == current_user_id
        
        elif resource_type == 'conversation':
            # Users can access conversations they're part of
            if current_user_type == 'user':
                return user_id == current_user_id
            # Pharmacies can access conversations they're part of
            elif current_user_type == 'pharmacy':
                return pharmacy_id == current_user_id
        
        elif resource_type == 'review':
            # Users can access their own reviews
            if current_user_type == 'user':
                return user_id == current_user_id
            # Pharmacies can access reviews for their products
            elif current_user_type == 'pharmacy':
                return pharmacy_id == current_user_id
        
        return False
    
    @staticmethod
    def get_user_language():
        """Get current user's preferred language"""
        user = AuthService.get_current_user()
        if user:
            return getattr(user, 'preferred_language', 'ar')
        return 'ar'

