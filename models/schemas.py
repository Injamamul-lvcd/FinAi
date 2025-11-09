"""
Pydantic models for API requests and responses.
"""
from typing import Optional, List
from pydantic import BaseModel, Field
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
