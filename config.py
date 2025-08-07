import os
from dotenv import load_dotenv

# Load .env file if it exists
load_dotenv()

class Config:
    # Flask Configuration
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'your-secret-key-here'
    
    # Firebase Configuration
    FIREBASE_CREDENTIALS_PATH = os.environ.get('FIREBASE_CREDENTIALS_PATH') or 'kile-kitabu-firebase-adminsdk-pjk21-d2e073c9ae.json'
    FIREBASE_DATABASE_URL = os.environ.get('FIREBASE_DATABASE_URL') or 'https://kile-kitabu-default-rtdb.firebaseio.com'
    
    # App Configuration
    BASE_URL = os.environ.get('BASE_URL') or 'http://localhost:5000'
    
    # Payment Configuration
    DAILY_RATE = 5  # KSH 5 per day
    FREE_TRIAL_DAYS = 7
    
    # PesaPal Configuration
    PESAPAL_CONSUMER_KEY = os.environ.get('PESAPAL_CONSUMER_KEY')
    PESAPAL_CONSUMER_SECRET = os.environ.get('PESAPAL_CONSUMER_SECRET')
    PESAPAL_BASE_URL = os.environ.get('PESAPAL_BASE_URL') or 'https://www.pesapal.com'
    
    # App Configuration
    DEBUG = os.environ.get('FLASK_DEBUG', 'False').lower() == 'true'
    HOST = os.environ.get('HOST', '0.0.0.0')
    PORT = int(os.environ.get('PORT', 5000)) 