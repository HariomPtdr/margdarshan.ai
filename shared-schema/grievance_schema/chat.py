"""Chat-related schemas — request/response contracts for service-chatbot."""

from enum import Enum
from typing import Optional
from pydantic import BaseModel


class IntentEnum(str, Enum):
    GREETING = "GREETING"
    SMALLTALK = "SMALLTALK"
    COMPLAINT_NEW = "COMPLAINT_NEW"
    COMPLAINT_CONTINUE = "COMPLAINT_CONTINUE"
    STATUS_CHECK = "STATUS_CHECK"
    CLARIFICATION_REPLY = "CLARIFICATION_REPLY"
    ABUSE = "ABUSE"
    OFF_TOPIC = "OFF_TOPIC"


class StateEnum(str, Enum):
    IDLE = "IDLE"
    COLLECTING = "COLLECTING"
    READY = "READY"
    AWAITING_LOCATION = "AWAITING_LOCATION"
    ASK_MORE = "ASK_MORE"
    CONFIRMING = "CONFIRMING"
    FIELD_COLLECTION = "FIELD_COLLECTION"   # collecting portal-required fields
    SUBMITTED = "SUBMITTED"


class ChatRequest(BaseModel):
    user_id: str
    session_id: Optional[str] = None
    message: str
    language_preference: Optional[str] = None  # ui language hint


class ChatDecision(BaseModel):
    """Structured JSON returned by Claude inside Stage 0."""
    intent: IntentEnum
    language_detected: str
    complaint_buffer: str
    completeness_score: int
    ready_for_pipeline: bool
    next_state: StateEnum
    is_new_complaint: bool
    needs_location_pin: bool
    abandoned_signal: bool = False
    multiple_complaints_detected: bool = False
    reply_to_user: str


class ChatResponse(BaseModel):
    reply: str
    session_id: str
    complaint_id: Optional[str] = None
    intent: IntentEnum
    state: StateEnum
    needs_location_pin: bool = False
    pipeline_triggered: bool = False
