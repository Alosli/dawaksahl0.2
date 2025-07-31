from datetime import datetime, timedelta
from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import (
    create_access_token, create_refresh_token, jwt_required, 
    get_jwt_identity, get_jwt
)
from marshmallow import ValidationError
import json

from src.models import db
from src.models.user import User, UserAddress, UserMedicalInfo
from src.models.pharmacy import Pharmacy
from src.schemas.auth_schemas import (
    LoginSchema, RegisterSchema, EmailVerificationSchema,
    ForgotPasswordSchema, ResetPasswordSchema, ChangePasswordSchema,
    RefreshTokenSchema, LoginResponseSchema, RegisterResponseSchema,
    MessageResponseSchema
)
from src.utils.helpers import (
    hash_password, check_password, generate_token, 
    success_response, error_response, validate_json_request,
    get_current_user
)
from src.services.email_service import EmailService

auth_bp = Blueprint('auth', __name__)

# Initialize schemas
login_schema = LoginSchema()
register_schema = RegisterSchema()
email_verification_schema = EmailVerificationSchema()
forgot_password_schema = ForgotPasswordSchema()
reset_password_schema = ResetPasswordSchema()
change_password_schema = ChangePasswordSchema()
refresh_token_schema = RefreshTokenSchema()

@auth_bp.route('/register', methods=['POST'])
def register():
    """Register a new user with multilingual support."""
    
    # Validate JSON request
    validation_error = validate_json_request()
    if validation_error:
        return validation_error
    
    try:
        # Validate request data
        data = register_schema.load(request.json)
    except ValidationError as err:
        return error_response(
            "Validation failed",
            "فشل في التحقق من صحة البيانات",
            400,
            err.messages
        )
    
    # Check if user already exists
    existing_user = User.query.filter_by(email=data['email']).first()
    if existing_user:
        return error_response(
            "Email address already exists",
            "عنوان البريد الإلكتروني موجود بالفعل",
            409
        )
    
    # Check phone number uniqueness
    if data.get('phone'):
        existing_phone = User.query.filter_by(phone=data['phone']).first()
        if existing_phone:
            return error_response(
                "Phone number already exists",
                "رقم الهاتف موجود بالفعل",
                409
            )
    
    # For pharmacy registration, check license uniqueness
    if data['user_type'] == 'pharmacy' and data.get('license_number'):
        existing_license = Pharmacy.query.filter_by(license_number=data['license_number']).first()
        if existing_license:
            return error_response(
                "License number already exists",
                "رقم الترخيص موجود بالفعل",
                409
            )
    
    try:
        # Create user
        user = User(
            email=data['email'],
            password_hash=hash_password(data['password']),
            user_type=data['user_type'],
            first_name=data['first_name'],
            last_name=data['last_name'],
            phone=data.get('phone'),
            date_of_birth=data.get('date_of_birth'),
            gender=data.get('gender'),
            email_verification_token=generate_token(),
            email_verification_expires=datetime.utcnow() + current_app.config['EMAIL_VERIFICATION_EXPIRES']
        )
        
        db.session.add(user)
        db.session.flush()  # Get user ID
        
        # Create address
        address = UserAddress(
            user_id=user.id,
            country=data.get('country', 'SA'),
            city=data['city'],
            district=data['district'],
            street=data['street'],
            building_number=data['building_number'],
            postal_code=data['postal_code'],
            is_default=True
        )
        db.session.add(address)
        
        # Create pharmacy profile if user is pharmacy
        if data['user_type'] == 'pharmacy':
            pharmacy = Pharmacy(
                user_id=user.id,
                pharmacy_name=data['pharmacy_name'],
                pharmacy_name_ar=data['pharmacy_name_ar'],
                license_number=data['license_number'],
                pharmacist_name=data['pharmacist_name'],
                pharmacist_license=data['pharmacist_license'],
                establishment_date=data['establishment_date'],
                phone=data.get('phone', user.phone),
                email=user.email,
                address=address.get_formatted_address(),
                city=data['city'],
                district=data['district'],
                postal_code=data['postal_code'],
                operating_hours=json.dumps(data.get('operating_hours', {})),
                services=json.dumps(data.get('services', []))
            )
            db.session.add(pharmacy)
        
        # Create medical info if user is patient
        elif data['user_type'] == 'patient':
            medical_info = UserMedicalInfo(
                user_id=user.id,
                chronic_conditions=json.dumps(data.get('chronic_conditions', [])),
                allergies=json.dumps(data.get('allergies', [])),
                current_medications=json.dumps(data.get('current_medications', [])),
                emergency_contact=data.get('emergency_contact'),
                insurance_provider=data.get('insurance_provider'),
                insurance_number=data.get('insurance_number'),
                blood_type=data.get('blood_type')
            )
            db.session.add(medical_info)
        
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
    """User login with multilingual support."""
    
    # Validate JSON request
    validation_error = validate_json_request()
    if validation_error:
        return validation_error
    
    try:
        # Validate request data
        data = login_schema.load(request.json)
    except ValidationError as err:
        return error_response(
            "Validation failed",
            "فشل في التحقق من صحة البيانات",
            400,
            err.messages
        )
    
    # Find user by email
    user = User.query.filter_by(email=data['email']).first()
    
    if not user or not check_password(data['password'], user.password_hash):
        return error_response(
            "Invalid email or password",
            "بريد إلكتروني أو كلمة مرور غير صحيحة",
            401
        )
    
    if not user.is_active:
        return error_response(
            "Account is deactivated",
            "الحساب معطل",
            401
        )
    
    # Create tokens
    access_token = create_access_token(
        identity=str(user.id),
        expires_delta=current_app.config['JWT_ACCESS_TOKEN_EXPIRES']
    )
    refresh_token = create_refresh_token(identity=str(user.id))
    
    # Update last login
    user.last_login = datetime.utcnow()
    db.session.commit()
    
    return success_response(
        {
            'access_token': access_token,
            'refresh_token': refresh_token,
            'user': user.to_dict(),
            'expires_in': int(current_app.config['JWT_ACCESS_TOKEN_EXPIRES'].total_seconds())
        },
        "Login successful",
        "تم تسجيل الدخول بنجاح"
    )

@auth_bp.route('/verify-email', methods=['POST'])
def verify_email():
    """Verify user email with token."""
    
    # Validate JSON request
    validation_error = validate_json_request()
    if validation_error:
        return validation_error
    
    try:
        # Validate request data
        data = email_verification_schema.load(request.json)
    except ValidationError as err:
        return error_response(
            "Validation failed",
            "فشل في التحقق من صحة البيانات",
            400,
            err.messages
        )
    
    # Find user by verification token
    user = User.query.filter_by(email_verification_token=data['token']).first()
    
    if not user:
        return error_response(
            "Invalid verification token",
            "رمز التحقق غير صحيح",
            400
        )
    
    if user.email_verification_expires < datetime.utcnow():
        return error_response(
            "Verification token has expired",
            "انتهت صلاحية رمز التحقق",
            400
        )
    
    # Verify email
    user.is_email_verified = True
    user.email_verification_token = None
    user.email_verification_expires = None
    db.session.commit()
    
    return success_response(
        None,
        "Email verified successfully",
        "تم التحقق من البريد الإلكتروني بنجاح"
    )

@auth_bp.route('/forgot-password', methods=['POST'])
def forgot_password():
    """Send password reset email."""
    
    # Validate JSON request
    validation_error = validate_json_request()
    if validation_error:
        return validation_error
    
    try:
        # Validate request data
        data = forgot_password_schema.load(request.json)
    except ValidationError as err:
        return error_response(
            "Validation failed",
            "فشل في التحقق من صحة البيانات",
            400,
            err.messages
        )
    
    # Find user by email
    user = User.query.filter_by(email=data['email']).first()
    
    if user and user.is_active:
        # Generate reset token
        user.password_reset_token = generate_token()
        user.password_reset_expires = datetime.utcnow() + current_app.config['PASSWORD_RESET_EXPIRES']
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
    
    # Validate JSON request
    validation_error = validate_json_request()
    if validation_error:
        return validation_error
    
    try:
        # Validate request data
        data = reset_password_schema.load(request.json)
    except ValidationError as err:
        return error_response(
            "Validation failed",
            "فشل في التحقق من صحة البيانات",
            400,
            err.messages
        )
    
    # Find user by reset token
    user = User.query.filter_by(password_reset_token=data['token']).first()
    
    if not user:
        return error_response(
            "Invalid reset token",
            "رمز إعادة التعيين غير صحيح",
            400
        )
    
    if user.password_reset_expires < datetime.utcnow():
        return error_response(
            "Reset token has expired",
            "انتهت صلاحية رمز إعادة التعيين",
            400
        )
    
    # Reset password
    user.password_hash = hash_password(data['new_password'])
    user.password_reset_token = None
    user.password_reset_expires = None
    db.session.commit()
    
    return success_response(
        None,
        "Password reset successfully",
        "تم إعادة تعيين كلمة المرور بنجاح"
    )

@auth_bp.route('/refresh-token', methods=['POST'])
@jwt_required(refresh=True)
def refresh_token():
    """Refresh access token."""
    
    current_user_id = get_jwt_identity()
    user = User.query.get(current_user_id)
    
    if not user or not user.is_active:
        return error_response(
            "User not found or inactive",
            "المستخدم غير موجود أو غير نشط",
            401
        )
    
    # Create new access token
    access_token = create_access_token(
        identity=str(user.id),
        expires_delta=current_app.config['JWT_ACCESS_TOKEN_EXPIRES']
    )
    
    return success_response(
        {
            'access_token': access_token,
            'expires_in': int(current_app.config['JWT_ACCESS_TOKEN_EXPIRES'].total_seconds())
        },
        "Token refreshed successfully",
        "تم تحديث الرمز المميز بنجاح"
    )

@auth_bp.route('/logout', methods=['POST'])
@jwt_required()
def logout():
    """Logout user (in a real app, you'd blacklist the token)."""
    
    # In a production app, you would add the token to a blacklist
    # For now, we'll just return success
    
    return success_response(
        None,
        "Logged out successfully",
        "تم تسجيل الخروج بنجاح"
    )

@auth_bp.route('/change-password', methods=['POST'])
@jwt_required()
def change_password():
    """Change user password."""
    
    # Validate JSON request
    validation_error = validate_json_request()
    if validation_error:
        return validation_error
    
    try:
        # Validate request data
        data = change_password_schema.load(request.json)
    except ValidationError as err:
        return error_response(
            "Validation failed",
            "فشل في التحقق من صحة البيانات",
            400,
            err.messages
        )
    
    user = get_current_user()
    
    # Verify current password
    if not check_password(data['current_password'], user.password_hash):
        return error_response(
            "Current password is incorrect",
            "كلمة المرور الحالية غير صحيحة",
            400
        )
    
    # Update password
    user.password_hash = hash_password(data['new_password'])
    db.session.commit()
    
    return success_response(
        None,
        "Password changed successfully",
        "تم تغيير كلمة المرور بنجاح"
    )

