from flask_sqlalchemy import SQLAlchemy

# Initialize SQLAlchemy
db = SQLAlchemy()

# Import all models to ensure they are registered with SQLAlchemy
from .user import (
    db,
    User,
    UserAddress,
    UserMedicalInfo,
    PharmacyInfo,
    find_nearby_pharmacies
)
from src.models.medication import Medication, MedicationCategory, PharmacyInventory
from src.models.prescription import Prescription
from src.models.order import Order, OrderItem
from src.models.review import Review
from src.models.chat import ChatConversation, ChatMessage
from src.models.notification import Notification

__all__ = [
    'db',
    'User',
    'UserAddress', 
    'UserMedicalInfo',
    'PharmacyInfo',
    'find_nearby_pharmacies',
    'DeviceToken',
    'Pharmacy',
    'PharmacyDocument',
    'Medication',
    'MedicationCategory',
    'PharmacyInventory',
    'Prescription',
    'Order',
    'OrderItem',
    'Review',
    'ChatConversation',
    'ChatMessage',
    'Notification'
]

