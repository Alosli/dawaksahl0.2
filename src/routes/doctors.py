from flask import Blueprint, request, jsonify, current_app
from werkzeug.utils import secure_filename
from datetime import datetime, timedelta
import os
import uuid
from functools import wraps
from src.models import db
from werkzeug.security import check_password_hash, generate_password_hash



# Import your models (adjust imports based on your project structure)
from src.models.doctor import Doctor, DoctorReview, TimeSlot
from src.utils.file_upload import upload_file  # Assuming you have a file upload utility

doctor_auth_bp = Blueprint('doctor_auth', __name__, url_prefix='/api/v1/doctors')

def doctor_auth_required(f):
    """Decorator to require doctor authentication"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        token = request.headers.get('Authorization')
        if not token:
            return jsonify({
                'success': False,
                'message': 'رمز المصادقة مطلوب',
                'message_en': 'Authentication token required'
            }), 401
        
        try:
            # Remove 'Bearer ' prefix if present
            if token.startswith('Bearer '):
                token = token[7:]
            
            doctor = Doctor.verify_auth_token(token)
            if not doctor:
                return jsonify({
                    'success': False,
                    'message': 'رمز مصادقة غير صالح',
                    'message_en': 'Invalid authentication token'
                }), 401
            
            request.current_doctor = doctor
            return f(*args, **kwargs)
            
        except Exception as e:
            return jsonify({
                'success': False,
                'message': 'خطأ في المصادقة',
                'message_en': 'Authentication error'
            }), 401
    
    return decorated_function

def get_language():
    """Get language from request headers"""
    return request.headers.get('Accept-Language', 'ar')

@doctor_auth_bp.route('/register', methods=['POST'])
def register_doctor():
    """Register a new doctor with email verification"""
    try:
        # Get form data
        data = request.get_json() if request.is_json else request.form.to_dict()
        files = request.files
        language = get_language()
        email = data['email'].lower().strip()
        password = data['password']    
        
        # Validate required fields
        required_fields = [
            'first_name', 'last_name', 'email', 'phone', 'password',
            'medical_license_number', 'specialty', 'years_of_experience',
            'medical_school', 'graduation_year', 'clinic_hospital_name',
            'clinic_address', 'working_hours', 'consultation_fee'
        ]
        
        missing_fields = [field for field in required_fields if not data.get(field)]
        if missing_fields:
            return jsonify({
                'success': False,
                'message': f'الحقول التالية مطلوبة: {", ".join(missing_fields)}',
                'message_en': f'Required fields missing: {", ".join(missing_fields)}',
                'errors': {field: 'مطلوب' if language == 'ar' else 'Required' for field in missing_fields}
            }), 400
        
        # Check if email already exists
        from src.models.user import User
        from src.models.pharmacy import Pharmacy
        
        existing_user = User.query.filter_by(email=email).first()
        existing_pharmacy = Pharmacy.query.filter_by(email=email).first()
        existing_doctor = Doctor.query.filter_by(email=email).first()
        
        if existing_user or existing_pharmacy or existing_doctor:
            return jsonify({
                'success': False,
                'message': 'Email already registered',
                'message_ar': 'البريد الإلكتروني مسجل بالفعل'
            }), 409
        
        # Check if license number already exists
        if Doctor.query.filter_by(medical_license_number=data['medical_license_number']).first():
            return jsonify({
                'success': False,
                'message': 'رقم الترخيص مستخدم بالفعل',
                'message_en': 'License number already registered',
                'errors': {'medical_license_number': 'رقم الترخيص مستخدم بالفعل' if language == 'ar' else 'License number already exists'}
            }), 400
        
        # Handle file uploads
        profile_picture_url = None
        license_document_url = None
        
        if 'profile_picture' in files and files['profile_picture'].filename:
            try:
                profile_picture_url = upload_file(files['profile_picture'], 'doctor_profiles')
            except Exception as e:
                return jsonify({
                    'success': False,
                    'message': 'خطأ في رفع الصورة الشخصية',
                    'message_en': 'Error uploading profile picture'
                }), 400
        
        if 'license_document' in files and files['license_document'].filename:
            try:
                license_document_url = upload_file(files['license_document'], 'doctor_licenses')
            except Exception as e:
                return jsonify({
                    'success': False,
                    'message': 'خطأ في رفع وثيقة الترخيص',
                    'message_en': 'Error uploading license document'
                }), 400
        
        # Parse location data (NEW)
        latitude = None
        longitude = None
        if data.get('latitude') and data.get('longitude'):
            try:
                latitude = float(data['latitude'])
                longitude = float(data['longitude'])
            except (ValueError, TypeError):
                return jsonify({
                    'success': False,
                    'message': 'إحداثيات الموقع غير صالحة',
                    'message_en': 'Invalid location coordinates',
                    'errors': {'location': 'إحداثيات الموقع غير صالحة' if language == 'ar' else 'Invalid coordinates'}
                }), 400
        
        # Parse dates
        date_of_birth = None
        license_expiry_date = None
        
        if data.get('date_of_birth'):
            try:
                date_of_birth = datetime.strptime(data['date_of_birth'], '%Y-%m-%d').date()
            except ValueError:
                pass
        
        if data.get('license_expiry_date'):
            try:
                license_expiry_date = datetime.strptime(data['license_expiry_date'], '%Y-%m-%d').date()
            except ValueError:
                pass
        
        # Parse working hours and languages
        languages_spoken = ['ar']  # Default to Arabic
        
        if data.get('working_hours'):
            try:
                import json
                working_hours = json.loads(data['working_hours']) if isinstance(data['working_hours'], str) else data['working_hours']
            except (json.JSONDecodeError, TypeError):
                pass
        
        if data.get('languages_spoken'):
            try:
                import json
                languages_spoken = json.loads(data['languages_spoken']) if isinstance(data['languages_spoken'], str) else data['languages_spoken']
            except (json.JSONDecodeError, TypeError):
                languages_spoken = ['ar']
        
        # Create doctor instance
        doctor = Doctor(
            # Personal Information
            first_name=data['first_name'],
            first_name_ar=data.get('first_name_ar', data['first_name']),
            last_name=data['last_name'],
            last_name_ar=data.get('last_name_ar', data['last_name']),
            email=email,
            phone=data['phone'],
            password_hash=generate_password_hash(password),
            date_of_birth=date_of_birth,
            gender=data.get('gender'),
            nationality=data.get('nationality'),
            
            # Professional Information
            medical_license_number=data['medical_license_number'],
            license_expiry_date=license_expiry_date,
            primary_specialty=data['specialty'],            # match model field
            subspecialties=data.get('subspecialty'),
            primary_specialty_ar=data.get('specialty_ar', data['specialty']),
            years_of_experience=int(data['years_of_experience']),
            medical_school=data['medical_school'],
            medical_school_ar=data.get('medical_school_ar'),
            graduation_year=int(data['graduation_year']),
            
            # Practice Information
            clinic_hospital_name=data['clinic_hospital_name'],
            clinic_hospital_name_ar=data.get('clinic_hospital_name_ar', data['clinic_hospital_name']),
            address=data['clinic_address'],
            clinic_phone=data.get('clinic_phone'),
            address_ar=data.get('clinic_address_ar', data['clinic_address']),
            consultation_fee=float(data['consultation_fee']),
            bio=data.get('bio'),
            bio_ar=data.get('bio_ar'),
            
            # NEW: Location Information
            latitude=latitude,
            longitude=longitude,
            
            # Files
            profile_picture=profile_picture_url,
            license_document=license_document_url,
            
            # Settings
            accepts_insurance=data.get('accepts_insurance', True),
            offers_telemedicine=data.get('offers_telemedicine', False),
            languages_spoken=languages_spoken,
            working_hours=data.get('working_hours'),

            # ✅ EMAIL VERIFICATION SETUP
            preferred_language=data.get('preferred_language', 'ar'),
            is_verified=False,
            email_verified=False,
            verification_status='pending'
        )


        # ✅ GENERATE VERIFICATION TOKEN
        verification_token = doctor.generate_verification_token()
        
        # Save to database
        db.session.add(doctor)
        db.session.commit()
        
        # Generate authentication token
        token = doctor.generate_token()
        
        # ✅ SEND VERIFICATION EMAIL
        try:
            from src.services.email_service import EmailService
            EmailService.send_doctor_verification_email(
                doctor.email, 
                verification_token, 
                doctor.preferred_language
            )
            current_app.logger.info(f"Doctor verification email sent to {doctor.email}")
        except Exception as e:
            current_app.logger.error(f"Failed to send verification email: {str(e)}")

        return jsonify({
            'success': True,
            'message': 'Doctor registration successful. Please check your email to verify your account and wait for approval.',
            'message_ar': 'تم تسجيل الطبيب بنجاح. يرجى التحقق من بريدك الإلكتروني وانتظار الموافقة.',
            'data': {
                'doctor_id': doctor.id,
                'doctor_number': doctor.doctor_number,
                'email': doctor.email,
                'user_type': 'doctor'
            }
        }), 201

    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Doctor registration error: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'Registration failed',
            'message_ar': 'فشل في التسجيل',
            'error': str(e)
        }), 500
@doctor_auth_bp.route('/verify-email', methods=['POST'])
def verify_doctor_email():
    """Verify doctor email address"""
    try:
        data = request.get_json()
        token = data.get('token')
        
        if not token:
            return jsonify({
                'success': False,
                'message': 'Verification token is required',
                'message_ar': 'رمز التحقق مطلوب'
            }), 400
        
        doctor = Doctor.query.filter_by(email_verification_token=token).first()
        if not doctor:
            return jsonify({
                'success': False,
                'message': 'Invalid verification token',
                'message_ar': 'رمز التحقق غير صحيح'
            }), 400
        
        if not doctor.is_verification_token_valid(token):
            return jsonify({
                'success': False,
                'message': 'Verification token has expired',
                'message_ar': 'انتهت صلاحية رمز التحقق'
            }), 400
        
        # Verify email
        doctor.verify_email()
        db.session.commit()
        
        current_app.logger.info(f"Doctor email verified: {doctor.email}")
        
        return jsonify({
            'success': True,
            'message': 'Email verified successfully. Your account is now pending approval.',
            'message_ar': 'تم تفعيل البريد الإلكتروني بنجاح. حسابك الآن في انتظار الموافقة.'
        }), 200
        
    except Exception as e:
        current_app.logger.error(f"Email verification error: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'Email verification failed',
            'message_ar': 'فشل في تفعيل البريد الإلكتروني'
        }), 500

@doctor_auth_bp.route('/resend-verification', methods=['POST'])
def resend_doctor_verification():
    """Resend verification email to doctor"""
    try:
        data = request.get_json()
        email = data.get('email', '').lower().strip()
        
        if not email:
            return jsonify({
                'success': False,
                'message': 'Email is required',
                'message_ar': 'البريد الإلكتروني مطلوب'
            }), 400
        
        doctor = Doctor.query.filter_by(email=email).first()
        if not doctor:
            return jsonify({
                'success': False,
                'message': 'Doctor not found',
                'message_ar': 'الطبيب غير موجود'
            }), 404
        
        if doctor.is_verified and doctor.email_verified:
            return jsonify({
                'success': False,
                'message': 'Email is already verified',
                'message_ar': 'البريد الإلكتروني مفعل بالفعل'
            }), 400
        
        # Generate new verification token
        verification_token = doctor.generate_verification_token()
        db.session.commit()
        
        # Send verification email
        try:
            from src.services.email_service import EmailService
            EmailService.send_doctor_verification_email(
                doctor.email, 
                verification_token, 
                doctor.preferred_language
            )
            current_app.logger.info(f"Verification email resent to {doctor.email}")
        except Exception as e:
            current_app.logger.error(f"Failed to resend verification email: {str(e)}")
            return jsonify({
                'success': False,
                'message': 'Failed to send verification email',
                'message_ar': 'فشل في إرسال بريد التفعيل'
            }), 500
        
        return jsonify({
            'success': True,
            'message': 'Verification email sent successfully',
            'message_ar': 'تم إرسال بريد التفعيل بنجاح'
        }), 200
        
    except Exception as e:
        current_app.logger.error(f"Resend verification error: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'Failed to resend verification email',
            'message_ar': 'فشل في إعادة إرسال بريد التفعيل'
        }), 500


@doctor_auth_bp.route('/login', methods=['POST'])
def login_doctor():
    """Doctor login"""
    try:
        data = request.get_json()
        language = get_language()
        
        if not data or not data.get('email') or not data.get('password'):
            return jsonify({
                'success': False,
                'message': 'البريد الإلكتروني وكلمة المرور مطلوبان',
                'message_en': 'Email and password required'
            }), 400
        
        # Find doctor by email
        doctor = Doctor.query.filter_by(email=data['email'].lower()).first()
        
        if not doctor or not doctor.check_password(data['password']):
            return jsonify({
                'success': False,
                'message': 'البريد الإلكتروني أو كلمة المرور غير صحيحة',
                'message_en': 'Invalid email or password'
            }), 401
        
        if not doctor.is_active:
            return jsonify({
                'success': False,
                'message': 'الحساب معطل',
                'message_en': 'Account is deactivated'
            }), 401
        
        # Update last login
        doctor.last_login = datetime.utcnow()
        db.session.commit()
        
        # Generate token
        token = doctor.generate_token()
        
        return jsonify({
            'success': True,
            'message': 'تم تسجيل الدخول بنجاح',
            'message_en': 'Login successful',
            'data': {
                'doctor': doctor.to_dict(include_sensitive=True, language=language),
                'token': token
            }
        }), 200
        
    except Exception as e:
        current_app.logger.error(f"Doctor login error: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'خطأ في تسجيل الدخول',
            'message_en': 'Login error'
        }), 500

@doctor_auth_bp.route('/profile', methods=['GET'])

def get_doctor_profile():
    """Get doctor profile"""
    try:
        language = get_language()
        doctor = request.current_doctor
        
        return jsonify({
            'success': True,
            'data': {
                'doctor': doctor.to_dict(include_sensitive=True, language=language)
            }
        }), 200
        
    except Exception as e:
        current_app.logger.error(f"Get doctor profile error: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'خطأ في جلب الملف الشخصي',
            'message_en': 'Error fetching profile'
        }), 500

@doctor_auth_bp.route('/profile', methods=['PUT'])
@doctor_auth_required
def update_doctor_profile():
    """Update doctor profile with location support"""
    try:
        data = request.get_json() if request.is_json else request.form.to_dict()
        files = request.files
        language = get_language()
        doctor = request.current_doctor
        
        # Update basic information
        updatable_fields = [
            'first_name', 'first_name_ar', 'last_name', 'last_name_ar',
            'phone', 'date_of_birth', 'gender', 'nationality',
            'subspecialty', 'clinic_hospital_name', 'clinic_hospital_name_ar',
            'clinic_address', 'clinic_address_ar', 'clinic_phone',
            'consultation_fee', 'bio', 'bio_ar', 'accepts_insurance',
            'offers_telemedicine'
        ]
        
        for field in updatable_fields:
            if field in data:
                if field == 'consultation_fee':
                    setattr(doctor, field, float(data[field]))
                elif field == 'date_of_birth' and data[field]:
                    try:
                        setattr(doctor, field, datetime.strptime(data[field], '%Y-%m-%d').date())
                    except ValueError:
                        pass
                elif field in ['accepts_insurance', 'offers_telemedicine']:
                    setattr(doctor, field, bool(data[field]))
                else:
                    setattr(doctor, field, data[field])
        
        # Update location (NEW)
        if data.get('latitude') and data.get('longitude'):
            try:
                doctor.latitude = float(data['latitude'])
                doctor.longitude = float(data['longitude'])
            except (ValueError, TypeError):
                return jsonify({
                    'success': False,
                    'message': 'إحداثيات الموقع غير صالحة',
                    'message_en': 'Invalid location coordinates'
                }), 400
        
        # Update working hours and languages
        if data.get('working_hours'):
            try:
                import json
                doctor.working_hours = json.loads(data['working_hours']) if isinstance(data['working_hours'], str) else data['working_hours']
            except (json.JSONDecodeError, TypeError):
                pass
        
        if data.get('languages_spoken'):
            try:
                import json
                doctor.languages_spoken = json.loads(data['languages_spoken']) if isinstance(data['languages_spoken'], str) else data['languages_spoken']
            except (json.JSONDecodeError, TypeError):
                pass
        
        # Handle file uploads
        if 'profile_picture' in files and files['profile_picture'].filename:
            try:
                doctor.profile_picture = upload_file(files['profile_picture'], 'doctor_profiles')
            except Exception as e:
                return jsonify({
                    'success': False,
                    'message': 'خطأ في رفع الصورة الشخصية',
                    'message_en': 'Error uploading profile picture'
                }), 400
        
        # Update timestamp
        doctor.updated_at = datetime.utcnow()
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'تم تحديث الملف الشخصي بنجاح',
            'message_en': 'Profile updated successfully',
            'data': {
                'doctor': doctor.to_dict(include_sensitive=True, language=language)
            }
        }), 200
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Update doctor profile error: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'خطأ في تحديث الملف الشخصي',
            'message_en': 'Error updating profile'
        }), 500

@doctor_auth_bp.route('/change-password', methods=['POST'])
@doctor_auth_required
def change_password():
    """Change doctor password"""
    try:
        data = request.get_json()
        language = get_language()
        doctor = request.current_doctor
        
        if not data or not data.get('current_password') or not data.get('new_password'):
            return jsonify({
                'success': False,
                'message': 'كلمة المرور الحالية والجديدة مطلوبتان',
                'message_en': 'Current and new password required'
            }), 400
        
        # Verify current password
        if not doctor.check_password(data['current_password']):
            return jsonify({
                'success': False,
                'message': 'كلمة المرور الحالية غير صحيحة',
                'message_en': 'Current password is incorrect'
            }), 400
        
        # Validate new password
        if len(data['new_password']) < 8:
            return jsonify({
                'success': False,
                'message': 'كلمة المرور الجديدة يجب أن تكون 8 أحرف على الأقل',
                'message_en': 'New password must be at least 8 characters'
            }), 400
        
        # Update password
        doctor.set_password(data['new_password'])
        doctor.updated_at = datetime.utcnow()
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'تم تغيير كلمة المرور بنجاح',
            'message_en': 'Password changed successfully'
        }), 200
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Change password error: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'خطأ في تغيير كلمة المرور',
            'message_en': 'Error changing password'
        }), 500

@doctor_auth_bp.route('/stats', methods=['GET'])
@doctor_auth_required
def get_doctor_stats():
    """Get doctor statistics"""
    try:
        language = get_language()
        doctor = request.current_doctor
        
        # Update statistics
        doctor.update_statistics()
        
        # Get additional stats
        today = datetime.now().date()
        this_month = datetime.now().replace(day=1).date()
        
        # Today's appointments
        today_appointments = doctor.appointments.filter(
            db.func.date(doctor.appointments.c.appointment_date) == today
        ).count()
        
        # This month's appointments
        month_appointments = doctor.appointments.filter(
            doctor.appointments.c.appointment_date >= this_month
        ).count()
        
        # Revenue this month (completed appointments only)
        month_revenue = db.session.query(db.func.sum(doctor.appointments.c.consultation_fee)).filter(
            doctor.appointments.c.appointment_date >= this_month,
            doctor.appointments.c.status == 'completed'
        ).scalar() or 0
        
        # Next appointment
        next_appointment = doctor.appointments.filter(
            doctor.appointments.c.appointment_date >= datetime.now(),
            doctor.appointments.c.status.in_(['confirmed', 'pending'])
        ).order_by(doctor.appointments.c.appointment_date).first()
        
        stats = {
            'total_appointments': doctor.total_appointments,
            'completed_appointments': doctor.completed_appointments,
            'cancelled_appointments': doctor.cancelled_appointments,
            'total_prescriptions': doctor.total_prescriptions,
            'average_rating': doctor.average_rating,
            'total_reviews': doctor.total_reviews,
            'today_appointments': today_appointments,
            'month_appointments': month_appointments,
            'month_revenue': float(month_revenue),
            'next_appointment': next_appointment.to_dict(language=language) if next_appointment else None,
            'verification_status': doctor.verification_status,
            'is_verified': doctor.is_verified
        }
        
        return jsonify({
            'success': True,
            'data': {
                'stats': stats
            }
        }), 200
        
    except Exception as e:
        current_app.logger.error(f"Get doctor stats error: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'خطأ في جلب الإحصائيات',
            'message_en': 'Error fetching statistics'
        }), 500

@doctor_auth_bp.route('/verify-email', methods=['POST'])
def verify_email():
    """Verify doctor email (placeholder for email verification system)"""
    try:
        data = request.get_json()
        language = get_language()
        
        if not data or not data.get('token'):
            return jsonify({
                'success': False,
                'message': 'رمز التحقق مطلوب',
                'message_en': 'Verification token required'
            }), 400
        
        # TODO: Implement email verification logic
        # This would typically involve:
        # 1. Decode the verification token
        # 2. Find the doctor by token
        # 3. Mark email as verified
        # 4. Update verification status
        
        return jsonify({
            'success': True,
            'message': 'تم التحقق من البريد الإلكتروني بنجاح',
            'message_en': 'Email verified successfully'
        }), 200
        
    except Exception as e:
        current_app.logger.error(f"Email verification error: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'خطأ في التحقق من البريد الإلكتروني',
            'message_en': 'Email verification error'
        }), 500
@doctor_auth_bp.route('/public', methods=['GET'])
@doctor_auth_bp.route('/public', methods=['GET'])
def get_public_doctors():
    """Get verified doctors for public viewing"""
    try:
        # Query parameters
        specialty = request.args.get('specialty')
        city = request.args.get('city')
        rating_min = request.args.get('rating_min', type=float)
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 10, type=int)
        
        # Build query for verified doctors only - FIXED!
        query = Doctor.query.filter_by(
            is_verified=True,
            is_active=True,
            verification_status='approved'  # ✅ Changed from 'approved' to 'verified'
        )
        
        if specialty:
            query = query.filter_by(primary_specialty=specialty)
        
        if city:
            # Better city search in full address
            query = query.filter(Doctor.address.city)
        
        
        
        # Paginate results
        doctors = query.paginate(
            page=page, per_page=per_page, error_out=False
        )
        
        # Return public doctor data (no sensitive info)
        result = []
        for doctor in doctors.items:
            doctor_data = {
                'id': doctor.id,
                'first_name': doctor.first_name,
                'last_name': doctor.last_name,
                'first_name_ar': doctor.first_name_ar,
                'last_name_ar': doctor.last_name_ar,
                'primary_specialty': doctor.primary_specialty,
                'primary_specialty_ar': doctor.primary_specialty_ar,
                'years_of_experience': doctor.years_of_experience,
                'consultation_fee': doctor.consultation_fee,
                'clinic_hospital_name': doctor.clinic_hospital_name,
                'clinic_hospital_name_ar': doctor.clinic_hospital_name_ar,
                'address': doctor.address,
                'address_ar': doctor.address_ar,
                'profile_picture': doctor.profile_picture,
                'bio': doctor.bio,
                'bio_ar': doctor.bio_ar,
                'total_reviews': doctor.total_reviews,
                'accepts_insurance': doctor.accepts_insurance,
                'offers_telemedicine': doctor.offers_telemedicine,
                'languages_spoken': doctor.languages_spoken
            }
            result.append(doctor_data)
        
        return jsonify({
            'success': True,
            'data': result,
            'pagination': {
                'page': page,
                'per_page': per_page,
                'total': doctors.total,
                'pages': doctors.pages
            }
        }), 200
        
    except Exception as e:
        current_app.logger.error(f"Error getting public doctors: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'Failed to retrieve doctors'
        }), 500

@doctor_auth_bp.route('/public/<int:doctor_id>', methods=['GET'])
def get_public_doctor_profile(doctor_id):
    """Get public doctor profile"""
    try:
        doctor = Doctor.query.filter_by(
            id=doctor_id,
            is_verified=True,
            is_active=True,
            verification_status='approved'
        ).first()
        
        if not doctor:
            return jsonify({
                'success': False,
                'message': 'Doctor not found'
            }), 404
        
        # Return detailed public profile
        doctor_data = {
            'id': doctor.id,
            'first_name': doctor.first_name,
            'last_name': doctor.last_name,
            'first_name_ar': doctor.first_name_ar,
            'last_name_ar': doctor.last_name_ar,
            'primary_specialty': doctor.primary_specialty,
            'primary_specialty_ar': doctor.primary_specialty_ar,
            'subspecialties': doctor.subspecialties,
            'years_of_experience': doctor.years_of_experience,
            'consultation_fee': doctor.consultation_fee,
            'clinic_hospital_name': doctor.clinic_hospital_name,
            'clinic_hospital_name_ar': doctor.clinic_hospital_name_ar,
            'address': doctor.address,
            'address_ar': doctor.address_ar,
            'clinic_phone': doctor.clinic_phone,
            'profile_picture': doctor.profile_picture,
            'bio': doctor.bio,
            'bio_ar': doctor.bio_ar,
            'medical_school': doctor.medical_school,
            'medical_school_ar': doctor.medical_school_ar,
            'graduation_year': doctor.graduation_year,
            'rating': doctor.rating,
            'total_reviews': doctor.total_reviews,
            'accepts_insurance': doctor.accepts_insurance,
            'offers_telemedicine': doctor.offers_telemedicine,
            'languages_spoken': doctor.languages_spoken,
            'working_hours': doctor.working_hours
        }
        
        return jsonify({
            'success': True,
            'data': doctor_data
        }), 200
        
    except Exception as e:
        current_app.logger.error(f"Error getting doctor profile: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'Failed to retrieve doctor profile'
        }), 500

@doctor_auth_bp.route('/<int:doctor_id>/time-slots', methods=['GET'])
def get_doctor_time_slots(doctor_id):
    """Get available time slots for a doctor"""
    try:
        # Get query parameters
        date_from = request.args.get('date_from')
        date_to = request.args.get('date_to')
        consultation_mode = request.args.get('consultation_mode')
        
        # Verify doctor exists and is active
        doctor = Doctor.query.filter_by(
            id=doctor_id,
            is_verified=True,
            is_active=True,
            verification_status='approved'
        ).first()
        
        if not doctor:
            return jsonify({
                'success': False,
                'message': 'Doctor not found'
            }), 404
        
        # Build time slot query
        query = TimeSlot.query.filter_by(
            doctor_id=doctor_id,
            is_available=True
        )
        
        if date_from:
            date_from_obj = datetime.strptime(date_from, '%Y-%m-%d').date()
            query = query.filter(TimeSlot.date >= date_from_obj)
        
        if date_to:
            date_to_obj = datetime.strptime(date_to, '%Y-%m-%d').date()
            query = query.filter(TimeSlot.date <= date_to_obj)
        
        if consultation_mode:
            query = query.filter_by(consultation_mode=consultation_mode)
        
        # Get available time slots
        time_slots = query.order_by(TimeSlot.date, TimeSlot.start_time).all()
        
        result = []
        for slot in time_slots:
            slot_data = {
                'id': slot.id,
                'doctor_id': slot.doctor_id,
                'date': slot.date.isoformat(),
                'start_time': slot.start_time.strftime('%H:%M'),
                'end_time': slot.end_time.strftime('%H:%M'),
                'consultation_mode': slot.consultation_mode,
                'consultation_fee': slot.get_consultation_fee(),
                'is_available': slot.is_available,
                'max_patients': slot.max_patients,
                'current_bookings': slot.current_bookings
            }
            result.append(slot_data)
        
        return jsonify({
            'success': True,
            'data': result
        }), 200
        
    except Exception as e:
        current_app.logger.error(f"Error getting doctor time slots: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'Failed to retrieve time slots'
        }), 500

@doctor_auth_bp.route('/<int:doctor_id>/available-slots', methods=['GET'])
def get_available_slots(doctor_id):
    """Generate available slots dynamically from working hours"""
    
    # Get doctor's working hours
    doctor = Doctor.query.get(doctor_id)
    working_hours = doctor.working_hours  # JSON: {"monday": {"start": "09:00", "end": "17:00"}}
    
    # Get requested date range
    date_from = request.args.get('date_from')
    date_to = request.args.get('date_to')
    
    available_slots = []
    
    for single_date in date_range(date_from, date_to):
        day_name = single_date.strftime('%A').lower()
        
        if day_name in working_hours:
            day_hours = working_hours[day_name]
            
            # Generate 30-minute slots
            current_time = datetime.strptime(day_hours['start'], '%H:%M').time()
            end_time = datetime.strptime(day_hours['end'], '%H:%M').time()
            
            while current_time < end_time:
                slot_datetime = datetime.combine(single_date, current_time)
                
                # Check if slot is already booked
                existing_appointment = Appointment.query.filter_by(
                    doctor_id=doctor_id,
                    appointment_date=single_date,
                    appointment_time=current_time
                ).first()
                
                if not existing_appointment:
                    available_slots.append({
                        'date': single_date.isoformat(),
                        'time': current_time.strftime('%H:%M'),
                        'datetime': slot_datetime.isoformat(),
                        'available': True
                    })
                
                # Add 30 minutes
                current_time = (datetime.combine(single_date, current_time) + timedelta(minutes=30)).time()
    
    return jsonify({
        'success': True,
        'data': available_slots
    })        
# Error handlers
@doctor_auth_bp.errorhandler(404)
def not_found(error):
    return jsonify({
        'success': False,
        'message': 'الصفحة غير موجودة',
        'message_en': 'Endpoint not found'
    }), 404

@doctor_auth_bp.errorhandler(405)
def method_not_allowed(error):
    return jsonify({
        'success': False,
        'message': 'الطريقة غير مسموحة',
        'message_en': 'Method not allowed'
    }), 405

@doctor_auth_bp.errorhandler(500)
def internal_error(error):
    db.session.rollback()
    return jsonify({
        'success': False,
        'message': 'خطأ داخلي في الخادم',
        'message_en': 'Internal server error'
    }), 500
