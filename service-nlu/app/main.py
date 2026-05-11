"""service-nlu — Stage 2 preprocessing + Layer 2 conversation brain.

GET  /healthz                    — health check
POST /api/v1/process             — Stage 2: normalize, mask PII, extract keywords (Layer 3 enhanced)
POST /api/v1/converse            — Layer 2: manage conversation state, decide what to ask
DELETE /api/v1/converse/{user_id} — reset conversation session
"""

import asyncio
import json
import logging
import os
import uuid
from typing import Optional

import anthropic
import redis.asyncio as redis_async
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from grievance_schema import PipelineEvent, StageEnum

from .keywords import extract_keywords
from .normalize import normalize
from .pii import extract_pii
from .session import store as conv_store, ConvSession
from .state_machine import StateMachine
from .nlu_extractor import extract_intent

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

REDIS_HOST = os.getenv("REDIS_HOST", "redis")
REDIS_PORT = int(os.getenv("REDIS_PORT", "6379"))
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")
CLAUDE_MODEL = os.getenv("CLAUDE_MODEL", "claude-haiku-4-5")

# Known Indian states for location extraction
INDIAN_STATES = {
    "andhra pradesh", "arunachal pradesh", "assam", "bihar", "chhattisgarh",
    "goa", "gujarat", "haryana", "himachal pradesh", "jharkhand", "karnataka",
    "kerala", "madhya pradesh", "maharashtra", "manipur", "meghalaya", "mizoram",
    "nagaland", "odisha", "punjab", "rajasthan", "sikkim", "tamil nadu", "telangana",
    "tripura", "uttar pradesh", "uttarakhand", "west bengal", "delhi", "jammu",
    "kashmir", "ladakh", "chandigarh", "puducherry", "andaman", "nicobar",
    "dadra", "daman", "lakshadweep",
}

# Common Indian cities/districts
INDIAN_CITIES = {
    "mumbai", "delhi", "bangalore", "bengaluru", "hyderabad", "chennai", "kolkata",
    "pune", "ahmedabad", "surat", "jaipur", "lucknow", "kanpur", "nagpur", "indore",
    "thane", "bhopal", "visakhapatnam", "patna", "vadodara", "ghaziabad", "ludhiana",
    "agra", "nashik", "faridabad", "meerut", "rajkot", "varanasi", "srinagar",
    "aurangabad", "dhanbad", "amritsar", "navi mumbai", "allahabad", "howrah",
    "gwalior", "jabalpur", "coimbatore", "vijayawada", "jodhpur", "madurai",
    "raipur", "kota", "chandigarh", "guwahati", "solapur", "hubli", "dharwad",
    "bareilly", "moradabad", "mysore", "mysuru", "ranchi", "jalandhar", "tiruchirappalli",
    "bhubaneswar", "salem", "warangal", "thiruvananthapuram", "guntur", "bhiwandi",
    "saharanpur", "gorakhpur", "bikaner", "amravati", "noida", "jamshedpur",
    "bhilai", "cuttack", "firozabad", "kochi", "ernakulam", "nellore", "ajmer",
}

app = FastAPI(title="service-nlu", version="2.0.0")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

_redis: Optional[redis_async.Redis] = None

# State machine singleton — Python controls all transitions; LLM only for NLU
_state_machine = StateMachine(nlu_extract_fn=extract_intent)


@app.on_event("startup")
async def startup():
    global _redis
    _redis = redis_async.Redis(host=REDIS_HOST, port=REDIS_PORT, decode_responses=True)


@app.get("/healthz")
async def healthz():
    return {"status": "ok", "service": "nlu"}


# ── Stage 2 / Layer 3: NLU processing pipeline endpoint ───────────────────────

class ProcessRequest(BaseModel):
    complaint_id: str
    text_raw: str
    language_hint: Optional[str] = None


class NLUResponse(BaseModel):
    complaint_id: str
    # Core Stage 2 fields
    text_raw: str
    text_normalized: str
    text_for_classifier: str
    language: str
    domain_hints: list[str]
    keywords: list[str]
    entities: dict
    # Layer 3 multilingual fields
    text_en: str
    text_hi: str
    text_hinglish: str
    language_detected: str  # en | hi | hinglish
    state: Optional[str]
    city: Optional[str]
    source: str
    multi_domain: bool


def _extract_location_from_data(keywords: list[str], entities: dict) -> tuple[Optional[str], Optional[str]]:
    """Extract Indian state and city/district from keywords and entities."""
    state_found: Optional[str] = None
    city_found: Optional[str] = None

    # Check entities for location data first
    location_fields = entities.get("location", []) or []
    all_location_text = " ".join(location_fields).lower() if location_fields else ""

    # Build combined text to search through
    all_text = " ".join(keywords).lower() + " " + all_location_text

    # Check for states
    for state in INDIAN_STATES:
        if state in all_text:
            state_found = state.title()
            break

    # Check for cities
    for city in INDIAN_CITIES:
        if city in all_text:
            city_found = city.title()
            break

    return state_found, city_found


async def _generate_multilingual(
    text: str,
    domain_hints: list[str],
    entities: dict,
) -> dict[str, str]:
    """Use Claude Haiku to generate EN/HI/Hinglish versions of the complaint text."""
    if not ANTHROPIC_API_KEY:
        return {"text_en": text, "text_hi": "", "text_hinglish": text}

    domain = ", ".join(domain_hints) if domain_hints else "general"
    prompt = (
        f'Given this Indian complaint text: "{text}"\n'
        f"Domain: {domain}\n"
        "Generate all 3 versions. Return ONLY JSON:\n"
        "{\n"
        '  "text_en": "English translation/version of the complaint",\n'
        '  "text_hi": "Hindi translation in Devanagari script",\n'
        '  "text_hinglish": "Hinglish version in Roman script"\n'
        "}"
    )

    try:
        client = anthropic.AsyncAnthropic(api_key=ANTHROPIC_API_KEY)
        response = await asyncio.wait_for(
            client.messages.create(
                model=CLAUDE_MODEL,
                max_tokens=512,
                messages=[{"role": "user", "content": prompt}],
            ),
            timeout=10.0,
        )
        raw = response.content[0].text.strip()
        # Strip markdown code fences if present
        if raw.startswith("```"):
            raw = raw.split("```")[1]
            if raw.startswith("json"):
                raw = raw[4:]
        result = json.loads(raw)
        return {
            "text_en": result.get("text_en", text),
            "text_hi": result.get("text_hi", ""),
            "text_hinglish": result.get("text_hinglish", text),
        }
    except Exception as exc:
        logger.warning("Multilingual generation failed: %s", exc)
        return {"text_en": text, "text_hi": "", "text_hinglish": text}


def _detect_language(text: str, language_hint: Optional[str]) -> str:
    """Detect whether text is English, Hindi, or Hinglish."""
    if language_hint in ("en", "hi", "hinglish"):
        return language_hint
    # Heuristic: check for Devanagari script characters
    devanagari_count = sum(1 for c in text if "ऀ" <= c <= "ॿ")
    if devanagari_count > 3:
        return "hi"
    # Check for common English words
    lower = text.lower()
    english_markers = ["the", "is", "my", "i ", "we ", "please", "not", "has", "have"]
    english_hits = sum(1 for m in english_markers if m in lower)
    if english_hits >= 2:
        return "en"
    return "hinglish"


@app.post("/api/v1/process", response_model=NLUResponse)
async def process(req: ProcessRequest):
    await _publish(req.complaint_id, "started", {})

    text_norm = normalize(req.text_raw)
    pii, text_masked = extract_pii(text_norm)
    keywords, domain_hints = extract_keywords(text_norm)

    canonical_prefix_parts = []
    if domain_hints:
        canonical_prefix_parts.append(f"[DOMAIN:{','.join(domain_hints)}]")
    text_for_classifier = " ".join(canonical_prefix_parts + [text_masked]).strip()

    entities = {
        "phone": pii.get("PHONE", []),
        "pincode": pii.get("PINCODE", []),
        "vehicle_no": pii.get("VEHICLE_NO", []),
        "aadhaar": pii.get("AADHAAR", []),
        "email": pii.get("EMAIL", []),
        "consumer_no": pii.get("CONSUMER_NO", []),
    }

    # Layer 3: language detection
    language_detected = _detect_language(req.text_raw, req.language_hint)

    # Layer 3: location extraction
    state_detected, city_detected = _extract_location_from_data(keywords, entities)

    # Layer 3: multilingual generation (async, 10s timeout)
    multilingual = await _generate_multilingual(text_norm, domain_hints, entities)

    # Layer 3: multi-domain detection (2+ domain hints)
    multi_domain = len(domain_hints) >= 2

    payload = {
        "complaint_id": req.complaint_id,
        "text_raw": req.text_raw,
        "text_normalized": text_norm,
        "text_for_classifier": text_for_classifier,
        "language": req.language_hint or language_detected,
        "entities": entities,
        "keywords": keywords,
        "domain_hints": domain_hints,
        # Layer 3 fields
        "text_en": multilingual["text_en"],
        "text_hi": multilingual["text_hi"],
        "text_hinglish": multilingual["text_hinglish"],
        "language_detected": language_detected,
        "state": state_detected,
        "city": city_detected,
        "source": "web",
        "multi_domain": multi_domain,
    }

    await _publish(req.complaint_id, "completed", payload)
    return NLUResponse(**payload)


async def _publish(complaint_id: str, status: str, payload: dict):
    event = PipelineEvent(
        complaint_id=complaint_id,
        stage=StageEnum.STAGE_2_NLU,
        status=status,
        payload=payload,
    )
    await _redis.publish(f"pipeline:{complaint_id}", event.model_dump_json())
    await _redis.publish("pipeline:all", event.model_dump_json())


# ── Layer 2: Conversation brain (new) ─────────────────────────────────────────

class ConverseRequest(BaseModel):
    user_id: str
    message: str
    session_id: Optional[str] = None
    language_preference: Optional[str] = "hinglish"


class ConverseResponse(BaseModel):
    reply: str
    session_id: str
    state: str
    needs_location_pin: bool = False
    is_complete: bool = False          # True when chatbot should trigger pipeline
    complaint_buffer: str = ""         # structured description when complete
    language: str = "hinglish"
    slots: dict = {}


@app.post("/api/v1/converse", response_model=ConverseResponse)
async def converse(req: ConverseRequest):
    """Layer 2 brain: manages conversation state, decides what to ask next.
    Called by chatbot (Layer 1) for EVERY user message."""
    session = await conv_store.load(req.user_id)
    if session is None:
        session = ConvSession(
            user_id=req.user_id,
            session_id=req.session_id or str(uuid.uuid4()),
            language=req.language_preference or "hinglish",
        )
    elif req.language_preference:
        session.language = req.language_preference

    # Run state machine
    result = await _state_machine.process(session, req.message)
    await conv_store.save(session)

    is_complete = result.get("ready_for_pipeline", False)

    return ConverseResponse(
        reply=result["reply"],
        session_id=session.session_id,
        state=result["state"],
        needs_location_pin=result.get("needs_location_pin", False),
        is_complete=is_complete,
        complaint_buffer=session.complaint_buffer if hasattr(session, "complaint_buffer") else "",
        language=session.language,
        slots=session.slots,
    )


@app.delete("/api/v1/converse/{user_id}")
async def reset_converse(user_id: str):
    """Reset the NLU conversation session for a user."""
    await conv_store.delete(user_id)
    return {"status": "ok"}
