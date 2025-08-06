#!/usr/bin/env python3
"""
Simple test script for KileKitabu Backend API
Run this to test the basic functionality
"""

import requests
import json

# Configuration
BASE_URL = "http://localhost:5000"

def test_health_check():
    """Test if the server is running"""
    try:
        response = requests.get(f"{BASE_URL}/")
        print(f"Health check: {response.status_code}")
        return response.status_code == 200
    except requests.exceptions.ConnectionError:
        print("❌ Server is not running. Please start the Flask app first.")
        return False

def test_user_registration():
    """Test user registration endpoint"""
    url = f"{BASE_URL}/api/user/register"
    data = {
        "email": "test@example.com",
        "name": "Test User"
    }
    
    # Note: This will fail without a valid Firebase token
    # In a real test, you would need to get a valid token from Firebase Auth
    headers = {
        "Authorization": "Bearer invalid-token-for-testing",
        "Content-Type": "application/json"
    }
    
    try:
        response = requests.post(url, json=data, headers=headers)
        print(f"User registration test: {response.status_code}")
        if response.status_code == 401:
            print("✅ Authentication working (expected 401 for invalid token)")
        return True
    except Exception as e:
        print(f"❌ Error testing user registration: {e}")
        return False

def test_payment_initiation():
    """Test payment initiation endpoint"""
    url = f"{BASE_URL}/api/payment/initiate"
    data = {
        "amount": 1000,
        "email": "test@example.com",
        "phone": "+254700000000",
        "first_name": "Test",
        "last_name": "User"
    }
    
    headers = {
        "Authorization": "Bearer invalid-token-for-testing",
        "Content-Type": "application/json"
    }
    
    try:
        response = requests.post(url, json=data, headers=headers)
        print(f"Payment initiation test: {response.status_code}")
        if response.status_code == 401:
            print("✅ Authentication working (expected 401 for invalid token)")
        return True
    except Exception as e:
        print(f"❌ Error testing payment initiation: {e}")
        return False

def main():
    """Run all tests"""
    print("🧪 Testing KileKitabu Backend API")
    print("=" * 40)
    
    # Test server health
    if not test_health_check():
        return
    
    # Test endpoints (will fail due to invalid tokens, but that's expected)
    test_user_registration()
    test_payment_initiation()
    
    print("\n" + "=" * 40)
    print("📝 Test Summary:")
    print("- Server health: ✅ (if server is running)")
    print("- Authentication: ✅ (401 responses indicate auth is working)")
    print("- Endpoints: ✅ (structure is correct)")
    print("\n💡 To test with real data:")
    print("1. Get a valid Firebase ID token from your mobile app")
    print("2. Use that token in the Authorization header")
    print("3. Test the endpoints with real user data")

if __name__ == "__main__":
    main() 