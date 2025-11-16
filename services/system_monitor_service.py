"""
System Monitor Service for health checks and metrics.

This module provides the SystemMonitorService class for monitoring system health,
performance metrics, storage usage, API usage, and error logs.
"""

import logging
import os
import shutil
import psutil
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure
import sqlite3
import time

logger = logging.getLogger(__name__)


class SystemMonitorService:
    """
    Manages system monitoring operations including health checks,
    metrics collection, storage monitoring, and error log retrieval.
    """
    
    def __init__(
        self,
        connection_string: str,
        database_name: str,
        vector_store_manager=None,
        session_db_path: str = "./data/sessions.db"
    ):
        """
        Initialize the SystemMonitorService.
        
        Args:
            connection_string: MongoDB connection string
            database_name: MongoDB database name
            vector_store_manager: VectorStoreManager instance for health checks
            session_db_path: Path to SQLite session database
        """
        self.connection_string = connection_string
        self.database_name = database_name
        self.vector_store_manager = vector_store_manager
        self.session_db_path = session_db_path
        
        # MongoDB client
        self.client = MongoClient(connection_string)
        self.db = self.client[database_name]
        
        # Collections
        self.api_metrics_collection = self.db['api_metrics']
        
        # Create indexes for api_metrics
        self._create_indexes()
        
        # Track application start time
        self.start_time = datetime.now()
        
        logger.info("SystemMonitorService initialized")
    
    def _create_indexes(self):
        """Create necessary indexes for api_metrics collection."""
        try:
            # Index on timestamp for time-based queries
            self.api_metrics_collection.create_index([("timestamp", -1)])
            
            # Index on endpoint for filtering by endpoint
            self.api_metrics_collection.create_index([("endpoint", 1)])
            
            # Compound index for efficient endpoint metrics queries
            self.api_metrics_collection.create_index([("timestamp", -1), ("endpoint", 1)])
            
            # Index on status_code for error filtering
            self.api_metrics_collection.create_index([("status_code", 1)])
            
            # Index on response_time_ms for performance analysis
            self.api_metrics_collection.create_index([("response_time_ms", -1)])
            
            logger.info("API metrics indexes created")
        except Exception as e:
            logger.error(f"Failed to create indexes: {e}")
    
    def get_health_status(self) -> Dict[str, Any]:
        """
        Check health status of all system components.
        
        Returns:
            Dictionary containing:
                - status: Overall system status (healthy/degraded/unhealthy)
                - vector_db_status: ChromaDB connection status
                - llm_api_status: LLM API availability status
                - session_db_status: SQLite session database status
                - mongodb_status: MongoDB connection status
                - timestamp: Current timestamp
                - error_details: Optional error information
        """
        health_status = {
            "status": "healthy",
            "vector_db_status": "unknown",
            "llm_api_status": "unknown",
            "session_db_status": "unknown",
            "mongodb_status": "unknown",
            "timestamp": datetime.now().isoformat(),
            "error_details": {}
        }
        
        unhealthy_count = 0
        
        # Check MongoDB
        try:
            self.client.admin.command('ping')
            health_status["mongodb_status"] = "healthy"
        except ConnectionFailure as e:
            health_status["mongodb_status"] = "unhealthy"
            health_status["error_details"]["mongodb"] = str(e)
            unhealthy_count += 1
        except Exception as e:
            health_status["mongodb_status"] = "unhealthy"
            health_status["error_details"]["mongodb"] = str(e)
            unhealthy_count += 1
        
        # Check Vector DB (ChromaDB)
        if self.vector_store_manager:
            try:
                # Try to get stats from vector store
                self.vector_store_manager.get_stats()
                health_status["vector_db_status"] = "healthy"
            except Exception as e:
                health_status["vector_db_status"] = "unhealthy"
                health_status["error_details"]["vector_db"] = str(e)
                unhealthy_count += 1
        else:
            health_status["vector_db_status"] = "not_configured"
        
        # Check Session DB (SQLite)
        try:
            conn = sqlite3.connect(self.session_db_path)
            cursor = conn.cursor()
            cursor.execute("SELECT 1")
            conn.close()
            health_status["session_db_status"] = "healthy"
        except Exception as e:
            health_status["session_db_status"] = "unhealthy"
            health_status["error_details"]["session_db"] = str(e)
            unhealthy_count += 1
        
        # Check LLM API (Gemini)
        # Note: We can't directly check Gemini API without making a request
        # For now, we'll mark it as healthy if we can import the library
        try:
            import google.generativeai as genai
            health_status["llm_api_status"] = "healthy"
        except ImportError as e:
            health_status["llm_api_status"] = "unhealthy"
            health_status["error_details"]["llm_api"] = "Google Generative AI library not available"
            unhealthy_count += 1
        except Exception as e:
            health_status["llm_api_status"] = "degraded"
            health_status["error_details"]["llm_api"] = str(e)
        
        # Determine overall status
        if unhealthy_count == 0:
            health_status["status"] = "healthy"
        elif unhealthy_count <= 1:
            health_status["status"] = "degraded"
        else:
            health_status["status"] = "unhealthy"
        
        # Remove error_details if empty
        if not health_status["error_details"]:
            del health_status["error_details"]
        
        return health_status
    
    def get_system_metrics(self) -> Dict[str, Any]:
        """
        Get current system performance metrics.
        
        Returns:
            Dictionary containing:
                - active_sessions: Number of active sessions
                - total_requests_24h: Total API requests in last 24 hours
                - avg_response_time_ms: Average response time in milliseconds
                - memory_usage_percent: Memory usage percentage
                - disk_usage_percent: Disk usage percentage
                - uptime_hours: Application uptime in hours
        """
        metrics = {
            "active_sessions": 0,
            "total_requests_24h": 0,
            "avg_response_time_ms": 0.0,
            "memory_usage_percent": 0.0,
            "disk_usage_percent": 0.0,
            "uptime_hours": 0.0
        }
        
        # Get active sessions count
        try:
            conn = sqlite3.connect(self.session_db_path)
            cursor = conn.cursor()
            # Consider sessions active if they had activity in last 24 hours
            cutoff = datetime.now() - timedelta(hours=24)
            cursor.execute(
                "SELECT COUNT(*) FROM sessions WHERE last_activity > ?",
                (cutoff,)
            )
            metrics["active_sessions"] = cursor.fetchone()[0]
            conn.close()
        except Exception as e:
            logger.error(f"Failed to get active sessions count: {e}")
        
        # Get API metrics from last 24 hours
        try:
            cutoff = datetime.now() - timedelta(hours=24)
            
            # Total requests
            total_requests = self.api_metrics_collection.count_documents({
                "timestamp": {"$gte": cutoff}
            })
            metrics["total_requests_24h"] = total_requests
            
            # Average response time
            if total_requests > 0:
                pipeline = [
                    {"$match": {"timestamp": {"$gte": cutoff}}},
                    {"$group": {
                        "_id": None,
                        "avg_response_time": {"$avg": "$response_time_ms"}
                    }}
                ]
                result = list(self.api_metrics_collection.aggregate(pipeline))
                if result:
                    metrics["avg_response_time_ms"] = round(result[0]["avg_response_time"], 2)
        except Exception as e:
            logger.error(f"Failed to get API metrics: {e}")
        
        # Get memory usage
        try:
            process = psutil.Process()
            memory_info = process.memory_info()
            memory_percent = process.memory_percent()
            metrics["memory_usage_percent"] = round(memory_percent, 2)
        except Exception as e:
            logger.error(f"Failed to get memory usage: {e}")
        
        # Get disk usage
        try:
            disk_usage = psutil.disk_usage('/')
            metrics["disk_usage_percent"] = round(disk_usage.percent, 2)
        except Exception as e:
            logger.error(f"Failed to get disk usage: {e}")
        
        # Calculate uptime
        uptime = datetime.now() - self.start_time
        metrics["uptime_hours"] = round(uptime.total_seconds() / 3600, 2)
        
        return metrics

    def get_storage_metrics(self) -> Dict[str, Any]:
        """
        Get storage usage metrics for all databases and disk.
        
        Returns:
            Dictionary containing:
                - vector_db_size_mb: Vector database size in megabytes
                - session_db_size_mb: Session database size in megabytes
                - mongodb_size_mb: MongoDB size in megabytes
                - total_document_size_mb: Total uploaded document size
                - available_disk_gb: Available disk space in gigabytes
                - disk_usage_percent: Disk usage percentage
                - growth_rate_7d_percent: Storage growth rate over last 7 days
        """
        metrics = {
            "vector_db_size_mb": 0.0,
            "session_db_size_mb": 0.0,
            "mongodb_size_mb": 0.0,
            "total_document_size_mb": 0.0,
            "available_disk_gb": 0.0,
            "disk_usage_percent": 0.0,
            "growth_rate_7d_percent": 0.0
        }
        
        # Get Vector DB size (ChromaDB directory)
        try:
            chroma_path = "./data/chroma"
            if os.path.exists(chroma_path):
                total_size = 0
                for dirpath, dirnames, filenames in os.walk(chroma_path):
                    for filename in filenames:
                        filepath = os.path.join(dirpath, filename)
                        if os.path.exists(filepath):
                            total_size += os.path.getsize(filepath)
                metrics["vector_db_size_mb"] = round(total_size / (1024 * 1024), 2)
        except Exception as e:
            logger.error(f"Failed to get vector DB size: {e}")
        
        # Get Session DB size (SQLite)
        try:
            if os.path.exists(self.session_db_path):
                size = os.path.getsize(self.session_db_path)
                metrics["session_db_size_mb"] = round(size / (1024 * 1024), 2)
        except Exception as e:
            logger.error(f"Failed to get session DB size: {e}")
        
        # Get MongoDB size
        try:
            stats = self.db.command("dbStats")
            metrics["mongodb_size_mb"] = round(stats.get("dataSize", 0) / (1024 * 1024), 2)
        except Exception as e:
            logger.error(f"Failed to get MongoDB size: {e}")
        
        # Get total document size from ChromaDB metadata
        try:
            if self.vector_store_manager:
                stats = self.vector_store_manager.get_stats()
                total_doc_size = 0
                for doc_id, doc_info in stats.get("documents", {}).items():
                    total_doc_size += doc_info.get("file_size_bytes", 0)
                metrics["total_document_size_mb"] = round(total_doc_size / (1024 * 1024), 2)
        except Exception as e:
            logger.error(f"Failed to get total document size: {e}")
        
        # Get disk usage
        try:
            disk_usage = psutil.disk_usage('/')
            metrics["available_disk_gb"] = round(disk_usage.free / (1024 * 1024 * 1024), 2)
            metrics["disk_usage_percent"] = round(disk_usage.percent, 2)
        except Exception as e:
            logger.error(f"Failed to get disk usage: {e}")
        
        # Calculate growth rate (7 days)
        # This is a simplified calculation - in production, you'd track historical data
        try:
            # For now, return 0 as we don't have historical tracking yet
            metrics["growth_rate_7d_percent"] = 0.0
        except Exception as e:
            logger.error(f"Failed to calculate growth rate: {e}")
        
        return metrics
    
    def get_api_usage_metrics(self, hours: int = 24) -> Dict[str, Any]:
        """
        Get API usage metrics for the specified time period.
        
        Args:
            hours: Number of hours to look back (default 24)
        
        Returns:
            Dictionary containing:
                - total_requests: Total requests in time period
                - success_count: Number of successful requests (2xx)
                - error_count: Number of failed requests (4xx, 5xx)
                - endpoints: List of metrics by endpoint
                - slowest_requests: Top 5 slowest requests
                - hourly_rate: Request rate per hour
        """
        metrics = {
            "total_requests": 0,
            "success_count": 0,
            "error_count": 0,
            "endpoints": [],
            "slowest_requests": [],
            "hourly_rate": []
        }
        
        try:
            cutoff = datetime.now() - timedelta(hours=hours)
            
            # Total requests
            total_requests = self.api_metrics_collection.count_documents({
                "timestamp": {"$gte": cutoff}
            })
            metrics["total_requests"] = total_requests
            
            # Success and error counts
            success_count = self.api_metrics_collection.count_documents({
                "timestamp": {"$gte": cutoff},
                "status_code": {"$gte": 200, "$lt": 300}
            })
            error_count = self.api_metrics_collection.count_documents({
                "timestamp": {"$gte": cutoff},
                "status_code": {"$gte": 400}
            })
            metrics["success_count"] = success_count
            metrics["error_count"] = error_count
            
            # Metrics by endpoint
            pipeline = [
                {"$match": {"timestamp": {"$gte": cutoff}}},
                {"$group": {
                    "_id": "$endpoint",
                    "total_requests": {"$sum": 1},
                    "success_count": {
                        "$sum": {
                            "$cond": [
                                {"$and": [
                                    {"$gte": ["$status_code", 200]},
                                    {"$lt": ["$status_code", 300]}
                                ]},
                                1,
                                0
                            ]
                        }
                    },
                    "error_count": {
                        "$sum": {
                            "$cond": [
                                {"$gte": ["$status_code", 400]},
                                1,
                                0
                            ]
                        }
                    },
                    "avg_response_time": {"$avg": "$response_time_ms"}
                }},
                {"$sort": {"total_requests": -1}}
            ]
            endpoint_metrics = list(self.api_metrics_collection.aggregate(pipeline))
            
            metrics["endpoints"] = [
                {
                    "endpoint": em["_id"],
                    "total_requests": em["total_requests"],
                    "success_count": em["success_count"],
                    "error_count": em["error_count"],
                    "avg_response_time_ms": round(em["avg_response_time"], 2)
                }
                for em in endpoint_metrics
            ]
            
            # Top 5 slowest requests
            slowest = list(self.api_metrics_collection.find(
                {"timestamp": {"$gte": cutoff}},
                {"endpoint": 1, "response_time_ms": 1, "timestamp": 1, "status_code": 1}
            ).sort("response_time_ms", -1).limit(5))
            
            metrics["slowest_requests"] = [
                {
                    "endpoint": req["endpoint"],
                    "response_time_ms": round(req["response_time_ms"], 2),
                    "timestamp": req["timestamp"].isoformat(),
                    "status_code": req["status_code"]
                }
                for req in slowest
            ]
            
            # Hourly request rate
            pipeline = [
                {"$match": {"timestamp": {"$gte": cutoff}}},
                {"$group": {
                    "_id": {
                        "$dateToString": {
                            "format": "%Y-%m-%dT%H:00:00Z",
                            "date": "$timestamp"
                        }
                    },
                    "request_count": {"$sum": 1}
                }},
                {"$sort": {"_id": 1}}
            ]
            hourly_data = list(self.api_metrics_collection.aggregate(pipeline))
            
            metrics["hourly_rate"] = [
                {
                    "hour": hd["_id"],
                    "request_count": hd["request_count"]
                }
                for hd in hourly_data
            ]
            
        except Exception as e:
            logger.error(f"Failed to get API usage metrics: {e}")
        
        return metrics
    
    def get_error_logs(
        self,
        severity: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        page: int = 1,
        page_size: int = 50
    ) -> Dict[str, Any]:
        """
        Get error logs with filtering and pagination.
        
        Args:
            severity: Filter by severity (INFO/WARNING/ERROR/CRITICAL)
            start_date: Start date for filtering
            end_date: End date for filtering
            page: Page number (1-indexed)
            page_size: Number of records per page
        
        Returns:
            Dictionary containing:
                - logs: List of error log entries
                - total: Total number of matching logs
                - page: Current page number
                - page_size: Records per page
                - total_pages: Total number of pages
        """
        try:
            # Build query filter
            query_filter = {}
            
            if severity:
                query_filter["severity"] = severity.upper()
            
            if start_date or end_date:
                query_filter["timestamp"] = {}
                if start_date:
                    query_filter["timestamp"]["$gte"] = start_date
                if end_date:
                    query_filter["timestamp"]["$lte"] = end_date
            
            # Get total count
            total = self.api_metrics_collection.count_documents(
                {**query_filter, "error_message": {"$exists": True}}
            )
            
            # Calculate pagination
            skip = (page - 1) * page_size
            total_pages = (total + page_size - 1) // page_size
            
            # Get logs
            logs_cursor = self.api_metrics_collection.find(
                {**query_filter, "error_message": {"$exists": True}},
                {
                    "_id": 1,
                    "timestamp": 1,
                    "endpoint": 1,
                    "status_code": 1,
                    "error_message": 1,
                    "user_id": 1
                }
            ).sort("timestamp", -1).skip(skip).limit(page_size)
            
            logs = []
            for log in logs_cursor:
                # Determine severity based on status code
                status_code = log.get("status_code", 500)
                if status_code >= 500:
                    log_severity = "ERROR"
                elif status_code >= 400:
                    log_severity = "WARNING"
                else:
                    log_severity = "INFO"
                
                logs.append({
                    "log_id": str(log["_id"]),
                    "timestamp": log["timestamp"].isoformat(),
                    "severity": log_severity,
                    "error_type": f"HTTP{status_code}Error",
                    "error_message": log.get("error_message", "Unknown error"),
                    "endpoint": log.get("endpoint"),
                    "stack_trace": None,
                    "user_id": log.get("user_id")
                })
            
            return {
                "logs": logs,
                "total": total,
                "page": page,
                "page_size": page_size,
                "total_pages": total_pages
            }
            
        except Exception as e:
            logger.error(f"Failed to get error logs: {e}")
            return {
                "logs": [],
                "total": 0,
                "page": page,
                "page_size": page_size,
                "total_pages": 0
            }