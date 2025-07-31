import uuid
from datetime import datetime
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy import Column, String, Boolean, DateTime, Date, Enum, Text, ForeignKey, Integer, Float
from sqlalchemy.orm import relationship
from src.models import db

class ChatConversation(db.Model):
    """Chat conversation model with multilingual support."""
    
    __tablename__ = 'chat_conversations'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey('users.id'), nullable=False)
    pharmacy_id = Column(UUID(as_uuid=True), ForeignKey('pharmacies.id'), nullable=False)
    
    # Conversation status
    status = Column(Enum(
        'active',
        'closed',
        'archived',
        name='conversation_statuses'
    ), default='active')
    
    # Conversation metadata
    subject = Column(String(200), nullable=True)
    subject_ar = Column(String(200), nullable=True)
    last_message_at = Column(DateTime, nullable=True)
    
    # Language preference for this conversation
    preferred_language = Column(Enum('en', 'ar', name='conversation_languages'), default='ar')
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = relationship('User', back_populates='chat_conversations')
    pharmacy = relationship('Pharmacy', back_populates='chat_conversations')
    messages = relationship('ChatMessage', back_populates='conversation', cascade='all, delete-orphan', order_by='ChatMessage.created_at')
    
    def __repr__(self):
        return f'<ChatConversation {self.id}>'
    
    def to_dict(self, language='en'):
        """Convert conversation to dictionary with language support."""
        data = {
            'id': str(self.id),
            'user_id': str(self.user_id),
            'pharmacy_id': str(self.pharmacy_id),
            'status': self.status,
            'status_display': self.get_status_display(language),
            'subject': self.subject_ar if language == 'ar' and self.subject_ar else self.subject,
            'last_message_at': self.last_message_at.isoformat() if self.last_message_at else None,
            'preferred_language': self.preferred_language,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat(),
            'unread_count': self.get_unread_count_for_user()
        }
        
        return data
    
    def get_status_display(self, language='en'):
        """Get human-readable status in specified language."""
        status_translations = {
            'active': {'en': 'Active', 'ar': 'نشط'},
            'closed': {'en': 'Closed', 'ar': 'مغلق'},
            'archived': {'en': 'Archived', 'ar': 'مؤرشف'}
        }
        return status_translations.get(self.status, {}).get(language, self.status)
    
    def get_unread_count_for_user(self, user_id=None):
        """Get count of unread messages for a specific user."""
        if user_id is None:
            user_id = self.user_id
        
        return len([msg for msg in self.messages if not msg.is_read and str(msg.sender_id) != str(user_id)])
    
    def get_last_message(self):
        """Get the last message in the conversation."""
        return self.messages[-1] if self.messages else None
    
    def mark_messages_as_read(self, user_id):
        """Mark all messages as read for a specific user."""
        for message in self.messages:
            if str(message.sender_id) != str(user_id) and not message.is_read:
                message.is_read = True
                message.read_at = datetime.utcnow()

class ChatMessage(db.Model):
    """Chat message model with multilingual support."""
    
    __tablename__ = 'chat_messages'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    conversation_id = Column(UUID(as_uuid=True), ForeignKey('chat_conversations.id'), nullable=False)
    sender_id = Column(UUID(as_uuid=True), ForeignKey('users.id'), nullable=False)
    
    # Message content
    message_type = Column(Enum(
        'text',
        'image',
        'file',
        'prescription',
        'system',
        name='message_types'
    ), default='text')
    
    content = Column(Text, nullable=False)
    content_ar = Column(Text, nullable=True)  # For system messages or translations
    
    # File attachments
    file_url = Column(String(500), nullable=True)
    file_name = Column(String(255), nullable=True)
    file_size = Column(Integer, nullable=True)
    
    # Message metadata
    is_read = Column(Boolean, default=False)
    read_at = Column(DateTime, nullable=True)
    
    # Language of the message
    message_language = Column(Enum('en', 'ar', 'system', name='message_languages'), default='ar')
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    conversation = relationship('ChatConversation', back_populates='messages')
    sender = relationship('User', back_populates='sent_messages')
    
    def __repr__(self):
        return f'<ChatMessage {self.message_type} from {self.sender_id}>'
    
    def to_dict(self, language='en'):
        """Convert message to dictionary with language support."""
        data = {
            'id': str(self.id),
            'conversation_id': str(self.conversation_id),
            'sender_id': str(self.sender_id),
            'message_type': self.message_type,
            'message_type_display': self.get_message_type_display(language),
            'file_url': self.file_url,
            'file_name': self.file_name,
            'file_size': self.file_size,
            'is_read': self.is_read,
            'read_at': self.read_at.isoformat() if self.read_at else None,
            'message_language': self.message_language,
            'created_at': self.created_at.isoformat()
        }
        
        # Add content based on message type and language
        if self.message_type == 'system':
            data['content'] = self.content_ar if language == 'ar' and self.content_ar else self.content
        else:
            data['content'] = self.content
        
        return data
    
    def get_message_type_display(self, language='en'):
        """Get human-readable message type in specified language."""
        type_translations = {
            'text': {'en': 'Text Message', 'ar': 'رسالة نصية'},
            'image': {'en': 'Image', 'ar': 'صورة'},
            'file': {'en': 'File', 'ar': 'ملف'},
            'prescription': {'en': 'Prescription', 'ar': 'وصفة طبية'},
            'system': {'en': 'System Message', 'ar': 'رسالة النظام'}
        }
        return type_translations.get(self.message_type, {}).get(language, self.message_type)
    
    def is_from_pharmacy(self):
        """Check if message is from pharmacy user."""
        return self.sender.user_type == 'pharmacy'
    
    def is_recent(self, minutes=5):
        """Check if message is recent (within specified minutes)."""
        from datetime import timedelta
        return (datetime.utcnow() - self.created_at) <= timedelta(minutes=minutes)
    
    def can_be_edited(self):
        """Check if message can be edited (only text messages within 5 minutes)."""
        return self.message_type == 'text' and self.is_recent(minutes=5)

