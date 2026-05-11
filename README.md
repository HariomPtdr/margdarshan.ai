# Margdarshan.ai — Multilingual Grievance Redressal System

BGI Hackathon 2026 · Team: Merge Conflict (ID 2515) · Problem: BT1P1

A conversational AI platform that lets any citizen describe a problem in **Hindi, English, or Hinglish** — including voice — and automatically performs the entire downstream pipeline: language understanding, department classification, location-aware portal routing, semantic deduplication, portal-specific field collection, submission, periodic status tracking, and resolution notification.

The same backend powers a second product surface — a **Department / Government Dashboard** — where reviewers monitor complaints, audit AI decisions, override classifications, and watch tamper-evident audit chains.

> The name *margdarshan* means "guidance / showing the way" — the system guides citizens to the right portal out of more than seventy government grievance destinations.

---

## Quick start

Bring up the entire stack (10 services + Postgres + Redis + frontend) with Docker:

```bash
cp .env.example .env
# Edit .env: at minimum set ANTHROPIC_API_KEY (Claude Haiku 4.5)
# Optional: LOCATIONIQ_API_KEY (falls back to OpenStreetMap if missing)

docker compose up -d
```

Then open:

- **Citizen UI:** http://localhost:5173
- **Gateway API:** http://localhost:8000/healthz
- **OpenAPI docs:** http://localhost:8000/docs

The admin dashboard is the same SPA — log in with the bootstrapped admin account:

| field    | value                    |
|----------|--------------------------|
| email    | `admin@margdarshan.ai`   |
| password | `Admin@1234`             |

(Override via `ADMIN_EMAIL` / `ADMIN_PASSWORD` in `.env`.)

End-to-end smoke test:

```bash
bash scripts/smoke_test.sh
```

---

## What the citizen flow does

1. **Chat in your language.** Type or speak in Hindi, English, or Hinglish ("bijli 3 din se nahi aa rahi", "no electricity for 3 days", or the mix). The bot replies in the same language.
2. **AI understands.** Claude Haiku extracts intent, entities, and complaint structure. A keyword/domain map produces hints for the classifier.
3. **AI classifies.** A trained MuRIL model (or a rule-based fallback) predicts the **department** (25 classes), **sub-category** (142 classes), **priority**, and **sentiment** with a calibrated confidence score. Low-confidence cases trigger a clarifying question instead of acting on a wrong guess.
4. **Pin your location.** A Leaflet/OpenStreetMap modal collects the exact spot. We reverse-geocode (LocationIQ → OSM Nominatim fallback) and look up the pincode (offline cache → India Post API).
5. **AI picks the right portal.** A hierarchical lookup against a 70-portal registry: **Regional > State-specific > State catch-all > Central-specific > Central catch-all**. A power cut in Bhopal goes to MPPKVVCL, not to a national catch-all that would forward it for weeks.
6. **AI deduplicates.** Multilingual S-BERT embeddings (`paraphrase-multilingual-MiniLM-L12-v2`, cosine ≥ 0.85) detect whether the same person — or other citizens in the same district — already filed this complaint.
7. **Conversational field collection.** Portal-specific fields are asked one at a time in chat, with 11 regex validators (pincode, mobile, Aadhaar Verhoeff checksum, etc.). Many fields are auto-prefilled from the conversation.
8. **Plug-and-play submission.** Portal adapters (CPGRAMS, MP CM Helpline 181, MPPKVVCL) handle portal-specific schemas. A 7-attempt exponential backoff retry covers transient portal outages (`1m → 2m → 5m → 15m → 1h → 4h → 24h`).
9. **Adaptive status tracking.** Polls the portal every 1h for the first day, 6h for the first week, daily after that, until a terminal state. Status strings are normalised into a canonical state machine.
10. **Bilingual notifications.** Every status change pings the citizen on WhatsApp (mock Twilio) in Hindi first, then English. RESOLVED triggers a satisfaction prompt — reply 1/2 closes the feedback loop.

---

## What the department dashboard does

- **Stats overview** — hero cards for total complaints, duplicates, by status, by department, by district, plus the 10 most recent.
- **Portal registry view** — full list of 70 portals with authority, districts covered, helpline, online-filing flag, complaint count routed to each.
- **Complaints list** — filterable by status / department / district, with priority and sentiment badges and duplicate flags.
- **Complaint drill-down** — filer info (PII-masked), classification with top-3 alternatives, portal routing explanation, collected fields, full SHA-256 hash-chained audit timeline.
- **Review form** — reviewers rate the AI (thumbs up/down) and can override department, sub-category, priority, sentiment. Every override lands in `complaint_reviews` and becomes training feedback for the next model cycle.
- **Duplicate-filer detection** — surfaces both repeat filers and cross-user clusters of the same incident (e.g., 30 households reporting the same transformer fault).
- **Routing explanation** — for every complaint, the exact rule that fired (tier matched, district match, fallback path).
- **API trace** — animated 5-step demo view showing the live JSON exchanges between services for a single complaint.

---

## Architecture

```
                          ┌─────────────────────────────────────────────┐
                          │       web-frontend  (port 5173)             │
                          │ React 18 · Vite · Tailwind · i18n · Leaflet │
                          │  Citizen chat UI  +  Department dashboard   │
                          └─────────────────────────────────────────────┘
                                              │
                                              ▼
                          ┌─────────────────────────────────────────────┐
                          │     service-gateway  (port 8000)            │
                          │ Public REST + WebSocket · JWT auth          │
                          │ Pipeline orchestrator · SHA-256 audit chain │
                          │ S-BERT dedup · Submission retry scheduler   │
                          └─────────────────────────────────────────────┘
                                              │
        ┌─────────────────┬────────────┬──────┴──────┬────────────┬──────────────────┐
        ▼                 ▼            ▼             ▼            ▼                  ▼
┌──────────────┐ ┌──────────────┐ ┌──────────┐ ┌──────────┐ ┌────────────┐  ┌──────────────┐
│   chatbot    │ │   location   │ │   nlu    │ │classifier│ │  routing   │  │  submission  │
│    :8001     │ │    :8002     │ │   :8003  │ │  :8004   │ │   :8005    │  │    :8006     │
│ Claude Haiku │ │ LocationIQ + │ │ State    │ │ MuRIL or │ │ 70-portal  │  │ Adapters:    │
│ field-fill   │ │ OSM Nominatim│ │ machine  │ │rule-based│ │ Regional/  │  │ CPGRAMS,     │
│ session mgmt │ │ India Post   │ │ + Claude │ │ 25 dept  │ │ State/     │  │ MPCM181,     │
│              │ │ pincode      │ │ NLU      │ │ 142 subs │ │ Central    │  │ MPPKVVCL,    │
│              │ │              │ │          │ │          │ │ hierarchy  │  │ generic mock │
└──────────────┘ └──────────────┘ └──────────┘ └──────────┘ └────────────┘  └──────────────┘
                                                                                     │
                                                                                     ▼
                                                                             ┌──────────────┐
                                                                             │   tracker    │
                                                                             │    :8007     │
                                                                             │ Adaptive     │
                                                                             │ status poll  │
                                                                             │ + bilingual  │
                                                                             │ WhatsApp     │
                                                                             └──────────────┘

                       Redis (pub/sub, sessions, retry queues, feedback queue)
                       Postgres (users, complaints, messages, audit chain, reviews)
```

The pipeline event bus is **Redis Pub/Sub** on a single `pipeline:all` channel. Each stage emits `PipelineEvent(complaint_id, stage, status, payload)` messages; the gateway orchestrator subscribes and triggers the next stage. The same events stream live to the frontend over WebSocket so the right-hand panel lights up in real time.

---

## Folder layout

```
margdarshan.ai/
├── shared-schema/          # UCO + PipelineEvent + chat Pydantic models
├── service-gateway/        # Public API, auth, orchestrator, audit chain, dedup
├── service-chatbot/        # Thin chat interface, session, field-collection
├── service-location/       # Reverse geocode + pincode lookup
├── service-nlu/            # State machine, intent, entities, Claude NLU
├── service-classifier/     # MuRIL + 4 sklearn heads (+ rule-based fallback)
├── service-routing/        # 70-portal hierarchical lookup
├── service-submission/     # Adapter pattern + 7-attempt exponential backoff
├── service-tracker/        # Adaptive poller, status normaliser, notifications
├── web-frontend/           # React + Vite SPA (citizen + admin)
├── dataset/                # Training data & dataset-collection Google Form
├── scripts/
│   ├── smoke_test.sh       # End-to-end stack health probe
│   └── build_docs_pdf.py   # Generates the technical PDF (reportlab)
└── docs/
    └── Margdarshan-ai-Technical-Doc.pdf  # 35-page deep-dive
```

Every service has its own `Dockerfile`, `requirements.txt`, and FastAPI app. Independent deploy.

---

## Technology

| Layer            | Choice                                                                                       |
|------------------|----------------------------------------------------------------------------------------------|
| Backend          | Python 3.11 · FastAPI 0.115 · uvicorn · asyncpg · httpx · pydantic v2                         |
| Database         | PostgreSQL 16 (JSONB for the UCO blob, `FLOAT8[]` for S-BERT vectors, partial indices)         |
| Cache + Bus      | Redis 7 (pub/sub, sessions, retry queues)                                                     |
| Conversational LLM | Anthropic **Claude Haiku 4.5** (`claude-haiku-4-5-20251001`) — temperature 0.2, ~700 ms latency |
| Classifier       | Fine-tuned **MuRIL** (`google/muril-base-cased`) + 4 sklearn heads (dept / sub-cat / priority / sentiment) — toggleable via `USE_RULE_BASED_CLASSIFIER` |
| Dedup            | **sentence-transformers** `paraphrase-multilingual-MiniLM-L12-v2` (117 MB, 384-dim)            |
| Maps             | LocationIQ (preferred, 5k/day free) → OpenStreetMap Nominatim fallback                        |
| Frontend         | React 18 · TypeScript · Vite 5 · Tailwind 3 · react-i18next · Leaflet + react-leaflet         |
| Auth             | bcrypt + PyJWT (HS256), JWT in `localStorage`                                                  |
| Audit            | SHA-256 hash chain per complaint over the `complaint_events` table                            |

---

## Languages supported

UI strings, bot replies, and notifications all support:

- **हिन्दी** (Hindi, Devanagari)
- **English**
- **Hinglish** (Roman-script Hindi, default for new users)

Switch any time via the top-right language selector. Voice input uses the browser Web Speech API with `hi-IN` / `en-IN` locales.

---

## Service status — what's wired vs stubbed

| Service      | Status | Notes                                                                                                  |
|--------------|--------|--------------------------------------------------------------------------------------------------------|
| gateway      | ✅ Full | Public API, JWT auth, pipeline orchestrator, SHA-256 audit, S-BERT dedup, retry scheduler              |
| chatbot      | ✅ Full | Thin proxy + field-collection mode (Claude Haiku extract_field)                                        |
| nlu          | ✅ Full | State machine, intent classifier, entity extractor, language detect, Claude-based decision JSON         |
| location     | ✅ Full | LocationIQ → OSM fallback, offline pincode cache + India Post API                                       |
| classifier   | ✅ Full | MuRIL trained (dept F1 0.91, sub-cat ~0.85). Currently running rule-based (`USE_RULE_BASED_CLASSIFIER=true`); flip the env var to enable MuRIL |
| routing      | ✅ Full | 70 portals, hierarchical lookup, specificity sort                                                       |
| submission   | ✅ Full | CPGRAMS, MPCM181, MPPKVVCL adapters (mocked external POST for the hackathon); generic adapter fallback   |
| tracker      | ✅ Full | Adaptive 1h/6h/24h polling, status normaliser, mock Twilio WhatsApp, feedback queue                     |
| web-frontend | ✅ Full | Citizen chat + admin dashboard (stats, portals, drill-down, review form, duplicate filers, API trace)   |

The mocks are in the outbound POST to each government portal (since we don't have department MoUs yet). Everything **above** that boundary — classification, routing, dedup, retry, tracking, notifications, audit — is real.

---

## Test the chat API directly

```bash
curl -X POST http://localhost:8000/api/v1/chat \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "test-user-1",
    "message": "bijli 3 din se nahi aa rahi, Bhopal MP",
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

Then attach the location pin and the pipeline runs all the way through to a portal ticket id.

---

## Run a single service locally (without Docker)

```bash
pip install -e ./shared-schema

cd service-chatbot
pip install -r requirements.txt
ANTHROPIC_API_KEY=sk-ant-... REDIS_HOST=localhost \
  uvicorn app.main:app --reload --port 8001
```

Other services follow the same pattern; ports and env vars are listed in `.env.example`.

---

## Documentation

For an in-depth technical walkthrough of every layer — including AI/ML rationale, training methodology, accuracy metrics, comparative analysis against CPGRAMS / MP CM Helpline 181 / MyGov, and the future roadmap — see:

**[`docs/Margdarshan-ai-Technical-Doc.pdf`](docs/Margdarshan-ai-Technical-Doc.pdf)** (35 pages)

Regenerate with `python3 scripts/build_docs_pdf.py`.

---

## Hackathon

Built for **BGI Hackathon 2026**, problem statement **BT1P1**, by **Team Merge Conflict** (Team ID 2515).
