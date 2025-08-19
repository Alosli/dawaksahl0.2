"""
Authentication utilities for DawakSahl backend
Provides decorators for role-based access control
"""

from functools import wraps
from flask import jsonify, request
from flask_jwt_extended import jwt_required, get_jwt_identity
from src.models.user import User
from src.models.pharmacy import Pharmacy
from src.models.doctor import Doctor


def token_required(f):
    """
    Basic JWT token requirement decorator
    """
    @wraps(f)
    @jwt_required()
    def decorated(*args, **kwargs):
        return f(*args, **kwargs)
    return decorated


def user_required(f):
    """
    Decorator to require user authentication (patients/users only)
    """
    @wraps(f)
    @jwt_required()
    def decorated(*args, **kwargs):
        try:
            current_user_identity = get_jwt_identity()
            
            # Extract user ID from the identity object
            if isinstance(current_user_identity, dict):
                current_user_id = current_user_identity.get('id')
                user_type = current_user_identity.get('type')
            else:
                current_user_id = current_user_identity
                user_type = None
            
            # Check if it's a user/patient
            user = User.query.filter_by(id=current_user_id).first()
            
            if not user:
                return jsonify({
                    'success': False,
                    'message': 'User authentication required',
                    'message_ar': 'مطلوب تسجيل دخول المستخدم'
                }), 401
            
            # Verify user type
            if user_type and user_type != 'user':
                return jsonify({
                    'success': False,
                    'message': 'User access required',
                    'message_ar': 'مطلوب وصول المستخدم'
                }), 403
            
            # Add user to kwargs for easy access in the route
            kwargs['current_user'] = user
            
            return f(*args, **kwargs)
            
        except Exception as e:
            print(f"❌ Authentication error: {str(e)}")
            return jsonify({
                'success': False,
                'message': 'Authentication failed',
                'message_ar': 'فشل في المصادقة'
            }), 401
    
    return decorated



def pharmacy_required(f):
    """
    Decorator to require pharmacy authentication
    """
    @wraps(f)
    @jwt_required()
    def decorated(*args, **kwargs):
        try:
            current_user_id = get_jwt_identity()
            
            # Check if it's a pharmacy
            pharmacy = Pharmacy.query.filter_by(id=current_user_id).first()
            
            if not pharmacy:
                return jsonify({
                    'success': False,
                    'message': 'Pharmacy authentication required',
                    'message_ar': 'مطلوب تسجيل دخول الصيدلية'
                }), 401
            
            # Add pharmacy to kwargs for easy access in the route
            kwargs['current_pharmacy'] = pharmacy
            
            return f(*args, **kwargs)
            
        except Exception as e:
            return jsonify({
                'success': False,
                'message': 'Authentication failed',
                'message_ar': 'فشل في المصادقة'
            }), 401
    
    return decorated


def doctor_required(f):
    """
    Decorator to require doctor authentication
    """
    @wraps(f)
    @jwt_required()
    def decorated(*args, **kwargs):
        try:
            current_user_id = get_jwt_identity()
            
            # Check if it's a doctor
            doctor = Doctor.query.filter_by(id=current_user_id).first()
            
            if not doctor:
                return jsonify({
                    'success': False,
                    'message': 'Doctor authentication required',
                    'message_ar': 'مطلوب تسجيل دخول الطبيب'
                }), 401
            
            # Add doctor to kwargs for easy access in the route
            kwargs['current_doctor'] = doctor
            
            return f(*args, **kwargs)
            
        except Exception as e:
            return jsonify({
                'success': False,
                'message': 'Authentication failed',
                'message_ar': 'فشل في المصادقة'
            }), 401
    
    return decorated


def admin_required(f):
    """
    Decorator to require admin authentication
    """
    @wraps(f)
    @jwt_required()
    def decorated(*args, **kwargs):
        try:
            current_user_id = get_jwt_identity()
            
            # Check if it's an admin user
            user = User.query.filter_by(id=current_user_id).first()
            
            if not user or not getattr(user, 'is_admin', False):
                return jsonify({
                    'success': False,
                    'message': 'Admin authentication required',
                    'message_ar': 'مطلوب تسجيل دخول المدير'
                }), 403
            
            # Add user to kwargs for easy access in the route
            kwargs['current_admin'] = user
            
            return f(*args, **kwargs)
            
        except Exception as e:
            return jsonify({
                'success': False,
                'message': 'Authentication failed',
                'message_ar': 'فشل في المصادقة'
            }), 401
    
    return decorated


def role_required(*allowed_roles):
    """
    Decorator to require specific roles
    Usage: @role_required('user', 'pharmacy', 'doctor')
    """
    def decorator(f):
        @wraps(f)
        @jwt_required()
        def decorated(*args, **kwargs):
            try:
                current_user_id = get_jwt_identity()
                current_entity = None
                user_role = None
                
                # Check user
                user = User.query.filter_by(id=current_user_id).first()
                if user:
                    current_entity = user
                    user_role = 'user'
                
                # Check pharmacy
                if not current_entity:
                    pharmacy = Pharmacy.query.filter_by(id=current_user_id).first()
                    if pharmacy:
                        current_entity = pharmacy
                        user_role = 'pharmacy'
                
                # Check doctor
                if not current_entity:
                    doctor = Doctor.query.filter_by(id=current_user_id).first()
                    if doctor:
                        current_entity = doctor
                        user_role = 'doctor'
                
                if not current_entity or user_role not in allowed_roles:
                    return jsonify({
                        'success': False,
                        'message': f'Access denied. Required roles: {", ".join(allowed_roles)}',
                        'message_ar': f'تم رفض الوصول. الأدوار المطلوبة: {", ".join(allowed_roles)}'
                    }), 403
                
                # Add current entity and role to kwargs
                kwargs['current_entity'] = current_entity
                kwargs['user_role'] = user_role
                
                return f(*args, **kwargs)
                
            except Exception as e:
                return jsonify({
                    'success': False,
                    'message': 'Authentication failed',
                    'message_ar': 'فشل في المصادقة'
                }), 401
        
        return decorated
    return decorator


def get_current_user():
    """
    Helper function to get current authenticated user/pharmacy/doctor
    Returns tuple: (entity, role) or (None, None) if not authenticated
    """
    try:
        current_user_id = get_jwt_identity()
        
        if not current_user_id:
            return None, None
        
        # Check user
        user = User.query.filter_by(id=current_user_id).first()
        if user:
            return user, 'user'
        
        # Check pharmacy
        pharmacy = Pharmacy.query.filter_by(id=current_user_id).first()
        if pharmacy:
            return pharmacy, 'pharmacy'
        
        # Check doctor
        doctor = Doctor.query.filter_by(id=current_user_id).first()
        if doctor:
            return doctor, 'doctor'
        
        return None, None
        
    except Exception:
        return None, None


def verify_user_access(user_id):
    """
    Verify if current authenticated user can access specific user data
    """
    try:
        current_user_id = get_jwt_identity()
        
        # Users can only access their own data
        if str(current_user_id) != str(user_id):
            return False
        
        return True
        
    except Exception:
        return False


def verify_pharmacy_access(pharmacy_id):
    """
    Verify if current authenticated pharmacy can access specific pharmacy data
    """
    try:
        current_user_id = get_jwt_identity()
        
        # Pharmacies can only access their own data
        if str(current_user_id) != str(pharmacy_id):
            return False
        
        return True
        
    except Exception:
        return False


def verify_doctor_access(doctor_id):
    """
    Verify if current authenticated doctor can access specific doctor data
    """
    try:
        current_user_id = get_jwt_identity()
        
        # Doctors can only access their own data
        if str(current_user_id) != str(doctor_id):
            return False
        
        return True
        
    except Exception:
        return False


def get_user_permissions(user_role):
    """
    Get permissions based on user role
    """
    permissions = {
        'user': [
            'view_medications',
            'create_orders',
            'view_own_orders',
            'upload_prescriptions',
            'book_appointments',
            'view_own_appointments',
            'rate_pharmacies',
            'rate_doctors'
        ],
        'pharmacy': [
            'view_orders',
            'update_order_status',
            'manage_inventory',
            'view_analytics',
            'verify_prescriptions',
            'manage_pharmacy_profile'
        ],
        'doctor': [
            'view_appointments',
            'manage_appointments',
            'create_prescriptions',
            'view_patients',
            'manage_schedule',
            'view_medical_history',
            'manage_doctor_profile'
        ]
    }
    
    return permissions.get(user_role, [])


def has_permission(user_role, permission):
    """
    Check if user role has specific permission
    """
    user_permissions = get_user_permissions(user_role)
    return permission in user_permissions

