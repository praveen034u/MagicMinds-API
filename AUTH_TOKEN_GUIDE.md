# Getting Auth0 Token - Manual Method

Since the Password Grant flow requires additional Auth0 configuration, here's the **easiest way** to get a token for testing:

## Method 1: Auth0 Dashboard (Recommended - Takes 30 seconds)

### Step 1: Create a Machine-to-Machine Application

1. Go to https://manage.auth0.com
2. Navigate to **Applications** → **Applications**
3. Click **Create Application**
4. Name: `MagicMinds API Test`
5. Type: **Machine to Machine Applications**
6. Click **Create**
7. Select API: **Auth0 Management API** (or create your own API)
8. Click **Authorize**

### Step 2: Get Token from Test Tab

1. Go to **Applications** → **APIs**
2. Click on your API (or create one):
   - Name: `MagicMinds API`
   - Identifier: `https://magicminds.api`
3. Go to the **Test** tab
4. Click **Copy Token**
5. Save this token!

**OR use the Test Application:**

1. Still in the API section, scroll down to **Test with**
2. Select your application
3. Click **Copy** next to the curl command
4. Extract the token from the Authorization header

### Step 3: Use the Token

Save the token to a file:
```powershell
# PowerShell
Set-Content -Path "auth_token.txt" -Value "YOUR_TOKEN_HERE"
```

Or export as environment variable:
```powershell
$env:AUTH0_TOKEN = "YOUR_TOKEN_HERE"
```

## Method 2: Create API and Use Test Client (Alternative)

### Create Your Own API in Auth0:

1. Go to **Applications** → **APIs** → **Create API**
2. Fill in:
   - **Name**: `MagicMinds API`
   - **Identifier**: `https://api.magicminds.com` (can be any unique URL)
   - **Signing Algorithm**: RS256
3. Click **Create**

### Get Test Token:

1. Click on your new API
2. Go to **Test** tab
3. Under "Get Access Tokens for Testing", you'll see a curl command
4. Click **Copy Token** or copy from the curl command

### Update Your .env:

```env
AUTH0_AUDIENCE=https://api.magicminds.com  # Your API identifier
```

## Method 3: Using cURL Directly

If you have a user created in Auth0:

```powershell
$body = @{
    grant_type = "http://auth0.com/oauth/grant-type/password-realm"
    username = "test@example.com"
    password = "TestPass123!"
    client_id = "eh3lkyPjejB7dngFewuGp6FSP1l6j39D"
    audience = "https://dev-jbrriuc5vyjmiwtx.us.auth0.com/userinfo"
    realm = "Username-Password-Authentication"
    scope = "openid profile email"
} | ConvertTo-Json

$response = Invoke-RestMethod -Uri "https://dev-jbrriuc5vyjmiwtx.us.auth0.com/oauth/token" -Method Post -Body $body -ContentType "application/json"

$response.access_token | Set-Content "auth_token.txt"
Write-Host "Token saved to auth_token.txt"
```

## Quick Test Without Auth (For Development)

If you want to test endpoints without authentication temporarily, you can comment out the auth dependency:

**In `app/routers/profiles.py`:**
```python
# Comment out the auth dependency for testing
# current_user: CurrentUser = Depends(get_current_user),

@router.post("/parent", response_model=ParentProfileResponse)
async def create_parent_profile(
    profile_data: ParentProfileCreate,
    # current_user: CurrentUser = Depends(get_current_user),  # TEMPORARY
    db: AsyncSession = Depends(get_db)
):
    # For testing, hardcode a user ID
    auth0_user_id = "test_user_123"
    email = "test@example.com"
    
    # ... rest of the code
```

⚠️ **Remember to restore authentication before deploying!**

## After Getting Token

Once you have a token, test it:

```powershell
# Read token
$TOKEN = Get-Content auth_token.txt

# Test health (no auth needed)
curl http://localhost:8080/healthz

# Test authenticated endpoint
curl -H "Authorization: Bearer $TOKEN" http://localhost:8080/profiles/parent
```

## Using Swagger UI (Easiest!)

1. Open http://localhost:8080/docs
2. Click 🔒 **Authorize** button
3. Paste your token (without "Bearer" prefix)
4. Click **Authorize**
5. Test any endpoint!

---

**Need Help?**
- Auth0 Dashboard: https://manage.auth0.com
- Auth0 Docs: https://auth0.com/docs/get-started/authentication-and-authorization-flow
