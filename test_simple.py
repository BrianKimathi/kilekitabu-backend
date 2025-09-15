import requests
import json

# Test health endpoint first
print("Testing health endpoint...")
try:
    health_response = requests.get('http://localhost:5000/')
    print(f'Health Status: {health_response.status_code}')
    print(f'Health Response: {health_response.text}')
except Exception as e:
    print(f'Health check failed: {e}')

print("\nTesting FCM tokens endpoint...")
try:
    # Check if FCM tokens are stored
    tokens_response = requests.get('http://localhost:5000/api/notifications/tokens')
    print(f'Tokens Status: {tokens_response.status_code}')
    print(f'Tokens Response: {tokens_response.text}')
except Exception as e:
    print(f'Tokens check failed: {e}')

print("\nTesting FCM endpoint...")
try:
    # Test FCM endpoint
    response = requests.post('http://localhost:5000/api/notifications/test', 
                            json={'user_id': 'GI7PPaaRh7hRogozJcDHt33RQEw2'})
    
    print(f'FCM Status: {response.status_code}')
    print(f'FCM Response: {response.text}')
except Exception as e:
    print(f'FCM test failed: {e}')