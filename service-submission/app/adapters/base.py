"""Abstract base class — every portal adapter implements these 4 methods."""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass
class SubmissionResult:
    ticket_id: str
    portal_status_raw: str
    canonical_status: str          # PENDING | IN_PROGRESS | RESOLVED | FAILED
    submitted_at: datetime
    portal_url: Optional[str] = None   # direct link to complaint on portal


@dataclass
class StatusResult:
    ticket_id: str
    portal_status_raw: str
    canonical_status: str
    last_updated: datetime
    remarks: Optional[str] = None


class PortalAdapter(ABC):
    portal_id: str
    portal_name: str

    # ── 4-method contract ─────────────────────────────────────────────────

    @abstractmethod
    async def submit(self, portal_fields: dict, uco_meta: dict) -> SubmissionResult:
        """Transform portal_fields dict → submit to portal → return ticket."""
        ...

    @abstractmethod
    async def fetch_status(self, ticket_id: str) -> StatusResult:
        """Poll portal for current status of an existing ticket."""
        ...

    # ── Helpers (optional override) ───────────────────────────────────────

    def transform_fields(self, portal_fields: dict, uco_meta: dict) -> dict:
        """Map collected fields + UCO metadata into portal-specific payload.
        Default: pass through as-is. Override for portals that need remapping."""
        return {**portal_fields, **uco_meta}

    def map_canonical_status(self, raw_status: str) -> str:
        """Normalise portal-specific status strings to UCO canonical statuses."""
        mapping = {
            "submitted":      "PENDING",
            "received":       "PENDING",
            "under review":   "IN_PROGRESS",
            "in progress":    "IN_PROGRESS",
            "pending":        "PENDING",
            "resolved":       "RESOLVED",
            "closed":         "RESOLVED",
            "rejected":       "REJECTED",
            "disposed":       "RESOLVED",
        }
        return mapping.get(raw_status.lower().strip(), "IN_PROGRESS")
