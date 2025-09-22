#!/usr/bin/env python3
"""
Debug script to log all debts and test the _find_due_reminders method
"""

import requests
import json
import datetime
import time

# Configuration
BACKEND_URL = "http://localhost:5000"
TEST_USER_ID = "GI7PPaaRh7hRogozJcDHt33RQEw2"

def get_user_debts():
    """Get all debts for the user"""
    print("📊 Getting all debts for user...")
    
    try:
        response = requests.get(f"{BACKEND_URL}/get_user_debts/{TEST_USER_ID}", timeout=30)
        
        if response.status_code == 200:
            result = response.json()
            debts = result.get('debts', [])
            print(f"✅ Found {len(debts)} total debts")
            
            # Filter debts with due dates
            debts_with_due_dates = [debt for debt in debts if debt.get('due_date', 0) > 0]
            print(f"📅 Found {len(debts_with_due_dates)} debts with due dates")
            
            # Show debts with due dates
            print("\n📋 Debts with due dates:")
            for i, debt in enumerate(debts_with_due_dates, 1):
                due_date_ms = debt.get('due_date', 0)
                due_date_str = debt.get('date', 'Unknown')
                current_time = datetime.datetime.now().timestamp() * 1000
                days_until_due = max(0, int((due_date_ms - current_time) / (24 * 60 * 60 * 1000)))
                
                print(f"  {i}. {debt.get('account_name', 'Unknown')} - KSh {debt.get('debt_amount', '0')}")
                print(f"     Due Date: {due_date_str} (timestamp: {due_date_ms})")
                print(f"     Days until due: {days_until_due}")
                print(f"     Phone: {debt.get('phone_number', 'Unknown')}")
                print(f"     Debt ID: {debt.get('debt_id', 'Unknown')}")
                print()
            
            return debts_with_due_dates
        else:
            print(f"❌ Error getting debts: {response.status_code} - {response.text}")
            return []
            
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return []

def test_reminder_detection():
    """Test the reminder detection directly"""
    print("🔍 Testing reminder detection...")
    
    try:
        # Test the SMS reminder endpoint
        response = requests.post(f"{BACKEND_URL}/check_sms_reminders", 
                               json={"user_id": TEST_USER_ID},
                               timeout=30)
        
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.text}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"\n📊 Reminders found: {result.get('reminders_found', 0)}")
            
            if result.get('reminders'):
                print("\n📋 Reminder details:")
                for i, reminder in enumerate(result['reminders'], 1):
                    print(f"  {i}. {reminder.get('debtor_name', 'Unknown')} - KSh {reminder.get('amount', '0')}")
                    print(f"     Phone: {reminder.get('debtor_phone', 'Unknown')}")
                    print(f"     Message: {reminder.get('message', 'No message')}")
                    print()
            else:
                print("❌ No reminders found despite 6 debts being due")
                print("This suggests the _find_due_reminders method is not working correctly")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    print("🚀 Starting debt detection debug...")
    print(f"👤 User ID: {TEST_USER_ID}")
    print(f"🌐 Backend URL: {BACKEND_URL}")
    print("=" * 60)
    
    # Get all debts first
    debts = get_user_debts()
    
    print("\n" + "=" * 60)
    
    # Test reminder detection
    test_reminder_detection()
    
    print("\n" + "=" * 60)
    print("✅ Debug completed!")

