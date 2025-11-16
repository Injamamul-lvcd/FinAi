"""
Quick test script to verify auth endpoints are working
"""
import requests
import json

BASE_URL = "http://localhost:8000"

def test_register():
    """Test user registration"""
    print("\n=== Testing Registration ===")
    url = f"{BASE_URL}/api/v1/auth/register"
    
    data = {
        "username": "testuser456",
        "email": "test456@example.com",
        "password": "Test123456",
        "full_name": "Test User"
    }
    
    try:
        response = requests.post(url, json=data, timeout=10)
        print(f"Status Code: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}")
        return response.status_code == 201
    except requests.exceptions.Timeout:
        print("ERROR: Request timed out after 10 seconds")
        return False
    except Exception as e:
        print(f"ERROR: {e}")
        return False

def test_login():
    """Test user login"""
    print("\n=== Testing Login ===")
    url = f"{BASE_URL}/api/v1/auth/login"
    
    data = {
        "username": "testuser456",
        "password": "Test123456"
    }
    
    try:
        response = requests.post(url, json=data, timeout=10)
        print(f"Status Code: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}")
        return response.status_code == 200
    except requests.exceptions.Timeout:
        print("ERROR: Request timed out after 10 seconds")
        return False
    except Exception as e:
        print(f"ERROR: {e}")
        return False

def test_health():
    """Test health endpoint"""
    print("\n=== Testing Health Endpoint ===")
    url = f"{BASE_URL}/api/v1/health"
    
    try:
        response = requests.get(url, timeout=5)
        print(f"Status Code: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}")
        return response.status_code == 200
    except requests.exceptions.Timeout:
        print("ERROR: Request timed out after 5 seconds")
        return False
    except Exception as e:
        print(f"ERROR: {e}")
        return False

if __name__ == "__main__":
    print("Starting Auth Endpoint Tests...")
    print("Make sure the server is running on http://localhost:8000")
    
    # Test health first
    if not test_health():
        print("\n❌ Health check failed. Is the server running?")
        exit(1)
    
    # Test registration
    test_register()
    
    # Test login
    test_login()
    
    print("\n=== Tests Complete ===")
