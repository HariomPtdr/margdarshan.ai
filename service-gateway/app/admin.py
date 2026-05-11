"""Government dashboard admin endpoints.

All data is read-only (reads) or write (review/status). No auth guard for prototype.

GET  /api/v1/admin/stats                              — system-wide metrics
GET  /api/v1/admin/portals                            — portal list with complaint counts
GET  /api/v1/admin/portals/{portal_id}               — portal detail + complaints routed to it
GET  /api/v1/admin/complaints                        — paginated complaint list (filterable)
GET  /api/v1/admin/complaints/{complaint_id}         — full complaint with audit chain + dup filers
POST /api/v1/admin/complaints/{complaint_id}/review  — submit reviewer feedback
POST /api/v1/admin/complaints/{complaint_id}/status  — update complaint status (notifies user)
"""

import json
import logging
import os
from typing import Optional

import httpx
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel

from . import auth, db
from .audit import get_chain

logger = logging.getLogger(__name__)

ROUTING_URL = os.getenv("ROUTING_URL", "http://service-routing:8005")
CHATBOT_URL = os.getenv("CHATBOT_URL", "http://service-chatbot:8001")
REDIS_HOST  = os.getenv("REDIS_HOST", "redis")
REDIS_PORT  = int(os.getenv("REDIS_PORT", "6379"))

router = APIRouter(prefix="/api/v1/admin", tags=["admin"])


async def require_admin(user_id: str = Depends(auth.get_current_user_id)) -> str:
    """Dependency: raises 403 if the logged-in user is not an admin."""
    async with db.pool().acquire() as conn:
        is_admin = await conn.fetchval("SELECT is_admin FROM users WHERE id=$1::uuid", user_id)
    if not is_admin:
        raise HTTPException(403, "Admin access required")
    return user_id

_http: Optional[httpx.AsyncClient] = None
_redis = None


def set_http_client(client: httpx.AsyncClient):
    global _http
    _http = client


async def _get_redis():
    global _redis
    if _redis is None:
        import redis.asyncio as redis_async
        _redis = redis_async.Redis(host=REDIS_HOST, port=REDIS_PORT, decode_responses=True)
    return _redis


# ── Pydantic models for write endpoints ────────────────────────────────

class ReviewPayload(BaseModel):
    classification_correct: Optional[bool] = None
    correct_department: Optional[str] = None
    correct_sub_category: Optional[str] = None
    correct_priority: Optional[str] = None
    sentiment_correct: Optional[bool] = None
    reviewer_notes: Optional[str] = None
    rating: str  # "positive" | "negative"


class StatusPayload(BaseModel):
    status: str  # "resolved" | "rejected" | "in_progress" | "pending"


# ── Stats ─────────────────────────────────────────────────────────────

@router.get("/stats")
async def stats(_uid: str = Depends(require_admin)):
    async with db.pool().acquire() as conn:
        total = await conn.fetchval("SELECT COUNT(*) FROM complaints")
        by_status = await conn.fetch(
            "SELECT status, COUNT(*) AS n FROM complaints GROUP BY status ORDER BY n DESC"
        )
        by_dept = await conn.fetch(
            "SELECT department, COUNT(*) AS n FROM complaints "
            "WHERE department IS NOT NULL GROUP BY department ORDER BY n DESC LIMIT 8"
        )
        by_district = await conn.fetch(
            "SELECT district, COUNT(*) AS n FROM complaints "
            "WHERE district IS NOT NULL GROUP BY district ORDER BY n DESC LIMIT 8"
        )
        recent = await conn.fetch(
            "SELECT complaint_id, summary, status, department, created_at "
            "FROM complaints ORDER BY created_at DESC LIMIT 10"
        )
        duplicate_total = await conn.fetchval(
            "SELECT COUNT(*) FROM complaints "
            "WHERE (pipeline_data->'dedup'->>'is_duplicate')::boolean = true"
        )

    return {
        "total_complaints": total,
        "duplicate_complaints": duplicate_total or 0,
        "by_status":   [{"status": r["status"], "count": r["n"]} for r in by_status],
        "by_department": [{"department": r["department"], "count": r["n"]} for r in by_dept],
        "by_district": [{"district": r["district"], "count": r["n"]} for r in by_district],
        "recent": [
            {
                "complaint_id": str(r["complaint_id"]),
                "summary": r["summary"],
                "status": r["status"],
                "department": r["department"],
                "created_at": int(r["created_at"].timestamp() * 1000),
            }
            for r in recent
        ],
    }


# ── Portals ────────────────────────────────────────────────────────────

@router.get("/portals")
async def admin_portals(_uid: str = Depends(require_admin)):
    # Complaint counts from Postgres.
    async with db.pool().acquire() as conn:
        counts_rows = await conn.fetch(
            "SELECT portal_id, COUNT(*) AS n FROM complaints "
            "WHERE portal_id IS NOT NULL GROUP BY portal_id"
        )
    counts = {r["portal_id"]: r["n"] for r in counts_rows}

    # Portal metadata from service-routing.
    portals_meta = []
    try:
        resp = await _http.get(f"{ROUTING_URL}/api/v1/portals", timeout=5.0)
        portals_meta = resp.json()
    except Exception as e:
        logger.warning("Could not fetch portals from routing: %s", e)

    # Merge.
    result = []
    for p in portals_meta:
        pid = p["portal_id"]
        result.append({**p, "complaint_count": counts.get(pid, 0)})

    # Also include portals that have complaints but no metadata (shouldn't happen).
    known_ids = {p["portal_id"] for p in portals_meta}
    for pid, n in counts.items():
        if pid not in known_ids:
            result.append({"portal_id": pid, "portal_name": pid, "complaint_count": n})

    result.sort(key=lambda x: x["complaint_count"], reverse=True)
    return result


@router.get("/portals/{portal_id}")
async def admin_portal_detail(portal_id: str, limit: int = Query(50, le=200), _uid: str = Depends(require_admin)):
    # Portal metadata.
    portal_meta = {}
    try:
        resp = await _http.get(f"{ROUTING_URL}/api/v1/portals/{portal_id}", timeout=5.0)
        portal_meta = resp.json() if resp.status_code == 200 else {}
    except Exception:
        pass

    # Complaints routed to this portal.
    async with db.pool().acquire() as conn:
        rows = await conn.fetch(
            """
            SELECT c.complaint_id, c.summary, c.status, c.department, c.sub_category,
                   c.district, c.ticket_id, c.created_at, c.updated_at,
                   c.pipeline_data,
                   u.name AS user_name, u.mobile AS user_mobile
            FROM complaints c
            JOIN users u ON c.user_id = u.id
            WHERE c.portal_id = $1
            ORDER BY c.created_at DESC
            LIMIT $2
            """,
            portal_id, limit,
        )

    complaints = []
    for r in rows:
        pd = r["pipeline_data"] or {}
        classification = pd.get("classification", {})
        dedup = pd.get("dedup", {})
        complaints.append({
            "complaint_id":  str(r["complaint_id"]),
            "summary":       r["summary"],
            "status":        r["status"],
            "department":    r["department"],
            "sub_category":  r["sub_category"],
            "district":      r["district"],
            "ticket_id":     r["ticket_id"],
            "user_name":     r["user_name"],
            "user_mobile":   r["user_mobile"][-4:].rjust(10, "*") if r["user_mobile"] else "",
            "priority":      classification.get("priority"),
            "sentiment":     classification.get("sentiment"),
            "is_duplicate":  bool(dedup.get("is_duplicate")),
            "duplicate_count": dedup.get("duplicate_count", 0),
            "created_at":    int(r["created_at"].timestamp() * 1000),
            "updated_at":    int(r["updated_at"].timestamp() * 1000),
        })

    return {"portal": portal_meta, "complaints": complaints, "total": len(complaints)}


# ── Complaints ─────────────────────────────────────────────────────────

@router.get("/complaints")
async def admin_complaints(
    _uid: str = Depends(require_admin),
    status: Optional[str] = None,
    department: Optional[str] = None,
    district: Optional[str] = None,
    limit: int = Query(50, le=200),
    offset: int = 0,
):
    filters = ["1=1"]
    params: list = []
    i = 1
    if status:
        filters.append(f"c.status = ${i}"); params.append(status); i += 1
    if department:
        filters.append(f"c.department = ${i}"); params.append(department); i += 1
    if district:
        filters.append(f"c.district = ${i}"); params.append(district); i += 1

    where = " AND ".join(filters)
    params += [limit, offset]

    async with db.pool().acquire() as conn:
        rows = await conn.fetch(
            f"""
            SELECT c.complaint_id, c.summary, c.status, c.department, c.sub_category,
                   c.district, c.portal_id, c.ticket_id, c.created_at,
                   u.name AS user_name
            FROM complaints c
            JOIN users u ON c.user_id = u.id
            WHERE {where}
            ORDER BY c.created_at DESC
            LIMIT ${i} OFFSET ${i+1}
            """,
            *params,
        )
        total = await conn.fetchval(
            f"SELECT COUNT(*) FROM complaints c JOIN users u ON c.user_id = u.id WHERE {where}",
            *params[:-2],
        )

    return {
        "complaints": [
            {
                "complaint_id": str(r["complaint_id"]),
                "summary":      r["summary"],
                "status":       r["status"],
                "department":   r["department"],
                "sub_category": r["sub_category"],
                "district":     r["district"],
                "portal_id":    r["portal_id"],
                "ticket_id":    r["ticket_id"],
                "user_name":    r["user_name"],
                "created_at":   int(r["created_at"].timestamp() * 1000),
            }
            for r in rows
        ],
        "total": total,
        "limit": limit,
        "offset": offset,
    }


@router.get("/complaints/{complaint_id}")
async def admin_complaint_detail(complaint_id: str, _uid: str = Depends(require_admin)):
    async with db.pool().acquire() as conn:
        row = await conn.fetchrow(
            """
            SELECT c.*, u.name AS user_name, u.mobile AS user_mobile,
                   u.email AS user_email, u.district AS user_district
            FROM complaints c
            JOIN users u ON c.user_id = u.id
            WHERE c.complaint_id = $1
            """,
            complaint_id,
        )
    if not row:
        from fastapi import HTTPException
        raise HTTPException(404, "Complaint not found")

    pd = row["pipeline_data"] or {}

    # Routing explanation: why this portal was chosen.
    routing = pd.get("routing", {})
    routing_explanation = None
    if routing:
        routing_explanation = {
            "portal_id":    routing.get("portal_id"),
            "portal_name":  routing.get("portal_name"),
            "level":        routing.get("jurisdiction_level"),
            "reason":       f"Department '{row['department']}' in district '{row['district']}' matched {routing.get('portal_name')} at {routing.get('jurisdiction_level')} level.",
        }

    # Duplicate filers.
    dedup = pd.get("dedup", {})
    duplicate_filers = dedup.get("duplicate_details", [])

    # Audit chain.
    chain = await get_chain(complaint_id)

    raw_mobile = row["user_mobile"] or ""
    masked = ("*" * (len(raw_mobile) - 4) + raw_mobile[-4:]) if len(raw_mobile) >= 4 else "****"

    return {
        "complaint_id":   str(row["complaint_id"]),
        "summary":        row["summary"],
        "status":         row["status"],
        "department":     row["department"],
        "sub_category":   row["sub_category"],
        "district":       row["district"],
        "portal_id":      row["portal_id"],
        "ticket_id":      row["ticket_id"],
        "created_at":     int(row["created_at"].timestamp() * 1000),
        "updated_at":     int(row["updated_at"].timestamp() * 1000),
        "filer": {
            "name":     row["user_name"],
            "mobile":   masked,
            "email":    row["user_email"],
            "district": row["user_district"],
        },
        "pipeline": {
            "location":       pd.get("location"),
            "nlu":            pd.get("nlu"),
            "classification": pd.get("classification"),
            "routing":        pd.get("routing"),
            "portal_fields":  pd.get("portal_fields"),
            "submission":     pd.get("submission"),
        },
        "routing_explanation": routing_explanation,
        "dedup": {
            "is_duplicate":    bool(dedup.get("is_duplicate")),
            "is_same_user":    bool(dedup.get("is_same_user")),
            "duplicate_count": dedup.get("duplicate_count", 0),
            "duplicate_filers": duplicate_filers,
        },
        "audit_chain": chain,
    }


# ── Review endpoint ─────────────────────────────────────────────────────

@router.post("/complaints/{complaint_id}/review")
async def submit_review(complaint_id: str, payload: ReviewPayload, _uid: str = Depends(require_admin)):
    """Store reviewer feedback on AI classification in DB and Redis cache."""
    if payload.rating not in ("positive", "negative"):
        raise HTTPException(400, "rating must be 'positive' or 'negative'")

    async with db.pool().acquire() as conn:
        # Verify complaint exists
        exists = await conn.fetchval(
            "SELECT complaint_id FROM complaints WHERE complaint_id = $1",
            complaint_id,
        )
        if not exists:
            raise HTTPException(404, "Complaint not found")

        review_id = await conn.fetchval(
            """
            INSERT INTO complaint_reviews (
                complaint_id, classification_correct, correct_department,
                correct_sub_category, correct_priority, sentiment_correct,
                reviewer_notes, rating
            ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
            RETURNING id
            """,
            complaint_id,
            payload.classification_correct,
            payload.correct_department,
            payload.correct_sub_category,
            payload.correct_priority,
            payload.sentiment_correct,
            payload.reviewer_notes,
            payload.rating,
        )

    # Cache in Redis for quick access
    try:
        r = await _get_redis()
        review_data = {
            "id": str(review_id),
            "complaint_id": complaint_id,
            "rating": payload.rating,
            "classification_correct": payload.classification_correct,
            "correct_department": payload.correct_department,
            "correct_sub_category": payload.correct_sub_category,
            "correct_priority": payload.correct_priority,
            "sentiment_correct": payload.sentiment_correct,
            "reviewer_notes": payload.reviewer_notes,
        }
        await r.setex(f"review:{complaint_id}", 86400, json.dumps(review_data))
    except Exception as exc:
        logger.warning("Redis cache for review failed: %s", exc)

    return {"status": "ok", "review_id": str(review_id)}


# ── Status update endpoint ──────────────────────────────────────────────

_STATUS_MESSAGES = {
    "resolved": (
        "Aapki shikayat (ID: {ticket_id}) resolve ho gayi. "
        "Kya aapki samasya solve hui? Reply 1 for Yes, 2 for No"
    ),
    "rejected": (
        "Aapki shikayat review ke baad reject ho gayi. "
        "Reason: {status}. Naya complaint darne ke liye 'new' type karein."
    ),
    "in_progress": (
        "Aapki shikayat par kaam chal raha hai. Hum jald update denge."
    ),
    "pending": (
        "Aapki shikayat pending status mein hai. Hum jald review karenge."
    ),
}


@router.post("/complaints/{complaint_id}/status")
async def update_status(complaint_id: str, payload: StatusPayload, _uid: str = Depends(require_admin)):
    """Update complaint status in DB and notify the user via chatbot."""
    valid_statuses = {"resolved", "rejected", "in_progress", "pending"}
    if payload.status not in valid_statuses:
        raise HTTPException(400, f"status must be one of: {', '.join(valid_statuses)}")

    async with db.pool().acquire() as conn:
        row = await conn.fetchrow(
            """
            UPDATE complaints SET status = $1, updated_at = NOW()
            WHERE complaint_id = $2
            RETURNING complaint_id, user_id, ticket_id, status
            """,
            payload.status,
            complaint_id,
        )
        if not row:
            raise HTTPException(404, "Complaint not found")

        user_id = str(row["user_id"])
        ticket_id = row["ticket_id"] or complaint_id

    # Publish Redis event for WebSocket notification
    try:
        r = await _get_redis()
        event = json.dumps({
            "type": "status_update",
            "complaint_id": complaint_id,
            "status": payload.status,
            "ticket_id": ticket_id,
        })
        await r.publish(f"pipeline:{complaint_id}", event)
        await r.publish("pipeline:all", event)
    except Exception as exc:
        logger.warning("Redis publish for status update failed: %s", exc)

    # Notify user via chatbot pending_notification
    notification_template = _STATUS_MESSAGES.get(payload.status, _STATUS_MESSAGES["pending"])
    notification = notification_template.format(ticket_id=ticket_id, status=payload.status)

    try:
        resp = await _http.post(
            f"{CHATBOT_URL}/api/v1/session/notify",
            json={"user_id": user_id, "message": notification},
            timeout=5.0,
        )
        if resp.status_code not in (200, 404):
            logger.warning("Chatbot notify returned %d", resp.status_code)
    except Exception as exc:
        # Non-fatal: status was already updated in DB
        logger.warning("Could not notify user via chatbot: %s", exc)

    return {"status": "ok", "complaint_id": complaint_id, "new_status": payload.status}
