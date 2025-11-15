"""
Admin User Service for user management operations.

This module provides the AdminUserService class for administrative user management,
including listing users, updating status, resetting passwords, and retrieving activity logs.
"""

import logging
import secrets
import string
from datetime import datetime
from typing import Optional, Dict, List
from pymongo import MongoClient, ASCENDING, DESCENDING
from pymongo.errors import ConnectionFailure
from bson import ObjectId

logger = logging.getLogger(__name__)


class AdminUserService:
    """
    Handles administrative user management operations.
    
    Provides methods for listing users with pagination and filtering,
    retrieving user details, updating account status, resetting passwords,
    and retrieving user activity logs.
    """
    
    def __init__(
        self,
        connection_string: str = "mongodb://localhost:27017/",
        database_name: str = "financial_chatbot"
    ):
        """
        Initialize the AdminUserService.
        
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
            logger.info(f"AdminUserService connected to MongoDB at {connection_string}")
            
            # Get database and collections
            self.db = self.client[database_name]
            self.users_collection = self.db['users']
            
            # Create indexes for better performance
            self._create_indexes()
            
        except ConnectionFailure as e:
            logger.error(f"Failed to connect to MongoDB: {e}")
            raise
        except Exception as e:
            logger.error(f"Error initializing AdminUserService: {e}")
            raise
    
    def _create_indexes(self):
        """Create database indexes for better query performance."""
        try:
            # Indexes for user queries
            self.users_collection.create_index([("username", ASCENDING)])
            self.users_collection.create_index([("email", ASCENDING)])
            self.users_collection.create_index([("is_admin", ASCENDING)])
            self.users_collection.create_index([("created_at", DESCENDING)])
            self.users_collection.create_index([("last_login", DESCENDING)])
            
            logger.info("AdminUserService indexes created successfully")
            
        except Exception as e:
            logger.warning(f"Error creating AdminUserService indexes: {e}")
    
    def get_users(
        self,
        page: int = 1,
        page_size: int = 50,
        search: Optional[str] = None,
        sort_by: str = "created_at",
        sort_order: str = "desc"
    ) -> Dict:
        """
        Get list of users with pagination, search, and sorting.
        
        Args:
            page: Page number (1-indexed)
            page_size: Number of records per page (10-100)
            search: Optional search string for username/email (case-insensitive)
            sort_by: Field to sort by (created_at, last_login, username)
            sort_order: Sort order (asc or desc)
            
        Returns:
            Dict: Dictionary containing:
                - users: List of user records
                - total: Total number of matching users
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
            
            if search:
                # Case-insensitive search on username or email
                query_filter["$or"] = [
                    {"username": {"$regex": search, "$options": "i"}},
                    {"email": {"$regex": search, "$options": "i"}}
                ]
            
            # Validate sort_by field
            valid_sort_fields = ["created_at", "last_login", "username"]
            if sort_by not in valid_sort_fields:
                sort_by = "created_at"
            
            # Determine sort direction
            sort_direction = DESCENDING if sort_order == "desc" else ASCENDING
            
            # Get total count
            total = self.users_collection.count_documents(query_filter)
            
            # Calculate pagination
            skip = (page - 1) * page_size
            total_pages = (total + page_size - 1) // page_size  # Ceiling division
            
            # Get users with pagination
            users_cursor = self.users_collection.find(
                query_filter
            ).sort(sort_by, sort_direction).skip(skip).limit(page_size)
            
            # Convert to list and format
            users = []
            for user in users_cursor:
                user_data = {
                    "user_id": str(user["_id"]),
                    "username": user["username"],
                    "email": user["email"],
                    "full_name": user.get("full_name"),
                    "is_active": user.get("is_active", True),
                    "is_admin": user.get("is_admin", False),
                    "created_at": user["created_at"].isoformat() if user.get("created_at") else None,
                    "last_login": user["last_login"].isoformat() if user.get("last_login") else None
                }
                users.append(user_data)
            
            return {
                "users": users,
                "total": total,
                "page": page,
                "page_size": page_size,
                "total_pages": total_pages
            }
            
        except Exception as e:
            logger.error(f"Error retrieving users: {e}")
            return {
                "users": [],
                "total": 0,
                "page": page,
                "page_size": page_size,
                "total_pages": 0
            }

    def get_user_details(self, user_id: str) -> Optional[Dict]:
        """
        Get complete user information including document count and query count.
        
        Args:
            user_id: User ID to retrieve details for
            
        Returns:
            Optional[Dict]: User details with document and query counts, or None if not found
        """
        try:
            # Validate and convert user_id to ObjectId
            try:
                user_obj_id = ObjectId(user_id)
            except Exception:
                logger.warning(f"Invalid user_id format: {user_id}")
                return None
            
            # Get user from database
            user = self.users_collection.find_one({"_id": user_obj_id})
            
            if not user:
                logger.warning(f"User not found: {user_id}")
                return None
            
            # Get document count from ChromaDB metadata
            # We'll query the vector store to count documents uploaded by this user
            document_count = 0
            query_count = 0
            
            try:
                # Import here to avoid circular dependency
                from services.vector_store import VectorStoreManager
                from config.settings import get_settings
                
                settings = get_settings()
                vector_store = VectorStoreManager(
                    persist_directory=settings.chroma_persist_dir,
                    collection_name=settings.chroma_collection_name
                )
                
                # Get all documents and filter by user_id
                all_items = vector_store.collection.get()
                
                # Track unique documents for this user
                user_documents = set()
                
                for metadata in all_items['metadatas']:
                    if metadata.get('user_id') == user_id:
                        doc_id = metadata.get('document_id')
                        if doc_id:
                            user_documents.add(doc_id)
                        # Count queries if metadata has query_count
                        query_count += metadata.get('query_count', 0)
                
                document_count = len(user_documents)
                
            except Exception as e:
                logger.warning(f"Error getting document/query counts for user {user_id}: {e}")
            
            # Format user details
            user_details = {
                "user_id": str(user["_id"]),
                "username": user["username"],
                "email": user["email"],
                "full_name": user.get("full_name"),
                "is_active": user.get("is_active", True),
                "is_admin": user.get("is_admin", False),
                "password_reset_required": user.get("password_reset_required", False),
                "created_at": user["created_at"].isoformat() if user.get("created_at") else None,
                "updated_at": user["updated_at"].isoformat() if user.get("updated_at") else None,
                "last_login": user["last_login"].isoformat() if user.get("last_login") else None,
                "document_count": document_count,
                "query_count": query_count
            }
            
            return user_details
            
        except Exception as e:
            logger.error(f"Error retrieving user details for {user_id}: {e}")
            return None
    
    def update_user_status(
        self,
        user_id: str,
        is_active: bool,
        admin_id: str,
        reason: Optional[str] = None
    ) -> bool:
        """
        Enable or disable a user account with activity logging.
        
        Args:
            user_id: User ID to update
            is_active: New active status (True to enable, False to disable)
            admin_id: Admin user ID performing the action
            reason: Optional reason for status change
            
        Returns:
            bool: True if update successful, False otherwise
        """
        try:
            # Validate and convert user_id to ObjectId
            try:
                user_obj_id = ObjectId(user_id)
            except Exception:
                logger.warning(f"Invalid user_id format: {user_id}")
                return False
            
            # Check if user exists
            user = self.users_collection.find_one({"_id": user_obj_id})
            if not user:
                logger.warning(f"User not found: {user_id}")
                return False
            
            # Update user status
            result = self.users_collection.update_one(
                {"_id": user_obj_id},
                {
                    "$set": {
                        "is_active": is_active,
                        "updated_at": datetime.utcnow()
                    }
                }
            )
            
            if result.modified_count > 0:
                # Log the activity
                try:
                    from services.activity_logger import ActivityLogger
                    
                    activity_logger = ActivityLogger(
                        connection_string=self.connection_string,
                        database_name=self.database_name
                    )
                    
                    action_type = "user_enabled" if is_active else "user_disabled"
                    
                    activity_logger.log_action(
                        admin_id=admin_id,
                        action_type=action_type,
                        resource_type="user",
                        resource_id=user_id,
                        details={
                            "username": user["username"],
                            "reason": reason,
                            "previous_status": user.get("is_active", True),
                            "new_status": is_active
                        },
                        result="success"
                    )
                    
                    activity_logger.close()
                    
                except Exception as e:
                    logger.warning(f"Error logging activity: {e}")
                
                logger.info(f"User {user_id} status updated to {'active' if is_active else 'inactive'}")
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Error updating user status for {user_id}: {e}")
            return False
    
    def reset_user_password(
        self,
        user_id: str,
        admin_id: str
    ) -> Optional[str]:
        """
        Generate secure temporary password and reset user password.
        
        Generates a 12-character password with mixed character types
        (uppercase, lowercase, numbers, special characters).
        
        Args:
            user_id: User ID to reset password for
            admin_id: Admin user ID performing the action
            
        Returns:
            Optional[str]: Temporary password if successful, None otherwise
        """
        try:
            # Validate and convert user_id to ObjectId
            try:
                user_obj_id = ObjectId(user_id)
            except Exception:
                logger.warning(f"Invalid user_id format: {user_id}")
                return None
            
            # Check if user exists
            user = self.users_collection.find_one({"_id": user_obj_id})
            if not user:
                logger.warning(f"User not found: {user_id}")
                return None
            
            # Generate secure temporary password (12 characters)
            # Include uppercase, lowercase, numbers, and special characters
            uppercase = string.ascii_uppercase
            lowercase = string.ascii_lowercase
            digits = string.digits
            special = "!@#$%^&*"
            
            # Ensure at least one character from each category
            temp_password = [
                secrets.choice(uppercase),
                secrets.choice(lowercase),
                secrets.choice(digits),
                secrets.choice(special)
            ]
            
            # Fill remaining 8 characters randomly
            all_chars = uppercase + lowercase + digits + special
            temp_password.extend(secrets.choice(all_chars) for _ in range(8))
            
            # Shuffle to avoid predictable pattern
            secrets.SystemRandom().shuffle(temp_password)
            temp_password = ''.join(temp_password)
            
            # Hash the password
            from passlib.context import CryptContext
            pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
            hashed_password = pwd_context.hash(temp_password)
            
            # Update user with new password and set reset flag
            result = self.users_collection.update_one(
                {"_id": user_obj_id},
                {
                    "$set": {
                        "hashed_password": hashed_password,
                        "password_reset_required": True,
                        "updated_at": datetime.utcnow()
                    }
                }
            )
            
            if result.modified_count > 0:
                # Log the activity
                try:
                    from services.activity_logger import ActivityLogger
                    
                    activity_logger = ActivityLogger(
                        connection_string=self.connection_string,
                        database_name=self.database_name
                    )
                    
                    activity_logger.log_action(
                        admin_id=admin_id,
                        action_type="password_reset",
                        resource_type="user",
                        resource_id=user_id,
                        details={
                            "username": user["username"]
                        },
                        result="success"
                    )
                    
                    activity_logger.close()
                    
                except Exception as e:
                    logger.warning(f"Error logging activity: {e}")
                
                logger.info(f"Password reset for user {user_id}")
                return temp_password
            
            return None
            
        except Exception as e:
            logger.error(f"Error resetting password for user {user_id}: {e}")
            return None
    
    def get_user_activity(
        self,
        user_id: str,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        page: int = 1,
        page_size: int = 50
    ) -> Dict:
        """
        Retrieve activity logs for a specific user with date range filtering.
        
        Args:
            user_id: User ID to retrieve activity for
            start_date: Optional filter by start date (inclusive)
            end_date: Optional filter by end date (inclusive)
            page: Page number (1-indexed)
            page_size: Number of records per page (10-100)
            
        Returns:
            Dict: Dictionary containing activity logs and pagination info
        """
        try:
            # Import ActivityLogger
            from services.activity_logger import ActivityLogger
            
            activity_logger = ActivityLogger(
                connection_string=self.connection_string,
                database_name=self.database_name
            )
            
            # Get activity logs for this user (as resource)
            # This retrieves logs where actions were performed ON this user
            result = activity_logger.get_logs_by_resource(
                resource_type="user",
                resource_id=user_id,
                page=page,
                page_size=page_size
            )
            
            # If date filtering is needed, we need to filter the results
            if start_date or end_date:
                filtered_logs = []
                for log in result["logs"]:
                    log_timestamp = datetime.fromisoformat(log["timestamp"])
                    
                    # Check date range
                    if start_date and log_timestamp < start_date:
                        continue
                    if end_date and log_timestamp > end_date:
                        continue
                    
                    filtered_logs.append(log)
                
                result["logs"] = filtered_logs
                result["total"] = len(filtered_logs)
            
            activity_logger.close()
            
            return result
            
        except Exception as e:
            logger.error(f"Error retrieving user activity for {user_id}: {e}")
            return {
                "logs": [],
                "total": 0,
                "page": page,
                "page_size": page_size,
                "total_pages": 0
            }
    
    def close(self):
        """Close the MongoDB connection."""
        try:
            self.client.close()
            logger.info("AdminUserService MongoDB connection closed")
        except Exception as e:
            logger.error(f"Error closing MongoDB connection: {e}")
