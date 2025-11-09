# Financial Chatbot RAG System

A backend API application that uses Retrieval-Augmented Generation (RAG) to answer financial questions based on uploaded documents. The system leverages Google Gemini for embeddings and chat completion, ChromaDB for vector storage, and FastAPI for the REST API layer.

## Overview

The Financial Chatbot allows users to:
- Upload financial documents (PDF, DOCX, TXT) for knowledge base creation
- Ask questions via API and receive context-aware answers
- Maintain conversation history across multiple turns
- Manage the document collection (list, delete, view statistics)

### Architecture

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
            │      (SQLite)        │
            └──────────────────────┘
```

## Prerequisites

- Python 3.9 or higher
- Google API key (for Gemini API access)
- 500MB free disk space (for vector database and session storage)

## Installation

### 1. Clone the Repository

```bash
git clone <repository-url>
cd financial-chatbot-rag
```

### 2. Create Virtual Environment

```bash
# Windows
python -m venv venv
venv\Scripts\activate

# Linux/Mac
python3 -m venv venv
source venv/bin/activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

## Configuration

### 1. Create Environment File

Copy the example environment file and configure it:

```bash
# Windows
copy .env.example .env

# Linux/Mac
cp .env.example .env
```

### 2. Obtain Google API Key

1. Go to [Google AI Studio](https://makersuite.google.com/app/apikey)
2. Sign in with your Google account
3. Click "Create API Key"
4. Copy the generated API key

### 3. Configure Environment Variables

Edit the `.env` file and add your Google API key:

```env
# Google Gemini Configuration
GOOGLE_API_KEY=your_api_key_here
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

## Running the Application

### Start the Server

```bash
# Development mode with auto-reload
uvicorn main:app --reload

# Production mode
uvicorn main:app --host 0.0.0.0 --port 8000
```

The API will be available at `http://localhost:8000`

### Access API Documentation

Once the server is running, you can access:
- Swagger UI: `http://localhost:8000/api/docs`
- ReDoc: `http://localhost:8000/api/redoc`

## API Endpoints

### Health Check

Check if the system is running and all components are healthy.

**Endpoint:** `GET /api/v1/health`

**Example Request:**
```bash
curl http://localhost:8000/api/v1/health
```

**Example Response:**
```json
{
  "status": "healthy",
  "vector_db": "connected",
  "llm_api": "connected"
}
```

### Upload Document

Upload a financial document to the knowledge base.

**Endpoint:** `POST /api/v1/documents/upload`

**Supported Formats:** PDF, DOCX, TXT (max 10MB)

**Example Request (curl):**
```bash
curl -X POST http://localhost:8000/api/v1/documents/upload \
  -F "file=@/path/to/document.pdf"
```

**Example Request (Postman):**
1. Method: POST
2. URL: `http://localhost:8000/api/v1/documents/upload`
3. Body: form-data
   - Key: `file` (type: File)
   - Value: Select your document file

**Example Response:**
```json
{
  "document_id": "doc_1234567890",
  "filename": "financial_report_2024.pdf",
  "chunks_created": 45,
  "upload_date": "2024-11-09T10:30:00"
}
```

### List Documents

Get a list of all uploaded documents with metadata.

**Endpoint:** `GET /api/v1/documents`

**Example Request:**
```bash
curl http://localhost:8000/api/v1/documents
```

**Example Response:**
```json
{
  "documents": [
    {
      "id": "doc_1234567890",
      "filename": "financial_report_2024.pdf",
      "upload_date": "2024-11-09T10:30:00",
      "chunks": 45
    },
    {
      "id": "doc_0987654321",
      "filename": "investment_guide.docx",
      "upload_date": "2024-11-09T11:15:00",
      "chunks": 32
    }
  ]
}
```

### Get Document Statistics

Get statistics about the document collection.

**Endpoint:** `GET /api/v1/documents/stats`

**Example Request:**
```bash
curl http://localhost:8000/api/v1/documents/stats
```

**Example Response:**
```json
{
  "total_documents": 5,
  "total_chunks": 234
}
```

### Delete Document

Remove a document and all its chunks from the knowledge base.

**Endpoint:** `DELETE /api/v1/documents/{document_id}`

**Example Request:**
```bash
curl -X DELETE http://localhost:8000/api/v1/documents/doc_1234567890
```

**Example Response:**
```json
{
  "success": true,
  "message": "Document doc_1234567890 deleted successfully"
}
```

### Chat Query

Ask a financial question and receive a context-aware answer.

**Endpoint:** `POST /api/v1/chat`

**Example Request (curl):**
```bash
curl -X POST http://localhost:8000/api/v1/chat \
  -H "Content-Type: application/json" \
  -d '{
    "query": "What are the key financial metrics for Q4 2024?",
    "session_id": "session_abc123"
  }'
```

**Example Request (Postman):**
1. Method: POST
2. URL: `http://localhost:8000/api/v1/chat`
3. Headers:
   - Key: `Content-Type`, Value: `application/json`
4. Body: raw (JSON)
```json
{
  "query": "What are the key financial metrics for Q4 2024?",
  "session_id": "session_abc123"
}
```

**Example Response:**
```json
{
  "response": "Based on the financial report, the key metrics for Q4 2024 include: Revenue of $2.5M (up 15% YoY), Net Profit of $450K (18% margin), and Operating Cash Flow of $380K. The company showed strong growth in all major categories.",
  "sources": [
    {
      "document_id": "doc_1234567890",
      "filename": "financial_report_2024.pdf",
      "chunk_text": "Q4 2024 Financial Summary: Revenue: $2.5M, Net Profit: $450K...",
      "relevance_score": 0.89
    }
  ],
  "session_id": "session_abc123"
}
```

**Note:** The `session_id` is optional. If not provided, a new session will be created. Use the same `session_id` for follow-up questions to maintain conversation context.

## Postman Collection

### Import Collection

You can create a Postman collection with all endpoints:

1. Open Postman
2. Click "Import" → "Link"
3. Enter: `http://localhost:8000/openapi.json`
4. Click "Continue" and "Import"

### Manual Setup

Alternatively, create requests manually using the examples above.

**Environment Variables (optional):**
- `base_url`: `http://localhost:8000`
- `session_id`: `session_abc123` (or any unique identifier)

## Testing

### Run Unit Tests

```bash
pytest test_health_unit.py -v
```

### Run Integration Tests

```bash
# Test document upload
pytest test_upload.py -v

# Test document management
pytest test_document_management.py -v

# Test health endpoint
pytest test_health.py -v
```

### Run All Tests

```bash
pytest -v
```

## Troubleshooting

### Issue: "ModuleNotFoundError" when starting the application

**Solution:**
- Ensure virtual environment is activated
- Reinstall dependencies: `pip install -r requirements.txt`
- Check Python version: `python --version` (should be 3.9+)

### Issue: "onnxruntime DLL load failed" or "onnxruntime not installed" error

**Solution:**
This is a known ChromaDB issue on Windows. The application has a built-in workaround, but if you still encounter issues:
- Reinstall onnxruntime: `pip uninstall onnxruntime` then `pip install onnxruntime==1.16.0`
- Install Visual C++ Redistributable: [Download here](https://aka.ms/vs/17/release/vc_redist.x64.exe)
- The application uses Google Gemini for embeddings, so onnxruntime is not actually required for functionality

### Issue: "Invalid API key" or "403 Forbidden" errors

**Solution:**
- Verify your Google API key in the `.env` file
- Ensure the API key has access to Gemini API
- Check if you've exceeded the free tier quota
- Generate a new API key at [Google AI Studio](https://makersuite.google.com/app/apikey)

### Issue: "Vector database connection failed"

**Solution:**
- Check if the `data/chroma` directory exists and is writable
- Delete the `data/chroma` directory and restart (will recreate)
- Ensure sufficient disk space (at least 500MB free)

### Issue: "File upload fails with 413 Payload Too Large"

**Solution:**
- Check file size (must be under 10MB)
- Compress or split large documents
- Adjust `MAX_FILE_SIZE_MB` in `.env` if needed

### Issue: "Session database locked" errors

**Solution:**
- Close any other processes accessing `data/sessions.db`
- Delete `data/sessions.db` (will recreate on next request)
- Ensure only one instance of the application is running

### Issue: "No response" or "Insufficient context" from chat endpoint

**Solution:**
- Ensure documents have been uploaded first
- Check if documents were processed successfully (check logs)
- Try more specific questions related to uploaded content
- Verify `TOP_K_CHUNKS` setting in `.env` (increase if needed)

### Issue: Application crashes on startup

**Solution:**
- Check logs in `logs/` directory for error details
- Verify all environment variables are set correctly
- Ensure required directories exist: `data/`, `logs/`
- Try deleting `data/` directory and restarting

### Issue: Slow response times

**Solution:**
- Reduce `CHUNK_SIZE` in `.env` for faster processing
- Decrease `TOP_K_CHUNKS` to retrieve fewer chunks
- Check internet connection (Gemini API calls require network)
- Consider upgrading to Gemini Pro for better performance

### Issue: "Rate limit exceeded" errors

**Solution:**
- You've exceeded Google's free tier limits
- Wait for the quota to reset (usually daily)
- Upgrade to a paid Google Cloud account
- Reduce the number of requests

## Logs

Application logs are stored in the `logs/` directory:
- `logs/test.log`: General application logs
- `logs/test_errors.log`: Error-specific logs

View logs in real-time:
```bash
# Windows
type logs\test.log

# Linux/Mac
tail -f logs/test.log
```

## Project Structure

```
financial-chatbot-rag/
├── api/
│   └── routes/
│       ├── chat.py          # Chat endpoint
│       ├── documents.py     # Document management endpoints
│       └── health.py        # Health check endpoint
├── config/
│   └── settings.py          # Configuration management
├── data/
│   ├── chroma/              # Vector database storage
│   └── sessions.db          # Conversation history
├── logs/
│   ├── test.log             # Application logs
│   └── test_errors.log      # Error logs
├── models/
│   └── schemas.py           # Pydantic models
├── services/
│   ├── document_processor.py  # Document processing
│   ├── rag_engine.py          # RAG query engine
│   ├── session_manager.py     # Session management
│   └── vector_store.py        # Vector database interface
├── utils/
│   ├── exceptions.py        # Custom exceptions
│   ├── logger.py            # Logging configuration
│   └── middleware.py        # API middleware
├── .env                     # Environment variables (create from .env.example)
├── .env.example             # Example environment file
├── main.py                  # Application entry point
├── requirements.txt         # Python dependencies
└── README.md               # This file
```

## Development

### Code Style

The project follows PEP 8 style guidelines. Format code using:
```bash
black .
```

### Adding New Features

1. Update requirements in `.kiro/specs/financial-chatbot-rag/requirements.md`
2. Update design in `.kiro/specs/financial-chatbot-rag/design.md`
3. Add tasks to `.kiro/specs/financial-chatbot-rag/tasks.md`
4. Implement the feature
5. Add tests
6. Update this README

## License

[Add your license information here]

## Support

For issues and questions:
- Check the Troubleshooting section above
- Review logs in the `logs/` directory
- Consult the API documentation at `http://localhost:8000/api/docs`

## Acknowledgments

- Built with [FastAPI](https://fastapi.tiangolo.com/)
- Powered by [Google Gemini](https://ai.google.dev/)
- Vector storage by [ChromaDB](https://www.trychroma.com/)
- RAG framework by [LangChain](https://www.langchain.com/)
