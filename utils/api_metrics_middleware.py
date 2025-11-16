"""
API Metrics Collection Middleware for performance monitoring and analytics.

This module provides middleware to capture and store API request/response metrics
in MongoDB for system monitoring and usage analysis.
"""

import time
import logging
from datetime import datetime
from typing import Callable, Optional
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp
from pymongo import MongoClient, ASCENDING, DESCENDING
from pymongo.errors import ConnectionFailure

logger = logging.getLogger(__name__)


class APIMetricsCollector:
    """
    Collects and stores API metrics in MongoDB.
    
    Records endpoint, method, status code, response time, timestamp,
    user_id (if available), and error messages for failed requests.
    """
    
    def __init__(
        self,
        connection_string: str = "mongodb://localhost:27017/",
        database_name: str = "financial_chatbot"
    ):
        """
        Initialize the APIMetricsCollector.
        
        Args:
            connection_string: MongoDB connection string
            database_name: Name of the database to use
        """
        self.connection_string = connection_string
        self.database_name = database_name
        self.client: Optional[MongoClient] = None
        self.db = None
        self.api_metrics_collection = None
        
        try:
            # Initialize MongoDB client
            self.client = MongoClient(connection_string, serverSelectionTimeoutMS=5000)
            
            # Test connection
            self.client.admin.command('ping')
            logger.info(f"APIMetricsCollector connected to MongoDB at {connection_string}")
            
            # Get database and collection
            self.db = self.client[database_name]
            self.api_metrics_collection = self.db['api_metrics']
            
            # Create indexes for better performance
            self._create_indexes()
            
        except ConnectionFailure as e:
            logger.error(f"Failed to connect to MongoDB for metrics: {e}")
            # Don't raise - allow app to continue without metrics
            self.client = None
        except Exception as e:
            logger.error(f"Error initializing APIMetricsCollector: {e}")
            self.client = None
    
    def _create_indexes(self):
        """Create database indexes for better query performance."""
        try:
            # Index on timestamp for time-based queries
            self.api_metrics_collection.create_index([("timestamp", DESCENDING)])
            
            # Index on endpoint for endpoint-specific queries
            self.api_metrics_collection.create_index([("endpoint", ASCENDING)])
            
            # Compound index for efficient filtering
            self.api_metrics_collection.create_index([
                ("endpoint", ASCENDING),
                ("timestamp", DESCENDING)
            ])
            
            # Index on status_code for error analysis
            self.api_metrics_collection.create_index([("status_code", ASCENDING)])
            
            # Index on user_id for user-specific metrics
            self.api_metrics_collection.create_index([("user_id", ASCENDING)])
            
            logger.info("API metrics indexes created successfully")
            
        except Exception as e:
            logger.warning(f"Error creating API metrics indexes: {e}")
    
    def record_metric(
        self,
        endpoint: str,
        method: str,
        status_code: int,
        response_time_ms: float,
        user_id: Optional[str] = None,
        error_message: Optional[str] = None
    ) -> bool:
        """
        Record an API request metric to MongoDB.
        
        Args:
            endpoint: API endpoint path
            method: HTTP method (GET, POST, etc.)
            status_code: HTTP response status code
            response_time_ms: Response time in milliseconds
            user_id: Optional user ID if authenticated
            error_message: Optional error message for failed requests
            
        Returns:
            bool: True if metric was recorded successfully, False otherwise
        """
        # Skip if MongoDB connection failed
        if self.client is None or self.api_metrics_collection is None:
            return False
        
        try:
            metric_entry = {
                "endpoint": endpoint,
                "method": method,
                "status_code": status_code,
                "response_time_ms": round(response_time_ms, 2),
                "timestamp": datetime.utcnow(),
                "user_id": user_id,
                "error_message": error_message
            }
            
            self.api_metrics_collection.insert_one(metric_entry)
            
            logger.debug(
                f"Metric recorded: {method} {endpoint} - {status_code} "
                f"({response_time_ms:.2f}ms)"
            )
            return True
            
        except Exception as e:
            logger.error(f"Error recording API metric: {e}")
            return False
    
    def close(self):
        """Close the MongoDB connection."""
        try:
            if self.client:
                self.client.close()
                logger.info("APIMetricsCollector MongoDB connection closed")
        except Exception as e:
            logger.error(f"Error closing MongoDB connection: {e}")


class APIMetricsMiddleware(BaseHTTPMiddleware):
    """
    Middleware to capture and store API request/response metrics.
    
    Records endpoint, method, status code, response time, timestamp,
    user_id (if available), and error messages for failed requests.
    """
    
    def __init__(
        self,
        app: ASGIApp,
        connection_string: str = "mongodb://localhost:27017/",
        database_name: str = "financial_chatbot"
    ):
        """
        Initialize the middleware.
        
        Args:
            app: The ASGI application
            connection_string: MongoDB connection string
            database_name: MongoDB database name
        """
        super().__init__(app)
        self.metrics_collector = APIMetricsCollector(
            connection_string=connection_string,
            database_name=database_name
        )
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """
        Process the request and record metrics.
        
        Args:
            request: The incoming request
            call_next: The next middleware or route handler
            
        Returns:
            The response from the application
        """
        # Record start time
        start_time = time.time()
        
        # Initialize variables
        status_code = 500
        error_message = None
        
        # Process request
        try:
            response = await call_next(request)
            status_code = response.status_code
            
        except Exception as e:
            # Capture error for failed requests
            error_message = str(e)
            logger.error(f"Request failed: {request.method} {request.url.path} - {error_message}")
            raise
        
        finally:
            # Calculate response time
            response_time_ms = (time.time() - start_time) * 1000
            
            # Extract user_id if available (from request state or token)
            user_id = None
            if hasattr(request.state, "user"):
                user = getattr(request.state, "user", None)
                if user and isinstance(user, dict):
                    user_id = user.get("user_id") or user.get("_id")
            
            # Record metric
            self.metrics_collector.record_metric(
                endpoint=request.url.path,
                method=request.method,
                status_code=status_code,
                response_time_ms=response_time_ms,
                user_id=user_id,
                error_message=error_message
            )
        
        return response
    
    def __del__(self):
        """Cleanup when middleware is destroyed."""
        try:
            self.metrics_collector.close()
        except Exception:
            pass
