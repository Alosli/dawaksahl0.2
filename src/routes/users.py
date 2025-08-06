from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity
from werkzeug.security import check_password_hash, generate_password_hash
from datetime import datetime

from src.models.user import db, User
from src.services.auth_service import AuthService

users_bp = Blueprint('users', __name__)

@users_bp.route('/profile', methods=['GET'])
@jwt_required()
def get_profile():
    """Get current user profile"""
    try:
        current_identity = get_jwt_identity()
        if current_identity['type'] != 'user':
            return jsonify({
                'success': False,
                'message': 'Only users can access this endpoint',
                'message_ar': 'المستخدمون فقط يمكنهم الوصول لهذه النقطة'
            }), 403
        
        user_id = current_identity['id']
        language = request.args.get('language', 'ar')
        
        user = User.query.get(user_id)
        if not user:
            return jsonify({
                'success': False,
                'message': 'User not found',
                'message_ar': 'المستخدم غير موجود'
            }), 404
        
        return jsonify({
            'success': True,
            'data': user.to_dict(language=language)
        }), 200
        
    except Exception as e:
        current_app.logger.error(f"Get profile error: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'Failed to fetch profile',
            'message_ar': 'فشل في جلب الملف الشخصي'
        }), 500

@users_bp.route('/profile', methods=['PUT'])
@jwt_required()
def update_profile():
    """Update current user profile"""
    try:
        current_identity = get_jwt_identity()
        if current_identity['type'] != 'user':
            return jsonify({
                'success': False,
                'message': 'Only users can update profile',
                'message_ar': 'المستخدمون فقط يمكنهم تحديث الملف الشخصي'
            }), 403
        
        user_id = current_identity['id']
        data = request.get_json()
        
        user = User.query.get(user_id)
        if not user:
            return jsonify({
                'success': False,
                'message': 'User not found',
                'message_ar': 'المستخدم غير موجود'
            }), 404
        
        # Update allowed fields
        allowed_fields = [
            'first_name', 'last_name', 'phone_number', 'date_of_birth',
            'gender', 'preferred_language', 'profile_image_url',
            'address_line1', 'address_line2', 'city', 'state', 'postal_code',
            'country', 'latitude', 'longitude', 'emergency_contact_name',
            'emergency_contact_phone', 'emergency_contact_relationship',
            'medical_conditions', 'allergies', 'current_medications',
            'blood_type', 'height', 'weight', 'insurance_provider',
            'insurance_policy_number', 'email_notifications', 'push_notifications'
        ]
        
        for field in allowed_fields:
            if field in data:
                setattr(user, field, data[field])
        
        user.updated_at = datetime.utcnow()
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Profile updated successfully',
            'message_ar': 'تم تحديث الملف الشخصي بنجاح',
            'data': user.to_dict()
        }), 200
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Update profile error: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'Failed to update profile',
            'message_ar': 'فشل في تحديث الملف الشخصي'
        }), 500

@users_bp.route('/change-email', methods=['PUT'])
@jwt_required()
def change_email():
    """Change user email address"""
    try:
        current_identity = get_jwt_identity()
        if current_identity['type'] != 'user':
            return jsonify({
                'success': False,
                'message': 'Only users can change email',
                'message_ar': 'المستخدمون فقط يمكنهم تغيير البريد الإلكتروني'
            }), 403
        
        user_id = current_identity['id']
        data = request.get_json()
        
        new_email = data.get('new_email', '').lower().strip()
        password = data.get('password')
        
        if not new_email or not password:
            return jsonify({
                'success': False,
                'message': 'New email and password are required',
                'message_ar': 'البريد الإلكتروني الجديد وكلمة المرور مطلوبان'
            }), 400
        
        user = User.query.get(user_id)
        if not user:
            return jsonify({
                'success': False,
                'message': 'User not found',
                'message_ar': 'المستخدم غير موجود'
            }), 404
        
        # Verify current password
        if not check_password_hash(user.password_hash, password):
            return jsonify({
                'success': False,
                'message': 'Current password is incorrect',
                'message_ar': 'كلمة المرور الحالية غير صحيحة'
            }), 400
        
        # Check if new email is already in use
        existing_user = User.query.filter_by(email=new_email).first()
        if existing_user and existing_user.id != user_id:
            return jsonify({
                'success': False,
                'message': 'Email is already in use',
                'message_ar': 'البريد الإلكتروني مستخدم بالفعل'
            }), 409
        
        # Update email and require re-verification
        user.email = new_email
        user.is_email_verified = False
        user.email_verified_at = None
        user.updated_at = datetime.utcnow()
        
        # Generate new verification token
        import secrets
        from datetime import timedelta
        user.email_verification_token = secrets.token_urlsafe(32)
        user.email_verification_expires = datetime.utcnow() + timedelta(hours=24)
        
        db.session.commit()
        
        # Send verification email
        try:
            from src.services.email_service import EmailService
            EmailService.send_verification_email(user.email, user.email_verification_token, user.preferred_language)
        except Exception as e:
            current_app.logger.error(f"Failed to send verification email: {str(e)}")
        
        return jsonify({
            'success': True,
            'message': 'Email updated successfully. Please verify your new email address.',
            'message_ar': 'تم تحديث البريد الإلكتروني بنجاح. يرجى تفعيل عنوان بريدك الإلكتروني الجديد.'
        }), 200
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Change email error: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'Failed to change email',
            'message_ar': 'فشل في تغيير البريد الإلكتروني'
        }), 500

@users_bp.route('/upload-avatar', methods=['POST'])
@jwt_required()
def upload_avatar():
    """Upload user avatar image"""
    try:
        current_identity = get_jwt_identity()
        if current_identity['type'] != 'user':
            return jsonify({
                'success': False,
                'message': 'Only users can upload avatar',
                'message_ar': 'المستخدمون فقط يمكنهم رفع الصورة الشخصية'
            }), 403
        
        user_id = current_identity['id']
        
        # Check if file is present
        if 'avatar' not in request.files:
            return jsonify({
                'success': False,
                'message': 'No file uploaded',
                'message_ar': 'لم يتم رفع أي ملف'
            }), 400
        
        file = request.files['avatar']
        
        if file.filename == '':
            return jsonify({
                'success': False,
                'message': 'No file selected',
                'message_ar': 'لم يتم اختيار أي ملف'
            }), 400
        
        # Validate file type
        allowed_extensions = {'png', 'jpg', 'jpeg', 'gif', 'webp'}
        if not ('.' in file.filename and file.filename.rsplit('.', 1)[1].lower() in allowed_extensions):
            return jsonify({
                'success': False,
                'message': 'Invalid file type. Only images are allowed.',
                'message_ar': 'نوع الملف غير صحيح. الصور فقط مسموحة.'
            }), 400
        
        # TODO: Implement file upload to cloud storage (AWS S3, Cloudinary, etc.)
        # For now, return a placeholder URL
        avatar_url = f"https://api.dawaksahl.com/uploads/avatars/user_{user_id}_{datetime.now().timestamp()}.jpg"
        
        # Update user profile
        user = User.query.get(user_id)
        if not user:
            return jsonify({
                'success': False,
                'message': 'User not found',
                'message_ar': 'المستخدم غير موجود'
            }), 404
        
        user.profile_image_url = avatar_url
        user.updated_at = datetime.utcnow()
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Avatar uploaded successfully',
            'message_ar': 'تم رفع الصورة الشخصية بنجاح',
            'data': {
                'avatar_url': avatar_url
            }
        }), 200
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Upload avatar error: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'Failed to upload avatar',
            'message_ar': 'فشل في رفع الصورة الشخصية'
        }), 500

@users_bp.route('/deactivate', methods=['PUT'])
@jwt_required()
def deactivate_account():
    """Deactivate user account"""
    try:
        current_identity = get_jwt_identity()
        if current_identity['type'] != 'user':
            return jsonify({
                'success': False,
                'message': 'Only users can deactivate account',
                'message_ar': 'المستخدمون فقط يمكنهم إلغاء تفعيل الحساب'
            }), 403
        
        user_id = current_identity['id']
        data = request.get_json()
        
        password = data.get('password')
        reason = data.get('reason', 'User requested deactivation')
        
        if not password:
            return jsonify({
                'success': False,
                'message': 'Password is required',
                'message_ar': 'كلمة المرور مطلوبة'
            }), 400
        
        user = User.query.get(user_id)
        if not user:
            return jsonify({
                'success': False,
                'message': 'User not found',
                'message_ar': 'المستخدم غير موجود'
            }), 404
        
        # Verify password
        if not check_password_hash(user.password_hash, password):
            return jsonify({
                'success': False,
                'message': 'Password is incorrect',
                'message_ar': 'كلمة المرور غير صحيحة'
            }), 400
        
        # Deactivate account
        user.is_active = False
        user.deactivated_at = datetime.utcnow()
        user.deactivation_reason = reason
        user.updated_at = datetime.utcnow()
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Account deactivated successfully',
            'message_ar': 'تم إلغاء تفعيل الحساب بنجاح'
        }), 200
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Deactivate account error: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'Failed to deactivate account',
            'message_ar': 'فشل في إلغاء تفعيل الحساب'
        }), 500

@users_bp.route('/delete', methods=['DELETE'])
@jwt_required()
def delete_account():
    """Delete user account permanently"""
    try:
        current_identity = get_jwt_identity()
        if current_identity['type'] != 'user':
            return jsonify({
                'success': False,
                'message': 'Only users can delete account',
                'message_ar': 'المستخدمون فقط يمكنهم حذف الحساب'
            }), 403
        
        user_id = current_identity['id']
        data = request.get_json()
        
        password = data.get('password')
        confirmation = data.get('confirmation')
        
        if not password or not confirmation:
            return jsonify({
                'success': False,
                'message': 'Password and confirmation are required',
                'message_ar': 'كلمة المرور والتأكيد مطلوبان'
            }), 400
        
        if confirmation.lower() != 'delete my account':
            return jsonify({
                'success': False,
                'message': 'Please type "delete my account" to confirm',
                'message_ar': 'يرجى كتابة "delete my account" للتأكيد'
            }), 400
        
        user = User.query.get(user_id)
        if not user:
            return jsonify({
                'success': False,
                'message': 'User not found',
                'message_ar': 'المستخدم غير موجود'
            }), 404
        
        # Verify password
        if not check_password_hash(user.password_hash, password):
            return jsonify({
                'success': False,
                'message': 'Password is incorrect',
                'message_ar': 'كلمة المرور غير صحيحة'
            }), 400
        
        # TODO: Handle data cleanup (orders, reviews, favorites, etc.)
        # For now, just mark as deleted
        user.is_active = False
        user.is_deleted = True
        user.deleted_at = datetime.utcnow()
        user.email = f"deleted_{user_id}@deleted.com"  # Anonymize email
        user.phone_number = None
        user.first_name = "Deleted"
        user.last_name = "User"
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Account deleted successfully',
            'message_ar': 'تم حذف الحساب بنجاح'
        }), 200
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Delete account error: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'Failed to delete account',
            'message_ar': 'فشل في حذف الحساب'
        }), 500

@users_bp.route('/stats', methods=['GET'])
@jwt_required()
def get_user_stats():
    """Get user statistics"""
    try:
        current_identity = get_jwt_identity()
        if current_identity['type'] != 'user':
            return jsonify({
                'success': False,
                'message': 'Only users can view stats',
                'message_ar': 'المستخدمون فقط يمكنهم عرض الإحصائيات'
            }), 403
        
        user_id = current_identity['id']
        
        # Get order stats
        from src.models.order import Order
        total_orders = Order.query.filter_by(user_id=user_id).count()
        completed_orders = Order.query.filter_by(user_id=user_id, status='delivered').count()
        pending_orders = Order.query.filter_by(user_id=user_id, status='pending').count()
        
        # Get total spent
        from sqlalchemy import func
        total_spent_result = db.session.query(
            func.sum(Order.total_amount)
        ).filter_by(
            user_id=user_id,
            status='delivered'
        ).scalar()
        
        total_spent = float(total_spent_result) if total_spent_result else 0.0
        
        # Get favorites count
        from src.models.favorite import UserFavorite
        total_favorites = UserFavorite.query.filter_by(user_id=user_id).count()
        
        # Get reviews count
        from src.models.review import Review
        total_reviews = Review.query.filter_by(user_id=user_id).count()
        
        return jsonify({
            'success': True,
            'data': {
                'orders': {
                    'total': total_orders,
                    'completed': completed_orders,
                    'pending': pending_orders
                },
                'total_spent': total_spent,
                'total_favorites': total_favorites,
                'total_reviews': total_reviews
            }
        }), 200
        
    except Exception as e:
        current_app.logger.error(f"Get user stats error: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'Failed to fetch user statistics',
            'message_ar': 'فشل في جلب إحصائيات المستخدم'
        }), 500

