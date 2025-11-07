"""
Low Credit Notification Scheduler
Sends daily notifications at 8 AM to users with credits <= 2
"""
import logging
import threading
import time
from datetime import datetime
from firebase_admin import db

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class LowCreditScheduler:
    """Scheduler for low credit notifications"""
    
    def __init__(self, fcm_service):
        self.fcm_service = fcm_service
        self.db = db.reference()
        self.running = False
        self.thread = None
        self.last_check_date = None
    
    def start_scheduler(self):
        """Start the low credit notification scheduler"""
        if self.running:
            logger.warning("Low credit scheduler is already running")
            return
        
        logger.info("🚀 Starting low credit notification scheduler...")
        self.running = True
        self.thread = threading.Thread(target=self._run_scheduler, daemon=True)
        self.thread.start()
        logger.info("✅ Low credit notification scheduler started successfully")
        logger.info("📅 Scheduled check: 8:00 AM daily")
    
    def stop_scheduler(self):
        """Stop the low credit notification scheduler"""
        self.running = False
        if self.thread:
            self.thread.join(timeout=5)
        logger.info("Low credit notification scheduler stopped")
    
    def _run_scheduler(self):
        """Main scheduler loop - checks every minute"""
        while self.running:
            try:
                current_time = datetime.now()
                
                # Check if it's time for daily low credit check (8:00 AM)
                if current_time.hour == 8 and current_time.minute == 0:
                    # Only run once per day
                    today = current_time.date()
                    if self.last_check_date != today:
                        self.check_low_credits()
                        self.last_check_date = today
                
                # Sleep for 1 minute before next check
                time.sleep(60)
                
            except Exception as e:
                logger.error(f"Error in low credit scheduler loop: {e}")
                time.sleep(60)  # Sleep for 1 minute before retrying
    
    def check_low_credits(self):
        """Check for users with credits <= 2 and send notifications"""
        logger.info("🔍 Checking for users with low credits (<= 2)...")
        
        try:
            # Get all users with FCM tokens
            fcm_tokens_ref = self.db.child('fcm_tokens')
            fcm_tokens = fcm_tokens_ref.get()
            
            if not fcm_tokens:
                logger.info("No FCM tokens found")
                return
            
            # Get all registered users
            users_ref = self.db.child('registeredUser')
            users = users_ref.get()
            
            if not users:
                logger.info("No registered users found")
                return
            
            notifications_sent = 0
            users_notified = []
            
            for user_id, fcm_token in fcm_tokens.items():
                if not fcm_token:
                    continue
                
                # Get user's credit balance
                user_data = users.get(user_id)
                if not user_data:
                    continue
                
                credit_balance = user_data.get('credit_balance', 0)
                
                # Check if credits are <= 2
                try:
                    credit_balance = float(credit_balance) if credit_balance else 0.0
                except (ValueError, TypeError):
                    credit_balance = 0.0
                
                if credit_balance <= 2:
                    # Send low credit notification
                    success = self._send_low_credit_notification(
                        fcm_token, user_id, credit_balance
                    )
                    if success:
                        notifications_sent += 1
                        users_notified.append(user_id)
                        logger.info(f"✅ Sent low credit notification to user {user_id} (credits: {credit_balance})")
            
            logger.info(f"📤 Sent {notifications_sent} low credit notifications to users: {users_notified}")
            
        except Exception as e:
            logger.error(f"❌ Error checking low credits: {e}")
            import traceback
            logger.error(traceback.format_exc())
    
    def _send_low_credit_notification(self, fcm_token, user_id, credit_balance):
        """Send low credit notification to a user"""
        try:
            # Determine message based on credit balance
            if credit_balance == 0:
                title = "⚠️ No Credits Remaining"
                body = "Your account has no credits. Please add credits to continue using KileKitabu."
            elif credit_balance == 1:
                title = "⚠️ Low Credits: 1 Day Remaining"
                body = "You have only 1 credit remaining. Add credits now to avoid service interruption."
            else:
                title = "⚠️ Low Credits: 2 Days Remaining"
                body = "You have only 2 credits remaining. Add credits now to continue using KileKitabu."
            
            # Prepare notification data
            notification_data = {
                "type": "low_credit",
                "user_id": user_id,
                "credit_balance": str(credit_balance),
                "timestamp": str(int(time.time())),
                "notification_type": "low_credit_alert",
                "click_action": "com.jeff.kilekitabu.PAYMENT"
            }
            
            # Send notification using FCM service
            success = self.fcm_service.send_notification(
                fcm_token, title, body, notification_data
            )
            
            return success
            
        except Exception as e:
            logger.error(f"❌ Error sending low credit notification to user {user_id}: {e}")
            return False

