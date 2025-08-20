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
    """Get current authenticated user"""
    try:
        jwt_data = get_jwt_identity()
        if not jwt_data:
            return None
        
        # Extract user ID from JWT object
        if isinstance(jwt_data, dict):
            current_user_id = jwt_data.get('id')
        else:
            current_user_id = jwt_data
        
        if not current_user_id:
            return None
        
        # Find user with the extracted ID
        user = User.query.filter_by(id=str(current_user_id)).first()
        return user
        
    except Exception as e:
        print(f"Error in get_current_user: {e}")
        return None

def get_current_pharmacy():
    """Get current authenticated pharmacy"""
    try:
        jwt_data = get_jwt_identity()
        if not jwt_data:
            return None
        
        # Extract pharmacy ID from JWT object
        if isinstance(jwt_data, dict):
            current_pharmacy_id = jwt_data.get('id')
        else:
            current_pharmacy_id = jwt_data
        
        if not current_pharmacy_id:
            return None
        
        # Find pharmacy with the extracted ID
        pharmacy = Pharmacy.query.filter_by(id=str(current_pharmacy_id)).first()
        return pharmacy
        
    except Exception as e:
        print(f"Error in get_current_pharmacy: {e}")
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

@prescriptions_bp.route('/prescriptions', methods=['POST'])
@jwt_required()
def create_prescription():
    """Create a new prescription"""
    try:
        current_user = get_current_user()
        if not current_user:
            return jsonify({
                'success': False,
                'message': 'User not found',
                'message_ar': 'المستخدم غير موجود'
            }), 404
        
        data = request.get_json() if request.is_json else request.form.to_dict()
        
        required_fields = ['doctor_name', 'issued_date', 'medications']
        for field in required_fields:
            if not data.get(field):
                return jsonify({
                    'success': False,
                    'message': f'{field} is required',
                    'message_ar': f'{field} مطلوب'
                }), 400
        
        prescription_image_url = None
        if 'prescription_image' in request.files:
            file = request.files['prescription_image']
            prescription_image_url = upload_prescription_file(file)
        
        medications_data = data.get('medications')
        if isinstance(medications_data, str):
            import json
            medications_data = json.loads(medications_data)
        
        prescription = Prescription(
            patient_id=current_user.id,
            doctor_name=data.get('doctor_name'),
            doctor_name_ar=data.get('doctor_name_ar'),
            doctor_license_number=data.get('doctor_license_number'),
            doctor_specialty=data.get('doctor_specialty'),
            doctor_specialty_ar=data.get('doctor_specialty_ar'),
            doctor_phone=data.get('doctor_phone'),
            doctor_email=data.get('doctor_email'),
            clinic_hospital_name=data.get('clinic_hospital_name'),
            clinic_hospital_name_ar=data.get('clinic_hospital_name_ar'),
            clinic_address=data.get('clinic_address'),
            clinic_address_ar=data.get('clinic_address_ar'),
            diagnosis=data.get('diagnosis'),
            diagnosis_ar=data.get('diagnosis_ar'),
            diagnosis_code=data.get('diagnosis_code'),
            prescription_image_url=prescription_image_url,
            issued_date=datetime.strptime(data.get('issued_date'), '%Y-%m-%d').date(),
            expiry_date=datetime.strptime(data.get('expiry_date'), '%Y-%m-%d').date() if data.get('expiry_date') else None,
            refills_allowed=int(data.get('refills_allowed', 0)),
            general_instructions=data.get('general_instructions'),
            general_instructions_ar=data.get('general_instructions_ar'),
            dietary_restrictions=data.get('dietary_restrictions'),
            dietary_restrictions_ar=data.get('dietary_restrictions_ar'),
            lifestyle_recommendations=data.get('lifestyle_recommendations'),
            lifestyle_recommendations_ar=data.get('lifestyle_recommendations_ar'),
            is_emergency=data.get('is_emergency', False),
            emergency_contact_name=data.get('emergency_contact_name'),
            emergency_contact_phone=data.get('emergency_contact_phone'),
            insurance_provider=data.get('insurance_provider'),
            insurance_policy_number=data.get('insurance_policy_number'),
            insurance_coverage_percentage=float(data.get('insurance_coverage_percentage', 0)),
            patient_copay_amount=float(data.get('patient_copay_amount', 0)),
            follow_up_required=data.get('follow_up_required', False),
            follow_up_date=datetime.strptime(data.get('follow_up_date'), '%Y-%m-%d').date() if data.get('follow_up_date') else None,
            follow_up_instructions=data.get('follow_up_instructions'),
            follow_up_instructions_ar=data.get('follow_up_instructions_ar'),
            prescription_type=data.get('prescription_type', 'acute'),
            priority=data.get('priority', 'normal'),
            requires_counseling=data.get('requires_counseling', False),
            requires_monitoring=data.get('requires_monitoring', False),
            has_drug_interactions=data.get('has_drug_interactions', False),
            has_allergies_warnings=data.get('has_allergies_warnings', False)
        )
        
        db.session.add(prescription)
        db.session.flush()
        
        for med_data in medications_data:
            medication = PrescriptionMedication(
                prescription_id=prescription.id,
                product_id=med_data.get('product_id'),
                medication_name=med_data.get('medication_name'),
                medication_name_ar=med_data.get('medication_name_ar'),
                generic_name=med_data.get('generic_name'),
                generic_name_ar=med_data.get('generic_name_ar'),
                brand_name=med_data.get('brand_name'),
                brand_name_ar=med_data.get('brand_name_ar'),
                strength=med_data.get('strength'),
                dosage_form=med_data.get('dosage_form'),
                dosage_form_ar=med_data.get('dosage_form_ar'),
                quantity_prescribed=int(med_data.get('quantity_prescribed', 1)),
                unit=med_data.get('unit', 'tablet'),
                dosage_instructions=med_data.get('dosage_instructions'),
                dosage_instructions_ar=med_data.get('dosage_instructions_ar'),
                frequency=med_data.get('frequency'),
                frequency_ar=med_data.get('frequency_ar'),
                duration=med_data.get('duration'),
                duration_ar=med_data.get('duration_ar'),
                route_of_administration=med_data.get('route_of_administration'),
                route_of_administration_ar=med_data.get('route_of_administration_ar'),
                timing_instructions=med_data.get('timing_instructions'),
                timing_instructions_ar=med_data.get('timing_instructions_ar'),
                special_instructions=med_data.get('special_instructions'),
                special_instructions_ar=med_data.get('special_instructions_ar'),
                storage_instructions=med_data.get('storage_instructions'),
                storage_instructions_ar=med_data.get('storage_instructions_ar'),
                warnings=med_data.get('warnings'),
                warnings_ar=med_data.get('warnings_ar'),
                contraindications=med_data.get('contraindications'),
                contraindications_ar=med_data.get('contraindications_ar'),
                side_effects=med_data.get('side_effects'),
                side_effects_ar=med_data.get('side_effects_ar'),
                food_interactions=med_data.get('food_interactions'),
                food_interactions_ar=med_data.get('food_interactions_ar'),
                unit_price=float(med_data.get('unit_price', 0)) if med_data.get('unit_price') else None,
                is_controlled_substance=med_data.get('is_controlled_substance', False),
                controlled_substance_schedule=med_data.get('controlled_substance_schedule'),
                refills_allowed=int(med_data.get('refills_allowed', 0))
            )
            
            if med_data.get('drug_interactions'):
                medication.set_drug_interactions(med_data['drug_interactions'])
            
            medication.calculate_total_cost()
            db.session.add(medication)
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Prescription created successfully',
            'message_ar': 'تم إنشاء الوصفة الطبية بنجاح',
            'data': prescription.to_dict(language=request.headers.get('Accept-Language', 'ar'))
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': f'Error creating prescription: {str(e)}',
            'message_ar': 'خطأ في إنشاء الوصفة الطبية'
        }), 500

@prescriptions_bp.route('/prescriptions', methods=['GET'])
@jwt_required()
def get_prescriptions():
    """Get user's prescriptions"""
    try:
        current_user = get_current_user()
        if not current_user:
            return jsonify({
                'success': False,
                'message': 'User not found',
                'message_ar': 'المستخدم غير موجود'
            }), 404
        
        page = int(request.args.get('page', 1))
        per_page = min(int(request.args.get('per_page', 10)), 50)
        status = request.args.get('status')
        prescription_type = request.args.get('type')
        
        query = Prescription.query.filter_by(patient_id=current_user.id)
        
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
        
        if current_user and prescription.patient_id != current_user.id:
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
        
        if current_user and prescription.patient_id != current_user.id:
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
        
        if prescription.patient_id != current_user.id:
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
            total = Prescription.query.filter_by(patient_id=current_user.id).count()
            pending = Prescription.query.filter_by(patient_id=current_user.id, status='pending').count()
            verified = Prescription.query.filter_by(patient_id=current_user.id, status='verified').count()
            filled = Prescription.query.filter_by(patient_id=current_user.id, status='filled').count()
            expired = Prescription.query.filter_by(patient_id=current_user.id).filter(
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
@prescriptions_bp.route('/prescriptions/doctor', methods=['GET'])
@jwt_required()
def get_doctor_prescriptions():
    """
    🏥 GET DOCTOR'S PRESCRIPTIONS
    Retrieve all prescriptions created by the current doctor
    """
    try:
        # Get current doctor from JWT
        jwt_data = get_jwt_identity()
        
        # Extract doctor ID from JWT identity
        if isinstance(jwt_data, dict):
            current_doctor_id = jwt_data.get('id')
            user_type = jwt_data.get('type', 'user')
        else:
            current_doctor_id = jwt_data
            user_type = 'doctor'  # Assume doctor if not specified
        
        # Verify this is a doctor
        if user_type != 'doctor':
            return jsonify({
                'success': False,
                'message': 'Doctor authentication required',
                'message_ar': 'مصادقة الطبيب مطلوبة'
            }), 401
        
        # Query parameters
        page = int(request.args.get('page', 1))
        per_page = min(int(request.args.get('per_page', 10)), 50)
        status = request.args.get('status')
        prescription_type = request.args.get('type')
        patient_name = request.args.get('patient_name')
        date_from = request.args.get('date_from')
        date_to = request.args.get('date_to')
        
        # Build query - Filter by doctor_id
        query = Prescription.query.filter_by(doctor_id=current_doctor_id)
        
        # Apply filters
        if status:
            query = query.filter(Prescription.status == status)
        
        if prescription_type:
            query = query.filter(Prescription.prescription_type == prescription_type)
        
        if patient_name:
            # Join with User table to search by patient name
            from src.models.user import User
            query = query.join(User, Prescription.patient_id == User.id).filter(
                User.first_name.ilike(f'%{patient_name}%') |
                User.last_name.ilike(f'%{patient_name}%')
            )
        
        if date_from:
            date_from_obj = datetime.strptime(date_from, '%Y-%m-%d')
            query = query.filter(Prescription.issue_date >= date_from_obj)
        
        if date_to:
            date_to_obj = datetime.strptime(date_to, '%Y-%m-%d')
            query = query.filter(Prescription.issue_date <= date_to_obj)
        
        # Order by creation date (newest first)
        query = query.order_by(Prescription.created_at.desc())
        
        # Paginate results
        prescriptions = query.paginate(
            page=page, per_page=per_page, error_out=False
        )
        
        # Get language preference
        language = request.headers.get('Accept-Language', 'ar')
        
        # Prepare response data
        prescription_data = []
        for prescription in prescriptions.items:
            # Get patient name
            patient_name = f"{prescription.patient.first_name} {prescription.patient.last_name}" if prescription.patient else "Unknown Patient"
            
            prescription_dict = prescription.to_dict(include_doctor_info=False)  # Don't include doctor info since this is for the doctor
            prescription_dict['patient_name'] = patient_name
            prescription_dict['patient_phone'] = prescription.patient.phone if prescription.patient else None
            prescription_dict['medication_count'] = len(prescription.medications)
            
            prescription_data.append(prescription_dict)
        
        # Calculate statistics
        total_prescriptions = Prescription.query.filter_by(doctor_id=current_doctor_id).count()
        pending_prescriptions = Prescription.query.filter_by(
            doctor_id=current_doctor_id, 
            status=PrescriptionStatus.PENDING
        ).count()
        filled_prescriptions = Prescription.query.filter_by(
            doctor_id=current_doctor_id, 
            status=PrescriptionStatus.FILLED
        ).count()
        
        # Today's prescriptions
        today = datetime.now().date()
        todays_prescriptions = Prescription.query.filter(
            Prescription.doctor_id == current_doctor_id,
            db.func.date(Prescription.issue_date) == today
        ).count()
        
        return jsonify({
            'success': True,
            'prescriptions': prescription_data,
            'stats': {
                'total_prescriptions': total_prescriptions,
                'pending_prescriptions': pending_prescriptions,
                'filled_prescriptions': filled_prescriptions,
                'todays_prescriptions': todays_prescriptions
            },
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
        current_app.logger.error(f"Error getting doctor prescriptions: {str(e)}")
        print(f"❌ Error getting doctor prescriptions: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'Error fetching prescriptions: {str(e)}',
            'message_ar': 'خطأ في جلب الوصفات الطبية'
        }), 500


# ALSO ADD THIS ENDPOINT FOR PRESCRIPTION STATISTICS
@prescriptions_bp.route('/prescriptions/doctor/stats', methods=['GET'])
@jwt_required()
def get_doctor_prescription_stats():
    """
    📊 GET DOCTOR'S PRESCRIPTION STATISTICS
    Get detailed statistics for doctor's prescriptions
    """
    try:
        # Get current doctor from JWT
        jwt_data = get_jwt_identity()
        
        if isinstance(jwt_data, dict):
            current_doctor_id = jwt_data.get('id')
            user_type = jwt_data.get('type', 'user')
        else:
            current_doctor_id = jwt_data
            user_type = 'doctor'
        
        if user_type != 'doctor':
            return jsonify({
                'success': False,
                'message': 'Doctor authentication required',
                'message_ar': 'مصادقة الطبيب مطلوبة'
            }), 401
        
        # Calculate comprehensive statistics
        total_prescriptions = Prescription.query.filter_by(doctor_id=current_doctor_id).count()
        
        # Status-based counts
        pending_count = Prescription.query.filter_by(
            doctor_id=current_doctor_id, 
            status=PrescriptionStatus.PENDING
        ).count()
        
        verified_count = Prescription.query.filter_by(
            doctor_id=current_doctor_id, 
            status=PrescriptionStatus.VERIFIED
        ).count()
        
        filled_count = Prescription.query.filter_by(
            doctor_id=current_doctor_id, 
            status=PrescriptionStatus.FILLED
        ).count()
        
        cancelled_count = Prescription.query.filter_by(
            doctor_id=current_doctor_id, 
            status=PrescriptionStatus.CANCELLED
        ).count()
        
        # Time-based counts
        today = datetime.now().date()
        this_month = datetime.now().replace(day=1).date()
        
        todays_count = Prescription.query.filter(
            Prescription.doctor_id == current_doctor_id,
            db.func.date(Prescription.issue_date) == today
        ).count()
        
        this_month_count = Prescription.query.filter(
            Prescription.doctor_id == current_doctor_id,
            Prescription.issue_date >= this_month
        ).count()
        
        # Emergency prescriptions
        emergency_count = Prescription.query.filter_by(
            doctor_id=current_doctor_id,
            is_emergency=True
        ).count()
        
        # Controlled substances
        controlled_count = Prescription.query.filter_by(
            doctor_id=current_doctor_id,
            is_controlled_substance=True
        ).count()
        
        return jsonify({
            'success': True,
            'stats': {
                'total_prescriptions': total_prescriptions,
                'pending_prescriptions': pending_count,
                'verified_prescriptions': verified_count,
                'filled_prescriptions': filled_count,
                'cancelled_prescriptions': cancelled_count,
                'todays_prescriptions': todays_count,
                'this_month_prescriptions': this_month_count,
                'emergency_prescriptions': emergency_count,
                'controlled_prescriptions': controlled_count,
                'fill_rate': (filled_count / total_prescriptions * 100) if total_prescriptions > 0 else 0
            }
        }), 200
        
    except Exception as e:
        current_app.logger.error(f"Error getting doctor prescription stats: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'Error fetching prescription statistics: {str(e)}',
            'message_ar': 'خطأ في جلب إحصائيات الوصفات الطبية'
        }), 500

