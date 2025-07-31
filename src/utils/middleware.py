from functools import wraps
from flask import request, jsonify, current_app, g
from flask_jwt_extended import verify_jwt_in_request, get_jwt_identity, get_jwt
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
import re
import bleach
from datetime import datetime

# Initialize rate limiter
limiter = Limiter(
    key_func=get_remote_address,
    default_limits=["1000 per hour"]
)

def security_headers(response):
    """Add security headers to all responses."""
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['X-Frame-Options'] = 'DENY'
    response.headers['X-XSS-Protection'] = '1; mode=block'
    response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
    response.headers['Content-Security-Policy'] = "default-src 'self'"
    response.headers['Referrer-Policy'] = 'strict-origin-when-cross-origin'
    return response

def validate_content_type(allowed_types=['application/json']):
    """Decorator to validate request content type."""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if request.method in ['POST', 'PUT', 'PATCH']:
                if request.content_type not in allowed_types:
                    return jsonify({
                        'success': False,
                        'message': 'Invalid content type',
                        'message_ar': 'نوع المحتوى غير صحيح'
                    }), 400
            return f(*args, **kwargs)
        return decorated_function
    return decorator

def sanitize_input(data):
    """Sanitize input data to prevent XSS attacks."""
    if isinstance(data, dict):
        return {key: sanitize_input(value) for key, value in data.items()}
    elif isinstance(data, list):
        return [sanitize_input(item) for item in data]
    elif isinstance(data, str):
        # Remove potentially dangerous HTML tags and attributes
        return bleach.clean(data, tags=[], attributes={}, strip=True)
    else:
        return data

def validate_input_length(max_length=1000):
    """Decorator to validate input length."""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if request.is_json and request.json:
                def check_length(obj, path=""):
                    if isinstance(obj, dict):
                        for key, value in obj.items():
                            check_length(value, f"{path}.{key}" if path else key)
                    elif isinstance(obj, list):
                        for i, item in enumerate(obj):
                            check_length(item, f"{path}[{i}]")
                    elif isinstance(obj, str) and len(obj) > max_length:
                        raise ValueError(f"Input too long at {path}: {len(obj)} > {max_length}")
                
                try:
                    check_length(request.json)
                except ValueError as e:
                    return jsonify({
                        'success': False,
                        'message': str(e),
                        'message_ar': 'المدخلات طويلة جداً'
                    }), 400
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator

def require_auth(f):
    """Decorator to require authentication."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        try:
            verify_jwt_in_request()
            current_user_id = get_jwt_identity()
            
            # Import here to avoid circular imports
            from src.models.user import User
            user = User.query.get(current_user_id)
            
            if not user or not user.is_active:
                return jsonify({
                    'success': False,
                    'message': 'User not found or inactive',
                    'message_ar': 'المستخدم غير موجود أو غير نشط'
                }), 401
            
            # Store user in Flask's g object for use in the request
            g.current_user = user
            
        except Exception as e:
            return jsonify({
                'success': False,
                'message': 'Authentication required',
                'message_ar': 'المصادقة مطلوبة'
            }), 401
        
        return f(*args, **kwargs)
    return decorated_function

def require_roles(allowed_roles):
    """Decorator to require specific user roles."""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            try:
                verify_jwt_in_request()
                current_user_id = get_jwt_identity()
                
                # Import here to avoid circular imports
                from src.models.user import User
                user = User.query.get(current_user_id)
                
                if not user or not user.is_active:
                    return jsonify({
                        'success': False,
                        'message': 'User not found or inactive',
                        'message_ar': 'المستخدم غير موجود أو غير نشط'
                    }), 401
                
                if user.user_type not in allowed_roles:
                    return jsonify({
                        'success': False,
                        'message': 'Insufficient permissions',
                        'message_ar': 'صلاحيات غير كافية'
                    }), 403
                
                # Store user in Flask's g object for use in the request
                g.current_user = user
                
            except Exception as e:
                return jsonify({
                    'success': False,
                    'message': 'Authentication required',
                    'message_ar': 'المصادقة مطلوبة'
                }), 401
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator

def require_email_verified(f):
    """Decorator to require email verification."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        try:
            verify_jwt_in_request()
            current_user_id = get_jwt_identity()
            
            # Import here to avoid circular imports
            from src.models.user import User
            user = User.query.get(current_user_id)
            
            if not user or not user.is_active:
                return jsonify({
                    'success': False,
                    'message': 'User not found or inactive',
                    'message_ar': 'المستخدم غير موجود أو غير نشط'
                }), 401
            
            if not user.is_email_verified:
                return jsonify({
                    'success': False,
                    'message': 'Email verification required',
                    'message_ar': 'التحقق من البريد الإلكتروني مطلوب'
                }), 403
            
            # Store user in Flask's g object for use in the request
            g.current_user = user
            
        except Exception as e:
            return jsonify({
                'success': False,
                'message': 'Authentication required',
                'message_ar': 'المصادقة مطلوبة'
            }), 401
        
        return f(*args, **kwargs)
    return decorated_function

def validate_file_upload(allowed_extensions=None, max_size=None):
    """Decorator to validate file uploads."""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not allowed_extensions:
                allowed_ext = current_app.config.get('ALLOWED_EXTENSIONS', set())
            else:
                allowed_ext = allowed_extensions
            
            if not max_size:
                max_file_size = current_app.config.get('MAX_CONTENT_LENGTH', 16 * 1024 * 1024)
            else:
                max_file_size = max_size
            
            # Check if files are in request
            if request.files:
                for file_key, file in request.files.items():
                    if file.filename == '':
                        continue
                    
                    # Check file extension
                    if '.' not in file.filename:
                        return jsonify({
                            'success': False,
                            'message': 'File must have an extension',
                            'message_ar': 'يجب أن يحتوي الملف على امتداد'
                        }), 400
                    
                    ext = file.filename.rsplit('.', 1)[1].lower()
                    if ext not in allowed_ext:
                        return jsonify({
                            'success': False,
                            'message': f'File type .{ext} not allowed',
                            'message_ar': f'نوع الملف .{ext} غير مسموح'
                        }), 400
                    
                    # Check file size (approximate)
                    file.seek(0, 2)  # Seek to end
                    file_size = file.tell()
                    file.seek(0)  # Reset to beginning
                    
                    if file_size > max_file_size:
                        return jsonify({
                            'success': False,
                            'message': 'File too large',
                            'message_ar': 'الملف كبير جداً'
                        }), 400
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator

def log_request(f):
    """Decorator to log requests."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Log request details
        current_app.logger.info(f"Request: {request.method} {request.url} from {request.remote_addr}")
        
        # Add request timestamp
        g.request_start_time = datetime.utcnow()
        
        try:
            response = f(*args, **kwargs)
            
            # Log response time
            if hasattr(g, 'request_start_time'):
                duration = (datetime.utcnow() - g.request_start_time).total_seconds()
                current_app.logger.info(f"Response time: {duration:.3f}s")
            
            return response
            
        except Exception as e:
            current_app.logger.error(f"Request failed: {str(e)}")
            raise
        
    return decorated_function

def validate_json_schema(schema):
    """Decorator to validate JSON request against a schema."""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not request.is_json:
                return jsonify({
                    'success': False,
                    'message': 'Request must be JSON',
                    'message_ar': 'يجب أن يكون الطلب بصيغة JSON'
                }), 400
            
            try:
                # Validate using marshmallow schema
                data = schema.load(request.json)
                # Store validated data in g for use in the view
                g.validated_data = data
            except Exception as e:
                return jsonify({
                    'success': False,
                    'message': 'Validation failed',
                    'message_ar': 'فشل في التحقق من صحة البيانات',
                    'errors': str(e)
                }), 400
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator

def rate_limit_by_user():
    """Rate limit by authenticated user ID instead of IP."""
    def get_user_id():
        try:
            verify_jwt_in_request(optional=True)
            user_id = get_jwt_identity()
            return user_id or get_remote_address()
        except:
            return get_remote_address()
    
    return get_user_id

def cors_preflight_response():
    """Handle CORS preflight requests."""
    response = jsonify({'status': 'OK'})
    response.headers.add('Access-Control-Allow-Origin', '*')
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization,Accept-Language')
    response.headers.add('Access-Control-Allow-Methods', 'GET,PUT,POST,DELETE,OPTIONS')
    return response

