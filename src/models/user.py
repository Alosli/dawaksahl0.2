from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
import json
import math

db = SQLAlchemy()

class User(db.Model):
    """Enhanced User model supporting both patients and pharmacies"""
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    user_type = db.Column(db.String(20), nullable=False)  # 'patient', 'pharmacy', 'doctor'
    
    # Basic Information
    first_name = db.Column(db.String(50), nullable=False)
    last_name = db.Column(db.String(50), nullable=False)
    phone = db.Column(db.String(20), nullable=False)
    
    # Account Status
    is_active = db.Column(db.Boolean, default=True)
    is_verified = db.Column(db.Boolean, default=False)
    email_verification_token = db.Column(db.String(255))
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_login = db.Column(db.DateTime)
    
    # Relationships
    addresses = db.relationship('UserAddress', backref='user', lazy='dynamic', cascade='all, delete-orphan')
    medical_info = db.relationship('UserMedicalInfo', backref='user', uselist=False, cascade='all, delete-orphan')
    pharmacy_info = db.relationship('PharmacyInfo', backref='user', uselist=False, cascade='all, delete-orphan')
    
    def set_password(self, password):
        """Set password hash"""
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        """Check password"""
        return check_password_hash(self.password_hash, password)
    
    def get_default_address(self):
        """Get user's default address"""
        return self.addresses.filter_by(is_default=True).first() or self.addresses.first()
    
    def calculate_distance_to(self, target_lat, target_lng):
        """Calculate distance to target coordinates using Haversine formula"""
        address = self.get_default_address()
        if not address or not address.latitude or not address.longitude:
            return float('inf')
        
        # Haversine formula
        R = 6371  # Earth's radius in kilometers
        
        lat1, lon1 = math.radians(address.latitude), math.radians(address.longitude)
        lat2, lon2 = math.radians(target_lat), math.radians(target_lng)
        
        dlat = lat2 - lat1
        dlon = lon2 - lon1
        
        a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2
        c = 2 * math.asin(math.sqrt(a))
        
        return R * c
    
    def to_dict(self):
        """Convert user to dictionary"""
        data = {
            'id': self.id,
            'email': self.email,
            'user_type': self.user_type,
            'first_name': self.first_name,
            'last_name': self.last_name,
            'phone': self.phone,
            'is_active': self.is_active,
            'is_verified': self.is_verified,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'last_login': self.last_login.isoformat() if self.last_login else None
        }
        
        # Add address information
        default_address = self.get_default_address()
        if default_address:
            data['address'] = default_address.to_dict()
        
        # Add medical info for patients
        if self.user_type == 'patient' and self.medical_info:
            data['medical_info'] = self.medical_info.to_dict()
        
        # Add pharmacy info for pharmacies
        if self.user_type == 'pharmacy' and self.pharmacy_info:
            data['pharmacy_info'] = self.pharmacy_info.to_dict()
        
        return data

class UserAddress(db.Model):
    """Enhanced address model with GPS coordinates"""
    __tablename__ = 'user_addresses'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    
    # Address Components
    street = db.Column(db.String(200), nullable=False)
    district = db.Column(db.String(100), nullable=False)
    city = db.Column(db.String(100), nullable=False)
    country = db.Column(db.String(2), default='YE')  # ISO country code
    building_number = db.Column(db.String(20))
    postal_code = db.Column(db.String(20))
    landmark = db.Column(db.String(200))
    
    # GPS Coordinates
    latitude = db.Column(db.Float, nullable=False)
    longitude = db.Column(db.Float, nullable=False)
    coordinates = db.Column(db.Text)  # JSON string for coordinates object
    formatted_address = db.Column(db.Text)  # Full formatted address
    
    # Address Type
    address_type = db.Column(db.String(20), default='home')  # 'home', 'work', 'pharmacy'
    is_default = db.Column(db.Boolean, default=False)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def set_coordinates(self, coordinates):
        """Set coordinates from dict or list"""
        if isinstance(coordinates, dict):
            self.latitude = coordinates.get('lat')
            self.longitude = coordinates.get('lng')
        elif isinstance(coordinates, (list, tuple)) and len(coordinates) >= 2:
            self.latitude = coordinates[0]
            self.longitude = coordinates[1]
        
        # Store as JSON string
        self.coordinates = json.dumps({
            'lat': self.latitude,
            'lng': self.longitude
        })
    
    def get_coordinates(self):
        """Get coordinates as dict"""
        if self.coordinates:
            try:
                return json.loads(self.coordinates)
            except:
                pass
        return {'lat': self.latitude, 'lng': self.longitude}
    
    def to_dict(self):
        """Convert address to dictionary"""
        return {
            'id': self.id,
            'street': self.street,
            'district': self.district,
            'city': self.city,
            'country': self.country,
            'building_number': self.building_number,
            'postal_code': self.postal_code,
            'landmark': self.landmark,
            'latitude': self.latitude,
            'longitude': self.longitude,
            'coordinates': self.get_coordinates(),
            'formatted_address': self.formatted_address,
            'address_type': self.address_type,
            'is_default': self.is_default
        }

class UserMedicalInfo(db.Model):
    """Medical information for patients"""
    __tablename__ = 'user_medical_info'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    
    # Personal Medical Info
    date_of_birth = db.Column(db.Date)
    gender = db.Column(db.String(10))
    blood_type = db.Column(db.String(5))
    height = db.Column(db.Float)  # in cm
    weight = db.Column(db.Float)  # in kg
    
    # Medical History (stored as JSON strings)
    chronic_conditions = db.Column(db.Text)  # JSON array
    allergies = db.Column(db.Text)  # JSON array
    current_medications = db.Column(db.Text)  # JSON array
    past_surgeries = db.Column(db.Text)  # JSON array
    family_medical_history = db.Column(db.Text)  # JSON array
    
    # Emergency Contact
    emergency_contact_name = db.Column(db.String(100))
    emergency_contact_phone = db.Column(db.String(20))
    emergency_contact_relation = db.Column(db.String(50))
    
    # Insurance Information
    insurance_provider = db.Column(db.String(100))
    insurance_number = db.Column(db.String(100))
    insurance_expiry = db.Column(db.Date)
    
    # Preferences
    preferred_language = db.Column(db.String(10), default='ar')
    preferred_pharmacy_id = db.Column(db.Integer)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def set_array_field(self, field_name, data):
        """Set array field as JSON string"""
        if data and isinstance(data, list) and data != ['none'] and data != ['no_allergies']:
            setattr(self, field_name, json.dumps(data))
        else:
            setattr(self, field_name, None)
    
    def get_array_field(self, field_name):
        """Get array field from JSON string"""
        value = getattr(self, field_name)
        if value:
            try:
                return json.loads(value)
            except:
                pass
        return []
    
    def to_dict(self):
        """Convert medical info to dictionary"""
        return {
            'id': self.id,
            'date_of_birth': self.date_of_birth.isoformat() if self.date_of_birth else None,
            'gender': self.gender,
            'blood_type': self.blood_type,
            'height': self.height,
            'weight': self.weight,
            'chronic_conditions': self.get_array_field('chronic_conditions'),
            'allergies': self.get_array_field('allergies'),
            'current_medications': self.get_array_field('current_medications'),
            'past_surgeries': self.get_array_field('past_surgeries'),
            'family_medical_history': self.get_array_field('family_medical_history'),
            'emergency_contact_name': self.emergency_contact_name,
            'emergency_contact_phone': self.emergency_contact_phone,
            'emergency_contact_relation': self.emergency_contact_relation,
            'insurance_provider': self.insurance_provider,
            'insurance_number': self.insurance_number,
            'insurance_expiry': self.insurance_expiry.isoformat() if self.insurance_expiry else None,
            'preferred_language': self.preferred_language,
            'preferred_pharmacy_id': self.preferred_pharmacy_id
        }

class PharmacyInfo(db.Model):
    """Enhanced pharmacy information model"""
    __tablename__ = 'pharmacy_info'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    
    # Business Information
    pharmacy_name = db.Column(db.String(200), nullable=False)
    pharmacy_name_ar = db.Column(db.String(200))
    license_number = db.Column(db.String(100), nullable=False, unique=True)
    commercial_registration = db.Column(db.String(100))
    tax_id = db.Column(db.String(100))
    establishment_date = db.Column(db.Date)
    pharmacy_type = db.Column(db.String(50))  # 'community', 'hospital', 'clinic', 'specialized'
    
    # Contact Information (additional to user phone/email)
    website = db.Column(db.String(200))
    
    # Staff Information
    pharmacist_name = db.Column(db.String(100), nullable=False)
    pharmacist_license = db.Column(db.String(100), nullable=False)
    pharmacist_phone = db.Column(db.String(20))
    total_staff = db.Column(db.Integer, default=1)
    languages_spoken = db.Column(db.Text)  # JSON array
    
    # Services & Operations (stored as JSON strings)
    services = db.Column(db.Text)  # JSON array
    specializations = db.Column(db.Text)  # JSON array
    operating_hours = db.Column(db.Text)  # JSON object
    
    # Delivery & Operations
    is_24_hours = db.Column(db.Boolean, default=False)
    has_delivery = db.Column(db.Boolean, default=True)
    delivery_radius = db.Column(db.Float, default=5.0)  # in km
    delivery_fee = db.Column(db.Float, default=500.0)  # in YER
    
    # Special Services
    has_cold_chain = db.Column(db.Boolean, default=False)
    has_compounding = db.Column(db.Boolean, default=False)
    has_controlled_substances = db.Column(db.Boolean, default=False)
    
    # Insurance
    accepts_insurance = db.Column(db.Boolean, default=False)
    insurance_providers = db.Column(db.Text)  # JSON array
    
    # Status & Verification
    is_verified = db.Column(db.Boolean, default=False)
    verification_date = db.Column(db.DateTime)
    is_active = db.Column(db.Boolean, default=True)
    
    # Ratings & Reviews
    average_rating = db.Column(db.Float, default=0.0)
    total_reviews = db.Column(db.Integer, default=0)
    total_orders = db.Column(db.Integer, default=0)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def set_array_field(self, field_name, data):
        """Set array field as JSON string"""
        if data and isinstance(data, list):
            setattr(self, field_name, json.dumps(data))
        else:
            setattr(self, field_name, None)
    
    def get_array_field(self, field_name):
        """Get array field from JSON string"""
        value = getattr(self, field_name)
        if value:
            try:
                return json.loads(value)
            except:
                pass
        return []
    
    def set_operating_hours(self, hours_data):
        """Set operating hours as JSON string"""
        if hours_data and isinstance(hours_data, dict):
            self.operating_hours = json.dumps(hours_data)
    
    def get_operating_hours(self):
        """Get operating hours from JSON string"""
        if self.operating_hours:
            try:
                return json.loads(self.operating_hours)
            except:
                pass
        return {}
    
    def calculate_distance_to_user(self, user):
        """Calculate distance to user"""
        pharmacy_address = self.user.get_default_address()
        user_address = user.get_default_address()
        
        if not pharmacy_address or not user_address:
            return float('inf')
        
        return user.calculate_distance_to(pharmacy_address.latitude, pharmacy_address.longitude)
    
    def is_within_delivery_radius(self, user):
        """Check if user is within delivery radius"""
        if not self.has_delivery:
            return False
        
        distance = self.calculate_distance_to_user(user)
        return distance <= self.delivery_radius
    
    def to_dict(self):
        """Convert pharmacy info to dictionary"""
        data = {
            'id': self.id,
            'pharmacy_name': self.pharmacy_name,
            'pharmacy_name_ar': self.pharmacy_name_ar,
            'license_number': self.license_number,
            'commercial_registration': self.commercial_registration,
            'tax_id': self.tax_id,
            'establishment_date': self.establishment_date.isoformat() if self.establishment_date else None,
            'pharmacy_type': self.pharmacy_type,
            'website': self.website,
            'pharmacist_name': self.pharmacist_name,
            'pharmacist_license': self.pharmacist_license,
            'pharmacist_phone': self.pharmacist_phone,
            'total_staff': self.total_staff,
            'languages_spoken': self.get_array_field('languages_spoken'),
            'services': self.get_array_field('services'),
            'specializations': self.get_array_field('specializations'),
            'operating_hours': self.get_operating_hours(),
            'is_24_hours': self.is_24_hours,
            'has_delivery': self.has_delivery,
            'delivery_radius': self.delivery_radius,
            'delivery_fee': self.delivery_fee,
            'has_cold_chain': self.has_cold_chain,
            'has_compounding': self.has_compounding,
            'has_controlled_substances': self.has_controlled_substances,
            'accepts_insurance': self.accepts_insurance,
            'insurance_providers': self.get_array_field('insurance_providers'),
            'is_verified': self.is_verified,
            'verification_date': self.verification_date.isoformat() if self.verification_date else None,
            'is_active': self.is_active,
            'average_rating': self.average_rating,
            'total_reviews': self.total_reviews,
            'total_orders': self.total_orders,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
        
        # Add address information
        pharmacy_address = self.user.get_default_address()
        if pharmacy_address:
            data['address'] = pharmacy_address.to_dict()
        
        return data

# Helper function to find nearby pharmacies
def find_nearby_pharmacies(user, max_distance=10, limit=10):
    """Find nearby pharmacies for a user"""
    user_address = user.get_default_address()
    if not user_address:
        return []
    
    # Get all active pharmacies
    pharmacies = db.session.query(PharmacyInfo).join(User).filter(
        User.is_active == True,
        PharmacyInfo.is_active == True,
        PharmacyInfo.is_verified == True
    ).all()
    
    # Calculate distances and filter
    nearby_pharmacies = []
    for pharmacy in pharmacies:
        distance = user.calculate_distance_to(
            pharmacy.user.get_default_address().latitude,
            pharmacy.user.get_default_address().longitude
        )
        
        if distance <= max_distance:
            pharmacy_data = pharmacy.to_dict()
            pharmacy_data['distance'] = round(distance, 2)
            nearby_pharmacies.append(pharmacy_data)
    
    # Sort by distance and limit results
    nearby_pharmacies.sort(key=lambda x: x['distance'])
    return nearby_pharmacies[:limit]
