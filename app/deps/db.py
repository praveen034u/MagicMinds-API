"""Database session management with RLS support."""
from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import declarative_base
from sqlalchemy import text, event
from ..config import get_settings
import logging

logger = logging.getLogger(__name__)

settings = get_settings()

# Create async engine
engine = create_async_engine(
    settings.DATABASE_URL,
    echo=settings.DEBUG,
    pool_pre_ping=True,
    pool_size=10,
    max_overflow=20,
)

# Create async session factory
AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)

# Base class for models
Base = declarative_base()

async def set_rls_context(session: AsyncSession, auth0_user_id: str):
    """Set RLS context for the session.
    
    This executes: SELECT set_config('app.current_auth0_user_id', :user_id, false)
    which enables RLS policies to filter data by the authenticated user.
    """
    try:
        await session.execute(
            text("SELECT set_config('app.current_auth0_user_id', :user_id, false)"),
            {"user_id": auth0_user_id}
        )
        logger.debug(f"Set RLS context for user: {auth0_user_id}")
    except Exception as e:
        logger.error(f"Failed to set RLS context: {e}")
        raise

async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Dependency to get database session.
    
    Note: RLS context should be set per-request after authentication.
    Use set_rls_context(session, user.sub) in your endpoints.
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()

async def init_db():
    """Initialize database (create tables if needed - for dev only)."""
    async with engine.begin() as conn:
        # In production, use Alembic migrations instead
        # await conn.run_sync(Base.metadata.create_all)
        pass

async def close_db():
    """Close database connections."""
    await engine.dispose()
