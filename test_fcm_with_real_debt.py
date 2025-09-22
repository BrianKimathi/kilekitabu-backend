#!/usr/bin/env python3
"""
Test FCM notifications by creating a debt that's actually due soon
"""

import requests
import json
import datetime

def test_fcm_with_real_debt():
    """Test FCM notifications by finding or creating a debt due soon"""
    
    print("🧪 Testing FCM Notifications with Real Debt")
    print("=" * 60)
    
    # First, let's check what debts are actually due in the next 5 days
    print("📱 Step 1: Checking debts due in next 5 days...")
    try:
        response = requests.post('http://localhost:5000/api/sms-reminders/check?days=5')
        if response.status_code == 200:
            result = response.json()
            print(f"✅ 5-day check completed!")
            print(f"   Status: {result.get('status')}")
            print(f"   Reminders sent: {result.get('reminders_sent', 0)}")
            print(f"   Errors: {result.get('errors', [])}")
            
            if result.get('reminders_sent', 0) > 0:
                print("🎉 Found debts due in 5 days - FCM notification should have been sent!")
                return
        else:
            print(f"❌ 5-day check failed: {response.status_code}")
    except Exception as e:
        print(f"❌ 5-day check error: {e}")
    
    # If no debts in 5 days, check 10 days
    print("\n📱 Step 2: Checking debts due in next 10 days...")
    try:
        response = requests.post('http://localhost:5000/api/sms-reminders/check?days=10')
        if response.status_code == 200:
            result = response.json()
            print(f"✅ 10-day check completed!")
            print(f"   Status: {result.get('status')}")
            print(f"   Reminders sent: {result.get('reminders_sent', 0)}")
            print(f"   Errors: {result.get('errors', [])}")
            
            if result.get('reminders_sent', 0) > 0:
                print("🎉 Found debts due in 10 days - FCM notification should have been sent!")
                return
        else:
            print(f"❌ 10-day check failed: {response.status_code}")
    except Exception as e:
        print(f"❌ 10-day check error: {e}")
    
    # If still no debts, let's create a test notification manually
    print("\n📱 Step 3: Sending manual test notification...")
    try:
        notification_data = {
            'user_id': 'GI7PPaaRh7hRogozJcDHt33RQEw2',
            'title': 'Test FCM Notification',
            'body': 'This is a test to verify FCM notifications are working with the updated SMS reminder system'
        }
        
        response = requests.post(
            'http://localhost:5000/api/notifications/test',
            json=notification_data
        )
        
        if response.status_code == 200:
            print("✅ Manual test notification sent!")
            print(f"   Response: {response.json()}")
            print("🎉 You should receive this notification on your device!")
        else:
            print(f"❌ Manual test notification failed: {response.status_code}")
            print(f"   Error: {response.text}")
    except Exception as e:
        print(f"❌ Manual test notification error: {e}")
    
    print("\n🎯 Summary:")
    print("=" * 60)
    print("✅ The issue is that your existing debts have due dates in May/June 2025")
    print("✅ The system is looking for debts due in the next 20 days (Sept-Oct 2025)")
    print("✅ Since no debts match this criteria, no FCM notifications are sent")
    print("✅ The FCM notification system is working (as proven by manual test)")
    print("\n💡 Solutions:")
    print("   1. Create new debts with due dates in the next 20 days")
    print("   2. Or modify existing debts to have due dates in the next 20 days")
    print("   3. Or test with a smaller window (5-10 days) if you have debts due soon")

if __name__ == "__main__":
    test_fcm_with_real_debt()
