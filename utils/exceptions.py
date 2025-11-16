"""
Custom exception handlers for the Financial Chatbot RAG API.

This module provides exception handlers for FastAPI to ensure consistent
error responses across all endpoints.
"""

import logging
from typing import Union, Optional, Dict, Any
from datetime import datetime
from fastapi import Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError, HTTPException
from pydantic import ValidationError

logger = logging.getLogger(__name__)


# ============================================================================
# Custom Exception Classes for Admin Panel
# ============================================================================

class AdminAuthorizationError(Exception):
    """
    Raised when a user lacks admin privileges to perform an action.
    
    This exception should be raised when a user attempts to access admin
    functionality without proper authorization.
    """
    
    def __init__(
        self,
        message: str = "Admin access required",
        details: Optional[Dict[str, Any]] = None
    ):
        self.message = message
        self.details = details or {}
        super().__init__(self.message)


class ResourceNotFoundError(Exception):
    """
    Raised when a requested resource doesn't exist.
    
    This exception should be raised when attempting to access or modify
    a resource (user, document, config setting, etc.) that doesn't exist.
    """
    
    def __init__(
        self,
        resource_type: str,
        resource_id: str,
        message: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        self.resource_type = resource_type
        self.resource_id = resource_id
        self.message = message or f"{resource_type} not found: {resource_id}"
        self.details = details or {
            "resource_type": resource_type,
            "resource_id": resource_id
        }
        super().__init__(self.message)


class ConfigValidationError(Exception):
    """
    Raised when a configuration value fails validation.
    
    This exception should be raised when attempting to update a configuration
    setting with an invalid value (wrong type, out of range, etc.).
    """
    
    def __init__(
        self,
        setting_name: str,
        value: Any,
        message: str,
        details: Optional[Dict[str, Any]] = None
    ):
        self.setting_name = setting_name
        self.value = value
        self.message = message
        self.details = details or {
            "setting_name": setting_name,
            "provided_value": str(value)
        }
        super().__init__(self.message)


async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
    """
    Handle HTTPException instances raised by route handlers.
    
    Formats the exception into a consistent JSON error response.
    
    Args:
        request: The request that caused the exception
        exc: The HTTPException instance
        
    Returns:
        JSONResponse with error details
    """
    # Get request ID if available
    request_id = getattr(request.state, "request_id", None)
    
    # Extract error details from exception
    if isinstance(exc.detail, dict):
        # Detail is already structured
        error_content = exc.detail.copy()
    else:
        # Detail is a string, wrap it
        error_content = {
            "error": "HTTPException",
            "message": str(exc.detail),
            "details": None
        }
    
    # Add request ID if available
    if request_id:
        if "details" not in error_content or error_content["details"] is None:
            error_content["details"] = {}
        if isinstance(error_content["details"], dict):
            error_content["details"]["request_id"] = request_id
    
    # Add timestamp if not present
    if "timestamp" not in error_content:
        error_content["timestamp"] = datetime.utcnow().isoformat() + "Z"
    
    # Log the error
    logger.warning(
        f"HTTP {exc.status_code}: {request.method} {request.url.path}",
        extra={
            "request_id": request_id,
            "status_code": exc.status_code,
            "error": error_content
        }
    )
    
    return JSONResponse(
        status_code=exc.status_code,
        content=error_content
    )


async def validation_exception_handler(
    request: Request,
    exc: Union[RequestValidationError, ValidationError]
) -> JSONResponse:
    """
    Handle validation errors from Pydantic models.
    
    Formats validation errors into a consistent JSON error response.
    
    Args:
        request: The request that caused the exception
        exc: The validation error instance
        
    Returns:
        JSONResponse with validation error details
    """
    # Get request ID if available
    request_id = getattr(request.state, "request_id", None)
    
    # Extract validation errors
    errors = []
    for error in exc.errors():
        errors.append({
            "field": ".".join(str(loc) for loc in error["loc"]),
            "message": error["msg"],
            "type": error["type"]
        })
    
    error_content = {
        "error": "ValidationError",
        "message": "Request validation failed",
        "details": {
            "errors": errors,
            "request_id": request_id
        },
        "timestamp": datetime.utcnow().isoformat() + "Z"
    }
    
    # Log the validation error
    logger.warning(
        f"Validation error: {request.method} {request.url.path}",
        extra={
            "request_id": request_id,
            "validation_errors": errors
        }
    )
    
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content=error_content
    )


async def admin_authorization_exception_handler(
    request: Request,
    exc: AdminAuthorizationError
) -> JSONResponse:
    """
    Handle AdminAuthorizationError exceptions.
    
    Returns a 403 Forbidden response when a user lacks admin privileges.
    
    Args:
        request: The request that caused the exception
        exc: The AdminAuthorizationError instance
        
    Returns:
        JSONResponse with error details
    """
    # Get request ID if available
    request_id = getattr(request.state, "request_id", None)
    
    # Add request ID to details
    details = exc.details.copy() if exc.details else {}
    if request_id:
        details["request_id"] = request_id
    
    error_content = {
        "error": "AdminAuthorizationError",
        "message": exc.message,
        "details": details,
        "timestamp": datetime.utcnow().isoformat() + "Z"
    }
    
    # Log the authorization failure
    logger.warning(
        f"Admin authorization failed: {request.method} {request.url.path}",
        extra={
            "request_id": request_id,
            "error": exc.message,
            "details": exc.details
        }
    )
    
    return JSONResponse(
        status_code=status.HTTP_403_FORBIDDEN,
        content=error_content
    )


async def resource_not_found_exception_handler(
    request: Request,
    exc: ResourceNotFoundError
) -> JSONResponse:
    """
    Handle ResourceNotFoundError exceptions.
    
    Returns a 404 Not Found response when a requested resource doesn't exist.
    
    Args:
        request: The request that caused the exception
        exc: The ResourceNotFoundError instance
        
    Returns:
        JSONResponse with error details
    """
    # Get request ID if available
    request_id = getattr(request.state, "request_id", None)
    
    # Add request ID to details
    details = exc.details.copy() if exc.details else {}
    if request_id:
        details["request_id"] = request_id
    
    error_content = {
        "error": "ResourceNotFoundError",
        "message": exc.message,
        "details": details,
        "timestamp": datetime.utcnow().isoformat() + "Z"
    }
    
    # Log the not found error
    logger.info(
        f"Resource not found: {exc.resource_type} - {exc.resource_id}",
        extra={
            "request_id": request_id,
            "resource_type": exc.resource_type,
            "resource_id": exc.resource_id,
            "path": request.url.path
        }
    )
    
    return JSONResponse(
        status_code=status.HTTP_404_NOT_FOUND,
        content=error_content
    )


async def config_validation_exception_handler(
    request: Request,
    exc: ConfigValidationError
) -> JSONResponse:
    """
    Handle ConfigValidationError exceptions.
    
    Returns a 400 Bad Request response when configuration validation fails.
    
    Args:
        request: The request that caused the exception
        exc: The ConfigValidationError instance
        
    Returns:
        JSONResponse with error details
    """
    # Get request ID if available
    request_id = getattr(request.state, "request_id", None)
    
    # Add request ID to details
    details = exc.details.copy() if exc.details else {}
    if request_id:
        details["request_id"] = request_id
    
    error_content = {
        "error": "ConfigValidationError",
        "message": exc.message,
        "details": details,
        "timestamp": datetime.utcnow().isoformat() + "Z"
    }
    
    # Log the validation error
    logger.warning(
        f"Configuration validation failed: {exc.setting_name}",
        extra={
            "request_id": request_id,
            "setting_name": exc.setting_name,
            "provided_value": str(exc.value),
            "error": exc.message
        }
    )
    
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content=error_content
    )


async def generic_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """
    Handle any unhandled exceptions.
    
    This is a catch-all handler for exceptions that aren't caught by
    more specific handlers.
    
    Args:
        request: The request that caused the exception
        exc: The exception instance
        
    Returns:
        JSONResponse with error details
    """
    # Get request ID if available
    request_id = getattr(request.state, "request_id", None)
    
    # Log the error with full traceback
    logger.error(
        f"Unhandled exception: {type(exc).__name__}",
        extra={
            "request_id": request_id,
            "method": request.method,
            "path": request.url.path,
            "error_type": type(exc).__name__,
            "error_message": str(exc)
        },
        exc_info=True
    )
    
    # Return generic error response (don't expose internal details)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": "InternalServerError",
            "message": "An unexpected error occurred while processing your request",
            "details": {
                "request_id": request_id,
                "error_type": type(exc).__name__
            },
            "timestamp": datetime.utcnow().isoformat() + "Z"
        }
    )


def register_exception_handlers(app) -> None:
    """
    Register all custom exception handlers with the FastAPI application.
    
    Registers handlers in order of specificity:
    1. Admin-specific exceptions (most specific)
    2. HTTP and validation exceptions
    3. Generic exception handler (catch-all)
    
    Args:
        app: The FastAPI application instance
    """
    # Register admin-specific exception handlers
    app.add_exception_handler(AdminAuthorizationError, admin_authorization_exception_handler)
    app.add_exception_handler(ResourceNotFoundError, resource_not_found_exception_handler)
    app.add_exception_handler(ConfigValidationError, config_validation_exception_handler)
    
    # Register standard exception handlers
    app.add_exception_handler(HTTPException, http_exception_handler)
    app.add_exception_handler(RequestValidationError, validation_exception_handler)
    app.add_exception_handler(ValidationError, validation_exception_handler)
    
    # Register catch-all handler (must be last)
    app.add_exception_handler(Exception, generic_exception_handler)
    
    logger.info("Custom exception handlers registered (including admin-specific handlers)")
