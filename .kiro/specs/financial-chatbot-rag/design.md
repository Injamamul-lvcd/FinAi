# Financial Chatbot RAG System - Design Document

## Overview

The Financial Chatbot is a backend API application that uses Retrieval-Augmented Generation (RAG) to answer financial questions. The system consists of three main components: a REST API layer, a RAG pipeline for document processing and query handling, and a vector database for semantic search. The application will be built using Python with FastAPI for the API layer, LangChain for RAG orchestration, ChromaDB as the vector database, and Google Gemini API for embeddings and chat completion.

## Architecture

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                         REST API Layer                       │
│                          (FastAPI)                           │
├──────────────────────┬──────────────────────────────────────┤
│  Document Ingestion  │         Query Service                │
│      Endpoints       │          Endpoints                   │
└──────────┬───────────┴────────────┬─────────────────────────┘
           │                        │
           ▼                        ▼
┌──────────────────────┐  ┌─────────────────────────┐
│  Document Processor  │  │    RAG Query Engine     │
│   - Text Extraction  │  │  - Context Retrieval    │
│   - Chunking         │  │  - Prompt Construction  │
│   - Embedding        │  │  - LLM Generation       │
└──────────┬───────────┘  └────────┬────────────────┘
           │                       │
           └───────────┬───────────┘
                       ▼
            ┌──────────────────────┐
            │   Vector Database    │
            │     (ChromaDB)       │
            └──────────────────────┘
                       │
                       ▼
            ┌──────────────────────┐
            │  Session Storage     │
            │   (JSON/SQLite)      │
            └──────────────────────┘
```

### Technology Stack

- **API Framework**: FastAPI (Python) - Fast, modern, with automatic OpenAPI documentation
- **RAG Framework**: LangChain - Provides abstractions for document loading, splitting, and RAG chains
- **Vector Database**: ChromaDB - Lightweight, embedded vector database (no separate server needed)
- **Embeddings**: Google Gemini text-embedding-004 - Free tier available, good performance
- **LLM**: Google Gemini 1.5 Flash - Fast, cost-effective, and has a generous free tier
- **Document Processing**: PyPDF2 (PDF), python-docx (DOCX), built-in file handling (TXT)
- **Session Storage**: SQLite - Simple, file-based storage for conversation history

## Components and Interfaces

### 1. REST API Layer

**Technology**: FastAPI with Pydantic models for request/response validation

**Endpoints**:

```python
POST /api/v1/chat
- Request: { "query": str, "session_id": Optional[str] }
- Response: { "response": str, "sources": List[dict], "session_id": str }

POST /api/v1/documents/upload
- Request: multipart/form-data with file
- Response: { "document_id": str, "filename": str, "chunks_created": int }

GET /api/v1/documents
- Response: { "documents": List[{ "id": str, "filename": str, "upload_date": str, "chunks": int }] }

DELETE /api/v1/documents/{document_id}
- Response: { "success": bool, "message": str }

GET /api/v1/documents/stats
- Response: { "total_documents": int, "total_chunks": int }

GET /api/v1/health
- Response: { "status": str, "vector_db": str, "llm": str }
```

### 2. Document Processor

**Responsibilities**:
- Extract text from uploaded documents (PDF, DOCX, TXT)
- Split text into overlapping chunks
- Generate embeddings for each chunk
- Store chunks and embeddings in vector database

**Key Classes**:

```python
class DocumentProcessor:
    def __init__(self, embedding_model, vector_store, chunk_size=800, chunk_overlap=100):
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap
        )
        self.embedding_model = embedding_model
        self.vector_store = vector_store
    
    def process_document(self, file_path: str, document_id: str) -> int:
        # Extract text based on file type
        # Split into chunks
        # Generate embeddings
        # Store in vector database
        # Return number of chunks created
        pass
    
    def extract_text(self, file_path: str, file_type: str) -> str:
        # Handle PDF, DOCX, TXT extraction
        pass
```

### 3. RAG Query Engine

**Responsibilities**:
- Retrieve relevant document chunks based on query similarity
- Construct prompts with retrieved context and conversation history
- Generate responses using LLM
- Track conversation sessions

**Key Classes**:

```python
class RAGQueryEngine:
    def __init__(self, vector_store, llm, embedding_model, top_k=5):
        self.vector_store = vector_store
        self.llm = llm
        self.embedding_model = embedding_model
        self.top_k = top_k
        self.session_manager = SessionManager()
    
    def query(self, user_query: str, session_id: Optional[str] = None) -> dict:
        # Retrieve relevant chunks
        # Get conversation history if session_id provided
        # Construct prompt with context
        # Generate response
        # Save to session history
        # Return response with sources
        pass
    
    def retrieve_context(self, query: str) -> List[Document]:
        # Query vector database for similar chunks
        pass
    
    def construct_prompt(self, query: str, context: List[Document], history: List[dict]) -> str:
        # Build prompt with system message, context, history, and query
        pass
```

### 4. Vector Store Manager

**Responsibilities**:
- Initialize and manage ChromaDB collection
- Store document chunks with embeddings and metadata
- Perform similarity search
- Delete documents and associated chunks

**Key Classes**:

```python
class VectorStoreManager:
    def __init__(self, persist_directory: str, collection_name: str):
        self.client = chromadb.PersistentClient(path=persist_directory)
        self.collection = self.client.get_or_create_collection(
            name=collection_name,
            metadata={"hnsw:space": "cosine"}
        )
    
    def add_documents(self, chunks: List[str], embeddings: List[List[float]], 
                     metadatas: List[dict], ids: List[str]):
        # Add chunks to collection
        pass
    
    def similarity_search(self, query_embedding: List[float], top_k: int) -> List[dict]:
        # Query collection for similar chunks
        pass
    
    def delete_by_document_id(self, document_id: str):
        # Remove all chunks for a document
        pass
```

### 5. Session Manager

**Responsibilities**:
- Store and retrieve conversation history
- Manage session lifecycle
- Limit history to recent turns

**Implementation**: SQLite database with simple schema

```sql
CREATE TABLE sessions (
    id TEXT PRIMARY KEY,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE messages (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id TEXT,
    role TEXT,  -- 'user' or 'assistant'
    content TEXT,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (session_id) REFERENCES sessions(id)
);
```

## Data Models

### Request/Response Models (Pydantic)

```python
class ChatRequest(BaseModel):
    query: str = Field(..., min_length=1, max_length=2000)
    session_id: Optional[str] = None

class Source(BaseModel):
    document_id: str
    filename: str
    chunk_text: str
    relevance_score: float

class ChatResponse(BaseModel):
    response: str
    sources: List[Source]
    session_id: str

class DocumentUploadResponse(BaseModel):
    document_id: str
    filename: str
    chunks_created: int
    upload_date: str

class DocumentInfo(BaseModel):
    id: str
    filename: str
    upload_date: str
    chunks: int

class DocumentListResponse(BaseModel):
    documents: List[DocumentInfo]

class DocumentStats(BaseModel):
    total_documents: int
    total_chunks: int
```

### Internal Data Models

```python
@dataclass
class DocumentChunk:
    chunk_id: str
    document_id: str
    text: str
    embedding: List[float]
    metadata: dict  # filename, chunk_index, document_type

@dataclass
class ConversationTurn:
    role: str  # 'user' or 'assistant'
    content: str
    timestamp: datetime
```

## Error Handling

### Error Categories and Responses

1. **Client Errors (4xx)**:
   - 400 Bad Request: Invalid input, unsupported file type
   - 404 Not Found: Document ID not found
   - 413 Payload Too Large: File size exceeds limit (10MB)

2. **Server Errors (5xx)**:
   - 500 Internal Server Error: Unexpected errors
   - 503 Service Unavailable: Vector DB or LLM API unavailable

### Error Response Format

```python
class ErrorResponse(BaseModel):
    error: str
    message: str
    details: Optional[dict] = None
```

### Retry Logic

- LLM API calls: Retry up to 2 times with exponential backoff (1s, 2s)
- Vector DB operations: No retry (fail fast)
- Document processing: No retry (return error to client)

### Logging Strategy

- Use Python's logging module with structured logging
- Log levels:
  - INFO: API requests, document uploads, successful operations
  - WARNING: Retry attempts, degraded performance
  - ERROR: Failed operations, exceptions
- Log format: `[timestamp] [level] [component] message {context}`
- Log to file: `logs/app.log` with daily rotation

## Testing Strategy

### Unit Tests

- Test document text extraction for each file type
- Test text chunking with various input sizes
- Test prompt construction with different context sizes
- Test session history retrieval and limiting
- Test error handling for invalid inputs

### Integration Tests

- Test complete document upload flow (file → chunks → vector DB)
- Test complete query flow (query → retrieval → LLM → response)
- Test session continuity across multiple queries
- Test document deletion and cleanup

### API Tests

- Test all endpoints with valid inputs
- Test error responses for invalid inputs
- Test file upload with different file types and sizes
- Test concurrent requests

### Testing Tools

- pytest for test framework
- pytest-asyncio for async endpoint testing
- httpx for API client testing
- Mock LLM responses to avoid API costs during testing

## Configuration

### Environment Variables

```
# Google Gemini Configuration
GOOGLE_API_KEY=AIza...
GEMINI_EMBEDDING_MODEL=models/text-embedding-004
GEMINI_CHAT_MODEL=gemini-1.5-flash
GEMINI_TEMPERATURE=0.7
GEMINI_MAX_TOKENS=500

# Vector Database
CHROMA_PERSIST_DIR=./data/chroma
CHROMA_COLLECTION_NAME=financial_docs

# Document Processing
CHUNK_SIZE=800
CHUNK_OVERLAP=100
MAX_FILE_SIZE_MB=10

# RAG Configuration
TOP_K_CHUNKS=5
MAX_CONVERSATION_TURNS=20

# Session Storage
SESSION_DB_PATH=./data/sessions.db

# API Configuration
API_HOST=0.0.0.0
API_PORT=8000
LOG_LEVEL=INFO
```

### Configuration Loading

Use `pydantic-settings` for type-safe configuration management:

```python
class Settings(BaseSettings):
    google_api_key: str
    gemini_embedding_model: str = "models/text-embedding-004"
    gemini_chat_model: str = "gemini-1.5-flash"
    # ... other settings
    
    class Config:
        env_file = ".env"
```

## Deployment Considerations

### Local Development

- Run with `uvicorn main:app --reload`
- Use `.env` file for configuration
- ChromaDB and SQLite use local file storage

### Production Considerations (Future)

- Use proper vector database (Pinecone, Weaviate) for scale
- Add authentication/authorization
- Implement rate limiting
- Use Redis for session storage
- Add monitoring and metrics
- Containerize with Docker

## Security Considerations

- Validate and sanitize all file uploads
- Limit file sizes to prevent DoS
- Store API keys in environment variables, never in code
- Implement input validation on all endpoints
- Add request size limits
- Consider adding API key authentication for production use
