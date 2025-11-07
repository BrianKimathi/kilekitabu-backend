"""Configuration settings for KileKitabu backend."""
import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    """Application configuration."""
    
    # Firebase Configuration
    FIREBASE_CREDENTIALS_PATH = os.getenv(
        'FIREBASE_CREDENTIALS_PATH',
        'kile-kitabu-firebase-adminsdk-pjk21-68cbd0c3b4.json'
    )
    FIREBASE_DATABASE_URL = os.getenv(
        'FIREBASE_DATABASE_URL',
        'https://kile-kitabu-default-rtdb.firebaseio.com'
    )
    
    # Application Configuration
    DEBUG = os.getenv('DEBUG', 'False').lower() == 'true'
    BASE_URL = os.getenv('BASE_URL', 'https://9c390d019f26.ngrok-free.app')
    SECRET_KEY = os.getenv('SECRET_KEY', 'your-secret-key-here')
    CRON_SECRET_KEY = os.getenv('CRON_SECRET_KEY', SECRET_KEY)  # Defaults to SECRET_KEY if not set
    LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
    
    # Test flags
    ALLOW_UNAUTH_TEST = os.getenv('ALLOW_UNAUTH_TEST', 'False').lower() == 'true'
    FORCE_TRIAL_END = os.getenv('FORCE_TRIAL_END', 'False').lower() == 'true'
    
    # Subscription Configuration
    DAILY_RATE = float(os.getenv('DAILY_RATE', '5.0'))  # Cost per day in KES
    FREE_TRIAL_DAYS = int(os.getenv('FREE_TRIAL_DAYS', '14'))  # Free trial period in days
    MONTHLY_CAP_KES = float(os.getenv('MONTHLY_CAP_KES', '150'))  # Monthly cap in KES
    
    # M-Pesa Daraja Configuration
    MPESA_ENV = os.getenv('MPESA_ENV', 'sandbox')  # sandbox | production
    MPESA_CONSUMER_KEY = os.getenv('MPESA_CONSUMER_KEY', '')
    MPESA_CONSUMER_SECRET = os.getenv('MPESA_CONSUMER_SECRET', '')
    MPESA_SHORT_CODE = os.getenv('MPESA_SHORT_CODE', '174379')
    MPESA_PASSKEY = os.getenv('MPESA_PASSKEY', 'bfb279f9aa9bdbcf158e97dd71a467cd2e0c893059b10f78e6b72ada1ed2c919')
    MPESA_CALLBACK_URL = f"{BASE_URL}/api/mpesa/callback"
    
    # CyberSource Configuration
    CYBERSOURCE_ENV = os.getenv('CYBERSOURCE_ENV', 'sandbox')  # sandbox | production
    CYBERSOURCE_MERCHANT_ID = os.getenv('CYBERSOURCE_MERCHANT_ID', '')
    CYBERSOURCE_API_KEY_ID = os.getenv('CYBERSOURCE_API_KEY_ID', '')
    CYBERSOURCE_SECRET_KEY = os.getenv('CYBERSOURCE_SECRET_KEY', '')
    CYBERSOURCE_WEBHOOK_SECRET = os.getenv('CYBERSOURCE_WEBHOOK_SECRET', '')  # For signature validation
    
    # CyberSource API URLs
    CYBERSOURCE_API_BASE = (
        'https://apitest.cybersource.com' if CYBERSOURCE_ENV == 'sandbox' 
        else 'https://api.cybersource.com'
    )
    CYBERSOURCE_CALLBACK_URL = os.getenv(
        'CYBERSOURCE_CALLBACK_URL',
        f"{BASE_URL}/api/cybersource/webhook"
    )
    
    # Validation Rules
    VALIDATION_RULES = {
        'min_amount': 10.0,
        'max_amount': 1000000.0,
        'phone_regex': r'^\+?254\d{9}$',
        'email_regex': r'^[\w\.-]+@[\w\.-]+\.\w+$',
    }
    
    # Payment Status Codes
    PAYMENT_STATUS = {
        'PENDING': 'PENDING',
        'COMPLETED': 'COMPLETED',
        'FAILED': 'FAILED',
        'CANCELLED': 'CANCELLED',
    }
