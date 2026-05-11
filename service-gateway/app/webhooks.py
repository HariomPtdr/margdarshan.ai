"""Webhook receiver — govt portals push status updates to us here.

CPGRAMS calls: POST /api/v1/webhook/cpgrams
We verify signature → update DB → notify user
"""

import hashlib
import hmac
import json
import logging
import os
from fastapi import APIRouter, HTTPException, Request

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1/webhook", tags=["webhooks"])

CPGRAMS_WEBHOOK_SECRET = os.getenv("CPGRAMS_WEBHOOK_SECRET", "")


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
    from . import _redis, db
    async with db.pool().acquire() as conn:
        row = await conn.fetchrow(
            "SELECT complaint_id, user_id FROM complaints WHERE ticket_id = $1",
            grievance_id
        )

    if row:
        await _redis.publish("pipeline:all", json.dumps({
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
