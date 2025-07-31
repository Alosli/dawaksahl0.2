from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity
from marshmallow import ValidationError, Schema, fields, validate
import json

from src.models import db
from src.models.user import User, UserAddress, UserMedicalInfo, DeviceToken
from src.utils.helpers import (
    success_response, error_response, validate_json_request,
    get_current_user, save_avatar, get_pagination_params, paginate_query
)

users_bp = Blueprint('users', __name__)

# Schemas for user management
class UpdateProfileSchema(Schema):
    """Schema for updating user profile."""
    first_name = fields.Str(validate=validate.Length(min=2, max=100))
    last_name = fields.Str(validate=validate.Length(min=2, max=100))
    phone = fields.Str(validate=validate.Length(max=20))
    date_of_birth = fields.Date()
    gender = fields.Str(validate=validate.OneOf(['male', 'female']))

class AddressSchema(Schema):
    """Schema for address management."""
    country = fields.Str(validate=validate.Length(max=10), load_default='SA')
    city = fields.Str(required=True, validate=validate.Length(max=100))
    district = fields.Str(required=True, validate=validate.Length(max=100))
    street = fields.Str(required=True, validate=validate.Length(max=255))
    building_number = fields.Str(required=True, validate=validate.Length(max=20))
    postal_code = fields.Str(required=True, validate=validate.Length(max=20))
    address_type = fields.Str(validate=validate.OneOf(['home', 'work', 'other']), load_default='home')
    is_default = fields.Bool(load_default=False)

class MedicalInfoSchema(Schema):
    """Schema for medical information."""
    chronic_conditions = fields.List(fields.Str())
    allergies = fields.List(fields.Str())
    current_medications = fields.List(fields.Str())
    emergency_contact = fields.Str(validate=validate.Length(max=20))
    insurance_provider = fields.Str(validate=validate.Length(max=100))
    insurance_number = fields.Str(validate=validate.Length(max=50))
    blood_type = fields.Str(validate=validate.Length(max=5))
    height = fields.Float()
    weight = fields.Float()

class DeviceTokenSchema(Schema):
    """Schema for device token registration."""
    token = fields.Str(required=True, validate=validate.Length(max=255))
    device_type = fields.Str(required=True, validate=validate.OneOf(['ios', 'android', 'web']))

# Initialize schemas
update_profile_schema = UpdateProfileSchema()
address_schema = AddressSchema()
medical_info_schema = MedicalInfoSchema()
device_token_schema = DeviceTokenSchema()

@users_bp.route('/profile', methods=['GET'])
@jwt_required()
def get_profile():
    """Get current user profile with multilingual support."""
    
    user = get_current_user()
    language = request.args.get('lang', 'ar')
    
    profile_data = user.to_dict()
    
    # Include addresses
    profile_data['addresses'] = [addr.to_dict() for addr in user.addresses]
    
    # Include medical info for patients
    if user.user_type == 'patient' and user.medical_info:
        profile_data['medical_info'] = user.medical_info.to_dict()
    
    # Include pharmacy info for pharmacies
    if user.user_type == 'pharmacy' and user.pharmacy:
        profile_data['pharmacy'] = user.pharmacy.to_dict(language=language)
    
    return success_response(
        profile_data,
        "Profile retrieved successfully",
        "تم استرداد الملف الشخصي بنجاح"
    )

@users_bp.route('/profile', methods=['PUT'])
@jwt_required()
def update_profile():
    """Update user profile."""
    
    # Validate JSON request
    validation_error = validate_json_request()
    if validation_error:
        return validation_error
    
    try:
        # Validate request data
        data = update_profile_schema.load(request.json)
    except ValidationError as err:
        return error_response(
            "Validation failed",
            "فشل في التحقق من صحة البيانات",
            400,
            err.messages
        )
    
    user = get_current_user()
    
    # Check if phone number is already taken by another user
    if 'phone' in data and data['phone'] != user.phone:
        existing_phone = User.query.filter_by(phone=data['phone']).first()
        if existing_phone and existing_phone.id != user.id:
            return error_response(
                "Phone number already exists",
                "رقم الهاتف موجود بالفعل",
                409
            )
    
    # Update user fields
    for field, value in data.items():
        setattr(user, field, value)
    
    try:
        db.session.commit()
        
        return success_response(
            user.to_dict(),
            "Profile updated successfully",
            "تم تحديث الملف الشخصي بنجاح"
        )
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Profile update error: {e}")
        return error_response(
            "Failed to update profile",
            "فشل في تحديث الملف الشخصي",
            500
        )

@users_bp.route('/upload-avatar', methods=['POST'])
@jwt_required()
def upload_avatar():
    """Upload user avatar."""
    
    if 'avatar' not in request.files:
        return error_response(
            "No avatar file provided",
            "لم يتم توفير ملف الصورة الشخصية",
            400
        )
    
    file = request.files['avatar']
    if file.filename == '':
        return error_response(
            "No file selected",
            "لم يتم اختيار ملف",
            400
        )
    
    user = get_current_user()
    
    # Save avatar
    avatar_path = save_avatar(file, user.id)
    if not avatar_path:
        return error_response(
            "Failed to upload avatar",
            "فشل في رفع الصورة الشخصية",
            400
        )
    
    # Update user avatar URL
    user.avatar_url = f"/uploads/{avatar_path}"
    
    try:
        db.session.commit()
        
        return success_response(
            {'avatar_url': user.avatar_url},
            "Avatar uploaded successfully",
            "تم رفع الصورة الشخصية بنجاح"
        )
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Avatar upload error: {e}")
        return error_response(
            "Failed to save avatar",
            "فشل في حفظ الصورة الشخصية",
            500
        )

@users_bp.route('/addresses', methods=['GET'])
@jwt_required()
def get_addresses():
    """Get user addresses."""
    
    user = get_current_user()
    addresses = [addr.to_dict() for addr in user.addresses]
    
    return success_response(
        addresses,
        "Addresses retrieved successfully",
        "تم استرداد العناوين بنجاح"
    )

@users_bp.route('/addresses', methods=['POST'])
@jwt_required()
def add_address():
    """Add new address."""
    
    # Validate JSON request
    validation_error = validate_json_request()
    if validation_error:
        return validation_error
    
    try:
        # Validate request data
        data = address_schema.load(request.json)
    except ValidationError as err:
        return error_response(
            "Validation failed",
            "فشل في التحقق من صحة البيانات",
            400,
            err.messages
        )
    
    user = get_current_user()
    
    # If this is set as default, unset other default addresses
    if data.get('is_default', False):
        for addr in user.addresses:
            addr.is_default = False
    
    # Create new address
    address = UserAddress(
        user_id=user.id,
        **data
    )
    
    try:
        db.session.add(address)
        db.session.commit()
        
        return success_response(
            address.to_dict(),
            "Address added successfully",
            "تم إضافة العنوان بنجاح",
            201
        )
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Add address error: {e}")
        return error_response(
            "Failed to add address",
            "فشل في إضافة العنوان",
            500
        )

@users_bp.route('/addresses/<address_id>', methods=['PUT'])
@jwt_required()
def update_address(address_id):
    """Update address."""
    
    # Validate JSON request
    validation_error = validate_json_request()
    if validation_error:
        return validation_error
    
    try:
        # Validate request data
        data = address_schema.load(request.json)
    except ValidationError as err:
        return error_response(
            "Validation failed",
            "فشل في التحقق من صحة البيانات",
            400,
            err.messages
        )
    
    user = get_current_user()
    
    # Find address
    address = UserAddress.query.filter_by(id=address_id, user_id=user.id).first()
    if not address:
        return error_response(
            "Address not found",
            "العنوان غير موجود",
            404
        )
    
    # If this is set as default, unset other default addresses
    if data.get('is_default', False):
        for addr in user.addresses:
            if addr.id != address.id:
                addr.is_default = False
    
    # Update address fields
    for field, value in data.items():
        setattr(address, field, value)
    
    try:
        db.session.commit()
        
        return success_response(
            address.to_dict(),
            "Address updated successfully",
            "تم تحديث العنوان بنجاح"
        )
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Update address error: {e}")
        return error_response(
            "Failed to update address",
            "فشل في تحديث العنوان",
            500
        )

@users_bp.route('/addresses/<address_id>', methods=['DELETE'])
@jwt_required()
def delete_address(address_id):
    """Delete address."""
    
    user = get_current_user()
    
    # Find address
    address = UserAddress.query.filter_by(id=address_id, user_id=user.id).first()
    if not address:
        return error_response(
            "Address not found",
            "العنوان غير موجود",
            404
        )
    
    # Don't allow deleting the only address
    if len(user.addresses) == 1:
        return error_response(
            "Cannot delete the only address",
            "لا يمكن حذف العنوان الوحيد",
            400
        )
    
    try:
        db.session.delete(address)
        
        # If this was the default address, set another as default
        if address.is_default and user.addresses:
            user.addresses[0].is_default = True
        
        db.session.commit()
        
        return success_response(
            None,
            "Address deleted successfully",
            "تم حذف العنوان بنجاح"
        )
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Delete address error: {e}")
        return error_response(
            "Failed to delete address",
            "فشل في حذف العنوان",
            500
        )

@users_bp.route('/medical-info', methods=['GET'])
@jwt_required()
def get_medical_info():
    """Get user medical information (patients only)."""
    
    user = get_current_user()
    
    if user.user_type != 'patient':
        return error_response(
            "Medical info is only available for patients",
            "المعلومات الطبية متاحة للمرضى فقط",
            403
        )
    
    if not user.medical_info:
        return success_response(
            {},
            "No medical information found",
            "لم يتم العثور على معلومات طبية"
        )
    
    return success_response(
        user.medical_info.to_dict(),
        "Medical information retrieved successfully",
        "تم استرداد المعلومات الطبية بنجاح"
    )

@users_bp.route('/medical-info', methods=['PUT'])
@jwt_required()
def update_medical_info():
    """Update user medical information (patients only)."""
    
    # Validate JSON request
    validation_error = validate_json_request()
    if validation_error:
        return validation_error
    
    try:
        # Validate request data
        data = medical_info_schema.load(request.json)
    except ValidationError as err:
        return error_response(
            "Validation failed",
            "فشل في التحقق من صحة البيانات",
            400,
            err.messages
        )
    
    user = get_current_user()
    
    if user.user_type != 'patient':
        return error_response(
            "Medical info is only available for patients",
            "المعلومات الطبية متاحة للمرضى فقط",
            403
        )
    
    # Get or create medical info
    medical_info = user.medical_info
    if not medical_info:
        medical_info = UserMedicalInfo(user_id=user.id)
        db.session.add(medical_info)
    
    # Update fields
    for field, value in data.items():
        if field in ['chronic_conditions', 'allergies', 'current_medications']:
            setattr(medical_info, field, json.dumps(value) if value else None)
        else:
            setattr(medical_info, field, value)
    
    try:
        db.session.commit()
        
        return success_response(
            medical_info.to_dict(),
            "Medical information updated successfully",
            "تم تحديث المعلومات الطبية بنجاح"
        )
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Medical info update error: {e}")
        return error_response(
            "Failed to update medical information",
            "فشل في تحديث المعلومات الطبية",
            500
        )

@users_bp.route('/device-tokens', methods=['POST'])
@jwt_required()
def register_device_token():
    """Register device token for push notifications."""
    
    # Validate JSON request
    validation_error = validate_json_request()
    if validation_error:
        return validation_error
    
    try:
        # Validate request data
        data = device_token_schema.load(request.json)
    except ValidationError as err:
        return error_response(
            "Validation failed",
            "فشل في التحقق من صحة البيانات",
            400,
            err.messages
        )
    
    user = get_current_user()
    
    # Check if token already exists
    existing_token = DeviceToken.query.filter_by(
        token=data['token'],
        user_id=user.id
    ).first()
    
    if existing_token:
        # Update existing token
        existing_token.device_type = data['device_type']
        existing_token.is_active = True
        token = existing_token
    else:
        # Create new token
        token = DeviceToken(
            user_id=user.id,
            token=data['token'],
            device_type=data['device_type']
        )
        db.session.add(token)
    
    try:
        db.session.commit()
        
        return success_response(
            token.to_dict(),
            "Device token registered successfully",
            "تم تسجيل رمز الجهاز بنجاح"
        )
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Device token registration error: {e}")
        return error_response(
            "Failed to register device token",
            "فشل في تسجيل رمز الجهاز",
            500
        )

