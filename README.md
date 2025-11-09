# FastAPI + Postgres Migration - MagicMinds API

Production-grade FastAPI backend replacing Supabase Edge Functions with direct Postgres (Supabase) connection and Auth0 JWT authentication.

## 🎯 Migration Status

### ✅ Completed
- [x] Project structure created
- [x] Configuration with Auth0 settings
- [x] Auth0 JWT validation with JWKS (RS256)
- [x] Database connection with RLS support
- [x] Connection string configured: `postgresql://postgres:Admin@1234@db.varjcgwapgivwikpgfin.supabase.co:5432/postgres`

### 🚧 To Complete
- [ ] SQLAlchemy models (9 models)
- [ ] Pydantic schemas
- [ ] Service layer
- [ ] FastAPI routers (6 routers)
- [ ] Middleware (CORS, logging, rate limit)
- [ ] Main application
- [ ] Dockerfile + Cloud Run deployment
- [ ] Alembic migrations
- [ ] Tests

## 📁 Project Structure

```
/app/api/
├── app/
│   ├── config.py              ✅ Settings with Auth0 + DB config
│   ├── main.py                ⏳ FastAPI app (TODO)
│   ├── deps/
│   │   ├── auth.py            ✅ Auth0 JWT validation
│   │   └── db.py              ✅ Async SQLAlchemy + RLS
│   ├── models/                ⏳ SQLAlchemy models (TODO)
│   │   ├── __init__.py        ✅
│   │   ├── parent_profile.py
│   │   ├── child_profile.py
│   │   ├── friend.py
│   │   ├── game_room.py
│   │   ├── join_request.py
│   │   ├── game_session.py
│   │   ├── generated_story.py
│   │   └── voice_subscription.py
│   ├── schemas/               ⏳ Pydantic models (TODO)
│   ├── routers/               ⏳ API endpoints (TODO)
│   │   ├── profiles.py
│   │   ├── friends.py
│   │   ├── rooms.py
│   │   ├── sessions.py
│   │   ├── stories.py
│   │   ├── billing.py
│   │   └── health.py
│   ├── services/              ⏳ Business logic (TODO)
│   ├── middleware/            ⏳ CORS, logging, rate limit (TODO)
│   └── utils/
├── migrations/                ⏳ Alembic (TODO)
├── tests/
├── .env.example               ✅
├── .env                       ⏳ (Create from .env.example)
├── Dockerfile                 ⏳ (TODO)
├── pyproject.toml             ⏳ (TODO)
└── README.md                  ✅ This file
```

## 🔑 Environment Setup

### 1. Create `.env` file

```bash
cp .env.example .env
```

### 2. Update `.env` with your values

```env
# Database (ALREADY CONFIGURED)
DATABASE_URL=postgresql+asyncpg://postgres:Admin@1234@db.varjcgwapgivwikpgfin.supabase.co:5432/postgres

# Auth0 (ALREADY CONFIGURED)
AUTH0_DOMAIN=dev-jbrriuc5vyjmiwtx.us.auth0.com
AUTH0_CLIENT_ID=eh3lkyPjejB7dngFewuGp6FSP1l6j39D
AUTH0_AUDIENCE=https://dev-jbrriuc5vyjmiwtx.us.auth0.com/userinfo
AUTH0_ISSUER=https://dev-jbrriuc5vyjmiwtx.us.auth0.com/
AUTH0_JWKS_URL=https://dev-jbrriuc5vyjmiwtx.us.auth0.com/.well-known/jwks.json

# CORS
ALLOWED_ORIGINS=http://localhost:3000,https://your-frontend.vercel.app

# Server
PORT=8080
DEBUG=false
```

## 🏗️ What's Already Built

### 1. Auth0 JWT Validation (`app/deps/auth.py`)

**Features:**
- ✅ JWKS fetching from Auth0
- ✅ RS256 signature verification
- ✅ Validates: iss, aud, exp, nbf, iat
- ✅ Extracts `sub` and `email` from token
- ✅ Returns `CurrentUser` object
- ✅ FastAPI dependency: `get_current_user()`

**Usage in routers:**
```python
from app.deps.auth import get_current_user, CurrentUser

@router.get("/profiles/parent")
async def get_parent_profile(
    current_user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    # current_user.sub = Auth0 user ID
    # current_user.email = User email
    pass
```

### 2. Database with RLS Support (`app/deps/db.py`)

**Features:**
- ✅ Async SQLAlchemy engine
- ✅ Session management
- ✅ RLS context setting: `set_rls_context(session, auth0_user_id)`
- ✅ Connection pooling
- ✅ FastAPI dependency: `get_db()`

**Usage in routers:**
```python
from app.deps.db import get_db, set_rls_context
from sqlalchemy.ext.asyncio import AsyncSession

@router.get("/profiles/parent")
async def get_parent_profile(
    current_user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    # CRITICAL: Set RLS context first!
    await set_rls_context(db, current_user.sub)
    
    # Now all queries respect RLS policies
    result = await db.execute(
        select(ParentProfile).where(
            ParentProfile.auth0_user_id == current_user.sub
        )
    )
    parent = result.scalar_one_or_none()
    return parent
```

## 📋 Edge Function → FastAPI Mapping

### Profiles Router (`/api/profiles/*`)

| Edge Function Action | New FastAPI Route | Method | Auth |
|---------------------|-------------------|--------|------|
| `create_parent` | `POST /profiles/parent` | POST | Required |
| `get_parent` | `GET /profiles/parent` | GET | Required |
| `create_child` | `POST /profiles/children` | POST | Required |
| `get_children` | `GET /profiles/children` | GET | Required |
| `update_child` | `PATCH /profiles/children/{id}` | PATCH | Required |
| `delete_child` | `DELETE /profiles/children/{id}` | DELETE | Required |
| `set_child_online_status` | `POST /profiles/children/{id}/status` | POST | Required |
| `update_in_room_status` | `POST /profiles/children/{id}/status` | POST | Required |

### Friends Router (`/api/friends/*`)

| Edge Function Action | New FastAPI Route | Method |
|---------------------|-------------------|--------|
| `send_friend_request` | `POST /friends/requests` | POST |
| `accept_friend_request` | `POST /friends/requests/{id}/accept` | POST |
| `decline_friend_request` | `POST /friends/requests/{id}/decline` | POST |
| `list_friends` | `GET /friends` | GET |
| `get_friend_requests` | `GET /friends/requests` | GET |
| `search_children` | `GET /children/search?q={query}` | GET |
| `get_friends_by_ids` | `POST /friends/by-ids` | POST |
| `list_all_children` | `GET /children` | GET |
| `unfriend` | `DELETE /friends/{child_id}` | DELETE |

### Game Rooms Router (`/api/rooms/*`)

| Edge Function Action | New FastAPI Route | Method |
|---------------------|-------------------|--------|
| `create_room` | `POST /rooms` | POST |
| `join_room` | `POST /rooms/join` | POST |
| `leave_room` | `POST /rooms/leave` | POST |
| `close_room` | `POST /rooms/close` | POST |
| `get_current_room` | `GET /rooms/current?child_id={id}` | GET |
| `get_room_participants` | `GET /rooms/{room_id}/participants` | GET |
| `invite_friends` | `POST /rooms/{room_id}/invite` | POST |
| `request_to_join` | `POST /rooms/{room_id}/requests` | POST |
| `handle_join_request` | `POST /rooms/requests/{request_id}/handle` | POST |
| `get_pending_invitations` | `GET /rooms/invitations/pending?child_id={id}` | GET |
| `accept_invitation` | `POST /rooms/invitations/{invitation_id}/accept` | POST |
| `decline_invitation` | `POST /rooms/invitations/{invitation_id}/decline` | POST |

## 🛠️ Next Steps to Complete Migration

### Step 1: Install Dependencies

```bash
cd /app/api
pip install fastapi uvicorn[standard] sqlalchemy[asyncio] asyncpg \
    python-jose[cryptography] python-multipart pydantic-settings \
    alembic httpx
```

### Step 2: Create `pyproject.toml`

```toml
[project]
name = "magicminds-api"
version = "1.0.0"
requires-python = ">=3.12"
dependencies = [
    "fastapi>=0.109.0",
    "uvicorn[standard]>=0.27.0",
    "sqlalchemy[asyncio]>=2.0.25",
    "asyncpg>=0.29.0",
    "python-jose[cryptography]>=3.3.0",
    "pydantic>=2.6.0",
    "pydantic-settings>=2.1.0",
    "alembic>=1.13.1",
    "httpx>=0.26.0",
]

[build-system]
requires = ["setuptools>=68.0"]
build-backend = "setuptools.build_meta"
```

### Step 3: Create Remaining Models

Follow this pattern for all 9 models (example for `ParentProfile`):

```python
# app/models/parent_profile.py
from sqlalchemy import Column, String, DateTime, text
from sqlalchemy.dialects.postgresql import UUID
from datetime import datetime
from ..deps.db import Base

class ParentProfile(Base):
    __tablename__ = "parent_profiles"
    __table_args__ = {"schema": "public"}
    
    id = Column(UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()"))
    auth0_user_id = Column(String, unique=True, nullable=False)
    email = Column(String, nullable=False)
    name = Column(String)
    created_at = Column(DateTime(timezone=True), server_default=text("now()"))
    updated_at = Column(DateTime(timezone=True), server_default=text("now()"), onupdate=datetime.utcnow)
```

### Step 4: Create Main App

```python
# app/main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .config import get_settings
from .routers import profiles, friends, rooms, sessions, stories, billing, health

settings = get_settings()

app = FastAPI(
    title="MagicMinds API",
    version="1.0.0",
    docs_url="/docs",
    openapi_url="/openapi.json"
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(health.router, tags=["Health"])
app.include_router(profiles.router, prefix="/profiles", tags=["Profiles"])
app.include_router(friends.router, prefix="/friends", tags=["Friends"])
app.include_router(rooms.router, prefix="/rooms", tags=["Rooms"])
app.include_router(sessions.router, prefix="/sessions", tags=["Sessions"])
app.include_router(stories.router, prefix="/stories", tags=["Stories"])
app.include_router(billing.router, prefix="/billing", tags=["Billing"])

@app.on_event("startup")
async def startup():
    from .deps.db import init_db
    await init_db()

@app.on_event("shutdown")
async def shutdown():
    from .deps.db import close_db
    await close_db()
```

### Step 5: Run Locally

```bash
cd /app/api
uvicorn app.main:app --host 0.0.0.0 --port 8080 --reload
```

### Step 6: Test Auth0 JWT

```bash
# Get token from your frontend, then:
curl -H "Authorization: Bearer YOUR_AUTH0_TOKEN" \\
  http://localhost:8080/profiles/parent
```

## 🚀 Cloud Run Deployment

### Dockerfile

```dockerfile
FROM python:3.12-slim

WORKDIR /app

COPY pyproject.toml ./
RUN pip install --no-cache-dir .

COPY app ./app

RUN useradd -m appuser && chown -R appuser:appuser /app
USER appuser

EXPOSE 8080

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8080"]
```

### Deploy Commands

```bash
# Build
gcloud builds submit --tag gcr.io/YOUR_PROJECT/magicminds-api

# Deploy
gcloud run deploy magicminds-api \\
  --image gcr.io/YOUR_PROJECT/magicminds-api \\
  --platform managed \\
  --region us-central1 \\
  --allow-unauthenticated \\
  --set-env-vars "DATABASE_URL=postgresql+asyncpg://...,AUTH0_DOMAIN=..." \\
  --max-instances 10
```

## 📊 API Documentation

Once running, visit:
- **Swagger UI**: http://localhost:8080/docs
- **ReDoc**: http://localhost:8080/redoc
- **OpenAPI JSON**: http://localhost:8080/openapi.json

## 🔐 Security Notes

1. **RLS is CRITICAL**: Always call `await set_rls_context(db, current_user.sub)` before any database query
2. **Auth0 JWT**: Validates RS256 signatures, checks iss/aud/exp
3. **No Service Role Key**: Direct Postgres connection, no Supabase keys needed
4. **CORS**: Configure `ALLOWED_ORIGINS` for your frontend domains

## ✅ Testing Checklist

- [ ] GET /healthz returns 200
- [ ] Auth0 JWT validation works (401 without token)
- [ ] RLS policies work (users can only see their data)
- [ ] Create parent profile
- [ ] Create child profile
- [ ] Send friend request
- [ ] Create game room
- [ ] Join game room
- [ ] All Edge Function actions ported

## 📞 Support

For issues with:
- **Auth0**: Check JWT claims at https://jwt.io
- **Database**: Verify RLS policies in Supabase dashboard
- **Cloud Run**: Check logs in GCP Console

---

**Status**: Foundation complete. Ready to build remaining routers and deploy!
