#!/usr/bin/env python3
"""
Test script to trigger debt due notifications
This will test the actual debt reminder system, not just test notifications
"""

import requests
import json
import datetime

# Configuration
BACKEND_URL = "http://localhost:5000"
TEST_USER_ID = "GI7PPaaRh7hRogozJcDHt33RQEw2"

def test_debt_reminder_system():
    """Test the actual debt reminder system"""
    print("🔔 Testing debt reminder system...")
    print(f"👤 User ID: {TEST_USER_ID}")
    print("=" * 60)
    
    try:
        # Test the SMS reminder endpoint which should trigger debt notifications
        response = requests.post(f"{BACKEND_URL}/check_sms_reminders", 
                               json={"user_id": TEST_USER_ID},
                               timeout=30)
        
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.text}")
        
        if response.status_code == 200:
            result = response.json()
            print("✅ Debt reminder system test successful!")
            print(f"Reminders found: {result.get('reminders_found', 0)}")
            
            if result.get('reminders'):
                print("\n📋 Debt reminders:")
                for i, reminder in enumerate(result['reminders'], 1):
                    print(f"  {i}. {reminder.get('debtor_name', 'Unknown')} - KSh {reminder.get('amount', '0')}")
                    print(f"     Due: {reminder.get('due_date', 'Unknown')}")
                    print(f"     Phone: {reminder.get('phone_number', 'Unknown')}")
                    print(f"     Message: {reminder.get('message', 'No message')}")
                    print()
            
            return True
        else:
            print("❌ Debt reminder system test failed!")
            return False
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def test_manual_debt_notification():
    """Test sending a manual debt notification"""
    print("\n🔔 Testing manual debt notification...")
    
    try:
        # Send a manual notification with debt-specific data
        notification_data = {
            "user_id": TEST_USER_ID,
            "title": "Debt Due Reminder",
            "body": "Test Debtor Today debt of Ksh. 3000.00 is due soon. Please contact them for repayment.",
            "data": {
                "type": "debt_due_reminder",
                "debtor_name": "Test Debtor Today",
                "debtor_phone": "+254720239719",
                "amount": "3000.00",
                "debt_id": "test_debt_today_1758378250"
            }
        }
        
        response = requests.post(f"{BACKEND_URL}/api/notifications/send", 
                               json=notification_data,
                               timeout=10)
        
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.text}")
        
        if response.status_code == 200:
            print("✅ Manual debt notification sent successfully!")
            return True
        else:
            print("❌ Manual debt notification failed!")
            return False
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def check_user_debts_due_today():
    """Check which debts are due today or soon"""
    print("\n📊 Checking debts due today or soon...")
    
    try:
        response = requests.get(f"{BACKEND_URL}/get_user_debts/{TEST_USER_ID}", 
                               timeout=10)
        
        if response.status_code == 200:
            result = response.json()
            debts = result.get('debts', [])
            
            current_time = datetime.datetime.now()
            current_timestamp = int(current_time.timestamp() * 1000)
            
            # Check for debts due in the next 5 days
            due_soon = []
            for debt in debts:
                due_date = debt.get('due_date', 0)
                if due_date > 0:
                    # Convert to datetime for comparison
                    debt_due_date = datetime.datetime.fromtimestamp(due_date / 1000)
                    days_until_due = (debt_due_date - current_time).days
                    
                    if 0 <= days_until_due <= 5:
                        due_soon.append({
                            'debt': debt,
                            'days_until_due': days_until_due,
                            'due_date_str': debt_due_date.strftime('%d/%m/%Y')
                        })
            
            print(f"Found {len(due_soon)} debts due in the next 5 days:")
            for item in due_soon:
                debt = item['debt']
                print(f"  - {debt['account_name']} - KSh {debt['debt_amount']}")
                print(f"    Due in {item['days_until_due']} days ({item['due_date_str']})")
                print(f"    Phone: {debt['phone_number']}")
                print(f"    Description: {debt['description']}")
                print()
            
            return due_soon
        else:
            print(f"❌ Failed to get user debts: {response.status_code}")
            return []
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return []

def main():
    """Main test function"""
    print("🚀 Testing Debt Notification System")
    print("=" * 60)
    
    # Check which debts are due soon
    due_debts = check_user_debts_due_today()
    
    # Test the debt reminder system
    test_debt_reminder_system()
    
    # Test manual debt notification
    test_manual_debt_notification()
    
    print("\n" + "=" * 60)
    print("✅ Debt notification tests completed!")
    print("\n💡 Expected results:")
    print("1. You should receive notifications for debts due in 5 days or less")
    print("2. Notifications should appear in your Android app")
    print("3. Tapping notifications should open the SMS screen")
    print("4. Check the notifications screen in the app")

if __name__ == "__main__":
    main()
