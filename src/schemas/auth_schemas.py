from marshmallow import Schema, fields, validate, validates, validates_schema, ValidationError
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
    
    @validates_schema
    def validate_schema(self, data, **kwargs):
        """Custom validation for the entire schema."""
        errors = {}
        
        # Check password confirmation
        if data.get('password') != data.get('confirm_password'):
            errors['confirm_password'] = ['Passwords do not match']
        
        # Validate email format using custom function
        email = data.get('email')
        if email and not is_valid_email(email):
            errors['email'] = ['Invalid email format']
        
        # Validate phone format using custom function
        phone = data.get('phone')
        if phone and not is_valid_phone(phone):
            errors['phone'] = ['Invalid phone number format']
        
        # Validate password strength
        password = data.get('password')
        if password:
            password_errors = []
            if len(password) < 8:
                password_errors.append('Password must be at least 8 characters long')
            if not any(c.isupper() for c in password):
                password_errors.append('Password must contain at least one uppercase letter')
            if not any(c.islower() for c in password):
                password_errors.append('Password must contain at least one lowercase letter')
            if not any(c.isdigit() for c in password):
                password_errors.append('Password must contain at least one digit')
            
            if password_errors:
                errors['password'] = password_errors
        
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
    
    @validates_schema
    def validate_schema(self, data, **kwargs):
        """Custom validation for password reset."""
        errors = {}
        
        # Check password confirmation
        if data.get('new_password') != data.get('confirm_password'):
            errors['confirm_password'] = ['Passwords do not match']
        
        # Validate password strength
        password = data.get('new_password')
        if password:
            password_errors = []
            if len(password) < 8:
                password_errors.append('Password must be at least 8 characters long')
            if not any(c.isupper() for c in password):
                password_errors.append('Password must contain at least one uppercase letter')
            if not any(c.islower() for c in password):
                password_errors.append('Password must contain at least one lowercase letter')
            if not any(c.isdigit() for c in password):
                password_errors.append('Password must contain at least one digit')
            
            if password_errors:
                errors['new_password'] = password_errors
        
        if errors:
            raise ValidationError(errors)

class ChangePasswordSchema(Schema):
    """Schema for changing password."""
    current_password = fields.Str(required=True)
    new_password = fields.Str(required=True, validate=validate.Length(min=8, max=255))
    confirm_password = fields.Str(required=True)
    
    @validates_schema
    def validate_schema(self, data, **kwargs):
        """Custom validation for password change."""
        errors = {}
        
        # Check password confirmation
        if data.get('new_password') != data.get('confirm_password'):
            errors['confirm_password'] = ['Passwords do not match']
        
        # Check if new password is different from current
        if data.get('current_password') == data.get('new_password'):
            errors['new_password'] = ['New password must be different from current password']
        
        # Validate password strength
        password = data.get('new_password')
        if password:
            password_errors = []
            if len(password) < 8:
                password_errors.append('Password must be at least 8 characters long')
            if not any(c.isupper() for c in password):
                password_errors.append('Password must contain at least one uppercase letter')
            if not any(c.islower() for c in password):
                password_errors.append('Password must contain at least one lowercase letter')
            if not any(c.isdigit() for c in password):
                password_errors.append('Password must contain at least one digit')
            
            if password_errors:
                if 'new_password' in errors:
                    errors['new_password'].extend(password_errors)
                else:
                    errors['new_password'] = password_errors
        
        if errors:
            raise ValidationError(errors)

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

