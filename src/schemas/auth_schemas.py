from marshmallow import Schema, fields, validates_schema, ValidationError, pre_load
from marshmallow.validate import OneOf, Length, Email, Range
from datetime import datetime
import json

class PharmacyRegisterSchema(Schema):
    """Enhanced schema for pharmacy registration"""
    
    # Basic User Fields
    email = fields.Email(required=True, validate=Length(max=120))
    password = fields.Str(required=True, validate=Length(min=8, max=128))
    confirm_password = fields.Str(required=True)
    user_type = fields.Str(required=True, validate=OneOf(['pharmacy']))
    first_name = fields.Str(required=True, validate=Length(min=1, max=50))
    last_name = fields.Str(required=True, validate=Length(min=1, max=50))
    phone = fields.Str(required=True, validate=Length(max=20))
    
    # Address Information
    country = fields.Str(required=True, validate=OneOf(['YE']))
    city = fields.Str(required=True, validate=Length(max=100))
    district = fields.Str(required=True, validate=Length(max=100))
    street = fields.Str(required=True, validate=Length(max=200))
    building_number = fields.Str(validate=Length(max=20))
    postal_code = fields.Str(validate=Length(max=20))
    landmark = fields.Str(validate=Length(max=200))
    
    # GPS Coordinates - Accept both formats
    coordinates = fields.Raw()  # Can be dict {lat, lng} or list [lat, lng]
    latitude = fields.Float()
    longitude = fields.Float()
    formatted_address = fields.Str(validate=Length(max=500))
    
    # Pharmacy Business Information
    pharmacy_name = fields.Str(required=True, validate=Length(min=1, max=200))
    pharmacy_name_ar = fields.Str(validate=Length(max=200))
    license_number = fields.Str(required=True, validate=Length(min=1, max=100))
    commercial_registration = fields.Str(validate=Length(max=100))
    tax_id = fields.Str(validate=Length(max=100))
    establishment_date = fields.Date()
    pharmacy_type = fields.Str(validate=OneOf(['community', 'hospital', 'clinic', 'specialized']))
    website = fields.Url()
    
    # Staff Information
    pharmacist_name = fields.Str(required=True, validate=Length(min=1, max=100))
    pharmacist_license = fields.Str(required=True, validate=Length(min=1, max=100))
    pharmacist_phone = fields.Str(validate=Length(max=20))
    total_staff = fields.Int(validate=Range(min=1, max=100))
    languages_spoken = fields.List(fields.Str())
    
    # Services & Operations
    services = fields.List(fields.Str())
    specializations = fields.List(fields.Str())
    operating_hours = fields.Raw()  # Dict of operating hours
    
    # Delivery & Operations
    is_24_hours = fields.Bool()
    has_delivery = fields.Bool()
    delivery_radius = fields.Float(validate=Range(min=0, max=50))
    delivery_fee = fields.Float(validate=Range(min=0))
    
    # Special Services
    has_cold_chain = fields.Bool()
    has_compounding = fields.Bool()
    has_controlled_substances = fields.Bool()
    
    # Insurance
    accepts_insurance = fields.Bool()
    insurance_providers = fields.List(fields.Str())
    
    @pre_load
    def preprocess_data(self, data, **kwargs):
        """Preprocess registration data"""
        # Handle coordinates - extract lat/lng if provided as object
        if 'coordinates' in data and data['coordinates']:
            coords = data['coordinates']
            if isinstance(coords, dict):
                data['latitude'] = coords.get('lat')
                data['longitude'] = coords.get('lng')
            elif isinstance(coords, (list, tuple)) and len(coords) >= 2:
                data['latitude'] = coords[0]
                data['longitude'] = coords[1]
        
        # Handle establishment_date string conversion
        if 'establishment_date' in data and isinstance(data['establishment_date'], str):
            try:
                # Handle different date formats
                if len(data['establishment_date']) == 4:  # Just year
                    data['establishment_date'] = f"{data['establishment_date']}-01-01"
            except:
                pass
        
        # Ensure arrays are properly formatted
        array_fields = ['services', 'specializations', 'languages_spoken', 'insurance_providers']
        for field in array_fields:
            if field in data and not isinstance(data[field], list):
                if isinstance(data[field], str):
                    try:
                        data[field] = json.loads(data[field])
                    except:
                        data[field] = [data[field]] if data[field] else []
                else:
                    data[field] = []
        
        # Handle operating_hours if it's a string
        if 'operating_hours' in data and isinstance(data['operating_hours'], str):
            try:
                data['operating_hours'] = json.loads(data['operating_hours'])
            except:
                pass
        
        return data
    
    @validates_schema
    def validate_schema(self, data, **kwargs):
        """Validate the entire schema"""
        errors = {}
        
        # Password confirmation
        if data.get('password') != data.get('confirm_password'):
            errors['confirm_password'] = 'Passwords do not match'
        
        # Coordinates validation
        if not data.get('latitude') or not data.get('longitude'):
            errors['coordinates'] = 'Valid coordinates are required'
        else:
            # Validate Yemen coordinates (rough bounds)
            lat, lng = data['latitude'], data['longitude']
            if not (12.0 <= lat <= 19.0 and 42.0 <= lng <= 54.0):
                errors['coordinates'] = 'Coordinates must be within Yemen'
        
        # Services validation
        if not data.get('services') or len(data['services']) == 0:
            errors['services'] = 'At least one service must be selected'
        
        # Languages validation
        if not data.get('languages_spoken') or len(data['languages_spoken']) == 0:
            errors['languages_spoken'] = 'At least one language must be selected'
        
        # Operating hours validation
        operating_hours = data.get('operating_hours', {})
        if operating_hours and isinstance(operating_hours, dict):
            required_days = ['monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday']
            for day in required_days:
                if day not in operating_hours:
                    errors['operating_hours'] = f'Operating hours for {day} are missing'
                    break
        
        if errors:
            raise ValidationError(errors)

class UserRegisterSchema(Schema):
    """Enhanced schema for patient registration"""
    
    # Basic User Fields
    email = fields.Email(required=True, validate=Length(max=120))
    password = fields.Str(required=True, validate=Length(min=8, max=128))
    confirm_password = fields.Str(required=True)
    user_type = fields.Str(required=True, validate=OneOf(['patient']))
    first_name = fields.Str(required=True, validate=Length(min=1, max=50))
    last_name = fields.Str(required=True, validate=Length(min=1, max=50))
    phone = fields.Str(required=True, validate=Length(max=20))
    
    # Personal Information
    date_of_birth = fields.Date()
    gender = fields.Str(validate=OneOf(['male', 'female', 'other']))
    blood_type = fields.Str(validate=OneOf(['A+', 'A-', 'B+', 'B-', 'AB+', 'AB-', 'O+', 'O-']))
    height = fields.Float(validate=Range(min=50, max=250))
    weight = fields.Float(validate=Range(min=20, max=300))
    
    # Address Information
    country = fields.Str(required=True, validate=OneOf(['YE']))
    city = fields.Str(required=True, validate=Length(max=100))
    district = fields.Str(required=True, validate=Length(max=100))
    street = fields.Str(required=True, validate=Length(max=200))
    building_number = fields.Str(validate=Length(max=20))
    postal_code = fields.Str(validate=Length(max=20))
    landmark = fields.Str(validate=Length(max=200))
    
    # GPS Coordinates - Accept both formats
    coordinates = fields.Raw()  # Can be dict {lat, lng} or list [lat, lng]
    latitude = fields.Float()
    longitude = fields.Float()
    formatted_address = fields.Str(validate=Length(max=500))
    
    # Medical Information (stored as JSON arrays)
    chronic_conditions = fields.List(fields.Str())
    allergies = fields.List(fields.Str())
    current_medications = fields.List(fields.Str())
    past_surgeries = fields.List(fields.Str())
    family_medical_history = fields.List(fields.Str())
    
    # Emergency Contact
    emergency_contact_name = fields.Str(validate=Length(max=100))
    emergency_contact_phone = fields.Str(validate=Length(max=20))
    emergency_contact_relation = fields.Str(validate=Length(max=50))
    
    # Insurance Information
    insurance_provider = fields.Str(validate=Length(max=100))
    insurance_number = fields.Str(validate=Length(max=100))
    insurance_expiry = fields.Date()
    
    # Preferences
    preferred_language = fields.Str(validate=OneOf(['ar', 'en']), load_default='ar')
    preferred_pharmacy_id = fields.Int()
    
    @pre_load
    def preprocess_data(self, data, **kwargs):
        """Preprocess registration data"""
        # Handle coordinates - extract lat/lng if provided as object
        if 'coordinates' in data and data['coordinates']:
            coords = data['coordinates']
            if isinstance(coords, dict):
                data['latitude'] = coords.get('lat')
                data['longitude'] = coords.get('lng')
            elif isinstance(coords, (list, tuple)) and len(coords) >= 2:
                data['latitude'] = coords[0]
                data['longitude'] = coords[1]
        
        # Handle medical arrays - convert 'none' and 'no_allergies' to None
        medical_arrays = ['chronic_conditions', 'allergies', 'current_medications', 'past_surgeries', 'family_medical_history']
        for field in medical_arrays:
            if field in data:
                if isinstance(data[field], list):
                    # Filter out 'none' and 'no_allergies'
                    filtered = [item for item in data[field] if item not in ['none', 'no_allergies', '']]
                    data[field] = filtered if filtered else None
                elif isinstance(data[field], str):
                    try:
                        parsed = json.loads(data[field])
                        if isinstance(parsed, list):
                            filtered = [item for item in parsed if item not in ['none', 'no_allergies', '']]
                            data[field] = filtered if filtered else None
                    except:
                        data[field] = None if data[field] in ['none', 'no_allergies', ''] else [data[field]]
        
        # Handle insurance - convert 'none' to None
        if data.get('insurance_provider') in ['none', '']:
            data['insurance_provider'] = None
            data['insurance_number'] = None
        
        return data
    
    @validates_schema
    def validate_schema(self, data, **kwargs):
        """Validate the entire schema"""
        errors = {}
        
        # Password confirmation
        if data.get('password') != data.get('confirm_password'):
            errors['confirm_password'] = 'Passwords do not match'
        
        # Coordinates validation
        if not data.get('latitude') or not data.get('longitude'):
            errors['coordinates'] = 'Valid coordinates are required'
        else:
            # Validate Yemen coordinates (rough bounds)
            lat, lng = data['latitude'], data['longitude']
            if not (12.0 <= lat <= 19.0 and 42.0 <= lng <= 54.0):
                errors['coordinates'] = 'Coordinates must be within Yemen'
        
        # Date of birth validation
        if data.get('date_of_birth'):
            today = datetime.now().date()
            if data['date_of_birth'] > today:
                errors['date_of_birth'] = 'Date of birth cannot be in the future'
            elif (today - data['date_of_birth']).days < 365:  # Less than 1 year old
                errors['date_of_birth'] = 'Patient must be at least 1 year old'
        
        if errors:
            raise ValidationError(errors)

class LoginSchema(Schema):
    """Schema for user login"""
    email = fields.Email(required=True)
    password = fields.Str(required=True)

class EmailVerificationSchema(Schema):
    """Schema for email verification"""
    token = fields.Str(required=True)

class PasswordResetRequestSchema(Schema):
    """Schema for password reset request"""
    email = fields.Email(required=True)

class PasswordResetSchema(Schema):
    """Schema for password reset"""
    token = fields.Str(required=True)
    password = fields.Str(required=True, validate=Length(min=8, max=128))
    confirm_password = fields.Str(required=True)
    
    @validates_schema
    def validate_passwords(self, data, **kwargs):
        if data['password'] != data['confirm_password']:
            raise ValidationError({'confirm_password': 'Passwords do not match'})

