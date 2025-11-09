# Local Testing Guide - MagicMinds API

Complete guide to test the FastAPI backend locally before deploying to Cloud Run.

## 📋 Prerequisites

- Python 3.12+
- pip
- Auth0 account (already configured)
- Supabase account (already configured)

## 🚀 Quick Start (5 minutes)

### Step 1: Install Dependencies

```bash
cd /app/api
pip install fastapi uvicorn[standard] sqlalchemy[asyncio] asyncpg python-jose[cryptography] httpx pydantic-settings
```

Or install all dependencies from pyproject.toml:

```bash
pip install -e .
```

### Step 2: Verify Environment

The `.env` file is already created with your Supabase and Auth0 credentials:

```bash
cat .env
```

You should see:
- ✅ `DATABASE_URL=postgresql+asyncpg://postgres:Admin@1234@...` (Supabase)
- ✅ `AUTH0_DOMAIN=dev-jbrriuc5vyjmiwtx.us.auth0.com`
- ✅ All other Auth0 settings

### Step 3: Run the API

```bash
uvicorn app.main:app --reload --port 8080
```

Expected output:
```
INFO:     Will watch for changes in these directories: ['/app/api']
INFO:     Uvicorn running on http://0.0.0.0:8080 (Press CTRL+C to quit)
INFO:     Started reloader process
INFO:     Started server process
INFO:     Waiting for application startup.
INFO:     Starting FastAPI application...
INFO:     Database initialized
INFO:     Application startup complete.
```

### Step 4: Test Health Endpoints

```bash
# Liveness probe (should work immediately)
curl http://localhost:8080/healthz

# Expected: {"status":"healthy"}

# Readiness probe (tests database connection)
curl http://localhost:8080/readyz

# Expected: {"status":"ready","database":"connected"}
```

### Step 5: Access API Documentation

Open in browser:
- **Swagger UI**: http://localhost:8080/docs
- **ReDoc**: http://localhost:8080/redoc
- **OpenAPI JSON**: http://localhost:8080/openapi.json

## 🔐 Testing with Auth0 JWT

### Option 1: Get Token from Frontend

If you have a frontend that already authenticates with Auth0:

1. Login to your frontend
2. Open browser DevTools → Network tab
3. Find an API request with `Authorization` header
4. Copy the token (starts with `eyJ...`)

### Option 2: Get Token via Auth0 Dashboard

1. Go to https://manage.auth0.com
2. Navigate to Applications → APIs
3. Select your API
4. Go to "Test" tab
5. Copy the access token

### Option 3: Use Auth0 Test Tool

```bash
# Install Auth0 CLI (optional)
brew install auth0

# Get token
auth0 test token
```

### Test Protected Endpoint (Example)

```bash
# Replace YOUR_TOKEN with actual Auth0 JWT
curl -H "Authorization: Bearer YOUR_TOKEN" \\
  http://localhost:8080/profiles/parent
```

**Expected responses:**
- ✅ `200 OK` with user data (if authenticated)
- ❌ `401 Unauthorized` (if token invalid/expired)
- ❌ `404 Not Found` (if profile doesn't exist yet)

## 🧪 Testing RLS (Row Level Security)

### Verify RLS Context Setting

The API automatically sets RLS context on every authenticated request:

```sql
SELECT set_config('app.current_auth0_user_id', :user_id, false)
```

### Test RLS in Supabase Dashboard

1. Go to https://supabase.com/dashboard
2. Select your project
3. Go to SQL Editor
4. Run:

```sql
-- Set RLS context manually
SELECT set_config('app.current_auth0_user_id', 'auth0|YOUR_USER_ID', false);

-- Now query with RLS active
SELECT * FROM public.parent_profiles;
```

You should only see YOUR data, not all users.

## 📊 Database Verification

### Check Tables Exist

```bash
# Using psql
psql "postgresql://postgres:Admin@1234@db.varjcgwapgivwikpgfin.supabase.co:5432/postgres" \\
  -c "\\dt public.*"
```

Expected tables:
- ✅ parent_profiles
- ✅ children_profiles
- ✅ friends
- ✅ game_rooms
- ✅ room_participants
- ✅ join_requests
- ✅ multiplayer_game_sessions
- ✅ multiplayer_game_scores
- ✅ generated_stories
- ✅ voice_subscriptions

### Verify RLS Policies

```bash
psql "postgresql://postgres:Admin@1234@..." \\
  -c "SELECT tablename, policyname FROM pg_policies WHERE schemaname = 'public';"
```

## 🐛 Troubleshooting

### Issue: `ModuleNotFoundError`

```bash
# Solution: Install missing dependencies
pip install fastapi uvicorn sqlalchemy asyncpg python-jose httpx pydantic-settings
```

### Issue: Database Connection Error

```bash
# Check 1: Verify DATABASE_URL in .env
cat .env | grep DATABASE_URL

# Check 2: Test connection directly
psql "postgresql://postgres:Admin@1234@db.varjcgwapgivwikpgfin.supabase.co:5432/postgres" -c "SELECT 1"

# Check 3: Verify Supabase project is active
# Go to https://supabase.com/dashboard and check project status
```

### Issue: `401 Unauthorized` with valid token

```bash
# Check 1: Verify token hasn't expired
# Decode at https://jwt.io - check 'exp' claim

# Check 2: Verify Auth0 settings in .env
cat .env | grep AUTH0

# Check 3: Check JWKS is accessible
curl https://dev-jbrriuc5vyjmiwtx.us.auth0.com/.well-known/jwks.json
```

### Issue: RLS Blocking Queries

```bash
# Check 1: Verify user_id in token matches database
# Token 'sub' claim must match parent_profiles.auth0_user_id

# Check 2: Check RLS context was set
# Add logging in deps/db.py to verify set_rls_context() is called

# Check 3: Temporarily disable RLS for testing
psql "..." -c "ALTER TABLE public.parent_profiles DISABLE ROW LEVEL SECURITY;"
```

## 📝 Example API Calls

### 1. Create Parent Profile

```bash
curl -X POST http://localhost:8080/profiles/parent \\
  -H "Authorization: Bearer YOUR_TOKEN" \\
  -H "Content-Type: application/json" \\
  -d '{"name": "John Doe"}'
```

### 2. Get Parent Profile

```bash
curl http://localhost:8080/profiles/parent \\
  -H "Authorization: Bearer YOUR_TOKEN"
```

### 3. Create Child Profile

```bash
curl -X POST http://localhost:8080/profiles/children \\
  -H "Authorization: Bearer YOUR_TOKEN" \\
  -H "Content-Type: application/json" \\
  -d '{
    "name": "Alice",
    "age_group": "5-7",
    "avatar": "https://example.com/avatar.png"
  }'
```

### 4. List Children

```bash
curl http://localhost:8080/profiles/children \\
  -H "Authorization: Bearer YOUR_TOKEN"
```

## ✅ Success Criteria

Your API is working correctly if:

1. ✅ Health checks return 200 OK
2. ✅ `/docs` loads Swagger UI
3. ✅ Database connection works (`/readyz`)
4. ✅ Auth0 JWT validation works (401 without token)
5. ✅ RLS policies work (users only see their own data)
6. ✅ CRUD operations succeed with valid token

## 🎯 Next Steps

Once local testing passes:

1. **Complete remaining routers** (profiles, friends, rooms, etc.)
2. **Write unit tests** (`pytest`)
3. **Deploy to Cloud Run** (see README.md)
4. **Set up CI/CD** (GitHub Actions)
5. **Monitor logs** (GCP Console)

## 📞 Need Help?

### Check Logs

```bash
# API logs
tail -f /var/log/supervisor/api.log

# Or run with verbose logging
uvicorn app.main:app --reload --log-level debug
```

### Common Commands

```bash
# Restart API
pkill -f uvicorn
uvicorn app.main:app --reload --port 8080

# Check what's running
ps aux | grep uvicorn

# Check port usage
lsof -i :8080
```

---

**Happy Testing! 🚀**

Once everything works locally, push to GitHub and deploy to Cloud Run using the instructions in README.md.
