from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity
from datetime import datetime

from src.models import db
from src.models.notification import Notification
from src.services.auth_service import AuthService

notifications_bp = Blueprint('notifications', __name__)

@notifications_bp.route('', methods=['GET'])
@jwt_required()
def get_notifications():
    """Get notifications for current user"""
    try:
        current_identity = get_jwt_identity()
        user_id = current_identity['id']
        user_type = current_identity['type']
        
        # Get query parameters
        page = request.args.get('page', 1, type=int)
        per_page = min(request.args.get('per_page', 20, type=int), 100)
        language = request.args.get('language', 'ar')
        category = request.args.get('category')  # info, warning, error, success
        is_read = request.args.get('is_read', type=bool)
        
        # Build query based on user type
        if user_type == 'user':
            query = Notification.query.filter_by(user_id=user_id)
        elif user_type == 'pharmacy':
            query = Notification.query.filter_by(pharmacy_id=user_id)
        else:
            return jsonify({
                'success': False,
                'message': 'Invalid user type',
                'message_ar': 'نوع المستخدم غير صحيح'
            }), 400
        
        # Apply filters
        if category:
            query = query.filter_by(category=category)
        
        if is_read is not None:
            query = query.filter_by(is_read=is_read)
        
        # Order by creation date (newest first)
        query = query.order_by(Notification.created_at.desc())
        
        # Paginate
        pagination = query.paginate(
            page=page,
            per_page=per_page,
            error_out=False
        )
        
        notifications = [notification.to_dict(language=language) for notification in pagination.items]
        
        # Get unread count
        unread_count = Notification.query.filter_by(
            user_id=user_id if user_type == 'user' else None,
            pharmacy_id=user_id if user_type == 'pharmacy' else None,
            is_read=False
        ).count()
        
        return jsonify({
            'success': True,
            'data': {
                'items': notifications,
                'page': page,
                'pages': pagination.pages,
                'per_page': per_page,
                'total': pagination.total,
                'has_next': pagination.has_next,
                'has_prev': pagination.has_prev,
                'unread_count': unread_count
            }
        }), 200
        
    except Exception as e:
        current_app.logger.error(f"Get notifications error: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'Failed to fetch notifications',
            'message_ar': 'فشل في جلب الإشعارات'
        }), 500

@notifications_bp.route('/<notification_id>', methods=['GET'])
@jwt_required()
def get_notification(notification_id):
    """Get single notification"""
    try:
        current_identity = get_jwt_identity()
        user_id = current_identity['id']
        user_type = current_identity['type']
        language = request.args.get('language', 'ar')
        
        # Build query based on user type
        if user_type == 'user':
            notification = Notification.query.filter_by(id=notification_id, user_id=user_id).first()
        elif user_type == 'pharmacy':
            notification = Notification.query.filter_by(id=notification_id, pharmacy_id=user_id).first()
        else:
            return jsonify({
                'success': False,
                'message': 'Invalid user type',
                'message_ar': 'نوع المستخدم غير صحيح'
            }), 400
        
        if not notification:
            return jsonify({
                'success': False,
                'message': 'Notification not found',
                'message_ar': 'الإشعار غير موجود'
            }), 404
        
        # Mark as read if not already read
        if not notification.is_read:
            notification.is_read = True
            notification.read_at = datetime.utcnow()
            db.session.commit()
        
        return jsonify({
            'success': True,
            'data': notification.to_dict(language=language)
        }), 200
        
    except Exception as e:
        current_app.logger.error(f"Get notification error: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'Failed to fetch notification',
            'message_ar': 'فشل في جلب الإشعار'
        }), 500

@notifications_bp.route('/<notification_id>/read', methods=['PUT'])
@jwt_required()
def mark_as_read(notification_id):
    """Mark notification as read"""
    try:
        current_identity = get_jwt_identity()
        user_id = current_identity['id']
        user_type = current_identity['type']
        
        # Build query based on user type
        if user_type == 'user':
            notification = Notification.query.filter_by(id=notification_id, user_id=user_id).first()
        elif user_type == 'pharmacy':
            notification = Notification.query.filter_by(id=notification_id, pharmacy_id=user_id).first()
        else:
            return jsonify({
                'success': False,
                'message': 'Invalid user type',
                'message_ar': 'نوع المستخدم غير صحيح'
            }), 400
        
        if not notification:
            return jsonify({
                'success': False,
                'message': 'Notification not found',
                'message_ar': 'الإشعار غير موجود'
            }), 404
        
        notification.is_read = True
        notification.read_at = datetime.utcnow()
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Notification marked as read',
            'message_ar': 'تم تمييز الإشعار كمقروء'
        }), 200
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Mark as read error: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'Failed to mark notification as read',
            'message_ar': 'فشل في تمييز الإشعار كمقروء'
        }), 500

@notifications_bp.route('/mark-all-read', methods=['PUT'])
@jwt_required()
def mark_all_as_read():
    """Mark all notifications as read"""
    try:
        current_identity = get_jwt_identity()
        user_id = current_identity['id']
        user_type = current_identity['type']
        
        # Build query based on user type
        if user_type == 'user':
            notifications = Notification.query.filter_by(user_id=user_id, is_read=False).all()
        elif user_type == 'pharmacy':
            notifications = Notification.query.filter_by(pharmacy_id=user_id, is_read=False).all()
        else:
            return jsonify({
                'success': False,
                'message': 'Invalid user type',
                'message_ar': 'نوع المستخدم غير صحيح'
            }), 400
        
        # Mark all as read
        for notification in notifications:
            notification.is_read = True
            notification.read_at = datetime.utcnow()
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': f'{len(notifications)} notifications marked as read',
            'message_ar': f'تم تمييز {len(notifications)} إشعار كمقروء'
        }), 200
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Mark all as read error: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'Failed to mark notifications as read',
            'message_ar': 'فشل في تمييز الإشعارات كمقروءة'
        }), 500

@notifications_bp.route('/<notification_id>', methods=['DELETE'])
@jwt_required()
def delete_notification(notification_id):
    """Delete notification"""
    try:
        current_identity = get_jwt_identity()
        user_id = current_identity['id']
        user_type = current_identity['type']
        
        # Build query based on user type
        if user_type == 'user':
            notification = Notification.query.filter_by(id=notification_id, user_id=user_id).first()
        elif user_type == 'pharmacy':
            notification = Notification.query.filter_by(id=notification_id, pharmacy_id=user_id).first()
        else:
            return jsonify({
                'success': False,
                'message': 'Invalid user type',
                'message_ar': 'نوع المستخدم غير صحيح'
            }), 400
        
        if not notification:
            return jsonify({
                'success': False,
                'message': 'Notification not found',
                'message_ar': 'الإشعار غير موجود'
            }), 404
        
        db.session.delete(notification)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Notification deleted successfully',
            'message_ar': 'تم حذف الإشعار بنجاح'
        }), 200
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Delete notification error: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'Failed to delete notification',
            'message_ar': 'فشل في حذف الإشعار'
        }), 500

@notifications_bp.route('/clear-all', methods=['DELETE'])
@jwt_required()
def clear_all_notifications():
    """Clear all notifications for current user"""
    try:
        current_identity = get_jwt_identity()
        user_id = current_identity['id']
        user_type = current_identity['type']
        
        # Build query based on user type
        if user_type == 'user':
            notifications = Notification.query.filter_by(user_id=user_id).all()
        elif user_type == 'pharmacy':
            notifications = Notification.query.filter_by(pharmacy_id=user_id).all()
        else:
            return jsonify({
                'success': False,
                'message': 'Invalid user type',
                'message_ar': 'نوع المستخدم غير صحيح'
            }), 400
        
        # Delete all notifications
        for notification in notifications:
            db.session.delete(notification)
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': f'{len(notifications)} notifications cleared',
            'message_ar': f'تم مسح {len(notifications)} إشعار'
        }), 200
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Clear all notifications error: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'Failed to clear notifications',
            'message_ar': 'فشل في مسح الإشعارات'
        }), 500

@notifications_bp.route('/unread-count', methods=['GET'])
@jwt_required()
def get_unread_count():
    """Get unread notification count"""
    try:
        current_identity = get_jwt_identity()
        user_id = current_identity['id']
        user_type = current_identity['type']
        
        # Build query based on user type
        if user_type == 'user':
            unread_count = Notification.query.filter_by(user_id=user_id, is_read=False).count()
        elif user_type == 'pharmacy':
            unread_count = Notification.query.filter_by(pharmacy_id=user_id, is_read=False).count()
        else:
            return jsonify({
                'success': False,
                'message': 'Invalid user type',
                'message_ar': 'نوع المستخدم غير صحيح'
            }), 400
        
        return jsonify({
            'success': True,
            'data': {
                'unread_count': unread_count
            }
        }), 200
        
    except Exception as e:
        current_app.logger.error(f"Get unread count error: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'Failed to fetch unread count',
            'message_ar': 'فشل في جلب عدد الإشعارات غير المقروءة'
        }), 500

@notifications_bp.route('/preferences', methods=['GET'])
@jwt_required()
def get_notification_preferences():
    """Get notification preferences for current user"""
    try:
        current_identity = get_jwt_identity()
        user_id = current_identity['id']
        user_type = current_identity['type']
        
        # Get user/pharmacy to check notification preferences
        if user_type == 'user':
            from src.models.user import User
            user = User.query.get(user_id)
            if not user:
                return jsonify({
                    'success': False,
                    'message': 'User not found',
                    'message_ar': 'المستخدم غير موجود'
                }), 404
            
            preferences = {
                'email_notifications': user.email_notifications,
                'push_notifications': user.push_notifications,
                'sms_notifications': getattr(user, 'sms_notifications', False),
                'order_updates': True,
                'promotional_emails': getattr(user, 'promotional_emails', True),
                'security_alerts': True
            }
        
        elif user_type == 'pharmacy':
            from src.models.pharmacy import Pharmacy
            pharmacy = Pharmacy.query.get(user_id)
            if not pharmacy:
                return jsonify({
                    'success': False,
                    'message': 'Pharmacy not found',
                    'message_ar': 'الصيدلية غير موجودة'
                }), 404
            
            preferences = {
                'email_notifications': pharmacy.email_notifications,
                'push_notifications': pharmacy.push_notifications,
                'sms_notifications': getattr(pharmacy, 'sms_notifications', False),
                'order_notifications': True,
                'inventory_alerts': True,
                'promotional_emails': getattr(pharmacy, 'promotional_emails', True),
                'security_alerts': True
            }
        
        return jsonify({
            'success': True,
            'data': preferences
        }), 200
        
    except Exception as e:
        current_app.logger.error(f"Get notification preferences error: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'Failed to fetch notification preferences',
            'message_ar': 'فشل في جلب تفضيلات الإشعارات'
        }), 500

@notifications_bp.route('/preferences', methods=['PUT'])
@jwt_required()
def update_notification_preferences():
    """Update notification preferences for current user"""
    try:
        current_identity = get_jwt_identity()
        user_id = current_identity['id']
        user_type = current_identity['type']
        
        data = request.get_json()
        
        # Update user/pharmacy notification preferences
        if user_type == 'user':
            from src.models.user import User
            user = User.query.get(user_id)
            if not user:
                return jsonify({
                    'success': False,
                    'message': 'User not found',
                    'message_ar': 'المستخدم غير موجود'
                }), 404
            
            # Update preferences
            if 'email_notifications' in data:
                user.email_notifications = data['email_notifications']
            if 'push_notifications' in data:
                user.push_notifications = data['push_notifications']
        
        elif user_type == 'pharmacy':
            from src.models.pharmacy import Pharmacy
            pharmacy = Pharmacy.query.get(user_id)
            if not pharmacy:
                return jsonify({
                    'success': False,
                    'message': 'Pharmacy not found',
                    'message_ar': 'الصيدلية غير موجودة'
                }), 404
            
            # Update preferences
            if 'email_notifications' in data:
                pharmacy.email_notifications = data['email_notifications']
            if 'push_notifications' in data:
                pharmacy.push_notifications = data['push_notifications']
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Notification preferences updated successfully',
            'message_ar': 'تم تحديث تفضيلات الإشعارات بنجاح'
        }), 200
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Update notification preferences error: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'Failed to update notification preferences',
            'message_ar': 'فشل في تحديث تفضيلات الإشعارات'
        }), 500

