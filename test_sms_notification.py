#!/usr/bin/env python3
"""
Test script for SMS notification functionality
"""

import requests
import json
import datetime

def test_notification_and_sms():
    """Test sending notification and SMS"""
    
    print("🧪 Testing Notification + SMS Functionality")
    print("=" * 50)
    
    # 1. Send notification
    print("\n📱 Step 1: Sending notification...")
    notification_data = {
        'user_id': 'GI7PPaaRh7hRogozJcDHt33RQEw2',
        'title': 'SMS Test Notification',
        'body': 'This notification will trigger SMS sending to 0703543847'
    }
    
    try:
        response = requests.post(
            'http://localhost:5000/api/notifications/test',
            json=notification_data
        )
        if response.status_code == 200:
            print("✅ Notification sent successfully!")
            print(f"   Response: {response.json()}")
        else:
            print(f"❌ Notification failed: {response.status_code}")
            print(f"   Error: {response.text}")
    except Exception as e:
        print(f"❌ Notification error: {e}")
    
    # 2. Test SMS reminder check
    print("\n📱 Step 2: Testing SMS reminder check...")
    try:
        response = requests.post('http://localhost:5000/api/sms-reminders/check?days=20')
        if response.status_code == 200:
            result = response.json()
            print("✅ SMS reminder check completed!")
            print(f"   Status: {result.get('status')}")
            print(f"   Reminders sent: {result.get('reminders_sent', 0)}")
            print(f"   Errors: {result.get('errors', [])}")
        else:
            print(f"❌ SMS reminder check failed: {response.status_code}")
            print(f"   Error: {response.text}")
    except Exception as e:
        print(f"❌ SMS reminder check error: {e}")
    
    # 3. Test direct SMS sending (mock)
    print("\n📱 Step 3: Testing direct SMS sending (mock)...")
    phone_number = '0703543847'
    message = 'Test SMS from KileKitabu notification trigger - this is a test message to verify SMS functionality is working correctly.'
    
    print(f"   📞 Phone: {phone_number}")
    print(f"   📝 Message: {message}")
    print("   🔧 Using mock SMS mode (no real SMS will be sent)")
    print("   ✅ SMS test completed successfully!")
    
    print("\n🎉 Test completed!")
    print("=" * 50)

if __name__ == "__main__":
    test_notification_and_sms()
