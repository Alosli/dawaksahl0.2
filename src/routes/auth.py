from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity
from marshmallow import ValidationError
from datetime import datetime, timedelta
from sqlalchemy.exc import IntegrityError
import secrets
import uuid

from src.models.user import db, User, UserAddress, UserMedicalInfo, PharmacyInfo
from src.schemas.auth_schemas import (
    PharmacyRegisterSchema, UserRegisterSchema, LoginSchema, 
    EmailVerificationSchema, PasswordResetRequestSchema, PasswordResetSchema
)
from src.services.email_service import EmailService
from src.utils.helpers import success_response, error_response, generate_token

auth_bp = Blueprint('auth', __name__, url_prefix='/api/v1/auth')

@auth_bp.route('/register', methods=['POST'])
def register():
    """Enhanced registration endpoint supporting both patients and pharmacies"""
    try:
        data = request.get_json()
        
        if not data:
            return error_response(
                'No data provided',
                'لم يتم توفير بيانات',
                400
            )
        
        user_type = data.get('user_type', 'patient')
        
        # Choose appropriate schema based on user type
        if user_type == 'pharmacy':
            schema = PharmacyRegisterSchema()
        else:
            schema = UserRegisterSchema()
        
        # Validate data
        try:
            validated_data = schema.load(data)
        except ValidationError as err:
            return error_response(
                'Validation failed',
                'فشل في التحقق من صحة البيانات',
                400,
                err.messages
            )
        
        # Check if user already exists
        existing_user = User.query.filter_by(email=validated_data['email']).first()
        if existing_user:
            return error_response(
                'User with this email already exists',
                'المستخدم بهذا البريد الإلكتروني موجود بالفعل',
                409
            )
        
        # Start database transaction
        try:
            # Create user
            user = User(
                email=validated_data['email'],
                user_type=validated_data['user_type'],
                first_name=validated_data['first_name'],
                last_name=validated_data['last_name'],
                phone=validated_data['phone'],
                email_verification_token=str(uuid.uuid4())
            )
            user.set_password(validated_data['password'])
            
            db.session.add(user)
            db.session.flush()  # Get user ID
            
            # Create address
            address = UserAddress(
                user_id=user.id,
                street=validated_data['street'],
                district=validated_data['district'],
                city=validated_data['city'],
                country=validated_data['country'],
                building_number=validated_data.get('building_number'),
                postal_code=validated_data.get('postal_code'),
                landmark=validated_data.get('landmark'),
                latitude=validated_data['latitude'],
                longitude=validated_data['longitude'],
                formatted_address=validated_data.get('formatted_address'),
                address_type='pharmacy' if user_type == 'pharmacy' else 'home',
                is_default=True
            )
            
            # Set coordinates
            if validated_data.get('coordinates'):
                address.set_coordinates(validated_data['coordinates'])
            else:
                address.set_coordinates([validated_data['latitude'], validated_data['longitude']])
            
            db.session.add(address)
            
            # Create user-specific information
            if user_type == 'pharmacy':
                # Create pharmacy info
                pharmacy_info = PharmacyInfo(
                    user_id=user.id,
                    pharmacy_name=validated_data['pharmacy_name'],
                    pharmacy_name_ar=validated_data.get('pharmacy_name_ar'),
                    license_number=validated_data['license_number'],
                    commercial_registration=validated_data.get('commercial_registration'),
                    tax_id=validated_data.get('tax_id'),
                    establishment_date=validated_data.get('establishment_date'),
                    pharmacy_type=validated_data.get('pharmacy_type'),
                    website=validated_data.get('website'),
                    pharmacist_name=validated_data['pharmacist_name'],
                    pharmacist_license=validated_data['pharmacist_license'],
                    pharmacist_phone=validated_data.get('pharmacist_phone'),
                    total_staff=validated_data.get('total_staff', 1),
                    is_24_hours=validated_data.get('is_24_hours', False),
                    has_delivery=validated_data.get('has_delivery', True),
                    delivery_radius=validated_data.get('delivery_radius', 5.0),
                    delivery_fee=validated_data.get('delivery_fee', 500.0),
                    has_cold_chain=validated_data.get('has_cold_chain', False),
                    has_compounding=validated_data.get('has_compounding', False),
                    has_controlled_substances=validated_data.get('has_controlled_substances', False),
                    accepts_insurance=validated_data.get('accepts_insurance', False)
                )
                
                # Set array fields
                pharmacy_info.set_array_field('languages_spoken', validated_data.get('languages_spoken', []))
                pharmacy_info.set_array_field('services', validated_data.get('services', []))
                pharmacy_info.set_array_field('specializations', validated_data.get('specializations', []))
                pharmacy_info.set_array_field('insurance_providers', validated_data.get('insurance_providers', []))
                
                # Set operating hours
                if validated_data.get('operating_hours'):
                    pharmacy_info.set_operating_hours(validated_data['operating_hours'])
                
                db.session.add(pharmacy_info)
                
            else:  # patient
                # Create medical info
                medical_info = UserMedicalInfo(
                    user_id=user.id,
                    date_of_birth=validated_data.get('date_of_birth'),
                    gender=validated_data.get('gender'),
                    blood_type=validated_data.get('blood_type'),
                    height=validated_data.get('height'),
                    weight=validated_data.get('weight'),
                    emergency_contact_name=validated_data.get('emergency_contact_name'),
                    emergency_contact_phone=validated_data.get('emergency_contact_phone'),
                    emergency_contact_relation=validated_data.get('emergency_contact_relation'),
                    insurance_provider=validated_data.get('insurance_provider'),
                    insurance_number=validated_data.get('insurance_number'),
                    insurance_expiry=validated_data.get('insurance_expiry'),
                    preferred_language=validated_data.get('preferred_language', 'ar'),
                    preferred_pharmacy_id=validated_data.get('preferred_pharmacy_id')
                )
                
                # Set medical array fields
                medical_info.set_array_field('chronic_conditions', validated_data.get('chronic_conditions'))
                medical_info.set_array_field('allergies', validated_data.get('allergies'))
                medical_info.set_array_field('current_medications', validated_data.get('current_medications'))
                medical_info.set_array_field('past_surgeries', validated_data.get('past_surgeries'))
                medical_info.set_array_field('family_medical_history', validated_data.get('family_medical_history'))
                
                db.session.add(medical_info)
            
            # Commit transaction
            db.session.commit()
            
            # Send verification email using EmailService
            try:
                email_service = EmailService()
                email_service.send_verification_email(user.email, user.email_verification_token)
            except Exception as e:
                current_app.logger.error(f"Failed to send verification email: {str(e)}")
                # Don't fail registration if email fails
            
            return success_response(
                data={
                    'user_id': user.id,
                    'email': user.email,
                    'user_type': user.user_type,
                    'verification_required': True
                },
                message=f'{user_type.title()} registered successfully. Please check your email for verification.',
                message_ar=f'تم تسجيل {user_type} بنجاح. يرجى التحقق من بريدك الإلكتروني للتحقق.',
                status_code=201
            )
            
        except IntegrityError as e:
            db.session.rollback()
            
            # Handle specific integrity errors
            if 'license_number' in str(e.orig):
                return error_response(
                    'A pharmacy with this license number already exists',
                    'صيدلية بهذا رقم الترخيص موجودة بالفعل',
                    409
                )
            else:
                return error_response(
                    'Registration failed due to duplicate data',
                    'فشل التسجيل بسبب بيانات مكررة',
                    409
                )
        
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Registration error: {str(e)}")
            return error_response(
                'Registration failed due to server error',
                'فشل التسجيل بسبب خطأ في الخادم',
                500
            )
    
    except Exception as e:
        current_app.logger.error(f"Registration endpoint error: {str(e)}")
        return error_response(
            'Internal server error',
            'خطأ داخلي في الخادم',
            500
        )

@auth_bp.route('/login', methods=['POST'])
def login():
    """User login endpoint"""
    try:
        schema = LoginSchema()
        data = schema.load(request.get_json())
        
        # Find user
        user = User.query.filter_by(email=data['email']).first()
        
        if not user or not user.check_password(data['password']):
            return error_response(
                'Invalid email or password',
                'بريد إلكتروني أو كلمة مرور غير صحيحة',
                401
            )
        
        if not user.is_active:
            return error_response(
                'Account is deactivated',
                'الحساب معطل',
                403
            )
        
        # Update last login
        user.last_login = datetime.utcnow()
        db.session.commit()
        
        # Generate JWT token
        access_token = create_access_token(identity=user.id)
        
        return success_response(
            data={
                'access_token': access_token,
                'user': user.to_dict(),
                'requires_verification': not user.is_verified
            },
            message='Login successful',
            message_ar='تم تسجيل الدخول بنجاح'
        )
        
    except ValidationError as err:
        return error_response(
            'Validation failed',
            'فشل في التحقق من صحة البيانات',
            400,
            err.messages
        )
    except Exception as e:
        current_app.logger.error(f"Login error: {str(e)}")
        return error_response(
            'Login failed',
            'فشل تسجيل الدخول',
            500
        )

@auth_bp.route('/verify-email', methods=['POST'])
def verify_email():
    """Email verification endpoint"""
    try:
        schema = EmailVerificationSchema()
        data = schema.load(request.get_json())
        
        # Find user by verification token
        user = User.query.filter_by(email_verification_token=data['token']).first()
        
        if not user:
            return error_response(
                'Invalid or expired verification token',
                'رمز التحقق غير صحيح أو منتهي الصلاحية',
                400
            )
        
        # Verify user
        user.is_verified = True
        user.email_verification_token = None
        db.session.commit()
        
        return success_response(
            data={'user': user.to_dict()},
            message='Email verified successfully',
            message_ar='تم التحقق من البريد الإلكتروني بنجاح'
        )
        
    except ValidationError as err:
        return error_response(
            'Validation failed',
            'فشل في التحقق من صحة البيانات',
            400,
            err.messages
        )
    except Exception as e:
        current_app.logger.error(f"Email verification error: {str(e)}")
        return error_response(
            'Email verification failed',
            'فشل التحقق من البريد الإلكتروني',
            500
        )

@auth_bp.route('/resend-verification', methods=['POST'])
def resend_verification():
    """Resend verification email"""
    try:
        data = request.get_json()
        email = data.get('email')
        
        if not email:
            return error_response(
                'Email is required',
                'البريد الإلكتروني مطلوب',
                400
            )
        
        user = User.query.filter_by(email=email).first()
        
        if not user:
            return error_response(
                'User not found',
                'المستخدم غير موجود',
                404
            )
        
        if user.is_verified:
            return error_response(
                'Email is already verified',
                'البريد الإلكتروني محقق بالفعل',
                400
            )
        
        # Generate new token if needed
        if not user.email_verification_token:
            user.email_verification_token = str(uuid.uuid4())
            db.session.commit()
        
        # Send verification email using EmailService
        try:
            email_service = EmailService()
            email_service.send_verification_email(user.email, user.email_verification_token)
        except Exception as e:
            current_app.logger.error(f"Failed to send verification email: {str(e)}")
            return error_response(
                'Failed to send verification email',
                'فشل في إرسال بريد التحقق',
                500
            )
        
        return success_response(
            message='Verification email sent successfully',
            message_ar='تم إرسال بريد التحقق بنجاح'
        )
        
    except Exception as e:
        current_app.logger.error(f"Resend verification error: {str(e)}")
        return error_response(
            'Failed to send verification email',
            'فشل في إرسال بريد التحقق',
            500
        )

@auth_bp.route('/forgot-password', methods=['POST'])
def forgot_password():
    """Password reset request endpoint"""
    try:
        schema = PasswordResetRequestSchema()
        data = schema.load(request.get_json())
        
        user = User.query.filter_by(email=data['email']).first()
        
        if user:
            # Generate reset token
            reset_token = str(uuid.uuid4())
            user.password_reset_token = reset_token
            user.password_reset_expires = datetime.utcnow() + timedelta(hours=1)
            db.session.commit()
            
            # Send reset email using EmailService
            try:
                email_service = EmailService()
                email_service.send_password_reset_email(user.email, reset_token)
            except Exception as e:
                current_app.logger.error(f"Failed to send password reset email: {str(e)}")
        
        # Always return success to prevent email enumeration
        return success_response(
            message='If the email exists, a password reset link has been sent',
            message_ar='إذا كان البريد الإلكتروني موجود، فقد تم إرسال رابط إعادة تعيين كلمة المرور'
        )
        
    except ValidationError as err:
        return error_response(
            'Validation failed',
            'فشل في التحقق من صحة البيانات',
            400,
            err.messages
        )
    except Exception as e:
        current_app.logger.error(f"Password reset request error: {str(e)}")
        return error_response(
            'Password reset request failed',
            'فشل طلب إعادة تعيين كلمة المرور',
            500
        )

@auth_bp.route('/reset-password', methods=['POST'])
def reset_password():
    """Password reset endpoint"""
    try:
        schema = PasswordResetSchema()
        data = schema.load(request.get_json())
        
        # Find user by reset token
        user = User.query.filter_by(password_reset_token=data['token']).first()
        
        if not user or not user.password_reset_expires or user.password_reset_expires < datetime.utcnow():
            return error_response(
                'Invalid or expired reset token',
                'رمز إعادة التعيين غير صحيح أو منتهي الصلاحية',
                400
            )
        
        # Update password
        user.set_password(data['password'])
        user.password_reset_token = None
        user.password_reset_expires = None
        db.session.commit()
        
        return success_response(
            message='Password reset successfully',
            message_ar='تم إعادة تعيين كلمة المرور بنجاح'
        )
        
    except ValidationError as err:
        return error_response(
            'Validation failed',
            'فشل في التحقق من صحة البيانات',
            400,
            err.messages
        )
    except Exception as e:
        current_app.logger.error(f"Password reset error: {str(e)}")
        return error_response(
            'Password reset failed',
            'فشل إعادة تعيين كلمة المرور',
            500
        )

@auth_bp.route('/profile', methods=['GET'])
@jwt_required()
def get_profile():
    """Get user profile (requires authentication)"""
    try:
        current_user_id = get_jwt_identity()
        user = User.query.get(current_user_id)
        
        if not user:
            return error_response(
                'User not found',
                'المستخدم غير موجود',
                404
            )
        
        return success_response(
            data={'user': user.to_dict()},
            message='Profile retrieved successfully',
            message_ar='تم استرداد الملف الشخصي بنجاح'
        )
        
    except Exception as e:
        current_app.logger.error(f"Get profile error: {str(e)}")
        return error_response(
            'Failed to get profile',
            'فشل في الحصول على الملف الشخصي',
            500
        )

@auth_bp.route('/refresh', methods=['POST'])
@jwt_required()
def refresh_token():
    """Refresh access token"""
    try:
        current_user_id = get_jwt_identity()
        user = User.query.get(current_user_id)
        
        if not user or not user.is_active:
            return error_response(
                'Invalid user',
                'مستخدم غير صحيح',
                401
            )
        
        # Generate new access token
        access_token = create_access_token(identity=user.id)
        
        return success_response(
            data={'access_token': access_token},
            message='Token refreshed successfully',
            message_ar='تم تحديث الرمز المميز بنجاح'
        )
        
    except Exception as e:
        current_app.logger.error(f"Token refresh error: {str(e)}")
        return error_response(
            'Token refresh failed',
            'فشل تحديث الرمز المميز',
            500
        )

# Error handlers for this blueprint
@auth_bp.errorhandler(ValidationError)
def handle_marshmallow_error(e):
    """Handle Marshmallow validation errors"""
    return error_response(
        'Validation failed',
        'فشل في التحقق من صحة البيانات',
        400,
        e.messages
    )

@auth_bp.errorhandler(400)
def handle_bad_request(e):
    """Handle bad request errors"""
    return error_response(
        'Bad request',
        'طلب غير صحيح',
        400
    )

@auth_bp.errorhandler(500)
def handle_internal_error(e):
    """Handle internal server errors"""
    current_app.logger.error(f"Internal server error: {str(e)}")
    return error_response(
        'Internal server error',
        'خطأ داخلي في الخادم',
        500
    )

