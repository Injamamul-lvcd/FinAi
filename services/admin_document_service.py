"""
Admin Document Service for document management operations.

This module provides the AdminDocumentService class for administrative
document operations including listing, searching, deleting, and statistics.
"""

import logging
from datetime import datetime, timedelta
from typing import Optional, Dict, List
from pymongo import MongoClient, ASCENDING, DESCENDING
from pymongo.errors import ConnectionFailure

from services.vector_store import VectorStoreManager
from services.activity_logger import ActivityLogger

logger = logging.getLogger(__name__)


class AdminDocumentService:
    """
    Manages document-related administrative operations.
    
    Provides functionality for listing documents with pagination and filtering,
    deleting documents with vector database cleanup, and generating document
    statistics and usage analytics.
    """
    
    def __init__(
        self,
        vector_store: VectorStoreManager,
        activity_logger: ActivityLogger,
        connection_string: str = "mongodb://localhost:27017/",
        database_name: str = "financial_chatbot"
    ):
        """
        Initialize the AdminDocumentService.
        
        Args:
            vector_store: VectorStoreManager instance for document operations
            activity_logger: ActivityLogger instance for audit trail
            connection_string: MongoDB connection string
            database_name: Name of the database to use
        """
        self.vector_store = vector_store
        self.activity_logger = activity_logger
        self.connection_string = connection_string
        self.database_name = database_name
        
        try:
            # Initialize MongoDB client
            self.client = MongoClient(connection_string, serverSelectionTimeoutMS=5000)
            
            # Test connection
            self.client.admin.command('ping')
            logger.info(f"AdminDocumentService connected to MongoDB at {connection_string}")
            
            # Get database
            self.db = self.client[database_name]
            
        except ConnectionFailure as e:
            logger.error(f"Failed to connect to MongoDB: {e}")
            raise
        except Exception as e:
            logger.error(f"Error initializing AdminDocumentService: {e}")
            raise
    
    def get_all_documents(
        self,
        page: int = 1,
        page_size: int = 50,
        search: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> Dict:
        """
        Retrieve all documents with pagination, search, and date range filtering.
        
        Args:
            page: Page number (1-indexed)
            page_size: Number of records per page (10-100)
            search: Optional search string for filename or username
            start_date: Optional filter by upload start date (inclusive)
            end_date: Optional filter by upload end date (inclusive)
            
        Returns:
            Dict: Dictionary containing:
                - documents: List of document records with metadata
                - total: Total number of matching documents
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
            
            # Get all items from ChromaDB
            all_items = self.vector_store.collection.get()
            
            # Group chunks by document_id and build document list
            documents_map = {}
            
            for i, metadata in enumerate(all_items['metadatas']):
                doc_id = metadata.get('document_id')
                if not doc_id:
                    continue
                
                # Initialize document entry if not exists
                if doc_id not in documents_map:
                    filename = metadata.get('filename', 'unknown')
                    upload_date_str = metadata.get('upload_date', '')
                    user_id = metadata.get('user_id', 'unknown')
                    username = metadata.get('username', 'unknown')
                    file_size_bytes = metadata.get('file_size_bytes', 0)
                    query_count = metadata.get('query_count', 0)
                    
                    documents_map[doc_id] = {
                        'document_id': doc_id,
                        'filename': filename,
                        'uploader_user_id': user_id,
                        'uploader_username': username,
                        'upload_date': upload_date_str,
                        'file_size_bytes': file_size_bytes,
                        'chunk_count': 0,
                        'query_count': query_count
                    }
                
                # Increment chunk count
                documents_map[doc_id]['chunk_count'] += 1
            
            # Convert to list
            documents_list = list(documents_map.values())
            
            # Apply search filter
            if search:
                search_lower = search.lower()
                documents_list = [
                    doc for doc in documents_list
                    if search_lower in doc['filename'].lower() or
                       search_lower in doc['uploader_username'].lower()
                ]
            
            # Apply date range filter
            if start_date or end_date:
                filtered_docs = []
                for doc in documents_list:
                    try:
                        upload_date = datetime.fromisoformat(doc['upload_date'])
                        
                        if start_date and upload_date < start_date:
                            continue
                        if end_date and upload_date > end_date:
                            continue
                        
                        filtered_docs.append(doc)
                    except (ValueError, TypeError):
                        # Skip documents with invalid dates
                        continue
                
                documents_list = filtered_docs
            
            # Sort by upload date (descending - most recent first)
            documents_list.sort(
                key=lambda x: x.get('upload_date', ''),
                reverse=True
            )
            
            # Calculate pagination
            total = len(documents_list)
            total_pages = (total + page_size - 1) // page_size if total > 0 else 0
            
            # Apply pagination
            start_idx = (page - 1) * page_size
            end_idx = start_idx + page_size
            paginated_docs = documents_list[start_idx:end_idx]
            
            # Format documents with file size in MB
            formatted_docs = []
            for doc in paginated_docs:
                formatted_doc = doc.copy()
                formatted_doc['file_size_mb'] = round(doc['file_size_bytes'] / (1024 * 1024), 2)
                formatted_docs.append(formatted_doc)
            
            logger.info(
                f"Retrieved {len(formatted_docs)} documents "
                f"(page {page}/{total_pages}, total: {total})"
            )
            
            return {
                "documents": formatted_docs,
                "total": total,
                "page": page,
                "page_size": page_size,
                "total_pages": total_pages
            }
            
        except Exception as e:
            logger.error(f"Error retrieving documents: {e}")
            return {
                "documents": [],
                "total": 0,
                "page": page,
                "page_size": page_size,
                "total_pages": 0
            }

    def delete_document(
        self,
        document_id: str,
        admin_id: str
    ) -> Optional[Dict]:
        """
        Delete a document and all its chunks from the vector database.
        
        Args:
            document_id: ID of document to delete
            admin_id: ID of admin performing the deletion
            
        Returns:
            Optional[Dict]: Dictionary with deletion details if successful, None if document not found
                - document_id: ID of deleted document
                - filename: Name of deleted document
                - chunks_deleted: Number of chunks removed
        """
        try:
            # Get all items from ChromaDB
            all_items = self.vector_store.collection.get()
            
            # Find chunks belonging to this document
            chunk_ids_to_delete = []
            document_info = None
            
            for i, metadata in enumerate(all_items['metadatas']):
                if metadata.get('document_id') == document_id:
                    chunk_ids_to_delete.append(all_items['ids'][i])
                    
                    # Store document info from first chunk
                    if document_info is None:
                        document_info = {
                            'document_id': document_id,
                            'filename': metadata.get('filename', 'unknown'),
                            'uploader_username': metadata.get('username', 'unknown'),
                            'uploader_user_id': metadata.get('user_id', 'unknown')
                        }
            
            # If no chunks found, document doesn't exist
            if not chunk_ids_to_delete:
                logger.warning(f"Document {document_id} not found for deletion")
                return None
            
            # Delete chunks from ChromaDB
            self.vector_store.collection.delete(ids=chunk_ids_to_delete)
            
            logger.info(
                f"Deleted document {document_id} ({document_info['filename']}) "
                f"with {len(chunk_ids_to_delete)} chunks"
            )
            
            # Log the deletion activity
            self.activity_logger.log_action(
                admin_id=admin_id,
                action_type="document_deleted",
                resource_type="document",
                resource_id=document_id,
                details={
                    "filename": document_info['filename'],
                    "chunks_deleted": len(chunk_ids_to_delete),
                    "uploader_username": document_info['uploader_username'],
                    "uploader_user_id": document_info['uploader_user_id']
                }
            )
            
            return {
                "document_id": document_id,
                "filename": document_info['filename'],
                "chunks_deleted": len(chunk_ids_to_delete)
            }
            
        except Exception as e:
            logger.error(f"Error deleting document {document_id}: {e}")
            return None
    
    def get_document_statistics(self) -> Dict:
        """
        Get comprehensive document statistics.
        
        Returns:
            Dict: Dictionary containing:
                - total_documents: Total number of documents
                - total_chunks: Total number of chunks
                - total_size_mb: Total storage size in MB
                - avg_chunks_per_doc: Average chunks per document
                - documents_by_type: List of document counts by file type with percentages
                - upload_trend: Upload count per day for last 30 days
                - top_documents: Top 10 most queried documents
        """
        try:
            # Get all items from ChromaDB
            all_items = self.vector_store.collection.get()
            
            # Group by document_id
            documents_map = {}
            file_type_counts = {}
            upload_dates = []
            
            for i, metadata in enumerate(all_items['metadatas']):
                doc_id = metadata.get('document_id')
                if not doc_id:
                    continue
                
                # Initialize document entry if not exists
                if doc_id not in documents_map:
                    filename = metadata.get('filename', 'unknown')
                    upload_date_str = metadata.get('upload_date', '')
                    file_size_bytes = metadata.get('file_size_bytes', 0)
                    query_count = metadata.get('query_count', 0)
                    
                    # Extract file type
                    file_type = filename.split('.')[-1].lower() if '.' in filename else 'unknown'
                    
                    documents_map[doc_id] = {
                        'document_id': doc_id,
                        'filename': filename,
                        'upload_date': upload_date_str,
                        'file_size_bytes': file_size_bytes,
                        'chunk_count': 0,
                        'query_count': query_count,
                        'file_type': file_type
                    }
                    
                    # Count file types
                    file_type_counts[file_type] = file_type_counts.get(file_type, 0) + 1
                    
                    # Collect upload dates
                    try:
                        upload_date = datetime.fromisoformat(upload_date_str)
                        upload_dates.append(upload_date.date())
                    except (ValueError, TypeError):
                        pass
                
                # Increment chunk count
                documents_map[doc_id]['chunk_count'] += 1
            
            # Calculate basic statistics
            total_documents = len(documents_map)
            total_chunks = len(all_items['ids'])
            total_size_bytes = sum(doc['file_size_bytes'] for doc in documents_map.values())
            total_size_mb = round(total_size_bytes / (1024 * 1024), 2)
            avg_chunks_per_doc = round(total_chunks / total_documents, 2) if total_documents > 0 else 0
            
            # Calculate documents by type with percentages
            documents_by_type = []
            for file_type, count in sorted(file_type_counts.items(), key=lambda x: x[1], reverse=True):
                percentage = round((count / total_documents * 100), 2) if total_documents > 0 else 0
                documents_by_type.append({
                    "file_type": file_type,
                    "count": count,
                    "percentage": percentage
                })
            
            # Calculate upload trend for last 30 days
            today = datetime.now().date()
            date_counts = {}
            for i in range(30):
                date = today - timedelta(days=i)
                date_counts[date] = 0
            
            for upload_date in upload_dates:
                if upload_date in date_counts:
                    date_counts[upload_date] += 1
            
            upload_trend = [
                {
                    "date": date.isoformat(),
                    "count": count
                }
                for date, count in sorted(date_counts.items())
            ]
            
            # Get top 10 most queried documents
            documents_list = list(documents_map.values())
            documents_list.sort(key=lambda x: x['query_count'], reverse=True)
            top_documents = [
                {
                    "document_id": doc['document_id'],
                    "filename": doc['filename'],
                    "query_count": doc['query_count'],
                    "last_queried": None  # Would need separate tracking for this
                }
                for doc in documents_list[:10]
            ]
            
            logger.info(
                f"Generated document statistics: {total_documents} documents, "
                f"{total_chunks} chunks, {total_size_mb} MB"
            )
            
            return {
                "total_documents": total_documents,
                "total_chunks": total_chunks,
                "total_size_mb": total_size_mb,
                "avg_chunks_per_doc": avg_chunks_per_doc,
                "documents_by_type": documents_by_type,
                "upload_trend": upload_trend,
                "top_documents": top_documents
            }
            
        except Exception as e:
            logger.error(f"Error generating document statistics: {e}")
            return {
                "total_documents": 0,
                "total_chunks": 0,
                "total_size_mb": 0.0,
                "avg_chunks_per_doc": 0.0,
                "documents_by_type": [],
                "upload_trend": [],
                "top_documents": []
            }
