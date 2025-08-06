from datetime import datetime
from src.models.user import db
import uuid
import json

class Conversation(db.Model):
    """Conversation model for chat between users and pharmacies"""
    __tablename__ = 'conversations'
    
    # Primary Key
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    
    # Conversation Type
    conversation_type = db.Column(db.Enum(
        'user_pharmacy', 'user_support', 'pharmacy_support', 'group', name='conversation_types'
    ), default='user_pharmacy')
    
    # Conversation Details
    title = db.Column(db.String(255))
    title_ar = db.Column(db.String(255))
    description = db.Column(db.Text)
    description_ar = db.Column(db.Text)
    
    # Related Order (if conversation is about an order)
    order_id = db.Column(db.String(36), db.ForeignKey('orders.id'))
    
    # Status
    status = db.Column(db.Enum(
        'active', 'closed', 'archived', 'blocked', name='conversation_statuses'
    ), default='active')
    
    # Priority (for support conversations)
    priority = db.Column(db.Enum(
        'low', 'normal', 'high', 'urgent', name='conversation_priorities'
    ), default='normal')
    
    # Settings
    is_muted = db.Column(db.Boolean, default=False)
    auto_close_after_hours = db.Column(db.Integer, default=24)
    
    # meta_data
    meta_data = db.Column(db.Text)  # JSON for additional data
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_message_at = db.Column(db.DateTime)
    closed_at = db.Column(db.DateTime)
    
    # Relationships
    participants = db.relationship('ChatParticipant', backref='conversation', lazy='dynamic', cascade='all, delete-orphan')
    messages = db.relationship('Message', backref='conversation', lazy='dynamic', cascade='all, delete-orphan')
    
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
    
    def add_participant(self, user_id=None, pharmacy_id=None, role='member'):
        """Add participant to conversation"""
        participant = ChatParticipant(
            conversation_id=self.id,
            user_id=user_id,
            pharmacy_id=pharmacy_id,
            role=role
        )
        db.session.add(participant)
        return participant
    
    def remove_participant(self, user_id=None, pharmacy_id=None):
        """Remove participant from conversation"""
        query = self.participants
        if user_id:
            query = query.filter_by(user_id=user_id)
        if pharmacy_id:
            query = query.filter_by(pharmacy_id=pharmacy_id)
        
        participant = query.first()
        if participant:
            db.session.delete(participant)
    
    def get_participants_list(self):
        """Get list of all participants"""
        participants = []
        for participant in self.participants:
            if participant.user_id:
                participants.append({
                    'type': 'user',
                    'id': participant.user_id,
                    'user': participant.user.to_dict() if participant.user else None,
                    'role': participant.role,
                    'joined_at': participant.joined_at.isoformat()
                })
            elif participant.pharmacy_id:
                participants.append({
                    'type': 'pharmacy',
                    'id': participant.pharmacy_id,
                    'pharmacy': participant.pharmacy.to_dict() if participant.pharmacy else None,
                    'role': participant.role,
                    'joined_at': participant.joined_at.isoformat()
                })
        return participants
    
    def get_other_participant(self, current_user_id=None, current_pharmacy_id=None):
        """Get the other participant in a two-person conversation"""
        for participant in self.participants:
            if current_user_id and participant.user_id != current_user_id:
                return participant
            elif current_pharmacy_id and participant.pharmacy_id != current_pharmacy_id:
                return participant
        return None
    
    def get_unread_count(self, user_id=None, pharmacy_id=None):
        """Get unread message count for a participant"""
        participant = self.participants.filter(
            db.or_(
                ChatParticipant.user_id == user_id,
                ChatParticipant.pharmacy_id == pharmacy_id
            )
        ).first()
        
        if not participant:
            return 0
        
        return self.messages.filter(
            Message.created_at > participant.last_read_at if participant.last_read_at else datetime.min
        ).count()
    
    def mark_as_read(self, user_id=None, pharmacy_id=None):
        """Mark conversation as read for a participant"""
        participant = self.participants.filter(
            db.or_(
                ChatParticipant.user_id == user_id,
                ChatParticipant.pharmacy_id == pharmacy_id
            )
        ).first()
        
        if participant:
            participant.last_read_at = datetime.utcnow()
    
    def close_conversation(self, reason=None):
        """Close the conversation"""
        self.status = 'closed'
        self.closed_at = datetime.utcnow()
        
        if reason:
            meta_data = self.get_meta_data()
            meta_data['close_reason'] = reason
            self.set_meta_data(meta_data)
    
    def should_auto_close(self):
        """Check if conversation should be auto-closed"""
        if not self.auto_close_after_hours or self.status != 'active':
            return False
        
        if not self.last_message_at:
            return False
        
        hours_since_last_message = (datetime.utcnow() - self.last_message_at).total_seconds() / 3600
        return hours_since_last_message >= self.auto_close_after_hours
    
    def to_dict(self, language='ar', include_messages=False, current_user_id=None, current_pharmacy_id=None):
        """Convert conversation to dictionary"""
        data = {
            'id': self.id,
            'conversation_type': self.conversation_type,
            'title': self.title_ar if language == 'ar' and self.title_ar else self.title,
            'description': self.description_ar if language == 'ar' and self.description_ar else self.description,
            'order_id': self.order_id,
            'status': self.status,
            'priority': self.priority,
            'is_muted': self.is_muted,
            'participants': self.get_participants_list(),
            'unread_count': self.get_unread_count(current_user_id, current_pharmacy_id),
            'meta_data': self.get_meta_data(),
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat(),
            'last_message_at': self.last_message_at.isoformat() if self.last_message_at else None,
            'closed_at': self.closed_at.isoformat() if self.closed_at else None
        }
        
        if include_messages:
            data['messages'] = [
                message.to_dict(language=language) 
                for message in self.messages.order_by(Message.created_at.desc()).limit(50)
            ]
        
        # Add last message preview
        last_message = self.messages.order_by(Message.created_at.desc()).first()
        if last_message:
            data['last_message'] = {
                'id': last_message.id,
                'content': last_message.content[:100] + '...' if len(last_message.content) > 100 else last_message.content,
                'message_type': last_message.message_type,
                'sender_type': 'user' if last_message.sender_user_id else 'pharmacy',
                'created_at': last_message.created_at.isoformat()
            }
        
        return data
    
    def __repr__(self):
        return f'<Conversation {self.id}>'


class Message(db.Model):
    """Message model for individual chat messages"""
    __tablename__ = 'messages'
    
    # Primary Key
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    
    # Foreign Keys
    conversation_id = db.Column(db.String(36), db.ForeignKey('conversations.id'), nullable=False)
    
    # Sender (either user or pharmacy)
    sender_user_id = db.Column(db.String(36), db.ForeignKey('users.id'))
    sender_pharmacy_id = db.Column(db.String(36), db.ForeignKey('pharmacies.id'))
    
    # Message Content
    content = db.Column(db.Text, nullable=False)
    message_type = db.Column(db.Enum(
        'text', 'image', 'file', 'audio', 'video', 'location', 'order', 'prescription', 'system', name='message_types'
    ), default='text')
    
    # File Attachments
    file_url = db.Column(db.String(500))
    file_name = db.Column(db.String(255))
    file_size = db.Column(db.Integer)
    file_type = db.Column(db.String(50))
    
    # Location Data (for location messages)
    latitude = db.Column(db.Float)
    longitude = db.Column(db.Float)
    location_name = db.Column(db.String(255))
    location_name_ar = db.Column(db.String(255))
    
    # Related Data
    related_order_id = db.Column(db.String(36))
    related_product_id = db.Column(db.Integer)
    
    # Message Status
    is_edited = db.Column(db.Boolean, default=False)
    is_deleted = db.Column(db.Boolean, default=False)
    is_system_message = db.Column(db.Boolean, default=False)
    
    # Delivery Status
    delivery_status = db.Column(db.Enum(
        'sent', 'delivered', 'read', 'failed', name='delivery_statuses'
    ), default='sent')
    
    # Reply/Thread Support
    reply_to_message_id = db.Column(db.String(36), db.ForeignKey('messages.id'))
    thread_id = db.Column(db.String(36))
    
    # meta_data
    meta_data = db.Column(db.Text)  # JSON for additional data
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    edited_at = db.Column(db.DateTime)
    deleted_at = db.Column(db.DateTime)
    
    # Relationships
    sender_user = db.relationship('User', foreign_keys=[sender_user_id])
    sender_pharmacy = db.relationship('Pharmacy', foreign_keys=[sender_pharmacy_id])
    reply_to = db.relationship('Message', remote_side=[id], backref='replies')
    
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
    
    def get_sender_info(self):
        """Get sender information"""
        if self.sender_user_id:
            return {
                'type': 'user',
                'id': self.sender_user_id,
                'name': self.sender_user.get_full_name() if self.sender_user else 'Unknown User',
                'avatar': self.sender_user.profile_picture if self.sender_user else None
            }
        elif self.sender_pharmacy_id:
            return {
                'type': 'pharmacy',
                'id': self.sender_pharmacy_id,
                'name': self.sender_pharmacy.pharmacy_name if self.sender_pharmacy else 'Unknown Pharmacy',
                'avatar': None  # Pharmacies might not have avatars
            }
        else:
            return {
                'type': 'system',
                'id': None,
                'name': 'System',
                'avatar': None
            }
    
    def edit_message(self, new_content):
        """Edit message content"""
        self.content = new_content
        self.is_edited = True
        self.edited_at = datetime.utcnow()
    
    def delete_message(self, soft_delete=True):
        """Delete message (soft or hard delete)"""
        if soft_delete:
            self.is_deleted = True
            self.deleted_at = datetime.utcnow()
            self.content = "This message was deleted"
        else:
            db.session.delete(self)
    
    def mark_as_read(self):
        """Mark message as read"""
        self.delivery_status = 'read'
    
    def get_file_info(self):
        """Get file attachment information"""
        if self.file_url:
            return {
                'url': self.file_url,
                'name': self.file_name,
                'size': self.file_size,
                'type': self.file_type,
                'is_image': self.file_type.startswith('image/') if self.file_type else False,
                'is_video': self.file_type.startswith('video/') if self.file_type else False,
                'is_audio': self.file_type.startswith('audio/') if self.file_type else False
            }
        return None
    
    def get_location_info(self, language='ar'):
        """Get location information"""
        if self.latitude and self.longitude:
            return {
                'latitude': self.latitude,
                'longitude': self.longitude,
                'name': self.location_name_ar if language == 'ar' and self.location_name_ar else self.location_name,
                'google_maps_url': f"https://maps.google.com/?q={self.latitude},{self.longitude}"
            }
        return None
    
    def to_dict(self, language='ar'):
        """Convert message to dictionary"""
        data = {
            'id': self.id,
            'conversation_id': self.conversation_id,
            'sender': self.get_sender_info(),
            'content': self.content if not self.is_deleted else "This message was deleted",
            'message_type': self.message_type,
            'delivery_status': self.delivery_status,
            'is_edited': self.is_edited,
            'is_deleted': self.is_deleted,
            'is_system_message': self.is_system_message,
            'reply_to_message_id': self.reply_to_message_id,
            'thread_id': self.thread_id,
            'related_order_id': self.related_order_id,
            'related_product_id': self.related_product_id,
            'meta_data': self.get_meta_data(),
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat(),
            'edited_at': self.edited_at.isoformat() if self.edited_at else None,
            'deleted_at': self.deleted_at.isoformat() if self.deleted_at else None
        }
        
        # Add file info if applicable
        file_info = self.get_file_info()
        if file_info:
            data['file'] = file_info
        
        # Add location info if applicable
        location_info = self.get_location_info(language)
        if location_info:
            data['location'] = location_info
        
        # Add reply info if applicable
        if self.reply_to:
            data['reply_to'] = {
                'id': self.reply_to.id,
                'content': self.reply_to.content[:100] + '...' if len(self.reply_to.content) > 100 else self.reply_to.content,
                'sender': self.reply_to.get_sender_info()
            }
        
        return data
    
    def __repr__(self):
        return f'<Message {self.id}>'


class ChatParticipant(db.Model):
    """Chat participant model for managing conversation membership"""
    __tablename__ = 'chat_participants'
    
    # Primary Key
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    
    # Foreign Keys
    conversation_id = db.Column(db.String(36), db.ForeignKey('conversations.id'), nullable=False)
    user_id = db.Column(db.String(36), db.ForeignKey('users.id'))
    pharmacy_id = db.Column(db.String(36), db.ForeignKey('pharmacies.id'))
    
    # Participant Role
    role = db.Column(db.Enum(
        'member', 'admin', 'moderator', 'support', name='participant_roles'
    ), default='member')
    
    # Participant Status
    status = db.Column(db.Enum(
        'active', 'left', 'removed', 'blocked', name='participant_statuses'
    ), default='active')
    
    # Settings
    is_muted = db.Column(db.Boolean, default=False)
    notifications_enabled = db.Column(db.Boolean, default=True)
    
    # Read Status
    last_read_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Timestamps
    joined_at = db.Column(db.DateTime, default=datetime.utcnow)
    left_at = db.Column(db.DateTime)
    
    # Relationships
    user = db.relationship('User', foreign_keys=[user_id])
    pharmacy = db.relationship('Pharmacy', foreign_keys=[pharmacy_id])
    
    def leave_conversation(self):
        """Leave the conversation"""
        self.status = 'left'
        self.left_at = datetime.utcnow()
    
    def rejoin_conversation(self):
        """Rejoin the conversation"""
        self.status = 'active'
        self.left_at = None
        self.joined_at = datetime.utcnow()
    
    def mute_conversation(self):
        """Mute conversation notifications"""
        self.is_muted = True
        self.notifications_enabled = False
    
    def unmute_conversation(self):
        """Unmute conversation notifications"""
        self.is_muted = False
        self.notifications_enabled = True
    
    def to_dict(self):
        """Convert participant to dictionary"""
        return {
            'id': self.id,
            'conversation_id': self.conversation_id,
            'user_id': self.user_id,
            'pharmacy_id': self.pharmacy_id,
            'user': self.user.to_dict() if self.user else None,
            'pharmacy': self.pharmacy.to_dict() if self.pharmacy else None,
            'role': self.role,
            'status': self.status,
            'is_muted': self.is_muted,
            'notifications_enabled': self.notifications_enabled,
            'last_read_at': self.last_read_at.isoformat() if self.last_read_at else None,
            'joined_at': self.joined_at.isoformat(),
            'left_at': self.left_at.isoformat() if self.left_at else None
        }
    
    def __repr__(self):
        participant_type = 'User' if self.user_id else 'Pharmacy'
        participant_id = self.user_id or self.pharmacy_id
        return f'<ChatParticipant {participant_type}:{participant_id}>'

