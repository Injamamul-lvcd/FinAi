# Admin Panel Error Handling Documentation

## Overview

This document describes the comprehensive error handling implementation for the Admin Panel APIs. The error handling system provides consistent, informative error responses across all admin endpoints with proper HTTP status codes and detailed error information.

## Custom Exception Classes

### 1. AdminAuthorizationError

**Purpose**: Raised when a user lacks admin privileges to perform an action.

**HTTP Status Code**: 403 Forbidden

**Usage Example**:
```python
from utils.exceptions import AdminAuthorizationError

# Raise when user lacks admin privileges
raise AdminAuthorizationError(
    message="Admin access required",
    details={"required_role": "admin", "user_role": "user"}
)
```

**Error Response Format**:
```json
{
    "error": "AdminAuthorizationError",
    "message": "Admin access required",
    "details": {
        "required_role": "admin",
        "user_role": "user",
        "request_id": "abc123"
    },
    "timestamp": "2024-11-16T10:30:00.000Z"
}
```

### 2. ResourceNotFoundError

**Purpose**: Raised when a requested resource doesn't exist.

**HTTP Status Code**: 404 Not Found

**Usage Example**:
```python
from utils.exceptions import ResourceNotFoundError

# Raise when resource not found
raise ResourceNotFoundError(
    resource_type="user",
    resource_id="user123",
    message="User not found: user123"  # Optional, auto-generated if not provided
)
```

**Error Response Format**:
```json
{
    "error": "ResourceNotFoundError",
    "message": "User not found: user123",
    "details": {
        "resource_type": "user",
        "resource_id": "user123",
        "request_id": "abc123"
    },
    "timestamp": "2024-11-16T10:30:00.000Z"
}
```

### 3. ConfigValidationError

**Purpose**: Raised when a configuration value fails validation.

**HTTP Status Code**: 400 Bad Request

**Usage Example**:
```python
from utils.exceptions import ConfigValidationError

# Raise when config validation fails
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
```

**Error Response Format**:
```json
{
    "error": "ConfigValidationError",
    "message": "Value exceeds maximum allowed: 500",
    "details": {
        "setting_name": "max_file_size_mb",
        "provided_value": "1000",
        "max_value": 500,
        "min_value": 1,
        "request_id": "abc123"
    },
    "timestamp": "2024-11-16T10:30:00.000Z"
}
```

## Standard HTTP Error Responses

### 401 Unauthorized

Returned when authentication fails (invalid/expired token, inactive user).

**Example Response**:
```json
{
    "error": "AuthenticationError",
    "message": "Invalid or expired authentication token",
    "details": {
        "reason": "token_invalid",
        "request_id": "abc123"
    },
    "timestamp": "2024-11-16T10:30:00.000Z"
}
```

**Common Reasons**:
- `token_invalid`: Token is malformed or expired
- `missing_username`: Token doesn't contain username
- `user_not_found`: User doesn't exist in database
- `account_inactive`: User account is disabled

### 403 Forbidden

Returned when user is authenticated but lacks admin privileges.

**Example Response**:
```json
{
    "error": "AdminAuthorizationError",
    "message": "Admin access required",
    "details": {
        "reason": "insufficient_privileges",
        "required_role": "admin",
        "request_id": "abc123"
    },
    "timestamp": "2024-11-16T10:30:00.000Z"
}
```

### 404 Not Found

Returned when a requested resource doesn't exist.

**Example Response**:
```json
{
    "error": "ResourceNotFoundError",
    "message": "document not found: doc123",
    "details": {
        "resource_type": "document",
        "resource_id": "doc123",
        "request_id": "abc123"
    },
    "timestamp": "2024-11-16T10:30:00.000Z"
}
```

### 422 Validation Error

Returned when request validation fails (invalid parameters, missing fields).

**Example Response**:
```json
{
    "error": "ValidationError",
    "message": "Request validation failed",
    "details": {
        "errors": [
            {
                "field": "page_size",
                "message": "ensure this value is less than or equal to 100",
                "type": "value_error.number.not_le"
            }
        ],
        "request_id": "abc123"
    },
    "timestamp": "2024-11-16T10:30:00.000Z"
}
```

## Error Response Format

All error responses follow a consistent format:

```json
{
    "error": "ErrorType",           // Type of error (e.g., "AuthenticationError")
    "message": "Human-readable message",  // Clear description of the error
    "details": {                    // Additional context (optional)
        "key": "value",
        "request_id": "abc123"      // Request ID for tracking
    },
    "timestamp": "2024-11-16T10:30:00.000Z"  // ISO 8601 timestamp
}
```

## Using Custom Exceptions in Admin Services

### Example: User Management Service

```python
from utils.exceptions import ResourceNotFoundError, AdminAuthorizationError

class AdminUserService:
    def update_user_status(self, user_id: str, is_active: bool, admin_id: str):
        # Check if user exists
        user = self.get_user_by_id(user_id)
        if not user:
            raise ResourceNotFoundError(
                resource_type="user",
                resource_id=user_id
            )
        
        # Update user status
        # ... implementation ...
        
        return True
```

### Example: Configuration Service

```python
from utils.exceptions import ConfigValidationError, ResourceNotFoundError

class ConfigManager:
    def update_setting(self, setting_name: str, value: Any, admin_id: str):
        # Check if setting exists
        setting = self.get_setting(setting_name)
        if not setting:
            raise ResourceNotFoundError(
                resource_type="configuration_setting",
                resource_id=setting_name
            )
        
        # Validate value
        is_valid, error_message = self.validate_setting_value(setting_name, value)
        if not is_valid:
            raise ConfigValidationError(
                setting_name=setting_name,
                value=value,
                message=error_message,
                details={
                    "setting_name": setting_name,
                    "provided_value": str(value),
                    "data_type": setting["data_type"],
                    "min_value": setting.get("min_value"),
                    "max_value": setting.get("max_value")
                }
            )
        
        # Update setting
        # ... implementation ...
        
        return True
```

### Example: Document Service

```python
from utils.exceptions import ResourceNotFoundError

class AdminDocumentService:
    def delete_document(self, document_id: str, admin_id: str):
        # Check if document exists
        document = self.get_document_by_id(document_id)
        if not document:
            raise ResourceNotFoundError(
                resource_type="document",
                resource_id=document_id,
                message=f"Document not found: {document_id}"
            )
        
        # Delete document
        # ... implementation ...
        
        return True
```

## Exception Handler Registration

Exception handlers are automatically registered in `main.py` via the `register_exception_handlers()` function:

```python
from utils.exceptions import register_exception_handlers

# Register all exception handlers
register_exception_handlers(app)
```

The handlers are registered in order of specificity:
1. Admin-specific exceptions (most specific)
2. HTTP and validation exceptions
3. Generic exception handler (catch-all)

## Logging

All errors are automatically logged with appropriate severity levels:

- **AdminAuthorizationError**: WARNING level
- **ResourceNotFoundError**: INFO level
- **ConfigValidationError**: WARNING level
- **Authentication errors**: WARNING level
- **Unhandled exceptions**: ERROR level with full traceback

Log entries include:
- Request ID (if available)
- Request method and path
- Error type and message
- Additional context (user ID, resource ID, etc.)

## Testing

Run the error handling tests:

```bash
python test_admin_error_handling.py
```

This tests:
- Custom exception class instantiation
- Error message formatting
- Details dictionary handling
- Consistent error response format

## Best Practices

1. **Use specific exceptions**: Choose the most appropriate exception type for the error condition.

2. **Provide helpful details**: Include relevant context in the `details` dictionary to help with debugging.

3. **Don't expose sensitive data**: Never include passwords, tokens, or other sensitive information in error responses.

4. **Log appropriately**: Use appropriate log levels (INFO for expected errors like 404, WARNING for authorization failures, ERROR for unexpected issues).

5. **Consistent messages**: Use clear, consistent error messages that help users understand what went wrong.

6. **Include request IDs**: Request IDs are automatically added to error responses for tracking and debugging.

## Requirements Coverage

This implementation satisfies the following requirements:

- **Requirement 2.5**: Consistent error responses for user management operations
- **Requirement 6.3**: Proper error handling for document deletion
- **Requirement 13.3**: Configuration validation error handling
- **Requirement 16.1**: 401 responses for invalid/expired tokens
- **Requirement 16.2**: 403 responses for non-admin users
- **Requirement 16.3**: Consistent error response format with error type, message, details, and timestamp

## Future Enhancements

1. **Error codes**: Add numeric error codes for programmatic error handling
2. **Localization**: Support multiple languages for error messages
3. **Error aggregation**: Collect and analyze error patterns for system improvements
4. **Rate limiting errors**: Add specific handling for rate limit exceeded errors
