import uuid
from datetime import datetime
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy import Column, String, Boolean, DateTime, Date, Enum, Text, ForeignKey, Integer, Float, Numeric
from sqlalchemy.orm import relationship
from src.models import db

class MedicationCategory(db.Model):
    """Medication category model."""
    
    __tablename__ = 'medication_categories'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(200), nullable=False)
    name_ar = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    description_ar = Column(Text, nullable=True)
    parent_id = Column(UUID(as_uuid=True), ForeignKey('medication_categories.id'), nullable=True)
    icon = Column(String(100), nullable=True)
    is_active = Column(Boolean, default=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    parent = relationship('MedicationCategory', remote_side=[id], backref='subcategories')
    medications = relationship('Medication', back_populates='category')
    
    def __repr__(self):
        return f'<MedicationCategory {self.name}>'
    
    def to_dict(self):
        """Convert category to dictionary."""
        return {
            'id': str(self.id),
            'name': self.name,
            'name_ar': self.name_ar,
            'description': self.description,
            'description_ar': self.description_ar,
            'parent_id': str(self.parent_id) if self.parent_id else None,
            'icon': self.icon,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat(),
            'subcategories': [sub.to_dict() for sub in self.subcategories] if hasattr(self, 'subcategories') else []
        }

class Medication(db.Model):
    """Medication model."""
    
    __tablename__ = 'medications'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(200), nullable=False, index=True)
    name_ar = Column(String(200), nullable=False, index=True)
    generic_name = Column(String(200), nullable=False)
    generic_name_ar = Column(String(200), nullable=False)
    brand_name = Column(String(200), nullable=True)
    brand_name_ar = Column(String(200), nullable=True)
    category_id = Column(UUID(as_uuid=True), ForeignKey('medication_categories.id'), nullable=False)
    description = Column(Text, nullable=False)
    description_ar = Column(Text, nullable=False)
    
    # Medication details
    dosage_form = Column(String(50), nullable=False)  # tablet, capsule, syrup, etc.
    strength = Column(String(50), nullable=False)  # 500mg, 10ml, etc.
    active_ingredients = Column(Text, nullable=False)  # JSON string
    contraindications = Column(Text, nullable=True)  # JSON string
    side_effects = Column(Text, nullable=True)  # JSON string
    storage_conditions = Column(String(500), nullable=True)
    requires_prescription = Column(Boolean, default=True)
    
    # Product information
    barcode = Column(String(50), nullable=True, unique=True)
    manufacturer = Column(String(200), nullable=False)
    country_of_origin = Column(String(100), nullable=False)
    image_url = Column(String(500), nullable=True)
    
    # Status
    is_active = Column(Boolean, default=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    category = relationship('MedicationCategory', back_populates='medications')
    inventory = relationship('PharmacyInventory', back_populates='medication', cascade='all, delete-orphan')
    order_items = relationship('OrderItem', back_populates='medication')
    reviews = relationship('Review', back_populates='medication', cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<Medication {self.name}>'
    
    def to_dict(self, include_detailed=False):
        """Convert medication to dictionary."""
        import json
        
        data = {
            'id': str(self.id),
            'name': self.name,
            'name_ar': self.name_ar,
            'generic_name': self.generic_name,
            'generic_name_ar': self.generic_name_ar,
            'brand_name': self.brand_name,
            'brand_name_ar': self.brand_name_ar,
            'category_id': str(self.category_id),
            'dosage_form': self.dosage_form,
            'strength': self.strength,
            'requires_prescription': self.requires_prescription,
            'manufacturer': self.manufacturer,
            'country_of_origin': self.country_of_origin,
            'image_url': self.image_url,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }
        
        if include_detailed:
            data.update({
                'description': self.description,
                'description_ar': self.description_ar,
                'active_ingredients': json.loads(self.active_ingredients) if self.active_ingredients else [],
                'contraindications': json.loads(self.contraindications) if self.contraindications else [],
                'side_effects': json.loads(self.side_effects) if self.side_effects else [],
                'storage_conditions': self.storage_conditions,
                'barcode': self.barcode
            })
        
        return data
    
    def get_average_rating(self):
        """Get average rating for this medication."""
        if self.reviews:
            total_rating = sum(review.rating for review in self.reviews)
            return total_rating / len(self.reviews)
        return 0.0
    
    def get_lowest_price(self):
        """Get lowest price from all pharmacies."""
        if self.inventory:
            prices = [inv.price for inv in self.inventory if inv.is_available]
            return min(prices) if prices else None
        return None

class PharmacyInventory(db.Model):
    """Pharmacy inventory model."""
    
    __tablename__ = 'pharmacy_inventory'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    pharmacy_id = Column(UUID(as_uuid=True), ForeignKey('pharmacies.id'), nullable=False)
    medication_id = Column(UUID(as_uuid=True), ForeignKey('medications.id'), nullable=False)
    quantity = Column(Integer, nullable=False, default=0)
    price = Column(Numeric(10, 2), nullable=False)
    discount_percentage = Column(Float, default=0.0)
    expiry_date = Column(Date, nullable=False)
    batch_number = Column(String(50), nullable=True)
    is_available = Column(Boolean, default=True)
    low_stock_threshold = Column(Integer, default=10)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    pharmacy = relationship('Pharmacy', back_populates='inventory')
    medication = relationship('Medication', back_populates='inventory')
    order_items = relationship('OrderItem', back_populates='pharmacy_inventory')
    
    def __repr__(self):
        return f'<PharmacyInventory {self.medication_id} at {self.pharmacy_id}>'
    
    def to_dict(self):
        """Convert inventory to dictionary."""
        return {
            'id': str(self.id),
            'pharmacy_id': str(self.pharmacy_id),
            'medication_id': str(self.medication_id),
            'quantity': self.quantity,
            'price': float(self.price),
            'discount_percentage': self.discount_percentage,
            'expiry_date': self.expiry_date.isoformat(),
            'batch_number': self.batch_number,
            'is_available': self.is_available,
            'low_stock_threshold': self.low_stock_threshold,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }
    
    def get_discounted_price(self):
        """Get price after discount."""
        if self.discount_percentage > 0:
            discount_amount = float(self.price) * (self.discount_percentage / 100)
            return float(self.price) - discount_amount
        return float(self.price)
    
    def is_low_stock(self):
        """Check if inventory is low stock."""
        return self.quantity <= self.low_stock_threshold
    
    def is_expired(self):
        """Check if medication is expired."""
        from datetime import date
        return self.expiry_date < date.today()
    
    def can_fulfill_quantity(self, requested_quantity):
        """Check if inventory can fulfill requested quantity."""
        return self.is_available and not self.is_expired() and self.quantity >= requested_quantity

