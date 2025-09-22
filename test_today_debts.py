#!/usr/bin/env python3
"""
Test script to check today's debts and trigger notifications
"""

import sys
import os
from datetime import datetime, timedelta

# Add the current directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Initialize Firebase Admin SDK
import firebase_admin
from firebase_admin import credentials, db

def initialize_firebase():
    """Initialize Firebase Admin SDK"""
    try:
        # Check if Firebase is already initialized
        firebase_admin.get_app()
        print("✅ Firebase already initialized")
        return True
    except ValueError:
        # Firebase not initialized, initialize it
        try:
            credentials_path = 'kile-kitabu-firebase-adminsdk-pjk21-68cbd0c3b4.json'
            
            if os.path.exists(credentials_path):
                cred = credentials.Certificate(credentials_path)
                firebase_admin.initialize_app(cred, {
                    'databaseURL': 'https://kile-kitabu-default-rtdb.firebaseio.com/'
                })
                print("✅ Firebase initialized successfully")
                return True
            else:
                print(f"❌ Firebase credentials file not found: {credentials_path}")
                return False
        except Exception as e:
            print(f"❌ Error initializing Firebase: {e}")
            return False

from simple_debt_scheduler import SimpleDebtScheduler
from fcm_v1_service import MockFCMV1Service

def test_today_debts():
    """Test the today's debts notification system"""
    print("🧪 Testing Today's Debts Notification System")
    print("=" * 50)
    
    # Initialize the scheduler with mock FCM service
    mock_fcm = MockFCMV1Service()
    scheduler = SimpleDebtScheduler(mock_fcm)
    
    print("📅 Current time:", datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
    print("🔍 Checking for debts due today...")
    print()
    
    # Test the check_due_debts method
    try:
        scheduler.check_due_debts()
        print("✅ Today's debts check completed successfully")
    except Exception as e:
        print(f"❌ Error checking today's debts: {e}")
        import traceback
        traceback.print_exc()
    
    print()
    print("🔍 Checking for overdue debts...")
    
    # Test the check_overdue_debts method
    try:
        scheduler.check_overdue_debts()
        print("✅ Overdue debts check completed successfully")
    except Exception as e:
        print(f"❌ Error checking overdue debts: {e}")
        import traceback
        traceback.print_exc()

def test_manual_notification():
    """Test sending a manual notification"""
    print("\n" + "=" * 50)
    print("🧪 Testing Manual Notification")
    print("=" * 50)
    
    # Initialize the scheduler with mock FCM service
    mock_fcm = MockFCMV1Service()
    scheduler = SimpleDebtScheduler(mock_fcm)
    
    # Test data
    test_user_id = "test_user_123"
    test_title = "Test Debt Notification"
    test_body = "This is a test notification for today's debts"
    test_data = {
        "type": "test_notification",
        "debt_count": "2",
        "total_amount": "1500.00"
    }
    
    print(f"📤 Sending test notification to user: {test_user_id}")
    print(f"📝 Title: {test_title}")
    print(f"📄 Body: {test_body}")
    print(f"📊 Data: {test_data}")
    
    try:
        success = scheduler.send_manual_notification(
            test_user_id, 
            test_title, 
            test_body, 
            test_data
        )
        
        if success:
            print("✅ Manual notification sent successfully")
        else:
            print("❌ Manual notification failed")
            
    except Exception as e:
        print(f"❌ Error sending manual notification: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    print("🚀 Starting Debt Notification Tests")
    print("=" * 50)
    
    # Initialize Firebase first
    if not initialize_firebase():
        print("❌ Failed to initialize Firebase. Exiting.")
        sys.exit(1)
    
    # Test today's debts
    test_today_debts()
    
    # Test manual notification
    test_manual_notification()
    
    print("\n" + "=" * 50)
    print("✅ All tests completed")
    print("=" * 50)
