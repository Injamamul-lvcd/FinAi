# How the Financial Chatbot RAG System Works

## Overview

This application uses **Retrieval-Augmented Generation (RAG)** to answer financial questions based on your uploaded documents. Think of it as a smart assistant that reads your documents and answers questions about them.

## Architecture Flow

```
User Question → Embedding → Vector Search → Context Retrieval → LLM → Answer
                    ↓                              ↓
              Vector DB                    Conversation History
```

## Core Components

### 1. Document Processing Pipeline

**What happens when you upload a document:**

```
PDF/DOCX/TXT File
    ↓
Text Extraction (PyPDF2, python-docx)
    ↓
Text Chunking (800 chars with 100 overlap)
    ↓
Generate Embeddings (Google Gemini)
    ↓
Store in Vector Database (ChromaDB)
```

**Step-by-Step:**

1. **File Upload** (`api/routes/documents.py`)
   - Validates file type (PDF, DOCX, TXT)
   - Checks file size (max 10MB)
   - Saves temporarily for processing

2. **Text Extraction** (`services/document_processor.py`)
   - **PDF**: Uses PyPDF2 to extract text from each page
   - **DOCX**: Uses python-docx to extract paragraphs
   - **TXT**: Reads plain text directly

3. **Text Chunking** (`services/document_processor.py`)
   - Splits text into 800-character chunks
   - Overlaps by 100 characters to maintain context
   - Example: "...revenue increased by 15%" appears in multiple chunks

4. **Embedding Generation** (`services/document_processor.py`)
   - Sends each chunk to Google Gemini API
   - Receives a 768-dimensional vector (list of numbers)
   - This vector represents the "meaning" of the text

5. **Vector Storage** (`services/vector_store.py`)
   - Stores chunks + embeddings + metadata in ChromaDB
   - Metadata includes: document_id, filename, upload_date, chunk_index
   - Uses cosine similarity for searching

**Example:**
```
Original Text: "Q4 revenue was $2.5M, up 15% from Q3's $2.17M"

Chunk 1: "Q4 revenue was $2.5M, up 15% from Q3's $2.17M"
Embedding 1: [0.234, -0.567, 0.891, ..., 0.123] (768 numbers)

Stored in ChromaDB with metadata:
{
  "document_id": "doc_123",
  "filename": "financial_report.pdf",
  "upload_date": "2025-11-09T10:30:00",
  "chunk_index": 0
}
```

---

### 2. Query Processing Pipeline (RAG)

**What happens when you ask a question:**

```
User Query: "What was the Q4 revenue?"
    ↓
Generate Query Embedding
    ↓
Search Vector Database (Top 5 similar chunks)
    ↓
Retrieve Conversation History
    ↓
Construct Prompt (System + Context + History + Query)
    ↓
Send to Google Gemini LLM
    ↓
Generate Answer
    ↓
Store in Session History
    ↓
Return Response + Sources
```

**Step-by-Step:**

1. **Query Embedding** (`services/rag_engine.py`)
   - Your question: "What was the Q4 revenue?"
   - Sent to Google Gemini embedding model
   - Returns vector: [0.245, -0.543, 0.876, ..., 0.134]

2. **Similarity Search** (`services/vector_store.py`)
   - Compares query vector with all stored chunk vectors
   - Uses cosine similarity (measures angle between vectors)
   - Returns top 5 most similar chunks
   
   **Example:**
   ```
   Query: "What was the Q4 revenue?"
   
   Top Results:
   1. "Q4 revenue was $2.5M..." (similarity: 0.92)
   2. "Revenue breakdown by quarter..." (similarity: 0.87)
   3. "Financial highlights Q4..." (similarity: 0.81)
   ```

3. **Retrieve Conversation History** (`services/session_manager.py`)
   - Fetches last 5 messages from SQLite database
   - Includes both user questions and assistant answers
   - Helps maintain context across conversation

4. **Prompt Construction** (`services/rag_engine.py`)
   - Combines multiple pieces:
   
   ```
   === SYSTEM INSTRUCTIONS ===
   You are a helpful financial assistant...
   
   === RELEVANT FINANCIAL DOCUMENTS ===
   [Document 1: financial_report.pdf]
   Q4 revenue was $2.5M, up 15% from Q3's $2.17M
   
   [Document 2: financial_report.pdf]
   Revenue breakdown by quarter: Q1: $1.8M, Q2: $2.0M...
   
   === CONVERSATION HISTORY ===
   USER: What are the key metrics?
   ASSISTANT: The key metrics include revenue of $2.5M...
   
   === CURRENT QUESTION ===
   What was the Q4 revenue?
   
   Please provide a helpful answer based on the context above.
   ```

5. **LLM Generation** (`services/rag_engine.py`)
   - Sends complete prompt to Google Gemini (gemini-1.5-flash)
   - Temperature: 0.7 (controls creativity)
   - Max tokens: 500 (limits response length)
   - Receives generated answer

6. **Response Formatting** (`api/routes/chat.py`)
   - Extracts source information (which documents were used)
   - Calculates relevance scores
   - Stores conversation in session
   - Returns JSON response

**Example Response:**
```json
{
  "response": "Based on the financial report, Q4 revenue was $2.5M, representing a 15% increase from Q3's $2.17M.",
  "sources": [
    {
      "document_id": "doc_123",
      "filename": "financial_report.pdf",
      "chunk_text": "Q4 revenue was $2.5M, up 15% from Q3's $2.17M",
      "relevance_score": 0.92
    }
  ],
  "session_id": "550e8400-e29b-41d4-a716-446655440000"
}
```

---

### 3. Session Management

**How conversation history works:**

1. **Session Creation** (`services/session_manager.py`)
   - First message creates a new session
   - Generates unique UUID: `550e8400-e29b-41d4-a716-446655440000`
   - Stores in SQLite database

2. **Message Storage**
   - Each message stored with:
     - session_id
     - role (user or assistant)
     - content (the actual message)
     - timestamp
   
   **Database Schema:**
   ```sql
   CREATE TABLE sessions (
     id TEXT PRIMARY KEY,
     created_at TIMESTAMP
   );
   
   CREATE TABLE messages (
     id INTEGER PRIMARY KEY,
     session_id TEXT,
     role TEXT,
     content TEXT,
     timestamp TIMESTAMP
   );
   ```

3. **History Retrieval**
   - Fetches last 5 messages for context
   - Ordered by timestamp
   - Helps LLM understand conversation flow

4. **Session Limits**
   - Max 20 turns per session (configurable)
   - Prevents database bloat
   - Maintains conversation quality

---

## Key Technologies Explained

### Vector Embeddings

**What are they?**
- Numbers that represent text meaning
- Similar meanings = similar numbers
- Example:
  ```
  "revenue" → [0.2, 0.8, -0.3, ...]
  "income"  → [0.3, 0.7, -0.2, ...]  (similar!)
  "banana"  → [-0.9, 0.1, 0.8, ...]  (different!)
  ```

**Why use them?**
- Enables semantic search (meaning-based, not keyword-based)
- "What was the income?" finds chunks about "revenue"
- Traditional search would miss this connection

### ChromaDB (Vector Database)

**What it does:**
- Stores embeddings efficiently
- Performs fast similarity searches
- Persists data to disk (`./data/chroma/`)

**How it works:**
- Uses HNSW (Hierarchical Navigable Small World) algorithm
- Creates a graph structure for fast nearest-neighbor search
- Cosine similarity: measures angle between vectors

### Google Gemini API

**Two models used:**

1. **text-embedding-004** (Embedding Model)
   - Converts text → 768-dimensional vectors
   - Fast and efficient
   - Used for both documents and queries

2. **gemini-1.5-flash** (Chat Model)
   - Generates human-like responses
   - Understands context and instructions
   - Balances quality and speed

---

## Data Flow Example

Let's trace a complete interaction:

### Upload Phase

```
1. User uploads "Q4_Report.pdf"
   ↓
2. Extract text: "Q4 revenue was $2.5M. Net profit: $450K..."
   ↓
3. Split into chunks:
   - Chunk 1: "Q4 revenue was $2.5M. Net profit: $450K..."
   - Chunk 2: "Net profit: $450K. Operating expenses: $2.05M..."
   ↓
4. Generate embeddings:
   - Chunk 1 → [0.234, -0.567, 0.891, ...]
   - Chunk 2 → [0.123, -0.456, 0.789, ...]
   ↓
5. Store in ChromaDB:
   - ID: "doc_123_chunk_0"
   - Text: "Q4 revenue was $2.5M..."
   - Embedding: [0.234, -0.567, ...]
   - Metadata: {document_id: "doc_123", filename: "Q4_Report.pdf"}
```

### Query Phase

```
1. User asks: "What was the Q4 revenue?"
   ↓
2. Generate query embedding: [0.245, -0.543, 0.876, ...]
   ↓
3. Search ChromaDB:
   - Compare with all stored embeddings
   - Find top 5 most similar
   - Result: Chunk 1 (similarity: 0.92)
   ↓
4. Retrieve history:
   - Previous Q: "What are the key metrics?"
   - Previous A: "Key metrics include revenue of $2.5M..."
   ↓
5. Build prompt:
   System: "You are a financial assistant..."
   Context: "Q4 revenue was $2.5M..."
   History: "USER: What are the key metrics?..."
   Query: "What was the Q4 revenue?"
   ↓
6. Send to Gemini:
   - Model: gemini-1.5-flash
   - Temperature: 0.7
   - Max tokens: 500
   ↓
7. Receive response:
   "Based on the Q4 report, revenue was $2.5M, representing..."
   ↓
8. Store in session:
   - Role: user, Content: "What was the Q4 revenue?"
   - Role: assistant, Content: "Based on the Q4 report..."
   ↓
9. Return to user:
   {
     "response": "Based on the Q4 report...",
     "sources": [{...}],
     "session_id": "550e8400..."
   }
```

---

## Configuration Parameters

### Document Processing
- `CHUNK_SIZE=800`: Size of text chunks (characters)
- `CHUNK_OVERLAP=100`: Overlap between chunks (maintains context)
- `MAX_FILE_SIZE_MB=10`: Maximum upload size

### RAG Configuration
- `TOP_K_CHUNKS=5`: Number of chunks to retrieve
- `MAX_CONVERSATION_TURNS=20`: Session history limit

### LLM Configuration
- `GEMINI_TEMPERATURE=0.7`: Creativity (0=deterministic, 2=creative)
- `GEMINI_MAX_TOKENS=500`: Response length limit

---

## Why This Architecture?

### Advantages

1. **Scalability**
   - Add unlimited documents
   - Fast retrieval regardless of database size
   - Efficient vector search

2. **Accuracy**
   - Semantic search finds relevant content
   - Context-aware responses
   - Source attribution

3. **Conversation Memory**
   - Maintains context across questions
   - Natural dialogue flow
   - Session-based isolation

4. **Flexibility**
   - Easy to swap LLM providers
   - Configurable chunk sizes
   - Adjustable retrieval parameters

### Limitations

1. **Context Window**
   - Only top 5 chunks used (configurable)
   - May miss relevant information in large documents

2. **Embedding Quality**
   - Depends on Google Gemini's embedding model
   - May not capture domain-specific nuances

3. **LLM Hallucination**
   - May generate plausible but incorrect information
   - Always cites sources for verification

4. **Cost**
   - Google API calls cost money
   - Embedding: ~$0.00001 per 1K characters
   - Generation: ~$0.00015 per 1K tokens

---

## File Structure

```
financial-chatbot-rag/
├── api/routes/
│   ├── documents.py      # Upload, list, delete endpoints
│   ├── chat.py           # Chat query endpoint
│   └── health.py         # Health check endpoint
│
├── services/
│   ├── document_processor.py  # Text extraction, chunking, embedding
│   ├── vector_store.py        # ChromaDB operations
│   ├── rag_engine.py          # RAG pipeline orchestration
│   └── session_manager.py     # Conversation history
│
├── models/
│   └── schemas.py        # Pydantic models for API
│
├── config/
│   └── settings.py       # Configuration management
│
├── utils/
│   ├── logger.py         # Logging setup
│   ├── middleware.py     # Request logging, error handling
│   └── exceptions.py     # Custom exception handlers
│
├── data/
│   ├── chroma/           # Vector database storage
│   └── sessions.db       # SQLite conversation history
│
└── main.py               # FastAPI application entry point
```

---

## Performance Considerations

### Embedding Generation
- **Speed**: ~100ms per chunk
- **Bottleneck**: Network latency to Google API
- **Optimization**: Batch processing (up to 100 chunks at once)

### Vector Search
- **Speed**: ~10ms for 1000 chunks
- **Bottleneck**: Database size
- **Optimization**: HNSW algorithm provides O(log n) search

### LLM Generation
- **Speed**: ~2-5 seconds per response
- **Bottleneck**: Model inference time
- **Optimization**: Use gemini-1.5-flash (faster than Pro)

### Total Response Time
- Typical: 3-6 seconds
- Breakdown:
  - Query embedding: 100ms
  - Vector search: 10ms
  - LLM generation: 2-5s
  - Overhead: 100ms

---

## Security Considerations

1. **API Key Protection**
   - Stored in `.env` file (not in code)
   - Never committed to version control
   - Server-side only (not exposed to frontend)

2. **File Upload Validation**
   - Type checking (PDF, DOCX, TXT only)
   - Size limits (10MB max)
   - Malware scanning (recommended for production)

3. **Session Isolation**
   - Each session has unique ID
   - No cross-session data leakage
   - Session cleanup after expiry

4. **Input Sanitization**
   - Query length limits (2000 chars)
   - SQL injection prevention (parameterized queries)
   - XSS prevention (JSON encoding)

---

## Monitoring and Debugging

### Logs
- Location: `./logs/app.log`
- Levels: INFO, WARNING, ERROR
- Includes: Request IDs, timestamps, error traces

### Key Metrics to Monitor
- Document upload success rate
- Average query response time
- LLM API error rate
- Vector database size
- Session count

### Common Issues

1. **"No relevant documents found"**
   - Cause: Query doesn't match document content
   - Solution: Rephrase query or upload relevant documents

2. **Slow responses**
   - Cause: Large number of chunks or slow API
   - Solution: Reduce TOP_K_CHUNKS or optimize network

3. **Out of memory**
   - Cause: Too many embeddings in memory
   - Solution: Restart server or increase RAM

---

## Future Enhancements

1. **Multi-modal Support**
   - Extract text from images (OCR)
   - Process tables and charts
   - Handle spreadsheets

2. **Advanced RAG Techniques**
   - Re-ranking retrieved chunks
   - Query expansion
   - Hybrid search (keyword + semantic)

3. **Caching**
   - Cache frequent queries
   - Cache embeddings
   - Reduce API costs

4. **Analytics**
   - Track popular queries
   - Measure answer quality
   - User feedback loop

---

## Summary

The Financial Chatbot RAG system works by:

1. **Converting documents into searchable vectors** (embeddings)
2. **Finding relevant content** when you ask a question (similarity search)
3. **Generating contextual answers** using an LLM (Google Gemini)
4. **Maintaining conversation history** for natural dialogue

This architecture provides accurate, source-backed answers to financial questions while maintaining conversation context and scalability.
