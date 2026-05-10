"""service-classifier — Stage 3 multi-head MuRIL classifier.

Uses fine-tuned MuRIL + sklearn heads to predict:
  department, sub_category, sentiment, priority

Falls back to rule-based if model artifacts aren't present.
Returns needs_clarification=true + a question when department confidence < threshold.
"""

import logging
import os
from typing import Optional

import redis.asyncio as redis_async
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from grievance_schema import PipelineEvent, StageEnum
from .muril_predictor import predictor

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

REDIS_HOST = os.getenv("REDIS_HOST", "redis")
REDIS_PORT = int(os.getenv("REDIS_PORT", "6379"))

CRITICAL_KEYWORDS = {"fata", "burst", "fire", "electrocution", "death", "injury"}

DOMAIN_TO_DEPT = {
    "electricity": ("ELECTRICITY",        "Power outage"),
    "water":       ("WATER_SUPPLY",       "No water supply"),
    "roads":       ("ROADS",              "Pothole or road damage"),
    "waste":       ("SANITATION",         "Garbage not collected"),
    "police":      ("POLICE",             "Complaint registration"),
    "banking":     ("BANKING",            "Service issue"),
    "health":      ("HEALTH",             "Service issue"),
    "education":   ("EDUCATION_SCHOOL",   "Service issue"),
    "transport":   ("TRANSPORT_VEHICLE",  "Service issue"),
    "corruption":  ("CORRUPTION",         "Bribery or misconduct"),
    "agriculture": ("AGRICULTURE",        "Subsidy or scheme issue"),
    "pension":     ("PENSION_SOCIAL",     "Payment not received"),
    "ration":      ("FOOD_RATION",        "Ration card or FPS issue"),
    "cyber":       ("CYBER_CRIME",        "Online fraud"),
    "housing":     ("HOUSING_URBAN",      "Property or civic issue"),
}

app = FastAPI(title="service-classifier", version="2.0.0")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

_redis: Optional[redis_async.Redis] = None


@app.on_event("startup")
async def startup():
    global _redis
    _redis = redis_async.Redis(host=REDIS_HOST, port=REDIS_PORT, decode_responses=True)
    predictor.load()


@app.get("/healthz")
async def healthz():
    return {
        "status": "ok",
        "service": "classifier",
        "model": "muril" if predictor.ready else "rule-based",
    }


class ClassifyRequest(BaseModel):
    complaint_id: str
    text_normalized: Optional[str] = ""
    text_for_classifier: Optional[str] = ""
    domain_hints: list[str] = []
    keywords: list[str] = []
    language: Optional[str] = "en"


@app.post("/api/v1/classify")
async def classify(req: ClassifyRequest):
    await _publish(req.complaint_id, "started", {})
    result = _run_classifier(req)
    await _publish(req.complaint_id, "completed", result)
    return result


def _run_classifier(req: ClassifyRequest) -> dict:
    text = (req.text_normalized or req.text_for_classifier or "").strip()

    # Try MuRIL first.
    if predictor.ready and text:
        muril_result = predictor.predict(text)
        if muril_result:
            dept_label = muril_result["department"]["label"]
            dept_conf  = muril_result["department"]["confidence"]

            # If NLU domain_hints strongly disagree with MuRIL, trust the hints.
            # MuRIL was trained on formal English; Hinglish short texts may misfire.
            # Trust NLU domain_hints over MuRIL when the top MuRIL prediction
            # isn't already in the same domain family as the hint.
            hint_key = req.domain_hints[0].lower() if req.domain_hints else ""
            hint_dept_from_map, _ = DOMAIN_TO_DEPT.get(hint_key, ("", ""))
            muril_matches_hint = hint_dept_from_map and (
                hint_dept_from_map.upper() in dept_label.upper() or
                dept_label.upper() in hint_dept_from_map.upper()
            )
            if req.domain_hints and hint_dept_from_map and not muril_matches_hint:
                hint_dept, hint_sub = DOMAIN_TO_DEPT.get(
                    hint_key,
                    (dept_label, muril_result["sub_category"]["label"])
                )
                dept_label = hint_dept
                dept_conf  = 0.75   # synthetic confidence for hint override

            return {
                "department": dept_label,
                "sub_category": muril_result["sub_category"]["label"],
                "priority": muril_result["priority"]["label"],
                "sentiment": muril_result["sentiment"]["label"],
                "confidence": dept_conf,
                "needs_clarification": dept_conf < 0.40,
                "clarifying_question": muril_result["clarifying_question"],
                "top3_departments": muril_result["department"]["top3"],
                "tier3_used": False,
                "model": "muril+hint" if req.domain_hints and hint_dept_from_map and not muril_matches_hint else "muril",
            }

    # Rule-based fallback.
    return _rule_based(req)


def _rule_based(req: ClassifyRequest) -> dict:
    domain = req.domain_hints[0] if req.domain_hints else "electricity"
    dept, sub_cat = DOMAIN_TO_DEPT.get(domain, ("General Administration", "Other"))
    text = (req.text_normalized or "").lower()

    priority = "Med"
    if any(w in text for w in CRITICAL_KEYWORDS):
        priority = "Critical"
    elif any(w in text for w in ["urgent", "emergency", "jaldi", "abhi", "din", "days"]):
        priority = "High"

    sentiment = "Neutral"
    if any(w in text for w in ["pareshan", "tang", "frustrated", "angry"]):
        sentiment = "Frustrated"
    if any(w in text for w in ["help", "madad", "please", "kripya", "death", "injury"]):
        sentiment = "Distressed"

    confidence = 0.85 if req.domain_hints else 0.50
    return {
        "department": dept,
        "sub_category": sub_cat,
        "priority": priority,
        "sentiment": sentiment,
        "confidence": confidence,
        "needs_clarification": confidence < 0.40,
        "clarifying_question": None,
        "top3_departments": [],
        "tier3_used": False,
        "model": "rule-based",
    }


async def _publish(complaint_id: str, status: str, payload: dict):
    event = PipelineEvent(
        complaint_id=complaint_id,
        stage=StageEnum.STAGE_3_CLASSIFY,
        status=status,
        payload=payload,
    )
    await _redis.publish(f"pipeline:{complaint_id}", event.model_dump_json())
    await _redis.publish("pipeline:all", event.model_dump_json())
