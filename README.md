# Shikayat Saathi — Multilingual Grievance Redressal System

BGI Hackathon 2026 · Team: Merge Conflict (ID 2515) · Problem: BT1P1

A multilingual chatbot that takes citizen complaints in Hindi/English/Hinglish, classifies them, picks the right portal based on map-pinned location, and submits via plug-and-play adapters.

## Architecture (multi-service, deploy independently)

```
┌──────────────────────────────────────────────────────────────┐
│                  web-frontend (port 5173)                     │
│   3-column React UI · 3 languages · Voice · Map picker        │
└──────────────────────────────────────────────────────────────┘
                             │
                             ▼
┌──────────────────────────────────────────────────────────────┐
│                service-gateway (port 8000)                    │
│        Single public API + WebSocket bridge                   │
└──────────────────────────────────────────────────────────────┘
       │            │             │              │
       ▼            ▼             ▼              ▼
 ┌──────────┐ ┌──────────┐ ┌──────────┐  ┌──────────────┐
 │ chatbot  │ │ location │ │   nlu    │  │  classifier  │
 │  :8001   │ │  :8002   │ │  :8003   │  │    :8004     │
 │ (Claude) │ │ (Mappls/ │ │ (norm,   │  │ (MuRIL stub) │
 │          │ │  OSM)    │ │  PII,    │  │              │
 │          │ │          │ │  KW)     │  │              │
 └──────────┘ └──────────┘ └──────────┘  └──────────────┘
                  │                │             │
                  ▼                ▼             ▼
            ┌──────────┐    ┌────────────┐ ┌──────────┐
            │ routing  │    │ submission │ │ tracker  │
            │  :8005   │    │   :8006    │ │  :8007   │
            └──────────┘    └────────────┘ └──────────┘
                  │                │             │
                  ▼                ▼             ▼
                  Redis (pub/sub) + Postgres (UCO state)
```

## Folder layout

```
grievance-system/
├── shared-schema/        # UCO contract (Python pkg)
├── service-gateway/      # Public API + WebSocket
├── service-chatbot/      # Stage 0 — Claude Haiku dialogue
├── service-location/     # Map reverse-geocode
├── service-nlu/          # Stage 2 — preprocess
├── service-classifier/   # Stage 3 — multi-head (stub for now)
├── service-routing/      # Stage 5 — portal lookup
├── service-submission/   # Stage 8 — plug-and-play adapters
├── service-tracker/      # Stage 10 — status polling
└── web-frontend/         # React + Vite + Tailwind + i18n
```

Each service is independently deployable.

## Languages

UI + bot replies support:
- **हिंदी** (Hindi, Devanagari)
- **English**
- **Hinglish** (Roman Hindi, default)

Switch any time via top-right language button.

## Quick start

### 1. Clone + configure

```bash
cd /Users/hariom/grievance-system
cp .env.example .env
# Edit .env to set ANTHROPIC_API_KEY
# (MAPPLS_API_KEY is optional — will fall back to OpenStreetMap)
```

### 2. Run with Docker

```bash
docker compose up --build
```

### 3. Open

- Frontend: http://localhost:5173
- Gateway: http://localhost:8000/healthz
- Chatbot: http://localhost:8001/healthz

## Run a single service locally (without Docker)

```bash
# Install shared schema once
pip install -e ./shared-schema

# Then any service:
cd service-chatbot
pip install -r requirements.txt
ANTHROPIC_API_KEY=YOUR_ANTHROPIC_KEY REDIS_HOST=localhost \
  uvicorn app.main:app --reload --port 8001
```

## Languages of the underlying technology

- **Backend**: Python 3.11, FastAPI, async
- **Frontend**: React 18, TypeScript, Vite, Tailwind, react-i18next
- **Storage**: Postgres 16 (UCO), Redis 7 (sessions + pub/sub)
- **LLM**: Claude Haiku 4.5 (dialogue), Sonnet 4.6 (Tier-3 reasoning, future)
- **Map**: OpenStreetMap (Leaflet); Mappls in production

## What's wired up vs stubbed

| Service | Status |
|---|---|
| chatbot | ✅ Full — Claude API + Redis + JSON decision parsing |
| location | ✅ Full — Mappls + OSM fallback + India Post pincode API |
| gateway | ✅ Full — proxy + orchestrator + WebSocket bridge |
| nlu | ✅ Real — normalize + PII + keyword + canonical prepend |
| classifier | 🟡 Rule-based stub (uses domain_hints from NLU) |
| routing | ✅ Real — hierarchical portal lookup |
| submission | 🟡 Mock adapter (returns fake ticket) |
| tracker | 🟡 Stub (returns fake history) |

The pipeline runs end-to-end in the demo. Replace classifier+submission with real models/adapters when ready.

## Test the chatbot directly

```bash
curl -X POST http://localhost:8000/api/v1/chat \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "test-user-1",
    "message": "bijli nahi aa rahi 3 din se",
    "language_preference": "hinglish"
  }'
```

Response:
```json
{
  "reply": "Theek hai, bijli ki samasya samajh aa gayi. Apni location map par pin karein...",
  "session_id": "...",
  "complaint_id": "...",
  "intent": "COMPLAINT_NEW",
  "state": "AWAITING_LOCATION",
  "needs_location_pin": true,
  "pipeline_triggered": true
}
```
