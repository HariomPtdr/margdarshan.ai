"""Redis session store for Layer 2 conversation state."""

import json
import os
import uuid
from datetime import datetime
from typing import Optional

import redis.asyncio as redis_async

REDIS_HOST = os.getenv("REDIS_HOST", "redis")
REDIS_PORT = int(os.getenv("REDIS_PORT", "6379"))
SESSION_TTL = 21600  # 6 hours


class ConvSession:
    def __init__(
        self,
        user_id: str,
        session_id: Optional[str] = None,
        state: str = "IDLE",
        slots: Optional[dict] = None,
        language: str = "hinglish",
        complaint_buffer: str = "",
    ):
        self.user_id = user_id
        self.session_id = session_id or str(uuid.uuid4())
        self.state = state
        self.slots = slots or {}
        self.language = language
        self.complaint_buffer = complaint_buffer
        self.last_active = datetime.utcnow().isoformat()

    def to_dict(self) -> dict:
        return {
            "user_id": self.user_id,
            "session_id": self.session_id,
            "state": self.state,
            "slots": self.slots,
            "language": self.language,
            "complaint_buffer": self.complaint_buffer,
            "last_active": self.last_active,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "ConvSession":
        s = cls(
            user_id=data["user_id"],
            session_id=data.get("session_id"),
            state=data.get("state", "IDLE"),
            slots=data.get("slots") or {},
            language=data.get("language", "hinglish"),
            complaint_buffer=data.get("complaint_buffer", ""),
        )
        s.last_active = data.get("last_active", s.last_active)
        return s

    # StateMachine reads/writes session.language_preference — alias it
    @property
    def language_preference(self) -> str:
        return self.language

    @language_preference.setter
    def language_preference(self, value: str):
        self.language = value


class ConvSessionStore:
    """Redis-backed session storage for NLU conversation state."""

    def __init__(self):
        self._redis: Optional[redis_async.Redis] = None

    async def _connect(self) -> redis_async.Redis:
        if self._redis is None:
            self._redis = redis_async.Redis(
                host=REDIS_HOST,
                port=REDIS_PORT,
                decode_responses=True,
            )
        return self._redis

    async def load(self, user_id: str) -> Optional[ConvSession]:
        r = await self._connect()
        raw = await r.get(self._key(user_id))
        if not raw:
            return None
        return ConvSession.from_dict(json.loads(raw))

    async def save(self, session: ConvSession):
        r = await self._connect()
        session.last_active = datetime.utcnow().isoformat()
        await r.set(
            self._key(session.user_id),
            json.dumps(session.to_dict()),
            ex=SESSION_TTL,
        )

    async def delete(self, user_id: str):
        r = await self._connect()
        await r.delete(self._key(user_id))

    @staticmethod
    def _key(user_id: str) -> str:
        return f"nlu_session:{user_id}"


store = ConvSessionStore()
