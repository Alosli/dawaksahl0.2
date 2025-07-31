from marshmallow import Schema, fields, validate, validates, ValidationError
from marshmallow_sqlalchemy import SQLAlchemyAutoSchema
from src.models.user import User
from src.utils.helpers import is_valid_email, is_valid_phone

class LoginSchema(Schema):
    """Schema for user login validation."""
    email = fields.Email(required=True, validate=validate.Length(max=120))
    password = fields.Str(required=True, validate=validate.Length(min=6, max=255))
    remember_me = fields.Bool(load_default=False)

class RegisterSchema(Schema):
    """Schema for user registration validation."""
    # Basic info
    email = fields.Email(required=True, validate=validate.Length(max=120))
    password = fields.Str(required=True, validate=validate.Length(min=8, max=255))
    confirm_password = fields.Str(required=True)
    user_type = fields.Str(required=True, validate=validate.OneOf(['patient', 'pharmacy', 'doctor']))
    first_name = fields.Str(required=True, validate=validate.Length(min=2, max=100))
    last_name = fields.Str(required=True, validate=validate.Length(min=2, max=100))
    phone = fields.Str(required=True, validate=validate.Length(max=20))
    date_of_birth = fields.Date(required=False, allow_none=True)
    gender = fields.Str(required=False, validate=validate.OneOf(['male', 'female']), allow_none=True)
    
    # Address info
    country = fields.Str(load_default='SA', validate=validate.Length(max=10))
    city = fields.Str(required=True, validate=validate.Length(max=100))
    district = fields.Str(required=True, validate=validate.Length(max=100))
    street = fields.Str(required=True, validate=validate.Length(max=255))
    building_number = fields.Str(required=True, validate=validate.Length(max=20))
    postal_code = fields.Str(required=True, validate=validate.Length(max=20))
    
    # Pharmacy-specific fields
    pharmacy_name = fields.Str(required=False, validate=validate.Length(max=200), allow_none=True)
    pharmacy_name_ar = fields.Str(required=False, validate=validate.Length(max=200), allow_none=True)
    license_number = fields.Str(required=False, validate=validate.Length(max=50), allow_none=True)
    pharmacist_name = fields.Str(required=False, validate=validate.Length(max=200), allow_none=True)
    pharmacist_license = fields.Str(required=False, validate=validate.Length(max=50), allow_none=True)
    establishment_date = fields.Date(required=False, allow_none=True)
    operating_hours = fields.Dict(required=False, allow_none=True)
    services = fields.List(fields.Str(), required=False, allow_none=True)
    
    # Medical info for patients
    chronic_conditions = fields.List(fields.Str(), required=False, allow_none=True)
    allergies = fields.List(fields.Str(), required=False, allow_none=True)
    current_medications = fields.List(fields.Str(), required=False, allow_none=True)
    emergency_contact = fields.Str(required=False, validate=validate.Length(max=20), allow_none=True)
    insurance_provider = fields.Str(required=False, validate=validate.Length(max=100), allow_none=True)
    insurance_number = fields.Str(required=False, validate=validate.Length(max=50), allow_none=True)
    blood_type = fields.Str(required=False, validate=validate.Length(max=5), allow_none=True)
    
    @validates('email')
    def validate_email(self, value):
        if not is_valid_email(value):
            raise ValidationError('Invalid email format')
    
    @validates('phone')
    def validate_phone(self, value):
        if not is_valid_phone(value):
            raise ValidationError('Invalid phone number format')
    
    @validates('password')
    def validate_password(self, value):
        if len(value) < 8:
            raise ValidationError('Password must be at least 8 characters long')
        if not any(c.isupper() for c in value):
            raise ValidationError('Password must contain at least one uppercase letter')
        if not any(c.islower() for c in value):
            raise ValidationError('Password must contain at least one lowercase letter')
        if not any(c.isdigit() for c in value):
            raise ValidationError('Password must contain at least one digit')
    
    def validate(self, data, **kwargs):
        errors = {}
        
        # Check password confirmation
        if data.get('password') != data.get('confirm_password'):
            errors['confirm_password'] = ['Passwords do not match']
        
        # Validate pharmacy-specific fields
        if data.get('user_type') == 'pharmacy':
            required_pharmacy_fields = [
                'pharmacy_name', 'pharmacy_name_ar', 'license_number',
                'pharmacist_name', 'pharmacist_license', 'establishment_date'
            ]
            for field in required_pharmacy_fields:
                if not data.get(field):
                    errors[field] = [f'{field} is required for pharmacy registration']
        
        if errors:
            raise ValidationError(errors)
        
        return data

class EmailVerificationSchema(Schema):
    """Schema for email verification."""
    token = fields.Str(required=True, validate=validate.Length(min=10, max=255))

class ForgotPasswordSchema(Schema):
    """Schema for forgot password request."""
    email = fields.Email(required=True, validate=validate.Length(max=120))

class ResetPasswordSchema(Schema):
    """Schema for password reset."""
    token = fields.Str(required=True, validate=validate.Length(min=10, max=255))
    new_password = fields.Str(required=True, validate=validate.Length(min=8, max=255))
    confirm_password = fields.Str(required=True)
    
    @validates('new_password')
    def validate_password(self, value):
        if len(value) < 8:
            raise ValidationError('Password must be at least 8 characters long')
        if not any(c.isupper() for c in value):
            raise ValidationError('Password must contain at least one uppercase letter')
        if not any(c.islower() for c in value):
            raise ValidationError('Password must contain at least one lowercase letter')
        if not any(c.isdigit() for c in value):
            raise ValidationError('Password must contain at least one digit')
    
    def validate(self, data, **kwargs):
        errors = {}
        
        if data.get('new_password') != data.get('confirm_password'):
            errors['confirm_password'] = ['Passwords do not match']
        
        if errors:
            raise ValidationError(errors)
        
        return data

class ChangePasswordSchema(Schema):
    """Schema for changing password."""
    current_password = fields.Str(required=True)
    new_password = fields.Str(required=True, validate=validate.Length(min=8, max=255))
    confirm_password = fields.Str(required=True)
    
    @validates('new_password')
    def validate_password(self, value):
        if len(value) < 8:
            raise ValidationError('Password must be at least 8 characters long')
        if not any(c.isupper() for c in value):
            raise ValidationError('Password must contain at least one uppercase letter')
        if not any(c.islower() for c in value):
            raise ValidationError('Password must contain at least one lowercase letter')
        if not any(c.isdigit() for c in value):
            raise ValidationError('Password must contain at least one digit')
    
    def validate(self, data, **kwargs):
        errors = {}
        
        if data.get('new_password') != data.get('confirm_password'):
            errors['confirm_password'] = ['Passwords do not match']
        
        if data.get('current_password') == data.get('new_password'):
            errors['new_password'] = ['New password must be different from current password']
        
        if errors:
            raise ValidationError(errors)
        
        return data

class RefreshTokenSchema(Schema):
    """Schema for token refresh."""
    refresh_token = fields.Str(required=False, allow_none=True)

# Response schemas
class UserResponseSchema(SQLAlchemyAutoSchema):
    """Schema for user response."""
    class Meta:
        model = User
        load_instance = True
        exclude = ('password_hash', 'email_verification_token', 'password_reset_token')

class LoginResponseSchema(Schema):
    """Schema for login response."""
    success = fields.Bool()
    message = fields.Str()
    message_ar = fields.Str()
    access_token = fields.Str()
    refresh_token = fields.Str()
    user = fields.Nested(UserResponseSchema)
    expires_in = fields.Int()

class RegisterResponseSchema(Schema):
    """Schema for registration response."""
    success = fields.Bool()
    message = fields.Str()
    message_ar = fields.Str()
    user = fields.Nested(UserResponseSchema)
    verification_required = fields.Bool()

class MessageResponseSchema(Schema):
    """Schema for simple message responses."""
    success = fields.Bool()
    message = fields.Str()
    message_ar = fields.Str()

