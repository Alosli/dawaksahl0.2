from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity
from datetime import datetime, timedelta
import uuid
import os
from werkzeug.utils import secure_filename

from src.models import db
from src.models.prescription import Prescription, PrescriptionMedication
from src.models.user import User
from src.models.pharmacy import Pharmacy
from src.models.product import Product

prescriptions_bp = Blueprint('prescriptions', __name__)

def get_current_user():
    try:
        current_user_id = get_jwt_identity()
        if not current_user_id:
            return None
        
        # Use filter_by for string UUIDs (more reliable)
        user = User.query.filter_by(id=str(current_user_id)).first()
        return user
    except Exception as e:
        print(f"Error getting current user: {e}")
        return None


def get_current_pharmacy():
    """Get current authenticated pharmacy"""
    try:
        current_pharmacy_id = get_jwt_identity()
        return Pharmacy.query.get(current_pharmacy_id)
    except:
        return None

def allowed_file(filename):
    """Check if file extension is allowed"""
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'pdf'}
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def upload_prescription_file(file):
    """Upload prescription file and return URL"""
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S_')
        filename = timestamp + filename
        
        upload_dir = os.path.join(current_app.config.get('UPLOAD_FOLDER', 'uploads'), 'prescriptions')
        os.makedirs(upload_dir, exist_ok=True)
        
        file_path = os.path.join(upload_dir, filename)
        file.save(file_path)
        
        return f"/uploads/prescriptions/{filename}"
    return None

@prescriptions_bp.route('/prescriptions', methods=['GET'])
@jwt_required()
def get_prescriptions():
    """Get user's prescriptions"""
    try:
        # Direct JWT identity handling
        current_user_id = get_jwt_identity()
        if not current_user_id:
            return jsonify({
                'success': False,
                'message': 'Authentication required',
                'message_ar': 'المصادقة مطلوبة'
            }), 401
        
        # Find user directly
        current_user = User.query.filter_by(id=str(current_user_id)).first()
        if not current_user:
            return jsonify({
                'success': False,
                'message': 'User not found',
                'message_ar': 'المستخدم غير موجود'
            }), 404
        
        # Get query parameters
        page = int(request.args.get('page', 1))
        per_page = min(int(request.args.get('per_page', 10)), 50)
        status = request.args.get('status')
        prescription_type = request.args.get('type')
        
        # Build query
        query = Prescription.query.filter_by(user_id=current_user.id)
        
        if status:
            query = query.filter(Prescription.status == status)
        
        if prescription_type:
            query = query.filter(Prescription.prescription_type == prescription_type)
        
        query = query.order_by(Prescription.created_at.desc())
        
        prescriptions = query.paginate(
            page=page, per_page=per_page, error_out=False
        )
        
        language = request.headers.get('Accept-Language', 'ar')
        
        return jsonify({
            'success': True,
            'data': [p.to_dict(language=language) for p in prescriptions.items],
            'pagination': {
                'page': page,
                'per_page': per_page,
                'total': prescriptions.total,
                'pages': prescriptions.pages,
                'has_next': prescriptions.has_next,
                'has_prev': prescriptions.has_prev
            }
        }), 200
        
    except Exception as e:
        current_app.logger.error(f"Error fetching prescriptions: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'Error fetching prescriptions: {str(e)}',
            'message_ar': 'خطأ في جلب الوصفات الطبية'
        }), 500

@prescriptions_bp.route('/prescriptions/<prescription_id>', methods=['GET'])
@jwt_required()
def get_prescription(prescription_id):
    """Get specific prescription details"""
    try:
        current_user = get_current_user()
        current_pharmacy = get_current_pharmacy()
        
        prescription = Prescription.query.get(prescription_id)
        if not prescription:
            return jsonify({
                'success': False,
                'message': 'Prescription not found',
                'message_ar': 'الوصفة الطبية غير موجودة'
            }), 404
        
        if current_user and prescription.user_id != current_user.id:
            return jsonify({
                'success': False,
                'message': 'Access denied',
                'message_ar': 'الوصول مرفوض'
            }), 403
        
        if not current_user and not current_pharmacy:
            return jsonify({
                'success': False,
                'message': 'Authentication required',
                'message_ar': 'المصادقة مطلوبة'
            }), 401
        
        language = request.headers.get('Accept-Language', 'ar')
        
        return jsonify({
            'success': True,
            'data': prescription.to_dict(language=language)
        }), 200
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Error fetching prescription: {str(e)}',
            'message_ar': 'خطأ في جلب الوصفة الطبية'
        }), 500

@prescriptions_bp.route('/prescriptions/<prescription_id>/verify', methods=['POST'])
@jwt_required()
def verify_prescription(prescription_id):
    """Verify prescription by pharmacist"""
    try:
        current_pharmacy = get_current_pharmacy()
        if not current_pharmacy:
            return jsonify({
                'success': False,
                'message': 'Pharmacy authentication required',
                'message_ar': 'مصادقة الصيدلية مطلوبة'
            }), 401
        
        prescription = Prescription.query.get(prescription_id)
        if not prescription:
            return jsonify({
                'success': False,
                'message': 'Prescription not found',
                'message_ar': 'الوصفة الطبية غير موجودة'
            }), 404
        
        if prescription.status != 'pending':
            return jsonify({
                'success': False,
                'message': 'Prescription cannot be verified',
                'message_ar': 'لا يمكن التحقق من الوصفة الطبية'
            }), 400
        
        data = request.get_json()
        notes = data.get('notes', '')
        
        prescription.verify_prescription(current_pharmacy.id, notes)
        
        db.session.commit()
        
        language = request.headers.get('Accept-Language', 'ar')
        
        return jsonify({
            'success': True,
            'message': 'Prescription verified successfully',
            'message_ar': 'تم التحقق من الوصفة الطبية بنجاح',
            'data': prescription.to_dict(language=language)
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': f'Error verifying prescription: {str(e)}',
            'message_ar': 'خطأ في التحقق من الوصفة الطبية'
        }), 500

@prescriptions_bp.route('/prescriptions/<prescription_id>/fill', methods=['POST'])
@jwt_required()
def fill_prescription(prescription_id):
    """Fill prescription (mark as filled)"""
    try:
        current_pharmacy = get_current_pharmacy()
        if not current_pharmacy:
            return jsonify({
                'success': False,
                'message': 'Pharmacy authentication required',
                'message_ar': 'مصادقة الصيدلية مطلوبة'
            }), 401
        
        prescription = Prescription.query.get(prescription_id)
        if not prescription:
            return jsonify({
                'success': False,
                'message': 'Prescription not found',
                'message_ar': 'الوصفة الطبية غير موجودة'
            }), 404
        
        if not prescription.is_valid():
            return jsonify({
                'success': False,
                'message': 'Prescription is not valid for filling',
                'message_ar': 'الوصفة الطبية غير صالحة للصرف'
            }), 400
        
        data = request.get_json()
        partial = data.get('partial', False)
        medications_filled = data.get('medications', [])
        
        for med_data in medications_filled:
            medication = PrescriptionMedication.query.get(med_data.get('medication_id'))
            if medication and medication.prescription_id == prescription.id:
                quantity_dispensed = med_data.get('quantity_dispensed', medication.quantity_prescribed)
                medication.dispense_medication(quantity_dispensed)
        
        prescription.fill_prescription(partial=partial)
        
        db.session.commit()
        
        language = request.headers.get('Accept-Language', 'ar')
        
        return jsonify({
            'success': True,
            'message': 'Prescription filled successfully',
            'message_ar': 'تم صرف الوصفة الطبية بنجاح',
            'data': prescription.to_dict(language=language)
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': f'Error filling prescription: {str(e)}',
            'message_ar': 'خطأ في صرف الوصفة الطبية'
        }), 500

@prescriptions_bp.route('/prescriptions/<prescription_id>/cancel', methods=['POST'])
@jwt_required()
def cancel_prescription(prescription_id):
    """Cancel prescription"""
    try:
        current_user = get_current_user()
        current_pharmacy = get_current_pharmacy()
        
        prescription = Prescription.query.get(prescription_id)
        if not prescription:
            return jsonify({
                'success': False,
                'message': 'Prescription not found',
                'message_ar': 'الوصفة الطبية غير موجودة'
            }), 404
        
        if current_user and prescription.user_id != current_user.id:
            return jsonify({
                'success': False,
                'message': 'Access denied',
                'message_ar': 'الوصول مرفوض'
            }), 403
        
        if prescription.status in ['filled', 'cancelled']:
            return jsonify({
                'success': False,
                'message': 'Prescription cannot be cancelled',
                'message_ar': 'لا يمكن إلغاء الوصفة الطبية'
            }), 400
        
        data = request.get_json()
        reason = data.get('reason', 'Cancelled by user')
        
        prescription.cancel_prescription(reason)
        
        db.session.commit()
        
        language = request.headers.get('Accept-Language', 'ar')
        
        return jsonify({
            'success': True,
            'message': 'Prescription cancelled successfully',
            'message_ar': 'تم إلغاء الوصفة الطبية بنجاح',
            'data': prescription.to_dict(language=language)
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': f'Error cancelling prescription: {str(e)}',
            'message_ar': 'خطأ في إلغاء الوصفة الطبية'
        }), 500

@prescriptions_bp.route('/prescriptions/<prescription_id>/refill', methods=['POST'])
@jwt_required()
def refill_prescription(prescription_id):
    """Request prescription refill"""
    try:
        current_user = get_current_user()
        if not current_user:
            return jsonify({
                'success': False,
                'message': 'User authentication required',
                'message_ar': 'مصادقة المستخدم مطلوبة'
            }), 401
        
        prescription = Prescription.query.get(prescription_id)
        if not prescription:
            return jsonify({
                'success': False,
                'message': 'Prescription not found',
                'message_ar': 'الوصفة الطبية غير موجودة'
            }), 404
        
        if prescription.user_id != current_user.id:
            return jsonify({
                'success': False,
                'message': 'Access denied',
                'message_ar': 'الوصول مرفوض'
            }), 403
        
        if not prescription.can_be_refilled():
            return jsonify({
                'success': False,
                'message': 'Prescription cannot be refilled',
                'message_ar': 'لا يمكن إعادة صرف الوصفة الطبية'
            }), 400
        
        if prescription.use_refill():
            prescription.status = 'verified'
            db.session.commit()
            
            language = request.headers.get('Accept-Language', 'ar')
            
            return jsonify({
                'success': True,
                'message': 'Prescription refill requested successfully',
                'message_ar': 'تم طلب إعادة صرف الوصفة الطبية بنجاح',
                'data': prescription.to_dict(language=language)
            }), 200
        else:
            return jsonify({
                'success': False,
                'message': 'No refills remaining',
                'message_ar': 'لا توجد إعادة صرف متبقية'
            }), 400
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': f'Error processing refill: {str(e)}',
            'message_ar': 'خطأ في معالجة إعادة الصرف'
        }), 500

@prescriptions_bp.route('/prescriptions/pending', methods=['GET'])
@jwt_required()
def get_pending_prescriptions():
    """Get pending prescriptions for pharmacy verification"""
    try:
        current_pharmacy = get_current_pharmacy()
        if not current_pharmacy:
            return jsonify({
                'success': False,
                'message': 'Pharmacy authentication required',
                'message_ar': 'مصادقة الصيدلية مطلوبة'
            }), 401
        
        page = int(request.args.get('page', 1))
        per_page = min(int(request.args.get('per_page', 10)), 50)
        priority = request.args.get('priority')
        
        query = Prescription.query.filter(
            Prescription.status.in_(['pending', 'verified'])
        )
        
        if priority:
            query = query.filter(Prescription.priority == priority)
        
        query = query.order_by(
            Prescription.priority.desc(),
            Prescription.created_at.asc()
        )
        
        prescriptions = query.paginate(
            page=page, per_page=per_page, error_out=False
        )
        
        language = request.headers.get('Accept-Language', 'ar')
        
        return jsonify({
            'success': True,
            'data': [p.to_dict(language=language) for p in prescriptions.items],
            'pagination': {
                'page': page,
                'per_page': per_page,
                'total': prescriptions.total,
                'pages': prescriptions.pages,
                'has_next': prescriptions.has_next,
                'has_prev': prescriptions.has_prev
            }
        }), 200
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Error fetching pending prescriptions: {str(e)}',
            'message_ar': 'خطأ في جلب الوصفات المعلقة'
        }), 500

@prescriptions_bp.route('/prescriptions/stats', methods=['GET'])
@jwt_required()
def get_prescription_stats():
    """Get prescription statistics"""
    try:
        current_user = get_current_user()
        current_pharmacy = get_current_pharmacy()
        
        if current_user:
            total = Prescription.query.filter_by(user_id=current_user.id).count()
            pending = Prescription.query.filter_by(user_id=current_user.id, status='pending').count()
            verified = Prescription.query.filter_by(user_id=current_user.id, status='verified').count()
            filled = Prescription.query.filter_by(user_id=current_user.id, status='filled').count()
            expired = Prescription.query.filter_by(user_id=current_user.id).filter(
                Prescription.expiry_date < datetime.now().date()
            ).count()
            
        elif current_pharmacy:
            total = Prescription.query.count()
            pending = Prescription.query.filter_by(status='pending').count()
            verified = Prescription.query.filter_by(status='verified').count()
            filled = Prescription.query.filter_by(status='filled').count()
            expired = Prescription.query.filter(
                Prescription.expiry_date < datetime.now().date()
            ).count()
        else:
            return jsonify({
                'success': False,
                'message': 'Authentication required',
                'message_ar': 'المصادقة مطلوبة'
            }), 401
        
        return jsonify({
            'success': True,
            'data': {
                'total_prescriptions': total,
                'pending_prescriptions': pending,
                'verified_prescriptions': verified,
                'filled_prescriptions': filled,
                'expired_prescriptions': expired
            }
        }), 200
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Error fetching prescription stats: {str(e)}',
            'message_ar': 'خطأ في جلب إحصائيات الوصفات'
        }), 500

