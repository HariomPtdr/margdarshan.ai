"""service-nlu — Stage 2 preprocessing.

Normalize, mask PII, extract keywords + domain hints, build text_for_classifier.
NER for LOCATION is INTENTIONALLY removed — location comes from map picker.
"""

import json
import logging
import os
from typing import Optional

import redis.asyncio as redis_async
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from grievance_schema import PipelineEvent, StageEnum

from .keywords import extract_keywords
from .normalize import normalize
from .pii import extract_pii

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

REDIS_HOST = os.getenv("REDIS_HOST", "redis")
REDIS_PORT = int(os.getenv("REDIS_PORT", "6379"))

app = FastAPI(title="service-nlu", version="1.0.0")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

_redis: Optional[redis_async.Redis] = None


@app.on_event("startup")
async def startup():
    global _redis
    _redis = redis_async.Redis(host=REDIS_HOST, port=REDIS_PORT, decode_responses=True)


@app.get("/healthz")
async def healthz():
    return {"status": "ok", "service": "nlu"}


class ProcessRequest(BaseModel):
    complaint_id: str
    text_raw: str
    language_hint: Optional[str] = None


@app.post("/api/v1/process")
async def process(req: ProcessRequest):
    await _publish(req.complaint_id, "started", {})

    text_norm = normalize(req.text_raw)
    pii, text_masked = extract_pii(text_norm)
    keywords, domain_hints = extract_keywords(text_norm)

    canonical_prefix_parts = []
    if domain_hints:
        canonical_prefix_parts.append(f"[DOMAIN:{','.join(domain_hints)}]")
    text_for_classifier = " ".join(canonical_prefix_parts + [text_masked]).strip()

    payload = {
        "text_normalized": text_norm,
        "text_for_classifier": text_for_classifier,
        "language": req.language_hint or "en",
        "entities": {
            "phone": pii.get("PHONE", []),
            "pincode": pii.get("PINCODE", []),
            "vehicle_no": pii.get("VEHICLE_NO", []),
            "aadhaar": pii.get("AADHAAR", []),
            "email": pii.get("EMAIL", []),
            "consumer_no": pii.get("CONSUMER_NO", []),
        },
        "keywords": keywords,
        "domain_hints": domain_hints,
    }

    await _publish(req.complaint_id, "completed", payload)
    return payload


async def _publish(complaint_id: str, status: str, payload: dict):
    event = PipelineEvent(
        complaint_id=complaint_id,
        stage=StageEnum.STAGE_2_NLU,
        status=status,
        payload=payload,
    )
    await _redis.publish(f"pipeline:{complaint_id}", event.model_dump_json())
    await _redis.publish("pipeline:all", event.model_dump_json())
