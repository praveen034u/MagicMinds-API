# API Testing Guide - MagicMinds API

Complete guide for creating users and testing all API endpoints.

## 🔐 Getting an Auth0 Token

### Method 1: Using Auth0 Dashboard (Quickest for Testing)

1. **Go to Auth0 Dashboard**: https://manage.auth0.com
2. Navigate to **Applications** → **APIs**
3. Select your API (or create a test API)
4. Go to the **Test** tab
5. Click **"Copy Token"** - this is your JWT token
6. Token will look like: `eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9...`

### Method 2: Create a Test User via Auth0

1. Go to https://manage.auth0.com
2. Navigate to **User Management** → **Users**
3. Click **Create User**
4. Fill in:
   - Email: `test@example.com`
   - Password: `TestPass123!`
   - Connection: `Username-Password-Authentication`
5. Click **Create**

### Method 3: Programmatically Get Token (Recommended for Development)

Create a file `get_token.py`:

```python
import requests
import json

# Your Auth0 credentials
AUTH0_DOMAIN = "dev-jbrriuc5vyjmiwtx.us.auth0.com"
AUTH0_CLIENT_ID = "eh3lkyPjejB7dngFewuGp6FSP1l6j39D"
AUTH0_AUDIENCE = "https://dev-jbrriuc5vyjmiwtx.us.auth0.com/userinfo"

# Test user credentials (create this user in Auth0 dashboard first)
USERNAME = "test@example.com"
PASSWORD = "TestPass123!"

def get_token():
    """Get Auth0 access token using Resource Owner Password Grant."""
    url = f"https://{AUTH0_DOMAIN}/oauth/token"
    
    payload = {
        "grant_type": "password",
        "username": USERNAME,
        "password": PASSWORD,
        "client_id": AUTH0_CLIENT_ID,
        "audience": AUTH0_AUDIENCE,
        "scope": "openid profile email"
    }
    
    headers = {"content-type": "application/json"}
    
    response = requests.post(url, json=payload, headers=headers)
    
    if response.status_code == 200:
        token_data = response.json()
        access_token = token_data.get("access_token")
        print("✅ Token obtained successfully!")
        print(f"\nAccess Token:\n{access_token}\n")
        print(f"Token Type: {token_data.get('token_type')}")
        print(f"Expires In: {token_data.get('expires_in')} seconds")
        return access_token
    else:
        print(f"❌ Error: {response.status_code}")
        print(response.text)
        return None

if __name__ == "__main__":
    token = get_token()
    
    # Save token to file for easy reuse
    if token:
        with open("auth_token.txt", "w") as f:
            f.write(token)
        print("\n💾 Token saved to auth_token.txt")
```

Run it:
```powershell
python get_token.py
```

**Note**: You may need to enable "Password" grant type in Auth0:
1. Go to Applications → Settings
2. Scroll to "Advanced Settings" → "Grant Types"
3. Enable "Password"
4. Save

## 🧪 Testing the API

### Option 1: Using Swagger UI (Easiest)

1. **Open Swagger UI**: http://localhost:8080/docs
2. Click the **"Authorize"** button (🔒 icon at top right)
3. Enter your token in the format: `Bearer YOUR_TOKEN_HERE`
4. Click **Authorize**
5. Now all endpoints will include the Authorization header automatically
6. Test any endpoint by clicking "Try it out"

### Option 2: Using cURL (Command Line)

First, set your token as an environment variable:

```powershell
# PowerShell
$TOKEN = "eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9..."
```

Or read from file:
```powershell
$TOKEN = Get-Content auth_token.txt
```

#### Test Endpoints:

**1. Create Parent Profile:**
```powershell
curl -X POST "http://localhost:8080/profiles/parent" `
  -H "Authorization: Bearer $TOKEN" `
  -H "Content-Type: application/json" `
  -d '{"name": "John Doe"}'
```

**2. Get Parent Profile:**
```powershell
curl -X GET "http://localhost:8080/profiles/parent" `
  -H "Authorization: Bearer $TOKEN"
```

**3. Create Child Profile:**
```powershell
curl -X POST "http://localhost:8080/profiles/children" `
  -H "Authorization: Bearer $TOKEN" `
  -H "Content-Type: application/json" `
  -d '{
    "name": "Alice",
    "age_group": "5-7",
    "avatar": "https://example.com/avatar.png"
  }'
```

**4. Get All Children:**
```powershell
curl -X GET "http://localhost:8080/profiles/children" `
  -H "Authorization: Bearer $TOKEN"
```

**5. Health Check (No Auth Required):**
```powershell
curl http://localhost:8080/healthz
curl http://localhost:8080/readyz
```

### Option 3: Using Python Requests

Create a test script `test_api.py`:

```python
import requests
import json

# Base URL
BASE_URL = "http://localhost:8080"

# Read token from file
with open("auth_token.txt", "r") as f:
    TOKEN = f.read().strip()

headers = {
    "Authorization": f"Bearer {TOKEN}",
    "Content-Type": "application/json"
}

def test_health():
    """Test health endpoints."""
    print("\n=== Testing Health Endpoints ===")
    
    response = requests.get(f"{BASE_URL}/healthz")
    print(f"GET /healthz: {response.status_code} - {response.json()}")
    
    response = requests.get(f"{BASE_URL}/readyz")
    print(f"GET /readyz: {response.status_code} - {response.json()}")

def test_create_parent():
    """Create parent profile."""
    print("\n=== Creating Parent Profile ===")
    
    data = {"name": "John Doe"}
    response = requests.post(
        f"{BASE_URL}/profiles/parent",
        headers=headers,
        json=data
    )
    print(f"Status: {response.status_code}")
    if response.status_code in [200, 201]:
        parent = response.json()
        print(f"Created Parent ID: {parent['id']}")
        print(f"Name: {parent['name']}")
        print(f"Email: {parent['email']}")
        return parent
    else:
        print(f"Error: {response.text}")
        return None

def test_get_parent():
    """Get parent profile."""
    print("\n=== Getting Parent Profile ===")
    
    response = requests.get(
        f"{BASE_URL}/profiles/parent",
        headers=headers
    )
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        parent = response.json()
        print(f"Parent ID: {parent['id']}")
        print(f"Name: {parent['name']}")
        return parent
    else:
        print(f"Error: {response.text}")
        return None

def test_create_child():
    """Create child profile."""
    print("\n=== Creating Child Profile ===")
    
    data = {
        "name": "Alice",
        "age_group": "5-7",
        "avatar": "https://example.com/alice.png"
    }
    response = requests.post(
        f"{BASE_URL}/profiles/children",
        headers=headers,
        json=data
    )
    print(f"Status: {response.status_code}")
    if response.status_code in [200, 201]:
        child = response.json()
        print(f"Created Child ID: {child['id']}")
        print(f"Name: {child['name']}")
        print(f"Age Group: {child['age_group']}")
        return child
    else:
        print(f"Error: {response.text}")
        return None

def test_get_children():
    """Get all children."""
    print("\n=== Getting All Children ===")
    
    response = requests.get(
        f"{BASE_URL}/profiles/children",
        headers=headers
    )
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        children = response.json()
        print(f"Total Children: {len(children)}")
        for child in children:
            print(f"  - {child['name']} (Age: {child['age_group']})")
        return children
    else:
        print(f"Error: {response.text}")
        return None

def test_create_room(child_id):
    """Create a game room."""
    print("\n=== Creating Game Room ===")
    
    data = {
        "game_id": "math_quest",
        "difficulty": "medium",
        "max_players": 4,
        "has_ai_player": True,
        "ai_player_name": "RoboMath",
        "selected_category": "addition"
    }
    response = requests.post(
        f"{BASE_URL}/rooms",
        headers=headers,
        json=data
    )
    print(f"Status: {response.status_code}")
    if response.status_code in [200, 201]:
        room = response.json()
        print(f"Room Code: {room['room_code']}")
        print(f"Room ID: {room['id']}")
        print(f"Max Players: {room['max_players']}")
        print(f"Current Players: {room['current_players']}")
        return room
    else:
        print(f"Error: {response.text}")
        return None

def test_create_story(child_id):
    """Create a generated story."""
    print("\n=== Creating Story ===")
    
    data = {
        "child_id": child_id,
        "story_text": "Once upon a time, in a magical land...",
        "prompt_used": "Create a story about a magical adventure",
        "voice_audio_url": "https://example.com/story_audio.mp3"
    }
    response = requests.post(
        f"{BASE_URL}/stories",
        headers=headers,
        json=data
    )
    print(f"Status: {response.status_code}")
    if response.status_code in [200, 201]:
        story = response.json()
        print(f"Story ID: {story['id']}")
        print(f"Story Preview: {story['story_text'][:50]}...")
        return story
    else:
        print(f"Error: {response.text}")
        return None

def run_full_test():
    """Run complete test suite."""
    print("=" * 60)
    print("MagicMinds API - Full Test Suite")
    print("=" * 60)
    
    # Test health
    test_health()
    
    # Test parent profile
    parent = test_create_parent()
    if not parent:
        parent = test_get_parent()
    
    # Test child profile
    child = test_create_child()
    if not child:
        children = test_get_children()
        if children:
            child = children[0]
    
    # Test game room
    if child:
        room = test_create_room(child['id'])
        story = test_create_story(child['id'])
    
    print("\n" + "=" * 60)
    print("✅ Test Suite Complete!")
    print("=" * 60)

if __name__ == "__main__":
    run_full_test()
```

Run it:
```powershell
python test_api.py
```

### Option 4: Using Postman

1. **Import OpenAPI Spec:**
   - Open Postman
   - File → Import
   - Enter URL: `http://localhost:8080/openapi.json`
   - Click Import

2. **Set Up Authorization:**
   - Create a new Environment
   - Add variable: `token` = `YOUR_AUTH0_TOKEN`
   - In each request, add Header:
     - Key: `Authorization`
     - Value: `Bearer {{token}}`

3. **Test endpoints** from the imported collection

## 🔍 Viewing Data in Database

### Using Docker:

```powershell
# Connect to PostgreSQL
docker exec -it magicminds_postgres psql -U postgres -d magicminds

# View parent profiles
SELECT * FROM parent_profiles;

# View children
SELECT * FROM children_profiles;

# View friends
SELECT * FROM friends;

# View game rooms
SELECT * FROM game_rooms;

# Exit
\q
```

### Using Supabase Dashboard:

1. Go to https://supabase.com/dashboard
2. Select your project
3. Go to **Table Editor**
4. Select tables to view data
5. Or use **SQL Editor** to run custom queries

## 📝 Complete Test Workflow

Here's a complete workflow to test all features:

### 1. Setup (One Time)
```powershell
# Get Auth0 token
python get_token.py

# Verify API is running
curl http://localhost:8080/healthz
```

### 2. Create User Profile
```powershell
# Create parent (first time only)
curl -X POST "http://localhost:8080/profiles/parent" `
  -H "Authorization: Bearer $(Get-Content auth_token.txt)" `
  -H "Content-Type: application/json" `
  -d '{"name": "Test Parent"}'

# Create children
curl -X POST "http://localhost:8080/profiles/children" `
  -H "Authorization: Bearer $(Get-Content auth_token.txt)" `
  -H "Content-Type: application/json" `
  -d '{"name": "Alice", "age_group": "5-7"}'
```

### 3. Test All Features
```powershell
# Run comprehensive test
python test_api.py
```

### 4. Check Logs
```powershell
# API logs are visible in the terminal running uvicorn
# Check for any errors or authentication issues
```

## 🐛 Troubleshooting

### Issue: 401 Unauthorized

**Cause**: Invalid or expired token

**Solution**:
```powershell
# Get a fresh token
python get_token.py

# Verify token is valid at https://jwt.io
```

### Issue: 404 Parent Profile Not Found

**Cause**: No parent profile created yet

**Solution**:
```powershell
# Create parent profile first
curl -X POST "http://localhost:8080/profiles/parent" `
  -H "Authorization: Bearer YOUR_TOKEN" `
  -H "Content-Type: application/json" `
  -d '{"name": "Your Name"}'
```

### Issue: Connection Refused

**Cause**: API not running

**Solution**:
```powershell
# Start the API
uvicorn app.main:app --reload --port 8080
```

## 📊 Expected Response Examples

### Successful Parent Creation:
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "auth0_user_id": "auth0|1234567890",
  "email": "test@example.com",
  "name": "John Doe",
  "created_at": "2025-11-09T21:30:00.000Z",
  "updated_at": "2025-11-09T21:30:00.000Z"
}
```

### Successful Child Creation:
```json
{
  "id": "660e8400-e29b-41d4-a716-446655440001",
  "parent_id": "550e8400-e29b-41d4-a716-446655440000",
  "name": "Alice",
  "age_group": "5-7",
  "avatar": "https://example.com/avatar.png",
  "voice_clone_enabled": false,
  "voice_clone_url": null,
  "is_online": false,
  "last_seen_at": "2025-11-09T21:30:00.000Z",
  "in_room": false,
  "room_id": null,
  "created_at": "2025-11-09T21:30:00.000Z",
  "updated_at": "2025-11-09T21:30:00.000Z"
}
```

---

**Happy Testing! 🚀**

For more endpoints, check the interactive API docs at http://localhost:8080/docs
