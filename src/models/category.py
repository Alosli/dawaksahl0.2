from datetime import datetime
from src.models.user import db
import uuid

class Category(db.Model):
    """Unified Category model - replaces both product_categories and medication_categories"""
    __tablename__ = 'categories'
    
    # Primary Key
    id = db.Column(db.Integer, primary_key=True)
    uuid = db.Column(db.String(36), unique=True, index=True, default=lambda: str(uuid.uuid4()))
    
    # Category Information
    name = db.Column(db.String(100), nullable=False)
    name_ar = db.Column(db.String(100))
    description = db.Column(db.Text)
    description_ar = db.Column(db.Text)
    
    # Hierarchy Support
    parent_id = db.Column(db.Integer, db.ForeignKey('categories.id'))
    level = db.Column(db.Integer, default=0)  # 0 = root, 1 = subcategory, etc.
    path = db.Column(db.String(500))  # e.g., "1/5/12" for hierarchy navigation
    
    # Display Properties
    icon = db.Column(db.String(50))  # Icon name or class
    color = db.Column(db.String(7))  # Hex color code
    image_url = db.Column(db.String(500))  # Category image
    sort_order = db.Column(db.Integer, default=0)
    
    # Category Properties
    category_code = db.Column(db.String(20), unique=True)  # 'PAIN', 'ANTI', 'VITA', etc.
    requires_prescription = db.Column(db.Boolean, default=False)
    is_controlled = db.Column(db.Boolean, default=False)
    age_restriction = db.Column(db.Integer)  # Minimum age required
    
    # SEO and Marketing
    slug = db.Column(db.String(100), unique=True)  # URL-friendly name
    meta_title = db.Column(db.String(200))
    meta_description = db.Column(db.Text)
    keywords = db.Column(db.Text)  # Comma-separated keywords
    
    # Status
    is_active = db.Column(db.Boolean, default=True)
    is_featured = db.Column(db.Boolean, default=False)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    parent = db.relationship('Category', remote_side=[id], backref='children')
    products = db.relationship('Product', backref='category', lazy='dynamic')
    
    def __init__(self, **kwargs):
        super(Category, self).__init__(**kwargs)
        if not self.slug and self.name:
            self.slug = self.generate_slug(self.name)
        if not self.category_code and self.name:
            self.category_code = self.generate_code(self.name)
    
    def generate_slug(self, name):
        """Generate URL-friendly slug from name"""
        import re
        slug = re.sub(r'[^\w\s-]', '', name.lower())
        slug = re.sub(r'[-\s]+', '-', slug)
        return slug.strip('-')
    
    def generate_code(self, name):
        """Generate category code from name"""
        words = name.upper().split()
        if len(words) == 1:
            return words[0][:4]
        else:
            return ''.join(word[0] for word in words[:4])
    
    def update_path(self):
        """Update the path based on parent hierarchy"""
        if self.parent:
            self.parent.update_path()  # Ensure parent path is updated
            self.path = f"{self.parent.path}/{self.id}"
            self.level = self.parent.level + 1
        else:
            self.path = str(self.id)
            self.level = 0
    
    def get_ancestors(self):
        """Get all ancestor categories"""
        if not self.path:
            return []
        
        ancestor_ids = [int(id) for id in self.path.split('/')[:-1]]
        if not ancestor_ids:
            return []
        
        return Category.query.filter(Category.id.in_(ancestor_ids)).order_by(Category.level).all()
    
    def get_descendants(self):
        """Get all descendant categories"""
        return Category.query.filter(Category.path.like(f"{self.path}/%")).all()
    
    def get_siblings(self):
        """Get sibling categories"""
        return Category.query.filter(
            Category.parent_id == self.parent_id,
            Category.id != self.id
        ).order_by(Category.sort_order, Category.name).all()
    
    def get_root_category(self):
        """Get the root category of this hierarchy"""
        if self.parent:
            return self.parent.get_root_category()
        return self
    
    def get_breadcrumb(self):
        """Get breadcrumb trail"""
        breadcrumb = []
        ancestors = self.get_ancestors()
        for ancestor in ancestors:
            breadcrumb.append({
                'id': ancestor.id,
                'name': ancestor.name,
                'name_ar': ancestor.name_ar,
                'slug': ancestor.slug
            })
        breadcrumb.append({
            'id': self.id,
            'name': self.name,
            'name_ar': self.name_ar,
            'slug': self.slug
        })
        return breadcrumb
    
    def get_product_count(self, include_descendants=True):
        """Get total number of products in this category"""
        count = self.products.filter_by(is_active=True).count()
        
        if include_descendants:
            for child in self.children:
                count += child.get_product_count(include_descendants=True)
        
        return count
    
    def get_featured_products(self, limit=10):
        """Get featured products from this category"""
        return self.products.filter_by(
            is_active=True,
            is_featured=True
        ).limit(limit).all()
    
    def to_dict(self, include_children=False, include_products=False):
        """Convert category to dictionary"""
        data = {
            'id': self.id,
            'uuid': self.uuid,
            'name': self.name,
            'name_ar': self.name_ar,
            'description': self.description,
            'description_ar': self.description_ar,
            'parent_id': self.parent_id,
            'level': self.level,
            'path': self.path,
            'icon': self.icon,
            'color': self.color,
            'image_url': self.image_url,
            'sort_order': self.sort_order,
            'category_code': self.category_code,
            'requires_prescription': self.requires_prescription,
            'is_controlled': self.is_controlled,
            'age_restriction': self.age_restriction,
            'slug': self.slug,
            'meta_title': self.meta_title,
            'meta_description': self.meta_description,
            'keywords': self.keywords,
            'is_active': self.is_active,
            'is_featured': self.is_featured,
            'product_count': self.get_product_count(),
            'breadcrumb': self.get_breadcrumb(),
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }
        
        if include_children:
            data['children'] = [
                child.to_dict(include_children=True) 
                for child in self.children 
                if child.is_active
            ]
        
        if include_products:
            data['products'] = [
                product.to_dict() 
                for product in self.get_featured_products()
            ]
        
        return data
    
    @classmethod
    def get_tree(cls, parent_id=None):
        """Get category tree structure"""
        categories = cls.query.filter_by(
            parent_id=parent_id,
            is_active=True
        ).order_by(cls.sort_order, cls.name).all()
        
        tree = []
        for category in categories:
            category_data = category.to_dict()
            category_data['children'] = cls.get_tree(category.id)
            tree.append(category_data)
        
        return tree
    
    @classmethod
    def get_featured_categories(cls, limit=10):
        """Get featured categories"""
        return cls.query.filter_by(
            is_active=True,
            is_featured=True
        ).order_by(cls.sort_order).limit(limit).all()
    
    @classmethod
    def search(cls, query, language='en'):
        """Search categories by name or description"""
        if language == 'ar':
            return cls.query.filter(
                db.or_(
                    cls.name_ar.contains(query),
                    cls.description_ar.contains(query)
                ),
                cls.is_active == True
            ).all()
        else:
            return cls.query.filter(
                db.or_(
                    cls.name.contains(query),
                    cls.description.contains(query),
                    cls.keywords.contains(query)
                ),
                cls.is_active == True
            ).all()
    
    def __repr__(self):
        return f'<Category {self.name}>'

