"""service-chatbot — Stage 0 Conversation Manager + Stage 6 Field Collector.

POST /api/v1/chat                       — main chat entry point
POST /api/v1/field-collection/start     — gateway calls this after dedup to arm field collection
POST /api/v1/session/notify             — gateway calls this to set a pending notification
DELETE /api/v1/session/{user_id}        — reset session
GET  /api/v1/session/{user_id}          — debug, returns current session
"""

import json
import logging
import uuid
from datetime import datetime
from typing import Optional

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from grievance_schema import ChatRequest, ChatResponse, IntentEnum, StateEnum, PipelineEvent, StageEnum

from .chatbot import chatbot
from .config import config
from .session import Session, store
from .validators import validate

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="service-chatbot", version="2.0.0")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])


@app.get("/healthz")
async def healthz():
    return {"status": "ok", "service": "chatbot"}


@app.get("/api/v1/session/{user_id}")
async def get_session(user_id: str):
    session = await store.load(user_id)
    return session.to_dict() if session else {"empty": True}


@app.delete("/api/v1/session/{user_id}")
async def reset_session(user_id: str):
    await store.delete(user_id)
    return {"status": "ok"}


class RestoreSessionRequest(BaseModel):
    user_id: str
    complaint_id: str
    complaint_buffer: Optional[str] = ""
    state: Optional[str] = "COLLECTING"
    language_preference: Optional[str] = "hinglish"
    messages: list[dict] = []   # [{"role":"user"|"assistant","content":"..."}]


@app.post("/api/v1/session/restore")
async def restore_session(req: RestoreSessionRequest):
    """Rebuild a chatbot session from DB messages for an in-progress complaint.
    Called when user clicks an active (unsubmitted) complaint from history.
    """
    session = Session(
        user_id=req.user_id,
        language_preference=req.language_preference,
        state=req.state or "COLLECTING",
        complaint_id=req.complaint_id,
        complaint_buffer=req.complaint_buffer or "",
    )
    # Rebuild history from stored messages (cap to last 20 turns)
    for msg in req.messages[-config.MAX_HISTORY_TURNS * 2:]:
        session.history.append({"role": msg["role"], "content": msg["content"]})
    await store.save(session)
    return {"status": "ok", "session_id": session.session_id}


# ── Stage 6: Field Collection setup endpoints ─────────────────────────

class StartFieldCollectionRequest(BaseModel):
    user_id: str
    complaint_id: str
    portal_id: str
    portal_name: str
    required_fields: list[str]
    pre_filled: dict = {}               # fields already known from NER / location
    dedup_info: Optional[dict] = None   # populated when is_duplicate=True, is_same_user=False


@app.post("/api/v1/field-collection/start")
async def start_field_collection(req: StartFieldCollectionRequest):
    """Called by the gateway after Stage 7 (dedup) to arm the chatbot session
    for field collection. Returns the opening message so the gateway can
    push it to the WebSocket immediately."""

    session = await store.load(req.user_id)
    if not session:
        raise HTTPException(404, "Session not found — user must have an active session")

    # Skip fields already known from NER / location — only ask what's missing.
    already_known = req.pre_filled or {}
    pending = [f for f in req.required_fields if f not in already_known]

    session.state = StateEnum.FIELD_COLLECTION.value
    session.field_collection = {
        "complaint_id": req.complaint_id,
        "portal_id": req.portal_id,
        "portal_name": req.portal_name,
        "pending_fields": pending,
        "collected_fields": dict(already_known),   # start with pre-filled values
        "dedup_info": req.dedup_info,
        "retry_count": 0,
    }

    lang = session.language_preference or "hinglish"
    dedup = req.dedup_info or {}
    first = pending[0] if pending else ""

    # If every field was pre-filled, skip straight to done.
    if not pending:
        session.state = StateEnum.SUBMITTED.value
        await store.save(session)
        await _publish_pipeline_event(
            complaint_id=req.complaint_id,
            stage=StageEnum.STAGE_6_FILLER,
            status="completed",
            payload={
                "user_id": req.user_id,
                "session_id": session.session_id,
                "portal_id": req.portal_id,
                "portal_name": req.portal_name,
                "portal_fields": already_known,
                "dedup_info": req.dedup_info,
            },
        )
        done = _done_reply(lang, req.portal_name)
        return {"opening_message": done, "first_field": None, "pre_filled_count": len(already_known)}

    prefill_count = len(already_known)
    prefill_note = ""
    if prefill_count:
        if lang == "hi":
            prefill_note = f" ({prefill_count} जानकारी आपकी शिकायत से पहले से मिल गई।)"
        elif lang == "en":
            prefill_note = f" ({prefill_count} field(s) already filled from your complaint.)"
        else:
            prefill_note = f" ({prefill_count} fields aapki shikayat se pehle se bhar gayi.)"

    if dedup.get("is_duplicate") and not dedup.get("is_same_user"):
        count = dedup.get("duplicate_count", 0)
        dept  = dedup.get("department", "")
        dist  = dedup.get("district", "")
        if lang == "hi":
            opening = (
                f"ध्यान दें: {dist} में '{dept}' की {count} ऐसी ही शिकायत पहले से दर्ज है।\n"
                f"हम फिर भी आपकी शिकायत register करेंगे और सरकार को बताएंगे कि यह समस्या {count+1} लोगों को है।\n"
                f"{prefill_note}\n\n"
                f"अब '{req.portal_name}' के लिए जानकारी चाहिए। पहला सवाल:\n{first}"
            )
        elif lang == "en":
            opening = (
                f"Note: {count} similar complaint(s) for '{dept}' already exist in {dist}.\n"
                f"We will still register yours and show the government this affects {count+1} people.\n"
                f"{prefill_note}\n\n"
                f"I need a few details for {req.portal_name}. First:\n{first}"
            )
        else:
            opening = (
                f"Dhyan dein: {dist} mein '{dept}' ki {count} aisi hi shikayat pehle se darj hai.\n"
                f"Hum phir bhi aapki shikayat register karenge aur sarkar ko batayenge ki yeh {count+1} logon ki samasya hai.\n"
                f"{prefill_note}\n\n"
                f"Ab '{req.portal_name}' ke liye kuch details chahiye. Pehla sawaal:\n{first}"
            )
    else:
        if lang == "hi":
            opening = (
                f"शिकायत तैयार है।{prefill_note} अब '{req.portal_name}' पोर्टल के लिए थोड़ी जानकारी चाहिए।\n\n"
                f"पहला सवाल:\n{first}"
            )
        elif lang == "en":
            opening = (
                f"Complaint noted.{prefill_note} I need a few details for {req.portal_name}.\n\n"
                f"First:\n{first}"
            )
        else:
            opening = (
                f"Shikayat ready hai!{prefill_note} Ab '{req.portal_name}' portal ke liye kuch details chahiye.\n\n"
                f"Pehla sawaal:\n{first}"
            )

    await store.save(session)
    logger.info(
        "field_collection armed: user=%s complaint=%s portal=%s pending=%d pre_filled=%d",
        req.user_id, req.complaint_id, req.portal_id, len(pending), prefill_count,
    )
    return {"opening_message": opening, "first_field": first, "pre_filled_count": prefill_count}


class NotifyRequest(BaseModel):
    user_id: str
    message: str


@app.post("/api/v1/session/notify")
async def session_notify(req: NotifyRequest):
    """Gateway calls this to queue a bot message that is delivered on the
    user's very next chat turn (without waiting for an LLM call)."""
    session = await store.load(req.user_id)
    if not session:
        raise HTTPException(404, "Session not found")
    session.pending_notification = req.message
    await store.save(session)
    return {"status": "ok"}


# ── Main chat handler ──────────────────────────────────────────────────

@app.post("/api/v1/chat", response_model=ChatResponse)
async def chat(req: ChatRequest):
    if len(req.message) > config.MAX_MESSAGE_LENGTH:
        raise HTTPException(400, "Message too long")
    if len(req.message.strip()) == 0:
        raise HTTPException(400, "Empty message")

    if not await store.rate_limit_check(req.user_id):
        return ChatResponse(
            reply="Aap zyada messages bhej rahe hain. Kripya thodi der baad try karein.",
            session_id=req.session_id or str(uuid.uuid4()),
            intent=IntentEnum.OFF_TOPIC,
            state=StateEnum.IDLE,
        )

    session = await store.load(req.user_id)
    if session is None:
        session = Session(user_id=req.user_id, language_preference=req.language_preference)
    elif req.language_preference:
        session.language_preference = req.language_preference

    # ── Priority 1a: feedback reply ("1" or "2") from a resolved complaint ──
    if session.state == StateEnum.SUBMITTED.value and req.message.strip() in ("1", "2"):
        lang = session.language_preference or "hinglish"
        if req.message.strip() == "1":
            if lang == "hi":
                reply = "धन्यवाद! आपकी प्रतिक्रिया दर्ज कर ली गई है। अगर भविष्य में कोई समस्या हो तो हमें बताएं।"
            elif lang == "en":
                reply = "Thank you! Your feedback has been recorded. Feel free to reach out if you face any issues."
            else:
                reply = "Shukriya! Aapka feedback note kar liya gaya. Aage koi dikkat ho toh batayein."
        else:
            if lang == "hi":
                reply = "हमें खेद है कि समस्या हल नहीं हुई। आपकी शिकायत escalate की जा रही है। हम जल्द संपर्क करेंगे।"
            elif lang == "en":
                reply = "We're sorry the issue wasn't resolved. Your complaint is being escalated. We will follow up soon."
            else:
                reply = "Maafi chahte hain ki samasya haal nahi hui. Aapki shikayat escalate ho rahi hai. Jald follow up milega."
        session.history.append({"role": "user", "content": req.message})
        session.history.append({"role": "assistant", "content": reply})
        await store.save(session)
        return ChatResponse(
            reply=reply,
            session_id=session.session_id,
            complaint_id=session.complaint_id,
            intent=IntentEnum.COMPLAINT_CONTINUE,
            state=StateEnum.SUBMITTED,
        )

    # ── Priority 1b: deliver a pending notification (e.g. same-user duplicate) ──
    if session.pending_notification:
        msg = session.pending_notification
        session.pending_notification = None
        session.history.append({"role": "user", "content": req.message})
        session.history.append({"role": "assistant", "content": msg})
        await store.save(session)
        return ChatResponse(
            reply=msg,
            session_id=session.session_id,
            complaint_id=session.complaint_id,
            intent=IntentEnum.COMPLAINT_CONTINUE,
            state=StateEnum(session.state),
        )

    # ── Priority 2: field collection mode ─────────────────────────────────────
    if session.state == StateEnum.FIELD_COLLECTION.value and session.field_collection:
        return await _handle_field_collection(req, session)

    # ── Normal intake flow ─────────────────────────────────────────────────────
    decision = await chatbot.call(
        history=session.history,
        new_message=req.message,
        language_preference=session.language_preference,
        current_state=session.state,
        complaint_buffer=session.complaint_buffer,
    )

    session.history.append({"role": "user", "content": req.message})
    session.history.append({"role": "assistant", "content": decision["reply_to_user"]})
    session.state = decision["next_state"]
    session.complaint_buffer = decision["complaint_buffer"]

    complaint_id = session.complaint_id
    pipeline_triggered = False

    if decision["intent"] == IntentEnum.ABUSE.value:
        await _log_abuse(req.user_id, req.message)

    elif decision["ready_for_pipeline"]:
        is_new_intent = decision["intent"] == IntentEnum.COMPLAINT_NEW.value
        if (is_new_intent and decision.get("is_new_complaint")) or not complaint_id:
            complaint_id = str(uuid.uuid4())
            session.complaint_id = complaint_id

        await _publish_pipeline_event(
            complaint_id=complaint_id,
            stage=StageEnum.STAGE_0_CHAT,
            status="completed",
            payload={
                "user_id": req.user_id,
                "session_id": session.session_id,
                "complaint_buffer": decision["complaint_buffer"],
                "language": decision["language_detected"],
                "needs_location_pin": decision["needs_location_pin"],
            },
        )
        pipeline_triggered = True

    await store.save(session)

    return ChatResponse(
        reply=decision["reply_to_user"],
        session_id=session.session_id,
        complaint_id=complaint_id,
        intent=IntentEnum(decision["intent"]),
        state=StateEnum(decision["next_state"]),
        needs_location_pin=decision["needs_location_pin"],
        pipeline_triggered=pipeline_triggered,
    )


# ── Field collection turn handler ──────────────────────────────────────

async def _handle_field_collection(req: ChatRequest, session: Session) -> ChatResponse:
    fc = session.field_collection
    pending: list[str] = fc.get("pending_fields", [])
    collected: dict   = fc.get("collected_fields", {})

    if not pending:
        # All fields already collected — should not normally reach here.
        reply = _done_reply(session.language_preference, fc.get("portal_name", "portal"))
        session.state = StateEnum.SUBMITTED.value
        await store.save(session)
        return ChatResponse(
            reply=reply,
            session_id=session.session_id,
            complaint_id=session.complaint_id,
            intent=IntentEnum.COMPLAINT_CONTINUE,
            state=StateEnum.SUBMITTED,
        )

    current_field = pending[0]
    next_field     = pending[1] if len(pending) > 1 else None

    extraction = await chatbot.extract_field(
        field_name=current_field,
        user_message=req.message,
        language_preference=session.language_preference or "hinglish",
        next_field=next_field,
    )

    session.history.append({"role": "user", "content": req.message})
    session.history.append({"role": "assistant", "content": extraction["reply"]})

    if extraction["extracted"] is not None:
        value = extraction["extracted"]
        is_valid, hint = validate(current_field, value)

        if not is_valid:
            retries = fc.get("retry_count", 0)
            if retries < 2:
                # Invalid — ask again with a format hint, but don't loop forever.
                fc["retry_count"] = retries + 1
                lang = session.language_preference or "hinglish"
                if lang == "hi":
                    retry_msg = f"'{value}' सही format में नहीं है। {hint}। कृपया फिर से बताएं।"
                elif lang == "en":
                    retry_msg = f"'{value}' doesn't look right. Expected: {hint}. Please try again."
                else:
                    retry_msg = f"'{value}' sahi nahi laga. {hint}. Dobara try karein."
                session.history[-1]["content"] = retry_msg
                await store.save(session)
                return ChatResponse(
                    reply=retry_msg,
                    session_id=session.session_id,
                    complaint_id=session.complaint_id,
                    intent=IntentEnum.COMPLAINT_CONTINUE,
                    state=StateEnum.FIELD_COLLECTION,
                )
            # After 2 failed attempts: accept as-is and move on.

        fc["retry_count"] = 0
        collected[current_field] = value
        pending.pop(0)
        fc["collected_fields"] = collected
        fc["pending_fields"]   = pending

        if not pending:
            # ── All fields collected ──────────────────────────────────
            done_msg = _done_reply(session.language_preference, fc.get("portal_name", "portal"))
            session.history[-1]["content"] = done_msg   # replace last assistant msg
            session.state = StateEnum.SUBMITTED.value
            await store.save(session)

            await _publish_pipeline_event(
                complaint_id=session.complaint_id,
                stage=StageEnum.STAGE_6_FILLER,
                status="completed",
                payload={
                    "user_id": req.user_id,
                    "session_id": session.session_id,
                    "portal_id": fc.get("portal_id", ""),
                    "portal_name": fc.get("portal_name", ""),
                    "portal_fields": collected,
                    "dedup_info": fc.get("dedup_info"),
                },
            )

            return ChatResponse(
                reply=done_msg,
                session_id=session.session_id,
                complaint_id=session.complaint_id,
                intent=IntentEnum.COMPLAINT_CONTINUE,
                state=StateEnum.SUBMITTED,
                pipeline_triggered=True,
            )
    else:
        # Value not extracted — session unchanged, ask again via extraction reply.
        pass

    await store.save(session)
    return ChatResponse(
        reply=extraction["reply"],
        session_id=session.session_id,
        complaint_id=session.complaint_id,
        intent=IntentEnum.COMPLAINT_CONTINUE,
        state=StateEnum.FIELD_COLLECTION,
    )


def _done_reply(lang: Optional[str], portal_name: str) -> str:
    if lang == "hi":
        return f"सभी जानकारी मिल गई। आपकी शिकायत '{portal_name}' पोर्टल पर submit की जा रही है।"
    if lang == "en":
        return f"All details collected. Your complaint is being submitted to {portal_name}."
    return f"Saari details aa gayi. Aapki shikayat '{portal_name}' portal par submit ho rahi hai."


# ── Helpers ─────────────────────────────────────────────────────────────

async def _log_abuse(user_id: str, message: str):
    r = await store.connect()
    await r.lpush(
        "abuse_log",
        json.dumps({"user_id": user_id, "message": message, "at": datetime.utcnow().isoformat()}),
    )


async def _publish_pipeline_event(complaint_id: str, stage: StageEnum, status: str, payload: dict):
    r = await store.connect()
    event = PipelineEvent(complaint_id=complaint_id, stage=stage, status=status, payload=payload)
    await r.publish(f"pipeline:{complaint_id}", event.model_dump_json())
    await r.publish("pipeline:all", event.model_dump_json())
