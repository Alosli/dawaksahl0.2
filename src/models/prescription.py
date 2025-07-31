import uuid
from datetime import datetime
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy import Column, String, Boolean, DateTime, Date, Enum, Text, ForeignKey, Integer, Float
from sqlalchemy.orm import relationship
from src.models import db

class Prescription(db.Model):
    """Prescription model with multilingual support."""
    
    __tablename__ = 'prescriptions'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey('users.id'), nullable=False)
    
    # Doctor information
    doctor_name = Column(String(200), nullable=False)
    doctor_name_ar = Column(String(200), nullable=True)
    doctor_license = Column(String(50), nullable=True)
    hospital_clinic = Column(String(200), nullable=True)
    hospital_clinic_ar = Column(String(200), nullable=True)
    prescription_date = Column(Date, nullable=False)
    
    # File information
    file_url = Column(String(500), nullable=False)
    file_name = Column(String(255), nullable=False)
    file_size = Column(Integer, nullable=False)
    
    # Status and verification
    status = Column(Enum(
        'pending', 
        'verified', 
        'rejected', 
        'filled',
        name='prescription_statuses'
    ), default='pending')
    
    # Verification details
    verification_notes = Column(Text, nullable=True)
    verification_notes_ar = Column(Text, nullable=True)
    verified_by = Column(UUID(as_uuid=True), ForeignKey('users.id'), nullable=True)
    verified_at = Column(DateTime, nullable=True)
    
    # AI extracted medications (JSON string)
    medications_extracted = Column(Text, nullable=True)  # JSON string
    
    # Status
    is_active = Column(Boolean, default=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = relationship('User', back_populates='prescriptions', foreign_keys=[user_id])
    verifier = relationship('User', foreign_keys=[verified_by])
    orders = relationship('Order', back_populates='prescription')
    
    def __repr__(self):
        return f'<Prescription {self.id} - {self.status}>'
    
    def to_dict(self, language='en'):
        """Convert prescription to dictionary with language support."""
        import json
        
        data = {
            'id': str(self.id),
            'user_id': str(self.user_id),
            'doctor_name': self.doctor_name_ar if language == 'ar' and self.doctor_name_ar else self.doctor_name,
            'doctor_license': self.doctor_license,
            'hospital_clinic': self.hospital_clinic_ar if language == 'ar' and self.hospital_clinic_ar else self.hospital_clinic,
            'prescription_date': self.prescription_date.isoformat(),
            'file_url': self.file_url,
            'file_name': self.file_name,
            'file_size': self.file_size,
            'status': self.status,
            'verification_notes': self.verification_notes_ar if language == 'ar' and self.verification_notes_ar else self.verification_notes,
            'verified_by': str(self.verified_by) if self.verified_by else None,
            'verified_at': self.verified_at.isoformat() if self.verified_at else None,
            'medications_extracted': json.loads(self.medications_extracted) if self.medications_extracted else [],
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }
        
        return data
    
    def get_status_display(self, language='en'):
        """Get human-readable status in specified language."""
        status_translations = {
            'pending': {
                'en': 'Pending Verification',
                'ar': 'في انتظار التحقق'
            },
            'verified': {
                'en': 'Verified',
                'ar': 'تم التحقق'
            },
            'rejected': {
                'en': 'Rejected',
                'ar': 'مرفوض'
            },
            'filled': {
                'en': 'Filled',
                'ar': 'تم الصرف'
            }
        }
        
        return status_translations.get(self.status, {}).get(language, self.status)
    
    def can_be_filled(self):
        """Check if prescription can be filled."""
        return self.status == 'verified' and self.is_active
    
    def is_expired(self, days_valid=30):
        """Check if prescription is expired (default 30 days)."""
        from datetime import date, timedelta
        expiry_date = self.prescription_date + timedelta(days=days_valid)
        return date.today() > expiry_date

