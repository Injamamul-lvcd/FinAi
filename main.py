"""
Financial Chatbot RAG System - Main Application Entry Point
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

from api.routes import documents, health
from config.settings import get_settings
from utils.logger import setup_logging, get_logger
from utils.middleware import RequestLoggingMiddleware, ErrorHandlingMiddleware
from utils.exceptions import register_exception_handlers

# Import chat routes
from api.routes import chat
CHAT_AVAILABLE = True

# Import auth routes
from api.routes import auth
AUTH_AVAILABLE = True

# Initialize settings to get log level
settings = get_settings()

# Configure structured logging with file rotation
setup_logging(
    log_level=settings.log_level,
    log_dir="./logs",
    log_file="app.log",
    console_level=settings.log_level
)

logger = get_logger(__name__)

# Create FastAPI application
app = FastAPI(
    title="Financial Chatbot RAG API",
    description="A Retrieval-Augmented Generation chatbot for financial questions",
    version="1.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add custom middleware for logging and error handling
app.add_middleware(ErrorHandlingMiddleware)
app.add_middleware(RequestLoggingMiddleware)

# Register custom exception handlers
register_exception_handlers(app)

# Register routers
app.include_router(documents.router)
app.include_router(health.router)

# Register auth router if available
if AUTH_AVAILABLE:
    app.include_router(auth.router)
    logger.info("Auth routes registered")

# Register chat router if available
if CHAT_AVAILABLE:
    app.include_router(chat.router)
    logger.info("Chat routes registered")


@app.on_event("startup")
async def startup_event():
    """Initialize application on startup"""
    logger.info("Starting Financial Chatbot RAG API...")
    
    try:
        # Load and validate configuration
        settings = get_settings()
        logger.info(f"Configuration loaded successfully")
        logger.info(f"Vector DB: {settings.chroma_persist_dir}")
        logger.info(f"Max file size: {settings.max_file_size_mb}MB")
        
        # Initialize document services
        documents.initialize_document_services()
        logger.info("Document services initialized")
        
        # Initialize auth services
        if AUTH_AVAILABLE:
            auth.initialize_auth_service()
            logger.info("Auth services initialized")
        
        # Initialize chat services
        if CHAT_AVAILABLE:
            chat.initialize_chat_services()
            logger.info("Chat services initialized")
        
        logger.info("Application startup complete")
        
    except Exception as e:
        logger.error(f"Failed to initialize application: {e}", exc_info=True)
        raise


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on application shutdown"""
    logger.info("Shutting down Financial Chatbot RAG API...")
    
    try:
        # Perform any necessary cleanup
        # Note: ChromaDB and SQLite connections are automatically closed
        logger.info("Cleanup completed successfully")
    except Exception as e:
        logger.error(f"Error during shutdown cleanup: {e}", exc_info=True)
    
    logger.info("Application shutdown complete")


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "Financial Chatbot RAG API",
        "version": "1.0.0",
        "docs": "/api/docs"
    }


if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )
