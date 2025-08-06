from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity, get_jwt
from sqlalchemy import or_, and_, func
from datetime import datetime

from src.models import db
from src.models.product import Product
from src.models.category import Category
from src.models.pharmacy import Pharmacy
from src.services.auth_service import AuthService

products_bp = Blueprint('products', __name__)

@products_bp.route('/products', methods=['GET'])
def get_products():
    """Get products for patients (public endpoint)"""
    try:
        # Get query parameters
        page = request.args.get('page', 1, type=int)
        per_page = min(request.args.get('per_page', 20, type=int), 100)
        search = request.args.get('search', '').strip()
        category_id = request.args.get('category_id', type=int)
        pharmacy_id = request.args.get('pharmacy_id')
        sort_by = request.args.get('sort_by', 'relevance')
        language = request.args.get('language', 'ar')
        
        # Filters
        in_stock = request.args.get('in_stock', type=bool)
        prescription_required = request.args.get('prescription_required', type=bool)
        is_generic = request.args.get('is_generic', type=bool)
        min_price = request.args.get('min_price', type=float)
        max_price = request.args.get('max_price', type=float)
        
        # Build query
        query = Product.query.filter(Product.is_active == True, Product.is_available == True)
        
        # Apply filters
        if search:
            if language == 'ar':
                search_filter = or_(
                    Product.product_name_ar.contains(search),
                    Product.generic_name_ar.contains(search),
                    Product.brand_name_ar.contains(search),
                    Product.description_ar.contains(search),
                    Product.manufacturer_ar.contains(search),
                    Product.keywords_ar.contains(search)
                )
            else:
                search_filter = or_(
                    Product.product_name.contains(search),
                    Product.generic_name.contains(search),
                    Product.brand_name.contains(search),
                    Product.description.contains(search),
                    Product.manufacturer.contains(search),
                    Product.keywords.contains(search)
                )
            query = query.filter(search_filter)
        
        if category_id:
            query = query.filter(Product.category_id == category_id)
        
        if pharmacy_id:
            query = query.filter(Product.pharmacy_id == pharmacy_id)
        
        if in_stock is not None:
            if in_stock:
                query = query.filter(Product.current_stock > 0)
            else:
                query = query.filter(Product.current_stock <= 0)
        
        if prescription_required is not None:
            query = query.filter(Product.requires_prescription == prescription_required)
        
        if is_generic is not None:
            query = query.filter(Product.is_generic == is_generic)
        
        if min_price is not None:
            query = query.filter(Product.selling_price >= min_price)
        
        if max_price is not None:
            query = query.filter(Product.selling_price <= max_price)
        
        # Apply sorting
        if sort_by == 'price_asc':
            query = query.order_by(Product.selling_price.asc())
        elif sort_by == 'price_desc':
            query = query.order_by(Product.selling_price.desc())
        elif sort_by == 'name':
            if language == 'ar':
                query = query.order_by(Product.product_name_ar.asc())
            else:
                query = query.order_by(Product.product_name.asc())
        elif sort_by == 'rating_desc':
            query = query.order_by(Product.rating.desc())
        elif sort_by == 'newest':
            query = query.order_by(Product.created_at.desc())
        elif sort_by == 'popularity':
            query = query.order_by(Product.total_sales.desc())
        else:  # relevance (default)
            if search:
                # Simple relevance scoring - can be improved
                query = query.order_by(Product.rating.desc(), Product.total_sales.desc())
            else:
                query = query.order_by(Product.rating.desc(), Product.created_at.desc())
        
        # Paginate
        pagination = query.paginate(
            page=page,
            per_page=per_page,
            error_out=False
        )
        
        products = [product.to_dict(language=language, include_medical_info=False) for product in pagination.items]
        
        return jsonify({
            'success': True,
            'data': {
                'items': products,
                'page': page,
                'pages': pagination.pages,
                'per_page': per_page,
                'total': pagination.total,
                'has_next': pagination.has_next,
                'has_prev': pagination.has_prev
            }
        }), 200
        
    except Exception as e:
        current_app.logger.error(f"Get products error: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'Failed to fetch products',
            'message_ar': 'فشل في جلب المنتجات'
        }), 500

@products_bp.route('/products/<int:product_id>', methods=['GET'])
def get_product(product_id):
    """Get single product details"""
    try:
        language = request.args.get('language', 'ar')
        
        product = Product.query.filter_by(id=product_id, is_active=True).first()
        if not product:
            return jsonify({
                'success': False,
                'message': 'Product not found',
                'message_ar': 'المنتج غير موجود'
            }), 404
        
        return jsonify({
            'success': True,
            'data': product.to_dict(language=language, include_medical_info=True)
        }), 200
        
    except Exception as e:
        current_app.logger.error(f"Get product error: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'Failed to fetch product',
            'message_ar': 'فشل في جلب المنتج'
        }), 500

@products_bp.route('/categories', methods=['GET'])
def get_categories():
    """Get product categories"""
    try:
        language = request.args.get('language', 'ar')
        
        categories = Category.query.filter_by(is_active=True).order_by(Category.sort_order, Category.name).all()
        
        return jsonify({
            'success': True,
            'data': [category.to_dict(language=language) for category in categories]
        }), 200
        
    except Exception as e:
        current_app.logger.error(f"Get categories error: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'Failed to fetch categories',
            'message_ar': 'فشل في جلب الفئات'
        }), 500

@products_bp.route('/pharmacy/products', methods=['GET'])
@jwt_required()
def get_pharmacy_products():
    """Get products for pharmacy management"""
    try:
        current_identity = get_jwt_identity()
        if current_identity['type'] != 'pharmacy':
            return jsonify({
                'success': False,
                'message': 'Access denied',
                'message_ar': 'الوصول مرفوض'
            }), 403
        
        pharmacy_id = current_identity['id']
        
        # Get query parameters
        page = request.args.get('page', 1, type=int)
        per_page = min(request.args.get('per_page', 20, type=int), 100)
        search = request.args.get('search', '').strip()
        category_id = request.args.get('category_id', type=int)
        sort_by = request.args.get('sort_by', 'name')
        language = request.args.get('language', 'ar')
        
        # Filters
        in_stock = request.args.get('in_stock', type=bool)
        low_stock = request.args.get('low_stock', type=bool)
        expired = request.args.get('expired', type=bool)
        near_expiry = request.args.get('near_expiry', type=bool)
        
        # Build query for pharmacy's products
        query = Product.query.filter(Product.pharmacy_id == pharmacy_id)
        
        # Apply filters
        if search:
            if language == 'ar':
                search_filter = or_(
                    Product.product_name_ar.contains(search),
                    Product.generic_name_ar.contains(search),
                    Product.brand_name_ar.contains(search),
                    Product.sku.contains(search),
                    Product.barcode.contains(search)
                )
            else:
                search_filter = or_(
                    Product.product_name.contains(search),
                    Product.generic_name.contains(search),
                    Product.brand_name.contains(search),
                    Product.sku.contains(search),
                    Product.barcode.contains(search)
                )
            query = query.filter(search_filter)
        
        if category_id:
            query = query.filter(Product.category_id == category_id)
        
        if in_stock is not None:
            if in_stock:
                query = query.filter(Product.current_stock > 0)
            else:
                query = query.filter(Product.current_stock <= 0)
        
        if low_stock:
            query = query.filter(Product.current_stock <= Product.minimum_stock)
        
        if expired:
            query = query.filter(Product.expiry_date <= datetime.now().date())
        
        if near_expiry:
            from datetime import timedelta
            warning_date = datetime.now().date() + timedelta(days=30)
            query = query.filter(
                and_(
                    Product.expiry_date <= warning_date,
                    Product.expiry_date > datetime.now().date()
                )
            )
        
        # Apply sorting
        if sort_by == 'name':
            if language == 'ar':
                query = query.order_by(Product.product_name_ar.asc())
            else:
                query = query.order_by(Product.product_name.asc())
        elif sort_by == 'stock':
            query = query.order_by(Product.current_stock.asc())
        elif sort_by == 'price':
            query = query.order_by(Product.selling_price.asc())
        elif sort_by == 'expiry':
            query = query.order_by(Product.expiry_date.asc())
        elif sort_by == 'created':
            query = query.order_by(Product.created_at.desc())
        else:
            query = query.order_by(Product.product_name.asc())
        
        # Paginate
        pagination = query.paginate(
            page=page,
            per_page=per_page,
            error_out=False
        )
        
        products = [product.to_dict(language=language, include_medical_info=True) for product in pagination.items]
        
        return jsonify({
            'success': True,
            'data': {
                'items': products,
                'page': page,
                'pages': pagination.pages,
                'per_page': per_page,
                'total': pagination.total,
                'has_next': pagination.has_next,
                'has_prev': pagination.has_prev
            }
        }), 200
        
    except Exception as e:
        current_app.logger.error(f"Get pharmacy products error: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'Failed to fetch products',
            'message_ar': 'فشل في جلب المنتجات'
        }), 500

@products_bp.route('/pharmacy/products', methods=['POST'])
@jwt_required()
def create_product():
    """Create new product (pharmacy only)"""
    try:
        current_identity = get_jwt_identity()
        if current_identity['type'] != 'pharmacy':
            return jsonify({
                'success': False,
                'message': 'Access denied',
                'message_ar': 'الوصول مرفوض'
            }), 403
        
        pharmacy_id = current_identity['id']
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['product_name', 'category_id', 'selling_price', 'current_stock']
        for field in required_fields:
            if not data.get(field):
                return jsonify({
                    'success': False,
                    'message': f'{field} is required',
                    'message_ar': f'{field} مطلوب'
                }), 400
        
        # Create product
        product = Product(
            pharmacy_id=pharmacy_id,
            created_by=pharmacy_id,
            **data
        )
        
        db.session.add(product)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Product created successfully',
            'message_ar': 'تم إنشاء المنتج بنجاح',
            'data': product.to_dict()
        }), 201
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Create product error: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'Failed to create product',
            'message_ar': 'فشل في إنشاء المنتج'
        }), 500

@products_bp.route('/pharmacy/products/<int:product_id>', methods=['PUT'])
@jwt_required()
def update_product(product_id):
    """Update product (pharmacy only)"""
    try:
        current_identity = get_jwt_identity()
        if current_identity['type'] != 'pharmacy':
            return jsonify({
                'success': False,
                'message': 'Access denied',
                'message_ar': 'الوصول مرفوض'
            }), 403
        
        pharmacy_id = current_identity['id']
        
        product = Product.query.filter_by(id=product_id, pharmacy_id=pharmacy_id).first()
        if not product:
            return jsonify({
                'success': False,
                'message': 'Product not found',
                'message_ar': 'المنتج غير موجود'
            }), 404
        
        data = request.get_json()
        
        # Update allowed fields
        allowed_fields = [
            'product_name', 'product_name_ar', 'generic_name', 'generic_name_ar',
            'brand_name', 'brand_name_ar', 'description', 'description_ar',
            'manufacturer', 'manufacturer_ar', 'category_id', 'selling_price',
            'current_stock', 'minimum_stock', 'maximum_stock', 'reorder_level',
            'dosage_form', 'dosage_form_ar', 'strength', 'strength_ar',
            'requires_prescription', 'is_otc', 'is_generic', 'is_available',
            'storage_temperature', 'storage_temperature_ar', 'storage_instructions',
            'storage_instructions_ar', 'expiry_date', 'image_url'
        ]
        
        for field in allowed_fields:
            if field in data:
                setattr(product, field, data[field])
        
        product.updated_by = pharmacy_id
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Product updated successfully',
            'message_ar': 'تم تحديث المنتج بنجاح',
            'data': product.to_dict()
        }), 200
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Update product error: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'Failed to update product',
            'message_ar': 'فشل في تحديث المنتج'
        }), 500

@products_bp.route('/pharmacy/products/<int:product_id>', methods=['DELETE'])
@jwt_required()
def delete_product(product_id):
    """Delete product (pharmacy only)"""
    try:
        current_identity = get_jwt_identity()
        if current_identity['type'] != 'pharmacy':
            return jsonify({
                'success': False,
                'message': 'Access denied',
                'message_ar': 'الوصول مرفوض'
            }), 403
        
        pharmacy_id = current_identity['id']
        
        product = Product.query.filter_by(id=product_id, pharmacy_id=pharmacy_id).first()
        if not product:
            return jsonify({
                'success': False,
                'message': 'Product not found',
                'message_ar': 'المنتج غير موجود'
            }), 404
        
        # Soft delete
        product.is_active = False
        product.updated_by = pharmacy_id
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Product deleted successfully',
            'message_ar': 'تم حذف المنتج بنجاح'
        }), 200
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Delete product error: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'Failed to delete product',
            'message_ar': 'فشل في حذف المنتج'
        }), 500

@products_bp.route('/pharmacy/products/<int:product_id>/stock', methods=['PUT'])
@jwt_required()
def update_stock(product_id):
    """Update product stock (pharmacy only)"""
    try:
        current_identity = get_jwt_identity()
        if current_identity['type'] != 'pharmacy':
            return jsonify({
                'success': False,
                'message': 'Access denied',
                'message_ar': 'الوصول مرفوض'
            }), 403
        
        pharmacy_id = current_identity['id']
        
        product = Product.query.filter_by(id=product_id, pharmacy_id=pharmacy_id).first()
        if not product:
            return jsonify({
                'success': False,
                'message': 'Product not found',
                'message_ar': 'المنتج غير موجود'
            }), 404
        
        data = request.get_json()
        quantity = data.get('quantity')
        operation = data.get('operation', 'set')  # 'add', 'subtract', 'set'
        
        if quantity is None:
            return jsonify({
                'success': False,
                'message': 'Quantity is required',
                'message_ar': 'الكمية مطلوبة'
            }), 400
        
        old_stock = product.current_stock
        product.update_stock(quantity, operation)
        product.updated_by = pharmacy_id
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Stock updated successfully',
            'message_ar': 'تم تحديث المخزون بنجاح',
            'data': {
                'old_stock': old_stock,
                'new_stock': product.current_stock,
                'operation': operation,
                'quantity': quantity
            }
        }), 200
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Update stock error: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'Failed to update stock',
            'message_ar': 'فشل في تحديث المخزون'
        }), 500

@products_bp.route('/pharmacy/stats', methods=['GET'])
@jwt_required()
def get_pharmacy_stats():
    """Get pharmacy product statistics"""
    try:
        current_identity = get_jwt_identity()
        if current_identity['type'] != 'pharmacy':
            return jsonify({
                'success': False,
                'message': 'Access denied',
                'message_ar': 'الوصول مرفوض'
            }), 403
        
        pharmacy_id = current_identity['id']
        
        # Get basic stats
        total_products = Product.query.filter_by(pharmacy_id=pharmacy_id, is_active=True).count()
        in_stock = Product.query.filter(
            Product.pharmacy_id == pharmacy_id,
            Product.is_active == True,
            Product.current_stock > 0
        ).count()
        out_of_stock = Product.query.filter(
            Product.pharmacy_id == pharmacy_id,
            Product.is_active == True,
            Product.current_stock <= 0
        ).count()
        low_stock = Product.query.filter(
            Product.pharmacy_id == pharmacy_id,
            Product.is_active == True,
            Product.current_stock <= Product.minimum_stock,
            Product.current_stock > 0
        ).count()
        
        # Get expiry stats
        from datetime import timedelta
        today = datetime.now().date()
        warning_date = today + timedelta(days=30)
        
        expired = Product.query.filter(
            Product.pharmacy_id == pharmacy_id,
            Product.is_active == True,
            Product.expiry_date <= today
        ).count()
        
        near_expiry = Product.query.filter(
            Product.pharmacy_id == pharmacy_id,
            Product.is_active == True,
            Product.expiry_date <= warning_date,
            Product.expiry_date > today
        ).count()
        
        # Get category breakdown
        category_stats = db.session.query(
            Category.name,
            Category.name_ar,
            func.count(Product.id).label('count')
        ).join(Product).filter(
            Product.pharmacy_id == pharmacy_id,
            Product.is_active == True
        ).group_by(Category.id).all()
        
        return jsonify({
            'success': True,
            'data': {
                'inventory': {
                    'total_products': total_products,
                    'in_stock': in_stock,
                    'out_of_stock': out_of_stock,
                    'low_stock': low_stock
                },
                'expiry': {
                    'expired': expired,
                    'near_expiry': near_expiry
                },
                'categories': [
                    {
                        'name': stat.name,
                        'name_ar': stat.name_ar,
                        'count': stat.count
                    }
                    for stat in category_stats
                ]
            }
        }), 200
        
    except Exception as e:
        current_app.logger.error(f"Get pharmacy stats error: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'Failed to fetch statistics',
            'message_ar': 'فشل في جلب الإحصائيات'
        }), 500

@products_bp.route('/search', methods=['GET'])
def search_products():
    """Advanced product search"""
    try:
        query_text = request.args.get('q', '').strip()
        language = request.args.get('language', 'ar')
        limit = min(request.args.get('limit', 10, type=int), 50)
        
        if not query_text:
            return jsonify({
                'success': True,
                'data': []
            }), 200
        
        # Search products
        products = Product.search(
            query=query_text,
            language=language
        ).filter(
            Product.is_active == True,
            Product.is_available == True
        ).limit(limit).all()
        
        return jsonify({
            'success': True,
            'data': [product.to_dict(language=language, include_medical_info=False) for product in products]
        }), 200
        
    except Exception as e:
        current_app.logger.error(f"Search products error: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'Search failed',
            'message_ar': 'فشل البحث'
        }), 500

