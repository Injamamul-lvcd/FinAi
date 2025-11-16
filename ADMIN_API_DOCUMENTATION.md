# Admin Panel API Documentation

## Overview

The Admin Panel APIs provide comprehensive administrative capabilities for the Financial Chatbot RAG System. These APIs enable administrators to manage users, documents, monitor system health, view analytics, and configure system settings.

**Base URL:** `/api/v1/admin`

**Authentication:** All endpoints require a valid JWT token with admin privileges.

---

## Table of Contents

1. [Authentication](#authentication)
2. [User Management](#user-management)
3. [Document Management](#document-management)
4. [System Monitoring](#system-monitoring)
5. [Analytics](#analytics)
6. [Configuration Management](#configuration-management)
7. [Common Parameters](#common-parameters)
8. [Error Responses](#error-responses)

---

## Authentication

### Requirements

All admin endpoints require authentication with a valid JWT token that has admin privileges.

**Header Format:**
```
Authorization: Bearer <your_jwt_token>
```

### Token Properties

- **Expiration:** 8 hours
- **Required Role:** `is_admin=true`
- **Validation:** Checked on every request

### Error Responses

- **401 Unauthorized:** Invalid or expired token
- **403 Forbidden:** Valid token but user lacks admin privileges

**Example Error Response:**
```json
{
    "error": "AuthorizationError",
    "message": "Admin privileges required to access this resource",
    "details": null
}
```

---

## User Management

### 1. List All Users

**Endpoint:** `GET /api/v1/admin/users`

**Description:** Retrieve a paginated list of all registered users with their details.

**Query Parameters:**
- `page` (integer, optional): Page number (default: 1, min: 1)
- `page_size` (integer, optional): Records per page (default: 50, min: 10, max: 100)
- `search` (string, optional): Search by username or email (case-insensitive, max: 100 chars)
- `sort_by` (string, optional): Sort field - `created_at`, `last_login`, or `username` (default: `created_at`)
- `sort_order` (string, optional): Sort order - `asc` or `desc` (default: `desc`)

**Response Example:**
```json
{
    "users": [
        {
            "user_id": "507f1f77bcf86cd799439011",
            "username": "john_doe",
            "email": "john@example.com",
            "full_name": "John Doe",
            "is_active": true,
            "is_admin": false,
            "password_reset_required": false,
            "created_at": "2024-11-09T10:30:00",
            "updated_at": "2024-11-14T15:20:00",
            "last_login": "2024-11-14T09:15:00",
            "document_count": 5,
            "query_count": 42
        }
    ],
    "total": 150,
    "page": 1,
    "page_size": 50,
    "total_pages": 3
}
```

---

### 2. Get User Details

**Endpoint:** `GET /api/v1/admin/users/{user_id}`

**Description:** Retrieve complete information for a specific user account.

**Path Parameters:**
- `user_id` (string, required): User identifier

**Response Example:**
```json
{
    "user_id": "507f1f77bcf86cd799439011",
    "username": "john_doe",
    "email": "john@example.com",
    "full_name": "John Doe",
    "is_active": true,
    "is_admin": false,
    "password_reset_required": false,
    "created_at": "2024-11-09T10:30:00",
    "updated_at": "2024-11-14T15:20:00",
    "last_login": "2024-11-14T09:15:00",
    "document_count": 5,
    "query_count": 42
}
```

**Error Responses:**
- **404 Not Found:** User does not exist

---

### 3. Update User Account Status

**Endpoint:** `PUT /api/v1/admin/users/{user_id}/status`

**Description:** Enable or disable a user account to control system access.

**Path Parameters:**
- `user_id` (string, required): User identifier

**Request Body:**
```json
{
    "is_active": false,
    "reason": "Account suspended due to policy violation"
}
```

**Response Example:**
```json
{
    "user_id": "507f1f77bcf86cd799439011",
    "username": "john_doe",
    "email": "john@example.com",
    "is_active": false,
    ...
}
```

**Notes:**
- Action is logged for audit trail
- Disabled users cannot authenticate

---

### 4. Reset User Password

**Endpoint:** `POST /api/v1/admin/users/{user_id}/reset-password`

**Description:** Generate a secure temporary password for a user account.

**Path Parameters:**
- `user_id` (string, required): User identifier

**Response Example:**
```json
{
    "temporary_password": "Xy9$mK2pL#4q",
    "expires_at": "User must change password on next login",
    "message": "Password reset successfully. Provide the temporary password to the user."
}
```

**Password Requirements:**
- 12 characters minimum
- Mix of uppercase, lowercase, numbers, and special characters
- User must change on next login

---

### 5. Get User Activity Logs

**Endpoint:** `GET /api/v1/admin/users/{user_id}/activity`

**Description:** Retrieve activity logs for administrative actions performed on a user account.

**Path Parameters:**
- `user_id` (string, required): User identifier

**Query Parameters:**
- `page` (integer, optional): Page number (default: 1)
- `page_size` (integer, optional): Records per page (default: 50, min: 10, max: 100)
- `start_date` (string, optional): Start date in ISO format (YYYY-MM-DDTHH:MM:SS)
- `end_date` (string, optional): End date in ISO format (YYYY-MM-DDTHH:MM:SS)

**Response Example:**
```json
{
    "logs": [
        {
            "log_id": "507f1f77bcf86cd799439012",
            "admin_username": "admin_user",
            "action_type": "user_disabled",
            "resource_type": "user",
            "resource_id": "507f1f77bcf86cd799439011",
            "details": {
                "username": "john_doe",
                "reason": "Policy violation"
            },
            "ip_address": "192.168.1.100",
            "timestamp": "2024-11-14T10:30:00",
            "result": "success"
        }
    ],
    "total": 25,
    "page": 1,
    "page_size": 50,
    "total_pages": 1
}
```

---

## Document Management

### 1. List All Documents

**Endpoint:** `GET /api/v1/admin/documents`

**Description:** Retrieve a paginated list of all documents across all users.

**Query Parameters:**
- `page` (integer, optional): Page number (default: 1)
- `page_size` (integer, optional): Records per page (default: 50, min: 10, max: 100)
- `search` (string, optional): Search by filename or uploader username (max: 100 chars)
- `start_date` (string, optional): Start date filter in ISO format
- `end_date` (string, optional): End date filter in ISO format

**Response Example:**
```json
{
    "documents": [
        {
            "document_id": "doc_123",
            "filename": "financial_report_q4.pdf",
            "uploader_username": "john_doe",
            "uploader_user_id": "507f1f77bcf86cd799439011",
            "upload_date": "2024-11-14T10:30:00",
            "file_size_mb": 2.45,
            "chunk_count": 42,
            "query_count": 15
        }
    ],
    "total": 150,
    "page": 1,
    "page_size": 50,
    "total_pages": 3
}
```

---

### 2. Delete Document

**Endpoint:** `DELETE /api/v1/admin/documents/{document_id}`

**Description:** Delete a document and all its chunks from the vector database.

**Path Parameters:**
- `document_id` (string, required): Document identifier

**Response Example:**
```json
{
    "message": "Document deleted successfully",
    "document_id": "doc_123",
    "filename": "financial_report_q4.pdf",
    "chunks_deleted": 42
}
```

**Warning:** This action is permanent and cannot be undone.

---

### 3. Get Document Statistics

**Endpoint:** `GET /api/v1/admin/documents/stats`

**Description:** Retrieve comprehensive document statistics and usage analytics.

**Response Example:**
```json
{
    "total_documents": 150,
    "total_chunks": 6300,
    "total_size_mb": 245.67,
    "avg_chunks_per_doc": 42.0,
    "documents_by_type": [
        {
            "file_type": "pdf",
            "count": 100,
            "percentage": 66.67
        },
        {
            "file_type": "docx",
            "count": 50,
            "percentage": 33.33
        }
    ],
    "upload_trend": [
        {
            "date": "2024-11-14",
            "count": 5
        }
    ],
    "top_documents": [
        {
            "document_id": "doc_123",
            "filename": "financial_report_q4.pdf",
            "query_count": 150,
            "last_queried": "2024-11-14T15:30:00"
        }
    ]
}
```

---

## System Monitoring

### 1. Get System Health Status

**Endpoint:** `GET /api/v1/admin/system/health`

**Description:** Check health status of all system components.

**Response Example (Healthy):**
```json
{
    "status": "healthy",
    "vector_db_status": "healthy",
    "llm_api_status": "healthy",
    "session_db_status": "healthy",
    "mongodb_status": "healthy",
    "timestamp": "2024-11-14T10:30:00Z",
    "error_details": null
}
```

**Response Example (Degraded):**
```json
{
    "status": "degraded",
    "vector_db_status": "healthy",
    "llm_api_status": "unhealthy",
    "session_db_status": "healthy",
    "mongodb_status": "healthy",
    "timestamp": "2024-11-14T10:30:00Z",
    "error_details": {
        "llm_api": "Connection timeout after 30 seconds"
    }
}
```

**Status Values:**
- `healthy`: All components operational
- `degraded`: Some components have issues
- `unhealthy`: Critical components not operational

---

### 2. Get System Performance Metrics

**Endpoint:** `GET /api/v1/admin/system/metrics`

**Description:** Retrieve current system performance metrics.

**Response Example:**
```json
{
    "active_sessions": 42,
    "total_requests_24h": 1523,
    "avg_response_time_ms": 245.67,
    "memory_usage_percent": 45.2,
    "disk_usage_percent": 62.8,
    "uptime_hours": 72.5
}
```

---

### 3. Get Storage Usage Metrics

**Endpoint:** `GET /api/v1/admin/system/storage`

**Description:** Retrieve storage usage metrics for all databases and disk space.

**Response Example:**
```json
{
    "vector_db_size_mb": 512.45,
    "session_db_size_mb": 24.67,
    "mongodb_size_mb": 128.34,
    "total_document_size_mb": 245.67,
    "available_disk_gb": 45.2,
    "disk_usage_percent": 62.8,
    "growth_rate_7d_percent": 5.3
}
```

---

### 4. Get API Usage Metrics

**Endpoint:** `GET /api/v1/admin/system/api-usage`

**Description:** Retrieve API usage metrics for a specified time period.

**Query Parameters:**
- `hours` (integer, optional): Number of hours to look back (default: 24, min: 1, max: 168)

**Response Example:**
```json
{
    "total_requests": 1523,
    "success_count": 1450,
    "error_count": 73,
    "endpoints": [
        {
            "endpoint": "/api/v1/chat",
            "total_requests": 523,
            "success_count": 498,
            "error_count": 25,
            "avg_response_time_ms": 245.67
        }
    ],
    "slowest_requests": [
        {
            "endpoint": "/api/v1/chat",
            "response_time_ms": 1523.45,
            "timestamp": "2024-11-14T10:30:00Z",
            "status_code": 200
        }
    ],
    "hourly_rate": [
        {
            "hour": "2024-11-14T10:00:00Z",
            "request_count": 125
        }
    ]
}
```

---

### 5. Get Error Logs

**Endpoint:** `GET /api/v1/admin/system/logs`

**Description:** Retrieve error logs with filtering and pagination.

**Query Parameters:**
- `page` (integer, optional): Page number (default: 1)
- `page_size` (integer, optional): Records per page (default: 50, min: 10, max: 100)
- `severity` (string, optional): Filter by severity - `INFO`, `WARNING`, `ERROR`, or `CRITICAL`
- `start_date` (string, optional): Start date in ISO format
- `end_date` (string, optional): End date in ISO format

**Response Example:**
```json
{
    "logs": [
        {
            "log_id": "507f1f77bcf86cd799439013",
            "timestamp": "2024-11-14T10:30:00Z",
            "severity": "ERROR",
            "error_type": "DatabaseConnectionError",
            "error_message": "Failed to connect to MongoDB",
            "endpoint": "/api/v1/chat",
            "stack_trace": "Traceback (most recent call last)...",
            "user_id": "507f1f77bcf86cd799439011"
        }
    ],
    "total": 25,
    "page": 1,
    "page_size": 50,
    "total_pages": 1
}
```

---

## Analytics

### 1. Get User Engagement Metrics

**Endpoint:** `GET /api/v1/admin/analytics/users`

**Description:** Retrieve user engagement metrics for a specified time period.

**Query Parameters:**
- `days` (integer, optional): Number of days to analyze (default: 30, min: 1, max: 365)

**Response Example:**
```json
{
    "total_users": 500,
    "active_users_30d": 125,
    "avg_queries_per_user": 15.5,
    "daily_active_users": [
        {
            "date": "2024-11-14",
            "count": 25
        }
    ],
    "top_users": [
        {
            "username": "john_doe",
            "query_count": 150,
            "last_activity": "2024-11-14T15:30:00"
        }
    ],
    "retention_rate_percent": 68.5
}
```

---

### 2. Get Session Analytics

**Endpoint:** `GET /api/v1/admin/analytics/sessions`

**Description:** Retrieve chat session analytics for a specified time period.

**Query Parameters:**
- `days` (integer, optional): Number of days to analyze (default: 30, min: 1, max: 365)

**Response Example:**
```json
{
    "total_sessions": 250,
    "avg_session_duration_minutes": 8.5,
    "avg_messages_per_session": 6.2,
    "session_distribution": {
        "1-5": 45,
        "6-10": 30,
        "11-20": 20,
        "21+": 5
    },
    "top_query_topics": [
        {
            "topic": "revenue",
            "count": 85
        },
        {
            "topic": "profit",
            "count": 72
        }
    ],
    "session_trend": [
        {
            "date": "2024-11-14",
            "count": 12
        }
    ]
}
```

---

### 3. Get Document Usage Analytics

**Endpoint:** `GET /api/v1/admin/analytics/documents`

**Description:** Retrieve document usage analytics and query patterns.

**Response Example:**
```json
{
    "total_queries": 1523,
    "unique_documents_queried": 45,
    "avg_queries_per_document": 33.8,
    "most_queried_documents": [
        {
            "document_id": "doc_123",
            "filename": "financial_report_q4.pdf",
            "query_count": 150,
            "last_queried": "2024-11-14T15:30:00"
        }
    ]
}
```

---

## Configuration Management

### 1. Get All Configuration Settings

**Endpoint:** `GET /api/v1/admin/config`

**Description:** Retrieve all system configuration settings.

**Response Example:**
```json
{
    "settings": [
        {
            "setting_name": "chunk_size",
            "value": 800,
            "default_value": 800,
            "data_type": "int",
            "description": "Size of text chunks in characters",
            "category": "rag",
            "min_value": 100,
            "max_value": 2000,
            "updated_at": "2024-11-14T10:30:00",
            "updated_by": "admin_user"
        }
    ],
    "total": 15
}
```

**Configuration Categories:**
- `rag`: RAG engine settings (chunk size, overlap, top_k)
- `document`: Document processing settings (max file size)
- `llm`: LLM API settings (temperature, max tokens)
- `api`: API settings (rate limits, timeouts)

---

### 2. Get Specific Configuration Setting

**Endpoint:** `GET /api/v1/admin/config/{setting_name}`

**Description:** Retrieve detailed information for a specific configuration setting.

**Path Parameters:**
- `setting_name` (string, required): Setting identifier

**Response Example:**
```json
{
    "setting_name": "chunk_size",
    "value": 800,
    "default_value": 800,
    "data_type": "int",
    "description": "Size of text chunks in characters",
    "category": "rag",
    "min_value": 100,
    "max_value": 2000,
    "updated_at": "2024-11-14T10:30:00",
    "updated_by": "admin_user"
}
```

---

### 3. Update Configuration Setting

**Endpoint:** `PUT /api/v1/admin/config/{setting_name}`

**Description:** Update a configuration setting with validation.

**Path Parameters:**
- `setting_name` (string, required): Setting identifier

**Request Body:**
```json
{
    "value": 1000
}
```

**Response Example:**
```json
{
    "message": "Configuration setting updated successfully",
    "setting": {
        "setting_name": "chunk_size",
        "value": 1000,
        "default_value": 800,
        "data_type": "int",
        "description": "Size of text chunks in characters",
        "category": "rag",
        "min_value": 100,
        "max_value": 2000,
        "updated_at": "2024-11-14T10:35:00",
        "updated_by": "admin_user"
    }
}
```

**Validation:**
- Data type checking (int, float, str, bool)
- Range validation for numeric types
- All changes are logged for audit trail

**Error Responses:**
- **400 Bad Request:** Invalid value or validation failed
- **404 Not Found:** Setting does not exist

---

## Common Parameters

### Pagination Parameters

Used in list endpoints to control result pagination:

- `page` (integer): Page number, 1-indexed (default: 1, min: 1)
- `page_size` (integer): Records per page (default: 50, min: 10, max: 100)

### Date Parameters

Used for date range filtering:

- Format: ISO 8601 (YYYY-MM-DDTHH:MM:SS)
- Example: `2024-11-14T10:30:00`
- Parameters: `start_date`, `end_date`

### Search Parameters

Used for text-based filtering:

- Case-insensitive partial matching
- Maximum length: 100 characters
- Searches multiple fields (username, email, filename, etc.)

### Sort Parameters

Used for result ordering:

- `sort_by`: Field name to sort by
- `sort_order`: `asc` (ascending) or `desc` (descending)

---

## Error Responses

All endpoints return consistent error responses with the following structure:

```json
{
    "error": "ErrorType",
    "message": "Human-readable error message",
    "details": {
        "field": "Additional context"
    }
}
```

### Common HTTP Status Codes

- **200 OK:** Request successful
- **400 Bad Request:** Invalid request parameters or validation failed
- **401 Unauthorized:** Invalid or missing authentication token
- **403 Forbidden:** Valid token but insufficient privileges
- **404 Not Found:** Requested resource does not exist
- **429 Too Many Requests:** Rate limit exceeded
- **500 Internal Server Error:** Server-side error

### Error Types

- `AuthenticationError`: Invalid or expired token
- `AuthorizationError`: Insufficient privileges
- `ValidationError`: Invalid request parameters
- `ResourceNotFoundError`: Resource does not exist
- `InternalServerError`: Server-side error

---

## Rate Limiting

Admin endpoints have separate rate limits to prevent abuse:

- **Default Limit:** 100 requests per minute per admin
- **Response:** 429 Too Many Requests when exceeded
- **Headers:** Rate limit information in response headers

---

## Audit Trail

All administrative actions are automatically logged:

**Logged Actions:**
- User status changes
- Password resets
- Document deletions
- Configuration updates

**Log Information:**
- Admin user ID and username
- Action type and timestamp
- Resource affected
- Action details and result
- IP address

**Access Logs:** Use the activity log endpoints to view audit trail.

---

## Best Practices

### Security

1. **Protect Admin Tokens:** Never expose JWT tokens in logs or client-side code
2. **Use HTTPS:** Always use HTTPS in production
3. **Rotate Tokens:** Implement token rotation for long-running sessions
4. **Monitor Activity:** Regularly review audit logs for suspicious activity

### Performance

1. **Use Pagination:** Always use pagination for large result sets
2. **Filter Results:** Use search and date filters to reduce response size
3. **Cache When Possible:** Cache analytics data that doesn't change frequently
4. **Monitor Metrics:** Use system monitoring endpoints to track performance

### Error Handling

1. **Check Status Codes:** Always check HTTP status codes
2. **Parse Error Details:** Use error details for debugging
3. **Implement Retries:** Implement exponential backoff for transient errors
4. **Log Errors:** Log all errors for troubleshooting

---

## Support

For issues or questions about the Admin Panel APIs:

1. Check the error response details
2. Review the audit logs for context
3. Consult the system health and metrics endpoints
4. Contact system administrators

---

## Changelog

### Version 1.0.0 (2024-11-14)

- Initial release of Admin Panel APIs
- User management endpoints
- Document management endpoints
- System monitoring endpoints
- Analytics endpoints
- Configuration management endpoints
