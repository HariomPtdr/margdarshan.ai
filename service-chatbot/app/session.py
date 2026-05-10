"""Redis session store for Stage 0 conversation state."""

import json
import uuid
from datetime import datetime
from typing import Optional

import redis.asyncio as redis_async

from .config import config


class Session:
    def __init__(
        self,
        user_id: str,
        session_id: Optional[str] = None,
        history: Optional[list] = None,
        state: str = "IDLE",
        complaint_id: Optional[str] = None,
        complaint_buffer: str = "",
        language_preference: Optional[str] = None,
        field_collection: Optional[dict] = None,
        pending_notification: Optional[str] = None,
    ):
        self.user_id = user_id
        self.session_id = session_id or str(uuid.uuid4())
        self.history = history or []
        self.state = state
        self.complaint_id = complaint_id
        self.complaint_buffer = complaint_buffer
        self.language_preference = language_preference
        # field_collection holds: complaint_id, portal_id, portal_name,
        # pending_fields (list), collected_fields (dict), dedup_info (dict|None)
        self.field_collection: dict = field_collection or {}
        # pre-written message delivered on the user's very next turn, then cleared
        self.pending_notification: Optional[str] = pending_notification
        self.last_active = datetime.utcnow().isoformat()

    def to_dict(self) -> dict:
        return {
            "user_id": self.user_id,
            "session_id": self.session_id,
            "history": self.history,
            "state": self.state,
            "complaint_id": self.complaint_id,
            "complaint_buffer": self.complaint_buffer,
            "language_preference": self.language_preference,
            "field_collection": self.field_collection,
            "pending_notification": self.pending_notification,
            "last_active": self.last_active,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Session":
        s = cls(
            user_id=data["user_id"],
            session_id=data["session_id"],
            history=data.get("history", []),
            state=data.get("state", "IDLE"),
            complaint_id=data.get("complaint_id"),
            complaint_buffer=data.get("complaint_buffer", ""),
            language_preference=data.get("language_preference"),
            field_collection=data.get("field_collection") or {},
            pending_notification=data.get("pending_notification"),
        )
        s.last_active = data.get("last_active", s.last_active)
        return s


class SessionStore:
    """Redis-backed session storage with TTL."""

    def __init__(self):
        self._redis: Optional[redis_async.Redis] = None

    async def connect(self):
        if self._redis is None:
            self._redis = redis_async.Redis(
                host=config.REDIS_HOST,
                port=config.REDIS_PORT,
                decode_responses=True,
            )
        return self._redis

    async def load(self, user_id: str) -> Optional[Session]:
        r = await self.connect()
        raw = await r.get(self._key(user_id))
        if not raw:
            return None
        return Session.from_dict(json.loads(raw))

    async def save(self, session: Session):
        r = await self.connect()
        # cap history to control token cost
        if len(session.history) > config.MAX_HISTORY_TURNS * 2:
            session.history = session.history[-config.MAX_HISTORY_TURNS * 2:]
        await r.set(
            self._key(session.user_id),
            json.dumps(session.to_dict()),
            ex=config.SESSION_TTL_SECONDS,
        )

    async def delete(self, user_id: str):
        r = await self.connect()
        await r.delete(self._key(user_id))

    async def rate_limit_check(self, user_id: str) -> bool:
        """True if user is within rate limit, False if exceeded."""
        r = await self.connect()
        key = f"ratelimit:{user_id}"
        count = await r.incr(key)
        if count == 1:
            await r.expire(key, 3600)  # 1 hour window
        return count <= config.RATE_LIMIT_MESSAGES_PER_HOUR

    @staticmethod
    def _key(user_id: str) -> str:
        return f"session:{user_id}"


store = SessionStore()
