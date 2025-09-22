#!/usr/bin/env python3
"""
Debug script to check why debt reminders are not being found
"""

import requests
import json
import datetime

# Configuration
BACKEND_URL = "http://localhost:5000"
TEST_USER_ID = "GI7PPaaRh7hRogozJcDHt33RQEw2"

def debug_debt_reminders():
    """Debug the debt reminder detection"""
    print("🔍 Debugging debt reminder detection...")
    
    try:
        # Get user debts
        response = requests.get(f"{BACKEND_URL}/get_user_debts/{TEST_USER_ID}", timeout=10)
        
        if response.status_code == 200:
            result = response.json()
            debts = result.get('debts', [])
            
            print(f"📊 Found {len(debts)} total debts")
            
            current_time = datetime.datetime.now()
            current_timestamp = int(current_time.timestamp() * 1000)
            
            # Check for debts due in the next 5 days
            due_soon = []
            for debt in debts:
                due_date = debt.get('due_date', 0)
                if due_date > 0:
                    debt_due_date = datetime.datetime.fromtimestamp(due_date / 1000)
                    days_until_due = (debt_due_date - current_time).days
                    
                    if 0 <= days_until_due <= 5:
                        due_soon.append({
                            'debt': debt,
                            'days_until_due': days_until_due,
                            'due_date_str': debt_due_date.strftime('%d/%m/%Y')
                        })
            
            print(f"\n📅 Debts due in next 5 days: {len(due_soon)}")
            for item in due_soon:
                debt = item['debt']
                print(f"  - {debt['account_name']} - KSh {debt['debt_amount']}")
                print(f"    Due in {item['days_until_due']} days ({item['due_date_str']})")
                print(f"    Phone: {debt['phone_number']}")
                print(f"    Due Date (ms): {debt['due_date']}")
                print()
            
            # Test the SMS reminder service directly
            print("🔍 Testing SMS reminder service directly...")
            from sms_reminder_service import SMSReminderService
            from firebase_admin import db
            
            sms_service = SMSReminderService(db)
            reminders = sms_service.check_due_reminders(TEST_USER_ID)
            
            print(f"📋 SMS service found {len(reminders)} reminders:")
            for reminder in reminders:
                print(f"  - {reminder['debtor_name']} - KSh {reminder['amount']}")
                print(f"    Phone: {reminder['debtor_phone']}")
                print(f"    Message: {reminder['message']}")
                print()
            
        else:
            print(f"❌ Failed to get user debts: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    debug_debt_reminders()
