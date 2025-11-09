"""
Session Manager for conversation history.

This module provides the SessionManager class for managing conversation sessions
and message history using SQLite database.
"""

import sqlite3
import uuid
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from contextlib import contextmanager
import os


class SessionManager:
    """
    Manages conversation sessions and message history.
    
    Stores user queries and assistant responses in SQLite database,
    retrieves conversation history, and handles session lifecycle.
    """
    
    def __init__(self, db_path: str, max_turns: int = 20):
        """
        Initialize the SessionManager.
        
        Args:
            db_path: Path to SQLite database file
            max_turns: Maximum number of conversation turns to keep in history
        """
        self.db_path = db_path
        self.max_turns = max_turns
        
        # Ensure parent directory exists
        parent_dir = os.path.dirname(db_path)
        if parent_dir and not os.path.exists(parent_dir):
            os.makedirs(parent_dir, exist_ok=True)
        
        # Initialize database schema
        self._init_db()
    
    def _init_db(self):
        """Create database tables if they don't exist."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            # Create sessions table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS sessions (
                    id TEXT PRIMARY KEY,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    last_activity TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Create messages table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS messages (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id TEXT NOT NULL,
                    role TEXT NOT NULL,
                    content TEXT NOT NULL,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (session_id) REFERENCES sessions(id) ON DELETE CASCADE
                )
            """)
            
            # Create index on session_id for faster queries
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_messages_session_id 
                ON messages(session_id)
            """)
            
            # Create index on timestamp for cleanup queries
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_sessions_last_activity 
                ON sessions(last_activity)
            """)
            
            conn.commit()
    
    @contextmanager
    def _get_connection(self):
        """
        Context manager for database connections.
        
        Yields:
            sqlite3.Connection: Database connection
        """
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row  # Enable column access by name
        try:
            yield conn
        finally:
            conn.close()
    
    def create_session(self) -> str:
        """
        Create a new conversation session.
        
        Returns:
            str: Unique session identifier (UUID)
        """
        session_id = str(uuid.uuid4())
        
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO sessions (id, created_at, last_activity) VALUES (?, ?, ?)",
                (session_id, datetime.now(), datetime.now())
            )
            conn.commit()
        
        return session_id
    
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
        
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            # Check if session exists
            cursor.execute("SELECT id FROM sessions WHERE id = ?", (session_id,))
            if not cursor.fetchone():
                return False
            
            # Add message
            cursor.execute(
                "INSERT INTO messages (session_id, role, content, timestamp) VALUES (?, ?, ?, ?)",
                (session_id, role, content, datetime.now())
            )
            
            # Update session last_activity
            cursor.execute(
                "UPDATE sessions SET last_activity = ? WHERE id = ?",
                (datetime.now(), session_id)
            )
            
            conn.commit()
        
        return True
    
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
        
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            # Get most recent messages, limited by turns
            # Each turn consists of a user message and assistant response
            # So we need to get limit * 2 messages
            cursor.execute("""
                SELECT role, content, timestamp
                FROM messages
                WHERE session_id = ?
                ORDER BY timestamp DESC
                LIMIT ?
            """, (session_id, limit * 2))
            
            rows = cursor.fetchall()
        
        # Reverse to get chronological order (oldest to newest)
        messages = [
            {
                'role': row['role'],
                'content': row['content']
            }
            for row in reversed(rows)
        ]
        
        return messages
    
    def session_exists(self, session_id: str) -> bool:
        """
        Check if a session exists.
        
        Args:
            session_id: Session identifier
            
        Returns:
            bool: True if session exists, False otherwise
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT id FROM sessions WHERE id = ?", (session_id,))
            return cursor.fetchone() is not None
    
    def cleanup_old_sessions(self, days: int = 30) -> int:
        """
        Delete sessions older than specified days.
        
        Args:
            days: Number of days of inactivity before deletion
            
        Returns:
            int: Number of sessions deleted
        """
        cutoff_date = datetime.now() - timedelta(days=days)
        
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            # Get count of sessions to be deleted
            cursor.execute(
                "SELECT COUNT(*) FROM sessions WHERE last_activity < ?",
                (cutoff_date,)
            )
            count = cursor.fetchone()[0]
            
            # Delete old sessions (messages will be deleted via CASCADE)
            cursor.execute(
                "DELETE FROM sessions WHERE last_activity < ?",
                (cutoff_date,)
            )
            
            conn.commit()
        
        return count
    
    def get_session_stats(self, session_id: str) -> Optional[Dict]:
        """
        Get statistics for a session.
        
        Args:
            session_id: Session identifier
            
        Returns:
            Optional[Dict]: Dictionary with session stats or None if session doesn't exist
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            # Get session info
            cursor.execute(
                "SELECT created_at, last_activity FROM sessions WHERE id = ?",
                (session_id,)
            )
            session_row = cursor.fetchone()
            
            if not session_row:
                return None
            
            # Get message count
            cursor.execute(
                "SELECT COUNT(*) FROM messages WHERE session_id = ?",
                (session_id,)
            )
            message_count = cursor.fetchone()[0]
        
        return {
            'session_id': session_id,
            'created_at': session_row['created_at'],
            'last_activity': session_row['last_activity'],
            'message_count': message_count,
            'turn_count': message_count // 2  # Approximate turns (user + assistant pairs)
        }
    
    def delete_session(self, session_id: str) -> bool:
        """
        Delete a session and all its messages.
        
        Args:
            session_id: Session identifier
            
        Returns:
            bool: True if session was deleted, False if session didn't exist
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM sessions WHERE id = ?", (session_id,))
            deleted = cursor.rowcount > 0
            conn.commit()
        
        return deleted
