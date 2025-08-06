from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity
from datetime import datetime

from src.models.user import db
from src.models.favorite import UserFavorite
from src.models.product import Product
from src.models.pharmacy import Pharmacy
from src.services.auth_service import AuthService

favorites_bp = Blueprint('favorites', __name__)

@favorites_bp.route('', methods=['GET'])
@jwt_required()
def get_favorites():
    """Get user's favorite items"""
    try:
        current_identity = get_jwt_identity()
        if current_identity['type'] != 'user':
            return jsonify({
                'success': False,
                'message': 'Only users can have favorites',
                'message_ar': 'المستخدمون فقط يمكنهم الحصول على المفضلة'
            }), 403
        
        user_id = current_identity['id']
        
        # Get query parameters
        page = request.args.get('page', 1, type=int)
        per_page = min(request.args.get('per_page', 20, type=int), 100)
        language = request.args.get('language', 'ar')
        item_type = request.args.get('type')  # 'product' or 'pharmacy'
        
        # Build query
        query = UserFavorite.query.filter_by(user_id=user_id)
        
        if item_type:
            query = query.filter_by(item_type=item_type)
        
        # Order by creation date (newest first)
        query = query.order_by(UserFavorite.created_at.desc())
        
        # Paginate
        pagination = query.paginate(
            page=page,
            per_page=per_page,
            error_out=False
        )
        
        favorites = []
        for favorite in pagination.items:
            fav_data = favorite.to_dict(language=language)
            
            # Add item details
            if favorite.item_type == 'product':
                product = Product.query.get(favorite.item_id)
                if product:
                    fav_data['item'] = product.to_dict(language=language, include_medical_info=False)
            elif favorite.item_type == 'pharmacy':
                pharmacy = Pharmacy.query.get(favorite.item_id)
                if pharmacy:
                    fav_data['item'] = pharmacy.to_dict(language=language)
            
            favorites.append(fav_data)
        
        return jsonify({
            'success': True,
            'data': {
                'items': favorites,
                'page': page,
                'pages': pagination.pages,
                'per_page': per_page,
                'total': pagination.total,
                'has_next': pagination.has_next,
                'has_prev': pagination.has_prev
            }
        }), 200
        
    except Exception as e:
        current_app.logger.error(f"Get favorites error: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'Failed to fetch favorites',
            'message_ar': 'فشل في جلب المفضلة'
        }), 500

@favorites_bp.route('', methods=['POST'])
@jwt_required()
def add_favorite():
    """Add item to favorites"""
    try:
        current_identity = get_jwt_identity()
        if current_identity['type'] != 'user':
            return jsonify({
                'success': False,
                'message': 'Only users can add favorites',
                'message_ar': 'المستخدمون فقط يمكنهم إضافة المفضلة'
            }), 403
        
        user_id = current_identity['id']
        data = request.get_json()
        
        # Validate required fields
        item_id = data.get('item_id')
        item_type = data.get('item_type')
        
        if not item_id or not item_type:
            return jsonify({
                'success': False,
                'message': 'Item ID and type are required',
                'message_ar': 'معرف العنصر ونوعه مطلوبان'
            }), 400
        
        if item_type not in ['product', 'pharmacy']:
            return jsonify({
                'success': False,
                'message': 'Invalid item type',
                'message_ar': 'نوع العنصر غير صحيح'
            }), 400
        
        # Check if item exists
        if item_type == 'product':
            item = Product.query.get(item_id)
            if not item or not item.is_active:
                return jsonify({
                    'success': False,
                    'message': 'Product not found',
                    'message_ar': 'المنتج غير موجود'
                }), 404
        elif item_type == 'pharmacy':
            item = Pharmacy.query.get(item_id)
            if not item or item.account_status != 'active':
                return jsonify({
                    'success': False,
                    'message': 'Pharmacy not found',
                    'message_ar': 'الصيدلية غير موجودة'
                }), 404
        
        # Check if already in favorites
        existing_favorite = UserFavorite.query.filter_by(
            user_id=user_id,
            item_id=item_id,
            item_type=item_type
        ).first()
        
        if existing_favorite:
            return jsonify({
                'success': False,
                'message': 'Item is already in favorites',
                'message_ar': 'العنصر موجود في المفضلة بالفعل'
            }), 409
        
        # Create favorite
        favorite = UserFavorite(
            user_id=user_id,
            item_id=item_id,
            item_type=item_type,
            notes=data.get('notes'),
            notes_ar=data.get('notes_ar')
        )
        
        db.session.add(favorite)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Item added to favorites successfully',
            'message_ar': 'تم إضافة العنصر إلى المفضلة بنجاح',
            'data': favorite.to_dict()
        }), 201
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Add favorite error: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'Failed to add to favorites',
            'message_ar': 'فشل في إضافة إلى المفضلة'
        }), 500

@favorites_bp.route('/<favorite_id>', methods=['DELETE'])
@jwt_required()
def remove_favorite(favorite_id):
    """Remove item from favorites"""
    try:
        current_identity = get_jwt_identity()
        if current_identity['type'] != 'user':
            return jsonify({
                'success': False,
                'message': 'Only users can remove favorites',
                'message_ar': 'المستخدمون فقط يمكنهم إزالة المفضلة'
            }), 403
        
        user_id = current_identity['id']
        
        favorite = UserFavorite.query.filter_by(
            id=favorite_id,
            user_id=user_id
        ).first()
        
        if not favorite:
            return jsonify({
                'success': False,
                'message': 'Favorite not found',
                'message_ar': 'المفضلة غير موجودة'
            }), 404
        
        db.session.delete(favorite)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Item removed from favorites successfully',
            'message_ar': 'تم إزالة العنصر من المفضلة بنجاح'
        }), 200
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Remove favorite error: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'Failed to remove from favorites',
            'message_ar': 'فشل في إزالة من المفضلة'
        }), 500

@favorites_bp.route('/remove', methods=['DELETE'])
@jwt_required()
def remove_favorite_by_item():
    """Remove item from favorites by item ID and type"""
    try:
        current_identity = get_jwt_identity()
        if current_identity['type'] != 'user':
            return jsonify({
                'success': False,
                'message': 'Only users can remove favorites',
                'message_ar': 'المستخدمون فقط يمكنهم إزالة المفضلة'
            }), 403
        
        user_id = current_identity['id']
        data = request.get_json()
        
        item_id = data.get('item_id')
        item_type = data.get('item_type')
        
        if not item_id or not item_type:
            return jsonify({
                'success': False,
                'message': 'Item ID and type are required',
                'message_ar': 'معرف العنصر ونوعه مطلوبان'
            }), 400
        
        favorite = UserFavorite.query.filter_by(
            user_id=user_id,
            item_id=item_id,
            item_type=item_type
        ).first()
        
        if not favorite:
            return jsonify({
                'success': False,
                'message': 'Favorite not found',
                'message_ar': 'المفضلة غير موجودة'
            }), 404
        
        db.session.delete(favorite)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Item removed from favorites successfully',
            'message_ar': 'تم إزالة العنصر من المفضلة بنجاح'
        }), 200
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Remove favorite by item error: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'Failed to remove from favorites',
            'message_ar': 'فشل في إزالة من المفضلة'
        }), 500

@favorites_bp.route('/check', methods=['POST'])
@jwt_required()
def check_favorite():
    """Check if item is in favorites"""
    try:
        current_identity = get_jwt_identity()
        if current_identity['type'] != 'user':
            return jsonify({
                'success': False,
                'message': 'Only users can check favorites',
                'message_ar': 'المستخدمون فقط يمكنهم التحقق من المفضلة'
            }), 403
        
        user_id = current_identity['id']
        data = request.get_json()
        
        item_id = data.get('item_id')
        item_type = data.get('item_type')
        
        if not item_id or not item_type:
            return jsonify({
                'success': False,
                'message': 'Item ID and type are required',
                'message_ar': 'معرف العنصر ونوعه مطلوبان'
            }), 400
        
        favorite = UserFavorite.query.filter_by(
            user_id=user_id,
            item_id=item_id,
            item_type=item_type
        ).first()
        
        return jsonify({
            'success': True,
            'data': {
                'is_favorite': favorite is not None,
                'favorite_id': favorite.id if favorite else None
            }
        }), 200
        
    except Exception as e:
        current_app.logger.error(f"Check favorite error: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'Failed to check favorite status',
            'message_ar': 'فشل في التحقق من حالة المفضلة'
        }), 500

@favorites_bp.route('/toggle', methods=['POST'])
@jwt_required()
def toggle_favorite():
    """Toggle favorite status (add if not exists, remove if exists)"""
    try:
        current_identity = get_jwt_identity()
        if current_identity['type'] != 'user':
            return jsonify({
                'success': False,
                'message': 'Only users can toggle favorites',
                'message_ar': 'المستخدمون فقط يمكنهم تبديل المفضلة'
            }), 403
        
        user_id = current_identity['id']
        data = request.get_json()
        
        item_id = data.get('item_id')
        item_type = data.get('item_type')
        
        if not item_id or not item_type:
            return jsonify({
                'success': False,
                'message': 'Item ID and type are required',
                'message_ar': 'معرف العنصر ونوعه مطلوبان'
            }), 400
        
        if item_type not in ['product', 'pharmacy']:
            return jsonify({
                'success': False,
                'message': 'Invalid item type',
                'message_ar': 'نوع العنصر غير صحيح'
            }), 400
        
        # Check if already in favorites
        existing_favorite = UserFavorite.query.filter_by(
            user_id=user_id,
            item_id=item_id,
            item_type=item_type
        ).first()
        
        if existing_favorite:
            # Remove from favorites
            db.session.delete(existing_favorite)
            db.session.commit()
            
            return jsonify({
                'success': True,
                'message': 'Item removed from favorites',
                'message_ar': 'تم إزالة العنصر من المفضلة',
                'data': {
                    'is_favorite': False,
                    'action': 'removed'
                }
            }), 200
        else:
            # Check if item exists
            if item_type == 'product':
                item = Product.query.get(item_id)
                if not item or not item.is_active:
                    return jsonify({
                        'success': False,
                        'message': 'Product not found',
                        'message_ar': 'المنتج غير موجود'
                    }), 404
            elif item_type == 'pharmacy':
                item = Pharmacy.query.get(item_id)
                if not item or item.account_status != 'active':
                    return jsonify({
                        'success': False,
                        'message': 'Pharmacy not found',
                        'message_ar': 'الصيدلية غير موجودة'
                    }), 404
            
            # Add to favorites
            favorite = UserFavorite(
                user_id=user_id,
                item_id=item_id,
                item_type=item_type,
                notes=data.get('notes'),
                notes_ar=data.get('notes_ar')
            )
            
            db.session.add(favorite)
            db.session.commit()
            
            return jsonify({
                'success': True,
                'message': 'Item added to favorites',
                'message_ar': 'تم إضافة العنصر إلى المفضلة',
                'data': {
                    'is_favorite': True,
                    'action': 'added',
                    'favorite_id': favorite.id
                }
            }), 200
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Toggle favorite error: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'Failed to toggle favorite',
            'message_ar': 'فشل في تبديل المفضلة'
        }), 500

@favorites_bp.route('/clear', methods=['DELETE'])
@jwt_required()
def clear_favorites():
    """Clear all favorites for current user"""
    try:
        current_identity = get_jwt_identity()
        if current_identity['type'] != 'user':
            return jsonify({
                'success': False,
                'message': 'Only users can clear favorites',
                'message_ar': 'المستخدمون فقط يمكنهم مسح المفضلة'
            }), 403
        
        user_id = current_identity['id']
        item_type = request.args.get('type')  # Optional: clear only specific type
        
        query = UserFavorite.query.filter_by(user_id=user_id)
        
        if item_type:
            query = query.filter_by(item_type=item_type)
        
        favorites = query.all()
        
        for favorite in favorites:
            db.session.delete(favorite)
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': f'{len(favorites)} favorites cleared',
            'message_ar': f'تم مسح {len(favorites)} مفضلة'
        }), 200
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Clear favorites error: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'Failed to clear favorites',
            'message_ar': 'فشل في مسح المفضلة'
        }), 500

@favorites_bp.route('/stats', methods=['GET'])
@jwt_required()
def get_favorites_stats():
    """Get favorites statistics for current user"""
    try:
        current_identity = get_jwt_identity()
        if current_identity['type'] != 'user':
            return jsonify({
                'success': False,
                'message': 'Only users can view favorites stats',
                'message_ar': 'المستخدمون فقط يمكنهم عرض إحصائيات المفضلة'
            }), 403
        
        user_id = current_identity['id']
        
        # Get counts by type
        total_favorites = UserFavorite.query.filter_by(user_id=user_id).count()
        product_favorites = UserFavorite.query.filter_by(user_id=user_id, item_type='product').count()
        pharmacy_favorites = UserFavorite.query.filter_by(user_id=user_id, item_type='pharmacy').count()
        
        return jsonify({
            'success': True,
            'data': {
                'total_favorites': total_favorites,
                'product_favorites': product_favorites,
                'pharmacy_favorites': pharmacy_favorites
            }
        }), 200
        
    except Exception as e:
        current_app.logger.error(f"Get favorites stats error: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'Failed to fetch favorites statistics',
            'message_ar': 'فشل في جلب إحصائيات المفضلة'
        }), 500

