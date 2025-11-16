"""
Admin authentication and authorization utilities.

This module provides dependencies and utilities for admin-only endpoints,
including role verification and activity logging.
"""

import logging
from typing import Optional
from datetime import datetime
from fastapi import Depends, HTTPException, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

logger = logging.getLogger(__name__)

# Security scheme
security = HTTPBearer()


def _create_error_response(error_type: str, message: str, details: Optional[dict] = None) -> dict:
    """
    Create a consistent error response format.
    
    Args:
        error_type: Type of error (e.g., "AuthenticationError")
        message: Human-readable error message
        details: Optional additional details
        
    Returns:
        dict: Formatted error response
    """
    return {
        "error": error_type,
        "message": message,
        "details": details,
        "timestamp": datetime.utcnow().isoformat() + "Z"
    }


async def get_current_admin(
    request: Request,
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> dict:
    """
    Dependency to get current authenticated admin user from JWT token.
    
    This dependency verifies:
    1. Token is valid
    2. User exists
    3. User is active
    4. User has admin role
    
    Args:
        request: FastAPI request object (for IP address logging)
        credentials: HTTP Bearer token credentials
        
    Returns:
        dict: Current admin user information
        
    Raises:
        HTTPException: 401 if token invalid, 403 if not admin
    """
    # Import here to avoid circular dependency
    from api.routes.auth import get_auth_service
    
    auth_svc = get_auth_service()
    
    # Decode token
    payload = auth_svc.decode_token(credentials.credentials)
    
    if payload is None:
        logger.warning("Invalid token in admin authentication attempt")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=_create_error_response(
                "AuthenticationError",
                "Invalid or expired authentication token",
                {"reason": "token_invalid"}
            ),
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Get username from token
    username: str = payload.get("sub")
    if username is None:
        logger.warning("Token missing username in admin authentication attempt")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=_create_error_response(
                "AuthenticationError",
                "Invalid authentication credentials",
                {"reason": "missing_username"}
            ),
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Get user from database
    user = auth_svc.get_user_by_username(username)
    if user is None:
        logger.warning(f"User not found in admin authentication: {username}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=_create_error_response(
                "AuthenticationError",
                "User not found",
                {"reason": "user_not_found"}
            ),
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Check if user is active
    if not user.get("is_active", True):
        logger.warning(f"Inactive user attempted admin access: {username}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=_create_error_response(
                "AuthenticationError",
                "User account is inactive",
                {"reason": "account_inactive"}
            ),
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Check if user has admin role
    if not user.get("is_admin", False):
        logger.warning(f"Non-admin user attempted admin access: {username}")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=_create_error_response(
                "AdminAuthorizationError",
                "Admin access required",
                {"reason": "insufficient_privileges", "required_role": "admin"}
            )
        )
    
    # Add IP address to user info for logging
    client_host = request.client.host if request.client else None
    user["ip_address"] = client_host
    
    logger.info(f"Admin authenticated successfully: {username}")
    
    return user


def get_client_ip(request: Request) -> Optional[str]:
    """
    Extract client IP address from request.
    
    Args:
        request: FastAPI request object
        
    Returns:
        Optional[str]: Client IP address or None
    """
    # Check for forwarded IP (behind proxy)
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0].strip()
    
    # Check for real IP header
    real_ip = request.headers.get("X-Real-IP")
    if real_ip:
        return real_ip
    
    # Fall back to direct client IP
    if request.client:
        return request.client.host
    
    return None
