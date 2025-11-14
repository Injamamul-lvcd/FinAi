# Authentication API Reference

## Overview

The Financial Chatbot RAG API now includes JWT-based authentication for secure access to chat and document management endpoints. All authenticated endpoints require a valid JWT token in the Authorization header.

## Base URL
```
http://localhost:8000
```

## Authentication Flow

1. **Register** a new user account (`POST /api/v1/auth/register`)
2. **Login** to receive a JWT access token (`POST /api/v1/auth/login`)
3. **Use the token** in the Authorization header for protected endpoints
4. **Token expires** after 30 minutes (configurable)

---

## Authentication Endpoints

### 1. Register User

Create a new user account.

#### `POST /api/v1/auth/register`

**Request Headers:**
- `Content-Type: application/json`

**Request Body:**
```json
{
  "username": "john_doe",
  "email": "john@example.com",
  "password": "SecurePass123!",
  "full_name": "John Doe"
}
```

**Request Fields:**
- `username` (string, required): Unique username (3-50 characters)
- `email` (string, required): Valid email address
- `password` (string, required): Password (minimum 8 characters)
- `full_name` (string, optional): User's full name (max 100 characters)

**Response (201 Created):**
```json
{
  "user_id": "507f1f77bcf86cd799439011",
  "username": "john_doe",
  "email": "john@example.com",
  "full_name": "John Doe",
  "is_active": true,
  "created_at": "2024-11-14T10:30:00"
}
```

**Error Responses:**
- `400 Bad Request`: Username or email already exists
- `422 Unprocessable Entity`: Validation error (invalid email, short password, etc.)
- `500 Internal Server Error`: Server error

**Example Request (curl):**
```bash
curl -X POST http://localhost:8000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "username": "john_doe",
    "email": "john@example.com",
    "password": "SecurePass123!",
    "full_name": "John Doe"
  }'
```

**Example Request (Python):**
```python
import requests

response = requests.post(
    "http://localhost:8000/api/v1/auth/register",
    json={
        "username": "john_doe",
        "email": "john@example.com",
        "password": "SecurePass123!",
        "full_name": "John Doe"
    }
)
user = response.json()
print(f"User created: {user['username']}")
```

---

### 2. Login

Authenticate and receive a JWT access token.

#### `POST /api/v1/auth/login`

**Request Headers:**
- `Content-Type: application/json`

**Request Body:**
```json
{
  "username": "john_doe",
  "password": "SecurePass123!"
}
```

**Request Fields:**
- `username` (string, required): Username
- `password` (string, required): Password

**Response (200 OK):**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJqb2huX2RvZSIsImV4cCI6MTYzOTU4NzYwMH0.abc123...",
  "token_type": "bearer",
  "user": {
    "user_id": "507f1f77bcf86cd799439011",
    "username": "john_doe",
    "email": "john@example.com",
    "full_name": "John Doe",
    "is_active": true
  }
}
```

**Response Fields:**
- `access_token` (string): JWT token for authentication
- `token_type` (string): Always "bearer"
- `user` (object): User information

**Error Responses:**
- `401 Unauthorized`: Invalid username or password
- `500 Internal Server Error`: Server error

**Example Request (curl):**
```bash
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "username": "john_doe",
    "password": "SecurePass123!"
  }'
```

**Example Request (Python):**
```python
import requests

response = requests.post(
    "http://localhost:8000/api/v1/auth/login",
    json={
        "username": "john_doe",
        "password": "SecurePass123!"
    }
)
data = response.json()
token = data["access_token"]
print(f"Token: {token}")
```

---

### 3. Get Current User

Get information about the currently authenticated user.

#### `GET /api/v1/auth/me`

**Request Headers:**
- `Authorization: Bearer <access_token>`

**Response (200 OK):**
```json
{
  "user_id": "507f1f77bcf86cd799439011",
  "username": "john_doe",
  "email": "john@example.com",
  "full_name": "John Doe",
  "is_active": true,
  "created_at": "2024-11-14T10:30:00"
}
```

**Error Responses:**
- `401 Unauthorized`: Invalid or missing token
- `500 Internal Server Error`: Server error

**Example Request (curl):**
```bash
curl -X GET http://localhost:8000/api/v1/auth/me \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
```

**Example Request (Python):**
```python
import requests

headers = {
    "Authorization": f"Bearer {token}"
}

response = requests.get(
    "http://localhost:8000/api/v1/auth/me",
    headers=headers
)
user = response.json()
print(f"Current user: {user['username']}")
```

---

### 4. Change Password

Change the password for the currently authenticated user.

#### `POST /api/v1/auth/change-password`

**Request Headers:**
- `Authorization: Bearer <access_token>`
- `Content-Type: application/json`

**Request Body:**
```json
{
  "old_password": "SecurePass123!",
  "new_password": "NewSecurePass456!"
}
```

**Request Fields:**
- `old_password` (string, required): Current password
- `new_password` (string, required): New password (minimum 8 characters)

**Response (200 OK):**
```json
{
  "success": true,
  "message": "Password changed successfully"
}
```

**Error Responses:**
- `400 Bad Request`: Invalid old password
- `401 Unauthorized`: Invalid or missing token
- `422 Unprocessable Entity`: New password too short
- `500 Internal Server Error`: Server error

**Example Request (curl):**
```bash
curl -X POST http://localhost:8000/api/v1/auth/change-password \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..." \
  -H "Content-Type: application/json" \
  -d '{
    "old_password": "SecurePass123!",
    "new_password": "NewSecurePass456!"
  }'
```

---

### 5. Forgot Password

Request a password reset token when user forgets their password.

#### `POST /api/v1/auth/forgot-password`

**Request Headers:**
- `Content-Type: application/json`

**Request Body:**
```json
{
  "email": "john@example.com"
}
```

**Request Fields:**
- `email` (string, required): User's email address

**Response (200 OK):**
```json
{
  "message": "If the email exists, a password reset link has been sent.",
  "reset_token": null
}
```

**Response Fields:**
- `message` (string): Success message
- `reset_token` (string, optional): Reset token (only in DEBUG mode for testing)

**Security Note:**
For security reasons, this endpoint always returns success even if the email doesn't exist. This prevents email enumeration attacks.

**Error Responses:**
- `500 Internal Server Error`: Server error

**Example Request (curl):**
```bash
curl -X POST http://localhost:8000/api/v1/auth/forgot-password \
  -H "Content-Type: application/json" \
  -d '{
    "email": "john@example.com"
  }'
```

**Example Request (Python):**
```python
import requests

response = requests.post(
    "http://localhost:8000/api/v1/auth/forgot-password",
    json={
        "email": "john@example.com"
    }
)
result = response.json()
print(result["message"])

# In DEBUG mode, you might get the token
if result.get("reset_token"):
    print(f"Reset token: {result['reset_token']}")
```

**Development/Testing:**
In DEBUG mode (`LOG_LEVEL=DEBUG` in `.env`), the reset token is returned in the response for testing purposes. In production, the token should be sent via email and not returned in the response.

---

### 6. Reset Password

Reset password using the reset token received.

#### `POST /api/v1/auth/reset-password`

**Request Headers:**
- `Content-Type: application/json`

**Request Body:**
```json
{
  "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "new_password": "NewSecurePass456!"
}
```

**Request Fields:**
- `token` (string, required): Password reset token (from forgot-password endpoint or email)
- `new_password` (string, required): New password (minimum 8 characters)

**Response (200 OK):**
```json
{
  "success": true,
  "message": "Password reset successfully. You can now login with your new password."
}
```

**Error Responses:**
- `400 Bad Request`: Invalid or expired token
- `422 Unprocessable Entity`: New password too short
- `500 Internal Server Error`: Server error

**Example Request (curl):**
```bash
curl -X POST http://localhost:8000/api/v1/auth/reset-password \
  -H "Content-Type: application/json" \
  -d '{
    "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "new_password": "NewSecurePass456!"
  }'
```

**Example Request (Python):**
```python
import requests

response = requests.post(
    "http://localhost:8000/api/v1/auth/reset-password",
    json={
        "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
        "new_password": "NewSecurePass456!"
    }
)
result = response.json()
print(result["message"])
```

**Token Expiration:**
Reset tokens are valid for 1 hour. After expiration, the user must request a new reset token.

---

## Using Authentication with Protected Endpoints

### Protected Endpoints

The following endpoints now require authentication:

- `POST /api/v1/chat` - Chat query
- All document management endpoints (optional, can be configured)

### Adding Authorization Header

**Format:**
```
Authorization: Bearer <access_token>
```

**Example with Chat Endpoint (curl):**
```bash
# 1. Login to get token
TOKEN=$(curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username": "john_doe", "password": "SecurePass123!"}' \
  | jq -r '.access_token')

# 2. Use token for chat
curl -X POST http://localhost:8000/api/v1/chat \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "What are the key financial metrics?",
    "session_id": null
  }'
```

**Example with Chat Endpoint (Python):**
```python
import requests

# 1. Login
login_response = requests.post(
    "http://localhost:8000/api/v1/auth/login",
    json={
        "username": "john_doe",
        "password": "SecurePass123!"
    }
)
token = login_response.json()["access_token"]

# 2. Use token for chat
headers = {
    "Authorization": f"Bearer {token}",
    "Content-Type": "application/json"
}

chat_response = requests.post(
    "http://localhost:8000/api/v1/chat",
    headers=headers,
    json={
        "query": "What are the key financial metrics?",
        "session_id": None
    }
)

result = chat_response.json()
print(f"Answer: {result['response']}")
```

---

## Password Reset Workflow

### Complete Forgot Password Flow

```python
import requests

BASE_URL = "http://localhost:8000"

# Step 1: User forgets password and requests reset
print("1. Requesting password reset...")
forgot_response = requests.post(
    f"{BASE_URL}/api/v1/auth/forgot-password",
    json={
        "email": "john@example.com"
    }
)

if forgot_response.status_code == 200:
    result = forgot_response.json()
    print(f"✓ {result['message']}")
    
    # In DEBUG mode, token might be returned
    reset_token = result.get('reset_token')
    if reset_token:
        print(f"  Reset token (DEBUG): {reset_token[:50]}...")
    else:
        print("  Check your email for the reset link")
else:
    print(f"✗ Request failed: {forgot_response.json()}")
    exit(1)

# Step 2: User receives token (via email in production, or from response in DEBUG)
# For this example, assume we have the token
if not reset_token:
    reset_token = input("Enter reset token from email: ")

# Step 3: User resets password with token
print("\n2. Resetting password...")
reset_response = requests.post(
    f"{BASE_URL}/api/v1/auth/reset-password",
    json={
        "token": reset_token,
        "new_password": "NewSecurePass456!"
    }
)

if reset_response.status_code == 200:
    result = reset_response.json()
    print(f"✓ {result['message']}")
else:
    print(f"✗ Reset failed: {reset_response.json()}")
    exit(1)

# Step 4: User logs in with new password
print("\n3. Logging in with new password...")
login_response = requests.post(
    f"{BASE_URL}/api/v1/auth/login",
    json={
        "username": "john_doe",
        "password": "NewSecurePass456!"
    }
)

if login_response.status_code == 200:
    data = login_response.json()
    token = data["access_token"]
    print(f"✓ Login successful!")
    print(f"  Token: {token[:50]}...")
else:
    print(f"✗ Login failed: {login_response.json()}")

print("\n✓ Password reset workflow completed successfully!")
```

---

## Complete Workflow Example

### Python Complete Example

```python
import requests

BASE_URL = "http://localhost:8000"

# Step 1: Register a new user
print("1. Registering user...")
register_response = requests.post(
    f"{BASE_URL}/api/v1/auth/register",
    json={
        "username": "jane_analyst",
        "email": "jane@example.com",
        "password": "SecurePass123!",
        "full_name": "Jane Analyst"
    }
)

if register_response.status_code == 201:
    print(f"✓ User registered: {register_response.json()['username']}")
else:
    print(f"✗ Registration failed: {register_response.json()}")
    exit(1)

# Step 2: Login to get token
print("\n2. Logging in...")
login_response = requests.post(
    f"{BASE_URL}/api/v1/auth/login",
    json={
        "username": "jane_analyst",
        "password": "SecurePass123!"
    }
)

if login_response.status_code == 200:
    token = login_response.json()["access_token"]
    print(f"✓ Login successful")
    print(f"  Token: {token[:50]}...")
else:
    print(f"✗ Login failed: {login_response.json()}")
    exit(1)

# Step 3: Get current user info
print("\n3. Getting user info...")
headers = {"Authorization": f"Bearer {token}"}

me_response = requests.get(
    f"{BASE_URL}/api/v1/auth/me",
    headers=headers
)

if me_response.status_code == 200:
    user = me_response.json()
    print(f"✓ Current user: {user['username']} ({user['email']})")
else:
    print(f"✗ Failed to get user info")

# Step 4: Upload a document (if needed)
print("\n4. Uploading document...")
with open("financial_report.pdf", "rb") as f:
    upload_response = requests.post(
        f"{BASE_URL}/api/v1/documents/upload",
        files={"file": f}
    )

if upload_response.status_code == 201:
    doc = upload_response.json()
    print(f"✓ Document uploaded: {doc['filename']} ({doc['chunks_created']} chunks)")
else:
    print(f"✗ Upload failed")

# Step 5: Ask a question
print("\n5. Asking a question...")
chat_response = requests.post(
    f"{BASE_URL}/api/v1/chat",
    headers=headers,
    json={
        "query": "What are the key financial metrics for Q4?",
        "session_id": None
    }
)

if chat_response.status_code == 200:
    result = chat_response.json()
    print(f"✓ Answer received:")
    print(f"  {result['response'][:200]}...")
    print(f"  Sources: {len(result['sources'])} documents")
    print(f"  Session ID: {result['session_id']}")
else:
    print(f"✗ Chat failed: {chat_response.json()}")

# Step 6: Follow-up question (using same session)
print("\n6. Follow-up question...")
session_id = result['session_id']

followup_response = requests.post(
    f"{BASE_URL}/api/v1/chat",
    headers=headers,
    json={
        "query": "How does that compare to Q3?",
        "session_id": session_id
    }
)

if followup_response.status_code == 200:
    result = followup_response.json()
    print(f"✓ Follow-up answer:")
    print(f"  {result['response'][:200]}...")
else:
    print(f"✗ Follow-up failed")

print("\n✓ Complete workflow finished successfully!")
```

---

## Token Management

### Token Expiration

- Default expiration: 30 minutes
- Configurable via `JWT_ACCESS_TOKEN_EXPIRE_MINUTES` in `.env`
- After expiration, you must login again to get a new token

### Token Storage

**Best Practices:**
- Store tokens securely (not in plain text files)
- Use environment variables or secure storage
- Never commit tokens to version control
- Implement token refresh logic in production apps

### Handling Expired Tokens

When a token expires, you'll receive a `401 Unauthorized` response:

```python
def make_authenticated_request(url, token, data):
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.post(url, headers=headers, json=data)
    
    if response.status_code == 401:
        # Token expired, login again
        print("Token expired, logging in again...")
        token = login()  # Your login function
        headers = {"Authorization": f"Bearer {token}"}
        response = requests.post(url, headers=headers, json=data)
    
    return response
```

---

## Security Considerations

### Password Requirements

- Minimum 8 characters
- Recommended: Mix of uppercase, lowercase, numbers, and special characters
- Passwords are hashed using bcrypt before storage

### JWT Secret Key

- Change the default secret key in production
- Use a strong, random key (at least 32 characters)
- Generate with: `openssl rand -hex 32`
- Set in `.env`: `JWT_SECRET_KEY=your-generated-key`

### HTTPS

- Always use HTTPS in production
- Tokens sent over HTTP can be intercepted
- Configure reverse proxy (nginx, Apache) with SSL/TLS

### Rate Limiting

- Consider implementing rate limiting for auth endpoints
- Prevent brute force attacks
- Use libraries like `slowapi` or `fastapi-limiter`

---

## Error Handling

### Common Error Responses

**401 Unauthorized:**
```json
{
  "detail": {
    "error": "AuthenticationError",
    "message": "Invalid authentication credentials",
    "details": null
  }
}
```

**400 Bad Request:**
```json
{
  "detail": {
    "error": "RegistrationError",
    "message": "Username already exists",
    "details": null
  }
}
```

**422 Validation Error:**
```json
{
  "detail": [
    {
      "loc": ["body", "password"],
      "msg": "String should have at least 8 characters",
      "type": "string_too_short"
    }
  ]
}
```

---

## MongoDB Session Storage

### Session Management

- Sessions are now stored in MongoDB instead of SQLite
- Each session is associated with a user
- Sessions include conversation history
- Automatic cleanup of old sessions (30 days by default)

### Session Structure

```json
{
  "_id": "550e8400-e29b-41d4-a716-446655440000",
  "session_id": "550e8400-e29b-41d4-a716-446655440000",
  "user_id": "507f1f77bcf86cd799439011",
  "created_at": "2024-11-14T10:30:00",
  "last_activity": "2024-11-14T11:45:00"
}
```

### Message Structure

```json
{
  "session_id": "550e8400-e29b-41d4-a716-446655440000",
  "role": "user",
  "content": "What are the key financial metrics?",
  "timestamp": "2024-11-14T10:30:00"
}
```

---

## Configuration

### Environment Variables

Add to your `.env` file:

```env
# MongoDB Configuration
MONGODB_CONNECTION_STRING=mongodb://localhost:27017/
MONGODB_DATABASE_NAME=financial_chatbot

# JWT Authentication Configuration
JWT_SECRET_KEY=your-secret-key-change-in-production
JWT_ALGORITHM=HS256
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=30
```

### MongoDB Setup

1. Install MongoDB locally or use MongoDB Atlas
2. Start MongoDB service:
   ```bash
   # Windows
   net start MongoDB
   
   # Linux/Mac
   sudo systemctl start mongod
   ```
3. Verify connection:
   ```bash
   mongosh
   ```

---

## Testing Authentication

### Using Postman

1. **Register User:**
   - Method: POST
   - URL: `http://localhost:8000/api/v1/auth/register`
   - Body (JSON):
     ```json
     {
       "username": "test_user",
       "email": "test@example.com",
       "password": "TestPass123!"
     }
     ```

2. **Login:**
   - Method: POST
   - URL: `http://localhost:8000/api/v1/auth/login`
   - Body (JSON):
     ```json
     {
       "username": "test_user",
       "password": "TestPass123!"
     }
     ```
   - Copy the `access_token` from response

3. **Use Token:**
   - Method: POST
   - URL: `http://localhost:8000/api/v1/chat`
   - Headers:
     - Key: `Authorization`
     - Value: `Bearer <paste_token_here>`
   - Body (JSON):
     ```json
     {
       "query": "What are the key metrics?"
     }
     ```

### Using curl

```bash
# Register
curl -X POST http://localhost:8000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{"username":"test_user","email":"test@example.com","password":"TestPass123!"}'

# Login and save token
TOKEN=$(curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"test_user","password":"TestPass123!"}' \
  | jq -r '.access_token')

# Use token
curl -X POST http://localhost:8000/api/v1/chat \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"query":"What are the key metrics?"}'
```

---

## Migration from SQLite to MongoDB

### Automatic Migration

The system now uses MongoDB for session storage. Old SQLite sessions are not automatically migrated.

### Manual Migration (if needed)

If you need to preserve old sessions:

1. Export SQLite data
2. Transform to MongoDB format
3. Import to MongoDB

Contact support for migration scripts if needed.

---

## Support

For authentication issues:
1. Verify MongoDB is running
2. Check `.env` configuration
3. Ensure JWT_SECRET_KEY is set
4. Review logs in `./logs/app.log`
5. Test with Swagger UI at `/api/docs`

## API Documentation

Interactive API documentation with authentication support:
- Swagger UI: `http://localhost:8000/api/docs`
- ReDoc: `http://localhost:8000/api/redoc`

In Swagger UI, click "Authorize" button and enter your token as: `Bearer <your_token>`
