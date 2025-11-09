# Error Handling and Logging Implementation

## Overview

This document describes the comprehensive error handling and logging system implemented for the Financial Chatbot RAG API.

## Components Implemented

### 1. Structured Logging (`utils/logger.py`)

**Features:**
- Structured log formatting with timestamps, log levels, and component names
- Daily log file rotation (keeps 30 days of logs)
- Separate console and file log levels
- JSON-formatted context data for structured logging
- Utility functions for request and error logging

**Format:**
```
[timestamp] [level] [component] message {context}
```

**Key Functions:**
- `setup_logging()`: Configure application-wide logging
- `log_request()`: Log API requests with timing and status
- `log_error()`: Log errors with structured context
- `get_logger()`: Get logger instance for a component

**Configuration:**
- Log directory: `./logs`
- Log file: `app.log`
- Rotation: Daily at midnight
- Retention: 30 days

### 2. Request Logging Middleware (`utils/middleware.py`)

**RequestLoggingMiddleware:**
- Logs all incoming requests with method, path, and client info
- Tracks request duration in milliseconds
- Generates unique request ID for each request
- Adds `X-Request-ID` header to responses
- Logs response status codes with appropriate log levels:
  - INFO: 2xx, 3xx
  - WARNING: 4xx
  - ERROR: 5xx

**ErrorHandlingMiddleware:**
- Catches unhandled exceptions from the application
- Logs exceptions with full context and traceback
- Returns consistent JSON error responses
- Prevents internal error details from leaking to clients

### 3. Exception Handlers (`utils/exceptions.py`)

**Custom Exception Handlers:**

1. **HTTPException Handler**
   - Handles all HTTPException instances
   - Formats errors into consistent JSON structure
   - Adds request ID to error details
   - Logs with appropriate level based on status code

2. **Validation Exception Handler**
   - Handles Pydantic validation errors
   - Returns 422 status code
   - Provides detailed field-level error information
   - Formats validation errors in user-friendly format

3. **Generic Exception Handler**
   - Catch-all for unhandled exceptions
   - Returns 500 status code
   - Logs full traceback for debugging
   - Hides internal details from clients

**Error Response Format:**
```json
{
  "error": "ErrorType",
  "message": "Human-readable error message",
  "details": {
    "request_id": "uuid",
    "additional": "context"
  }
}
```

## HTTP Status Codes

The system implements proper HTTP status codes for different error types:

- **200 OK**: Successful request
- **400 Bad Request**: Invalid input, validation errors
- **404 Not Found**: Resource not found
- **413 Payload Too Large**: File size exceeds limit
- **422 Unprocessable Entity**: Request validation failed
- **500 Internal Server Error**: Unexpected server errors
- **503 Service Unavailable**: External service unavailable (DB, API)

## Integration with FastAPI

The error handling and logging system is integrated in `main.py`:

```python
# Configure structured logging
setup_logging(
    log_level=settings.log_level,
    log_dir="./logs",
    log_file="app.log"
)

# Add middleware
app.add_middleware(ErrorHandlingMiddleware)
app.add_middleware(RequestLoggingMiddleware)

# Register exception handlers
register_exception_handlers(app)
```

## Log Levels

The system uses standard Python logging levels:

- **DEBUG**: Detailed diagnostic information
- **INFO**: General informational messages, successful operations
- **WARNING**: Warning messages, 4xx errors
- **ERROR**: Error messages, 5xx errors, exceptions
- **CRITICAL**: Critical errors that may cause system failure

## Request/Response Logging

Every API request is logged with:
- Request ID (UUID)
- HTTP method and path
- Client IP address
- User agent
- Response status code
- Request duration in milliseconds
- Additional context (error details, validation errors, etc.)

## Error Context

All errors are logged with rich context:
- Timestamp
- Request ID
- Request method and path
- Error type and message
- Stack trace (for exceptions)
- Additional details (varies by error type)

## Testing

The implementation has been tested with:
- Successful requests (200)
- Client errors (400, 404, 422)
- Server errors (500, 503)
- Unhandled exceptions
- Validation errors
- Request/response logging
- Log file creation and rotation

All tests passed successfully.

## Usage Examples

### Logging in Route Handlers

```python
from utils.logger import get_logger

logger = get_logger(__name__)

@router.get("/example")
async def example():
    logger.info("Processing request")
    
    try:
        # Process request
        result = do_something()
        logger.info("Request successful", extra={"result_count": len(result)})
        return result
    except Exception as e:
        logger.error("Request failed", exc_info=True)
        raise
```

### Raising HTTP Exceptions

```python
from fastapi import HTTPException, status

# Structured error response
raise HTTPException(
    status_code=status.HTTP_404_NOT_FOUND,
    detail={
        "error": "NotFound",
        "message": "Document not found",
        "details": {"document_id": doc_id}
    }
)
```

### Validation with Pydantic

```python
from pydantic import BaseModel, Field

class Request(BaseModel):
    name: str = Field(..., min_length=1, max_length=50)
    age: int = Field(..., ge=0, le=150)

# Validation errors are automatically caught and formatted
```

## Benefits

1. **Consistent Error Responses**: All errors follow the same JSON structure
2. **Comprehensive Logging**: Every request and error is logged with context
3. **Request Tracking**: Unique request IDs enable tracing requests through logs
4. **Log Rotation**: Automatic daily rotation prevents disk space issues
5. **Structured Logs**: JSON context makes logs machine-readable
6. **Security**: Internal error details are hidden from clients
7. **Debugging**: Full stack traces and context aid in troubleshooting
8. **Monitoring**: Log levels enable filtering for monitoring systems

## Configuration

Error handling and logging can be configured via environment variables:

```env
LOG_LEVEL=INFO  # DEBUG, INFO, WARNING, ERROR, CRITICAL
```

## Files Created

- `utils/logger.py`: Structured logging configuration
- `utils/middleware.py`: Request logging and error handling middleware
- `utils/exceptions.py`: Custom exception handlers
- `utils/__init__.py`: Package initialization

## Files Modified

- `main.py`: Integrated logging and error handling system

## Requirements Satisfied

This implementation satisfies all requirements from task 12:

✓ Create utils/logger.py with structured logging configuration
✓ Configure log file output with daily rotation
✓ Add error handling middleware to FastAPI application
✓ Implement proper HTTP status codes (400, 404, 413, 422, 500, 503)
✓ Add request/response logging for all API endpoints
✓ Log all errors with context (timestamps, request details)

**Requirements Coverage:**
- 5.1: Appropriate HTTP status codes for different error types
- 5.2: Descriptive error messages in response body
- 5.3: Log all errors with timestamps and request context
- 5.4: Return 503 when services are unavailable
- 5.5: Error handling with proper logging
