import os
import uuid
import secrets
import hashlib
from datetime import datetime, timedelta
from functools import wraps
from flask import request, jsonify, current_app
from flask_jwt_extended import get_jwt_identity, verify_jwt_in_request
from werkzeug.utils import secure_filename
from PIL import Image

def create_upload_folders(app):
    """Create upload folders if they don't exist."""
    upload_folder = app.config['UPLOAD_FOLDER']
    folders = [
        'avatars',
        'prescriptions',
        'documents',
        'pharmacy_docs',
        'chat_files'
    ]
    
    for folder in folders:
        folder_path = os.path.join(upload_folder, folder)
        if not os.path.exists(folder_path):
            os.makedirs(folder_path)

def generate_uuid():
    """Generate a UUID string."""
    return str(uuid.uuid4())

def generate_token():
    """Generate a secure random token."""
    return secrets.token_urlsafe(32)

def generate_order_number():
    """Generate a unique order number."""
    timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
    random_part = secrets.token_hex(4).upper()
    return f"DWK{timestamp}{random_part}"

def allowed_file(filename, allowed_extensions=None):
    """Check if file extension is allowed."""
    if allowed_extensions is None:
        allowed_extensions = current_app.config['ALLOWED_EXTENSIONS']
    
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in allowed_extensions

def save_uploaded_file(file, folder, filename=None):
    """Save uploaded file and return the file path."""
    if not file or not allowed_file(file.filename):
        return None
    
    if filename is None:
        filename = secure_filename(file.filename)
        # Add UUID to prevent filename conflicts
        name, ext = os.path.splitext(filename)
        filename = f"{name}_{generate_uuid()[:8]}{ext}"
    
    upload_folder = current_app.config['UPLOAD_FOLDER']
    folder_path = os.path.join(upload_folder, folder)
    
    if not os.path.exists(folder_path):
        os.makedirs(folder_path)
    
    file_path = os.path.join(folder_path, filename)
    file.save(file_path)
    
    return os.path.join(folder, filename)

def save_avatar(file, user_id):
    """Save user avatar with resizing."""
    if not file or not allowed_file(file.filename, {'png', 'jpg', 'jpeg'}):
        return None
    
    # Generate filename
    ext = file.filename.rsplit('.', 1)[1].lower()
    filename = f"avatar_{user_id}.{ext}"
    
    upload_folder = current_app.config['UPLOAD_FOLDER']
    folder_path = os.path.join(upload_folder, 'avatars')
    
    if not os.path.exists(folder_path):
        os.makedirs(folder_path)
    
    file_path = os.path.join(folder_path, filename)
    
    # Resize image
    try:
        image = Image.open(file)
        image = image.resize((200, 200), Image.Resampling.LANCZOS)
        image.save(file_path, optimize=True, quality=85)
        return os.path.join('avatars', filename)
    except Exception as e:
        current_app.logger.error(f"Error saving avatar: {e}")
        return None

def hash_password(password):
    """Hash password using bcrypt."""
    import bcrypt
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

def check_password(password, hashed):
    """Check password against hash."""
    import bcrypt
    return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))

def paginate_query(query, page=1, per_page=20):
    """Paginate a SQLAlchemy query."""
    max_per_page = current_app.config.get('MAX_ITEMS_PER_PAGE', 100)
    per_page = min(per_page, max_per_page)
    
    total = query.count()
    items = query.offset((page - 1) * per_page).limit(per_page).all()
    
    return {
        'items': items,
        'total': total,
        'page': page,
        'per_page': per_page,
        'pages': (total + per_page - 1) // per_page,
        'has_prev': page > 1,
        'has_next': page * per_page < total
    }

def get_pagination_params():
    """Get pagination parameters from request."""
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', current_app.config.get('ITEMS_PER_PAGE', 20), type=int)
    return page, per_page

def success_response(data=None, message="Success", message_ar="نجح", status_code=200):
    """Create a success response."""
    response = {
        'success': True,
        'message': message,
        'message_ar': message_ar
    }
    
    if data is not None:
        response['data'] = data
    
    return jsonify(response), status_code

def error_response(message="Error occurred", message_ar="حدث خطأ", status_code=400, errors=None):
    """Create an error response."""
    response = {
        'success': False,
        'message': message,
        'message_ar': message_ar
    }
    
    if errors:
        response['errors'] = errors
    
    return jsonify(response), status_code

def validate_json_request():
    """Validate that request contains JSON data."""
    if not request.is_json:
        return error_response(
            "Request must contain JSON data",
            "يجب أن يحتوي الطلب على بيانات JSON",
            400
        )
    return None

def role_required(roles):
    """Decorator to require specific user roles."""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            verify_jwt_in_request()
            current_user_id = get_jwt_identity()
            
            # Import here to avoid circular imports
            from src.models.user import User
            user = User.query.get(current_user_id)
            
            if not user or user.user_type not in roles:
                return error_response(
                    "Insufficient permissions",
                    "صلاحيات غير كافية",
                    403
                )
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator

def get_current_user():
    """Get current authenticated user."""
    verify_jwt_in_request()
    current_user_id = get_jwt_identity()
    
    from src.models.user import User
    return User.query.get(current_user_id)

def calculate_distance(lat1, lon1, lat2, lon2):
    """Calculate distance between two coordinates in kilometers."""
    from math import radians, cos, sin, asin, sqrt
    
    # Convert decimal degrees to radians
    lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])
    
    # Haversine formula
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
    c = 2 * asin(sqrt(a))
    r = 6371  # Radius of earth in kilometers
    
    return c * r

def format_datetime(dt, format_str='%Y-%m-%d %H:%M:%S'):
    """Format datetime object to string."""
    if dt is None:
        return None
    return dt.strftime(format_str)

def parse_datetime(date_str, format_str='%Y-%m-%d %H:%M:%S'):
    """Parse datetime string to datetime object."""
    try:
        return datetime.strptime(date_str, format_str)
    except (ValueError, TypeError):
        return None

def is_valid_email(email):
    """Basic email validation."""
    import re
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None

def is_valid_phone(phone):
    """Basic phone validation for Saudi Arabia."""
    import re
    # Saudi phone number patterns
    patterns = [
        r'^(\+966|966|0)?5[0-9]{8}$',  # Mobile
        r'^(\+966|966|0)?1[0-9]{7}$',  # Landline
    ]
    
    for pattern in patterns:
        if re.match(pattern, phone):
            return True
    return False

def sanitize_filename(filename):
    """Sanitize filename for safe storage."""
    import re
    # Remove or replace unsafe characters
    filename = re.sub(r'[^\w\s-.]', '', filename)
    filename = re.sub(r'[-\s]+', '-', filename)
    return filename.strip('-.')

def generate_verification_code():
    """Generate 6-digit verification code."""
    return f"{secrets.randbelow(900000) + 100000}"

def mask_email(email):
    """Mask email for privacy (e.g., j***@example.com)."""
    if '@' not in email:
        return email
    
    local, domain = email.split('@', 1)
    if len(local) <= 2:
        masked_local = local
    else:
        masked_local = local[0] + '*' * (len(local) - 2) + local[-1]
    
    return f"{masked_local}@{domain}"

def mask_phone(phone):
    """Mask phone number for privacy."""
    if len(phone) <= 4:
        return phone
    
    return phone[:2] + '*' * (len(phone) - 4) + phone[-2:]

def create_response(success=True, message="", data=None, status_code=200):
    response = {
        "success": success,
        "message": message,
    }
    if data is not None:
        response["data"] = data
    return response, status_code

