import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class Config:
    # Firebase Configuration
    FIREBASE_CREDENTIALS_PATH = os.getenv('FIREBASE_CREDENTIALS_PATH', 'kile-kitabu-firebase-adminsdk-pjk21-68cbd0c3b4.json')
    FIREBASE_DATABASE_URL = os.getenv('FIREBASE_DATABASE_URL', 'https://kile-kitabu-default-rtdb.firebaseio.com')
    
    # Application Configuration
    DEBUG = os.getenv('DEBUG', 'False').lower() == 'true'
    
    # Credit System Configuration
    DAILY_RATE = float(os.getenv('DAILY_RATE', '1.0'))  # Cost per day in KES
    FREE_TRIAL_DAYS = int(os.getenv('FREE_TRIAL_DAYS', '7'))  # Free trial period in days
    
    # Pesapal Configuration
    PESAPAL_CONSUMER_KEY = os.getenv('PESAPAL_CONSUMER_KEY', 'sRE8q61NY+L2TophDXPUsfF/fLZ+Wz7Z')
    PESAPAL_CONSUMER_SECRET = os.getenv('PESAPAL_CONSUMER_SECRET', 'VgLnSaRRXpuZsH69EMRH62uFmdk=')
    
    # Pesapal Environment (sandbox or production)
    PESAPAL_ENVIRONMENT = os.getenv('PESAPAL_ENVIRONMENT', 'production')  # Default to sandbox for development
    
    # Pesapal Base URLs
    PESAPAL_BASE_URL = os.getenv('PESAPAL_BASE_URL', 
        'https://cybqa.pesapal.com/pesapalv3' if PESAPAL_ENVIRONMENT == 'sandbox'
        else 'https://pay.pesapal.com/v3'
    )
    
    # Application Configuration
    BASE_URL = os.getenv('BASE_URL', 'https://kilekitabu-backend.onrender.com')
    FRONTEND_URL = os.getenv('FRONTEND_URL', 'http://localhost:3000')
    
    # IPN Configuration for Live Environment
    IPN_URL = f"{BASE_URL}/api/payment/ipn"
    CALLBACK_URL = f"{BASE_URL}/api/payment/callback"
    CANCELLATION_URL = f"{BASE_URL}/api/payment/cancel"
    
    # Database Configuration (if using database)
    DATABASE_URL = os.getenv('DATABASE_URL', 'sqlite:///kilekitabu.db')
    
    # Security Configuration
    SECRET_KEY = os.getenv('SECRET_KEY', 'your-secret-key-here')
    
    # Logging Configuration
    LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
    
    # Payment Configuration
    CURRENCY = 'KES'
    COUNTRY_CODE = 'KE'
    
    # Subscription Configuration
    DEFAULT_SUBSCRIPTION_FREQUENCY = 'MONTHLY'
    DEFAULT_SUBSCRIPTION_DURATION_DAYS = 365
    
    # Error Messages
    ERROR_MESSAGES = {
        'missing_credentials': 'Pesapal credentials not configured',
        'invalid_amount': 'Invalid payment amount',
        'payment_failed': 'Payment processing failed',
        'network_error': 'Network connection error',
        'invalid_response': 'Invalid response from payment provider',
    }
    
    # Success Messages
    SUCCESS_MESSAGES = {
        'payment_created': 'Payment request created successfully',
        'payment_completed': 'Payment completed successfully',
        'payment_cancelled': 'Payment cancelled successfully',
        'refund_requested': 'Refund request submitted successfully',
    }
    
    # Payment Status Codes
    PAYMENT_STATUS = {
        'PENDING': 'PENDING',
        'COMPLETED': 'COMPLETED',
        'FAILED': 'FAILED',
        'CANCELLED': 'CANCELLED',
        'REVERSED': 'REVERSED',
    }
    
    # Subscription Frequencies
    SUBSCRIPTION_FREQUENCIES = ['DAILY', 'WEEKLY', 'MONTHLY', 'YEARLY']
    
    # Validation Rules
    VALIDATION_RULES = {
        'min_amount': 1.0,
        'max_amount': 1000000.0,
        'phone_regex': r'^\+?254\d{9}$',  # Kenyan phone number format
        'email_regex': r'^[\w\.-]+@[\w\.-]+\.\w+$',
    }
    
    @classmethod
    def validate_config(cls):
        """Validate that all required configuration is set"""
        required_vars = [
            'PESAPAL_CONSUMER_KEY',
            'PESAPAL_CONSUMER_SECRET',
        ]
        
        missing_vars = []
        for var in required_vars:
            if not getattr(cls, var) or getattr(cls, var).startswith('your_'):
                missing_vars.append(var)
        
        if missing_vars:
            raise ValueError(f"Missing required configuration: {', '.join(missing_vars)}")
        
        return True
    
    @classmethod
    def get_pesapal_urls(cls):
        """Get Pesapal API URLs based on environment"""
        base_url = cls.PESAPAL_BASE_URL
        return {
            'auth': f"{base_url}/api/Auth/RequestToken",
            'submit_order': f"{base_url}/api/Transactions/SubmitOrderRequest",
            'get_status': f"{base_url}/api/Transactions/GetTransactionStatus",
            'register_ipn': f"{base_url}/api/URLSetup/RegisterIPN",
            'cancel_order': f"{base_url}/api/Transactions/CancelOrder",
            'refund_request': f"{base_url}/api/Transactions/RefundRequest",
        }
    
    @classmethod
    def is_sandbox(cls):
        """Check if running in sandbox mode"""
        return cls.PESAPAL_ENVIRONMENT == 'sandbox'
    
    @classmethod
    def is_production(cls):
        """Check if running in production mode"""
        return cls.PESAPAL_ENVIRONMENT == 'production' 