"""
SMS Reminder Scheduler for KileKitabu Backend
Handles daily scheduling of SMS reminders
"""

import schedule
import time
import threading
import logging
from datetime import datetime
from sms_reminder_service import SMSReminderService

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SMSReminderScheduler:
    """Scheduler for SMS reminders"""
    
    def __init__(self, firebase_db, sms_api_key: str = None, fcm_service=None):
        self.sms_service = SMSReminderService(firebase_db, sms_api_key, fcm_service=fcm_service)
        self.is_running = False
        self.scheduler_thread = None
        
    def start_scheduler(self):
        """Start the SMS reminder scheduler"""
        if self.is_running:
            logger.warning("SMS reminder scheduler is already running")
            return
        
        logger.info("🚀 Starting SMS reminder scheduler...")
        
        # Schedule daily reminder check at 9:00 AM
        schedule.every().day.at("09:00").do(self._run_reminder_check)
        
        # Schedule additional check at 2:00 PM as backup
        schedule.every().day.at("14:00").do(self._run_reminder_check)
        
        # Start scheduler in background thread
        self.is_running = True
        self.scheduler_thread = threading.Thread(target=self._run_scheduler, daemon=True)
        self.scheduler_thread.start()
        
        logger.info("✅ SMS reminder scheduler started successfully")
        logger.info("📅 Scheduled checks: 9:00 AM and 2:00 PM daily")
    
    def stop_scheduler(self):
        """Stop the SMS reminder scheduler"""
        if not self.is_running:
            logger.warning("SMS reminder scheduler is not running")
            return
        
        logger.info("🛑 Stopping SMS reminder scheduler...")
        self.is_running = False
        
        if self.scheduler_thread and self.scheduler_thread.is_alive():
            self.scheduler_thread.join(timeout=5)
        
        schedule.clear()
        logger.info("✅ SMS reminder scheduler stopped")
    
    def _run_scheduler(self):
        """Main scheduler loop"""
        while self.is_running:
            try:
                schedule.run_pending()
                time.sleep(60)  # Check every minute
            except Exception as e:
                logger.error(f"Error in scheduler loop: {str(e)}")
                time.sleep(60)
    
    def _run_reminder_check(self):
        """Run the reminder check (called by scheduler)"""
        try:
            logger.info(f"🕘 Running scheduled SMS reminder check at {datetime.now()}")
            result = self.sms_service.check_and_send_reminders()
            
            if result['status'] == 'success':
                logger.info(f"✅ Reminder check completed: {result['reminders_sent']} reminders sent")
            else:
                logger.error(f"❌ Reminder check failed: {result.get('message', 'Unknown error')}")
                
        except Exception as e:
            logger.error(f"❌ Error in scheduled reminder check: {str(e)}")
    
    def run_manual_check(self):
        """Manually trigger a reminder check"""
        logger.info("🔧 Running manual SMS reminder check...")
        return self.sms_service.check_and_send_reminders()
    
    def run_manual_check_within(self, days_ahead: int):
        """Manually trigger a reminder check for debts due within N days"""
        logger.info(f"🔧 Running manual SMS reminder check within {days_ahead} days...")
        return self.sms_service.check_and_send_reminders_within(days_ahead)
    
    def get_scheduler_status(self):
        """Get current scheduler status"""
        return {
            "is_running": self.is_running,
            "next_run": schedule.next_run(),
            "scheduled_jobs": len(schedule.jobs)
        }
    
    def get_reminder_stats(self, days: int = 7):
        """Get reminder statistics"""
        return self.sms_service.get_reminder_stats(days)

# Global scheduler instance
sms_scheduler = None

def initialize_sms_scheduler(firebase_db, sms_api_key: str = None, fcm_service=None):
    """Initialize the global SMS scheduler"""
    global sms_scheduler
    if sms_scheduler is None:
        sms_scheduler = SMSReminderScheduler(firebase_db, sms_api_key, fcm_service)
        sms_scheduler.start_scheduler()
        logger.info("🌐 Global SMS reminder scheduler initialized")
    return sms_scheduler

def get_sms_scheduler():
    """Get the global SMS scheduler instance"""
    return sms_scheduler
