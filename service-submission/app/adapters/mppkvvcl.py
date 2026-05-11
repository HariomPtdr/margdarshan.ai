"""MPPKVVCL adapter — MP electricity distribution company.

Demo adapter: shows how a real electricity portal would be integrated.
In production: drives https://mppkvvcl.com/grievance using their API.
For demo: returns realistic ticket IDs and simulates status flow.
"""

import random
import string
from datetime import datetime

from .base import PortalAdapter, SubmissionResult, StatusResult


class MPPKVVCLAdapter(PortalAdapter):
    portal_id   = "P062"
    portal_name = "MPPKVVCL — MP Electricity Board"

    def transform_fields(self, portal_fields: dict, uco_meta: dict) -> dict:
        """Map our field labels → MPPKVVCL's form field names."""
        return {
            "consumerName":    portal_fields.get("Full Name", uco_meta.get("user_name", "")),
            "ivrsNo":          portal_fields.get("IVRS Consumer Number", ""),
            "mobileNo":        portal_fields.get("Mobile Number", ""),
            "address":         portal_fields.get("Full address of connection", ""),
            "complaintType":   portal_fields.get("Complaint type", "Power Outage"),
            "complaintDesc":   portal_fields.get("Description of issue",
                                                  uco_meta.get("complaint_text", "")),
            "district":        uco_meta.get("district", ""),
        }

    async def submit(self, portal_fields: dict, uco_meta: dict) -> SubmissionResult:
        # In production: POST to https://mppkvvcl.com/api/grievance
        payload = self.transform_fields(portal_fields, uco_meta)
        ticket = "ELE/" + "".join(random.choices(string.digits, k=10))
        return SubmissionResult(
            ticket_id=ticket,
            portal_status_raw="Registered",
            canonical_status="PENDING",
            submitted_at=datetime.utcnow(),
            portal_url=f"https://mppkvvcl.com/grievance/status/{ticket}",
        )

    async def fetch_status(self, ticket_id: str) -> StatusResult:
        # Simulates realistic status progression
        statuses = [
            ("Registered",       "PENDING"),
            ("Under Review",     "IN_PROGRESS"),
            ("Assigned to JE",   "IN_PROGRESS"),
            ("Field Visit Done", "IN_PROGRESS"),
            ("Resolved",         "RESOLVED"),
        ]
        raw, canonical = random.choice(statuses)
        return StatusResult(
            ticket_id=ticket_id,
            portal_status_raw=raw,
            canonical_status=canonical,
            last_updated=datetime.utcnow(),
            remarks="MPPKVVCL field team update",
        )
