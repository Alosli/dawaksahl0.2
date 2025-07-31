import uuid
from datetime import datetime
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy import Column, String, Boolean, DateTime, Date, Enum, Text, ForeignKey, Integer, Float, Numeric
from sqlalchemy.orm import relationship
from src.models import db

class Pharmacy(db.Model):
    """Pharmacy model."""
    
    __tablename__ = 'pharmacies'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey('users.id'), nullable=False)
    pharmacy_name = Column(String(200), nullable=False)
    pharmacy_name_ar = Column(String(200), nullable=False)
    license_number = Column(String(50), unique=True, nullable=False)
    pharmacist_name = Column(String(200), nullable=False)
    pharmacist_license = Column(String(50), nullable=False)
    establishment_date = Column(Date, nullable=False)
    description = Column(Text, nullable=True)
    description_ar = Column(Text, nullable=True)
    
    # Contact information
    phone = Column(String(20), nullable=False)
    email = Column(String(120), nullable=False)
    website = Column(String(255), nullable=True)
    
    # Location
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)
    address = Column(String(500), nullable=False)
    city = Column(String(100), nullable=False)
    district = Column(String(100), nullable=False)
    postal_code = Column(String(20), nullable=False)
    
    # Operating hours (JSON string)
    operating_hours = Column(Text, nullable=False)  # JSON string
    
    # Services (JSON string)
    services = Column(Text, nullable=True)  # JSON string
    
    # Status and verification
    is_verified = Column(Boolean, default=False)
    is_active = Column(Boolean, default=True)
    
    # Rating
    rating = Column(Float, default=0.0)
    total_reviews = Column(Integer, default=0)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = relationship('User', back_populates='pharmacy')
    documents = relationship('PharmacyDocument', back_populates='pharmacy', cascade='all, delete-orphan')
    inventory = relationship('PharmacyInventory', back_populates='pharmacy', cascade='all, delete-orphan')
    orders = relationship('Order', back_populates='pharmacy', cascade='all, delete-orphan')
    reviews = relationship('Review', back_populates='pharmacy', cascade='all, delete-orphan')
    chat_conversations = relationship('ChatConversation', back_populates='pharmacy', cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<Pharmacy {self.pharmacy_name}>'
    
    def to_dict(self, include_sensitive=False):
        """Convert pharmacy to dictionary."""
        import json
        
        data = {
            'id': str(self.id),
            'user_id': str(self.user_id),
            'pharmacy_name': self.pharmacy_name,
            'pharmacy_name_ar': self.pharmacy_name_ar,
            'pharmacist_name': self.pharmacist_name,
            'establishment_date': self.establishment_date.isoformat(),
            'description': self.description,
            'description_ar': self.description_ar,
            'phone': self.phone,
            'email': self.email,
            'website': self.website,
            'latitude': self.latitude,
            'longitude': self.longitude,
            'address': self.address,
            'city': self.city,
            'district': self.district,
            'postal_code': self.postal_code,
            'operating_hours': json.loads(self.operating_hours) if self.operating_hours else {},
            'services': json.loads(self.services) if self.services else [],
            'is_verified': self.is_verified,
            'is_active': self.is_active,
            'rating': self.rating,
            'total_reviews': self.total_reviews,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }
        
        if include_sensitive:
            data.update({
                'license_number': self.license_number,
                'pharmacist_license': self.pharmacist_license
            })
        
        return data
    
    def update_rating(self):
        """Update pharmacy rating based on reviews."""
        if self.reviews:
            total_rating = sum(review.rating for review in self.reviews)
            self.rating = total_rating / len(self.reviews)
            self.total_reviews = len(self.reviews)
        else:
            self.rating = 0.0
            self.total_reviews = 0
    
    def is_open_now(self):
        """Check if pharmacy is currently open."""
        import json
        from datetime import datetime
        
        now = datetime.now()
        day_name = now.strftime('%A').lower()
        current_time = now.strftime('%H:%M')
        
        try:
            hours = json.loads(self.operating_hours)
            day_hours = hours.get(day_name, {})
            
            if day_hours.get('closed', False):
                return False
            
            open_time = day_hours.get('open')
            close_time = day_hours.get('close')
            
            if open_time and close_time:
                return open_time <= current_time <= close_time
            
        except (json.JSONDecodeError, KeyError):
            pass
        
        return False

class PharmacyDocument(db.Model):
    """Pharmacy document model for license and verification documents."""
    
    __tablename__ = 'pharmacy_documents'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    pharmacy_id = Column(UUID(as_uuid=True), ForeignKey('pharmacies.id'), nullable=False)
    document_type = Column(Enum(
        'national_id', 
        'pharmacy_license', 
        'pharmacist_license', 
        'commercial_registration',
        name='document_types'
    ), nullable=False)
    file_url = Column(String(500), nullable=False)
    file_name = Column(String(255), nullable=False)
    file_size = Column(Integer, nullable=False)
    is_verified = Column(Boolean, default=False)
    
    # Timestamps
    uploaded_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    pharmacy = relationship('Pharmacy', back_populates='documents')
    
    def __repr__(self):
        return f'<PharmacyDocument {self.document_type}>'
    
    def to_dict(self):
        """Convert document to dictionary."""
        return {
            'id': str(self.id),
            'pharmacy_id': str(self.pharmacy_id),
            'document_type': self.document_type,
            'file_url': self.file_url,
            'file_name': self.file_name,
            'file_size': self.file_size,
            'is_verified': self.is_verified,
            'uploaded_at': self.uploaded_at.isoformat()
        }

