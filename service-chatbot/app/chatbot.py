"""Claude (Anthropic) wrapper for Stage 0 Conversation Manager.

Uses prompt caching on the system prompt to minimize token cost.
"""

import asyncio
import json
import logging
from typing import Optional

from anthropic import AsyncAnthropic, APIStatusError

from .config import config
from .prompts import FIELD_EXTRACTION_PROMPT, SYSTEM_PROMPT

logger = logging.getLogger(__name__)


class Chatbot:
    def __init__(self):
        self.client = AsyncAnthropic(api_key=config.ANTHROPIC_API_KEY)

    async def call(
        self,
        history: list[dict],
        new_message: str,
        language_preference: Optional[str] = None,
        current_state: Optional[str] = None,
        complaint_buffer: Optional[str] = None,
    ) -> dict:
        user_content = self._wrap_user(
            new_message, language_preference, current_state, complaint_buffer
        )
        messages = list(history) + [{"role": "user", "content": user_content}]

        delays = [5, 15, 30]
        for attempt in range(3):
            try:
                response = await self.client.messages.create(
                    model=config.CLAUDE_MODEL,
                    max_tokens=config.CLAUDE_MAX_TOKENS,
                    temperature=config.CLAUDE_TEMPERATURE,
                    system=[
                        {
                            "type": "text",
                            "text": SYSTEM_PROMPT,
                            "cache_control": {"type": "ephemeral"},
                        }
                    ],
                    messages=messages,
                )
                break
            except APIStatusError as e:
                if e.status_code == 429 and attempt < 2:
                    logger.warning(f"Claude 429, retrying in {delays[attempt]}s")
                    await asyncio.sleep(delays[attempt])
                    continue
                logger.error(f"Claude API error: {e}")
                return self._fallback_decision("Thodi der baad dobara try karein.")
            except Exception as e:
                logger.error(f"Claude error: {e}")
                return self._fallback_decision("Thodi der baad dobara try karein.")
        else:
            return self._fallback_decision("Thodi der baad dobara try karein.")

        raw_text = response.content[0].text.strip()
        logger.info(
            f"Claude usage: in={response.usage.input_tokens} "
            f"out={response.usage.output_tokens} "
            f"cache_read={getattr(response.usage, 'cache_read_input_tokens', 0)}"
        )
        return self._parse_decision(raw_text, new_message)

    @staticmethod
    def _wrap_user(
        message: str,
        language_preference: Optional[str],
        current_state: Optional[str] = None,
        complaint_buffer: Optional[str] = None,
    ) -> str:
        parts = []
        if language_preference:
            parts.append(f"[user_language_preference: {language_preference}]")
        if current_state and current_state != "IDLE" and complaint_buffer:
            parts.append(
                f"[SYSTEM_NOTE: ACTIVE COMPLAINT IN PROGRESS. "
                f"state={current_state}. "
                f"complaint_buffer=\"{complaint_buffer[:150]}\". "
                f"DO NOT greet as new user. DO NOT reset context. "
                f"Stay focused on this complaint.]"
            )
        parts.append(message)
        return "\n".join(parts)

    @staticmethod
    def _parse_decision(raw_text: str, original_message: str) -> dict:
        text = raw_text
        if text.startswith("```"):
            lines = text.split("\n")
            text = "\n".join(l for l in lines if not l.strip().startswith("```"))

        try:
            decision = json.loads(text)
        except json.JSONDecodeError:
            logger.warning(f"Bad JSON from Claude: {raw_text[:200]}")
            return Chatbot._fallback_decision("Samajh nahi paaya, kripya dobara likhein.")

        defaults = {
            "intent": "OFF_TOPIC",
            "language_detected": "en",
            "complaint_buffer": "",
            "completeness_score": 0,
            "ready_for_pipeline": False,
            "next_state": "IDLE",
            "is_new_complaint": False,
            "needs_location_pin": False,
            "abandoned_signal": False,
            "multiple_complaints_detected": False,
            "reply_to_user": "Samajh nahi paaya.",
        }
        for k, v in defaults.items():
            decision.setdefault(k, v)
        return decision

    @staticmethod
    def _fallback_decision(reply: str) -> dict:
        return {
            "intent": "OFF_TOPIC",
            "language_detected": "en",
            "complaint_buffer": "",
            "completeness_score": 0,
            "ready_for_pipeline": False,
            "next_state": "IDLE",
            "is_new_complaint": False,
            "needs_location_pin": False,
            "abandoned_signal": False,
            "multiple_complaints_detected": False,
            "reply_to_user": reply,
        }


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
                temperature=0.1,
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
            return {"extracted": value, "reply": f"Note kar liya." + (f" Ab batayein: {next_field}" if next_field else "")}


chatbot = Chatbot()
