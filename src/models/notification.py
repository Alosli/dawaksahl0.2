from datetime import datetime
from src.models import db
import uuid
import json

class Notification(db.Model):
    """Notification model for system alerts and updates"""
    __tablename__ = 'notifications'
    
    # Primary Key
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    
    # Recipients (either user or pharmacy)
    user_id = db.Column(db.String(36), db.ForeignKey('users.id'))
    pharmacy_id = db.Column(db.String(36), db.ForeignKey('pharmacies.id'))
    
    # Notification Type
    notification_type = db.Column(db.Enum(
        'order_status', 'payment', 'delivery', 'prescription', 'product', 'pharmacy',
        'system', 'promotion', 'reminder', 'chat', 'review', 'security', name='notification_types'
    ), nullable=False)
    
    # Notification Category
    category = db.Column(db.Enum(
        'info', 'success', 'warning', 'error', 'urgent', name='notification_categories'
    ), default='info')
    
    # Content (Arabic + English)
    title = db.Column(db.String(255), nullable=False)
    title_ar = db.Column(db.String(255))
    message = db.Column(db.Text, nullable=False)
    message_ar = db.Column(db.Text)
    
    # Action Information
    action_type = db.Column(db.String(50))  # 'view_order', 'open_chat', 'view_product', etc.
    action_url = db.Column(db.String(500))
    action_data = db.Column(db.Text)  # JSON for additional action data
    
    # Related Entities
    related_order_id = db.Column(db.String(36))
    related_product_id = db.Column(db.Integer)
    related_pharmacy_id = db.Column(db.String(36))
    related_conversation_id = db.Column(db.String(36))
    
    # Status
    is_read = db.Column(db.Boolean, default=False)
    is_sent = db.Column(db.Boolean, default=False)
    is_email_sent = db.Column(db.Boolean, default=False)
    is_sms_sent = db.Column(db.Boolean, default=False)
    is_push_sent = db.Column(db.Boolean, default=False)
    
    # Priority
    priority = db.Column(db.Enum(
        'low', 'normal', 'high', 'urgent', name='notification_priorities'
    ), default='normal')
    
    # Scheduling
    scheduled_for = db.Column(db.DateTime)  # For scheduled notifications
    expires_at = db.Column(db.DateTime)  # When notification expires
    
    # Delivery Channels
    send_email = db.Column(db.Boolean, default=False)
    send_sms = db.Column(db.Boolean, default=False)
    send_push = db.Column(db.Boolean, default=True)
    send_in_app = db.Column(db.Boolean, default=True)
    
    # meta_data
    meta_data = db.Column(db.Text)  # JSON for additional data
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    read_at = db.Column(db.DateTime)
    sent_at = db.Column(db.DateTime)
    
    def get_meta_data(self):
        """Get meta_data as dictionary"""
        if self.meta_data:
            try:
                return json.loads(self.meta_data)
            except:
                return {}
        return {}
    
    def set_meta_data(self, data):
        """Set meta_data from dictionary"""
        if data:
            self.meta_data = json.dumps(data, ensure_ascii=False)
        else:
            self.meta_data = None
    
    def get_action_data(self):
        """Get action data as dictionary"""
        if self.action_data:
            try:
                return json.loads(self.action_data)
            except:
                return {}
        return {}
    
    def set_action_data(self, data):
        """Set action data from dictionary"""
        if data:
            self.action_data = json.dumps(data, ensure_ascii=False)
        else:
            self.action_data = None
    
    def get_localized_title(self, language='ar'):
        """Get title in specified language"""
        if language == 'ar' and self.title_ar:
            return self.title_ar
        return self.title
    
    def get_localized_message(self, language='ar'):
        """Get message in specified language"""
        if language == 'ar' and self.message_ar:
            return self.message_ar
        return self.message
    
    def mark_as_read(self):
        """Mark notification as read"""
        if not self.is_read:
            self.is_read = True
            self.read_at = datetime.utcnow()
    
    def mark_as_sent(self):
        """Mark notification as sent"""
        if not self.is_sent:
            self.is_sent = True
            self.sent_at = datetime.utcnow()
    
    def is_expired(self):
        """Check if notification is expired"""
        if not self.expires_at:
            return False
        return datetime.utcnow() > self.expires_at
    
    def should_be_sent(self):
        """Check if notification should be sent now"""
        if self.is_sent:
            return False
        
        if self.is_expired():
            return False
        
        if self.scheduled_for and datetime.utcnow() < self.scheduled_for:
            return False
        
        return True
    
    def get_recipient_info(self):
        """Get recipient information"""
        if self.user_id:
            return {
                'type': 'user',
                'id': self.user_id,
                'user': self.user.to_dict() if self.user else None
            }
        elif self.pharmacy_id:
            return {
                'type': 'pharmacy',
                'id': self.pharmacy_id,
                'pharmacy': self.pharmacy.to_dict() if self.pharmacy else None
            }
        return None
    
    def get_icon(self):
        """Get icon based on notification type and category"""
        icons = {
            'order_status': '📦',
            'payment': '💳',
            'delivery': '🚚',
            'prescription': '💊',
            'product': '🏷️',
            'pharmacy': '🏥',
            'system': '⚙️',
            'promotion': '🎉',
            'reminder': '⏰',
            'chat': '💬',
            'review': '⭐',
            'security': '🔒'
        }
        return icons.get(self.notification_type, '📢')
    
    def get_color(self):
        """Get color based on category"""
        colors = {
            'info': '#3B82F6',
            'success': '#10B981',
            'warning': '#F59E0B',
            'error': '#EF4444',
            'urgent': '#DC2626'
        }
        return colors.get(self.category, '#6B7280')
    
    def to_dict(self, language='ar'):
        """Convert notification to dictionary"""
        return {
            'id': self.id,
            'recipient': self.get_recipient_info(),
            'notification_type': self.notification_type,
            'category': self.category,
            'title': self.get_localized_title(language),
            'message': self.get_localized_message(language),
            'action': {
                'type': self.action_type,
                'url': self.action_url,
                'data': self.get_action_data()
            } if self.action_type else None,
            'related_entities': {
                'order_id': self.related_order_id,
                'product_id': self.related_product_id,
                'pharmacy_id': self.related_pharmacy_id,
                'conversation_id': self.related_conversation_id
            },
            'status': {
                'is_read': self.is_read,
                'is_sent': self.is_sent,
                'is_email_sent': self.is_email_sent,
                'is_sms_sent': self.is_sms_sent,
                'is_push_sent': self.is_push_sent
            },
            'priority': self.priority,
            'delivery_channels': {
                'email': self.send_email,
                'sms': self.send_sms,
                'push': self.send_push,
                'in_app': self.send_in_app
            },
            'scheduling': {
                'scheduled_for': self.scheduled_for.isoformat() if self.scheduled_for else None,
                'expires_at': self.expires_at.isoformat() if self.expires_at else None,
                'is_expired': self.is_expired()
            },
            'ui': {
                'icon': self.get_icon(),
                'color': self.get_color()
            },
            'meta_data': self.get_meta_data(),
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat(),
            'read_at': self.read_at.isoformat() if self.read_at else None,
            'sent_at': self.sent_at.isoformat() if self.sent_at else None
        }
    
    @classmethod
    def create_order_notification(cls, user_id, order_id, status, language='ar'):
        """Create order status notification"""
        status_messages = {
            'confirmed': {
                'title': 'Order Confirmed',
                'title_ar': 'تم تأكيد الطلب',
                'message': 'Your order has been confirmed and is being prepared.',
                'message_ar': 'تم تأكيد طلبك وجاري تحضيره.'
            },
            'ready': {
                'title': 'Order Ready',
                'title_ar': 'الطلب جاهز',
                'message': 'Your order is ready for pickup or delivery.',
                'message_ar': 'طلبك جاهز للاستلام أو التوصيل.'
            },
            'delivered': {
                'title': 'Order Delivered',
                'title_ar': 'تم توصيل الطلب',
                'message': 'Your order has been successfully delivered.',
                'message_ar': 'تم توصيل طلبك بنجاح.'
            },
            'cancelled': {
                'title': 'Order Cancelled',
                'title_ar': 'تم إلغاء الطلب',
                'message': 'Your order has been cancelled.',
                'message_ar': 'تم إلغاء طلبك.'
            }
        }
        
        message_data = status_messages.get(status, {
            'title': 'Order Update',
            'title_ar': 'تحديث الطلب',
            'message': f'Your order status has been updated to {status}.',
            'message_ar': f'تم تحديث حالة طلبك إلى {status}.'
        })
        
        notification = cls(
            user_id=user_id,
            notification_type='order_status',
            category='info' if status != 'cancelled' else 'warning',
            title=message_data['title'],
            title_ar=message_data['title_ar'],
            message=message_data['message'],
            message_ar=message_data['message_ar'],
            action_type='view_order',
            action_url=f'/orders/{order_id}',
            related_order_id=order_id,
            send_push=True,
            send_in_app=True
        )
        
        return notification
    
    @classmethod
    def create_chat_notification(cls, recipient_user_id, recipient_pharmacy_id, conversation_id, sender_name, message_preview, language='ar'):
        """Create chat message notification"""
        if recipient_user_id:
            title = f'New message from {sender_name}'
            title_ar = f'رسالة جديدة من {sender_name}'
        else:
            title = f'New message from {sender_name}'
            title_ar = f'رسالة جديدة من {sender_name}'
        
        notification = cls(
            user_id=recipient_user_id,
            pharmacy_id=recipient_pharmacy_id,
            notification_type='chat',
            category='info',
            title=title,
            title_ar=title_ar,
            message=message_preview[:100] + '...' if len(message_preview) > 100 else message_preview,
            message_ar=message_preview[:100] + '...' if len(message_preview) > 100 else message_preview,
            action_type='open_chat',
            action_url=f'/chat/{conversation_id}',
            related_conversation_id=conversation_id,
            send_push=True,
            send_in_app=True
        )
        
        return notification
    
    @classmethod
    def create_review_notification(cls, pharmacy_id, product_id, reviewer_name, rating, language='ar'):
        """Create new review notification"""
        notification = cls(
            pharmacy_id=pharmacy_id,
            notification_type='review',
            category='info',
            title='New Review Received',
            title_ar='تم استلام تقييم جديد',
            message=f'{reviewer_name} left a {rating}-star review for your product.',
            message_ar=f'{reviewer_name} ترك تقييم {rating} نجوم لمنتجك.',
            action_type='view_product',
            action_url=f'/products/{product_id}',
            related_product_id=product_id,
            send_push=True,
            send_in_app=True
        )
        
        return notification
    
    @classmethod
    def get_unread_count(cls, user_id=None, pharmacy_id=None):
        """Get unread notification count"""
        query = cls.query.filter_by(is_read=False)
        
        if user_id:
            query = query.filter_by(user_id=user_id)
        elif pharmacy_id:
            query = query.filter_by(pharmacy_id=pharmacy_id)
        else:
            return 0
        
        return query.count()
    
    @classmethod
    def mark_all_as_read(cls, user_id=None, pharmacy_id=None):
        """Mark all notifications as read for a user/pharmacy"""
        query = cls.query.filter_by(is_read=False)
        
        if user_id:
            query = query.filter_by(user_id=user_id)
        elif pharmacy_id:
            query = query.filter_by(pharmacy_id=pharmacy_id)
        else:
            return 0
        
        notifications = query.all()
        for notification in notifications:
            notification.mark_as_read()
        
        return len(notifications)
    
    def __repr__(self):
        return f'<Notification {self.notification_type}: {self.title}>'

