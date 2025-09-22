#!/usr/bin/env python3
"""
Create a test debt that's due today for testing the message system
"""

import firebase_admin
from firebase_admin import credentials, db
import datetime
import os
import sys

def create_test_debt_today():
    """Create a test debt due today"""
    
    # Initialize Firebase
    try:
        # Check if Firebase is already initialized
        try:
            firebase_admin.get_app()
            print("Firebase already initialized")
        except ValueError:
            # Initialize Firebase
            cred_path = "kile-kitabu-firebase-adminsdk-pjk21-68cbd0c3b4.json"
            if os.path.exists(cred_path):
                cred = credentials.Certificate(cred_path)
                firebase_admin.initialize_app(cred, {
                    'databaseURL': 'https://kile-kitabu-default-rtdb.firebaseio.com/'
                })
                print("Firebase initialized successfully")
            else:
                print(f"Firebase credentials file not found: {cred_path}")
                return False
    except Exception as e:
        print(f"Firebase initialization error: {e}")
        return False
    
    # Test user ID (replace with actual user ID)
    user_id = "GI7PPaaRh7hRogozJcDHt33RQEw2"
    
    # Calculate today's date in milliseconds
    today = datetime.datetime.now()
    today_ms = int(today.timestamp() * 1000)
    
    # Create test debt data
    test_debt_id = f"test_debt_today_{int(datetime.datetime.now().timestamp())}"
    test_debt = {
        "debtAmount": "2500.00",
        "balance": "2500.00",
        "description": "Test debt for message system - due today",
        "date": today.strftime("%d/%m/%Y"),
        "dueDate": today_ms,
        "isComplete": False,
        "timestamp": today_ms
    }
    
    # Phone number for the test debt
    phone_number = "+254720239719"
    
    try:
        # Get existing user debts
        user_debts_ref = db.reference(f'UserDebts/{user_id}')
        user_debts = user_debts_ref.get()
        
        if not user_debts:
            user_debts = {}
        
        # Check if phone number group exists
        if phone_number not in user_debts:
            user_debts[phone_number] = {
                "accountName": "Test Debtor Today",
                "phoneNumber": phone_number,
                "debts": {}
            }
        
        # Add the test debt
        user_debts[phone_number]["debts"][test_debt_id] = test_debt
        
        # Update Firebase
        user_debts_ref.set(user_debts)
        
        print(f"✅ Test debt created successfully!")
        print(f"📱 User ID: {user_id}")
        print(f"📞 Phone: {phone_number}")
        print(f"🆔 Debt ID: {test_debt_id}")
        print(f"💰 Amount: {test_debt['debtAmount']}")
        print(f"📅 Due Date: {today.strftime('%d/%m/%Y')}")
        print(f"⏰ Due Date (ms): {today_ms}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error creating test debt: {e}")
        return False

if __name__ == "__main__":
    print("🚀 Creating test debt due today...")
    success = create_test_debt_today()
    
    if success:
        print("\n✅ Test debt created! Now you can:")
        print("1. Run the SMS reminder check to trigger individual notifications")
        print("2. Test the Android app notification handling")
        print("3. Test the message screen functionality")
    else:
        print("\n❌ Failed to create test debt")
        sys.exit(1)
