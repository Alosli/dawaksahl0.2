"""
🔥 FIXED APPOINTMENT ROUTES 🔥
Proper architecture: Uses Doctor TimeSlots correctly
No more duplicate imports - clean and logical API design!
"""

from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity, get_jwt
from datetime import datetime, timedelta, date, time
from sqlalchemy import and_, or_, desc, asc
from sqlalchemy.orm import joinedload
import uuid

# Import models with correct architecture
from src.models.user import User
from src.models.doctor import Doctor, TimeSlot, DoctorReview  # TimeSlot from doctor model!
from src.models.appointment import Appointment, AppointmentHistory, AppointmentReminder, AppointmentWaitingList  # No TimeSlot here!
from src.models.prescription import Prescription
from src.models import db
from src.utils.auth import doctor_required, user_required
from src.utils.file_upload import upload_file

# Create blueprint
appointments_bp = Blueprint('appointments', __name__, url_prefix='/api/v1/appointments')

# ================================
# PATIENT APPOINTMENT ENDPOINTS
# ================================

@appointments_bp.route('', methods=['POST'])
@jwt_required()
@user_required
def book_appointment(**kwargs):
    """
    📅 BOOK NEW APPOINTMENT
    Patient books an appointment with a doctor's time slot
    """
    current_user = kwargs.get('current_user')
    try:
        current_user_id = get_jwt_identity()
        data = request.get_json()
        
        # Required fields
        required_fields = ['time_slot_id', 'appointment_type', 'chief_complaint']
        for field in required_fields:
            if field not in data:
                return jsonify({'error': f'{field} is required'}), 400
        
        # Get the time slot (from doctor model!)
        time_slot = TimeSlot.query.get(data['time_slot_id'])
        if not time_slot:
            return jsonify({'error': 'Time slot not found'}), 404
        
        # Check if time slot is available
        can_book, message = time_slot.can_book_appointment(
            patient_age=data.get('patient_age'),
            patient_gender=data.get('patient_gender')
        )
        
        if not can_book:
            return jsonify({'error': message}), 400
        
        # Get doctor from time slot
        doctor = time_slot.doctor
        if not doctor or not doctor.is_active:
            return jsonify({'error': 'Doctor is not available'}), 400
        
        # Create appointment
        appointment = Appointment(
            patient_id=current_user_id,
            doctor_id=doctor.id,
            time_slot_id=time_slot.id,
            appointment_type=data['appointment_type'],
            consultation_mode=data.get('consultation_mode', time_slot.consultation_mode),
            chief_complaint=data['chief_complaint'],
            chief_complaint_ar=data.get('chief_complaint_ar'),
            symptoms=data.get('symptoms'),
            symptoms_ar=data.get('symptoms_ar'),
            current_medications=data.get('current_medications', []),
            allergies=data.get('allergies', []),
            medical_history_notes=data.get('medical_history_notes'),
            emergency_contact_name=data.get('emergency_contact_name'),
            emergency_contact_phone=data.get('emergency_contact_phone'),
            emergency_contact_relationship=data.get('emergency_contact_relationship'),
            consultation_fee=time_slot.get_consultation_fee(),
            payment_method=data.get('payment_method', 'card'),
            insurance_provider=data.get('insurance_provider'),
            insurance_policy_number=data.get('insurance_policy_number'),
            insurance_coverage_percentage=data.get('insurance_coverage_percentage', 0),
            is_emergency=data.get('is_emergency', False),
            requires_interpreter=data.get('requires_interpreter', False),
            interpreter_language=data.get('interpreter_language'),
            has_mobility_issues=data.get('has_mobility_issues', False),
            requires_wheelchair_access=data.get('requires_wheelchair_access', False),
            booking_source=data.get('booking_source', 'web'),
            booking_ip_address=request.remote_addr
        )
        
        # Generate appointment number
        appointment.generate_appointment_number()
        
        # Calculate total amount
        appointment.total_amount = appointment.calculate_total_amount()
        
        # Check if first visit
        existing_appointments = Appointment.query.filter_by(
            patient_id=current_user_id,
            doctor_id=doctor.id
        ).count()
        appointment.is_first_visit = existing_appointments == 0
        
        # Book the time slot
        time_slot.book_appointment()
        
        # Generate meeting link for video consultations
        if appointment.consultation_mode == 'video_call':
            appointment.meeting_link = time_slot.generate_meeting_link()
            appointment.meeting_password = time_slot.meeting_password
        
        # Save to database
        db.session.add(appointment)
        db.session.commit()
        
        # Create appointment history
        history = AppointmentHistory(
            appointment_id=appointment.id,
            changed_by_type='patient',
            changed_by_id=current_user_id,
            change_type='created',
            new_values={
                'status': appointment.status,
                'time_slot_id': appointment.time_slot_id,
                'appointment_type': appointment.appointment_type
            }
        )
        db.session.add(history)
        
        # Schedule reminders
        if data.get('send_reminders', True):
            schedule_appointment_reminders(appointment)
        
        db.session.commit()
        
        # Send confirmation
        appointment.send_confirmation()
        
        return jsonify({
            'message': 'Appointment booked successfully',
            'appointment': appointment.to_dict(),
            'doctor': doctor.to_dict(),
            'time_slot': time_slot.to_dict()
        }), 201
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error booking appointment: {str(e)}")
        return jsonify({'error': 'Failed to book appointment'}), 500


@appointments_bp.route('', methods=['GET'])
@jwt_required()
@user_required
def get_user_appointments():
    """
    📋 GET USER'S APPOINTMENTS
    Retrieve all appointments for the current user
    """
    try:
        current_user_id = get_jwt_identity()
        
        # Query parameters
        status = request.args.get('status')
        page = int(request.args.get('page', 1))
        per_page = min(int(request.args.get('per_page', 10)), 100)
        
        # Build query
        query = Appointment.query.filter_by(patient_id=current_user_id)
        
        if status:
            query = query.filter_by(status=status)
        
        # Order by appointment date (through time slot)
        query = query.join(TimeSlot).order_by(desc(TimeSlot.date), desc(TimeSlot.start_time))
        
        # Paginate
        appointments = query.paginate(
            page=page, per_page=per_page, error_out=False
        )
        
        # Include related data
        result = []
        for appointment in appointments.items:
            appointment_data = appointment.to_dict()
            appointment_data['doctor'] = appointment.doctor.to_dict()
            appointment_data['time_slot'] = appointment.time_slot.to_dict()
            result.append(appointment_data)
        
        return jsonify({
            'appointments': result,
            'pagination': {
                'page': page,
                'per_page': per_page,
                'total': appointments.total,
                'pages': appointments.pages,
                'has_next': appointments.has_next,
                'has_prev': appointments.has_prev
            }
        }), 200
        
    except Exception as e:
        current_app.logger.error(f"Error getting user appointments: {str(e)}")
        return jsonify({'error': 'Failed to retrieve appointments'}), 500


@appointments_bp.route('/<int:appointment_id>', methods=['GET'])
@jwt_required()
def get_appointment_details(appointment_id):
    """
    🔍 GET APPOINTMENT DETAILS
    Get detailed information about a specific appointment
    """
    try:
        current_user_id = get_jwt_identity()
        user_type = get_jwt().get('user_type', 'user')
        
        # Get appointment with related data
        appointment = Appointment.query.options(
            joinedload(Appointment.doctor),
            joinedload(Appointment.time_slot),
            joinedload(Appointment.prescription)
        ).get(appointment_id)
        
        if not appointment:
            return jsonify({'error': 'Appointment not found'}), 404
        
        # Check permissions
        if user_type == 'user' and appointment.patient_id != current_user_id:
            return jsonify({'error': 'Access denied'}), 403
        elif user_type == 'doctor' and appointment.doctor_id != current_user_id:
            return jsonify({'error': 'Access denied'}), 403
        
        # Prepare response data
        appointment_data = appointment.to_dict(include_sensitive=True)
        appointment_data['doctor'] = appointment.doctor.to_dict()
        appointment_data['time_slot'] = appointment.time_slot.to_dict()
        
        if appointment.prescription:
            appointment_data['prescription'] = appointment.prescription.to_dict()
        
        # Include appointment history for doctors
        if user_type == 'doctor':
            history = [h.to_dict() for h in appointment.history]
            appointment_data['history'] = history
        
        return jsonify({'appointment': appointment_data}), 200
        
    except Exception as e:
        current_app.logger.error(f"Error getting appointment details: {str(e)}")
        return jsonify({'error': 'Failed to retrieve appointment details'}), 500


@appointments_bp.route('/<int:appointment_id>/cancel', methods=['POST'])
@jwt_required()
def cancel_appointment(appointment_id):
    """
    ❌ CANCEL APPOINTMENT
    Cancel an existing appointment
    """
    try:
        current_user_id = get_jwt_identity()
        user_type = get_jwt().get('user_type', 'user')
        data = request.get_json() or {}
        
        appointment = Appointment.query.get(appointment_id)
        if not appointment:
            return jsonify({'error': 'Appointment not found'}), 404
        
        # Check permissions
        if user_type == 'user' and appointment.patient_id != current_user_id:
            return jsonify({'error': 'Access denied'}), 403
        elif user_type == 'doctor' and appointment.doctor_id != current_user_id:
            return jsonify({'error': 'Access denied'}), 403
        
        # Check if can be cancelled
        can_cancel, reason = appointment.can_be_cancelled()
        if not can_cancel:
            return jsonify({'error': reason}), 400
        
        # Cancel the appointment
        appointment.cancel_appointment(
            cancelled_by=user_type,
            reason=data.get('reason')
        )
        
        # Create history record
        history = AppointmentHistory(
            appointment_id=appointment.id,
            changed_by_type=user_type,
            changed_by_id=current_user_id,
            change_type='cancelled',
            change_reason=data.get('reason'),
            previous_values={'status': 'confirmed'},
            new_values={'status': 'cancelled'}
        )
        db.session.add(history)
        db.session.commit()
        
        return jsonify({
            'message': 'Appointment cancelled successfully',
            'appointment': appointment.to_dict()
        }), 200
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error cancelling appointment: {str(e)}")
        return jsonify({'error': 'Failed to cancel appointment'}), 500


@appointments_bp.route('/<int:appointment_id>/reschedule', methods=['POST'])
@jwt_required()
@user_required
def reschedule_appointment(appointment_id):
    """
    🔄 RESCHEDULE APPOINTMENT
    Move appointment to a different time slot
    """
    try:
        current_user_id = get_jwt_identity()
        data = request.get_json()
        
        if 'new_time_slot_id' not in data:
            return jsonify({'error': 'new_time_slot_id is required'}), 400
        
        appointment = Appointment.query.get(appointment_id)
        if not appointment:
            return jsonify({'error': 'Appointment not found'}), 404
        
        if appointment.patient_id != current_user_id:
            return jsonify({'error': 'Access denied'}), 403
        
        # Check if can be rescheduled
        can_reschedule, reason = appointment.can_be_rescheduled()
        if not can_reschedule:
            return jsonify({'error': reason}), 400
        
        # Get new time slot
        new_time_slot = TimeSlot.query.get(data['new_time_slot_id'])
        if not new_time_slot:
            return jsonify({'error': 'New time slot not found'}), 404
        
        # Check if new slot is available
        can_book, message = new_time_slot.can_book_appointment()
        if not can_book:
            return jsonify({'error': f'New time slot: {message}'}), 400
        
        # Free up old time slot
        old_time_slot = appointment.time_slot
        old_time_slot.cancel_appointment()
        
        # Book new time slot
        new_time_slot.book_appointment()
        
        # Update appointment
        appointment.reschedule_appointment(
            new_time_slot_id=new_time_slot.id,
            rescheduled_by='patient'
        )
        
        # Update consultation fee if different
        appointment.consultation_fee = new_time_slot.get_consultation_fee()
        appointment.total_amount = appointment.calculate_total_amount()
        
        # Create history record
        history = AppointmentHistory(
            appointment_id=appointment.id,
            changed_by_type='patient',
            changed_by_id=current_user_id,
            change_type='rescheduled',
            change_reason=data.get('reason'),
            previous_values={'time_slot_id': old_time_slot.id},
            new_values={'time_slot_id': new_time_slot.id}
        )
        db.session.add(history)
        db.session.commit()
        
        return jsonify({
            'message': 'Appointment rescheduled successfully',
            'appointment': appointment.to_dict(),
            'new_time_slot': new_time_slot.to_dict()
        }), 200
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error rescheduling appointment: {str(e)}")
        return jsonify({'error': 'Failed to reschedule appointment'}), 500


# ================================
# DOCTOR APPOINTMENT ENDPOINTS
# ================================

@appointments_bp.route('/doctor', methods=['GET'])
@jwt_required()
@doctor_required
def get_doctor_appointments():
    """
    🏥 GET DOCTOR'S APPOINTMENTS
    Retrieve all appointments for the current doctor
    """
    try:
        current_doctor_id = get_jwt_identity()
        
        # Query parameters
        status = request.args.get('status')
        date_from = request.args.get('date_from')
        date_to = request.args.get('date_to')
        page = int(request.args.get('page', 1))
        per_page = min(int(request.args.get('per_page', 20)), 100)
        
        # Build query
        query = Appointment.query.filter_by(doctor_id=current_doctor_id)
        
        if status:
            query = query.filter_by(status=status)
        
        if date_from:
            date_from_obj = datetime.strptime(date_from, '%Y-%m-%d').date()
            query = query.join(TimeSlot).filter(TimeSlot.date >= date_from_obj)
        
        if date_to:
            date_to_obj = datetime.strptime(date_to, '%Y-%m-%d').date()
            query = query.join(TimeSlot).filter(TimeSlot.date <= date_to_obj)
        
        # Order by appointment date
        query = query.join(TimeSlot).order_by(asc(TimeSlot.date), asc(TimeSlot.start_time))
        
        # Paginate
        appointments = query.paginate(
            page=page, per_page=per_page, error_out=False
        )
        
        # Include patient data
        result = []
        for appointment in appointments.items:
            appointment_data = appointment.to_dict(include_sensitive=True)
            appointment_data['patient'] = {
                'id': appointment.patient.id,
                'name': appointment.patient.get_full_name(),
                'phone': appointment.patient.phone,
                'email': appointment.patient.email
            }
            appointment_data['time_slot'] = appointment.time_slot.to_dict()
            result.append(appointment_data)
        
        return jsonify({
            'appointments': result,
            'pagination': {
                'page': page,
                'per_page': per_page,
                'total': appointments.total,
                'pages': appointments.pages,
                'has_next': appointments.has_next,
                'has_prev': appointments.has_prev
            }
        }), 200
        
    except Exception as e:
        current_app.logger.error(f"Error getting doctor appointments: {str(e)}")
        return jsonify({'error': 'Failed to retrieve appointments'}), 500


@appointments_bp.route('/<int:appointment_id>/confirm', methods=['POST'])
@jwt_required()
@doctor_required
def confirm_appointment(appointment_id):
    """
    ✅ CONFIRM APPOINTMENT
    Doctor confirms a pending appointment
    """
    try:
        current_doctor_id = get_jwt_identity()
        
        appointment = Appointment.query.get(appointment_id)
        if not appointment:
            return jsonify({'error': 'Appointment not found'}), 404
        
        if appointment.doctor_id != current_doctor_id:
            return jsonify({'error': 'Access denied'}), 403
        
        if appointment.status != 'pending':
            return jsonify({'error': 'Appointment is not pending'}), 400
        
        # Confirm appointment
        appointment.status = 'confirmed'
        
        # Create history record
        history = AppointmentHistory(
            appointment_id=appointment.id,
            changed_by_type='doctor',
            changed_by_id=current_doctor_id,
            change_type='confirmed',
            previous_values={'status': 'pending'},
            new_values={'status': 'confirmed'}
        )
        db.session.add(history)
        db.session.commit()
        
        return jsonify({
            'message': 'Appointment confirmed successfully',
            'appointment': appointment.to_dict()
        }), 200
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error confirming appointment: {str(e)}")
        return jsonify({'error': 'Failed to confirm appointment'}), 500


@appointments_bp.route('/<int:appointment_id>/start', methods=['POST'])
@jwt_required()
@doctor_required
def start_appointment(appointment_id):
    """
    ▶️ START APPOINTMENT
    Doctor starts the appointment consultation
    """
    try:
        current_doctor_id = get_jwt_identity()
        
        appointment = Appointment.query.get(appointment_id)
        if not appointment:
            return jsonify({'error': 'Appointment not found'}), 404
        
        if appointment.doctor_id != current_doctor_id:
            return jsonify({'error': 'Access denied'}), 403
        
        if appointment.status not in ['confirmed', 'pending']:
            return jsonify({'error': 'Appointment cannot be started'}), 400
        
        # Start appointment
        appointment.start_appointment()
        
        # Create history record
        history = AppointmentHistory(
            appointment_id=appointment.id,
            changed_by_type='doctor',
            changed_by_id=current_doctor_id,
            change_type='started',
            previous_values={'status': appointment.status},
            new_values={'status': 'in_progress'}
        )
        db.session.add(history)
        db.session.commit()
        
        return jsonify({
            'message': 'Appointment started successfully',
            'appointment': appointment.to_dict(include_sensitive=True)
        }), 200
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error starting appointment: {str(e)}")
        return jsonify({'error': 'Failed to start appointment'}), 500


@appointments_bp.route('/<int:appointment_id>/complete', methods=['POST'])
@jwt_required()
@doctor_required
def complete_appointment(appointment_id):
    """
    ✅ COMPLETE APPOINTMENT
    Doctor completes the appointment with notes and diagnosis
    """
    try:
        current_doctor_id = get_jwt_identity()
        data = request.get_json() or {}
        
        appointment = Appointment.query.get(appointment_id)
        if not appointment:
            return jsonify({'error': 'Appointment not found'}), 404
        
        if appointment.doctor_id != current_doctor_id:
            return jsonify({'error': 'Access denied'}), 403
        
        if appointment.status != 'in_progress':
            return jsonify({'error': 'Appointment is not in progress'}), 400
        
        # Update appointment with completion data
        appointment.doctor_notes = data.get('doctor_notes')
        appointment.doctor_notes_ar = data.get('doctor_notes_ar')
        appointment.diagnosis = data.get('diagnosis')
        appointment.diagnosis_ar = data.get('diagnosis_ar')
        appointment.treatment_plan = data.get('treatment_plan')
        appointment.treatment_plan_ar = data.get('treatment_plan_ar')
        appointment.follow_up_required = data.get('follow_up_required', False)
        appointment.follow_up_instructions = data.get('follow_up_instructions')
        appointment.follow_up_instructions_ar = data.get('follow_up_instructions_ar')
        
        # Vital signs
        appointment.blood_pressure = data.get('blood_pressure')
        appointment.heart_rate = data.get('heart_rate')
        appointment.temperature = data.get('temperature')
        appointment.weight = data.get('weight')
        appointment.height = data.get('height')
        
        # Follow-up date
        if data.get('follow_up_date'):
            appointment.follow_up_date = datetime.strptime(
                data['follow_up_date'], '%Y-%m-%d'
            ).date()
        
        # Complete appointment
        appointment.complete_appointment()
        
        # Create history record
        history = AppointmentHistory(
            appointment_id=appointment.id,
            changed_by_type='doctor',
            changed_by_id=current_doctor_id,
            change_type='completed',
            previous_values={'status': 'in_progress'},
            new_values={'status': 'completed'}
        )
        db.session.add(history)
        db.session.commit()
        
        return jsonify({
            'message': 'Appointment completed successfully',
            'appointment': appointment.to_dict(include_sensitive=True)
        }), 200
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error completing appointment: {str(e)}")
        return jsonify({'error': 'Failed to complete appointment'}), 500


# ================================
# TIME SLOT MANAGEMENT ENDPOINTS
# ================================

@appointments_bp.route('/time-slots/available', methods=['GET'])
def get_available_time_slots():
    """
    🕐 GET AVAILABLE TIME SLOTS
    Get available time slots for booking appointments
    """
    try:
        # Query parameters
        doctor_id = request.args.get('doctor_id', type=int)
        date_from = request.args.get('date_from')
        date_to = request.args.get('date_to')
        consultation_mode = request.args.get('consultation_mode')
        
        if not doctor_id:
            return jsonify({'error': 'doctor_id is required'}), 400
        
        # Build query for available time slots
        query = TimeSlot.query.filter_by(
            doctor_id=doctor_id,
            is_available=True,
            is_booked=False,
            status='active'
        ).filter(TimeSlot.is_holiday == False)
        
        # Date filters
        if date_from:
            date_from_obj = datetime.strptime(date_from, '%Y-%m-%d').date()
            query = query.filter(TimeSlot.date >= date_from_obj)
        else:
            # Default to today onwards
            query = query.filter(TimeSlot.date >= date.today())
        
        if date_to:
            date_to_obj = datetime.strptime(date_to, '%Y-%m-%d').date()
            query = query.filter(TimeSlot.date <= date_to_obj)
        
        if consultation_mode:
            query = query.filter_by(consultation_mode=consultation_mode)
        
        # Order by date and time
        time_slots = query.order_by(TimeSlot.date, TimeSlot.start_time).all()
        
        # Group by date
        slots_by_date = {}
        for slot in time_slots:
            date_str = slot.date.isoformat()
            if date_str not in slots_by_date:
                slots_by_date[date_str] = []
            slots_by_date[date_str].append(slot.to_dict())
        
        return jsonify({
            'available_slots': slots_by_date,
            'total_slots': len(time_slots)
        }), 200
        
    except Exception as e:
        current_app.logger.error(f"Error getting available time slots: {str(e)}")
        return jsonify({'error': 'Failed to retrieve available time slots'}), 500


# ================================
# UTILITY FUNCTIONS
# ================================

def schedule_appointment_reminders(appointment):
    """
    📅 SCHEDULE APPOINTMENT REMINDERS
    Create reminder records for an appointment
    """
    try:
        appointment_datetime = appointment.get_appointment_datetime()
        if not appointment_datetime:
            return
        
        # Default reminder times (24 hours and 2 hours before)
        reminder_times = [24, 2]
        reminder_methods = ['sms', 'email']
        
        for hours_before in reminder_times:
            reminder_time = appointment_datetime - timedelta(hours=hours_before)
            
            # Only schedule if reminder time is in the future
            if reminder_time > datetime.now():
                for method in reminder_methods:
                    reminder = AppointmentReminder(
                        appointment_id=appointment.id,
                        reminder_type=method,
                        reminder_time=reminder_time,
                        message_template=f"Appointment reminder: {hours_before} hours before"
                    )
                    db.session.add(reminder)
        
    except Exception as e:
        current_app.logger.error(f"Error scheduling reminders: {str(e)}")


# ================================
# STATISTICS AND ANALYTICS
# ================================

@appointments_bp.route('/stats', methods=['GET'])
@jwt_required()
def get_appointment_stats():
    """
    📊 GET APPOINTMENT STATISTICS
    Get appointment statistics for current user (patient or doctor)
    """
    try:
        current_user_id = get_jwt_identity()
        user_type = get_jwt().get('user_type', 'user')
        
        if user_type == 'doctor':
            # Doctor statistics
            total_appointments = Appointment.query.filter_by(doctor_id=current_user_id).count()
            completed_appointments = Appointment.query.filter_by(
                doctor_id=current_user_id, status='completed'
            ).count()
            pending_appointments = Appointment.query.filter_by(
                doctor_id=current_user_id, status='pending'
            ).count()
            cancelled_appointments = Appointment.query.filter_by(
                doctor_id=current_user_id, status='cancelled'
            ).count()
            
            # Today's appointments
            today = date.today()
            todays_appointments = Appointment.query.join(TimeSlot).filter(
                Appointment.doctor_id == current_user_id,
                TimeSlot.date == today
            ).count()
            
            stats = {
                'total_appointments': total_appointments,
                'completed_appointments': completed_appointments,
                'pending_appointments': pending_appointments,
                'cancelled_appointments': cancelled_appointments,
                'todays_appointments': todays_appointments,
                'completion_rate': (completed_appointments / total_appointments * 100) if total_appointments > 0 else 0
            }
            
        else:
            # Patient statistics
            total_appointments = Appointment.query.filter_by(patient_id=current_user_id).count()
            completed_appointments = Appointment.query.filter_by(
                patient_id=current_user_id, status='completed'
            ).count()
            upcoming_appointments = Appointment.query.join(TimeSlot).filter(
                Appointment.patient_id == current_user_id,
                Appointment.status.in_(['pending', 'confirmed']),
                TimeSlot.date >= date.today()
            ).count()
            
            stats = {
                'total_appointments': total_appointments,
                'completed_appointments': completed_appointments,
                'upcoming_appointments': upcoming_appointments
            }
        
        return jsonify({'stats': stats}), 200
        
    except Exception as e:
        current_app.logger.error(f"Error getting appointment stats: {str(e)}")
        return jsonify({'error': 'Failed to retrieve statistics'}), 500


# Register error handlers
@appointments_bp.errorhandler(404)
def not_found(error):
    return jsonify({'error': 'Endpoint not found'}), 404

@appointments_bp.errorhandler(500)
def internal_error(error):
    db.session.rollback()
    return jsonify({'error': 'Internal server error'}), 500
