"""Environment + runtime configuration."""

import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    ANTHROPIC_API_KEY: str = os.getenv("ANTHROPIC_API_KEY", "")
    REDIS_HOST: str = os.getenv("REDIS_HOST", "localhost")
    REDIS_PORT: int = int(os.getenv("REDIS_PORT", "6379"))

    SESSION_TTL_SECONDS: int = 21600  # 6 hours
    MAX_HISTORY_TURNS: int = 20
    MAX_MESSAGE_LENGTH: int = 2000

    CLAUDE_MODEL: str = "claude-haiku-4-5-20251001"
    CLAUDE_MAX_TOKENS: int = 600
    CLAUDE_TEMPERATURE: float = 0.2

    RATE_LIMIT_MESSAGES_PER_HOUR: int = 60


config = Config()
