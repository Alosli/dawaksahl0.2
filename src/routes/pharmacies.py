from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity
from werkzeug.security import check_password_hash, generate_password_hash
from datetime import datetime

from src.models.user import db
from src.models.pharmacy import Pharmacy
from src.services.auth_service import AuthService

pharmacies_bp = Blueprint('pharmacies', __name__)

@pharmacies_bp.route('', methods=['GET'])
def get_pharmacies():
    """Get list of pharmacies (public endpoint)"""
    try:
        # Get query parameters
        page = request.args.get('page', 1, type=int)
        per_page = min(request.args.get('per_page', 20, type=int), 100)
        language = request.args.get('language', 'ar')
        city = request.args.get('city')
        is_24_hours = request.args.get('is_24_hours', type=bool)
        has_delivery = request.args.get('has_delivery', type=bool)
        search = request.args.get('search', '').strip()
        latitude = request.args.get('latitude', type=float)
        longitude = request.args.get('longitude', type=float)
        radius = request.args.get('radius', 10, type=float)  # km
        
        # Build query
        query = Pharmacy.query.filter_by(account_status='active')
        
        # Apply filters
        if city:
            query = query.filter(Pharmacy.city.ilike(f'%{city}%'))
        
        if is_24_hours is not None:
            query = query.filter_by(is_24_hours=is_24_hours)
        
        if has_delivery is not None:
            query = query.filter_by(has_delivery=has_delivery)
        
        if search:
            search_term = f'%{search}%'
            query = query.filter(
                db.or_(
                    Pharmacy.pharmacy_name.ilike(search_term),
                    Pharmacy.pharmacy_name_ar.ilike(search_term),
                    Pharmacy.description.ilike(search_term),
                    Pharmacy.description_ar.ilike(search_term),
                    Pharmacy.specializations.ilike(search_term),
                    Pharmacy.specializations_ar.ilike(search_term)
                )
            )
        
        # Location-based filtering
        if latitude and longitude:
            # TODO: Implement proper geospatial query
            # For now, filter by approximate distance
            lat_range = radius / 111.0  # Rough conversion
            lng_range = radius / (111.0 * abs(latitude))
            
            query = query.filter(
                Pharmacy.latitude.between(latitude - lat_range, latitude + lat_range),
                Pharmacy.longitude.between(longitude - lng_range, longitude + lng_range)
            )
        
        # Order by rating and distance
        query = query.order_by(Pharmacy.average_rating.desc(), Pharmacy.created_at.desc())
        
        # Paginate
        pagination = query.paginate(
            page=page,
            per_page=per_page,
            error_out=False
        )
        
        pharmacies = [pharmacy.to_dict(language=language) for pharmacy in pagination.items]
        
        return jsonify({
            'success': True,
            'data': {
                'items': pharmacies,
                'page': page,
                'pages': pagination.pages,
                'per_page': per_page,
                'total': pagination.total,
                'has_next': pagination.has_next,
                'has_prev': pagination.has_prev
            }
        }), 200
        
    except Exception as e:
        current_app.logger.error(f"Get pharmacies error: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'Failed to fetch pharmacies',
            'message_ar': 'فشل في جلب الصيدليات'
        }), 500

@pharmacies_bp.route('/<pharmacy_id>', methods=['GET'])
def get_pharmacy(pharmacy_id):
    """Get single pharmacy details (public endpoint)"""
    try:
        language = request.args.get('language', 'ar')
        
        pharmacy = Pharmacy.query.filter_by(
            id=pharmacy_id,
            account_status='active'
        ).first()
        
        if not pharmacy:
            return jsonify({
                'success': False,
                'message': 'Pharmacy not found',
                'message_ar': 'الصيدلية غير موجودة'
            }), 404
        
        return jsonify({
            'success': True,
            'data': pharmacy.to_dict(language=language, include_sensitive=False)
        }), 200
        
    except Exception as e:
        current_app.logger.error(f"Get pharmacy error: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'Failed to fetch pharmacy',
            'message_ar': 'فشل في جلب الصيدلية'
        }), 500

@pharmacies_bp.route('/profile', methods=['GET'])
@jwt_required()
def get_pharmacy_profile():
    """Get current pharmacy profile"""
    try:
        current_identity = get_jwt_identity()
        if current_identity['type'] != 'pharmacy':
            return jsonify({
                'success': False,
                'message': 'Only pharmacies can access this endpoint',
                'message_ar': 'الصيدليات فقط يمكنها الوصول لهذه النقطة'
            }), 403
        
        pharmacy_id = current_identity['id']
        language = request.args.get('language', 'ar')
        
        pharmacy = Pharmacy.query.get(pharmacy_id)
        if not pharmacy:
            return jsonify({
                'success': False,
                'message': 'Pharmacy not found',
                'message_ar': 'الصيدلية غير موجودة'
            }), 404
        
        return jsonify({
            'success': True,
            'data': pharmacy.to_dict(language=language, include_sensitive=True)
        }), 200
        
    except Exception as e:
        current_app.logger.error(f"Get pharmacy profile error: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'Failed to fetch profile',
            'message_ar': 'فشل في جلب الملف الشخصي'
        }), 500

@pharmacies_bp.route('/profile', methods=['PUT'])
@jwt_required()
def update_pharmacy_profile():
    """Update current pharmacy profile"""
    try:
        current_identity = get_jwt_identity()
        if current_identity['type'] != 'pharmacy':
            return jsonify({
                'success': False,
                'message': 'Only pharmacies can update profile',
                'message_ar': 'الصيدليات فقط يمكنها تحديث الملف الشخصي'
            }), 403
        
        pharmacy_id = current_identity['id']
        data = request.get_json()
        
        pharmacy = Pharmacy.query.get(pharmacy_id)
        if not pharmacy:
            return jsonify({
                'success': False,
                'message': 'Pharmacy not found',
                'message_ar': 'الصيدلية غير موجودة'
            }), 404
        
        # Update allowed fields
        allowed_fields = [
            'pharmacy_name', 'pharmacy_name_ar', 'description', 'description_ar',
            'phone_number', 'whatsapp_number', 'website_url', 'logo_url',
            'address_line1', 'address_line2', 'city', 'state', 'postal_code',
            'country', 'latitude', 'longitude', 'opening_hours', 'closing_hours',
            'is_24_hours', 'has_delivery', 'delivery_fee', 'minimum_order_amount',
            'delivery_radius', 'specializations', 'specializations_ar',
            'services_offered', 'services_offered_ar', 'accepts_insurance',
            'insurance_providers', 'payment_methods', 'social_media_links',
            'email_notifications', 'push_notifications'
        ]
        
        for field in allowed_fields:
            if field in data:
                setattr(pharmacy, field, data[field])
        
        pharmacy.updated_at = datetime.utcnow()
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Profile updated successfully',
            'message_ar': 'تم تحديث الملف الشخصي بنجاح',
            'data': pharmacy.to_dict()
        }), 200
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Update pharmacy profile error: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'Failed to update profile',
            'message_ar': 'فشل في تحديث الملف الشخصي'
        }), 500

@pharmacies_bp.route('/change-email', methods=['PUT'])
@jwt_required()
def change_pharmacy_email():
    """Change pharmacy email address"""
    try:
        current_identity = get_jwt_identity()
        if current_identity['type'] != 'pharmacy':
            return jsonify({
                'success': False,
                'message': 'Only pharmacies can change email',
                'message_ar': 'الصيدليات فقط يمكنها تغيير البريد الإلكتروني'
            }), 403
        
        pharmacy_id = current_identity['id']
        data = request.get_json()
        
        new_email = data.get('new_email', '').lower().strip()
        password = data.get('password')
        
        if not new_email or not password:
            return jsonify({
                'success': False,
                'message': 'New email and password are required',
                'message_ar': 'البريد الإلكتروني الجديد وكلمة المرور مطلوبان'
            }), 400
        
        pharmacy = Pharmacy.query.get(pharmacy_id)
        if not pharmacy:
            return jsonify({
                'success': False,
                'message': 'Pharmacy not found',
                'message_ar': 'الصيدلية غير موجودة'
            }), 404
        
        # Verify current password
        if not check_password_hash(pharmacy.password_hash, password):
            return jsonify({
                'success': False,
                'message': 'Current password is incorrect',
                'message_ar': 'كلمة المرور الحالية غير صحيحة'
            }), 400
        
        # Check if new email is already in use
        existing_pharmacy = Pharmacy.query.filter_by(email=new_email).first()
        if existing_pharmacy and existing_pharmacy.id != pharmacy_id:
            return jsonify({
                'success': False,
                'message': 'Email is already in use',
                'message_ar': 'البريد الإلكتروني مستخدم بالفعل'
            }), 409
        
        # Update email and require re-verification
        pharmacy.email = new_email
        pharmacy.is_email_verified = False
        pharmacy.email_verified_at = None
        pharmacy.updated_at = datetime.utcnow()
        
        # Generate new verification token
        import secrets
        from datetime import timedelta
        pharmacy.email_verification_token = secrets.token_urlsafe(32)
        pharmacy.email_verification_expires = datetime.utcnow() + timedelta(hours=24)
        
        db.session.commit()
        
        # Send verification email
        try:
            from src.services.email_service import EmailService
            EmailService.send_verification_email(pharmacy.email, pharmacy.email_verification_token, 'ar')
        except Exception as e:
            current_app.logger.error(f"Failed to send verification email: {str(e)}")
        
        return jsonify({
            'success': True,
            'message': 'Email updated successfully. Please verify your new email address.',
            'message_ar': 'تم تحديث البريد الإلكتروني بنجاح. يرجى تفعيل عنوان بريدك الإلكتروني الجديد.'
        }), 200
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Change pharmacy email error: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'Failed to change email',
            'message_ar': 'فشل في تغيير البريد الإلكتروني'
        }), 500

@pharmacies_bp.route('/upload-logo', methods=['POST'])
@jwt_required()
def upload_pharmacy_logo():
    """Upload pharmacy logo"""
    try:
        current_identity = get_jwt_identity()
        if current_identity['type'] != 'pharmacy':
            return jsonify({
                'success': False,
                'message': 'Only pharmacies can upload logo',
                'message_ar': 'الصيدليات فقط يمكنها رفع الشعار'
            }), 403
        
        pharmacy_id = current_identity['id']
        
        # Check if file is present
        if 'logo' not in request.files:
            return jsonify({
                'success': False,
                'message': 'No file uploaded',
                'message_ar': 'لم يتم رفع أي ملف'
            }), 400
        
        file = request.files['logo']
        
        if file.filename == '':
            return jsonify({
                'success': False,
                'message': 'No file selected',
                'message_ar': 'لم يتم اختيار أي ملف'
            }), 400
        
        # Validate file type
        allowed_extensions = {'png', 'jpg', 'jpeg', 'gif', 'webp', 'svg'}
        if not ('.' in file.filename and file.filename.rsplit('.', 1)[1].lower() in allowed_extensions):
            return jsonify({
                'success': False,
                'message': 'Invalid file type. Only images are allowed.',
                'message_ar': 'نوع الملف غير صحيح. الصور فقط مسموحة.'
            }), 400
        
        # TODO: Implement file upload to cloud storage
        logo_url = f"https://api.dawaksahl.com/uploads/logos/pharmacy_{pharmacy_id}_{datetime.now().timestamp()}.jpg"
        
        # Update pharmacy profile
        pharmacy = Pharmacy.query.get(pharmacy_id)
        if not pharmacy:
            return jsonify({
                'success': False,
                'message': 'Pharmacy not found',
                'message_ar': 'الصيدلية غير موجودة'
            }), 404
        
        pharmacy.logo_url = logo_url
        pharmacy.updated_at = datetime.utcnow()
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Logo uploaded successfully',
            'message_ar': 'تم رفع الشعار بنجاح',
            'data': {
                'logo_url': logo_url
            }
        }), 200
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Upload pharmacy logo error: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'Failed to upload logo',
            'message_ar': 'فشل في رفع الشعار'
        }), 500

@pharmacies_bp.route('/stats', methods=['GET'])
@jwt_required()
def get_pharmacy_stats():
    """Get pharmacy statistics"""
    try:
        current_identity = get_jwt_identity()
        if current_identity['type'] != 'pharmacy':
            return jsonify({
                'success': False,
                'message': 'Only pharmacies can view stats',
                'message_ar': 'الصيدليات فقط يمكنها عرض الإحصائيات'
            }), 403
        
        pharmacy_id = current_identity['id']
        
        # Get product stats
        from src.models.product import Product
        total_products = Product.query.filter_by(pharmacy_id=pharmacy_id, is_active=True).count()
        out_of_stock = Product.query.filter_by(pharmacy_id=pharmacy_id, is_active=True, stock_quantity=0).count()
        low_stock = Product.query.filter(
            Product.pharmacy_id == pharmacy_id,
            Product.is_active == True,
            Product.stock_quantity > 0,
            Product.stock_quantity <= Product.low_stock_threshold
        ).count()
        
        # Get order stats
        from src.models.order import Order
        total_orders = Order.query.filter_by(pharmacy_id=pharmacy_id).count()
        pending_orders = Order.query.filter_by(pharmacy_id=pharmacy_id, status='pending').count()
        completed_orders = Order.query.filter_by(pharmacy_id=pharmacy_id, status='delivered').count()
        
        # Get revenue stats
        from sqlalchemy import func
        total_revenue_result = db.session.query(
            func.sum(Order.total_amount)
        ).filter_by(
            pharmacy_id=pharmacy_id,
            status='delivered'
        ).scalar()
        
        total_revenue = float(total_revenue_result) if total_revenue_result else 0.0
        
        # Get review stats
        from src.models.review import Review
        total_reviews = Review.query.filter_by(pharmacy_id=pharmacy_id, is_active=True).count()
        
        return jsonify({
            'success': True,
            'data': {
                'products': {
                    'total': total_products,
                    'out_of_stock': out_of_stock,
                    'low_stock': low_stock
                },
                'orders': {
                    'total': total_orders,
                    'pending': pending_orders,
                    'completed': completed_orders
                },
                'total_revenue': total_revenue,
                'total_reviews': total_reviews
            }
        }), 200
        
    except Exception as e:
        current_app.logger.error(f"Get pharmacy stats error: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'Failed to fetch pharmacy statistics',
            'message_ar': 'فشل في جلب إحصائيات الصيدلية'
        }), 500

@pharmacies_bp.route('/nearby', methods=['GET'])
def get_nearby_pharmacies():
    """Get nearby pharmacies based on location"""
    try:
        latitude = request.args.get('latitude', type=float)
        longitude = request.args.get('longitude', type=float)
        radius = request.args.get('radius', 10, type=float)  # km
        language = request.args.get('language', 'ar')
        limit = min(request.args.get('limit', 10, type=int), 50)
        
        if not latitude or not longitude:
            return jsonify({
                'success': False,
                'message': 'Latitude and longitude are required',
                'message_ar': 'خط العرض وخط الطول مطلوبان'
            }), 400
        
        # TODO: Implement proper geospatial query with PostGIS
        # For now, use simple distance calculation
        lat_range = radius / 111.0  # Rough conversion
        lng_range = radius / (111.0 * abs(latitude))
        
        pharmacies = Pharmacy.query.filter(
            Pharmacy.account_status == 'active',
            Pharmacy.latitude.between(latitude - lat_range, latitude + lat_range),
            Pharmacy.longitude.between(longitude - lng_range, longitude + lng_range)
        ).limit(limit).all()
        
        # Calculate actual distances and sort
        pharmacy_data = []
        for pharmacy in pharmacies:
            if pharmacy.latitude and pharmacy.longitude:
                # Simple distance calculation (not accurate for large distances)
                lat_diff = pharmacy.latitude - latitude
                lng_diff = pharmacy.longitude - longitude
                distance = (lat_diff**2 + lng_diff**2)**0.5 * 111.0  # Rough km conversion
                
                if distance <= radius:
                    data = pharmacy.to_dict(language=language)
                    data['distance'] = round(distance, 2)
                    pharmacy_data.append(data)
        
        # Sort by distance
        pharmacy_data.sort(key=lambda x: x['distance'])
        
        return jsonify({
            'success': True,
            'data': {
                'items': pharmacy_data,
                'total': len(pharmacy_data)
            }
        }), 200
        
    except Exception as e:
        current_app.logger.error(f"Get nearby pharmacies error: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'Failed to fetch nearby pharmacies',
            'message_ar': 'فشل في جلب الصيدليات القريبة'
        }), 500

@pharmacies_bp.route('/search', methods=['GET'])
def search_pharmacies():
    """Search pharmacies by name, location, or services"""
    try:
        query_text = request.args.get('q', '').strip()
        page = request.args.get('page', 1, type=int)
        per_page = min(request.args.get('per_page', 20, type=int), 100)
        language = request.args.get('language', 'ar')
        
        if not query_text:
            return jsonify({
                'success': False,
                'message': 'Search query is required',
                'message_ar': 'استعلام البحث مطلوب'
            }), 400
        
        # Build search query
        search_term = f'%{query_text}%'
        query = Pharmacy.query.filter(
            Pharmacy.account_status == 'active'
        ).filter(
            db.or_(
                Pharmacy.pharmacy_name.ilike(search_term),
                Pharmacy.pharmacy_name_ar.ilike(search_term),
                Pharmacy.description.ilike(search_term),
                Pharmacy.description_ar.ilike(search_term),
                Pharmacy.city.ilike(search_term),
                Pharmacy.specializations.ilike(search_term),
                Pharmacy.specializations_ar.ilike(search_term),
                Pharmacy.services_offered.ilike(search_term),
                Pharmacy.services_offered_ar.ilike(search_term)
            )
        ).order_by(Pharmacy.average_rating.desc())
        
        # Paginate
        pagination = query.paginate(
            page=page,
            per_page=per_page,
            error_out=False
        )
        
        pharmacies = [pharmacy.to_dict(language=language) for pharmacy in pagination.items]
        
        return jsonify({
            'success': True,
            'data': {
                'items': pharmacies,
                'page': page,
                'pages': pagination.pages,
                'per_page': per_page,
                'total': pagination.total,
                'has_next': pagination.has_next,
                'has_prev': pagination.has_prev,
                'query': query_text
            }
        }), 200
        
    except Exception as e:
        current_app.logger.error(f"Search pharmacies error: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'Failed to search pharmacies',
            'message_ar': 'فشل في البحث عن الصيدليات'
        }), 500

