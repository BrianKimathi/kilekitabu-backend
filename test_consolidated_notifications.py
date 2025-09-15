#!/usr/bin/env python3
"""
Test: Consolidated Debt Notifications
"""

import requests
import json
from datetime import datetime

def test_consolidated_notifications():
    """Test the consolidated notification system"""
    print("🎯 Testing Consolidated Debt Notifications")
    print("=" * 60)
    
    # Test 1: Check due debts (should send consolidated notification)
    print("\n1️⃣ Testing due debt check...")
    try:
        response = requests.post('http://localhost:5000/api/notifications/check-due')
        print(f"   Status: {response.status_code}")
        print(f"   Response: {response.text}")
        
        if response.status_code == 200:
            print("   ✅ Due debt check completed!")
        else:
            print("   ❌ Due debt check failed!")
            
    except Exception as e:
        print(f"   Error: {e}")
    
    # Test 2: Send manual consolidated notification
    print("\n2️⃣ Testing manual consolidated notification...")
    test_data = {
        "user_id": "1nvyRCYN9lTYk5hbnn8cA95Xgg73",
        "type": "debt_due_consolidated",
        "title": "You have 3 debts due today!",
        "body": "Total amount due: KSh 15,000. Tap to view all due debts.",
        "debt_count": "3",
        "total_amount": "15000",
        "due_date": datetime.now().date().strftime('%Y-%m-%d'),
        "debts": [
            {
                "id": "debt_001",
                "account_name": "John Doe",
                "account_phone": "+254712345678",
                "amount": "5000",
                "due_date": datetime.now().date().strftime('%Y-%m-%d'),
                "description": "Laptop purchase"
            },
            {
                "id": "debt_002", 
                "account_name": "Jane Smith",
                "account_phone": "+254712345679",
                "amount": "7000",
                "due_date": datetime.now().date().strftime('%Y-%m-%d'),
                "description": "Rent payment"
            },
            {
                "id": "debt_003",
                "account_name": "Mike Johnson", 
                "account_phone": "+254712345680",
                "amount": "3000",
                "due_date": datetime.now().date().strftime('%Y-%m-%d'),
                "description": "Utility bill"
            }
        ]
    }
    
    try:
        response = requests.post('http://localhost:5000/api/notifications/send', 
                               json=test_data,
                               headers={'Content-Type': 'application/json'})
        print(f"   Status: {response.status_code}")
        print(f"   Response: {response.text}")
        
        if response.status_code == 200:
            print("   ✅ Consolidated notification sent!")
            print("   📱 Check your Android device for the notification!")
        else:
            print("   ❌ Consolidated notification failed!")
            
    except Exception as e:
        print(f"   Error: {e}")
    
    # Test 3: Test single debt notification
    print("\n3️⃣ Testing single debt notification...")
    single_debt_data = {
        "user_id": "1nvyRCYN9lTYk5hbnn8cA95Xgg73",
        "type": "debt_due_consolidated",
        "title": "Debt Due Today!",
        "body": "You have 1 debt due today. Amount: KSh 5,000",
        "debt_count": "1",
        "total_amount": "5000",
        "due_date": datetime.now().date().strftime('%Y-%m-%d'),
        "debts": [
            {
                "id": "debt_001",
                "account_name": "John Doe",
                "account_phone": "+254712345678",
                "amount": "5000",
                "due_date": datetime.now().date().strftime('%Y-%m-%d'),
                "description": "Laptop purchase"
            }
        ]
    }
    
    try:
        response = requests.post('http://localhost:5000/api/notifications/send', 
                               json=single_debt_data,
                               headers={'Content-Type': 'application/json'})
        print(f"   Status: {response.status_code}")
        print(f"   Response: {response.text}")
        
        if response.status_code == 200:
            print("   ✅ Single debt notification sent!")
        else:
            print("   ❌ Single debt notification failed!")
            
    except Exception as e:
        print(f"   Error: {e}")

def main():
    test_consolidated_notifications()
    
    print("\n" + "=" * 60)
    print("🎉 Consolidated notification tests completed!")
    print("📱 Check your Android device for notifications!")
    print("💡 The notification should open the DebtNotificationsActivity")

if __name__ == "__main__":
    main()
