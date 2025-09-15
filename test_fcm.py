#!/usr/bin/env python3
"""
Test script for FCM functionality
"""
import requests
import json
import time

# Backend URL
BASE_URL = "http://localhost:5000"

def test_health():
    """Test if backend is running"""
    try:
        response = requests.get(f"{BASE_URL}/")
        print(f"✅ Backend is running: {response.status_code}")
        return True
    except Exception as e:
        print(f"❌ Backend not accessible: {e}")
        return False

def test_fcm_endpoints():
    """Test FCM endpoints"""

    # Test data - using real FCM token from Android app
    test_data = {
        "user_id": "GI7PPaaRh7hRogozJcDHt33RQEw2",  # Real user ID from logs
        "title": "Test FCM Notification",
        "body": "This is a test notification from KileKitabu backend",
        "data": {
            "type": "test",
            "debt_id": "test_debt_123"
        }
    }
    
    # Headers for FCM endpoints (no authentication required)
    headers = {
        "Content-Type": "application/json"
    }
    
    print("\n🧪 Testing FCM Endpoints...")
    
    # Test 1: Send manual notification
    print("\n1. Testing manual notification...")
    try:
        response = requests.post(
            f"{BASE_URL}/api/notifications/send",
            headers=headers,
            json=test_data
        )
        print(f"   Status: {response.status_code}")
        print(f"   Response: {response.text}")
    except Exception as e:
        print(f"   Error: {e}")
    
    # Test 2: Send test notification
    print("\n2. Testing test notification...")
    try:
        response = requests.post(
            f"{BASE_URL}/api/notifications/test",
            headers=headers
        )
        print(f"   Status: {response.status_code}")
        print(f"   Response: {response.text}")
    except Exception as e:
        print(f"   Error: {e}")
    
    # Test 3: Check due debts manually
    print("\n3. Testing due debt check...")
    try:
        response = requests.post(
            f"{BASE_URL}/api/notifications/check-due",
            headers=headers
        )
        print(f"   Status: {response.status_code}")
        print(f"   Response: {response.text}")
    except Exception as e:
        print(f"   Error: {e}")
    
    # Test 4: Check overdue debts manually
    print("\n4. Testing overdue debt check...")
    try:
        response = requests.post(
            f"{BASE_URL}/api/notifications/check-overdue",
            headers=headers
        )
        print(f"   Status: {response.status_code}")
        print(f"   Response: {response.text}")
    except Exception as e:
        print(f"   Error: {e}")

def test_android_fcm():
    """Instructions for testing Android FCM"""
    print("\n📱 Android FCM Testing Instructions:")
    print("1. Build and install the Android app")
    print("2. Open the app and log in")
    print("3. Check the logs for FCM token generation:")
    print("   - Look for 'FCM Registration Token:' in Android logs")
    print("4. The token will be automatically stored in Firebase")
    print("5. Use that token to test backend notifications")

def main():
    print("🚀 KileKitabu FCM Testing Script")
    print("=" * 40)
    
    # Test backend health
    if not test_health():
        print("❌ Backend is not running. Please start it first.")
        return
    
    # Test FCM endpoints
    test_fcm_endpoints()
    
    # Android testing instructions
    test_android_fcm()
    
    print("\n✅ FCM testing completed!")
    print("\n📝 Next Steps:")
    print("1. Fix Firebase configuration by adding the service account key")
    print("2. Test with real Firebase tokens from the Android app")
    print("3. Deploy to Render and test with production setup")

if __name__ == "__main__":
    main()

