"""
Admin Panel API Routes

This module provides comprehensive administrative endpoints for the Financial Chatbot RAG System.

## Overview

The Admin Panel APIs enable administrators to manage users, documents, monitor system health,
view analytics, and configure system settings through secure, role-based REST endpoints.

## Authentication

**All admin endpoints require authentication with a valid JWT token.**

### How to Authenticate:

1. Obtain an admin JWT token by logging in with admin credentials
2. Include the token in the Authorization header of all requests:
   ```
   Authorization: Bearer <your_jwt_token>
   ```

### Token Requirements:

- Token must be valid and not expired (8-hour expiration)
- User associated with token must have admin role (is_admin=true)
- Invalid or missing tokens return 401 Unauthorized
- Non-admin users return 403 Forbidden

## Endpoint Categories

### User Management (`/api/v1/admin/users`)
- List all users with pagination, search, and sorting
- View detailed user information
- Enable/disable user accounts
- Reset user passwords
- View user activity logs

### Document Management (`/api/v1/admin/documents`)
- List all documents across all users
- Delete documents with audit logging
- View document statistics and usage analytics

### System Monitoring (`/api/v1/admin/system`)
- Check system health status
- View performance metrics
- Monitor storage usage
- Analyze API usage patterns
- Retrieve error logs

### Analytics (`/api/v1/admin/analytics`)
- User engagement metrics
- Session analytics
- Document usage analytics

### Configuration Management (`/api/v1/admin/config`)
- View all configuration settings
- Get specific setting details
- Update settings with validation

## Pagination

Endpoints that return lists support pagination with the following parameters:

- `page`: Page number (1-indexed, default: 1)
- `page_size`: Records per page (10-100, default: 50)

Responses include:
- `total`: Total number of matching records
- `page`: Current page number
- `page_size`: Records per page
- `total_pages`: Total number of pages

## Filtering and Sorting

Many endpoints support filtering and sorting:

- **Search**: Case-insensitive partial matching on specified fields
- **Date Range**: ISO format dates (YYYY-MM-DDTHH:MM:SS)
- **Sort**: Specify field and order (asc/desc)

## Error Responses

All endpoints return consistent error responses:

```json
{
    "error": "ErrorType",
    "message": "Human-readable error message",
    "details": {
        "field": "Additional context"
    }
}
```

Common error codes:
- 400: Bad Request (validation errors)
- 401: Unauthorized (invalid/missing token)
- 403: Forbidden (admin access required)
- 404: Not Found (resource doesn't exist)
- 500: Internal Server Error

## Audit Trail

Administrative actions are automatically logged for audit purposes:
- User status changes
- Password resets
- Document deletions
- Configuration updates

Logs include admin ID, timestamp, action details, and IP address.

## Rate Limiting

Admin endpoints have separate rate limits (default: 100 requests/minute per admin).
Exceeding rate limits returns 429 Too Many Requests.

## Security Considerations

- All passwords are hashed before storage
- Temporary passwords are cryptographically random
- Sensitive data is masked in logs
- All admin actions are logged for audit trail
- CORS is configured for admin endpoints
"""

import logging
from typing import Optional
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status, Query

from models.schemas import (
    UserListResponse,
    UserDetail,
    UserStatusUpdate,
    PasswordResetResponse,
    ActivityLogResponse,
    ErrorResponse,
    AdminDocumentListResponse,
    DocumentStatsResponse,
    DocumentDeleteResponse,
    SystemHealthResponse,
    SystemMetricsResponse,
    StorageMetricsResponse,
    APIUsageMetrics,
    ErrorLogsResponse,
    UserEngagementMetrics,
    SessionAnalytics,
    DocumentUsageAnalytics,
    ConfigSettingsListResponse,
    ConfigSetting,
    ConfigUpdateRequest,
    ConfigUpdateResponse
)
from utils.admin_auth import get_current_admin
from services.admin_user_service import AdminUserService
from config.settings import get_settings

logger = logging.getLogger(__name__)

# Create router
router = APIRouter(
    prefix="/api/v1/admin",
    tags=["Admin Panel"],
    responses={
        401: {
            "model": ErrorResponse,
            "description": "Unauthorized - Invalid or missing token",
            "content": {
                "application/json": {
                    "example": {
                        "error": "AuthenticationError",
                        "message": "Invalid or expired authentication token",
                        "details": None
                    }
                }
            }
        },
        403: {
            "model": ErrorResponse,
            "description": "Forbidden - Admin access required",
            "content": {
                "application/json": {
                    "example": {
                        "error": "AuthorizationError",
                        "message": "Admin privileges required to access this resource",
                        "details": None
                    }
                }
            }
        },
    }
)

# Global service instances
_admin_user_service: Optional[AdminUserService] = None


def get_admin_user_service() -> AdminUserService:
    """
    Get or create AdminUserService instance.
    
    Returns:
        AdminUserService: The admin user service instance
    """
    global _admin_user_service
    if _admin_user_service is None:
        settings = get_settings()
        _admin_user_service = AdminUserService(
            connection_string=settings.mongodb_connection_string,
            database_name=settings.mongodb_database_name
        )
    return _admin_user_service


def initialize_admin_services():
    """Initialize admin services on application startup."""
    try:
        get_admin_user_service()
        logger.info("Admin services initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize admin services: {e}")
        raise


# User Management Endpoints

@router.get(
    "/users",
    response_model=UserListResponse,
    summary="List all users",
    description="""
    Retrieve a paginated list of all registered users with their details.
    
    **Features:**
    - Pagination with configurable page size (10-100 records)
    - Search by username or email (case-insensitive partial matching)
    - Sort by registration date, last login, or username
    - Returns total count and page information
    
    **Authentication:** Requires valid admin JWT token in Authorization header.
    
    **Use Cases:**
    - Monitor user accounts and activity
    - Search for specific users
    - Track user registration trends
    """,
    responses={
        200: {
            "description": "Successfully retrieved user list",
            "content": {
                "application/json": {
                    "example": {
                        "users": [
                            {
                                "user_id": "507f1f77bcf86cd799439011",
                                "username": "john_doe",
                                "email": "john@example.com",
                                "full_name": "John Doe",
                                "is_active": True,
                                "is_admin": False,
                                "password_reset_required": False,
                                "created_at": "2024-11-09T10:30:00",
                                "updated_at": "2024-11-14T15:20:00",
                                "last_login": "2024-11-14T09:15:00",
                                "document_count": 5,
                                "query_count": 42
                            }
                        ],
                        "total": 150,
                        "page": 1,
                        "page_size": 50,
                        "total_pages": 3
                    }
                }
            }
        },
        500: {
            "model": ErrorResponse,
            "description": "Internal server error",
            "content": {
                "application/json": {
                    "example": {
                        "error": "InternalServerError",
                        "message": "Failed to retrieve users",
                        "details": None
                    }
                }
            }
        }
    }
)
async def list_users(
    page: int = Query(1, ge=1, description="Page number (1-indexed)", example=1),
    page_size: int = Query(50, ge=10, le=100, description="Number of records per page (10-100)", example=50),
    search: Optional[str] = Query(None, max_length=100, description="Search by username or email (case-insensitive)", example="john"),
    sort_by: str = Query("created_at", description="Field to sort by: created_at, last_login, or username", example="created_at"),
    sort_order: str = Query("desc", description="Sort order: asc (ascending) or desc (descending)", example="desc"),
    current_admin: dict = Depends(get_current_admin)
):
    """
    List all users with pagination, search, and sorting.
    
    Requires admin authentication.
    """
    try:
        admin_user_service = get_admin_user_service()
        
        result = admin_user_service.get_users(
            page=page,
            page_size=page_size,
            search=search,
            sort_by=sort_by,
            sort_order=sort_order
        )
        
        logger.info(
            f"Admin {current_admin['username']} listed users "
            f"(page {page}, search: {search})"
        )
        
        return result
        
    except Exception as e:
        logger.error(f"Error listing users: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": "InternalServerError",
                "message": "Failed to retrieve users",
                "details": None
            }
        )


@router.get(
    "/users/{user_id}",
    response_model=UserDetail,
    summary="Get user details",
    description="""
    Retrieve complete information for a specific user account.
    
    **Returns:**
    - User profile information (username, email, full name)
    - Account status and role
    - Activity metrics (document count, query count)
    - Timestamps (created, updated, last login)
    
    **Authentication:** Requires valid admin JWT token in Authorization header.
    
    **Use Cases:**
    - View detailed user information
    - Check user activity and engagement
    - Verify account status before taking action
    """,
    responses={
        200: {
            "description": "Successfully retrieved user details",
            "content": {
                "application/json": {
                    "example": {
                        "user_id": "507f1f77bcf86cd799439011",
                        "username": "john_doe",
                        "email": "john@example.com",
                        "full_name": "John Doe",
                        "is_active": True,
                        "is_admin": False,
                        "password_reset_required": False,
                        "created_at": "2024-11-09T10:30:00",
                        "updated_at": "2024-11-14T15:20:00",
                        "last_login": "2024-11-14T09:15:00",
                        "document_count": 5,
                        "query_count": 42
                    }
                }
            }
        },
        404: {
            "model": ErrorResponse,
            "description": "User not found",
            "content": {
                "application/json": {
                    "example": {
                        "error": "ResourceNotFoundError",
                        "message": "User with ID 507f1f77bcf86cd799439011 not found",
                        "details": None
                    }
                }
            }
        }
    }
)
async def get_user_details(
    user_id: str,
    current_admin: dict = Depends(get_current_admin)
):
    """
    Get detailed information for a specific user.
    
    Requires admin authentication.
    """
    try:
        admin_user_service = get_admin_user_service()
        
        user_details = admin_user_service.get_user_details(user_id)
        
        if user_details is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={
                    "error": "ResourceNotFoundError",
                    "message": f"User with ID {user_id} not found",
                    "details": None
                }
            )
        
        logger.info(f"Admin {current_admin['username']} retrieved details for user {user_id}")
        
        return user_details
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving user details: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": "InternalServerError",
                "message": "Failed to retrieve user details",
                "details": None
            }
        )


@router.put(
    "/users/{user_id}/status",
    response_model=UserDetail,
    summary="Update user account status",
    description="""
    Enable or disable a user account to control system access.
    
    **Actions:**
    - Enable account: Set is_active to true, allows user authentication
    - Disable account: Set is_active to false, prevents user authentication
    
    **Audit Trail:** All status changes are logged with admin ID, timestamp, and optional reason.
    
    **Authentication:** Requires valid admin JWT token in Authorization header.
    
    **Use Cases:**
    - Suspend accounts for policy violations
    - Temporarily disable inactive accounts
    - Re-enable previously suspended accounts
    """,
    responses={
        200: {
            "description": "Successfully updated user status",
            "content": {
                "application/json": {
                    "example": {
                        "user_id": "507f1f77bcf86cd799439011",
                        "username": "john_doe",
                        "email": "john@example.com",
                        "full_name": "John Doe",
                        "is_active": False,
                        "is_admin": False,
                        "password_reset_required": False,
                        "created_at": "2024-11-09T10:30:00",
                        "updated_at": "2024-11-14T15:20:00",
                        "last_login": "2024-11-14T09:15:00",
                        "document_count": 5,
                        "query_count": 42
                    }
                }
            }
        },
        404: {
            "model": ErrorResponse,
            "description": "User not found",
            "content": {
                "application/json": {
                    "example": {
                        "error": "ResourceNotFoundError",
                        "message": "User with ID 507f1f77bcf86cd799439011 not found or update failed",
                        "details": None
                    }
                }
            }
        }
    }
)
async def update_user_status(
    user_id: str,
    status_update: UserStatusUpdate,
    current_admin: dict = Depends(get_current_admin)
):
    """
    Update user account status (enable/disable).
    
    Requires admin authentication. Action is logged for audit trail.
    """
    try:
        admin_user_service = get_admin_user_service()
        
        # Update status
        success = admin_user_service.update_user_status(
            user_id=user_id,
            is_active=status_update.is_active,
            admin_id=current_admin['user_id'],
            reason=status_update.reason
        )
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={
                    "error": "ResourceNotFoundError",
                    "message": f"User with ID {user_id} not found or update failed",
                    "details": None
                }
            )
        
        # Get updated user details
        user_details = admin_user_service.get_user_details(user_id)
        
        logger.info(
            f"Admin {current_admin['username']} updated status for user {user_id} "
            f"to {'active' if status_update.is_active else 'inactive'}"
        )
        
        return user_details
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating user status: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": "InternalServerError",
                "message": "Failed to update user status",
                "details": None
            }
        )


@router.post(
    "/users/{user_id}/reset-password",
    response_model=PasswordResetResponse,
    summary="Reset user password",
    description="""
    Generate a secure temporary password for a user account.
    
    **Password Requirements:**
    - 12 characters minimum
    - Mix of uppercase, lowercase, numbers, and special characters
    - Cryptographically random generation
    
    **Security:**
    - User must change password on next login
    - Temporary password is hashed before storage
    - Action is logged for audit trail
    
    **Authentication:** Requires valid admin JWT token in Authorization header.
    
    **Use Cases:**
    - Help users regain access to locked accounts
    - Reset compromised passwords
    - Provide initial passwords for new accounts
    """,
    responses={
        200: {
            "description": "Successfully reset password",
            "content": {
                "application/json": {
                    "example": {
                        "temporary_password": "Xy9$mK2pL#4q",
                        "expires_at": "User must change password on next login",
                        "message": "Password reset successfully. Provide the temporary password to the user."
                    }
                }
            }
        },
        404: {
            "model": ErrorResponse,
            "description": "User not found",
            "content": {
                "application/json": {
                    "example": {
                        "error": "ResourceNotFoundError",
                        "message": "User with ID 507f1f77bcf86cd799439011 not found or reset failed",
                        "details": None
                    }
                }
            }
        }
    }
)
async def reset_user_password(
    user_id: str,
    current_admin: dict = Depends(get_current_admin)
):
    """
    Reset user password with a secure temporary password.
    
    Generates a 12-character password with mixed character types.
    User will be required to change password on next login.
    
    Requires admin authentication. Action is logged for audit trail.
    """
    try:
        admin_user_service = get_admin_user_service()
        
        # Reset password
        temp_password = admin_user_service.reset_user_password(
            user_id=user_id,
            admin_id=current_admin['user_id']
        )
        
        if temp_password is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={
                    "error": "ResourceNotFoundError",
                    "message": f"User with ID {user_id} not found or reset failed",
                    "details": None
                }
            )
        
        logger.info(f"Admin {current_admin['username']} reset password for user {user_id}")
        
        return {
            "temporary_password": temp_password,
            "expires_at": "User must change password on next login",
            "message": "Password reset successfully. Provide the temporary password to the user."
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error resetting user password: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": "InternalServerError",
                "message": "Failed to reset user password",
                "details": None
            }
        )


@router.get(
    "/users/{user_id}/activity",
    response_model=ActivityLogResponse,
    summary="Get user activity logs",
    description="""
    Retrieve activity logs for administrative actions performed on a user account.
    
    **Log Information:**
    - Action type (user_disabled, user_enabled, password_reset, etc.)
    - Admin who performed the action
    - Timestamp and IP address
    - Action details and result
    
    **Filtering:**
    - Date range filtering with ISO format dates
    - Pagination with configurable page size
    
    **Authentication:** Requires valid admin JWT token in Authorization header.
    
    **Use Cases:**
    - Audit trail for user account changes
    - Troubleshoot user issues
    - Compliance and security monitoring
    """,
    responses={
        200: {
            "description": "Successfully retrieved activity logs",
            "content": {
                "application/json": {
                    "example": {
                        "logs": [
                            {
                                "log_id": "507f1f77bcf86cd799439012",
                                "admin_username": "admin_user",
                                "action_type": "user_disabled",
                                "resource_type": "user",
                                "resource_id": "507f1f77bcf86cd799439011",
                                "details": {
                                    "username": "john_doe",
                                    "reason": "Policy violation"
                                },
                                "ip_address": "192.168.1.100",
                                "timestamp": "2024-11-14T10:30:00",
                                "result": "success"
                            }
                        ],
                        "total": 25,
                        "page": 1,
                        "page_size": 50,
                        "total_pages": 1
                    }
                }
            }
        },
        400: {
            "model": ErrorResponse,
            "description": "Invalid date format",
            "content": {
                "application/json": {
                    "example": {
                        "error": "ValidationError",
                        "message": "Invalid start_date format. Use ISO format (YYYY-MM-DDTHH:MM:SS)",
                        "details": None
                    }
                }
            }
        }
    }
)
async def get_user_activity(
    user_id: str,
    page: int = Query(1, ge=1, description="Page number (1-indexed)", example=1),
    page_size: int = Query(50, ge=10, le=100, description="Number of records per page (10-100)", example=50),
    start_date: Optional[str] = Query(None, description="Start date in ISO format (YYYY-MM-DDTHH:MM:SS)", example="2024-11-01T00:00:00"),
    end_date: Optional[str] = Query(None, description="End date in ISO format (YYYY-MM-DDTHH:MM:SS)", example="2024-11-14T23:59:59"),
    current_admin: dict = Depends(get_current_admin)
):
    """
    Get activity logs for a specific user.
    
    Returns logs of administrative actions performed on this user account.
    
    Requires admin authentication.
    """
    try:
        admin_user_service = get_admin_user_service()
        
        # Parse dates if provided
        start_datetime = None
        end_datetime = None
        
        if start_date:
            try:
                start_datetime = datetime.fromisoformat(start_date)
            except ValueError:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail={
                        "error": "ValidationError",
                        "message": "Invalid start_date format. Use ISO format (YYYY-MM-DDTHH:MM:SS)",
                        "details": None
                    }
                )
        
        if end_date:
            try:
                end_datetime = datetime.fromisoformat(end_date)
            except ValueError:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail={
                        "error": "ValidationError",
                        "message": "Invalid end_date format. Use ISO format (YYYY-MM-DDTHH:MM:SS)",
                        "details": None
                    }
                )
        
        # Get activity logs
        result = admin_user_service.get_user_activity(
            user_id=user_id,
            start_date=start_datetime,
            end_date=end_datetime,
            page=page,
            page_size=page_size
        )
        
        logger.info(
            f"Admin {current_admin['username']} retrieved activity logs for user {user_id}"
        )
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving user activity: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": "InternalServerError",
                "message": "Failed to retrieve user activity",
                "details": None
            }
        )



# Document Management Endpoints

# Global document service instance
_admin_document_service: Optional['AdminDocumentService'] = None


def get_admin_document_service() -> 'AdminDocumentService':
    """
    Get or create AdminDocumentService instance.
    
    Returns:
        AdminDocumentService: The admin document service instance
    """
    global _admin_document_service
    if _admin_document_service is None:
        from services.admin_document_service import AdminDocumentService
        from services.vector_store import VectorStoreManager
        from services.activity_logger import ActivityLogger
        
        settings = get_settings()
        
        # Initialize dependencies
        vector_store = VectorStoreManager()
        activity_logger = ActivityLogger(
            connection_string=settings.mongodb_connection_string,
            database_name=settings.mongodb_database_name
        )
        
        _admin_document_service = AdminDocumentService(
            vector_store=vector_store,
            activity_logger=activity_logger,
            connection_string=settings.mongodb_connection_string,
            database_name=settings.mongodb_database_name
        )
    return _admin_document_service


@router.get(
    "/documents",
    response_model=AdminDocumentListResponse,
    summary="List all documents",
    description="""
    Retrieve a paginated list of all documents across all users.
    
    **Document Information:**
    - Document ID and filename
    - Uploader username and user ID
    - Upload date and file size
    - Chunk count and query count
    
    **Filtering:**
    - Search by filename or uploader username (case-insensitive)
    - Date range filtering by upload date
    - Pagination with configurable page size (10-100)
    
    **Authentication:** Requires valid admin JWT token in Authorization header.
    
    **Use Cases:**
    - Monitor document repository
    - Search for specific documents
    - Track document uploads by user
    - Identify large or frequently queried documents
    """,
    responses={
        200: {
            "description": "Successfully retrieved document list",
            "content": {
                "application/json": {
                    "example": {
                        "documents": [
                            {
                                "document_id": "doc_123",
                                "filename": "financial_report_q4.pdf",
                                "uploader_username": "john_doe",
                                "uploader_user_id": "507f1f77bcf86cd799439011",
                                "upload_date": "2024-11-14T10:30:00",
                                "file_size_mb": 2.45,
                                "chunk_count": 42,
                                "query_count": 15
                            }
                        ],
                        "total": 150,
                        "page": 1,
                        "page_size": 50,
                        "total_pages": 3
                    }
                }
            }
        },
        400: {
            "model": ErrorResponse,
            "description": "Invalid date format",
            "content": {
                "application/json": {
                    "example": {
                        "error": "ValidationError",
                        "message": "Invalid start_date format. Use ISO format (YYYY-MM-DDTHH:MM:SS)",
                        "details": None
                    }
                }
            }
        }
    }
)
async def list_documents(
    page: int = Query(1, ge=1, description="Page number (1-indexed)", example=1),
    page_size: int = Query(50, ge=10, le=100, description="Number of records per page (10-100)", example=50),
    search: Optional[str] = Query(None, max_length=100, description="Search by filename or uploader username", example="financial"),
    start_date: Optional[str] = Query(None, description="Start date filter in ISO format", example="2024-11-01T00:00:00"),
    end_date: Optional[str] = Query(None, description="End date filter in ISO format", example="2024-11-14T23:59:59"),
    current_admin: dict = Depends(get_current_admin)
):
    """
    List all documents with pagination, search, and date filtering.
    
    Requires admin authentication.
    """
    try:
        admin_document_service = get_admin_document_service()
        
        # Parse dates if provided
        start_datetime = None
        end_datetime = None
        
        if start_date:
            try:
                start_datetime = datetime.fromisoformat(start_date)
            except ValueError:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail={
                        "error": "ValidationError",
                        "message": "Invalid start_date format. Use ISO format (YYYY-MM-DDTHH:MM:SS)",
                        "details": None
                    }
                )
        
        if end_date:
            try:
                end_datetime = datetime.fromisoformat(end_date)
            except ValueError:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail={
                        "error": "ValidationError",
                        "message": "Invalid end_date format. Use ISO format (YYYY-MM-DDTHH:MM:SS)",
                        "details": None
                    }
                )
        
        result = admin_document_service.get_all_documents(
            page=page,
            page_size=page_size,
            search=search,
            start_date=start_datetime,
            end_date=end_datetime
        )
        
        logger.info(
            f"Admin {current_admin['username']} listed documents "
            f"(page {page}, search: {search})"
        )
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error listing documents: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": "InternalServerError",
                "message": "Failed to retrieve documents",
                "details": None
            }
        )


@router.delete(
    "/documents/{document_id}",
    response_model=DocumentDeleteResponse,
    summary="Delete a document",
    description="""
    Delete a document and all its chunks from the vector database.
    
    **Deletion Process:**
    - Removes document metadata from ChromaDB
    - Deletes all associated text chunks
    - Updates document statistics
    - Logs action for audit trail
    
    **Warning:** This action is permanent and cannot be undone.
    
    **Authentication:** Requires valid admin JWT token in Authorization header.
    
    **Use Cases:**
    - Remove inappropriate or outdated content
    - Clean up duplicate documents
    - Manage storage space
    - Comply with data deletion requests
    """,
    responses={
        200: {
            "description": "Successfully deleted document",
            "content": {
                "application/json": {
                    "example": {
                        "message": "Document deleted successfully",
                        "document_id": "doc_123",
                        "filename": "financial_report_q4.pdf",
                        "chunks_deleted": 42
                    }
                }
            }
        },
        404: {
            "model": ErrorResponse,
            "description": "Document not found",
            "content": {
                "application/json": {
                    "example": {
                        "error": "ResourceNotFoundError",
                        "message": "Document with ID doc_123 not found",
                        "details": None
                    }
                }
            }
        }
    }
)
async def delete_document(
    document_id: str,
    current_admin: dict = Depends(get_current_admin)
):
    """
    Delete a document with proper authorization.
    
    Removes document metadata and all associated chunks from vector database.
    Action is logged for audit trail.
    
    Requires admin authentication.
    """
    try:
        admin_document_service = get_admin_document_service()
        
        # Delete document
        result = admin_document_service.delete_document(
            document_id=document_id,
            admin_id=current_admin['user_id']
        )
        
        if result is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={
                    "error": "ResourceNotFoundError",
                    "message": f"Document with ID {document_id} not found",
                    "details": None
                }
            )
        
        logger.info(
            f"Admin {current_admin['username']} deleted document {document_id} "
            f"({result['filename']})"
        )
        
        return {
            "message": "Document deleted successfully",
            "document_id": result['document_id'],
            "filename": result['filename'],
            "chunks_deleted": result['chunks_deleted']
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting document: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": "InternalServerError",
                "message": "Failed to delete document",
                "details": None
            }
        )


@router.get(
    "/documents/stats",
    response_model=DocumentStatsResponse,
    summary="Get document statistics",
    description="""
    Retrieve comprehensive document statistics and usage analytics.
    
    **Statistics Included:**
    - Total documents, chunks, and storage size
    - Average chunks per document
    - Document count by file type with percentages
    - Upload trend for last 30 days
    - Top 10 most queried documents
    
    **Authentication:** Requires valid admin JWT token in Authorization header.
    
    **Use Cases:**
    - Monitor document repository growth
    - Identify most valuable documents
    - Plan storage capacity
    - Understand document usage patterns
    - Track upload trends over time
    """,
    responses={
        200: {
            "description": "Successfully retrieved document statistics",
            "content": {
                "application/json": {
                    "example": {
                        "total_documents": 150,
                        "total_chunks": 6300,
                        "total_size_mb": 245.67,
                        "avg_chunks_per_doc": 42.0,
                        "documents_by_type": [
                            {
                                "file_type": "pdf",
                                "count": 100,
                                "percentage": 66.67
                            },
                            {
                                "file_type": "docx",
                                "count": 50,
                                "percentage": 33.33
                            }
                        ],
                        "upload_trend": [
                            {
                                "date": "2024-11-14",
                                "count": 5
                            }
                        ],
                        "top_documents": [
                            {
                                "document_id": "doc_123",
                                "filename": "financial_report_q4.pdf",
                                "query_count": 150,
                                "last_queried": "2024-11-14T15:30:00"
                            }
                        ]
                    }
                }
            }
        }
    }
)
async def get_document_statistics(
    current_admin: dict = Depends(get_current_admin)
):
    """
    Get document statistics and usage analytics.
    
    Returns total documents, chunks, storage size, file type distribution,
    upload trends, and top queried documents.
    
    Requires admin authentication.
    """
    try:
        admin_document_service = get_admin_document_service()
        
        stats = admin_document_service.get_document_statistics()
        
        logger.info(f"Admin {current_admin['username']} retrieved document statistics")
        
        return stats
        
    except Exception as e:
        logger.error(f"Error retrieving document statistics: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": "InternalServerError",
                "message": "Failed to retrieve document statistics",
                "details": None
            }
        )



# System Monitoring Endpoints

# Global system monitor service instance
_system_monitor_service: Optional['SystemMonitorService'] = None


def get_system_monitor_service() -> 'SystemMonitorService':
    """
    Get or create SystemMonitorService instance.
    
    Returns:
        SystemMonitorService: The system monitor service instance
    """
    global _system_monitor_service
    if _system_monitor_service is None:
        from services.system_monitor_service import SystemMonitorService
        from services.vector_store import VectorStoreManager
        
        settings = get_settings()
        
        # Initialize dependencies
        vector_store = VectorStoreManager()
        
        _system_monitor_service = SystemMonitorService(
            connection_string=settings.mongodb_connection_string,
            database_name=settings.mongodb_database_name,
            vector_store_manager=vector_store,
            session_db_path="./data/sessions.db"
        )
    return _system_monitor_service


@router.get(
    "/system/health",
    response_model=SystemHealthResponse,
    summary="Get system health status",
    description="""
    Check health status of all system components.
    
    **Components Monitored:**
    - ChromaDB vector database connection
    - LLM API availability
    - SQLite session database
    - MongoDB connection
    
    **Status Values:**
    - healthy: Component is operational
    - degraded: Component has issues but is functional
    - unhealthy: Component is not operational
    
    **Authentication:** Requires valid admin JWT token in Authorization header.
    
    **Use Cases:**
    - Monitor system availability
    - Troubleshoot connection issues
    - Verify system readiness
    - Set up health check alerts
    """,
    responses={
        200: {
            "description": "Successfully retrieved health status",
            "content": {
                "application/json": {
                    "examples": {
                        "healthy": {
                            "summary": "All systems healthy",
                            "value": {
                                "status": "healthy",
                                "vector_db_status": "healthy",
                                "llm_api_status": "healthy",
                                "session_db_status": "healthy",
                                "mongodb_status": "healthy",
                                "timestamp": "2024-11-14T10:30:00Z",
                                "error_details": None
                            }
                        },
                        "degraded": {
                            "summary": "Some components unhealthy",
                            "value": {
                                "status": "degraded",
                                "vector_db_status": "healthy",
                                "llm_api_status": "unhealthy",
                                "session_db_status": "healthy",
                                "mongodb_status": "healthy",
                                "timestamp": "2024-11-14T10:30:00Z",
                                "error_details": {
                                    "llm_api": "Connection timeout after 30 seconds"
                                }
                            }
                        }
                    }
                }
            }
        }
    }
)
async def get_system_health(
    current_admin: dict = Depends(get_current_admin)
):
    """
    Get system health status.
    
    Returns status of vector DB, LLM API, session DB, and MongoDB connections.
    
    Requires admin authentication.
    """
    try:
        system_monitor_service = get_system_monitor_service()
        
        health_status = system_monitor_service.get_health_status()
        
        logger.info(
            f"Admin {current_admin['username']} retrieved system health status: "
            f"{health_status['status']}"
        )
        
        return health_status
        
    except Exception as e:
        logger.error(f"Error retrieving system health: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": "InternalServerError",
                "message": "Failed to retrieve system health status",
                "details": None
            }
        )


@router.get(
    "/system/metrics",
    response_model=SystemMetricsResponse,
    summary="Get system performance metrics",
    description="""
    Retrieve current system performance metrics.
    
    **Metrics Included:**
    - Active chat sessions count
    - Total API requests in last 24 hours
    - Average API response time (milliseconds)
    - Memory usage percentage
    - Disk usage percentage
    - Application uptime (hours)
    
    **Authentication:** Requires valid admin JWT token in Authorization header.
    
    **Use Cases:**
    - Monitor system performance
    - Identify performance bottlenecks
    - Track resource utilization
    - Plan capacity upgrades
    - Set up performance alerts
    """,
    responses={
        200: {
            "description": "Successfully retrieved system metrics",
            "content": {
                "application/json": {
                    "example": {
                        "active_sessions": 42,
                        "total_requests_24h": 1523,
                        "avg_response_time_ms": 245.67,
                        "memory_usage_percent": 45.2,
                        "disk_usage_percent": 62.8,
                        "uptime_hours": 72.5
                    }
                }
            }
        }
    }
)
async def get_system_metrics(
    current_admin: dict = Depends(get_current_admin)
):
    """
    Get system performance metrics.
    
    Returns active sessions, API requests, response times, memory and disk usage.
    
    Requires admin authentication.
    """
    try:
        system_monitor_service = get_system_monitor_service()
        
        metrics = system_monitor_service.get_system_metrics()
        
        logger.info(f"Admin {current_admin['username']} retrieved system metrics")
        
        return metrics
        
    except Exception as e:
        logger.error(f"Error retrieving system metrics: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": "InternalServerError",
                "message": "Failed to retrieve system metrics",
                "details": None
            }
        )


@router.get(
    "/system/storage",
    response_model=StorageMetricsResponse,
    summary="Get storage usage metrics",
    description="""
    Retrieve storage usage metrics for all databases and disk space.
    
    **Storage Metrics:**
    - Vector database size (ChromaDB)
    - Session database size (SQLite)
    - MongoDB size
    - Total uploaded document size
    - Available disk space
    - Disk usage percentage
    - Storage growth rate over last 7 days
    
    **Authentication:** Requires valid admin JWT token in Authorization header.
    
    **Use Cases:**
    - Monitor storage consumption
    - Plan capacity upgrades
    - Identify storage growth trends
    - Set up storage alerts
    - Optimize storage usage
    """,
    responses={
        200: {
            "description": "Successfully retrieved storage metrics",
            "content": {
                "application/json": {
                    "example": {
                        "vector_db_size_mb": 512.45,
                        "session_db_size_mb": 24.67,
                        "mongodb_size_mb": 128.34,
                        "total_document_size_mb": 245.67,
                        "available_disk_gb": 45.2,
                        "disk_usage_percent": 62.8,
                        "growth_rate_7d_percent": 5.3
                    }
                }
            }
        }
    }
)
async def get_storage_metrics(
    current_admin: dict = Depends(get_current_admin)
):
    """
    Get storage usage metrics.
    
    Returns database sizes, disk usage, and storage growth rate.
    
    Requires admin authentication.
    """
    try:
        system_monitor_service = get_system_monitor_service()
        
        storage_metrics = system_monitor_service.get_storage_metrics()
        
        logger.info(f"Admin {current_admin['username']} retrieved storage metrics")
        
        return storage_metrics
        
    except Exception as e:
        logger.error(f"Error retrieving storage metrics: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": "InternalServerError",
                "message": "Failed to retrieve storage metrics",
                "details": None
            }
        )


@router.get(
    "/system/api-usage",
    response_model=APIUsageMetrics,
    summary="Get API usage metrics",
    description="""
    Retrieve API usage metrics for a specified time period.
    
    **Metrics Included:**
    - Total requests and success/error counts
    - Request counts by endpoint
    - Average response time per endpoint
    - Top 5 slowest requests
    - Hourly request rate time series
    
    **Time Range:** 1 hour to 7 days (168 hours)
    
    **Authentication:** Requires valid admin JWT token in Authorization header.
    
    **Use Cases:**
    - Monitor API usage patterns
    - Identify performance issues
    - Track endpoint popularity
    - Detect unusual traffic patterns
    - Optimize slow endpoints
    """,
    responses={
        200: {
            "description": "Successfully retrieved API usage metrics",
            "content": {
                "application/json": {
                    "example": {
                        "total_requests": 1523,
                        "success_count": 1450,
                        "error_count": 73,
                        "endpoints": [
                            {
                                "endpoint": "/api/v1/chat",
                                "total_requests": 523,
                                "success_count": 498,
                                "error_count": 25,
                                "avg_response_time_ms": 245.67
                            }
                        ],
                        "slowest_requests": [
                            {
                                "endpoint": "/api/v1/chat",
                                "response_time_ms": 1523.45,
                                "timestamp": "2024-11-14T10:30:00Z",
                                "status_code": 200
                            }
                        ],
                        "hourly_rate": [
                            {
                                "hour": "2024-11-14T10:00:00Z",
                                "request_count": 125
                            }
                        ]
                    }
                }
            }
        }
    }
)
async def get_api_usage_metrics(
    hours: int = Query(24, ge=1, le=168, description="Number of hours to look back (1-168, max 7 days)", example=24),
    current_admin: dict = Depends(get_current_admin)
):
    """
    Get API usage metrics for the specified time period.
    
    Returns request counts by endpoint, success/error rates, response times,
    slowest requests, and hourly request rate.
    
    Requires admin authentication.
    """
    try:
        system_monitor_service = get_system_monitor_service()
        
        api_metrics = system_monitor_service.get_api_usage_metrics(hours=hours)
        
        logger.info(
            f"Admin {current_admin['username']} retrieved API usage metrics "
            f"(last {hours} hours)"
        )
        
        return api_metrics
        
    except Exception as e:
        logger.error(f"Error retrieving API usage metrics: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": "InternalServerError",
                "message": "Failed to retrieve API usage metrics",
                "details": None
            }
        )


@router.get(
    "/system/logs",
    response_model=ErrorLogsResponse,
    summary="Get error logs",
    description="""
    Retrieve error logs with filtering and pagination.
    
    **Log Information:**
    - Timestamp and severity level
    - Error type and message
    - Affected endpoint
    - Stack trace (if available)
    - User ID (if applicable)
    
    **Filtering:**
    - Severity: INFO, WARNING, ERROR, CRITICAL
    - Date range with ISO format dates
    - Pagination with configurable page size
    
    **Authentication:** Requires valid admin JWT token in Authorization header.
    
    **Use Cases:**
    - Troubleshoot system errors
    - Monitor error patterns
    - Identify recurring issues
    - Debug production problems
    - Compliance and audit logging
    """,
    responses={
        200: {
            "description": "Successfully retrieved error logs",
            "content": {
                "application/json": {
                    "example": {
                        "logs": [
                            {
                                "log_id": "507f1f77bcf86cd799439013",
                                "timestamp": "2024-11-14T10:30:00Z",
                                "severity": "ERROR",
                                "error_type": "DatabaseConnectionError",
                                "error_message": "Failed to connect to MongoDB",
                                "endpoint": "/api/v1/chat",
                                "stack_trace": "Traceback (most recent call last)...",
                                "user_id": "507f1f77bcf86cd799439011"
                            }
                        ],
                        "total": 25,
                        "page": 1,
                        "page_size": 50,
                        "total_pages": 1
                    }
                }
            }
        },
        400: {
            "model": ErrorResponse,
            "description": "Invalid parameters",
            "content": {
                "application/json": {
                    "example": {
                        "error": "ValidationError",
                        "message": "Invalid severity. Must be one of: INFO, WARNING, ERROR, CRITICAL",
                        "details": None
                    }
                }
            }
        }
    }
)
async def get_error_logs(
    page: int = Query(1, ge=1, description="Page number (1-indexed)", example=1),
    page_size: int = Query(50, ge=10, le=100, description="Number of records per page (10-100)", example=50),
    severity: Optional[str] = Query(None, description="Filter by severity: INFO, WARNING, ERROR, or CRITICAL", example="ERROR"),
    start_date: Optional[str] = Query(None, description="Start date in ISO format", example="2024-11-01T00:00:00"),
    end_date: Optional[str] = Query(None, description="End date in ISO format", example="2024-11-14T23:59:59"),
    current_admin: dict = Depends(get_current_admin)
):
    """
    Get error logs with filtering and pagination.
    
    Returns error logs with timestamp, severity, error type, message, and affected endpoint.
    
    Requires admin authentication.
    """
    try:
        system_monitor_service = get_system_monitor_service()
        
        # Parse dates if provided
        start_datetime = None
        end_datetime = None
        
        if start_date:
            try:
                start_datetime = datetime.fromisoformat(start_date)
            except ValueError:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail={
                        "error": "ValidationError",
                        "message": "Invalid start_date format. Use ISO format (YYYY-MM-DDTHH:MM:SS)",
                        "details": None
                    }
                )
        
        if end_date:
            try:
                end_datetime = datetime.fromisoformat(end_date)
            except ValueError:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail={
                        "error": "ValidationError",
                        "message": "Invalid end_date format. Use ISO format (YYYY-MM-DDTHH:MM:SS)",
                        "details": None
                    }
                )
        
        # Validate severity if provided
        if severity and severity.upper() not in ["INFO", "WARNING", "ERROR", "CRITICAL"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "error": "ValidationError",
                    "message": "Invalid severity. Must be one of: INFO, WARNING, ERROR, CRITICAL",
                    "details": None
                }
            )
        
        # Get error logs
        result = system_monitor_service.get_error_logs(
            severity=severity,
            start_date=start_datetime,
            end_date=end_datetime,
            page=page,
            page_size=page_size
        )
        
        logger.info(
            f"Admin {current_admin['username']} retrieved error logs "
            f"(page {page}, severity: {severity})"
        )
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving error logs: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": "InternalServerError",
                "message": "Failed to retrieve error logs",
                "details": None
            }
        )



# Analytics Endpoints

# Global analytics service instance
_analytics_service: Optional['AnalyticsService'] = None


def get_analytics_service() -> 'AnalyticsService':
    """
    Get or create AnalyticsService instance.
    
    Returns:
        AnalyticsService: The analytics service instance
    """
    global _analytics_service
    if _analytics_service is None:
        from services.analytics_service import AnalyticsService
        
        settings = get_settings()
        
        _analytics_service = AnalyticsService(
            connection_string=settings.mongodb_connection_string,
            database_name=settings.mongodb_database_name
        )
    return _analytics_service


@router.get(
    "/analytics/users",
    response_model=UserEngagementMetrics,
    summary="Get user engagement analytics",
    description="""
    Retrieve user engagement metrics for a specified time period.
    
    **Metrics Included:**
    - Total registered users
    - Active users in the period
    - Average queries per active user
    - Daily active user time series
    - Top 10 most active users
    - User retention rate percentage
    
    **Time Range:** 1 to 365 days (default 30 days)
    
    **Authentication:** Requires valid admin JWT token in Authorization header.
    
    **Use Cases:**
    - Monitor user engagement trends
    - Identify power users
    - Track user retention
    - Measure platform adoption
    - Plan user growth strategies
    """,
    responses={
        200: {
            "description": "Successfully retrieved user engagement metrics",
            "content": {
                "application/json": {
                    "example": {
                        "total_users": 500,
                        "active_users_30d": 125,
                        "avg_queries_per_user": 15.5,
                        "daily_active_users": [
                            {
                                "date": "2024-11-14",
                                "count": 25
                            }
                        ],
                        "top_users": [
                            {
                                "username": "john_doe",
                                "query_count": 150,
                                "last_activity": "2024-11-14T15:30:00"
                            }
                        ],
                        "retention_rate_percent": 68.5
                    }
                }
            }
        }
    }
)
async def get_user_analytics(
    days: int = Query(30, ge=1, le=365, description="Number of days to analyze (1-365, default 30)", example=30),
    current_admin: dict = Depends(get_current_admin)
):
    """
    Get user engagement analytics for the specified time period.
    
    Returns total users, active users, average queries per user,
    daily active user trends, top users, and retention rate.
    
    Requires admin authentication.
    """
    try:
        analytics_service = get_analytics_service()
        
        metrics = analytics_service.get_user_engagement_metrics(days=days)
        
        logger.info(
            f"Admin {current_admin['username']} retrieved user engagement metrics "
            f"(last {days} days)"
        )
        
        return metrics
        
    except Exception as e:
        logger.error(f"Error retrieving user engagement metrics: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": "InternalServerError",
                "message": "Failed to retrieve user engagement metrics",
                "details": None
            }
        )


@router.get(
    "/analytics/sessions",
    response_model=SessionAnalytics,
    summary="Get session analytics",
    description="""
    Retrieve chat session analytics for a specified time period.
    
    **Metrics Included:**
    - Total sessions count
    - Average session duration (minutes)
    - Average messages per session
    - Session distribution by message count (1-5, 6-10, 11-20, 21+)
    - Top 10 query topics by keyword frequency
    - Daily session creation trend
    
    **Time Range:** 1 to 365 days (default 30 days)
    
    **Authentication:** Requires valid admin JWT token in Authorization header.
    
    **Use Cases:**
    - Understand conversation patterns
    - Identify popular topics
    - Measure session quality
    - Track engagement depth
    - Optimize chatbot responses
    """,
    responses={
        200: {
            "description": "Successfully retrieved session analytics",
            "content": {
                "application/json": {
                    "example": {
                        "total_sessions": 250,
                        "avg_session_duration_minutes": 8.5,
                        "avg_messages_per_session": 6.2,
                        "session_distribution": {
                            "1-5": 45,
                            "6-10": 30,
                            "11-20": 20,
                            "21+": 5
                        },
                        "top_query_topics": [
                            {
                                "topic": "revenue",
                                "count": 85
                            },
                            {
                                "topic": "profit",
                                "count": 72
                            }
                        ],
                        "session_trend": [
                            {
                                "date": "2024-11-14",
                                "count": 12
                            }
                        ]
                    }
                }
            }
        }
    }
)
async def get_session_analytics(
    days: int = Query(30, ge=1, le=365, description="Number of days to analyze (1-365, default 30)", example=30),
    current_admin: dict = Depends(get_current_admin)
):
    """
    Get session analytics for the specified time period.
    
    Returns total sessions, average duration, average messages per session,
    session distribution by message count, top query topics, and session trends.
    
    Requires admin authentication.
    """
    try:
        analytics_service = get_analytics_service()
        
        analytics = analytics_service.get_session_analytics(days=days)
        
        logger.info(
            f"Admin {current_admin['username']} retrieved session analytics "
            f"(last {days} days)"
        )
        
        return analytics
        
    except Exception as e:
        logger.error(f"Error retrieving session analytics: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": "InternalServerError",
                "message": "Failed to retrieve session analytics",
                "details": None
            }
        )


@router.get(
    "/analytics/documents",
    response_model=DocumentUsageAnalytics,
    summary="Get document usage analytics",
    description="""
    Retrieve document usage analytics and query patterns.
    
    **Metrics Included:**
    - Total document queries
    - Unique documents queried
    - Average queries per document
    - Most queried documents with query counts
    
    **Authentication:** Requires valid admin JWT token in Authorization header.
    
    **Use Cases:**
    - Identify most valuable documents
    - Understand document usage patterns
    - Optimize document collection
    - Track document relevance
    - Plan content strategy
    """,
    responses={
        200: {
            "description": "Successfully retrieved document usage analytics",
            "content": {
                "application/json": {
                    "example": {
                        "total_queries": 1523,
                        "unique_documents_queried": 45,
                        "avg_queries_per_document": 33.8,
                        "most_queried_documents": [
                            {
                                "document_id": "doc_123",
                                "filename": "financial_report_q4.pdf",
                                "query_count": 150,
                                "last_queried": "2024-11-14T15:30:00"
                            }
                        ]
                    }
                }
            }
        }
    }
)
async def get_document_analytics(
    current_admin: dict = Depends(get_current_admin)
):
    """
    Get document usage analytics.
    
    Returns total queries, unique documents queried, average queries per document,
    and most queried documents.
    
    Requires admin authentication.
    """
    try:
        analytics_service = get_analytics_service()
        
        analytics = analytics_service.get_document_usage_analytics()
        
        logger.info(
            f"Admin {current_admin['username']} retrieved document usage analytics"
        )
        
        return analytics
        
    except Exception as e:
        logger.error(f"Error retrieving document usage analytics: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": "InternalServerError",
                "message": "Failed to retrieve document usage analytics",
                "details": None
            }
        )



# Configuration Management Endpoints

# Global config manager service instance
_config_manager: Optional['ConfigManager'] = None


def get_config_manager() -> 'ConfigManager':
    """
    Get or create ConfigManager instance.
    
    Returns:
        ConfigManager: The config manager service instance
    """
    global _config_manager
    if _config_manager is None:
        from services.config_manager import ConfigManager
        from services.activity_logger import ActivityLogger
        
        settings = get_settings()
        
        # Initialize activity logger
        activity_logger = ActivityLogger(
            connection_string=settings.mongodb_connection_string,
            database_name=settings.mongodb_database_name
        )
        
        _config_manager = ConfigManager(
            connection_string=settings.mongodb_connection_string,
            database_name=settings.mongodb_database_name,
            activity_logger=activity_logger
        )
    return _config_manager


@router.get(
    "/config",
    response_model=ConfigSettingsListResponse,
    summary="Get all configuration settings",
    description="""
    Retrieve all system configuration settings.
    
    **Setting Information:**
    - Setting name and current value
    - Default value and data type
    - Description and category
    - Constraints (min/max for numeric types)
    - Last update timestamp and admin
    
    **Categories:**
    - rag: RAG engine settings (chunk size, overlap, top_k)
    - document: Document processing settings (max file size)
    - llm: LLM API settings (temperature, max tokens)
    - api: API settings (rate limits, timeouts)
    
    **Authentication:** Requires valid admin JWT token in Authorization header.
    
    **Use Cases:**
    - Review current system configuration
    - Compare with default values
    - Plan configuration changes
    - Document system settings
    """,
    responses={
        200: {
            "description": "Successfully retrieved configuration settings",
            "content": {
                "application/json": {
                    "example": {
                        "settings": [
                            {
                                "setting_name": "chunk_size",
                                "value": 800,
                                "default_value": 800,
                                "data_type": "int",
                                "description": "Size of text chunks in characters",
                                "category": "rag",
                                "min_value": 100,
                                "max_value": 2000,
                                "updated_at": "2024-11-14T10:30:00",
                                "updated_by": "admin_user"
                            }
                        ],
                        "total": 15
                    }
                }
            }
        }
    }
)
async def get_all_config_settings(
    current_admin: dict = Depends(get_current_admin)
):
    """
    Get all configuration settings.
    
    Returns all system configuration settings including current values,
    default values, data types, and constraints.
    
    Requires admin authentication.
    """
    try:
        config_manager = get_config_manager()
        
        result = config_manager.get_all_settings()
        
        logger.info(f"Admin {current_admin['username']} retrieved all configuration settings")
        
        return result
        
    except Exception as e:
        logger.error(f"Error retrieving configuration settings: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": "InternalServerError",
                "message": "Failed to retrieve configuration settings",
                "details": None
            }
        )


@router.get(
    "/config/{setting_name}",
    response_model=ConfigSetting,
    summary="Get a specific configuration setting",
    description="""
    Retrieve detailed information for a specific configuration setting.
    
    **Setting Information:**
    - Current value and default value
    - Data type and constraints
    - Description and category
    - Last update information
    
    **Authentication:** Requires valid admin JWT token in Authorization header.
    
    **Use Cases:**
    - Check current value of a setting
    - Review constraints before updating
    - Verify recent changes
    - Understand setting purpose
    """,
    responses={
        200: {
            "description": "Successfully retrieved configuration setting",
            "content": {
                "application/json": {
                    "example": {
                        "setting_name": "chunk_size",
                        "value": 800,
                        "default_value": 800,
                        "data_type": "int",
                        "description": "Size of text chunks in characters",
                        "category": "rag",
                        "min_value": 100,
                        "max_value": 2000,
                        "updated_at": "2024-11-14T10:30:00",
                        "updated_by": "admin_user"
                    }
                }
            }
        },
        404: {
            "model": ErrorResponse,
            "description": "Setting not found",
            "content": {
                "application/json": {
                    "example": {
                        "error": "ResourceNotFoundError",
                        "message": "Configuration setting 'invalid_setting' not found",
                        "details": None
                    }
                }
            }
        }
    }
)
async def get_config_setting(
    setting_name: str,
    current_admin: dict = Depends(get_current_admin)
):
    """
    Get a specific configuration setting.
    
    Returns detailed information about a single configuration setting
    including current value, default value, constraints, and metadata.
    
    Requires admin authentication.
    """
    try:
        config_manager = get_config_manager()
        
        setting = config_manager.get_setting(setting_name)
        
        if setting is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={
                    "error": "ResourceNotFoundError",
                    "message": f"Configuration setting '{setting_name}' not found",
                    "details": None
                }
            )
        
        logger.info(
            f"Admin {current_admin['username']} retrieved configuration setting: {setting_name}"
        )
        
        return setting
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving configuration setting: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": "InternalServerError",
                "message": "Failed to retrieve configuration setting",
                "details": None
            }
        )


@router.put(
    "/config/{setting_name}",
    response_model=ConfigUpdateResponse,
    summary="Update a configuration setting",
    description="""
    Update a configuration setting with validation.
    
    **Validation:**
    - Data type checking (int, float, str, bool)
    - Range validation for numeric types (min/max)
    - Value format validation
    
    **Audit Trail:** All changes are logged with admin ID, old value, new value, and timestamp.
    
    **Authentication:** Requires valid admin JWT token in Authorization header.
    
    **Use Cases:**
    - Optimize RAG performance (chunk size, top_k)
    - Adjust document processing limits
    - Configure LLM parameters
    - Update API rate limits
    
    **Warning:** Configuration changes may affect system behavior. Test in non-production first.
    """,
    responses={
        200: {
            "description": "Successfully updated configuration setting",
            "content": {
                "application/json": {
                    "example": {
                        "message": "Configuration setting updated successfully",
                        "setting": {
                            "setting_name": "chunk_size",
                            "value": 1000,
                            "default_value": 800,
                            "data_type": "int",
                            "description": "Size of text chunks in characters",
                            "category": "rag",
                            "min_value": 100,
                            "max_value": 2000,
                            "updated_at": "2024-11-14T10:35:00",
                            "updated_by": "admin_user"
                        }
                    }
                }
            }
        },
        400: {
            "model": ErrorResponse,
            "description": "Invalid value or validation failed",
            "content": {
                "application/json": {
                    "examples": {
                        "type_error": {
                            "summary": "Invalid data type",
                            "value": {
                                "error": "ValidationError",
                                "message": "Invalid value for setting 'chunk_size'",
                                "details": {
                                    "validation_error": "Value must be an integer"
                                }
                            }
                        },
                        "range_error": {
                            "summary": "Value out of range",
                            "value": {
                                "error": "ValidationError",
                                "message": "Invalid value for setting 'chunk_size'",
                                "details": {
                                    "validation_error": "Value must be between 100 and 2000"
                                }
                            }
                        }
                    }
                }
            }
        },
        404: {
            "model": ErrorResponse,
            "description": "Setting not found",
            "content": {
                "application/json": {
                    "example": {
                        "error": "ResourceNotFoundError",
                        "message": "Configuration setting 'invalid_setting' not found",
                        "details": None
                    }
                }
            }
        }
    }
)
async def update_config_setting(
    setting_name: str,
    update_request: 'ConfigUpdateRequest',
    current_admin: dict = Depends(get_current_admin)
):
    """
    Update a configuration setting.
    
    Updates a configuration setting with validation against data type
    and range constraints. All changes are logged for audit trail.
    
    Requires admin authentication.
    """
    try:
        config_manager = get_config_manager()
        
        # Check if setting exists
        existing_setting = config_manager.get_setting(setting_name)
        if existing_setting is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={
                    "error": "ResourceNotFoundError",
                    "message": f"Configuration setting '{setting_name}' not found",
                    "details": None
                }
            )
        
        # Validate the new value
        is_valid, error_message = config_manager.validate_setting_value(
            setting_name,
            update_request.value
        )
        
        if not is_valid:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "error": "ValidationError",
                    "message": f"Invalid value for setting '{setting_name}'",
                    "details": {"validation_error": error_message}
                }
            )
        
        # Update the setting
        success = config_manager.update_setting(
            setting_name=setting_name,
            value=update_request.value,
            admin_id=current_admin['user_id'],
            admin_username=current_admin['username']
        )
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail={
                    "error": "InternalServerError",
                    "message": "Failed to update configuration setting",
                    "details": None
                }
            )
        
        # Get updated setting
        updated_setting = config_manager.get_setting(setting_name)
        
        logger.info(
            f"Admin {current_admin['username']} updated configuration setting "
            f"{setting_name} to {update_request.value}"
        )
        
        return {
            "message": "Configuration setting updated successfully",
            "setting": updated_setting
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating configuration setting: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": "InternalServerError",
                "message": "Failed to update configuration setting",
                "details": None
            }
        )
