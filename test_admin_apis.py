"""
Test script to verify admin API endpoints are working correctly.
"""
import sys
from fastapi.testclient import TestClient
from main import app

# Create test client
client = TestClient(app)

def test_admin_routes_registered():
    """Test that admin routes are registered."""
    print("\n=== Testing Admin Routes Registration ===")
    
    # Get all routes
    admin_routes = [route for route in app.routes if hasattr(route, 'path') and '/admin' in route.path]
    
    print(f"✓ Found {len(admin_routes)} admin routes")
    
    # Expected admin endpoints
    expected_endpoints = [
        "/api/v1/admin/users",
        "/api/v1/admin/users/{user_id}",
        "/api/v1/admin/users/{user_id}/status",
        "/api/v1/admin/users/{user_id}/reset-password",
        "/api/v1/admin/users/{user_id}/activity",
        "/api/v1/admin/documents",
        "/api/v1/admin/documents/{document_id}",
        "/api/v1/admin/documents/stats",
        "/api/v1/admin/system/health",
        "/api/v1/admin/system/metrics",
        "/api/v1/admin/system/storage",
        "/api/v1/admin/system/api-usage",
        "/api/v1/admin/system/logs",
        "/api/v1/admin/analytics/users",
        "/api/v1/admin/analytics/sessions",
        "/api/v1/admin/analytics/documents",
        "/api/v1/admin/config",
        "/api/v1/admin/config/{setting_name}",
    ]
    
    registered_paths = [route.path for route in admin_routes]
    
    print("\nRegistered admin endpoints:")
    for path in sorted(set(registered_paths)):
        print(f"  • {path}")
    
    # Check if all expected endpoints are registered
    missing = []
    for endpoint in expected_endpoints:
        if endpoint not in registered_paths:
            missing.append(endpoint)
    
    if missing:
        print(f"\n✗ Missing endpoints: {missing}")
        return False
    else:
        print(f"\n✓ All {len(expected_endpoints)} expected admin endpoints are registered")
        return True


def test_admin_auth_required():
    """Test that admin endpoints require authentication."""
    print("\n=== Testing Admin Authentication ===")
    
    # Test without authentication
    response = client.get("/api/v1/admin/users")
    
    if response.status_code == 403:
        print("✓ Admin endpoints require authentication (403 Forbidden)")
        return True
    elif response.status_code == 401:
        print("✓ Admin endpoints require authentication (401 Unauthorized)")
        return True
    else:
        print(f"✗ Unexpected status code: {response.status_code}")
        print(f"  Response: {response.json()}")
        return False


def test_openapi_schema():
    """Test that OpenAPI schema is generated correctly."""
    print("\n=== Testing OpenAPI Schema ===")
    
    response = client.get("/openapi.json")
    
    if response.status_code == 200:
        schema = response.json()
        admin_paths = [path for path in schema.get('paths', {}).keys() if '/admin' in path]
        print(f"✓ OpenAPI schema generated successfully")
        print(f"✓ Found {len(admin_paths)} admin endpoints in schema")
        return True
    else:
        print(f"✗ Failed to get OpenAPI schema: {response.status_code}")
        return False


def test_health_endpoint():
    """Test that health endpoint works (non-admin)."""
    print("\n=== Testing Health Endpoint (Non-Admin) ===")
    
    response = client.get("/api/v1/health")
    
    if response.status_code == 200:
        data = response.json()
        print(f"✓ Health endpoint working")
        print(f"  Status: {data.get('status')}")
        return True
    else:
        print(f"✗ Health endpoint failed: {response.status_code}")
        return False


def main():
    """Run all tests."""
    print("=" * 60)
    print("Admin API Verification Tests")
    print("=" * 60)
    
    tests = [
        test_admin_routes_registered,
        test_admin_auth_required,
        test_openapi_schema,
        test_health_endpoint,
    ]
    
    results = []
    for test in tests:
        try:
            result = test()
            results.append(result)
        except Exception as e:
            print(f"\n✗ Test failed with exception: {e}")
            import traceback
            traceback.print_exc()
            results.append(False)
    
    # Summary
    print("\n" + "=" * 60)
    print("Test Summary")
    print("=" * 60)
    passed = sum(results)
    total = len(results)
    print(f"Passed: {passed}/{total}")
    
    if passed == total:
        print("\n✓ All tests passed! Admin APIs are working correctly.")
        return 0
    else:
        print(f"\n✗ {total - passed} test(s) failed.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
