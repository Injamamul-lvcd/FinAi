# Admin Panel APIs Design Document

## Overview

The Admin Panel APIs provide a comprehensive administrative interface for the Financial Chatbot RAG System. These APIs enable administrators to manage users, documents, monitor system health, view analytics, and configure system settings through secure, role-based REST endpoints.

The design extends the existing FastAPI application with a new admin router module, leveraging the current MongoDB infrastructure for user management and adding new collections for activity logging and system metrics. All admin endpoints require JWT authentication with administrator role verification.

## Architecture

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Admin Panel Frontend                      │
│                   (External - Not in scope)                  │
└────────────────────────────┬─────────────────────────────────┘
                             │ HTTPS/REST
                             ▼
┌─────────────────────────────────────────────────────────────┐
│                      FastAPI Application                     │
│  ┌──────────────────────────────────────────────────────┐   │
│  │              Admin Router (/api/v1/admin)            │   │
│  │  - User Management Endpoints                         │   │
│  │  - Document Management Endpoints                     │   │
│  │  - System Monitoring Endpoints                       │   │
│  │  - Analytics Endpoints                               │   │
│  │  - Configuration Endpoints                           │   │
│  └──────────────────────────────────────────────────────┘   │
│  ┌──────────────────────────────────────────────────────┐   │
│  │           Admin Middleware & Dependencies            │   │
│  │  - JWT Token Verification                            │   │
│  │  - Admin Role Authorization                          │   │
│  │  - Activity Logging                                  │   │
│  └──────────────────────────────────────────────────────┘   │
└────────────────────────────┬─────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────┐
│                      Service Layer                           │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │ Admin User   │  │ Admin Doc    │  │ Admin        │      │
│  │ Service      │  │ Service      │  │ Analytics    │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │ System       │  │ Activity     │  │ Config       │      │
│  │ Monitor      │  │ Logger       │  │ Manager      │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
└────────────────────────────┬─────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────┐
│                      Data Layer                              │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │   MongoDB    │  │   ChromaDB   │  │   SQLite     │      │
│  │   - users    │  │   - vectors  │  │   - sessions │      │
│  │   - activity │  │   - metadata │  │              │      │
│  │   - config   │  │              │  │              │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
└─────────────────────────────────────────────────────────────┘
```

### Component Integration

The admin panel integrates with existing system components:

1. **Authentication System**: Extends the existing `AuthService` to support admin role verification
2. **Document Management**: Leverages existing `VectorStore` and `DocumentProcessor` for document operations
3. **Session Management**: Uses existing `SessionManager` for chat session analytics
4. **Configuration**: Extends existing `Settings` class for dynamic configuration management

## Components and Interfaces

### 1. Admin Router (`api/routes/admin.py`)

Main FastAPI router handling all admin endpoints with role-based access control.

**Endpoints:**

```python
# User Management
GET    /api/v1/admin/users                    # List all users
GET    /api/v1/admin/users/{user_id}          # Get user details
PUT    /api/v1/admin/users/{user_id}/status   # Enable/disable user
POST   /api/v1/admin/users/{user_id}/reset-password  # Reset password
GET    /api/v1/admin/users/{user_id}/activity # Get user activity logs

# Document Management
GET    /api/v1/admin/documents                # List all documents
DELETE /api/v1/admin/documents/{document_id}  # Delete document
GET    /api/v1/admin/documents/stats          # Document statistics

# System Monitoring
GET    /api/v1/admin/system/health            # System health status
GET    /api/v1/admin/system/metrics           # System metrics
GET    /api/v1/admin/system/storage           # Storage usage
GET    /api/v1/admin/system/logs              # Error logs

# Analytics
GET    /api/v1/admin/analytics/users          # User engagement metrics
GET    /api/v1/admin/analytics/sessions       # Session analytics
GET    /api/v1/admin/analytics/api-usage      # API usage metrics

# Configuration
GET    /api/v1/admin/config                   # Get all settings
PUT    /api/v1/admin/config/{setting_name}    # Update setting

# Admin Authentication
POST   /api/v1/admin/auth/login               # Admin login
```

### 2. Admin Service Layer

#### AdminUserService (`services/admin_user_service.py`)

Manages user-related administrative operations.

**Key Methods:**
```python
class AdminUserService:
    def get_users(
        self,
        page: int = 1,
        page_size: int = 50,
        search: Optional[str] = None,
        sort_by: str = "created_at",
        sort_order: str = "desc"
    ) -> Dict
    
    def get_user_details(self, user_id: str) -> Optional[Dict]
    
    def update_user_status(
        self,
        user_id: str,
        is_active: bool,
        admin_id: str,
        reason: Optional[str] = None
    ) -> bool
    
    def reset_user_password(
        self,
        user_id: str,
        admin_id: str
    ) -> Optional[str]
    
    def get_user_activity(
        self,
        user_id: str,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        page: int = 1,
        page_size: int = 50
    ) -> Dict
```

#### AdminDocumentService (`services/admin_document_service.py`)

Manages document-related administrative operations.

**Key Methods:**
```python
class AdminDocumentService:
    def get_all_documents(
        self,
        page: int = 1,
        page_size: int = 50,
        search: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> Dict
    
    def delete_document(
        self,
        document_id: str,
        admin_id: str
    ) -> bool
    
    def get_document_statistics(self) -> Dict
    
    def get_document_usage_stats(self) -> Dict
```

#### SystemMonitorService (`services/system_monitor_service.py`)

Monitors system health and performance metrics.

**Key Methods:**
```python
class SystemMonitorService:
    def get_health_status(self) -> Dict
    
    def get_system_metrics(self) -> Dict
    
    def get_storage_metrics(self) -> Dict
    
    def get_api_usage_metrics(
        self,
        hours: int = 24
    ) -> Dict
    
    def get_error_logs(
        self,
        severity: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        page: int = 1,
        page_size: int = 50
    ) -> Dict
```

#### AnalyticsService (`services/analytics_service.py`)

Provides analytics and reporting functionality.

**Key Methods:**
```python
class AnalyticsService:
    def get_user_engagement_metrics(
        self,
        days: int = 30
    ) -> Dict
    
    def get_session_analytics(
        self,
        days: int = 30
    ) -> Dict
    
    def get_document_usage_analytics(self) -> Dict
    
    def get_query_topic_analysis(
        self,
        limit: int = 10
    ) -> List[Dict]
```

#### ActivityLogger (`services/activity_logger.py`)

Logs administrative actions for audit trail.

**Key Methods:**
```python
class ActivityLogger:
    def log_action(
        self,
        admin_id: str,
        action_type: str,
        resource_type: str,
        resource_id: str,
        details: Optional[Dict] = None,
        ip_address: Optional[str] = None
    ) -> bool
    
    def get_activity_logs(
        self,
        user_id: Optional[str] = None,
        action_type: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        page: int = 1,
        page_size: int = 50
    ) -> Dict
```

#### ConfigManager (`services/config_manager.py`)

Manages dynamic system configuration.

**Key Methods:**
```python
class ConfigManager:
    def get_all_settings(self) -> Dict
    
    def get_setting(self, setting_name: str) -> Optional[Dict]
    
    def update_setting(
        self,
        setting_name: str,
        value: Any,
        admin_id: str
    ) -> bool
    
    def validate_setting_value(
        self,
        setting_name: str,
        value: Any
    ) -> Tuple[bool, Optional[str]]
```

### 3. Authentication & Authorization

#### Admin Dependency (`utils/admin_auth.py`)

FastAPI dependency for admin authentication and authorization.

**Implementation:**
```python
async def get_current_admin(
    token: str = Depends(oauth2_scheme),
    auth_service: AuthService = Depends(get_auth_service)
) -> Dict:
    """
    Verify JWT token and ensure user has admin role.
    
    Raises:
        HTTPException: 401 if token invalid, 403 if not admin
    """
    # Decode token
    payload = auth_service.decode_token(token)
    if not payload:
        raise HTTPException(status_code=401, detail="Invalid token")
    
    # Get user
    username = payload.get("sub")
    user = auth_service.get_user_by_username(username)
    
    if not user:
        raise HTTPException(status_code=401, detail="User not found")
    
    # Check admin role
    if not user.get("is_admin", False):
        raise HTTPException(status_code=403, detail="Admin access required")
    
    return user
```

### 4. Middleware

#### Activity Logging Middleware

Automatically logs all admin actions for audit trail.

```python
class AdminActivityMiddleware:
    async def __call__(self, request: Request, call_next):
        # Extract admin user from token
        # Log request details
        # Call endpoint
        # Log response status
        # Return response
```

## Data Models

### MongoDB Collections

#### users Collection (Extended)

```python
{
    "_id": ObjectId,
    "username": str,
    "email": str,
    "hashed_password": str,
    "full_name": Optional[str],
    "is_active": bool,
    "is_admin": bool,  # NEW: Admin role flag
    "created_at": datetime,
    "updated_at": datetime,
    "last_login": Optional[datetime],
    "password_reset_required": bool  # NEW: Force password change
}
```

#### activity_logs Collection (NEW)

```python
{
    "_id": ObjectId,
    "admin_id": str,  # User ID of admin who performed action
    "admin_username": str,
    "action_type": str,  # e.g., "user_disabled", "document_deleted"
    "resource_type": str,  # e.g., "user", "document", "config"
    "resource_id": str,
    "details": dict,  # Additional action-specific details
    "ip_address": Optional[str],
    "timestamp": datetime,
    "result": str  # "success" or "failure"
}
```

#### system_config Collection (NEW)

```python
{
    "_id": ObjectId,
    "setting_name": str,  # Unique setting identifier
    "value": Any,  # Current value
    "default_value": Any,
    "data_type": str,  # "int", "float", "str", "bool"
    "min_value": Optional[float],
    "max_value": Optional[float],
    "description": str,
    "category": str,  # "rag", "document", "api", etc.
    "updated_at": datetime,
    "updated_by": Optional[str]  # Admin username
}
```

#### api_metrics Collection (NEW)

```python
{
    "_id": ObjectId,
    "endpoint": str,
    "method": str,
    "status_code": int,
    "response_time_ms": float,
    "timestamp": datetime,
    "user_id": Optional[str],
    "error_message": Optional[str]
}
```

### ChromaDB Metadata (Extended)

Existing document metadata in ChromaDB will be extended:

```python
{
    "document_id": str,
    "filename": str,
    "upload_date": str,
    "user_id": str,  # NEW: Track uploader
    "username": str,  # NEW: Track uploader username
    "file_size_bytes": int,  # NEW: Track file size
    "query_count": int  # NEW: Track usage (updated on queries)
}
```

### Pydantic Models

#### Admin Request/Response Models (`models/admin_schemas.py`)

```python
# User Management
class UserListResponse(BaseModel):
    users: List[UserDetail]
    total: int
    page: int
    page_size: int

class UserDetail(BaseModel):
    user_id: str
    username: str
    email: str
    full_name: Optional[str]
    is_active: bool
    is_admin: bool
    created_at: str
    last_login: Optional[str]
    document_count: int
    query_count: int

class UserStatusUpdate(BaseModel):
    is_active: bool
    reason: Optional[str]

class PasswordResetResponse(BaseModel):
    temporary_password: str
    expires_at: str

# Document Management
class AdminDocumentInfo(BaseModel):
    document_id: str
    filename: str
    uploader_username: str
    uploader_user_id: str
    upload_date: str
    file_size_mb: float
    chunks: int
    query_count: int

class AdminDocumentListResponse(BaseModel):
    documents: List[AdminDocumentInfo]
    total: int
    page: int
    page_size: int

class DocumentStatsResponse(BaseModel):
    total_documents: int
    total_chunks: int
    total_size_mb: float
    avg_chunks_per_doc: float
    documents_by_type: Dict[str, int]
    upload_trend: List[Dict[str, Any]]
    top_documents: List[Dict[str, Any]]

# System Monitoring
class SystemHealthResponse(BaseModel):
    status: str
    vector_db_status: str
    llm_api_status: str
    session_db_status: str
    mongodb_status: str
    timestamp: str
    error_details: Optional[Dict]

class SystemMetricsResponse(BaseModel):
    active_sessions: int
    total_requests_24h: int
    avg_response_time_ms: float
    memory_usage_percent: float
    disk_usage_percent: float
    uptime_hours: float

class StorageMetricsResponse(BaseModel):
    vector_db_size_mb: float
    session_db_size_mb: float
    mongodb_size_mb: float
    total_document_size_mb: float
    available_disk_gb: float
    disk_usage_percent: float
    growth_rate_7d_percent: float

# Analytics
class UserEngagementMetrics(BaseModel):
    total_users: int
    active_users_30d: int
    avg_queries_per_user: float
    daily_active_users: List[Dict[str, Any]]
    top_users: List[Dict[str, Any]]
    retention_rate_percent: float

class SessionAnalytics(BaseModel):
    total_sessions: int
    avg_session_duration_minutes: float
    avg_messages_per_session: float
    session_distribution: Dict[str, int]
    top_query_topics: List[Dict[str, Any]]
    session_trend: List[Dict[str, Any]]

# Configuration
class ConfigSetting(BaseModel):
    setting_name: str
    value: Any
    default_value: Any
    data_type: str
    description: str
    category: str
    min_value: Optional[float]
    max_value: Optional[float]
    updated_at: Optional[str]
    updated_by: Optional[str]

class ConfigUpdateRequest(BaseModel):
    value: Any

# Activity Logs
class ActivityLogEntry(BaseModel):
    log_id: str
    admin_username: str
    action_type: str
    resource_type: str
    resource_id: str
    details: Dict
    ip_address: Optional[str]
    timestamp: str
    result: str

class ActivityLogResponse(BaseModel):
    logs: List[ActivityLogEntry]
    total: int
    page: int
    page_size: int
```

## Error Handling

### Admin-Specific Exceptions

```python
class AdminAuthorizationError(Exception):
    """Raised when user lacks admin privileges"""
    pass

class ResourceNotFoundError(Exception):
    """Raised when requested resource doesn't exist"""
    pass

class ConfigValidationError(Exception):
    """Raised when configuration value is invalid"""
    pass

class SystemHealthError(Exception):
    """Raised when system component is unhealthy"""
    pass
```

### Error Response Format

All admin endpoints return consistent error responses:

```python
{
    "error": "ErrorType",
    "message": "Human-readable error message",
    "details": {
        "field": "Additional context"
    },
    "timestamp": "2024-11-14T10:30:00Z"
}
```

## Testing Strategy

### Unit Tests

1. **Service Layer Tests**
   - Test each service method independently
   - Mock database connections
   - Verify correct data transformations
   - Test error handling

2. **Authentication Tests**
   - Test admin role verification
   - Test token validation
   - Test unauthorized access handling

3. **Validation Tests**
   - Test Pydantic model validation
   - Test configuration value validation
   - Test query parameter validation

### Integration Tests

1. **Endpoint Tests**
   - Test each admin endpoint with valid admin token
   - Test endpoints with non-admin token (should fail)
   - Test endpoints without token (should fail)
   - Test pagination and filtering
   - Test error responses

2. **Database Integration Tests**
   - Test MongoDB operations
   - Test ChromaDB queries
   - Test SQLite session queries
   - Test transaction handling

3. **End-to-End Tests**
   - Test complete admin workflows
   - Test user management flow
   - Test document management flow
   - Test analytics data accuracy

### Performance Tests

1. **Load Testing**
   - Test admin endpoints under concurrent requests
   - Test large dataset pagination
   - Test analytics query performance

2. **Stress Testing**
   - Test system behavior with many users
   - Test with large document collections
   - Test with extensive activity logs

## Security Considerations

### Authentication & Authorization

1. **JWT Token Security**
   - Admin tokens expire after 8 hours
   - Tokens include admin role claim
   - Token signature verification on every request
   - Refresh token mechanism for extended sessions

2. **Role-Based Access Control**
   - Separate admin role flag in user document
   - Admin role verified on every admin endpoint
   - Activity logging for all admin actions

3. **Password Security**
   - Temporary passwords are cryptographically random
   - Password reset requires admin authentication
   - Password changes are logged

### Data Protection

1. **Sensitive Data Handling**
   - Passwords never returned in responses
   - User emails masked in logs
   - IP addresses anonymized after 90 days

2. **Audit Trail**
   - All admin actions logged with timestamp
   - Logs include admin identifier and IP address
   - Logs are immutable (append-only)

### API Security

1. **Rate Limiting**
   - Admin endpoints have separate rate limits
   - Higher limits than regular user endpoints
   - Per-admin rate limiting

2. **Input Validation**
   - All inputs validated with Pydantic
   - SQL injection prevention (using ORMs)
   - XSS prevention (input sanitization)

3. **CORS Configuration**
   - Restrict admin endpoints to specific origins
   - Separate CORS policy for admin routes

## Performance Optimization

### Database Indexing

```python
# MongoDB Indexes
users_collection.create_index("username", unique=True)
users_collection.create_index("email", unique=True)
users_collection.create_index("is_admin")
users_collection.create_index("created_at")
users_collection.create_index("last_login")

activity_logs_collection.create_index("admin_id")
activity_logs_collection.create_index("timestamp")
activity_logs_collection.create_index([("resource_type", 1), ("resource_id", 1)])

api_metrics_collection.create_index("timestamp")
api_metrics_collection.create_index("endpoint")

system_config_collection.create_index("setting_name", unique=True)
```

### Caching Strategy

1. **Configuration Caching**
   - Cache system configuration in memory
   - Invalidate cache on configuration updates
   - TTL of 5 minutes for config cache

2. **Statistics Caching**
   - Cache expensive analytics queries
   - TTL of 15 minutes for analytics data
   - Cache key includes query parameters

3. **User Data Caching**
   - Cache user list for pagination
   - Invalidate on user updates
   - TTL of 2 minutes

### Query Optimization

1. **Pagination**
   - Use cursor-based pagination for large datasets
   - Limit page size to maximum 100 records
   - Index fields used for sorting

2. **Aggregation Pipelines**
   - Use MongoDB aggregation for analytics
   - Pre-compute common metrics
   - Use projection to limit returned fields

3. **Batch Operations**
   - Batch document metadata queries
   - Batch user activity queries
   - Use bulk operations for updates

## Deployment Considerations

### Environment Variables

New environment variables for admin panel:

```env
# Admin Configuration
ADMIN_TOKEN_EXPIRE_HOURS=8
ADMIN_RATE_LIMIT_PER_MINUTE=100
ENABLE_ADMIN_PANEL=true

# Activity Logging
ACTIVITY_LOG_RETENTION_DAYS=365
ANONYMIZE_IP_AFTER_DAYS=90

# Analytics
ANALYTICS_CACHE_TTL_MINUTES=15
METRICS_RETENTION_DAYS=90
```

### Database Migrations

1. **Add is_admin field to existing users**
   - Default to False for all existing users
   - Manually set first admin user

2. **Create new collections**
   - activity_logs
   - system_config
   - api_metrics

3. **Extend ChromaDB metadata**
   - Add user_id, username, file_size_bytes to existing documents
   - Backfill from existing data where possible

### Monitoring & Logging

1. **Admin Action Monitoring**
   - Alert on bulk user deactivations
   - Alert on configuration changes
   - Alert on bulk document deletions

2. **Performance Monitoring**
   - Track admin endpoint response times
   - Monitor database query performance
   - Track cache hit rates

3. **Security Monitoring**
   - Alert on failed admin login attempts
   - Alert on unauthorized access attempts
   - Monitor for suspicious activity patterns

## Future Enhancements

1. **Advanced Analytics**
   - Machine learning for usage predictions
   - Anomaly detection for security
   - Custom report generation

2. **Bulk Operations**
   - Bulk user import/export
   - Bulk document operations
   - Batch configuration updates

3. **Notification System**
   - Email notifications for admin actions
   - Webhook support for external integrations
   - Real-time alerts dashboard

4. **Audit Compliance**
   - Export audit logs in standard formats
   - Compliance reporting (GDPR, SOC2)
   - Data retention policy enforcement
