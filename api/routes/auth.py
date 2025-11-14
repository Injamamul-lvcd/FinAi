"""
Authentication endpoints for user registration and login.

This module provides endpoints for user authentication including
registration, login, and token management.
"""

import logging
from typing import Optional
from fastapi import APIRouter, HTTPException, status, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from models.schemas import (
    UserRegister,
    UserLogin,
    Token,
    UserResponse,
    PasswordChange,
    ForgotPasswordRequest,
    ResetPasswordRequest,
    ForgotPasswordResponse,
    ErrorResponse
)
from services.auth_service import AuthService
from config.settings import get_settings

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/v1/auth",
    tags=["authentication"]
)

# Security scheme
security = HTTPBearer()

# Global auth service instance
auth_service: Optional[AuthService] = None


def initialize_auth_service():
    """
    Initialize authentication service.
    Called during application startup.
    """
    global auth_service
    
    try:
        settings = get_settings()
        
        auth_service = AuthService(
            connection_string=settings.mongodb_connection_string,
            database_name=settings.mongodb_database_name,
            secret_key=settings.jwt_secret_key,
            algorithm=settings.jwt_algorithm,
            access_token_expire_minutes=settings.jwt_access_token_expire_minutes
        )
        
        logger.info("Authentication service initialized successfully")
        
    except Exception as e:
        logger.error(f"Failed to initialize authentication service: {e}")
        raise


def get_auth_service() -> AuthService:
    """Get the auth service instance."""
    if auth_service is None:
        raise RuntimeError("Authentication service not initialized")
    return auth_service


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> dict:
    """
    Dependency to get current authenticated user from JWT token.
    
    Args:
        credentials: HTTP Bearer token credentials
        
    Returns:
        dict: Current user information
        
    Raises:
        HTTPException: If token is invalid or user not found
    """
    auth_svc = get_auth_service()
    
    # Decode token
    payload = auth_svc.decode_token(credentials.credentials)
    
    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Get username from token
    username: str = payload.get("sub")
    if username is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Get user from database
    user = auth_svc.get_user_by_username(username)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    return user


@router.post(
    "/register",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new user",
    description="Create a new user account with username, email, and password",
    responses={
        201: {
            "description": "User registered successfully",
            "model": UserResponse
        },
        400: {
            "description": "Invalid input or user already exists",
            "model": ErrorResponse
        },
        500: {
            "description": "Internal server error",
            "model": ErrorResponse
        }
    }
)
async def register(user_data: UserRegister) -> UserResponse:
    """
    Register a new user account.
    
    Args:
        user_data: User registration data
        
    Returns:
        UserResponse: Created user information
        
    Raises:
        HTTPException: If registration fails
    """
    auth_svc = get_auth_service()
    
    try:
        logger.info(f"Registration attempt for username: {user_data.username}")
        
        # Register user
        user = auth_svc.register_user(
            username=user_data.username,
            email=user_data.email,
            password=user_data.password,
            full_name=user_data.full_name
        )
        
        logger.info(f"User registered successfully: {user_data.username}")
        
        return UserResponse(**user)
        
    except ValueError as e:
        # Handle duplicate username/email
        logger.warning(f"Registration failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "error": "RegistrationError",
                "message": str(e),
                "details": None
            }
        )
    except Exception as e:
        logger.error(f"Registration error: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": "RegistrationError",
                "message": "Failed to register user",
                "details": {"error": str(e)}
            }
        )


@router.post(
    "/login",
    response_model=Token,
    status_code=status.HTTP_200_OK,
    summary="Login user",
    description="Authenticate user and receive JWT access token",
    responses={
        200: {
            "description": "Login successful",
            "model": Token
        },
        401: {
            "description": "Invalid credentials",
            "model": ErrorResponse
        },
        500: {
            "description": "Internal server error",
            "model": ErrorResponse
        }
    }
)
async def login(credentials: UserLogin) -> Token:
    """
    Authenticate user and return JWT token.
    
    Args:
        credentials: User login credentials
        
    Returns:
        Token: JWT access token and user information
        
    Raises:
        HTTPException: If authentication fails
    """
    auth_svc = get_auth_service()
    
    try:
        logger.info(f"Login attempt for username: {credentials.username}")
        
        # Authenticate user
        user = auth_svc.authenticate_user(
            username=credentials.username,
            password=credentials.password
        )
        
        if user is None:
            logger.warning(f"Login failed for username: {credentials.username}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail={
                    "error": "AuthenticationError",
                    "message": "Incorrect username or password",
                    "details": None
                },
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        # Create access token
        access_token = auth_svc.create_access_token(
            data={"sub": user["username"]}
        )
        
        logger.info(f"Login successful for username: {credentials.username}")
        
        return Token(
            access_token=access_token,
            token_type="bearer",
            user=UserResponse(**user)
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Login error: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": "AuthenticationError",
                "message": "Failed to authenticate user",
                "details": {"error": str(e)}
            }
        )


@router.get(
    "/me",
    response_model=UserResponse,
    status_code=status.HTTP_200_OK,
    summary="Get current user",
    description="Get information about the currently authenticated user",
    responses={
        200: {
            "description": "User information retrieved successfully",
            "model": UserResponse
        },
        401: {
            "description": "Not authenticated",
            "model": ErrorResponse
        }
    }
)
async def get_me(current_user: dict = Depends(get_current_user)) -> UserResponse:
    """
    Get current authenticated user information.
    
    Args:
        current_user: Current user from JWT token (injected by dependency)
        
    Returns:
        UserResponse: Current user information
    """
    return UserResponse(**current_user)


@router.post(
    "/change-password",
    status_code=status.HTTP_200_OK,
    summary="Change password",
    description="Change the password for the currently authenticated user",
    responses={
        200: {
            "description": "Password changed successfully"
        },
        400: {
            "description": "Invalid old password",
            "model": ErrorResponse
        },
        401: {
            "description": "Not authenticated",
            "model": ErrorResponse
        }
    }
)
async def change_password(
    password_data: PasswordChange,
    current_user: dict = Depends(get_current_user)
):
    """
    Change user password.
    
    Args:
        password_data: Old and new password
        current_user: Current user from JWT token (injected by dependency)
        
    Returns:
        Success message
        
    Raises:
        HTTPException: If password change fails
    """
    auth_svc = get_auth_service()
    
    try:
        logger.info(f"Password change attempt for user: {current_user['username']}")
        
        # Change password
        success = auth_svc.change_password(
            username=current_user['username'],
            old_password=password_data.old_password,
            new_password=password_data.new_password
        )
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "error": "PasswordChangeError",
                    "message": "Invalid old password",
                    "details": None
                }
            )
        
        logger.info(f"Password changed successfully for user: {current_user['username']}")
        
        return {
            "success": True,
            "message": "Password changed successfully"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Password change error: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": "PasswordChangeError",
                "message": "Failed to change password",
                "details": {"error": str(e)}
            }
        )


@router.post(
    "/forgot-password",
    response_model=ForgotPasswordResponse,
    status_code=status.HTTP_200_OK,
    summary="Request password reset",
    description="Request a password reset token for the given email address",
    responses={
        200: {
            "description": "Password reset request processed",
            "model": ForgotPasswordResponse
        },
        500: {
            "description": "Internal server error",
            "model": ErrorResponse
        }
    }
)
async def forgot_password(request: ForgotPasswordRequest) -> ForgotPasswordResponse:
    """
    Request a password reset token.
    
    For security reasons, this endpoint always returns success even if the email
    doesn't exist. This prevents email enumeration attacks.
    
    In production, the reset token should be sent via email. For development/testing,
    the token can be returned in the response (controlled by settings).
    
    Args:
        request: Forgot password request with email
        
    Returns:
        ForgotPasswordResponse with success message
        
    Raises:
        HTTPException: If request processing fails
    """
    auth_svc = get_auth_service()
    
    try:
        logger.info(f"Password reset requested for email: {request.email}")
        
        # Create reset token
        reset_token = auth_svc.create_password_reset_token(request.email)
        
        # For security, always return success message
        # This prevents email enumeration attacks
        message = "If the email exists, a password reset link has been sent."
        
        # In production, send email here
        # For development/testing, we can return the token
        # TODO: Implement email sending service
        if reset_token:
            logger.info(f"Password reset token created for email: {request.email}")
            # In development, you might want to log or return the token
            # In production, send it via email and don't return it
            
            # For development/testing only - remove in production
            settings = get_settings()
            if settings.log_level == "DEBUG":
                logger.debug(f"Reset token (DEBUG only): {reset_token}")
                return ForgotPasswordResponse(
                    message=message,
                    reset_token=reset_token  # Only for development
                )
        else:
            logger.info(f"Password reset requested for non-existent email: {request.email}")
        
        # Production response (no token)
        return ForgotPasswordResponse(
            message=message,
            reset_token=None
        )
        
    except Exception as e:
        logger.error(f"Forgot password error: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": "ForgotPasswordError",
                "message": "Failed to process password reset request",
                "details": {"error": str(e)}
            }
        )


@router.post(
    "/reset-password",
    status_code=status.HTTP_200_OK,
    summary="Reset password",
    description="Reset password using the reset token received via email",
    responses={
        200: {
            "description": "Password reset successfully"
        },
        400: {
            "description": "Invalid or expired token",
            "model": ErrorResponse
        },
        500: {
            "description": "Internal server error",
            "model": ErrorResponse
        }
    }
)
async def reset_password(request: ResetPasswordRequest):
    """
    Reset password using reset token.
    
    Args:
        request: Reset password request with token and new password
        
    Returns:
        Success message
        
    Raises:
        HTTPException: If password reset fails
    """
    auth_svc = get_auth_service()
    
    try:
        logger.info("Password reset attempt with token")
        
        # Reset password
        success = auth_svc.reset_password(
            token=request.token,
            new_password=request.new_password
        )
        
        if not success:
            logger.warning("Password reset failed: invalid or expired token")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "error": "ResetPasswordError",
                    "message": "Invalid or expired reset token",
                    "details": None
                }
            )
        
        logger.info("Password reset successful")
        
        return {
            "success": True,
            "message": "Password reset successfully. You can now login with your new password."
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Reset password error: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": "ResetPasswordError",
                "message": "Failed to reset password",
                "details": {"error": str(e)}
            }
        )
