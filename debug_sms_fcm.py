#!/usr/bin/env python3
"""
Debug SMS reminder FCM integration
"""

import requests
import json

def debug_sms_fcm_integration():
    """Debug why FCM notifications aren't being sent with SMS reminders"""
    
    print("🔍 Debugging SMS + FCM Integration")
    print("=" * 50)
    
    # Test 1: Check if FCM service is available
    print("📱 Test 1: Checking FCM service availability...")
    try:
        response = requests.get('http://localhost:5000/api/notifications/tokens')
        if response.status_code == 200:
            tokens_data = response.json()
            print(f"✅ FCM service is working - found {len(tokens_data.get('tokens', {}))} tokens")
        else:
            print(f"❌ FCM service check failed: {response.status_code}")
    except Exception as e:
        print(f"❌ FCM service check error: {e}")
    
    # Test 2: Check SMS reminder status
    print("\n📱 Test 2: Checking SMS reminder status...")
    try:
        response = requests.get('http://localhost:5000/api/sms-reminders/status')
        if response.status_code == 200:
            status = response.json()
            print(f"✅ SMS reminder service is running: {status.get('is_running')}")
            print(f"   Next run: {status.get('next_run')}")
            print(f"   Scheduled jobs: {status.get('scheduled_jobs')}")
        else:
            print(f"❌ SMS reminder status check failed: {response.status_code}")
    except Exception as e:
        print(f"❌ SMS reminder status check error: {e}")
    
    # Test 3: Run SMS reminder check and look for FCM logs
    print("\n📱 Test 3: Running SMS reminder check (watch for FCM logs)...")
    print("   (Check the backend console for FCM notification logs)")
    try:
        response = requests.post('http://localhost:5000/api/sms-reminders/check?days=20')
        if response.status_code == 200:
            result = response.json()
            print(f"✅ SMS reminder check completed!")
            print(f"   Status: {result.get('status')}")
            print(f"   Reminders sent: {result.get('reminders_sent', 0)}")
            print(f"   Errors: {result.get('errors', [])}")
            
            if result.get('reminders_sent', 0) > 0:
                print("🔍 Look for FCM notification logs in the backend console")
                print("   Expected logs: 'FCM notification sent to user...' or 'FCM service not available'")
            else:
                print("ℹ️  No reminders sent - no FCM notifications expected")
        else:
            print(f"❌ SMS reminder check failed: {response.status_code}")
    except Exception as e:
        print(f"❌ SMS reminder check error: {e}")
    
    print("\n🎯 Debug Summary:")
    print("=" * 50)
    print("✅ FCM notifications work (manual test passed)")
    print("✅ SMS reminders work (10 reminders sent)")
    print("❓ FCM + SMS integration needs debugging")
    print("\n💡 Next steps:")
    print("   1. Check backend console for FCM logs during SMS reminder check")
    print("   2. Look for 'FCM service not available' or similar error messages")
    print("   3. Verify FCM service is properly passed to SMS reminder service")

if __name__ == "__main__":
    debug_sms_fcm_integration()
