"""service-routing — Stage 5 portal lookup.

Receives classification output (dept tag + complaint_id).
Reads location from Redis (written by service-location).
Returns the best-matched portal and its required fields.

Hierarchy: Regional > State > Central. Dept tag is the primary filter.
"""

import json
import logging
import os
from typing import Optional

import redis.asyncio as redis_async
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from grievance_schema import PipelineEvent, StageEnum, Portal
from .portal_loader import load_portals, find_portal, portal_count

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

REDIS_HOST = os.getenv("REDIS_HOST", "redis")
REDIS_PORT = int(os.getenv("REDIS_PORT", "6379"))

app = FastAPI(title="service-routing", version="2.0.0")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

_redis: Optional[redis_async.Redis] = None


@app.on_event("startup")
async def startup():
    global _redis
    load_portals()
    logger.info("Portal registry loaded: %d portals", portal_count())
    _redis = redis_async.Redis(host=REDIS_HOST, port=REDIS_PORT, decode_responses=True)


@app.get("/healthz")
async def healthz():
    return {"status": "ok", "service": "routing", "portals_loaded": portal_count()}


class RouteRequest(BaseModel):
    complaint_id: str
    department: str          # classifier_dept_tag, e.g. "ELECTRICITY"
    sub_category: Optional[str] = None
    priority: Optional[str] = None


@app.post("/api/v1/route", response_model=Portal)
async def route(req: RouteRequest):
    await _publish(req.complaint_id, "started", {})

    location = await _get_location(req.complaint_id)
    if not location:
        raise HTTPException(status_code=422, detail="Location not found for complaint — run service-location first")

    district = location.get("district", "")
    state = location.get("state", "")

    entry = find_portal(req.department, district, state)

    # Map CSV portal_level to UCO jurisdiction_level vocabulary
    level_map = {"Regional": "municipal", "State": "state", "Central": "national"}
    jurisdiction_level = level_map.get(entry.portal_level, entry.portal_level.lower())

    portal = Portal(
        portal_id=entry.portal_id,
        portal_name=entry.portal_name,
        jurisdiction_level=jurisdiction_level,
        required_fields=entry.required_fields,
        collected_fields={},
    )

    payload = portal.model_dump()
    payload["portal_website"] = entry.website
    payload["helpline"] = entry.helpline
    payload["whatsapp"] = entry.whatsapp

    await _publish(req.complaint_id, "completed", payload)
    logger.info(
        "complaint=%s dept=%s district=%s → portal=%s (%s)",
        req.complaint_id, req.department, district, entry.portal_id, entry.portal_level,
    )
    return portal


@app.get("/api/v1/portals")
async def list_portals():
    from .portal_loader import _portals
    return [
        {
            "portal_id": p.portal_id,
            "portal_name": p.portal_name,
            "portal_level": p.portal_level,
            "authority_name": p.authority_name,
            "covers_districts": p.covers_districts,
            "website": p.website,
            "has_online": p.has_online,
            "classifier_dept_tags": p.classifier_dept_tags,
            "complaint_categories": p.complaint_categories,
            "required_fields": p.required_fields,
            "helpline": p.helpline,
            "whatsapp": p.whatsapp,
        }
        for p in _portals
    ]


@app.get("/api/v1/portals/{portal_id}")
async def get_portal(portal_id: str):
    from .portal_loader import get_by_id
    entry = get_by_id(portal_id)
    if not entry:
        raise HTTPException(status_code=404, detail=f"Portal {portal_id} not found")
    return {
        "portal_id": entry.portal_id,
        "portal_name": entry.portal_name,
        "portal_level": entry.portal_level,
        "authority_name": entry.authority_name,
        "website": entry.website,
        "has_online": entry.has_online,
        "required_fields": entry.required_fields,
        "helpline": entry.helpline,
        "whatsapp": entry.whatsapp,
    }


async def _get_location(complaint_id: str) -> Optional[dict]:
    raw = await _redis.get(f"complaint:{complaint_id}:location")
    return json.loads(raw) if raw else None


async def _publish(complaint_id: str, status: str, payload: dict):
    event = PipelineEvent(
        complaint_id=complaint_id,
        stage=StageEnum.STAGE_5_ROUTE,
        status=status,
        payload=payload,
    )
    await _redis.publish(f"pipeline:{complaint_id}", event.model_dump_json())
    await _redis.publish("pipeline:all", event.model_dump_json())
