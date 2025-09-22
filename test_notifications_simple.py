#!/usr/bin/env python3
"""
Simple test script to test notifications using the existing backend API
Uses the user ID from the reminders for testing
"""

import requests
import json
import time

# Configuration
BACKEND_URL = "http://localhost:5000"
TEST_USER_ID = "GI7PPaaRh7hRogozJcDHt33RQEw2"

def test_backend_health():
    """Test if backend is running"""
    try:
        response = requests.get(f"{BACKEND_URL}/health", timeout=5)
        if response.status_code == 200:
            print("✅ Backend is running")
            return True
        else:
            print(f"❌ Backend health check failed: {response.status_code}")
            return False
    except requests.exceptions.RequestException as e:
        print(f"❌ Backend is not running: {e}")
        return False

def test_notification_api():
    """Test the notification API"""
    print(f"\n🔔 Testing notification API for user: {TEST_USER_ID}")
    
    try:
        # Test the notification endpoint
        response = requests.post(f"{BACKEND_URL}/send_notification", 
                               json={"user_id": TEST_USER_ID},
                               timeout=10)
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Notification API response: {result}")
            return True
        else:
            print(f"❌ Notification API failed: {response.status_code}")
            print(f"Response: {response.text}")
            return False
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Error calling notification API: {e}")
        return False

def test_sms_reminder_api():
    """Test the SMS reminder API"""
    print(f"\n📱 Testing SMS reminder API for user: {TEST_USER_ID}")
    
    try:
        # Test the SMS reminder endpoint
        response = requests.post(f"{BACKEND_URL}/check_sms_reminders", 
                               json={"user_id": TEST_USER_ID},
                               timeout=10)
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ SMS reminder API response: {result}")
            return True
        else:
            print(f"❌ SMS reminder API failed: {response.status_code}")
            print(f"Response: {response.text}")
            return False
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Error calling SMS reminder API: {e}")
        return False

def test_debt_details_api():
    """Test getting debt details"""
    print(f"\n📊 Testing debt details API for user: {TEST_USER_ID}")
    
    try:
        # Test getting user debts
        response = requests.get(f"{BACKEND_URL}/get_user_debts/{TEST_USER_ID}", 
                               timeout=10)
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Debt details API response: {result}")
            return True
        else:
            print(f"❌ Debt details API failed: {response.status_code}")
            print(f"Response: {response.text}")
            return False
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Error calling debt details API: {e}")
        return False

def main():
    """Main test function"""
    print("🚀 Starting notification tests...")
    print(f"👤 Test User ID: {TEST_USER_ID}")
    print(f"🌐 Backend URL: {BACKEND_URL}")
    print("=" * 60)
    
    # Test backend health
    if not test_backend_health():
        print("\n❌ Backend is not running. Please start the backend first:")
        print("   python app.py")
        return
    
    # Test debt details
    test_debt_details_api()
    
    # Test SMS reminders
    test_sms_reminder_api()
    
    # Test notifications
    test_notification_api()
    
    print("\n" + "=" * 60)
    print("✅ Notification tests completed!")
    print("\n💡 Next steps:")
    print("1. Check your Android device for notifications")
    print("2. Check the notifications screen in the app")
    print("3. Verify that notifications are saved in the local database")

if __name__ == "__main__":
    main()