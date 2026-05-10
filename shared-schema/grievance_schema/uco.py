"""UCO — Unified Complaint Object. Single source of truth across services."""

from datetime import datetime
from enum import Enum
from typing import Optional
from pydantic import BaseModel, Field


class LanguageEnum(str, Enum):
    EN = "en"
    HI = "hi"
    HINGLISH = "hinglish"


class PriorityEnum(str, Enum):
    LOW = "Low"
    MED = "Med"
    HIGH = "High"
    CRITICAL = "Critical"


class SentimentEnum(str, Enum):
    NEUTRAL = "Neutral"
    FRUSTRATED = "Frustrated"
    DISTRESSED = "Distressed"


class CanonicalStatusEnum(str, Enum):
    DRAFT = "DRAFT"
    PENDING = "PENDING"
    IN_PROGRESS = "IN_PROGRESS"
    AWAITING_USER = "AWAITING_USER"
    RESOLVED = "RESOLVED"
    ESCALATED = "ESCALATED"
    REJECTED = "REJECTED"


class LocationData(BaseModel):
    """From map picker — never extracted from chat text."""
    lat: float
    lon: float
    pincode: str
    ward: Optional[str] = None
    ward_id: Optional[str] = None
    district: str
    state: str
    address_text: str
    map_provider: str = "mappls"


class Entities(BaseModel):
    """Extracted from chat text by Stage 2 NLU. Location intentionally absent."""
    person: list[str] = []
    organization: list[str] = []
    duration: list[str] = []
    infrastructure: list[str] = []
    phone: list[str] = []
    consumer_no: list[str] = []
    account_no: list[str] = []
    vehicle_no: list[str] = []
    pincode: list[str] = []
    aadhaar: list[str] = []
    email: list[str] = []


class Classification(BaseModel):
    """Output of Stage 3 multi-head classifier."""
    department: str
    sub_category: str
    priority: PriorityEnum
    sentiment: SentimentEnum
    confidence: float = Field(..., ge=0.0, le=1.0)
    tier3_used: bool = False


class Portal(BaseModel):
    """Output of Stage 5 routing."""
    portal_id: str
    portal_name: str
    jurisdiction_level: str       # municipal | district | state | national
    required_fields: list[str] = []
    collected_fields: dict = {}


class Status(BaseModel):
    """Output of Stage 10 tracker."""
    portal_ticket_id: Optional[str] = None
    portal_status_raw: Optional[str] = None
    canonical_status: CanonicalStatusEnum = CanonicalStatusEnum.DRAFT
    last_polled_at: Optional[datetime] = None


class UCO(BaseModel):
    """Single object that flows through the pipeline.

    Each stage reads in a UCO, writes its outputs back, returns the same UCO.
    """
    complaint_id: str
    user_id: str
    session_id: str

    text_raw: str
    text_normalized: Optional[str] = None
    text_for_classifier: Optional[str] = None
    language: Optional[LanguageEnum] = None

    location: Optional[LocationData] = None
    entities: Entities = Field(default_factory=Entities)
    keywords: list[str] = []
    domain_hints: list[str] = []

    classification: Optional[Classification] = None
    portal: Optional[Portal] = None
    status: Status = Field(default_factory=Status)

    created_at: datetime = Field(default_factory=datetime.utcnow)
    submitted_at: Optional[datetime] = None
    resolved_at: Optional[datetime] = None
