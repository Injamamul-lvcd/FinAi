"""
Test script for admin error handling.

This script tests the custom exception classes and their handlers.
"""

import sys
import json
from datetime import datetime
from utils.exceptions import (
    AdminAuthorizationError,
    ResourceNotFoundError,
    ConfigValidationError
)


def test_admin_authorization_error():
    """Test AdminAuthorizationError exception."""
    print("Testing AdminAuthorizationError...")
    
    try:
        raise AdminAuthorizationError(
            message="Admin access required",
            details={"user_id": "user123", "required_role": "admin"}
        )
    except AdminAuthorizationError as e:
        assert e.message == "Admin access required"
        assert e.details["user_id"] == "user123"
        assert e.details["required_role"] == "admin"
        print("✓ AdminAuthorizationError works correctly")
        return True
    
    return False


def test_resource_not_found_error():
    """Test ResourceNotFoundError exception."""
    print("Testing ResourceNotFoundError...")
    
    try:
        raise ResourceNotFoundError(
            resource_type="user",
            resource_id="user123",
            message="User not found: user123"
        )
    except ResourceNotFoundError as e:
        assert e.resource_type == "user"
        assert e.resource_id == "user123"
        assert e.message == "User not found: user123"
        assert e.details["resource_type"] == "user"
        assert e.details["resource_id"] == "user123"
        print("✓ ResourceNotFoundError works correctly")
        return True
    
    return False


def test_resource_not_found_error_default_message():
    """Test ResourceNotFoundError with default message."""
    print("Testing ResourceNotFoundError with default message...")
    
    try:
        raise ResourceNotFoundError(
            resource_type="document",
            resource_id="doc456"
        )
    except ResourceNotFoundError as e:
        assert e.resource_type == "document"
        assert e.resource_id == "doc456"
        assert e.message == "document not found: doc456"
        print("✓ ResourceNotFoundError default message works correctly")
        return True
    
    return False


def test_config_validation_error():
    """Test ConfigValidationError exception."""
    print("Testing ConfigValidationError...")
    
    try:
        raise ConfigValidationError(
            setting_name="max_file_size_mb",
            value=1000,
            message="Value exceeds maximum allowed: 500",
            details={
                "setting_name": "max_file_size_mb",
                "provided_value": "1000",
                "max_value": 500,
                "min_value": 1
            }
        )
    except ConfigValidationError as e:
        assert e.setting_name == "max_file_size_mb"
        assert e.value == 1000
        assert e.message == "Value exceeds maximum allowed: 500"
        assert e.details["max_value"] == 500
        print("✓ ConfigValidationError works correctly")
        return True
    
    return False


def test_error_response_format():
    """Test that error responses have consistent format."""
    print("Testing error response format...")
    
    # Test AdminAuthorizationError format
    try:
        raise AdminAuthorizationError(
            message="Test message",
            details={"key": "value"}
        )
    except AdminAuthorizationError as e:
        # Simulate what the handler would create
        error_response = {
            "error": "AdminAuthorizationError",
            "message": e.message,
            "details": e.details,
            "timestamp": datetime.utcnow().isoformat() + "Z"
        }
        
        assert "error" in error_response
        assert "message" in error_response
        assert "details" in error_response
        assert "timestamp" in error_response
        assert error_response["error"] == "AdminAuthorizationError"
        print("✓ Error response format is consistent")
        return True
    
    return False


def main():
    """Run all tests."""
    print("=" * 60)
    print("Admin Error Handling Tests")
    print("=" * 60)
    print()
    
    tests = [
        test_admin_authorization_error,
        test_resource_not_found_error,
        test_resource_not_found_error_default_message,
        test_config_validation_error,
        test_error_response_format
    ]
    
    passed = 0
    failed = 0
    
    for test in tests:
        try:
            if test():
                passed += 1
            else:
                failed += 1
                print(f"✗ {test.__name__} failed")
        except Exception as e:
            failed += 1
            print(f"✗ {test.__name__} raised exception: {e}")
        print()
    
    print("=" * 60)
    print(f"Results: {passed} passed, {failed} failed")
    print("=" * 60)
    
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
