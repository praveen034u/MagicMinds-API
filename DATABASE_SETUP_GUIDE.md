# Database Setup Guide

This guide explains how to set up your database from scratch using the migration and initialization scripts.

## Overview

The database setup is split into two stages:

1. **`run_migrations.py`** - Applies SQL migrations (RLS policies, functions, indexes, additional columns)
2. **`init_db.py`** - Creates tables from SQLAlchemy models

## Prerequisites

- Python 3.11+
- PostgreSQL database (local or Supabase)
- `.env` file configured with `DATABASE_URL`
- Required Python packages installed:
  ```bash
  pip install asyncpg python-dotenv
  ```

## Step-by-Step Setup

### 1. Configure Environment

Ensure your `.env` file has the correct database URL:

```env
# For Supabase (production)
DATABASE_URL=postgresql+asyncpg://postgres:Admin%401234@db.varjcgwapgivwikpgfin.supabase.co:5432/postgres

# For local development
# DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/magicminds
```

### 2. Run Migrations First

```bash
python run_migrations.py
```

**What this does:**
- ✅ Creates utility functions (`update_updated_at_column`, `set_config`, `notify_reload_schema`)
- ✅ Adds columns not in SQLAlchemy models:
  - `children_profiles.is_online`
  - `children_profiles.last_seen_at`
  - `children_profiles.in_room`
  - `children_profiles.room_id`
  - `game_rooms.selected_category`
  - `join_requests.room_id`
- ✅ Creates indexes for performance
- ✅ Sets up foreign key constraints
- ✅ Synchronizes data (in_room flags, room_id references)
- ✅ Enables realtime (Supabase only, optional)

**Expected output:**
```
================================================================================
Starting database migrations...
================================================================================
Executing: Create update_updated_at_column function
✓ Success: Create update_updated_at_column function
...
✓ All migrations completed successfully!
================================================================================
```

### 3. Initialize Tables

```bash
python init_db.py
```

**What this does:**
- ✅ Creates all tables defined in SQLAlchemy models
- ✅ Verifies existing tables (idempotent - safe to run multiple times)
- ✅ Preserves existing data

**Expected output:**
```
================================================================================
Creating database tables from SQLAlchemy models...
================================================================================

Tables managed by SQLAlchemy (10):
  1. parent_profiles
  2. children_profiles
  3. friends
  4. game_rooms
  5. room_participants
  6. join_requests
  7. multiplayer_game_sessions
  8. multiplayer_game_scores
  9. generated_stories
  10. voice_subscriptions
...
✓ Database tables created/verified successfully!
```

### 4. Start the API

```bash
python -m uvicorn app.main:app --reload --port 8080
```

Visit http://localhost:8080/docs to see the API documentation.

## Tables Created

### Core Tables (from SQLAlchemy models)

1. **parent_profiles** - Parent user accounts
   - `id`, `auth0_user_id`, `email`, `name`

2. **children_profiles** - Child profiles
   - `id`, `parent_id`, `name`, `age_group`, `avatar`
   - `voice_clone_enabled`, `voice_clone_url`
   - `is_online`, `last_seen_at`, `in_room`, `room_id` ✨ (from migrations)

3. **friends** - Friend relationships
   - `id`, `requester_id`, `addressee_id`, `status`

4. **game_rooms** - Multiplayer game rooms
   - `id`, `room_code`, `host_child_id`, `game_id`
   - `difficulty`, `max_players`, `current_players`, `status`
   - `has_ai_player`, `ai_player_name`, `ai_player_avatar`
   - `selected_category` ✨ (from migrations)

5. **room_participants** - Players in rooms
   - `id`, `room_id`, `child_id`, `player_name`, `is_ai`

6. **join_requests** - Room invitations
   - `id`, `room_code`, `child_id`, `player_name`, `status`
   - `room_id` ✨ (from migrations)

7. **multiplayer_game_sessions** - Game sessions
   - `id`, `room_id`, `game_data`, `game_state`

8. **multiplayer_game_scores** - Player scores
   - `id`, `room_id`, `child_id`, `score`, `total_questions`

9. **generated_stories** - AI-generated stories
   - `id`, `child_id`, `title`, `content`, `audio_url`

10. **voice_subscriptions** - Billing subscriptions
    - `id`, `parent_id`, `stripe_subscription_id`, `status`

### Functions Created (from migrations)

- **`update_updated_at_column()`** - Trigger function for auto-updating timestamps
- **`set_config(setting, value)`** - Security definer for RLS context
- **`notify_reload_schema()`** - PostgREST schema cache reload

### Indexes Created (from migrations)

- `idx_children_profiles_online_status` - Fast online status queries
- `idx_join_requests_room_id` - Fast join request lookups
- `idx_children_profiles_room_id` - Fast room membership queries

## Important Notes

### ⚠️ RLS Policies

The migrations script does **NOT** create RLS policies. These are assumed to be already set up in Supabase or need to be added separately.

If you need RLS policies, you can find them in the original SQL migration files under `/migrations/`.

### 🔄 Idempotency

Both scripts are idempotent (safe to run multiple times):
- `run_migrations.py` - Uses `IF NOT EXISTS` checks
- `init_db.py` - Uses `CREATE TABLE IF NOT EXISTS` (via SQLAlchemy)

### 📊 Data Preservation

Both scripts preserve existing data:
- Tables are **not dropped** by default
- Existing columns are **not modified**
- Only missing columns/indexes are added

### 🆕 Starting Fresh

To completely reset the database (⚠️ **DANGER - DELETES ALL DATA**):

1. Uncomment the drop line in `init_db.py`:
   ```python
   await conn.run_sync(Base.metadata.drop_all)
   ```

2. Run:
   ```bash
   python init_db.py
   python run_migrations.py
   ```

## Troubleshooting

### Error: "relation does not exist"

**Solution:** Run `init_db.py` first to create tables, then `run_migrations.py`

### Error: "asyncpg not found"

**Solution:**
```bash
pip install asyncpg
```

### Error: "DATABASE_URL not found"

**Solution:** Ensure `.env` file exists and contains `DATABASE_URL`

### Error: Connection refused

**Solution:** 
- For local: Start PostgreSQL server
- For Supabase: Check database URL and password encoding

### Warning: "Could not set REPLICA IDENTITY"

**Solution:** This is normal for non-Supabase databases. It's an optional step for realtime subscriptions.

## Migration Files Reference

The `run_migrations.py` script consolidates these SQL migrations:

1. `20250925020431_*.sql` - Core tables (parent_profiles, children_profiles, etc.)
2. `20250925020918_*.sql` - set_config function
3. `20250925020955_*.sql` - set_config security fix
4. `20250926044741_*.sql` - Friends and game rooms tables
5. `20250926045031_*.sql` - Foreign key constraints
6. `20250928094148_*.sql` - Online status columns
7. `20250928100855_*.sql` - Realtime configuration
8. `20250928103735_*.sql` - in_room flag
9. `20250928111018_*.sql` - join_requests table
10. `20250928124732_*.sql` - multiplayer_game_scores table
11. `20251004155854_*.sql` - join_requests.room_id with foreign key
12. `20251102000000_*.sql` - selected_category column
13. `20250129000000_*.sql` - join_requests foreign key fix
14. `20250129000001_*.sql` - notify_reload_schema function

## What Gets Created Where

| Feature | Created By | File |
|---------|-----------|------|
| Tables | `init_db.py` | SQLAlchemy models |
| Columns (base) | `init_db.py` | SQLAlchemy models |
| Columns (extra) | `run_migrations.py` | SQL migrations |
| Indexes | `run_migrations.py` | SQL migrations |
| Functions | `run_migrations.py` | SQL migrations |
| Triggers | `run_migrations.py` | SQL migrations |
| Foreign Keys | `run_migrations.py` | SQL migrations |
| RLS Policies | **Manual** | Original SQL files |

## Quick Start (TL;DR)

```bash
# 1. Ensure .env has DATABASE_URL
# 2. Run migrations
python run_migrations.py

# 3. Create tables
python init_db.py

# 4. Start API
python -m uvicorn app.main:app --reload --port 8080
```

Done! 🎉
