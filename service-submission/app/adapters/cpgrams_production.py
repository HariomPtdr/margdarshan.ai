"""CPGRAMS Production Adapter.

HOW TO GET API KEY:
1. Email grievance-darpg@nic.in
2. Provide: organization name, use case, contact details
3. They send: API key + ministry code list

Set in .env:
  CPGRAMS_API_KEY=Bearer sk_cpgrams_your_key_here
  CPGRAMS_BASE_URL=https://pgportal.gov.in/api/v1
"""

import logging
import os
from datetime import datetime
import httpx
from .base import PortalAdapter, SubmissionResult, StatusResult

logger = logging.getLogger(__name__)

# ── Ministry codes from CPGRAMS documentation ────────────────────────────
# They give you this list. Each department maps to their ministry code.
MINISTRY_CODES = {
    "ELECTRICITY":      "PWR",   # Ministry of Power
    "WATER_SUPPLY":     "JLN",   # Ministry of Jal Shakti
    "ROADS":            "RTH",   # Ministry of Road Transport & Highways
    "HEALTH":           "HFW",   # Ministry of Health & Family Welfare
    "RAILWAYS":         "RLY",   # Ministry of Railways
    "POLICE":           "HMA",   # Ministry of Home Affairs
    "EDUCATION_SCHOOL": "EDN",   # Ministry of Education
    "FOOD_RATION":      "CAF",   # Ministry of Consumer Affairs
    "PENSION_SOCIAL":   "SJE",   # Ministry of Social Justice
    "TELECOM":          "DOT",   # Department of Telecom
    "BANKING":          "DFS",   # Dept of Financial Services
    "INCOME_TAX":       "CBT",   # CBDT
    "POSTAL":           "POS",   # Department of Posts
    "AADHAAR":          "UDA",   # UIDAI
    "EPF_ESIC":         "LBR",   # Ministry of Labour
    "INSURANCE":        "DFS",   # DFS
    "PASSPORT":         "MEA",   # Ministry of External Affairs
}


class CPGRAMSProductionAdapter(PortalAdapter):
    portal_id   = "P001"
    portal_name = "CPGRAMS"

    def __init__(self):
        self.api_key  = os.getenv("CPGRAMS_API_KEY", "")
        self.base_url = os.getenv("CPGRAMS_BASE_URL", "https://pgportal.gov.in/api/v1")

    @property
    def headers(self):
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type":  "application/json",
            "Accept":        "application/json",
        }

    # ── STEP 1: Map our fields → CPGRAMS fields ──────────────────────────
    def transform_fields(self, portal_fields: dict, uco_meta: dict) -> dict:
        """
        OUR FIELD NAMES          →  CPGRAMS FIELD NAMES
        ─────────────────────────────────────────────────
        "Full Name"              →  "complainantName"
        "Mobile Number"          →  "mobileNumber"
        "Email Address"          →  "emailId"
        "Aadhaar Number"         →  "aadhaarNumber"
        "Address..."             →  "addressLine1" + "district" + "state"
        complaint_text (uco)     →  "grievanceText"
        department (uco)         →  "ministryCode"
        """
        address = portal_fields.get("Address with State District and Pincode", "")
        
        return {
            "complainantName":  portal_fields.get("Full Name", ""),
            "mobileNumber":     portal_fields.get("Mobile Number", ""),
            "emailId":          portal_fields.get("Email Address", ""),
            "aadhaarNumber":    portal_fields.get("Aadhaar Number (optional)", ""),
            "addressLine1":     address.split(",")[0] if address else "",
            "district":         uco_meta.get("district", ""),
            "state":            "Madhya Pradesh",
            "pinCode":          portal_fields.get("Pincode", ""),
            "ministryCode":     MINISTRY_CODES.get(uco_meta.get("department", ""), "DPG"),
            "grievanceSubject": uco_meta.get("complaint_text", "")[:100],
            "grievanceText":    uco_meta.get("complaint_text", "")[:4000],
            "attachments":      [],
        }

    # ── STEP 2: Call CPGRAMS API to submit ───────────────────────────────
    async def submit(self, portal_fields: dict, uco_meta: dict) -> SubmissionResult:
        payload = self.transform_fields(portal_fields, uco_meta)

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                f"{self.base_url}/grievance/register",
                json=payload,
                headers=self.headers,
            )
            response.raise_for_status()
            data = response.json()

        ticket_id = data["grievanceId"]    # e.g. "DOEL/E/2026/123456"
        logger.info("CPGRAMS submitted: ticket=%s", ticket_id)

        return SubmissionResult(
            ticket_id=ticket_id,
            portal_status_raw="Registered",
            canonical_status="PENDING",
            submitted_at=datetime.utcnow(),
            portal_url=data.get("trackingUrl", f"https://pgportal.gov.in/track/{ticket_id}"),
        )

    # ── STEP 3: Poll CPGRAMS for status updates ──────────────────────────
    async def fetch_status(self, ticket_id: str) -> StatusResult:
        async with httpx.AsyncClient(timeout=15.0) as client:
            response = await client.get(
                f"{self.base_url}/grievance/{ticket_id}/status",
                headers=self.headers,
            )
            response.raise_for_status()
            data = response.json()

        return StatusResult(
            ticket_id=ticket_id,
            portal_status_raw=data["status"],
            canonical_status=self.map_canonical_status(data["status"]),
            last_updated=datetime.utcnow(),
            remarks=data.get("remarks", ""),
        )
