import os
from datetime import timedelta
from dotenv import load_dotenv

load_dotenv()

class Config:
    """Base configuration class"""
    
    # Basic Flask Configuration
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dawaksahl-super-secret-key-2025'
    
    # Database configuration
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or f"sqlite:///{os.path.join(os.path.dirname(__file__), 'database', 'app.db')}"
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_pre_ping': True,
        'pool_recycle': 300,
    }
    
    # JWT Configuration
    JWT_SECRET_KEY = os.environ.get('JWT_SECRET_KEY') or 'jwt-secret-string'
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(hours=24)
    JWT_REFRESH_TOKEN_EXPIRES = timedelta(days=30)
    JWT_ALGORITHM = 'HS256'
    
    # CORS Configuration
    CORS_ORIGINS = ['*']  # Allow all origins for development
    
    # Email Configuration (SendGrid)
    SENDGRID_API_KEY = os.environ.get('SENDGRID_API_KEY')
    SENDGRID_FROM_EMAIL = os.environ.get('SENDGRID_FROM_EMAIL') or 'noreply@dawaksahl.com'
    SENDGRID_FROM_NAME = os.environ.get('SENDGRID_FROM_NAME') or 'DawakSahl'
    
    # File Upload Configuration
    UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'uploads')
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max file size
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'pdf', 'doc', 'docx', 'csv', 'xlsx'}
    
    # API Configuration
    API_PREFIX = '/api/v1'
    API_TITLE = 'DawakSahl API'
    API_VERSION = '1.0.0'
    
    # Pagination
    DEFAULT_PAGE_SIZE = 20
    MAX_PAGE_SIZE = 100
    
    # Rate Limiting
    RATELIMIT_STORAGE_URL = os.environ.get('REDIS_URL') or 'memory://'
    
    # Logging
    LOG_LEVEL = 'INFO'
    LOG_FILE = 'dawaksahl.log'
    
    # Application Settings
    APP_NAME = 'DawakSahl'
    APP_VERSION = '1.0.0'
    TIMEZONE = 'Asia/Aden'
    DEFAULT_LANGUAGE = 'ar'
    SUPPORTED_LANGUAGES = ['ar', 'en']
    
    # Security Settings
    PASSWORD_MIN_LENGTH = 8
    PASSWORD_REQUIRE_UPPERCASE = True
    PASSWORD_REQUIRE_LOWERCASE = True
    PASSWORD_REQUIRE_NUMBERS = True
    PASSWORD_REQUIRE_SPECIAL = False
    
    # Email Verification
    EMAIL_VERIFICATION_REQUIRED = True
    EMAIL_VERIFICATION_TOKEN_EXPIRES = timedelta(hours=24)
    
    # Password Reset
    PASSWORD_RESET_TOKEN_EXPIRES = timedelta(hours=1)
    
    # Chat Configuration
    CHAT_MESSAGE_MAX_LENGTH = 1000
    CHAT_FILE_MAX_SIZE = 5 * 1024 * 1024  # 5MB
    CHAT_ALLOWED_FILE_TYPES = {'png', 'jpg', 'jpeg', 'gif', 'pdf', 'doc', 'docx'}
    
    # Business Rules
    ORDER_EXPIRY_HOURS = 24
    PRESCRIPTION_EXPIRY_DAYS = 30
    REVIEW_COOLDOWN_HOURS = 24
    
    @staticmethod
    def init_app(app):
        """Initialize app with configuration"""
        pass

class DevelopmentConfig(Config):
    """Development configuration."""
    DEBUG = True
    TESTING = False

class ProductionConfig(Config):
    """Production configuration."""
    DEBUG = False
    TESTING = False
    
    # Use PostgreSQL in production
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'postgresql://user:password@localhost/dawaksahl'
    
    # Stricter security in production
    SESSION_COOKIE_SECURE = True
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'

class TestingConfig(Config):
    """Testing configuration."""
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(days=7)
    WTF_CSRF_ENABLED = False

# Configuration dictionary
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}

# Helper functions
def get_config():
    """Get current configuration"""
    return config[os.environ.get('FLASK_ENV', 'development')]

def is_development():
    """Check if running in development mode"""
    return os.environ.get('FLASK_ENV', 'development') == 'development'

def is_production():
    """Check if running in production mode"""
    return os.environ.get('FLASK_ENV', 'development') == 'production'

