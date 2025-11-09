"""
Document Processor for extracting, chunking, and embedding documents.

This module provides the DocumentProcessor class for handling document ingestion,
including text extraction from multiple file formats, chunking, embedding generation,
and storage in the vector database.
"""

import logging
from typing import List, Dict, Any, Optional
from datetime import datetime
import os
import uuid

# Document processing libraries
import PyPDF2
from docx import Document as DocxDocument

# LangChain for text splitting
from langchain.text_splitter import RecursiveCharacterTextSplitter

# Google Gemini for embeddings
import google.generativeai as genai

from services.vector_store import VectorStoreManager

logger = logging.getLogger(__name__)


class DocumentProcessor:
    """
    Processes documents for the RAG system.
    
    Handles text extraction from PDF, DOCX, and TXT files,
    splits text into chunks, generates embeddings, and stores
    in the vector database.
    """
    
    def __init__(
        self,
        vector_store: VectorStoreManager,
        google_api_key: str,
        embedding_model: str = "models/text-embedding-004",
        chunk_size: int = 800,
        chunk_overlap: int = 100
    ):
        """
        Initialize the DocumentProcessor.
        
        Args:
            vector_store: VectorStoreManager instance for storage
            google_api_key: Google API key for Gemini embeddings
            embedding_model: Name of the Gemini embedding model
            chunk_size: Size of text chunks in characters
            chunk_overlap: Overlap between chunks in characters
        """
        self.vector_store = vector_store
        self.embedding_model_name = embedding_model
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        
        # Configure Google Gemini API
        genai.configure(api_key=google_api_key)
        
        # Initialize text splitter
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            length_function=len,
            separators=["\n\n", "\n", ". ", " ", ""]
        )
        
        logger.info(
            f"DocumentProcessor initialized with chunk_size={chunk_size}, "
            f"chunk_overlap={chunk_overlap}, embedding_model={embedding_model}"
        )
    
    def extract_text(self, file_path: str, file_type: str) -> str:
        """
        Extract text from a document based on file type.
        
        Args:
            file_path: Path to the document file
            file_type: File extension (pdf, docx, txt)
            
        Returns:
            Extracted text content
            
        Raises:
            ValueError: If file type is not supported
            Exception: If text extraction fails
        """
        file_type = file_type.lower().strip('.')
        
        try:
            if file_type == 'pdf':
                return self._extract_from_pdf(file_path)
            elif file_type == 'docx':
                return self._extract_from_docx(file_path)
            elif file_type == 'txt':
                return self._extract_from_txt(file_path)
            else:
                raise ValueError(f"Unsupported file type: {file_type}")
                
        except Exception as e:
            logger.error(f"Failed to extract text from {file_path}: {e}")
            raise
    
    def _extract_from_pdf(self, file_path: str) -> str:
        """
        Extract text from a PDF file using PyPDF2.
        
        Args:
            file_path: Path to the PDF file
            
        Returns:
            Extracted text content
        """
        text_content = []
        
        with open(file_path, 'rb') as file:
            pdf_reader = PyPDF2.PdfReader(file)
            num_pages = len(pdf_reader.pages)
            
            logger.info(f"Extracting text from PDF with {num_pages} pages")
            
            for page_num in range(num_pages):
                page = pdf_reader.pages[page_num]
                text = page.extract_text()
                if text.strip():
                    text_content.append(text)
        
        full_text = "\n\n".join(text_content)
        logger.info(f"Extracted {len(full_text)} characters from PDF")
        return full_text
    
    def _extract_from_docx(self, file_path: str) -> str:
        """
        Extract text from a DOCX file using python-docx.
        
        Args:
            file_path: Path to the DOCX file
            
        Returns:
            Extracted text content
        """
        doc = DocxDocument(file_path)
        text_content = []
        
        for paragraph in doc.paragraphs:
            if paragraph.text.strip():
                text_content.append(paragraph.text)
        
        full_text = "\n\n".join(text_content)
        logger.info(f"Extracted {len(full_text)} characters from DOCX")
        return full_text
    
    def _extract_from_txt(self, file_path: str) -> str:
        """
        Extract text from a TXT file.
        
        Args:
            file_path: Path to the TXT file
            
        Returns:
            Extracted text content
        """
        with open(file_path, 'r', encoding='utf-8') as file:
            text = file.read()
        
        logger.info(f"Extracted {len(text)} characters from TXT")
        return text

    def _chunk_text(self, text: str) -> List[str]:
        """
        Split text into overlapping chunks.
        
        Args:
            text: Text content to split
            
        Returns:
            List of text chunks
        """
        chunks = self.text_splitter.split_text(text)
        logger.info(f"Split text into {len(chunks)} chunks")
        return chunks
    
    def _generate_embeddings(self, texts: List[str]) -> List[List[float]]:
        """
        Generate embeddings for text chunks using Google Gemini.
        
        Args:
            texts: List of text chunks to embed
            
        Returns:
            List of embedding vectors
            
        Raises:
            Exception: If embedding generation fails
        """
        embeddings = []
        
        try:
            for i, text in enumerate(texts):
                # Generate embedding using Gemini
                result = genai.embed_content(
                    model=self.embedding_model_name,
                    content=text,
                    task_type="retrieval_document"
                )
                embeddings.append(result['embedding'])
                
                if (i + 1) % 10 == 0:
                    logger.info(f"Generated embeddings for {i + 1}/{len(texts)} chunks")
            
            logger.info(f"Successfully generated {len(embeddings)} embeddings")
            return embeddings
            
        except Exception as e:
            logger.error(f"Failed to generate embeddings: {e}")
            raise
    
    def process_document(
        self,
        file_path: str,
        filename: str,
        document_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Process a document end-to-end: extract, chunk, embed, and store.
        
        This method orchestrates the complete document processing pipeline:
        1. Extract text from the document
        2. Split text into chunks
        3. Generate embeddings for each chunk
        4. Store chunks with embeddings and metadata in vector database
        
        Args:
            file_path: Path to the document file
            filename: Original filename
            document_id: Optional document ID (generated if not provided)
            
        Returns:
            Dictionary containing:
                - document_id: Unique document identifier
                - filename: Original filename
                - chunks_created: Number of chunks created
                - upload_date: ISO format timestamp
                
        Raises:
            ValueError: If file type is not supported
            Exception: If processing fails at any stage
        """
        # Generate document ID if not provided
        if document_id is None:
            document_id = str(uuid.uuid4())
        
        # Get file extension
        file_extension = os.path.splitext(filename)[1].lower().strip('.')
        
        # Get current timestamp
        upload_date = datetime.utcnow().isoformat()
        
        logger.info(f"Processing document: {filename} (ID: {document_id})")
        
        try:
            # Step 1: Extract text
            logger.info("Step 1: Extracting text from document")
            text = self.extract_text(file_path, file_extension)
            
            if not text.strip():
                raise ValueError("Extracted text is empty")
            
            # Step 2: Chunk text
            logger.info("Step 2: Chunking text")
            chunks = self._chunk_text(text)
            
            if not chunks:
                raise ValueError("No chunks created from text")
            
            # Step 3: Generate embeddings
            logger.info("Step 3: Generating embeddings")
            embeddings = self._generate_embeddings(chunks)
            
            # Step 4: Prepare metadata and IDs
            logger.info("Step 4: Preparing metadata and storing in vector database")
            chunk_ids = []
            metadatas = []
            
            for i in range(len(chunks)):
                chunk_id = f"{document_id}_chunk_{i}"
                chunk_ids.append(chunk_id)
                
                metadata = {
                    'document_id': document_id,
                    'filename': filename,
                    'chunk_index': i,
                    'upload_date': upload_date,
                    'file_type': file_extension
                }
                metadatas.append(metadata)
            
            # Step 5: Store in vector database
            self.vector_store.add_documents(
                chunks=chunks,
                embeddings=embeddings,
                metadatas=metadatas,
                ids=chunk_ids
            )
            
            result = {
                'document_id': document_id,
                'filename': filename,
                'chunks_created': len(chunks),
                'upload_date': upload_date
            }
            
            logger.info(
                f"Successfully processed document {filename}: "
                f"{len(chunks)} chunks created"
            )
            
            return result
            
        except Exception as e:
            logger.error(f"Failed to process document {filename}: {e}")
            raise
    
    def get_supported_file_types(self) -> List[str]:
        """
        Get list of supported file types.
        
        Returns:
            List of supported file extensions
        """
        return ['pdf', 'docx', 'txt']
    
    def validate_file_type(self, filename: str) -> bool:
        """
        Check if a file type is supported.
        
        Args:
            filename: Name of the file to validate
            
        Returns:
            True if file type is supported, False otherwise
        """
        file_extension = os.path.splitext(filename)[1].lower().strip('.')
        return file_extension in self.get_supported_file_types()
