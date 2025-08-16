"""
🔥 FIXED APPOINTMENT MODEL 🔥
Proper architecture: Appointments reference Doctor TimeSlots
No duplicate TimeSlot class - clean and logical design!
"""

from datetime import datetime, timedelta
from sqlalchemy import Index
from sqlalchemy.orm import relationship, validates
from flask_sqlalchemy import SQLAlchemy
import uuid

from src.models import db

class Appointment(db.Model):
    """
    📅 COMPREHENSIVE APPOINTMENT MODEL
    Links patients to doctor time slots for appointment booking
    This is the correct way to handle appointments!
    """
    __tablename__ = 'appointments'

    # ================================
    # PRIMARY FIELDS
    # ================================
    id = db.Column(db.Integer, primary_key=True)
    appointment_number = db.Column(db.String(20), unique=True, nullable=False)  # APT001, APT002, etc.
    
    # ================================
    # RELATIONSHIPS - PROPER ARCHITECTURE
    # ================================
    patient_id = db.Column(db.String(36), db.ForeignKey('users.id'), nullable=False)
    doctor_id = db.Column(db.Integer, db.ForeignKey('doctors.id'), nullable=False)
    time_slot_id = db.Column(db.Integer, db.ForeignKey('time_slots.id'), nullable=False)  # Links to doctor's TimeSlot!
    
    # ================================
    # APPOINTMENT DETAILS
    # ================================
    appointment_type = db.Column(db.String(20), default='consultation')  # consultation, follow_up, checkup, emergency
    consultation_mode = db.Column(db.String(20))  # Inherited from TimeSlot, but can be overridden
    
    # Status and Workflow
    status = db.Column(db.String(20), default='pending')  # pending, confirmed, in_progress, completed, cancelled, no_show
    booking_status = db.Column(db.String(20), default='active')  # active, rescheduled, cancelled
    
    # ================================
    # MEDICAL INFORMATION
    # ================================
    chief_complaint = db.Column(db.Text)
    chief_complaint_ar = db.Column(db.Text)
    symptoms = db.Column(db.Text)
    symptoms_ar = db.Column(db.Text)
    
    # Medical History for this appointment
    current_medications = db.Column(db.JSON)  # Array of current medications
    allergies = db.Column(db.JSON)  # Array of allergies
    medical_history_notes = db.Column(db.Text)
    
    # Vital Signs (filled during appointment)
    blood_pressure = db.Column(db.String(20))  # e.g., "120/80"
    heart_rate = db.Column(db.Integer)
    temperature = db.Column(db.DECIMAL(4, 1))  # e.g., 37.5
    weight = db.Column(db.DECIMAL(5, 2))  # e.g., 70.50 kg
    height = db.Column(db.DECIMAL(5, 2))  # e.g., 175.00 cm
    
    # ================================
    # EMERGENCY CONTACT
    # ================================
    emergency_contact_name = db.Column(db.String(100))
    emergency_contact_phone = db.Column(db.String(20))
    emergency_contact_relationship = db.Column(db.String(50))
    
    # ================================
    # PAYMENT AND INSURANCE
    # ================================
    consultation_fee = db.Column(db.DECIMAL(10, 2), nullable=False)  # Copied from TimeSlot at booking
    additional_fees = db.Column(db.DECIMAL(10, 2), default=0.00)  # Any additional charges
    total_amount = db.Column(db.DECIMAL(10, 2), nullable=False)
    
    payment_method = db.Column(db.String(20))  # card, apple_pay, stc_pay, cash, insurance
    payment_status = db.Column(db.String(20), default='pending')  # pending, paid, failed, refunded, partial
    payment_reference = db.Column(db.String(100))  # Payment gateway reference
    
    # Insurance Information
    insurance_provider = db.Column(db.String(100))
    insurance_policy_number = db.Column(db.String(50))
    insurance_coverage_percentage = db.Column(db.DECIMAL(5, 2), default=0.00)
    insurance_covered_amount = db.Column(db.DECIMAL(10, 2), default=0.00)
    patient_copay = db.Column(db.DECIMAL(10, 2))
    
    # ================================
    # APPOINTMENT RESULTS
    # ================================
    doctor_notes = db.Column(db.Text)
    doctor_notes_ar = db.Column(db.Text)
    diagnosis = db.Column(db.Text)
    diagnosis_ar = db.Column(db.Text)
    treatment_plan = db.Column(db.Text)
    treatment_plan_ar = db.Column(db.Text)
    
    # Prescription issued during appointment
    prescription_id = db.Column(db.Integer, db.ForeignKey('prescriptions.id'))
    
    # Follow-up Requirements
    follow_up_required = db.Column(db.Boolean, default=False)
    follow_up_date = db.Column(db.Date)
    follow_up_instructions = db.Column(db.Text)
    follow_up_instructions_ar = db.Column(db.Text)
    
    # ================================
    # APPOINTMENT LOGISTICS
    # ================================
    check_in_time = db.Column(db.DateTime)  # When patient checked in
    appointment_start_time = db.Column(db.DateTime)  # When appointment actually started
    appointment_end_time = db.Column(db.DateTime)  # When appointment ended
    actual_duration = db.Column(db.Integer)  # Actual duration in minutes
    
    # Location Details (if different from default)
    appointment_location = db.Column(db.String(200))
    room_number = db.Column(db.String(20))
    
    # Online Consultation Details
    meeting_link = db.Column(db.String(500))  # Video call link
    meeting_password = db.Column(db.String(50))  # Meeting password
    meeting_started_at = db.Column(db.DateTime)
    meeting_ended_at = db.Column(db.DateTime)
    
    # ================================
    # CANCELLATION AND RESCHEDULING
    # ================================
    cancelled_at = db.Column(db.DateTime)
    cancelled_by = db.Column(db.String(20))  # patient, doctor, admin, system
    cancellation_reason = db.Column(db.Text)
    cancellation_reason_ar = db.Column(db.Text)
    
    # Rescheduling
    original_time_slot_id = db.Column(db.Integer, db.ForeignKey('time_slots.id'))  # Original slot if rescheduled
    rescheduled_count = db.Column(db.Integer, default=0)  # Number of times rescheduled
    rescheduled_at = db.Column(db.DateTime)
    rescheduled_by = db.Column(db.String(20))  # patient, doctor, admin
    
    # ================================
    # RATING AND FEEDBACK
    # ================================
    patient_rating = db.Column(db.Integer)  # 1-5 stars from patient
    patient_review = db.Column(db.Text)
    patient_review_ar = db.Column(db.Text)
    patient_feedback_date = db.Column(db.DateTime)
    
    doctor_rating = db.Column(db.Integer)  # 1-5 stars from doctor (rating the patient)
    doctor_review = db.Column(db.Text)  # Doctor's notes about the patient
    doctor_feedback_date = db.Column(db.DateTime)
    
    # ================================
    # REMINDERS AND NOTIFICATIONS
    # ================================
    reminder_sent = db.Column(db.Boolean, default=False)
    reminder_sent_at = db.Column(db.DateTime)
    confirmation_sent = db.Column(db.Boolean, default=False)
    confirmation_sent_at = db.Column(db.DateTime)
    
    # Patient Preferences
    preferred_reminder_methods = db.Column(db.JSON)  # ["sms", "email", "push"]
    preferred_reminder_times = db.Column(db.JSON)  # [24, 2] hours before
    
    # ================================
    # QUALITY AND COMPLIANCE
    # ================================
    appointment_quality_score = db.Column(db.DECIMAL(3, 2))  # Overall quality score
    wait_time_minutes = db.Column(db.Integer)  # How long patient waited
    patient_satisfaction = db.Column(db.Integer)  # 1-5 satisfaction rating
    
    # Compliance Tracking
    patient_arrived_on_time = db.Column(db.Boolean)
    doctor_started_on_time = db.Column(db.Boolean)
    appointment_completed_successfully = db.Column(db.Boolean, default=False)
    
    # ================================
    # SPECIAL FLAGS
    # ================================
    is_emergency = db.Column(db.Boolean, default=False)
    is_first_visit = db.Column(db.Boolean, default=False)
    is_follow_up = db.Column(db.Boolean, default=False)
    requires_interpreter = db.Column(db.Boolean, default=False)
    interpreter_language = db.Column(db.String(50))
    
    # Special Needs
    has_mobility_issues = db.Column(db.Boolean, default=False)
    requires_wheelchair_access = db.Column(db.Boolean, default=False)
    has_hearing_impairment = db.Column(db.Boolean, default=False)
    has_visual_impairment = db.Column(db.Boolean, default=False)
    
    # ================================
    # METADATA
    # ================================
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    completed_at = db.Column(db.DateTime)
    
    # Booking Information
    booked_by = db.Column(db.String(20), default='patient')  # patient, doctor, admin, system
    booking_source = db.Column(db.String(20), default='web')  # web, mobile, phone, walk_in
    booking_ip_address = db.Column(db.String(45))  # For security tracking
    
    # ================================
    # RELATIONSHIPS - PROPER ARCHITECTURE
    # ================================
    # Patient who booked the appointment
    patient = db.relationship("User", foreign_keys=[patient_id])
    
    # Doctor for the appointment
    doctor = db.relationship("Doctor", foreign_keys=[doctor_id], back_populates="appointments")
    
    # Time slot this appointment is booked for (THE KEY RELATIONSHIP!)
    time_slot = db.relationship("TimeSlot", back_populates="appointments", foreign_keys=[time_slot_id])
    
    # Original time slot if rescheduled
    original_time_slot = db.relationship("TimeSlot", foreign_keys=[original_time_slot_id])
    
    # Prescription issued during appointment
    prescription = db.relationship("Prescription",foreign_keys="Prescription.appointment_id", back_populates="appointment")
    
    # Appointment history and changes
    history = db.relationship("AppointmentHistory", foreign_keys="AppointmentHistory.appointment_id", back_populates="appointment", cascade="all, delete-orphan")    
    # Reminders for this appointment
    reminders = db.relationship("AppointmentReminder", foreign_keys="AppointmentReminder.appointment_id", back_populates="appointment", cascade="all, delete-orphan")
    
    review = db.relationship(
        'DoctorReview',
        back_populates='appointment',
        uselist=False,                                   # 1:1
        cascade='all, delete-orphan',
        foreign_keys='DoctorReview.appointment_id'
    )

    # ================================
    # INDEXES FOR PERFORMANCE
    # ================================
    __table_args__ = (
        Index('idx_appointment_patient', 'patient_id'),
        Index('idx_appointment_doctor', 'doctor_id'),
        Index('idx_appointment_timeslot', 'time_slot_id'),
        Index('idx_appointment_status', 'status'),
        Index('idx_appointment_date', 'created_at'),
        Index('idx_appointment_number', 'appointment_number'),
        Index('idx_appointment_payment', 'payment_status'),
    )

    # ================================
    # VALIDATION METHODS
    # ================================
    @validates('appointment_number')
    def validate_appointment_number(self, key, value):
        """Validate appointment number format"""
        if not value or not value.startswith('APT'):
            raise ValueError('Appointment number must start with APT')
        return value.upper()

    @validates('patient_rating', 'doctor_rating')
    def validate_ratings(self, key, value):
        """Validate rating values"""
        if value is not None and (value < 1 or value > 5):
            raise ValueError('Rating must be between 1 and 5')
        return value

    # ================================
    # UTILITY METHODS
    # ================================
    def get_appointment_DateTime(self):
        """Get appointment Date and time from time slot"""
        if self.time_slot:
            return datetime.combine(self.time_slot.Date, self.time_slot.start_time)
        return None

    def get_appointment_duration(self):
        """Get appointment duration from time slot"""
        if self.time_slot:
            return self.time_slot.duration
        return 30  # Default 30 minutes

    def can_be_cancelled(self):
        """Check if appointment can be cancelled"""
        if self.status in ['completed', 'cancelled', 'no_show']:
            return False, "Appointment cannot be cancelled"
        
        appointment_datetime = self.get_appointment_datetime()
        if not appointment_datetime:
            return False, "Invalid appointment time"
        
        # Check cancellation deadline
        hours_until_appointment = (appointment_datetime - datetime.now()).total_seconds() / 3600
        cancellation_deadline = self.time_slot.cancellation_deadline_hours if self.time_slot else 24
        
        if hours_until_appointment < cancellation_deadline:
            return False, f"Cannot cancel within {cancellation_deadline} hours of appointment"
        
        return True, "Appointment can be cancelled"

    def can_be_rescheduled(self):
        """Check if appointment can be rescheduled"""
        can_cancel, reason = self.can_be_cancelled()
        if not can_cancel:
            return False, reason
        
        # Additional rescheduling rules
        if self.rescheduled_count >= 3:
            return False, "Maximum reschedule limit reached"
        
        return True, "Appointment can be rescheduled"

    def calculate_total_amount(self):
        """Calculate total appointment amount"""
        base_fee = float(self.consultation_fee) if self.consultation_fee else 0
        additional = float(self.additional_fees) if self.additional_fees else 0
        total = base_fee + additional
        
        # Apply insurance coverage
        if self.insurance_coverage_percentage:
            coverage = float(self.insurance_coverage_percentage) / 100
            self.insurance_covered_amount = total * coverage
            self.patient_copay = total - self.insurance_covered_amount
            return self.patient_copay
        
        return total

    def generate_appointment_number(self):
        """Generate unique appointment number"""
        if not self.appointment_number:
            # Generate based on Date and sequence
            today = datetime.now().strftime('%Y%m%d')
            # This would typically query the database for the next sequence number
            # For now, use a simple approach
            import random
            sequence = random.randint(1000, 9999)
            self.appointment_number = f"APT{today}{sequence}"

    def send_confirmation(self):
        """Send appointment confirmation"""
        # This would integrate with your notification service
        self.confirmation_sent = True
        self.confirmation_sent_at = datetime.utcnow()

    def check_in_patient(self):
        """Check in patient for appointment"""
        self.check_in_time = datetime.utcnow()
        self.status = 'confirmed'

    def start_appointment(self):
        """Start the appointment"""
        self.appointment_start_time = datetime.utcnow()
        self.status = 'in_progress'

    def complete_appointment(self):
        """Complete the appointment"""
        self.appointment_end_time = datetime.utcnow()
        self.completed_at = datetime.utcnow()
        self.status = 'completed'
        self.appointment_completed_successfully = True
        
        # Calculate actual duration
        if self.appointment_start_time:
            duration = (self.appointment_end_time - self.appointment_start_time).total_seconds() / 60
            self.actual_duration = int(duration)

    def cancel_appointment(self, cancelled_by, reason=None):
        """Cancel the appointment"""
        self.status = 'cancelled'
        self.cancelled_at = datetime.utcnow()
        self.cancelled_by = cancelled_by
        self.cancellation_reason = reason
        
        # Free up the time slot
        if self.time_slot:
            self.time_slot.cancel_appointment()

    def reschedule_appointment(self, new_time_slot_id, rescheduled_by):
        """Reschedule appointment to new time slot"""
        # Store original time slot
        self.original_time_slot_id = self.time_slot_id
        
        # Update to new time slot
        self.time_slot_id = new_time_slot_id
        self.rescheduled_count += 1
        self.rescheduled_at = datetime.utcnow()
        self.rescheduled_by = rescheduled_by
        
        # Update status
        self.booking_status = 'rescheduled'
        self.status = 'pending'  # Reset to pending for new slot

    def to_dict(self, include_sensitive=False):
        """Convert appointment to dictionary"""
        appointment_DateTime = self.get_appointment_DateTime()
        
        data = {
            'id': self.id,
            'appointment_number': self.appointment_number,
            'patient_id': self.patient_id,
            'doctor_id': self.doctor_id,
            'time_slot_id': self.time_slot_id,
            'appointment_type': self.appointment_type,
            'consultation_mode': self.consultation_mode,
            'status': self.status,
            'booking_status': self.booking_status,
            'appointment_DateTime': appointment_datetime.isoformat() if appointment_datetime else None,
            'duration': self.get_appointment_duration(),
            'chief_complaint': self.chief_complaint,
            'symptoms': self.symptoms,
            'consultation_fee': float(self.consultation_fee) if self.consultation_fee else 0,
            'total_amount': float(self.total_amount) if self.total_amount else 0,
            'payment_status': self.payment_status,
            'is_emergency': self.is_emergency,
            'is_first_visit': self.is_first_visit,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
        
        if include_sensitive:
            data.update({
                'emergency_contact_name': self.emergency_contact_name,
                'emergency_contact_phone': self.emergency_contact_phone,
                'medical_history_notes': self.medical_history_notes,
                'doctor_notes': self.doctor_notes,
                'diagnosis': self.diagnosis,
                'treatment_plan': self.treatment_plan,
                'meeting_link': self.meeting_link,
                'payment_reference': self.payment_reference
            })
        
        return data


class AppointmentHistory(db.Model):
    """
    📋 APPOINTMENT HISTORY MODEL
    Tracks all changes made to appointments for audit trail
    """
    __tablename__ = 'appointment_history'

    id = db.Column(db.Integer, primary_key=True)
    patient_id = db.Column(db.String(36), db.ForeignKey('users.id'), nullable=True, index=True)
    appointment_id = db.Column(db.Integer, db.ForeignKey('appointments.id'), nullable=False, index=True)
    
    # Change Details
    changed_by_type = db.Column(db.String(20), nullable=False)  # patient, doctor, admin, system
    changed_by_id = db.Column(db.Integer)
    change_type = db.Column(db.String(50), nullable=False)  # created, updated, cancelled, rescheduled, completed
    
    # Previous and New Values
    previous_values = db.Column(db.JSON)
    new_values = db.Column(db.JSON)
    change_reason = db.Column(db.Text)
    
    # Metadata
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    appointment = db.relationship("Appointment", back_populates="history", foreign_keys=[appointment_id])

    def to_dict(self):
        return {
            'id': self.id,
            'change_type': self.change_type,
            'changed_by_type': self.changed_by_type,
            'change_reason': self.change_reason,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }


class AppointmentReminder(db.Model):
    """
    🔔 APPOINTMENT REMINDER MODEL
    Manages reminders sent to patients and doctors
    """
    __tablename__ = 'appointment_reminders'

    id = db.Column(db.Integer, primary_key=True)
    patient_id = db.Column(db.String(36), db.ForeignKey('users.id'), nullable=True, index=True)    
    appointment_id = db.Column(db.Integer, db.ForeignKey('appointments.id'), nullable=False, index=True)
    
    # Reminder Details
    reminder_type = db.Column(db.String(20), nullable=False)  # sms, email, push, whatsapp
    recipient_type = db.Column(db.String(20), default='patient')  # patient, doctor
    reminder_time = db.Column(db.DateTime, nullable=False)
    message_template = db.Column(db.String(500))
    
    # Status
    status = db.Column(db.String(20), default='pending')  # pending, sent, failed, cancelled
    sent_at = db.Column(db.DateTime)
    error_message = db.Column(db.Text)
    
    # Metadata
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    appointment = db.relationship("Appointment", back_populates="reminders", foreign_keys=[appointment_id])

    def to_dict(self):
        return {
            'id': self.id,
            'reminder_type': self.reminder_type,
            'recipient_type': self.recipient_type,
            'reminder_time': self.reminder_time.isoformat() if self.reminder_time else None,
            'status': self.status,
            'sent_at': self.sent_at.isoformat() if self.sent_at else None
        }


class AppointmentWaitingList(db.Model):
    """
    ⏳ APPOINTMENT WAITING LIST MODEL
    Manages patients waiting for fully booked time slots
    """
    __tablename__ = 'appointment_waiting_list'

    id = db.Column(db.Integer, primary_key=True)
    patient_id = db.Column(db.String(36), db.ForeignKey('users.id'), nullable=False)
    doctor_id = db.Column(db.Integer, db.ForeignKey('doctors.id'), nullable=False)
    
    # Preferred Appointment Details
    preferred_date = db.Column(db.Date)
    preferred_time_start = db.Column(db.Time)
    preferred_time_end = db.Column(db.Time)
    consultation_mode = db.Column(db.String(20))
    appointment_type = db.Column(db.String(20))
    
    # Priority and Status
    priority = db.Column(db.Integer, default=1)  # 1=normal, 2=urgent, 3=emergency
    status = db.Column(db.String(20), default='waiting')  # waiting, notified, expired, cancelled
    
    # Contact Preferences
    notification_methods = db.Column(db.JSON)  # ["sms", "email", "push"]
    
    # Metadata
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    expires_at = db.Column(db.DateTime)
    notified_at = db.Column(db.DateTime)
    
    # Relationships
    patient = db.relationship("User", foreign_keys=[patient_id])
    doctor = db.relationship("Doctor", foreign_keys=[doctor_id])
    
    def to_dict(self):
        return {
            'id': self.id,
            'patient_id': self.patient_id,
            'doctor_id': self.doctor_id,
            'preferred_date': self.preferred_date.isoformat() if self.preferred_date else None,
            'priority': self.priority,
            'status': self.status,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
