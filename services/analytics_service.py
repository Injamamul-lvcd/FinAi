"""
Analytics Service for Admin Panel

This module provides analytics and reporting functionality for user engagement,
session analytics, document usage, and query topic analysis.
"""

import logging
from typing import Dict, List, Optional
from datetime import datetime, timedelta
from pymongo import MongoClient, DESCENDING
from collections import Counter
import re

logger = logging.getLogger(__name__)


class AnalyticsService:
    """
    Provides analytics and reporting functionality for the admin panel.
    
    Handles user engagement metrics, session analytics, document usage analytics,
    and query topic analysis.
    """
    
    def __init__(
        self,
        connection_string: str = "mongodb://localhost:27017/",
        database_name: str = "financial_chatbot"
    ):
        """
        Initialize the AnalyticsService.
        
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
            logger.info(f"AnalyticsService connected to MongoDB at {connection_string}")
            
            # Get database and collections
            self.db = self.client[database_name]
            self.users_collection = self.db['users']
            self.sessions_collection = self.db['sessions']
            self.messages_collection = self.db['messages']
            
        except Exception as e:
            logger.error(f"Failed to initialize AnalyticsService: {e}")
            raise
    
    def get_user_engagement_metrics(self, days: int = 30) -> Dict:
        """
        Get user engagement metrics for the specified time period.
        
        Calculates total users, active users, average queries per user,
        daily active users time series, top users, and retention rate.
        
        Args:
            days: Number of days to analyze (default 30)
            
        Returns:
            Dict containing:
                - total_users: Total registered users
                - active_users_30d: Users active in last 30 days
                - avg_queries_per_user: Average queries per active user
                - daily_active_users: Time series of daily active users
                - top_users: Top 10 most active users
                - retention_rate_percent: User retention rate
        """
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=days)
            previous_period_cutoff = cutoff_date - timedelta(days=days)
            
            # Total registered users
            total_users = self.users_collection.count_documents({})
            
            # Active users in last N days (users with sessions)
            active_user_ids = self.sessions_collection.distinct(
                "user_id",
                {"last_activity": {"$gte": cutoff_date}, "user_id": {"$ne": None}}
            )
            active_users_count = len(active_user_ids)
            
            # Calculate average queries per active user
            total_queries = 0
            if active_users_count > 0:
                # Count user messages in sessions
                total_queries = self.messages_collection.count_documents({
                    "role": "user",
                    "timestamp": {"$gte": cutoff_date}
                })
            
            avg_queries_per_user = round(total_queries / active_users_count, 2) if active_users_count > 0 else 0.0
            
            # Daily active users time series
            daily_active_users = self._get_daily_active_users(days)
            
            # Top 10 most active users
            top_users = self._get_top_users(days, limit=10)
            
            # Retention rate: users active in both current and previous period
            previous_period_active_users = set(self.sessions_collection.distinct(
                "user_id",
                {
                    "last_activity": {"$gte": previous_period_cutoff, "$lt": cutoff_date},
                    "user_id": {"$ne": None}
                }
            ))
            
            current_period_active_users = set(active_user_ids)
            
            retained_users = len(previous_period_active_users & current_period_active_users)
            retention_rate = round(
                (retained_users / len(previous_period_active_users) * 100) if previous_period_active_users else 0.0,
                2
            )
            
            return {
                "total_users": total_users,
                "active_users_30d": active_users_count,
                "avg_queries_per_user": avg_queries_per_user,
                "daily_active_users": daily_active_users,
                "top_users": top_users,
                "retention_rate_percent": retention_rate
            }
            
        except Exception as e:
            logger.error(f"Error getting user engagement metrics: {e}")
            raise
    
    def _get_daily_active_users(self, days: int) -> List[Dict]:
        """
        Get daily active user counts for the last N days.
        
        Args:
            days: Number of days to analyze
            
        Returns:
            List of dicts with 'date' and 'count' keys
        """
        try:
            daily_data = []
            
            for i in range(days):
                date = datetime.utcnow().date() - timedelta(days=days - i - 1)
                start_of_day = datetime.combine(date, datetime.min.time())
                end_of_day = datetime.combine(date, datetime.max.time())
                
                # Count unique users with activity on this day
                active_users = self.sessions_collection.distinct(
                    "user_id",
                    {
                        "last_activity": {"$gte": start_of_day, "$lte": end_of_day},
                        "user_id": {"$ne": None}
                    }
                )
                
                daily_data.append({
                    "date": date.isoformat(),
                    "count": len(active_users)
                })
            
            return daily_data
            
        except Exception as e:
            logger.error(f"Error getting daily active users: {e}")
            return []
    
    def _get_top_users(self, days: int, limit: int = 10) -> List[Dict]:
        """
        Get top most active users by query count.
        
        Args:
            days: Number of days to analyze
            limit: Number of top users to return
            
        Returns:
            List of dicts with user info and query counts
        """
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=days)
            
            # Aggregate user messages to get query counts
            pipeline = [
                {
                    "$match": {
                        "role": "user",
                        "timestamp": {"$gte": cutoff_date}
                    }
                },
                {
                    "$lookup": {
                        "from": "sessions",
                        "localField": "session_id",
                        "foreignField": "session_id",
                        "as": "session"
                    }
                },
                {"$unwind": "$session"},
                {
                    "$group": {
                        "_id": "$session.user_id",
                        "query_count": {"$sum": 1},
                        "last_activity": {"$max": "$timestamp"}
                    }
                },
                {"$match": {"_id": {"$ne": None}}},
                {"$sort": {"query_count": -1}},
                {"$limit": limit}
            ]
            
            results = list(self.messages_collection.aggregate(pipeline))
            
            # Enrich with user information
            top_users = []
            for result in results:
                user = self.users_collection.find_one({"_id": result["_id"]})
                if user:
                    top_users.append({
                        "username": user.get("username", "unknown"),
                        "query_count": result["query_count"],
                        "last_activity": result["last_activity"].isoformat()
                    })
            
            return top_users
            
        except Exception as e:
            logger.error(f"Error getting top users: {e}")
            return []
    
    def get_session_analytics(self, days: int = 30) -> Dict:
        """
        Get session analytics for the specified time period.
        
        Calculates total sessions, average duration, average messages per session,
        session distribution by message count, top query topics, and session trends.
        
        Args:
            days: Number of days to analyze (default 30)
            
        Returns:
            Dict containing:
                - total_sessions: Total number of sessions
                - avg_session_duration_minutes: Average session duration
                - avg_messages_per_session: Average messages per session
                - session_distribution: Distribution by message count ranges
                - top_query_topics: Top 10 query topics by keyword frequency
                - session_trend: Daily session creation trend
        """
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=days)
            
            # Total sessions in period
            total_sessions = self.sessions_collection.count_documents({
                "created_at": {"$gte": cutoff_date}
            })
            
            # Get all sessions with their message counts and durations
            sessions = list(self.sessions_collection.find({
                "created_at": {"$gte": cutoff_date}
            }))
            
            # Calculate average session duration
            total_duration_minutes = 0
            session_count_with_duration = 0
            
            for session in sessions:
                created_at = session.get("created_at")
                last_activity = session.get("last_activity")
                
                if created_at and last_activity:
                    duration = (last_activity - created_at).total_seconds() / 60
                    total_duration_minutes += duration
                    session_count_with_duration += 1
            
            avg_duration = round(
                total_duration_minutes / session_count_with_duration, 2
            ) if session_count_with_duration > 0 else 0.0
            
            # Calculate average messages per session
            total_messages = self.messages_collection.count_documents({
                "timestamp": {"$gte": cutoff_date}
            })
            
            avg_messages = round(
                total_messages / total_sessions, 2
            ) if total_sessions > 0 else 0.0
            
            # Session distribution by message count
            session_distribution = self._get_session_distribution(cutoff_date)
            
            # Top query topics
            top_query_topics = self.get_query_topic_analysis(limit=10, days=days)
            
            # Session trend (daily session creation)
            session_trend = self._get_session_trend(days)
            
            return {
                "total_sessions": total_sessions,
                "avg_session_duration_minutes": avg_duration,
                "avg_messages_per_session": avg_messages,
                "session_distribution": session_distribution,
                "top_query_topics": top_query_topics,
                "session_trend": session_trend
            }
            
        except Exception as e:
            logger.error(f"Error getting session analytics: {e}")
            raise
    
    def _get_session_distribution(self, cutoff_date: datetime) -> Dict[str, int]:
        """
        Get distribution of sessions by message count ranges.
        
        Args:
            cutoff_date: Start date for analysis
            
        Returns:
            Dict with message count ranges as keys and session counts as values
        """
        try:
            # Get message counts per session
            pipeline = [
                {"$match": {"timestamp": {"$gte": cutoff_date}}},
                {
                    "$group": {
                        "_id": "$session_id",
                        "message_count": {"$sum": 1}
                    }
                }
            ]
            
            results = list(self.messages_collection.aggregate(pipeline))
            
            # Categorize into ranges
            distribution = {
                "1-5": 0,
                "6-10": 0,
                "11-20": 0,
                "21+": 0
            }
            
            for result in results:
                count = result["message_count"]
                if count <= 5:
                    distribution["1-5"] += 1
                elif count <= 10:
                    distribution["6-10"] += 1
                elif count <= 20:
                    distribution["11-20"] += 1
                else:
                    distribution["21+"] += 1
            
            return distribution
            
        except Exception as e:
            logger.error(f"Error getting session distribution: {e}")
            return {"1-5": 0, "6-10": 0, "11-20": 0, "21+": 0}
    
    def _get_session_trend(self, days: int) -> List[Dict]:
        """
        Get daily session creation trend.
        
        Args:
            days: Number of days to analyze
            
        Returns:
            List of dicts with 'date' and 'count' keys
        """
        try:
            trend_data = []
            
            for i in range(days):
                date = datetime.utcnow().date() - timedelta(days=days - i - 1)
                start_of_day = datetime.combine(date, datetime.min.time())
                end_of_day = datetime.combine(date, datetime.max.time())
                
                # Count sessions created on this day
                session_count = self.sessions_collection.count_documents({
                    "created_at": {"$gte": start_of_day, "$lte": end_of_day}
                })
                
                trend_data.append({
                    "date": date.isoformat(),
                    "count": session_count
                })
            
            return trend_data
            
        except Exception as e:
            logger.error(f"Error getting session trend: {e}")
            return []
    
    def get_document_usage_analytics(self) -> Dict:
        """
        Get document usage analytics.
        
        Analyzes document query patterns from ChromaDB metadata.
        Note: This requires ChromaDB metadata to include query_count field.
        
        Returns:
            Dict containing document usage statistics
        """
        try:
            # This method would need access to ChromaDB to get document query patterns
            # For now, return a placeholder structure
            # In a full implementation, this would query ChromaDB metadata
            
            logger.warning("get_document_usage_analytics not fully implemented - requires ChromaDB integration")
            
            return {
                "total_queries": 0,
                "unique_documents_queried": 0,
                "avg_queries_per_document": 0.0,
                "most_queried_documents": []
            }
            
        except Exception as e:
            logger.error(f"Error getting document usage analytics: {e}")
            raise
    
    def get_query_topic_analysis(self, limit: int = 10, days: int = 30) -> List[Dict]:
        """
        Analyze query topics using keyword frequency analysis.
        
        Extracts keywords from user queries and identifies the most common topics.
        
        Args:
            limit: Number of top topics to return (default 10)
            days: Number of days to analyze (default 30)
            
        Returns:
            List of dicts with 'topic' and 'count' keys
        """
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=days)
            
            # Get all user messages from the period
            user_messages = self.messages_collection.find({
                "role": "user",
                "timestamp": {"$gte": cutoff_date}
            })
            
            # Extract keywords from queries
            all_keywords = []
            
            # Common stop words to filter out
            stop_words = {
                'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for',
                'of', 'with', 'by', 'from', 'as', 'is', 'was', 'are', 'were', 'been',
                'be', 'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would',
                'could', 'should', 'may', 'might', 'can', 'what', 'when', 'where',
                'who', 'how', 'why', 'which', 'this', 'that', 'these', 'those',
                'i', 'you', 'he', 'she', 'it', 'we', 'they', 'me', 'him', 'her',
                'us', 'them', 'my', 'your', 'his', 'its', 'our', 'their'
            }
            
            for message in user_messages:
                content = message.get("content", "").lower()
                
                # Extract words (alphanumeric sequences)
                words = re.findall(r'\b[a-z]{3,}\b', content)
                
                # Filter out stop words and add to keyword list
                keywords = [word for word in words if word not in stop_words]
                all_keywords.extend(keywords)
            
            # Count keyword frequencies
            keyword_counts = Counter(all_keywords)
            
            # Get top N keywords
            top_topics = [
                {"topic": keyword, "count": count}
                for keyword, count in keyword_counts.most_common(limit)
            ]
            
            return top_topics
            
        except Exception as e:
            logger.error(f"Error analyzing query topics: {e}")
            return []
    
    def close(self):
        """Close the MongoDB connection."""
        try:
            self.client.close()
            logger.info("AnalyticsService MongoDB connection closed")
        except Exception as e:
            logger.error(f"Error closing MongoDB connection: {e}")
