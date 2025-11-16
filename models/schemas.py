"""
Pydantic models for API requests and responses.
"""
from typing import Optional, List, Dict, Any
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


# Admin System Monitoring Schemas

class SystemHealthResponse(BaseModel):
    """Response model for system health status."""
    status: str = Field(..., description="Overall system status (healthy/degraded/unhealthy)")
    vector_db_status: str = Field(..., description="ChromaDB connection status")
    llm_api_status: str = Field(..., description="LLM API availability status")
    session_db_status: str = Field(..., description="SQLite session database status")
    mongodb_status: str = Field(..., description="MongoDB connection status")
    timestamp: str = Field(..., description="Timestamp of health check")
    error_details: Optional[Dict] = Field(None, description="Error details if any component is unhealthy")

    class Config:
        json_schema_extra = {
            "example": {
                "status": "healthy",
                "vector_db_status": "healthy",
                "llm_api_status": "healthy",
                "session_db_status": "healthy",
                "mongodb_status": "healthy",
                "timestamp": "2024-11-14T10:30:00Z",
                "error_details": None
            }
        }


class SystemMetricsResponse(BaseModel):
    """Response model for system performance metrics."""
    active_sessions: int = Field(..., ge=0, description="Number of active sessions")
    total_requests_24h: int = Field(..., ge=0, description="Total API requests in last 24 hours")
    avg_response_time_ms: float = Field(..., ge=0, description="Average response time in milliseconds")
    memory_usage_percent: float = Field(..., ge=0, le=100, description="Memory usage percentage")
    disk_usage_percent: float = Field(..., ge=0, le=100, description="Disk usage percentage")
    uptime_hours: float = Field(..., ge=0, description="Application uptime in hours")

    class Config:
        json_schema_extra = {
            "example": {
                "active_sessions": 42,
                "total_requests_24h": 1523,
                "avg_response_time_ms": 245.67,
                "memory_usage_percent": 45.2,
                "disk_usage_percent": 62.8,
                "uptime_hours": 72.5
            }
        }


class StorageMetricsResponse(BaseModel):
    """Response model for storage usage metrics."""
    vector_db_size_mb: float = Field(..., ge=0, description="Vector database size in megabytes")
    session_db_size_mb: float = Field(..., ge=0, description="Session database size in megabytes")
    mongodb_size_mb: float = Field(..., ge=0, description="MongoDB size in megabytes")
    total_document_size_mb: float = Field(..., ge=0, description="Total uploaded document size in megabytes")
    available_disk_gb: float = Field(..., ge=0, description="Available disk space in gigabytes")
    disk_usage_percent: float = Field(..., ge=0, le=100, description="Disk usage percentage")
    growth_rate_7d_percent: float = Field(..., description="Storage growth rate over last 7 days")

    class Config:
        json_schema_extra = {
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


class APIEndpointMetric(BaseModel):
    """Model for API endpoint metrics."""
    endpoint: str = Field(..., description="API endpoint path")
    total_requests: int = Field(..., ge=0, description="Total number of requests")
    success_count: int = Field(..., ge=0, description="Number of successful requests (2xx)")
    error_count: int = Field(..., ge=0, description="Number of failed requests (4xx, 5xx)")
    avg_response_time_ms: float = Field(..., ge=0, description="Average response time in milliseconds")

    class Config:
        json_schema_extra = {
            "example": {
                "endpoint": "/api/v1/chat",
                "total_requests": 523,
                "success_count": 498,
                "error_count": 25,
                "avg_response_time_ms": 245.67
            }
        }


class SlowestRequest(BaseModel):
    """Model for slowest API requests."""
    endpoint: str = Field(..., description="API endpoint path")
    response_time_ms: float = Field(..., ge=0, description="Response time in milliseconds")
    timestamp: str = Field(..., description="Request timestamp")
    status_code: int = Field(..., description="HTTP status code")

    class Config:
        json_schema_extra = {
            "example": {
                "endpoint": "/api/v1/chat",
                "response_time_ms": 1523.45,
                "timestamp": "2024-11-14T10:30:00Z",
                "status_code": 200
            }
        }


class HourlyRequestData(BaseModel):
    """Model for hourly request rate data."""
    hour: str = Field(..., description="Hour timestamp")
    request_count: int = Field(..., ge=0, description="Number of requests in this hour")

    class Config:
        json_schema_extra = {
            "example": {
                "hour": "2024-11-14T10:00:00Z",
                "request_count": 125
            }
        }


class APIUsageMetrics(BaseModel):
    """Response model for API usage metrics."""
    total_requests: int = Field(..., ge=0, description="Total requests in time period")
    success_count: int = Field(..., ge=0, description="Number of successful requests (2xx)")
    error_count: int = Field(..., ge=0, description="Number of failed requests (4xx, 5xx)")
    endpoints: List[APIEndpointMetric] = Field(
        default_factory=list,
        description="Metrics by endpoint"
    )
    slowest_requests: List[SlowestRequest] = Field(
        default_factory=list,
        description="Top 5 slowest requests"
    )
    hourly_rate: List[HourlyRequestData] = Field(
        default_factory=list,
        description="Request rate per hour"
    )

    class Config:
        json_schema_extra = {
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


class ErrorLogEntry(BaseModel):
    """Model for error log entry."""
    log_id: str = Field(..., description="Unique log entry identifier")
    timestamp: str = Field(..., description="Error timestamp")
    severity: str = Field(..., description="Error severity (INFO/WARNING/ERROR/CRITICAL)")
    error_type: str = Field(..., description="Type of error")
    error_message: str = Field(..., description="Error message")
    endpoint: Optional[str] = Field(None, description="Affected endpoint")
    stack_trace: Optional[str] = Field(None, description="Stack trace if available")
    user_id: Optional[str] = Field(None, description="User ID if applicable")

    class Config:
        json_schema_extra = {
            "example": {
                "log_id": "507f1f77bcf86cd799439013",
                "timestamp": "2024-11-14T10:30:00Z",
                "severity": "ERROR",
                "error_type": "DatabaseConnectionError",
                "error_message": "Failed to connect to MongoDB",
                "endpoint": "/api/v1/chat",
                "stack_trace": "Traceback (most recent call last)...",
                "user_id": "507f1f77bcf86cd799439011"
            }
        }


class ErrorLogsResponse(BaseModel):
    """Response model for error logs with pagination."""
    logs: List[ErrorLogEntry] = Field(..., description="List of error log entries")
    total: int = Field(..., ge=0, description="Total number of matching logs")
    page: int = Field(..., ge=1, description="Current page number")
    page_size: int = Field(..., ge=10, le=100, description="Records per page")
    total_pages: int = Field(..., ge=0, description="Total number of pages")

    class Config:
        json_schema_extra = {
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


# Admin Analytics Schemas

class DailyActiveUserData(BaseModel):
    """Model for daily active user data point."""
    date: str = Field(..., description="Date in YYYY-MM-DD format")
    count: int = Field(..., ge=0, description="Number of active users on this date")

    class Config:
        json_schema_extra = {
            "example": {
                "date": "2024-11-14",
                "count": 25
            }
        }


class TopUser(BaseModel):
    """Model for top active user."""
    username: str = Field(..., description="Username")
    query_count: int = Field(..., ge=0, description="Number of queries made")
    last_activity: str = Field(..., description="Last activity timestamp")

    class Config:
        json_schema_extra = {
            "example": {
                "username": "john_doe",
                "query_count": 150,
                "last_activity": "2024-11-14T15:30:00"
            }
        }


class UserEngagementMetrics(BaseModel):
    """Response model for user engagement analytics."""
    total_users: int = Field(..., ge=0, description="Total registered users")
    active_users_30d: int = Field(..., ge=0, description="Users active in last 30 days")
    avg_queries_per_user: float = Field(..., ge=0, description="Average queries per active user")
    daily_active_users: List[DailyActiveUserData] = Field(
        default_factory=list,
        description="Daily active user counts for the period"
    )
    top_users: List[TopUser] = Field(
        default_factory=list,
        description="Top 10 most active users"
    )
    retention_rate_percent: float = Field(
        ...,
        ge=0,
        le=100,
        description="User retention rate percentage"
    )

    class Config:
        json_schema_extra = {
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


class SessionDistribution(BaseModel):
    """Model for session distribution by message count."""
    range_1_5: int = Field(..., ge=0, description="Sessions with 1-5 messages", alias="1-5")
    range_6_10: int = Field(..., ge=0, description="Sessions with 6-10 messages", alias="6-10")
    range_11_20: int = Field(..., ge=0, description="Sessions with 11-20 messages", alias="11-20")
    range_21_plus: int = Field(..., ge=0, description="Sessions with 21+ messages", alias="21+")

    class Config:
        populate_by_name = True
        json_schema_extra = {
            "example": {
                "1-5": 45,
                "6-10": 30,
                "11-20": 20,
                "21+": 5
            }
        }


class QueryTopic(BaseModel):
    """Model for query topic analysis."""
    topic: str = Field(..., description="Topic keyword")
    count: int = Field(..., ge=0, description="Frequency count")

    class Config:
        json_schema_extra = {
            "example": {
                "topic": "revenue",
                "count": 85
            }
        }


class SessionTrendData(BaseModel):
    """Model for session trend data point."""
    date: str = Field(..., description="Date in YYYY-MM-DD format")
    count: int = Field(..., ge=0, description="Number of sessions created on this date")

    class Config:
        json_schema_extra = {
            "example": {
                "date": "2024-11-14",
                "count": 12
            }
        }


class SessionAnalytics(BaseModel):
    """Response model for session analytics."""
    total_sessions: int = Field(..., ge=0, description="Total number of sessions")
    avg_session_duration_minutes: float = Field(
        ...,
        ge=0,
        description="Average session duration in minutes"
    )
    avg_messages_per_session: float = Field(
        ...,
        ge=0,
        description="Average messages per session"
    )
    session_distribution: Dict[str, int] = Field(
        ...,
        description="Distribution of sessions by message count ranges"
    )
    top_query_topics: List[QueryTopic] = Field(
        default_factory=list,
        description="Top 10 most common query topics"
    )
    session_trend: List[SessionTrendData] = Field(
        default_factory=list,
        description="Daily session creation trend"
    )

    class Config:
        json_schema_extra = {
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


class DocumentUsageAnalytics(BaseModel):
    """Response model for document usage analytics."""
    total_queries: int = Field(..., ge=0, description="Total document queries")
    unique_documents_queried: int = Field(..., ge=0, description="Number of unique documents queried")
    avg_queries_per_document: float = Field(..., ge=0, description="Average queries per document")
    most_queried_documents: List[TopDocument] = Field(
        default_factory=list,
        description="Most queried documents"
    )

    class Config:
        json_schema_extra = {
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


# Admin Configuration Management Schemas

class ConfigSetting(BaseModel):
    """Model representing a system configuration setting."""
    setting_name: str = Field(..., description="Unique setting identifier")
    value: Any = Field(..., description="Current value of the setting")
    default_value: Any = Field(..., description="Default value of the setting")
    data_type: str = Field(..., description="Data type (int, float, str, bool)")
    description: str = Field(..., description="Description of the setting")
    category: str = Field(..., description="Category (rag, document, api, llm, etc.)")
    min_value: Optional[float] = Field(None, description="Minimum value constraint (for numeric types)")
    max_value: Optional[float] = Field(None, description="Maximum value constraint (for numeric types)")
    updated_at: Optional[str] = Field(None, description="Last update timestamp (ISO format)")
    updated_by: Optional[str] = Field(None, description="Admin username who last updated")

    class Config:
        json_schema_extra = {
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


class ConfigSettingsListResponse(BaseModel):
    """Response model for listing all configuration settings."""
    settings: List[ConfigSetting] = Field(..., description="List of configuration settings")
    total: int = Field(..., ge=0, description="Total number of settings")

    class Config:
        json_schema_extra = {
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


class ConfigUpdateRequest(BaseModel):
    """Request model for updating a configuration setting."""
    value: Any = Field(..., description="New value for the setting")

    class Config:
        json_schema_extra = {
            "example": {
                "value": 1000
            }
        }


class ConfigUpdateResponse(BaseModel):
    """Response model for configuration update operation."""
    message: str = Field(..., description="Success message")
    setting: ConfigSetting = Field(..., description="Updated setting details")

    class Config:
        json_schema_extra = {
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
