from flask_sqlalchemy import SQLAlchemy

# Initialize SQLAlchemy
db = SQLAlchemy()

# Import all models to ensure they are registered with SQLAlchemy
from src.models.user import User, UserAddress, UserMedicalInfo, DeviceToken
from src.models.pharmacy import User, UserAddress, UsermediaclInfo, PharmacyInfo
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

