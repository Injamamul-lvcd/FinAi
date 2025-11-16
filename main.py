"""
Financial Chatbot RAG System - Main Application Entry Point
"""
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response
import uvicorn

from api.routes import documents, health
from config.settings import get_settings
from utils.logger import setup_logging, get_logger
from utils.middleware import RequestLoggingMiddleware, ErrorHandlingMiddleware
from utils.api_metrics_middleware import APIMetricsMiddleware
from utils.exceptions import register_exception_handlers

# Import chat routes
from api.routes import chat
CHAT_AVAILABLE = True

# Import auth routes
from api.routes import auth
AUTH_AVAILABLE = True

# Import admin routes
from api.routes import admin
ADMIN_AVAILABLE = True

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


class AdminCORSMiddleware(BaseHTTPMiddleware):
    """
    Custom CORS middleware that applies different CORS policies for admin endpoints.
    
    Admin endpoints (/api/v1/admin/*) use restricted CORS origins for security,
    while regular endpoints use the standard CORS configuration.
    """
    
    async def dispatch(self, request: Request, call_next):
        # Check if this is an admin endpoint
        is_admin_endpoint = request.url.path.startswith("/api/v1/admin")
        
        # Get appropriate CORS origins
        if is_admin_endpoint:
            allowed_origins = settings.admin_cors_origins_list
        else:
            allowed_origins = settings.cors_origins_list
        
        # Get origin from request
        origin = request.headers.get("origin")
        
        # Handle preflight requests
        if request.method == "OPTIONS":
            # Allow requests with or without origin header
            if allowed_origins == ["*"] or not origin or origin in allowed_origins:
                return Response(
                    status_code=200,
                    headers={
                        "Access-Control-Allow-Origin": origin if (origin and allowed_origins != ["*"]) else "*",
                        "Access-Control-Allow-Methods": "GET, POST, PUT, DELETE, OPTIONS",
                        "Access-Control-Allow-Headers": "Content-Type, Authorization",
                        "Access-Control-Allow-Credentials": "true" if (origin and allowed_origins != ["*"]) else "false",
                        "Access-Control-Max-Age": "600",
                    }
                )
        
        # Process the request
        response = await call_next(request)
        
        # Add CORS headers to response
        # Allow requests with or without origin header when CORS is set to "*"
        if allowed_origins == ["*"]:
            response.headers["Access-Control-Allow-Origin"] = "*"
            response.headers["Access-Control-Allow-Credentials"] = "false"
        elif origin and origin in allowed_origins:
            response.headers["Access-Control-Allow-Origin"] = origin
            response.headers["Access-Control-Allow-Credentials"] = "true"
        
        return response


# Create FastAPI application
app = FastAPI(
    title="Financial Chatbot RAG API",
    description="A Retrieval-Augmented Generation chatbot for financial questions",
    version="1.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc"
)

# Configure CORS with custom middleware for admin endpoints
# This provides separate CORS policies for admin and regular endpoints
app.add_middleware(AdminCORSMiddleware)

# Note: The AdminCORSMiddleware handles CORS for all endpoints including admin.
# Admin endpoints use admin_cors_origins_list (default: "*", should be restricted in production)
# Regular endpoints use cors_origins_list (default: "*")
# 
# To configure in production, set environment variables:
# CORS_ORIGINS=https://yourapp.com,https://www.yourapp.com
# ADMIN_CORS_ORIGINS=https://admin.yourapp.com

# Add custom middleware for logging, error handling, and metrics collection
app.add_middleware(ErrorHandlingMiddleware)
app.add_middleware(RequestLoggingMiddleware)

# Add API metrics collection middleware
# Note: If MongoDB is slow or unavailable, this might cause delays
try:
    app.add_middleware(
        APIMetricsMiddleware,
        connection_string=settings.mongodb_connection_string,
        database_name=settings.mongodb_database_name
    )
    logger.info("API metrics middleware enabled")
except Exception as e:
    logger.warning(f"API metrics middleware disabled due to error: {e}")

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

# Register admin router if available
if ADMIN_AVAILABLE:
    app.include_router(admin.router)
    logger.info("Admin routes registered")


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
        
        # Initialize admin services
        if ADMIN_AVAILABLE:
            admin.initialize_admin_services()
            logger.info("Admin services initialized")
        
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
