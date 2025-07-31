import uuid
from datetime import datetime
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy import Column, String, Boolean, DateTime, Date, Enum, Text, ForeignKey, Integer, Float
from sqlalchemy.orm import relationship
from src.models import db

class Review(db.Model):
    """Review model with multilingual support."""
    
    __tablename__ = 'reviews'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey('users.id'), nullable=False)
    pharmacy_id = Column(UUID(as_uuid=True), ForeignKey('pharmacies.id'), nullable=True)
    medication_id = Column(UUID(as_uuid=True), ForeignKey('medications.id'), nullable=True)
    order_id = Column(UUID(as_uuid=True), ForeignKey('orders.id'), nullable=True)
    
    # Review content
    rating = Column(Integer, nullable=False)  # 1-5 stars
    title = Column(String(200), nullable=True)
    title_ar = Column(String(200), nullable=True)
    comment = Column(Text, nullable=True)
    comment_ar = Column(Text, nullable=True)
    
    # Review metadata
    is_verified_purchase = Column(Boolean, default=False)
    is_approved = Column(Boolean, default=True)
    helpful_count = Column(Integer, default=0)
    
    # Language of the review
    review_language = Column(Enum('en', 'ar', 'both', name='review_languages'), default='en')
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = relationship('User', back_populates='reviews')
    pharmacy = relationship('Pharmacy', back_populates='reviews')
    medication = relationship('Medication', back_populates='reviews')
    order = relationship('Order')
    
    def __repr__(self):
        return f'<Review {self.rating} stars by {self.user_id}>'
    
    def to_dict(self, language='en'):
        """Convert review to dictionary with language support."""
        data = {
            'id': str(self.id),
            'user_id': str(self.user_id),
            'pharmacy_id': str(self.pharmacy_id) if self.pharmacy_id else None,
            'medication_id': str(self.medication_id) if self.medication_id else None,
            'order_id': str(self.order_id) if self.order_id else None,
            'rating': self.rating,
            'rating_display': self.get_rating_display(language),
            'is_verified_purchase': self.is_verified_purchase,
            'is_approved': self.is_approved,
            'helpful_count': self.helpful_count,
            'review_language': self.review_language,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }
        
        # Add title and comment based on language preference
        if language == 'ar':
            data['title'] = self.title_ar if self.title_ar else self.title
            data['comment'] = self.comment_ar if self.comment_ar else self.comment
        else:
            data['title'] = self.title if self.title else self.title_ar
            data['comment'] = self.comment if self.comment else self.comment_ar
        
        return data
    
    def get_rating_display(self, language='en'):
        """Get human-readable rating in specified language."""
        rating_translations = {
            1: {'en': 'Very Poor', 'ar': 'سيء جداً'},
            2: {'en': 'Poor', 'ar': 'سيء'},
            3: {'en': 'Average', 'ar': 'متوسط'},
            4: {'en': 'Good', 'ar': 'جيد'},
            5: {'en': 'Excellent', 'ar': 'ممتاز'}
        }
        return rating_translations.get(self.rating, {}).get(language, str(self.rating))
    
    def get_review_type(self, language='en'):
        """Get the type of review in specified language."""
        if self.pharmacy_id and self.medication_id:
            return {'en': 'Pharmacy & Medication Review', 'ar': 'مراجعة الصيدلية والدواء'}[language]
        elif self.pharmacy_id:
            return {'en': 'Pharmacy Review', 'ar': 'مراجعة الصيدلية'}[language]
        elif self.medication_id:
            return {'en': 'Medication Review', 'ar': 'مراجعة الدواء'}[language]
        else:
            return {'en': 'General Review', 'ar': 'مراجعة عامة'}[language]
    
    def is_recent(self, days=30):
        """Check if review is recent (within specified days)."""
        from datetime import timedelta
        return (datetime.utcnow() - self.created_at) <= timedelta(days=days)
    
    def can_be_edited_by(self, user_id):
        """Check if review can be edited by the specified user."""
        return str(self.user_id) == str(user_id) and self.is_recent(days=7)  # Allow editing within 7 days

