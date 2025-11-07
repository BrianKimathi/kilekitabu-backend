"""
SMS Reminder Service for KileKitabu Backend
Handles automated SMS reminders for debts due in 5 days
"""

import os
import json
import requests
import datetime
from typing import List, Dict, Optional
from dataclasses import dataclass
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class DebtReminder:
    """Data class for debt reminder information"""
    user_id: str
    debtor_name: str
    debtor_phone: str
    total_amount: float
    due_date: str
    debt_count: int
    debt_ids: List[str]
    message: str

class SMSReminderService:
    """Service to handle SMS reminders for due debts"""
    
    def __init__(self, firebase_db, sms_api_key: str = None, sms_api_url: str = None, fcm_service=None):
        self.db = firebase_db
        self.sms_api_key = sms_api_key or os.getenv('SMS_API_KEY')
        self.sms_api_url = sms_api_url or os.getenv('SMS_API_URL', 'https://api.africastalking.com/version1/messaging')
        self.sms_username = os.getenv('SMS_USERNAME', 'sandbox')
        self.fcm_service = fcm_service
        
    def check_and_send_reminders(self) -> Dict[str, any]:
        """Main method to check for due debts and send SMS reminders"""
        try:
            logger.info("🔍 Starting SMS reminder check...")
            
            # Get all users and their debts
            users_data = self._get_all_users_with_debts()
            if not users_data:
                logger.info("No users found with debts")
                return {"status": "success", "message": "No users with debts found", "reminders_sent": 0}
            
            reminders_sent = 0
            errors = []
            
            for user_id, user_debts in users_data.items():
                try:
                    # Find debts due in default window (5 days)
                    due_reminders = self._find_due_reminders(user_debts)
                    
                    if due_reminders:
                        logger.info(f"Found {len(due_reminders)} debtors with due reminders for user {user_id}")
                        
                        # Send FCM notification to app user first
                        self._send_fcm_notification_for_user(user_id, due_reminders)
                        
                        # Send SMS for each debtor
                        for reminder in due_reminders:
                            success = self._send_sms_reminder(reminder)
                            if success:
                                reminders_sent += 1
                                logger.info(f"✅ SMS sent to {reminder.debtor_phone} for {reminder.debtor_name}")
                            else:
                                errors.append(f"Failed to send SMS to {reminder.debtor_phone}")
                    else:
                        logger.info(f"No due reminders found for user {user_id}")
                        
                except Exception as e:
                    error_msg = f"Error processing user {user_id}: {str(e)}"
                    logger.error(error_msg)
                    errors.append(error_msg)
            
            result = {
                "status": "success",
                "reminders_sent": reminders_sent,
                "errors": errors,
                "timestamp": datetime.datetime.now().isoformat()
            }
            
            logger.info(f"📊 SMS reminder check completed: {reminders_sent} reminders sent")
            return result
            
        except Exception as e:
            logger.error(f"❌ Error in SMS reminder check: {str(e)}")
            return {
                "status": "error",
                "message": str(e),
                "reminders_sent": 0
            }
    
    def _get_all_users_with_debts(self) -> Dict[str, List[Dict]]:
        """Get all users and their active debts from Firebase"""
        try:
            users_debts = {}
            
            # Get all user debts from Firebase
            debts_ref = self.db.reference('UserDebts')
            all_debts = debts_ref.get()
            
            if not all_debts:
                return users_debts
            
            # Group debts by user - handle the actual Firebase structure
            for user_id, user_debts in all_debts.items():
                if user_debts and isinstance(user_debts, dict):
                    # The structure is: {phone_number: {accountName, phoneNumber, debts: {debt_id: debt_data}}}
                    # We need to flatten the debts and add user info
                    active_debts = []
                    
                    # Process each phone number group
                    for phone_number, phone_data in user_debts.items():
                        if isinstance(phone_data, dict) and 'debts' in phone_data:
                            # Get user info from this phone number group
                            account_name = phone_data.get('accountName', 'Unknown')
                            phone_num = phone_data.get('phoneNumber', phone_number)  # Use phone_number as fallback
                            
                            logger.info(f"🔍 Debug: User {user_id} - Phone: {phone_number} - accountName: '{account_name}', phoneNumber: '{phone_num}'")
                            
                            # Process each debt in this phone number group
                            debts_dict = phone_data.get('debts', {})
                            if isinstance(debts_dict, dict):
                                for debt_id, debt_data in debts_dict.items():
                                    if isinstance(debt_data, dict) and not debt_data.get('isComplete', False):
                                        # Create a flattened debt record with user info
                                        flattened_debt = {
                                            'id': debt_id,
                                            'accountName': account_name,
                                            'phoneNumber': phone_num,
                                            'debtAmount': debt_data.get('debtAmount', '0'),
                                            'balance': debt_data.get('balance', '0'),
                                            'description': debt_data.get('description', ''),
                                            'date': debt_data.get('date', ''),
                                            'receiptCamera': debt_data.get('receiptCamera', ''),
                                            'receiptGallery': debt_data.get('receiptGallery', ''),
                                            'isComplete': debt_data.get('isComplete', False)
                                        }
                                        
                                        # Add due date if not present (for existing debts)
                                        if 'dueDate' not in debt_data:
                                            # Calculate 30 days from creation date
                                            created_date = debt_data.get('timestamp', 0)
                                            if created_date:
                                                due_date = created_date + (30 * 24 * 60 * 60 * 1000)  # 30 days in milliseconds
                                                flattened_debt['dueDate'] = due_date
                                        else:
                                            flattened_debt['dueDate'] = debt_data.get('dueDate', 0)
                                        
                                        active_debts.append(flattened_debt)
                    
                    if active_debts:
                        users_debts[user_id] = active_debts
            
            return users_debts
            
        except Exception as e:
            logger.error(f"Error getting users with debts: {str(e)}")
            return {}
    
    def check_and_send_reminders_within(self, days_ahead: int) -> Dict[str, any]:
        """Check for debts due within N days and send SMS reminders"""
        try:
            logger.info(f"🔍 Starting SMS reminder check for debts within {days_ahead} days...")
            users_data = self._get_all_users_with_debts()
            if not users_data:
                return {"status": "success", "message": "No users with debts found", "reminders_sent": 0}

            reminders_sent = 0
            errors = []
            for user_id, user_debts in users_data.items():
                try:
                    due_reminders = self._find_due_reminders(user_debts, window_days=days_ahead)
                    for reminder in due_reminders:
                        success = self._send_sms_reminder(reminder)
                        if success:
                            reminders_sent += 1
                        else:
                            errors.append(f"Failed to send SMS to {reminder.debtor_phone}")
                except Exception as e:
                    errors.append(f"Error processing user {user_id}: {str(e)}")

            return {
                "status": "success",
                "reminders_sent": reminders_sent,
                "errors": errors,
                "timestamp": datetime.datetime.now().isoformat(),
                "window_days": days_ahead,
            }
        except Exception as e:
            logger.error(f"❌ Error in SMS reminder check within {days_ahead} days: {str(e)}")
            return {"status": "error", "message": str(e), "reminders_sent": 0, "window_days": days_ahead}

    def _find_due_reminders(self, user_debts: List[Dict], window_days: int = 5) -> List[DebtReminder]:
        """Find debts due within window_days and group by debtor"""
        try:
            current_time = datetime.datetime.now().timestamp() * 1000  # Convert to milliseconds
            window_end = current_time + (window_days * 24 * 60 * 60 * 1000)  # window in milliseconds
            # Start from today (no buffer) to include debts due today
            window_start = current_time
            
            logger.info(f"🔍 Debug: Current time: {datetime.datetime.now()}")
            logger.info(f"🔍 Debug: Looking for debts due between {datetime.datetime.fromtimestamp(window_start/1000)} and {datetime.datetime.fromtimestamp(window_end/1000)}")
            logger.info(f"🔍 Debug: Processing {len(user_debts)} debts for user")
            
            # Group debts by debtor phone number
            debtor_debts = {}
            
            for debt in user_debts:
                logger.info(f"🔍 Debug: Processing debt: {debt}")
                
                # Try to get due date from different possible fields
                due_date = 0
                
                # First priority: dueDate field (in milliseconds)
                due_date = debt.get('dueDate', 0)
                if due_date > 0:
                    logger.info(f"🔍 Debug: Found dueDate field: {due_date} ({datetime.datetime.fromtimestamp(due_date/1000)})")
                else:
                    # Second priority: date field (in DD/MM/YYYY format)
                    due_date_str = debt.get('date', '')
                    if due_date_str and due_date_str != "Debt Due Date":
                        try:
                            # Try to parse date in DD/MM/YYYY format
                            if '/' in due_date_str:
                                parsed_date = datetime.datetime.strptime(due_date_str, '%d/%m/%Y')
                                due_date = int(parsed_date.timestamp() * 1000)  # Convert to milliseconds
                                logger.info(f"🔍 Debug: Parsed date '{due_date_str}' to {due_date} ({parsed_date})")
                            else:
                                logger.info(f"🔍 Debug: Date format not recognized: '{due_date_str}'")
                        except ValueError as e:
                            logger.info(f"🔍 Debug: Failed to parse date '{due_date_str}': {e}")
                
                logger.info(f"🔍 Debug: Debt due date: {due_date} ({datetime.datetime.fromtimestamp(due_date/1000) if due_date > 0 else 'No due date'})")
                
                # Check if debt is due within window (including today)
                if due_date > 0 and window_start <= due_date <= window_end:
                    logger.info(f"✅ Debug: Debt is within window!")
                    debtor_phone = debt.get('phoneNumber', '')
                    debtor_name = debt.get('accountName', 'Unknown')
                    
                    if debtor_phone:
                        if debtor_phone not in debtor_debts:
                            debtor_debts[debtor_phone] = {
                                'name': debtor_name,
                                'debts': [],
                                'total_amount': 0.0
                            }
                        
                        # Parse amount (remove commas and convert to float)
                        amount_str = debt.get('debtAmount', '0').replace(',', '')
                        try:
                            amount = float(amount_str)
                        except ValueError:
                            amount = 0.0
                        
                        debtor_debts[debtor_phone]['debts'].append(debt)
                        debtor_debts[debtor_phone]['total_amount'] += amount
                else:
                    logger.info(f"❌ Debug: Debt not in window - due_date: {due_date}, window_start: {window_start}, window_end: {window_end}")
            
            # Create DebtReminder objects
            reminders = []
            for phone, data in debtor_debts.items():
                due_date_str = datetime.datetime.fromtimestamp(
                    data['debts'][0]['dueDate'] / 1000
                ).strftime('%d/%m/%Y')
                
                # Create reminder message with the specific format requested
                days_until_due = self._get_days_until_due(data['debts'][0]['dueDate'])
                if days_until_due == 0:
                    message = f"{data['name']} debt of Ksh. {data['total_amount']:,.2f} is due today. Please contact them for repayment."
                elif days_until_due == 1:
                    message = f"{data['name']} debt of Ksh. {data['total_amount']:,.2f} is due tomorrow. Please contact them for repayment."
                else:
                    message = f"{data['name']} debt of Ksh. {data['total_amount']:,.2f} is due in {days_until_due} days. Please contact them for repayment."
                
                reminder = DebtReminder(
                    user_id=data['debts'][0].get('uid', ''),
                    debtor_name=data['name'],
                    debtor_phone=phone,
                    total_amount=data['total_amount'],
                    due_date=due_date_str,
                    debt_count=len(data['debts']),
                    debt_ids=[debt.get('id', '') for debt in data['debts']],
                    message=message
                )
                reminders.append(reminder)
            
            return reminders
            
        except Exception as e:
            logger.error(f"Error finding due reminders: {str(e)}")
            return []

    def _get_days_until_due(self, due_date_ms: int) -> int:
        """Return non-negative integer days between now and due_date_ms (UTC-based)."""
        try:
            if not due_date_ms or due_date_ms <= 0:
                return 0
            now_ms = int(datetime.datetime.now().timestamp() * 1000)
            diff_ms = max(0, due_date_ms - now_ms)
            # Convert to days, rounding down
            return int(diff_ms // (24 * 60 * 60 * 1000))
        except Exception:
            return 0
    
    def _send_sms_reminder(self, reminder: DebtReminder) -> bool:
        """Send SMS reminder to debtor"""
        try:
            # Format amount with commas
            formatted_amount = f"{reminder.total_amount:,.2f}"
            
            # Create message
            if reminder.debt_count == 1:
                message = f"Hello {reminder.debtor_name}, this is a friendly reminder that you have a debt of Ksh {formatted_amount} due on {reminder.due_date}. Please make arrangements to settle this amount. Thank you for your attention to this matter."
            else:
                message = f"Hello {reminder.debtor_name}, this is a friendly reminder that you have {reminder.debt_count} debts totaling Ksh {formatted_amount} due on {reminder.due_date}. Please make arrangements to settle these amounts. Thank you for your attention to this matter."
            
            # Send SMS via API
            success = self._send_sms_via_api(reminder.debtor_phone, message)
            
            if success:
                # Log the reminder in Firebase
                self._log_reminder_sent(reminder)
            
            return success
            
        except Exception as e:
            logger.error(f"Error sending SMS reminder: {str(e)}")
            return False
    
    def _send_sms_via_api(self, phone_number: str, message: str) -> bool:
        """Send SMS via external API (Africa's Talking or similar)"""
        try:
            if not self.sms_api_key:
                logger.warning("SMS API key not configured, using mock SMS")
                logger.info(f"📱 MOCK SMS to {phone_number}: {message}")
                return True
            
            # Prepare request data
            headers = {
                'apiKey': self.sms_api_key,
                'Content-Type': 'application/x-www-form-urlencoded',
                'Accept': 'application/json'
            }
            
            data = {
                'username': self.sms_username,
                'to': phone_number,
                'message': message
            }
            
            # Send request
            response = requests.post(self.sms_api_url, headers=headers, data=data)
            
            if response.status_code == 201:
                logger.info(f"✅ SMS sent successfully to {phone_number}")
                return True
            else:
                logger.error(f"❌ SMS failed to {phone_number}: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            logger.error(f"Error sending SMS via API: {str(e)}")
            return False
    
    def _log_reminder_sent(self, reminder: DebtReminder):
        """Log the reminder in Firebase for tracking"""
        try:
            reminder_log = {
                'user_id': reminder.user_id,
                'debtor_name': reminder.debtor_name,
                'debtor_phone': reminder.debtor_phone,
                'total_amount': reminder.total_amount,
                'due_date': reminder.due_date,
                'debt_count': reminder.debt_count,
                'debt_ids': reminder.debt_ids,
                'sent_at': datetime.datetime.now().isoformat(),
                'status': 'sent'
            }
            
            # Store in Firebase
            log_id = f"reminder_{int(datetime.datetime.now().timestamp())}"
            self.db.reference(f'sms_reminders/{log_id}').set(reminder_log)
            
        except Exception as e:
            logger.error(f"Error logging reminder: {str(e)}")
    
    def check_due_reminders(self, user_id: str) -> List[Dict]:
        """Check for due reminders for a specific user"""
        try:
            # Get user debts
            debts_ref = self.db.reference(f'UserDebts/{user_id}')
            user_debts = debts_ref.get()
            
            if not user_debts:
                return []
            
            # Convert to list format expected by _find_due_reminders
            debts_list = []
            for phone_number, phone_data in user_debts.items():
                if isinstance(phone_data, dict) and 'debts' in phone_data:
                    for debt_id, debt_data in phone_data.get('debts', {}).items():
                        debts_list.append({
                            'user_id': user_id,
                            'phoneNumber': phone_number,
                            'accountName': phone_data.get('accountName', 'Unknown'),
                            'debt_id': debt_id,
                            'debtAmount': debt_data.get('debtAmount', '0'),
                            'balance': debt_data.get('balance', '0'),
                            'description': debt_data.get('description', ''),
                            'date': debt_data.get('date', ''),
                            'dueDate': debt_data.get('dueDate', 0),
                            'isComplete': debt_data.get('isComplete', False)
                        })
            
            # Find due reminders
            reminders = self._find_due_reminders(debts_list, window_days=5)
            
            # Convert to dictionary format for API response
            reminder_dicts = []
            for reminder in reminders:
                reminder_dicts.append({
                    'user_id': reminder.user_id,
                    'debtor_name': reminder.debtor_name,
                    'debtor_phone': reminder.debtor_phone,
                    'amount': str(reminder.total_amount),
                    'due_date': reminder.due_date,
                    'debt_count': reminder.debt_count,
                    'debt_ids': reminder.debt_ids,
                    'message': reminder.message
                })
            
            return reminder_dicts
            
        except Exception as e:
            logger.error(f"Error checking due reminders for user {user_id}: {e}")
            return []

    def get_reminder_stats(self, days: int = 7) -> Dict:
        """Get statistics about sent reminders"""
        try:
            reminders_ref = self.db.reference('sms_reminders')
            all_reminders = reminders_ref.get()
            
            if not all_reminders:
                return {"total_reminders": 0, "recent_reminders": []}
            
            # Filter recent reminders
            cutoff_date = datetime.datetime.now() - datetime.timedelta(days=days)
            recent_reminders = []
            
            for reminder_id, reminder_data in all_reminders.items():
                if isinstance(reminder_data, dict):
                    sent_at_str = reminder_data.get('sent_at', '')
                    if sent_at_str:
                        try:
                            sent_at = datetime.datetime.fromisoformat(sent_at_str.replace('Z', '+00:00'))
                            if sent_at >= cutoff_date:
                                recent_reminders.append(reminder_data)
                        except ValueError:
                            continue
            
            return {
                "total_reminders": len(all_reminders),
                "recent_reminders": recent_reminders,
                "period_days": days
            }
            
        except Exception as e:
            logger.error(f"Error getting reminder stats: {str(e)}")
            return {"error": str(e)}
    
    def _send_fcm_notification_for_user(self, user_id: str, due_reminders: List[DebtReminder]):
        """Send individual FCM notifications for each debt due today"""
        try:
            if not self.fcm_service:
                logger.warning("FCM service not available, skipping FCM notification")
                return False
            
            # Get FCM token for user
            fcm_tokens_ref = self.db.reference('fcm_tokens')
            fcm_token = fcm_tokens_ref.child(user_id).get()
            
            if not fcm_token:
                logger.warning(f"No FCM token found for user {user_id}")
                return False
            
            # Send individual notification for each debt
            notifications_sent = 0
            for reminder in due_reminders:
                for i, debt_id in enumerate(reminder.debt_ids):
                    # Get individual debt details
                    debt_details = self._get_debt_details(user_id, debt_id)
                    if debt_details:
                        # Calculate days until due date
                        due_date_ms = debt_details.get('dueDate', 0)
                        if due_date_ms > 0:
                            current_time = datetime.datetime.now().timestamp() * 1000
                            days_until_due = max(0, int((due_date_ms - current_time) / (24 * 60 * 60 * 1000)))
                            
                            if days_until_due == 0:
                                title = "💰 Debt Due Today!"
                            elif days_until_due == 1:
                                title = "💰 Debt Due Tomorrow!"
                            else:
                                title = "💰 Debt Due Soon!"
                        else:
                            title = "💰 Debt Due Soon!"
                        
                        # Use the message from the DebtReminder object
                        body = reminder.message
                        
                        # Send individual FCM notification
                        success = self.fcm_service.send_manual_notification(
                            user_id,
                            title, 
                            body, 
                            {
                                "type": "debt_due_reminder",
                                "debt_id": debt_id,
                                "debtor_name": reminder.debtor_name,
                                "debtor_phone": reminder.debtor_phone,
                                "amount": str(reminder.total_amount),
                                "due_date": reminder.due_date,
                                "days_until_due": str(days_until_due if due_date_ms > 0 else 0),
                                "title": title,
                                "body": body,
                                "message": reminder.message,
                                "user_id": user_id
                            }
                        )
                        
                        if success:
                            notifications_sent += 1
                            logger.info(f"✅ Individual FCM notification sent for debt {debt_id}")
                        else:
                            logger.error(f"❌ Failed to send FCM notification for debt {debt_id}")
            
            logger.info(f"📱 Sent {notifications_sent} individual notifications to user {user_id}")
            return notifications_sent > 0
            
        except Exception as e:
            logger.error(f"Error sending FCM notifications to user {user_id}: {str(e)}")
            return False
    
    def _get_debt_details(self, user_id: str, debt_id: str) -> Optional[Dict]:
        """Get specific debt details by ID"""
        try:
            debts_ref = self.db.reference(f'UserDebts/{user_id}')
            user_debts = debts_ref.get()
            
            if not user_debts:
                return None
            
            # Search through all phone number groups for the specific debt
            for phone_number, phone_data in user_debts.items():
                if isinstance(phone_data, dict) and 'debts' in phone_data:
                    debts_dict = phone_data.get('debts', {})
                    if debt_id in debts_dict:
                        debt_data = debts_dict[debt_id]
                        return {
                            'id': debt_id,
                            'accountName': phone_data.get('accountName', 'Unknown'),
                            'phoneNumber': phone_data.get('phoneNumber', phone_number),
                            'debtAmount': debt_data.get('debtAmount', '0'),
                            'balance': debt_data.get('balance', '0'),
                            'description': debt_data.get('description', ''),
                            'date': debt_data.get('date', ''),
                            'dueDate': debt_data.get('dueDate', 0),
                            'isComplete': debt_data.get('isComplete', False)
                        }
            
            return None
            
        except Exception as e:
            logger.error(f"Error getting debt details for {debt_id}: {str(e)}")
            return None
