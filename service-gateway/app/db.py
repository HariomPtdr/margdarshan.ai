"""Postgres pool + schema bootstrap for users and complaints."""

import logging
import os
from typing import Optional

import asyncpg

logger = logging.getLogger(__name__)

POSTGRES_HOST = os.getenv("POSTGRES_HOST", "postgres")
POSTGRES_PORT = int(os.getenv("POSTGRES_PORT", "5432"))
POSTGRES_USER = os.getenv("POSTGRES_USER", "grievance")
POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD", "changeme")
POSTGRES_DB = os.getenv("POSTGRES_DB", "grievance")

_pool: Optional[asyncpg.Pool] = None

SCHEMA_SQL = """
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

CREATE TABLE IF NOT EXISTS users (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  name TEXT NOT NULL,
  gender TEXT,
  email TEXT UNIQUE NOT NULL,
  mobile TEXT UNIQUE NOT NULL,
  phone TEXT,
  password_hash TEXT NOT NULL,
  address TEXT,
  sub_locality TEXT,
  locality TEXT,
  state TEXT,
  district TEXT,
  pincode TEXT,
  country TEXT DEFAULT 'India',
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS complaints (
  complaint_id UUID PRIMARY KEY,
  user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  summary TEXT NOT NULL DEFAULT '',
  intent TEXT,
  state TEXT,
  department TEXT,
  ticket_id TEXT,
  status TEXT NOT NULL DEFAULT 'active',
  pipeline_data JSONB NOT NULL DEFAULT '{}'::jsonb,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_complaints_user_id ON complaints(user_id);
CREATE INDEX IF NOT EXISTS idx_complaints_created_at ON complaints(created_at DESC);

-- Columns used by the duplicate-check query (Stage 7).
ALTER TABLE complaints ADD COLUMN IF NOT EXISTS sub_category   TEXT;
ALTER TABLE complaints ADD COLUMN IF NOT EXISTS district       TEXT;
ALTER TABLE complaints ADD COLUMN IF NOT EXISTS portal_id      TEXT;
-- S-BERT 384-dim embedding stored as a float8 array for cosine-similarity dedup.
ALTER TABLE complaints ADD COLUMN IF NOT EXISTS text_embedding FLOAT8[];

-- Covering index for the dedup query: dept + sub_cat + district, unresolved, recent.
CREATE INDEX IF NOT EXISTS idx_complaints_dedup
    ON complaints(department, sub_category, district, status, created_at DESC)
    WHERE status NOT IN ('resolved', 'rejected');

CREATE TABLE IF NOT EXISTS messages (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  complaint_id UUID REFERENCES complaints(complaint_id) ON DELETE SET NULL,
  user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  session_id TEXT NOT NULL DEFAULT '',
  role TEXT NOT NULL CHECK (role IN ('user', 'assistant')),
  content TEXT NOT NULL,
  seq BIGSERIAL,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Migrations for existing deployments.
ALTER TABLE messages ADD COLUMN IF NOT EXISTS seq BIGSERIAL;
ALTER TABLE messages ADD COLUMN IF NOT EXISTS user_id UUID REFERENCES users(id) ON DELETE CASCADE;
ALTER TABLE messages ADD COLUMN IF NOT EXISTS session_id TEXT NOT NULL DEFAULT '';
ALTER TABLE messages ALTER COLUMN complaint_id DROP NOT NULL;

CREATE INDEX IF NOT EXISTS idx_messages_complaint_id ON messages(complaint_id, seq);
CREATE INDEX IF NOT EXISTS idx_messages_user_session ON messages(user_id, session_id, seq);

-- Tamper-evident audit trail: each event hashes itself + the previous event.
CREATE TABLE IF NOT EXISTS complaint_events (
    event_id      UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
    complaint_id  UUID        NOT NULL REFERENCES complaints(complaint_id) ON DELETE CASCADE,
    event_type    TEXT        NOT NULL,
    actor         TEXT        NOT NULL DEFAULT 'system',
    details       JSONB       NOT NULL DEFAULT '{}'::jsonb,
    prev_hash     TEXT,
    event_hash    TEXT        NOT NULL,
    created_at    TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_events_complaint ON complaint_events(complaint_id, created_at);
"""


async def _init_connection(conn: asyncpg.Connection):
    """Register JSON codec so JSONB columns are auto-decoded to Python dicts."""
    import json as _json
    await conn.set_type_codec(
        "jsonb",
        encoder=_json.dumps,
        decoder=_json.loads,
        schema="pg_catalog",
        format="text",
    )
    await conn.set_type_codec(
        "json",
        encoder=_json.dumps,
        decoder=_json.loads,
        schema="pg_catalog",
        format="text",
    )


async def connect():
    global _pool
    import asyncio
    delays = [2, 4, 8, 15, 30]
    last_exc: Exception = RuntimeError("never tried")
    for delay in [0] + delays:
        if delay:
            logger.info("Postgres not ready, retrying in %ds…", delay)
            await asyncio.sleep(delay)
        try:
            _pool = await asyncpg.create_pool(
                host=POSTGRES_HOST,
                port=POSTGRES_PORT,
                user=POSTGRES_USER,
                password=POSTGRES_PASSWORD,
                database=POSTGRES_DB,
                min_size=1,
                max_size=10,
                init=_init_connection,
            )
            async with _pool.acquire() as conn:
                await conn.execute(SCHEMA_SQL)
            logger.info("Postgres pool ready, schema applied")
            return
        except Exception as exc:
            last_exc = exc
            logger.warning("Postgres connection failed: %s", exc)
    raise RuntimeError(f"Could not connect to Postgres after retries: {last_exc}") from last_exc


async def close():
    global _pool
    if _pool:
        await _pool.close()
        _pool = None


def pool() -> asyncpg.Pool:
    if _pool is None:
        raise RuntimeError("DB pool not initialized")
    return _pool
