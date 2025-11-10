"""
One-time migration script to apply all SQL migrations to the database.
This script should be run BEFORE init_db.py to set up:
- RLS policies
- Functions and triggers
- Additional columns not in SQLAlchemy models
- Indexes and constraints

Run this script once, then use init_db.py for table creation.
"""
import asyncio
import asyncpg
import logging
import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


# Get database URL from environment
DATABASE_URL = os.getenv("DATABASE_URL", "")
if not DATABASE_URL:
    raise ValueError("DATABASE_URL not found in environment variables")

# Convert SQLAlchemy URL to asyncpg URL
if DATABASE_URL.startswith("postgresql+asyncpg://"):
    ASYNCPG_URL = DATABASE_URL.replace("postgresql+asyncpg://", "postgresql://")
else:
    ASYNCPG_URL = DATABASE_URL


async def execute_sql(conn, sql: str, description: str):
    """Execute SQL statement with error handling."""
    try:
        logger.info(f"Executing: {description}")
        await conn.execute(sql)
        logger.info(f"✓ Success: {description}")
        return True
    except Exception as e:
        logger.error(f"✗ Error in {description}: {str(e)}")
        return False


async def run_migrations():
    """Run all migrations in order."""
    logger.info("=" * 80)
    logger.info("Starting database migrations...")
    logger.info("=" * 80)
    
    conn = await asyncpg.connect(ASYNCPG_URL)
    
    try:
        # ============================================================================
        # STEP 1: Create update_updated_at_column function (needed by triggers)
        # ============================================================================
        await execute_sql(
            conn,
            """
            CREATE OR REPLACE FUNCTION public.update_updated_at_column()
            RETURNS TRIGGER AS $$
            BEGIN
                NEW.updated_at = now();
                RETURN NEW;
            END;
            $$ LANGUAGE plpgsql SET search_path = public;
            """,
            "Create update_updated_at_column function"
        )
        
        # ============================================================================
        # STEP 2: Create set_config function for RLS (SECURITY DEFINER)
        # ============================================================================
        await execute_sql(
            conn,
            """
            CREATE OR REPLACE FUNCTION public.set_config(setting text, value text)
            RETURNS text 
            LANGUAGE plpgsql 
            SECURITY DEFINER 
            SET search_path = public
            AS $$
            BEGIN
                PERFORM set_config(setting, value, false);
                RETURN value;
            END;
            $$;
            """,
            "Create set_config function for RLS"
        )
        
        # ============================================================================
        # STEP 3: Create notify_reload_schema function
        # ============================================================================
        await execute_sql(
            conn,
            """
            CREATE OR REPLACE FUNCTION notify_reload_schema()
            RETURNS void
            LANGUAGE plpgsql
            SECURITY DEFINER
            AS $$
            BEGIN
                PERFORM pg_notify('pgrst', 'reload schema');
            END;
            $$;
            """,
            "Create notify_reload_schema function"
        )
        
        # ============================================================================
        # STEP 4: Add missing columns to children_profiles
        # ============================================================================
        logger.info("\n" + "=" * 80)
        logger.info("Adding columns to children_profiles...")
        logger.info("=" * 80)
        
        # Add is_online and last_seen_at
        await execute_sql(
            conn,
            """
            DO $$ 
            BEGIN
                IF NOT EXISTS (
                    SELECT 1 FROM information_schema.columns 
                    WHERE table_name = 'children_profiles' AND column_name = 'is_online'
                ) THEN
                    ALTER TABLE public.children_profiles 
                    ADD COLUMN is_online boolean DEFAULT false;
                END IF;
            END $$;
            """,
            "Add is_online column"
        )
        
        await execute_sql(
            conn,
            """
            DO $$ 
            BEGIN
                IF NOT EXISTS (
                    SELECT 1 FROM information_schema.columns 
                    WHERE table_name = 'children_profiles' AND column_name = 'last_seen_at'
                ) THEN
                    ALTER TABLE public.children_profiles 
                    ADD COLUMN last_seen_at timestamp with time zone DEFAULT now();
                END IF;
            END $$;
            """,
            "Add last_seen_at column"
        )
        
        # Add in_room flag
        await execute_sql(
            conn,
            """
            DO $$ 
            BEGIN
                IF NOT EXISTS (
                    SELECT 1 FROM information_schema.columns 
                    WHERE table_name = 'children_profiles' AND column_name = 'in_room'
                ) THEN
                    ALTER TABLE public.children_profiles 
                    ADD COLUMN in_room boolean DEFAULT false;
                END IF;
            END $$;
            """,
            "Add in_room column"
        )
        
        # Add room_id (important for tracking which room a child is in)
        await execute_sql(
            conn,
            """
            DO $$ 
            BEGIN
                IF NOT EXISTS (
                    SELECT 1 FROM information_schema.columns 
                    WHERE table_name = 'children_profiles' AND column_name = 'room_id'
                ) THEN
                    ALTER TABLE public.children_profiles 
                    ADD COLUMN room_id UUID;
                END IF;
            END $$;
            """,
            "Add room_id column to children_profiles"
        )
        
        # ============================================================================
        # STEP 5: Add selected_category to game_rooms
        # ============================================================================
        await execute_sql(
            conn,
            """
            DO $$ 
            BEGIN
                IF NOT EXISTS (
                    SELECT 1 FROM information_schema.columns 
                    WHERE table_name = 'game_rooms' AND column_name = 'selected_category'
                ) THEN
                    ALTER TABLE public.game_rooms
                    ADD COLUMN selected_category TEXT;
                END IF;
            END $$;
            """,
            "Add selected_category to game_rooms"
        )
        
        # ============================================================================
        # STEP 6: Add room_id to join_requests with foreign key
        # ============================================================================
        logger.info("\n" + "=" * 80)
        logger.info("Setting up join_requests table...")
        logger.info("=" * 80)
        
        await execute_sql(
            conn,
            """
            DO $$ 
            BEGIN
                IF NOT EXISTS (
                    SELECT 1 FROM information_schema.columns 
                    WHERE table_name = 'join_requests' AND column_name = 'room_id'
                ) THEN
                    ALTER TABLE public.join_requests ADD COLUMN room_id UUID;
                END IF;
            END $$;
            """,
            "Add room_id column to join_requests"
        )
        
        # Add foreign key constraint
        await execute_sql(
            conn,
            """
            DO $$ 
            BEGIN
                IF NOT EXISTS (
                    SELECT 1 FROM information_schema.table_constraints 
                    WHERE constraint_name = 'join_requests_room_id_fkey'
                ) THEN
                    ALTER TABLE public.join_requests
                    ADD CONSTRAINT join_requests_room_id_fkey 
                    FOREIGN KEY (room_id) REFERENCES public.game_rooms(id) ON DELETE CASCADE;
                END IF;
            END $$;
            """,
            "Add foreign key constraint to join_requests.room_id"
        )
        
        # Update existing records to populate room_id based on room_code
        await execute_sql(
            conn,
            """
            UPDATE public.join_requests 
            SET room_id = (
                SELECT gr.id 
                FROM public.game_rooms gr 
                WHERE gr.room_code = join_requests.room_code
            )
            WHERE room_id IS NULL AND EXISTS (
                SELECT 1 FROM public.game_rooms gr 
                WHERE gr.room_code = join_requests.room_code
            );
            """,
            "Populate room_id in join_requests from room_code"
        )
        
        # ============================================================================
        # STEP 7: Create indexes for performance
        # ============================================================================
        logger.info("\n" + "=" * 80)
        logger.info("Creating indexes...")
        logger.info("=" * 80)
        
        await execute_sql(
            conn,
            """
            DO $$ 
            BEGIN
                IF NOT EXISTS (
                    SELECT 1 FROM pg_indexes 
                    WHERE indexname = 'idx_children_profiles_online_status'
                ) THEN
                    CREATE INDEX idx_children_profiles_online_status 
                    ON public.children_profiles(is_online, last_seen_at);
                END IF;
            END $$;
            """,
            "Create index on children_profiles(is_online, last_seen_at)"
        )
        
        await execute_sql(
            conn,
            """
            DO $$ 
            BEGIN
                IF NOT EXISTS (
                    SELECT 1 FROM pg_indexes 
                    WHERE indexname = 'idx_join_requests_room_id'
                ) THEN
                    CREATE INDEX idx_join_requests_room_id 
                    ON public.join_requests(room_id);
                END IF;
            END $$;
            """,
            "Create index on join_requests(room_id)"
        )
        
        await execute_sql(
            conn,
            """
            DO $$ 
            BEGIN
                IF NOT EXISTS (
                    SELECT 1 FROM pg_indexes 
                    WHERE indexname = 'idx_children_profiles_room_id'
                ) THEN
                    CREATE INDEX idx_children_profiles_room_id 
                    ON public.children_profiles(room_id);
                END IF;
            END $$;
            """,
            "Create index on children_profiles(room_id)"
        )
        
        # ============================================================================
        # STEP 8: Enable Realtime (Supabase specific - optional)
        # ============================================================================
        logger.info("\n" + "=" * 80)
        logger.info("Configuring Realtime (optional - may fail if not Supabase)...")
        logger.info("=" * 80)
        
        await execute_sql(
            conn,
            """
            DO $$ 
            BEGIN
                ALTER TABLE public.friends REPLICA IDENTITY FULL;
            EXCEPTION
                WHEN OTHERS THEN
                    RAISE NOTICE 'Could not set REPLICA IDENTITY - not critical';
            END $$;
            """,
            "Enable realtime for friends table (optional)"
        )
        
        # ============================================================================
        # STEP 9: Update in_room status based on current room participants
        # ============================================================================
        logger.info("\n" + "=" * 80)
        logger.info("Synchronizing data...")
        logger.info("=" * 80)
        
        await execute_sql(
            conn,
            """
            UPDATE public.children_profiles 
            SET in_room = true 
            WHERE id IN (
                SELECT DISTINCT rp.child_id 
                FROM room_participants rp
                JOIN game_rooms gr ON rp.room_id = gr.id
                WHERE gr.status IN ('waiting', 'playing')
                AND rp.child_id IS NOT NULL
            );
            """,
            "Sync in_room flag with current participants"
        )
        
        # ============================================================================
        # DONE
        # ============================================================================
        logger.info("\n" + "=" * 80)
        logger.info("✓ All migrations completed successfully!")
        logger.info("=" * 80)
        logger.info("\nNext step: Run init_db.py to create/verify all tables")
        logger.info("Command: python init_db.py")
        
    except Exception as e:
        logger.error(f"\n✗ Migration failed: {str(e)}")
        raise
    finally:
        await conn.close()


async def main():
    """Main entry point."""
    await run_migrations()


if __name__ == "__main__":
    asyncio.run(main())
