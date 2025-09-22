#!/usr/bin/env python3
"""
Debug script to test the SMS reminder detection
"""

import requests
import json
import datetime

# Configuration
BACKEND_URL = "http://localhost:5000"
TEST_USER_ID = "GI7PPaaRh7hRogozJcDHt33RQEw2"

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
    test_reminder_detection()

