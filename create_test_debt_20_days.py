#!/usr/bin/env python3
"""
Create a test debt that's due in 20 days to test FCM notifications
"""

import requests
import json
import datetime
from firebase_admin import db

def create_test_debt_due_in_20_days():
    """Create a test debt that's due in 20 days"""
    
    print("🧪 Creating test debt due in 20 days")
    print("=" * 50)
    
    # Calculate due date (20 days from now)
    current_time = datetime.datetime.now()
    due_date = current_time + datetime.timedelta(days=20)
    due_date_timestamp = int(due_date.timestamp() * 1000)
    
    # Test debt data
    test_debt = {
        'id': f'test_debt_20_days_{int(current_time.timestamp())}',
        'accountName': 'Test Debtor 20 Days',
        'phoneNumber': '0703543847',
        'debtAmount': '2500.00',
        'balance': '2500.00',
        'description': 'Test debt for 20-day notification',
        'date': due_date.strftime('%d/%m/%Y'),
        'dueDate': due_date_timestamp,
        'isComplete': False,
        'receiptCamera': '',
        'receiptGallery': ''
    }
    
    print(f"📝 Test debt details:")
    print(f"   Account: {test_debt['accountName']}")
    print(f"   Phone: {test_debt['phoneNumber']}")
    print(f"   Amount: {test_debt['debtAmount']}")
    print(f"   Due Date: {test_debt['date']} ({due_date_timestamp})")
    print(f"   Debt ID: {test_debt['id']}")
    
    try:
        # Add to Firebase for user GI7PPaaRh7hRogozJcDHt33RQEw2
        user_id = 'GI7PPaaRh7hRogozJcDHt33RQEw2'
        phone_number = test_debt['phoneNumber']
        
        # Firebase path: UserDebts/{user_id}/{phone_number}/debts/{debt_id}
        debt_path = f'UserDebts/{user_id}/{phone_number}/debts/{test_debt["id"]}'
        
        # Create the debt structure
        debt_data = {
            'debtAmount': test_debt['debtAmount'],
            'balance': test_debt['balance'],
            'complete': test_debt['isComplete'],
            'date': test_debt['date'],
            'description': test_debt['description'],
            'id': test_debt['id'],
            'receiptGallery': test_debt['receiptGallery'],
            'receiptCamera': test_debt['receiptCamera'],
            'dueDate': test_debt['dueDate'],
            'isComplete': test_debt['isComplete']
        }
        
        # Also set the phone number group data
        phone_group_data = {
            'accountName': test_debt['accountName'],
            'phoneNumber': test_debt['phoneNumber'],
            'debts': {
                test_debt['id']: debt_data
            }
        }
        
        # Update Firebase
        db.reference(f'UserDebts/{user_id}/{phone_number}').set(phone_group_data)
        
        print("✅ Test debt created successfully in Firebase!")
        print(f"   Path: {debt_path}")
        
        # Now test the SMS reminder check
        print("\n📱 Testing SMS reminder check with new debt...")
        response = requests.post('http://localhost:5000/api/sms-reminders/check?days=20')
        
        if response.status_code == 200:
            result = response.json()
            print("✅ SMS reminder check completed!")
            print(f"   Status: {result.get('status')}")
            print(f"   Reminders sent: {result.get('reminders_sent', 0)}")
            print(f"   Window days: {result.get('window_days', 'N/A')}")
            print(f"   Errors: {result.get('errors', [])}")
            
            if result.get('reminders_sent', 0) > 0:
                print("🎉 FCM notification should have been sent to your device!")
            else:
                print("ℹ️  No reminders sent - check the logs for details")
        else:
            print(f"❌ SMS reminder check failed: {response.status_code}")
            print(f"   Error: {response.text}")
            
    except Exception as e:
        print(f"❌ Error creating test debt: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    create_test_debt_due_in_20_days()
