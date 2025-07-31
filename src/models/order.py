import uuid
from datetime import datetime
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy import Column, String, Boolean, DateTime, Date, Enum, Text, ForeignKey, Integer, Float, Numeric
from sqlalchemy.orm import relationship
from src.models import db

class Order(db.Model):
    """Order model with multilingual support."""
    
    __tablename__ = 'orders'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey('users.id'), nullable=False)
    pharmacy_id = Column(UUID(as_uuid=True), ForeignKey('pharmacies.id'), nullable=False)
    prescription_id = Column(UUID(as_uuid=True), ForeignKey('prescriptions.id'), nullable=True)
    order_number = Column(String(50), unique=True, nullable=False)
    
    # Order status
    status = Column(Enum(
        'pending',
        'confirmed', 
        'preparing',
        'ready',
        'out_for_delivery',
        'delivered',
        'cancelled',
        name='order_statuses'
    ), default='pending')
    
    # Pricing
    total_amount = Column(Numeric(10, 2), nullable=False)
    discount_amount = Column(Numeric(10, 2), default=0.0)
    delivery_fee = Column(Numeric(10, 2), default=0.0)
    tax_amount = Column(Numeric(10, 2), default=0.0)
    final_amount = Column(Numeric(10, 2), nullable=False)
    
    # Payment
    payment_method = Column(Enum(
        'cash',
        'card', 
        'insurance',
        'wallet',
        name='payment_methods'
    ), nullable=False)
    payment_status = Column(Enum(
        'pending',
        'paid',
        'failed',
        'refunded',
        name='payment_statuses'
    ), default='pending')
    
    # Delivery information (JSON string)
    delivery_address = Column(Text, nullable=False)  # JSON string
    delivery_notes = Column(Text, nullable=True)
    delivery_notes_ar = Column(Text, nullable=True)
    
    # Delivery timing
    estimated_delivery = Column(DateTime, nullable=True)
    delivered_at = Column(DateTime, nullable=True)
    
    # Cancellation
    cancelled_reason = Column(String(500), nullable=True)
    cancelled_reason_ar = Column(String(500), nullable=True)
    cancelled_at = Column(DateTime, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = relationship('User', back_populates='orders')
    pharmacy = relationship('Pharmacy', back_populates='orders')
    prescription = relationship('Prescription', back_populates='orders')
    items = relationship('OrderItem', back_populates='order', cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<Order {self.order_number}>'
    
    def to_dict(self, language='en'):
        """Convert order to dictionary with language support."""
        import json
        
        data = {
            'id': str(self.id),
            'user_id': str(self.user_id),
            'pharmacy_id': str(self.pharmacy_id),
            'prescription_id': str(self.prescription_id) if self.prescription_id else None,
            'order_number': self.order_number,
            'status': self.status,
            'status_display': self.get_status_display(language),
            'total_amount': float(self.total_amount),
            'discount_amount': float(self.discount_amount),
            'delivery_fee': float(self.delivery_fee),
            'tax_amount': float(self.tax_amount),
            'final_amount': float(self.final_amount),
            'payment_method': self.payment_method,
            'payment_method_display': self.get_payment_method_display(language),
            'payment_status': self.payment_status,
            'payment_status_display': self.get_payment_status_display(language),
            'delivery_address': json.loads(self.delivery_address) if self.delivery_address else {},
            'delivery_notes': self.delivery_notes_ar if language == 'ar' and self.delivery_notes_ar else self.delivery_notes,
            'estimated_delivery': self.estimated_delivery.isoformat() if self.estimated_delivery else None,
            'delivered_at': self.delivered_at.isoformat() if self.delivered_at else None,
            'cancelled_reason': self.cancelled_reason_ar if language == 'ar' and self.cancelled_reason_ar else self.cancelled_reason,
            'cancelled_at': self.cancelled_at.isoformat() if self.cancelled_at else None,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }
        
        return data
    
    def get_status_display(self, language='en'):
        """Get human-readable status in specified language."""
        status_translations = {
            'pending': {'en': 'Pending', 'ar': 'في الانتظار'},
            'confirmed': {'en': 'Confirmed', 'ar': 'مؤكد'},
            'preparing': {'en': 'Preparing', 'ar': 'قيد التحضير'},
            'ready': {'en': 'Ready for Pickup', 'ar': 'جاهز للاستلام'},
            'out_for_delivery': {'en': 'Out for Delivery', 'ar': 'في الطريق للتوصيل'},
            'delivered': {'en': 'Delivered', 'ar': 'تم التوصيل'},
            'cancelled': {'en': 'Cancelled', 'ar': 'ملغي'}
        }
        return status_translations.get(self.status, {}).get(language, self.status)
    
    def get_payment_method_display(self, language='en'):
        """Get human-readable payment method in specified language."""
        method_translations = {
            'cash': {'en': 'Cash on Delivery', 'ar': 'الدفع عند الاستلام'},
            'card': {'en': 'Credit/Debit Card', 'ar': 'بطاقة ائتمان/خصم'},
            'insurance': {'en': 'Insurance', 'ar': 'التأمين'},
            'wallet': {'en': 'Digital Wallet', 'ar': 'المحفظة الرقمية'}
        }
        return method_translations.get(self.payment_method, {}).get(language, self.payment_method)
    
    def get_payment_status_display(self, language='en'):
        """Get human-readable payment status in specified language."""
        status_translations = {
            'pending': {'en': 'Payment Pending', 'ar': 'الدفع في الانتظار'},
            'paid': {'en': 'Paid', 'ar': 'مدفوع'},
            'failed': {'en': 'Payment Failed', 'ar': 'فشل الدفع'},
            'refunded': {'en': 'Refunded', 'ar': 'مسترد'}
        }
        return status_translations.get(self.payment_status, {}).get(language, self.payment_status)
    
    def can_be_cancelled(self):
        """Check if order can be cancelled."""
        return self.status in ['pending', 'confirmed', 'preparing']
    
    def calculate_totals(self):
        """Calculate order totals from items."""
        if self.items:
            self.total_amount = sum(item.total_price for item in self.items)
            self.final_amount = self.total_amount - self.discount_amount + self.delivery_fee + self.tax_amount
        else:
            self.total_amount = 0
            self.final_amount = 0

class OrderItem(db.Model):
    """Order item model."""
    
    __tablename__ = 'order_items'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    order_id = Column(UUID(as_uuid=True), ForeignKey('orders.id'), nullable=False)
    medication_id = Column(UUID(as_uuid=True), ForeignKey('medications.id'), nullable=False)
    pharmacy_inventory_id = Column(UUID(as_uuid=True), ForeignKey('pharmacy_inventory.id'), nullable=False)
    quantity = Column(Integer, nullable=False)
    unit_price = Column(Numeric(10, 2), nullable=False)
    discount_percentage = Column(Float, default=0.0)
    total_price = Column(Numeric(10, 2), nullable=False)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    order = relationship('Order', back_populates='items')
    medication = relationship('Medication', back_populates='order_items')
    pharmacy_inventory = relationship('PharmacyInventory', back_populates='order_items')
    
    def __repr__(self):
        return f'<OrderItem {self.medication_id} x{self.quantity}>'
    
    def to_dict(self, language='en'):
        """Convert order item to dictionary."""
        return {
            'id': str(self.id),
            'order_id': str(self.order_id),
            'medication_id': str(self.medication_id),
            'pharmacy_inventory_id': str(self.pharmacy_inventory_id),
            'quantity': self.quantity,
            'unit_price': float(self.unit_price),
            'discount_percentage': self.discount_percentage,
            'total_price': float(self.total_price),
            'created_at': self.created_at.isoformat()
        }
    
    def calculate_total(self):
        """Calculate total price for this item."""
        subtotal = float(self.unit_price) * self.quantity
        if self.discount_percentage > 0:
            discount_amount = subtotal * (self.discount_percentage / 100)
            self.total_price = subtotal - discount_amount
        else:
            self.total_price = subtotal

