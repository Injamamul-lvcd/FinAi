"""
Custom exception handlers for the Financial Chatbot RAG API.

This module provides exception handlers for FastAPI to ensure consistent
error responses across all endpoints.
"""

import logging
from typing import Union
from fastapi import Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError, HTTPException
from pydantic import ValidationError

logger = logging.getLogger(__name__)


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
        error_content = exc.detail
    else:
        # Detail is a string, wrap it
        error_content = {
            "error": "HTTPException",
            "message": str(exc.detail),
            "details": None
        }
    
    # Add request ID if available
    if request_id and "details" in error_content:
        if error_content["details"] is None:
            error_content["details"] = {}
        if isinstance(error_content["details"], dict):
            error_content["details"]["request_id"] = request_id
    
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
        }
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
            }
        }
    )


def register_exception_handlers(app) -> None:
    """
    Register all custom exception handlers with the FastAPI application.
    
    Args:
        app: The FastAPI application instance
    """
    app.add_exception_handler(HTTPException, http_exception_handler)
    app.add_exception_handler(RequestValidationError, validation_exception_handler)
    app.add_exception_handler(ValidationError, validation_exception_handler)
    app.add_exception_handler(Exception, generic_exception_handler)
    
    logger.info("Custom exception handlers registered")
