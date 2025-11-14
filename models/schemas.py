"""
Pydantic models for API requests and responses.
"""
from typing import Optional, List
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
    created_at: Optional[str] = Field(None, description="Account creation timestamp")

    class Config:
        json_schema_extra = {
            "example": {
                "user_id": "507f1f77bcf86cd799439011",
                "username": "john_doe",
                "email": "john@example.com",
                "full_name": "John Doe",
                "is_active": True,
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
