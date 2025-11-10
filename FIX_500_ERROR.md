# Fixing the 500 Error - Auth0 Setup Guide

## The Problem

You're getting a 500 Internal Server Error because:

1. **Wrong Audience**: The token is being requested for `https://dev-jbrriuc5vyjmiwtx.us.auth0.com/userinfo` (Auth0's userinfo endpoint)
2. **JWE vs JWT**: This returns an encrypted JWE token instead of a signed JWT that the API expects
3. **API Expects**: A JWT token signed with RS256 for your API's audience

## The Solution - 3 Steps

### Step 1: Create an API in Auth0

1. Go to https://manage.auth0.com
2. Navigate to **Applications → APIs**
3. Click **Create API**
4. Fill in:
   - **Name**: MagicMinds API
   - **Identifier**: `https://magicminds-api` (this is your audience)
   - **Signing Algorithm**: RS256
5. Click **Create**

### Step 2: Enable Password Grant for Your Application

1. Go to **Applications → Applications**
2. Find your application (Client ID: `eh3lkyPjejB7dngFewuGp6FSP1l6j39D`)
3. Go to **Settings** tab
4. Scroll to **Advanced Settings** → **Grant Types**
5. Enable:
   - ✅ **Password**
   - ✅ **Refresh Token**
6. Click **Save Changes**

### Step 3: Create a Test User

1. Go to **User Management → Users**
2. Click **Create User**
3. Fill in:
   - **Email**: `test@example.com`
   - **Password**: `TestPass123!`
   - **Connection**: Username-Password-Authentication
4. Click **Create**

## Get a New Token

Now run the updated token script:

```powershell
python get_token.py
```

This should now give you a proper JWT token that looks like:
```
eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCIsImtpZCI6...
```

**Key difference**:
- ❌ **Old token** (JWE): Starts with `eyJhbGciOiJkaXIiLCJlbmMi...` (encrypted)
- ✅ **New token** (JWT): Starts with `eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCIsImtpZCI6...` (signed)

## Restart the API Server

The `.env` file was updated, so restart the server:

```powershell
# Stop current server (Ctrl+C)
# Then restart:
python -m uvicorn app.main:app --reload --port 8080
```

## Test the API

Now you can test:

```powershell
# Test without auth (should work)
curl http://localhost:8080/profiles/test

# Test with auth (should work now)
$TOKEN = Get-Content auth_token.txt
curl -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" -X POST http://localhost:8080/profiles/parent -d '{"name":"John Doe"}'
```

Or use the test script:
```powershell
python test_api.py
```

## Verify Token Manually

You can decode and verify your token at https://jwt.io

Paste your token and it should show:
- **Header**: `{ "alg": "RS256", "typ": "JWT" }`
- **Payload**: Contains `sub`, `aud`, `iss`, `exp`, etc.
- **Signature**: Should be verified with Auth0's public key

## Common Issues

### Issue: "Password grant not enabled"
**Solution**: Follow Step 2 above to enable Password grant type

### Issue: "Invalid credentials"  
**Solution**: Follow Step 3 to create the test user with correct credentials

### Issue: "Invalid audience"
**Solution**: Make sure the API identifier in Auth0 matches `https://magicminds-api` in both:
- Auth0 API settings
- `.env` file (`AUTH0_AUDIENCE`)
- `get_token.py` file

### Issue: Still getting JWE token
**Solution**: Check that `AUTH0_AUDIENCE` is set to your API identifier (`https://magicminds-api`), NOT the userinfo endpoint

## Files Updated

1. **`.env`** - Changed `AUTH0_AUDIENCE` to `https://magicminds-api`
2. **`get_token.py`** - Changed `AUTH0_AUDIENCE` to `https://magicminds-api`
3. **`app/deps/auth.py`** - Added better error messages
4. **`app/routers/profiles.py`** - Added test endpoint at `/profiles/test`

## Test Flow

```
1. Create API in Auth0 ✓
2. Enable Password Grant ✓
3. Create Test User ✓
4. Run: python get_token.py
5. Verify: Token starts with "eyJhbGciOiJSUzI1NiI..."
6. Restart API server
7. Test: curl http://localhost:8080/profiles/test
8. Test with auth: Use saved token to call authenticated endpoints
```

## Summary

The 500 error was because:
- ❌ Token was for Auth0's userinfo endpoint (JWE encrypted)
- ❌ API expected JWT for your API (RS256 signed)

After fixing:
- ✅ Token is for your API identifier
- ✅ Token is properly signed JWT
- ✅ API can verify and decode it
