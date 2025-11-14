"""
Chat endpoint for RAG-based query processing.

This module provides the chat endpoint that processes user queries
using the RAG pipeline and returns context-aware responses.
"""

from fastapi import APIRouter, HTTPException, status, Depends
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
import logging

from models.schemas import ChatRequest, ChatResponse, Source
from services.rag_engine import RAGQueryEngine
from services.vector_store import VectorStoreManager
from services.mongodb_session_manager import MongoDBSessionManager
from config.settings import get_settings
from api.routes.auth import get_current_user

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/v1",
    tags=["chat"]
)

# Global instances (initialized in initialize_chat_services)
rag_engine: Optional[RAGQueryEngine] = None


def initialize_chat_services():
    """
    Initialize chat services including RAG engine.
    Called during application startup.
    """
    global rag_engine
    
    try:
        settings = get_settings()
        
        # Initialize vector store
        vector_store = VectorStoreManager(
            persist_directory=settings.chroma_persist_dir,
            collection_name=settings.chroma_collection_name
        )
        
        # Initialize MongoDB session manager
        session_manager = MongoDBSessionManager(
            connection_string=settings.mongodb_connection_string,
            database_name=settings.mongodb_database_name,
            max_turns=settings.max_conversation_turns
        )
        
        # Initialize RAG engine
        rag_engine = RAGQueryEngine(
            vector_store=vector_store,
            session_manager=session_manager,
            google_api_key=settings.google_api_key,
            embedding_model_name=settings.gemini_embedding_model,
            chat_model_name=settings.gemini_chat_model,
            temperature=settings.gemini_temperature,
            max_tokens=settings.gemini_max_tokens,
            top_k=settings.top_k_chunks
        )
        
        logger.info("Chat services initialized successfully with MongoDB")
        
    except Exception as e:
        logger.error(f"Failed to initialize chat services: {e}")
        raise


@router.post(
    "/chat",
    response_model=ChatResponse,
    status_code=status.HTTP_200_OK,
    summary="Process a chat query",
    description="Submit a financial question and receive a context-aware answer based on uploaded documents (requires authentication)"
)
async def chat_query(
    request: ChatRequest,
    current_user: dict = Depends(get_current_user)
) -> ChatResponse:
    """
    Process a user query using RAG pipeline.
    
    Args:
        request: ChatRequest containing query and optional session_id
        current_user: Current authenticated user (injected by dependency)
        
    Returns:
        ChatResponse with generated answer, sources, and session_id
        
    Raises:
        HTTPException: If query processing fails
    """
    if rag_engine is None:
        logger.error("Chat services not initialized")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Chat service is not available. Please try again later."
        )
    
    try:
        logger.info(f"Received chat query from user {current_user['username']}: '{request.query[:50]}...'")
        
        # Process query through RAG pipeline
        result = rag_engine.query(
            user_query=request.query,
            session_id=request.session_id,
            user_id=current_user['user_id']
        )
        
        # Convert sources to response format
        sources = [
            Source(
                document_id=src['document_id'],
                filename=src['filename'],
                chunk_text=src['chunk_text'],
                relevance_score=src['relevance_score']
            )
            for src in result['sources']
        ]
        
        response = ChatResponse(
            response=result['response'],
            sources=sources,
            session_id=result['session_id']
        )
        
        logger.info(f"Chat query processed successfully, session_id={result['session_id']}")
        return response
    
    except Exception as e:
        logger.error(f"Chat query failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to process query: {str(e)}"
        )
