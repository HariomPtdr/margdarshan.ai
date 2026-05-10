# service-chatbot

Stage 0 — Conversation Manager. Talks to the user, decides when complaint is ready, hands off to pipeline.

## Endpoints

```
POST /api/v1/chat
  body: { user_id, session_id?, message, language_preference? }
  returns: { reply, session_id, complaint_id?, intent, state, needs_location_pin, pipeline_triggered }

GET  /api/v1/session/{user_id}    # debug
DELETE /api/v1/session/{user_id}  # reset
GET  /healthz
```

## How it works

1. Loads session from Redis (or creates new)
2. Sends conversation history + new message to Claude Haiku 4.5
3. Claude returns JSON decision: `{intent, ready_for_pipeline, reply_to_user, ...}`
4. If `ready_for_pipeline`: publishes `stage_0_completed` event to Redis
5. Returns reply to caller

System prompt is **cached** on Anthropic side — first call writes, all subsequent calls read.

## Languages

Supports English, Hindi (Devanagari), Hinglish (Roman). Bot replies in whichever the user used.

## Run locally

```bash
pip install -r requirements.txt
pip install -e ../shared-schema
ANTHROPIC_API_KEY=YOUR_ANTHROPIC_KEY REDIS_HOST=localhost \
  uvicorn app.main:app --reload --port 8001
```
