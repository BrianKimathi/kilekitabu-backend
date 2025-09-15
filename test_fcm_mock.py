#!/usr/bin/env python3
"""
Test FCM functionality with mock service
"""
import requests
import json

def test_fcm_endpoints():
    """Test FCM endpoints with the running backend"""
    
    print("🚀 Testing FCM Endpoints with Mock Service")
    print("=" * 50)
    
    # Test 1: Check FCM tokens
    print("\n1. Checking FCM tokens...")
    try:
        response = requests.get('http://localhost:5000/api/notifications/tokens')
        print(f"   Status: {response.status_code}")
        print(f"   Response: {response.text}")
        
        if response.status_code == 200:
            data = response.json()
            tokens = data.get('tokens', {})
            if tokens:
                print(f"   ✅ Found {len(tokens)} FCM tokens")
                for user_id, token in tokens.items():
                    print(f"      - User: {user_id}")
                    print(f"      - Token: {token[:50]}...")
            else:
                print("   ❌ No FCM tokens found")
        else:
            print(f"   ❌ Failed to get tokens: {response.text}")
            
    except Exception as e:
        print(f"   ❌ Error checking tokens: {e}")
    
    # Test 2: Send test notification
    print("\n2. Sending test notification...")
    try:
        response = requests.post('http://localhost:5000/api/notifications/test', 
                               json={'user_id': 'GI7PPaaRh7hRogozJcDHt33RQEw2'})
        print(f"   Status: {response.status_code}")
        print(f"   Response: {response.text}")
        
        if response.status_code == 200:
            print("   ✅ Test notification sent successfully!")
        else:
            print(f"   ❌ Failed to send notification: {response.text}")
            
    except Exception as e:
        print(f"   ❌ Error sending notification: {e}")
    
    # Test 3: Send manual notification
    print("\n3. Sending manual notification...")
    try:
        notification_data = {
            "user_id": "GI7PPaaRh7hRogozJcDHt33RQEw2",
            "title": "Manual Test Notification",
            "body": "This is a manual test notification from the backend",
            "data": {
                "type": "manual_test",
                "debt_id": "test_debt_123"
            }
        }
        
        response = requests.post('http://localhost:5000/api/notifications/send', 
                               json=notification_data)
        print(f"   Status: {response.status_code}")
        print(f"   Response: {response.text}")
        
        if response.status_code == 200:
            print("   ✅ Manual notification sent successfully!")
        else:
            print(f"   ❌ Failed to send manual notification: {response.text}")
            
    except Exception as e:
        print(f"   ❌ Error sending manual notification: {e}")
    
    # Test 4: Check due debts
    print("\n4. Checking due debts...")
    try:
        response = requests.post('http://localhost:5000/api/notifications/check-due')
        print(f"   Status: {response.status_code}")
        print(f"   Response: {response.text}")
        
        if response.status_code == 200:
            print("   ✅ Due debt check completed!")
        else:
            print(f"   ❌ Failed to check due debts: {response.text}")
            
    except Exception as e:
        print(f"   ❌ Error checking due debts: {e}")

if __name__ == "__main__":
    test_fcm_endpoints()
    
    print("\n" + "=" * 50)
    print("📱 Next Steps:")
    print("1. Check your Android device for notifications")
    print("2. If no notifications appear, check the backend logs")
    print("3. Verify the FCM token is correct in the Android app")
    print("4. Make sure the Android app is running in the background")

