import requests
import json

def test_backend_health():
    """Test if backend is running and accessible"""
    print("🔍 Testing Backend Health...")
    print("=" * 40)
    
    try:
        # Test 1: Health check
        print("1️⃣ Testing health endpoint...")
        response = requests.get('http://localhost:5000/api/health', timeout=5)
        print(f"   Status: {response.status_code}")
        print(f"   Response: {response.text}")
        
        if response.status_code == 200:
            print("   ✅ Health check passed")
        else:
            print("   ❌ Health check failed")
            
    except requests.exceptions.ConnectionError:
        print("   ❌ Cannot connect to backend")
        print("   🔍 Make sure backend is running: python app.py")
        return False
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return False
    
    try:
        # Test 2: FCM tokens endpoint
        print("\n2️⃣ Testing FCM tokens endpoint...")
        response = requests.get('http://localhost:5000/api/notifications/tokens', timeout=5)
        print(f"   Status: {response.status_code}")
        print(f"   Response: {response.text}")
        
        if response.status_code == 200:
            print("   ✅ FCM tokens endpoint accessible")
        else:
            print("   ❌ FCM tokens endpoint failed")
            
    except Exception as e:
        print(f"   ❌ FCM tokens test error: {e}")
    
    try:
        # Test 3: Test notification endpoint
        print("\n3️⃣ Testing FCM test endpoint...")
        test_data = {
            "user_id": "GI7PPaaRh7hRogozJcDHt33RQEw2",
            "type": "test",
            "title": "Health Check Test",
            "body": "Testing if FCM endpoint is working"
        }
        
        print(f"   📋 Sending test data: {json.dumps(test_data, indent=2)}")
        response = requests.post('http://localhost:5000/api/notifications/test', 
                               json=test_data, 
                               headers={'Content-Type': 'application/json'},
                               timeout=10)
        
        print(f"   Status: {response.status_code}")
        print(f"   Response: {response.text}")
        
        if response.status_code == 200:
            print("   ✅ FCM test endpoint working")
        else:
            print("   ❌ FCM test endpoint failed")
            print(f"   🔍 This might be the issue - check backend logs")
            
    except Exception as e:
        print(f"   ❌ FCM test error: {e}")
        print(f"   🔍 Error type: {type(e).__name__}")
    
    print("\n" + "=" * 40)
    print("🏁 Backend health check completed")
    return True

if __name__ == "__main__":
    test_backend_health()
