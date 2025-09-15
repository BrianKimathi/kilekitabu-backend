#!/usr/bin/env python3
"""
Direct FCM test without Flask backend
"""
import os
import sys

# Add current directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

try:
    import firebase_admin
    from firebase_admin import credentials, messaging
    print("✅ Firebase Admin SDK imported successfully")
except ImportError as e:
    print(f"❌ Failed to import Firebase Admin SDK: {e}")
    print("Please install firebase-admin: pip install firebase-admin")
    sys.exit(1)

def test_fcm():
    """Test FCM functionality directly"""
    try:
        # Initialize Firebase Admin SDK
        cred_path = 'kile-kitabu-firebase-adminsdk-pjk21-68cbd0c3b4.json'
        if not os.path.exists(cred_path):
            print(f"❌ Firebase credentials file not found: {cred_path}")
            return False
        
        cred = credentials.Certificate(cred_path)
        firebase_admin.initialize_app(cred, {
            'databaseURL': 'https://kile-kitabu-default-rtdb.firebaseio.com'
        })
        print("✅ Firebase Admin SDK initialized successfully")
        
        # Test FCM token (from your Android app logs)
        fcm_token = "dXGAET7eS6i8kLXIyGrkJg:APA91bHLM3vqHzXPnF5YKXmJcMkuRQPIcq8dxWQJWjbuHdslmt7ZiAdqzMvSM-FVahCWC4Y_qOWm8FbXK2y24PPbUaPJAXf4dFr1EyJWw_MGBjhwX1ETIwc"
        
        # Create test notification
        notification = messaging.Notification(
            title="🧪 Test FCM Notification",
            body="This is a direct test from the backend!"
        )
        
        data = {
            "type": "test",
            "debt_id": "test_123",
            "click_action": "com.jeff.kilekitabu.DEBT_NOTIFICATION"
        }
        
        android_config = messaging.AndroidConfig(
            priority=messaging.AndroidConfig.Priority.HIGH,
            notification=messaging.AndroidNotification(
                icon="ic_notification",
                color="#0C57A6",
                sound="default",
                click_action="com.jeff.kilekitabu.DEBT_NOTIFICATION"
            )
        )
        
        message = messaging.Message(
            notification=notification,
            data=data,
            android=android_config,
            token=fcm_token
        )
        
        # Send notification
        print("📤 Sending FCM notification...")
        response = messaging.send(message)
        print(f"✅ FCM notification sent successfully: {response}")
        return True
        
    except Exception as e:
        print(f"❌ FCM test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("🚀 Testing FCM functionality directly...")
    print("=" * 50)
    
    success = test_fcm()
    
    if success:
        print("\n✅ FCM test completed successfully!")
        print("Check your Android device for the notification.")
    else:
        print("\n❌ FCM test failed!")
        print("Please check the error messages above.")

