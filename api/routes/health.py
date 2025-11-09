"""
Health check endpoint for the Financial Chatbot RAG API.

This module provides a health check endpoint to verify the status of critical
system components including the vector database and Google Gemini API.
"""

import logging
from typing import Dict, Any

from fastapi import APIRouter, status
from fastapi.responses import JSONResponse

from config.settings import get_settings
from services.vector_store import VectorStoreManager
import google.generativeai as genai

logger = logging.getLogger(__name__)

# Create router
router = APIRouter(prefix="/api/v1", tags=["health"])


def check_vector_database() -> Dict[str, Any]:
    """
    Check vector database connectivity and health.
    
    Returns:
        Dictionary with status and details
    """
    try:
        settings = get_settings()
        
        # Initialize vector store to test connectivity
        vector_store = VectorStoreManager(
            persist_directory=settings.chroma_persist_dir,
            collection_name=settings.chroma_collection_name
        )
        
        # Try to get stats to verify database is operational
        stats = vector_store.get_stats()
        
        return {
            "status": "healthy",
            "details": {
                "total_documents": stats.get('total_documents', 0),
                "total_chunks": stats.get('total_chunks', 0)
            }
        }
    except Exception as e:
        logger.error(f"Vector database health check failed: {e}")
        return {
            "status": "unhealthy",
            "error": str(e)
        }


def check_gemini_api() -> Dict[str, Any]:
    """
    Check Google Gemini API connectivity and health.
    
    Returns:
        Dictionary with status and details
    """
    try:
        settings = get_settings()
        
        # Configure Gemini API
        genai.configure(api_key=settings.google_api_key)
        
        # Try to list models to verify API connectivity
        models = genai.list_models()
        model_list = [m.name for m in models]
        
        # Check if required models are available
        embedding_model_available = any(
            settings.gemini_embedding_model in model 
            for model in model_list
        )
        chat_model_available = any(
            settings.gemini_chat_model in model 
            for model in model_list
        )
        
        return {
            "status": "healthy",
            "details": {
                "embedding_model": settings.gemini_embedding_model,
                "embedding_model_available": embedding_model_available,
                "chat_model": settings.gemini_chat_model,
                "chat_model_available": chat_model_available
            }
        }
    except Exception as e:
        logger.error(f"Gemini API health check failed: {e}")
        return {
            "status": "unhealthy",
            "error": str(e)
        }


@router.get(
    "/health",
    status_code=status.HTTP_200_OK,
    responses={
        200: {
            "description": "All components are healthy"
        },
        503: {
            "description": "One or more critical components are unavailable"
        }
    }
)
async def health_check():
    """
    Check the health status of all system components.
    
    This endpoint verifies:
    - Vector database connectivity and operational status
    - Google Gemini API connectivity and model availability
    
    Returns:
        JSON response with status of each component
        - 200 OK if all components are healthy
        - 503 Service Unavailable if any critical component is unhealthy
    """
    logger.info("Health check requested")
    
    # Check vector database
    vector_db_status = check_vector_database()
    
    # Check Gemini API
    gemini_api_status = check_gemini_api()
    
    # Determine overall status
    all_healthy = (
        vector_db_status["status"] == "healthy" and
        gemini_api_status["status"] == "healthy"
    )
    
    response_data = {
        "status": "healthy" if all_healthy else "unhealthy",
        "components": {
            "vector_database": vector_db_status,
            "gemini_api": gemini_api_status
        }
    }
    
    # Return appropriate status code
    if all_healthy:
        logger.info("Health check passed: all components healthy")
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content=response_data
        )
    else:
        logger.warning("Health check failed: one or more components unhealthy")
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content=response_data
        )
