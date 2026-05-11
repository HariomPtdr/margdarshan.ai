"""CPGRAMS Real Adapter — Web Automation via Playwright.

Automates https://pgportal.gov.in complaint submission form.
No API key needed — works like a human filling the form.

Install: pip install playwright && playwright install chromium
"""

import logging
from datetime import datetime
from .base import PortalAdapter, SubmissionResult, StatusResult

logger = logging.getLogger(__name__)

CPGRAMS_URL = "https://pgportal.gov.in"

# Ministry codes used by CPGRAMS form
DEPT_TO_MINISTRY = {
    "ELECTRICITY":     "Ministry of Power",
    "WATER_SUPPLY":    "Ministry of Jal Shakti",
    "ROADS":           "Ministry of Road Transport",
    "HEALTH":          "Ministry of Health & Family Welfare",
    "RAILWAYS":        "Ministry of Railways",
    "POLICE":          "Ministry of Home Affairs",
    "EDUCATION_SCHOOL":"Ministry of Education",
    "FOOD_RATION":     "Ministry of Consumer Affairs, Food & PDS",
    "PENSION_SOCIAL":  "Ministry of Social Justice",
    "TELECOM":         "Department of Telecom",
    "BANKING":         "Ministry of Finance (DFS)",
    "INCOME_TAX":      "Ministry of Finance (CBDT)",
    "POSTAL":          "Department of Posts",
    "AADHAAR":         "UIDAI",
}


class CPGRAMSRealAdapter(PortalAdapter):
    portal_id   = "P001"
    portal_name = "CPGRAMS — Central Govt"

    async def submit(self, portal_fields: dict, uco_meta: dict) -> SubmissionResult:
        try:
            from playwright.async_api import async_playwright
        except ImportError:
            logger.error("Playwright not installed. Run: pip install playwright && playwright install chromium")
            raise

        ministry = DEPT_TO_MINISTRY.get(uco_meta.get("department", ""), "Ministry of Personnel")

        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page()

            # ── Step 1: Go to CPGRAMS ──────────────────────────
            await page.goto(f"{CPGRAMS_URL}/lodgeComplaint")
            await page.wait_for_load_state("networkidle")

            # ── Step 2: Fill personal details ─────────────────
            await page.fill("#complainantName",
                            portal_fields.get("Full Name", ""))
            await page.fill("#mobileNumber",
                            portal_fields.get("Mobile Number", ""))
            await page.fill("#emailId",
                            portal_fields.get("Email Address", ""))

            # ── Step 3: Select ministry ────────────────────────
            await page.select_option("#ministryName", label=ministry)

            # ── Step 4: Fill address ───────────────────────────
            await page.fill("#address",
                            portal_fields.get("Address with State District and Pincode", ""))

            # ── Step 5: Write complaint text ───────────────────
            await page.fill("#grievanceText",
                            uco_meta.get("complaint_text", "")[:4000])

            # ── Step 6: Submit ─────────────────────────────────
            await page.click("#submitBtn")
            await page.wait_for_load_state("networkidle")

            # ── Step 7: Extract ticket ID from success page ────
            ticket_elem = await page.query_selector(".grievanceNo, #grievanceNo, .ticket-id")
            ticket_id = await ticket_elem.inner_text() if ticket_elem else f"CPGRAMS/PENDING"
            ticket_id = ticket_id.strip()

            await browser.close()

        logger.info("CPGRAMS submitted: ticket=%s", ticket_id)
        return SubmissionResult(
            ticket_id=ticket_id,
            portal_status_raw="Submitted",
            canonical_status="PENDING",
            submitted_at=datetime.utcnow(),
            portal_url=f"{CPGRAMS_URL}/TrackGrievance/{ticket_id}",
        )

    async def fetch_status(self, ticket_id: str) -> StatusResult:
        try:
            from playwright.async_api import async_playwright
        except ImportError:
            raise

        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page()

            await page.goto(f"{CPGRAMS_URL}/TrackGrievance/{ticket_id}")
            await page.wait_for_load_state("networkidle")

            status_elem = await page.query_selector(".grievanceStatus, #status")
            raw_status = await status_elem.inner_text() if status_elem else "Unknown"

            await browser.close()

        return StatusResult(
            ticket_id=ticket_id,
            portal_status_raw=raw_status,
            canonical_status=self.map_canonical_status(raw_status),
            last_updated=datetime.utcnow(),
        )
