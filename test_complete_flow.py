#!/usr/bin/env python3
"""
Complete test flow for the debt message system
1. Create a test debt due today
2. Trigger SMS reminder check (should send individual notifications)
3. Test debt details API
4. Test manual SMS API
"""

import requests
import json
import datetime
import time
import firebase_admin
from firebase_admin import credentials, db
import os

# Configuration
BACKEND_URL = "http://localhost:5000"
TEST_USER_ID = "GI7PPaaRh7hRogozJcDHt33RQEw2"

def initialize_firebase():
    """Initialize Firebase connection"""
    try:
        firebase_admin.get_app()
        print("✅ Firebase already initialized")
        return True
    except ValueError:
        try:
            cred_path = "kile-kitabu-firebase-adminsdk-pjk21-68cbd0c3b4.json"
            if os.path.exists(cred_path):
                cred = credentials.Certificate(cred_path)
                firebase_admin.initialize_app(cred, {
                    'databaseURL': 'https://kile-kitabu-default-rtdb.firebaseio.com/'
                })
                print("✅ Firebase initialized successfully")
                return True
            else:
                print(f"❌ Firebase credentials file not found: {cred_path}")
                return False
        except Exception as e:
            print(f"❌ Firebase initialization error: {e}")
            return False

def create_test_debt():
    """Create a test debt due today"""
    print("📝 Creating test debt due today...")
    
    # Calculate today's date in milliseconds
    today = datetime.datetime.now()
    today_ms = int(today.timestamp() * 1000)
    
    # Create test debt data
    test_debt_id = f"test_debt_today_{int(datetime.datetime.now().timestamp())}"
    test_debt = {
        "debtAmount": "3000.00",
        "balance": "3000.00",
        "description": "Test debt for complete flow testing - due today",
        "date": today.strftime("%d/%m/%Y"),
        "dueDate": today_ms,
        "isComplete": False,
        "timestamp": today_ms
    }
    
    # Phone number for the test debt
    phone_number = "+254720239719"
    
    try:
        # Get existing user debts
        user_debts_ref = db.reference(f'UserDebts/{TEST_USER_ID}')
        user_debts = user_debts_ref.get()
        
        if not user_debts:
            user_debts = {}
        
        # Check if phone number group exists
        if phone_number not in user_debts:
            user_debts[phone_number] = {
                "accountName": "Test Debtor Complete Flow",
                "phoneNumber": phone_number,
                "debts": {}
            }
        
        # Add the test debt
        user_debts[phone_number]["debts"][test_debt_id] = test_debt
        
        # Update Firebase
        user_debts_ref.set(user_debts)
        
        print(f"✅ Test debt created successfully!")
        print(f"🆔 Debt ID: {test_debt_id}")
        print(f"💰 Amount: {test_debt['debtAmount']}")
        print(f"📅 Due Date: {today.strftime('%d/%m/%Y')}")
        
        return test_debt_id
        
    except Exception as e:
        print(f"❌ Error creating test debt: {e}")
        return None


def test_debt_details_api(debt_id):
    """Test the debt details API"""
    print(f"🔍 Testing debt details API for debt: {debt_id}")
    
    try:
        response = requests.get(f"{BACKEND_URL}/api/debt/{debt_id}?user_id={TEST_USER_ID}")
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Debt details API response:")
            print(f"   Status: {data.get('status')}")
            if 'debt' in data:
                debt = data['debt']
                print(f"   Debtor: {debt.get('accountName')}")
                print(f"   Phone: {debt.get('phoneNumber')}")
                print(f"   Amount: {debt.get('debtAmount')}")
                print(f"   Description: {debt.get('description')}")
            return True
        else:
            print(f"❌ Debt details API failed: {response.status_code} - {response.text}")
            return False
    except Exception as e:
        print(f"❌ Error testing debt details API: {e}")
        return False

def test_manual_sms_api():
    """Test the manual SMS API"""
    print("📱 Testing manual SMS API...")
    
    sms_data = {
        "phone_number": "+254720239719",
        "message": "Test message from complete flow testing - Hello [DEBTOR_NAME], you have a debt of [AMOUNT] due on [DUE_DATE]. Please settle it soon!",
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
            print(f"✅ Manual SMS API response:")
            print(f"   Status: {data.get('status')}")
            print(f"   Message: {data.get('message')}")
            return True
        else:
            print(f"❌ Manual SMS API failed: {response.status_code} - {response.text}")
            return False
    except Exception as e:
        print(f"❌ Error testing manual SMS API: {e}")
        return False

def test_notification_api():
    """Test the notification API with proper format"""
    print("🔔 Testing notification API with improved format...")
    
    notification_data = {
        "user_id": TEST_USER_ID,
        "title": "💰 Debt Due Today!",
        "body": "Debt notification: Test Debtor Complete Flow debt of KSh 3,000.00 due date closing in today.",
        "data": {
            "type": "debt_due_reminder",
            "debt_id": "test_debt_123",
            "debtor_name": "Test Debtor Complete Flow",
            "debtor_phone": "+254720239719",
            "amount": "3000.00",
            "due_date": datetime.datetime.now().strftime("%d/%m/%Y"),
            "days_until_due": "0",
            "title": "💰 Debt Due Today!",
            "body": "Debt notification: Test Debtor Complete Flow debt of KSh 3,000.00 due date closing in today."
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
            print(f"✅ Notification API response:")
            print(f"   Status: {data.get('status')}")
            print(f"   Message: {data.get('message')}")
            return True
        else:
            print(f"❌ Notification API failed: {response.status_code} - {response.text}")
            return False
    except Exception as e:
        print(f"❌ Error testing notification API: {e}")
        return False

def main():
    """Run the complete test flow"""
    print("🚀 Starting complete debt message system test flow...")
    print(f"📡 Backend URL: {BACKEND_URL}")
    print(f"👤 Test User ID: {TEST_USER_ID}")
    print("=" * 60)
    
    # Step 1: Initialize Firebase
    if not initialize_firebase():
        print("❌ Cannot proceed without Firebase connection")
        return
    
    # Step 2: Create test debt
    debt_id = create_test_debt()
    if not debt_id:
        print("❌ Cannot proceed without test debt")
        return
    
    print("\n" + "=" * 60)
    
    # Step 3: Test SMS reminder check for 5 days (should send individual notifications)
    print("🔔 Testing SMS reminder check for 5 days...")
    try:
        response = requests.post(f"{BACKEND_URL}/api/sms-reminders/check?days=5")
        if response.status_code == 200:
            data = response.json()
            print(f"✅ 5-day SMS reminder check response:")
            print(f"   Status: {data.get('status')}")
            print(f"   Reminders sent: {data.get('reminders_sent', 0)}")
            print(f"   Errors: {data.get('errors', [])}")
        else:
            print(f"❌ 5-day SMS reminder check failed: {response.status_code} - {response.text}")
    except Exception as e:
        print(f"❌ Error testing 5-day SMS reminder check: {e}")
    
    print("\n" + "=" * 60)
    
    # Step 4: Test debt details API
    test_debt_details_api(debt_id)
    
    print("\n" + "=" * 60)
    
    # Step 5: Test manual SMS API
    test_manual_sms_api()
    
    print("\n" + "=" * 60)
    
    # Step 6: Test notification API
    test_notification_api()
    
    print("\n" + "=" * 60)
    print("✅ Complete test flow finished!")
    print("\n📋 Next steps for Android testing:")
    print("1. Make sure the Android app is running")
    print("2. Check if you received individual notifications")
    print("3. Tap on a notification to open the message screen")
    print("4. Test sending SMS from the message screen")
    print("5. Verify placeholder replacement works correctly")

if __name__ == "__main__":
    main()
