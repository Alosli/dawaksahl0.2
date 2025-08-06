from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity
from datetime import datetime

from src.models.user import db
from src.models.order import Order, OrderItem
from src.models.product import Product
from src.models.notification import Notification
from src.services.auth_service import AuthService

orders_bp = Blueprint('orders', __name__)

@orders_bp.route('', methods=['GET'])
@jwt_required()
def get_orders():
    """Get orders for current user/pharmacy"""
    try:
        current_identity = get_jwt_identity()
        user_id = current_identity['id']
        user_type = current_identity['type']
        
        # Get query parameters
        page = request.args.get('page', 1, type=int)
        per_page = min(request.args.get('per_page', 20, type=int), 100)
        status = request.args.get('status')
        language = request.args.get('language', 'ar')
        
        # Build query based on user type
        if user_type == 'user':
            query = Order.query.filter_by(user_id=user_id)
        elif user_type == 'pharmacy':
            query = Order.query.filter_by(pharmacy_id=user_id)
        else:
            return jsonify({
                'success': False,
                'message': 'Invalid user type',
                'message_ar': 'نوع المستخدم غير صحيح'
            }), 400
        
        # Apply status filter
        if status:
            query = query.filter_by(status=status)
        
        # Order by creation date (newest first)
        query = query.order_by(Order.created_at.desc())
        
        # Paginate
        pagination = query.paginate(
            page=page,
            per_page=per_page,
            error_out=False
        )
        
        orders = [order.to_dict(language=language) for order in pagination.items]
        
        return jsonify({
            'success': True,
            'data': {
                'items': orders,
                'page': page,
                'pages': pagination.pages,
                'per_page': per_page,
                'total': pagination.total,
                'has_next': pagination.has_next,
                'has_prev': pagination.has_prev
            }
        }), 200
        
    except Exception as e:
        current_app.logger.error(f"Get orders error: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'Failed to fetch orders',
            'message_ar': 'فشل في جلب الطلبات'
        }), 500

@orders_bp.route('/<order_id>', methods=['GET'])
@jwt_required()
def get_order(order_id):
    """Get single order details"""
    try:
        current_identity = get_jwt_identity()
        user_id = current_identity['id']
        user_type = current_identity['type']
        language = request.args.get('language', 'ar')
        
        order = Order.query.get(order_id)
        if not order:
            return jsonify({
                'success': False,
                'message': 'Order not found',
                'message_ar': 'الطلب غير موجود'
            }), 404
        
        # Check access permissions
        if user_type == 'user' and order.user_id != user_id:
            return jsonify({
                'success': False,
                'message': 'Access denied',
                'message_ar': 'الوصول مرفوض'
            }), 403
        elif user_type == 'pharmacy' and order.pharmacy_id != user_id:
            return jsonify({
                'success': False,
                'message': 'Access denied',
                'message_ar': 'الوصول مرفوض'
            }), 403
        
        return jsonify({
            'success': True,
            'data': order.to_dict(language=language, include_items=True)
        }), 200
        
    except Exception as e:
        current_app.logger.error(f"Get order error: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'Failed to fetch order',
            'message_ar': 'فشل في جلب الطلب'
        }), 500

@orders_bp.route('', methods=['POST'])
@jwt_required()
def create_order():
    """Create new order (users only)"""
    try:
        current_identity = get_jwt_identity()
        if current_identity['type'] != 'user':
            return jsonify({
                'success': False,
                'message': 'Only users can create orders',
                'message_ar': 'المستخدمون فقط يمكنهم إنشاء الطلبات'
            }), 403
        
        user_id = current_identity['id']
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['pharmacy_id', 'items', 'delivery_method']
        for field in required_fields:
            if not data.get(field):
                return jsonify({
                    'success': False,
                    'message': f'{field} is required',
                    'message_ar': f'{field} مطلوب'
                }), 400
        
        if not data['items']:
            return jsonify({
                'success': False,
                'message': 'Order must contain at least one item',
                'message_ar': 'يجب أن يحتوي الطلب على عنصر واحد على الأقل'
            }), 400
        
        # Create order
        order = Order(
            user_id=user_id,
            pharmacy_id=data['pharmacy_id'],
            delivery_method=data['delivery_method'],
            order_type=data.get('order_type', 'regular'),
            payment_method=data.get('payment_method', 'cash'),
            delivery_address_line1=data.get('delivery_address_line1'),
            delivery_address_line2=data.get('delivery_address_line2'),
            delivery_city=data.get('delivery_city'),
            delivery_state=data.get('delivery_state'),
            delivery_postal_code=data.get('delivery_postal_code'),
            delivery_latitude=data.get('delivery_latitude'),
            delivery_longitude=data.get('delivery_longitude'),
            delivery_notes=data.get('delivery_notes'),
            delivery_notes_ar=data.get('delivery_notes_ar'),
            contact_name=data.get('contact_name'),
            contact_phone=data.get('contact_phone'),
            special_instructions=data.get('special_instructions'),
            special_instructions_ar=data.get('special_instructions_ar'),
            prescription_id=data.get('prescription_id'),
            prescription_image_url=data.get('prescription_image_url'),
            preferred_delivery_time=datetime.fromisoformat(data['preferred_delivery_time']) if data.get('preferred_delivery_time') else None
        )
        
        db.session.add(order)
        db.session.flush()  # Get order ID
        
        # Add order items
        for item_data in data['items']:
            product = Product.query.get(item_data['product_id'])
            if not product:
                db.session.rollback()
                return jsonify({
                    'success': False,
                    'message': f'Product {item_data["product_id"]} not found',
                    'message_ar': f'المنتج {item_data["product_id"]} غير موجود'
                }), 400
            
            if product.pharmacy_id != data['pharmacy_id']:
                db.session.rollback()
                return jsonify({
                    'success': False,
                    'message': f'Product {product.product_name} does not belong to this pharmacy',
                    'message_ar': f'المنتج {product.product_name} لا ينتمي لهذه الصيدلية'
                }), 400
            
            # Check stock availability
            if product.current_stock < item_data['quantity']:
                db.session.rollback()
                return jsonify({
                    'success': False,
                    'message': f'Insufficient stock for {product.product_name}',
                    'message_ar': f'مخزون غير كافي للمنتج {product.product_name}'
                }), 400
            
            order_item = OrderItem(
                order_id=order.id,
                product_id=product.id,
                quantity=item_data['quantity'],
                unit_price=product.calculate_final_price(),
                total_price=item_data['quantity'] * product.calculate_final_price(),
                prescription_quantity=item_data.get('prescription_quantity'),
                dosage_instructions=item_data.get('dosage_instructions'),
                dosage_instructions_ar=item_data.get('dosage_instructions_ar')
            )
            
            db.session.add(order_item)
        
        # Calculate totals
        order.calculate_totals()
        
        # Set delivery fee if applicable
        if order.delivery_method == 'delivery':
            order.delivery_fee = data.get('delivery_fee', 0.0)
            order.calculate_totals()
        
        db.session.commit()
        
        # Create notification for pharmacy
        notification = Notification.create_order_notification(
            user_id=None,  # For pharmacy
            order_id=order.id,
            status='new_order'
        )
        notification.pharmacy_id = order.pharmacy_id
        notification.title = 'New Order Received'
        notification.title_ar = 'طلب جديد'
        notification.message = f'New order #{order.order_number} received'
        notification.message_ar = f'تم استلام طلب جديد #{order.order_number}'
        db.session.add(notification)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Order created successfully',
            'message_ar': 'تم إنشاء الطلب بنجاح',
            'data': order.to_dict(include_items=True)
        }), 201
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Create order error: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'Failed to create order',
            'message_ar': 'فشل في إنشاء الطلب'
        }), 500

@orders_bp.route('/<order_id>/status', methods=['PUT'])
@jwt_required()
def update_order_status(order_id):
    """Update order status (pharmacy only)"""
    try:
        current_identity = get_jwt_identity()
        if current_identity['type'] != 'pharmacy':
            return jsonify({
                'success': False,
                'message': 'Only pharmacies can update order status',
                'message_ar': 'الصيدليات فقط يمكنها تحديث حالة الطلب'
            }), 403
        
        pharmacy_id = current_identity['id']
        data = request.get_json()
        
        new_status = data.get('status')
        notes = data.get('notes')
        
        if not new_status:
            return jsonify({
                'success': False,
                'message': 'Status is required',
                'message_ar': 'الحالة مطلوبة'
            }), 400
        
        order = Order.query.filter_by(id=order_id, pharmacy_id=pharmacy_id).first()
        if not order:
            return jsonify({
                'success': False,
                'message': 'Order not found',
                'message_ar': 'الطلب غير موجود'
            }), 404
        
        # Validate status transition
        valid_statuses = ['pending', 'confirmed', 'preparing', 'ready', 'out_for_delivery', 'delivered', 'cancelled']
        if new_status not in valid_statuses:
            return jsonify({
                'success': False,
                'message': 'Invalid status',
                'message_ar': 'حالة غير صحيحة'
            }), 400
        
        # Update stock when order is confirmed
        if new_status == 'confirmed' and order.status == 'pending':
            for item in order.items:
                product = item.product
                if product.current_stock >= item.quantity:
                    product.update_stock(item.quantity, 'subtract')
                else:
                    return jsonify({
                        'success': False,
                        'message': f'Insufficient stock for {product.product_name}',
                        'message_ar': f'مخزون غير كافي للمنتج {product.product_name}'
                    }), 400
        
        # Restore stock if order is cancelled
        if new_status == 'cancelled' and order.status in ['confirmed', 'preparing', 'ready']:
            for item in order.items:
                product = item.product
                product.update_stock(item.quantity, 'add')
        
        # Update order status
        order.update_status(new_status, notes)
        db.session.commit()
        
        # Create notification for user
        notification = Notification.create_order_notification(
            user_id=order.user_id,
            order_id=order.id,
            status=new_status
        )
        db.session.add(notification)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Order status updated successfully',
            'message_ar': 'تم تحديث حالة الطلب بنجاح',
            'data': order.to_dict()
        }), 200
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Update order status error: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'Failed to update order status',
            'message_ar': 'فشل في تحديث حالة الطلب'
        }), 500

@orders_bp.route('/<order_id>/cancel', methods=['PUT'])
@jwt_required()
def cancel_order(order_id):
    """Cancel order (users only)"""
    try:
        current_identity = get_jwt_identity()
        if current_identity['type'] != 'user':
            return jsonify({
                'success': False,
                'message': 'Only users can cancel orders',
                'message_ar': 'المستخدمون فقط يمكنهم إلغاء الطلبات'
            }), 403
        
        user_id = current_identity['id']
        data = request.get_json()
        reason = data.get('reason', 'Cancelled by user')
        
        order = Order.query.filter_by(id=order_id, user_id=user_id).first()
        if not order:
            return jsonify({
                'success': False,
                'message': 'Order not found',
                'message_ar': 'الطلب غير موجود'
            }), 404
        
        if not order.can_be_cancelled():
            return jsonify({
                'success': False,
                'message': 'Order cannot be cancelled at this stage',
                'message_ar': 'لا يمكن إلغاء الطلب في هذه المرحلة'
            }), 400
        
        # Restore stock if order was confirmed
        if order.status in ['confirmed', 'preparing', 'ready']:
            for item in order.items:
                product = item.product
                product.update_stock(item.quantity, 'add')
        
        # Update order status
        order.update_status('cancelled', reason)
        db.session.commit()
        
        # Create notification for pharmacy
        notification = Notification(
            pharmacy_id=order.pharmacy_id,
            notification_type='order_status',
            category='warning',
            title='Order Cancelled',
            title_ar='تم إلغاء الطلب',
            message=f'Order #{order.order_number} was cancelled by customer',
            message_ar=f'تم إلغاء الطلب #{order.order_number} من قبل العميل',
            related_order_id=order.id
        )
        db.session.add(notification)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Order cancelled successfully',
            'message_ar': 'تم إلغاء الطلب بنجاح',
            'data': order.to_dict()
        }), 200
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Cancel order error: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'Failed to cancel order',
            'message_ar': 'فشل في إلغاء الطلب'
        }), 500

@orders_bp.route('/stats', methods=['GET'])
@jwt_required()
def get_order_stats():
    """Get order statistics for pharmacy"""
    try:
        current_identity = get_jwt_identity()
        if current_identity['type'] != 'pharmacy':
            return jsonify({
                'success': False,
                'message': 'Only pharmacies can view order statistics',
                'message_ar': 'الصيدليات فقط يمكنها عرض إحصائيات الطلبات'
            }), 403
        
        pharmacy_id = current_identity['id']
        
        # Get basic stats
        total_orders = Order.query.filter_by(pharmacy_id=pharmacy_id).count()
        pending_orders = Order.query.filter_by(pharmacy_id=pharmacy_id, status='pending').count()
        confirmed_orders = Order.query.filter_by(pharmacy_id=pharmacy_id, status='confirmed').count()
        delivered_orders = Order.query.filter_by(pharmacy_id=pharmacy_id, status='delivered').count()
        cancelled_orders = Order.query.filter_by(pharmacy_id=pharmacy_id, status='cancelled').count()
        
        # Get revenue stats
        from sqlalchemy import func
        revenue_result = db.session.query(
            func.sum(Order.total_amount)
        ).filter_by(
            pharmacy_id=pharmacy_id,
            status='delivered'
        ).scalar()
        
        total_revenue = float(revenue_result) if revenue_result else 0.0
        
        # Get today's stats
        today = datetime.now().date()
        today_orders = Order.query.filter(
            Order.pharmacy_id == pharmacy_id,
            func.date(Order.created_at) == today
        ).count()
        
        return jsonify({
            'success': True,
            'data': {
                'total_orders': total_orders,
                'pending_orders': pending_orders,
                'confirmed_orders': confirmed_orders,
                'delivered_orders': delivered_orders,
                'cancelled_orders': cancelled_orders,
                'total_revenue': total_revenue,
                'today_orders': today_orders
            }
        }), 200
        
    except Exception as e:
        current_app.logger.error(f"Get order stats error: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'Failed to fetch order statistics',
            'message_ar': 'فشل في جلب إحصائيات الطلبات'
        }), 500

