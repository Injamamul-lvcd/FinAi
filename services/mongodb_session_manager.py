"""
MongoDB Session Manager for conversation history.

This module provides the MongoDBSessionManager class for managing conversation sessions
and message history using MongoDB database.
"""

import uuid
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from pymongo import MongoClient, ASCENDING, DESCENDING
from pymongo.errors import ConnectionFailure, OperationFailure
import logging

logger = logging.getLogger(__name__)


class MongoDBSessionManager:
    """
    Manages conversation sessions and message history using MongoDB.
    
    Stores user queries and assistant responses in MongoDB database,
    retrieves conversation history, and handles session lifecycle.
    """
    
    def __init__(
        self, 
        connection_string: str = "mongodb://localhost:27017/",
        database_name: str = "financial_chatbot",
        max_turns: int = 20
    ):
        """
        Initialize the MongoDBSessionManager.
        
        Args:
            connection_string: MongoDB connection string
            database_name: Name of the database to use
            max_turns: Maximum number of conversation turns to keep in history
        """
        self.connection_string = connection_string
        self.database_name = database_name
        self.max_turns = max_turns
        
        try:
            # Initialize MongoDB client
            self.client = MongoClient(connection_string, serverSelectionTimeoutMS=5000)
            
            # Test connection
            self.client.admin.command('ping')
            logger.info(f"Successfully connected to MongoDB at {connection_string}")
            
            # Get database and collections
            self.db = self.client[database_name]
            self.sessions_collection = self.db['sessions']
            self.messages_collection = self.db['messages']
            
            # Create indexes for better performance
            self._create_indexes()
            
        except ConnectionFailure as e:
            logger.error(f"Failed to connect to MongoDB: {e}")
            raise
        except Exception as e:
            logger.error(f"Error initializing MongoDB session manager: {e}")
            raise
    
    def _create_indexes(self):
        """Create database indexes for better query performance."""
        try:
            # Index on session_id for messages
            self.messages_collection.create_index([("session_id", ASCENDING)])
            
            # Index on timestamp for messages (for ordering)
            self.messages_collection.create_index([("timestamp", DESCENDING)])
            
            # Index on last_activity for sessions (for cleanup)
            self.sessions_collection.create_index([("last_activity", DESCENDING)])
            
            # Compound index for efficient message queries
            self.messages_collection.create_index([
                ("session_id", ASCENDING),
                ("timestamp", DESCENDING)
            ])
            
            logger.info("MongoDB indexes created successfully")
            
        except Exception as e:
            logger.warning(f"Error creating indexes: {e}")
    
    def create_session(self, user_id: Optional[str] = None) -> str:
        """
        Create a new conversation session.
        
        Args:
            user_id: Optional user ID to associate with the session
        
        Returns:
            str: Unique session identifier (UUID)
        """
        session_id = str(uuid.uuid4())
        
        session_doc = {
            "_id": session_id,
            "session_id": session_id,
            "user_id": user_id,
            "created_at": datetime.utcnow(),
            "last_activity": datetime.utcnow()
        }
        
        try:
            self.sessions_collection.insert_one(session_doc)
            logger.info(f"Created new session: {session_id}")
            return session_id
            
        except Exception as e:
            logger.error(f"Error creating session: {e}")
            raise
    
    def add_message(self, session_id: str, role: str, content: str) -> bool:
        """
        Add a message to the conversation history.
        
        Args:
            session_id: Session identifier
            role: Message role ('user' or 'assistant')
            content: Message content
            
        Returns:
            bool: True if message was added successfully, False otherwise
        """
        if role not in ['user', 'assistant']:
            raise ValueError(f"Invalid role: {role}. Must be 'user' or 'assistant'")
        
        try:
            # Check if session exists
            session = self.sessions_collection.find_one({"session_id": session_id})
            if not session:
                logger.warning(f"Session not found: {session_id}")
                return False
            
            # Add message
            message_doc = {
                "session_id": session_id,
                "role": role,
                "content": content,
                "timestamp": datetime.utcnow()
            }
            
            self.messages_collection.insert_one(message_doc)
            
            # Update session last_activity
            self.sessions_collection.update_one(
                {"session_id": session_id},
                {"$set": {"last_activity": datetime.utcnow()}}
            )
            
            logger.debug(f"Added {role} message to session {session_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error adding message: {e}")
            return False
    
    def get_history(self, session_id: str, limit: Optional[int] = None) -> List[Dict[str, str]]:
        """
        Retrieve conversation history for a session.
        
        Returns the most recent conversation turns, limited by max_turns or the provided limit.
        
        Args:
            session_id: Session identifier
            limit: Maximum number of turns to retrieve (defaults to max_turns)
            
        Returns:
            List[Dict[str, str]]: List of messages with 'role' and 'content' keys,
                                  ordered from oldest to newest
        """
        if limit is None:
            limit = self.max_turns
        
        try:
            # Get most recent messages (limit * 2 for user + assistant pairs)
            messages = self.messages_collection.find(
                {"session_id": session_id}
            ).sort("timestamp", DESCENDING).limit(limit * 2)
            
            # Convert to list and reverse to get chronological order
            messages_list = [
                {
                    'role': msg['role'],
                    'content': msg['content']
                }
                for msg in reversed(list(messages))
            ]
            
            return messages_list
            
        except Exception as e:
            logger.error(f"Error retrieving history: {e}")
            return []
    
    def session_exists(self, session_id: str) -> bool:
        """
        Check if a session exists.
        
        Args:
            session_id: Session identifier
            
        Returns:
            bool: True if session exists, False otherwise
        """
        try:
            return self.sessions_collection.find_one({"session_id": session_id}) is not None
        except Exception as e:
            logger.error(f"Error checking session existence: {e}")
            return False
    
    def cleanup_old_sessions(self, days: int = 30) -> int:
        """
        Delete sessions older than specified days.
        
        Args:
            days: Number of days of inactivity before deletion
            
        Returns:
            int: Number of sessions deleted
        """
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        
        try:
            # Find sessions to delete
            old_sessions = self.sessions_collection.find(
                {"last_activity": {"$lt": cutoff_date}}
            )
            
            session_ids = [session['session_id'] for session in old_sessions]
            
            if not session_ids:
                return 0
            
            # Delete messages for these sessions
            self.messages_collection.delete_many(
                {"session_id": {"$in": session_ids}}
            )
            
            # Delete sessions
            result = self.sessions_collection.delete_many(
                {"last_activity": {"$lt": cutoff_date}}
            )
            
            count = result.deleted_count
            logger.info(f"Cleaned up {count} old sessions")
            return count
            
        except Exception as e:
            logger.error(f"Error cleaning up old sessions: {e}")
            return 0
    
    def get_session_stats(self, session_id: str) -> Optional[Dict]:
        """
        Get statistics for a session.
        
        Args:
            session_id: Session identifier
            
        Returns:
            Optional[Dict]: Dictionary with session stats or None if session doesn't exist
        """
        try:
            # Get session info
            session = self.sessions_collection.find_one({"session_id": session_id})
            
            if not session:
                return None
            
            # Get message count
            message_count = self.messages_collection.count_documents(
                {"session_id": session_id}
            )
            
            return {
                'session_id': session_id,
                'user_id': session.get('user_id'),
                'created_at': session['created_at'].isoformat(),
                'last_activity': session['last_activity'].isoformat(),
                'message_count': message_count,
                'turn_count': message_count // 2
            }
            
        except Exception as e:
            logger.error(f"Error getting session stats: {e}")
            return None
    
    def delete_session(self, session_id: str) -> bool:
        """
        Delete a session and all its messages.
        
        Args:
            session_id: Session identifier
            
        Returns:
            bool: True if session was deleted, False if session didn't exist
        """
        try:
            # Delete messages
            self.messages_collection.delete_many({"session_id": session_id})
            
            # Delete session
            result = self.sessions_collection.delete_one({"session_id": session_id})
            
            deleted = result.deleted_count > 0
            if deleted:
                logger.info(f"Deleted session: {session_id}")
            
            return deleted
            
        except Exception as e:
            logger.error(f"Error deleting session: {e}")
            return False
    
    def get_user_sessions(self, user_id: str, limit: int = 10) -> List[Dict]:
        """
        Get all sessions for a specific user.
        
        Args:
            user_id: User identifier
            limit: Maximum number of sessions to return
            
        Returns:
            List[Dict]: List of session information
        """
        try:
            sessions = self.sessions_collection.find(
                {"user_id": user_id}
            ).sort("last_activity", DESCENDING).limit(limit)
            
            return [
                {
                    'session_id': session['session_id'],
                    'created_at': session['created_at'].isoformat(),
                    'last_activity': session['last_activity'].isoformat()
                }
                for session in sessions
            ]
            
        except Exception as e:
            logger.error(f"Error getting user sessions: {e}")
            return []
    
    def close(self):
        """Close the MongoDB connection."""
        try:
            self.client.close()
            logger.info("MongoDB connection closed")
        except Exception as e:
            logger.error(f"Error closing MongoDB connection: {e}")
