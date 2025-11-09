# Postman Testing Guide for Financial Chatbot RAG

## Quick Start

Your server is running at: `http://localhost:8000`

## Step-by-Step Guide

### 1. Upload a Document First

Before you can chat, you need to upload at least one financial document.

**Request:**
- Method: `POST`
- URL: `http://localhost:8000/api/v1/documents/upload`
- Body: `form-data`
  - Key: `file` (type: File)
  - Value: Select a PDF, DOCX, or TXT file

**Example Response:**
```json
{
  "document_id": "doc_1731110914",
  "filename": "financial_report.pdf",
  "chunks_created": 45,
  "upload_date": "2025-11-09T02:48:34"
}
```

### 2. Chat with the Bot

Now you can ask questions about your uploaded documents!

**Request:**
- Method: `POST`
- URL: `http://localhost:8000/api/v1/chat`
- Headers:
  - `Content-Type`: `application/json`
- Body: `raw` (JSON)

**Example Body (First Message):**
```json
{
  "query": "What are the key financial metrics mentioned in the document?"
}
```

**Example Response:**
```json
{
  "response": "Based on the financial report, the key metrics include...",
  "sources": [
    {
      "document_id": "doc_1731110914",
      "filename": "financial_report.pdf",
      "chunk_text": "Revenue increased by 15% in Q4...",
      "relevance_score": 0.92
    }
  ],
  "session_id": "550e8400-e29b-41d4-a716-446655440000"
}
```

### 3. Continue the Conversation

To maintain conversation context, include the `session_id` from the previous response:

**Example Body (Follow-up Message):**
```json
{
  "query": "Can you tell me more about the revenue growth?",
  "session_id": "550e8400-e29b-41d4-a716-446655440000"
}
```

The bot will remember your previous questions and provide contextual answers!

## Additional Endpoints

### Check System Health
- Method: `GET`
- URL: `http://localhost:8000/api/v1/health`

### List All Documents
- Method: `GET`
- URL: `http://localhost:8000/api/v1/documents`

### Get Document Statistics
- Method: `GET`
- URL: `http://localhost:8000/api/v1/documents/stats`

### Delete a Document
- Method: `DELETE`
- URL: `http://localhost:8000/api/v1/documents/{document_id}`
- Replace `{document_id}` with actual ID from upload response

## Sample Questions to Ask

After uploading a financial document, try these questions:

1. "What is the total revenue mentioned in the document?"
2. "Summarize the key financial highlights"
3. "What are the main expenses listed?"
4. "Tell me about the profit margins"
5. "What financial risks are mentioned?"

## Tips

1. **Session Management**: Save the `session_id` to continue conversations
2. **Multiple Documents**: Upload multiple documents to build a larger knowledge base
3. **Specific Questions**: More specific questions get better answers
4. **Context Matters**: The bot only answers based on uploaded documents

## Troubleshooting

### "No relevant documents found"
- Make sure you've uploaded documents first
- Try rephrasing your question to match document content

### "Failed to process query"
- Check your Google API key in `.env` file
- Verify you have internet connection (for Gemini API)
- Check server logs for detailed error messages

## API Documentation

For complete API documentation, visit:
- Swagger UI: `http://localhost:8000/api/docs`
- ReDoc: `http://localhost:8000/api/redoc`
