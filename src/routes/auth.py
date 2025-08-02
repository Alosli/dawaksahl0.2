from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import create_access_token, create_refresh_token, jwt_required, get_jwt_identity
from werkzeug.security import generate_password_hash, check_password_hash
from marshmallow import ValidationError
from datetime import datetime, timedelta
import secrets
import uuid

from src.models import db
from src.models.user import User, UserAddress, UserMedicalInfo
from src.schemas.auth_schemas import (
    RegisterSchema, LoginSchema, ForgotPasswordSchema, 
    ResetPasswordSchema, ChangePasswordSchema, EmailVerificationSchema,
    ResendVerificationSchema
)
from src.utils.helpers import (
    hash_password, check_password, generate_token, 
    success_response, error_response, validate_json_request,
    get_current_user
)
from src.services.email_service import EmailService

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/register', methods=['POST'])
def register():
    """Register a new user with complete profile information."""
    try:
        # Validate request data
        schema = RegisterSchema()
        data = schema.load(request.json)
        
        # Check if user already exists
        existing_user = User.query.filter_by(email=data['email']).first()
        if existing_user:
            return error_response('User with this email already exists', 400)
        
        # Create user
        user = User(
            email=data['email'],
            password_hash=generate_password_hash(data['password']),
            user_type=data['user_type'],
            first_name=data['first_name'],
            last_name=data['last_name'],
            phone=data['phone'],
            date_of_birth=data.get('date_of_birth'),
            gender=data.get('gender'),
            national_id=data.get('national_id'),
            email_verification_token=secrets.token_urlsafe(32),
            email_verification_expires=datetime.utcnow() + timedelta(hours=24)
        )
        
        db.session.add(user)
        db.session.flush()  # Get user ID
        
        # Create user address with coordinates
        address = UserAddress(
            user_id=user.id,
            country=data.get('country', 'YE'),
            city=data['city'],
            district=data['district'],
            street=data['street'],
            building_number=data.get('building_number'),
            postal_code=data.get('postal_code'),
            floor_apartment=data.get('floor_apartment'),
            landmark=data.get('landmark'),
            special_delivery_instructions=data.get('special_delivery_instructions'),
            latitude=data.get('latitude'),  # Essential for distance calculation
            longitude=data.get('longitude'),  # Essential for distance calculation
            coordinates=data.get('coordinates'),  # Store full coordinates object
            formatted_address=data.get('formatted_address'),  # Google Maps formatted address
            is_default=True
        )
        
        db.session.add(address)
        
        # Create medical information for patients
        if data['user_type'] == 'patient':
            medical_info = UserMedicalInfo(
                user_id=user.id,
                blood_type=data.get('blood_type'),
                chronic_conditions=data.get('chronic_conditions'),
                allergies=data.get('allergies'),
                current_medications=data.get('current_medications'),
                emergency_contact_name=data.get('emergency_contact_name'),
                emergency_contact_phone=data.get('emergency_contact_phone'),
                emergency_contact_relation=data.get('emergency_contact_relation'),
                primary_doctor_name=data.get('primary_doctor_name'),
                primary_doctor_phone=data.get('primary_doctor_phone'),
                insurance_provider=data.get('insurance_provider'),
                insurance_number=data.get('insurance_number'),
                insurance_coverage_type=data.get('insurance_coverage_type'),
                preferred_language=data.get('preferred_language', 'ar'),
                delivery_time_preference=data.get('delivery_time_preference'),
                accessibility_needs=data.get('accessibility_needs'),
                communication_preferences=data.get('communication_preferences')
            )
            
            db.session.add(medical_info)
        
        # Commit all changes
        db.session.commit()
        
        # Send verification email
        try:
            email_service = EmailService()
            email_service.send_verification_email(user)
        except Exception as e:
            current_app.logger.error(f"Failed to send verification email: {e}")
            # Don't fail registration if email fails
        
        return success_response(
            {
                'user': user.to_dict(),
                'verification_required': True
            },
            "Registration successful. Please check your email for verification.",
            "تم التسجيل بنجاح. يرجى التحقق من بريدك الإلكتروني للتحقق.",
            201
        )
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Registration error: {e}")
        return error_response(
            "Registration failed. Please try again.",
            "فشل التسجيل. يرجى المحاولة مرة أخرى.",
            500
        )

@auth_bp.route('/login', methods=['POST'])
def login():
    """Login user and return JWT tokens."""
    try:
        schema = LoginSchema()
        data = schema.load(request.json)
        
        user = User.query.filter_by(email=data['email']).first()
        
        if not user or not check_password_hash(user.password_hash, data['password']):
            return error_response('Invalid email or password', 401)
        
        if not user.is_active:
            return error_response('Account is deactivated', 401)
        
        if not user.is_email_verified:
            return error_response('Please verify your email before logging in', 401)
        
        # Update last login
        user.last_login = datetime.utcnow()
        db.session.commit()
        
        # Create tokens
        access_token = create_access_token(identity=str(user.id))
        refresh_token = create_refresh_token(identity=str(user.id))
        
        return success_response({
            'message': 'Login successful',
            'user': user.to_dict(),
            'access_token': access_token,
            'refresh_token': refresh_token
        })
        
    except ValidationError as e:
        return error_response('Validation failed', 400, {'errors': e.messages})
    except Exception as e:
        current_app.logger.error(f"Login error: {str(e)}")
        return error_response('Login failed', 500)

@auth_bp.route('/verify-email', methods=['POST'])
def verify_email():
    """Verify user email with token."""
    try:
        schema = EmailVerificationSchema()
        data = schema.load(request.json)
        
        user = User.query.filter_by(email_verification_token=data['token']).first()
        
        if not user:
            return error_response('Invalid verification token', 400)
        
        if user.email_verification_expires < datetime.utcnow():
            return error_response('Verification token has expired', 400)
        
        if user.is_email_verified:
            return error_response('Email is already verified', 400)
        
        # Verify email
        user.is_email_verified = True
        user.email_verification_token = None
        user.email_verification_expires = None
        db.session.commit()
        
        return success_response({
            'message': 'Email verified successfully',
            'user': user.to_dict()
        })
        
    except ValidationError as e:
        return error_response('Validation failed', 400, {'errors': e.messages})
    except Exception as e:
        current_app.logger.error(f"Email verification error: {str(e)}")
        return error_response('Email verification failed', 500)

@auth_bp.route('/resend-verification', methods=['POST'])
def resend_verification():
    """Resend email verification."""
    try:
        schema = ResendVerificationSchema()
        data = schema.load(request.json)
        
        user = User.query.filter_by(email=data['email']).first()
        
        if not user:
            return error_response('User not found', 404)
        
        if user.is_email_verified:
            return error_response('Email is already verified', 400)
        
        # Generate new verification token
        user.email_verification_token = secrets.token_urlsafe(32)
        user.email_verification_expires = datetime.utcnow() + timedelta(hours=24)
        db.session.commit()
        
        # Send verification email
        try:
            send_verification_email(user.email, user.email_verification_token)
        except Exception as e:
            current_app.logger.error(f"Failed to send verification email: {str(e)}")
            return error_response('Failed to send verification email', 500)
        
        return success_response({
            'message': 'Verification email sent successfully'
        })
        
    except ValidationError as e:
        return error_response('Validation failed', 400, {'errors': e.messages})
    except Exception as e:
        current_app.logger.error(f"Resend verification error: {str(e)}")
        return error_response('Failed to resend verification email', 500)

@auth_bp.route('/forgot-password', methods=['POST'])
def forgot_password():
    """Send password reset email."""
    try:
        schema = ForgotPasswordSchema()
        data = schema.load(request.json)
        
        user = User.query.filter_by(email=data['email']).first()
        
        if not user:
            # Don't reveal if user exists
            return success_response({
                'message': 'If an account with this email exists, a password reset link has been sent.'
            })
        
        # Generate reset token
        user.password_reset_token = secrets.token_urlsafe(32)
        user.password_reset_expires = datetime.utcnow() + timedelta(hours=1)
        db.session.commit()
        
        # Send reset email
        try:
            email_service = EmailService()
            email_service.send_password_reset_email(user)
        except Exception as e:
            current_app.logger.error(f"Failed to send password reset email: {e}")
    
    # Always return success for security
    return success_response(
        None,
        "If the email exists, a password reset link has been sent",
        "إذا كان البريد الإلكتروني موجوداً، فقد تم إرسال رابط إعادة تعيين كلمة المرور"
    )

@auth_bp.route('/reset-password', methods=['POST'])
def reset_password():
    """Reset password with token."""
    try:
        schema = ResetPasswordSchema()
        data = schema.load(request.json)
        
        user = User.query.filter_by(password_reset_token=data['token']).first()
        
        if not user:
            return error_response('Invalid reset token', 400)
        
        if user.password_reset_expires < datetime.utcnow():
            return error_response('Reset token has expired', 400)
        
        # Reset password
        user.password_hash = generate_password_hash(data['password'])
        user.password_reset_token = None
        user.password_reset_expires = None
        db.session.commit()
        
        return success_response({
            'message': 'Password reset successfully'
        })
        
    except ValidationError as e:
        return error_response('Validation failed', 400, {'errors': e.messages})
    except Exception as e:
        current_app.logger.error(f"Password reset error: {str(e)}")
        return error_response('Password reset failed', 500)

@auth_bp.route('/change-password', methods=['POST'])
@jwt_required()
def change_password():
    """Change user password."""
    try:
        schema = ChangePasswordSchema()
        data = schema.load(request.json)
        
        user_id = get_jwt_identity()
        user = User.query.get(user_id)
        
        if not user:
            return error_response('User not found', 404)
        
        if not check_password_hash(user.password_hash, data['current_password']):
            return error_response('Current password is incorrect', 400)
        
        # Change password
        user.password_hash = generate_password_hash(data['new_password'])
        db.session.commit()
        
        return success_response({
            'message': 'Password changed successfully'
        })
        
    except ValidationError as e:
        return error_response('Validation failed', 400, {'errors': e.messages})
    except Exception as e:
        current_app.logger.error(f"Change password error: {str(e)}")
        return error_response('Password change failed', 500)

@auth_bp.route('/refresh', methods=['POST'])
@jwt_required(refresh=True)
def refresh():
    """Refresh access token."""
    try:
        user_id = get_jwt_identity()
        user = User.query.get(user_id)
        
        if not user or not user.is_active:
            return error_response('User not found or inactive', 404)
        
        access_token = create_access_token(identity=str(user.id))
        
        return success_response({
            'access_token': access_token
        })
        
    except Exception as e:
        current_app.logger.error(f"Token refresh error: {str(e)}")
        return error_response('Token refresh failed', 500)

@auth_bp.route('/me', methods=['GET'])
@jwt_required()
def get_current_user():
    """Get current user information."""
    try:
        user_id = get_jwt_identity()
        user = User.query.get(user_id)
        
        if not user:
            return error_response('User not found', 404)
        
        # Include address and medical info
        user_data = user.to_dict()
        
        # Add address information
        default_address = user.get_default_address()
        if default_address:
            user_data['address'] = default_address.to_dict()
        
        # Add medical information for patients
        if user.user_type == 'patient' and user.medical_info:
            user_data['medical_info'] = user.medical_info.to_dict()
        
        return success_response({
            'user': user_data
        })
        
    except Exception as e:
        current_app.logger.error(f"Get current user error: {str(e)}")
        return error_response('Failed to get user information', 500)

