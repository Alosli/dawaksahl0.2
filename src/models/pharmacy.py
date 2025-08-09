from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from src.models import db
import uuid
import json

class Pharmacy(db.Model):
    """Consolidated Pharmacy model - stores ALL pharmacy data in one table"""
    __tablename__ = 'pharmacies'
    
    # Primary Key
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    
    # Authentication
    email = db.Column(db.String(255), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    
    # Business Information
    pharmacy_name = db.Column(db.String(200), nullable=False)
    pharmacy_name_ar = db.Column(db.String(200))
    license_number = db.Column(db.String(100), unique=True, nullable=False)
    commercial_registration = db.Column(db.String(100))
    tax_id = db.Column(db.String(100))
    
    # Contact Information
    phone = db.Column(db.String(20), nullable=False)
    whatsapp_number = db.Column(db.String(20))
    website_url = db.Column(db.String(255))
    
    # Address Information
    address_line1 = db.Column(db.String(255), nullable=False)
    address_line2 = db.Column(db.String(255))
    city = db.Column(db.String(100), nullable=False)
    state = db.Column(db.String(100), nullable=False)
    postal_code = db.Column(db.String(20))
    country = db.Column(db.String(100), default='Yemen')
    latitude = db.Column(db.Float)
    longitude = db.Column(db.Float)
    
    # Pharmacist Information
    pharmacist_name = db.Column(db.String(100), nullable=False)
    pharmacist_license = db.Column(db.String(100), nullable=False)
    pharmacist_phone = db.Column(db.String(20))
    pharmacist_email = db.Column(db.String(120))
    
    # Business Details
    description = db.Column(db.Text)
    description_ar = db.Column(db.Text)
    establishment_date = db.Column(db.Date)
    pharmacy_type = db.Column(db.Enum('community', 'hospital', 'clinic', 'online', name='pharmacy_types'), default='community')
    
    # Staff and Capabilities
    total_staff = db.Column(db.Integer, default=1)
    is_24_hours = db.Column(db.Boolean, default=False)
    has_delivery = db.Column(db.Boolean, default=True)
    has_cold_chain = db.Column(db.Boolean, default=False)
    has_compounding = db.Column(db.Boolean, default=False)
    has_controlled_substances = db.Column(db.Boolean, default=False)
    
    # Services and Specializations (JSON arrays)
    services = db.Column(db.Text)  # JSON array
    specializations = db.Column(db.Text)  # JSON array
    languages_spoken = db.Column(db.Text)  # JSON array
    
    # Operating Hours (JSON object)
    operating_hours = db.Column(db.Text)  # JSON object
    
    # Delivery Information
    offers_delivery = db.Column(db.Boolean, default=True)
    delivery_radius = db.Column(db.Float, default=10.0)  # in km
    delivery_fee = db.Column(db.Float, default=0.0)
    free_delivery_threshold = db.Column(db.Float)
    delivery_areas = db.Column(db.Text)  # JSON array
    
    # Insurance
    accepts_insurance = db.Column(db.Boolean, default=True)
    insurance_providers = db.Column(db.Text)  # JSON array
    
    # Documents and Verification
    license_document_url = db.Column(db.String(500))
    tax_certificate_url = db.Column(db.String(500))
    additional_documents = db.Column(db.Text)  # JSON array
    verification_status = db.Column(db.Enum('pending', 'verified', 'rejected', name='verification_statuses'), default='pending')
    verified_at = db.Column(db.DateTime)
    verification_notes = db.Column(db.Text)
    
    # Business Metrics
    rating = db.Column(db.Float, default=0.0)
    total_reviews = db.Column(db.Integer, default=0)
    total_orders = db.Column(db.Integer, default=0)
    total_products = db.Column(db.Integer, default=0)
    
    # Social Media (JSON object)
    social_media = db.Column(db.Text)  # JSON object
    
    # Account Status
    is_active = db.Column(db.Boolean, default=True)
    is_verified = db.Column(db.Boolean, default=False)
    email_verified = db.Column(db.Boolean, default=False)
    phone_verified = db.Column(db.Boolean, default=False)
    preferred_language = db.Column(db.Enum('ar', 'en', name='language_types'), default='ar')

    # Subscription
    subscription_plan = db.Column(db.Enum('basic', 'premium', 'enterprise', name='subscription_plans'), default='basic')
    subscription_expires_at = db.Column(db.DateTime)
    
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
    products = db.relationship('Product', backref='pharmacy', lazy='dynamic', cascade='all, delete-orphan',foreign_keys='Product.pharmacy_id')
    orders = db.relationship('Order', backref='pharmacy', lazy='dynamic')
    reviews = db.relationship('Review', backref='pharmacy', lazy='dynamic')
    notifications = db.relationship('Notification', backref='pharmacy', lazy='dynamic', cascade='all, delete-orphan')
    
    def set_password(self, password):
        """Set password hash"""
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        """Check password against hash"""
        return check_password_hash(self.password_hash, password)
    
    def get_address(self):
        """Get formatted address"""
        parts = [self.address_line1, self.address_line2, self.city, self.state, self.country]
        return ', '.join([part for part in parts if part])
    
    def get_coordinates(self):
        """Get coordinates as tuple"""
        if self.latitude and self.longitude:
            return (self.latitude, self.longitude)
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
    
    def get_services(self):
        """Get services list"""
        return self.get_json_field('services')
    
    def get_specializations(self):
        """Get specializations list"""
        return self.get_json_field('specializations')
    
    def get_languages_spoken(self):
        """Get languages spoken list"""
        return self.get_json_field('languages_spoken')
    
    def get_operating_hours(self):
        """Get operating hours object"""
        return self.get_json_field('operating_hours')
    
    def get_delivery_areas(self):
        """Get delivery areas list"""
        return self.get_json_field('delivery_areas')
    
    def get_insurance_providers(self):
        """Get insurance providers list"""
        return self.get_json_field('insurance_providers')
    
    def get_additional_documents(self):
        """Get additional documents list"""
        return self.get_json_field('additional_documents')
    
    def get_social_media(self):
        """Get social media object"""
        return self.get_json_field('social_media')
    
    def calculate_distance_to(self, target_lat, target_lng):
        """Calculate distance to target coordinates using Haversine formula"""
        if not self.latitude or not self.longitude:
            return None
        
        import math
        
        # Haversine formula
        R = 6371  # Earth's radius in kilometers
        
        lat1 = math.radians(float(self.latitude))
        lon1 = math.radians(float(self.longitude))
        lat2 = math.radians(float(target_lat))
        lon2 = math.radians(float(target_lng))
        
        dlat = lat2 - lat1
        dlon = lon2 - lon1
        
        a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2
        c = 2 * math.asin(math.sqrt(a))
        distance = R * c
        
        return round(distance, 2)
    
    def is_open_now(self):
        """Check if pharmacy is currently open"""
        operating_hours = self.get_operating_hours()
        if not operating_hours:
            return True  # Assume open if no hours specified
        
        if self.is_24_hours:
            return True
        
        # Implementation would check current time against operating hours
        # This is a simplified version
        return True
    
    def can_deliver_to(self, lat, lng):
        """Check if pharmacy can deliver to given coordinates"""
        if not self.offers_delivery:
            return False
        
        distance = self.calculate_distance_to(lat, lng)
        if distance is None:
            return False
        
        return distance <= self.delivery_radius
    
    def calculate_delivery_fee(self, order_total):
        """Calculate delivery fee for given order total"""
        if not self.offers_delivery:
            return None
        
        if self.free_delivery_threshold and order_total >= self.free_delivery_threshold:
            return 0.0
        
        return self.delivery_fee
    
    def update_metrics(self):
        """Update pharmacy metrics"""
        self.total_products = self.products.filter_by(is_active=True).count()
        self.total_orders = self.orders.count()
        
        # Calculate average rating
        reviews = self.reviews.filter_by(is_approved=True).all()
        if reviews:
            self.rating = sum(review.rating for review in reviews) / len(reviews)
            self.total_reviews = len(reviews)
        else:
            self.rating = 0.0
            self.total_reviews = 0
    
    def to_dict(self, language='ar', include_sensitive=False):
        """Convert pharmacy to dictionary"""
        data = {
            'id': self.id,
            'email': self.email,
            'pharmacy_name': self.pharmacy_name,
            'pharmacy_name_ar': self.pharmacy_name_ar,
            'license_number': self.license_number,
            'phone': self.phone,
            'whatsapp_number': self.whatsapp_number,
            'website_url': self.website_url,
            'preferred_language': self.preferred_language,
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
            'pharmacist': {
                'name': self.pharmacist_name,
                'license': self.pharmacist_license,
                'phone': self.pharmacist_phone,
                'email': self.pharmacist_email
            },
            'description': self.description,
            'description_ar': self.description_ar,
            'establishment_date': self.establishment_date.isoformat() if self.establishment_date else None,
            'pharmacy_type': self.pharmacy_type,
            'capabilities': {
                'is_24_hours': self.is_24_hours,
                'has_delivery': self.has_delivery,
                'has_cold_chain': self.has_cold_chain,
                'has_compounding': self.has_compounding,
                'has_controlled_substances': self.has_controlled_substances
            },
            'services': self.get_services(),
            'specializations': self.get_specializations(),
            'languages_spoken': self.get_languages_spoken(),
            'operating_hours': self.get_operating_hours(),
            'delivery': {
                'offers_delivery': self.offers_delivery,
                'delivery_radius': self.delivery_radius,
                'delivery_fee': self.delivery_fee,
                'free_delivery_threshold': self.free_delivery_threshold,
                'delivery_areas': self.get_delivery_areas()
            },
            'insurance': {
                'accepts_insurance': self.accepts_insurance,
                'providers': self.get_insurance_providers()
            },
            'verification': {
                'status': self.verification_status,
                'verified_at': self.verified_at.isoformat() if self.verified_at else None
            },
            'metrics': {
                'rating': self.rating,
                'total_reviews': self.total_reviews,
                'total_orders': self.total_orders,
                'total_products': self.total_products
            },
            'social_media': self.get_social_media(),
            'subscription_plan': self.subscription_plan,
            'is_active': self.is_active,
            'is_verified': self.is_verified,
            'email_verified': self.email_verified,
            'phone_verified': self.phone_verified,
            'is_open_now': self.is_open_now(),
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat(),
            'last_login': self.last_login.isoformat() if self.last_login else None
        }
        
        if include_sensitive:
            data.update({
                'commercial_registration': self.commercial_registration,
                'tax_id': self.tax_id,
                'documents': {
                    'license_document_url': self.license_document_url,
                    'tax_certificate_url': self.tax_certificate_url,
                    'additional_documents': self.get_additional_documents()
                },
                'verification_notes': self.verification_notes,
                'total_staff': self.total_staff,
                'subscription_expires_at': self.subscription_expires_at.isoformat() if self.subscription_expires_at else None
            })
        
        return data
    
    def __repr__(self):
        return f'<Pharmacy {self.pharmacy_name}>'

