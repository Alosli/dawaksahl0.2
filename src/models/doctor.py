"""
🔥 FIXED DOCTOR MODEL WITH COMPREHENSIVE TIMESLOT 🔥
Proper architecture: Doctor creates TimeSlots, Appointments reference TimeSlots
This is the correct way to design appointment scheduling!
"""

from datetime import datetime, timedelta, time, date
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, validates, Session
from werkzeug.security import generate_password_hash, check_password_hash
import jwt
import os
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import Index, event

# Import your existing db instance
from src.models import db
class Doctor(db.Model):
    """
    🏥 COMPREHENSIVE DOCTOR MODEL
    Complete medical professional profile with all necessary fields
    """
    __tablename__ = 'doctors'

    # ================================
    # PRIMARY FIELDS
    # ================================
    id = db.Column(db.Integer, primary_key=True)
    doctor_number = db.Column(db.String(20), unique=True, nullable=False)  # DR001, DR002, etc.
    
    # ================================
    # PERSONAL INFORMATION
    # ================================
    first_name = db.Column(db.String(100), nullable=False)
    first_name_ar = db.Column(db.String(100), nullable=False)
    last_name = db.Column(db.String(100), nullable=False)
    last_name_ar = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    phone = db.Column(db.String(20), nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    
    # Profile
    profile_picture = db.Column(db.String(255))
    date_of_birth = db.Column(db.Date)
    gender = db.Column(db.String(10))  # male, female
    nationality = db.Column(db.String(50))
    
    # ================================
    # MEDICAL CREDENTIALS
    # ================================
    medical_license_number = db.Column(db.String(50), unique=True, nullable=False)
    license_expiry_date = db.Column(db.Date, nullable=False)
    license_issuing_authority = db.Column(db.String(100))
    license_document = db.Column(db.String(255))  # File path to license document
    
    # Education and Training
    medical_school = db.Column(db.String(200))
    medical_school_ar = db.Column(db.String(200))
    graduation_year = db.Column(db.Integer)
    residency_program = db.Column(db.String(200))
    fellowship_program = db.Column(db.String(200))
    
    # Specialization
    primary_specialty = db.Column(db.String(100), nullable=False)
    primary_specialty_ar = db.Column(db.String(100), nullable=False)
    secondary_specialties = db.Column(db.TEXT)  # Array of additional specialties
    subspecialties = db.Column(db.TEXT)  # Array of subspecialties
    
    # Professional Experience
    years_of_experience = db.Column(db.Integer, default=0)
    board_certifications = db.Column(db.TEXT)  # Array of certifications
    professional_memberships = db.Column(db.TEXT)  # Array of memberships
    
    # ================================
    # PRACTICE INFORMATION
    # ================================
    clinic_hospital_name = db.Column(db.String(200), nullable=False)
    clinic_hospital_name_ar = db.Column(db.String(200), nullable=False)
    clinic_type = db.Column(db.String(50))  # private_clinic, hospital, medical_center
    
    # Address and Location
    address = db.Column(db.Text, nullable=False)
    address_ar = db.Column(db.Text, nullable=False)
    city = db.Column(db.String(100), nullable=False)
    district = db.Column(db.String(100))
    postal_code = db.Column(db.String(20))
    latitude = db.Column(db.DECIMAL(10, 8), index=True)  # For location-based searches
    longitude = db.Column(db.DECIMAL(11, 8), index=True)  # For location-based searches
    
    # Contact Information
    clinic_phone = db.Column(db.String(20))
    clinic_email = db.Column(db.String(120))
    website = db.Column(db.String(255))
    
    # ================================
    # CONSULTATION AND FEES
    # ================================
    consultation_fee = db.Column(db.DECIMAL(10, 2), nullable=False)
    follow_up_fee = db.Column(db.DECIMAL(10, 2))
    emergency_fee = db.Column(db.DECIMAL(10, 2))
    home_visit_fee = db.Column(db.DECIMAL(10, 2))
    video_consultation_fee = db.Column(db.DECIMAL(10, 2))
    phone_consultation_fee = db.Column(db.DECIMAL(10, 2))
    
    # Payment Methods Accepted
    accepted_payment_methods = db.Column(db.TEXT)  # ["card", "cash", "apple_pay", "stc_pay", "insurance"]
    accepted_insurance_providers = db.Column(db.TEXT)  # Array of insurance companies
    accepts_insurance = db.Column(db.Boolean, default=False)
    offers_telemedicine = db.Column(db.Boolean, default=False)

    # ================================
    # AVAILABILITY AND SCHEDULING
    # ================================
    consultation_duration = db.Column(db.Integer, default=30)  # Default appointment duration in minutes
    advance_booking_days = db.Column(db.Integer, default=30)  # How far in advance patients can book
    cancellation_policy_hours = db.Column(db.Integer, default=24)  # Cancellation notice required
    working_hours = db.Column(db.Text, nullable=False)
    # Consultation Modes
    offers_in_person = db.Column(db.Boolean, default=True)
    offers_video_consultation = db.Column(db.Boolean, default=False)
    offers_phone_consultation = db.Column(db.Boolean, default=False)
    offers_home_visits = db.Column(db.Boolean, default=False)
    
    # ================================
    # PROFESSIONAL PROFILE
    # ================================
    bio = db.Column(db.Text)
    bio_ar = db.Column(db.Text)
    languages_spoken = db.Column(db.TEXT)  # ["Arabic", "English", "French"]
    
    # Services and Treatments
    services_offered = db.Column(db.TEXT)  # Array of services
    services_offered_ar = db.Column(db.TEXT)  # Arabic services
    conditions_treated = db.Column(db.TEXT)  # Array of conditions
    conditions_treated_ar = db.Column(db.TEXT)  # Arabic conditions
    
    # ================================
    # RATINGS AND REVIEWS
    # ================================
    average_rating = db.Column(db.DECIMAL(3, 2), default=0.00)
    total_reviews = db.Column(db.Integer, default=0)
    total_patients = db.Column(db.Integer, default=0)
    total_consultations = db.Column(db.Integer, default=0)
    
    # ================================
    # VERIFICATION AND STATUS
    # ================================
    is_verified = db.Column(db.Boolean, default=False)
    verification_date = db.Column(db.DateTime)
    verification_status = db.Column(db.String(20), default='pending')  # pending, verified, rejected
    
    is_active = db.Column(db.Boolean, default=True)
    is_available = db.Column(db.Boolean, default=True)
    is_accepting_new_patients = db.Column(db.Boolean, default=True)
    
    # Account Status
    email_verified = db.Column(db.Boolean, default=False)
    phone_verified = db.Column(db.Boolean, default=False)
    profile_completed = db.Column(db.Boolean, default=False)
    
    # ================================
    # METADATA
    # ================================
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_login = db.Column(db.DateTime)
    last_activity = db.Column(db.DateTime)
    
    # ================================
    # RELATIONSHIPS
    # ================================
    # TimeSlots (Doctor's availability)
    time_slots = db.relationship("TimeSlot", back_populates="doctor", cascade="all, delete-orphan")
    
    # Appointments (through TimeSlots)
    appointments = db.relationship("Appointment", back_populates="doctor", cascade="all, delete-orphan")
    
    # Prescriptions issued by this doctor
    prescriptions = db.relationship("Prescription", back_populates="doctor", cascade="all, delete-orphan")
    
    issued_prescriptions = db.relationship(
        'Prescription',
        foreign_keys='Prescription.doctor_id',
        back_populates='doctor',
        cascade='all, delete-orphan'
    )


    # Reviews received by this doctor
    reviews = db.relationship("DoctorReview", back_populates="doctor", cascade="all, delete-orphan")
    
    # ================================
    # INDEXES FOR PERFORMANCE
    # ================================
    __table_args__ = (
        Index('idx_doctor_specialty', 'primary_specialty'),
        Index('idx_doctor_location', 'latitude', 'longitude'),
        Index('idx_doctor_city', 'city'),
        Index('idx_doctor_rating', 'average_rating'),
        Index('idx_doctor_status', 'is_active', 'is_verified'),
        Index('idx_doctor_license', 'medical_license_number'),
    )
    def __init__(self, **kwargs):
        # Remove doctor_number from kwargs if present (we'll auto-generate)
        kwargs.pop('doctor_number', None)
        super().__init__(**kwargs)
    
    @staticmethod
    def generate_doctor_number():
        """Generate next doctor number in format DR00001"""
        # Get the highest existing doctor number
        last_doctor = Doctor.query.filter(
            Doctor.doctor_number.like('DR%')
        ).order_by(Doctor.doctor_number.desc()).first()
        
        if last_doctor:
            # Extract number from DR00001 format
            try:
                last_number = int(last_doctor.doctor_number[2:])  # Remove 'DR' prefix
                next_number = last_number + 1
            except (ValueError, IndexError):
                next_number = 1
        else:
            next_number = 1
        
        # Format as DR00001 (5 digits with leading zeros)
        return f"DR{next_number:05d}"


    # ================================
    # PASSWORD METHODS
    # ================================
    def set_password(self, password):
        """Set password hash"""
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        """Check password against hash"""
        return check_password_hash(self.password_hash, password)

    # ================================
    # JWT TOKEN METHODS
    # ================================
    def generate_token(self, expires_in=3600):
        """Generate JWT token for authentication"""
        payload = {
            'doctor_id': self.id,
            'email': self.email,
            'exp': datetime.utcnow() + timedelta(seconds=expires_in)
        }
        return jwt.encode(payload, os.getenv('SECRET_KEY', 'dev-secret'), algorithm='HS256')

    @staticmethod
    def verify_token(token):
        """Verify JWT token and return doctor"""
        try:
            payload = jwt.decode(token, os.getenv('SECRET_KEY', 'dev-secret'), algorithms=['HS256'])
            return payload.get('doctor_id')
        except jwt.ExpiredSignatureError:
            return None
        except jwt.InvalidTokenError:
            return None

    # ================================
    # VALIDATION METHODS
    # ================================
    @validates('email')
    def validate_email(self, key, email):
        """Validate email format"""
        import re
        if not re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', email):
            raise ValueError('Invalid email format')
        return email.lower()

    @validates('phone')
    def validate_phone(self, key, phone):
        """Validate Saudi phone number"""
        import re
        # Saudi phone number format: +966XXXXXXXXX or 05XXXXXXXX
        if not re.match(r'^(\+967|7)?[0-9]{9}$', phone):
            raise ValueError('Invalid Saudi phone number format')
        return phone

    @validates('medical_license_number')
    def validate_license(self, key, license_number):
        """Validate medical license number format"""
        if not license_number or len(license_number) < 5:
            raise ValueError('Medical license number is required and must be at least 5 characters')
        return license_number.upper()

    # ================================
    # UTILITY METHODS
    # ================================
    def get_full_name(self, language='en'):
        """Get full name in specified language"""
        if language == 'ar':
            return f"{self.first_name_ar} {self.last_name_ar}"
        return f"{self.first_name} {self.last_name}"

    def calculate_distance(self, user_lat, user_lng):
        """Calculate distance from user location using Haversine formula"""
        if not self.latitude or not self.longitude:
            return None
        
        from math import radians, cos, sin, asin, sqrt
        
        # Convert to radians
        lat1, lng1, lat2, lng2 = map(radians, [float(self.latitude), float(self.longitude), user_lat, user_lng])
        
        # Haversine formula
        dlat = lat2 - lat1
        dlng = lng2 - lng1
        a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlng/2)**2
        c = 2 * asin(sqrt(a))
        r = 6371  # Radius of earth in kilometers
        
        return c * r

    def get_next_available_slot(self):
        """Get the next available time slot for this doctor"""
        
        # Get available slots for the next 7 days
        start_date = datetime.now().Date()
        end_date = start_date + timedelta(days=7)
        
        available_slots = []
        for slot in self.time_slots:
            if (slot.Date >= start_date and slot.Date <= end_date and 
                slot.is_available and not slot.is_booked):
                available_slots.append(slot)
        
        return min(available_slots, key=lambda x: (x.date, x.start_time)) if available_slots else None

    def get_statistics(self):
        """Get doctor statistics"""
        return {
            'total_patients': self.total_patients,
            'total_consultations': self.total_consultations,
            'average_rating': float(self.average_rating) if self.average_rating else 0,
            'total_reviews': self.total_reviews,
            'years_experience': self.years_of_experience,
            'specialties': [self.primary_specialty] + (self.secondary_specialties or []),
            'consultation_modes': {
                'in_person': self.offers_in_person,
                'video': self.offers_video_consultation,
                'phone': self.offers_phone_consultation,
                'home_visit': self.offers_home_visits
            }
        }

    def to_dict(self, include_sensitive=False):
        """Convert doctor to dictionary"""
        data = {
            'id': self.id,
            'doctor_number': self.doctor_number,
            'name': self.get_full_name(),
            'name_ar': self.get_full_name('ar'),
            'email': self.email if include_sensitive else None,
            'phone': self.phone if include_sensitive else None,
            'specialty': self.primary_specialty,
            'specialty_ar': self.primary_specialty_ar,
            'clinic_name': self.clinic_hospital_name,
            'clinic_name_ar': self.clinic_hospital_name_ar,
            'address': self.address,
            'city': self.city,
            'latitude': float(self.latitude) if self.latitude else None,
            'longitude': float(self.longitude) if self.longitude else None,
            'consultation_fee': float(self.consultation_fee),
            'average_rating': float(self.average_rating) if self.average_rating else 0,
            'total_reviews': self.total_reviews,
            'years_experience': self.years_of_experience,
            'is_verified': self.is_verified,
            'is_available': self.is_available,
            'profile_picture': self.profile_picture,
            'bio': self.bio,
            'bio_ar': self.bio_ar,
            'languages': self.languages_spoken,
            'working_hours': self.working_hours,
            'services': self.services_offered,
            'consultation_modes': {
                'in_person': self.offers_in_person,
                'video': self.offers_video_consultation,
                'phone': self.offers_phone_consultation,
                'home_visit': self.offers_home_visits
            }
        }
        return data

# Auto-generate doctor_number before insert
@event.listens_for(Doctor, 'before_insert')
def generate_doctor_number_before_insert(mapper, connection, target):
    """Auto-generate doctor number before inserting new doctor"""
    if not target.doctor_number:
        # Use raw SQL to avoid session conflicts
        result = connection.execute(
            "SELECT doctor_number FROM doctors WHERE doctor_number LIKE 'DR%' ORDER BY doctor_number DESC LIMIT 1"
        ).fetchone()
            
        if result:
            try:
                last_number = int(result[0][2:])  # Remove 'DR' prefix
                next_number = last_number + 1
            except (ValueError, IndexError):
                next_number = 1
        else:
            next_number = 1
            
        target.doctor_number = f"DR{next_number:05d}"

class TimeSlot(db.Model):
    """
    🕐 COMPREHENSIVE TIMESLOT MODEL
    Manages doctor availability and appointment scheduling
    This is where doctors define their available hours!
    """
    __tablename__ = 'time_slots'

    # ================================
    # PRIMARY FIELDS
    # ================================
    id = db.Column(db.Integer, primary_key=True)
    doctor_id = db.Column(db.Integer, db.ForeignKey('doctors.id'), nullable=False)
    
    # ================================
    # TIME AND DATE INFORMATION
    # ================================
    date = db.Column(db.Date, nullable=False)  # Specific date for this slot
    start_time = db.Column(db.Time, nullable=False)  # Start time (e.g., 09:00)
    end_time = db.Column(db.Time, nullable=False)  # End time (e.g., 09:30)
    duration = db.Column(db.Integer, default=30)  # Duration in minutes
    
    # ================================
    # SLOT CONFIGURATION
    # ================================
    slot_type = db.Column(db.String(20), default='regular')  # regular, emergency, follow_up, consultation
    consultation_mode = db.Column(db.String(20), default='in_person')  # in_person, video_call, phone_call, home_visit
    
    # Capacity and Booking
    max_appointments = db.Column(db.Integer, default=1)  # How many appointments this slot can handle
    current_appointments = db.Column(db.Integer, default=0)  # Current number of booked appointments
    is_available = db.Column(db.Boolean, default=True)  # Is this slot available for booking
    is_booked = db.Column(db.Boolean, default=False)  # Is this slot fully booked
    
    # ================================
    # PRICING AND FEES
    # ================================
    consultation_fee = db.Column(db.DECIMAL(10, 2))  # Override doctor's default fee if needed
    emergency_fee = db.Column(db.DECIMAL(10, 2))  # Additional fee for emergency slots
    
    # ================================
    # RECURRING PATTERNS
    # ================================
    is_recurring = db.Column(db.Boolean, default=False)  # Is this part of a recurring pattern
    recurrence_pattern = db.Column(db.String(20))  # daily, weekly, monthly
    recurrence_end_date = db.Column(db.Date)  # When does the recurrence end
    parent_slot_id = db.Column(db.Integer, db.ForeignKey('time_slots.id'), nullable=True, index=True)
    # ================================
    # SPECIAL CONDITIONS
    # ================================
    is_holiday = db.Column(db.Boolean, default=False)  # Is this a holiday/unavailable slot
    holiday_reason = db.Column(db.String(200))  # Reason for unavailability
    
    # Special Requirements
    requires_preparation = db.Column(db.Boolean, default=False)  # Does this appointment need prep time
    preparation_time = db.Column(db.Integer, default=0)  # Preparation time in minutes
    
    # Patient Restrictions
    new_patients_only = db.Column(db.Boolean, default=False)  # Only for new patients
    follow_up_only = db.Column(db.Boolean, default=False)  # Only for follow-up appointments
    specific_conditions = db.Column(db.TEXT)  # Array of conditions this slot is for
    
    # ================================
    # BOOKING RESTRICTIONS
    # ================================
    advance_booking_hours = db.Column(db.Integer, default=24)  # Minimum hours in advance to book
    cancellation_deadline_hours = db.Column(db.Integer, default=24)  # Deadline for cancellation
    
    # Age and Gender Restrictions
    min_patient_age = db.Column(db.Integer)  # Minimum patient age
    max_patient_age = db.Column(db.Integer)  # Maximum patient age
    gender_restriction = db.Column(db.String(10))  # male, female, null (no restriction)
    
    # ================================
    # LOCATION AND MODE
    # ================================
    location_type = db.Column(db.String(20), default='clinic')  # clinic, hospital, home, online
    specific_location = db.Column(db.String(200))  # Specific room/location if different from default
    
    # Online Consultation Details
    meeting_link = db.Column(db.String(500))  # Video call link (generated when booked)
    meeting_password = db.Column(db.String(50))  # Meeting password
    
    # ================================
    # STATUS AND WORKFLOW
    # ================================
    status = db.Column(db.String(20), default='active')  # active, cancelled, completed, blocked
    blocked_reason = db.Column(db.String(200))  # Reason if blocked
    
    # Automatic Management
    auto_confirm = db.Column(db.Boolean, default=True)  # Auto-confirm appointments for this slot
    requires_approval = db.Column(db.Boolean, default=False)  # Does doctor need to approve bookings
    
    # ================================
    # NOTIFICATIONS AND REMINDERS
    # ================================
    send_reminders = db.Column(db.Boolean, default=True)  # Send appointment reminders
    reminder_methods = db.Column(db.TEXT)  # ["sms", "email", "push"]
    reminder_times = db.Column(db.TEXT)  # [24, 2] hours before appointment
    
    # ================================
    # METADATA
    # ================================
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by = db.Column(db.String(20), default='doctor')  # doctor, admin, system
    
    # Booking Information
    first_booked_at = db.Column(db.DateTime)  # When was this slot first booked
    last_booked_at = db.Column(db.DateTime)  # When was this slot last booked
    total_bookings = db.Column(db.Integer, default=0)  # Total number of times this slot was booked
    
    # ================================
    # RELATIONSHIPS
    # ================================
    # Doctor who owns this time slot
    doctor = db.relationship("Doctor", back_populates="time_slots")
    
    # Appointments booked for this time slot
    appointments = db.relationship(
        'Appointment', 
        foreign_keys='Appointment.time_slot_id',
        back_populates='time_slot', 
        lazy='dynamic'
    )

    # Child recurring slots
    parent_slot = db.relationship('TimeSlot', remote_side=[id], back_populates='child_slots')
    child_slots = db.relationship('TimeSlot', back_populates='parent_slot')

    # ================================
    # INDEXES FOR PERFORMANCE
    # ================================
    __table_args__ = (
        Index('idx_timeslot_doctor', 'doctor_id'),
        Index('idx_timeslot_date', 'date'),
        Index('idx_timeslot_datetime', 'date', 'start_time'),
        Index('idx_timeslot_available', 'is_available', 'is_booked'),
        Index('idx_timeslot_status', 'status'),
        Index('idx_timeslot_mode', 'consultation_mode'),
    )

    # ================================
    # VALIDATION METHODS
    # ================================
    @validates('start_time', 'end_time')
    def validate_times(self, key, time_value):
        """Validate time slots are logical"""
        if key == 'end_time' and hasattr(self, 'start_time') and self.start_time:
            if time_value <= self.start_time:
                raise ValueError('End time must be after start time')
        return time_value

    @validates('max_appointments')
    def validate_max_appointments(self, key, value):
        """Validate maximum appointments"""
        if value < 1:
            raise ValueError('Maximum appointments must be at least 1')
        return value

    # ================================
    # UTILITY METHODS
    # ================================
    def is_slot_available(self):
        """Check if slot is available for booking"""
        return (self.is_available and 
                not self.is_booked and 
                self.current_appointments < self.max_appointments and
                self.status == 'active' and
                not self.is_holiday)

    def can_book_appointment(self, patient_age=None, patient_gender=None):
        """Check if a specific patient can book this slot"""
        if not self.is_slot_available():
            return False, "Slot is not available"
        
        # Check age restrictions
        if self.min_patient_age and patient_age and patient_age < self.min_patient_age:
            return False, f"Minimum age requirement: {self.min_patient_age}"
        
        if self.max_patient_age and patient_age and patient_age > self.max_patient_age:
            return False, f"Maximum age limit: {self.max_patient_age}"
        
        # Check gender restrictions
        if self.gender_restriction and patient_gender and patient_gender != self.gender_restriction:
            return False, f"This slot is restricted to {self.gender_restriction} patients"
        
        # Check advance booking requirement
        now = datetime.now()
        slot_datetime = datetime.combine(self.date, self.start_time)
        hours_until_slot = (slot_datetime - now).total_seconds() / 3600
        
        if hours_until_slot < self.advance_booking_hours:
            return False, f"Must book at least {self.advance_booking_hours} hours in advance"
        
        return True, "Slot is available"

    def book_appointment(self):
        """Book an appointment in this slot"""
        if not self.is_slot_available():
            raise ValueError("Slot is not available for booking")
        
        self.current_appointments += 1
        self.total_bookings += 1
        
        if not self.first_booked_at:
            self.first_booked_at = datetime.utcnow()
        self.last_booked_at = datetime.utcnow()
        
        # Mark as booked if at capacity
        if self.current_appointments >= self.max_appointments:
            self.is_booked = True

    def cancel_appointment(self):
        """Cancel an appointment from this slot"""
        if self.current_appointments > 0:
            self.current_appointments -= 1
            self.is_booked = False

    def get_available_capacity(self):
        """Get remaining appointment capacity"""
        return max(0, self.max_appointments - self.current_appointments)

    def get_slot_datetime(self):
        """Get slot as DateTime object"""
        return datetime.combine(self.date, self.start_time)

    def get_consultation_fee(self):
        """Get the consultation fee for this slot"""
        if self.consultation_fee:
            return float(self.consultation_fee)
        return float(self.doctor.consultation_fee) if self.doctor else 0

    def generate_meeting_link(self):
        """Generate video call meeting link"""
        if self.consultation_mode == 'video_call':
            # This would integrate with your video calling service
            # For now, return a placeholder
            import uuid
            meeting_id = str(uuid.uuid4())[:8]
            self.meeting_link = f"https://meet.dawaksahl.com/room/{meeting_id}"
            self.meeting_password = str(uuid.uuid4())[:6].upper()
            return self.meeting_link
        return None

    def to_dict(self):
        """Convert time slot to dictionary"""
        return {
            'id': self.id,
            'doctor_id': self.doctor_id,
            'date': self.date.isoformat() if self.date else None,
            'start_time': self.start_time.strftime('%H:%M') if self.start_time else None,
            'end_time': self.end_time.strftime('%H:%M') if self.end_time else None,
            'duration': self.duration,
            'slot_type': self.slot_type,
            'consultation_mode': self.consultation_mode,
            'is_available': self.is_available,
            'is_booked': self.is_booked,
            'available_capacity': self.get_available_capacity(),
            'consultation_fee': self.get_consultation_fee(),
            'location_type': self.location_type,
            'requires_approval': self.requires_approval,
            'advance_booking_hours': self.advance_booking_hours,
            'status': self.status
        }


class DoctorReview(db.Model):
    """
    ⭐ DOCTOR REVIEW MODEL
    Patient reviews and ratings for doctors
    """
    __tablename__ = 'doctor_reviews'

    id = db.Column(db.Integer, primary_key=True)
    doctor_id = db.Column(db.Integer, db.ForeignKey('doctors.id'), nullable=False)
    patient_id = db.Column(db.String(36), db.ForeignKey('users.id'), nullable=False)
    appointment_id = db.Column(db.Integer, db.ForeignKey('appointments.id'), nullable=False, unique=True, index=True)   # enforce 1:1)
    
    # Review Content
    rating = db.Column(db.Integer, nullable=False)  # 1-5 stars
    review_text = db.Column(db.Text)
    review_text_ar = db.Column(db.Text)
    
    # Review Categories
    communication_rating = db.Column(db.Integer)  # 1-5
    professionalism_rating = db.Column(db.Integer)  # 1-5
    facility_rating = db.Column(db.Integer)  # 1-5
    wait_time_rating = db.Column(db.Integer)  # 1-5
    
    # Verification
    is_verified = db.Column(db.Boolean, default=False)
    is_anonymous = db.Column(db.Boolean, default=False)
    
    # Doctor Response
    doctor_response = db.Column(db.Text)
    doctor_response_date = db.Column(db.DateTime)
    
    # Metadata
    created_at = db.Column(db.DateTime, default= datetime.utcnow)
    updated_at = db.Column(db.DateTime, default= datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    doctor = db.relationship("Doctor", back_populates="reviews")
    patient = db.relationship("User", back_populates="doctor_reviews")
    appointment = db.relationship("Appointment", back_populates="review",foreign_keys=[appointment_id])

    def to_dict(self):
        """Convert review to dictionary"""
        return {
            'id': self.id,
            'rating': self.rating,
            'review_text': self.review_text,
            'communication_rating': self.communication_rating,
            'professionalism_rating': self.professionalism_rating,
            'facility_rating': self.facility_rating,
            'wait_time_rating': self.wait_time_rating,
            'is_verified': self.is_verified,
            'doctor_response': self.doctor_response,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
