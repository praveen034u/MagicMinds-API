# Authentication Flow - How auth0_user_id and email are Extracted

## Overview

The API uses **Auth0 JWT (JSON Web Token)** authentication. The `auth0_user_id` and `email` are automatically extracted from the JWT token sent in the request headers.

## Step-by-Step Flow

### 1. Client Makes Request with JWT Token

When a client (frontend app) calls an authenticated endpoint, they include a JWT token in the Authorization header:

```http
POST /profiles/parent
Authorization: Bearer eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCIsImtpZCI6IjEyMzQ1Njc4OSJ9.eyJzdWIiOiJhdXRoMHwxMjM0NTY3ODkiLCJlbWFpbCI6InVzZXJAZXhhbXBsZS5jb20iLCJpYXQiOjE2OTkwMDAwMDAsImV4cCI6MTY5OTAwMzYwMCwiYXVkIjoiaHR0cHM6Ly9hcGkuZXhhbXBsZS5jb20iLCJpc3MiOiJodHRwczovL3lvdXItZG9tYWluLmF1dGgwLmNvbS8ifQ.signature
Content-Type: application/json

{
  "name": "John Doe"
}
```

### 2. FastAPI Security Extracts Token

The `HTTPBearer` security scheme (defined in `app/deps/auth.py`) automatically extracts the token from the `Authorization: Bearer <token>` header.

```python
security = HTTPBearer()

async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> CurrentUser:
    token = credentials.credentials  # This is the JWT token
```

### 3. JWT Token Structure

A JWT token consists of three parts separated by dots:
- **Header**: Algorithm and token type
- **Payload**: User claims (data)
- **Signature**: Cryptographic signature

Example decoded payload:
```json
{
  "sub": "auth0|123456789",           // Auth0 user ID
  "email": "user@example.com",        // User's email
  "name": "John Doe",                 // User's name
  "iat": 1699000000,                  // Issued at timestamp
  "exp": 1699003600,                  // Expiration timestamp
  "aud": "https://api.example.com",   // API audience
  "iss": "https://your-domain.auth0.com/"  // Token issuer
}
```

### 4. Token Verification Process

The `verify_token()` function performs several security checks:

#### 4.1 Get Signing Key from JWKS
```python
def get_signing_key(token: str) -> str:
    # Extract 'kid' (Key ID) from token header
    unverified_header = jwt.get_unverified_header(token)
    kid = unverified_header.get("kid")
    
    # Fetch public keys from Auth0's JWKS endpoint
    jwks = get_jwks()  # Cached call to https://your-domain.auth0.com/.well-known/jwks.json
    
    # Find matching key by kid
    for key in jwks.get("keys", []):
        if key.get("kid") == kid:
            return key
```

#### 4.2 Verify and Decode Token
```python
payload = jwt.decode(
    token,
    signing_key,
    algorithms=["RS256"],
    audience=settings.AUTH0_AUDIENCE,    # Verify token is for this API
    issuer=settings.AUTH0_ISSUER,        # Verify token is from Auth0
    options={
        "verify_signature": True,        # Verify cryptographic signature
        "verify_aud": True,              // Verify audience matches
        "verify_exp": True,              // Verify token not expired
        "verify_iss": True,              // Verify issuer matches
    }
)
```

This ensures:
- ✅ Token was issued by your Auth0 tenant
- ✅ Token is intended for your API (audience check)
- ✅ Token hasn't been tampered with (signature check)
- ✅ Token hasn't expired
- ✅ Token is not being used before it's valid

### 5. Extract User Information

After verification, extract user data from the payload:

```python
# Extract Auth0 user ID (always present)
sub = payload.get("sub")  # e.g., "auth0|123456789"

# Extract email (may be in standard claim or custom namespace)
email = payload.get("email") or payload.get("https://your-app.com/email")

# Create CurrentUser object
return CurrentUser(sub=sub, email=email, claims=payload)
```

### 6. Use in Route Handler

The `current_user` dependency is injected into route handlers:

```python
@router.post("/parent", response_model=ParentProfileResponse)
async def create_parent_profile(
    profile_data: ParentProfileCreate,
    current_user: CurrentUser = Depends(get_current_user),  # <-- Injected here
    db: AsyncSession = Depends(get_db)
):
    # Now we have access to:
    # - current_user.sub (auth0_user_id)
    # - current_user.email (email address)
    
    parent = ParentProfile(
        auth0_user_id=current_user.sub,    # From JWT token
        email=current_user.email,          # From JWT token
        name=profile_data.name             # From request body
    )
```

## Configuration

The authentication system requires these environment variables in `.env`:

```env
# Auth0 Configuration
AUTH0_DOMAIN=your-domain.auth0.com
AUTH0_AUDIENCE=https://your-api-audience
AUTH0_ISSUER=https://your-domain.auth0.com/

# Derived values (auto-constructed)
AUTH0_JWKS_URL=https://your-domain.auth0.com/.well-known/jwks.json
```

These are loaded in `app/config.py`:

```python
class Settings(BaseSettings):
    AUTH0_DOMAIN: str
    AUTH0_AUDIENCE: str
    AUTH0_ISSUER: str
    
    @property
    def AUTH0_JWKS_URL(self) -> str:
        return f"https://{self.AUTH0_DOMAIN}/.well-known/jwks.json"
```

## Security Features

### 1. **Public Key Cryptography (RS256)**
- Auth0 signs tokens with a private key
- API verifies with Auth0's public key (from JWKS)
- Impossible to forge tokens without the private key

### 2. **JWKS Caching**
- Public keys are fetched once and cached using `@lru_cache()`
- Reduces latency on subsequent requests
- Automatically refreshes if key rotation occurs

### 3. **Comprehensive Validation**
- Token signature verification
- Expiration time check
- Audience claim validation
- Issuer claim validation
- Not-before time check

### 4. **Error Handling**
Different error types with appropriate HTTP status codes:
- **401 Unauthorized**: Invalid, expired, or missing token
- **503 Service Unavailable**: Cannot reach Auth0 JWKS endpoint

## Example Request Flow

### Client Side (Frontend)
```javascript
// 1. User logs in with Auth0
const { getAccessTokenSilently } = useAuth0();

// 2. Get JWT token
const token = await getAccessTokenSilently({
  audience: 'https://your-api-audience',
});

// 3. Make API request with token
const response = await fetch('https://api.example.com/profiles/parent', {
  method: 'POST',
  headers: {
    'Authorization': `Bearer ${token}`,
    'Content-Type': 'application/json',
  },
  body: JSON.stringify({ name: 'John Doe' })
});
```

### Server Side (FastAPI)
```python
# 1. HTTPBearer extracts token from Authorization header
# 2. get_current_user() dependency:
#    - Fetches Auth0 public keys (cached)
#    - Verifies token signature
#    - Validates all claims
#    - Extracts sub and email
# 3. Route handler receives CurrentUser object
# 4. Uses current_user.sub and current_user.email to create profile
```

## Testing Authentication

### Using Swagger UI
1. Go to http://localhost:8080/docs
2. Click "Authorize" button (🔒 icon)
3. Enter your JWT token: `Bearer <your-token>`
4. Click "Authorize"
5. Now all requests will include the token

### Using curl
```bash
curl -X POST "http://localhost:8080/profiles/parent" \
  -H "Authorization: Bearer <your-jwt-token>" \
  -H "Content-Type: application/json" \
  -d '{"name": "John Doe"}'
```

### Using Postman
1. Create new request
2. Go to "Authorization" tab
3. Select "Bearer Token" type
4. Paste your JWT token
5. Send request

## Common Issues

### Issue: "Invalid token: missing subject"
- **Cause**: JWT token doesn't contain `sub` claim
- **Solution**: Check Auth0 configuration, ensure token includes user ID

### Issue: "Unable to find appropriate signing key"
- **Cause**: Token `kid` doesn't match any key in JWKS
- **Solution**: Check AUTH0_DOMAIN is correct, verify key rotation

### Issue: "Token has expired"
- **Cause**: JWT token is past its expiration time
- **Solution**: Request a new token from Auth0

### Issue: "Invalid token claims"
- **Cause**: Audience or issuer doesn't match configuration
- **Solution**: Verify AUTH0_AUDIENCE and AUTH0_ISSUER in .env file

## Summary

The extraction of `auth0_user_id` and `email` is fully automatic and secure:

1. ✅ **Client sends**: JWT token in Authorization header
2. ✅ **Server extracts**: Token from header using HTTPBearer
3. ✅ **Server verifies**: Token signature using Auth0 public keys
4. ✅ **Server validates**: All token claims (exp, aud, iss, etc.)
5. ✅ **Server extracts**: `sub` (user ID) and `email` from payload
6. ✅ **Route handler uses**: CurrentUser object with all user info

No need to manually pass user ID or email in request body - it's all handled securely via the JWT token! 🔐
