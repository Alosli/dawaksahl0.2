from flask import Blueprint, request, jsonify, current_app
from werkzeug.security import check_password_hash, generate_password_hash
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity, create_refresh_token
from datetime import datetime, timedelta
import uuid
import secrets
import re
import json

from src.models.user import User
from src.models import db
from src.models.pharmacy import Pharmacy
from src.services.email_service import EmailService
from src.services.auth_service import AuthService

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/register', methods=['POST'])
def register():
    """Register a new user or pharmacy"""
    try:
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['email', 'password', 'user_type']
        for field in required_fields:
            if not data.get(field):
                return jsonify({
                    'success': False,
                    'message': f'{field} is required',
                    'message_ar': f'{field} مطلوب'
                }), 400
        
        email = data['email'].lower().strip()
        password = data['password']
        user_type = data['user_type']  # 'patient' or 'pharmacy'
        
        # Validate email format
        if not re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', email):
            return jsonify({
                'success': False,
                'message': 'Invalid email format',
                'message_ar': 'تنسيق البريد الإلكتروني غير صحيح'
            }), 400
        
        # Validate password strength
        if len(password) < 8:
            return jsonify({
                'success': False,
                'message': 'Password must be at least 8 characters long',
                'message_ar': 'يجب أن تكون كلمة المرور 8 أحرف على الأقل'
            }), 400
        
        # Check if email already exists
        existing_user = User.query.filter_by(email=email).first()
        existing_pharmacy = Pharmacy.query.filter_by(email=email).first()
        
        if existing_user or existing_pharmacy:
            return jsonify({
                'success': False,
                'message': 'Email already registered',
                'message_ar': 'البريد الإلكتروني مسجل بالفعل'
            }), 409
        
        if user_type == 'patient':
            # Register patient with ALL fields from UserRegister_PERFECT.jsx
            user = User(
                email=email,
                password_hash=generate_password_hash(password),
                
                # Personal Information
                first_name=data.get('first_name', ''),
                last_name=data.get('last_name', ''),
                phone=data.get('phone', ''),
                date_of_birth=datetime.strptime(data.get('date_of_birth'), '%Y-%m-%d').date() if data.get('date_of_birth') else None,
                gender=data.get('gender'),
                
                # Address Information (mapped correctly)
                address_line1=data.get('address_line1', ''),
                address_line2=data.get('address_line2', ''),
                city=data.get('city', ''),
                state=data.get('state', ''),
                postal_code=data.get('postal_code', ''),
                country=data.get('country', 'Yemen'),
                
                # Coordinates
                latitude=data.get('latitude'),
                longitude=data.get('longitude'),
                
                # Medical Information (JSON fields)
                blood_type=data.get('blood_type'),
                allergies=data.get('allergies', '[]'),  # Already JSON string from frontend
                chronic_conditions=data.get('chronic_conditions', '[]'),  # Already JSON string
                current_medications=data.get('current_medications', '[]'),  # Already JSON string
                
                # Emergency Contact
                emergency_contact_name=data.get('emergency_contact_name', ''),
                emergency_contact_phone=data.get('emergency_contact_phone', ''),
                emergency_contact_relation=data.get('emergency_contact_relation', ''),
                
                # Insurance Information
                insurance_provider=data.get('insurance_provider', ''),
                insurance_number=data.get('insurance_number', ''),
                
                # Preferences
                preferred_language=data.get('preferred_language', 'ar'),
                
                # Email verification
                email_verification_token=secrets.token_urlsafe(32),
                email_verification_expires=datetime.utcnow() + timedelta(hours=24),
                is_verified=False,
                email_verified=False
            )
            
            db.session.add(user)
            db.session.commit()
            
            # Send verification email
            try:
                EmailService.send_verification_email(user.email, user.email_verification_token, user.preferred_language)
                current_app.logger.info(f"Verification email sent to {user.email}")
            except Exception as e:
                current_app.logger.error(f"Failed to send verification email: {str(e)}")
            
            return jsonify({
                'success': True,
                'message': 'Registration successful. Please check your email to verify your account.',
                'message_ar': 'تم التسجيل بنجاح. يرجى التحقق من بريدك الإلكتروني لتفعيل حسابك.',
                'user_id': user.id,
                'user_type': 'patient'
            }), 201
            
        elif user_type == 'pharmacy':
            # Register pharmacy with ALL fields from PharmacyRegister_PERFECT.jsx
            pharmacy = Pharmacy(
                email=email,
                password_hash=generate_password_hash(password),
                
                # Business Information
                pharmacy_name=data.get('pharmacy_name', ''),
                pharmacy_name_ar=data.get('pharmacy_name_ar', ''),
                license_number=data.get('license_number', ''),
                pharmacist_name=data.get('pharmacist_name', ''),
                pharmacist_license=data.get('pharmacist_license', ''),
                
                # Contact Information
                phone=data.get('phone', ''),
                website_url=data.get('website_url', ''),
                
                # Address Information (mapped correctly)
                address_line1=data.get('address_line1', ''),
                address_line2=data.get('address_line2', ''),
                city=data.get('city', ''),
                state=data.get('state', ''),
                postal_code=data.get('postal_code', ''),
                country=data.get('country', 'Yemen'),
                
                # Coordinates
                latitude=data.get('latitude'),
                longitude=data.get('longitude'),
                
                # Business Details
                establishment_date=datetime.strptime(data.get('establishment_date'), '%Y-%m-%d').date() if data.get('establishment_date') else None,
                description=data.get('description', ''),
                description_ar=data.get('description_ar', ''),
                
                # Services & Operations (JSON fields - already strings from frontend)
                services=data.get('services', '[]'),
                operating_hours=data.get('operating_hours', '{}'),
                
                # Preferences
                preferred_language=data.get('preferred_language', 'ar'),
                
                # Email verification
                email_verification_token=secrets.token_urlsafe(32),
                email_verification_expires=datetime.utcnow() + timedelta(hours=24),
                is_verified=False,
                email_verified=False,
                
                # Pharmacy approval status
                verification_status='pending'  # Pharmacies need approval
            )
            
            db.session.add(pharmacy)
            db.session.commit()
            
            # Send verification email
            try:
                EmailService.send_pharmacy_verification_email(pharmacy.email, pharmacy.email_verification_token, pharmacy.preferred_language)
                current_app.logger.info(f"Pharmacy verification email sent to {pharmacy.email}")
            except Exception as e:
                current_app.logger.error(f"Failed to send verification email: {str(e)}")
            
            return jsonify({
                'success': True,
                'message': 'Pharmacy registration successful. Please check your email to verify your account and wait for approval.',
                'message_ar': 'تم تسجيل الصيدلية بنجاح. يرجى التحقق من بريدك الإلكتروني وانتظار الموافقة.',
                'pharmacy_id': pharmacy.id,
                'user_type': 'pharmacy'
            }), 201
        
        else:
            return jsonify({
                'success': False,
                'message': 'Invalid user type',
                'message_ar': 'نوع المستخدم غير صحيح'
            }), 400
            
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Registration error: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'Registration failed',
            'message_ar': 'فشل في التسجيل'
        }), 500

@auth_bp.route('/login', methods=['POST'])
def login():
    """Login user or pharmacy"""
    try:
        data = request.get_json()
        
        email = data.get('email', '').lower().strip()
        password = data.get('password', '')
        
        if not email or not password:
            return jsonify({
                'success': False,
                'message': 'Email and password are required',
                'message_ar': 'البريد الإلكتروني وكلمة المرور مطلوبان'
            }), 400
        
        # Try to find user first
        user = User.query.filter_by(email=email).first()
        if user and check_password_hash(user.password_hash, password):
            # Check email verification using the correct field names
            if not user.is_verified and not user.email_verified:
                return jsonify({
                    'success': False,
                    'message': 'Please verify your email before logging in',
                    'message_ar': 'يرجى تفعيل بريدك الإلكتروني قبل تسجيل الدخول'
                }), 403
            
            if not user.is_active:
                return jsonify({
                    'success': False,
                    'message': 'Account is deactivated',
                    'message_ar': 'الحساب معطل'
                }), 403
            
            # Update last login
            user.last_login = datetime.utcnow()
            db.session.commit()
            
            # Create tokens
            access_token = create_access_token(
                identity={'id': user.id, 'type': 'user'},
                expires_delta=timedelta(hours=24)
            )
            refresh_token = create_refresh_token(
                identity={'id': user.id, 'type': 'user'}
            )
            
            return jsonify({
                'success': True,
                'message': 'Login successful',
                'message_ar': 'تم تسجيل الدخول بنجاح',
                'access_token': access_token,
                'refresh_token': refresh_token,
                'user': user.to_dict(),
                'user_type': 'patient'
            }), 200
        
        # Try to find pharmacy
        pharmacy = Pharmacy.query.filter_by(email=email).first()
        if pharmacy and check_password_hash(pharmacy.password_hash, password):
            # Check email verification using the correct field names
            if not pharmacy.is_verified and not pharmacy.email_verified:
                return jsonify({
                    'success': False,
                    'message': 'Please verify your email before logging in',
                    'message_ar': 'يرجى تفعيل بريدك الإلكتروني قبل تسجيل الدخول'
                }), 403
            
            if pharmacy.verification_status != 'verified':
                status_messages = {
                    'pending': 'Account is pending approval',
                    'rejected': 'Account application was rejected'
                }
                status_messages_ar = {
                    'pending': 'الحساب في انتظار الموافقة',
                    'rejected': 'تم رفض طلب الحساب'
                }
                
                return jsonify({
                    'success': False,
                    'message': status_messages.get(pharmacy.verification_status, 'Account is not verified'),
                    'message_ar': status_messages_ar.get(pharmacy.verification_status, 'الحساب غير مفعل')
                }), 403
            
            # Update last login
            pharmacy.last_login = datetime.utcnow()
            db.session.commit()
            
            # Create tokens
            access_token = create_access_token(
                identity={'id': pharmacy.id, 'type': 'pharmacy'},
                expires_delta=timedelta(hours=24)
            )
            refresh_token = create_refresh_token(
                identity={'id': pharmacy.id, 'type': 'pharmacy'}
            )
            
            return jsonify({
                'success': True,
                'message': 'Login successful',
                'message_ar': 'تم تسجيل الدخول بنجاح',
                'access_token': access_token,
                'refresh_token': refresh_token,
                'pharmacy': pharmacy.to_dict(),
                'user_type': 'pharmacy'
            }), 200

        # Add this to your login function in auth.py, after checking pharmacy
        # Try to find doctor
        doctor = Doctor.query.filter_by(email=email).first()
        if doctor and check_password_hash(doctor.password_hash, password):
            # Check email verification
            if not doctor.is_verified and not doctor.email_verified:
                return jsonify({
                    'success': False,
                    'message': 'Please verify your email before logging in',
                    'message_ar': 'يرجى تفعيل بريدك الإلكتروني قبل تسجيل الدخول'
                }), 403
            
            if doctor.verification_status != 'verified':
                status_messages = {
                    'pending': 'Account is pending approval',
                    'rejected': 'Account application was rejected'
                }
                status_messages_ar = {
                    'pending': 'الحساب في انتظار الموافقة',
                    'rejected': 'تم رفض طلب الحساب'
                }
                
                return jsonify({
                    'success': False,
                    'message': status_messages.get(doctor.verification_status, 'Account is not verified'),
                    'message_ar': status_messages_ar.get(doctor.verification_status, 'الحساب غير مفعل')
                }), 403
            
            # Update last login
            doctor.last_login = datetime.utcnow()
            db.session.commit()
            
            # Create tokens
            access_token = create_access_token(
                identity={'id': doctor.id, 'type': 'doctor'},
                expires_delta=timedelta(hours=24)
            )
            refresh_token = create_refresh_token(
                identity={'id': doctor.id, 'type': 'doctor'}
            )
            
            return jsonify({
                'success': True,
                'message': 'Login successful',
                'message_ar': 'تم تسجيل الدخول بنجاح',
                'access_token': access_token,
                'refresh_token': refresh_token,
                'doctor': doctor.to_dict(),
                'user_type': 'doctor'
            }), 200    
        
        # Invalid credentials
        return jsonify({
            'success': False,
            'message': 'Invalid email or password',
            'message_ar': 'البريد الإلكتروني أو كلمة المرور غير صحيحة'
        }), 401
        
    except Exception as e:
        current_app.logger.error(f"Login error: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'Login failed',
            'message_ar': 'فشل في تسجيل الدخول'
        }), 500

@auth_bp.route('/verify-email', methods=['POST'])
def verify_email():
    """Verify email address - FIXED to properly update boolean fields"""
    try:
        data = request.get_json()
        token = data.get('token')
        
        if not token:
            return jsonify({
                'success': False,
                'message': 'Verification token is required',
                'message_ar': 'رمز التحقق مطلوب'
            }), 400
        
        # Check users
        user = User.query.filter_by(email_verification_token=token).first()
        if user:
            if user.email_verification_expires and datetime.utcnow() > user.email_verification_expires:
                return jsonify({
                    'success': False,
                    'message': 'Verification token has expired',
                    'message_ar': 'انتهت صلاحية رمز التحقق'
                }), 400
            
            # ✅ PROPERLY UPDATE ALL EMAIL VERIFICATION FIELDS
            user.is_verified = True
            user.email_verified = True  # Update both boolean fields
            user.email_verification_token = None
            user.email_verification_expires = None
            user.email_verified_at = datetime.utcnow()
            db.session.commit()
            
            current_app.logger.info(f"User email verified: {user.email}")
            
            return jsonify({
                'success': True,
                'message': 'Email verified successfully',
                'message_ar': 'تم تفعيل البريد الإلكتروني بنجاح'
            }), 200
        
        # Check pharmacies
        pharmacy = Pharmacy.query.filter_by(email_verification_token=token).first()
        if pharmacy:
            if pharmacy.email_verification_expires and datetime.utcnow() > pharmacy.email_verification_expires:
                return jsonify({
                    'success': False,
                    'message': 'Verification token has expired',
                    'message_ar': 'انتهت صلاحية رمز التحقق'
                }), 400
            
            # ✅ PROPERLY UPDATE ALL EMAIL VERIFICATION FIELDS
            pharmacy.is_verified = True
            pharmacy.email_verified = True  # Update both boolean fields
            pharmacy.email_verification_token = None
            pharmacy.email_verification_expires = None
            pharmacy.email_verified_at = datetime.utcnow()
            db.session.commit()
            
            current_app.logger.info(f"Pharmacy email verified: {pharmacy.email}")
            
            return jsonify({
                'success': True,
                'message': 'Email verified successfully. Your pharmacy account is now pending approval.',
                'message_ar': 'تم تفعيل البريد الإلكتروني بنجاح. حساب الصيدلية في انتظار الموافقة.'
            }), 200
        
        return jsonify({
            'success': False,
            'message': 'Invalid verification token',
            'message_ar': 'رمز التحقق غير صحيح'
        }), 400
        
    except Exception as e:
        current_app.logger.error(f"Email verification error: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'Email verification failed',
            'message_ar': 'فشل في تفعيل البريد الإلكتروني'
        }), 500

@auth_bp.route('/forgot-password', methods=['POST'])
def forgot_password():
    """Request password reset"""
    try:
        data = request.get_json()
        email = data.get('email', '').lower().strip()
        
        if not email:
            return jsonify({
                'success': False,
                'message': 'Email is required',
                'message_ar': 'البريد الإلكتروني مطلوب'
            }), 400
        
        # Check users
        user = User.query.filter_by(email=email).first()
        if user:
            user.password_reset_token = secrets.token_urlsafe(32)
            user.password_reset_expires = datetime.utcnow() + timedelta(hours=1)
            db.session.commit()
            
            try:
                EmailService.send_password_reset_email(user.email, user.password_reset_token, user.preferred_language)
            except Exception as e:
                current_app.logger.error(f"Failed to send password reset email: {str(e)}")
            
            return jsonify({
                'success': True,
                'message': 'Password reset email sent',
                'message_ar': 'تم إرسال رابط إعادة تعيين كلمة المرور'
            }), 200
        
        # Check pharmacies
        pharmacy = Pharmacy.query.filter_by(email=email).first()
        if pharmacy:
            pharmacy.password_reset_token = secrets.token_urlsafe(32)
            pharmacy.password_reset_expires = datetime.utcnow() + timedelta(hours=1)
            db.session.commit()
            
            try:
                EmailService.send_password_reset_email(pharmacy.email, pharmacy.password_reset_token, pharmacy.preferred_language)
            except Exception as e:
                current_app.logger.error(f"Failed to send password reset email: {str(e)}")
            
            return jsonify({
                'success': True,
                'message': 'Password reset email sent',
                'message_ar': 'تم إرسال رابط إعادة تعيين كلمة المرور'
            }), 200
        
        # Always return success to prevent email enumeration
        return jsonify({
            'success': True,
            'message': 'If the email exists, a password reset link has been sent',
            'message_ar': 'إذا كان البريد الإلكتروني موجود، فقد تم إرسال رابط إعادة تعيين كلمة المرور'
        }), 200
        
    except Exception as e:
        current_app.logger.error(f"Forgot password error: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'Password reset failed',
            'message_ar': 'فشل في إعادة تعيين كلمة المرور'
        }), 500

@auth_bp.route('/reset-password', methods=['POST'])
def reset_password():
    """Reset password with token"""
    try:
        data = request.get_json()
        token = data.get('token')
        new_password = data.get('password')
        
        if not token or not new_password:
            return jsonify({
                'success': False,
                'message': 'Token and new password are required',
                'message_ar': 'الرمز وكلمة المرور الجديدة مطلوبان'
            }), 400
        
        if len(new_password) < 8:
            return jsonify({
                'success': False,
                'message': 'Password must be at least 8 characters long',
                'message_ar': 'يجب أن تكون كلمة المرور 8 أحرف على الأقل'
            }), 400
        
        # Check users
        user = User.query.filter_by(password_reset_token=token).first()
        if user:
            if user.password_reset_expires and datetime.utcnow() > user.password_reset_expires:
                return jsonify({
                    'success': False,
                    'message': 'Reset token has expired',
                    'message_ar': 'انتهت صلاحية رمز إعادة التعيين'
                }), 400
            
            user.password_hash = generate_password_hash(new_password)
            user.password_reset_token = None
            user.password_reset_expires = None
            db.session.commit()
            
            return jsonify({
                'success': True,
                'message': 'Password reset successfully',
                'message_ar': 'تم إعادة تعيين كلمة المرور بنجاح'
            }), 200
        
        # Check pharmacies
        pharmacy = Pharmacy.query.filter_by(password_reset_token=token).first()
        if pharmacy:
            if pharmacy.password_reset_expires and datetime.utcnow() > pharmacy.password_reset_expires:
                return jsonify({
                    'success': False,
                    'message': 'Reset token has expired',
                    'message_ar': 'انتهت صلاحية رمز إعادة التعيين'
                }), 400
            
            pharmacy.password_hash = generate_password_hash(new_password)
            pharmacy.password_reset_token = None
            pharmacy.password_reset_expires = None
            db.session.commit()
            
            return jsonify({
                'success': True,
                'message': 'Password reset successfully',
                'message_ar': 'تم إعادة تعيين كلمة المرور بنجاح'
            }), 200
        
        return jsonify({
            'success': False,
            'message': 'Invalid reset token',
            'message_ar': 'رمز إعادة التعيين غير صحيح'
        }), 400
        
    except Exception as e:
        current_app.logger.error(f"Password reset error: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'Password reset failed',
            'message_ar': 'فشل في إعادة تعيين كلمة المرور'
        }), 500

@auth_bp.route('/refresh', methods=['POST'])
@jwt_required(refresh=True)
def refresh():
    """Refresh access token"""
    try:
        current_user = get_jwt_identity()
        
        new_token = create_access_token(
            identity=current_user,
            expires_delta=timedelta(hours=24)
        )
        
        return jsonify({
            'success': True,
            'access_token': new_token
        }), 200
        
    except Exception as e:
        current_app.logger.error(f"Token refresh error: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'Token refresh failed',
            'message_ar': 'فشل في تحديث الرمز'
        }), 500

@auth_bp.route('/logout', methods=['POST'])
@jwt_required()
def logout():
    """Logout user"""
    try:
        # In a production app, you might want to blacklist the token
        return jsonify({
            'success': True,
            'message': 'Logged out successfully',
            'message_ar': 'تم تسجيل الخروج بنجاح'
        }), 200
        
    except Exception as e:
        current_app.logger.error(f"Logout error: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'Logout failed',
            'message_ar': 'فشل في تسجيل الخروج'
        }), 500

@auth_bp.route('/profile', methods=['GET'])
@jwt_required()
def get_profile():
    """Get current user profile"""
    try:
        current_user = get_jwt_identity()
        user_id = current_user['id']
        user_type = current_user['type']
        
        if user_type == 'user':
            user = User.query.get(user_id)
            if not user:
                return jsonify({
                    'success': False,
                    'message': 'User not found',
                    'message_ar': 'المستخدم غير موجود'
                }), 404
            
            return jsonify({
                'success': True,
                'user': user.to_dict(),
                'user_type': 'patient'
            }), 200
            
        elif user_type == 'pharmacy':
            pharmacy = Pharmacy.query.get(user_id)
            if not pharmacy:
                return jsonify({
                    'success': False,
                    'message': 'Pharmacy not found',
                    'message_ar': 'الصيدلية غير موجودة'
                }), 404
            
            return jsonify({
                'success': True,
                'pharmacy': pharmacy.to_dict(),
                'user_type': 'pharmacy'
            }), 200
        
        return jsonify({
            'success': False,
            'message': 'Invalid user type',
            'message_ar': 'نوع المستخدم غير صحيح'
        }), 400
        
    except Exception as e:
        current_app.logger.error(f"Get profile error: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'Failed to get profile',
            'message_ar': 'فشل في الحصول على الملف الشخصي'
        }), 500

@auth_bp.route('/resend-verification', methods=['POST'])
def resend_verification():
    """Resend email verification"""
    try:
        data = request.get_json()
        email = data.get('email', '').lower().strip()
        
        if not email:
            return jsonify({
                'success': False,
                'message': 'Email is required',
                'message_ar': 'البريد الإلكتروني مطلوب'
            }), 400
        
        # Validate email format
        if not re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', email):
            return jsonify({
                'success': False,
                'message': 'Invalid email format',
                'message_ar': 'تنسيق البريد الإلكتروني غير صحيح'
            }), 400
        
        # Check for user first
        user = User.query.filter_by(email=email).first()
        if user:
            # Check if already verified
            if user.is_verified or user.email_verified:
                return jsonify({
                    'success': False,
                    'message': 'Email is already verified',
                    'message_ar': 'البريد الإلكتروني مفعل بالفعل'
                }), 400
            
            # Check rate limiting (optional - prevent spam)
            if (user.email_verification_expires and 
                user.email_verification_expires > datetime.utcnow() and
                (datetime.utcnow() - (user.email_verification_expires - timedelta(hours=24))).total_seconds() < 300):  # 5 minutes
                return jsonify({
                    'success': False,
                    'message': 'Please wait 5 minutes before requesting another verification email',
                    'message_ar': 'يرجى الانتظار 5 دقائق قبل طلب بريد تفعيل آخر'
                }), 429
            
            # Generate new verification token
            user.email_verification_token = secrets.token_urlsafe(32)
            user.email_verification_expires = datetime.utcnow() + timedelta(hours=24)
            db.session.commit()
            
            # Send verification email
            try:
                EmailService.send_verification_email(user.email, user.email_verification_token, user.preferred_language)
                current_app.logger.info(f"Verification email resent to user: {user.email}")
                
                return jsonify({
                    'success': True,
                    'message': 'Verification email sent successfully',
                    'message_ar': 'تم إرسال بريد التفعيل بنجاح'
                }), 200
                
            except Exception as e:
                current_app.logger.error(f"Failed to resend verification email to user {user.email}: {str(e)}")
                return jsonify({
                    'success': False,
                    'message': 'Failed to send verification email',
                    'message_ar': 'فشل في إرسال بريد التفعيل'
                }), 500
        
        # Check for pharmacy
        pharmacy = Pharmacy.query.filter_by(email=email).first()
        if pharmacy:
            # Check if already verified
            if pharmacy.is_verified or pharmacy.email_verified:
                return jsonify({
                    'success': False,
                    'message': 'Email is already verified',
                    'message_ar': 'البريد الإلكتروني مفعل بالفعل'
                }), 400
            
            # Check rate limiting (optional - prevent spam)
            if (pharmacy.email_verification_expires and 
                pharmacy.email_verification_expires > datetime.utcnow() and
                (datetime.utcnow() - (pharmacy.email_verification_expires - timedelta(hours=24))).total_seconds() < 300):  # 5 minutes
                return jsonify({
                    'success': False,
                    'message': 'Please wait 5 minutes before requesting another verification email',
                    'message_ar': 'يرجى الانتظار 5 دقائق قبل طلب بريد تفعيل آخر'
                }), 429
            
            # Generate new verification token
            pharmacy.email_verification_token = secrets.token_urlsafe(32)
            pharmacy.email_verification_expires = datetime.utcnow() + timedelta(hours=24)
            db.session.commit()
            
            # Send verification email
            try:
                EmailService.send_pharmacy_verification_email(pharmacy.email, pharmacy.email_verification_token, pharmacy.preferred_language)
                current_app.logger.info(f"Verification email resent to pharmacy: {pharmacy.email}")
                
                return jsonify({
                    'success': True,
                    'message': 'Verification email sent successfully',
                    'message_ar': 'تم إرسال بريد التفعيل بنجاح'
                }), 200
                
            except Exception as e:
                current_app.logger.error(f"Failed to resend verification email to pharmacy {pharmacy.email}: {str(e)}")
                return jsonify({
                    'success': False,
                    'message': 'Failed to send verification email',
                    'message_ar': 'فشل في إرسال بريد التفعيل'
                }), 500
        
        # Email not found - return generic message to prevent email enumeration
        return jsonify({
            'success': True,
            'message': 'If the email exists and is not verified, a verification email has been sent',
            'message_ar': 'إذا كان البريد الإلكتروني موجود وغير مفعل، فقد تم إرسال بريد التفعيل'
        }), 200
        
    except Exception as e:
        current_app.logger.error(f"Resend verification error: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'Failed to resend verification email',
            'message_ar': 'فشل في إعادة إرسال بريد التفعيل'
        }), 500

@auth_bp.route('/check-verification-status', methods=['POST'])
def check_verification_status():
    """Check if email is verified (useful for frontend)"""
    try:
        data = request.get_json()
        email = data.get('email', '').lower().strip()
        
        if not email:
            return jsonify({
                'success': False,
                'message': 'Email is required',
                'message_ar': 'البريد الإلكتروني مطلوب'
            }), 400
        
        # Check user
        user = User.query.filter_by(email=email).first()
        if user:
            return jsonify({
                'success': True,
                'is_verified': user.is_verified or user.email_verified,
                'user_type': 'patient',
                'verification_status': 'verified' if (user.is_verified or user.email_verified) else 'pending'
            }), 200
        
        # Check pharmacy
        pharmacy = Pharmacy.query.filter_by(email=email).first()
        if pharmacy:
            return jsonify({
                'success': True,
                'is_verified': pharmacy.is_verified or pharmacy.email_verified,
                'user_type': 'pharmacy',
                'verification_status': pharmacy.verification_status if (pharmacy.is_verified or pharmacy.email_verified) else 'email_pending'
            }), 200
        
        # Email not found
        return jsonify({
            'success': False,
            'message': 'Email not found',
            'message_ar': 'البريد الإلكتروني غير موجود'
        }), 404
        
    except Exception as e:
        current_app.logger.error(f"Check verification status error: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'Failed to check verification status',
            'message_ar': 'فشل في التحقق من حالة التفعيل'
        }), 500

