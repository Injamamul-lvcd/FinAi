# Financial Chatbot RAG API Reference

## Base URL
```
http://localhost:8000
```

## Authentication
No authentication required for local development. All endpoints are publicly accessible.

## Content Types
- **Request**: `application/json` (for POST requests with JSON body)
- **Response**: `application/json`
- **File Upload**: `multipart/form-data`

## Error Handling
All endpoints return consistent error responses:

```json
{
  "error": "ErrorType",
  "message": "Human-readable error message",
  "details": {
    "request_id": "uuid",
    "additional_context": "value"
  }
}
```

## Common HTTP Status Codes
- `200` - Success
- `400` - Bad Request (invalid parameters)
- `404` - Not Found (resource doesn't exist)
- `413` - Payload Too Large (file size exceeded)
- `422` - Unprocessable Entity (validation error)
- `500` - Internal Server Error
- `503` - Service Unavailable

---

## Endpoints

### 1. Health Check

Check system health and component status.

#### `GET /api/v1/health`

**Description:** Returns the health status of the application and its components.

**Parameters:** None

**Request Headers:** None required

**Response:**
```json
{
  "status": "healthy",
  "components": {
    "vector_database": {
      "status": "healthy",
      "details": {
        "total_documents": 5,
        "total_chunks": 234
      }
    },
    "gemini_api": {
      "status": "healthy",
      "details": {
        "embedding_model": "models/text-embedding-004",
        "chat_model": "gemini-1.5-flash"
      }
    }
  }
}
```

**Response Fields:**
- `status` (string): Overall system status (`healthy`, `degraded`, `unhealthy`)
- `components` (object): Status of individual components
  - `vector_database` (object): ChromaDB status
    - `status` (string): Component status
    - `details.total_documents` (integer): Number of stored documents
    - `details.total_chunks` (integer): Number of stored chunks
  - `gemini_api` (object): Google Gemini API status
    - `status` (string): API connectivity status
    - `details.embedding_model` (string): Embedding model name
    - `details.chat_model` (string): Chat model name

**Example Request:**
```bash
curl -X GET http://localhost:8000/api/v1/health
```

**Error Responses:**
- `503 Service Unavailable`: One or more components are unhealthy

---

### 2. Upload Document

Upload a financial document to the knowledge base.

#### `POST /api/v1/documents/upload`

**Description:** Uploads and processes a document (PDF, DOCX, TXT) for the RAG system.

**Parameters:**
- `file` (file, required): Document file to upload

**Request Headers:**
- `Content-Type: multipart/form-data`

**File Constraints:**
- **Supported formats**: PDF (.pdf), Word Document (.docx), Text (.txt)
- **Maximum size**: 10MB
- **Encoding**: UTF-8 for text files

**Response:**
```json
{
  "document_id": "doc_1731110914",
  "filename": "financial_report_2024.pdf",
  "chunks_created": 45,
  "upload_date": "2025-11-09T10:30:00"
}
```

**Response Fields:**
- `document_id` (string): Unique identifier for the uploaded document
- `filename` (string): Original filename of the uploaded document
- `chunks_created` (integer): Number of text chunks created from the document
- `upload_date` (string): ISO 8601 timestamp of upload completion

**Example Request:**
```bash
curl -X POST http://localhost:8000/api/v1/documents/upload \
  -F "file=@/path/to/financial_report.pdf"
```

**Error Responses:**
- `400 Bad Request`: No file provided or invalid file type
- `413 Payload Too Large`: File exceeds 10MB limit
- `422 Unprocessable Entity`: File validation failed
- `500 Internal Server Error`: Processing failed

**Error Examples:**
```json
{
  "error": "ValidationError",
  "message": "Invalid file type. Only PDF, DOCX, and TXT files are supported.",
  "details": {
    "file_type": "xlsx",
    "allowed_types": ["pdf", "docx", "txt"]
  }
}
```

---

### 3. List Documents

Retrieve a list of all uploaded documents with metadata.

#### `GET /api/v1/documents`

**Description:** Returns metadata for all documents stored in the system.

**Parameters:** None

**Request Headers:** None required

**Response:**
```json
{
  "documents": [
    {
      "id": "doc_1731110914",
      "filename": "financial_report_2024.pdf",
      "upload_date": "2025-11-09T10:30:00",
      "chunks": 45
    },
    {
      "id": "doc_1731110920",
      "filename": "investment_guide.docx",
      "upload_date": "2025-11-09T11:15:00",
      "chunks": 32
    }
  ]
}
```

**Response Fields:**
- `documents` (array): List of document objects
  - `id` (string): Unique document identifier
  - `filename` (string): Original filename
  - `upload_date` (string): ISO 8601 upload timestamp
  - `chunks` (integer): Number of chunks created from this document

**Example Request:**
```bash
curl -X GET http://localhost:8000/api/v1/documents
```

**Error Responses:**
- `500 Internal Server Error`: Database query failed

---

### 4. Get Document Statistics

Retrieve statistics about the document collection.

#### `GET /api/v1/documents/stats`

**Description:** Returns aggregate statistics about all stored documents.

**Parameters:** None

**Request Headers:** None required

**Response:**
```json
{
  "total_documents": 15,
  "total_chunks": 523
}
```

**Response Fields:**
- `total_documents` (integer): Total number of documents in the system
- `total_chunks` (integer): Total number of text chunks across all documents

**Example Request:**
```bash
curl -X GET http://localhost:8000/api/v1/documents/stats
```

**Error Responses:**
- `500 Internal Server Error`: Database query failed

---

### 5. Delete Document

Remove a document and all its chunks from the knowledge base.

#### `DELETE /api/v1/documents/{document_id}`

**Description:** Permanently deletes a document and all associated chunks from the vector database.

**Path Parameters:**
- `document_id` (string, required): Unique identifier of the document to delete

**Request Headers:** None required

**Response:**
```json
{
  "success": true,
  "message": "Document doc_1731110914 deleted successfully",
  "chunks_deleted": 45
}
```

**Response Fields:**
- `success` (boolean): Whether the deletion was successful
- `message` (string): Confirmation message
- `chunks_deleted` (integer): Number of chunks removed

**Example Request:**
```bash
curl -X DELETE http://localhost:8000/api/v1/documents/doc_1731110914
```

**Error Responses:**
- `404 Not Found`: Document ID doesn't exist
- `500 Internal Server Error`: Deletion failed

**Error Example:**
```json
{
  "error": "NotFound",
  "message": "Document with ID 'doc_invalid' not found",
  "details": {
    "document_id": "doc_invalid"
  }
}
```

---

### 6. Chat Query

Submit a financial question and receive a context-aware answer.

#### `POST /api/v1/chat`

**Description:** Processes a user query using the RAG pipeline to generate answers based on uploaded documents.

**Request Headers:**
- `Content-Type: application/json`

**Request Body:**
```json
{
  "query": "What are the key financial metrics for Q4 2024?",
  "session_id": "550e8400-e29b-41d4-a716-446655440000"
}
```

**Request Fields:**
- `query` (string, required): The user's financial question
  - **Constraints**: 1-2000 characters
  - **Format**: Plain text
- `session_id` (string, optional): Session ID for conversation continuity
  - **Format**: UUID string
  - **Behavior**: If not provided, a new session is created

**Response:**
```json
{
  "response": "Based on the financial report, the key metrics for Q4 2024 include: Revenue of $2.5M (up 15% YoY), Net Profit of $450K (18% margin), and Operating Cash Flow of $380K. The company showed strong growth in all major categories.",
  "sources": [
    {
      "document_id": "doc_1731110914",
      "filename": "financial_report_2024.pdf",
      "chunk_text": "Q4 2024 Financial Summary: Revenue: $2.5M, Net Profit: $450K, Operating Cash Flow: $380K. Year-over-year revenue growth of 15% demonstrates strong market performance...",
      "relevance_score": 0.89
    },
    {
      "document_id": "doc_1731110914",
      "filename": "financial_report_2024.pdf",
      "chunk_text": "Key Performance Indicators: Revenue growth rate: 15%, Profit margin: 18%, Cash flow positive for 4 consecutive quarters...",
      "relevance_score": 0.76
    }
  ],
  "session_id": "550e8400-e29b-41d4-a716-446655440000"
}
```

**Response Fields:**
- `response` (string): AI-generated answer to the user's question
- `sources` (array): List of source documents used to generate the answer
  - `document_id` (string): ID of the source document
  - `filename` (string): Name of the source document
  - `chunk_text` (string): Relevant text excerpt (truncated to ~200 chars)
  - `relevance_score` (float): Relevance score between 0.0 and 1.0
- `session_id` (string): Session ID for conversation continuity

**Example Request:**
```bash
curl -X POST http://localhost:8000/api/v1/chat \
  -H "Content-Type: application/json" \
  -d '{
    "query": "What are the key financial metrics for Q4 2024?",
    "session_id": "550e8400-e29b-41d4-a716-446655440000"
  }'
```

**Conversation Flow:**
1. **First message**: Omit `session_id` to create a new session
2. **Follow-up messages**: Include the `session_id` from previous responses
3. **Session memory**: Last 5 messages are remembered for context

**Example Conversation:**
```bash
# First message (creates session)
curl -X POST http://localhost:8000/api/v1/chat \
  -H "Content-Type: application/json" \
  -d '{"query": "What was the Q4 revenue?"}'

# Response includes session_id: "abc-123"

# Follow-up message (uses session)
curl -X POST http://localhost:8000/api/v1/chat \
  -H "Content-Type: application/json" \
  -d '{
    "query": "How does that compare to Q3?",
    "session_id": "abc-123"
  }'
```

**Error Responses:**
- `400 Bad Request`: Invalid query format or missing required fields
- `404 Not Found`: No relevant documents found for the query
- `500 Internal Server Error`: RAG processing failed
- `503 Service Unavailable`: Chat service not initialized

**Error Examples:**
```json
{
  "error": "ValidationError",
  "message": "Request validation failed",
  "details": {
    "errors": [
      {
        "field": "query",
        "message": "String should have at least 1 character",
        "type": "string_too_short"
      }
    ]
  }
}
```

```json
{
  "error": "InsufficientContext",
  "message": "I apologize, but I don't have enough information in the available financial documents to answer your question. Please try rephrasing your question or upload relevant documents.",
  "details": {
    "query": "What is the weather like?",
    "documents_searched": 5
  }
}
```

---

## Rate Limits

**Current Implementation:** No rate limiting

**Recommendations for Production:**
- Chat endpoint: 10 requests/minute per IP
- Upload endpoint: 5 requests/minute per IP
- Other endpoints: 60 requests/minute per IP

---

## Request/Response Examples

### Complete Upload and Chat Flow

#### 1. Upload Document
```bash
curl -X POST http://localhost:8000/api/v1/documents/upload \
  -F "file=@quarterly_report.pdf"
```

**Response:**
```json
{
  "document_id": "doc_1731110914",
  "filename": "quarterly_report.pdf",
  "chunks_created": 28,
  "upload_date": "2025-11-09T14:30:00"
}
```

#### 2. First Chat Message
```bash
curl -X POST http://localhost:8000/api/v1/chat \
  -H "Content-Type: application/json" \
  -d '{"query": "What was the total revenue this quarter?"}'
```

**Response:**
```json
{
  "response": "According to the quarterly report, total revenue for this quarter was $3.2M, representing a 12% increase from the previous quarter.",
  "sources": [
    {
      "document_id": "doc_1731110914",
      "filename": "quarterly_report.pdf",
      "chunk_text": "Total quarterly revenue reached $3.2M, up 12% from Q2's $2.86M...",
      "relevance_score": 0.94
    }
  ],
  "session_id": "f47ac10b-58cc-4372-a567-0e02b2c3d479"
}
```

#### 3. Follow-up Chat Message
```bash
curl -X POST http://localhost:8000/api/v1/chat \
  -H "Content-Type: application/json" \
  -d '{
    "query": "What were the main drivers of this growth?",
    "session_id": "f47ac10b-58cc-4372-a567-0e02b2c3d479"
  }'
```

**Response:**
```json
{
  "response": "The main drivers of the 12% revenue growth were: 1) New customer acquisitions increased by 25%, 2) Existing customer expansion contributed $400K in additional revenue, and 3) New product launches generated $300K in incremental sales.",
  "sources": [
    {
      "document_id": "doc_1731110914",
      "filename": "quarterly_report.pdf",
      "chunk_text": "Revenue growth drivers: New customer acquisitions (+25%), customer expansion ($400K), new products ($300K)...",
      "relevance_score": 0.87
    }
  ],
  "session_id": "f47ac10b-58cc-4372-a567-0e02b2c3d479"
}
```

---

## SDK Examples

### Python
```python
import requests
import json

BASE_URL = "http://localhost:8000"

# Upload document
with open("financial_report.pdf", "rb") as f:
    response = requests.post(
        f"{BASE_URL}/api/v1/documents/upload",
        files={"file": f}
    )
    upload_result = response.json()
    print(f"Uploaded: {upload_result['document_id']}")

# Chat query
chat_data = {
    "query": "What are the key financial metrics?"
}
response = requests.post(
    f"{BASE_URL}/api/v1/chat",
    headers={"Content-Type": "application/json"},
    data=json.dumps(chat_data)
)
chat_result = response.json()
print(f"Answer: {chat_result['response']}")
print(f"Session: {chat_result['session_id']}")

# Follow-up query
followup_data = {
    "query": "Tell me more about revenue",
    "session_id": chat_result['session_id']
}
response = requests.post(
    f"{BASE_URL}/api/v1/chat",
    headers={"Content-Type": "application/json"},
    data=json.dumps(followup_data)
)
followup_result = response.json()
print(f"Follow-up: {followup_result['response']}")
```

### JavaScript (Node.js)
```javascript
const axios = require('axios');
const FormData = require('form-data');
const fs = require('fs');

const BASE_URL = 'http://localhost:8000';

async function uploadDocument(filePath) {
  const form = new FormData();
  form.append('file', fs.createReadStream(filePath));
  
  const response = await axios.post(
    `${BASE_URL}/api/v1/documents/upload`,
    form,
    { headers: form.getHeaders() }
  );
  
  return response.data;
}

async function chatQuery(query, sessionId = null) {
  const data = { query };
  if (sessionId) data.session_id = sessionId;
  
  const response = await axios.post(
    `${BASE_URL}/api/v1/chat`,
    data,
    { headers: { 'Content-Type': 'application/json' } }
  );
  
  return response.data;
}

// Usage
(async () => {
  // Upload document
  const uploadResult = await uploadDocument('./financial_report.pdf');
  console.log('Uploaded:', uploadResult.document_id);
  
  // First chat
  const chatResult = await chatQuery('What are the key metrics?');
  console.log('Answer:', chatResult.response);
  
  // Follow-up chat
  const followupResult = await chatQuery(
    'Tell me more about revenue',
    chatResult.session_id
  );
  console.log('Follow-up:', followupResult.response);
})();
```

---

## OpenAPI Specification

The API follows OpenAPI 3.1 specification. You can access:

- **Interactive Documentation**: `http://localhost:8000/api/docs` (Swagger UI)
- **Alternative Documentation**: `http://localhost:8000/api/redoc` (ReDoc)
- **OpenAPI JSON**: `http://localhost:8000/openapi.json`

---

## Changelog

### Version 1.0.0 (Current)
- Initial API release
- Document upload and management
- RAG-based chat functionality
- Session management
- Health monitoring

### Planned Features
- Bulk document upload
- Document versioning
- Advanced search filters
- User authentication
- Rate limiting
- Webhook notifications

---

## Support

For API issues or questions:
1. Check the logs in `./logs/app.log`
2. Verify your `.env` configuration
3. Test with the interactive documentation at `/docs`
4. Review the troubleshooting section in `README.md`