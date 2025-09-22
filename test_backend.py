#!/usr/bin/env python3
"""
Simple test script to check backend notifications
"""

import requests
import time
import json

def test_backend():
    print("🧪 Testing Backend Notifications...")
    print("=" * 50)
    
    # Wait for backend to start
    print("⏳ Waiting for backend to start...")
    time.sleep(5)
    
    # Test backend health
    try:
        print("🔍 Testing backend health...")
        response = requests.get('http://localhost:5000/test', timeout=10)
        print(f"✅ Backend Status: {response.status_code}")
        print(f"Response: {response.json()}")
    except Exception as e:
        print(f"❌ Backend not running: {e}")
        return False
    
    # Test notification endpoints
    try:
        print("\n🔔 Testing due debts check...")
        response = requests.post('http://localhost:5000/api/notifications/check-due', timeout=10)
        print(f"Due debts check status: {response.status_code}")
        print(f"Response: {response.json()}")
    except Exception as e:
        print(f"Due debts check failed: {e}")
    
    # Test SMS reminders
    try:
        print("\n📱 Testing SMS reminders check...")
        response = requests.post('http://localhost:5000/api/sms-reminders/check', timeout=10)
        print(f"SMS reminders check status: {response.status_code}")
        print(f"Response: {response.json()}")
    except Exception as e:
        print(f"SMS reminders check failed: {e}")
    
    # Test manual notification
    try:
        print("\n📤 Testing manual notification...")
        test_data = {
            'user_id': 'GI7PPaaRh7hRogozJcDHt33RQEw2',
            'title': 'Test Notification',
            'body': 'This is a test notification from the backend'
        }
        response = requests.post('http://localhost:5000/api/notifications/test', json=test_data, timeout=10)
        print(f"Manual notification status: {response.status_code}")
        print(f"Response: {response.json()}")
    except Exception as e:
        print(f"Manual notification failed: {e}")
    
    print("\n" + "=" * 50)
    print("✅ Backend testing completed!")

if __name__ == "__main__":
    test_backend()
