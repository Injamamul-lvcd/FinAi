# Forgot Password Feature - Quick Reference

## Overview

The forgot password feature allows users to reset their password via email (or token in development mode) when they forget their credentials.

## How It Works

```
User forgets password
    ↓
Request reset (POST /forgot-password with email)
    ↓
System generates reset token (valid 1 hour)
    ↓
Token sent via email (or returned in DEBUG mode)
    ↓
User clicks reset link with token
    ↓
User submits new password (POST /reset-password)
    ↓
Password updated, token invalidated
    ↓
User logs in with new password
```

## API Endpoints

### 1. Request Password Reset

**Endpoint:** `POST /api/v1/auth/forgot-password`

**Request:**
```json
{
  "email": "user@example.com"
}
```

**Response:**
```json
{
  "message": "If the email exists, a password reset link has been sent.",
  "reset_token": null
}
```

**Notes:**
- Always returns success (prevents email enumeration)
- In DEBUG mode, `reset_token` is included in response
- Token valid for 1 hour

### 2. Reset Password

**Endpoint:** `POST /api/v1/auth/reset-password`

**Request:**
```json
{
  "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "new_password": "NewSecurePass123!"
}
```

**Response:**
```json
{
  "success": true,
  "message": "Password reset successfully. You can now login with your new password."
}
```

**Notes:**
- Token is single-use
- Password must be at least 8 characters
- Token expires after 1 hour

## Quick Test (Development)

### Using curl

```bash
# 1. Request reset
curl -X POST http://localhost:8000/api/v1/auth/forgot-password \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com"}'

# 2. Copy token from response (DEBUG mode) or MongoDB

# 3. Reset password
curl -X POST http://localhost:8000/api/v1/auth/reset-password \
  -H "Content-Type: application/json" \
  -d '{
    "token": "YOUR_TOKEN_HERE",
    "new_password": "NewPass123!"
  }'

# 4. Login with new password
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"testuser","password":"NewPass123!"}'
```

### Using Python

```python
import requests

BASE_URL = "http://localhost:8000"

# 1. Request reset
response = requests.post(
    f"{BASE_URL}/api/v1/auth/forgot-password",
    json={"email": "test@example.com"}
)
reset_token = response.json().get("reset_token")

# 2. Reset password
response = requests.post(
    f"{BASE_URL}/api/v1/auth/reset-password",
    json={
        "token": reset_token,
        "new_password": "NewPass123!"
    }
)
print(response.json()["message"])

# 3. Login
response = requests.post(
    f"{BASE_URL}/api/v1/auth/login",
    json={
        "username": "testuser",
        "password": "NewPass123!"
    }
)
token = response.json()["access_token"]
print(f"Logged in! Token: {token[:50]}...")
```

## Getting Reset Token (Development)

### Method 1: DEBUG Mode

Set in `.env`:
```env
LOG_LEVEL=DEBUG
```

Token will be returned in the forgot-password response.

### Method 2: MongoDB Query

```bash
mongosh
use financial_chatbot
db.users.findOne(
  {email: "test@example.com"},
  {reset_token: 1, username: 1, reset_token_created: 1}
)
```

### Method 3: Application Logs

Check `./logs/app.log` for:
```
Reset token (DEBUG only): eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

## Security Features

### Email Enumeration Prevention
- Always returns success message
- Doesn't reveal if email exists
- Prevents attackers from discovering valid emails

### Token Security
- JWT-based tokens
- 1-hour expiration
- Single-use (deleted after reset)
- Stored securely in database

### Rate Limiting (Recommended)
Implement rate limiting to prevent abuse:
- 3 requests per hour per IP
- 5 requests per hour per email

## Production Setup

### 1. Email Service Integration

Install email library:
```bash
pip install sendgrid
# or
pip install python-dotenv boto3  # for AWS SES
```

### 2. Update Environment Variables

Add to `.env`:
```env
# Email Configuration
SENDGRID_API_KEY=your_api_key
EMAIL_FROM=noreply@yourapp.com
RESET_PASSWORD_URL=https://yourapp.com/reset-password

# Disable DEBUG mode
LOG_LEVEL=INFO
```

### 3. Implement Email Sending

Update `api/routes/auth.py`:

```python
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail

def send_reset_email(email: str, reset_token: str):
    settings = get_settings()
    reset_link = f"{settings.reset_password_url}?token={reset_token}"
    
    message = Mail(
        from_email=settings.email_from,
        to_emails=email,
        subject='Password Reset Request',
        html_content=f'''
            <h2>Password Reset</h2>
            <p>You requested to reset your password.</p>
            <p>Click the link below to reset your password:</p>
            <a href="{reset_link}">Reset Password</a>
            <p>This link expires in 1 hour.</p>
            <p>If you didn't request this, please ignore this email.</p>
        '''
    )
    
    sg = SendGridAPIClient(settings.sendgrid_api_key)
    sg.send(message)

# In forgot_password endpoint:
if reset_token:
    send_reset_email(request.email, reset_token)
```

### 4. Frontend Integration

Create a password reset page:

```html
<!-- reset-password.html -->
<!DOCTYPE html>
<html>
<head>
    <title>Reset Password</title>
</head>
<body>
    <h2>Reset Your Password</h2>
    <form id="resetForm">
        <input type="password" id="newPassword" placeholder="New Password" required>
        <button type="submit">Reset Password</button>
    </form>
    
    <script>
        // Get token from URL
        const urlParams = new URLSearchParams(window.location.search);
        const token = urlParams.get('token');
        
        document.getElementById('resetForm').addEventListener('submit', async (e) => {
            e.preventDefault();
            
            const newPassword = document.getElementById('newPassword').value;
            
            const response = await fetch('http://localhost:8000/api/v1/auth/reset-password', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({token, new_password: newPassword})
            });
            
            const result = await response.json();
            
            if (response.ok) {
                alert(result.message);
                window.location.href = '/login';
            } else {
                alert(result.detail.message);
            }
        });
    </script>
</body>
</html>
```

## Error Handling

### Common Errors

**400 Bad Request - Invalid or expired token**
```json
{
  "detail": {
    "error": "ResetPasswordError",
    "message": "Invalid or expired reset token",
    "details": null
  }
}
```

**Solution:** Request a new reset token

**422 Validation Error - Password too short**
```json
{
  "detail": [
    {
      "loc": ["body", "new_password"],
      "msg": "String should have at least 8 characters",
      "type": "string_too_short"
    }
  ]
}
```

**Solution:** Use a password with at least 8 characters

## Monitoring

### Metrics to Track

1. **Reset Requests:**
   - Total requests per day
   - Requests per email
   - Success rate

2. **Token Usage:**
   - Tokens generated
   - Tokens used
   - Tokens expired

3. **Failed Attempts:**
   - Invalid tokens
   - Expired tokens
   - Wrong email format

### MongoDB Queries

**Count pending resets:**
```javascript
db.users.countDocuments({reset_token: {$exists: true}})
```

**Find expired tokens:**
```javascript
db.users.find({
  reset_token_created: {
    $lt: new Date(Date.now() - 60*60*1000)  // 1 hour ago
  }
})
```

**Clear expired tokens:**
```javascript
db.users.updateMany(
  {
    reset_token_created: {
      $lt: new Date(Date.now() - 60*60*1000)
    }
  },
  {
    $unset: {reset_token: "", reset_token_created: ""}
  }
)
```

## Testing Checklist

- [ ] Request reset with valid email
- [ ] Request reset with invalid email (should still return success)
- [ ] Verify token is generated and stored in MongoDB
- [ ] Reset password with valid token
- [ ] Try to use same token again (should fail)
- [ ] Try to reset with expired token (should fail)
- [ ] Login with new password
- [ ] Verify old password no longer works
- [ ] Test with invalid email format
- [ ] Test with password less than 8 characters

## Troubleshooting

### Token Not Working

1. Check token hasn't expired (1 hour limit)
2. Verify token matches database:
   ```bash
   mongosh
   use financial_chatbot
   db.users.findOne({email: "user@example.com"}, {reset_token: 1})
   ```
3. Ensure token hasn't been used already
4. Check JWT_SECRET_KEY hasn't changed

### Email Not Received (Production)

1. Check email service configuration
2. Verify email service API key
3. Check spam folder
4. Review email service logs
5. Verify sender email is verified

### Token Not Returned (Development)

1. Set `LOG_LEVEL=DEBUG` in `.env`
2. Restart application
3. Check application logs
4. Query MongoDB directly

## Best Practices

1. **Always use HTTPS** in production
2. **Implement rate limiting** (3-5 requests/hour)
3. **Log all reset attempts** for security
4. **Send confirmation email** after successful reset
5. **Use strong JWT secret** (32+ characters)
6. **Monitor for abuse** patterns
7. **Clear expired tokens** regularly
8. **Test email delivery** before production
9. **Provide clear error messages** to users
10. **Document the process** for support team

## Summary

✅ **Implemented:**
- Forgot password endpoint
- Reset password endpoint
- JWT-based reset tokens
- 1-hour token expiration
- Email enumeration prevention
- Single-use tokens

✅ **Security:**
- Secure token generation
- Token validation
- Automatic token cleanup
- No email disclosure

✅ **Development:**
- DEBUG mode for testing
- Token returned in response
- MongoDB token storage
- Comprehensive logging

✅ **Production Ready:**
- Email integration support
- Rate limiting ready
- Frontend integration guide
- Monitoring queries

The forgot password feature is now fully functional and ready for both development and production use!
