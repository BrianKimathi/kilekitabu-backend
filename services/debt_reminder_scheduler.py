"""
Debt Reminder Scheduler
Sends notifications for debts due in X days (3 days, 1 day before due date)
"""
import logging
import threading
import time
from datetime import datetime, timedelta
from firebase_admin import db

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DebtReminderScheduler:
    """Scheduler for debt reminders (debts due in X days)"""
    
    def __init__(self, fcm_service):
        self.fcm_service = fcm_service
        self.db = db.reference()
        self.running = False
        self.thread = None
        self.last_check_date = None
        # Reminder days: check for debts due in 3 days and 1 day
        self.reminder_days = [3, 1]
    
    def start_scheduler(self):
        """Start the debt reminder scheduler"""
        if self.running:
            logger.warning("Debt reminder scheduler is already running")
            return
        
        logger.info("🚀 Starting debt reminder scheduler...")
        self.running = True
        self.thread = threading.Thread(target=self._run_scheduler, daemon=True)
        self.thread.start()
        logger.info("✅ Debt reminder scheduler started successfully")
        logger.info("📅 Scheduled check: 9:00 AM daily")
        logger.info(f"📋 Reminder days: {self.reminder_days} days before due date")
    
    def stop_scheduler(self):
        """Stop the debt reminder scheduler"""
        self.running = False
        if self.thread:
            self.thread.join(timeout=5)
        logger.info("Debt reminder scheduler stopped")
    
    def _run_scheduler(self):
        """Main scheduler loop - checks every minute"""
        while self.running:
            try:
                current_time = datetime.now()
                
                # Check if it's time for daily debt reminder check (9:00 AM)
                if current_time.hour == 9 and current_time.minute == 0:
                    # Only run once per day
                    today = current_time.date()
                    if self.last_check_date != today:
                        self.check_upcoming_debts()
                        self.last_check_date = today
                
                # Sleep for 1 minute before next check
                time.sleep(60)
                
            except Exception as e:
                logger.error(f"Error in debt reminder scheduler loop: {e}")
                time.sleep(60)  # Sleep for 1 minute before retrying
    
    def check_upcoming_debts(self):
        """Check for debts due in X days and send reminder notifications"""
        logger.info("🔍 Checking for upcoming debts...")
        
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
            users_notified = []
            
            for user_id, fcm_token in fcm_tokens.items():
                if not fcm_token:
                    continue
                
                # Get user's debts
                user_debts_data = user_debts.get(user_id)
                if not user_debts_data:
                    continue
                
                # Collect debts due in reminder_days
                upcoming_debts_by_days = {}  # {3: [debts], 1: [debts]}
                
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
                        
                        try:
                            debt_date_obj = datetime.strptime(debt_date, '%Y-%m-%d').date()
                            days_until_due = (debt_date_obj - today).days
                            
                            # Check if debt is due in one of our reminder days
                            if days_until_due in self.reminder_days:
                                debt_info = {
                                    'id': debt_id,
                                    'account_name': debtor_data.get('accountName', 'Unknown'),
                                    'account_phone': phone_number,
                                    'amount': debt.get('debtAmount', '0'),
                                    'due_date': debt_date,
                                    'description': debt.get('description', ''),
                                    'days_until_due': days_until_due
                                }
                                
                                if days_until_due not in upcoming_debts_by_days:
                                    upcoming_debts_by_days[days_until_due] = []
                                upcoming_debts_by_days[days_until_due].append(debt_info)
                                
                        except ValueError as e:
                            logger.warning(f"Invalid date format for debt {debt_id}: {debt_date}")
                            continue
                
                # Send notifications for each reminder day
                for days_until_due, debts_list in upcoming_debts_by_days.items():
                    if debts_list:
                        success = self._send_debt_reminder_notification(
                            fcm_token, user_id, debts_list, days_until_due
                        )
                        if success:
                            notifications_sent += 1
                            if user_id not in users_notified:
                                users_notified.append(user_id)
                            logger.info(f"✅ Sent {days_until_due}-day reminder for {len(debts_list)} debt(s) to user {user_id}")
            
            logger.info(f"📤 Sent {notifications_sent} debt reminder notifications to {len(users_notified)} users")
            
        except Exception as e:
            logger.error(f"❌ Error checking upcoming debts: {e}")
            import traceback
            logger.error(traceback.format_exc())
    
    def _send_debt_reminder_notification(self, fcm_token, user_id, debts, days_until_due):
        """Send debt reminder notification to a user"""
        try:
            # Calculate total amount
            total_amount = 0.0
            for debt in debts:
                try:
                    amount = float(debt.get('amount', '0'))
                    total_amount += amount
                except ValueError:
                    pass
            
            # Create notification message based on days until due
            if days_until_due == 3:
                if len(debts) == 1:
                    debt = debts[0]
                    title = "📅 Debt Reminder: 3 Days Left"
                    body = f"Debt from {debt['account_name']} is due in 3 days. Amount: KSh {debt['amount']}"
                else:
                    title = f"📅 {len(debts)} Debts Due in 3 Days"
                    body = f"You have {len(debts)} debts due in 3 days. Total: KSh {total_amount:,.2f}"
            elif days_until_due == 1:
                if len(debts) == 1:
                    debt = debts[0]
                    title = "⏰ Debt Due Tomorrow!"
                    body = f"Debt from {debt['account_name']} is due tomorrow. Amount: KSh {debt['amount']}"
                else:
                    title = f"⏰ {len(debts)} Debts Due Tomorrow!"
                    body = f"You have {len(debts)} debts due tomorrow. Total: KSh {total_amount:,.2f}"
            else:
                # Generic reminder
                if len(debts) == 1:
                    debt = debts[0]
                    title = f"📅 Debt Reminder: {days_until_due} Days Left"
                    body = f"Debt from {debt['account_name']} is due in {days_until_due} days. Amount: KSh {debt['amount']}"
                else:
                    title = f"📅 {len(debts)} Debts Due in {days_until_due} Days"
                    body = f"You have {len(debts)} debts due in {days_until_due} days. Total: KSh {total_amount:,.2f}"
            
            # Prepare notification data
            notification_data = {
                "type": "debt_reminder",
                "user_id": user_id,
                "days_until_due": str(days_until_due),
                "debt_count": str(len(debts)),
                "total_amount": str(total_amount),
                "timestamp": str(int(time.time())),
                "notification_type": "debt_reminder",
                "debts": debts,
                "click_action": "com.jeff.kilekitabu.DEBT_NOTIFICATION"
            }
            
            # Send notification using FCM service
            success = self.fcm_service.send_notification(
                fcm_token, title, body, notification_data
            )
            
            return success
            
        except Exception as e:
            logger.error(f"❌ Error sending debt reminder notification to user {user_id}: {e}")
            return False

