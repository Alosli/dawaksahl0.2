from marshmallow import Schema, fields, validates_schema, ValidationError, pre_load
from marshmallow.validate import OneOf
import re

class RegisterSchema(Schema):
    # Basic User Information
    email = fields.Email(required=True)
    password = fields.Str(required=True, validate=fields.Length(min=8))
    confirm_password = fields.Str(required=True)
    user_type = fields.Str(required=True, validate=fields.OneOf(['patient', 'pharmacy', 'doctor']))
    
    # Personal Information
    first_name = fields.Str(required=True, validate=fields.Length(min=1, max=100))
    last_name = fields.Str(required=True, validate=fields.Length(min=1, max=100))
    phone = fields.Str(required=True)
    date_of_birth = fields.Date(required=True)  # Made required to match frontend
    gender = fields.Str(required=True, validate=fields.OneOf(['male', 'female']))  # Made required
    national_id = fields.Str(allow_none=True, validate=fields.Length(max=20))
    
    # Address Information
    country = fields.Str(missing='YE')  # Yemen default
    city = fields.Str(required=True, validate=fields.Length(min=1, max=100))
    district = fields.Str(required=True, validate=fields.Length(min=1, max=100))
    street = fields.Str(required=True, validate=fields.Length(min=1, max=255))  # Made required
    building_number = fields.Str(allow_none=True, validate=fields.Length(max=20))
    postal_code = fields.Str(required=True, validate=fields.Length(max=20))  # Made required
    floor_apartment = fields.Str(allow_none=True, validate=fields.Length(max=50))
    landmark = fields.Str(allow_none=True, validate=fields.Length(max=200))
    special_delivery_instructions = fields.Str(allow_none=True)
    
    # GPS Coordinates - ESSENTIAL FOR DISTANCE CALCULATION
    coordinates = fields.Raw(allow_none=True)  # Accept the full coordinates object from frontend
    formatted_address = fields.Str(allow_none=True)  # Google Maps formatted address
    latitude = fields.Float(allow_none=True)  # Will be extracted from coordinates
    longitude = fields.Float(allow_none=True)  # Will be extracted from coordinates
    
    # Medical Information (for patients)
    blood_type = fields.Str(required=True, validate=fields.OneOf(['A+', 'A-', 'B+', 'B-', 'AB+', 'AB-', 'O+', 'O-']))  # Made required
    chronic_conditions = fields.List(fields.Str(), allow_none=True)
    allergies = fields.List(fields.Str(), allow_none=True)
    current_medications = fields.List(fields.Str(), allow_none=True)
    
    # Emergency Contact Information
    emergency_contact_name = fields.Str(required=True, validate=fields.Length(max=200))  # Made required
    emergency_contact_phone = fields.Str(required=True, validate=fields.Length(max=20))  # Made required
    emergency_contact_relation = fields.Str(required=True, validate=fields.OneOf(['spouse', 'parent', 'child', 'sibling', 'friend', 'other']))  # Made required
    
    # Primary Doctor Information
    primary_doctor_name = fields.Str(allow_none=True, validate=fields.Length(max=200))
    primary_doctor_phone = fields.Str(allow_none=True, validate=fields.Length(max=20))
    
    # Insurance Information
    insurance_provider = fields.Str(allow_none=True, validate=fields.Length(max=100))
    insurance_number = fields.Str(allow_none=True, validate=fields.Length(max=100))
    insurance_coverage_type = fields.Str(allow_none=True, validate=fields.OneOf(['basic', 'comprehensive', 'premium']))
    
    # Preferences
    preferred_language = fields.Str(missing='ar', validate=fields.OneOf(['ar', 'en']))
    delivery_time_preference = fields.Str(allow_none=True, validate=fields.OneOf(['morning', 'afternoon', 'evening', 'anytime']))
    accessibility_needs = fields.List(fields.Str(), allow_none=True)
    communication_preferences = fields.List(fields.Str(), allow_none=True)
    
    # Pharmacy-specific fields (for pharmacy registration)
    pharmacy_name = fields.Str(allow_none=True, validate=fields.Length(max=200))
    pharmacy_name_ar = fields.Str(allow_none=True, validate=fields.Length(max=200))
    license_number = fields.Str(allow_none=True, validate=fields.Length(max=100))
    pharmacist_name = fields.Str(allow_none=True, validate=fields.Length(max=200))
    pharmacist_license = fields.Str(allow_none=True, validate=fields.Length(max=100))
    establishment_date = fields.Date(allow_none=True)
    operating_hours = fields.Raw(allow_none=True)
    services = fields.List(fields.Str(), allow_none=True)
    
    @pre_load
    def preprocess_data(self, data, **kwargs):
        """Preprocess data to handle frontend format."""
        
        # Extract coordinates if provided
        if 'coordinates' in data and data['coordinates']:
            coords = data['coordinates']
            if isinstance(coords, dict):
                data['latitude'] = coords.get('lat')
                data['longitude'] = coords.get('lng')
        
        # Handle array fields that might be empty or contain 'none'/'no_allergies'
        array_fields = ['chronic_conditions', 'allergies', 'current_medications', 
                       'accessibility_needs', 'communication_preferences']
        for field in array_fields:
            if field in data:
                if not data[field] or data[field] == ['none'] or data[field] == ['no_allergies']:
                    data[field] = None
        
        # Convert empty strings to None for optional fields
        optional_fields = [
            'national_id', 'building_number', 'floor_apartment', 'landmark', 
            'special_delivery_instructions', 'primary_doctor_name', 'primary_doctor_phone',
            'insurance_provider', 'insurance_number', 'insurance_coverage_type',
            'delivery_time_preference', 'pharmacy_name', 'pharmacy_name_ar', 
            'license_number', 'pharmacist_name', 'pharmacist_license', 'establishment_date'
        ]
        
        for field in optional_fields:
            if field in data and data[field] == '':
                data[field] = None
        
        return data
    
    @validates_schema
    def validate_passwords_match(self, data, **kwargs):
        if data.get('password') != data.get('confirm_password'):
            raise ValidationError('Passwords do not match', 'confirm_password')
    
    @validates_schema
    def validate_phone_format(self, data, **kwargs):
        phone = data.get('phone')
        if phone:
            # Remove spaces and check format
            clean_phone = phone.replace(' ', '').replace('-', '')
            if not re.match(r'^\+?[1-9]\d{1,14}$', clean_phone):
                raise ValidationError('Invalid phone number format', 'phone')
    
    @validates_schema
    def validate_emergency_contact_phone(self, data, **kwargs):
        phone = data.get('emergency_contact_phone')
        if phone:
            # Remove spaces and check format
            clean_phone = phone.replace(' ', '').replace('-', '')
            if not re.match(r'^\+?[1-9]\d{1,14}$', clean_phone):
                raise ValidationError('Invalid emergency contact phone number format', 'emergency_contact_phone')
    
    @validates_schema
    def validate_pharmacy_fields(self, data, **kwargs):
        if data.get('user_type') == 'pharmacy':
            required_pharmacy_fields = ['pharmacy_name', 'license_number', 'pharmacist_name']
            for field in required_pharmacy_fields:
                if not data.get(field):
                    raise ValidationError(f'{field} is required for pharmacy registration', field)
    
    @validates_schema
    def validate_coordinates(self, data, **kwargs):
        lat = data.get('latitude')
        lng = data.get('longitude')
        
        # Coordinates are optional but if provided, both lat and lng must be valid
        if lat is not None or lng is not None:
            if lat is None or lng is None:
                raise ValidationError('Both latitude and longitude must be provided together')
            
            if not (-90 <= lat <= 90):
                raise ValidationError('Latitude must be between -90 and 90', 'latitude')
            
            if not (-180 <= lng <= 180):
                raise ValidationError('Longitude must be between -180 and 180', 'longitude')

class LoginSchema(Schema):
    email = fields.Email(required=True)
    password = fields.Str(required=True)

class ForgotPasswordSchema(Schema):
    email = fields.Email(required=True)

class ResetPasswordSchema(Schema):
    token = fields.Str(required=True)
    password = fields.Str(required=True, validate=fields.Length(min=8))
    confirm_password = fields.Str(required=True)
    
    @validates_schema
    def validate_passwords_match(self, data, **kwargs):
        if data.get('password') != data.get('confirm_password'):
            raise ValidationError('Passwords do not match', 'confirm_password')

class ChangePasswordSchema(Schema):
    current_password = fields.Str(required=True)
    new_password = fields.Str(required=True, validate=fields.Length(min=8))
    confirm_password = fields.Str(required=True)
    
    @validates_schema
    def validate_passwords_match(self, data, **kwargs):
        if data.get('new_password') != data.get('confirm_password'):
            raise ValidationError('New passwords do not match', 'confirm_password')

class EmailVerificationSchema(Schema):
    token = fields.Str(required=True)

class ResendVerificationSchema(Schema):
    email = fields.Email(required=True)

