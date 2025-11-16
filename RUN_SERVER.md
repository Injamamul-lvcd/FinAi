# How to Run the Application

## Option 1: Using uvicorn directly (Recommended)
```bash
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

## Option 2: Using Python module
```bash
python -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

## Option 3: Using the main.py script
```bash
python main.py
```

## Testing the Endpoints

After starting the server, you can test the auth endpoints:

```bash
python test_auth_endpoints.py
```

## Manual Testing with curl (PowerShell)

### Register a new user:
```powershell
Invoke-RestMethod -Uri "http://localhost:8000/api/v1/auth/register" -Method POST -ContentType "application/json" -Body '{"username":"testuser","email":"test@example.com","password":"Test123456","full_name":"Test User"}'
```

### Login:
```powershell
Invoke-RestMethod -Uri "http://localhost:8000/api/v1/auth/login" -Method POST -ContentType "application/json" -Body '{"username":"testuser","password":"Test123456"}'
```

### Check health:
```powershell
Invoke-RestMethod -Uri "http://localhost:8000/api/v1/health" -Method GET
```

## API Documentation

Once the server is running, visit:
- Swagger UI: http://localhost:8000/api/docs
- ReDoc: http://localhost:8000/api/redoc

## Troubleshooting

### If endpoints are not responding:

1. **Check if server is running:**
   ```powershell
   Get-Process python
   ```

2. **Check if port 8000 is in use:**
   ```powershell
   netstat -ano | findstr :8000
   ```

3. **Check MongoDB is running:**
   ```powershell
   Get-Process mongod
   ```

4. **Check server logs:**
   Look at `logs/app.log` for any errors

### Common Issues:

1. **CORS errors**: The CORS policy is set to "*" by default, allowing all origins. If you're still getting CORS errors, check the browser console for specific error messages.

2. **MongoDB connection errors**: Make sure MongoDB is running on `localhost:27017`

3. **Port already in use**: If port 8000 is already in use, change the port in `.env` file or use a different port:
   ```bash
   uvicorn main:app --host 0.0.0.0 --port 8001 --reload
   ```
