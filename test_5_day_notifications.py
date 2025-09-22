#!/usr/bin/env python3
"""
Test script for 5-day debt notifications
Creates test debts with different due dates and tests the notification system
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

def create_test_debts_for_5_days():
    """Create test debts with different due dates (today, 1 day, 3 days, 5 days)"""
    print("📝 Creating test debts for 5-day notification testing...")
    
    test_debts = []
    current_time = datetime.datetime.now()
    
    # Create debts for different days
    due_dates = [
        (0, "Today", "Test Debtor Today"),
        (1, "Tomorrow", "Test Debtor Tomorrow"), 
        (3, "3 Days", "Test Debtor 3 Days"),
        (5, "5 Days", "Test Debtor 5 Days")
    ]
    
    for days_ahead, day_name, debtor_name in due_dates:
        due_date = current_time + datetime.timedelta(days=days_ahead)
        due_date_ms = int(due_date.timestamp() * 1000)
        
        # Create test debt data
        test_debt_id = f"test_debt_{days_ahead}days_{int(datetime.datetime.now().timestamp())}"
        test_debt = {
            "debtAmount": f"{(days_ahead + 1) * 1000}.00",
            "balance": f"{(days_ahead + 1) * 1000}.00",
            "description": f"Test debt for {day_name} notification testing",
            "date": due_date.strftime("%d/%m/%Y"),
            "dueDate": due_date_ms,
            "isComplete": False,
            "timestamp": due_date_ms
        }
        
        # Phone number for the test debt
        phone_number = f"+25472023971{days_ahead}"
        
        try:
            # Get existing user debts
            user_debts_ref = db.reference(f'UserDebts/{TEST_USER_ID}')
            user_debts = user_debts_ref.get()
            
            if not user_debts:
                user_debts = {}
            
            # Check if phone number group exists
            if phone_number not in user_debts:
                user_debts[phone_number] = {
                    "accountName": debtor_name,
                    "phoneNumber": phone_number,
                    "debts": {}
                }
            
            # Add the test debt
            user_debts[phone_number]["debts"][test_debt_id] = test_debt
            
            # Update Firebase
            user_debts_ref.set(user_debts)
            
            test_debts.append({
                "debt_id": test_debt_id,
                "debtor_name": debtor_name,
                "phone": phone_number,
                "amount": test_debt["debtAmount"],
                "due_date": due_date.strftime("%d/%m/%Y"),
                "days_ahead": days_ahead
            })
            
            print(f"✅ {day_name} debt created: {debtor_name} - KSh {test_debt['debtAmount']} due {due_date.strftime('%d/%m/%Y')}")
            
        except Exception as e:
            print(f"❌ Error creating {day_name} debt: {e}")
    
    return test_debts

def test_5_day_notifications():
    """Test notifications for debts due in the next 5 days"""
    print("🔔 Testing 5-day notification system...")
    
    try:
        response = requests.post(f"{BACKEND_URL}/api/sms-reminders/check?days=5")
        if response.status_code == 200:
            data = response.json()
            print(f"✅ 5-day notification test response:")
            print(f"   Status: {data.get('status')}")
            print(f"   Reminders sent: {data.get('reminders_sent', 0)}")
            print(f"   Errors: {data.get('errors', [])}")
            
            if data.get('reminders_sent', 0) > 0:
                print("🎉 Notifications sent successfully! Check your Android device for individual notifications.")
            else:
                print("ℹ️  No notifications sent - this might be because no debts are due in the next 5 days")
            
            return True
        else:
            print(f"❌ 5-day notification test failed: {response.status_code} - {response.text}")
            return False
    except Exception as e:
        print(f"❌ Error testing 5-day notifications: {e}")
        return False

def test_individual_debt_details(test_debts):
    """Test getting details for each test debt"""
    print("🔍 Testing individual debt details...")
    
    for debt in test_debts:
        try:
            response = requests.get(f"{BACKEND_URL}/api/debt/{debt['debt_id']}?user_id={TEST_USER_ID}")
            if response.status_code == 200:
                data = response.json()
                if data.get('status') == 'success':
                    debt_info = data.get('debt', {})
                    print(f"✅ {debt['debtor_name']}: KSh {debt_info.get('debtAmount')} due {debt_info.get('date')}")
                else:
                    print(f"❌ Failed to get details for {debt['debtor_name']}")
            else:
                print(f"❌ API error for {debt['debtor_name']}: {response.status_code}")
        except Exception as e:
            print(f"❌ Error getting details for {debt['debtor_name']}: {e}")

def main():
    """Run the 5-day notification test"""
    print("🚀 Starting 5-day debt notification test...")
    print(f"📡 Backend URL: {BACKEND_URL}")
    print(f"👤 Test User ID: {TEST_USER_ID}")
    print("=" * 60)
    
    # Step 1: Initialize Firebase
    if not initialize_firebase():
        print("❌ Cannot proceed without Firebase connection")
        return
    
    # Step 2: Create test debts for different days
    test_debts = create_test_debts_for_5_days()
    if not test_debts:
        print("❌ Cannot proceed without test debts")
        return
    
    print("\n" + "=" * 60)
    
    # Step 3: Test 5-day notifications
    test_5_day_notifications()
    
    print("\n" + "=" * 60)
    
    # Step 4: Test individual debt details
    test_individual_debt_details(test_debts)
    
    print("\n" + "=" * 60)
    print("✅ 5-day notification test completed!")
    print("\n📋 Expected behavior:")
    print("1. You should receive individual notifications for each debt due in the next 5 days")
    print("2. Each notification should show: 'Debt notification: {name} debt of KSh {amount} due date closing in X days'")
    print("3. Tapping a notification should open the message screen")
    print("4. The message screen should show debt details and allow SMS composition")
    print("\n🔍 Check your Android device for notifications!")

if __name__ == "__main__":
    main()
