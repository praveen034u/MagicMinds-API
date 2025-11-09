"""FastAPI main application."""
import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from .config import get_settings
from .deps.db import init_db, close_db
from .routers import health
# Import other routers when created:
# from .routers import profiles, friends, rooms, sessions, stories, billing

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

settings = get_settings()

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events."""
    # Startup
    logger.info("Starting FastAPI application...")
    await init_db()
    logger.info("Database initialized")
    yield
    # Shutdown
    logger.info("Shutting down FastAPI application...")
    await close_db()
    logger.info("Database connections closed")

app = FastAPI(
    title="MagicMinds API",
    version="1.0.0",
    description="Production FastAPI backend with Auth0 JWT and Postgres (Supabase)",
    docs_url="/docs",
    openapi_url="/openapi.json",
    lifespan=lifespan
)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(health.router, tags=["Health"])

# TODO: Uncomment as routers are created
# app.include_router(profiles.router, prefix="/profiles", tags=["Profiles"])
# app.include_router(friends.router, prefix="/friends", tags=["Friends"])
# app.include_router(rooms.router, prefix="/rooms", tags=["Rooms"])
# app.include_router(sessions.router, prefix="/sessions", tags=["Sessions"])
# app.include_router(stories.router, prefix="/stories", tags=["Stories"])
# app.include_router(billing.router, prefix="/billing", tags=["Billing"])

@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "message": "MagicMinds API",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/healthz"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=settings.PORT,
        reload=settings.DEBUG
    )
