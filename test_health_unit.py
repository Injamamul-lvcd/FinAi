"""
Unit test for health check endpoint logic.
Tests the health check functions without requiring a running server.
"""
import sys
import os

# Add the project root to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_health_check_logic():
    """Test the health check endpoint logic"""
    print("Testing health check endpoint implementation...")
    print("=" * 60)
    
    # Test 1: Verify the health module can be imported
    print("\n1. Testing module import...")
    try:
        from api.routes import health
        print("   ✓ Health module imported successfully")
    except Exception as e:
        print(f"   ✗ Failed to import health module: {e}")
        return False
    
    # Test 2: Verify router is configured correctly
    print("\n2. Testing router configuration...")
    try:
        assert health.router.prefix == "/api/v1"
        assert "health" in health.router.tags
        print("   ✓ Router configured correctly")
        print(f"     - Prefix: {health.router.prefix}")
        print(f"     - Tags: {health.router.tags}")
    except AssertionError as e:
        print(f"   ✗ Router configuration incorrect: {e}")
        return False
    
    # Test 3: Verify endpoint is registered
    print("\n3. Testing endpoint registration...")
    try:
        routes = [route.path for route in health.router.routes]
        assert "/health" in routes
        print("   ✓ Health endpoint registered")
        print(f"     - Available routes: {routes}")
    except AssertionError:
        print(f"   ✗ Health endpoint not found in routes")
        return False
    
    # Test 4: Verify helper functions exist
    print("\n4. Testing helper functions...")
    try:
        assert hasattr(health, 'check_vector_database')
        assert hasattr(health, 'check_gemini_api')
        assert callable(health.check_vector_database)
        assert callable(health.check_gemini_api)
        print("   ✓ Helper functions exist and are callable")
        print("     - check_vector_database()")
        print("     - check_gemini_api()")
    except AssertionError:
        print("   ✗ Helper functions missing or not callable")
        return False
    
    # Test 5: Verify main.py includes health router
    print("\n5. Testing main.py integration...")
    try:
        with open('main.py', 'r') as f:
            main_content = f.read()
            assert 'from api.routes import documents, health' in main_content
            assert 'app.include_router(health.router)' in main_content
        print("   ✓ Health router registered in main.py")
    except AssertionError:
        print("   ✗ Health router not properly registered in main.py")
        return False
    except FileNotFoundError:
        print("   ✗ main.py not found")
        return False
    
    print("\n" + "=" * 60)
    print("✓ All health check implementation tests passed!")
    print("\nImplementation Summary:")
    print("- Created api/routes/health.py with GET /api/v1/health endpoint")
    print("- Checks vector database connectivity")
    print("- Checks Google Gemini API connectivity")
    print("- Returns 200 OK if all components healthy")
    print("- Returns 503 Service Unavailable if any component unhealthy")
    print("\nTo test with a running server:")
    print("1. Ensure ChromaDB dependencies are installed (see TROUBLESHOOTING.md)")
    print("2. Run: python main.py")
    print("3. Test: curl http://localhost:8000/api/v1/health")
    print("   Or visit: http://localhost:8000/api/docs")
    
    return True

if __name__ == "__main__":
    success = test_health_check_logic()
    sys.exit(0 if success else 1)
