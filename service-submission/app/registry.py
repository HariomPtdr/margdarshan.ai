"""Adapter registry — plug-and-play portal adapters.

Specific adapters: registered portals with real or detailed mock integrations.
Generic fallback: generates portal-appropriate ticket IDs based on portal name/type.
"""

import random
import string
from datetime import datetime

from .adapters import CPGRAMSAdapter, MPCM181Adapter, MPPKVVCLAdapter
from .adapters.base import PortalAdapter, SubmissionResult, StatusResult


class GenericMockAdapter(PortalAdapter):
    """Generic mock for any unregistered portal.
    Generates a ticket ID with a prefix matching the portal type, not CPGRAMS.
    """

    # Portal name keywords → ticket prefix
    _NAME_PREFIXES = [
        ("police",    "POL"),
        ("water",     "JAL"),
        ("jal",       "JAL"),
        ("electric",  "ELE"),
        ("discom",    "ELE"),
        ("bijli",     "ELE"),
        ("road",      "PWD"),
        ("health",    "NHM"),
        ("education", "EDU"),
        ("revenue",   "REV"),
        ("nagar",     "ULB"),
        ("municipal", "ULB"),
        ("cpgrams",   "CPGRAMS"),
        ("pmo",       "PMO-PG"),
        ("railway",   "RLY"),
        ("telecom",   "TRAI"),
    ]

    def __init__(self, portal_id: str = "", portal_name: str = ""):
        self._pid = portal_id
        self._pname = portal_name.lower()

    def _ticket_prefix(self) -> str:
        for keyword, prefix in self._NAME_PREFIXES:
            if keyword in self._pname:
                return prefix
        return "PG"   # generic grievance prefix

    async def submit(self, portal_fields: dict, uco_meta: dict) -> SubmissionResult:
        prefix = self._ticket_prefix()
        ticket = f"{prefix}/" + "".join(random.choices(string.digits, k=10))
        return SubmissionResult(
            ticket_id=ticket,
            portal_status_raw="Submitted",
            canonical_status="PENDING",
            submitted_at=datetime.utcnow(),
            portal_url=f"https://portal.gov.in/status/{ticket}",
        )

    async def fetch_status(self, ticket_id: str) -> StatusResult:
        raw = random.choice(["Submitted", "Under Review", "Forwarded to Department", "Resolved"])
        return StatusResult(
            ticket_id=ticket_id,
            portal_status_raw=raw,
            canonical_status=self.map_canonical_status(raw),
            last_updated=datetime.utcnow(),
            remarks="Mock status update for prototype",
        )


# Portals with specific adapters
_SPECIFIC: dict[str, PortalAdapter] = {
    "P001": CPGRAMSAdapter(),   # Central CPGRAMS
    "P002": CPGRAMSAdapter(),   # PMO → CPGRAMS
    "P031": MPCM181Adapter(),   # MP CM Helpline 181
    "P062": MPPKVVCLAdapter(),  # MPPKVVCL Bhopal Discom ← PLUGGED IN
    "P065": MPPKVVCLAdapter(),  # MPPKVVCL Indore Discom ← PLUGGED IN
}

# Portal names loaded from routing service at submission time
# (passed by gateway via uco_meta)
def get_adapter(portal_id: str, portal_name: str = "") -> PortalAdapter:
    if portal_id in _SPECIFIC:
        return _SPECIFIC[portal_id]
    return GenericMockAdapter(portal_id=portal_id, portal_name=portal_name)


def registered_portals() -> list[str]:
    return list(_SPECIFIC.keys())
