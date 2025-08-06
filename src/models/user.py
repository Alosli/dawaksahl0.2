from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from flask_sqlalchemy import SQLAlchemy
import uuid
import json

# Initialize db here to avoid circular imports
db = SQLAlchemy()

class User(db.Model):
    """Consolidated User model - stores ALL patient data in one table"""
    __tablename__ = 'users'
    
    # Primary Key
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    
    # Authentication
    email = db.Column(db.String(255), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    
    # Basic Information
    first_name = db.Column(db.String(100), nullable=False)
    last_name = db.Column(db.String(100), nullable=False)
    phone = db.Column(db.String(20), nullable=False)
    date_of_birth = db.Column(db.Date)
    gender = db.Column(db.Enum('male', 'female', 'other', name='gender_types'))
    
    # Address Information (consolidated from user_addresses table)
    address_line1 = db.Column(db.String(255))
    address_line2 = db.Column(db.String(255))
    city = db.Column(db.String(100))
    state = db.Column(db.String(100))
    postal_code = db.Column(db.String(20))
    country = db.Column(db.String(100), default='Yemen')
    latitude = db.Column(db.Float)
    longitude = db.Column(db.Float)
    
    # Medical Information (consolidated from user_medical_info table)
    blood_type = db.Column(db.Enum('A+', 'A-', 'B+', 'B-', 'AB+', 'AB-', 'O+', 'O-', name='blood_types'))
    height = db.Column(db.Float)  # in cm
    weight = db.Column(db.Float)  # in kg
    allergies = db.Column(db.Text)  # JSON array
    chronic_conditions = db.Column(db.Text)  # JSON array
    current_medications = db.Column(db.Text)  # JSON array
    
    # Emergency Contact
    emergency_contact_name = db.Column(db.String(100))
    emergency_contact_phone = db.Column(db.String(20))
    emergency_contact_relation = db.Column(db.String(50))
    
    # Insurance Information
    insurance_provider = db.Column(db.String(100))
    insurance_number = db.Column(db.String(100))
    insurance_expiry = db.Column(db.Date)
    
    # Preferences
    preferred_language = db.Column(db.Enum('ar', 'en', name='language_types'), default='ar')
    notification_preferences = db.Column(db.Text)  # JSON object
    
    # Profile
    profile_picture = db.Column(db.String(500))
    bio = db.Column(db.Text)
    
    # Account Status
    is_active = db.Column(db.Boolean, default=True)
    is_verified = db.Column(db.Boolean, default=False)
    email_verified = db.Column(db.Boolean, default=False)
    phone_verified = db.Column(db.Boolean, default=False)
    
    # Verification Tokens
    email_verification_token = db.Column(db.String(255))
    email_verification_expires = db.Column(db.DateTime)
    password_reset_token = db.Column(db.String(255))
    password_reset_expires = db.Column(db.DateTime)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_login = db.Column(db.DateTime)
    
    # Relationships
    orders = db.relationship('Order', backref='user', lazy='dynamic', cascade='all, delete-orphan')
    reviews = db.relationship('Review', backref='user', lazy='dynamic', cascade='all, delete-orphan')
    favorites = db.relationship('UserFavorite', backref='user', lazy='dynamic', cascade='all, delete-orphan')
    notifications = db.relationship('Notification', backref='user', lazy='dynamic', cascade='all, delete-orphan')
    
    def set_password(self, password):
        """Set password hash"""
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        """Check password against hash"""
        return check_password_hash(self.password_hash, password)
    
    def get_full_name(self):
        """Get user's full name"""
        return f"{self.first_name} {self.last_name}"
    
    def get_address(self):
        """Get formatted address"""
        parts = [self.address_line1, self.address_line2, self.city, self.state, self.country]
        return ', '.join([part for part in parts if part])
    
    def get_coordinates(self):
        """Get coordinates as tuple"""
        if self.latitude and self.longitude:
            return (self.latitude, self.longitude)
        return None
    
    def calculate_bmi(self):
        """Calculate BMI if height and weight are available"""
        if self.height and self.weight:
            height_m = self.height / 100  # Convert cm to meters
            return round(self.weight / (height_m ** 2), 2)
        return None
    
    def set_json_field(self, field_name, data):
        """Set JSON field"""
        if data:
            setattr(self, field_name, json.dumps(data))
        else:
            setattr(self, field_name, None)
    
    def get_json_field(self, field_name):
        """Get JSON field"""
        value = getattr(self, field_name)
        if value:
            try:
                return json.loads(value)
            except:
                return []
        return []
    
    def get_allergies(self):
        """Get allergies list"""
        return self.get_json_field('allergies')
    
    def get_chronic_conditions(self):
        """Get chronic conditions list"""
        return self.get_json_field('chronic_conditions')
    
    def get_current_medications(self):
        """Get current medications list"""
        return self.get_json_field('current_medications')
    
    def get_notification_preferences(self):
        """Get notification preferences"""
        return self.get_json_field('notification_preferences')
    
    def to_dict(self, include_sensitive=False):
        """Convert user to dictionary"""
        data = {
            'id': self.id,
            'email': self.email,
            'first_name': self.first_name,
            'last_name': self.last_name,
            'full_name': self.get_full_name(),
            'phone': self.phone,
            'date_of_birth': self.date_of_birth.isoformat() if self.date_of_birth else None,
            'gender': self.gender,
            'address': {
                'line1': self.address_line1,
                'line2': self.address_line2,
                'city': self.city,
                'state': self.state,
                'postal_code': self.postal_code,
                'country': self.country,
                'formatted': self.get_address(),
                'coordinates': self.get_coordinates()
            },
            'profile_picture': self.profile_picture,
            'bio': self.bio,
            'preferred_language': self.preferred_language,
            'is_active': self.is_active,
            'is_verified': self.is_verified,
            'email_verified': self.email_verified,
            'phone_verified': self.phone_verified,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat(),
            'last_login': self.last_login.isoformat() if self.last_login else None
        }
        
        if include_sensitive:
            data.update({
                'medical_info': {
                    'blood_type': self.blood_type,
                    'height': self.height,
                    'weight': self.weight,
                    'bmi': self.calculate_bmi(),
                    'allergies': self.get_allergies(),
                    'chronic_conditions': self.get_chronic_conditions(),
                    'current_medications': self.get_current_medications()
                },
                'emergency_contact': {
                    'name': self.emergency_contact_name,
                    'phone': self.emergency_contact_phone,
                    'relation': self.emergency_contact_relation
                },
                'insurance': {
                    'provider': self.insurance_provider,
                    'number': self.insurance_number,
                    'expiry': self.insurance_expiry.isoformat() if self.insurance_expiry else None
                },
                'notification_preferences': self.get_notification_preferences()
            })
        
        return data
    
    def __repr__(self):
        return f'<User {self.email}>'

