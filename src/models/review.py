from datetime import datetime
from src.models import db
import uuid

class Review(db.Model):
    """Review model for product and pharmacy ratings"""
    __tablename__ = 'reviews'
    
    # Primary Key
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    is_active = db.Column(db.Boolean, default=True, nullable=False)

    
    # Foreign Keys
    user_id = db.Column(db.String(36), db.ForeignKey('users.id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'))
    pharmacy_id = db.Column(db.String(36), db.ForeignKey('pharmacies.id'))
    order_id = db.Column(db.String(36), db.ForeignKey('orders.id'))
    
    # Review Type
    review_type = db.Column(db.Enum(
        'product', 'pharmacy', 'order', 'delivery', name='review_types'
    ), nullable=False)
    
    # Rating (1-5 stars)
    rating = db.Column(db.Integer, nullable=False)
    
    # Review Content (Arabic + English)
    title = db.Column(db.String(255))
    title_ar = db.Column(db.String(255))
    comment = db.Column(db.Text)
    comment_ar = db.Column(db.Text)
    
    # Detailed Ratings (for pharmacy reviews)
    service_rating = db.Column(db.Integer)  # 1-5
    delivery_rating = db.Column(db.Integer)  # 1-5
    price_rating = db.Column(db.Integer)  # 1-5
    quality_rating = db.Column(db.Integer)  # 1-5
    
    # Review Attributes
    is_verified_purchase = db.Column(db.Boolean, default=False)
    is_anonymous = db.Column(db.Boolean, default=False)
    
    # Moderation
    is_approved = db.Column(db.Boolean, default=True)
    is_flagged = db.Column(db.Boolean, default=False)
    moderation_notes = db.Column(db.Text)
    moderated_by = db.Column(db.String(36))
    moderated_at = db.Column(db.DateTime)
    
    # Helpfulness
    helpful_count = db.Column(db.Integer, default=0)
    not_helpful_count = db.Column(db.Integer, default=0)
    
    # Images
    images = db.Column(db.Text)  # JSON array of image URLs
    
    # Response from Pharmacy/Admin
    response_text = db.Column(db.Text)
    response_text_ar = db.Column(db.Text)
    response_by = db.Column(db.String(36))
    response_at = db.Column(db.DateTime)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def get_images(self):
        """Get review images as list"""
        if self.images:
            try:
                import json
                return json.loads(self.images)
            except:
                return []
        return []
    
    def set_images(self, image_list):
        """Set review images from list"""
        if image_list:
            import json
            self.images = json.dumps(image_list)
        else:
            self.images = None
    
    def get_localized_title(self, language='ar'):
        """Get title in specified language"""
        if language == 'ar' and self.title_ar:
            return self.title_ar
        return self.title
    
    def get_localized_comment(self, language='ar'):
        """Get comment in specified language"""
        if language == 'ar' and self.comment_ar:
            return self.comment_ar
        return self.comment
    
    def get_localized_response(self, language='ar'):
        """Get response in specified language"""
        if language == 'ar' and self.response_text_ar:
            return self.response_text_ar
        return self.response_text
    
    def calculate_overall_rating(self):
        """Calculate overall rating from detailed ratings"""
        ratings = [
            self.service_rating,
            self.delivery_rating,
            self.price_rating,
            self.quality_rating
        ]
        valid_ratings = [r for r in ratings if r is not None]
        
        if valid_ratings:
            return sum(valid_ratings) / len(valid_ratings)
        return self.rating
    
    def get_rating_breakdown(self):
        """Get detailed rating breakdown"""
        return {
            'overall': self.rating,
            'service': self.service_rating,
            'delivery': self.delivery_rating,
            'price': self.price_rating,
            'quality': self.quality_rating
        }
    
    def mark_helpful(self, is_helpful=True):
        """Mark review as helpful or not helpful"""
        if is_helpful:
            self.helpful_count += 1
        else:
            self.not_helpful_count += 1
    
    def get_helpfulness_ratio(self):
        """Get helpfulness ratio (0-1)"""
        total_votes = self.helpful_count + self.not_helpful_count
        if total_votes == 0:
            return 0
        return self.helpful_count / total_votes
    
    def flag_review(self, reason=None):
        """Flag review for moderation"""
        self.is_flagged = True
        if reason:
            self.moderation_notes = reason
    
    def approve_review(self, moderator_id=None):
        """Approve review"""
        self.is_approved = True
        self.is_flagged = False
        if moderator_id:
            self.moderated_by = moderator_id
            self.moderated_at = datetime.utcnow()
    
    def reject_review(self, moderator_id=None, reason=None):
        """Reject review"""
        self.is_approved = False
        if moderator_id:
            self.moderated_by = moderator_id
            self.moderated_at = datetime.utcnow()
        if reason:
            self.moderation_notes = reason
    
    def add_response(self, response_text, response_text_ar=None, responder_id=None):
        """Add response to review"""
        self.response_text = response_text
        self.response_text_ar = response_text_ar
        self.response_by = responder_id
        self.response_at = datetime.utcnow()
    
    def can_be_edited(self, user_id):
        """Check if review can be edited by user"""
        if self.user_id != user_id:
            return False
        
        # Allow editing within 24 hours
        hours_since_creation = (datetime.utcnow() - self.created_at).total_seconds() / 3600
        return hours_since_creation <= 24
    
    def can_be_deleted(self, user_id):
        """Check if review can be deleted by user"""
        return self.user_id == user_id
    
    def get_reviewer_info(self):
        """Get reviewer information (respecting anonymity)"""
        if self.is_anonymous:
            return {
                'name': 'Anonymous User',
                'name_ar': 'مستخدم مجهول',
                'is_verified': self.is_verified_purchase,
                'avatar': None
            }
        
        if self.user:
            return {
                'name': self.user.get_full_name(),
                'name_ar': self.user.get_full_name(),  # Could be localized
                'is_verified': self.is_verified_purchase,
                'avatar': self.user.profile_picture
            }
        
        return {
            'name': 'Unknown User',
            'name_ar': 'مستخدم غير معروف',
            'is_verified': False,
            'avatar': None
        }
    
    def to_dict(self, language='ar', include_user_info=True):
        """Convert review to dictionary"""
        data = {
            'id': self.id,
            'user_id': self.user_id,
            'product_id': self.product_id,
            'pharmacy_id': self.pharmacy_id,
            'order_id': self.order_id,
            'review_type': self.review_type,
            'rating': self.rating,
            'title': self.get_localized_title(language),
            'comment': self.get_localized_comment(language),
            'rating_breakdown': self.get_rating_breakdown(),
            'overall_rating': self.calculate_overall_rating(),
            'is_verified_purchase': self.is_verified_purchase,
            'is_anonymous': self.is_anonymous,
            'is_approved': self.is_approved,
            'is_flagged': self.is_flagged,
            'helpfulness': {
                'helpful_count': self.helpful_count,
                'not_helpful_count': self.not_helpful_count,
                'ratio': self.get_helpfulness_ratio()
            },
            'images': self.get_images(),
            'response': {
                'text': self.get_localized_response(language),
                'by': self.response_by,
                'at': self.response_at.isoformat() if self.response_at else None
            } if self.response_text else None,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }
        
        if include_user_info:
            data['reviewer'] = self.get_reviewer_info()
        
        # Include product info if it's a product review
        if self.product_id and self.product:
            data['product'] = {
                'id': self.product.id,
                'name': self.product.get_name(language),
                'image_url': self.product.image_url
            }
        
        # Include pharmacy info if it's a pharmacy review
        if self.pharmacy_id and self.pharmacy:
            data['pharmacy'] = {
                'id': self.pharmacy.id,
                'name': self.pharmacy.pharmacy_name_ar if language == 'ar' and self.pharmacy.pharmacy_name_ar else self.pharmacy.pharmacy_name
            }
        
        return data
    
    @classmethod
    def get_average_rating(cls, product_id=None, pharmacy_id=None):
        """Get average rating for product or pharmacy"""
        query = cls.query.filter_by(is_approved=True)
        
        if product_id:
            query = query.filter_by(product_id=product_id)
        elif pharmacy_id:
            query = query.filter_by(pharmacy_id=pharmacy_id)
        else:
            return 0.0
        
        reviews = query.all()
        if not reviews:
            return 0.0
        
        total_rating = sum(review.rating for review in reviews)
        return round(total_rating / len(reviews), 2)
    
    @classmethod
    def get_rating_distribution(cls, product_id=None, pharmacy_id=None):
        """Get rating distribution (1-5 stars)"""
        query = cls.query.filter_by(is_approved=True)
        
        if product_id:
            query = query.filter_by(product_id=product_id)
        elif pharmacy_id:
            query = query.filter_by(pharmacy_id=pharmacy_id)
        else:
            return {}
        
        reviews = query.all()
        distribution = {1: 0, 2: 0, 3: 0, 4: 0, 5: 0}
        
        for review in reviews:
            if 1 <= review.rating <= 5:
                distribution[review.rating] += 1
        
        total = len(reviews)
        if total > 0:
            for rating in distribution:
                distribution[rating] = {
                    'count': distribution[rating],
                    'percentage': round((distribution[rating] / total) * 100, 1)
                }
        
        return distribution
    
    @classmethod
    def get_recent_reviews(cls, product_id=None, pharmacy_id=None, limit=10):
        """Get recent approved reviews"""
        query = cls.query.filter_by(is_approved=True)
        
        if product_id:
            query = query.filter_by(product_id=product_id)
        elif pharmacy_id:
            query = query.filter_by(pharmacy_id=pharmacy_id)
        
        return query.order_by(cls.created_at.desc()).limit(limit).all()
    
    def __repr__(self):
        return f'<Review {self.rating}★ for {self.review_type}>'

