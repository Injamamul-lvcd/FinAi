"""
Pydantic models for API requests and responses.
"""
from typing import Optional, List, Dict
from pydantic import BaseModel, Field, EmailStr
from datetime import datetime


class ChatRequest(BaseModel):
    """Request model for chat query endpoint."""
    query: str = Field(
        ...,
        min_length=1,
        max_length=2000,
        description="User's financial query"
    )
    session_id: Optional[str] = Field(
        None,
        description="Optional session ID for conversation continuity"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "query": "What are the key financial metrics for Q4?",
                "session_id": "550e8400-e29b-41d4-a716-446655440000"
            }
        }


class Source(BaseModel):
    """Model representing a source document used in the response."""
    document_id: str = Field(..., description="Unique identifier of the source document")
    filename: str = Field(..., description="Name of the source document")
    chunk_text: str = Field(..., description="Relevant text chunk from the document")
    relevance_score: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Relevance score of the chunk (0-1)"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "document_id": "doc_123",
                "filename": "financial_report_q4.pdf",
                "chunk_text": "Revenue increased by 15% in Q4...",
                "relevance_score": 0.92
            }
        }


class ChatResponse(BaseModel):
    """Response model for chat query endpoint."""
    response: str = Field(..., description="AI-generated response to the query")
    sources: List[Source] = Field(
        default_factory=list,
        description="List of source documents used to generate the response"
    )
    session_id: str = Field(..., description="Session ID for conversation continuity")

    class Config:
        json_schema_extra = {
            "example": {
                "response": "Based on the Q4 financial report, revenue increased by 15%...",
                "sources": [
                    {
                        "document_id": "doc_123",
                        "filename": "financial_report_q4.pdf",
                        "chunk_text": "Revenue increased by 15% in Q4...",
                        "relevance_score": 0.92
                    }
                ],
                "session_id": "550e8400-e29b-41d4-a716-446655440000"
            }
        }


class DocumentUploadResponse(BaseModel):
    """Response model for document upload endpoint."""
    document_id: str = Field(..., description="Unique identifier assigned to the uploaded document")
    filename: str = Field(..., description="Name of the uploaded file")
    chunks_created: int = Field(
        ...,
        ge=0,
        description="Number of chunks created from the document"
    )
    upload_date: str = Field(..., description="ISO format timestamp of upload")

    class Config:
        json_schema_extra = {
            "example": {
                "document_id": "doc_456",
                "filename": "annual_report_2024.pdf",
                "chunks_created": 42,
                "upload_date": "2024-01-15T10:30:00Z"
            }
        }


class DocumentInfo(BaseModel):
    """Model representing metadata about a stored document."""
    id: str = Field(..., description="Unique identifier of the document")
    filename: str = Field(..., description="Name of the document file")
    upload_date: str = Field(..., description="ISO format timestamp of upload")
    chunks: int = Field(..., ge=0, description="Number of chunks in the document")

    class Config:
        json_schema_extra = {
            "example": {
                "id": "doc_456",
                "filename": "annual_report_2024.pdf",
                "upload_date": "2024-01-15T10:30:00Z",
                "chunks": 42
            }
        }


class DocumentListResponse(BaseModel):
    """Response model for listing all documents."""
    documents: List[DocumentInfo] = Field(
        default_factory=list,
        description="List of all stored documents with metadata"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "documents": [
                    {
                        "id": "doc_456",
                        "filename": "annual_report_2024.pdf",
                        "upload_date": "2024-01-15T10:30:00Z",
                        "chunks": 42
                    },
                    {
                        "id": "doc_789",
                        "filename": "quarterly_earnings.docx",
                        "upload_date": "2024-01-16T14:20:00Z",
                        "chunks": 28
                    }
                ]
            }
        }


class DocumentStats(BaseModel):
    """Response model for document statistics endpoint."""
    total_documents: int = Field(..., ge=0, description="Total number of documents stored")
    total_chunks: int = Field(..., ge=0, description="Total number of chunks across all documents")

    class Config:
        json_schema_extra = {
            "example": {
                "total_documents": 15,
                "total_chunks": 523
            }
        }


class ErrorResponse(BaseModel):
    """Response model for error responses."""
    error: str = Field(..., description="Error type or category")
    message: str = Field(..., description="Human-readable error message")
    details: Optional[dict] = Field(
        None,
        description="Additional error details or context"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "error": "ValidationError",
                "message": "Invalid file type. Only PDF, DOCX, and TXT files are supported.",
                "details": {
                    "file_type": "xlsx",
                    "allowed_types": ["pdf", "docx", "txt"]
                }
            }
        }


# Authentication Schemas

class UserRegister(BaseModel):
    """Request model for user registration."""
    username: str = Field(
        ...,
        min_length=3,
        max_length=50,
        description="Unique username"
    )
    email: EmailStr = Field(..., description="User email address")
    password: str = Field(
        ...,
        min_length=8,
        max_length=100,
        description="User password (min 8 characters)"
    )
    full_name: Optional[str] = Field(
        None,
        max_length=100,
        description="User's full name"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "username": "john_doe",
                "email": "john@example.com",
                "password": "SecurePass123!",
                "full_name": "John Doe"
            }
        }


class UserLogin(BaseModel):
    """Request model for user login."""
    username: str = Field(..., description="Username")
    password: str = Field(..., description="Password")

    class Config:
        json_schema_extra = {
            "example": {
                "username": "john_doe",
                "password": "SecurePass123!"
            }
        }


class Token(BaseModel):
    """Response model for authentication token."""
    access_token: str = Field(..., description="JWT access token")
    token_type: str = Field(default="bearer", description="Token type")
    user: "UserResponse" = Field(..., description="User information")

    class Config:
        json_schema_extra = {
            "example": {
                "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                "token_type": "bearer",
                "user": {
                    "user_id": "507f1f77bcf86cd799439011",
                    "username": "john_doe",
                    "email": "john@example.com",
                    "full_name": "John Doe",
                    "is_active": True
                }
            }
        }


class UserResponse(BaseModel):
    """Response model for user information."""
    user_id: str = Field(..., description="Unique user identifier")
    username: str = Field(..., description="Username")
    email: str = Field(..., description="Email address")
    full_name: Optional[str] = Field(None, description="Full name")
    is_active: bool = Field(default=True, description="Account active status")
    is_admin: bool = Field(default=False, description="Admin role status")
    password_reset_required: bool = Field(default=False, description="Password reset required flag")
    created_at: Optional[str] = Field(None, description="Account creation timestamp")

    class Config:
        json_schema_extra = {
            "example": {
                "user_id": "507f1f77bcf86cd799439011",
                "username": "john_doe",
                "email": "john@example.com",
                "full_name": "John Doe",
                "is_active": True,
                "is_admin": False,
                "password_reset_required": False,
                "created_at": "2024-11-09T10:30:00"
            }
        }


class PasswordChange(BaseModel):
    """Request model for password change."""
    old_password: str = Field(..., description="Current password")
    new_password: str = Field(
        ...,
        min_length=8,
        max_length=100,
        description="New password (min 8 characters)"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "old_password": "OldPass123!",
                "new_password": "NewSecurePass456!"
            }
        }


class ForgotPasswordRequest(BaseModel):
    """Request model for forgot password."""
    email: EmailStr = Field(..., description="User's email address")

    class Config:
        json_schema_extra = {
            "example": {
                "email": "john@example.com"
            }
        }


class ResetPasswordRequest(BaseModel):
    """Request model for password reset."""
    token: str = Field(..., description="Password reset token")
    new_password: str = Field(
        ...,
        min_length=8,
        max_length=100,
        description="New password (min 8 characters)"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                "new_password": "NewSecurePass456!"
            }
        }


class ForgotPasswordResponse(BaseModel):
    """Response model for forgot password."""
    message: str = Field(..., description="Success message")
    reset_token: Optional[str] = Field(None, description="Reset token (for development/testing only)")

    class Config:
        json_schema_extra = {
            "example": {
                "message": "If the email exists, a password reset link has been sent.",
                "reset_token": None
            }
        }


# Admin Authentication Schemas

class AdminLoginResponse(BaseModel):
    """Response model for admin login."""
    access_token: str = Field(..., description="JWT access token with 8-hour expiration")
    token_type: str = Field(default="bearer", description="Token type")
    admin_username: str = Field(..., description="Admin username")
    expires_at: str = Field(..., description="Token expiration timestamp")

    class Config:
        json_schema_extra = {
            "example": {
                "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                "token_type": "bearer",
                "admin_username": "admin_user",
                "expires_at": "2024-11-14T18:30:00Z"
            }
        }



# Admin User Management Schemas

class UserDetail(BaseModel):
    """Model representing detailed user information for admin panel."""
    user_id: str = Field(..., description="Unique user identifier")
    username: str = Field(..., description="Username")
    email: str = Field(..., description="Email address")
    full_name: Optional[str] = Field(None, description="Full name")
    is_active: bool = Field(..., description="Account active status")
    is_admin: bool = Field(..., description="Admin role status")
    password_reset_required: bool = Field(default=False, description="Password reset required flag")
    created_at: Optional[str] = Field(None, description="Account creation timestamp")
    updated_at: Optional[str] = Field(None, description="Last update timestamp")
    last_login: Optional[str] = Field(None, description="Last login timestamp")
    document_count: int = Field(default=0, ge=0, description="Number of documents uploaded by user")
    query_count: int = Field(default=0, ge=0, description="Number of queries made by user")

    class Config:
        json_schema_extra = {
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


class UserListResponse(BaseModel):
    """Response model for listing users with pagination."""
    users: List[UserDetail] = Field(..., description="List of user records")
    total: int = Field(..., ge=0, description="Total number of matching users")
    page: int = Field(..., ge=1, description="Current page number")
    page_size: int = Field(..., ge=10, le=100, description="Records per page")
    total_pages: int = Field(..., ge=0, description="Total number of pages")

    class Config:
        json_schema_extra = {
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


class UserStatusUpdate(BaseModel):
    """Request model for updating user account status."""
    is_active: bool = Field(..., description="New active status (True to enable, False to disable)")
    reason: Optional[str] = Field(
        None,
        max_length=500,
        description="Optional reason for status change"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "is_active": False,
                "reason": "Account suspended due to policy violation"
            }
        }


class PasswordResetResponse(BaseModel):
    """Response model for password reset operation."""
    temporary_password: str = Field(..., description="Temporary password for user")
    expires_at: str = Field(..., description="Password expiration timestamp (user must change on next login)")
    message: str = Field(..., description="Success message")

    class Config:
        json_schema_extra = {
            "example": {
                "temporary_password": "Xy9$mK2pL#4q",
                "expires_at": "User must change password on next login",
                "message": "Password reset successfully. Provide the temporary password to the user."
            }
        }


class ActivityLogEntry(BaseModel):
    """Model representing an activity log entry."""
    log_id: str = Field(..., description="Unique log entry identifier")
    admin_username: str = Field(..., description="Username of admin who performed action")
    action_type: str = Field(..., description="Type of action performed")
    resource_type: str = Field(..., description="Type of resource affected")
    resource_id: str = Field(..., description="ID of affected resource")
    details: Dict = Field(default_factory=dict, description="Additional action details")
    ip_address: Optional[str] = Field(None, description="IP address of admin")
    timestamp: str = Field(..., description="Timestamp of action")
    result: str = Field(..., description="Result of action (success or failure)")

    class Config:
        json_schema_extra = {
            "example": {
                "log_id": "507f1f77bcf86cd799439012",
                "admin_username": "admin_user",
                "action_type": "user_disabled",
                "resource_type": "user",
                "resource_id": "507f1f77bcf86cd799439011",
                "details": {
                    "username": "john_doe",
                    "reason": "Policy violation",
                    "previous_status": True,
                    "new_status": False
                },
                "ip_address": "192.168.1.100",
                "timestamp": "2024-11-14T10:30:00",
                "result": "success"
            }
        }


class ActivityLogResponse(BaseModel):
    """Response model for activity logs with pagination."""
    logs: List[ActivityLogEntry] = Field(..., description="List of activity log entries")
    total: int = Field(..., ge=0, description="Total number of matching logs")
    page: int = Field(..., ge=1, description="Current page number")
    page_size: int = Field(..., ge=10, le=100, description="Records per page")
    total_pages: int = Field(..., ge=0, description="Total number of pages")

    class Config:
        json_schema_extra = {
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


# Admin Document Management Schemas

class AdminDocumentInfo(BaseModel):
    """Model representing document information for admin panel."""
    document_id: str = Field(..., description="Unique document identifier")
    filename: str = Field(..., description="Name of the document file")
    uploader_username: str = Field(..., description="Username of user who uploaded document")
    uploader_user_id: str = Field(..., description="User ID of uploader")
    upload_date: str = Field(..., description="ISO format timestamp of upload")
    file_size_mb: float = Field(..., ge=0, description="File size in megabytes")
    chunk_count: int = Field(..., ge=0, description="Number of chunks in document")
    query_count: int = Field(default=0, ge=0, description="Number of times document has been queried")

    class Config:
        json_schema_extra = {
            "example": {
                "document_id": "doc_123",
                "filename": "financial_report_q4.pdf",
                "uploader_username": "john_doe",
                "uploader_user_id": "507f1f77bcf86cd799439011",
                "upload_date": "2024-11-14T10:30:00",
                "file_size_mb": 2.45,
                "chunk_count": 42,
                "query_count": 15
            }
        }


class AdminDocumentListResponse(BaseModel):
    """Response model for listing documents with pagination."""
    documents: List[AdminDocumentInfo] = Field(..., description="List of document records")
    total: int = Field(..., ge=0, description="Total number of matching documents")
    page: int = Field(..., ge=1, description="Current page number")
    page_size: int = Field(..., ge=10, le=100, description="Records per page")
    total_pages: int = Field(..., ge=0, description="Total number of pages")

    class Config:
        json_schema_extra = {
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


class DocumentTypeStats(BaseModel):
    """Model for document statistics by file type."""
    file_type: str = Field(..., description="File type extension")
    count: int = Field(..., ge=0, description="Number of documents of this type")
    percentage: float = Field(..., ge=0, le=100, description="Percentage of total documents")

    class Config:
        json_schema_extra = {
            "example": {
                "file_type": "pdf",
                "count": 45,
                "percentage": 75.0
            }
        }


class TopDocument(BaseModel):
    """Model for top queried documents."""
    document_id: str = Field(..., description="Document identifier")
    filename: str = Field(..., description="Document filename")
    query_count: int = Field(..., ge=0, description="Number of queries")
    last_queried: Optional[str] = Field(None, description="Last query timestamp")

    class Config:
        json_schema_extra = {
            "example": {
                "document_id": "doc_123",
                "filename": "financial_report_q4.pdf",
                "query_count": 150,
                "last_queried": "2024-11-14T15:30:00"
            }
        }


class UploadTrendData(BaseModel):
    """Model for upload trend data point."""
    date: str = Field(..., description="Date in YYYY-MM-DD format")
    count: int = Field(..., ge=0, description="Number of documents uploaded on this date")

    class Config:
        json_schema_extra = {
            "example": {
                "date": "2024-11-14",
                "count": 5
            }
        }


class DocumentStatsResponse(BaseModel):
    """Response model for document statistics."""
    total_documents: int = Field(..., ge=0, description="Total number of documents")
    total_chunks: int = Field(..., ge=0, description="Total number of chunks across all documents")
    total_size_mb: float = Field(..., ge=0, description="Total storage size in megabytes")
    avg_chunks_per_doc: float = Field(..., ge=0, description="Average chunks per document")
    documents_by_type: List[DocumentTypeStats] = Field(
        default_factory=list,
        description="Document count by file type"
    )
    upload_trend: List[UploadTrendData] = Field(
        default_factory=list,
        description="Upload trend for last 30 days"
    )
    top_documents: List[TopDocument] = Field(
        default_factory=list,
        description="Top 10 most queried documents"
    )

    class Config:
        json_schema_extra = {
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


class DocumentDeleteResponse(BaseModel):
    """Response model for document deletion."""
    message: str = Field(..., description="Success message")
    document_id: str = Field(..., description="ID of deleted document")
    filename: str = Field(..., description="Name of deleted document")
    chunks_deleted: int = Field(..., ge=0, description="Number of chunks deleted")

    class Config:
        json_schema_extra = {
            "example": {
                "message": "Document deleted successfully",
                "document_id": "doc_123",
                "filename": "financial_report_q4.pdf",
                "chunks_deleted": 42
            }
        }
