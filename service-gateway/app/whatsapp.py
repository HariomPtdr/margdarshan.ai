"""WhatsApp outbound client — provider-agnostic.

Mirror of service-tracker/app/whatsapp.py so the gateway can reply to
inbound WhatsApp messages without a cross-service hop. Same env vars.
"""

from __future__ import annotations

import asyncio
import logging
import os
from typing import Optional

import httpx

logger = logging.getLogger(__name__)


class WhatsAppClient:
    def __init__(self) -> None:
        self.provider = os.getenv("WHATSAPP_PROVIDER", "mock").lower()
        self._twilio = None
        if self.provider == "twilio":
            sid = os.getenv("TWILIO_ACCOUNT_SID", "")
            tok = os.getenv("TWILIO_AUTH_TOKEN", "")
            self._from = os.getenv("TWILIO_WHATSAPP_FROM", "whatsapp:+14155238886")
            if not sid or not tok:
                logger.warning("twilio creds missing — falling back to mock")
                self.provider = "mock"
            else:
                from twilio.rest import Client
                self._twilio = Client(sid, tok)
        elif self.provider == "meta":
            self._meta_token = os.getenv("META_WHATSAPP_TOKEN", "")
            self._meta_phone = os.getenv("META_WHATSAPP_PHONE_ID", "")
            if not self._meta_token or not self._meta_phone:
                logger.warning("meta creds missing — falling back to mock")
                self.provider = "mock"

    @staticmethod
    def _format_to(mobile: str) -> str:
        m = mobile.strip().replace(" ", "").replace("-", "")
        if not m.startswith("+"):
            m = "+91" + m.lstrip("0") if len(m) == 10 else "+" + m
        return f"whatsapp:{m}"

    @staticmethod
    def _mask(mobile: str) -> str:
        return ("*" * max(0, len(mobile) - 4) + mobile[-4:]) if mobile else "****"

    async def send(self, to: str, body: str) -> Optional[str]:
        if not to or not body:
            return None
        masked = self._mask(to)
        if self.provider == "mock":
            logger.info("[MOCK WhatsApp] → %s: %s", masked, body)
            return None
        if self.provider == "twilio":
            try:
                msg = await asyncio.to_thread(
                    self._twilio.messages.create,
                    from_=self._from,
                    to=self._format_to(to),
                    body=body,
                )
                logger.info("[Twilio WhatsApp] → %s: sid=%s", masked, msg.sid)
                return msg.sid
            except Exception as e:
                logger.warning("twilio send failed → %s: %s", masked, e)
                return None
        if self.provider == "meta":
            url = f"https://graph.facebook.com/v20.0/{self._meta_phone}/messages"
            headers = {"Authorization": f"Bearer {self._meta_token}",
                       "Content-Type": "application/json"}
            payload = {
                "messaging_product": "whatsapp",
                "to": self._format_to(to).replace("whatsapp:", ""),
                "type": "text",
                "text": {"body": body},
            }
            try:
                async with httpx.AsyncClient(timeout=10.0) as c:
                    r = await c.post(url, headers=headers, json=payload)
                    r.raise_for_status()
                    mid = r.json().get("messages", [{}])[0].get("id")
                    logger.info("[Meta WhatsApp] → %s: id=%s", masked, mid)
                    return mid
            except Exception as e:
                logger.warning("meta send failed → %s: %s", masked, e)
                return None
        return None


_singleton: Optional[WhatsAppClient] = None


def client() -> WhatsAppClient:
    global _singleton
    if _singleton is None:
        _singleton = WhatsAppClient()
    return _singleton
