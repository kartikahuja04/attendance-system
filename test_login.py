import requests
import json

BASE_URL = "http://localhost:8000"

print("="*60)
print("Testing Login Endpoint")
print("="*60)

# Test data
credentials = {
    "email": "teacher@test.com",
    "password": "password123"
}

print(f"\nSending login request...")
print(f"Email: {credentials['email']}")
print(f"Password: {credentials['password']}")

try:
    response = requests.post(
        f"{BASE_URL}/api/auth/login",
        json=credentials,
        timeout=5
    )
    
    print(f"\nStatus Code: {response.status_code}")
    print(f"Response Headers: {dict(response.headers)}")
    print(f"Response Body:\n{json.dumps(response.json(), indent=2)}")
    
    if response.status_code == 200:
        data = response.json()
        print(f"\n[SUCCESS] Login successful!")
        print(f"Token: {data['token'][:50]}...")
        print(f"User: {data['user']}")
    else:
        print(f"\n[ERROR] Login failed!")
        
except requests.exceptions.ConnectionError:
    print(f"\n[ERROR] Cannot connect to backend at {BASE_URL}")
    print("Make sure the backend server is running!")
except Exception as e:
    print(f"\n[ERROR] {type(e).__name__}: {str(e)}")
