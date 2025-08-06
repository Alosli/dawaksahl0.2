from datetime import datetime, timedelta
from src.models.user import db
import uuid
import json

class Order(db.Model):
    """Order model for managing customer orders"""
    __tablename__ = 'orders'
    
    # Primary Key
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    order_number = db.Column(db.String(20), unique=True, nullable=False, index=True)
    
    # Customer Information
    user_id = db.Column(db.String(36), db.ForeignKey('users.id'), nullable=False)
    pharmacy_id = db.Column(db.String(36), db.ForeignKey('pharmacies.id'), nullable=False)
    
    # Order Status
    status = db.Column(db.Enum(
        'pending', 'confirmed', 'preparing', 'ready', 'out_for_delivery', 
        'delivered', 'cancelled', 'refunded', name='order_statuses'
    ), default='pending', index=True)
    
    # Order Type
    order_type = db.Column(db.Enum(
        'regular', 'prescription', 'emergency', 'scheduled', name='order_types'
    ), default='regular')
    
    # Delivery Information
    delivery_method = db.Column(db.Enum(
        'pickup', 'delivery', 'express', name='delivery_methods'
    ), default='delivery')
    
    # Delivery Address (can be different from user's default address)
    delivery_address_line1 = db.Column(db.String(255))
    delivery_address_line2 = db.Column(db.String(255))
    delivery_city = db.Column(db.String(100))
    delivery_state = db.Column(db.String(100))
    delivery_postal_code = db.Column(db.String(20))
    delivery_latitude = db.Column(db.Float)
    delivery_longitude = db.Column(db.Float)
    delivery_notes = db.Column(db.Text)
    delivery_notes_ar = db.Column(db.Text)
    
    # Contact Information
    contact_name = db.Column(db.String(100))
    contact_phone = db.Column(db.String(20))
    alternative_phone = db.Column(db.String(20))
    
    # Pricing
    subtotal = db.Column(db.Float, nullable=False, default=0.0)
    tax_amount = db.Column(db.Float, default=0.0)
    delivery_fee = db.Column(db.Float, default=0.0)
    discount_amount = db.Column(db.Float, default=0.0)
    total_amount = db.Column(db.Float, nullable=False, default=0.0)
    currency = db.Column(db.String(3), default='YER')
    
    # Payment Information
    payment_method = db.Column(db.Enum(
        'cash', 'card', 'bank_transfer', 'wallet', 'insurance', name='payment_methods'
    ), default='cash')
    payment_status = db.Column(db.Enum(
        'pending', 'paid', 'failed', 'refunded', 'partial', name='payment_statuses'
    ), default='pending')
    payment_reference = db.Column(db.String(100))
    
    # Prescription Information (if applicable)
    prescription_id = db.Column(db.String(36))
    prescription_image_url = db.Column(db.String(500))
    requires_pharmacist_review = db.Column(db.Boolean, default=False)
    pharmacist_notes = db.Column(db.Text)
    pharmacist_notes_ar = db.Column(db.Text)
    
    # Timing
    estimated_preparation_time = db.Column(db.Integer)  # in minutes
    estimated_delivery_time = db.Column(db.Integer)  # in minutes
    preferred_delivery_time = db.Column(db.DateTime)
    
    # Special Instructions
    special_instructions = db.Column(db.Text)
    special_instructions_ar = db.Column(db.Text)
    
    # Tracking
    tracking_number = db.Column(db.String(50))
    delivery_driver_name = db.Column(db.String(100))
    delivery_driver_phone = db.Column(db.String(20))
    
    # Insurance
    insurance_provider = db.Column(db.String(100))
    insurance_claim_number = db.Column(db.String(100))
    insurance_coverage_percentage = db.Column(db.Float, default=0.0)
    patient_copay = db.Column(db.Float, default=0.0)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    confirmed_at = db.Column(db.DateTime)
    prepared_at = db.Column(db.DateTime)
    delivered_at = db.Column(db.DateTime)
    cancelled_at = db.Column(db.DateTime)
    
    # Relationships
    items = db.relationship('OrderItem', backref='order', lazy='dynamic', cascade='all, delete-orphan')
    
    def __init__(self, **kwargs):
        super(Order, self).__init__(**kwargs)
        if not self.order_number:
            self.order_number = self.generate_order_number()
    
    def generate_order_number(self):
        """Generate unique order number"""
        import random
        import string
        
        # Format: DWK-YYYYMMDD-XXXX
        date_str = datetime.now().strftime('%Y%m%d')
        random_str = ''.join(random.choices(string.digits, k=4))
        return f"DWK-{date_str}-{random_str}"
    
    def get_delivery_address(self):
        """Get formatted delivery address"""
        parts = [
            self.delivery_address_line1,
            self.delivery_address_line2,
            self.delivery_city,
            self.delivery_state
        ]
        return ', '.join([part for part in parts if part])
    
    def get_delivery_coordinates(self):
        """Get delivery coordinates as tuple"""
        if self.delivery_latitude and self.delivery_longitude:
            return (self.delivery_latitude, self.delivery_longitude)
        return None
    
    def calculate_totals(self):
        """Calculate order totals based on items"""
        self.subtotal = sum(item.total_price for item in self.items)
        
        # Calculate tax (if applicable)
        if hasattr(self.pharmacy, 'tax_rate') and self.pharmacy.tax_rate:
            self.tax_amount = self.subtotal * (self.pharmacy.tax_rate / 100)
        
        # Calculate total
        self.total_amount = self.subtotal + self.tax_amount + self.delivery_fee - self.discount_amount
        
        # Ensure total is not negative
        self.total_amount = max(0, self.total_amount)
    
    def add_item(self, product, quantity, unit_price=None):
        """Add item to order"""
        if unit_price is None:
            unit_price = product.calculate_final_price()
        
        # Check if item already exists
        existing_item = self.items.filter_by(product_id=product.id).first()
        if existing_item:
            existing_item.quantity += quantity
            existing_item.total_price = existing_item.quantity * existing_item.unit_price
        else:
            item = OrderItem(
                order_id=self.id,
                product_id=product.id,
                quantity=quantity,
                unit_price=unit_price,
                total_price=quantity * unit_price
            )
            db.session.add(item)
        
        self.calculate_totals()
    
    def remove_item(self, product_id):
        """Remove item from order"""
        item = self.items.filter_by(product_id=product_id).first()
        if item:
            db.session.delete(item)
            self.calculate_totals()
    
    def update_status(self, new_status, notes=None):
        """Update order status with timestamp"""
        self.status = new_status
        
        if new_status == 'confirmed':
            self.confirmed_at = datetime.utcnow()
        elif new_status == 'ready':
            self.prepared_at = datetime.utcnow()
        elif new_status == 'delivered':
            self.delivered_at = datetime.utcnow()
        elif new_status == 'cancelled':
            self.cancelled_at = datetime.utcnow()
        
        if notes:
            self.pharmacist_notes = notes
    
    def can_be_cancelled(self):
        """Check if order can be cancelled"""
        return self.status in ['pending', 'confirmed']
    
    def can_be_modified(self):
        """Check if order can be modified"""
        return self.status == 'pending'
    
    def is_overdue(self):
        """Check if order is overdue"""
        if not self.estimated_delivery_time:
            return False
        
        expected_delivery = self.created_at + timedelta(minutes=self.estimated_delivery_time)
        return datetime.utcnow() > expected_delivery and self.status not in ['delivered', 'cancelled']
    
    def get_estimated_delivery_time(self):
        """Get estimated delivery datetime"""
        if self.estimated_delivery_time:
            return self.created_at + timedelta(minutes=self.estimated_delivery_time)
        return None
    
    def to_dict(self, language='ar', include_items=True):
        """Convert order to dictionary"""
        data = {
            'id': self.id,
            'order_number': self.order_number,
            'user_id': self.user_id,
            'pharmacy_id': self.pharmacy_id,
            'pharmacy': self.pharmacy.to_dict() if self.pharmacy else None,
            'status': self.status,
            'order_type': self.order_type,
            'delivery_method': self.delivery_method,
            'delivery_address': {
                'line1': self.delivery_address_line1,
                'line2': self.delivery_address_line2,
                'city': self.delivery_city,
                'state': self.delivery_state,
                'postal_code': self.delivery_postal_code,
                'formatted': self.get_delivery_address(),
                'coordinates': self.get_delivery_coordinates(),
                'notes': self.delivery_notes_ar if language == 'ar' else self.delivery_notes
            },
            'contact': {
                'name': self.contact_name,
                'phone': self.contact_phone,
                'alternative_phone': self.alternative_phone
            },
            'pricing': {
                'subtotal': self.subtotal,
                'tax_amount': self.tax_amount,
                'delivery_fee': self.delivery_fee,
                'discount_amount': self.discount_amount,
                'total_amount': self.total_amount,
                'currency': self.currency
            },
            'payment': {
                'method': self.payment_method,
                'status': self.payment_status,
                'reference': self.payment_reference
            },
            'prescription': {
                'id': self.prescription_id,
                'image_url': self.prescription_image_url,
                'requires_review': self.requires_pharmacist_review,
                'pharmacist_notes': self.pharmacist_notes_ar if language == 'ar' else self.pharmacist_notes
            },
            'timing': {
                'estimated_preparation_time': self.estimated_preparation_time,
                'estimated_delivery_time': self.estimated_delivery_time,
                'preferred_delivery_time': self.preferred_delivery_time.isoformat() if self.preferred_delivery_time else None,
                'estimated_delivery_datetime': self.get_estimated_delivery_time().isoformat() if self.get_estimated_delivery_time() else None,
                'is_overdue': self.is_overdue()
            },
            'special_instructions': self.special_instructions_ar if language == 'ar' else self.special_instructions,
            'tracking': {
                'tracking_number': self.tracking_number,
                'driver_name': self.delivery_driver_name,
                'driver_phone': self.delivery_driver_phone
            },
            'insurance': {
                'provider': self.insurance_provider,
                'claim_number': self.insurance_claim_number,
                'coverage_percentage': self.insurance_coverage_percentage,
                'patient_copay': self.patient_copay
            },
            'permissions': {
                'can_be_cancelled': self.can_be_cancelled(),
                'can_be_modified': self.can_be_modified()
            },
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat(),
            'confirmed_at': self.confirmed_at.isoformat() if self.confirmed_at else None,
            'prepared_at': self.prepared_at.isoformat() if self.prepared_at else None,
            'delivered_at': self.delivered_at.isoformat() if self.delivered_at else None,
            'cancelled_at': self.cancelled_at.isoformat() if self.cancelled_at else None
        }
        
        if include_items:
            data['items'] = [item.to_dict(language=language) for item in self.items]
            data['total_items'] = self.items.count()
        
        return data
    
    def __repr__(self):
        return f'<Order {self.order_number}>'


class OrderItem(db.Model):
    """Order item model for individual products in an order"""
    __tablename__ = 'order_items'
    
    # Primary Key
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    
    # Foreign Keys
    order_id = db.Column(db.String(36), db.ForeignKey('orders.id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=False)
    
    # Item Details
    quantity = db.Column(db.Integer, nullable=False, default=1)
    unit_price = db.Column(db.Float, nullable=False)
    total_price = db.Column(db.Float, nullable=False)
    
    # Product snapshot (in case product details change)
    product_name = db.Column(db.String(255))
    product_name_ar = db.Column(db.String(255))
    product_image_url = db.Column(db.String(500))
    
    # Prescription details (if applicable)
    prescription_quantity = db.Column(db.Integer)  # Prescribed quantity
    dosage_instructions = db.Column(db.Text)
    dosage_instructions_ar = db.Column(db.Text)
    
    # Substitution information
    is_substituted = db.Column(db.Boolean, default=False)
    original_product_id = db.Column(db.Integer)
    substitution_reason = db.Column(db.Text)
    substitution_reason_ar = db.Column(db.Text)
    
    # Status
    status = db.Column(db.Enum(
        'pending', 'confirmed', 'out_of_stock', 'substituted', 'dispensed', name='item_statuses'
    ), default='pending')
    
    # Notes
    pharmacist_notes = db.Column(db.Text)
    pharmacist_notes_ar = db.Column(db.Text)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __init__(self, **kwargs):
        super(OrderItem, self).__init__(**kwargs)
        # Snapshot product details
        if self.product:
            self.product_name = self.product.product_name
            self.product_name_ar = self.product.product_name_ar
            self.product_image_url = self.product.image_url
    
    def calculate_total(self):
        """Calculate total price for this item"""
        self.total_price = self.quantity * self.unit_price
    
    def to_dict(self, language='ar'):
        """Convert order item to dictionary"""
        return {
            'id': self.id,
            'order_id': self.order_id,
            'product_id': self.product_id,
            'product': self.product.to_dict(language=language) if self.product else None,
            'product_snapshot': {
                'name': self.product_name_ar if language == 'ar' and self.product_name_ar else self.product_name,
                'image_url': self.product_image_url
            },
            'quantity': self.quantity,
            'unit_price': self.unit_price,
            'total_price': self.total_price,
            'prescription': {
                'quantity': self.prescription_quantity,
                'dosage_instructions': self.dosage_instructions_ar if language == 'ar' else self.dosage_instructions
            },
            'substitution': {
                'is_substituted': self.is_substituted,
                'original_product_id': self.original_product_id,
                'reason': self.substitution_reason_ar if language == 'ar' else self.substitution_reason
            },
            'status': self.status,
            'pharmacist_notes': self.pharmacist_notes_ar if language == 'ar' else self.pharmacist_notes,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }
    
    def __repr__(self):
        return f'<OrderItem {self.product_name} x{self.quantity}>'

