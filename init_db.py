"""Initialize database tables from SQLAlchemy models."""
import asyncio
import logging
from app.deps.db import engine, Base
from app.models import (
    parent_profile,
    child_profile,
    friend,
    game_room,
    game_session,
    generated_story,
    join_request,
    voice_subscription
)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

async def init_database():
    """Create all database tables from SQLAlchemy models."""
    logger.info("=" * 80)
    logger.info("Creating database tables from SQLAlchemy models...")
    logger.info("=" * 80)
    
    logger.info("\nNOTE: Make sure you've run 'python run_migrations.py' first!")
    logger.info("      Migrations add RLS policies, indexes, and additional columns.")
    
    async with engine.begin() as conn:
        # IMPORTANT: Do NOT drop tables if you have data
        # Uncomment the next line ONLY if you want to start fresh
        # await conn.run_sync(Base.metadata.drop_all)
        
        # Create all tables defined in SQLAlchemy models
        await conn.run_sync(Base.metadata.create_all)
    
    logger.info("\n" + "=" * 80)
    logger.info("✓ Database tables created/verified successfully!")
    logger.info("=" * 80)
    
    # Log all tables that were created/verified
    tables = [table.name for table in Base.metadata.sorted_tables]
    logger.info(f"\nTables managed by SQLAlchemy ({len(tables)}):")
    for i, table in enumerate(tables, 1):
        logger.info(f"  {i}. {table}")
    
    logger.info("\n" + "=" * 80)
    logger.info("Database initialization complete!")
    logger.info("=" * 80)
    logger.info("\nYou can now start the API server:")
    logger.info("  python -m uvicorn app.main:app --reload --port 8080")

async def main():
    """Main entry point."""
    try:
        await init_database()
    except Exception as e:
        logger.error(f"\n✗ Error during database initialization: {str(e)}")
        raise
    finally:
        await engine.dispose()

if __name__ == "__main__":
    asyncio.run(main())
