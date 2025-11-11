"""Main application entry point for KileKitabu backend."""
import os
import firebase_admin
from firebase_admin import credentials
from core.app_factory import create_app
from core.logging_config import init_logging
from config import Config
from services.mpesa_integration import MpesaClient
from services.cybersource_integration import CyberSourceClient
from services.fcm_v1_service import FCMV1Service, MockFCMV1Service
from services.simple_debt_scheduler import SimpleDebtScheduler
from services.low_credit_scheduler import LowCreditScheduler
from services.debt_reminder_scheduler import DebtReminderScheduler
from services.keep_alive_scheduler import KeepAliveScheduler
from services.sms_reminder_scheduler import initialize_sms_scheduler, get_sms_scheduler
from routes.health import bp as health_bp
from routes.notifications import bp as notifications_bp
from routes.payment import bp as payment_bp
from routes.config_info import bp as config_info_bp
from routes.subscription import bp as subscription_bp
from routes.cybersource import cybersource_bp
from routes.cron import bp as cron_bp

# Initialize logging
init_logging()

# Create Flask app
app = create_app(Config)

# Initialize Firebase Admin SDK
db = None
try:
    try:
        firebase_admin.get_app()
        from firebase_admin import db
        print("Firebase already initialized")
    except ValueError:
        if os.path.exists(Config.FIREBASE_CREDENTIALS_PATH):
            cred = credentials.Certificate(Config.FIREBASE_CREDENTIALS_PATH)
            firebase_admin.initialize_app(cred, {
                'databaseURL': Config.FIREBASE_DATABASE_URL
            })
            from firebase_admin import db
            print("Firebase initialized successfully")
        else:
            print(f"Firebase credentials not found: {Config.FIREBASE_CREDENTIALS_PATH}")
except Exception as e:
    print(f"Firebase initialization error: {e}")

# Mock Firebase service classes (defined at top-level to avoid indentation issues)
class MockFirebaseService:
    def __init__(self):
        self.data = {}
    
    def reference(self, path):
        return MockFirebaseReference(path, self.data)


class MockFirebaseReference:
    def __init__(self, path, data_store):
        self.path = path
        self.data_store = data_store
    
    def set(self, value):
        self.data_store[self.path] = value
        return self
    
    def get(self):
        if self.path in self.data_store:
            return self.data_store[self.path]
        nested_data = {}
        for key, value in self.data_store.items():
            if key.startswith(self.path + '/'):
                nested_key = key[len(self.path) + 1:]
                nested_data[nested_key] = value
        return nested_data if nested_data else None
    
    def update(self, value):
        if self.path in self.data_store:
            self.data_store[self.path].update(value)
        return self


# Fallback to mock service when Firebase DB is unavailable
if db is None:
    db = MockFirebaseService()
    print("Using mock Firebase service")

# Initialize M-Pesa Client
mpesa_client = None
try:
    print(f"[App Init] Checking M-Pesa configuration...")
    print(f"[App Init] MPESA_CONSUMER_KEY: {'SET' if Config.MPESA_CONSUMER_KEY else 'NOT SET'}")
    print(f"[App Init] MPESA_CONSUMER_SECRET: {'SET' if Config.MPESA_CONSUMER_SECRET else 'NOT SET'}")
    print(f"[App Init] MPESA_SHORT_CODE: {Config.MPESA_SHORT_CODE}")
    print(f"[App Init] MPESA_PASSKEY: {'SET' if Config.MPESA_PASSKEY else 'NOT SET'} (length: {len(Config.MPESA_PASSKEY) if Config.MPESA_PASSKEY else 0}, preview: {Config.MPESA_PASSKEY[:20] if Config.MPESA_PASSKEY else 'N/A'}...)")
    print(f"[App Init] MPESA_CALLBACK_URL: {Config.MPESA_CALLBACK_URL}")
    print(f"[App Init] MPESA_ENV: {Config.MPESA_ENV}")
    
    if all([
        Config.MPESA_CONSUMER_KEY,
        Config.MPESA_CONSUMER_SECRET,
        Config.MPESA_SHORT_CODE,
        Config.MPESA_PASSKEY,
    ]):
        mpesa_client = MpesaClient(
            consumer_key=Config.MPESA_CONSUMER_KEY,
            consumer_secret=Config.MPESA_CONSUMER_SECRET,
            short_code=Config.MPESA_SHORT_CODE,
            passkey=Config.MPESA_PASSKEY,
            callback_url=Config.MPESA_CALLBACK_URL,
            env=Config.MPESA_ENV,
        )
        print("✅ M-Pesa client initialized successfully")
    else:
        missing = []
        if not Config.MPESA_CONSUMER_KEY:
            missing.append("MPESA_CONSUMER_KEY")
        if not Config.MPESA_CONSUMER_SECRET:
            missing.append("MPESA_CONSUMER_SECRET")
        if not Config.MPESA_SHORT_CODE:
            missing.append("MPESA_SHORT_CODE")
        if not Config.MPESA_PASSKEY:
            missing.append("MPESA_PASSKEY")
        print(f"❌ M-Pesa not configured; missing: {', '.join(missing)}")
except Exception as e:
    print(f"❌ M-Pesa initialization error: {e}")
    import traceback
    print(f"Traceback: {traceback.format_exc()}")

# Initialize CyberSource Client
cybersource_client = None
try:
    print(f"[App Init] Checking CyberSource configuration...")
    print(f"[App Init] CYBERSOURCE_MERCHANT_ID: {'SET' if Config.CYBERSOURCE_MERCHANT_ID else 'NOT SET'}")
    print(f"[App Init] CYBERSOURCE_API_KEY_ID: {'SET' if Config.CYBERSOURCE_API_KEY_ID else 'NOT SET'}")
    print(f"[App Init] CYBERSOURCE_SECRET_KEY: {'SET' if Config.CYBERSOURCE_SECRET_KEY else 'NOT SET'}")
    print(f"[App Init] CYBERSOURCE_ENV: {Config.CYBERSOURCE_ENV}")
    print(f"[App Init] CYBERSOURCE_API_BASE: {Config.CYBERSOURCE_API_BASE}")
    
    if all([
        Config.CYBERSOURCE_MERCHANT_ID,
        Config.CYBERSOURCE_API_KEY_ID,
        Config.CYBERSOURCE_SECRET_KEY,
    ]):
        cybersource_client = CyberSourceClient(
            merchant_id=Config.CYBERSOURCE_MERCHANT_ID,
            api_key_id=Config.CYBERSOURCE_API_KEY_ID,
            secret_key=Config.CYBERSOURCE_SECRET_KEY,
            api_base=Config.CYBERSOURCE_API_BASE,
        )
        print("✅ CyberSource client initialized successfully")
    else:
        missing = []
        if not Config.CYBERSOURCE_MERCHANT_ID:
            missing.append("CYBERSOURCE_MERCHANT_ID")
        if not Config.CYBERSOURCE_API_KEY_ID:
            missing.append("CYBERSOURCE_API_KEY_ID")
        if not Config.CYBERSOURCE_SECRET_KEY:
            missing.append("CYBERSOURCE_SECRET_KEY")
        print(f"❌ CyberSource not configured; missing: {', '.join(missing)}")
except Exception as e:
    print(f"❌ CyberSource initialization error: {e}")
    import traceback
    print(f"Traceback: {traceback.format_exc()}")

# Initialize FCM Service and Schedulers
fcm_service = None
notification_scheduler = None
if db is not None:
    try:
        project_id = os.getenv('FIREBASE_PROJECT_ID', 'kile-kitabu')
        credentials_path = os.getenv(
            'FIREBASE_CREDENTIALS_PATH',
            'kile-kitabu-firebase-adminsdk-pjk21-68cbd0c3b4.json'
        )
        if os.path.exists(credentials_path):
            fcm_service = FCMV1Service(credentials_path, project_id)
        else:
            fcm_service = MockFCMV1Service()
        
        notification_scheduler = SimpleDebtScheduler(fcm_service)
        notification_scheduler.start_scheduler()
        print("FCM service and notification scheduler initialized")
        
        # Initialize low credit notification scheduler (8:00 AM daily)
        low_credit_scheduler = LowCreditScheduler(fcm_service)
        low_credit_scheduler.start_scheduler()
        print("Low credit notification scheduler initialized (8:00 AM daily)")
        
        # Initialize debt reminder scheduler (9:00 AM daily - debts due in 3 days, 1 day)
        debt_reminder_scheduler = DebtReminderScheduler(fcm_service)
        debt_reminder_scheduler.start_scheduler()
        print("Debt reminder scheduler initialized (9:00 AM daily - 3 days & 1 day reminders)")
        
        sms_api_key = os.getenv('SMS_API_KEY')
        initialize_sms_scheduler(db, sms_api_key, fcm_service)
        print("SMS reminder scheduler initialized")
        
        # Initialize keep-alive scheduler to prevent Render.com spin-down
        base_url = Config.BASE_URL
        if base_url:
            keep_alive_scheduler = KeepAliveScheduler(base_url)
            keep_alive_scheduler.start_scheduler()
            print(f"Keep-alive scheduler initialized (pings every 7 minutes: {base_url}/api/health/keep-alive)")
        else:
            print("⚠️ BASE_URL not set - keep-alive scheduler not started")
    except Exception as e:
        print(f"FCM initialization error: {e}")

# Configure app with services
app.config['DB'] = db
app.config['CONFIG'] = Config
app.config['FCM_SERVICE'] = fcm_service
app.config['MPESA_CLIENT'] = mpesa_client
app.config['cybersource_client'] = cybersource_client
app.config['GET_SMS_SCHEDULER'] = get_sms_scheduler

# Register blueprints
app.register_blueprint(health_bp)
app.register_blueprint(notifications_bp)
app.register_blueprint(payment_bp)
app.register_blueprint(subscription_bp)
app.register_blueprint(config_info_bp)
app.register_blueprint(cybersource_bp)
app.register_blueprint(cron_bp)

# Health check endpoint
@app.route('/', methods=['GET'])
def health_check():
    """Root health check endpoint."""
    return {
        'status': 'healthy',
        'service': 'KileKitabu Backend',
        'version': '1.0.0'
    }


if __name__ == '__main__':
    app.run(debug=Config.DEBUG, host='0.0.0.0', port=5000)
