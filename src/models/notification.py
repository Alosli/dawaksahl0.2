import uuid
from datetime import datetime
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy import Column, String, Boolean, DateTime, Date, Enum, Text, ForeignKey, Integer, Float
from sqlalchemy.orm import relationship
from src.models import db

class Notification(db.Model):
    """Notification model with multilingual support."""
    
    __tablename__ = 'notifications'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey('users.id'), nullable=False)
    
    # Notification content
    title = Column(String(200), nullable=False)
    title_ar = Column(String(200), nullable=False)
    message = Column(Text, nullable=False)
    message_ar = Column(Text, nullable=False)
    
    # Notification metadata
    notification_type = Column(Enum(
        'order',
        'prescription',
        'chat',
        'system',
        'promotion',
        'reminder',
        'security',
        name='notification_types'
    ), nullable=False)
    
    # Related entity ID (order_id, prescription_id, etc.)
    related_id = Column(String(50), nullable=True)
    related_type = Column(String(50), nullable=True)  # 'order', 'prescription', etc.
    
    # Action URL or deep link
    action_url = Column(String(500), nullable=True)
    
    # Priority level
    priority = Column(Enum(
        'low',
        'normal',
        'high',
        'urgent',
        name='notification_priorities'
    ), default='normal')
    
    # Status flags
    is_read = Column(Boolean, default=False)
    is_push_sent = Column(Boolean, default=False)
    is_email_sent = Column(Boolean, default=False)
    is_sms_sent = Column(Boolean, default=False)
    
    # Delivery timestamps
    push_sent_at = Column(DateTime, nullable=True)
    email_sent_at = Column(DateTime, nullable=True)
    sms_sent_at = Column(DateTime, nullable=True)
    read_at = Column(DateTime, nullable=True)
    
    # Expiry
    expires_at = Column(DateTime, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = relationship('User', back_populates='notifications')
    
    def __repr__(self):
        return f'<Notification {self.notification_type} for {self.user_id}>'
    
    def to_dict(self, language='en'):
        """Convert notification to dictionary with language support."""
        data = {
            'id': str(self.id),
            'user_id': str(self.user_id),
            'title': self.title_ar if language == 'ar' else self.title,
            'message': self.message_ar if language == 'ar' else self.message,
            'notification_type': self.notification_type,
            'notification_type_display': self.get_type_display(language),
            'related_id': self.related_id,
            'related_type': self.related_type,
            'action_url': self.action_url,
            'priority': self.priority,
            'priority_display': self.get_priority_display(language),
            'is_read': self.is_read,
            'is_push_sent': self.is_push_sent,
            'is_email_sent': self.is_email_sent,
            'is_sms_sent': self.is_sms_sent,
            'read_at': self.read_at.isoformat() if self.read_at else None,
            'expires_at': self.expires_at.isoformat() if self.expires_at else None,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat(),
            'is_expired': self.is_expired(),
            'time_ago': self.get_time_ago(language)
        }
        
        return data
    
    def get_type_display(self, language='en'):
        """Get human-readable notification type in specified language."""
        type_translations = {
            'order': {'en': 'Order Update', 'ar': 'تحديث الطلب'},
            'prescription': {'en': 'Prescription Update', 'ar': 'تحديث الوصفة'},
            'chat': {'en': 'New Message', 'ar': 'رسالة جديدة'},
            'system': {'en': 'System Notification', 'ar': 'إشعار النظام'},
            'promotion': {'en': 'Promotion', 'ar': 'عرض ترويجي'},
            'reminder': {'en': 'Reminder', 'ar': 'تذكير'},
            'security': {'en': 'Security Alert', 'ar': 'تنبيه أمني'}
        }
        return type_translations.get(self.notification_type, {}).get(language, self.notification_type)
    
    def get_priority_display(self, language='en'):
        """Get human-readable priority in specified language."""
        priority_translations = {
            'low': {'en': 'Low Priority', 'ar': 'أولوية منخفضة'},
            'normal': {'en': 'Normal Priority', 'ar': 'أولوية عادية'},
            'high': {'en': 'High Priority', 'ar': 'أولوية عالية'},
            'urgent': {'en': 'Urgent', 'ar': 'عاجل'}
        }
        return priority_translations.get(self.priority, {}).get(language, self.priority)
    
    def get_time_ago(self, language='en'):
        """Get human-readable time ago in specified language."""
        from datetime import timedelta
        
        now = datetime.utcnow()
        diff = now - self.created_at
        
        if diff < timedelta(minutes=1):
            return {'en': 'Just now', 'ar': 'الآن'}[language]
        elif diff < timedelta(hours=1):
            minutes = int(diff.total_seconds() / 60)
            if language == 'ar':
                return f'منذ {minutes} دقيقة' if minutes == 1 else f'منذ {minutes} دقائق'
            else:
                return f'{minutes} minute ago' if minutes == 1 else f'{minutes} minutes ago'
        elif diff < timedelta(days=1):
            hours = int(diff.total_seconds() / 3600)
            if language == 'ar':
                return f'منذ {hours} ساعة' if hours == 1 else f'منذ {hours} ساعات'
            else:
                return f'{hours} hour ago' if hours == 1 else f'{hours} hours ago'
        elif diff < timedelta(days=7):
            days = diff.days
            if language == 'ar':
                return f'منذ {days} يوم' if days == 1 else f'منذ {days} أيام'
            else:
                return f'{days} day ago' if days == 1 else f'{days} days ago'
        else:
            return self.created_at.strftime('%Y-%m-%d')
    
    def is_expired(self):
        """Check if notification is expired."""
        if self.expires_at:
            return datetime.utcnow() > self.expires_at
        return False
    
    def mark_as_read(self):
        """Mark notification as read."""
        if not self.is_read:
            self.is_read = True
            self.read_at = datetime.utcnow()
    
    def can_be_sent_via_push(self):
        """Check if notification can be sent via push."""
        return not self.is_push_sent and not self.is_expired()
    
    def can_be_sent_via_email(self):
        """Check if notification can be sent via email."""
        return not self.is_email_sent and not self.is_expired()
    
    def can_be_sent_via_sms(self):
        """Check if notification can be sent via SMS."""
        return not self.is_sms_sent and not self.is_expired() and self.priority in ['high', 'urgent']
    
    @staticmethod
    def create_order_notification(user_id, order_id, status, language='ar'):
        """Create an order status notification."""
        status_messages = {
            'confirmed': {
                'en': {'title': 'Order Confirmed', 'message': 'Your order has been confirmed and is being prepared.'},
                'ar': {'title': 'تم تأكيد الطلب', 'message': 'تم تأكيد طلبك وهو قيد التحضير.'}
            },
            'ready': {
                'en': {'title': 'Order Ready', 'message': 'Your order is ready for pickup or delivery.'},
                'ar': {'title': 'الطلب جاهز', 'message': 'طلبك جاهز للاستلام أو التوصيل.'}
            },
            'delivered': {
                'en': {'title': 'Order Delivered', 'message': 'Your order has been successfully delivered.'},
                'ar': {'title': 'تم توصيل الطلب', 'message': 'تم توصيل طلبك بنجاح.'}
            }
        }
        
        messages = status_messages.get(status, {})
        en_msg = messages.get('en', {'title': 'Order Update', 'message': f'Order status updated to {status}'})
        ar_msg = messages.get('ar', {'title': 'تحديث الطلب', 'message': f'تم تحديث حالة الطلب إلى {status}'})
        
        return Notification(
            user_id=user_id,
            title=en_msg['title'],
            title_ar=ar_msg['title'],
            message=en_msg['message'],
            message_ar=ar_msg['message'],
            notification_type='order',
            related_id=str(order_id),
            related_type='order',
            priority='normal'
        )

