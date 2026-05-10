"""Tamper-evident audit trail for complaint events.

Each event stores a SHA-256 hash of (prev_hash + event_type + details + timestamp).
The chain can be verified by any auditor by recomputing hashes from genesis.
"""

import hashlib
import json
import logging
from datetime import datetime, timezone

from . import db

logger = logging.getLogger(__name__)


async def log_event(
    complaint_id: str,
    event_type: str,
    details: dict,
    actor: str = "system",
) -> str:
    """Append an event to the audit chain for complaint_id. Returns the event_hash."""
    try:
        async with db.pool().acquire() as conn:
            # Fetch the most recent event hash for this complaint (the prev_hash).
            prev_hash: str | None = await conn.fetchval(
                "SELECT event_hash FROM complaint_events "
                "WHERE complaint_id = $1 ORDER BY created_at DESC LIMIT 1",
                complaint_id,
            )

            now = datetime.now(timezone.utc).isoformat()
            raw = f"{prev_hash or ''}{event_type}{json.dumps(details, sort_keys=True)}{now}"
            event_hash = hashlib.sha256(raw.encode()).hexdigest()

            await conn.execute(
                """
                INSERT INTO complaint_events
                    (complaint_id, event_type, actor, details, prev_hash, event_hash, created_at)
                VALUES ($1, $2, $3, $4, $5, $6, $7)
                """,
                complaint_id, event_type, actor,
                json.dumps(details), prev_hash, event_hash, now,
            )
            return event_hash
    except Exception as e:
        logger.error("audit.log_event failed for %s: %s", complaint_id, e)
        return ""


async def get_chain(complaint_id: str) -> list[dict]:
    """Return the full audit chain for a complaint, ordered oldest-first."""
    try:
        async with db.pool().acquire() as conn:
            rows = await conn.fetch(
                "SELECT event_id, event_type, actor, details, prev_hash, event_hash, created_at "
                "FROM complaint_events WHERE complaint_id = $1 ORDER BY created_at ASC",
                complaint_id,
            )
        return [
            {
                "event_id":   str(r["event_id"]),
                "event_type": r["event_type"],
                "actor":      r["actor"],
                "details":    r["details"],
                "prev_hash":  r["prev_hash"],
                "event_hash": r["event_hash"],
                "created_at": r["created_at"].isoformat(),
            }
            for r in rows
        ]
    except Exception as e:
        logger.error("audit.get_chain failed: %s", e)
        return []
