# Admin Panel CORS Configuration

## Overview

The Financial Chatbot RAG System implements separate CORS (Cross-Origin Resource Sharing) policies for admin endpoints and regular endpoints to enhance security. This document explains the configuration and how to customize it for production deployments.

## Architecture

### Custom CORS Middleware

The application uses a custom `AdminCORSMiddleware` class that:

1. **Detects admin endpoints** by checking if the request path starts with `/api/v1/admin`
2. **Applies different CORS policies** based on the endpoint type:
   - Admin endpoints use `ADMIN_CORS_ORIGINS` configuration
   - Regular endpoints use `CORS_ORIGINS` configuration
3. **Handles preflight requests** (OPTIONS) with appropriate headers
4. **Adds CORS headers** to all responses based on the allowed origins

### Configuration Properties

Two new configuration properties have been added to `config/settings.py`:

```python
# CORS Configuration
cors_origins: str = Field(
    default="*",
    description="Comma-separated list of allowed CORS origins for regular endpoints"
)

admin_cors_origins: str = Field(
    default="*",
    description="Comma-separated list of allowed CORS origins for admin endpoints"
)
```

These properties are automatically parsed into lists via helper methods:
- `cors_origins_list` - Returns list of allowed origins for regular endpoints
- `admin_cors_origins_list` - Returns list of allowed origins for admin endpoints

## Configuration

### Development Environment

By default, both regular and admin endpoints allow all origins (`*`):

```env
CORS_ORIGINS=*
ADMIN_CORS_ORIGINS=*
```

This is suitable for development but **should not be used in production**.

### Production Environment

For production deployments, restrict origins to specific domains:

```env
# Regular endpoints - allow your main application domains
CORS_ORIGINS=https://yourapp.com,https://www.yourapp.com

# Admin endpoints - restrict to admin panel domain only
ADMIN_CORS_ORIGINS=https://admin.yourapp.com
```

### Multiple Origins

You can specify multiple origins as a comma-separated list:

```env
ADMIN_CORS_ORIGINS=https://admin.yourapp.com,https://admin-staging.yourapp.com,https://admin-dev.yourapp.com
```

## Security Considerations

### Why Separate CORS Policies?

1. **Principle of Least Privilege**: Admin endpoints should only be accessible from authorized admin panel domains
2. **Attack Surface Reduction**: Limiting admin endpoint access reduces the risk of unauthorized access
3. **Defense in Depth**: Even with authentication, restricting CORS origins adds an additional security layer

### Production Recommendations

1. **Never use wildcard (`*`) in production** for admin endpoints
2. **Use HTTPS only** for all allowed origins
3. **Specify exact domains** - avoid wildcards in domain names
4. **Regularly review** allowed origins and remove unused ones
5. **Use environment-specific configurations** (dev, staging, production)

### CORS Headers Applied

The middleware applies the following CORS headers:

**For Preflight Requests (OPTIONS):**
- `Access-Control-Allow-Origin`: The requesting origin (if allowed)
- `Access-Control-Allow-Methods`: GET, POST, PUT, DELETE, OPTIONS
- `Access-Control-Allow-Headers`: Content-Type, Authorization
- `Access-Control-Allow-Credentials`: true (if not wildcard)
- `Access-Control-Max-Age`: 600 seconds

**For Regular Requests:**
- `Access-Control-Allow-Origin`: The requesting origin (if allowed)
- `Access-Control-Allow-Credentials`: true (if not wildcard)

## Testing CORS Configuration

### Test with curl

Test admin endpoint CORS:

```bash
# Preflight request
curl -X OPTIONS http://localhost:8000/api/v1/admin/users \
  -H "Origin: https://admin.yourapp.com" \
  -H "Access-Control-Request-Method: GET" \
  -v

# Actual request
curl -X GET http://localhost:8000/api/v1/admin/users \
  -H "Origin: https://admin.yourapp.com" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -v
```

### Test with Browser

1. Open browser developer tools (F12)
2. Go to Console tab
3. Run:

```javascript
// Test admin endpoint
fetch('http://localhost:8000/api/v1/admin/users', {
  method: 'GET',
  headers: {
    'Authorization': 'Bearer YOUR_TOKEN'
  }
})
.then(response => console.log('Success:', response))
.catch(error => console.error('CORS Error:', error));
```

### Expected Behavior

**Allowed Origin:**
- Request succeeds
- Response includes `Access-Control-Allow-Origin` header with the requesting origin

**Blocked Origin:**
- Request fails with CORS error
- Browser console shows: "Access to fetch at '...' from origin '...' has been blocked by CORS policy"

## Troubleshooting

### Issue: CORS errors in production

**Solution:** Verify that:
1. `ADMIN_CORS_ORIGINS` includes the exact origin of your admin panel
2. The origin includes the protocol (https://) and exact domain
3. No trailing slashes in the origin URL
4. The environment variables are properly loaded

### Issue: Credentials not being sent

**Solution:** 
1. Ensure `credentials: 'include'` is set in fetch requests
2. Verify `Access-Control-Allow-Credentials: true` is in the response
3. Check that you're not using wildcard (`*`) for origins when credentials are needed

### Issue: Preflight requests failing

**Solution:**
1. Verify the OPTIONS method is not blocked by other middleware
2. Check that `Access-Control-Allow-Methods` includes the method you're trying to use
3. Ensure `Access-Control-Allow-Headers` includes all headers you're sending

## Implementation Details

### File Changes

1. **config/settings.py**
   - Added `cors_origins` field
   - Added `admin_cors_origins` field
   - Added `cors_origins_list` property
   - Added `admin_cors_origins_list` property

2. **main.py**
   - Added `AdminCORSMiddleware` class
   - Replaced standard `CORSMiddleware` with custom middleware
   - Added documentation comments

3. **.env.example**
   - Added `CORS_ORIGINS` example
   - Added `ADMIN_CORS_ORIGINS` example with production recommendations

### Middleware Flow

```
Request → AdminCORSMiddleware
    ↓
Check if path starts with /api/v1/admin
    ↓
Select appropriate CORS origins list
    ↓
If OPTIONS request → Return CORS headers immediately
    ↓
Process request through application
    ↓
Add CORS headers to response
    ↓
Return response
```

## Future Enhancements

Potential improvements for future versions:

1. **Dynamic Origin Validation**: Load allowed origins from database for runtime updates
2. **Origin Patterns**: Support regex patterns for origin matching
3. **Per-Endpoint CORS**: More granular CORS control per endpoint
4. **CORS Logging**: Log CORS violations for security monitoring
5. **Rate Limiting by Origin**: Different rate limits based on origin

## References

- [MDN Web Docs - CORS](https://developer.mozilla.org/en-US/docs/Web/HTTP/CORS)
- [FastAPI CORS Documentation](https://fastapi.tiangolo.com/tutorial/cors/)
- [OWASP CORS Security Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Cross-Origin_Resource_Sharing_Cheat_Sheet.html)
