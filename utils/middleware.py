"""
Middleware for request/response logging and error handling.

This module provides FastAPI middleware for:
- Request/response logging with timing
- Automatic error handling and formatting
- Request context tracking
"""

import time
import uuid
from typing import Callable
from fastapi import Request, Response
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp
import logging

from utils.logger import log_request

logger = logging.getLogger(__name__)


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """
    Middleware to log all incoming requests and outgoing responses.
    
    Logs:
    - HTTP method and path
    - Response status code
    - Request duration
    - Client IP and user agent
    """
    
    def __init__(self, app: ASGIApp):
        """
        Initialize the middleware.
        
        Args:
            app: The ASGI application
        """
        super().__init__(app)
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """
        Process the request and log details.
        
        Args:
            request: The incoming request
            call_next: The next middleware or route handler
            
        Returns:
            The response from the application
        """
        # Generate request ID for tracking
        request_id = str(uuid.uuid4())
        request.state.request_id = request_id
        
        # Get client information
        client_ip = request.client.host if request.client else None
        user_agent = request.headers.get("user-agent")
        
        # Record start time
        start_time = time.time()
        
        # Log incoming request
        logger.info(
            f"Request started: {request.method} {request.url.path}",
            extra={
                "request_id": request_id,
                "method": request.method,
                "path": request.url.path,
                "client_ip": client_ip,
                "user_agent": user_agent
            }
        )
        
        # Process request
        try:
            response = await call_next(request)
        except Exception as e:
            # Log unexpected errors
            duration_ms = (time.time() - start_time) * 1000
            logger.error(
                f"Request failed with exception: {request.method} {request.url.path}",
                extra={
                    "request_id": request_id,
                    "method": request.method,
                    "path": request.url.path,
                    "duration_ms": duration_ms,
                    "error": str(e)
                },
                exc_info=True
            )
            raise
        
        # Calculate duration
        duration_ms = (time.time() - start_time) * 1000
        
        # Add request ID to response headers
        response.headers["X-Request-ID"] = request_id
        
        # Log request completion
        log_request(
            method=request.method,
            path=request.url.path,
            status_code=response.status_code,
            duration_ms=duration_ms,
            client_ip=client_ip,
            user_agent=user_agent
        )
        
        return response


class ErrorHandlingMiddleware(BaseHTTPMiddleware):
    """
    Middleware to catch and format unhandled exceptions.
    
    Ensures all errors return consistent JSON responses with proper
    status codes and error details.
    """
    
    def __init__(self, app: ASGIApp):
        """
        Initialize the middleware.
        
        Args:
            app: The ASGI application
        """
        super().__init__(app)
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """
        Process the request and handle any unhandled exceptions.
        
        Args:
            request: The incoming request
            call_next: The next middleware or route handler
            
        Returns:
            The response from the application or error response
        """
        try:
            response = await call_next(request)
            return response
        except Exception as e:
            # Get request ID if available
            request_id = getattr(request.state, "request_id", None)
            
            # Log the error
            logger.error(
                f"Unhandled exception in request: {str(e)}",
                extra={
                    "request_id": request_id,
                    "method": request.method,
                    "path": request.url.path,
                    "error_type": type(e).__name__
                },
                exc_info=True
            )
            
            # Return formatted error response
            return JSONResponse(
                status_code=500,
                content={
                    "error": "InternalServerError",
                    "message": "An unexpected error occurred",
                    "details": {
                        "request_id": request_id,
                        "error_type": type(e).__name__
                    }
                }
            )
