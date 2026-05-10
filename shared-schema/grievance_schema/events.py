"""Pipeline events — flow through Redis pub/sub to the WebSocket layer."""

from datetime import datetime
from enum import Enum
from typing import Any, Optional
from pydantic import BaseModel, Field


class StageEnum(str, Enum):
    STAGE_0_CHAT = "stage_0_chat"
    STAGE_1_INTAKE = "stage_1_intake"
    STAGE_2_NLU = "stage_2_nlu"
    STAGE_3_CLASSIFY = "stage_3_classify"
    STAGE_4_TIER3 = "stage_4_tier3"
    STAGE_5_ROUTE = "stage_5_route"
    STAGE_6_FILLER = "stage_6_filler"
    STAGE_7_DEDUP = "stage_7_dedup"
    STAGE_8_SUBMIT = "stage_8_submit"
    STAGE_10_STATUS = "stage_10_status"


class EventStatusEnum(str, Enum):
    STARTED = "started"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


class PipelineEvent(BaseModel):
    complaint_id: str
    stage: StageEnum
    status: EventStatusEnum
    payload: dict[str, Any] = Field(default_factory=dict)
    error: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
