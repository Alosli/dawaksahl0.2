"""
Updated Prescription Model for DawakSahl Backend
Now properly linked with Doctor model to automatically pull doctor information
"""

from datetime import datetime, timedelta
from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, Float, ForeignKey, Enum, JSON
from sqlalchemy.orm import relationship, validates
from sqlalchemy.ext.hybrid import hybrid_property
from src.models import db
import enum

class PrescriptionStatus(enum.Enum):
    PENDING = "pending"           # معلق
    VERIFIED = "verified"         # تم التحقق
    FILLED = "filled"            # تم الصرف
    PARTIALLY_FILLED = "partially_filled"  # تم الصرف جزئياً
    CANCELLED = "cancelled"       # ملغي
    EXPIRED = "expired"          # منتهي الصلاحية
    REFILL_REQUESTED = "refill_requested"  # طلب إعادة صرف

class PrescriptionType(enum.Enum):
    REGULAR = "regular"          # عادي
    EMERGENCY = "emergency"      # طارئ
    CHRONIC = "chronic"          # مزمن
    CONTROLLED = "controlled"    # مواد خاضعة للرقابة

class Prescription(db.Model):
    __tablename__ = 'prescriptions'
    
    # Primary Information
    id = Column(Integer, primary_key=True)
    prescription_number = Column(String(50), unique=True, nullable=False, index=True)
    
    # Foreign Keys - UPDATED TO LINK WITH DOCTOR
    patient_id = Column(Integer, ForeignKey('users.id'), nullable=False, index=True)
    doctor_id = Column(Integer, ForeignKey('doctors.id'), nullable=False, index=True)  # NEW
    pharmacy_id = Column(Integer, ForeignKey('pharmacies.id'), nullable=True, index=True)
    
    # Prescription Details
    status = Column(Enum(PrescriptionStatus), default=PrescriptionStatus.PENDING, nullable=False, index=True)
    prescription_type = Column(Enum(PrescriptionType), default=PrescriptionType.REGULAR, nullable=False)
    
    # Medical Information
    diagnosis = Column(Text)
    diagnosis_ar = Column(Text)
    medical_notes = Column(Text)
    medical_notes_ar = Column(Text)
    
    # REMOVED - Now pulled from Doctor model automatically
    # doctor_name = Column(String(200))  # REMOVED
    # doctor_name_ar = Column(String(200))  # REMOVED
    # doctor_license = Column(String(100))  # REMOVED
    # doctor_specialty = Column(String(100))  # REMOVED
    # doctor_phone = Column(String(20))  # REMOVED
    # doctor_email = Column(String(100))  # REMOVED
    # clinic_hospital_name = Column(String(200))  # REMOVED
    # clinic_address = Column(Text)  # REMOVED
    
    # Prescription Management
    issue_date = Column(DateTime, default=datetime.utcnow, nullable=False)
    expiry_date = Column(DateTime, nullable=False)
    valid_until = Column(DateTime)
    refills_allowed = Column(Integer, default=0)
    refills_remaining = Column(Integer, default=0)
    
    # Verification and Processing
    verification_date = Column(DateTime)
    verified_by_pharmacy_id = Column(Integer, ForeignKey('pharmacies.id'))
    fill_date = Column(DateTime)
    filled_by_pharmacy_id = Column(Integer, ForeignKey('pharmacies.id'))
    
    # Insurance and Payment
    insurance_coverage = Column(Float, default=0.0)
    patient_copay = Column(Float, default=0.0)
    total_cost = Column(Float, default=0.0)
    insurance_claim_number = Column(String(100))
    
    # File Management
    prescription_image = Column(String(500))
    scanned_document = Column(String(500))
    
    # Emergency and Special Handling
    is_emergency = Column(Boolean, default=False)
    is_controlled_substance = Column(Boolean, default=False)
    requires_consultation = Column(Boolean, default=False)
    
    # Drug Interactions and Allergies
    drug_interactions = Column(JSON)
    patient_allergies = Column(JSON)
    contraindications = Column(Text)
    
    # Tracking and Audit
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by = Column(String(100))
    last_modified_by = Column(String(100))
    
    # Relationships
    patient = relationship("User", foreign_keys=[patient_id], backref="prescriptions")
    doctor = relationship("Doctor", foreign_keys=[doctor_id], backref="issued_prescriptions")  # NEW
    pharmacy = relationship("Pharmacy", foreign_keys=[pharmacy_id], backref="processed_prescriptions")
    verified_by_pharmacy = relationship("Pharmacy", foreign_keys=[verified_by_pharmacy_id])
    filled_by_pharmacy = relationship("Pharmacy", foreign_keys=[filled_by_pharmacy_id])
    medications = relationship("PrescriptionMedication", back_populates="prescription", cascade="all, delete-orphan")
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        if not self.prescription_number:
            self.prescription_number = self.generate_prescription_number()
        if not self.expiry_date:
            self.expiry_date = datetime.utcnow() + timedelta(days=90)  # 3 months default
        self.refills_remaining = self.refills_allowed

    @staticmethod
    def generate_prescription_number():
        """Generate unique prescription number"""
        timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
        return f"RX{timestamp}"

    # HYBRID PROPERTIES - Automatically pull from Doctor model
    @hybrid_property
    def doctor_name(self):
        """Get doctor name from Doctor model"""
        return self.doctor.full_name if self.doctor else None
    
    @hybrid_property
    def doctor_name_ar(self):
        """Get doctor Arabic name from Doctor model"""
        return self.doctor.full_name_ar if self.doctor else None
    
    @hybrid_property
    def doctor_license(self):
        """Get doctor license from Doctor model"""
        return self.doctor.medical_license_number if self.doctor else None
    
    @hybrid_property
    def doctor_specialty(self):
        """Get doctor specialty from Doctor model"""
        return self.doctor.specialty if self.doctor else None
    
    @hybrid_property
    def doctor_specialty_ar(self):
        """Get doctor specialty in Arabic from Doctor model"""
        return self.doctor.specialty_ar if self.doctor else None
    
    @hybrid_property
    def doctor_phone(self):
        """Get doctor phone from Doctor model"""
        return self.doctor.phone if self.doctor else None
    
    @hybrid_property
    def doctor_email(self):
        """Get doctor email from Doctor model"""
        return self.doctor.email if self.doctor else None
    
    @hybrid_property
    def clinic_hospital_name(self):
        """Get clinic name from Doctor model"""
        return self.doctor.clinic_name if self.doctor else None
    
    @hybrid_property
    def clinic_hospital_name_ar(self):
        """Get clinic Arabic name from Doctor model"""
        return self.doctor.clinic_name_ar if self.doctor else None
    
    @hybrid_property
    def clinic_address(self):
        """Get clinic address from Doctor model"""
        return self.doctor.address if self.doctor else None
    
    @hybrid_property
    def doctor_years_experience(self):
        """Get doctor years of experience"""
        return self.doctor.years_of_experience if self.doctor else None

    @validates('doctor_id')
    def validate_doctor_id(self, key, doctor_id):
        """Validate that doctor exists and is active"""
        if doctor_id:
            from src.models.doctor import Doctor
            doctor = Doctor.query.get(doctor_id)
            if not doctor:
                raise ValueError("Doctor not found")
            if not doctor.is_active:
                raise ValueError("Doctor is not active")
        return doctor_id

    @validates('expiry_date')
    def validate_expiry_date(self, key, expiry_date):
        """Validate expiry date is in the future"""
        if expiry_date and expiry_date <= datetime.utcnow():
            raise ValueError("Expiry date must be in the future")
        return expiry_date

    def is_expired(self):
        """Check if prescription is expired"""
        return datetime.utcnow() > self.expiry_date

    def can_be_refilled(self):
        """Check if prescription can be refilled"""
        return (
            self.refills_remaining > 0 and
            not self.is_expired() and
            self.status in [PrescriptionStatus.FILLED, PrescriptionStatus.PARTIALLY_FILLED]
        )

    def calculate_total_cost(self):
        """Calculate total cost of all medications"""
        total = sum(med.total_cost for med in self.medications if med.total_cost)
        self.total_cost = total
        return total

    def get_medication_summary(self):
        """Get summary of all medications"""
        return [
            {
                'name': med.medication_name,
                'name_ar': med.medication_name_ar,
                'dosage': med.dosage,
                'frequency': med.frequency,
                'duration': med.duration_days,
                'quantity': med.quantity
            }
            for med in self.medications
        ]

    def to_dict(self, include_doctor_info=True):
        """Convert to dictionary with automatic doctor information"""
        data = {
            'id': self.id,
            'prescription_number': self.prescription_number,
            'patient_id': self.patient_id,
            'doctor_id': self.doctor_id,
            'pharmacy_id': self.pharmacy_id,
            'status': self.status.value if self.status else None,
            'prescription_type': self.prescription_type.value if self.prescription_type else None,
            'diagnosis': self.diagnosis,
            'diagnosis_ar': self.diagnosis_ar,
            'medical_notes': self.medical_notes,
            'medical_notes_ar': self.medical_notes_ar,
            'issue_date': self.issue_date.isoformat() if self.issue_date else None,
            'expiry_date': self.expiry_date.isoformat() if self.expiry_date else None,
            'refills_allowed': self.refills_allowed,
            'refills_remaining': self.refills_remaining,
            'total_cost': self.total_cost,
            'is_emergency': self.is_emergency,
            'is_controlled_substance': self.is_controlled_substance,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
        }
        
        # Automatically include doctor information
        if include_doctor_info and self.doctor:
            data['doctor_info'] = {
                'name': self.doctor_name,
                'name_ar': self.doctor_name_ar,
                'license': self.doctor_license,
                'specialty': self.doctor_specialty,
                'specialty_ar': self.doctor_specialty_ar,
                'phone': self.doctor_phone,
                'email': self.doctor_email,
                'clinic_name': self.clinic_hospital_name,
                'clinic_name_ar': self.clinic_hospital_name_ar,
                'clinic_address': self.clinic_address,
                'years_experience': self.doctor_years_experience
            }
        
        # Include medications
        data['medications'] = [med.to_dict() for med in self.medications]
        
        return data

    def __repr__(self):
        return f'<Prescription {self.prescription_number} - Dr. {self.doctor_name} for Patient {self.patient_id}>'


class PrescriptionMedication(db.Model):
    __tablename__ = 'prescription_medications'
    
    # Primary Information
    id = Column(Integer, primary_key=True)
    prescription_id = Column(Integer, ForeignKey('prescriptions.id'), nullable=False, index=True)
    
    # Medication Details
    medication_name = Column(String(200), nullable=False)
    medication_name_ar = Column(String(200))
    generic_name = Column(String(200))
    generic_name_ar = Column(String(200))
    brand_name = Column(String(200))
    brand_name_ar = Column(String(200))
    
    # Dosage and Administration
    dosage = Column(String(100), nullable=False)  # e.g., "500mg"
    dosage_form = Column(String(50))  # tablet, capsule, syrup, etc.
    frequency = Column(String(100), nullable=False)  # e.g., "twice daily"
    frequency_ar = Column(String(100))
    route_of_administration = Column(String(50))  # oral, topical, injection
    
    # Duration and Quantity
    duration_days = Column(Integer)
    quantity = Column(Integer, nullable=False)
    quantity_unit = Column(String(20), default='tablets')  # tablets, bottles, tubes
    
    # Instructions
    instructions = Column(Text)
    instructions_ar = Column(Text)
    special_instructions = Column(Text)
    special_instructions_ar = Column(Text)
    
    # Substitution and Alternatives
    substitution_allowed = Column(Boolean, default=True)
    alternative_medications = Column(JSON)
    
    # Cost and Insurance
    unit_price = Column(Float)
    total_cost = Column(Float)
    insurance_covered = Column(Boolean, default=False)
    copay_amount = Column(Float)
    
    # Safety and Monitoring
    side_effects = Column(Text)
    side_effects_ar = Column(Text)
    contraindications = Column(Text)
    monitoring_required = Column(Boolean, default=False)
    
    # Dispensing Information
    dispensed_quantity = Column(Integer, default=0)
    remaining_quantity = Column(Integer)
    last_dispensed_date = Column(DateTime)
    
    # Tracking
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    prescription = relationship("Prescription", back_populates="medications")
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        if self.quantity and not self.remaining_quantity:
            self.remaining_quantity = self.quantity

    @validates('quantity')
    def validate_quantity(self, key, quantity):
        """Validate quantity is positive"""
        if quantity is not None and quantity <= 0:
            raise ValueError("Quantity must be positive")
        return quantity

    def calculate_total_cost(self):
        """Calculate total cost based on unit price and quantity"""
        if self.unit_price and self.quantity:
            self.total_cost = self.unit_price * self.quantity
        return self.total_cost

    def can_be_dispensed(self, requested_quantity):
        """Check if requested quantity can be dispensed"""
        return (
            self.remaining_quantity and
            requested_quantity <= self.remaining_quantity and
            self.prescription.status in [PrescriptionStatus.VERIFIED, PrescriptionStatus.PARTIALLY_FILLED]
        )

    def dispense(self, quantity):
        """Dispense medication and update quantities"""
        if not self.can_be_dispensed(quantity):
            raise ValueError("Cannot dispense requested quantity")
        
        self.dispensed_quantity += quantity
        self.remaining_quantity -= quantity
        self.last_dispensed_date = datetime.utcnow()
        
        # Update prescription status
        if self.remaining_quantity == 0:
            # Check if all medications in prescription are fully dispensed
            all_dispensed = all(med.remaining_quantity == 0 for med in self.prescription.medications)
            if all_dispensed:
                self.prescription.status = PrescriptionStatus.FILLED
            else:
                self.prescription.status = PrescriptionStatus.PARTIALLY_FILLED

    def to_dict(self):
        """Convert to dictionary"""
        return {
            'id': self.id,
            'prescription_id': self.prescription_id,
            'medication_name': self.medication_name,
            'medication_name_ar': self.medication_name_ar,
            'generic_name': self.generic_name,
            'brand_name': self.brand_name,
            'dosage': self.dosage,
            'dosage_form': self.dosage_form,
            'frequency': self.frequency,
            'frequency_ar': self.frequency_ar,
            'duration_days': self.duration_days,
            'quantity': self.quantity,
            'quantity_unit': self.quantity_unit,
            'instructions': self.instructions,
            'instructions_ar': self.instructions_ar,
            'substitution_allowed': self.substitution_allowed,
            'unit_price': self.unit_price,
            'total_cost': self.total_cost,
            'dispensed_quantity': self.dispensed_quantity,
            'remaining_quantity': self.remaining_quantity,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

    def __repr__(self):
        return f'<PrescriptionMedication {self.medication_name} - {self.dosage}>'
