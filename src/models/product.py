from datetime import datetime, timedelta
from src.models import db
import uuid
import json

class Product(db.Model):
    """Unified Product model - replaces both products and medications tables"""
    __tablename__ = 'products'
    
    # Primary Key
    id = db.Column(db.Integer, primary_key=True)
    uuid = db.Column(db.String(36), unique=True, index=True, default=lambda: str(uuid.uuid4()))
    
    # Basic Information (Arabic + English)
    product_name = db.Column(db.String(255), nullable=False, index=True)
    product_name_ar = db.Column(db.String(255), index=True)
    generic_name = db.Column(db.String(255), index=True)
    generic_name_ar = db.Column(db.String(255), index=True)
    brand_name = db.Column(db.String(255), index=True)
    brand_name_ar = db.Column(db.String(255), index=True)
    description = db.Column(db.Text)
    description_ar = db.Column(db.Text)
    
    # Manufacturer Information (Arabic + English)
    manufacturer = db.Column(db.String(255))
    manufacturer_ar = db.Column(db.String(255))
    country_of_origin = db.Column(db.String(100))
    country_of_origin_ar = db.Column(db.String(100))
    
    # Product Classification
    category_id = db.Column(db.Integer, db.ForeignKey('categories.id'), nullable=False)
    therapeutic_class = db.Column(db.String(100))
    therapeutic_class_ar = db.Column(db.String(100))
    pharmacological_class = db.Column(db.String(100))
    pharmacological_class_ar = db.Column(db.String(100))
    atc_code = db.Column(db.String(20))  # Anatomical Therapeutic Chemical code
    
    # Physical Properties (Arabic + English)
    dosage_form = db.Column(db.String(100))
    dosage_form_ar = db.Column(db.String(100))
    strength = db.Column(db.String(100))
    strength_ar = db.Column(db.String(100))
    route = db.Column(db.String(100))
    route_ar = db.Column(db.String(100))
    package_size = db.Column(db.String(100))
    package_size_ar = db.Column(db.String(100))
    
    # Pricing
    cost_price = db.Column(db.Float)  # What pharmacy pays
    selling_price = db.Column(db.Float, nullable=False)  # What pharmacy charges
    discount_percentage = db.Column(db.Float, default=0.0)
    tax_percentage = db.Column(db.Float, default=0.0)
    currency = db.Column(db.String(3), default='YER')
    
    # Inventory Management
    current_stock = db.Column(db.Integer, nullable=False, default=0)
    minimum_stock = db.Column(db.Integer, default=10)
    maximum_stock = db.Column(db.Integer, default=1000)
    reorder_level = db.Column(db.Integer, default=20)
    
    # Product Identification
    barcode = db.Column(db.String(50), index=True)
    sku = db.Column(db.String(50), index=True)
    batch_number = db.Column(db.String(100))
    registration_number = db.Column(db.String(100))
    
    # Dates
    manufacturing_date = db.Column(db.Date)
    expiry_date = db.Column(db.Date)
    
    # Regulatory and Safety
    requires_prescription = db.Column(db.Boolean, default=False)
    is_controlled = db.Column(db.Boolean, default=False)
    controlled_class = db.Column(db.String(10))  # 'I', 'II', 'III', 'IV', 'V'
    age_restriction = db.Column(db.Integer)  # Minimum age
    pregnancy_category = db.Column(db.String(5))  # 'A', 'B', 'C', 'D', 'X'
    
    # Storage Requirements (Arabic + English)
    storage_temperature = db.Column(db.String(50))
    storage_temperature_ar = db.Column(db.String(50))
    storage_instructions = db.Column(db.Text)
    storage_instructions_ar = db.Column(db.Text)
    requires_refrigeration = db.Column(db.Boolean, default=False)
    
    # Medical Information (Arabic + English)
    active_ingredients = db.Column(db.Text)  # JSON array
    active_ingredients_ar = db.Column(db.Text)  # JSON array
    side_effects = db.Column(db.Text)  # JSON array
    side_effects_ar = db.Column(db.Text)  # JSON array
    contraindications = db.Column(db.Text)  # JSON array
    contraindications_ar = db.Column(db.Text)  # JSON array
    drug_interactions = db.Column(db.Text)  # JSON array
    drug_interactions_ar = db.Column(db.Text)  # JSON array
    warnings = db.Column(db.Text)  # JSON array
    warnings_ar = db.Column(db.Text)  # JSON array
    dosage_instructions = db.Column(db.Text)
    dosage_instructions_ar = db.Column(db.Text)
    
    # Images and Media
    image_url = db.Column(db.String(500))
    additional_images = db.Column(db.Text)  # JSON array
    package_insert_url = db.Column(db.String(500))
    
    # SEO and Marketing (Arabic + English)
    slug = db.Column(db.String(200), unique=True)
    meta_title = db.Column(db.String(200))
    meta_title_ar = db.Column(db.String(200))
    meta_description = db.Column(db.Text)
    meta_description_ar = db.Column(db.Text)
    keywords = db.Column(db.Text)  # Comma-separated
    keywords_ar = db.Column(db.Text)  # Comma-separated
    
    # Status and Flags
    is_active = db.Column(db.Boolean, default=True, index=True)
    is_featured = db.Column(db.Boolean, default=False)
    is_otc = db.Column(db.Boolean, default=True)  # Over-the-counter
    is_generic = db.Column(db.Boolean, default=False)
    is_available = db.Column(db.Boolean, default=True)
        
    # Quality and Ratings
    rating = db.Column(db.Float, default=0.0)
    total_reviews = db.Column(db.Integer, default=0)
    total_sales = db.Column(db.Integer, default=0)
    
    # Source and Import
    source = db.Column(db.String(50), default='manual')  # manual, fda_catalog, import
    import_batch_id = db.Column(db.String(100))
    
    # Foreign Keys
    pharmacy_id = db.Column(db.String(36), db.ForeignKey('pharmacies.id'), nullable=False)
    created_by = db.Column(db.String(36), db.ForeignKey('pharmacies.id'))
    updated_by = db.Column(db.String(36), db.ForeignKey('pharmacies.id'))
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_restocked = db.Column(db.DateTime)
    
    # Relationships
    reviews = db.relationship('Review', backref='product', lazy='dynamic', cascade='all, delete-orphan')
    order_items = db.relationship('OrderItem', backref='product', lazy='dynamic')
    favorites = db.relationship('UserFavorite', backref='product', lazy='dynamic', cascade='all, delete-orphan')
    
    def __init__(self, **kwargs):
        super(Product, self).__init__(**kwargs)
        if not self.slug and self.product_name:
            self.slug = self.generate_slug(self.product_name)
    
    def generate_slug(self, name):
        """Generate URL-friendly slug from name"""
        import re
        slug = re.sub(r'[^\w\s-]', '', name.lower())
        slug = re.sub(r'[-\s]+', '-', slug)
        return slug.strip('-')
    
    def set_json_field(self, field_name, data):
        """Set JSON field"""
        if data and isinstance(data, list):
            setattr(self, field_name, json.dumps(data, ensure_ascii=False))
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
    
    def get_localized_field(self, field_name, language='ar'):
        """Get localized field value with fallback"""
        if language == 'ar':
            ar_field = f"{field_name}_ar"
            ar_value = getattr(self, ar_field, None)
            if ar_value:
                return ar_value
        
        # Fallback to English
        return getattr(self, field_name, None)
    
    def get_name(self, language='ar'):
        """Get product name in specified language"""
        return self.get_localized_field('product_name', language)
    
    def get_description(self, language='ar'):
        """Get description in specified language"""
        return self.get_localized_field('description', language)
    
    def get_manufacturer(self, language='ar'):
        """Get manufacturer in specified language"""
        return self.get_localized_field('manufacturer', language)
    
    def get_active_ingredients(self, language='ar'):
        """Get active ingredients in specified language"""
        field_name = 'active_ingredients_ar' if language == 'ar' else 'active_ingredients'
        return self.get_json_field(field_name)
    
    def get_side_effects(self, language='ar'):
        """Get side effects in specified language"""
        field_name = 'side_effects_ar' if language == 'ar' else 'side_effects'
        return self.get_json_field(field_name)
    
    def get_contraindications(self, language='ar'):
        """Get contraindications in specified language"""
        field_name = 'contraindications_ar' if language == 'ar' else 'contraindications'
        return self.get_json_field(field_name)
    
    def get_warnings(self, language='ar'):
        """Get warnings in specified language"""
        field_name = 'warnings_ar' if language == 'ar' else 'warnings'
        return self.get_json_field(field_name)
    
    def get_additional_images(self):
        """Get additional images list"""
        return self.get_json_field('additional_images')
    
    def calculate_final_price(self):
        """Calculate final price after discount and tax"""
        price = self.selling_price
        
        # Apply discount
        if self.discount_percentage > 0:
            price = price * (1 - self.discount_percentage / 100)
        
        # Apply tax
        if self.tax_percentage > 0:
            price = price * (1 + self.tax_percentage / 100)
        
        return round(price, 2)
    
    def calculate_profit_margin(self):
        """Calculate profit margin percentage"""
        if not self.cost_price or self.cost_price == 0:
            return None
        
        profit = self.selling_price - self.cost_price
        margin = (profit / self.cost_price) * 100
        return round(margin, 2)
    
    def get_stock_status(self):
        """Get stock status"""
        if self.current_stock <= 0:
            return 'out_of_stock'
        elif self.current_stock <= self.minimum_stock:
            return 'low_stock'
        elif self.current_stock >= self.maximum_stock:
            return 'overstock'
        else:
            return 'in_stock'
    
    def is_expired(self):
        """Check if product is expired"""
        if not self.expiry_date:
            return False
        return datetime.now().date() > self.expiry_date
    
    def is_near_expiry(self, days=30):
        """Check if product is near expiry"""
        if not self.expiry_date:
            return False
        
        warning_date = datetime.now().date() + timedelta(days=days)
        return self.expiry_date <= warning_date
    
    def days_until_expiry(self):
        """Get number of days until expiry"""
        if not self.expiry_date:
            return None
        
        delta = self.expiry_date - datetime.now().date()
        return delta.days if delta.days >= 0 else 0
    
    def needs_reorder(self):
        """Check if product needs reordering"""
        return self.current_stock <= self.reorder_level
    
    def update_stock(self, quantity, operation='add'):
        """Update stock quantity"""
        if operation == 'add':
            self.current_stock += quantity
            self.last_restocked = datetime.utcnow()
        elif operation == 'subtract':
            self.current_stock = max(0, self.current_stock - quantity)
        elif operation == 'set':
            self.current_stock = max(0, quantity)
            self.last_restocked = datetime.utcnow()
    
    def update_rating(self):
        """Update product rating based on reviews"""
        approved_reviews = self.reviews.filter_by(is_approved=True).all()
        if approved_reviews:
            self.rating = sum(review.rating for review in approved_reviews) / len(approved_reviews)
            self.total_reviews = len(approved_reviews)
        else:
            self.rating = 0.0
            self.total_reviews = 0
    
    def to_dict(self, language='ar', include_medical_info=True):
        """Convert product to dictionary with language support"""
        data = {
            'id': self.id,
            'uuid': self.uuid,
            'product_name': self.get_name(language),
            'generic_name': self.get_localized_field('generic_name', language),
            'brand_name': self.get_localized_field('brand_name', language),
            'description': self.get_description(language),
            'manufacturer': self.get_manufacturer(language),
            'country_of_origin': self.get_localized_field('country_of_origin', language),
            'category_id': self.category_id,
            'category': self.category.to_dict() if self.category else None,
            'therapeutic_class': self.get_localized_field('therapeutic_class', language),
            'pharmacological_class': self.get_localized_field('pharmacological_class', language),
            'atc_code': self.atc_code,
            'dosage_form': self.get_localized_field('dosage_form', language),
            'strength': self.get_localized_field('strength', language),
            'route': self.get_localized_field('route', language),
            'package_size': self.get_localized_field('package_size', language),
            'pricing': {
                'cost_price': self.cost_price,
                'selling_price': self.selling_price,
                'final_price': self.calculate_final_price(),
                'discount_percentage': self.discount_percentage,
                'tax_percentage': self.tax_percentage,
                'currency': self.currency,
                'profit_margin': self.calculate_profit_margin()
            },
            'inventory': {
                'current_stock': self.current_stock,
                'minimum_stock': self.minimum_stock,
                'maximum_stock': self.maximum_stock,
                'reorder_level': self.reorder_level,
                'stock_status': self.get_stock_status(),
                'needs_reorder': self.needs_reorder(),
                'last_restocked': self.last_restocked.isoformat() if self.last_restocked else None
            },
            'identification': {
                'barcode': self.barcode,
                'sku': self.sku,
                'batch_number': self.batch_number,
                'registration_number': self.registration_number
            },
            'dates': {
                'manufacturing_date': self.manufacturing_date.isoformat() if self.manufacturing_date else None,
                'expiry_date': self.expiry_date.isoformat() if self.expiry_date else None,
                'days_until_expiry': self.days_until_expiry(),
                'is_expired': self.is_expired(),
                'is_near_expiry': self.is_near_expiry()
            },
            'regulatory': {
                'requires_prescription': self.requires_prescription,
                'is_controlled': self.is_controlled,
                'controlled_class': self.controlled_class,
                'age_restriction': self.age_restriction,
                'pregnancy_category': self.pregnancy_category
            },
            'storage': {
                'temperature': self.get_localized_field('storage_temperature', language),
                'instructions': self.get_localized_field('storage_instructions', language),
                'requires_refrigeration': self.requires_refrigeration
            },
            'media': {
                'image_url': self.image_url,
                'additional_images': self.get_additional_images(),
                'package_insert_url': self.package_insert_url
            },
            'status': {
                'is_active': self.is_active,
                'is_featured': self.is_featured,
                'is_otc': self.is_otc,
                'is_generic': self.is_generic,
                'is_available': self.is_available
            },
            'metrics': {
                'rating': self.rating,
                'total_reviews': self.total_reviews,
                'total_sales': self.total_sales
            },
            'pharmacy_id': self.pharmacy_id,
            'pharmacy': self.pharmacy.to_dict() if self.pharmacy else None,
            'source': self.source,
            'slug': self.slug,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }
        
        if include_medical_info:
            data['medical_info'] = {
                'active_ingredients': self.get_active_ingredients(language),
                'side_effects': self.get_side_effects(language),
                'contraindications': self.get_contraindications(language),
                'drug_interactions': self.get_json_field('drug_interactions_ar' if language == 'ar' else 'drug_interactions'),
                'warnings': self.get_warnings(language),
                'dosage_instructions': self.get_localized_field('dosage_instructions', language)
            }
        
        return data
    
    @classmethod
    def search(cls, query, language='ar', category_id=None, pharmacy_id=None):
        """Search products with language support"""
        search_query = cls.query.filter(cls.is_active == True)
        
        if category_id:
            search_query = search_query.filter(cls.category_id == category_id)
        
        if pharmacy_id:
            search_query = search_query.filter(cls.pharmacy_id == pharmacy_id)
        
        if query:
            if language == 'ar':
                search_query = search_query.filter(
                    db.or_(
                        cls.product_name_ar.contains(query),
                        cls.generic_name_ar.contains(query),
                        cls.brand_name_ar.contains(query),
                        cls.description_ar.contains(query),
                        cls.manufacturer_ar.contains(query),
                        cls.keywords_ar.contains(query)
                    )
                )
            else:
                search_query = search_query.filter(
                    db.or_(
                        cls.product_name.contains(query),
                        cls.generic_name.contains(query),
                        cls.brand_name.contains(query),
                        cls.description.contains(query),
                        cls.manufacturer.contains(query),
                        cls.keywords.contains(query)
                    )
                )
        
        return search_query
    
    def __repr__(self):
        return f'<Product {self.product_name}>'

