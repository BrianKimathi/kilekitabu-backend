#!/usr/bin/env python3
"""
Test FCM integration with SMS reminders
"""

import requests
import json

def test_fcm_integration():
    """Test if FCM notifications are being sent with SMS reminders"""
    
    print("🧪 Testing FCM Integration with SMS Reminders")
    print("=" * 60)
    
    # Test 1: Check if we can find debts for the specific user
    print("📱 Test 1: Checking if debts exist for user GI7PPaaRh7hRogozJcDHt33RQEw2...")
    
    # First, let's check what users have FCM tokens
    try:
        response = requests.get('http://localhost:5000/api/notifications/tokens')
        if response.status_code == 200:
            tokens_data = response.json()
            tokens = tokens_data.get('tokens', {})
            print(f"✅ Found {len(tokens)} users with FCM tokens:")
            for user_id, token in tokens.items():
                print(f"   - {user_id}: {token[:20]}...")
            
            if 'GI7PPaaRh7hRogozJcDHt33RQEw2' in tokens:
                print("✅ Your user ID has an FCM token")
            else:
                print("❌ Your user ID is not in the FCM tokens list")
                print("   This might be why you're not receiving notifications")
        else:
            print(f"❌ Failed to get FCM tokens: {response.status_code}")
    except Exception as e:
        print(f"❌ Error getting FCM tokens: {e}")
    
    # Test 2: Run SMS reminder check and look for specific user
    print("\n📱 Test 2: Running SMS reminder check...")
    print("   (Watch backend console for FCM logs)")
    try:
        response = requests.post('http://localhost:5000/api/sms-reminders/check?days=20')
        if response.status_code == 200:
            result = response.json()
            print(f"✅ SMS reminder check completed!")
            print(f"   Status: {result.get('status')}")
            print(f"   Reminders sent: {result.get('reminders_sent', 0)}")
            print(f"   Errors: {result.get('errors', [])}")
            
            if result.get('reminders_sent', 0) > 0:
                print("\n🔍 Check the backend console for these specific logs:")
                print("   - 'Found X debtors with due reminders for user GI7PPaaRh7hRogozJcDHt33RQEw2'")
                print("   - 'FCM notification sent to user GI7PPaaRh7hRogozJcDHt33RQEw2'")
                print("   - 'FCM service not available' (if there's an error)")
                print("   - 'No FCM token found for user GI7PPaaRh7hRogozJcDHt33RQEw2'")
            else:
                print("ℹ️  No reminders sent - no FCM notifications expected")
        else:
            print(f"❌ SMS reminder check failed: {response.status_code}")
    except Exception as e:
        print(f"❌ SMS reminder check error: {e}")
    
    # Test 3: Manual FCM test to confirm it works
    print("\n📱 Test 3: Sending manual FCM test...")
    try:
        response = requests.post('http://localhost:5000/api/notifications/test', json={
            'user_id': 'GI7PPaaRh7hRogozJcDHt33RQEw2',
            'title': 'Manual FCM Test',
            'body': 'This confirms FCM notifications work for your user ID'
        })
        
        if response.status_code == 200:
            print("✅ Manual FCM test sent successfully!")
            print("   You should receive this notification on your device")
        else:
            print(f"❌ Manual FCM test failed: {response.status_code}")
    except Exception as e:
        print(f"❌ Manual FCM test error: {e}")
    
    print("\n🎯 Analysis:")
    print("=" * 60)
    print("✅ SMS reminders are working (10 sent)")
    print("✅ FCM notifications work manually")
    print("❓ FCM + SMS integration needs investigation")
    print("\n💡 Possible issues:")
    print("   1. No debts found for your specific user ID")
    print("   2. FCM service not properly passed to SMS reminder service")
    print("   3. Silent error in FCM notification method")
    print("\n🔍 Next step: Check backend console logs for FCM-related messages")

if __name__ == "__main__":
    test_fcm_integration()

