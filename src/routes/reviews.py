from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity
from datetime import datetime

from src.models.user import db
from src.models.review import Review
from src.models.product import Product
from src.models.pharmacy import Pharmacy
from src.models.order import Order
from src.services.auth_service import AuthService

reviews_bp = Blueprint('reviews', __name__)

@reviews_bp.route('', methods=['GET'])
def get_reviews():
    """Get reviews for product or pharmacy"""
    try:
        # Get query parameters
        product_id = request.args.get('product_id', type=int)
        pharmacy_id = request.args.get('pharmacy_id', type=int)
        page = request.args.get('page', 1, type=int)
        per_page = min(request.args.get('per_page', 20, type=int), 100)
        language = request.args.get('language', 'ar')
        sort_by = request.args.get('sort_by', 'newest')  # newest, oldest, rating_high, rating_low
        
        if not product_id and not pharmacy_id:
            return jsonify({
                'success': False,
                'message': 'Product ID or Pharmacy ID is required',
                'message_ar': 'معرف المنتج أو معرف الصيدلية مطلوب'
            }), 400
        
        # Build query
        query = Review.query.filter_by(is_active=True)
        
        if product_id:
            query = query.filter_by(product_id=product_id)
        if pharmacy_id:
            query = query.filter_by(pharmacy_id=pharmacy_id)
        
        # Apply sorting
        if sort_by == 'oldest':
            query = query.order_by(Review.created_at.asc())
        elif sort_by == 'rating_high':
            query = query.order_by(Review.rating.desc(), Review.created_at.desc())
        elif sort_by == 'rating_low':
            query = query.order_by(Review.rating.asc(), Review.created_at.desc())
        else:  # newest (default)
            query = query.order_by(Review.created_at.desc())
        
        # Paginate
        pagination = query.paginate(
            page=page,
            per_page=per_page,
            error_out=False
        )
        
        reviews = [review.to_dict(language=language) for review in pagination.items]
        
        # Calculate statistics
        if product_id:
            stats = Review.get_product_stats(product_id)
        else:
            stats = Review.get_pharmacy_stats(pharmacy_id)
        
        return jsonify({
            'success': True,
            'data': {
                'items': reviews,
                'page': page,
                'pages': pagination.pages,
                'per_page': per_page,
                'total': pagination.total,
                'has_next': pagination.has_next,
                'has_prev': pagination.has_prev,
                'stats': stats
            }
        }), 200
        
    except Exception as e:
        current_app.logger.error(f"Get reviews error: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'Failed to fetch reviews',
            'message_ar': 'فشل في جلب التقييمات'
        }), 500

@reviews_bp.route('', methods=['POST'])
@jwt_required()
def create_review():
    """Create new review (users only)"""
    try:
        current_identity = get_jwt_identity()
        if current_identity['type'] != 'user':
            return jsonify({
                'success': False,
                'message': 'Only users can create reviews',
                'message_ar': 'المستخدمون فقط يمكنهم إنشاء التقييمات'
            }), 403
        
        user_id = current_identity['id']
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['rating']
        for field in required_fields:
            if not data.get(field):
                return jsonify({
                    'success': False,
                    'message': f'{field} is required',
                    'message_ar': f'{field} مطلوب'
                }), 400
        
        product_id = data.get('product_id')
        pharmacy_id = data.get('pharmacy_id')
        order_id = data.get('order_id')
        
        if not product_id and not pharmacy_id:
            return jsonify({
                'success': False,
                'message': 'Product ID or Pharmacy ID is required',
                'message_ar': 'معرف المنتج أو معرف الصيدلية مطلوب'
            }), 400
        
        # Validate rating
        rating = data['rating']
        if not isinstance(rating, (int, float)) or rating < 1 or rating > 5:
            return jsonify({
                'success': False,
                'message': 'Rating must be between 1 and 5',
                'message_ar': 'التقييم يجب أن يكون بين 1 و 5'
            }), 400
        
        # Check if user has already reviewed this product/pharmacy
        existing_review = Review.query.filter_by(
            user_id=user_id,
            product_id=product_id,
            pharmacy_id=pharmacy_id
        ).first()
        
        if existing_review:
            return jsonify({
                'success': False,
                'message': 'You have already reviewed this item',
                'message_ar': 'لقد قمت بتقييم هذا العنصر بالفعل'
            }), 409
        
        # If order_id provided, verify user owns the order
        if order_id:
            order = Order.query.filter_by(id=order_id, user_id=user_id).first()
            if not order:
                return jsonify({
                    'success': False,
                    'message': 'Order not found',
                    'message_ar': 'الطلب غير موجود'
                }), 404
        
        # Create review
        review = Review(
            user_id=user_id,
            product_id=product_id,
            pharmacy_id=pharmacy_id,
            order_id=order_id,
            rating=rating,
            title=data.get('title'),
            title_ar=data.get('title_ar'),
            comment=data.get('comment'),
            comment_ar=data.get('comment_ar'),
            pros=data.get('pros'),
            pros_ar=data.get('pros_ar'),
            cons=data.get('cons'),
            cons_ar=data.get('cons_ar'),
            would_recommend=data.get('would_recommend', True),
            delivery_rating=data.get('delivery_rating'),
            service_rating=data.get('service_rating'),
            value_rating=data.get('value_rating')
        )
        
        db.session.add(review)
        db.session.commit()
        
        # Update product/pharmacy rating
        if product_id:
            product = Product.query.get(product_id)
            if product:
                product.update_rating()
        
        if pharmacy_id:
            pharmacy = Pharmacy.query.get(pharmacy_id)
            if pharmacy:
                pharmacy.update_rating()
        
        return jsonify({
            'success': True,
            'message': 'Review created successfully',
            'message_ar': 'تم إنشاء التقييم بنجاح',
            'data': review.to_dict()
        }), 201
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Create review error: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'Failed to create review',
            'message_ar': 'فشل في إنشاء التقييم'
        }), 500

@reviews_bp.route('/<review_id>', methods=['GET'])
def get_review(review_id):
    """Get single review"""
    try:
        language = request.args.get('language', 'ar')
        
        review = Review.query.filter_by(id=review_id, is_active=True).first()
        if not review:
            return jsonify({
                'success': False,
                'message': 'Review not found',
                'message_ar': 'التقييم غير موجود'
            }), 404
        
        return jsonify({
            'success': True,
            'data': review.to_dict(language=language)
        }), 200
        
    except Exception as e:
        current_app.logger.error(f"Get review error: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'Failed to fetch review',
            'message_ar': 'فشل في جلب التقييم'
        }), 500

@reviews_bp.route('/<review_id>', methods=['PUT'])
@jwt_required()
def update_review(review_id):
    """Update review (author only)"""
    try:
        current_identity = get_jwt_identity()
        if current_identity['type'] != 'user':
            return jsonify({
                'success': False,
                'message': 'Only users can update reviews',
                'message_ar': 'المستخدمون فقط يمكنهم تحديث التقييمات'
            }), 403
        
        user_id = current_identity['id']
        
        review = Review.query.filter_by(id=review_id, user_id=user_id).first()
        if not review:
            return jsonify({
                'success': False,
                'message': 'Review not found',
                'message_ar': 'التقييم غير موجود'
            }), 404
        
        data = request.get_json()
        
        # Update allowed fields
        allowed_fields = [
            'rating', 'title', 'title_ar', 'comment', 'comment_ar',
            'pros', 'pros_ar', 'cons', 'cons_ar', 'would_recommend',
            'delivery_rating', 'service_rating', 'value_rating'
        ]
        
        for field in allowed_fields:
            if field in data:
                if field == 'rating' and data[field]:
                    # Validate rating
                    rating = data[field]
                    if not isinstance(rating, (int, float)) or rating < 1 or rating > 5:
                        return jsonify({
                            'success': False,
                            'message': 'Rating must be between 1 and 5',
                            'message_ar': 'التقييم يجب أن يكون بين 1 و 5'
                        }), 400
                
                setattr(review, field, data[field])
        
        review.updated_at = datetime.utcnow()
        db.session.commit()
        
        # Update product/pharmacy rating
        if review.product_id:
            product = Product.query.get(review.product_id)
            if product:
                product.update_rating()
        
        if review.pharmacy_id:
            pharmacy = Pharmacy.query.get(review.pharmacy_id)
            if pharmacy:
                pharmacy.update_rating()
        
        return jsonify({
            'success': True,
            'message': 'Review updated successfully',
            'message_ar': 'تم تحديث التقييم بنجاح',
            'data': review.to_dict()
        }), 200
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Update review error: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'Failed to update review',
            'message_ar': 'فشل في تحديث التقييم'
        }), 500

@reviews_bp.route('/<review_id>', methods=['DELETE'])
@jwt_required()
def delete_review(review_id):
    """Delete review (author only)"""
    try:
        current_identity = get_jwt_identity()
        if current_identity['type'] != 'user':
            return jsonify({
                'success': False,
                'message': 'Only users can delete reviews',
                'message_ar': 'المستخدمون فقط يمكنهم حذف التقييمات'
            }), 403
        
        user_id = current_identity['id']
        
        review = Review.query.filter_by(id=review_id, user_id=user_id).first()
        if not review:
            return jsonify({
                'success': False,
                'message': 'Review not found',
                'message_ar': 'التقييم غير موجود'
            }), 404
        
        # Soft delete
        review.is_active = False
        review.updated_at = datetime.utcnow()
        db.session.commit()
        
        # Update product/pharmacy rating
        if review.product_id:
            product = Product.query.get(review.product_id)
            if product:
                product.update_rating()
        
        if review.pharmacy_id:
            pharmacy = Pharmacy.query.get(review.pharmacy_id)
            if pharmacy:
                pharmacy.update_rating()
        
        return jsonify({
            'success': True,
            'message': 'Review deleted successfully',
            'message_ar': 'تم حذف التقييم بنجاح'
        }), 200
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Delete review error: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'Failed to delete review',
            'message_ar': 'فشل في حذف التقييم'
        }), 500

@reviews_bp.route('/<review_id>/helpful', methods=['POST'])
@jwt_required()
def mark_helpful(review_id):
    """Mark review as helpful/not helpful"""
    try:
        current_identity = get_jwt_identity()
        user_id = current_identity['id']
        user_type = current_identity['type']
        
        review = Review.query.filter_by(id=review_id, is_active=True).first()
        if not review:
            return jsonify({
                'success': False,
                'message': 'Review not found',
                'message_ar': 'التقييم غير موجود'
            }), 404
        
        data = request.get_json()
        is_helpful = data.get('is_helpful', True)
        
        # Update helpful count
        if is_helpful:
            review.helpful_count += 1
        else:
            review.not_helpful_count += 1
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Thank you for your feedback',
            'message_ar': 'شكراً لك على ملاحظاتك',
            'data': {
                'helpful_count': review.helpful_count,
                'not_helpful_count': review.not_helpful_count
            }
        }), 200
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Mark helpful error: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'Failed to update feedback',
            'message_ar': 'فشل في تحديث الملاحظات'
        }), 500

@reviews_bp.route('/my-reviews', methods=['GET'])
@jwt_required()
def get_my_reviews():
    """Get current user's reviews"""
    try:
        current_identity = get_jwt_identity()
        if current_identity['type'] != 'user':
            return jsonify({
                'success': False,
                'message': 'Only users can view their reviews',
                'message_ar': 'المستخدمون فقط يمكنهم عرض تقييماتهم'
            }), 403
        
        user_id = current_identity['id']
        
        # Get query parameters
        page = request.args.get('page', 1, type=int)
        per_page = min(request.args.get('per_page', 20, type=int), 100)
        language = request.args.get('language', 'ar')
        
        # Get user's reviews
        query = Review.query.filter_by(user_id=user_id).order_by(Review.created_at.desc())
        
        # Paginate
        pagination = query.paginate(
            page=page,
            per_page=per_page,
            error_out=False
        )
        
        reviews = [review.to_dict(language=language) for review in pagination.items]
        
        return jsonify({
            'success': True,
            'data': {
                'items': reviews,
                'page': page,
                'pages': pagination.pages,
                'per_page': per_page,
                'total': pagination.total,
                'has_next': pagination.has_next,
                'has_prev': pagination.has_prev
            }
        }), 200
        
    except Exception as e:
        current_app.logger.error(f"Get my reviews error: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'Failed to fetch reviews',
            'message_ar': 'فشل في جلب التقييمات'
        }), 500

@reviews_bp.route('/stats', methods=['GET'])
def get_review_stats():
    """Get review statistics for product or pharmacy"""
    try:
        product_id = request.args.get('product_id', type=int)
        pharmacy_id = request.args.get('pharmacy_id', type=int)
        
        if not product_id and not pharmacy_id:
            return jsonify({
                'success': False,
                'message': 'Product ID or Pharmacy ID is required',
                'message_ar': 'معرف المنتج أو معرف الصيدلية مطلوب'
            }), 400
        
        if product_id:
            stats = Review.get_product_stats(product_id)
        else:
            stats = Review.get_pharmacy_stats(pharmacy_id)
        
        return jsonify({
            'success': True,
            'data': stats
        }), 200
        
    except Exception as e:
        current_app.logger.error(f"Get review stats error: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'Failed to fetch review statistics',
            'message_ar': 'فشل في جلب إحصائيات التقييمات'
        }), 500

