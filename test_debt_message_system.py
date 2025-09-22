#!/usr/bin/env python3
"""
Test script for the debt message system
Tests individual notifications for debts due today and message screen functionality
"""

import requests
import json
import datetime
import time

# Configuration
BACKEND_URL = "http://localhost:5000"
TEST_USER_ID = "GI7PPaaRh7hRogozJcDHt33RQEw2"  # Replace with actual user ID

def test_debt_details_api():
    """Test the debt details API"""
    print("🔍 Testing debt details API...")
    
    # First, let's find a debt ID by checking SMS reminders
    try:
        response = requests.post(f"{BACKEND_URL}/api/sms-reminders/check?days=1")
        if response.status_code == 200:
            data = response.json()
            print(f"✅ SMS reminder check response: {data}")
        else:
            print(f"❌ SMS reminder check failed: {response.status_code}")
    except Exception as e:
        print(f"❌ Error checking SMS reminders: {e}")
    
    # Test with a sample debt ID (you'll need to replace this with actual debt ID)
    test_debt_id = "test_debt_123"
    
    try:
        response = requests.get(f"{BACKEND_URL}/api/debt/{test_debt_id}?user_id={TEST_USER_ID}")
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Debt details API response: {data}")
        else:
            print(f"❌ Debt details API failed: {response.status_code} - {response.text}")
    except Exception as e:
        print(f"❌ Error testing debt details API: {e}")

def test_manual_sms_api():
    """Test the manual SMS API"""
    print("📱 Testing manual SMS API...")
    
    sms_data = {
        "phone_number": "+254720239719",
        "message": "Test message from debt message system",
        "user_id": TEST_USER_ID
    }
    
    try:
        response = requests.post(
            f"{BACKEND_URL}/api/sms/send",
            json=sms_data,
            headers={"Content-Type": "application/json"}
        )
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Manual SMS API response: {data}")
        else:
            print(f"❌ Manual SMS API failed: {response.status_code} - {response.text}")
    except Exception as e:
        print(f"❌ Error testing manual SMS API: {e}")

def test_notification_system():
    """Test the notification system"""
    print("🔔 Testing notification system...")
    
    # Test sending a test notification
    notification_data = {
        "user_id": TEST_USER_ID,
        "title": "Test Debt Due Today",
        "body": "This is a test notification for debt due today",
        "data": {
            "type": "debt_due_today",
            "debt_id": "test_debt_123",
            "debtor_name": "Test Debtor",
            "debtor_phone": "+254720239719",
            "amount": "1000.00",
            "due_date": "2025-01-15"
        }
    }
    
    try:
        response = requests.post(
            f"{BACKEND_URL}/api/notifications/send",
            json=notification_data,
            headers={"Content-Type": "application/json"}
        )
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Notification API response: {data}")
        else:
            print(f"❌ Notification API failed: {response.status_code} - {response.text}")
    except Exception as e:
        print(f"❌ Error testing notification API: {e}")

def create_test_debt():
    """Create a test debt for today"""
    print("📝 Creating test debt for today...")
    
    # Calculate today's date in milliseconds
    today = datetime.datetime.now()
    today_ms = int(today.timestamp() * 1000)
    
    # Create a test debt that's due today
    test_debt = {
        "id": f"test_debt_{int(time.time())}",
        "accountName": "Test Debtor",
        "phoneNumber": "+254720239719",
        "debtAmount": "1500.00",
        "balance": "1500.00",
        "description": "Test debt for message system",
        "date": today.strftime("%d/%m/%Y"),
        "dueDate": today_ms,
        "isComplete": False
    }
    
    print(f"📝 Test debt data: {test_debt}")
    print("ℹ️  Note: You'll need to manually add this debt to Firebase for testing")
    
    return test_debt

def main():
    """Run all tests"""
    print("🚀 Starting debt message system tests...")
    print(f"📡 Backend URL: {BACKEND_URL}")
    print(f"👤 Test User ID: {TEST_USER_ID}")
    print("-" * 50)
    
    # Test 1: Create test debt
    test_debt = create_test_debt()
    print()
    
    # Test 2: Test debt details API
    test_debt_details_api()
    print()
    
    # Test 3: Test manual SMS API
    test_manual_sms_api()
    print()
    
    # Test 4: Test notification system
    test_notification_system()
    print()
    
    print("✅ All tests completed!")
    print("\n📋 Next steps:")
    print("1. Add the test debt to Firebase manually")
    print("2. Run the SMS reminder check to trigger individual notifications")
    print("3. Test the Android app notification handling")
    print("4. Test the message screen functionality")

if __name__ == "__main__":
    main()
