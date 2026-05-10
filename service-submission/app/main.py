"""service-submission — Stage 8 plug-and-play portal adapters.

POST /api/v1/submit              — submit complaint to portal via registered adapter
GET  /api/v1/status/{ticket_id}  — poll portal for ticket status
GET  /api/v1/adapters            — list registered portal adapters
"""

import logging
import os
from typing import Optional

import redis.asyncio as redis_async
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from grievance_schema import PipelineEvent, StageEnum

from .registry import get_adapter, registered_portals

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

REDIS_HOST = os.getenv("REDIS_HOST", "redis")
REDIS_PORT = int(os.getenv("REDIS_PORT", "6379"))

app = FastAPI(title="service-submission", version="2.0.0")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

_redis: Optional[redis_async.Redis] = None


@app.on_event("startup")
async def startup():
    global _redis
    _redis = redis_async.Redis(host=REDIS_HOST, port=REDIS_PORT, decode_responses=True)
    logger.info("Submission service ready. Registered adapters: %s", registered_portals())


@app.get("/healthz")
async def healthz():
    return {"status": "ok", "service": "submission", "adapters": registered_portals()}


@app.get("/api/v1/adapters")
async def list_adapters():
    return {"registered": registered_portals()}


class SubmitRequest(BaseModel):
    complaint_id: str
    portal_id: str
    portal_fields: dict         # collected by Stage 6 field collection
    uco_meta: dict = {}         # complaint_text, department, district, user_name, etc.


@app.post("/api/v1/submit")
async def submit(req: SubmitRequest):
    await _publish(req.complaint_id, "started", {"portal_id": req.portal_id})

    adapter = get_adapter(req.portal_id)
    logger.info("submit: complaint=%s portal=%s adapter=%s",
                req.complaint_id, req.portal_id, type(adapter).__name__)

    try:
        result = await adapter.submit(req.portal_fields, req.uco_meta)
    except Exception as e:
        logger.error("submit failed: complaint=%s portal=%s error=%s",
                     req.complaint_id, req.portal_id, e)
        await _publish(req.complaint_id, "failed", {"error": str(e), "portal_id": req.portal_id})
        raise HTTPException(502, f"Portal submission failed: {e}")

    payload = {
        "portal_ticket_id":  result.ticket_id,
        "portal_status_raw": result.portal_status_raw,
        "canonical_status":  result.canonical_status,
        "submitted_at":      result.submitted_at.isoformat(),
        "portal_url":        result.portal_url,
        "portal_id":         req.portal_id,
        "adapter":           type(adapter).__name__,
    }
    await _publish(req.complaint_id, "completed", payload)
    logger.info("submitted: complaint=%s ticket=%s", req.complaint_id, result.ticket_id)
    return payload


class StatusRequest(BaseModel):
    portal_id: str
    ticket_id: str


@app.post("/api/v1/status")
async def fetch_status(req: StatusRequest):
    adapter = get_adapter(req.portal_id)
    try:
        result = await adapter.fetch_status(req.ticket_id)
    except Exception as e:
        raise HTTPException(502, f"Status fetch failed: {e}")

    return {
        "ticket_id":         result.ticket_id,
        "portal_status_raw": result.portal_status_raw,
        "canonical_status":  result.canonical_status,
        "last_updated":      result.last_updated.isoformat(),
        "remarks":           result.remarks,
        "adapter":           type(adapter).__name__,
    }


async def _publish(complaint_id: str, status: str, payload: dict):
    event = PipelineEvent(
        complaint_id=complaint_id,
        stage=StageEnum.STAGE_8_SUBMIT,
        status=status,
        payload=payload,
    )
    await _redis.publish(f"pipeline:{complaint_id}", event.model_dump_json())
    await _redis.publish("pipeline:all", event.model_dump_json())
