from datetime import datetime
from src.models import db
import uuid

class UserFavorite(db.Model):
    """User favorite model for wishlist/favorites functionality"""
    __tablename__ = 'user_favorites'
    
    # Primary Key
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    
    # Foreign Keys
    user_id = db.Column(db.String(36), db.ForeignKey('users.id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'))
    pharmacy_id = db.Column(db.String(36), db.ForeignKey('pharmacies.id'))
    
    # Favorite Type
    favorite_type = db.Column(db.Enum(
        'product', 'pharmacy', name='favorite_types'
    ), nullable=False)
    
    # Notes (optional)
    notes = db.Column(db.Text)
    notes_ar = db.Column(db.Text)
    
    # Priority/Order
    sort_order = db.Column(db.Integer, default=0)
    
    # Notification Preferences
    notify_on_price_drop = db.Column(db.Boolean, default=True)
    notify_on_availability = db.Column(db.Boolean, default=True)
    notify_on_promotion = db.Column(db.Boolean, default=True)
    
    # Price Tracking (for products)
    target_price = db.Column(db.Float)  # User's desired price
    price_when_added = db.Column(db.Float)  # Price when added to favorites
    
    # Status
    is_active = db.Column(db.Boolean, default=True)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Unique constraint to prevent duplicate favorites
    __table_args__ = (
        db.UniqueConstraint('user_id', 'product_id', 'pharmacy_id', name='unique_user_favorite'),
    )
    
    def get_localized_notes(self, language='ar'):
        """Get notes in specified language"""
        if language == 'ar' and self.notes_ar:
            return self.notes_ar
        return self.notes
    
    def check_price_drop(self):
        """Check if product price has dropped below target"""
        if self.favorite_type != 'product' or not self.product or not self.target_price:
            return False
        
        current_price = self.product.calculate_final_price()
        return current_price <= self.target_price
    
    def check_availability(self):
        """Check if product is now available"""
        if self.favorite_type != 'product' or not self.product:
            return False
        
        return self.product.is_available and self.product.current_stock > 0
    
    def get_price_change_percentage(self):
        """Get price change percentage since added to favorites"""
        if self.favorite_type != 'product' or not self.product or not self.price_when_added:
            return None
        
        current_price = self.product.calculate_final_price()
        if self.price_when_added == 0:
            return None
        
        change = ((current_price - self.price_when_added) / self.price_when_added) * 100
        return round(change, 2)
    
    def update_price_tracking(self):
        """Update price tracking information"""
        if self.favorite_type == 'product' and self.product:
            current_price = self.product.calculate_final_price()
            if not self.price_when_added:
                self.price_when_added = current_price
    
    def to_dict(self, language='ar', include_details=True):
        """Convert favorite to dictionary"""
        data = {
            'id': self.id,
            'user_id': self.user_id,
            'favorite_type': self.favorite_type,
            'notes': self.get_localized_notes(language),
            'sort_order': self.sort_order,
            'notifications': {
                'price_drop': self.notify_on_price_drop,
                'availability': self.notify_on_availability,
                'promotion': self.notify_on_promotion
            },
            'price_tracking': {
                'target_price': self.target_price,
                'price_when_added': self.price_when_added,
                'price_change_percentage': self.get_price_change_percentage()
            } if self.favorite_type == 'product' else None,
            'status': {
                'is_active': self.is_active,
                'price_drop_alert': self.check_price_drop(),
                'availability_alert': self.check_availability()
            },
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }
        
        if include_details:
            if self.favorite_type == 'product' and self.product:
                data['product'] = self.product.to_dict(language=language, include_medical_info=False)
            elif self.favorite_type == 'pharmacy' and self.pharmacy:
                data['pharmacy'] = self.pharmacy.to_dict(include_sensitive=False)
        
        return data
    
    @classmethod
    def add_favorite(cls, user_id, product_id=None, pharmacy_id=None, notes=None, target_price=None):
        """Add item to favorites"""
        if product_id:
            favorite_type = 'product'
            # Check if already exists
            existing = cls.query.filter_by(
                user_id=user_id,
                product_id=product_id,
                favorite_type='product'
            ).first()
        elif pharmacy_id:
            favorite_type = 'pharmacy'
            # Check if already exists
            existing = cls.query.filter_by(
                user_id=user_id,
                pharmacy_id=pharmacy_id,
                favorite_type='pharmacy'
            ).first()
        else:
            raise ValueError("Either product_id or pharmacy_id must be provided")
        
        if existing:
            # Reactivate if it was deactivated
            existing.is_active = True
            existing.updated_at = datetime.utcnow()
            if notes:
                existing.notes = notes
            if target_price:
                existing.target_price = target_price
            return existing
        
        # Create new favorite
        favorite = cls(
            user_id=user_id,
            product_id=product_id,
            pharmacy_id=pharmacy_id,
            favorite_type=favorite_type,
            notes=notes,
            target_price=target_price
        )
        
        # Set price tracking for products
        if product_id:
            favorite.update_price_tracking()
        
        return favorite
    
    @classmethod
    def remove_favorite(cls, user_id, product_id=None, pharmacy_id=None):
        """Remove item from favorites"""
        query = cls.query.filter_by(user_id=user_id)
        
        if product_id:
            query = query.filter_by(product_id=product_id, favorite_type='product')
        elif pharmacy_id:
            query = query.filter_by(pharmacy_id=pharmacy_id, favorite_type='pharmacy')
        else:
            return False
        
        favorite = query.first()
        if favorite:
            db.session.delete(favorite)
            return True
        return False
    
    @classmethod
    def is_favorite(cls, user_id, product_id=None, pharmacy_id=None):
        """Check if item is in user's favorites"""
        query = cls.query.filter_by(user_id=user_id, is_active=True)
        
        if product_id:
            query = query.filter_by(product_id=product_id, favorite_type='product')
        elif pharmacy_id:
            query = query.filter_by(pharmacy_id=pharmacy_id, favorite_type='pharmacy')
        else:
            return False
        
        return query.first() is not None
    
    @classmethod
    def get_user_favorites(cls, user_id, favorite_type=None, language='ar'):
        """Get all favorites for a user"""
        query = cls.query.filter_by(user_id=user_id, is_active=True)
        
        if favorite_type:
            query = query.filter_by(favorite_type=favorite_type)
        
        favorites = query.order_by(cls.sort_order, cls.created_at.desc()).all()
        return [favorite.to_dict(language=language) for favorite in favorites]
    
    @classmethod
    def get_price_drop_alerts(cls, user_id):
        """Get products with price drops below target"""
        favorites = cls.query.filter_by(
            user_id=user_id,
            favorite_type='product',
            is_active=True,
            notify_on_price_drop=True
        ).all()
        
        alerts = []
        for favorite in favorites:
            if favorite.check_price_drop():
                alerts.append(favorite)
        
        return alerts
    
    @classmethod
    def get_availability_alerts(cls, user_id):
        """Get products that are now available"""
        favorites = cls.query.filter_by(
            user_id=user_id,
            favorite_type='product',
            is_active=True,
            notify_on_availability=True
        ).all()
        
        alerts = []
        for favorite in favorites:
            if favorite.check_availability():
                alerts.append(favorite)
        
        return alerts
    
    @classmethod
    def update_sort_order(cls, user_id, favorite_ids_in_order):
        """Update sort order for user's favorites"""
        for index, favorite_id in enumerate(favorite_ids_in_order):
            favorite = cls.query.filter_by(
                id=favorite_id,
                user_id=user_id
            ).first()
            if favorite:
                favorite.sort_order = index
    
    @classmethod
    def get_popular_products(cls, limit=10):
        """Get most favorited products"""
        from sqlalchemy import func
        
        popular = db.session.query(
            cls.product_id,
            func.count(cls.id).label('favorite_count')
        ).filter_by(
            favorite_type='product',
            is_active=True
        ).group_by(
            cls.product_id
        ).order_by(
            func.count(cls.id).desc()
        ).limit(limit).all()
        
        return popular
    
    @classmethod
    def get_popular_pharmacies(cls, limit=10):
        """Get most favorited pharmacies"""
        from sqlalchemy import func
        
        popular = db.session.query(
            cls.pharmacy_id,
            func.count(cls.id).label('favorite_count')
        ).filter_by(
            favorite_type='pharmacy',
            is_active=True
        ).group_by(
            cls.pharmacy_id
        ).order_by(
            func.count(cls.id).desc()
        ).limit(limit).all()
        
        return popular
    
    def __repr__(self):
        if self.favorite_type == 'product':
            return f'<UserFavorite User:{self.user_id} Product:{self.product_id}>'
        else:
            return f'<UserFavorite User:{self.user_id} Pharmacy:{self.pharmacy_id}>'

