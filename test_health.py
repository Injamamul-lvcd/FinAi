"""
Simple test script for the health check endpoint.
"""
import requests
import json

def test_health_endpoint():
    """Test the health check endpoint"""
    base_url = "http://localhost:8000"
    health_url = f"{base_url}/api/v1/health"
    
    print("Testing health check endpoint...")
    print(f"URL: {health_url}")
    print("-" * 50)
    
    try:
        response = requests.get(health_url, timeout=10)
        
        print(f"Status Code: {response.status_code}")
        print(f"Response:")
        print(json.dumps(response.json(), indent=2))
        
        if response.status_code == 200:
            print("\n✓ Health check passed - all components healthy")
        elif response.status_code == 503:
            print("\n⚠ Health check returned 503 - some components unhealthy")
        else:
            print(f"\n✗ Unexpected status code: {response.status_code}")
            
    except requests.exceptions.ConnectionError:
        print("✗ Error: Could not connect to server")
        print("Make sure the server is running with: python main.py")
    except Exception as e:
        print(f"✗ Error: {e}")

if __name__ == "__main__":
    test_health_endpoint()
