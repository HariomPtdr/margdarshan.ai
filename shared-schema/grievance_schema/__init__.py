"""Shared schema for grievance-system services.

The UCO (Unified Complaint Object) is the contract every service speaks.
Schema changes require a version bump in setup.py.
"""

from .uco import UCO, LocationData, Entities, Classification, Portal, Status
from .chat import ChatRequest, ChatResponse, ChatDecision, IntentEnum, StateEnum
from .events import PipelineEvent, StageEnum

__all__ = [
    "UCO", "LocationData", "Entities", "Classification", "Portal", "Status",
    "ChatRequest", "ChatResponse", "ChatDecision", "IntentEnum", "StateEnum",
    "PipelineEvent", "StageEnum",
]

__version__ = "1.0.0"
