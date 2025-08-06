from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate

# Initialize database
db = SQLAlchemy()
migrate = Migrate()

# Import all models to ensure they're registered with SQLAlchemy
from .user import User
from .pharmacy import Pharmacy
from .category import Category
from .product import Product
from .order import Order, OrderItem
from .chat import Conversation, Message, ChatParticipant
from .review import Review
from .notification import Notification
from .favorite import UserFavorite

# Export all models for easy importing
__all__ = [
    'db',
    'migrate',
    'User',
    'Pharmacy',
    'Category', 
    'Product',
    'Order',
    'OrderItem',
    'Conversation',
    'Message',
    'ChatParticipant',
    'Review',
    'Notification',
    'UserFavorite'
]

