# Authentication Setup Guide

## Overview

The Financial Chatbot RAG system has been upgraded with:
1. **MongoDB** for session storage (replacing SQLite)
2. **JWT Authentication** for secure API access
3. **User Management** with registration and login

## Prerequisites

- Python 3.9+
- MongoDB installed locally or MongoDB Atlas account
- Google API key (for Gemini)

## Quick Start

### 1. Install MongoDB

**Windows:**
```bash
# Download from https://www.mongodb.com/try/download/community
# Or use chocolatey
choco install mongodb

# Start MongoDB service
net start MongoDB
```

**Linux (Ubuntu/Debian):**
```bash
# Import MongoDB public key
wget -qO - https://www.mongodb.org/static/pgp/server-6.0.asc | sudo apt-key add -

# Add MongoDB repository
echo "deb [ arch=amd64,arm64 ] https://repo.mongodb.org/apt/ubuntu focal/mongodb-org/6.0 multiverse" | sudo tee /etc/apt/sources.list.d/mongodb-org-6.0.list

# Install MongoDB
sudo apt-get update
sudo apt-get install -y mongodb-org

# Start MongoDB
sudo systemctl start mongod
sudo systemctl enable mongod
```

**macOS:**
```bash
# Using Homebrew
brew tap mongodb/brew
brew install mongodb-community

# Start MongoDB
brew services start mongodb-community
```

**Verify MongoDB is running:**
```bash
mongosh
# Should connect successfully
```

### 2. Install Python Dependencies

```bash
# Activate virtual environment
# Windows
venv\Scripts\activate

# Linux/Mac
source venv/bin/activate

# Install new dependencies
pip install -r requirements.txt
```

### 3. Configure Environment Variables

Update your `.env` file with MongoDB and JWT settings:

```env
# MongoDB Configuration
MONGODB_CONNECTION_STRING=mongodb://localhost:27017/
MONGODB_DATABASE_NAME=financial_chatbot

# JWT Authentication Configuration
JWT_SECRET_KEY=your-secret-key-change-in-production-please-use-strong-random-key
JWT_ALGORITHM=HS256
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=30
```

**Generate a secure JWT secret key:**
```bash
# Using Python
python -c "import secrets; print(secrets.token_urlsafe(32))"

# Using OpenSSL
openssl rand -base64 32
```

### 4. Start the Application

```bash
# Development mode
uvicorn main:app --reload

# Production mode
uvicorn main:app --host 0.0.0.0 --port 8000
```

The API will be available at `http://localhost:8000`

### 5. Test Authentication

**Using curl:**

```bash
# 1. Register a user
curl -X POST http://localhost:8000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "username": "testuser",
    "email": "test@example.com",
    "password": "SecurePass123!",
    "full_name": "Test User"
  }'

# 2. Login to get token
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "username": "testuser",
    "password": "SecurePass123!"
  }'

# Copy the access_token from the response

# 3. Use token for chat
curl -X POST http://localhost:8000/api/v1/chat \
  -H "Authorization: Bearer YOUR_TOKEN_HERE" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "What are the key financial metrics?"
  }'
```

**Using Python:**

```python
import requests

BASE_URL = "http://localhost:8000"

# 1. Register
response = requests.post(
    f"{BASE_URL}/api/v1/auth/register",
    json={
        "username": "testuser",
        "email": "test@example.com",
        "password": "SecurePass123!",
        "full_name": "Test User"
    }
)
print("Registration:", response.json())

# 2. Login
response = requests.post(
    f"{BASE_URL}/api/v1/auth/login",
    json={
        "username": "testuser",
        "password": "SecurePass123!"
    }
)
token = response.json()["access_token"]
print("Token:", token[:50] + "...")

# 3. Use token
headers = {"Authorization": f"Bearer {token}"}
response = requests.post(
    f"{BASE_URL}/api/v1/chat",
    headers=headers,
    json={"query": "What are the key financial metrics?"}
)
print("Chat response:", response.json())
```

## API Endpoints

### Authentication Endpoints

| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| POST | `/api/v1/auth/register` | Register new user | No |
| POST | `/api/v1/auth/login` | Login and get token | No |
| GET | `/api/v1/auth/me` | Get current user info | Yes |
| POST | `/api/v1/auth/change-password` | Change password | Yes |
| POST | `/api/v1/auth/forgot-password` | Request password reset | No |
| POST | `/api/v1/auth/reset-password` | Reset password with token | No |

### Protected Endpoints

| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| POST | `/api/v1/chat` | Chat query | **Yes** |
| POST | `/api/v1/documents/upload` | Upload document | No (optional) |
| GET | `/api/v1/documents` | List documents | No (optional) |
| DELETE | `/api/v1/documents/{id}` | Delete document | No (optional) |
| GET | `/api/v1/documents/stats` | Get statistics | No (optional) |
| GET | `/api/v1/health` | Health check | No |

## MongoDB Collections

The system creates the following MongoDB collections:

### 1. users
Stores user account information:
```json
{
  "_id": ObjectId("..."),
  "username": "testuser",
  "email": "test@example.com",
  "hashed_password": "$2b$12$...",
  "full_name": "Test User",
  "is_active": true,
  "created_at": ISODate("2024-11-14T10:30:00Z"),
  "updated_at": ISODate("2024-11-14T10:30:00Z"),
  "last_login": ISODate("2024-11-14T11:00:00Z")
}
```

### 2. sessions
Stores conversation sessions:
```json
{
  "_id": "550e8400-e29b-41d4-a716-446655440000",
  "session_id": "550e8400-e29b-41d4-a716-446655440000",
  "user_id": "507f1f77bcf86cd799439011",
  "created_at": ISODate("2024-11-14T10:30:00Z"),
  "last_activity": ISODate("2024-11-14T11:45:00Z")
}
```

### 3. messages
Stores conversation messages:
```json
{
  "_id": ObjectId("..."),
  "session_id": "550e8400-e29b-41d4-a716-446655440000",
  "role": "user",
  "content": "What are the key financial metrics?",
  "timestamp": ISODate("2024-11-14T10:30:00Z")
}
```

### Password Reset Fields (in users collection)
When a user requests password reset, these fields are added:
```json
{
  "reset_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "reset_token_created": ISODate("2024-11-14T10:30:00Z")
}
```

These fields are automatically removed after successful password reset.

## Viewing MongoDB Data

### Using MongoDB Compass (GUI)

1. Download MongoDB Compass: https://www.mongodb.com/products/compass
2. Connect to: `mongodb://localhost:27017`
3. Select database: `financial_chatbot`
4. Browse collections: `users`, `sessions`, `messages`

### Using mongosh (CLI)

```bash
# Connect to MongoDB
mongosh

# Switch to database
use financial_chatbot

# View users
db.users.find().pretty()

# View sessions
db.sessions.find().pretty()

# View messages
db.messages.find().pretty()

# Count documents
db.users.countDocuments()
db.sessions.countDocuments()
db.messages.countDocuments()

# Find user by username
db.users.findOne({username: "testuser"})

# Find sessions for a user
db.sessions.find({user_id: "507f1f77bcf86cd799439011"})

# Find messages in a session
db.messages.find({session_id: "550e8400-e29b-41d4-a716-446655440000"})
```

## Troubleshooting

### MongoDB Connection Issues

**Error: "Failed to connect to MongoDB"**

1. Check if MongoDB is running:
   ```bash
   # Windows
   net start MongoDB
   
   # Linux/Mac
   sudo systemctl status mongod
   ```

2. Verify connection string in `.env`:
   ```env
   MONGODB_CONNECTION_STRING=mongodb://localhost:27017/
   ```

3. Test connection manually:
   ```bash
   mongosh
   ```

### Authentication Issues

**Error: "Invalid authentication credentials"**

1. Verify token is included in header:
   ```
   Authorization: Bearer <your_token>
   ```

2. Check token hasn't expired (default: 30 minutes)

3. Login again to get a new token

**Error: "Username already exists"**

- Username must be unique
- Try a different username
- Or login with existing credentials

### JWT Secret Key Issues

**Error: "Invalid token"**

1. Ensure JWT_SECRET_KEY is set in `.env`
2. Don't change the secret key after creating tokens
3. If you change it, all existing tokens become invalid

## Security Best Practices

### Production Deployment

1. **Change JWT Secret Key:**
   ```bash
   # Generate strong key
   python -c "import secrets; print(secrets.token_urlsafe(32))"
   ```

2. **Use HTTPS:**
   - Configure reverse proxy (nginx, Apache)
   - Obtain SSL certificate (Let's Encrypt)
   - Never send tokens over HTTP

3. **Secure MongoDB:**
   ```bash
   # Enable authentication
   mongosh
   use admin
   db.createUser({
     user: "admin",
     pwd: "strong_password",
     roles: ["userAdminAnyDatabase"]
   })
   ```
   
   Update connection string:
   ```env
   MONGODB_CONNECTION_STRING=mongodb://admin:strong_password@localhost:27017/
   ```

4. **Environment Variables:**
   - Never commit `.env` to version control
   - Use environment-specific configurations
   - Rotate secrets regularly

5. **Rate Limiting:**
   - Implement rate limiting for auth endpoints
   - Prevent brute force attacks
   - Use libraries like `slowapi`

6. **Password Policy:**
   - Enforce strong passwords
   - Implement password complexity rules
   - Add password reset functionality

## Migration from SQLite

### Automatic Handling

The system now uses MongoDB for new sessions. Old SQLite sessions are not automatically migrated but the SQLite database path is still in settings for backward compatibility.

### Clean Start

If you want to start fresh:

1. Delete old SQLite database:
   ```bash
   rm ./data/sessions.db
   ```

2. MongoDB will automatically create new collections

3. Users need to register new accounts

## API Documentation

Access interactive API documentation:

- **Swagger UI:** http://localhost:8000/api/docs
- **ReDoc:** http://localhost:8000/api/redoc

In Swagger UI:
1. Click "Authorize" button (top right)
2. Enter: `Bearer <your_token>`
3. Click "Authorize"
4. Now you can test protected endpoints

## Next Steps

1. **Test the system:**
   - Register a user
   - Login and get token
   - Upload a document
   - Ask questions via chat

2. **Review documentation:**
   - `API_AUTHENTICATION.md` - Complete API reference
   - `README.md` - General system documentation
   - `HOW_IT_WORKS.md` - System architecture

3. **Customize settings:**
   - Adjust token expiration time
   - Configure MongoDB connection
   - Set up production environment

4. **Monitor logs:**
   - Check `./logs/app.log` for issues
   - Monitor MongoDB logs
   - Set up log rotation

## Support

For issues:
1. Check logs in `./logs/app.log`
2. Verify MongoDB is running
3. Test with Swagger UI at `/api/docs`
4. Review this guide and `API_AUTHENTICATION.md`

## Summary of Changes

### What's New

✅ **MongoDB Session Storage**
- Replaces SQLite for better scalability
- Supports user-specific sessions
- Better performance for concurrent users

✅ **JWT Authentication**
- Secure token-based authentication
- 30-minute token expiration (configurable)
- Bearer token in Authorization header

✅ **User Management**
- User registration with email validation
- Secure password hashing (bcrypt)
- Password change functionality
- User profile management

✅ **Protected Endpoints**
- Chat endpoint now requires authentication
- User-specific conversation history
- Session isolation per user

### Breaking Changes

⚠️ **Chat endpoint now requires authentication**
- Must include `Authorization: Bearer <token>` header
- Register and login before using chat

⚠️ **MongoDB required**
- Must have MongoDB running locally or use MongoDB Atlas
- Old SQLite sessions not automatically migrated

### Backward Compatibility

✓ Document management endpoints still work without auth (optional)
✓ Health check endpoint remains public
✓ Existing document uploads are preserved
✓ Vector database (ChromaDB) unchanged


---

## Testing Forgot Password Feature

### Using curl

**Step 1: Request password reset**
```bash
curl -X POST http://localhost:8000/api/v1/auth/forgot-password \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com"}'
```

**Response:**
```json
{
  "message": "If the email exists, a password reset link has been sent.",
  "reset_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
}
```

**Step 2: Get reset token (for testing)**

In DEBUG mode, the token is returned in the response. Otherwise, check MongoDB:
```bash
mongosh
use financial_chatbot
db.users.findOne({email: "test@example.com"}, {reset_token: 1, username: 1})
```

**Step 3: Reset password with token**
```bash
curl -X POST http://localhost:8000/api/v1/auth/reset-password \
  -H "Content-Type: application/json" \
  -d '{
    "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "new_password": "NewPassword123!"
  }'
```

**Step 4: Login with new password**
```bash
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"test_user","password":"NewPassword123!"}'
```

### Using Python

```python
import requests

BASE_URL = "http://localhost:8000"

# Step 1: Request password reset
print("Requesting password reset...")
response = requests.post(
    f"{BASE_URL}/api/v1/auth/forgot-password",
    json={"email": "test@example.com"}
)
result = response.json()
print(result["message"])

# Get token (in DEBUG mode or from MongoDB)
reset_token = result.get("reset_token")
if not reset_token:
    reset_token = input("Enter reset token: ")

# Step 2: Reset password
print("\nResetting password...")
response = requests.post(
    f"{BASE_URL}/api/v1/auth/reset-password",
    json={
        "token": reset_token,
        "new_password": "NewPassword123!"
    }
)
print(response.json()["message"])

# Step 3: Login with new password
print("\nLogging in with new password...")
response = requests.post(
    f"{BASE_URL}/api/v1/auth/login",
    json={
        "username": "test_user",
        "password": "NewPassword123!"
    }
)
token = response.json()["access_token"]
print(f"Login successful! Token: {token[:50]}...")
```

### Using Postman

**1. Request Password Reset:**
- Method: POST
- URL: `http://localhost:8000/api/v1/auth/forgot-password`
- Body (JSON):
  ```json
  {
    "email": "test@example.com"
  }
  ```
- Copy the `reset_token` from response (if in DEBUG mode)

**2. Reset Password:**
- Method: POST
- URL: `http://localhost:8000/api/v1/auth/reset-password`
- Body (JSON):
  ```json
  {
    "token": "paste_reset_token_here",
    "new_password": "NewPassword123!"
  }
  ```

**3. Login with New Password:**
- Method: POST
- URL: `http://localhost:8000/api/v1/auth/login`
- Body (JSON):
  ```json
  {
    "username": "test_user",
    "password": "NewPassword123!"
  }
  ```

---

## Forgot Password Implementation Details

### Token Expiration

- Reset tokens are valid for **1 hour**
- After expiration, user must request a new token
- Tokens are single-use (deleted after successful reset)

### Security Features

1. **Email Enumeration Prevention:**
   - Always returns success message, even if email doesn't exist
   - Prevents attackers from discovering valid email addresses

2. **Token Storage:**
   - Reset token stored in user document
   - Token is hashed and validated on use
   - Token automatically removed after successful reset

3. **Rate Limiting (Recommended):**
   - Implement rate limiting on forgot-password endpoint
   - Prevent abuse and spam
   - Example: 3 requests per hour per IP

### Production Considerations

#### Email Integration

In production, integrate an email service to send reset links:

```python
# Example with SendGrid
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail

def send_reset_email(email: str, reset_token: str):
    reset_link = f"https://yourapp.com/reset-password?token={reset_token}"
    
    message = Mail(
        from_email='noreply@yourapp.com',
        to_emails=email,
        subject='Password Reset Request',
        html_content=f'''
            <h2>Password Reset</h2>
            <p>Click the link below to reset your password:</p>
            <a href="{reset_link}">Reset Password</a>
            <p>This link expires in 1 hour.</p>
            <p>If you didn't request this, please ignore this email.</p>
        '''
    )
    
    sg = SendGridAPIClient(os.environ.get('SENDGRID_API_KEY'))
    sg.send(message)
```

#### Environment Variables

Add to `.env`:
```env
# Email Configuration (for production)
SENDGRID_API_KEY=your_sendgrid_api_key
EMAIL_FROM=noreply@yourapp.com
RESET_PASSWORD_URL=https://yourapp.com/reset-password
```

#### Frontend Integration

Create a password reset page that:
1. Extracts token from URL query parameter
2. Shows password reset form
3. Calls `/api/v1/auth/reset-password` endpoint
4. Redirects to login on success

Example URL: `https://yourapp.com/reset-password?token=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...`

### Troubleshooting

**Issue: "Invalid or expired reset token"**
- Token may have expired (1 hour limit)
- Token may have been used already
- Request a new reset token

**Issue: Reset token not returned in response**
- This is normal in production mode
- Set `LOG_LEVEL=DEBUG` in `.env` for testing
- Or check MongoDB for the token

**Issue: Email not found**
- System returns success for security
- Check if email is correct
- Verify user exists in MongoDB

### Monitoring

Monitor these metrics in production:
- Number of password reset requests
- Failed reset attempts
- Token expiration rate
- Time between request and reset

### Best Practices

1. **Always use HTTPS** for password reset endpoints
2. **Implement rate limiting** to prevent abuse
3. **Log all password reset attempts** for security auditing
4. **Send confirmation email** after successful password reset
5. **Invalidate all sessions** after password reset (optional)
6. **Use strong, random tokens** (JWT with 1-hour expiration)
7. **Never expose whether email exists** in the system
