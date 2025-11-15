"""
Admin Panel API Routes

This module provides administrative endpoints for user management, document management,
system monitoring, analytics, and configuration.
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
    DocumentDeleteResponse
)
from utils.admin_auth import get_current_admin
from services.admin_user_service import AdminUserService
from config.settings import get_settings

logger = logging.getLogger(__name__)

# Create router
router = APIRouter(
    prefix="/api/v1/admin",
    tags=["Admin"],
    responses={
        401: {"model": ErrorResponse, "description": "Unauthorized - Invalid or missing token"},
        403: {"model": ErrorResponse, "description": "Forbidden - Admin access required"},
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
    description="Retrieve a paginated list of all users with optional search and sorting"
)
async def list_users(
    page: int = Query(1, ge=1, description="Page number (1-indexed)"),
    page_size: int = Query(50, ge=10, le=100, description="Number of records per page"),
    search: Optional[str] = Query(None, max_length=100, description="Search by username or email"),
    sort_by: str = Query("created_at", description="Field to sort by (created_at, last_login, username)"),
    sort_order: str = Query("desc", description="Sort order (asc or desc)"),
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
    description="Retrieve complete information for a specific user including document and query counts",
    responses={
        404: {"model": ErrorResponse, "description": "User not found"}
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
    description="Enable or disable a user account",
    responses={
        404: {"model": ErrorResponse, "description": "User not found"}
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
    description="Generate a secure temporary password for a user",
    responses={
        404: {"model": ErrorResponse, "description": "User not found"}
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
    description="Retrieve activity logs for a specific user with optional date range filtering",
    responses={
        404: {"model": ErrorResponse, "description": "User not found"}
    }
)
async def get_user_activity(
    user_id: str,
    page: int = Query(1, ge=1, description="Page number (1-indexed)"),
    page_size: int = Query(50, ge=10, le=100, description="Number of records per page"),
    start_date: Optional[str] = Query(None, description="Start date (ISO format)"),
    end_date: Optional[str] = Query(None, description="End date (ISO format)"),
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
    description="Retrieve a paginated list of all documents with optional search and date filtering"
)
async def list_documents(
    page: int = Query(1, ge=1, description="Page number (1-indexed)"),
    page_size: int = Query(50, ge=10, le=100, description="Number of records per page"),
    search: Optional[str] = Query(None, max_length=100, description="Search by filename or username"),
    start_date: Optional[str] = Query(None, description="Start date filter (ISO format)"),
    end_date: Optional[str] = Query(None, description="End date filter (ISO format)"),
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
    description="Delete a document and all its chunks from the vector database",
    responses={
        404: {"model": ErrorResponse, "description": "Document not found"}
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
    description="Retrieve comprehensive document statistics including totals, averages, and trends"
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
