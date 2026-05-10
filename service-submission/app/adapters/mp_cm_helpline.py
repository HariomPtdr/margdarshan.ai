"""MP CM Helpline 181 adapter (mock for prototype).

In production: drive https://cmhelpline.mp.gov.in via Playwright.
"""

import random
import string
from datetime import datetime

from .base import PortalAdapter, SubmissionResult, StatusResult


class MPCM181Adapter(PortalAdapter):
    portal_id   = "P031"
    portal_name = "MP CM Helpline 181"

    def transform_fields(self, portal_fields: dict, uco_meta: dict) -> dict:
        return {
            "name":        portal_fields.get("Full Name", uco_meta.get("user_name", "")),
            "mobile":      portal_fields.get("Mobile Number", ""),
            "aadhaar":     portal_fields.get("Aadhaar Number (optional)", ""),
            "district":    portal_fields.get("District", uco_meta.get("district", "")),
            "tehsil":      portal_fields.get("Tehsil", ""),
            "village":     portal_fields.get("Village or Ward", ""),
            "department":  portal_fields.get("Department name", uco_meta.get("department", "")),
            "complaint":   portal_fields.get("Complaint description", uco_meta.get("complaint_text", "")),
        }

    async def submit(self, portal_fields: dict, uco_meta: dict) -> SubmissionResult:
        payload = self.transform_fields(portal_fields, uco_meta)
        ticket = "CMH/" + "".join(random.choices(string.digits, k=8))
        return SubmissionResult(
            ticket_id=ticket,
            portal_status_raw="Registered",
            canonical_status="PENDING",
            submitted_at=datetime.utcnow(),
            portal_url=f"https://cmhelpline.mp.gov.in/track/{ticket}",
        )

    async def fetch_status(self, ticket_id: str) -> StatusResult:
        statuses = ["Registered", "Assigned to Officer", "Under Review", "Resolved"]
        raw = random.choice(statuses)
        return StatusResult(
            ticket_id=ticket_id,
            portal_status_raw=raw,
            canonical_status=self.map_canonical_status(raw),
            last_updated=datetime.utcnow(),
        )
