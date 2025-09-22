#!/usr/bin/env python3
"""
Test script to set up test data for notification testing
This script will create test debts and show you how to test notifications
"""

import requests
import json
import datetime
import time

# Configuration
BACKEND_URL = "http://localhost:5000"
TEST_USER_ID = "GI7PPaaRh7hRogozJcDHt33RQEw2"

def create_test_debt_for_notifications():
    """Create a test debt that will trigger notifications"""
    print("📝 Creating test debt for notification testing...")
    
    # Calculate today's date in milliseconds
    today = datetime.datetime.now()
    today_ms = int(today.timestamp() * 1000)
    
    # Create test debt data
    test_debt_id = f"test_notification_{int(datetime.datetime.now().timestamp())}"
    test_debt = {
        "debtAmount": "2500.00",
        "balance": "2500.00",
        "description": "Test debt for notification testing - due today",
        "date": today.strftime("%d/%m/%Y"),
        "dueDate": today_ms,
        "isComplete": False,
        "timestamp": today_ms
    }
    
    # Phone number for the test debt
    phone_number = "+254720239719"
    
    print(f"🆔 Test Debt ID: {test_debt_id}")
    print(f"💰 Amount: {test_debt['debtAmount']}")
    print(f"📅 Due Date: {today.strftime('%d/%m/%Y')}")
    print(f"📞 Phone: {phone_number}")
    
    return test_debt_id, test_debt, phone_number

def test_backend_connection():
    """Test if backend is accessible"""
    try:
        response = requests.get(f"{BACKEND_URL}/health", timeout=5)
        if response.status_code == 200:
            print("✅ Backend is running and accessible")
            return True
        else:
            print(f"⚠️  Backend responded with status: {response.status_code}")
            return False
    except requests.exceptions.RequestException as e:
        print(f"❌ Backend is not accessible: {e}")
        return False

def test_notification_endpoints():
    """Test the notification endpoints"""
    print("\n🔔 Testing notification endpoints...")
    
    endpoints_to_test = [
        ("/health", "GET", "Backend health check"),
        ("/check_sms_reminders", "POST", "SMS reminder check"),
        ("/send_notification", "POST", "Send notification"),
        (f"/get_user_debts/{TEST_USER_ID}", "GET", "Get user debts")
    ]
    
    for endpoint, method, description in endpoints_to_test:
        try:
            print(f"\n📡 Testing {description}...")
            
            if method == "GET":
                response = requests.get(f"{BACKEND_URL}{endpoint}", timeout=5)
            else:
                response = requests.post(f"{BACKEND_URL}{endpoint}", 
                                       json={"user_id": TEST_USER_ID}, 
                                       timeout=5)
            
            if response.status_code == 200:
                result = response.json()
                print(f"✅ {description}: SUCCESS")
                print(f"   Response: {json.dumps(result, indent=2)}")
            else:
                print(f"❌ {description}: FAILED (Status: {response.status_code})")
                print(f"   Response: {response.text}")
                
        except requests.exceptions.RequestException as e:
            print(f"❌ {description}: ERROR - {e}")

def show_testing_instructions():
    """Show instructions for testing notifications"""
    print("\n" + "="*80)
    print("📋 NOTIFICATION TESTING INSTRUCTIONS")
    print("="*80)
    
    print(f"\n👤 Test User ID: {TEST_USER_ID}")
    print(f"🌐 Backend URL: {BACKEND_URL}")
    
    print("\n🔧 STEP 1: Start the Backend")
    print("   In a terminal, run:")
    print("   cd kilekitabu-backend")
    print("   python app.py")
    
    print("\n🔧 STEP 2: Test Notifications")
    print("   In another terminal, run:")
    print("   cd kilekitabu-backend")
    print("   python test_notifications_simple.py")
    
    print("\n🔧 STEP 3: Check Android App")
    print("   1. Make sure your Android app is running")
    print("   2. Check if you receive notifications")
    print("   3. Go to the Notifications screen in the app")
    print("   4. Tap on a notification to open the SMS screen")
    
    print("\n🔧 STEP 4: Manual API Testing")
    print("   You can also test manually using curl or Postman:")
    print(f"   POST {BACKEND_URL}/send_notification")
    print(f"   Body: {{\"user_id\": \"{TEST_USER_ID}\"}}")
    
    print("\n🔧 STEP 5: Check Firebase")
    print("   Check your Firebase console to see if:")
    print("   1. Test debts are created")
    print("   2. FCM tokens are registered")
    print("   3. Notifications are being sent")
    
    print("\n📊 Expected Results:")
    print("   ✅ Backend should respond with success")
    print("   ✅ Android device should receive notifications")
    print("   ✅ Notifications should appear in the app")
    print("   ✅ Tapping notification should open SMS screen")
    
    print("\n🐛 Troubleshooting:")
    print("   ❌ No notifications received:")
    print("      - Check if FCM token is registered")
    print("      - Check if backend is running")
    print("      - Check if test debts exist")
    print("   ❌ Backend errors:")
    print("      - Check Firebase credentials")
    print("      - Check if all dependencies are installed")
    print("      - Check backend logs")

def main():
    """Main function"""
    print("🚀 Setting up notification testing...")
    print(f"👤 Test User ID: {TEST_USER_ID}")
    print("="*60)
    
    # Create test debt info
    test_debt_id, test_debt, phone_number = create_test_debt_for_notifications()
    
    # Test backend connection
    backend_running = test_backend_connection()
    
    if backend_running:
        # Test notification endpoints
        test_notification_endpoints()
    else:
        print("\n⚠️  Backend is not running. Please start it first.")
    
    # Show testing instructions
    show_testing_instructions()
    
    print("\n✅ Setup complete! Follow the instructions above to test notifications.")

if __name__ == "__main__":
    main()
