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
    BASE_URL = os.getenv('BASE_URL', 'https://a48a7d70de00.ngrok-free.app')
    SECRET_KEY = os.getenv('SECRET_KEY', 'your-secret-key-here')
    CRON_SECRET_KEY = os.getenv('CRON_SECRET_KEY', SECRET_KEY)  # Defaults to SECRET_KEY if not set
    LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
    
    # Test flags
    ALLOW_UNAUTH_TEST = os.getenv('ALLOW_UNAUTH_TEST', 'False').lower() == 'true'
    FORCE_TRIAL_END = os.getenv('FORCE_TRIAL_END', 'False').lower() == 'true'
    
    # Google Pay (structure)
    GOOGLE_PAY_ENABLED = os.getenv('GOOGLE_PAY_ENABLED', 'True').lower() == 'true'
    GOOGLE_PAY_MIN_AMOUNT = float(os.getenv('GOOGLE_PAY_MIN_AMOUNT', '1.0'))
    GOOGLE_PAY_PROCESSOR = os.getenv('GOOGLE_PAY_PROCESSOR', '')  # e.g., 'cybersource', 'stripe'
    GOOGLE_PAY_CURRENCY = os.getenv('GOOGLE_PAY_CURRENCY', 'USD')
    
    # User Reset Configuration
    # Automatic reset behavior:
    # - Users without registration_date will automatically get a fresh 14-day trial on login
    # - If RESET_USERS_ON_LOGIN=True, ALL users (including those with registration_date) will get reset on login
    # - This ensures all users (existing and new) get a fresh trial period
    TRIAL_RESET_DATE = os.getenv('TRIAL_RESET_DATE', '')  # e.g., '2024-01-15' or empty to disable (legacy)
    RESET_USERS_ON_LOGIN = os.getenv('RESET_USERS_ON_LOGIN', 'True').lower() == 'true'  # Enable automatic reset on login (default: True)
    
    # Subscription Configuration
    DAILY_RATE = float(os.getenv('DAILY_RATE', '5.0'))  # Cost per day in KES
    FREE_TRIAL_DAYS = int(os.getenv('FREE_TRIAL_DAYS', '14'))  # Free trial period in days
    MONTHLY_CAP_KES = float(os.getenv('MONTHLY_CAP_KES', '150'))  # Monthly cap in KES
    MAX_PREPAY_MONTHS = int(os.getenv('MAX_PREPAY_MONTHS', '12'))  # Allow paying up to N months in advance
    
    # M-Pesa Daraja Configuration
    # HARDCODED FOR PRODUCTION
    MPESA_ENV = 'production'  # Hardcoded to production
    MPESA_CONSUMER_KEY = 'rs7K6PTbaAzDFIcmkK0Rcg8u6GphrzUTAwfpuyd4DeSv43Og'  # Production Consumer Key
    MPESA_CONSUMER_SECRET = 'xshsALdAGkdfwjxALLBZCI7udGWB8dDSAubXs6tbbbUABvxqwfPuXml0hb7cbUYV'  # Production Consumer Secret
    MPESA_SHORT_CODE = '3576603'  # Production BusinessShortCode (Go Live shortcode)
    MPESA_TILL_NUMBER = '5695092'  # Production Till Number (PartyB)
    MPESA_PASSKEY = 'bcfeb194a2df8ca55f17c2816a55234c837516ce016dcade10621ce0ffc9e84d'  # Production passkey
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
