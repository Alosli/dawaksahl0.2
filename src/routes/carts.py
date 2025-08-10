from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity
from src.models import db
from src.models.cart import Cart
from src.models.product import Product
from src.models.user import User

cart_bp = Blueprint('cart', __name__)

@cart_bp.route('/', methods=['GET'])
@jwt_required()
def get_cart():
    """Get user's cart items"""
    try:
        current_identity = get_jwt_identity()
        user_id = current_identity['id']
        
        # Get all cart items for user
        cart_items = Cart.query.filter_by(user_id=user_id).all()
        
        # Include product details
        items_with_products = []
        for cart_item in cart_items:
            product = Product.query.get(cart_item.product_id)
            if product:
                item_data = cart_item.to_dict()
                item_data['product'] = product.to_dict()
                items_with_products.append(item_data)
        
        return jsonify({
            'success': True,
            'data': {
                'items': items_with_products,
                'total_items': len(items_with_products)
            }
        }), 200
        
    except Exception as e:
        current_app.logger.error(f"Get cart error: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'Failed to get cart',
            'message_ar': 'فشل في جلب السلة'
        }), 500

@cart_bp.route('/add', methods=['POST'])
@jwt_required()
def add_to_cart():
    """Add item to cart"""
    try:
        current_identity = get_jwt_identity()
        user_id = current_identity['id']
        
        data = request.get_json()
        product_id = data.get('product_id')
        quantity = data.get('quantity', 1)
        
        if not product_id:
            return jsonify({
                'success': False,
                'message': 'Product ID is required',
                'message_ar': 'معرف المنتج مطلوب'
            }), 400
        
        # Check if product exists
        product = Product.query.get(product_id)
        if not product:
            return jsonify({
                'success': False,
                'message': 'Product not found',
                'message_ar': 'المنتج غير موجود'
            }), 404
        
        # Check if item already in cart
        existing_item = Cart.query.filter_by(
            user_id=user_id,
            product_id=product_id
        ).first()
        
        if existing_item:
            # Update quantity
            existing_item.quantity += quantity
            existing_item.updated_at = datetime.utcnow()
        else:
            # Create new cart item
            cart_item = Cart(
                user_id=user_id,
                product_id=product_id,
                quantity=quantity
            )
            db.session.add(cart_item)
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Item added to cart',
            'message_ar': 'تم إضافة العنصر إلى السلة'
        }), 200
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Add to cart error: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'Failed to add item to cart',
            'message_ar': 'فشل في إضافة العنصر إلى السلة'
        }), 500

@cart_bp.route('/<cart_item_id>', methods=['PUT'])
@jwt_required()
def update_cart_item(cart_item_id):
    """Update cart item quantity"""
    try:
        current_identity = get_jwt_identity()
        user_id = current_identity['id']
        
        data = request.get_json()
        quantity = data.get('quantity')
        
        if quantity is None or quantity < 0:
            return jsonify({
                'success': False,
                'message': 'Valid quantity is required',
                'message_ar': 'الكمية المطلوبة غير صحيحة'
            }), 400
        
        # Find cart item
        cart_item = Cart.query.filter_by(
            id=cart_item_id,
            user_id=user_id
        ).first()
        
        if not cart_item:
            return jsonify({
                'success': False,
                'message': 'Cart item not found',
                'message_ar': 'عنصر السلة غير موجود'
            }), 404
        
        if quantity == 0:
            # Remove item if quantity is 0
            db.session.delete(cart_item)
        else:
            # Update quantity
            cart_item.quantity = quantity
            cart_item.updated_at = datetime.utcnow()
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Cart item updated',
            'message_ar': 'تم تحديث عنصر السلة'
        }), 200
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Update cart item error: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'Failed to update cart item',
            'message_ar': 'فشل في تحديث عنصر السلة'
        }), 500

@cart_bp.route('/<cart_item_id>', methods=['DELETE'])
@jwt_required()
def remove_cart_item(cart_item_id):
    """Remove item from cart"""
    try:
        current_identity = get_jwt_identity()
        user_id = current_identity['id']
        
        # Find cart item
        cart_item = Cart.query.filter_by(
            id=cart_item_id,
            user_id=user_id
        ).first()
        
        if not cart_item:
            return jsonify({
                'success': False,
                'message': 'Cart item not found',
                'message_ar': 'عنصر السلة غير موجود'
            }), 404
        
        db.session.delete(cart_item)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Item removed from cart',
            'message_ar': 'تم حذف العنصر من السلة'
        }), 200
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Remove cart item error: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'Failed to remove cart item',
            'message_ar': 'فشل في حذف عنصر السلة'
        }), 500

@cart_bp.route('/clear', methods=['DELETE'])
@jwt_required()
def clear_cart():
    """Clear all items from cart"""
    try:
        current_identity = get_jwt_identity()
        user_id = current_identity['id']
        
        Cart.query.filter_by(user_id=user_id).delete()
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Cart cleared',
            'message_ar': 'تم مسح السلة'
        }), 200
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Clear cart error: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'Failed to clear cart',
            'message_ar': 'فشل في مسح السلة'
        }), 500
