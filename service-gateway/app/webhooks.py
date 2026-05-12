"""Webhook receiver — govt portals push status updates to us here.

CPGRAMS calls: POST /api/v1/webhook/cpgrams
We verify signature → update DB → notify user

WhatsApp providers (Twilio / Meta) push inbound user messages to:
POST /api/v1/webhook/whatsapp
GET  /api/v1/webhook/whatsapp  (Meta verify handshake)
"""

import hashlib
import hmac
import json
import logging
import os
from fastapi import APIRouter, HTTPException, Request, Response

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1/webhook", tags=["webhooks"])

CPGRAMS_WEBHOOK_SECRET = os.getenv("CPGRAMS_WEBHOOK_SECRET", "")
WHATSAPP_VERIFY_TOKEN  = os.getenv("WHATSAPP_VERIFY_TOKEN", "change-me")
TWILIO_AUTH_TOKEN      = os.getenv("TWILIO_AUTH_TOKEN", "")


def verify_signature(payload: bytes, signature: str, secret: str) -> bool:
    """Verify the webhook came from CPGRAMS, not a fake request."""
    expected = "sha256=" + hmac.new(
        secret.encode(), payload, hashlib.sha256
    ).hexdigest()
    return hmac.compare_digest(expected, signature)


@router.post("/cpgrams")
async def cpgrams_webhook(request: Request):
    """CPGRAMS pushes status updates here when a complaint status changes."""
    body = await request.body()
    signature = request.headers.get("X-CPGRAMS-Signature", "")

    # Step 1: Verify it's really from CPGRAMS
    if CPGRAMS_WEBHOOK_SECRET:
        if not verify_signature(body, signature, CPGRAMS_WEBHOOK_SECRET):
            raise HTTPException(401, "Invalid signature")

    data = json.loads(body)
    grievance_id = data["grievanceId"]   # their ticket ID
    new_status   = data["status"]        # their status string
    remarks      = data.get("remarks", "")

    logger.info("CPGRAMS webhook: %s → %s", grievance_id, new_status)

    # Step 2: Find our complaint by ticket_id
    # (gateway main.py handles DB update and user notification)
    # Publish as a pipeline event so existing status update logic handles it
    from . import db
    async with db.pool().acquire() as conn:
        row = await conn.fetchrow(
            "SELECT complaint_id, user_id FROM complaints WHERE ticket_id = $1",
            grievance_id
        )

    if row:
        from .main import _redis as _r
        await _r.publish("pipeline:all", json.dumps({
            "complaint_id": str(row["complaint_id"]),
            "stage":  "stage_10_status",
            "status": "completed",
            "payload": {
                "ticket_id":          grievance_id,
                "portal_status_raw":  new_status,
                "canonical_status":   map_status(new_status),
                "remarks":            remarks,
            }
        }))

    return {"received": True}


def map_status(raw: str) -> str:
    mapping = {
        "resolved": "RESOLVED", "closed": "RESOLVED",
        "rejected": "REJECTED", "under review": "IN_PROGRESS",
        "registered": "PENDING", "submitted": "PENDING",
    }
    return mapping.get(raw.lower(), "IN_PROGRESS")


# ── WhatsApp inbound webhook ──────────────────────────────────────────

@router.get("/whatsapp")
async def whatsapp_verify(request: Request):
    """Meta verifies the webhook subscription with a GET handshake."""
    qp = request.query_params
    if qp.get("hub.mode") == "subscribe" and qp.get("hub.verify_token") == WHATSAPP_VERIFY_TOKEN:
        return Response(content=qp.get("hub.challenge", ""), media_type="text/plain")
    raise HTTPException(403, "verify token mismatch")


def _public_url(request: Request) -> str:
    """Rebuild the public URL Twilio used when computing the signature.
    Behind cloudflared/ngrok the gateway sees http://localhost:8000 — but
    Twilio signs the public https tunnel URL. Honour X-Forwarded-* headers.
    """
    base = os.getenv("PUBLIC_BASE_URL", "").strip().rstrip("/")
    path = request.url.path
    if base:
        return base + path
    proto = request.headers.get("x-forwarded-proto") or request.url.scheme
    host  = request.headers.get("x-forwarded-host") or request.headers.get("host", "")
    return f"{proto}://{host}{path}"


def _verify_twilio(request: Request, params: dict) -> bool:
    """Validate Twilio's X-Twilio-Signature using the auth token."""
    sig = request.headers.get("X-Twilio-Signature", "")
    if not sig or not TWILIO_AUTH_TOKEN:
        return False
    url = _public_url(request)
    sorted_items = "".join(f"{k}{v}" for k, v in sorted(params.items()))
    raw = (url + sorted_items).encode("utf-8")
    digest = hmac.new(TWILIO_AUTH_TOKEN.encode("utf-8"), raw, hashlib.sha1).digest()
    import base64
    expected = base64.b64encode(digest).decode()
    ok = hmac.compare_digest(expected, sig)
    if not ok:
        logger.warning("Twilio sig mismatch · url_used=%s sig_in=%s expected=%s",
                       url, sig[:12] + "…", expected[:12] + "…")
    return ok


@router.post("/whatsapp")
async def whatsapp_inbound(request: Request):
    """Handle inbound WhatsApp messages from Twilio (form) or Meta (JSON)."""
    from . import db
    from .audit import log_event

    content_type = request.headers.get("content-type", "")
    from_mobile = ""
    body_text   = ""

    if "application/json" in content_type:
        data = await request.json()
        try:
            entry = data["entry"][0]["changes"][0]["value"]
            msg = entry["messages"][0]
            from_mobile = "+" + msg["from"]
            if msg.get("type") == "text":
                body_text = msg["text"]["body"]
            elif msg.get("type") == "location":
                loc = msg["location"]
                body_text = f"__LOCATION__ {loc['latitude']},{loc['longitude']}"
        except (KeyError, IndexError):
            return {"received": True}
    else:
        form = await request.form()
        params = dict(form)
        if TWILIO_AUTH_TOKEN and not _verify_twilio(request, params):
            raise HTTPException(401, "Invalid Twilio signature")
        from_mobile = params.get("From", "").replace("whatsapp:", "").strip()
        body_text   = params.get("Body", "").strip()

    if not from_mobile or not body_text:
        return {"received": True}

    import re as _re
    digits_only = _re.sub(r"\D", "", from_mobile)
    mobile_local = digits_only[-10:] if len(digits_only) >= 10 else digits_only
    logger.info("WhatsApp inbound: %s → %r", from_mobile, body_text[:120])

    is_new_user = False
    async with db.pool().acquire() as conn:
        last10 = mobile_local[-10:]
        user = await conn.fetchrow(
            "SELECT id FROM users WHERE mobile LIKE $1 ORDER BY created_at DESC LIMIT 1",
            f"%{last10}",
        )
        if not user:
            user = await conn.fetchrow(
                """INSERT INTO users (name, email, mobile, password_hash)
                   VALUES ($1, $2, $3, $4)
                   ON CONFLICT (mobile) DO UPDATE SET mobile = EXCLUDED.mobile
                   RETURNING id""",
                "WhatsApp User",
                f"wa_{last10}@whatsapp.local",
                last10,
                "!",  # unsalted '!' is never a valid bcrypt hash — disables password login
            )
            is_new_user = True
            logger.info("auto-created WhatsApp user for mobile %s → %s", last10, user["id"])
        user_id = str(user["id"])

    if is_new_user:
        welcome = (
            "🙏 *Namaste! Margdarshan.ai mein aapka swagat hai.*\n\n"
            "Main aapki government grievance file karne, sahi portal par bhejne, aur status track karne mein madad karunga.\n\n"
            "🇮🇳 *Hindi, English, ya Hinglish* — kisi bhi bhasha mein likhein.\n\n"
            "📝 *Try kijiye:*\n"
            "• \"bijli 3 din se nahi aa rahi, Bhopal MP\"\n"
            "• \"paani nahi aa raha indore mein\"\n"
            "• \"garbage not collected since 5 days\"\n\n"
            "Apni shikayat abhi likhein 👇"
        )
        try:
            from .whatsapp import client as _wa_client
            await _wa_client().send(to=from_mobile, body=welcome)
            logger.info("sent welcome to new WhatsApp user %s", last10)
        except Exception as e:
            logger.warning("welcome send failed: %s", e)

    async with db.pool().acquire() as conn:
        resolved = await conn.fetchrow(
            """SELECT complaint_id, ticket_id FROM complaints
               WHERE user_id = $1 AND status = 'RESOLVED'
                 AND (feedback_received IS NULL OR feedback_received = '')
               ORDER BY updated_at DESC LIMIT 1""",
            user_id,
        )

    cleaned = body_text.strip()
    if resolved and cleaned in {"1", "2"}:
        from .main import _redis
        await _redis.lpush(
            "feedback_queue",
            json.dumps({
                "complaint_id": str(resolved["complaint_id"]),
                "ticket_id":    resolved["ticket_id"],
                "reply":        cleaned,
                "source":       "whatsapp",
            }),
        )
        try:
            async with db.pool().acquire() as conn:
                await conn.execute(
                    "UPDATE complaints SET feedback_received = $1 WHERE complaint_id = $2",
                    cleaned, resolved["complaint_id"],
                )
            await log_event(str(resolved["complaint_id"]), "whatsapp_feedback",
                            {"reply": cleaned}, actor=user_id)
        except Exception as e:
            logger.warning("whatsapp feedback persist failed: %s", e)
        return {"received": True, "kind": "feedback", "reply": cleaned}

    chatbot_url = os.getenv("CHATBOT_URL", "http://service-chatbot:8001")
    try:
        import httpx
        async with httpx.AsyncClient(timeout=15.0) as c:
            r = await c.post(
                f"{chatbot_url}/api/v1/chat",
                json={"user_id": user_id, "message": body_text,
                      "language_preference": "auto", "channel": "whatsapp"},
            )
            r.raise_for_status()
            reply = r.json().get("reply", "")
    except Exception as e:
        logger.warning("chatbot forward failed: %s", e)
        reply = ""

    if reply:
        from .whatsapp import client as _wa_client
        await _wa_client().send(to=from_mobile, body=reply)
    return {"received": True, "kind": "chat", "reply_len": len(reply)}
