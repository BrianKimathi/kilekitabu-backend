import logging
import threading
import time
from datetime import datetime, timedelta
from firebase_admin import db

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SimpleDebtScheduler:
    def __init__(self, fcm_service):
        self.fcm_service = fcm_service
        self.db = db.reference()
        self.running = False
        self.thread = None
    
    def start_scheduler(self):
        """Start the notification scheduler using simple threading"""
        if self.running:
            logger.warning("Scheduler is already running")
            return
        
        logger.info("Starting simple debt notification scheduler...")
        self.running = True
        self.thread = threading.Thread(target=self._run_scheduler, daemon=True)
        self.thread.start()
        logger.info("Simple debt notification scheduler started successfully")
    
    def stop_scheduler(self):
        """Stop the notification scheduler"""
        self.running = False
        if self.thread:
            self.thread.join(timeout=5)
        logger.info("Simple debt notification scheduler stopped")
    
    def _run_scheduler(self):
        """Main scheduler loop"""
        while self.running:
            try:
                current_time = datetime.now()
                
                # Check if it's time for daily debt check (9:00 AM)
                if current_time.hour == 9 and current_time.minute == 0:
                    self.check_due_debts()
                
                # Check if it's time for overdue debt check (10:00 AM every 3 days)
                elif current_time.hour == 10 and current_time.minute == 0:
                    if current_time.day % 3 == 0:  # Every 3rd day
                        self.check_overdue_debts()
                
                # Check if it's time for weekly reminders (Monday 11:00 AM)
                elif (current_time.weekday() == 0 and  # Monday
                      current_time.hour == 11 and current_time.minute == 0):
                    self.send_weekly_reminders()
                
                # Sleep for 1 minute before next check
                time.sleep(60)
                
            except Exception as e:
                logger.error(f"Error in scheduler loop: {e}")
                time.sleep(60)  # Sleep for 1 minute before retrying
    
    def check_due_debts(self):
        """Check for debts due today and send consolidated notifications"""
        logger.info("Checking for debts due today...")
        
        try:
            today = datetime.now().date()
            today_str = today.strftime('%Y-%m-%d')
            
            # Get all users with FCM tokens
            fcm_tokens_ref = self.db.child('fcm_tokens')
            fcm_tokens = fcm_tokens_ref.get()
            
            if not fcm_tokens:
                logger.info("No FCM tokens found")
                return
            
            # Get all user debts
            user_debts_ref = self.db.child('UserDebts')
            user_debts = user_debts_ref.get()
            
            if not user_debts:
                logger.info("No user debts found")
                return
            
            notifications_sent = 0
            
            for user_id, fcm_token in fcm_tokens.items():
                if not fcm_token:
                    continue
                
                # Get user's debts
                user_debts_data = user_debts.get(user_id)
                if not user_debts_data:
                    continue
                
                # Collect all due debts for this user
                due_debts = []
                total_amount = 0.0
                
                for phone_number, debtor_data in user_debts_data.items():
                    if phone_number == 'metadata':
                        continue
                    
                    debts = debtor_data.get('debts', {})
                    if not debts:
                        continue
                    
                    for debt_id, debt in debts.items():
                        if debt.get('isComplete', False):
                            continue
                        
                        debt_date = debt.get('date', '')
                        if not debt_date:
                            continue
                        
                        # Check if debt is due today
                        try:
                            debt_date_obj = datetime.strptime(debt_date, '%Y-%m-%d').date()
                            if debt_date_obj == today:
                                debt_info = {
                                    'id': debt_id,
                                    'account_name': debtor_data.get('accountName', 'Unknown'),
                                    'account_phone': phone_number,
                                    'amount': debt.get('debtAmount', '0'),
                                    'due_date': debt_date,
                                    'description': debt.get('description', '')
                                }
                                due_debts.append(debt_info)
                                
                                # Add to total amount
                                try:
                                    amount = float(debt.get('debtAmount', '0'))
                                    total_amount += amount
                                except ValueError:
                                    pass
                                
                        except ValueError as e:
                            logger.warning(f"Invalid date format for debt {debt_id}: {debt_date}")
                            continue
                
                # Send consolidated notification if there are due debts
                if due_debts:
                    success = self._send_consolidated_due_notification(
                        fcm_token, user_id, due_debts, total_amount
                    )
                    if success:
                        notifications_sent += 1
                        logger.info(f"Sent consolidated due debt notification for {len(due_debts)} debts to user {user_id}")
            
            logger.info(f"Sent {notifications_sent} consolidated debt due notifications")
            
        except Exception as e:
            logger.error(f"Error checking due debts: {e}")
    
    def _send_consolidated_due_notification(self, fcm_token, user_id, due_debts, total_amount):
        """Send a consolidated notification for all due debts"""
        try:
            from fcm_v1_service import FCMV1Service, MockFCMV1Service
            import os
            
            # Get project ID from environment or config
            project_id = os.getenv('FIREBASE_PROJECT_ID', 'kile-kitabu')
            credentials_path = os.getenv('FIREBASE_CREDENTIALS_PATH', 'kile-kitabu-firebase-adminsdk-pjk21-68cbd0c3b4.json')
            
            # Check if credentials file exists
            if os.path.exists(credentials_path):
                fcm_service = FCMV1Service(credentials_path, project_id)
            else:
                fcm_service = MockFCMV1Service()
            
            # Create notification content based on number of debts
            if len(due_debts) == 1:
                debt = due_debts[0]
                title = "Debt Due Today!"
                body = f"Debt from {debt['account_name']} is due today. Amount: KSh {debt['amount']}"
            else:
                title = f"You have {len(due_debts)} debts due today!"
                body = f"Total amount due: KSh {total_amount:,.2f}. Tap to view details."
            
            # Prepare debt data for the notification
            debt_data = {
                "type": "debt_due_consolidated",
                "user_id": user_id,
                "timestamp": str(int(time.time())),
                "notification_type": "debt_due",
                "debt_count": str(len(due_debts)),
                "total_amount": str(total_amount),
                "due_date": datetime.now().date().strftime('%Y-%m-%d'),
                "debts": due_debts  # Include all debt details
            }
            
            success = fcm_service.send_notification(fcm_token, title, body, debt_data)
            return success
            
        except Exception as e:
            logger.error(f"Error sending consolidated due notification: {e}")
            return False
    
    def check_overdue_debts(self):
        """Check for overdue debts and send reminder notifications"""
        logger.info("Checking for overdue debts...")
        
        try:
            today = datetime.now().date()
            
            # Get all users with FCM tokens
            fcm_tokens_ref = self.db.child('fcm_tokens')
            fcm_tokens = fcm_tokens_ref.get()
            
            if not fcm_tokens:
                logger.info("No FCM tokens found")
                return
            
            # Get all user debts
            user_debts_ref = self.db.child('UserDebts')
            user_debts = user_debts_ref.get()
            
            if not user_debts:
                logger.info("No user debts found")
                return
            
            notifications_sent = 0
            
            for user_id, fcm_token in fcm_tokens.items():
                if not fcm_token:
                    continue
                
                # Get user's debts
                user_debts_data = user_debts.get(user_id)
                if not user_debts_data:
                    continue
                
                for phone_number, debtor_data in user_debts_data.items():
                    if phone_number == 'metadata':
                        continue
                    
                    debts = debtor_data.get('debts', {})
                    if not debts:
                        continue
                    
                    for debt_id, debt in debts.items():
                        if debt.get('isComplete', False):
                            continue
                        
                        debt_date = debt.get('date', '')
                        if not debt_date:
                            continue
                        
                        # Check if debt is overdue
                        try:
                            debt_date_obj = datetime.strptime(debt_date, '%Y-%m-%d').date()
                            if debt_date_obj < today:
                                days_overdue = (today - debt_date_obj).days
                                
                                # Send notification
                                debt_data = {
                                    'id': debt_id,
                                    'account_name': debtor_data.get('accountName', 'Unknown'),
                                    'account_phone': phone_number,
                                    'amount': debt.get('debtAmount', '0'),
                                    'due_date': debt_date
                                }
                                
                                success = self.fcm_service.send_payment_reminder_notification(
                                    fcm_token, debt_data, days_overdue
                                )
                                if success:
                                    notifications_sent += 1
                                    logger.info(f"Sent overdue notification for debt {debt_id} ({days_overdue} days overdue)")
                                
                        except ValueError as e:
                            logger.warning(f"Invalid date format for debt {debt_id}: {debt_date}")
                            continue
            
            logger.info(f"Sent {notifications_sent} overdue debt notifications")
            
        except Exception as e:
            logger.error(f"Error checking overdue debts: {e}")
    
    def send_weekly_reminders(self):
        """Send weekly payment reminders for all active debts"""
        logger.info("Sending weekly payment reminders...")
        
        try:
            # Get all users with FCM tokens
            fcm_tokens_ref = self.db.child('fcm_tokens')
            fcm_tokens = fcm_tokens_ref.get()
            
            if not fcm_tokens:
                logger.info("No FCM tokens found")
                return
            
            # Get all user debts
            user_debts_ref = self.db.child('UserDebts')
            user_debts = user_debts_ref.get()
            
            if not user_debts:
                logger.info("No user debts found")
                return
            
            notifications_sent = 0
            
            for user_id, fcm_token in fcm_tokens.items():
                if not fcm_token:
                    continue
                
                # Get user's debts
                user_debts_data = user_debts.get(user_id)
                if not user_debts_data:
                    continue
                
                total_debts = 0
                total_amount = 0.0
                
                for phone_number, debtor_data in user_debts_data.items():
                    if phone_number == 'metadata':
                        continue
                    
                    debts = debtor_data.get('debts', {})
                    if not debts:
                        continue
                    
                    for debt_id, debt in debts.items():
                        if not debt.get('isComplete', False):
                            total_debts += 1
                            try:
                                amount = float(debt.get('debtAmount', '0'))
                                total_amount += amount
                            except ValueError:
                                continue
                
                if total_debts > 0:
                    # Send weekly summary notification
                    from firebase_admin import messaging
                    
                    notification = messaging.Notification(
                        title="📊 Weekly Debt Summary",
                        body=f"You have {total_debts} active debts totaling KSh {total_amount:,.2f}"
                    )
                    
                    data = {
                        "type": "weekly_summary",
                        "total_debts": str(total_debts),
                        "total_amount": str(total_amount),
                        "click_action": "com.jeff.kilekitabu.DEBT_NOTIFICATION"
                    }
                    
                    android_config = messaging.AndroidConfig(
                        priority=messaging.AndroidConfig.Priority.DEFAULT,
                        notification=messaging.AndroidNotification(
                            icon="ic_notification",
                            color="#2196F3",
                            sound="default",
                            click_action="com.jeff.kilekitabu.DEBT_NOTIFICATION"
                        )
                    )
                    
                    message = messaging.Message(
                        notification=notification,
                        data=data,
                        android=android_config,
                        token=fcm_token
                    )
                    
                    try:
                        response = messaging.send(message)
                        notifications_sent += 1
                        logger.info(f"Sent weekly summary to user {user_id}")
                    except Exception as e:
                        logger.error(f"Error sending weekly summary to user {user_id}: {e}")
            
            logger.info(f"Sent {notifications_sent} weekly reminder notifications")
            
        except Exception as e:
            logger.error(f"Error sending weekly reminders: {e}")
    
    def send_manual_notification(self, user_id, title, body, data=None):
        """Send a manual notification to a specific user using FCM v1 API"""
        try:
            print(f"🔍 Looking for FCM token for user: {user_id}")
            fcm_tokens_ref = self.db.child('fcm_tokens')
            fcm_token = fcm_tokens_ref.child(user_id).get()
            
            print(f"🔑 FCM token found: {fcm_token}")
            
            if not fcm_token:
                logger.warning(f"No FCM token found for user {user_id}")
                print(f"❌ No FCM token found for user {user_id}")
                return False
            
            print("📦 Using FCM v1 API...")
            try:
                from fcm_v1_service import FCMV1Service, MockFCMV1Service
                import os
                
                # Get project ID from environment or config
                project_id = os.getenv('FIREBASE_PROJECT_ID', 'kile-kitabu')
                credentials_path = os.getenv('FIREBASE_CREDENTIALS_PATH', 'kile-kitabu-firebase-adminsdk-pjk21-68cbd0c3b4.json')
                
                # Check if credentials file exists
                if os.path.exists(credentials_path):
                    fcm_service = FCMV1Service(credentials_path, project_id)
                    print("✅ FCM v1 service initialized with real credentials")
                else:
                    fcm_service = MockFCMV1Service()
                    print("🔧 FCM v1 service initialized in mock mode")
                
                print("📤 Sending notification via FCM v1...")
                # Include debt data in the notification
                enhanced_data = data or {}
                enhanced_data.update({
                    "user_id": user_id,
                    "timestamp": str(int(time.time())),
                    "notification_type": "debt_notification"
                })
                success = fcm_service.send_notification(fcm_token, title, body, enhanced_data)
                
                if success:
                    print(f"✅ FCM v1 notification sent successfully to user {user_id}")
                    logger.info(f"Successfully sent manual notification to user {user_id}")
                    return True
                else:
                    print(f"❌ FCM v1 notification failed for user {user_id}")
                    return False
                    
            except ImportError as e:
                print(f"❌ Failed to import FCM v1 service: {e}")
                logger.error(f"Failed to import FCM v1 service: {e}")
                return False
            
        except Exception as e:
            print(f"❌ Error sending manual notification to user {user_id}: {e}")
            print(f"🔍 Error type: {type(e).__name__}")
            import traceback
            traceback.print_exc()
            logger.error(f"Error sending manual notification to user {user_id}: {e}")
            return False

