#!/usr/bin/env python3
"""
Script to manually trigger debt notifications via API endpoints
"""

import requests
import json
from datetime import datetime

def trigger_due_debts():
    """Trigger today's debts check via API"""
    print("🔔 Triggering Today's Debts Check")
    print("=" * 40)
    
    try:
        # Replace with your actual backend URL
        url = "http://localhost:5000/api/trigger-due-debts"
        
        response = requests.post(url, timeout=30)
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Success: {result.get('message', 'No message')}")
            return True
        else:
            print(f"❌ Error: HTTP {response.status_code}")
            print(f"Response: {response.text}")
            return False
            
    except requests.exceptions.ConnectionError:
        print("❌ Error: Could not connect to backend server")
        print("💡 Make sure the backend is running on localhost:5000")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def trigger_overdue_debts():
    """Trigger overdue debts check via API"""
    print("\n🔔 Triggering Overdue Debts Check")
    print("=" * 40)
    
    try:
        # Replace with your actual backend URL
        url = "http://localhost:5000/api/trigger-overdue-debts"
        
        response = requests.post(url, timeout=30)
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Success: {result.get('message', 'No message')}")
            return True
        else:
            print(f"❌ Error: HTTP {response.status_code}")
            print(f"Response: {response.text}")
            return False
            
    except requests.exceptions.ConnectionError:
        print("❌ Error: Could not connect to backend server")
        print("💡 Make sure the backend is running on localhost:5000")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def check_backend_health():
    """Check if backend is running"""
    print("🏥 Checking Backend Health")
    print("=" * 40)
    
    try:
        # Replace with your actual backend URL
        url = "http://localhost:5000/api/health"
        
        response = requests.get(url, timeout=10)
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Backend is running: {result.get('message', 'OK')}")
            return True
        else:
            print(f"❌ Backend returned HTTP {response.status_code}")
            return False
            
    except requests.exceptions.ConnectionError:
        print("❌ Backend is not running or not accessible")
        print("💡 Start the backend with: python app.py")
        return False
    except Exception as e:
        print(f"❌ Error checking backend: {e}")
        return False

def main():
    """Main function"""
    print("🚀 Debt Notification Trigger Script")
    print("=" * 50)
    print(f"⏰ Current time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # Check backend health first
    if not check_backend_health():
        print("\n❌ Cannot proceed without backend. Exiting.")
        return
    
    print()
    
    # Trigger due debts check
    due_success = trigger_due_debts()
    
    # Trigger overdue debts check
    overdue_success = trigger_overdue_debts()
    
    print("\n" + "=" * 50)
    print("📊 Summary:")
    print(f"  Today's debts: {'✅ Success' if due_success else '❌ Failed'}")
    print(f"  Overdue debts: {'✅ Success' if overdue_success else '❌ Failed'}")
    print("=" * 50)

if __name__ == "__main__":
    main()
