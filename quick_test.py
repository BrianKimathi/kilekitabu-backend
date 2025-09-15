import requests

# Quick FCM test
print("🚀 Testing FCM notification...")

try:
    response = requests.post('http://localhost:5000/api/notifications/test', 
                           json={'user_id': 'GI7PPaaRh7hRogozJcDHt33RQEw2'})
    print(f"Status: {response.status_code}")
    print(f"Response: {response.text}")
    
    if response.status_code == 200:
        print("✅ Notification sent successfully!")
        print("📱 Check your Android device for the notification!")
    else:
        print("❌ Failed to send notification")
        
except Exception as e:
    print(f"❌ Error: {e}")

