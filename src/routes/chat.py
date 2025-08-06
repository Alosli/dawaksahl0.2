from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity
from datetime import datetime

from src.models import db
from src.models.chat import Conversation, Message, ChatParticipant
from src.models.user import User
from src.models.pharmacy import Pharmacy
from src.services.auth_service import AuthService

chat_bp = Blueprint('chat', __name__)

@chat_bp.route('/conversations', methods=['GET'])
@jwt_required()
def get_conversations():
    """Get conversations for current user"""
    try:
        current_identity = get_jwt_identity()
        user_id = current_identity['id']
        user_type = current_identity['type']
        
        # Get query parameters
        page = request.args.get('page', 1, type=int)
        per_page = min(request.args.get('per_page', 20, type=int), 100)
        language = request.args.get('language', 'ar')
        
        # Get conversations where user is a participant
        query = Conversation.query.join(ChatParticipant).filter(
            ChatParticipant.user_id == user_id,
            ChatParticipant.user_type == user_type
        ).order_by(Conversation.last_message_at.desc())
        
        # Paginate
        pagination = query.paginate(
            page=page,
            per_page=per_page,
            error_out=False
        )
        
        conversations = []
        for conversation in pagination.items:
            conv_data = conversation.to_dict(language=language)
            
            # Add other participant info
            other_participant = conversation.get_other_participant(user_id, user_type)
            if other_participant:
                conv_data['other_participant'] = other_participant
            
            # Add unread count
            conv_data['unread_count'] = conversation.get_unread_count(user_id, user_type)
            
            conversations.append(conv_data)
        
        return jsonify({
            'success': True,
            'data': {
                'items': conversations,
                'page': page,
                'pages': pagination.pages,
                'per_page': per_page,
                'total': pagination.total,
                'has_next': pagination.has_next,
                'has_prev': pagination.has_prev
            }
        }), 200
        
    except Exception as e:
        current_app.logger.error(f"Get conversations error: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'Failed to fetch conversations',
            'message_ar': 'فشل في جلب المحادثات'
        }), 500

@chat_bp.route('/conversations', methods=['POST'])
@jwt_required()
def create_conversation():
    """Create new conversation"""
    try:
        current_identity = get_jwt_identity()
        user_id = current_identity['id']
        user_type = current_identity['type']
        
        data = request.get_json()
        
        # Validate required fields
        other_user_id = data.get('other_user_id')
        other_user_type = data.get('other_user_type')
        
        if not other_user_id or not other_user_type:
            return jsonify({
                'success': False,
                'message': 'Other user ID and type are required',
                'message_ar': 'معرف المستخدم الآخر ونوعه مطلوبان'
            }), 400
        
        # Check if conversation already exists
        existing_conversation = Conversation.find_between_users(
            user_id, user_type, other_user_id, other_user_type
        )
        
        if existing_conversation:
            return jsonify({
                'success': True,
                'message': 'Conversation already exists',
                'message_ar': 'المحادثة موجودة بالفعل',
                'data': existing_conversation.to_dict()
            }), 200
        
        # Create new conversation
        conversation = Conversation(
            conversation_type=data.get('conversation_type', 'direct'),
            title=data.get('title'),
            title_ar=data.get('title_ar'),
            description=data.get('description'),
            description_ar=data.get('description_ar'),
            order_id=data.get('order_id'),
            created_by_id=user_id,
            created_by_type=user_type
        )
        
        db.session.add(conversation)
        db.session.flush()  # Get conversation ID
        
        # Add participants
        participant1 = ChatParticipant(
            conversation_id=conversation.id,
            user_id=user_id,
            user_type=user_type,
            role='member'
        )
        
        participant2 = ChatParticipant(
            conversation_id=conversation.id,
            user_id=other_user_id,
            user_type=other_user_type,
            role='member'
        )
        
        db.session.add(participant1)
        db.session.add(participant2)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Conversation created successfully',
            'message_ar': 'تم إنشاء المحادثة بنجاح',
            'data': conversation.to_dict()
        }), 201
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Create conversation error: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'Failed to create conversation',
            'message_ar': 'فشل في إنشاء المحادثة'
        }), 500

@chat_bp.route('/conversations/<conversation_id>/messages', methods=['GET'])
@jwt_required()
def get_messages(conversation_id):
    """Get messages in a conversation"""
    try:
        current_identity = get_jwt_identity()
        user_id = current_identity['id']
        user_type = current_identity['type']
        
        # Check if user is participant in conversation
        participant = ChatParticipant.query.filter_by(
            conversation_id=conversation_id,
            user_id=user_id,
            user_type=user_type
        ).first()
        
        if not participant:
            return jsonify({
                'success': False,
                'message': 'Access denied',
                'message_ar': 'الوصول مرفوض'
            }), 403
        
        # Get query parameters
        page = request.args.get('page', 1, type=int)
        per_page = min(request.args.get('per_page', 50, type=int), 100)
        language = request.args.get('language', 'ar')
        
        # Get messages
        query = Message.query.filter_by(
            conversation_id=conversation_id
        ).order_by(Message.created_at.desc())
        
        # Paginate
        pagination = query.paginate(
            page=page,
            per_page=per_page,
            error_out=False
        )
        
        messages = [message.to_dict(language=language) for message in pagination.items]
        
        # Mark messages as read
        Message.query.filter_by(
            conversation_id=conversation_id
        ).filter(
            Message.sender_id != user_id,
            Message.sender_type != user_type,
            Message.is_read == False
        ).update({'is_read': True, 'read_at': datetime.utcnow()})
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'data': {
                'items': messages,
                'page': page,
                'pages': pagination.pages,
                'per_page': per_page,
                'total': pagination.total,
                'has_next': pagination.has_next,
                'has_prev': pagination.has_prev
            }
        }), 200
        
    except Exception as e:
        current_app.logger.error(f"Get messages error: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'Failed to fetch messages',
            'message_ar': 'فشل في جلب الرسائل'
        }), 500

@chat_bp.route('/conversations/<conversation_id>/messages', methods=['POST'])
@jwt_required()
def send_message(conversation_id):
    """Send message in conversation"""
    try:
        current_identity = get_jwt_identity()
        user_id = current_identity['id']
        user_type = current_identity['type']
        
        # Check if user is participant in conversation
        participant = ChatParticipant.query.filter_by(
            conversation_id=conversation_id,
            user_id=user_id,
            user_type=user_type
        ).first()
        
        if not participant:
            return jsonify({
                'success': False,
                'message': 'Access denied',
                'message_ar': 'الوصول مرفوض'
            }), 403
        
        data = request.get_json()
        
        # Validate message content
        if not data.get('content') and not data.get('attachment_url'):
            return jsonify({
                'success': False,
                'message': 'Message content or attachment is required',
                'message_ar': 'محتوى الرسالة أو المرفق مطلوب'
            }), 400
        
        # Create message
        message = Message(
            conversation_id=conversation_id,
            sender_id=user_id,
            sender_type=user_type,
            message_type=data.get('message_type', 'text'),
            content=data.get('content'),
            attachment_url=data.get('attachment_url'),
            attachment_type=data.get('attachment_type'),
            attachment_name=data.get('attachment_name'),
            location_latitude=data.get('location_latitude'),
            location_longitude=data.get('location_longitude'),
            location_name=data.get('location_name'),
            location_name_ar=data.get('location_name_ar'),
            reply_to_message_id=data.get('reply_to_message_id')
        )
        
        db.session.add(message)
        
        # Update conversation last message
        conversation = Conversation.query.get(conversation_id)
        conversation.last_message_at = datetime.utcnow()
        conversation.last_message_content = data.get('content', '')[:100]
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Message sent successfully',
            'message_ar': 'تم إرسال الرسالة بنجاح',
            'data': message.to_dict()
        }), 201
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Send message error: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'Failed to send message',
            'message_ar': 'فشل في إرسال الرسالة'
        }), 500

@chat_bp.route('/messages/<message_id>', methods=['PUT'])
@jwt_required()
def edit_message(message_id):
    """Edit message (sender only)"""
    try:
        current_identity = get_jwt_identity()
        user_id = current_identity['id']
        user_type = current_identity['type']
        
        message = Message.query.filter_by(
            id=message_id,
            sender_id=user_id,
            sender_type=user_type
        ).first()
        
        if not message:
            return jsonify({
                'success': False,
                'message': 'Message not found or access denied',
                'message_ar': 'الرسالة غير موجودة أو الوصول مرفوض'
            }), 404
        
        # Check if message can be edited (within 15 minutes)
        if not message.can_be_edited():
            return jsonify({
                'success': False,
                'message': 'Message can no longer be edited',
                'message_ar': 'لا يمكن تعديل الرسالة بعد الآن'
            }), 400
        
        data = request.get_json()
        new_content = data.get('content')
        
        if not new_content:
            return jsonify({
                'success': False,
                'message': 'Content is required',
                'message_ar': 'المحتوى مطلوب'
            }), 400
        
        message.content = new_content
        message.is_edited = True
        message.edited_at = datetime.utcnow()
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Message edited successfully',
            'message_ar': 'تم تعديل الرسالة بنجاح',
            'data': message.to_dict()
        }), 200
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Edit message error: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'Failed to edit message',
            'message_ar': 'فشل في تعديل الرسالة'
        }), 500

@chat_bp.route('/messages/<message_id>', methods=['DELETE'])
@jwt_required()
def delete_message(message_id):
    """Delete message (sender only)"""
    try:
        current_identity = get_jwt_identity()
        user_id = current_identity['id']
        user_type = current_identity['type']
        
        message = Message.query.filter_by(
            id=message_id,
            sender_id=user_id,
            sender_type=user_type
        ).first()
        
        if not message:
            return jsonify({
                'success': False,
                'message': 'Message not found or access denied',
                'message_ar': 'الرسالة غير موجودة أو الوصول مرفوض'
            }), 404
        
        # Soft delete
        message.is_deleted = True
        message.deleted_at = datetime.utcnow()
        message.content = '[Message deleted]'
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Message deleted successfully',
            'message_ar': 'تم حذف الرسالة بنجاح'
        }), 200
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Delete message error: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'Failed to delete message',
            'message_ar': 'فشل في حذف الرسالة'
        }), 500

@chat_bp.route('/conversations/<conversation_id>/typing', methods=['POST'])
@jwt_required()
def set_typing_status(conversation_id):
    """Set typing status in conversation"""
    try:
        current_identity = get_jwt_identity()
        user_id = current_identity['id']
        user_type = current_identity['type']
        
        # Check if user is participant in conversation
        participant = ChatParticipant.query.filter_by(
            conversation_id=conversation_id,
            user_id=user_id,
            user_type=user_type
        ).first()
        
        if not participant:
            return jsonify({
                'success': False,
                'message': 'Access denied',
                'message_ar': 'الوصول مرفوض'
            }), 403
        
        data = request.get_json()
        is_typing = data.get('is_typing', False)
        
        participant.is_typing = is_typing
        participant.last_typing_at = datetime.utcnow() if is_typing else None
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Typing status updated',
            'message_ar': 'تم تحديث حالة الكتابة'
        }), 200
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Set typing status error: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'Failed to update typing status',
            'message_ar': 'فشل في تحديث حالة الكتابة'
        }), 500

@chat_bp.route('/conversations/<conversation_id>/mute', methods=['PUT'])
@jwt_required()
def mute_conversation(conversation_id):
    """Mute/unmute conversation"""
    try:
        current_identity = get_jwt_identity()
        user_id = current_identity['id']
        user_type = current_identity['type']
        
        participant = ChatParticipant.query.filter_by(
            conversation_id=conversation_id,
            user_id=user_id,
            user_type=user_type
        ).first()
        
        if not participant:
            return jsonify({
                'success': False,
                'message': 'Access denied',
                'message_ar': 'الوصول مرفوض'
            }), 403
        
        data = request.get_json()
        is_muted = data.get('is_muted', False)
        
        participant.is_muted = is_muted
        participant.muted_until = data.get('muted_until')
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Conversation mute status updated',
            'message_ar': 'تم تحديث حالة كتم المحادثة'
        }), 200
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Mute conversation error: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'Failed to update mute status',
            'message_ar': 'فشل في تحديث حالة الكتم'
        }), 500

@chat_bp.route('/unread-count', methods=['GET'])
@jwt_required()
def get_unread_count():
    """Get total unread message count"""
    try:
        current_identity = get_jwt_identity()
        user_id = current_identity['id']
        user_type = current_identity['type']
        
        # Get total unread count across all conversations
        total_unread = 0
        
        conversations = Conversation.query.join(ChatParticipant).filter(
            ChatParticipant.user_id == user_id,
            ChatParticipant.user_type == user_type
        ).all()
        
        for conversation in conversations:
            total_unread += conversation.get_unread_count(user_id, user_type)
        
        return jsonify({
            'success': True,
            'data': {
                'total_unread': total_unread
            }
        }), 200
        
    except Exception as e:
        current_app.logger.error(f"Get unread count error: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'Failed to fetch unread count',
            'message_ar': 'فشل في جلب عدد الرسائل غير المقروءة'
        }), 500

