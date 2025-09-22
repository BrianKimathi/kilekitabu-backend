#!/usr/bin/env python3
"""
Quick notification test - tests if notifications are working
"""

import requests
import json

# Configuration
BACKEND_URL = "http://localhost:5000"
TEST_USER_ID = "GI7PPaaRh7hRogozJcDHt33RQEw2"

def test_notification():
    """Test the notification endpoint"""
    print("🔔 Testing notification endpoint...")
    
    try:
        # Test the notification endpoint
        response = requests.post(f"{BACKEND_URL}/send_notification", 
                               json={"user_id": TEST_USER_ID},
                               timeout=10)
        
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.text}")
        
        if response.status_code == 200:
            result = response.json()
            print("✅ Notification test successful!")
            print(f"Result: {json.dumps(result, indent=2)}")
            return True
        else:
            print("❌ Notification test failed!")
            return False
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def test_sms_reminders():
    """Test the SMS reminder endpoint"""
    print("\n📱 Testing SMS reminder endpoint...")
    
    try:
        # Test the SMS reminder endpoint
        response = requests.post(f"{BACKEND_URL}/check_sms_reminders", 
                               json={"user_id": TEST_USER_ID},
                               timeout=10)
        
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.text}")
        
        if response.status_code == 200:
            result = response.json()
            print("✅ SMS reminder test successful!")
            print(f"Result: {json.dumps(result, indent=2)}")
            return True
        else:
            print("❌ SMS reminder test failed!")
            return False
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

if __name__ == "__main__":
    print("🚀 Quick Notification Test")
    print("=" * 40)
    
    # Test notifications
    test_notification()
    
    # Test SMS reminders
    test_sms_reminders()
    
    print("\n✅ Test completed!")
    print("\n💡 Check your Android device for notifications!")
