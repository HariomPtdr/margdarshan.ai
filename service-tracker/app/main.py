"""service-tracker — Stage 10 status polling + citizen notification.

Polling frequency (per spec 13.1):
  - Every 1 hour for the first day
  - Every 6 hours for the first week
  - Daily after that
  - Stops on terminal states (RESOLVED, REJECTED)

On status change: publishes stage_10_status event + mock WhatsApp notification.
On RESOLVED: queues citizen feedback ask in Redis.
"""

import asyncio
import json
import logging
import os
from datetime import datetime, timedelta, timezone
from typing import Optional

import asyncpg
import httpx
import redis.asyncio as redis_async
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from grievance_schema import PipelineEvent, StageEnum

from .whatsapp import WhatsAppClient

_wa = WhatsAppClient()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

REDIS_HOST     = os.getenv("REDIS_HOST",     "redis")
REDIS_PORT     = int(os.getenv("REDIS_PORT", "6379"))
POSTGRES_HOST  = os.getenv("POSTGRES_HOST",  "postgres")
POSTGRES_PORT  = int(os.getenv("POSTGRES_PORT", "5432"))
POSTGRES_USER  = os.getenv("POSTGRES_USER",  "grievance")
POSTGRES_PASS  = os.getenv("POSTGRES_PASSWORD", "changeme")
POSTGRES_DB    = os.getenv("POSTGRES_DB",    "grievance")
SUBMISSION_URL = os.getenv("SUBMISSION_URL", "http://service-submission:8006")

app = FastAPI(title="service-tracker", version="2.0.0")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

_redis: Optional[redis_async.Redis] = None
_pool:  Optional[asyncpg.Pool]      = None
_http:  Optional[httpx.AsyncClient] = None

# ── Status normalizer ─────────────────────────────────────────────────

_STATUS_MAP: dict[str, str] = {
    "submitted":             "PENDING",
    "registered":            "PENDING",
    "received":              "PENDING",
    "under review":          "IN_PROGRESS",
    "in progress":           "IN_PROGRESS",
    "forwarded to ministry": "IN_PROGRESS",
    "assigned to officer":   "IN_PROGRESS",
    "officer assigned":      "IN_PROGRESS",
    "awaiting response":     "AWAITING_USER",
    "टिप्पणी प्रतीक्षित":      "AWAITING_USER",
    "resolved":              "RESOLVED",
    "closed":                "RESOLVED",
    "disposed":              "RESOLVED",
    "rejected":              "REJECTED",
    "closed no action":      "REJECTED",
}

_TERMINAL = {"resolved", "rejected"}


def normalize_status(raw: str) -> str:
    return _STATUS_MAP.get(raw.lower().strip(), "IN_PROGRESS")


def poll_interval_seconds(submitted_at: datetime) -> int:
    age = datetime.now(timezone.utc) - submitted_at.replace(tzinfo=timezone.utc)
    if age < timedelta(days=1):
        return 3600
    if age < timedelta(days=7):
        return 21600
    return 86400


# ── Lifecycle ─────────────────────────────────────────────────────────

@app.on_event("startup")
async def startup():
    global _redis, _pool, _http
    _redis = redis_async.Redis(host=REDIS_HOST, port=REDIS_PORT, decode_responses=True)
    _pool  = await asyncpg.create_pool(
        host=POSTGRES_HOST, port=POSTGRES_PORT,
        user=POSTGRES_USER, password=POSTGRES_PASS,
        database=POSTGRES_DB, min_size=1, max_size=5,
    )
    _http = httpx.AsyncClient(timeout=15.0)
    asyncio.create_task(_bootstrap_polling())
    logger.info("Tracker started")


@app.on_event("shutdown")
async def shutdown():
    if _http:  await _http.aclose()
    if _pool:  await _pool.close()
    if _redis: await _redis.close()


@app.get("/healthz")
async def healthz():
    return {"status": "ok", "service": "tracker"}


# ── Manual poll (for admin / testing) ────────────────────────────────

class PollRequest(BaseModel):
    complaint_id: str
    portal_id: str
    ticket_id: str


@app.post("/api/v1/poll")
async def poll_now(req: PollRequest):
    terminal = await _poll_ticket(req.complaint_id, req.portal_id, req.ticket_id)
    return {"status": "polled", "terminal": terminal}


# ── Bootstrap ─────────────────────────────────────────────────────────

async def _bootstrap_polling():
    await asyncio.sleep(5)
    async with _pool.acquire() as conn:
        rows = await conn.fetch(
            """
            SELECT complaint_id, portal_id, ticket_id, created_at
            FROM complaints
            WHERE ticket_id IS NOT NULL
              AND status NOT IN ('resolved', 'rejected', 'failed')
            """
        )
    logger.info("Bootstrap: scheduling %d open tickets for polling", len(rows))
    for row in rows:
        asyncio.create_task(_poll_loop(
            str(row["complaint_id"]),
            row["portal_id"] or "P001",
            row["ticket_id"],
            row["created_at"],
        ))


# Also listen for new submissions via Redis so we start polling immediately.
@app.on_event("startup")
async def _start_submission_listener():
    asyncio.create_task(_submission_listener())


async def _submission_listener():
    pubsub = _redis.pubsub()
    await pubsub.subscribe("pipeline:all")
    async for msg in pubsub.listen():
        if msg["type"] != "message":
            continue
        try:
            evt = json.loads(msg["data"])
        except Exception:
            continue
        if evt.get("stage") == "stage_8_submit" and evt.get("status") == "completed":
            payload = evt.get("payload", {})
            cid       = evt.get("complaint_id")
            portal_id = payload.get("portal_id", "P001")
            ticket_id = payload.get("portal_ticket_id")
            if cid and ticket_id:
                asyncio.create_task(_poll_loop(cid, portal_id, ticket_id, datetime.utcnow()))
                logger.info("Tracker: started polling for new ticket %s", ticket_id)


# ── Poll loop ─────────────────────────────────────────────────────────

async def _poll_loop(complaint_id: str, portal_id: str, ticket_id: str, submitted_at: datetime):
    while True:
        await asyncio.sleep(poll_interval_seconds(submitted_at))
        terminal = await _poll_ticket(complaint_id, portal_id, ticket_id)
        if terminal:
            return


async def _poll_ticket(complaint_id: str, portal_id: str, ticket_id: str) -> bool:
    try:
        resp = await _http.post(
            f"{SUBMISSION_URL}/api/v1/status",
            json={"portal_id": portal_id, "ticket_id": ticket_id},
            timeout=10.0,
        )
        data = resp.json()
    except Exception as e:
        logger.warning("status fetch failed for %s: %s", ticket_id, e)
        return False

    raw_status = data.get("portal_status_raw", "")
    canonical  = normalize_status(raw_status)

    async with _pool.acquire() as conn:
        stored = await conn.fetchval(
            "SELECT status FROM complaints WHERE complaint_id = $1", complaint_id
        )

    if canonical.lower() == (stored or "").lower():
        return canonical.lower() in _TERMINAL

    # Status changed.
    async with _pool.acquire() as conn:
        await conn.execute(
            "UPDATE complaints SET status = $2, updated_at = NOW() WHERE complaint_id = $1",
            complaint_id, canonical.lower(),
        )

    event = PipelineEvent(
        complaint_id=complaint_id,
        stage=StageEnum.STAGE_10_STATUS,
        status="completed",
        payload={
            "ticket_id":         ticket_id,
            "portal_status_raw": raw_status,
            "canonical_status":  canonical,
            "changed_from":      stored,
        },
    )
    await _redis.publish(f"pipeline:{complaint_id}", event.model_dump_json())
    await _redis.publish("pipeline:all", event.model_dump_json())
    logger.info("ticket %s: %s → %s", ticket_id, stored, canonical)

    await _notify_citizen(complaint_id, canonical, ticket_id)

    if canonical == "RESOLVED":
        await _redis.lpush(
            "feedback_queue",
            json.dumps({
                "complaint_id": complaint_id,
                "ticket_id":    ticket_id,
                "at":           datetime.utcnow().isoformat(),
            }),
        )

    return canonical.lower() in _TERMINAL


# ── Citizen notification (mock Twilio WhatsApp) ────────────────────────

_NOTIFY_MSGS: dict[str, tuple[str, str]] = {
    "PENDING": (
        "Aapki shikayat #{t} portal par register ho gayi. Hum update dete rahenge.",
        "Your complaint #{t} is registered. We will keep you updated.",
    ),
    "IN_PROGRESS": (
        "Aapki shikayat #{t} review ho rahi hai. Officer jald assign hoga.",
        "Complaint #{t} is under review. An officer will be assigned shortly.",
    ),
    "AWAITING_USER": (
        "Shikayat #{t} ke liye aur jankari chahiye. Kripya portal par jawab dein.",
        "More info needed for complaint #{t}. Please respond on the portal.",
    ),
    "RESOLVED": (
        "Shikayat #{t} resolve ho gayi! Kya aap santusht hain? Reply 1 (haan) ya 2 (nahi).",
        "Complaint #{t} resolved! Are you satisfied? Reply 1 (Yes) or 2 (No).",
    ),
    "REJECTED": (
        "Shikayat #{t} reject hui. Agar galat laga toh reply karein — hum escalate karenge.",
        "Complaint #{t} was rejected. Reply if you'd like to escalate.",
    ),
}


async def _notify_citizen(complaint_id: str, canonical: str, ticket_id: str):
    msgs = _NOTIFY_MSGS.get(canonical)
    if not msgs:
        return
    try:
        async with _pool.acquire() as conn:
            row = await conn.fetchrow(
                "SELECT u.mobile, u.name FROM complaints c "
                "JOIN users u ON c.user_id = u.id WHERE c.complaint_id = $1",
                complaint_id,
            )
        if not row:
            return
        body_hi = msgs[0].replace("{t}", ticket_id[:12])
        body_en = msgs[1].replace("{t}", ticket_id[:12])
        msg = f"{body_hi}\n\n{body_en}"
        await _wa.send(to=row["mobile"], body=msg)
    except Exception as e:
        logger.warning("notify_citizen failed: %s", e)
