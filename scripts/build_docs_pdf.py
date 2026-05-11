"""Generate the comprehensive technical PDF for Margdarshan.ai.

Run: python3 scripts/build_docs_pdf.py
Output: docs/Margdarshan-ai-Technical-Doc.pdf
"""

from __future__ import annotations

import os
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm, mm
from reportlab.platypus import (
    BaseDocTemplate,
    Frame,
    PageBreak,
    PageTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
    KeepTogether,
)
from reportlab.platypus.flowables import HRFlowable
from reportlab.pdfgen import canvas


OUT_DIR = Path(__file__).resolve().parent.parent / "docs"
OUT_DIR.mkdir(exist_ok=True)
OUT_PATH = OUT_DIR / "Margdarshan-ai-Technical-Doc.pdf"


# ─── Styles ─────────────────────────────────────────────────────────────────
BRAND_DARK = colors.HexColor("#0F172A")
BRAND_PRIMARY = colors.HexColor("#1E3A8A")
BRAND_ACCENT = colors.HexColor("#F59E0B")
BRAND_GREEN = colors.HexColor("#15803D")
LIGHT_GREY = colors.HexColor("#F1F5F9")
MID_GREY = colors.HexColor("#475569")
CODE_BG = colors.HexColor("#0F172A")


styles = getSampleStyleSheet()


def make_styles():
    s = {}
    s["title"] = ParagraphStyle(
        "title", parent=styles["Heading1"],
        fontName="Helvetica-Bold", fontSize=30, leading=36,
        textColor=BRAND_DARK, spaceAfter=8, alignment=0,
    )
    s["subtitle"] = ParagraphStyle(
        "subtitle", parent=styles["Normal"],
        fontName="Helvetica", fontSize=14, leading=18,
        textColor=MID_GREY, spaceAfter=18,
    )
    s["h1"] = ParagraphStyle(
        "h1", parent=styles["Heading1"],
        fontName="Helvetica-Bold", fontSize=22, leading=26,
        textColor=BRAND_PRIMARY, spaceBefore=20, spaceAfter=10, keepWithNext=1,
    )
    s["h2"] = ParagraphStyle(
        "h2", parent=styles["Heading2"],
        fontName="Helvetica-Bold", fontSize=16, leading=20,
        textColor=BRAND_DARK, spaceBefore=14, spaceAfter=6, keepWithNext=1,
    )
    s["h3"] = ParagraphStyle(
        "h3", parent=styles["Heading3"],
        fontName="Helvetica-Bold", fontSize=12.5, leading=16,
        textColor=BRAND_DARK, spaceBefore=10, spaceAfter=4, keepWithNext=1,
    )
    s["h4"] = ParagraphStyle(
        "h4", parent=styles["Heading4"],
        fontName="Helvetica-Bold", fontSize=11, leading=14,
        textColor=BRAND_PRIMARY, spaceBefore=8, spaceAfter=3, keepWithNext=1,
    )
    s["body"] = ParagraphStyle(
        "body", parent=styles["Normal"],
        fontName="Helvetica", fontSize=10, leading=14,
        textColor=BRAND_DARK, spaceAfter=6, alignment=4,  # justified
    )
    s["bullet"] = ParagraphStyle(
        "bullet", parent=styles["Normal"],
        fontName="Helvetica", fontSize=10, leading=14,
        textColor=BRAND_DARK, leftIndent=14, bulletIndent=2, spaceAfter=2,
    )
    s["code"] = ParagraphStyle(
        "code", parent=styles["Code"],
        fontName="Courier", fontSize=8.5, leading=11,
        textColor=colors.white, backColor=CODE_BG,
        leftIndent=8, rightIndent=8, spaceBefore=4, spaceAfter=8,
        borderPadding=(6, 8, 6, 8),
    )
    s["small"] = ParagraphStyle(
        "small", parent=styles["Normal"],
        fontName="Helvetica", fontSize=9, leading=12,
        textColor=MID_GREY, spaceAfter=4,
    )
    s["caption"] = ParagraphStyle(
        "caption", parent=styles["Normal"],
        fontName="Helvetica-Oblique", fontSize=9, leading=11,
        textColor=MID_GREY, spaceAfter=10,
    )
    s["callout"] = ParagraphStyle(
        "callout", parent=styles["Normal"],
        fontName="Helvetica", fontSize=10, leading=14,
        textColor=BRAND_DARK, backColor=LIGHT_GREY,
        leftIndent=10, rightIndent=10, borderPadding=(8, 10, 8, 10),
        spaceBefore=6, spaceAfter=8,
    )
    return s


S = make_styles()


def P(t, style="body"):
    """Paragraph helper."""
    return Paragraph(t, S[style])


def H(t, level=1):
    return Paragraph(t, S[f"h{level}"])


def code(text):
    text = text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    text = text.replace("\n", "<br/>")
    text = text.replace(" ", "&nbsp;")
    return Paragraph(text, S["code"])


def bullets(items):
    out = []
    for it in items:
        out.append(Paragraph(f"&bull;&nbsp;&nbsp;{it}", S["bullet"]))
    return out


def kv_table(rows, col_widths=None):
    """Two-column key/value table."""
    if col_widths is None:
        col_widths = [4.5 * cm, 11.5 * cm]
    data = []
    for k, v in rows:
        kp = Paragraph(f"<b>{k}</b>", S["body"])
        vp = Paragraph(v, S["body"])
        data.append([kp, vp])
    t = Table(data, colWidths=col_widths, hAlign="LEFT")
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (0, -1), LIGHT_GREY),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("INNERGRID", (0, 0), (-1, -1), 0.25, colors.HexColor("#CBD5E1")),
        ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#CBD5E1")),
        ("LEFTPADDING", (0, 0), (-1, -1), 8),
        ("RIGHTPADDING", (0, 0), (-1, -1), 8),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
    ]))
    return t


def header_table(rows, col_widths=None, header_color=BRAND_PRIMARY):
    """Table with header row."""
    data = [[Paragraph(f"<b><font color='white'>{c}</font></b>", S["body"]) for c in rows[0]]]
    for row in rows[1:]:
        data.append([Paragraph(c, S["body"]) for c in row])
    t = Table(data, colWidths=col_widths, hAlign="LEFT", repeatRows=1)
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), header_color),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, LIGHT_GREY]),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("INNERGRID", (0, 0), (-1, -1), 0.25, colors.HexColor("#CBD5E1")),
        ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#CBD5E1")),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
    ]))
    return t


def hr():
    return HRFlowable(width="100%", thickness=0.6, color=colors.HexColor("#CBD5E1"), spaceBefore=6, spaceAfter=10)


def page_decoration(canv: canvas.Canvas, doc):
    """Footer + page number."""
    canv.saveState()
    canv.setStrokeColor(colors.HexColor("#CBD5E1"))
    canv.setLineWidth(0.4)
    canv.line(1.6 * cm, 1.3 * cm, A4[0] - 1.6 * cm, 1.3 * cm)
    canv.setFont("Helvetica", 8)
    canv.setFillColor(MID_GREY)
    canv.drawString(1.6 * cm, 0.9 * cm, "Margdarshan.ai  -  Comprehensive Technical Documentation  -  BGI Hackathon 2026")
    canv.drawRightString(A4[0] - 1.6 * cm, 0.9 * cm, f"Page {doc.page}")
    canv.restoreState()


def cover_decoration(canv, doc):
    """Cover page banner."""
    canv.saveState()
    # Top dark band
    canv.setFillColor(BRAND_DARK)
    canv.rect(0, A4[1] - 7 * cm, A4[0], 7 * cm, fill=1, stroke=0)
    # Saffron accent stripe
    canv.setFillColor(BRAND_ACCENT)
    canv.rect(0, A4[1] - 7.3 * cm, A4[0], 0.3 * cm, fill=1, stroke=0)
    # Title
    canv.setFillColor(colors.white)
    canv.setFont("Helvetica-Bold", 36)
    canv.drawString(1.8 * cm, A4[1] - 3.2 * cm, "Margdarshan.ai")
    canv.setFont("Helvetica", 16)
    canv.drawString(1.8 * cm, A4[1] - 4.2 * cm, "Multilingual AI Grievance Redressal Platform")
    canv.setFont("Helvetica-Oblique", 11)
    canv.setFillColor(colors.HexColor("#CBD5E1"))
    canv.drawString(1.8 * cm, A4[1] - 5.0 * cm, "Comprehensive Technical Documentation")
    canv.setFont("Helvetica", 10)
    canv.drawString(1.8 * cm, A4[1] - 6.0 * cm, "BGI Hackathon 2026  -  Team: Merge Conflict  -  Problem BT1P1")
    # Footer bar
    canv.setFillColor(BRAND_DARK)
    canv.rect(0, 0, A4[0], 1.4 * cm, fill=1, stroke=0)
    canv.setFont("Helvetica", 9)
    canv.setFillColor(colors.HexColor("#CBD5E1"))
    canv.drawString(1.8 * cm, 0.5 * cm, "Generated 2026-05-12  -  10 microservices  -  Hindi / English / Hinglish")
    canv.restoreState()


# ─── Content ─────────────────────────────────────────────────────────────────
def build_story():
    story = []

    # ───────── Cover ─────────
    story.append(Spacer(1, 10 * cm))
    story.append(P("This document provides an in-depth technical walkthrough of every layer of the Margdarshan.ai grievance redressal system, intended for technical evaluators, contributors, and future maintainers. It covers the problem context, end-to-end pipeline, machine learning models, software architecture, frontend, backend, database schema, evaluation, comparative analysis with existing systems, and the future roadmap.", "callout"))
    story.append(Spacer(1, 0.5 * cm))
    story.append(P("<b>Contents</b>", "h3"))
    toc = [
        "1.  Problem Statement and Solution Overview",
        "2.  System Architecture at a Glance",
        "3.  Citizen-Facing Flow - Layer by Layer",
        "4.  Department / Government Dashboard Flow - Layer by Layer",
        "5.  AI / ML / NLP Foundations Used in the System",
        "6.  Model Training, Evaluation, and Accuracy",
        "7.  Software Engineering Concepts in Play",
        "8.  Comparative Analysis with Existing Systems",
        "9.  Future Enhancements and Roadmap",
        "10. Appendix - APIs, Schemas, Deployment",
    ]
    for line in toc:
        story.append(P(line, "bullet"))
    story.append(PageBreak())

    # ───────── 1. Problem Statement ─────────
    story.append(H("1. Problem Statement and Solution Overview", 1))
    story.append(P(
        "<b>The problem.</b> India runs more than seventy public grievance portals across central ministries, state departments, "
        "and city utilities. A typical citizen with a real complaint - say a power cut in Bhopal or a missing pension "
        "credit - has to (a) identify the correct portal out of dozens, (b) read English-only instructions, "
        "(c) fill long forms with portal-specific fields they may not understand, and (d) keep checking different "
        "websites for status. The result: most genuine grievances either never get filed or get filed at the wrong "
        "portal where they are eventually rejected without action. Duplicate filings and \"complaint fatigue\" further "
        "clog official systems and drown out signal.",
    ))
    story.append(P(
        "<b>Our solution.</b> Margdarshan.ai (Hindi <i>margdarshan</i>: guidance / showing the way) is an AI-driven, multilingual "
        "conversational platform that lets any citizen describe a problem in Hindi, English, or Hinglish - in plain "
        "everyday language - and automatically performs the entire downstream pipeline: language understanding, "
        "department classification, location-aware portal routing, semantic deduplication, portal-specific field "
        "collection, submission, periodic status tracking, and resolution notification. The same backend powers a "
        "second product surface - a Department / Government Dashboard - where reviewers monitor complaints, audit "
        "AI decisions, override classifications, and watch tamper-evident event chains.",
    ))
    story.append(P("<b>Concretely the platform does:</b>", "h3"))
    for b in [
        "Accepts complaints in Hindi (Devanagari), English, and Hinglish (Roman-script Hindi) - including voice input.",
        "Uses a large language model (Claude Haiku 4.5) to extract complaint structure and slot-fill missing details.",
        "Classifies into 25 departments and 142 sub-categories with a fine-tuned MuRIL transformer (with a rule-based fallback).",
        "Routes to the most specific portal among 70 registered government portals (regional > state > central hierarchy).",
        "Deduplicates against past complaints using S-BERT multilingual embeddings (cosine threshold 0.85).",
        "Collects portal-specific fields conversationally - rather than dropping the user into another website.",
        "Submits via portal-specific adapters (CPGRAMS, MP CM Helpline 181, MPPKVVCL) with 7-attempt exponential backoff.",
        "Polls each portal at adaptive intervals (1h to 24h) and notifies citizens in their own language over WhatsApp.",
        "Maintains a SHA-256 hash-chained audit trail so every decision is verifiable end-to-end.",
        "Surfaces a real-time admin dashboard with stats, audit chains, AI review controls, and routing explanations.",
    ]:
        story.append(P(f"&bull; {b}", "bullet"))

    story.append(P("<b>Why this matters:</b>", "h3"))
    story.append(P(
        "Public grievance redressal is the most direct interface a citizen has with the state. Today that interface is "
        "fragmented, English-biased, and indifferent to context. Margdarshan.ai collapses the discovery and submission "
        "cost to a single conversation, while keeping every decision auditable so it can survive regulatory scrutiny.",
    ))

    story.append(PageBreak())

    # ───────── 2. Architecture overview ─────────
    story.append(H("2. System Architecture at a Glance", 1))
    story.append(P(
        "Margdarshan.ai is implemented as ten independent containerised services orchestrated by Docker Compose, "
        "with Redis Pub/Sub as the event bus and PostgreSQL as the source of truth. The system is built on the "
        "<b>microservices</b> pattern - each stage of the pipeline lives in its own service so it can be deployed, "
        "scaled, debugged, and replaced independently.",
    ))

    story.append(P("<b>The ten services and their ports:</b>", "h3"))
    services_tbl = [
        ["Service", "Port", "Role"],
        ["postgres", "5432", "Source of truth for users, complaints, messages, audit chain, reviews."],
        ["redis", "6379", "Pub/Sub event bus, session cache, retry queues, feedback queue."],
        ["service-gateway", "8000", "Public API, JWT auth, pipeline orchestrator, audit chain writer."],
        ["service-chatbot", "8001", "Thin conversation interface. Proxies every turn to NLU."],
        ["service-location", "8002", "Reverse geocoding (LocationIQ + OSM Nominatim) and pincode lookup."],
        ["service-nlu", "8003", "Conversation brain: state machine, decision tree, Claude-Haiku NLU."],
        ["service-classifier", "8004", "Department/sub-category/priority/sentiment classifier (MuRIL or rule-based)."],
        ["service-routing", "8005", "Portal lookup - 70 portals, hierarchical Regional/State/Central matching."],
        ["service-submission", "8006", "Portal adapters (CPGRAMS, MPCM181, MPPKVVCL, generic mock)."],
        ["service-tracker", "8007", "Adaptive status polling + bilingual WhatsApp notifications."],
        ["web-frontend", "5173", "React + Vite SPA - citizen chat UI and admin dashboard."],
    ]
    story.append(header_table(services_tbl, col_widths=[3.6*cm, 1.6*cm, 11*cm]))
    story.append(Spacer(1, 0.4*cm))

    story.append(P("<b>The pipeline:</b> citizen message -> chatbot -> NLU -> classifier -> routing -> dedup -> field collection -> submission -> tracker -> notification -> citizen.", "callout"))

    story.append(P("<b>Why microservices and not a monolith?</b>", "h3"))
    story.append(P(
        "(a) Different stages have radically different runtime profiles - the classifier needs PyTorch and 1.5 GB of RAM for MuRIL inference, "
        "the chatbot is largely I/O-bound talking to Anthropic, and the location service is just an HTTP proxy. "
        "Putting them together would lock the whole system to the heaviest dependency set. "
        "(b) Independent deploy: when we re-train MuRIL we only rebuild service-classifier. "
        "(c) Independent scaling: the chatbot can be scaled horizontally without touching the database-bound gateway. "
        "(d) Independent failure: if the tracker poller is degraded, complaint submission still works. "
        "(e) Clear contracts: each service exposes a small typed FastAPI surface, which becomes the integration contract.",
    ))

    story.append(P("<b>Why Redis Pub/Sub for the event bus?</b>", "h3"))
    story.append(P(
        "Redis is already in the stack as a session and cache store, so adding Pub/Sub is zero extra ops. We don't need "
        "Kafka-grade durability for a hackathon prototype, and the events we care about (stage transitions of a single "
        "complaint over a few minutes) fit naturally in pub-sub. The orchestrator listens on a single <code>pipeline:all</code> "
        "channel and routes events to the appropriate next-stage trigger. If we ever need at-least-once delivery for "
        "audit-critical stages we can swap the bus for Kafka or Redis Streams without changing service code - the "
        "event schema is already a typed Pydantic model in <code>shared-schema/events.py</code>.",
    ))

    story.append(P("<b>Why PostgreSQL?</b>", "h3"))
    story.append(P(
        "We need (a) ACID guarantees for the audit chain - inserting an event and its hash must be transactional, "
        "(b) JSONB to store the entire UCO (Unified Complaint Object) pipeline state without rigid column schemas, "
        "(c) array columns to store 384-dimensional S-BERT embeddings for semantic dedup, "
        "and (d) battle-tested admin tooling. Postgres gives us all four. A document database (MongoDB) would have made "
        "the audit chain harder to reason about and lost ACID; a pure relational design would have made the rapidly-evolving "
        "UCO blob painful.",
    ))

    story.append(PageBreak())

    # ───────── 3. Citizen flow - layer by layer ─────────
    story.append(H("3. Citizen-Facing Flow - Layer by Layer", 1))
    story.append(P(
        "The citizen flow is split into seven logical layers running across two services on the backend, plus the React frontend. "
        "Every user message travels through all seven layers before producing a reply.",
    ))

    # Layer 1 - Frontend chat
    story.append(H("Layer 1 - Frontend Chat Interface (React)", 2))
    story.append(P(
        "<b>Concept.</b> A three-panel single-page application: left panel lists the citizen's past complaints, "
        "centre panel is the conversational chat (text + voice), right panel is a live pipeline visualisation that "
        "lights up each stage in real time as backend events arrive over WebSocket.",
    ))
    story.append(P("<b>Stack and why we chose it:</b>", "h4"))
    for b in [
        "<b>React 18 + Vite</b> - fast HMR, modern JSX runtime, no Webpack baggage. Vite is dramatically faster than CRA for dev iteration.",
        "<b>TypeScript 5.6</b> - the pipeline payloads are non-trivial typed unions; TS catches integration drift between gateway and UI.",
        "<b>Tailwind CSS 3.4</b> - utility-first lets a small team converge on a consistent visual language without bikeshedding stylesheet structure.",
        "<b>React Context (no Redux)</b> - the global state we actually need (auth, chat, pipeline) is small and event-driven; Redux would be ceremony for no benefit.",
        "<b>react-i18next</b> - Hindi / English / Hinglish swapping with browser auto-detect and a clean t('key') call site.",
        "<b>Leaflet + OpenStreetMap</b> - the location pinning modal needs a free, offline-friendly map tile source; Leaflet is the de-facto standard with React Leaflet bindings.",
        "<b>Web Speech API</b> - native browser voice input (hi-IN, en-IN). No third-party STT cost, works fully on-device.",
    ]:
        story.append(P(f"&bull; {b}", "bullet"))

    story.append(P("<b>How the UI talks to the backend:</b>", "h4"))
    story.append(P(
        "All HTTP calls go through <code>src/lib/api.ts</code> against the gateway URL from <code>VITE_GATEWAY_URL</code>. "
        "Auth state is a JWT in <code>localStorage</code> under key <code>margdarshan_token</code>. "
        "The live pipeline panel subscribes over <code>ws://gateway/ws/pipeline/{complaint_id}</code> and receives JSON "
        "<code>PipelineEvent</code> messages on every stage transition.",
    ))
    story.append(P("<b>Why not Next.js / SSR?</b> The app is authenticated and dynamic by definition - there is "
                  "no SEO surface, no static content to render. SPA + REST + WebSocket is the simplest correct choice.", "small"))

    # Layer 2 - Chatbot proxy
    story.append(H("Layer 2 - Chatbot Service (Thin Interface)", 2))
    story.append(P(
        "<b>Role.</b> service-chatbot (port 8001) is intentionally <b>thin</b>. Every incoming message is forwarded to the NLU service, "
        "which owns the conversation brain. The chatbot's only responsibilities are session bookkeeping in Redis, rate limiting "
        "(60 messages/hour per user), and call-back hooks for portal field collection.",
    ))
    story.append(P("<b>Why a thin chatbot layer at all?</b> Decoupling presentation from decision logic. Tomorrow when we add a "
                  "WhatsApp bot or an IVR voice front-end, both can call the same chatbot service and reuse the entire NLU "
                  "brain without re-implementing state.", "small"))
    story.append(P("<b>Key files:</b>", "h4"))
    story.append(P("<code>main.py</code> - FastAPI app, <code>POST /api/v1/chat</code>, <code>POST /api/v1/session/notify</code>, <code>POST /api/v1/session/reset</code>.<br/>"
                  "<code>session.py</code> - Redis-backed session store (TTL 6 hours, max 20 history turns).<br/>"
                  "<code>chatbot.py</code> - Field-collection mode using Anthropic Claude (FIELD_EXTRACTION_PROMPT).<br/>"
                  "<code>config.py</code> - Claude model id, max tokens, temperature, rate limits."))

    # Layer 3 - NLU brain
    story.append(H("Layer 3 - NLU Service (Conversation Brain)", 2))
    story.append(P(
        "<b>Role.</b> service-nlu (port 8003) is the heart of the conversation. It does five jobs:",
    ))
    for b in [
        "<b>Language detection</b> - Devanagari vs Roman script vs mixed. Decides whether the user is in Hindi, English, or Hinglish.",
        "<b>Intent classification</b> - GREETING, SMALLTALK, COMPLAINT_NEW, COMPLAINT_CONTINUE, STATUS_CHECK, CLARIFICATION_REPLY, ABUSE, OFF_TOPIC.",
        "<b>Entity extraction</b> - phone, pincode, aadhaar, consumer_no, account_no, vehicle_no, email, organisation, person, duration, infrastructure.",
        "<b>Slot filling and state machine</b> - tracks where the conversation is (IDLE - COLLECTING - READY - AWAITING_LOCATION - CONFIRMING - FIELD_COLLECTION - SUBMITTED).",
        "<b>Domain keyword extraction</b> - maps surface words (\"bijli\", \"transformer\", \"पानी\", \"FIR\") to domain hints used by the classifier.",
    ]:
        story.append(P(f"&bull; {b}", "bullet"))

    story.append(P("<b>AI model used: Claude Haiku 4.5</b> (model id <code>claude-haiku-4-5-20251001</code>).", "h4"))
    story.append(P(
        "Specifically, we use Anthropic's Claude Haiku for two things: (a) the high-level NLU decision (intent + completeness + "
        "next state + reply text) at temperature 0.2 and max 600 tokens, and (b) field extraction during stage 6, where Claude "
        "reads a free-form citizen reply and returns a structured <code>{\"extracted\": ..., \"reply\": ...}</code> JSON object.",
    ))
    story.append(P("<b>Why Claude Haiku specifically:</b>", "h4"))
    for b in [
        "<b>Latency.</b> Haiku 4.5 returns full structured replies in 600 ms - 1.2 s. This matters because the user is waiting on a chat bubble.",
        "<b>Cost.</b> Haiku is roughly 10x cheaper per token than Sonnet and 60x cheaper than Opus - critical when we are paying per chat turn for a public-facing system.",
        "<b>Multilingual quality.</b> Anthropic's models handle Devanagari and Hinglish code-mixing significantly better than GPT-3.5 class models, which we found drop accents and mistranslate idioms (\"3 din se nahi aa rahi\" - \"hasn't been coming for 3 days\" used to get translated as \"hasn't come for 3 dinners\" by smaller models).",
        "<b>Structured-output reliability.</b> Haiku 4.5 reliably emits clean JSON without code fencing in our prompt.",
        "<b>Prompt caching.</b> The system prompt + decision-tree templates are cached on Anthropic's side, slashing per-turn cost.",
    ]:
        story.append(P(f"&bull; {b}", "bullet"))

    story.append(P("<b>Alternatives we considered:</b>", "h4"))
    for b in [
        "<b>Mistral 7B/Codestral.</b> Cheaper but noticeably worse on Hinglish code-mixing in our internal tests; we keep the key in .env but no longer call it.",
        "<b>GPT-4o-mini.</b> Comparable cost, slightly higher latency at the time of writing, weaker on Devanagari proper nouns.",
        "<b>Local IndicBERT / MuRIL for everything.</b> Great for classification but cannot generate conversational replies - they are encoders, not decoders.",
        "<b>Hand-rolled intent classifier.</b> Tried first. Fragile - users say things like \"yaar pichli baar wali shikayat ka kya hua?\" which is a status-check phrased like small talk.",
    ]:
        story.append(P(f"&bull; {b}", "bullet"))

    story.append(P("<b>Domain dictionary excerpt (keywords -> domain hints):</b>", "h4"))
    story.append(code(
        'DOMAIN_DICT = {\n'
        '    # Electricity\n'
        '    "bijli": "electricity", "बिजली": "electricity",\n'
        '    "transformer": "electricity", "meter": "electricity",\n'
        '    "power cut": "electricity", "voltage": "electricity",\n'
        '\n'
        '    # Water\n'
        '    "paani": "water", "पानी": "water", "tanker": "water",\n'
        '\n'
        '    # Roads (word-boundary matched)\n'
        '    "sadak": "roads", "सड़क": "roads", "pothole": "roads",\n'
        '    "नाली": "roads", "highway": "roads",\n'
        '\n'
        '    # Safety / encroachment / noise\n'
        '    "shor": "safety", "loudspeaker": "safety", "kabza": "safety",\n'
        '    ...\n'
        '}\n'
    ))
    story.append(P("<b>Subtle but important:</b> matching uses regex word boundaries so that \"ration\" inside the word \"duration\" does not falsely trigger the PDS domain. This bug bit us early in testing.", "small"))

    story.append(P("<b>State machine (excerpt):</b>", "h4"))
    story.append(code(
        'class StateEnum(str, Enum):\n'
        '    IDLE = "IDLE"\n'
        '    COLLECTING = "COLLECTING"          # gathering complaint text\n'
        '    READY = "READY"                    # complaint complete\n'
        '    AWAITING_LOCATION = "AWAITING_LOCATION"  # waiting for GPS pin\n'
        '    CONFIRMING = "CONFIRMING"          # asking user to confirm submission\n'
        '    FIELD_COLLECTION = "FIELD_COLLECTION"   # filling portal-specific fields\n'
        '    SUBMITTED = "SUBMITTED"\n'
    ))

    story.append(PageBreak())

    # Layer 4 - Classifier
    story.append(H("Layer 4 - Classifier Service (Department + Sub-category + Priority + Sentiment)", 2))
    story.append(P(
        "<b>Role.</b> service-classifier (port 8004) consumes the normalised text + domain hints from NLU and produces four parallel predictions: "
        "<b>department</b> (one of 25 classes), <b>sub_category</b> (one of 142 classes), <b>sentiment</b> (Neutral, Frustrated, Distressed) and "
        "<b>priority</b> (Low, Med, High, Critical).",
    ))

    story.append(P("<b>Model used: fine-tuned MuRIL</b> (google/muril-base-cased) + four sklearn classification heads.", "h4"))
    story.append(P(
        "MuRIL (Multilingual Representations for Indian Languages) is a Google-published BERT-family encoder pre-trained on 17 Indian languages "
        "<i>including transliterations</i>. That last property is the reason we use MuRIL instead of plain mBERT or XLM-R: "
        "Indian users write Hindi in both Devanagari and Roman script (\"bijli\" vs \"बिजली\") and MuRIL is the only widely-available "
        "encoder that places both forms close together in embedding space.",
    ))

    story.append(P("<b>Architecture:</b>", "h4"))
    story.append(P(
        "We freeze the MuRIL encoder and use it only to extract sentence embeddings. Embeddings are computed as "
        "<b>mean pooling over non-padding tokens</b> at max sequence length 128 (we tested 256 and 512; the gain was inside the noise floor "
        "but inference latency doubled). The 768-d vector is then fed into four independent sklearn classifiers, "
        "one per output head:",
    ))
    story.append(code(
        '# Department and sub_category (>30 classes each)\n'
        'Pipeline([\n'
        '    ("scaler", StandardScaler()),\n'
        '    ("sgd", SGDClassifier(\n'
        '        loss="modified_huber",   # calibrated probabilities\n'
        '        alpha=1e-4,\n'
        '        max_iter=200,\n'
        '        n_jobs=-1,\n'
        '        class_weight="balanced",\n'
        '    )),\n'
        '])\n'
        '\n'
        '# Sentiment and priority (<10 classes)\n'
        'Pipeline([\n'
        '    ("scaler", StandardScaler()),\n'
        '    ("lr", LogisticRegression(\n'
        '        max_iter=2000, C=1.0,\n'
        '        solver="saga", n_jobs=-1)),\n'
        '])\n'
    ))

    story.append(P("<b>Why this two-tier design (encoder + sklearn) and not a fine-tuned classification head on MuRIL?</b>", "h4"))
    for b in [
        "Speed of iteration. Re-training a single sklearn head takes seconds on CPU; fine-tuning the whole MuRIL encoder takes hours on GPU.",
        "Re-use of embeddings. We cache the entire training-set embedding matrix in <code>embeddings_cache.npy</code> and reuse it across all four heads.",
        "Calibrated probabilities. We need confidence scores not just argmax, because below 0.40 confidence we ask the user a clarifying question. SGD with modified_huber gives well-calibrated probabilities; vanilla cross-entropy on a small classification head does not.",
        "Imbalanced classes. <code>class_weight=\"balanced\"</code> in sklearn is one line; the equivalent in PyTorch is a sampler dance.",
    ]:
        story.append(P(f"&bull; {b}", "bullet"))

    story.append(P("<b>Three-tier inference pipeline:</b>", "h4"))
    story.append(P(
        "When a request lands, the classifier tries three sources of signal in priority order:",
    ))
    story.append(P(
        "<b>Tier 1 - layer2_confirmed.</b> If the chatbot already asked the user \"is this about Electricity / Water / ...?\" and the user picked, the chatbot forwards that <code>layer2_category</code>. We override department with the user's pick, confidence 0.92, model tag <code>layer2_confirmed</code>.<br/>"
        "<b>Tier 2 - MuRIL inference.</b> Embed -> 4 classifiers -> top-3. If MuRIL's top-1 disagrees with the NLU domain hints, we trust the hints (synthetic confidence 0.75, model tag <code>muril+hint</code>).<br/>"
        "<b>Tier 3 - rule-based fallback.</b> If MuRIL artifacts are missing or <code>USE_RULE_BASED_CLASSIFIER=true</code> is set, we use the <code>DOMAIN_TO_DEPT</code> static map. Confidence 0.85 if hints exist, 0.50 otherwise."
    ))

    story.append(P("<b>Department label set (25 classes):</b>", "h4"))
    depts = [
        "Aadhaar (UIDAI)", "Agriculture & Farmers Welfare", "Banking (DFS)", "Consumer Affairs",
        "EPFO", "Education (Higher / School)", "Electricity", "GST (CBIC)",
        "Health & Family Welfare", "Housing & Urban Affairs", "Income Tax (CBDT)", "Insurance (DFS)",
        "Passport (MEA)", "Pension & Pensioners' Welfare", "Petroleum & LPG", "Police",
        "Postal", "Public Distribution (PDS)", "Public Safety & Encroachment", "RTO / State Transport",
        "Railways", "Roads & Transportation", "Telecom", "Waste Management", "Water Supply",
    ]
    story.append(P(", ".join(depts), "body"))

    story.append(P("<b>Sub-categories:</b> 142 fine-grained labels including \"Bill Discrepancy\", \"Transformer Fault\", \"Cyber Fraud\", \"Aadhaar Linking\", \"Ration Card Issue\", \"FIR Registration\", \"PM-Kisan Payment\", \"TDS Mismatch\", \"Ambulance Delay\", \"Pothole or Road Damage\", \"Streetlight\", \"Sewage Overflow\", \"Public Nuisance\", and so on across all 25 departments.", "body"))

    story.append(P("<b>Clarification loop:</b>", "h4"))
    story.append(P(
        "If department confidence drops below 0.40 the classifier returns <code>needs_clarification=True</code> with a Hindi clarifying "
        "question built from the top-3 departments. The orchestrator routes this back to the chatbot, which asks the user. After "
        "the user picks, the next classification call has <code>layer2_category</code> set and Tier 1 takes over with high confidence. "
        "We cap at 2 clarification rounds per complaint to avoid infinite loops.",
    ))

    story.append(PageBreak())

    # Layer 5 - Routing
    story.append(H("Layer 5 - Routing Service (Portal Selection)", 2))
    story.append(P(
        "<b>Role.</b> service-routing (port 8005) takes a department tag + district + state and returns the single most appropriate "
        "government portal out of 70 registered options.",
    ))
    story.append(P("<b>Why a separate routing service?</b> Portal selection is a policy problem (which authority is responsible for what) "
                   "not an ML problem - so the right tool is a hand-curated registry with deterministic matching logic, not a model. "
                   "Keeping it separate also lets policy admins update <code>portals.csv</code> without touching code.", "small"))

    story.append(P("<b>The portal registry (portals.csv):</b>", "h4"))
    story.append(P("70 portals across three tiers:"))
    for b in [
        "<b>30 Central portals</b> (covers ALL_INDIA) - e.g. CPGRAMS (P001), PMO (P002), Income Tax e-Nivaran (P003), RailMadad (P007), UIDAI Aadhaar (P011), CGHS, EPFO grievance, NHAI Sukhad Yatra, PFRDA, India Post.",
        "<b>30 State (MP) portals</b> (covers ALL_MP) - e.g. CM Helpline 181 (P031), MP Lokayukta (P035), MP Jal Nigam (P040), MP School Education (P042), MP Agriculture (P049), MP RTO, MP Police state, etc.",
        "<b>10 Regional portals</b> (district-specific) - MPPKVVCL Bhopal Discom (P061), MPPaschim Indore Discom (P062), MPMKVVCL Jabalpur (P063), Bhopal Municipal Corp (P064), Indore Municipal Corp (P065), Gwalior Nagar Nigam, Jabalpur Nagar Nigam, Ujjain Nagar Nigam, Sagar Nagar Nigam, Bhopal Police (P070), Indore Police (P071).",
    ]:
        story.append(P(f"&bull; {b}", "bullet"))

    story.append(P("<b>CSV columns:</b> portal_id, portal_name, portal_level, authority_name, covers_districts (pipe-separated), website, has_online, classifier_dept_tags (pipe-separated), complaint_categories, required_fields (pipe-separated), helpline, whatsapp, fallback_portal_id.", "body"))

    story.append(P("<b>Decision algorithm:</b>", "h4"))
    story.append(P(
        "Hierarchical: <b>regional &gt; state-specific &gt; state catch-all &gt; central-specific &gt; central catch-all</b>. "
        "More specific portals are preferred because local authorities resolve faster and citizens expect local handling. "
        "We define a specificity key (fewer dept tags handled = more specialised) and break ties by that.",
    ))
    story.append(code(
        'def find_portal(dept_tag, district, state):\n'
        '    candidates = [p for p in portals if dept_tag in p.classifier_dept_tags and p.has_online]\n'
        '\n'
        '    if state in {"madhya pradesh", "mp", "m.p."}:\n'
        '        # Tier 1: Regional with district match\n'
        '        regional = [p for p in candidates\n'
        '                    if p.portal_level == "Regional" and district in p.covers_districts]\n'
        '        if regional: return min(regional, key=_specificity_key)\n'
        '\n'
        '        # Tier 2: State-specific (ALL_MP) excluding catch-alls\n'
        '        state_p = [p for p in candidates\n'
        '                   if p.portal_level == "State" and p.portal_id not in _CATCH_ALL_IDS]\n'
        '        if state_p: return min(state_p, key=_specificity_key)\n'
        '\n'
        '        # Tier 3: MP state catch-all (P031)\n'
        '        # Tier 4: Central-specific\n'
        '        # Tier 5: National catch-all (P001 CPGRAMS)\n'
        '        ...\n'
        '\n'
        '    # Non-MP user: skip MP tiers\n'
        '    central = [p for p in candidates\n'
        '               if p.portal_level == "Central" and p.portal_id not in _CATCH_ALL_IDS]\n'
        '    return min(central, key=_specificity_key) if central else _portal_by_id("P001")\n'
    ))

    story.append(P("<b>Worked example - power cut in Bhopal:</b>", "h4"))
    story.append(P(
        "dept_tag=ELECTRICITY, district=Bhopal, state=Madhya Pradesh. "
        "Candidates that handle ELECTRICITY: P061 (MPPKVVCL Bhopal, Regional), P062 (Indore Discom, Regional), P063 (Jabalpur Discom, Regional), "
        "P031 (CM Helpline, State catch-all), P001 (CPGRAMS, Central catch-all). "
        "Tier 1 match: P061 covers Bhopal. Result: <b>P061 MPPKVVCL Bhopal Discom</b>. The user filed a power cut complaint - it goes "
        "to the actual electricity board for Bhopal, not to a national catch-all where it would be re-forwarded down the chain over weeks.",
    ))

    # Layer 6 - Dedup
    story.append(H("Layer 6 - Semantic Deduplication (S-BERT)", 2))
    story.append(P(
        "<b>Role.</b> Before we file a complaint, we ask: \"has this exact complaint already been filed?\" - either by this user (block "
        "re-submission) or by other users in the same district (aggregate so the dashboard can show frequency). This stage lives in the "
        "gateway service, between routing and field-collection.",
    ))
    story.append(P("<b>Model used:</b> <code>paraphrase-multilingual-MiniLM-L12-v2</code> from sentence-transformers. 117 MB, 384-dimensional vectors, supports 50+ languages including Hindi and Hinglish in the same vector space.", "h4"))

    story.append(P("<b>Why S-BERT and not bag-of-words or exact-string match?</b>", "h4"))
    for b in [
        '"mera bijli connection nahi aa raha" and "power is not coming at my house" should be detected as the same complaint. Lexical matching cannot do this; semantic embeddings can.',
        'Multilingual sentence-transformers were trained on parallel corpora explicitly so that translation pairs land near each other in embedding space.',
        '384 dims is small enough to store in a Postgres FLOAT8[] column without ballooning row size.',
        'Inference is cheap - a few milliseconds per text on CPU.',
    ]:
        story.append(P(f"&bull; {b}", "bullet"))

    story.append(P("<b>Logic:</b>", "h4"))
    story.append(code(
        'SIMILARITY_THRESHOLD = 0.85\n'
        '\n'
        '# Candidate set: same dept + sub_cat + district, last 180 days, unresolved\n'
        'for cand in candidates:\n'
        '    sim = cosine_similarity(own_embedding, cand.text_embedding)\n'
        '    if sim >= SIMILARITY_THRESHOLD:\n'
        '        if cand.user_id == this_user:\n'
        '            block_resubmission()        # same user, same complaint\n'
        '        else:\n'
        '            cluster_count += 1          # different user, aggregate signal\n'
    ))

    story.append(P("<b>Why threshold 0.85?</b> Empirically calibrated on our small test set. Below 0.80 we get false positives (\"no electricity\" and \"no water\" being too similar in multilingual space). Above 0.92 we miss obvious rephrasings. 0.85 is the sweet spot - we will re-tune on real production data.", "small"))

    # Layer 7 - Field collection
    story.append(H("Layer 7 - Portal Field Collection", 2))
    story.append(P(
        "<b>Role.</b> Each portal expects different fields. CPGRAMS wants <i>complainantName, address, pinCode, mobileNumber, emailId, aadhaarNo, ministryId, grievanceText</i>. MPPKVVCL wants <i>IVRS consumer number, full address of connection, complaint type</i>. We refuse to dump that complexity on the citizen. Instead, after routing has selected the portal, the chatbot enters FIELD_COLLECTION state and asks for each missing field conversationally.",
    ))
    story.append(P("<b>Pre-fill from conversation.</b> Many fields are already inferable from the conversation so far: name and mobile from the user profile, address from the location pin, description from the original complaint, complaint type from the classifier. Only genuinely portal-specific fields (consumer number, IVRS, PNR) are asked. This dropped average questions-per-complaint from ~7 to ~2.", "body"))

    story.append(P("<b>Field extraction prompt (verbatim from chatbot/prompts.py):</b>", "h4"))
    story.append(code(
        'You are collecting form fields for a government grievance portal.\n'
        'The user is answering one field at a time.\n'
        '\n'
        'Current field to collect: {field_name}\n'
        'User language: {language}\n'
        'Next field (if any): {next_field}\n'
        '\n'
        'Rules:\n'
        '- Extract the value for "{field_name}" from the user message.\n'
        '- If the user says they don\'t know / "skip" / non-answer -> extracted=null.\n'
        '- Keep reply to 1 short sentence in the user language.\n'
        '- If extracted is not null and next_field given, mention next field in reply.\n'
        '- If extracted is null, give a brief hint about where to find this field.\n'
        '\n'
        'Respond ONLY with JSON (no markdown):\n'
        '{"extracted": "<value or null>", "reply": "<1 sentence>"}\n'
    ))
    story.append(P("<b>11 validators</b> live in <code>chatbot/validators.py</code> - regex checks for pincode (6 digits), mobile (10 digits, starts 6-9), aadhaar (12 digits, Verhoeff checksum), email (RFC-lite), PAN, IFSC, GST, vehicle number, consumer number, account number, PNR. If a validator rejects, we re-ask once with a corrective hint.", "body"))

    story.append(PageBreak())

    # Layer 8 - Submission
    story.append(H("Layer 8 - Submission Service (Adapter Pattern)", 2))
    story.append(P(
        "<b>Role.</b> service-submission (port 8006) is the integration layer that actually pushes complaints to the chosen portal's API. "
        "Different portals expose different schemas (and sometimes no API at all - just a form). We solved this with a classic "
        "<b>adapter pattern</b>: one base class, one adapter per portal family.",
    ))

    story.append(P("<b>4-method adapter contract (PortalAdapter base class):</b>", "h4"))
    story.append(code(
        'class PortalAdapter(ABC):\n'
        '    portal_id: str\n'
        '    portal_name: str\n'
        '\n'
        '    @abstractmethod\n'
        '    async def submit(self, portal_fields, uco_meta) -> SubmissionResult:\n'
        '        """Build payload -> POST -> return ticket."""\n'
        '\n'
        '    @abstractmethod\n'
        '    async def fetch_status(self, ticket_id) -> StatusResult:\n'
        '        """Poll the portal API for current status."""\n'
        '\n'
        '    def transform_fields(self, portal_fields, uco_meta) -> dict:\n'
        '        """Map our generic field labels -> portal-specific keys."""\n'
        '        return {**portal_fields, **uco_meta}\n'
        '\n'
        '    def map_canonical_status(self, raw_status: str) -> str:\n'
        '        """Portal-specific status strings -> UCO canonical status."""\n'
        '        return _STATUS_MAP.get(raw_status.lower(), "IN_PROGRESS")\n'
    ))

    story.append(P("<b>Registered adapters:</b>", "h4"))
    for b in [
        "<b>CPGRAMSAdapter</b> - handles P001 (CPGRAMS) and P002 (PMO Public Grievance). Maps to CPGRAMS field names like complainantName, grievanceText, ministryId.",
        "<b>MPCM181Adapter</b> - handles P031 (MP CM Helpline 181). Maps to district / tehsil / village fields.",
        "<b>MPPKVVCLAdapter</b> - handles P062 / P065 (MP electricity discoms). Needs IVRS consumer number.",
        "<b>GenericMockAdapter</b> - fallback for any portal not yet wired up; generates a realistic ticket id with the portal-type prefix (\"ELE/\", \"POL/\") for demo purposes.",
    ]:
        story.append(P(f"&bull; {b}", "bullet"))

    story.append(P("<b>Retry policy: 7-attempt exponential backoff.</b>", "h4"))
    story.append(code(
        '_RETRY_DELAYS = [60, 120, 300, 900, 3600, 14400, 86400]\n'
        '#                1m   2m   5m   15m   1h    4h     24h\n'
        '\n'
        'try:\n'
        '    await submission_service.submit(payload)\n'
        'except Exception:\n'
        '    if attempt < len(_RETRY_DELAYS):\n'
        '        loop.call_later(_RETRY_DELAYS[attempt],\n'
        '            lambda: trigger_submission(complaint_id, payload, attempt + 1))\n'
        '    else:\n'
        '        mark_complaint_failed_and_alert_admin()\n'
    ))

    story.append(P("<b>Why this exact backoff curve?</b> Most portal failures are transient (gateway timeout, captcha, brief outage). 1 and 2 minute retries handle those. The 15-minute and 1-hour gaps cover scheduled portal maintenance windows. 4-hour and 24-hour final attempts cover all-day outages. After 8 attempts we mark the complaint <code>failed</code> and surface it to the admin dashboard for human review.", "body"))

    # Layer 9 - Tracker
    story.append(H("Layer 9 - Status Tracker", 2))
    story.append(P(
        "<b>Role.</b> service-tracker (port 8007) polls each submitted complaint's portal at adaptive intervals until it reaches a terminal state, "
        "normalises portal-specific status strings into UCO canonical statuses, and notifies the citizen.",
    ))

    story.append(P("<b>Adaptive polling schedule:</b>", "h4"))
    story.append(code(
        'def poll_interval_seconds(submitted_at):\n'
        '    age = now() - submitted_at\n'
        '    if age < timedelta(days=1):  return 3600    # every 1 hour\n'
        '    if age < timedelta(days=7):  return 21600   # every 6 hours\n'
        '    return 86400                                # daily after that\n'
    ))
    story.append(P("Fresh complaints get checked frequently because that's when status changes happen. Old complaints get checked daily so we don't hammer portals for stale records.", "body"))

    story.append(P("<b>Status normaliser</b> - portal statuses are messy strings in mixed languages:", "h4"))
    story.append(code(
        '_STATUS_MAP = {\n'
        '    "submitted": "PENDING", "registered": "PENDING", "received": "PENDING",\n'
        '    "under review": "IN_PROGRESS", "in progress": "IN_PROGRESS",\n'
        '    "forwarded to ministry": "IN_PROGRESS", "officer assigned": "IN_PROGRESS",\n'
        '    "awaiting response": "AWAITING_USER",\n'
        '    "टिप्पणी प्रतीक्षित": "AWAITING_USER",       # Hindi\n'
        '    "resolved": "RESOLVED", "closed": "RESOLVED", "disposed": "RESOLVED",\n'
        '    "rejected": "REJECTED", "closed no action": "REJECTED",\n'
        '}\n'
    ))

    story.append(P("<b>Citizen notifications (mock Twilio WhatsApp):</b> on every status change we send a bilingual message - Hindi first, English fallback. On RESOLVED status the message asks \"Reply 1 (haan) or 2 (nahi)\" - this enters the feedback loop in the gateway, which records satisfaction and (on \"2\") escalates back to the admin queue.", "body"))

    # Audit chain
    story.append(H("Cross-cutting Layer - SHA-256 Tamper-Evident Audit Chain", 2))
    story.append(P(
        "Every meaningful event in the lifecycle of a complaint - <code>chat_message, submit_attempt, submit_failed, submit_exhausted, feedback_requested, status_changed</code> - is written to <code>complaint_events</code> with a SHA-256 hash that includes the previous event's hash.",
    ))
    story.append(code(
        'raw = f"{prev_hash or \'\'}{event_type}{json.dumps(details,sort_keys=True)}{now_iso}"\n'
        'event_hash = hashlib.sha256(raw.encode()).hexdigest()\n'
    ))
    story.append(P("This means an auditor (or the citizen themselves) can recompute every hash from the genesis event to verify that no event was deleted, re-ordered, or tampered with. Each chain is per-complaint, kept in the relational complaint_events table. The right column on the admin dashboard renders this chain visually.", "body"))

    story.append(PageBreak())

    # ───────── 4. Department dashboard ─────────
    story.append(H("4. Department / Government Dashboard Flow - Layer by Layer", 1))
    story.append(P(
        "The second product surface in Margdarshan.ai is the dashboard used by reviewing departments and oversight bodies. "
        "It is a separate routing inside the same React SPA, accessible after an admin user logs in (the <code>is_admin</code> flag on the user record gates this).",
    ))

    story.append(H("Layer 1 - Admin Authentication", 2))
    story.append(P(
        "Same login screen as citizens but the post-login router checks <code>users.is_admin</code>. The default admin "
        "account (<code>admin@margdarshan.ai / Admin@1234</code>) is bootstrapped on first gateway start if it doesn't exist. "
        "Auth uses bcrypt password hashing and PyJWT-signed tokens stored in localStorage.",
    ))

    story.append(H("Layer 2 - Stats Overview", 2))
    story.append(P(
        "Hero cards at the top show: total complaints, duplicate-complaint count, breakdown by status, breakdown by department, "
        "breakdown by district, and the 10 most recent complaints with summary, status, department, and timestamp. "
        "Endpoint: <code>GET /api/v1/admin/stats</code>. Backed by Postgres aggregation queries with appropriate indices "
        "(<code>idx_complaints_dedup</code>, <code>idx_complaints_created_at</code>).",
    ))

    story.append(H("Layer 3 - Portal Registry View", 2))
    story.append(P(
        "Full list of the 70 portals with portal_id, name, level (Regional/State/Central), authority, districts covered, "
        "website link, online filing flag, classifier dept tags, complaint categories, helpline, and the live count of complaints "
        "currently routed to each portal. Filterable by department, district, level. Endpoint: <code>GET /api/v1/admin/portals</code>.",
    ))
    story.append(P("<b>Why this matters:</b> The most common operational question for a state oversight body is \"are we sending complaints to the right places?\" This view answers that in one screen, and the per-portal complaint count flags portals that may be misconfigured.", "small"))

    story.append(H("Layer 4 - Complaints List with Filters", 2))
    story.append(P(
        "Filterable grid of all complaints in the system. Filters: status, department, district. Columns: complaint_id, summary, "
        "status badge, department, sub_category, district, portal_id, ticket_id, user_name, user_mobile, priority badge, sentiment badge, "
        "is_duplicate flag, duplicate_count, created_at. Pagination at 50 rows by default. Endpoint: <code>GET /api/v1/admin/complaints?status=&department=&district=&limit=&offset=</code>.",
    ))

    story.append(H("Layer 5 - Complaint Detail Drill-Down", 2))
    story.append(P(
        "Clicking any complaint opens a full detail view with five sections:",
    ))
    for b in [
        "<b>Filer info</b> - name, mobile, email, district. Anonymisable for cross-department views (PII masked except for last 4 digits of mobile).",
        "<b>Classification</b> - department, sub_category, priority, sentiment, confidence, plus the top-3 alternatives the classifier considered.",
        "<b>Portal routing explanation</b> - which portal_id was chosen, why (matching tier, district match, fallback path).",
        "<b>Portal fields</b> - the key-value pairs we collected and posted to the portal.",
        "<b>Audit chain</b> - the entire SHA-256 hash-chained event log for this complaint, rendered as a timeline.",
    ]:
        story.append(P(f"&bull; {b}", "bullet"))
    story.append(P("Endpoint: <code>GET /api/v1/admin/complaints/{id}</code>.", "body"))

    story.append(H("Layer 6 - Review Form (Thumbs Up / Down + Corrections)", 2))
    story.append(P(
        "On every complaint detail page, reviewing officers can rate the AI's decisions. The form accepts:",
    ))
    for b in [
        "rating (positive / negative) - the headline feedback",
        "classification_correct (bool)",
        "correct_department (text override)",
        "correct_sub_category (text override)",
        "correct_priority (Low/Med/High/Critical override)",
        "sentiment_correct (bool)",
        "reviewer_notes (free text)",
    ]:
        story.append(P(f"&bull; {b}", "bullet"))
    story.append(P("Posted to <code>POST /api/v1/admin/complaints/{id}/review</code>. The data lands in the <code>complaint_reviews</code> table, which forms our training feedback loop: every misclassification flagged by a real reviewer becomes a candidate row in the next MuRIL fine-tuning dataset.", "body"))

    story.append(H("Layer 7 - Duplicate Filer Detection", 2))
    story.append(P(
        "Surfaces (a) repeat complaints filed by the same person, and (b) clusters of complaints across different users in the same "
        "district that are semantically similar (cosine >= 0.85). The dashboard shows: complaint_id, filer name, mobile, filed_at, "
        "status, similarity score, plus the portal fields from each filing - which makes it easy to spot whether multiple citizens "
        "are reporting the same incident (e.g., a transformer fault that 30 households are calling about).",
    ))

    story.append(H("Layer 8 - Routing Explanation", 2))
    story.append(P(
        "For every complaint, we can answer \"why was this sent to Portal X?\". The explanation includes: (i) "
        "department tag from classifier, (ii) district/state from location pin, (iii) the matching tier that fired "
        "(Regional, State-specific, State catch-all, Central-specific, National catch-all), (iv) which specific portal-rule matched. "
        "This is a transparency feature that makes the system auditable for citizens and oversight bodies alike.",
    ))

    story.append(H("Layer 9 - API Trace / Demo Page", 2))
    story.append(P(
        "An animated 5-step page that shows the live API exchange for a single complaint: Classification request/response, Routing "
        "decision JSON, Portal submission request/response, Current tracking status. Built for demos but also a useful debug surface "
        "during incidents. Endpoint: <code>GET /api/v1/demo/trace/{complaint_id}</code>.",
    ))

    story.append(PageBreak())

    # ───────── 5. AI/ML/NLP foundations ─────────
    story.append(H("5. AI / ML / NLP Foundations Used in the System", 1))
    story.append(P(
        "This section explains the conceptual machinery in plain terms - useful for evaluators who want to know what each technical "
        "term means and why it is the right pick.",
    ))

    story.append(H("5.1 Transformers and Encoder Models", 2))
    story.append(P(
        "A <b>transformer</b> is a neural network architecture (Vaswani et al., 2017) that processes an input sequence by computing "
        "<b>self-attention</b> between every pair of tokens. The output for any token is a weighted blend of every other token's "
        "representation, with the weights learned during pretraining. This is why transformers handle context far better than the "
        "RNNs they replaced.",
    ))
    story.append(P(
        "An <b>encoder-only</b> transformer (BERT, MuRIL, XLM-R) takes a sequence in and produces a contextual vector for every token. "
        "A <b>decoder-only</b> transformer (GPT-class models, Claude, Llama) takes a sequence in and produces the next token, one at a time. "
        "We use encoder-only for classification (we need representations, not text generation) and decoder-only for the conversational "
        "chatbot (we need fluent text generation in three languages).",
    ))

    story.append(H("5.2 MuRIL (encoder we use for classification)", 2))
    story.append(P(
        "MuRIL is a BERT-base architecture (12 layers, 768 hidden size, 12 attention heads, ~236M params) pretrained by Google "
        "Research on 17 Indian languages. Crucially, it was pretrained on both native scripts <i>and</i> the Roman-script transliterations "
        "that Indian users actually type. Its tokeniser is wordpiece, vocab size 197k. The published BPC perplexities show it "
        "outperforms mBERT and XLM-R on 9 of 10 Indic NLP benchmarks.",
    ))
    story.append(P(
        "We use <b>mean pooling</b> (averaging the final-layer hidden states across all non-padding tokens) as our sentence "
        "representation rather than the <code>[CLS]</code> token, because empirical results in the sentence-BERT literature show "
        "mean pooling is marginally better when the encoder is frozen and you feed the embeddings into a downstream classifier.",
    ))

    story.append(H("5.3 Sentence-BERT (S-BERT) for Deduplication", 2))
    story.append(P(
        "S-BERT (Reimers and Gurevych, 2019) is a fine-tuning recipe that produces sentence embeddings where <b>semantic distance "
        "corresponds to cosine distance</b>. Vanilla BERT embeddings are not directly comparable that way. The specific model we use, "
        "<code>paraphrase-multilingual-MiniLM-L12-v2</code>, is a 12-layer student distilled from a multilingual XLM-R teacher, "
        "trained on the parallel paraphrase corpus across 50+ languages. 384 dims, 117 MB, sub-10 ms inference per sentence on CPU.",
    ))

    story.append(H("5.4 Claude Haiku 4.5 (decoder model for dialogue)", 2))
    story.append(P(
        "Claude is Anthropic's family of large language models. <b>Haiku 4.5</b> (model id <code>claude-haiku-4-5-20251001</code>) "
        "is the smallest tier - optimised for low latency and low cost. It is a decoder-only transformer with extended-context support "
        "(200k tokens), trained with Constitutional AI techniques. We invoke it via Anthropic's REST API with temperature 0.2 "
        "(low randomness - we want consistent intent classification, not creative text), max 600 tokens per response.",
    ))
    story.append(P(
        "Two prompt patterns in our system: (1) <b>structured NLU prompt</b> in service-nlu - returns a typed JSON object with intent, "
        "language, complaint_buffer, completeness, next_state, reply_to_user; (2) <b>field extraction prompt</b> in service-chatbot - "
        "returns <code>{extracted, reply}</code> for a single portal field per turn.",
    ))

    story.append(H("5.5 Cosine Similarity (the metric we threshold on)", 2))
    story.append(P(
        "Cosine similarity between two vectors a and b is <code>(a . b) / (|a| * |b|)</code>. It is in [-1, 1] for general vectors and "
        "in [0, 1] for non-negative embeddings. It measures the angle between the vectors, ignoring magnitude - which is exactly what "
        "you want when comparing semantic content irrespective of sentence length.",
    ))

    story.append(H("5.6 Calibrated Probabilities and Why We Care", 2))
    story.append(P(
        "An argmax of softmax scores tells you the most likely class, but it does not tell you <i>how sure</i> the model is. We need "
        "the latter so we can route low-confidence cases through a clarification loop instead of acting on a wrong guess. "
        "<code>SGDClassifier(loss=\"modified_huber\")</code> gives calibrated probabilities cheaply; we threshold at 0.40 on the "
        "department head.",
    ))

    story.append(H("5.7 Pub/Sub Pattern (event-driven orchestration)", 2))
    story.append(P(
        "Each service emits <code>PipelineEvent</code> messages with <code>(complaint_id, stage, status, payload)</code> to a single "
        "Redis channel. The gateway orchestrator subscribes and triggers the next stage. This decouples services in time and space - "
        "we can add, remove, or restart any service without rewiring the others.",
    ))

    story.append(H("5.8 Adapter Pattern (object-oriented portal integration)", 2))
    story.append(P(
        "A classical Gang-of-Four pattern. The 4-method <code>PortalAdapter</code> interface lets new portals slot in by writing one "
        "subclass; the rest of the submission service knows nothing about portal-specific schemas.",
    ))

    story.append(H("5.9 Hash Chains (tamper evidence)", 2))
    story.append(P(
        "Inspired by blockchain merkle structures but linear: every event includes the SHA-256 of the previous event in its own "
        "hash input. Mutating any historical event invalidates every subsequent hash, which a verifier can detect in linear time.",
    ))

    story.append(PageBreak())

    # ───────── 6. Training and accuracy ─────────
    story.append(H("6. Model Training, Evaluation, and Accuracy", 1))

    story.append(H("6.1 Classifier Training Dataset", 2))
    story.append(P(
        "We curated <b>v3_enriched.csv</b>, a 3,564-row labelled dataset of Indian grievances written in Hindi, English, and Hinglish. "
        "Each row has: <code>complaint_text</code>, <code>department</code> (one of 25), <code>sub_category</code> (one of 142), "
        "<code>priority</code>, <code>sentiment</code>. The dataset was bootstrapped from CPGRAMS publicly disclosed grievance excerpts, "
        "augmented with synthetic Hinglish paraphrases generated by Claude Sonnet and reviewed by a human (myself) before inclusion.",
    ))

    story.append(H("6.2 Training Pipeline (train_muril.py)", 2))
    story.append(P("<b>Hyperparameters:</b>", "h4"))
    train_tbl = [
        ["Parameter", "Value", "Why"],
        ["Encoder", "google/muril-base-cased (frozen)", "Best multilingual coverage of Indian languages incl. transliteration."],
        ["Max sequence length", "128 tokens", "Median complaint length 41 tokens; 128 covers p95 with no truncation loss."],
        ["Pooling", "Mean over non-padding tokens", "Empirically better than CLS for frozen-encoder classification."],
        ["Batch size", "32", "Fits in 8 GB RAM during embedding extraction."],
        ["Device", "MPS (Apple Silicon) or CPU", "GPU not required - MuRIL is small enough."],
        ["Department head", "SGDClassifier(modified_huber)", "Calibrated probabilities, balanced class weights."],
        ["Sub-category head", "SGDClassifier(modified_huber)", "Same - 142 classes need probabilities for top-k."],
        ["Sentiment / priority head", "LogisticRegression(saga)", "Few classes, smooth solver handles imbalance."],
        ["Train / val split", "85 / 15 stratified by department", "Preserve class balance in val set."],
        ["Eval metric", "weighted F1", "Robust to class imbalance, matches the misclassification cost we care about."],
    ]
    story.append(header_table(train_tbl, col_widths=[4.5*cm, 5*cm, 6.5*cm]))
    story.append(Spacer(1, 0.4*cm))

    story.append(H("6.3 Reported Accuracy", 2))
    acc_tbl = [
        ["Head", "Classes", "Weighted F1 (val)", "Notes"],
        ["Department", "25", "0.91", "Strong signal from domain hints + dedicated keyword overrides."],
        ["Sub-category", "142", "~0.85", "Range 0.60 to 1.00 per class - rare classes dominate the spread."],
        ["Sentiment", "3", "0.78", "Frustrated and Distressed often overlap lexically."],
        ["Priority", "4", "0.83", "Critical override by keyword set is rule-based and 100% recall."],
    ]
    story.append(header_table(acc_tbl, col_widths=[3.5*cm, 2*cm, 3.5*cm, 7*cm]))
    story.append(Spacer(1, 0.3*cm))

    story.append(H("6.4 Why F1 and not accuracy?", 2))
    story.append(P(
        "Class distribution is heavily imbalanced (Electricity and Water Supply dominate; Aadhaar-Linking has 50x fewer rows than "
        "Power Outage). Accuracy would let the model coast by always predicting majority classes. Weighted F1 penalises the model for "
        "ignoring minority classes proportionally to their support.",
    ))

    story.append(H("6.5 Confusion Matrix Observations", 2))
    for b in [
        "Most frequent confusion: Water Supply -> Roads & Transportation when complaints mention <i>nali</i> (drain) - both domains legitimately match. We bias toward Water in the rule-based fallback when <i>paani</i> or <i>tanker</i> also appears.",
        "Noise / loudspeaker complaints used to land in Waste Management because of an early keyword overlap. Fixed by moving <i>shor / loudspeaker / dj</i> into a dedicated <i>safety</i> domain and routing it to Public Safety & Encroachment.",
        "Aadhaar Linking vs Aadhaar Seeding - finer-grained sub-category confusion. We accept this; the routed portal is the same.",
    ]:
        story.append(P(f"&bull; {b}", "bullet"))

    story.append(H("6.6 Production Status of MuRIL", 2))
    story.append(P(
        "MuRIL inference is wired up and benchmarked but currently <b>disabled</b> in deployment via <code>USE_RULE_BASED_CLASSIFIER=true</code> in <code>.env</code>. "
        "The rule-based path (domain hints + keyword maps + layer-2 confirmation) is achieving department-level accuracy comparable "
        "to MuRIL on our hackathon test traffic, with simpler ops and faster cold-start. Re-enabling MuRIL is a one-line env-var toggle "
        "and a service-classifier rebuild.",
    ))

    story.append(H("6.7 How We Continuously Improve", 2))
    story.append(P(
        "Every classification with a thumbs-down review in the admin dashboard becomes a labelled training row in the next training cycle. "
        "The <code>complaint_reviews</code> table is structured exactly to be joined back to <code>complaints.pipeline_data</code> "
        "and emitted as a fresh CSV row. This closes the loop between operations and model quality.",
    ))

    story.append(PageBreak())

    # ───────── 7. Software engineering ─────────
    story.append(H("7. Software Engineering Concepts in Play", 1))

    story.append(H("7.1 Microservices vs Monolith", 2))
    story.append(P(
        "Each pipeline stage is its own service, deployed independently. Inter-service contracts are typed FastAPI bodies validated "
        "by Pydantic; the shared Pydantic models live in a single shared-schema package. Why not a monolith: separate runtime "
        "dependencies (PyTorch in classifier, anthropic SDK in chatbot, just httpx in location), independent scaling, independent "
        "failure domains.",
    ))

    story.append(H("7.2 FastAPI Everywhere", 2))
    story.append(P(
        "Every Python service is FastAPI 0.115 on uvicorn 0.30. Why FastAPI: (a) Pydantic validation gives us schema-correct request "
        "and response bodies for free, (b) async support out of the box - which matters because every service is I/O bound on "
        "Postgres, Redis, or external APIs, (c) auto-generated OpenAPI docs at <code>/docs</code> on every service.",
    ))

    story.append(H("7.3 Async I/O", 2))
    story.append(P(
        "All inter-service calls use <code>httpx.AsyncClient</code>. Database access uses <code>asyncpg</code>. The orchestrator "
        "loop is a single async task that handles the entire event stream. This lets a single uvicorn worker handle dozens of "
        "in-flight complaints concurrently without thread overhead.",
    ))

    story.append(H("7.4 Authentication and Authorization", 2))
    story.append(P(
        "Password storage: bcrypt with cost factor 12 (~150 ms to hash, safe against rainbow tables). Tokens: PyJWT-signed with "
        "HS256 and a 32-character secret from <code>JWT_SECRET</code> env var. Admin gating: the user record has an <code>is_admin</code> "
        "boolean - we never trust the client to set that.",
    ))

    story.append(H("7.5 Database Schema Highlights", 2))
    story.append(P("Six tables: <code>users</code>, <code>complaints</code> (with JSONB <code>pipeline_data</code> + FLOAT8[] "
                   "<code>text_embedding</code>), <code>messages</code>, <code>complaint_events</code> (the audit chain), "
                   "<code>complaint_reviews</code> (admin feedback). A partial index "
                   "<code>idx_complaints_dedup (department, sub_category, district, status, created_at DESC) WHERE status NOT IN "
                   "('resolved','rejected')</code> makes the dedup query O(log n) over relevant rows only.", "body"))

    story.append(H("7.6 Frontend Patterns", 2))
    for b in [
        "<b>Context + custom hooks</b> for global state (<code>useAuth</code>, <code>useChat</code>, <code>usePipeline</code>) - the right tool for a small but live-updating SPA.",
        "<b>Component-driven UI</b> - 20+ small composable components rather than a few mega-components.",
        "<b>WebSocket for live updates</b> - <code>usePipeline</code> opens <code>ws://gateway/ws/pipeline/{id}</code> and pushes events into the right panel as they arrive.",
        "<b>react-i18next</b> with three resource files - the entire UI swaps language with one dropdown click.",
        "<b>Leaflet + OSM</b> for the location pin - free, no API key, works offline once tiles are cached.",
    ]:
        story.append(P(f"&bull; {b}", "bullet"))

    story.append(H("7.7 DevOps", 2))
    for b in [
        "Docker Compose for the whole stack - <code>docker compose up -d</code> brings up 10 services + Postgres + Redis in under 30 seconds.",
        "Healthchecks on Postgres and Redis so dependent services wait for readiness, not just port-open.",
        "Volume mounts for hot-reloading frontend code and re-using the host's HuggingFace cache (no re-download of MuRIL on every rebuild).",
        "End-to-end smoke test script at <code>scripts/smoke_test.sh</code> exercises auth, chat, geocode, and admin endpoints.",
    ]:
        story.append(P(f"&bull; {b}", "bullet"))

    story.append(PageBreak())

    # ───────── 8. Comparative analysis ─────────
    story.append(H("8. Comparative Analysis with Existing Systems", 1))
    story.append(P(
        "Several public grievance systems exist in India today. We benchmarked Margdarshan.ai against the four most prominent.",
    ))
    cmp_tbl = [
        ["Capability", "CPGRAMS", "MP CM Helpline 181", "MyGov", "Per-utility portals (MPPKVVCL etc.)", "Margdarshan.ai"],
        ["Conversational input", "No - long form", "Yes (IVR)", "No - structured forms", "No - form per portal", "Yes - chat + voice"],
        ["Multilingual (Hindi / Hinglish)", "Limited - Hindi UI only", "Hindi IVR", "11 Indian languages but English forms", "Mostly English", "Hindi + English + Hinglish, end-to-end"],
        ["Auto portal selection", "No - user picks ministry", "Centralised - one portal", "No", "No - one portal each", "Yes - 70 portals, regional > state > central"],
        ["Semantic deduplication", "No", "No", "No", "No", "Yes - S-BERT cosine 0.85"],
        ["Field pre-fill from conversation", "No", "Operator collects", "No", "No", "Yes - location/name/desc pre-filled"],
        ["Citizen status notifications", "Email", "SMS", "Email", "Varies", "Bilingual WhatsApp + chat"],
        ["AI classification visibility / audit", "Closed", "Closed", "Closed", "Closed", "Open - top-3 alternatives + reviewer override"],
        ["Tamper-evident audit", "No", "No", "No", "No", "Yes - SHA-256 chain per complaint"],
        ["Single citizen surface across portals", "No", "No (MP only)", "No", "No", "Yes - one chat covers all 70"],
    ]
    story.append(header_table(cmp_tbl, col_widths=[3.4*cm, 1.9*cm, 2.0*cm, 1.7*cm, 2.5*cm, 3.0*cm]))

    story.append(Spacer(1, 0.4*cm))
    story.append(P("<b>How we do better - concretely:</b>", "h3"))
    for b in [
        "<b>One door, many portals.</b> CPGRAMS forwards rejected complaints down the chain over weeks. We pick the right door first time.",
        "<b>Citizen language, not bureaucratic language.</b> A user writes \"bijli 3 din se nahi aa rahi\" and the system handles it end-to-end. CPGRAMS would force them to translate that into English bullet points.",
        "<b>Conversational field collection.</b> No portal in India today asks you for required fields in chat form - all of them dump you into an HTML form. We collect fields one at a time with hints in your language.",
        "<b>Visible AI decisions.</b> Every classification ships with its top-3 alternatives and confidence. Departments can override and that override becomes training data. No existing system exposes this surface.",
        "<b>Hash-chained audit.</b> Closed systems make trust very hard. We make every event verifiable.",
        "<b>Semantic deduplication.</b> Across the same chamber, citizens often re-file the same complaint in different words. No public portal detects this; we do.",
    ]:
        story.append(P(f"&bull; {b}", "bullet"))

    story.append(PageBreak())

    # ───────── 9. Future work ─────────
    story.append(H("9. Future Enhancements and Roadmap", 1))

    story.append(H("9.1 Production Hardening", 2))
    for b in [
        "<b>Real portal integrations.</b> Replace mock adapters with HTTP submissions to actual portal APIs once we secure department MoUs. CPGRAMS already exposes such an API behind credentialed access.",
        "<b>OAuth integrations with DigiLocker</b> for verified identity proof during sensitive submissions (Aadhaar, passport).",
        "<b>Twilio WhatsApp Business</b> for real outbound messaging (current implementation is logged-only).",
        "<b>Rate limiting and abuse detection</b> beyond the per-hour limit - per-IP, per-user-mobile, per-text-fingerprint to deter mass campaign abuse.",
    ]:
        story.append(P(f"&bull; {b}", "bullet"))

    story.append(H("9.2 ML Quality", 2))
    for b in [
        "<b>Re-enable MuRIL</b> with the most recent training set incorporating department reviewer feedback (closing the feedback loop).",
        "<b>Active learning</b> - sample low-confidence classifications for human labelling rather than random.",
        "<b>Cross-lingual zero-shot</b> for languages we have no training data in - Marathi, Bengali, Tamil - using XLM-R as encoder.",
        "<b>Reranker for portal routing</b> - learn from \"complaints where the routed portal escalated back to a different one\" to improve the routing heuristics.",
        "<b>Better dedup</b> using HNSW (Hierarchical Navigable Small World) over <code>pgvector</code> instead of brute-force cosine - scales to millions of complaints.",
    ]:
        story.append(P(f"&bull; {b}", "bullet"))

    story.append(H("9.3 Product Surface", 2))
    for b in [
        "<b>Native mobile app</b> (React Native) - the chat surface translates trivially.",
        "<b>WhatsApp bot front-end</b> - reuse the same chatbot/NLU services; users who don't install apps can still file complaints.",
        "<b>Public dashboard</b> - anonymised, aggregate view of district-level grievance trends. Useful for civic journalism and citizen accountability.",
        "<b>Voice IVR</b> - call a toll-free number, the same NLU brain takes over. Critical for users with low literacy.",
        "<b>Document attachment</b> - photos of potholes, copies of bills - currently the schema supports it but the UI doesn't expose upload yet.",
        "<b>Multi-user complaint clustering on the citizen side</b> - tell a user \"23 of your neighbours also reported this; we're escalating as a group\".",
    ]:
        story.append(P(f"&bull; {b}", "bullet"))

    story.append(H("9.4 Department Side", 2))
    for b in [
        "<b>SLA timers</b> per portal - flag complaints crossing deadlines automatically.",
        "<b>Officer assignment workflow</b> - department reviewer can route specific complaints to specific officers from within the dashboard.",
        "<b>Trend dashboards</b> with department-level KPIs (resolution rate, time-to-first-response, citizen satisfaction).",
        "<b>API for departments</b> - departments can pull their queued complaints into their existing case-management software.",
    ]:
        story.append(P(f"&bull; {b}", "bullet"))

    story.append(H("9.5 Trust and Privacy", 2))
    for b in [
        "<b>End-to-end encryption</b> for sensitive complaints (sexual harassment, whistleblowing).",
        "<b>Differential privacy</b> on public-dashboard aggregates so individuals cannot be re-identified.",
        "<b>Right-to-erasure tooling</b> - users can purge their account; the audit chain handles tombstones rather than deletes.",
        "<b>External hash anchoring</b> - periodically write the latest chain head to a public blockchain so even our database admin cannot rewrite history undetected.",
    ]:
        story.append(P(f"&bull; {b}", "bullet"))

    story.append(PageBreak())

    # ───────── 10. Appendix ─────────
    story.append(H("10. Appendix - APIs, Schemas, Deployment", 1))

    story.append(H("10.1 Gateway API Surface (public endpoints)", 2))
    api_tbl = [
        ["Method", "Path", "Purpose"],
        ["POST", "/api/v1/auth/register", "Create user, return JWT."],
        ["POST", "/api/v1/auth/login", "Authenticate (email or mobile), return JWT."],
        ["GET", "/api/v1/auth/me", "Return current user profile."],
        ["POST", "/api/v1/chat", "Send a chat message, get reply + pipeline state."],
        ["POST", "/api/v1/complaint/attach-location", "Pin location to a complaint."],
        ["POST", "/api/v1/session/reset", "Clear chatbot + NLU session."],
        ["POST", "/api/v1/session/restore/{cid}", "Restore prior session for editing."],
        ["GET", "/api/v1/complaints", "List user's complaints."],
        ["GET", "/api/v1/complaints/{id}", "Full complaint detail incl. pipeline_data."],
        ["GET", "/api/v1/complaints/{id}/messages", "Chat history for a complaint."],
        ["WS", "/ws/pipeline/{id}", "Real-time pipeline event stream."],
        ["GET", "/api/v1/admin/stats", "Admin: aggregated counts and recent complaints."],
        ["GET", "/api/v1/admin/portals", "Admin: 70-portal registry."],
        ["GET", "/api/v1/admin/complaints", "Admin: filtered complaint list."],
        ["GET", "/api/v1/admin/complaints/{id}", "Admin: full complaint detail + audit chain."],
        ["POST", "/api/v1/admin/complaints/{id}/review", "Admin: submit AI-decision review (thumbs up/down + corrections)."],
        ["POST", "/api/v1/admin/complaints/{id}/status", "Admin: override complaint status."],
        ["GET", "/api/v1/demo/trace/{id}", "Demo: full API exchange JSON for a complaint."],
        ["POST", "/api/v1/location/reverse-geocode", "Proxy to service-location."],
        ["GET", "/api/v1/location/pincode/{pin}", "Proxy to service-location."],
    ]
    story.append(header_table(api_tbl, col_widths=[1.5*cm, 6.5*cm, 8*cm]))
    story.append(Spacer(1, 0.4*cm))

    story.append(H("10.2 Unified Complaint Object (UCO) - core schema", 2))
    story.append(code(
        'class UCO(BaseModel):\n'
        '    complaint_id: str\n'
        '    user_id: str\n'
        '    session_id: str\n'
        '    text_raw: str\n'
        '    text_normalized: Optional[str]\n'
        '    text_for_classifier: Optional[str]\n'
        '    language: Optional[LanguageEnum]              # en / hi / hinglish\n'
        '    location: Optional[LocationData]              # lat/lon/pincode/ward/district/state\n'
        '    entities: Entities                            # phone/aadhaar/email/...\n'
        '    keywords: list[str]\n'
        '    domain_hints: list[str]\n'
        '    classification: Optional[Classification]      # dept, sub_cat, priority, sentiment, confidence\n'
        '    portal: Optional[Portal]                      # portal_id, name, jurisdiction, required_fields\n'
        '    status: Status                                # PENDING/IN_PROGRESS/RESOLVED/...\n'
        '    created_at: datetime\n'
        '    submitted_at: Optional[datetime]\n'
        '    resolved_at: Optional[datetime]\n'
    ))

    story.append(H("10.3 Pipeline Event Schema", 2))
    story.append(code(
        'class PipelineEvent(BaseModel):\n'
        '    complaint_id: str\n'
        '    stage: StageEnum            # stage_0_chat / stage_2_nlu / stage_3_classify / ... / stage_10_status\n'
        '    status: EventStatusEnum     # started / completed / failed / skipped\n'
        '    payload: dict[str, Any]\n'
        '    error: Optional[str]\n'
        '    created_at: datetime\n'
    ))

    story.append(H("10.4 Database Tables", 2))
    story.append(code(
        'users           id, name, gender, email, mobile, phone, password_hash,\n'
        '                address, sub_locality, locality, state, district, pincode,\n'
        '                country, is_admin, created_at\n'
        '\n'
        'complaints      complaint_id (UUID PK), user_id, summary, intent, state,\n'
        '                department, sub_category, district, portal_id, ticket_id,\n'
        '                status, text_embedding (FLOAT8[384]),\n'
        '                pipeline_data (JSONB), created_at, updated_at\n'
        '                INDEX (department, sub_category, district, status, created_at DESC)\n'
        '                  WHERE status NOT IN (\'resolved\',\'rejected\')\n'
        '\n'
        'messages        id, complaint_id, user_id, session_id, role, content,\n'
        '                seq (BIGSERIAL), created_at\n'
        '\n'
        'complaint_events  event_id, complaint_id, event_type, actor, details (JSONB),\n'
        '                  prev_hash, event_hash, created_at\n'
        '\n'
        'complaint_reviews id, complaint_id, classification_correct, correct_department,\n'
        '                  correct_sub_category, correct_priority, sentiment_correct,\n'
        '                  reviewer_notes, rating (positive/negative), created_at\n'
    ))

    story.append(H("10.5 Deployment", 2))
    story.append(P("From repo root with Docker Desktop running:", "body"))
    story.append(code(
        '$ docker compose up -d\n'
        '\n'
        '# Then open the citizen UI:\n'
        '$ open http://localhost:5173\n'
        '\n'
        '# Admin login:\n'
        '#   email:    admin@margdarshan.ai\n'
        '#   password: Admin@1234\n'
        '\n'
        '# End-to-end smoke test:\n'
        '$ bash scripts/smoke_test.sh\n'
    ))

    story.append(H("10.6 Environment Variables", 2))
    story.append(code(
        'ANTHROPIC_API_KEY=sk-ant-api03-...   # Claude Haiku\n'
        'LOCATIONIQ_API_KEY=...               # optional, fallback to OSM\n'
        'POSTGRES_USER=grievance\n'
        'POSTGRES_PASSWORD=...\n'
        'POSTGRES_DB=grievance\n'
        'REDIS_HOST=redis  REDIS_PORT=6379\n'
        'JWT_SECRET=...                       # 32+ chars\n'
        'ADMIN_EMAIL=admin@margdarshan.ai    # bootstrapped on first start\n'
        'ADMIN_PASSWORD=Admin@1234\n'
        'USE_RULE_BASED_CLASSIFIER=true       # false -> MuRIL\n'
        'CHATBOT_URL=http://service-chatbot:8001\n'
        'NLU_URL=http://service-nlu:8003\n'
        'CLASSIFIER_URL=http://service-classifier:8004\n'
        'ROUTING_URL=http://service-routing:8005\n'
        'SUBMISSION_URL=http://service-submission:8006\n'
        'TRACKER_URL=http://service-tracker:8007\n'
        'LOCATION_URL=http://service-location:8002\n'
        'VITE_GATEWAY_URL=http://localhost:8000\n'
    ))

    story.append(Spacer(1, 1*cm))
    story.append(hr())
    story.append(P("Document end. Generated programmatically from the live codebase on 2026-05-12.", "caption"))

    return story


# ─── Build the doc ──────────────────────────────────────────────────────────
def main():
    doc = BaseDocTemplate(
        str(OUT_PATH),
        pagesize=A4,
        leftMargin=1.6 * cm, rightMargin=1.6 * cm,
        topMargin=1.6 * cm, bottomMargin=1.6 * cm,
        title="Margdarshan.ai - Technical Documentation",
        author="Team Merge Conflict - BGI Hackathon 2026",
    )

    cover_frame = Frame(0, 0, A4[0], A4[1], leftPadding=1.8*cm, rightPadding=1.8*cm,
                        topPadding=8*cm, bottomPadding=1.6*cm, id="cover")
    body_frame = Frame(doc.leftMargin, doc.bottomMargin,
                       doc.width, doc.height, id="body")

    doc.addPageTemplates([
        PageTemplate(id="Cover", frames=[cover_frame], onPage=cover_decoration),
        PageTemplate(id="Body", frames=[body_frame], onPage=page_decoration),
    ])

    story = build_story()
    doc.build(story)

    print(f"Wrote {OUT_PATH}  ({OUT_PATH.stat().st_size // 1024} KB)")


if __name__ == "__main__":
    main()
