"""
Activity Logger service for admin action tracking and audit trail.

This module provides the ActivityLogger class for recording and retrieving
administrative actions with MongoDB database integration.
"""

import logging
from datetime import datetime
from typing import Optional, Dict, List
from pymongo import MongoClient, ASCENDING, DESCENDING
from pymongo.errors import ConnectionFailure

logger = logging.getLogger(__name__)


class ActivityLogger:
    """
    Logs administrative actions for audit trail and compliance.
    
    Records admin actions with timestamp, admin_id, action_type, resource details,
    and IP address. Provides filtering and pagination for activity log retrieval.
    """
    
    def __init__(
        self,
        connection_string: str = "mongodb://localhost:27017/",
        database_name: str = "financial_chatbot"
    ):
        """
        Initialize the ActivityLogger.
        
        Args:
            connection_string: MongoDB connection string
            database_name: Name of the database to use
        """
        self.connection_string = connection_string
        self.database_name = database_name
        
        try:
            # Initialize MongoDB client
            self.client = MongoClient(connection_string, serverSelectionTimeoutMS=5000)
            
            # Test connection
            self.client.admin.command('ping')
            logger.info(f"ActivityLogger connected to MongoDB at {connection_string}")
            
            # Get database and collection
            self.db = self.client[database_name]
            self.activity_logs_collection = self.db['activity_logs']
            
            # Create indexes for better performance
            self._create_indexes()
            
        except ConnectionFailure as e:
            logger.error(f"Failed to connect to MongoDB: {e}")
            raise
        except Exception as e:
            logger.error(f"Error initializing ActivityLogger: {e}")
            raise
    
    def _create_indexes(self):
        """Create database indexes for better query performance."""
        try:
            # Index on admin_id for filtering by admin
            self.activity_logs_collection.create_index([("admin_id", ASCENDING)])
            
            # Index on timestamp for ordering and date range queries
            self.activity_logs_collection.create_index([("timestamp", DESCENDING)])
            
            # Index on resource_type and resource_id for resource-specific queries
            self.activity_logs_collection.create_index([("resource_type", ASCENDING)])
            self.activity_logs_collection.create_index([("resource_id", ASCENDING)])
            
            # Compound index for efficient filtering
            self.activity_logs_collection.create_index([
                ("admin_id", ASCENDING),
                ("timestamp", DESCENDING)
            ])
            
            # Compound index for resource queries
            self.activity_logs_collection.create_index([
                ("resource_type", ASCENDING),
                ("resource_id", ASCENDING),
                ("timestamp", DESCENDING)
            ])
            
            # Index on action_type for filtering
            self.activity_logs_collection.create_index([("action_type", ASCENDING)])
            
            logger.info("ActivityLogger indexes created successfully")
            
        except Exception as e:
            logger.warning(f"Error creating ActivityLogger indexes: {e}")
    
    def log_action(
        self,
        admin_id: str,
        action_type: str,
        resource_type: str,
        resource_id: str,
        details: Optional[Dict] = None,
        ip_address: Optional[str] = None,
        admin_username: Optional[str] = None,
        result: str = "success"
    ) -> bool:
        """
        Record an admin action to the activity log.
        
        Args:
            admin_id: User ID of the admin performing the action
            action_type: Type of action (e.g., "user_disabled", "document_deleted")
            resource_type: Type of resource affected (e.g., "user", "document", "config")
            resource_id: ID of the affected resource
            details: Optional dictionary with additional action-specific details
            ip_address: Optional IP address of the admin
            admin_username: Optional username of the admin
            result: Result of the action ("success" or "failure")
            
        Returns:
            bool: True if log entry was created successfully, False otherwise
        """
        try:
            log_entry = {
                "admin_id": admin_id,
                "admin_username": admin_username or "unknown",
                "action_type": action_type,
                "resource_type": resource_type,
                "resource_id": resource_id,
                "details": details or {},
                "ip_address": ip_address,
                "timestamp": datetime.utcnow(),
                "result": result
            }
            
            self.activity_logs_collection.insert_one(log_entry)
            
            logger.info(
                f"Activity logged: {action_type} on {resource_type}:{resource_id} "
                f"by admin {admin_id} - {result}"
            )
            return True
            
        except Exception as e:
            logger.error(f"Error logging activity: {e}")
            return False

    def get_activity_logs(
        self,
        user_id: Optional[str] = None,
        action_type: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        page: int = 1,
        page_size: int = 50
    ) -> Dict:
        """
        Retrieve activity logs with filtering and pagination.
        
        Args:
            user_id: Optional filter by admin user ID
            action_type: Optional filter by action type
            start_date: Optional filter by start date (inclusive)
            end_date: Optional filter by end date (inclusive)
            page: Page number (1-indexed)
            page_size: Number of records per page (10-100)
            
        Returns:
            Dict: Dictionary containing:
                - logs: List of activity log entries
                - total: Total number of matching logs
                - page: Current page number
                - page_size: Records per page
                - total_pages: Total number of pages
        """
        try:
            # Validate page_size
            if page_size < 10:
                page_size = 10
            elif page_size > 100:
                page_size = 100
            
            # Validate page
            if page < 1:
                page = 1
            
            # Build query filter
            query_filter = {}
            
            if user_id:
                query_filter["admin_id"] = user_id
            
            if action_type:
                query_filter["action_type"] = action_type
            
            # Date range filter
            if start_date or end_date:
                date_filter = {}
                if start_date:
                    date_filter["$gte"] = start_date
                if end_date:
                    date_filter["$lte"] = end_date
                query_filter["timestamp"] = date_filter
            
            # Get total count
            total = self.activity_logs_collection.count_documents(query_filter)
            
            # Calculate pagination
            skip = (page - 1) * page_size
            total_pages = (total + page_size - 1) // page_size  # Ceiling division
            
            # Get logs with pagination
            logs_cursor = self.activity_logs_collection.find(
                query_filter
            ).sort("timestamp", DESCENDING).skip(skip).limit(page_size)
            
            # Convert to list and format
            logs = []
            for log in logs_cursor:
                log_entry = {
                    "log_id": str(log["_id"]),
                    "admin_id": log["admin_id"],
                    "admin_username": log.get("admin_username", "unknown"),
                    "action_type": log["action_type"],
                    "resource_type": log["resource_type"],
                    "resource_id": log["resource_id"],
                    "details": log.get("details", {}),
                    "ip_address": log.get("ip_address"),
                    "timestamp": log["timestamp"].isoformat(),
                    "result": log.get("result", "success")
                }
                logs.append(log_entry)
            
            return {
                "logs": logs,
                "total": total,
                "page": page,
                "page_size": page_size,
                "total_pages": total_pages
            }
            
        except Exception as e:
            logger.error(f"Error retrieving activity logs: {e}")
            return {
                "logs": [],
                "total": 0,
                "page": page,
                "page_size": page_size,
                "total_pages": 0
            }
    
    def get_logs_by_resource(
        self,
        resource_type: str,
        resource_id: str,
        page: int = 1,
        page_size: int = 50
    ) -> Dict:
        """
        Retrieve activity logs for a specific resource.
        
        Args:
            resource_type: Type of resource (e.g., "user", "document")
            resource_id: ID of the resource
            page: Page number (1-indexed)
            page_size: Number of records per page (10-100)
            
        Returns:
            Dict: Dictionary containing logs and pagination info
        """
        try:
            # Validate page_size
            if page_size < 10:
                page_size = 10
            elif page_size > 100:
                page_size = 100
            
            # Validate page
            if page < 1:
                page = 1
            
            # Build query filter
            query_filter = {
                "resource_type": resource_type,
                "resource_id": resource_id
            }
            
            # Get total count
            total = self.activity_logs_collection.count_documents(query_filter)
            
            # Calculate pagination
            skip = (page - 1) * page_size
            total_pages = (total + page_size - 1) // page_size
            
            # Get logs with pagination
            logs_cursor = self.activity_logs_collection.find(
                query_filter
            ).sort("timestamp", DESCENDING).skip(skip).limit(page_size)
            
            # Convert to list and format
            logs = []
            for log in logs_cursor:
                log_entry = {
                    "log_id": str(log["_id"]),
                    "admin_id": log["admin_id"],
                    "admin_username": log.get("admin_username", "unknown"),
                    "action_type": log["action_type"],
                    "resource_type": log["resource_type"],
                    "resource_id": log["resource_id"],
                    "details": log.get("details", {}),
                    "ip_address": log.get("ip_address"),
                    "timestamp": log["timestamp"].isoformat(),
                    "result": log.get("result", "success")
                }
                logs.append(log_entry)
            
            return {
                "logs": logs,
                "total": total,
                "page": page,
                "page_size": page_size,
                "total_pages": total_pages
            }
            
        except Exception as e:
            logger.error(f"Error retrieving resource activity logs: {e}")
            return {
                "logs": [],
                "total": 0,
                "page": page,
                "page_size": page_size,
                "total_pages": 0
            }
    
    def get_recent_logs(self, limit: int = 100) -> List[Dict]:
        """
        Get the most recent activity logs.
        
        Args:
            limit: Maximum number of logs to retrieve (default: 100)
            
        Returns:
            List[Dict]: List of recent activity log entries
        """
        try:
            logs_cursor = self.activity_logs_collection.find().sort(
                "timestamp", DESCENDING
            ).limit(limit)
            
            logs = []
            for log in logs_cursor:
                log_entry = {
                    "log_id": str(log["_id"]),
                    "admin_id": log["admin_id"],
                    "admin_username": log.get("admin_username", "unknown"),
                    "action_type": log["action_type"],
                    "resource_type": log["resource_type"],
                    "resource_id": log["resource_id"],
                    "details": log.get("details", {}),
                    "ip_address": log.get("ip_address"),
                    "timestamp": log["timestamp"].isoformat(),
                    "result": log.get("result", "success")
                }
                logs.append(log_entry)
            
            return logs
            
        except Exception as e:
            logger.error(f"Error retrieving recent logs: {e}")
            return []
    
    def get_admin_activity_summary(self, admin_id: str) -> Dict:
        """
        Get activity summary for a specific admin.
        
        Args:
            admin_id: Admin user ID
            
        Returns:
            Dict: Summary statistics including total actions, action type breakdown
        """
        try:
            # Get total actions
            total_actions = self.activity_logs_collection.count_documents(
                {"admin_id": admin_id}
            )
            
            # Get action type breakdown using aggregation
            pipeline = [
                {"$match": {"admin_id": admin_id}},
                {"$group": {
                    "_id": "$action_type",
                    "count": {"$sum": 1}
                }},
                {"$sort": {"count": -1}}
            ]
            
            action_breakdown = list(self.activity_logs_collection.aggregate(pipeline))
            
            # Get most recent action
            recent_log = self.activity_logs_collection.find_one(
                {"admin_id": admin_id},
                sort=[("timestamp", DESCENDING)]
            )
            
            last_activity = None
            if recent_log:
                last_activity = recent_log["timestamp"].isoformat()
            
            return {
                "admin_id": admin_id,
                "total_actions": total_actions,
                "action_breakdown": [
                    {"action_type": item["_id"], "count": item["count"]}
                    for item in action_breakdown
                ],
                "last_activity": last_activity
            }
            
        except Exception as e:
            logger.error(f"Error getting admin activity summary: {e}")
            return {
                "admin_id": admin_id,
                "total_actions": 0,
                "action_breakdown": [],
                "last_activity": None
            }
    
    def close(self):
        """Close the MongoDB connection."""
        try:
            self.client.close()
            logger.info("ActivityLogger MongoDB connection closed")
        except Exception as e:
            logger.error(f"Error closing MongoDB connection: {e}")
