"""CPGRAMS adapter (mock for prototype).

In production: use Playwright to drive https://pgportal.gov.in.
For prototype: returns a realistic fake ticket and simulates status polling.
"""

import random
import string
from datetime import datetime, timedelta

from .base import PortalAdapter, SubmissionResult, StatusResult


class CPGRAMSAdapter(PortalAdapter):
    portal_id   = "P001"
    portal_name = "CPGRAMS"

    def transform_fields(self, portal_fields: dict, uco_meta: dict) -> dict:
        """Map our field labels to CPGRAMS form field names."""
        return {
            "complainantName":    portal_fields.get("Full Name", uco_meta.get("user_name", "")),
            "address":            portal_fields.get("Address with State District and Pincode", ""),
            "pinCode":            portal_fields.get("Pincode", ""),
            "mobileNumber":       portal_fields.get("Mobile Number", ""),
            "emailId":            portal_fields.get("Email Address", ""),
            "aadhaarNo":          portal_fields.get("Aadhaar Number (optional)", ""),
            "ministryId":         uco_meta.get("department", ""),
            "grievanceText":      uco_meta.get("complaint_text", ""),
            "grievanceDocuments": "",
        }

    async def submit(self, portal_fields: dict, uco_meta: dict) -> SubmissionResult:
        payload = self.transform_fields(portal_fields, uco_meta)
        ticket = "CPGRAMS/" + "".join(random.choices(string.digits, k=10))
        return SubmissionResult(
            ticket_id=ticket,
            portal_status_raw="Submitted",
            canonical_status="PENDING",
            submitted_at=datetime.utcnow(),
            portal_url=f"https://pgportal.gov.in/status/{ticket}",
        )

    async def fetch_status(self, ticket_id: str) -> StatusResult:
        # Mock: advance status based on age (for demo realism).
        statuses = ["Submitted", "Under Review", "Forwarded to Ministry", "Resolved"]
        raw = random.choice(statuses)
        return StatusResult(
            ticket_id=ticket_id,
            portal_status_raw=raw,
            canonical_status=self.map_canonical_status(raw),
            last_updated=datetime.utcnow(),
            remarks="Auto-updated by mock adapter",
        )
