import requests
import time
import json

# FCM Test with 10-second delay
print("🚀 FCM Delayed Test - Notification will be sent in 10 seconds...")

# Countdown
for i in range(10, 0, -1):
    print(f"⏰ Sending notification in {i} seconds...")
    time.sleep(1)

print("📤 Sending FCM notification now...")

# Test data
test_data = {
    "user_id": "GI7PPaaRh7hRogozJcDHt33RQEw2",  # Your user ID
    "type": "test",
    "title": "Test Notification - 10 Second Delay",
    "body": "This is a test notification sent after a 10-second delay! 🎉"
}

try:
    response = requests.post('http://localhost:5000/api/notifications/test', 
                           json=test_data)
    
    print(f"Status Code: {response.status_code}")
    print(f"Response: {response.text}")
    
    if response.status_code == 200:
        print("✅ Notification sent successfully!")
        print("📱 Check your Android device for the notification!")
    else:
        print("❌ Failed to send notification")
        
except Exception as e:
    print(f"❌ Error: {e}")
