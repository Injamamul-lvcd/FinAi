"""
Vector Store Manager for ChromaDB operations.

This module provides the VectorStoreManager class for managing document chunks
and embeddings in ChromaDB with persistent storage.
"""

import os
import sys

# Set environment variables BEFORE importing chromadb
# This prevents ChromaDB from trying to load onnxruntime for default embeddings
# We use Google Gemini for embeddings, so we don't need ChromaDB's default
os.environ['ANONYMIZED_TELEMETRY'] = 'False'
os.environ['ALLOW_RESET'] = 'TRUE'

# Workaround for onnxruntime DLL loading issues on Windows
# ChromaDB tries to import onnxruntime even though we don't use it
try:
    import chromadb
    from chromadb.config import Settings
except (ImportError, ValueError) as e:
    if 'onnxruntime' in str(e):
        # Create a mock onnxruntime module to satisfy ChromaDB's import
        import types
        mock_onnxruntime = types.ModuleType('onnxruntime')
        sys.modules['onnxruntime'] = mock_onnxruntime
        # Try importing again
        import chromadb
        from chromadb.config import Settings
    else:
        raise

from typing import List, Dict, Optional, Any
import logging
from datetime import datetime

logger = logging.getLogger(__name__)


class VectorStoreManager:
    """
    Manages vector storage operations using ChromaDB.
    
    Handles initialization, document storage, similarity search,
    and document deletion operations.
    """
    
    def __init__(self, persist_directory: str, collection_name: str = "financial_docs"):
        """
        Initialize the VectorStoreManager with persistent ChromaDB storage.
        
        Args:
            persist_directory: Path to directory for persistent storage
            collection_name: Name of the ChromaDB collection
        """
        self.persist_directory = persist_directory
        self.collection_name = collection_name
        
        # Initialize ChromaDB client with persistent storage
        self.client = chromadb.PersistentClient(path=persist_directory)
        
        # Get or create collection with cosine similarity
        # Set embedding_function to None since we provide our own embeddings
        self.collection = self.client.get_or_create_collection(
            name=collection_name,
            metadata={"hnsw:space": "cosine"},
            embedding_function=None
        )
        
        logger.info(f"VectorStoreManager initialized with collection '{collection_name}' at '{persist_directory}'")
    
    def add_documents(
        self,
        chunks: List[str],
        embeddings: List[List[float]],
        metadatas: List[Dict[str, Any]],
        ids: List[str]
    ) -> None:
        """
        Add document chunks with embeddings and metadata to the vector store.
        
        Args:
            chunks: List of text chunks to store
            embeddings: List of embedding vectors for each chunk
            metadatas: List of metadata dictionaries for each chunk
            ids: List of unique identifiers for each chunk
            
        Raises:
            ValueError: If input lists have different lengths
            Exception: If ChromaDB operation fails
        """
        # Validate input lengths
        if not (len(chunks) == len(embeddings) == len(metadatas) == len(ids)):
            raise ValueError(
                f"Input lists must have same length. Got chunks={len(chunks)}, "
                f"embeddings={len(embeddings)}, metadatas={len(metadatas)}, ids={len(ids)}"
            )
        
        if not chunks:
            logger.warning("add_documents called with empty lists")
            return
        
        try:
            # Add documents to collection
            self.collection.add(
                documents=chunks,
                embeddings=embeddings,
                metadatas=metadatas,
                ids=ids
            )
            logger.info(f"Added {len(chunks)} chunks to vector store")
        except Exception as e:
            logger.error(f"Failed to add documents to vector store: {e}")
            raise
    
    def similarity_search(
        self,
        query_embedding: List[float],
        top_k: int = 5,
        filter_dict: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        Query the vector store for relevant chunks based on similarity.
        
        Args:
            query_embedding: Embedding vector of the query
            top_k: Number of top results to return
            filter_dict: Optional metadata filter for results
            
        Returns:
            List of dictionaries containing:
                - id: Chunk identifier
                - document: Text content
                - metadata: Associated metadata
                - distance: Similarity distance (lower is more similar)
                
        Raises:
            Exception: If ChromaDB query fails
        """
        try:
            # Query collection for similar chunks
            results = self.collection.query(
                query_embeddings=[query_embedding],
                n_results=top_k,
                where=filter_dict
            )
            
            # Format results
            formatted_results = []
            if results['ids'] and results['ids'][0]:
                for i in range(len(results['ids'][0])):
                    formatted_results.append({
                        'id': results['ids'][0][i],
                        'document': results['documents'][0][i],
                        'metadata': results['metadatas'][0][i],
                        'distance': results['distances'][0][i]
                    })
            
            logger.info(f"Similarity search returned {len(formatted_results)} results")
            return formatted_results
            
        except Exception as e:
            logger.error(f"Similarity search failed: {e}")
            raise
    
    def delete_by_document_id(self, document_id: str) -> int:
        """
        Remove all chunks associated with a specific document.
        
        Args:
            document_id: The document identifier to delete
            
        Returns:
            Number of chunks deleted
            
        Raises:
            Exception: If ChromaDB deletion fails
        """
        try:
            # Query for all chunks with this document_id
            results = self.collection.get(
                where={"document_id": document_id}
            )
            
            chunk_ids = results['ids']
            
            if not chunk_ids:
                logger.warning(f"No chunks found for document_id: {document_id}")
                return 0
            
            # Delete all chunks
            self.collection.delete(ids=chunk_ids)
            
            logger.info(f"Deleted {len(chunk_ids)} chunks for document_id: {document_id}")
            return len(chunk_ids)
            
        except Exception as e:
            logger.error(f"Failed to delete document {document_id}: {e}")
            raise
    
    def get_stats(self) -> Dict[str, int]:
        """
        Get statistics about stored documents and chunks.
        
        Returns:
            Dictionary containing:
                - total_chunks: Total number of chunks in the collection
                - total_documents: Number of unique documents
                
        Raises:
            Exception: If ChromaDB operation fails
        """
        try:
            # Get all items from collection
            all_items = self.collection.get()
            
            total_chunks = len(all_items['ids'])
            
            # Extract unique document IDs from metadata
            unique_documents = set()
            for metadata in all_items['metadatas']:
                if 'document_id' in metadata:
                    unique_documents.add(metadata['document_id'])
            
            total_documents = len(unique_documents)
            
            stats = {
                'total_chunks': total_chunks,
                'total_documents': total_documents
            }
            
            logger.info(f"Vector store stats: {stats}")
            return stats
            
        except Exception as e:
            logger.error(f"Failed to get stats: {e}")
            raise
    
    def get_document_metadata(self, document_id: str) -> Optional[Dict[str, Any]]:
        """
        Get metadata for a specific document.
        
        Args:
            document_id: The document identifier
            
        Returns:
            Dictionary with document metadata or None if not found
        """
        try:
            results = self.collection.get(
                where={"document_id": document_id},
                limit=1
            )
            
            if results['metadatas']:
                return results['metadatas'][0]
            
            return None
            
        except Exception as e:
            logger.error(f"Failed to get metadata for document {document_id}: {e}")
            return None
    
    def list_all_documents(self) -> List[Dict[str, Any]]:
        """
        List all documents with their metadata.
        
        Returns:
            List of dictionaries containing document information:
                - document_id: Unique document identifier
                - filename: Original filename
                - upload_date: Upload timestamp
                - chunk_count: Number of chunks for this document
        """
        try:
            all_items = self.collection.get()
            
            # Group chunks by document_id
            documents_map = {}
            for metadata in all_items['metadatas']:
                doc_id = metadata.get('document_id')
                if doc_id:
                    if doc_id not in documents_map:
                        documents_map[doc_id] = {
                            'document_id': doc_id,
                            'filename': metadata.get('filename', 'unknown'),
                            'upload_date': metadata.get('upload_date', ''),
                            'chunk_count': 0
                        }
                    documents_map[doc_id]['chunk_count'] += 1
            
            documents_list = list(documents_map.values())
            logger.info(f"Listed {len(documents_list)} documents")
            return documents_list
            
        except Exception as e:
            logger.error(f"Failed to list documents: {e}")
            raise
