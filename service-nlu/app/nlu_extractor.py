"""Claude Haiku for NLU intent extraction — called only when keyword matching fails."""

import json
import logging
import os

from anthropic import AsyncAnthropic

logger = logging.getLogger(__name__)

client = AsyncAnthropic(api_key=os.getenv("ANTHROPIC_API_KEY", ""))

NLU_PROMPT = """You are an NLU engine for Indian government grievance system.
Extract from citizen message. Return ONLY JSON (no markdown):
{"category": "<one of the 25 categories below or null>",
 "sub_issue": "<sub-issue code or null>",
 "location_text": "<address/area/city mentioned or null>",
 "duration": "<how long e.g. '3 days' or null>",
 "language": "<en|hi|hinglish>"}

CATEGORIES (use exact name):
- Electricity: bijli/light/power/current/transformer/meter/voltage
- Water Supply: paani/water/nal/pipeline/jal
- Roads & Transportation: sadak/road/pothole/gadda/highway/footpath
- Waste Management: kachra/garbage/safai/mosquito/sewage/dustbin
- Public Safety & Encroachment: shor/noise/awaaz/loudspeaker/music/gaana/dhol/encroachment/nuisance/pradushan/pollution/disturbance
- Health & Family Welfare: hospital/doctor/medicine/ambulance
- Police: police/fir/thana/theft/crime/harassment
- Education (Higher / School): school/teacher/scholarship/admission/vidyalaya
- Housing & Urban Affairs: housing/makaan/pmay/property/building plan
- Agriculture & Farmers Welfare: kisan/farmer/fasal/mandi/pm-kisan
- Banking (DFS): bank/atm/account/loan/fraud
- Aadhaar (UIDAI): aadhaar/adhar/biometric/uidai
- Income Tax (CBDT): income tax/itr/refund/tds/pan
- GST (CBIC): gst/gstin/itc
- EPFO: epf/pf/uan/esic
- Insurance (DFS): insurance/claim/lic/pmjjby
- Passport (MEA): passport/visa
- Pension & Pensioners Welfare: pension/old age pension/widow pension/viklang
- Petroleum & LPG: lpg/gas cylinder/ujjwala/petrol
- Postal: post office/speed post/parcel
- Public Distribution (PDS): ration/fps/anaj/gehu/chawal
- RTO / State Transport: rto/driving licence/vehicle registration
- Railways: railway/train/irctc/ticket/rpf
- Telecom: mobile/network/internet/sim/broadband
- OTHER: corruption/bribery/yojana/welfare/other

If greeting only → all null except language.
If user picks a number → return all null."""


async def extract_intent(message: str, lang: str = "hinglish") -> dict:
    """Extract category/sub_issue/location from freetext. Falls back to safe nulls on error."""
    try:
        resp = await client.messages.create(
            model=os.getenv("CLAUDE_MODEL", "claude-haiku-4-5-20251001"),
            max_tokens=200,
            system=[{
                "type": "text",
                "text": NLU_PROMPT,
                "cache_control": {"type": "ephemeral"},
            }],
            messages=[{"role": "user", "content": message}],
        )
        raw = resp.content[0].text.strip()
        if raw.startswith("```"):
            raw = "\n".join(
                line for line in raw.split("\n")
                if not line.strip().startswith("```")
            )
        data = json.loads(raw)
        return {k: (v if v and v != "null" else None) for k, v in data.items()}
    except Exception as e:
        logger.warning("NLU extraction failed: %s", e)
        return {
            "category": None,
            "sub_issue": None,
            "location_text": None,
            "duration": None,
            "language": lang,
        }
