import uuid
from datetime import datetime
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy import Column, String, Boolean, DateTime, Date, Enum, Text, ForeignKey, Float, JSON
from sqlalchemy.orm import relationship
from src.models import db

class User(db.Model):
    """User model with multilingual support for patients, pharmacies, and doctors."""
    
    __tablename__ = 'users'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String(120), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    user_type = Column(Enum('patient', 'pharmacy', 'doctor', name='user_types'), nullable=False)
    
    # Basic information
    first_name = Column(String(100), nullable=False)
    last_name = Column(String(100), nullable=False)
    phone = Column(String(20), nullable=False)
    date_of_birth = Column(Date, nullable=True)
    gender = Column(Enum('male', 'female', name='genders'), nullable=True)
    national_id = Column(String(20), nullable=True)  # Added from frontend
    
    # Profile
    avatar_url = Column(String(500), nullable=True)
    bio = Column(Text, nullable=True)
    bio_ar = Column(Text, nullable=True)
    
    # Email verification
    is_email_verified = Column(Boolean, default=False)
    email_verification_token = Column(String(255), nullable=True)
    email_verification_expires = Column(DateTime, nullable=True)
    
    # Password reset
    password_reset_token = Column(String(255), nullable=True)
    password_reset_expires = Column(DateTime, nullable=True)
    
    # Account status
    is_active = Column(Boolean, default=True)
    is_verified = Column(Boolean, default=False)  # For pharmacy/doctor verification
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_login = Column(DateTime, nullable=True)
    
    # Relationships
    addresses = relationship('UserAddress', back_populates='user', cascade='all, delete-orphan')
    medical_info = relationship('UserMedicalInfo', back_populates='user', uselist=False, cascade='all, delete-orphan')
    device_tokens = relationship('DeviceToken', back_populates='user', cascade='all, delete-orphan')
    pharmacy = relationship('Pharmacy', back_populates='user', uselist=False, cascade='all, delete-orphan')
    prescriptions = relationship('Prescription', back_populates='user', foreign_keys='Prescription.user_id', cascade='all, delete-orphan')
    verified_prescriptions = relationship('Prescription', foreign_keys='Prescription.verified_by')
    orders = relationship('Order', back_populates='user', foreign_keys='Order.user_id', cascade='all, delete-orphan')
    reviews = relationship('Review', back_populates='user', cascade='all, delete-orphan')
    chat_conversations = relationship('ChatConversation', back_populates='user', cascade='all, delete-orphan')
    sent_messages = relationship('ChatMessage', back_populates='sender', cascade='all, delete-orphan')
    notifications = relationship('Notification', back_populates='user', cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<User {self.email}>'
    
    def to_dict(self, include_sensitive=False):
        """Convert user to dictionary."""
        data = {
            'id': str(self.id),
            'email': self.email,
            'user_type': self.user_type,
            'first_name': self.first_name,
            'last_name': self.last_name,
            'phone': self.phone,
            'date_of_birth': self.date_of_birth.isoformat() if self.date_of_birth else None,
            'gender': self.gender,
            'national_id': self.national_id,
            'is_email_verified': self.is_email_verified,
            'avatar_url': self.avatar_url,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat(),
            'last_login': self.last_login.isoformat() if self.last_login else None
        }
        
        if include_sensitive:
            data.update({
                'email_verification_token': self.email_verification_token,
                'password_reset_token': self.password_reset_token
            })
        
        return data
    
    def get_full_name(self):
        """Get user's full name."""
        return f"{self.first_name} {self.last_name}"
    
    def get_default_address(self):
        """Get user's default address."""
        return next((addr for addr in self.addresses if addr.is_default), None)

class UserAddress(db.Model):
    """User address model with GPS coordinates for distance calculation."""
    
    __tablename__ = 'user_addresses'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey('users.id'), nullable=False)
    
    # Address fields
    country = Column(String(10), default='YE')  # Yemen default
    city = Column(String(100), nullable=False)
    district = Column(String(100), nullable=False)
    street = Column(String(255), nullable=False)
    building_number = Column(String(20), nullable=True)
    postal_code = Column(String(20), nullable=True)
    floor_apartment = Column(String(50), nullable=True)  # Added from frontend
    landmark = Column(String(200), nullable=True)  # Added from frontend
    special_delivery_instructions = Column(Text, nullable=True)  # Added from frontend
    
    # GPS Coordinates - ESSENTIAL FOR DISTANCE CALCULATION
    latitude = Column(Float, nullable=True)  # Added for distance calculation
    longitude = Column(Float, nullable=True)  # Added for distance calculation
    coordinates = Column(JSON, nullable=True)  # Store full coordinates object from frontend
    formatted_address = Column(Text, nullable=True)  # Store Google Maps formatted address
    
    # Address metadata
    is_default = Column(Boolean, default=False)
    address_type = Column(Enum('home', 'work', 'other', name='address_types'), default='home')
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = relationship('User', back_populates='addresses')
    
    def __repr__(self):
        return f'<UserAddress {self.city}, {self.district}>'
    
    def to_dict(self):
        """Convert address to dictionary."""
        return {
            'id': str(self.id),
            'user_id': str(self.user_id),
            'country': self.country,
            'city': self.city,
            'district': self.district,
            'street': self.street,
            'building_number': self.building_number,
            'postal_code': self.postal_code,
            'floor_apartment': self.floor_apartment,
            'landmark': self.landmark,
            'special_delivery_instructions': self.special_delivery_instructions,
            'latitude': self.latitude,
            'longitude': self.longitude,
            'coordinates': self.coordinates,
            'formatted_address': self.formatted_address,
            'is_default': self.is_default,
            'address_type': self.address_type,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }
    
    def calculate_distance_to(self, other_lat, other_lng):
        """Calculate distance to another location using Haversine formula."""
        if not self.latitude or not self.longitude:
            return None
            
        import math
        
        # Convert latitude and longitude from degrees to radians
        lat1, lon1, lat2, lon2 = map(math.radians, [self.latitude, self.longitude, other_lat, other_lng])
        
        # Haversine formula
        dlat = lat2 - lat1
        dlon = lon2 - lon1
        a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2
        c = 2 * math.asin(math.sqrt(a))
        
        # Radius of earth in kilometers
        r = 6371
        
        return c * r

class UserMedicalInfo(db.Model):
    """User medical information model for patients - Updated to match frontend."""
    
    __tablename__ = 'user_medical_info'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey('users.id'), nullable=False)
    
    # Medical information - Updated to match frontend
    blood_type = Column(String(5), nullable=True)
    chronic_conditions = Column(JSON, nullable=True)  # Changed to JSON for array storage
    allergies = Column(JSON, nullable=True)  # Changed to JSON for array storage
    current_medications = Column(JSON, nullable=True)  # Changed to JSON for array storage
    
    # Emergency contact - Updated to match frontend structure
    emergency_contact_name = Column(String(200), nullable=True)
    emergency_contact_phone = Column(String(20), nullable=True)
    emergency_contact_relation = Column(Enum('spouse', 'parent', 'child', 'sibling', 'friend', 'other', name='emergency_relations'), nullable=True)
    
    # Primary doctor information - Added from frontend
    primary_doctor_name = Column(String(200), nullable=True)
    primary_doctor_phone = Column(String(20), nullable=True)
    
    # Insurance information - Updated to match frontend
    insurance_provider = Column(String(100), nullable=True)
    insurance_number = Column(String(50), nullable=True)
    insurance_coverage_type = Column(Enum('basic', 'comprehensive', 'premium', name='coverage_types'), nullable=True)
    
    # Preferences - Added from frontend
    preferred_language = Column(String(5), default='ar')
    delivery_time_preference = Column(Enum('morning', 'afternoon', 'evening', 'anytime', name='delivery_times'), nullable=True)
    accessibility_needs = Column(JSON, nullable=True)  # Array of accessibility needs
    communication_preferences = Column(JSON, nullable=True)  # Array of communication preferences
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = relationship('User', back_populates='medical_info')
    
    def __repr__(self):
        return f'<UserMedicalInfo {self.user_id}>'
    
    def to_dict(self):
        """Convert medical info to dictionary."""
        return {
            'id': str(self.id),
            'user_id': str(self.user_id),
            'blood_type': self.blood_type,
            'chronic_conditions': self.chronic_conditions or [],
            'allergies': self.allergies or [],
            'current_medications': self.current_medications or [],
            'emergency_contact_name': self.emergency_contact_name,
            'emergency_contact_phone': self.emergency_contact_phone,
            'emergency_contact_relation': self.emergency_contact_relation,
            'primary_doctor_name': self.primary_doctor_name,
            'primary_doctor_phone': self.primary_doctor_phone,
            'insurance_provider': self.insurance_provider,
            'insurance_number': self.insurance_number,
            'insurance_coverage_type': self.insurance_coverage_type,
            'preferred_language': self.preferred_language,
            'delivery_time_preference': self.delivery_time_preference,
            'accessibility_needs': self.accessibility_needs or [],
            'communication_preferences': self.communication_preferences or [],
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }

class DeviceToken(db.Model):
    """Device token model for push notifications."""
    
    __tablename__ = 'device_tokens'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey('users.id'), nullable=False)
    token = Column(String(500), nullable=False, unique=True)
    device_type = Column(Enum('ios', 'android', 'web', name='device_types'), nullable=False)
    is_active = Column(Boolean, default=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = relationship('User', back_populates='device_tokens')
    
    def __repr__(self):
        return f'<DeviceToken {self.device_type}>'

