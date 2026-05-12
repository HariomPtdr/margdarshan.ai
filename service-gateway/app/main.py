"""service-gateway — single public API + WebSocket bridge.

Frontend talks ONLY to the gateway. The gateway proxies to internal services,
owns auth (users in Postgres), and persists complaint history.
"""

import asyncio
import json
import logging
import os
from datetime import datetime, timedelta
from typing import Optional

import httpx
import redis.asyncio as redis_async
from fastapi import Depends, FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, EmailStr, Field

from . import auth, db
from .admin import router as admin_router, set_http_client as admin_set_http
from .webhooks import router as webhooks_router
from .audit import log_event
from .embedder import embed, is_duplicate as sbert_is_duplicate, cosine_similarity, SIMILARITY_THRESHOLD

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Service endpoints (internal docker network)
CHATBOT_URL = os.getenv("CHATBOT_URL", "http://service-chatbot:8001")
LOCATION_URL = os.getenv("LOCATION_URL", "http://service-location:8002")
NLU_URL = os.getenv("NLU_URL", "http://service-nlu:8003")
CLASSIFIER_URL = os.getenv("CLASSIFIER_URL", "http://service-classifier:8004")
ROUTING_URL = os.getenv("ROUTING_URL", "http://service-routing:8005")
SUBMISSION_URL = os.getenv("SUBMISSION_URL", "http://service-submission:8006")
TRACKER_URL = os.getenv("TRACKER_URL", "http://service-tracker:8007")

REDIS_HOST = os.getenv("REDIS_HOST", "redis")
REDIS_PORT = int(os.getenv("REDIS_PORT", "6379"))

app = FastAPI(title="service-gateway", version="2.0.0")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])
app.include_router(admin_router)
app.include_router(webhooks_router)


# ── Demo Trace endpoint — shows full API exchange for a complaint ─────────────

@app.get("/api/v1/demo/trace/{complaint_id}")
async def demo_trace(complaint_id: str, _uid: str = Depends(auth.get_current_user_id)):
    """Returns the full plug-and-play API trace for demo purposes.
    Shows: what was sent to portal, what came back, status updates, adapter used.
    """
    async with db.pool().acquire() as conn:
        row = await conn.fetchrow(
            "SELECT complaint_id, department, portal_id, ticket_id, status, pipeline_data "
            "FROM complaints WHERE complaint_id = $1",
            complaint_id,
        )
    if not row:
        raise HTTPException(404, "Complaint not found")

    pd = row["pipeline_data"] or {}
    portal_id   = row["portal_id"] or ""
    portal_fields = pd.get("portal_fields", {})
    submission  = pd.get("submission", {})
    routing     = pd.get("routing", {})
    clf         = pd.get("classification", {})
    loc         = pd.get("location", {})

    # Determine adapter name
    adapter_map = {
        "P001": "CPGRAMSAdapter",
        "P002": "CPGRAMSAdapter",
        "P031": "MPCM181Adapter",
        "P062": "MPPKVVCLAdapter",
        "P065": "MPPKVVCLAdapter",
    }
    adapter_name = adapter_map.get(portal_id, "GenericMockAdapter")

    return {
        "complaint_id": complaint_id,
        "adapter_used": adapter_name,

        # STEP 1: What our classifier decided
        "step_1_classification": {
            "label":       "Layer 4 — Classifier",
            "department":  clf.get("department", ""),
            "sub_category":clf.get("sub_category", ""),
            "priority":    clf.get("priority", ""),
            "confidence":  clf.get("confidence", 0),
        },

        # STEP 2: What routing found
        "step_2_routing": {
            "label":          "Layer 5 — Portal Routing",
            "portal_id":      routing.get("portal_id", ""),
            "portal_name":    routing.get("portal_name", ""),
            "portal_level":   routing.get("jurisdiction_level", ""),
            "portal_website": routing.get("portal_website", ""),
            "reason":         f"Best match for {clf.get('department','')} in {loc.get('district','')}",
        },

        # STEP 3: What we SENT to the portal (the API request)
        "step_3_api_request": {
            "label":    "Layer 7 — What we sent to portal",
            "method":   "POST",
            "url":      f"{routing.get('portal_website', 'https://portal.gov.in')}/api/grievance/register",
            "headers":  {"Authorization": "Bearer [API_KEY]", "Content-Type": "application/json"},
            "body":     portal_fields,
        },

        # STEP 4: What the portal sent back
        "step_4_api_response": {
            "label":     "Portal Response",
            "ticket_id": row["ticket_id"] or "",
            "status":    submission.get("portal_status_raw", ""),
            "portal_url":submission.get("portal_url", ""),
        },

        # STEP 5: Current status
        "step_5_current_status": {
            "label":        "Current Status",
            "our_status":   row["status"],
            "ticket":       row["ticket_id"] or "",
            "next_poll":    "Tracker polls every 1h for status updates",
        },

        "audit_chain": await _get_audit_events(complaint_id),
    }


async def _get_audit_events(complaint_id: str) -> list:
    try:
        async with db.pool().acquire() as conn:
            rows = await conn.fetch(
                "SELECT event_type, details, created_at FROM complaint_events "
                "WHERE complaint_id=$1 ORDER BY created_at ASC LIMIT 20",
                complaint_id,
            )
        return [{"event": r["event_type"], "at": r["created_at"].strftime("%H:%M:%S"), "details": r["details"]} for r in rows]
    except Exception:
        return []

_http: Optional[httpx.AsyncClient] = None
_redis: Optional[redis_async.Redis] = None


@app.on_event("startup")
async def startup():
    global _http, _redis
    _http = httpx.AsyncClient(timeout=15.0)
    _redis = redis_async.Redis(host=REDIS_HOST, port=REDIS_PORT, decode_responses=True)
    await db.connect()
    admin_set_http(_http)
    asyncio.create_task(_orchestrator_loop())
    asyncio.create_task(_persistence_loop())
    asyncio.create_task(_feedback_loop())
    await _seed_admin()
    logger.info("Gateway started — orchestrator + persistence + feedback loops running")


async def _seed_admin():
    """Create admin user from env vars if it doesn't exist yet."""
    admin_email = os.getenv("ADMIN_EMAIL", "").strip()
    admin_password = os.getenv("ADMIN_PASSWORD", "").strip()
    admin_mobile = os.getenv("ADMIN_MOBILE", "9000000000").strip()
    if not admin_email or not admin_password:
        return
    async with db.pool().acquire() as conn:
        existing = await conn.fetchrow("SELECT id, is_admin FROM users WHERE email=$1", admin_email)
        if existing:
            if not existing["is_admin"]:
                await conn.execute("UPDATE users SET is_admin=true WHERE email=$1", admin_email)
                logger.info("Promoted existing user %s to admin", admin_email)
        else:
            pwd_hash = auth.hash_password(admin_password)
            try:
                await conn.execute(
                    "INSERT INTO users (name, email, mobile, password_hash, is_admin) "
                    "VALUES ($1,$2,$3,$4,true) ON CONFLICT (mobile) DO NOTHING",
                    "Admin", admin_email, admin_mobile, pwd_hash,
                )
                logger.info("Admin account ensured: %s", admin_email)
            except Exception as e:
                logger.warning("admin seed skipped: %s", e)


@app.on_event("shutdown")
async def shutdown():
    if _http:
        await _http.aclose()
    if _redis:
        await _redis.close()
    await db.close()


@app.get("/healthz")
async def healthz():
    return {"status": "ok", "service": "gateway"}


# ── Auth ─────────────────────────────────────────────────────────────────

class RegisterRequest(BaseModel):
    name: str = Field(..., min_length=1)
    gender: Optional[str] = None
    email: EmailStr
    mobile: str = Field(..., min_length=10)
    phone: Optional[str] = None
    password: str = Field(..., min_length=6)
    address: Optional[str] = None
    sub_locality: Optional[str] = None
    locality: Optional[str] = None
    state: Optional[str] = None
    district: Optional[str] = None
    pincode: Optional[str] = None
    country: Optional[str] = "India"


class LoginRequest(BaseModel):
    identifier: str  # email, mobile, or username
    password: str


def _user_to_dict(row) -> dict:
    return {
        "id": str(row["id"]),
        "name": row["name"],
        "gender": row["gender"],
        "email": row["email"],
        "mobile": row["mobile"],
        "phone": row["phone"],
        "address": row["address"],
        "sub_locality": row["sub_locality"],
        "locality": row["locality"],
        "state": row["state"],
        "district": row["district"],
        "pincode": row["pincode"],
        "country": row["country"],
    }


@app.post("/api/v1/auth/register")
async def register(req: RegisterRequest):
    pw_hash = auth.hash_password(req.password)
    try:
        async with db.pool().acquire() as conn:
            row = await conn.fetchrow(
                """
                INSERT INTO users (name, gender, email, mobile, phone, password_hash,
                                   address, sub_locality, locality, state, district, pincode, country)
                VALUES ($1,$2,$3,$4,$5,$6,$7,$8,$9,$10,$11,$12,$13)
                RETURNING *
                """,
                req.name, req.gender, req.email.lower(), req.mobile, req.phone, pw_hash,
                req.address, req.sub_locality, req.locality, req.state, req.district,
                req.pincode, req.country or "India",
            )
    except Exception as e:
        msg = str(e).lower()
        if "users_email_key" in msg:
            raise HTTPException(409, "Email already registered")
        if "users_mobile_key" in msg:
            raise HTTPException(409, "Mobile already registered")
        logger.error(f"register failed: {e}")
        raise HTTPException(500, "Registration failed")

    user = _user_to_dict(row)
    token = auth.issue_token(user["id"])
    return {"token": token, "user": user}


@app.post("/api/v1/auth/login")
async def login(req: LoginRequest):
    ident = req.identifier.strip()
    async with db.pool().acquire() as conn:
        row = await conn.fetchrow(
            "SELECT * FROM users WHERE email = $1 OR mobile = $1 LIMIT 1",
            ident.lower() if "@" in ident else ident,
        )
    if not row or not auth.verify_password(req.password, row["password_hash"]):
        raise HTTPException(401, "Invalid credentials")

    user = _user_to_dict(row)
    token = auth.issue_token(user["id"])
    return {"token": token, "user": user}


@app.get("/api/v1/auth/me")
async def me(user_id: str = Depends(auth.get_current_user_id)):
    async with db.pool().acquire() as conn:
        row = await conn.fetchrow("SELECT * FROM users WHERE id = $1", user_id)
    if not row:
        raise HTTPException(404, "User not found")
    return _user_to_dict(row)


# ── Complaints (history) ─────────────────────────────────────────────────

@app.get("/api/v1/complaints")
async def list_complaints(user_id: str = Depends(auth.get_current_user_id)):
    async with db.pool().acquire() as conn:
        rows = await conn.fetch(
            """
            SELECT complaint_id, summary, intent, state, department, ticket_id,
                   status, created_at, updated_at
            FROM complaints WHERE user_id = $1
            ORDER BY created_at DESC LIMIT 50
            """,
            user_id,
        )
    return [
        {
            "complaint_id": str(r["complaint_id"]),
            "summary": r["summary"],
            "intent": r["intent"],
            "state": r["state"],
            "department": r["department"],
            "ticket_id": r["ticket_id"],
            "status": r["status"],
            "created_at": int(r["created_at"].timestamp() * 1000),
            "updated_at": int(r["updated_at"].timestamp() * 1000),
        }
        for r in rows
    ]


@app.get("/api/v1/complaints/{complaint_id}/messages")
async def get_complaint_messages(complaint_id: str, user_id: str = Depends(auth.get_current_user_id)):
    async with db.pool().acquire() as conn:
        owner = await conn.fetchval(
            "SELECT user_id FROM complaints WHERE complaint_id = $1", complaint_id
        )
        if owner is None:
            raise HTTPException(404, "Complaint not found")
        if str(owner) != user_id:
            raise HTTPException(403, "Forbidden")
        rows = await conn.fetch(
            "SELECT role, content, created_at, session_id FROM messages "
            "WHERE complaint_id = $1 ORDER BY seq ASC",
            complaint_id,
        )
    return [
        {
            "role": r["role"],
            "content": r["content"],
            "timestamp": int(r["created_at"].timestamp() * 1000),
        }
        for r in rows
    ]


@app.get("/api/v1/complaints/{complaint_id}")
async def get_complaint(complaint_id: str, user_id: str = Depends(auth.get_current_user_id)):
    async with db.pool().acquire() as conn:
        row = await conn.fetchrow(
            "SELECT * FROM complaints WHERE complaint_id = $1 AND user_id = $2",
            complaint_id, user_id,
        )
    if not row:
        raise HTTPException(404, "Complaint not found")
    _pd_r = row["pipeline_data"] or {}
    pd = json.loads(_pd_r) if isinstance(_pd_r, str) else _pd_r
    return {
        "complaint_id": str(row["complaint_id"]),
        "summary": row["summary"],
        "intent": row["intent"],
        "state": row["state"],
        "department": row["department"],
        "ticket_id": row["ticket_id"],
        "status": row["status"],
        "pipeline_data": pd,
        "created_at": int(row["created_at"].timestamp() * 1000),
        "updated_at": int(row["updated_at"].timestamp() * 1000),
    }


# ── Proxied endpoints ────────────────────────────────────────────────────

class ChatRequest(BaseModel):
    message: str
    session_id: Optional[str] = None
    language_preference: Optional[str] = "hinglish"


@app.post("/api/v1/chat")
async def proxy_chat(body: ChatRequest, user_id: str = Depends(auth.get_current_user_id)):
    payload = {
        "user_id": user_id,
        "session_id": body.session_id,
        "message": body.message,
        "language_preference": body.language_preference,
    }
    r = await _http.post(f"{CHATBOT_URL}/api/v1/chat", json=payload)
    resp = r.json()

    cid = resp.get("complaint_id")
    session_id = resp.get("session_id") or body.session_id or ""

    async with db.pool().acquire() as conn:
        async with conn.transaction():
            # Upsert complaint row when a complaint id is present.
            if cid:
                await conn.execute(
                    """
                    INSERT INTO complaints (complaint_id, user_id, summary, intent, state)
                    VALUES ($1, $2, $3, $4, $5)
                    ON CONFLICT (complaint_id) DO UPDATE
                    SET intent = COALESCE(EXCLUDED.intent, complaints.intent),
                        state = COALESCE(EXCLUDED.state, complaints.state),
                        updated_at = NOW()
                    """,
                    cid, user_id, body.message[:200], resp.get("intent"), resp.get("state"),
                )

            # Always store every turn — complaint_id is NULL for pre-complaint messages.
            await conn.execute(
                "INSERT INTO messages (complaint_id, user_id, session_id, role, content) "
                "VALUES ($1, $2, $3, 'user', $4)",
                cid, user_id, session_id, body.message,
            )
            if resp.get("reply"):
                await conn.execute(
                    "INSERT INTO messages (complaint_id, user_id, session_id, role, content) "
                    "VALUES ($1, $2, $3, 'assistant', $4)",
                    cid, user_id, session_id, resp["reply"],
                )

            # Retroactively link any earlier messages in this session that had no complaint_id.
            if cid and session_id:
                await conn.execute(
                    "UPDATE messages SET complaint_id = $1 "
                    "WHERE user_id = $2 AND session_id = $3 AND complaint_id IS NULL",
                    cid, user_id, session_id,
                )

    # Publish stage_0_chat ONLY after the DB INSERT — this guarantees the complaint row
    # exists before the pipeline orchestrator starts processing. Only publish when the
    # chatbot signals pipeline_triggered (conversation complete), not on every turn.
    if cid and resp.get("pipeline_triggered"):
        chat_event = {
            "complaint_id": cid,
            "stage": "stage_0_chat",
            "status": "completed",
            "payload": {
                "user_id": user_id,
                "session_id": resp.get("session_id", ""),
                "complaint_buffer": resp.get("complaint_buffer", ""),
                "language": resp.get("language", "hinglish"),
                "needs_location_pin": resp.get("needs_location_pin", False),
            },
        }
        await _redis.publish(f"pipeline:{cid}", json.dumps(chat_event))
        await _redis.publish("pipeline:all", json.dumps(chat_event))

    return resp


@app.post("/api/v1/session/reset")
async def reset_session(user_id: str = Depends(auth.get_current_user_id)):
    """Clear chatbot + NLU sessions so the next message starts a fresh complaint."""
    import asyncio
    results = await asyncio.gather(
        _http.delete(f"{CHATBOT_URL}/api/v1/session/{user_id}"),
        _http.delete(f"{NLU_URL}/api/v1/converse/{user_id}"),
        return_exceptions=True,
    )
    for r in results:
        if isinstance(r, Exception):
            logger.warning("Session reset partial failure: %s", r)
    return {"status": "ok"}


@app.post("/api/v1/session/restore/{complaint_id}")
async def restore_session(complaint_id: str, user_id: str = Depends(auth.get_current_user_id)):
    """Restore chatbot session from DB messages for an in-progress complaint."""
    async with db.pool().acquire() as conn:
        # Verify ownership
        row = await conn.fetchrow(
            "SELECT complaint_id, state, pipeline_data FROM complaints "
            "WHERE complaint_id = $1 AND user_id = $2",
            complaint_id, user_id,
        )
        if not row:
            raise HTTPException(404, "Complaint not found")
        msgs = await conn.fetch(
            "SELECT role, content FROM messages WHERE complaint_id = $1 ORDER BY seq ASC",
            complaint_id,
        )

    pd = row["pipeline_data"]
    if isinstance(pd, str):
        import json as _j; pd = _j.loads(pd) if pd else {}
    complaint_buffer = (pd.get("nlu") or {}).get("text_normalized", "")

    # Set correct state so chatbot doesn't re-ask for things already done.
    if pd.get("submission"):
        state = "SUBMITTED"
    elif pd.get("routing"):
        state = "SUBMITTED"   # portal picked — field collection handles next steps
    elif pd.get("location"):
        state = "COLLECTING"  # location done, shouldn't ask for it again
    else:
        state = row["state"] or "COLLECTING"

    messages = [{"role": r["role"], "content": r["content"]} for r in msgs]

    try:
        await _http.post(
            f"{CHATBOT_URL}/api/v1/session/restore",
            json={
                "user_id": user_id,
                "complaint_id": str(complaint_id),
                "complaint_buffer": complaint_buffer,
                "state": state,
                "messages": messages,
            },
        )
    except Exception as e:
        logger.warning(f"Session restore failed: {e}")
    return {"status": "ok"}


@app.post("/api/v1/location/reverse-geocode")
async def proxy_reverse_geocode(body: dict):
    r = await _http.post(f"{LOCATION_URL}/api/v1/reverse-geocode", json=body)
    return r.json()


@app.get("/api/v1/location/pincode/{pincode}")
async def proxy_pincode(pincode: str):
    r = await _http.get(f"{LOCATION_URL}/api/v1/pincode/{pincode}")
    return r.json()


class AttachLocationRequest(BaseModel):
    complaint_id: str
    lat: float
    lon: float


@app.post("/api/v1/complaint/attach-location")
async def attach_location(req: AttachLocationRequest):
    """Frontend calls this after user pins location.

    Reverse-geocodes and stores location for the complaint, then resumes pipeline.
    """
    geo_resp = await _http.post(
        f"{LOCATION_URL}/api/v1/reverse-geocode",
        json={"lat": req.lat, "lon": req.lon},
    )
    location = geo_resp.json()

    await _redis.set(
        f"complaint:{req.complaint_id}:location",
        json.dumps(location),
        ex=86400,
    )

    event = {
        "complaint_id": req.complaint_id,
        "stage": "stage_1_intake",
        "status": "completed",
        "payload": {"location": location},
    }
    await _redis.publish(f"pipeline:{req.complaint_id}", json.dumps(event))
    await _redis.publish("pipeline:all", json.dumps(event))

    return {"status": "ok", "location": location}


# ── WebSocket: live pipeline updates ──────────────────────────────────

@app.websocket("/ws/pipeline/{complaint_id}")
async def pipeline_ws(websocket: WebSocket, complaint_id: str):
    await websocket.accept()
    pubsub = _redis.pubsub()
    await pubsub.subscribe(f"pipeline:{complaint_id}")
    logger.info(f"WS subscribed: pipeline:{complaint_id}")

    try:
        # Replay all cached pipeline stages so late-connecting clients catch up.
        for stage_key, stage_name, payload_wrapper in [
            (f"complaint:{complaint_id}:location",       "stage_1_intake",   "location"),
            (f"complaint:{complaint_id}:nlu",            "stage_2_nlu",      None),
            (f"complaint:{complaint_id}:classification", "stage_3_classify", None),
            (f"complaint:{complaint_id}:routing",        "stage_5_route",    None),
            (f"complaint:{complaint_id}:submission",     "stage_8_submit",   None),
        ]:
            cached = await _redis.get(stage_key)
            if cached:
                payload = json.loads(cached)
                # Skip incomplete submission cache (only "started" payload, no ticket yet)
                if stage_name == "stage_8_submit" and not payload.get("portal_ticket_id"):
                    continue
                if payload_wrapper:
                    payload = {payload_wrapper: payload}
                await websocket.send_text(json.dumps({
                    "stage": stage_name,
                    "status": "completed",
                    "payload": payload,
                }))

        async for msg in pubsub.listen():
            if msg["type"] == "message":
                await websocket.send_text(msg["data"])
    except WebSocketDisconnect:
        logger.info(f"WS disconnected: {complaint_id}")
    finally:
        await pubsub.unsubscribe(f"pipeline:{complaint_id}")
        await pubsub.close()


# ── Orchestrator loop ─────────────────────────────────────────────────

async def _orchestrator_loop():
    pubsub = _redis.pubsub()
    await pubsub.subscribe("pipeline:all")

    async for msg in pubsub.listen():
        if msg["type"] != "message":
            continue
        try:
            event = json.loads(msg["data"])
        except Exception:
            continue

        stage = event.get("stage")
        status = event.get("status")
        complaint_id = event.get("complaint_id")
        payload = event.get("payload", {})

        if stage == "stage_0_chat" and status == "completed":
            already_classified = await _redis.get(f"complaint:{complaint_id}:classification")
            awaiting_clarification = await _redis.get(f"complaint:{complaint_id}:awaiting_clarification")
            if not already_classified or awaiting_clarification:
                # Re-run if awaiting classifier clarification (user answered, pipeline re-fires)
                if awaiting_clarification:
                    await _redis.delete(f"complaint:{complaint_id}:awaiting_clarification")
                    await _redis.delete(f"complaint:{complaint_id}:classification")
                await _trigger_nlu(complaint_id, payload)
        elif stage == "stage_2_nlu" and status == "completed":
            await _trigger_classifier(complaint_id, payload)
        elif stage == "stage_3_classify" and status == "completed":
            if payload.get("needs_clarification"):
                # Low classifier confidence — push clarifying question back to user via chatbot
                question = payload.get("clarifying_question", "")
                if question:
                    clarify_count_key = f"complaint:{complaint_id}:clarify_count"
                    count = int(await _redis.get(clarify_count_key) or 0)
                    if count < 2:
                        await _redis.incr(clarify_count_key)
                        await _redis.expire(clarify_count_key, 3600)
                        # Mark complaint as awaiting clarification so chatbot re-triggers pipeline
                        await _redis.set(f"complaint:{complaint_id}:awaiting_clarification", "1", ex=3600)
                        # Get user_id from DB
                        async with db.pool().acquire() as conn:
                            uid = await conn.fetchval(
                                "SELECT user_id FROM complaints WHERE complaint_id=$1", complaint_id
                            )
                        if uid:
                            await _http.post(
                                f"{CHATBOT_URL}/api/v1/session/notify",
                                json={"user_id": str(uid), "message": question},
                                timeout=5.0,
                            )
                        # Broadcast clarification event to frontend
                        await _redis.publish(f"pipeline:{complaint_id}", json.dumps({
                            "complaint_id": complaint_id, "stage": "stage_3_classify",
                            "status": "needs_clarification",
                            "payload": {"clarifying_question": question},
                        }))
                        return  # Wait for user answer; pipeline resumes when chatbot re-fires stage_0
                    # Max clarifications reached — proceed with current best guess
                # No question or max attempts — fall through to routing
            # High confidence OR max clarifications reached — proceed to routing
            loc = await _redis.get(f"complaint:{complaint_id}:location")
            if loc:
                await _trigger_routing(complaint_id, payload)
            else:
                await _redis.set(f"complaint:{complaint_id}:pending_route", json.dumps(payload), ex=86400)
        elif stage == "stage_1_intake" and status == "completed":
            # Location just confirmed — if classification already ran, trigger routing now.
            pending = await _redis.get(f"complaint:{complaint_id}:pending_route")
            if pending:
                await _redis.delete(f"complaint:{complaint_id}:pending_route")
                await _trigger_routing(complaint_id, json.loads(pending))
        elif stage == "stage_5_route" and status == "completed":
            # Cache routing payload immediately in orchestrator — don't wait for persistence loop.
            # Eliminates race condition where _trigger_field_collection runs before persistence
            # loop stores complaint:{id}:routing in Redis.
            await _redis.set(f"complaint:{complaint_id}:routing", json.dumps(payload), ex=86400)
            await _run_dedup(complaint_id)
        elif stage == "stage_7_dedup" and status == "completed":
            await _trigger_field_collection(complaint_id, payload)
        elif stage == "stage_6_filler" and status == "completed":
            await _trigger_submission(complaint_id, payload)


# ── Persistence loop: mirror pipeline events into Postgres ──────────────

async def _persistence_loop():
    pubsub = _redis.pubsub()
    await pubsub.subscribe("pipeline:all")

    async for msg in pubsub.listen():
        if msg["type"] != "message":
            continue
        try:
            event = json.loads(msg["data"])
        except Exception:
            continue

        cid = event.get("complaint_id")
        if not cid:
            continue
        stage = event.get("stage")
        payload = event.get("payload") or {}

        # Each downstream service publishes its result AS the payload (not nested).
        # stage_1_intake (gateway-emitted) is the exception: it wraps as {"location": ...}.
        try:
            async with db.pool().acquire() as conn:
                if stage == "stage_3_classify":
                    await _redis.set(f"complaint:{cid}:classification", json.dumps(payload), ex=86400)
                    dept    = payload.get("department")
                    sub_cat = payload.get("sub_category")
                    # Compute S-BERT embedding from normalized text (read from stored NLU pipeline_data).
                    existing = await conn.fetchval(
                        "SELECT pipeline_data FROM complaints WHERE complaint_id = $1", cid
                    )
                    existing_pd = existing or {}
                    nlu_text = existing_pd.get("nlu", {}).get("text_normalized", "")
                    # Run blocking SBERT inference in a thread pool — keeps the event loop free
                    # during the first model load (~15s) and subsequent encode() calls.
                    loop = asyncio.get_event_loop()
                    embedding = await loop.run_in_executor(None, embed, nlu_text) if nlu_text else None
                    if embedding:
                        await conn.execute(
                            "UPDATE complaints "
                            "SET department = COALESCE($2, department), "
                            "    sub_category = COALESCE($3, sub_category), "
                            "    text_embedding = $4, "
                            "    pipeline_data = pipeline_data || $5, "
                            "    updated_at = NOW() "
                            "WHERE complaint_id = $1",
                            cid, dept, sub_cat, embedding, {"classification": payload},
                        )
                    else:
                        await conn.execute(
                            "UPDATE complaints "
                            "SET department = COALESCE($2, department), "
                            "    sub_category = COALESCE($3, sub_category), "
                            "    pipeline_data = pipeline_data || $4, "
                            "    updated_at = NOW() "
                            "WHERE complaint_id = $1",
                            cid, dept, sub_cat, {"classification": payload},
                        )
                elif stage == "stage_5_route":
                    await _redis.set(f"complaint:{cid}:routing", json.dumps(payload), ex=86400)
                    pid = payload.get("portal_id")
                    await conn.execute(
                        "UPDATE complaints "
                        "SET portal_id = COALESCE($2, portal_id), "
                        "    pipeline_data = pipeline_data || $3, "
                        "    updated_at = NOW() "
                        "WHERE complaint_id = $1",
                        cid, pid, {"routing": payload},
                    )
                elif stage == "stage_7_dedup":
                    await conn.execute(
                        "UPDATE complaints "
                        "SET pipeline_data = pipeline_data || $2, "
                        "    updated_at = NOW() "
                        "WHERE complaint_id = $1",
                        cid, {"dedup": payload},
                    )
                elif stage == "stage_6_filler":
                    portal_fields = payload.get("portal_fields", {})
                    await conn.execute(
                        "UPDATE complaints "
                        "SET pipeline_data = pipeline_data || $2, "
                        "    updated_at = NOW() "
                        "WHERE complaint_id = $1",
                        cid, {"portal_fields": portal_fields},
                    )
                elif stage == "stage_8_submit":
                    status_val = event.get("status", "")
                    # Only cache + persist on completed (not started) to avoid overwriting good data
                    if status_val == "completed" and payload.get("portal_ticket_id"):
                        await _redis.set(f"complaint:{cid}:submission", json.dumps(payload), ex=86400)
                        ticket = payload.get("portal_ticket_id")
                        await conn.execute(
                            "UPDATE complaints SET ticket_id = COALESCE($2, ticket_id), "
                            "status = 'submitted', "
                            "pipeline_data = pipeline_data || $3, updated_at = NOW() "
                            "WHERE complaint_id = $1",
                            cid, ticket, {"submission": payload},
                        )
                        await log_event(cid, "submit_success", {"ticket_id": ticket, "portal_id": payload.get("portal_id")})
                        # Re-publish to the complaint-specific WS channel so frontend always gets it
                        ws_event = json.dumps({"stage": "stage_8_submit", "status": "completed", "payload": payload})
                        await _redis.publish(f"pipeline:{cid}", ws_event)

                    # ── Multi-domain reminder: notify user about pending domains ──
                    try:
                        l2_raw = await _redis.get(f"complaint:{cid}:layer2_slots")
                        if l2_raw:
                            l2_slots = json.loads(l2_raw)
                            pending = l2_slots.get("pending_domains", [])
                            if pending:
                                _CAT_EN = {
                                "Electricity": "Bijli/Electricity",
                                "Water Supply": "Paani/Water",
                                "Roads & Transportation": "Sadak/Roads",
                                "Waste Management": "Safai/Sanitation",
                                "Health & Family Welfare": "Health",
                                "Police": "Police",
                                "Education (Higher / School)": "Education",
                                "Housing & Urban Affairs": "Housing",
                                "Agriculture & Farmers Welfare": "Agriculture",
                                "Banking (DFS)": "Banking",
                                "Aadhaar (UIDAI)": "Aadhaar",
                                "Pension & Pensioners Welfare": "Pension",
                                "Petroleum & LPG": "LPG/Gas",
                                "Public Distribution (PDS)": "Ration",
                                "Public Safety & Encroachment": "Noise/Nuisance",
                                "Railways": "Railway",
                                "Telecom": "Telecom",
                                }
                                filed_cat = l2_slots.get("category", "")
                                filed_name = _CAT_EN.get(filed_cat, filed_cat)
                                pending_names = " & ".join(_CAT_EN.get(c, c) for c in pending)
                                ticket_str = ticket or cid[:8] + "..."
                                reminder = (
                                f"✅ Aapki {filed_name} shikayat darj ho gayi (Ticket: {ticket_str}).\n\n"
                                f"Aapne {pending_names} ki samasya bhi bataayi thi. "
                                f"Kripya 'New Complaint' button se use alag darj karein."
                                )
                                uid_row = await conn.fetchrow(
                                    "SELECT user_id FROM complaints WHERE complaint_id=$1", cid
                                )
                                if uid_row:
                                    await _http.post(
                                        f"{CHATBOT_URL}/api/v1/session/notify",
                                        json={"user_id": str(uid_row["user_id"]), "message": reminder},
                                        timeout=5.0,
                                    )
                    except Exception as rem_e:
                        logger.warning("multi-domain reminder failed: %s", rem_e)
                elif stage == "stage_2_nlu":
                    await conn.execute(
                        "UPDATE complaints SET pipeline_data = pipeline_data || $2, "
                        "updated_at = NOW() WHERE complaint_id = $1",
                        cid, {"nlu": payload},
                    )
                    await _redis.set(f"complaint:{cid}:nlu", json.dumps(payload), ex=86400)
                elif stage == "stage_1_intake":
                    loc = payload.get("location") or payload
                    district = loc.get("district") if isinstance(loc, dict) else None
                    await conn.execute(
                        "UPDATE complaints "
                        "SET district = COALESCE($2, district), "
                        "    pipeline_data = pipeline_data || $3, "
                        "    updated_at = NOW() "
                        "WHERE complaint_id = $1",
                        cid, district, {"location": loc},
                    )
                    await _redis.set(f"complaint:{cid}:location", json.dumps(loc), ex=86400)
        except Exception as e:
            logger.warning(f"persistence_loop update failed for {cid}: {e}")


async def _trigger_nlu(complaint_id: str, payload: dict):
    try:
        text_raw = payload.get("complaint_buffer", "").strip()

        # If buffer is too short, enrich with stored user messages from DB.
        if len(text_raw) < 15:
            try:
                async with db.pool().acquire() as conn:
                    msgs = await conn.fetch(
                        "SELECT content FROM messages WHERE complaint_id = $1 "
                        "AND role = 'user' ORDER BY seq ASC LIMIT 10",
                        complaint_id,
                    )
                if msgs:
                    text_raw = " ".join(r["content"] for r in msgs) + " " + text_raw
                    text_raw = text_raw.strip()
            except Exception:
                pass

        # Store Layer 2 slots in Redis so classifier can use them as strong prior
        slots = payload.get("slots", {})
        if slots:
            await _redis.set(
                f"complaint:{complaint_id}:layer2_slots",
                json.dumps(slots),
                ex=86400,
            )

        await _http.post(
            f"{NLU_URL}/api/v1/process",
            json={
                "complaint_id": complaint_id,
                "text_raw": text_raw or payload.get("complaint_buffer", ""),
                "language_hint": payload.get("language", "en"),
            },
            timeout=10.0,
        )
    except Exception as e:
        logger.error(f"NLU trigger failed: {e}")


async def _trigger_classifier(complaint_id: str, payload: dict):
    try:
        # Inject Layer 2 confirmed category as a strong domain hint.
        # Since the user explicitly selected/confirmed their complaint type in the
        # guided conversation, Layer 2's category is more reliable than NLU keyword matching.
        layer2_raw = await _redis.get(f"complaint:{complaint_id}:layer2_slots")
        if layer2_raw:
            slots = json.loads(layer2_raw)
            layer2_cat = slots.get("category", "")
            if layer2_cat:
                # Prepend Layer 2 category to domain_hints so classifier uses it first
                existing = payload.get("domain_hints", [])
                # Map Layer 2 category name to the domain key used by classifier
                cat_to_domain = {
                    "Electricity": "electricity",
                    "Water Supply": "water",
                    "Roads & Transportation": "roads",
                    "Waste Management": "waste",
                    "Health & Family Welfare": "health",
                    "Police": "police",
                    "Education (Higher / School)": "education",
                    "Housing & Urban Affairs": "housing",
                    "Agriculture & Farmers Welfare": "agriculture",
                    "Banking (DFS)": "banking",
                    "Aadhaar (UIDAI)": "aadhaar",
                    "Income Tax (CBDT)": "income_tax",
                    "GST (CBIC)": "gst",
                    "EPFO": "epfo",
                    "Insurance (DFS)": "insurance",
                    "Passport (MEA)": "passport",
                    "Pension & Pensioners Welfare": "pension",
                    "Petroleum & LPG": "lpg",
                    "Postal": "postal",
                    "Public Distribution (PDS)": "ration",
                    "Public Safety & Encroachment": "safety",
                    "RTO / State Transport": "transport",
                    "Railways": "railway",
                    "Telecom": "telecom",
                }
                domain = cat_to_domain.get(layer2_cat)
                if domain and domain not in existing:
                    payload = {**payload, "domain_hints": [domain] + existing}
                payload = {**payload, "layer2_category": layer2_cat}

        await _http.post(
            f"{CLASSIFIER_URL}/api/v1/classify",
            json={"complaint_id": complaint_id, **payload},
            timeout=10.0,
        )
    except Exception as e:
        logger.error(f"Classifier trigger failed: {e}")


# Maps classifier human-readable dept names → CSV classifier_dept_tags used by routing.
_DEPT_TO_TAG: dict[str, str] = {
    # MuRIL model output labels (exact matches from training data)
    "aadhaar (uidai)":                    "AADHAAR",
    "agriculture & farmers welfare":      "AGRICULTURE",
    "consumer affairs":                   "CONSUMER_PROTECTION",
    "epfo":                               "EPF_ESIC",
    "gst (cbic)":                         "GST",
    "health & family welfare":            "HEALTH",
    "housing & urban affairs":            "HOUSING_URBAN",
    "income tax (cbdt)":                  "INCOME_TAX",
    "insurance (dfs)":                    "INSURANCE",
    "passport (mea)":                     "PASSPORT",
    "pension & pensioners' welfare":      "PENSION_SOCIAL",
    "petroleum & lpg":                    "PETROLEUM_LPG",
    "public distribution (pds)":          "FOOD_RATION",
    "public safety & encroachment":       "POLICE",
    "railways":                           "RAILWAY",
    # Generic fallbacks
    "electricity":                 "ELECTRICITY",
    "water supply":                "WATER_SUPPLY",
    "roads & transportation":      "ROADS",
    "roads and transportation":    "ROADS",
    "roads":                       "ROADS",
    "waste management":            "SANITATION",
    "sanitation":                  "SANITATION",
    "solid waste":                 "SOLID_WASTE",
    "police":                      "POLICE",
    "banking (dfs)":               "BANKING",
    "banking":                     "BANKING",
    "health":                      "HEALTH",
    "education (higher / school)": "EDUCATION_SCHOOL",
    "education":                   "EDUCATION_SCHOOL",
    "higher education":            "EDUCATION_HIGHER",
    "rto / state transport":       "TRANSPORT_VEHICLE",
    "transport":                   "TRANSPORT_VEHICLE",
    "agriculture":                 "AGRICULTURE",
    "labour":                      "LABOUR_EMPLOYMENT",
    "labour & employment":         "LABOUR_EMPLOYMENT",
    "women & child":               "WOMEN_CHILD",
    "women and child":             "WOMEN_CHILD",
    "corruption":                  "CORRUPTION",
    "cyber crime":                 "CYBER_CRIME",
    "revenue & land":              "REVENUE_LAND",
    "revenue":                     "REVENUE_LAND",
    "food & ration":               "FOOD_RATION",
    "food":                        "FOOD_RATION",
    "pension":                     "PENSION_SOCIAL",
    "social welfare":              "SOCIAL_WELFARE_SCHEME",
    "housing":                     "HOUSING_URBAN",
    "forest":                      "FOREST_WILDLIFE",
    "environment":                 "ENVIRONMENT_POLLUTION",
    "mining":                      "MINING",
    "income tax":                  "INCOME_TAX",
    "gst":                         "GST",
    "epf / esic":                  "EPF_ESIC",
    "railway":                     "RAILWAY",
    "postal":                      "POSTAL",
    "passport":                    "PASSPORT",
    "aadhaar":                     "AADHAAR",
    "insurance":                   "INSURANCE",
    "consumer protection":         "CONSUMER_PROTECTION",
    "telecom":                     "TELECOM",
    "real estate":                 "REAL_ESTATE",
    "tribal rights":               "TRIBAL_RIGHTS",
    "human rights":                "HUMAN_RIGHTS",
    "welfare sc/st":               "WELFARE_SC_ST",
    "defence pension":             "DEFENCE_PENSION",
    "election":                    "ELECTION",
    "general administration":      "ELECTRICITY",   # safe default
}


def _dept_to_tag(dept: str) -> str:
    """Normalise a classifier department label to a routing CSV tag."""
    key = dept.lower().strip()
    if key in _DEPT_TO_TAG:
        return _DEPT_TO_TAG[key]
    # Already a tag (all-caps, no spaces)?
    if dept == dept.upper() and " " not in dept:
        return dept
    # Best-effort: upper + underscores
    return dept.upper().replace(" ", "_").replace("&", "AND").replace("/", "_").replace("(", "").replace(")", "")


async def _trigger_routing(complaint_id: str, payload: dict):
    try:
        dept_raw = payload.get("department", "")
        tag      = _dept_to_tag(dept_raw)
        if tag != dept_raw:
            logger.info("dept normalised: '%s' → '%s'", dept_raw, tag)
        routing_payload = {**payload, "department": tag}
        await _http.post(
            f"{ROUTING_URL}/api/v1/route",
            json={"complaint_id": complaint_id, **routing_payload},
            timeout=10.0,
        )
    except Exception as e:
        logger.error(f"Routing trigger failed: {e}")


# ── Stage 8: Submission ───────────────────────────────────────────────

SUBMISSION_URL = os.getenv("SUBMISSION_URL", "http://service-submission:8006")

_RETRY_DELAYS = [60, 120, 300, 900, 3600, 14400, 86400]   # seconds: 1m 2m 5m 15m 1h 4h 24h


async def _trigger_submission(complaint_id: str, payload: dict, attempt: int = 0) -> None:
    portal_id    = payload.get("portal_id", "P001")
    portal_fields = payload.get("portal_fields", {})

    async with db.pool().acquire() as conn:
        row = await conn.fetchrow(
            "SELECT user_id, pipeline_data FROM complaints WHERE complaint_id = $1",
            complaint_id,
        )
    if not row:
        return

    _pd_r = row["pipeline_data"] or {}
    pd = json.loads(_pd_r) if isinstance(_pd_r, str) else _pd_r
    classification = pd.get("classification", {})
    location       = pd.get("location", {})
    if isinstance(location, dict) and "location" in location:
        location = location["location"]
    nlu = pd.get("nlu", {})

    routing = pd.get("routing", {})
    portal_name = routing.get("portal_name", payload.get("portal_name", ""))

    uco_meta = {
        "complaint_text": nlu.get("text_normalized") or nlu.get("text_raw", ""),
        "department":     classification.get("department", ""),
        "sub_category":   classification.get("sub_category", ""),
        "district":       location.get("district", "") if isinstance(location, dict) else "",
        "user_id":        str(row["user_id"]),
        "portal_name":    portal_name,  # used by generic adapter for ticket prefix
    }

    await log_event(complaint_id, "submit_attempt", {"portal_id": portal_id, "attempt": attempt})

    try:
        await _http.post(
            f"{SUBMISSION_URL}/api/v1/submit",
            json={
                "complaint_id":  complaint_id,
                "portal_id":     portal_id,
                "portal_name":   portal_name,
                "portal_fields": portal_fields,
                "uco_meta":      uco_meta,
            },
            timeout=20.0,
        )
    except Exception as e:
        logger.error("submission attempt %d failed for %s: %s", attempt, complaint_id, e)
        await log_event(complaint_id, "submit_failed", {"attempt": attempt, "error": str(e)})

        if attempt < len(_RETRY_DELAYS):
            delay = _RETRY_DELAYS[attempt]
            logger.info("scheduling retry %d for %s in %ds", attempt + 1, complaint_id, delay)
            asyncio.get_event_loop().call_later(
                delay,
                lambda: asyncio.create_task(_trigger_submission(complaint_id, payload, attempt + 1)),
            )
        else:
            logger.error("all retries exhausted for %s — needs human review", complaint_id)
            await log_event(complaint_id, "submit_exhausted", {"total_attempts": attempt + 1})
            async with db.pool().acquire() as conn:
                await conn.execute(
                    "UPDATE complaints SET status = 'failed', updated_at = NOW() WHERE complaint_id = $1",
                    complaint_id,
                )


# ── Stage 7: Duplicate Check ──────────────────────────────────────────

_DEDUP_WINDOW_DAYS = 180  # 6 months


async def _run_dedup(complaint_id: str) -> None:
    """Query Postgres for duplicate complaints and publish stage_7_dedup event.
    Has a 20s timeout — if SBERT model is still loading, skips dedup and proceeds."""
    try:
        await asyncio.wait_for(_run_dedup_inner(complaint_id), timeout=20.0)
    except asyncio.TimeoutError:
        logger.warning("dedup timed out for %s — skipping, proceeding to field collection", complaint_id)
        await _publish_dedup(complaint_id, {"is_duplicate": False, "duplicate_count": 0, "skipped": True})
    except Exception as e:
        logger.error("dedup error for %s: %s", complaint_id, e)
        await _publish_dedup(complaint_id, {"is_duplicate": False, "duplicate_count": 0, "error": str(e)})


async def _run_dedup_inner(complaint_id: str) -> None:
    """Inner dedup logic — wrapped with timeout by _run_dedup.

    Match criteria: same department + sub_category + district,
    unresolved (status NOT IN resolved/rejected), within 6 months.

    Three outcomes:
      1. is_duplicate=False            → no duplicates, proceed to field collection
      2. is_duplicate=True, is_same_user=True  → user already filed this; block re-submission
      3. is_duplicate=True, is_same_user=False → aggregate: show count + details
    """
    try:
        async with db.pool().acquire() as conn:
            # Read the complaint's own metadata (user, dept, sub_cat, district).
            own = await conn.fetchrow(
                "SELECT user_id, department, sub_category, district "
                "FROM complaints WHERE complaint_id = $1",
                complaint_id,
            )

        if not own:
            logger.warning("dedup: complaint %s not found in DB", complaint_id)
            return

        user_id   = str(own["user_id"])
        dept      = own["department"]
        sub_cat   = own["sub_category"]
        district  = own["district"]

        # Can't deduplicate without classification or location yet.
        if not dept or not district:
            logger.info("dedup: skipping %s — missing dept=%s district=%s", complaint_id, dept, district)
            result = {"is_duplicate": False, "duplicate_count": 0, "skipped": True}
            await _publish_dedup(complaint_id, result)
            return

        cutoff = datetime.utcnow() - timedelta(days=_DEDUP_WINDOW_DAYS)

        async with db.pool().acquire() as conn:
            # Fetch own embedding for semantic comparison.
            own_emb_raw = await conn.fetchval(
                "SELECT text_embedding FROM complaints WHERE complaint_id = $1", complaint_id
            )
            own_embedding = list(own_emb_raw) if own_emb_raw else None

            rows = await conn.fetch(
                """
                SELECT
                    c.complaint_id,
                    c.user_id,
                    c.created_at,
                    c.status,
                    c.pipeline_data,
                    c.text_embedding,
                    u.name,
                    u.mobile,
                    (c.user_id = $5::uuid) AS is_same_user
                FROM complaints c
                JOIN users u ON c.user_id = u.id
                WHERE c.district     = $1
                  AND c.status NOT IN ('resolved', 'rejected')
                  AND c.created_at   > $2
                  AND c.complaint_id != $3::uuid
                  AND c.department   = $4
                ORDER BY c.created_at DESC
                LIMIT 100
                """,
                district, cutoff, complaint_id, dept, user_id,
            )

        if not rows:
            result = {"is_duplicate": False, "duplicate_count": 0}
            await _publish_dedup(complaint_id, result)
            logger.info("dedup: no candidates in district=%s dept=%s", district, dept)
            return

        # ── Semantic similarity filter ──────────────────────────────────
        # If S-BERT is ready, keep only candidates whose embedding cosine-sim ≥ threshold.
        # If model is not loaded yet, fall back to sub_category exact match.
        use_sbert = own_embedding is not None
        filtered_rows = []
        for row in rows:
            if use_sbert:
                cand_emb = row["text_embedding"]
                if cand_emb is None:
                    # Candidate has no embedding — fall back to sub_category match.
                    if row["complaint_id"] and sub_cat and sub_cat == (
                        (json.loads(row["pipeline_data"]) if isinstance(row["pipeline_data"], str) else (row["pipeline_data"] or {})).get("classification", {}).get("sub_category")
                    ):
                        filtered_rows.append((row, 0.0))
                else:
                    sim = cosine_similarity(own_embedding, list(cand_emb))
                    if sim >= SIMILARITY_THRESHOLD:
                        filtered_rows.append((row, sim))
            else:
                # No S-BERT — exact sub_category match
                _pd_row_r = row["pipeline_data"] or {}
                pd_row = json.loads(_pd_row_r) if isinstance(_pd_row_r, str) else _pd_row_r
                cand_sub_cat = pd_row.get("classification", {}).get("sub_category", "")
                if sub_cat and cand_sub_cat == sub_cat:
                    filtered_rows.append((row, 0.0))

        if not filtered_rows:
            result = {"is_duplicate": False, "duplicate_count": 0}
            await _publish_dedup(complaint_id, result)
            logger.info("dedup: no semantic duplicates for complaint %s (sbert=%s)", complaint_id, use_sbert)
            return

        # Sort by similarity descending.
        filtered_rows.sort(key=lambda x: x[1], reverse=True)

        # Check if any match belongs to the same user.
        same_user_row = next((r for r, _ in filtered_rows if r["is_same_user"]), None)
        if same_user_row:
            result = {
                "is_duplicate": True,
                "is_same_user": True,
                "existing_complaint_id": str(same_user_row["complaint_id"]),
                "filed_at": same_user_row["created_at"].isoformat(),
                "status": same_user_row["status"],
                "duplicate_count": 1,
            }
            await _publish_dedup(complaint_id, result)
            logger.info("dedup: same-user duplicate %s → existing %s",
                        complaint_id, same_user_row["complaint_id"])
            return

        # Different users — build aggregate details.
        details = []
        for row, sim in filtered_rows:
            _pd_row_r = row["pipeline_data"] or {}
            pd_row = json.loads(_pd_row_r) if isinstance(_pd_row_r, str) else _pd_row_r

            portal_fields = pd_row.get("portal_fields", {})
            raw_mobile = row["mobile"] or ""
            masked_mobile = ("*" * (len(raw_mobile) - 4) + raw_mobile[-4:]) if len(raw_mobile) >= 4 else "****"

            details.append({
                "complaint_id":  str(row["complaint_id"]),
                "name":          row["name"],
                "mobile":        masked_mobile,
                "filed_at":      row["created_at"].isoformat(),
                "status":        row["status"],
                "similarity":    round(sim, 3),
                "portal_fields": portal_fields,
            })

        result = {
            "is_duplicate": True,
            "is_same_user": False,
            "duplicate_count": len(details),
            "department": dept,
            "sub_category": sub_cat,
            "district": district,
            "duplicate_details": details,
        }
        await _publish_dedup(complaint_id, result)
        logger.info(
            "dedup: %d other-user duplicate(s) for complaint %s (dept=%s district=%s)",
            len(details), complaint_id, dept, district,
        )

    except Exception as e:
        logger.error("dedup failed for complaint %s: %s", complaint_id, e)
        # Publish a skipped event so the pipeline doesn't stall.
        await _publish_dedup(complaint_id, {"is_duplicate": False, "duplicate_count": 0, "error": str(e)})


async def _trigger_field_collection(complaint_id: str, dedup_result: dict) -> None:
    """After dedup: either block same-user duplicate or start field collection."""
    try:
        # Ensure dedup_result is a dict (might arrive as list in edge cases).
        if not isinstance(dedup_result, dict):
            logger.warning("field_collection: dedup_result is %s, expected dict — wrapping", type(dedup_result).__name__)
            dedup_result = {"is_duplicate": False, "duplicate_count": 0}

        async with db.pool().acquire() as conn:
            row = await conn.fetchrow(
                "SELECT user_id, pipeline_data FROM complaints WHERE complaint_id = $1",
                complaint_id,
            )
        if not row:
            logger.warning("field_collection: complaint %s not found", complaint_id)
            return

        user_id = str(row["user_id"])
        _pd_r = row["pipeline_data"] or {}
        pd = json.loads(_pd_r) if isinstance(_pd_r, str) else _pd_r

        # ── Same-user duplicate: block and notify ──────────────────────────
        if dedup_result.get("is_same_user"):
            existing_id = dedup_result.get("existing_complaint_id", "")[:8]
            msg = (
                f"Aapki yahi shikayat pehle se register hai (ID: {existing_id}...). "
                "Duplicate shikayat register nahi ki ja sakti. "
                "Apni purani shikayat ka status check karein."
            )
            await _http.post(
                f"{CHATBOT_URL}/api/v1/session/notify",
                json={"user_id": user_id, "message": msg},
                timeout=5.0,
            )
            logger.info("field_collection: blocked same-user duplicate for complaint %s", complaint_id)
            return

        # ── Start field collection ─────────────────────────────────────────
        # Prefer Redis cache (set by persistence_loop, faster than DB write).
        routing = pd.get("routing", {})
        if not routing.get("required_fields"):
            cached = await _redis.get(f"complaint:{complaint_id}:routing")
            if cached:
                routing = json.loads(cached)

        required_fields = routing.get("required_fields", [])
        portal_name     = routing.get("portal_name", "Portal")
        portal_id       = routing.get("portal_id", "")

        if not required_fields:
            # Last resort: re-query routing service with stored dept + location
            dept_tag = pd.get("classification", {}).get("department", "")
            loc_cached = await _redis.get(f"complaint:{complaint_id}:location")
            if dept_tag and loc_cached:
                loc = json.loads(loc_cached)
                try:
                    route_resp = await _http.post(
                        f"{ROUTING_URL}/api/v1/route",
                        json={"complaint_id": complaint_id, "department": dept_tag},
                        timeout=8.0,
                    )
                    routing = route_resp.json()
                    required_fields = routing.get("required_fields", [])
                    portal_name     = routing.get("portal_name", "Portal")
                    portal_id       = routing.get("portal_id", "")
                    await _redis.set(f"complaint:{complaint_id}:routing", json.dumps(routing), ex=86400)
                except Exception as re:
                    logger.warning("field_collection re-route failed: %s", re)

        if not required_fields:
            logger.warning("field_collection: no required_fields for complaint %s", complaint_id)
            return

        dedup_info = dedup_result if dedup_result.get("is_duplicate") else None
        pre_filled = _build_prefill(pd, required_fields)

        resp = await _http.post(
            f"{CHATBOT_URL}/api/v1/field-collection/start",
            json={
                "user_id": user_id,
                "complaint_id": complaint_id,
                "portal_id": portal_id,
                "portal_name": portal_name,
                "required_fields": required_fields,
                "pre_filled": pre_filled,
                "dedup_info": dedup_info,
            },
            timeout=10.0,
        )
        data = resp.json()
        opening_msg = data.get("opening_message", "")

        # Push the opening message to the WebSocket so the frontend displays
        # it immediately without waiting for the user to send a message.
        if opening_msg:
            event = {
                "complaint_id": complaint_id,
                "stage": "stage_6_filler",
                "status": "started",
                "payload": {
                    "bot_message": opening_msg,
                    "portal_id": portal_id,
                    "portal_name": portal_name,
                    "required_fields": required_fields,
                    "fields_total": len(required_fields),
                },
            }
            await _redis.publish(f"pipeline:{complaint_id}", json.dumps(event))
            await _redis.publish("pipeline:all", json.dumps(event))

    except Exception as e:
        logger.error("_trigger_field_collection failed for %s: %s", complaint_id, e)


def _build_prefill(pipeline_data: dict, required_fields: list[str]) -> dict:
    """Map all collected data into portal field names.

    Sources (in priority order):
    1. NER entities — aadhaar, phone, email extracted from conversation
    2. GPS location — address, district, state, pincode from map pin
    3. Classification — department, sub_category as "type of complaint"
    4. Complaint text — normalized description prefills "description" fields
    5. Conversation slots — duration/date from Layer 2 conversation
    """
    pre: dict[str, str] = {}
    nlu        = pipeline_data.get("nlu", {})
    entities   = nlu.get("entities", {})
    location   = pipeline_data.get("location", {})
    clf        = pipeline_data.get("classification", {})

    if isinstance(location, dict) and "location" in location:
        location = location["location"]

    # ── 1. NER entity → field mapping ────────────────────────────────────
    ENTITY_RULES = [
        ("phone",       ["mobile", "phone", "contact number", "mobile number"],  "first"),
        ("email",       ["email"],                                               "first"),
        ("aadhaar",     ["aadhaar", "aadhar"],                                   "last4_if_4digit_field"),
        ("consumer_no", ["consumer number", "ivrs", "consumer no"],              "first"),
        ("account_no",  ["bank account", "account number"],                      "first"),
        ("vehicle_no",  ["vehicle number", "vehicle no", "rc number"],           "first"),
    ]
    for entity_key, keywords, transform in ENTITY_RULES:
        values = entities.get(entity_key, [])
        if not values:
            continue
        raw_value = values[0]
        for field_name in required_fields:
            fl = field_name.lower()
            if any(kw in fl for kw in keywords) and field_name not in pre:
                if transform == "last4_if_4digit_field" and "last 4" in fl:
                    pre[field_name] = raw_value[-4:] if len(raw_value) >= 4 else raw_value
                else:
                    pre[field_name] = raw_value

    # ── 2. Location fields ────────────────────────────────────────────────
    addr_text = location.get("address_text", "") if isinstance(location, dict) else ""
    LOC_RULES = [
        (addr_text,                  ["address", "full address", "address of connection",
                                      "location", "incident location", "place of incident",
                                      "incident place", "complaint location"]),
        (location.get("pincode", "") if isinstance(location, dict) else "", ["pincode", "pin code"]),
        (location.get("district", "") if isinstance(location, dict) else "", ["district"]),
        (location.get("state", "")   if isinstance(location, dict) else "", ["state"]),
        (location.get("ward", "")    if isinstance(location, dict) else "", ["ward"]),
    ]
    for value, keywords in LOC_RULES:
        if not value:
            continue
        for field_name in required_fields:
            fl = field_name.lower()
            if any(kw in fl for kw in keywords) and field_name not in pre:
                pre[field_name] = value

    # ── 3. Classification → "type of complaint" / "nature of complaint" ──
    sub_cat = clf.get("sub_category", "") or clf.get("department", "")
    if sub_cat:
        for field_name in required_fields:
            fl = field_name.lower()
            if any(kw in fl for kw in ["type of complaint", "nature of complaint",
                                        "complaint type", "category", "complaint category"]):
                if field_name not in pre:
                    pre[field_name] = sub_cat

    # ── 4. Complaint description → "description" / "grievance" fields ────
    # Prefer text_en (Layer 3 clean English) over raw normalized text
    complaint_text = (
        nlu.get("text_en") or
        nlu.get("text_normalized") or
        nlu.get("text_raw") or ""
    ).strip()
    # Remove internal tags like "[WATER_SUPPLY]" from the description
    import re as _re
    complaint_text = _re.sub(r"^\[[A-Z_&/ ]+\]\s*", "", complaint_text)
    if complaint_text:
        for field_name in required_fields:
            fl = field_name.lower()
            if any(kw in fl for kw in ["description", "grievance description",
                                        "complaint description", "issue description",
                                        "detail", "incident description",
                                        "describe", "grievance"]):
                if field_name not in pre:
                    pre[field_name] = complaint_text[:500]

    # ── 5. Date/time fields — use today's date as fallback ───────────────
    from datetime import datetime as _dt
    today = _dt.now().strftime("%d-%m-%Y")
    for field_name in required_fields:
        fl = field_name.lower()
        if any(kw in fl for kw in ["date", "date and time", "incident date",
                                    "time of incident"]):
            if field_name not in pre:
                pre[field_name] = today

    if pre:
        logger.info("pre-fill: %d/%d fields resolved: %s",
                    len(pre), len(required_fields), list(pre.keys()))
    return pre


async def _feedback_loop():
    """Drain the feedback_queue populated by service-tracker on RESOLVED.
    Sends a feedback-ask notification to the citizen via the chatbot session.
    """
    while True:
        await asyncio.sleep(10)
        try:
            raw = await _redis.rpop("feedback_queue")
            if not raw:
                continue
            item = json.loads(raw)
            complaint_id = item.get("complaint_id")
            ticket_id    = item.get("ticket_id", "")
            if not complaint_id:
                continue

            async with db.pool().acquire() as conn:
                user_id = await conn.fetchval(
                    "SELECT user_id FROM complaints WHERE complaint_id = $1", complaint_id
                )
            if not user_id:
                continue

            msg = (
                f"Aapki shikayat (ticket: {ticket_id[:12]}) resolve ho gayi hai. "
                "Kya aapki samasya haal ho gayi? "
                "Reply karein: '1' haan ke liye, '2' nahi ke liye."
            )
            await _http.post(
                f"{CHATBOT_URL}/api/v1/session/notify",
                json={"user_id": str(user_id), "message": msg},
                timeout=5.0,
            )
            await log_event(complaint_id, "feedback_requested", {"ticket_id": ticket_id}, actor="system")
            logger.info("feedback ask sent for complaint %s", complaint_id)
        except Exception as e:
            logger.warning("feedback_loop error: %s", e)


async def _publish_dedup(complaint_id: str, payload: dict) -> None:
    event = {
        "complaint_id": complaint_id,
        "stage": "stage_7_dedup",
        "status": "completed",
        "payload": payload,
    }
    await _redis.publish(f"pipeline:{complaint_id}", json.dumps(event))
    await _redis.publish("pipeline:all", json.dumps(event))
