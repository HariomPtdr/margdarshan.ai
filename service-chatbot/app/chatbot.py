"""Claude API calls — NLU extraction + field extraction only.

The StateMachine controls conversation flow. Claude is used ONLY for:
1. extract_intent() — detect category/sub-issue/location from freetext
2. extract_field()  — extract portal field values during form filling
"""

import json
import logging
from typing import Optional

from anthropic import AsyncAnthropic, APIStatusError

from .config import config

logger = logging.getLogger(__name__)

NLU_SYSTEM_PROMPT = """\
You are an NLU engine for an Indian government grievance portal.
Extract structured information from a citizen's message.

Respond ONLY with this JSON (no markdown, no extra text):
{
  "category": "<ELECTRICITY|WATER_SUPPLY|ROADS|SANITATION|HEALTH|POLICE|EDUCATION|REVENUE_LAND|OTHER|null>",
  "sub_issue": "<specific sub-issue code or null>",
  "location_text": "<address/area/city mentioned or null>",
  "duration": "<how long the issue has lasted e.g. '3 days' or null>",
  "language": "<en|hi|hinglish>"
}

Category rules (detect from keywords in any language):
- ELECTRICITY: bijli, light, current, power, batti, electricity, transformer, meter, voltage
- WATER_SUPPLY: paani, water, nal, supply, pipeline, jal
- ROADS: sadak, road, pothole, gadda, drainage, footpath
- SANITATION: kachra, garbage, sweeper, safai, mosquito
- HEALTH: hospital, doctor, medicine, ambulance, health, clinic
- POLICE: police, fir, thana, theft, safety, harassment
- EDUCATION: school, teacher, scholarship, vidyalaya
- REVENUE_LAND: jameen, land, property, khasra, mutation, nakal
- OTHER: pension, ration, aadhaar, corruption, yojana

Sub-issue codes (if clearly mentioned):
ELECTRICITY: POWER_OUTAGE, VOLTAGE, TRANSFORMER, STREET_LIGHT, METER, NEW_CONNECTION
WATER_SUPPLY: NO_WATER, LOW_PRESSURE, DIRTY_WATER, PIPELINE_LEAK, NEW_CONNECTION
ROADS: POTHOLE, DRAINAGE, FOOTPATH, TRAFFIC, ROAD_LIGHT
SANITATION: GARBAGE_COLLECTION, GARBAGE_DUMPING, PUBLIC_TOILET, MOSQUITO_PEST, STRAY_ANIMALS
HEALTH: HOSPITAL_SERVICE, AMBULANCE, MEDICINE, DOCTOR_ABSENT, VACCINATION, PMJAY
POLICE: FIR, SAFETY, HARASSMENT, CRIME, VERIFICATION
EDUCATION: TEACHER_ABSENT, FACILITY, SCHOLARSHIP, ADMISSION, MIDDAY_MEAL
REVENUE_LAND: LAND_RECORD, PROPERTY_TAX, ENCROACHMENT, MUTATION, SURVEY
OTHER: PENSION, RATION, CORRUPTION, AADHAAR, GENERAL

If message is just a greeting (hi, hello, namaste) return all null except language.
If user selects a number (1-9) return all null — state machine handles number selection.
"""

FIELD_EXTRACTION_PROMPT = """\
You are collecting form fields for a government grievance portal. The user is answering one field at a time.

Current field to collect: {field_name}
User's language: {language}
Next field (if any): {next_field}

Rules:
- Extract the value for "{field_name}" from the user's message.
- If the user clearly provided a value, set extracted to that value (string).
- If the user says they don't know, says "skip", or gives a non-answer, set extracted to null.
- Keep reply to 1 short sentence in the user's language.
- If extracted is not null and next_field is given, mention the next field in your reply.
- If extracted is null, give a brief hint about where to find "{field_name}".

Respond ONLY with this JSON (no markdown, no extra text):
{{"extracted": "<value or null>", "reply": "<1 sentence>"}}
"""


class Chatbot:
    def __init__(self):
        self.client = AsyncAnthropic(api_key=config.ANTHROPIC_API_KEY)

    async def extract_intent(self, message: str, lang: str = "hinglish") -> dict:
        """Extract category/sub_issue/location from freetext. Used by StateMachine."""
        try:
            response = await self.client.messages.create(
                model=config.CLAUDE_MODEL,
                max_tokens=200,
                system=[{
                    "type": "text",
                    "text": NLU_SYSTEM_PROMPT,
                    "cache_control": {"type": "ephemeral"},
                }],
                messages=[{"role": "user", "content": message}],
            )
            raw = response.content[0].text.strip()
            if raw.startswith("```"):
                raw = "\n".join(l for l in raw.split("\n") if not l.strip().startswith("```"))
            data = json.loads(raw)
            # Sanitize nulls
            return {k: (v if v and v != "null" else None) for k, v in data.items()}
        except Exception as e:
            logger.warning("extract_intent failed: %s", e)
            return {"category": None, "sub_issue": None, "location_text": None, "duration": None, "language": lang}

    async def extract_field(
        self,
        field_name: str,
        user_message: str,
        language_preference: str,
        next_field: Optional[str] = None,
    ) -> dict:
        """Single-turn call: extract one portal field value from user's message."""
        prompt = FIELD_EXTRACTION_PROMPT.format(
            field_name=field_name,
            language=language_preference,
            next_field=next_field or "",
        )
        try:
            response = await self.client.messages.create(
                model=config.CLAUDE_MODEL,
                max_tokens=200,
                system=prompt,
                messages=[{"role": "user", "content": user_message}],
            )
            raw = response.content[0].text.strip()
            import json as _j
            data = _j.loads(raw)
            return {"extracted": data.get("extracted"), "reply": data.get("reply", "")}
        except Exception as e:
            logger.error(f"extract_field error: {e}")
            skip_phrases = {"nahi pata", "pata nahi", "dont know", "don't know", "skip", "na", "?", "no"}
            value = user_message.strip()
            if value.lower() in skip_phrases or len(value) < 2:
                return {"extracted": None, "reply": f"Koi baat nahi. {field_name} baad mein batayein ya 'skip' likhein."}
            return {"extracted": value, "reply": "Note kar liya." + (f" Ab batayein: {next_field}" if next_field else "")}


chatbot = Chatbot()
