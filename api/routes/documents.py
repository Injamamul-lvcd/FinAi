"""
Document management endpoints for the Financial Chatbot RAG API.

This module provides endpoints for uploading, listing, and managing documents
in the vector database.
"""

import logging
import os
import uuid
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, UploadFile, File, HTTPException, status
from fastapi.responses import JSONResponse

from models.schemas import (
    DocumentUploadResponse,
    DocumentListResponse,
    DocumentInfo,
    DocumentStats,
    ErrorResponse
)
from services.document_processor import DocumentProcessor
from services.vector_store import VectorStoreManager
from config.settings import get_settings

logger = logging.getLogger(__name__)

# Create router
router = APIRouter(prefix="/api/v1/documents", tags=["documents"])

# Global instances (will be initialized on startup)
_document_processor: Optional[DocumentProcessor] = None
_vector_store: Optional[VectorStoreManager] = None


def initialize_document_services():
    """
    Initialize document processing services.
    
    This should be called during application startup.
    """
    global _document_processor, _vector_store
    
    settings = get_settings()
    
    # Initialize vector store
    _vector_store = VectorStoreManager(
        persist_directory=settings.chroma_persist_dir,
        collection_name=settings.chroma_collection_name
    )
    
    # Initialize document processor
    _document_processor = DocumentProcessor(
        vector_store=_vector_store,
        google_api_key=settings.google_api_key,
        embedding_model=settings.gemini_embedding_model,
        chunk_size=settings.chunk_size,
        chunk_overlap=settings.chunk_overlap
    )
    
    logger.info("Document services initialized successfully")


def get_document_processor() -> DocumentProcessor:
    """Get the document processor instance."""
    if _document_processor is None:
        raise RuntimeError("Document processor not initialized")
    return _document_processor


def get_vector_store() -> VectorStoreManager:
    """Get the vector store instance."""
    if _vector_store is None:
        raise RuntimeError("Vector store not initialized")
    return _vector_store


@router.post(
    "/upload",
    response_model=DocumentUploadResponse,
    status_code=status.HTTP_201_CREATED,
    responses={
        201: {
            "description": "Document uploaded and processed successfully",
            "model": DocumentUploadResponse
        },
        400: {
            "description": "Invalid file type or empty file",
            "model": ErrorResponse
        },
        413: {
            "description": "File size exceeds maximum limit",
            "model": ErrorResponse
        },
        500: {
            "description": "Internal server error during processing",
            "model": ErrorResponse
        }
    }
)
async def upload_document(
    file: UploadFile = File(..., description="Document file to upload (PDF, DOCX, or TXT)")
):
    """
    Upload and process a financial document.
    
    This endpoint accepts PDF, DOCX, or TXT files, processes them by:
    1. Validating file type and size
    2. Extracting text content
    3. Splitting into chunks
    4. Generating embeddings
    5. Storing in vector database
    
    Args:
        file: Uploaded file (multipart/form-data)
        
    Returns:
        DocumentUploadResponse with document metadata
        
    Raises:
        HTTPException: For validation errors or processing failures
    """
    settings = get_settings()
    document_processor = get_document_processor()
    
    # Validate filename exists
    if not file.filename:
        logger.warning("Upload attempt with no filename")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "error": "ValidationError",
                "message": "Filename is required",
                "details": None
            }
        )
    
    logger.info(f"Received upload request for file: {file.filename}")
    
    # Validate file type
    file_extension = os.path.splitext(file.filename)[1].lower().strip('.')
    supported_types = document_processor.get_supported_file_types()
    
    if file_extension not in supported_types:
        logger.warning(f"Unsupported file type: {file_extension}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "error": "ValidationError",
                "message": f"Invalid file type. Only {', '.join(supported_types).upper()} files are supported.",
                "details": {
                    "file_type": file_extension,
                    "allowed_types": supported_types
                }
            }
        )
    
    # Read file content to validate size
    try:
        file_content = await file.read()
        file_size = len(file_content)
        
        # Validate file size
        max_size = settings.max_file_size_bytes
        if file_size > max_size:
            logger.warning(
                f"File size {file_size} bytes exceeds maximum {max_size} bytes"
            )
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail={
                    "error": "FileTooLarge",
                    "message": f"File size exceeds maximum limit of {settings.max_file_size_mb}MB",
                    "details": {
                        "file_size_mb": round(file_size / (1024 * 1024), 2),
                        "max_size_mb": settings.max_file_size_mb
                    }
                }
            )
        
        # Validate file is not empty
        if file_size == 0:
            logger.warning("Empty file uploaded")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "error": "ValidationError",
                    "message": "File is empty",
                    "details": None
                }
            )
        
        logger.info(f"File validation passed: {file.filename} ({file_size} bytes)")
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error reading uploaded file: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": "FileReadError",
                "message": "Failed to read uploaded file",
                "details": {"error": str(e)}
            }
        )
    
    # Generate unique document ID
    document_id = f"doc_{uuid.uuid4().hex[:12]}"
    
    # Save file temporarily for processing
    temp_dir = "./data/temp"
    os.makedirs(temp_dir, exist_ok=True)
    temp_file_path = os.path.join(temp_dir, f"{document_id}_{file.filename}")
    
    try:
        # Write file to temporary location
        with open(temp_file_path, "wb") as f:
            f.write(file_content)
        
        logger.info(f"Saved temporary file: {temp_file_path}")
        
        # Process the document
        result = document_processor.process_document(
            file_path=temp_file_path,
            filename=file.filename,
            document_id=document_id
        )
        
        logger.info(
            f"Successfully processed document {file.filename}: "
            f"{result['chunks_created']} chunks created"
        )
        
        # Return response
        return DocumentUploadResponse(
            document_id=result['document_id'],
            filename=result['filename'],
            chunks_created=result['chunks_created'],
            upload_date=result['upload_date']
        )
        
    except ValueError as e:
        # Handle validation errors from document processor
        logger.error(f"Validation error processing document: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "error": "ProcessingError",
                "message": str(e),
                "details": {"document_id": document_id}
            }
        )
    
    except Exception as e:
        # Handle unexpected processing errors
        logger.error(f"Error processing document {file.filename}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": "ProcessingError",
                "message": "Failed to process document",
                "details": {
                    "document_id": document_id,
                    "error": str(e)
                }
            }
        )
    
    finally:
        # Clean up temporary file
        try:
            if os.path.exists(temp_file_path):
                os.remove(temp_file_path)
                logger.info(f"Cleaned up temporary file: {temp_file_path}")
        except Exception as e:
            logger.warning(f"Failed to clean up temporary file {temp_file_path}: {e}")


@router.get(
    "",
    response_model=DocumentListResponse,
    status_code=status.HTTP_200_OK,
    responses={
        200: {
            "description": "List of all documents retrieved successfully",
            "model": DocumentListResponse
        },
        500: {
            "description": "Internal server error",
            "model": ErrorResponse
        }
    }
)
async def list_documents():
    """
    List all stored documents with metadata.
    
    Retrieves metadata for all documents currently stored in the vector database,
    including document ID, filename, upload date, and chunk count.
    
    Returns:
        DocumentListResponse containing list of all documents
        
    Raises:
        HTTPException: If retrieval fails
    """
    try:
        vector_store = get_vector_store()
        
        logger.info("Retrieving list of all documents")
        
        # Get all documents from vector store
        documents_data = vector_store.list_all_documents()
        
        # Convert to DocumentInfo models
        documents = [
            DocumentInfo(
                id=doc['document_id'],
                filename=doc['filename'],
                upload_date=doc['upload_date'],
                chunks=doc['chunk_count']
            )
            for doc in documents_data
        ]
        
        logger.info(f"Successfully retrieved {len(documents)} documents")
        
        return DocumentListResponse(documents=documents)
        
    except Exception as e:
        logger.error(f"Error listing documents: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": "RetrievalError",
                "message": "Failed to retrieve document list",
                "details": {"error": str(e)}
            }
        )


@router.delete(
    "/{document_id}",
    status_code=status.HTTP_200_OK,
    responses={
        200: {
            "description": "Document deleted successfully"
        },
        404: {
            "description": "Document not found",
            "model": ErrorResponse
        },
        500: {
            "description": "Internal server error",
            "model": ErrorResponse
        }
    }
)
async def delete_document(document_id: str):
    """
    Delete a document and all its associated chunks.
    
    Removes the specified document from the vector database, including all
    text chunks and embeddings associated with it.
    
    Args:
        document_id: Unique identifier of the document to delete
        
    Returns:
        Success message with deletion details
        
    Raises:
        HTTPException: If document not found or deletion fails
    """
    try:
        vector_store = get_vector_store()
        
        logger.info(f"Attempting to delete document: {document_id}")
        
        # Delete document and get count of deleted chunks
        deleted_count = vector_store.delete_by_document_id(document_id)
        
        # Check if document existed
        if deleted_count == 0:
            logger.warning(f"Document not found: {document_id}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={
                    "error": "NotFound",
                    "message": f"Document with ID '{document_id}' not found",
                    "details": {"document_id": document_id}
                }
            )
        
        logger.info(f"Successfully deleted document {document_id} ({deleted_count} chunks)")
        
        return {
            "success": True,
            "message": f"Document deleted successfully",
            "document_id": document_id,
            "chunks_deleted": deleted_count
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting document {document_id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": "DeletionError",
                "message": "Failed to delete document",
                "details": {
                    "document_id": document_id,
                    "error": str(e)
                }
            }
        )


@router.get(
    "/stats",
    response_model=DocumentStats,
    status_code=status.HTTP_200_OK,
    responses={
        200: {
            "description": "Document statistics retrieved successfully",
            "model": DocumentStats
        },
        500: {
            "description": "Internal server error",
            "model": ErrorResponse
        }
    }
)
async def get_document_stats():
    """
    Get statistics about stored documents.
    
    Returns aggregate statistics including the total number of documents
    and total number of chunks stored in the vector database.
    
    Returns:
        DocumentStats with total documents and chunks
        
    Raises:
        HTTPException: If retrieval fails
    """
    try:
        vector_store = get_vector_store()
        
        logger.info("Retrieving document statistics")
        
        # Get stats from vector store
        stats = vector_store.get_stats()
        
        logger.info(f"Statistics retrieved: {stats}")
        
        return DocumentStats(
            total_documents=stats['total_documents'],
            total_chunks=stats['total_chunks']
        )
        
    except Exception as e:
        logger.error(f"Error retrieving statistics: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": "RetrievalError",
                "message": "Failed to retrieve document statistics",
                "details": {"error": str(e)}
            }
        )
