"""Health check endpoints."""
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from ..deps.db import get_db

router = APIRouter()

@router.get("/healthz")
async def healthz():
    """Liveness probe for Kubernetes/Cloud Run."""
    return {"status": "healthy"}

@router.get("/readyz")
async def readyz(db: AsyncSession = Depends(get_db)):
    """Readiness probe - checks database connection."""
    try:
        await db.execute(text("SELECT 1"))
        return {"status": "ready", "database": "connected"}
    except Exception as e:
        return {"status": "not_ready", "database": "disconnected", "error": str(e)}
