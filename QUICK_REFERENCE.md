# Quick Reference Card

## 🚀 Start Application

```bash
# Start MongoDB
net start MongoDB  # Windows
sudo systemctl start mongod  # Linux

# Activate virtual environment
venv\Scripts\activate  # Windows
source venv/bin/activate  # Linux/Mac

# Start application
uvicorn main:app --reload
```

## 🔑 Authentication Flow

```bash
# 1. Register
curl -X POST http://localhost:8000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{"username":"user","email":"user@example.com","password":"Pass123!"}'

# 2. Login (get token)
TOKEN=$(curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"user","password":"Pass123!"}' | jq -r '.access_token')

# 3. Use token
curl -X POST http://localhost:8000/api/v1/chat \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"query":"What are the key metrics?"}'
```

## 🔐 Password Reset Flow

```bash
# 1. Request reset
curl -X POST http://localhost:8000/api/v1/auth/forgot-password \
  -H "Content-Type: application/json" \
  -d '{"email":"user@example.com"}'

# 2. Reset password (use token from response or MongoDB)
curl -X POST http://localhost:8000/api/v1/auth/reset-password \
  -H "Content-Type: application/json" \
  -d '{"token":"RESET_TOKEN","new_password":"NewPass123!"}'
```

## 📋 API Endpoints

### Auth (No Token Required)
- `POST /api/v1/auth/register` - Register
- `POST /api/v1/auth/login` - Login
- `POST /api/v1/auth/forgot-password` - Request reset
- `POST /api/v1/auth/reset-password` - Reset password

### Auth (Token Required)
- `GET /api/v1/auth/me` - Get user info
- `POST /api/v1/auth/change-password` - Change password

### Chat (Token Required)
- `POST /api/v1/chat` - Ask question

### Documents (No Token)
- `POST /api/v1/documents/upload` - Upload
- `GET /api/v1/documents` - List
- `DELETE /api/v1/documents/{id}` - Delete
- `GET /api/v1/documents/stats` - Stats

## 🗄️ MongoDB Commands

```javascript
// Connect
mongosh

// Switch database
use financial_chatbot

// View users
db.users.find().pretty()

// View sessions
db.sessions.find().pretty()

// View messages
db.messages.find().pretty()

// Count documents
db.users.countDocuments()
db.sessions.countDocuments()
db.messages.countDocuments()

// Find user
db.users.findOne({username: "user"})

// Find reset token
db.users.findOne({email: "user@example.com"}, {reset_token: 1})
```

## ⚙️ Environment Variables

```env
# Required
GOOGLE_API_KEY=your_api_key
MONGODB_CONNECTION_STRING=mongodb://localhost:27017/
JWT_SECRET_KEY=your-secret-key

# Optional (with defaults)
MONGODB_DATABASE_NAME=financial_chatbot
JWT_ALGORITHM=HS256
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=30
LOG_LEVEL=INFO
```

## 🐛 Troubleshooting

### MongoDB not running
```bash
# Windows
net start MongoDB

# Linux
sudo systemctl start mongod

# Check status
mongosh
```

### Token expired
```bash
# Login again to get new token
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"user","password":"Pass123!"}'
```

### View logs
```bash
# Windows
type logs\app.log

# Linux/Mac
tail -f logs/app.log
```

## 📚 Documentation

- **API Reference:** `API_AUTHENTICATION.md`
- **Setup Guide:** `AUTHENTICATION_SETUP.md`
- **Password Reset:** `FORGOT_PASSWORD_GUIDE.md`
- **Upgrade Info:** `UPGRADE_SUMMARY.md`
- **Complete Summary:** `IMPLEMENTATION_COMPLETE.md`
- **Interactive Docs:** http://localhost:8000/api/docs

## 🔗 URLs

- **API Base:** http://localhost:8000
- **Swagger UI:** http://localhost:8000/api/docs
- **ReDoc:** http://localhost:8000/api/redoc
- **Health Check:** http://localhost:8000/api/v1/health

## 🎯 Common Tasks

### Register and Chat
```python
import requests

BASE = "http://localhost:8000"

# Register
requests.post(f"{BASE}/api/v1/auth/register", 
  json={"username":"user","email":"user@example.com","password":"Pass123!"})

# Login
r = requests.post(f"{BASE}/api/v1/auth/login",
  json={"username":"user","password":"Pass123!"})
token = r.json()["access_token"]

# Chat
r = requests.post(f"{BASE}/api/v1/chat",
  headers={"Authorization": f"Bearer {token}"},
  json={"query":"What are the key metrics?"})
print(r.json()["response"])
```

### Reset Password
```python
import requests

BASE = "http://localhost:8000"

# Request reset
r = requests.post(f"{BASE}/api/v1/auth/forgot-password",
  json={"email":"user@example.com"})
token = r.json().get("reset_token")  # DEBUG mode only

# Reset
requests.post(f"{BASE}/api/v1/auth/reset-password",
  json={"token":token,"new_password":"NewPass123!"})
```

## ⚡ Quick Tips

1. **Token in Swagger:** Click "Authorize" → Enter `Bearer YOUR_TOKEN`
2. **DEBUG Mode:** Set `LOG_LEVEL=DEBUG` to see reset tokens
3. **MongoDB GUI:** Use MongoDB Compass for visual interface
4. **Token Expiry:** Default 30 minutes, configurable in `.env`
5. **Reset Token:** Valid for 1 hour, single-use only

## 🎉 Success Indicators

✅ MongoDB running
✅ Application starts without errors
✅ Can register user
✅ Can login and get token
✅ Can use token for chat
✅ Can reset password
✅ Swagger UI accessible

---

**Quick Start:** Install MongoDB → `pip install -r requirements.txt` → Update `.env` → `uvicorn main:app --reload`
