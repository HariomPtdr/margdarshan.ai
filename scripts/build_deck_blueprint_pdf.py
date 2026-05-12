"""Generate the slide-by-slide BUILD BLUEPRINT for the Margdarshan.ai pitch deck.

For each slide:
 - exact on-slide TEXT (title, subtitle, bullets — paste-ready into PPT)
 - an IMAGE / DIAGRAM PROMPT (ready to feed into Midjourney / DALL-E / Napkin / draw.io)
 - optional layout note

Run: python3 scripts/build_deck_blueprint_pdf.py
Output: docs/Margdarshan-ai-Deck-Blueprint.pdf
"""

from __future__ import annotations

from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.platypus import (
    BaseDocTemplate,
    Frame,
    PageBreak,
    PageTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
)
from reportlab.platypus.flowables import HRFlowable


OUT_DIR = Path(__file__).resolve().parent.parent / "docs"
OUT_DIR.mkdir(exist_ok=True)
OUT_PATH = OUT_DIR / "Margdarshan-ai-Deck-Blueprint.pdf"


BRAND_DARK = colors.HexColor("#0F172A")
BRAND_PRIMARY = colors.HexColor("#1E3A8A")
BRAND_ACCENT = colors.HexColor("#F59E0B")
LIGHT_GREY = colors.HexColor("#F1F5F9")
MID_GREY = colors.HexColor("#475569")
CARD_BG = colors.HexColor("#EFF6FF")
TEXT_BG = colors.HexColor("#ECFDF5")
IMG_BG = colors.HexColor("#FDF2F8")
LAYOUT_BG = colors.HexColor("#FFFBEB")

base = getSampleStyleSheet()


def styles():
    s = {}
    s["slide_no"] = ParagraphStyle("slide_no", parent=base["Normal"],
        fontName="Helvetica-Bold", fontSize=9, leading=12, textColor=BRAND_ACCENT, spaceAfter=2)
    s["slide_title"] = ParagraphStyle("slide_title", parent=base["Heading1"],
        fontName="Helvetica-Bold", fontSize=20, leading=24, textColor=BRAND_PRIMARY, spaceAfter=2)
    s["slide_sub"] = ParagraphStyle("slide_sub", parent=base["Normal"],
        fontName="Helvetica-Oblique", fontSize=11, leading=14, textColor=MID_GREY, spaceAfter=6)
    s["block_h"] = ParagraphStyle("block_h", parent=base["Normal"],
        fontName="Helvetica-Bold", fontSize=10, leading=13, textColor=BRAND_DARK, spaceAfter=3)
    s["text"] = ParagraphStyle("text", parent=base["Normal"],
        fontName="Helvetica", fontSize=10, leading=14, textColor=BRAND_DARK, spaceAfter=3, alignment=4)
    s["bullet"] = ParagraphStyle("bullet", parent=base["Normal"],
        fontName="Helvetica", fontSize=10, leading=13.5, textColor=BRAND_DARK,
        leftIndent=12, bulletIndent=2, spaceAfter=2)
    s["title_on_slide"] = ParagraphStyle("title_on_slide", parent=base["Normal"],
        fontName="Helvetica-Bold", fontSize=14, leading=18, textColor=BRAND_DARK, spaceAfter=4)
    s["subtitle_on_slide"] = ParagraphStyle("subtitle_on_slide", parent=base["Normal"],
        fontName="Helvetica-Oblique", fontSize=11, leading=14, textColor=MID_GREY, spaceAfter=4)
    s["caption"] = ParagraphStyle("caption", parent=base["Normal"],
        fontName="Helvetica", fontSize=9, leading=12, textColor=MID_GREY, spaceAfter=2)
    s["mono"] = ParagraphStyle("mono", parent=base["Normal"],
        fontName="Courier", fontSize=9, leading=12, textColor=BRAND_DARK, spaceAfter=2)
    return s


S = styles()


def slide_header(num, title, sub=None, time=None):
    out = [Paragraph(f"SLIDE {num:02d}{'  ·  ' + time if time else ''}", S["slide_no"]),
           Paragraph(title, S["slide_title"])]
    if sub:
        out.append(Paragraph(sub, S["slide_sub"]))
    out.append(HRFlowable(width="100%", thickness=1.2, color=BRAND_ACCENT, spaceAfter=6))
    return out


def labeled_box(label, paragraphs, bg, border):
    inner = [Paragraph(label, S["block_h"])] + paragraphs
    t = Table([[inner]], colWidths=[16.5 * cm])
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), bg),
        ("BOX", (0, 0), (-1, -1), 0.6, border),
        ("LEFTPADDING", (0, 0), (-1, -1), 9),
        ("RIGHTPADDING", (0, 0), (-1, -1), 9),
        ("TOPPADDING", (0, 0), (-1, -1), 7),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
    ]))
    return t


def text_box(items):
    """Exact text to put on the slide (paste-ready)."""
    paras = []
    for it in items:
        if it.startswith("__TITLE__"):
            paras.append(Paragraph(it.replace("__TITLE__", "").strip(), S["title_on_slide"]))
        elif it.startswith("__SUB__"):
            paras.append(Paragraph(it.replace("__SUB__", "").strip(), S["subtitle_on_slide"]))
        elif it.startswith("__PARA__"):
            paras.append(Paragraph(it.replace("__PARA__", "").strip(), S["text"]))
        elif it.startswith("__MONO__"):
            paras.append(Paragraph(it.replace("__MONO__", "").strip(), S["mono"]))
        else:
            paras.append(Paragraph(f"&bull;&nbsp;&nbsp;{it}", S["bullet"]))
    return labeled_box("📋 SLIDE TEXT (paste verbatim into PPT)", paras, TEXT_BG, BRAND_PRIMARY)


def image_box(prompt, tool_hint="Midjourney / DALL·E 3 / Ideogram"):
    paras = [
        Paragraph(f"<b>Suggested tools:</b> {tool_hint}", S["caption"]),
        Spacer(1, 2),
        Paragraph(prompt, S["text"]),
    ]
    return labeled_box("🎨 IMAGE / DIAGRAM PROMPT", paras, IMG_BG, colors.HexColor("#BE185D"))


def layout_box(text):
    return labeled_box("📐 LAYOUT NOTE", [Paragraph(text, S["text"])], LAYOUT_BG, BRAND_ACCENT)


def on_page(c, doc):
    c.saveState()
    c.setFillColor(BRAND_PRIMARY)
    c.rect(0, A4[1] - 0.7 * cm, A4[0], 0.7 * cm, stroke=0, fill=1)
    c.setFont("Helvetica-Bold", 9)
    c.setFillColor(colors.white)
    c.drawString(1.5 * cm, A4[1] - 0.46 * cm, "MARGDARSHAN.AI · Slide-by-Slide Build Blueprint")
    c.setFont("Helvetica", 9)
    c.drawRightString(A4[0] - 1.5 * cm, A4[1] - 0.46 * cm, "Team Merge Conflict · 2515 · BT1P1")
    c.setFillColor(MID_GREY)
    c.setFont("Helvetica", 8)
    c.drawCentredString(A4[0] / 2.0, 0.8 * cm, f"Page {doc.page}")
    c.restoreState()


def build():
    doc = BaseDocTemplate(str(OUT_PATH), pagesize=A4,
                          leftMargin=1.5 * cm, rightMargin=1.5 * cm,
                          topMargin=1.5 * cm, bottomMargin=1.5 * cm,
                          title="Margdarshan.ai — Deck Build Blueprint")
    frame = Frame(doc.leftMargin, doc.bottomMargin, doc.width, doc.height,
                  id="main", leftPadding=0, rightPadding=0, topPadding=0, bottomPadding=0)
    doc.addPageTemplates([PageTemplate(id="all", frames=[frame], onPage=on_page)])

    flow = []

    # ─── Cover ──────────────────────────────────────────────────────────────
    flow.append(Spacer(1, 1.0 * cm))
    flow.append(Paragraph("DECK BUILD BLUEPRINT", S["slide_no"]))
    flow.append(Paragraph("Margdarshan.ai", ParagraphStyle(
        "cover", parent=base["Heading1"], fontName="Helvetica-Bold",
        fontSize=40, leading=44, textColor=BRAND_PRIMARY, spaceAfter=8)))
    flow.append(Paragraph(
        "Build your PowerPoint slide-by-slide — exact text + image prompts",
        ParagraphStyle("cover_sub", parent=base["Normal"], fontName="Helvetica",
                       fontSize=14, leading=18, textColor=MID_GREY, spaceAfter=18)))
    flow.append(HRFlowable(width="60%", thickness=2, color=BRAND_ACCENT, spaceAfter=12))
    flow.append(Paragraph("BGI Hackathon 2026 · Problem BT1P1 · Team Merge Conflict (ID 2515)", S["text"]))
    flow.append(Spacer(1, 0.9 * cm))

    flow.append(Paragraph("How to use this blueprint", S["block_h"]))
    flow.append(Paragraph(
        "<b>Total slides: 18</b> &nbsp;·&nbsp; <b>Pitch time: 10 minutes</b> &nbsp;·&nbsp; <b>Aspect: 16:9</b><br/>"
        "For each slide you get three blocks:",
        S["text"]))
    flow.append(Spacer(1, 0.2 * cm))
    flow += [
        Paragraph("&bull;&nbsp;&nbsp;<b>📋 SLIDE TEXT</b> — copy/paste the headings and bullets directly into a PPT shape.", S["bullet"]),
        Paragraph("&bull;&nbsp;&nbsp;<b>🎨 IMAGE / DIAGRAM PROMPT</b> — paste this into Midjourney, DALL·E, Ideogram, or Napkin AI to generate the visual. For architecture diagrams, also works in draw.io / Mermaid / Eraser.", S["bullet"]),
        Paragraph("&bull;&nbsp;&nbsp;<b>📐 LAYOUT NOTE</b> — where to place text vs image on the 16:9 canvas.", S["bullet"]),
    ]
    flow.append(Spacer(1, 0.4 * cm))
    flow.append(Paragraph("Brand kit", S["block_h"]))
    flow.append(Paragraph(
        "<b>Colours</b> — primary <b>#1E3A8A</b> (deep blue), accent <b>#F59E0B</b> (amber), "
        "text <b>#0F172A</b>, mid-grey <b>#475569</b>, card bg <b>#EFF6FF</b>.<br/>"
        "<b>Fonts</b> — Inter / Helvetica / Calibri (titles bold 36–44pt, body 18–22pt).",
        S["text"]))
    flow.append(PageBreak())

    # ════════════════════════════════════════════════════════════════════════
    # SLIDE 1 — TITLE
    # ════════════════════════════════════════════════════════════════════════
    flow += slide_header(1, "Title slide", "Hook the room in 15 seconds", time="0:15")
    flow.append(text_box([
        "__TITLE__ Margdarshan.ai",
        "__SUB__ Guiding 1.4 billion citizens to the right grievance portal — in their own language",
        "Multilingual AI Grievance Redressal Pipeline",
        "BGI Hackathon 2026 · Problem BT1P1",
        "Team Merge Conflict · Team ID 2515",
        "<i>“Bolo, bot sunega — sahi jagah pahunchayega.”</i>",
    ]))
    flow.append(Spacer(1, 0.15 * cm))
    flow.append(image_box(
        "A modern Indian-themed hero illustration in flat vector style. "
        "Centre: a glowing chat bubble with a tiny compass needle inside it, pointing northeast. "
        "Background: faint Indian tricolour gradient (saffron-white-green) at 8% opacity, abstract circuitry overlay. "
        "Foreground silhouettes of diverse Indian citizens (rural woman with sari, urban youth with phone, "
        "elderly farmer, female student) looking up at the chat bubble. "
        "Colour palette: deep blue #1E3A8A, amber #F59E0B accents, off-white background. "
        "Style: clean, professional, hopeful, government-grade — no cartoon eyes, no emoji. "
        "Aspect ratio 16:9, 4K, vector illustration."
    ))
    flow.append(layout_box(
        "Top-left: small Margdarshan.ai logo. Centre-stage: huge product name (60pt) + tagline (24pt). "
        "Bottom-left: hackathon + team line. Bottom-right: QR code linking to demo. "
        "Hero illustration as full-bleed background at 15-20% opacity behind the title."
    ))
    flow.append(PageBreak())

    # ════════════════════════════════════════════════════════════════════════
    # SLIDE 2 — PROBLEM
    # ════════════════════════════════════════════════════════════════════════
    flow += slide_header(2, "The Problem", "Grievance redressal in India is broken at every step", time="0:45")
    flow.append(text_box([
        "__TITLE__ The Problem",
        "__SUB__ India's grievance system is fragmented, slow, and English-first",
        "<b>70+</b> government portals — overlapping, fragmented mandates",
        "<b>47 days</b> average resolution (CPGRAMS 2024 public data)",
        "<b>~38%</b> of complaints filed at the wrong portal",
        "<b>Language barrier</b> — most portals are English-first; 78% of India prefers a regional language",
        "<b>Duplicates flood officers</b> — 30 households, 1 transformer, 30 separate tickets",
        "<b>No closure loop</b> — citizens don't know if it's resolved unless they keep checking",
        "<b>No accountability</b> — no tamper-evident record of who acted, when",
    ]))
    flow.append(Spacer(1, 0.15 * cm))
    flow.append(image_box(
        "An infographic-style illustration showing a frustrated Indian citizen at the centre, "
        "surrounded by a chaotic maze of overlapping government portal logos and forms (CPGRAMS, "
        "MyGov, state helpline numbers, discom forms — generic looking, not real logos). "
        "Tangled arrows go in every direction. Stack of unread papers piling up. A wall calendar showing 47 days crossed off. "
        "Style: flat editorial illustration, slightly desaturated mood, palette of muted blues and "
        "warm orange accents on the citizen. Background: light grey #F1F5F9. "
        "Convey overwhelm without being depressing. Vector style, 16:9."
    ))
    flow.append(layout_box(
        "Left 40%: three big KPI cards stacked vertically — '70+', '47 days', '38%'. "
        "Right 60%: the chaos illustration. Below illustration: small caption ‘— and we asked: what if a citizen never had to choose?’"
    ))
    flow.append(PageBreak())

    # ════════════════════════════════════════════════════════════════════════
    # SLIDE 3 — WHY CURRENT TOOLS FAIL
    # ════════════════════════════════════════════════════════════════════════
    flow += slide_header(3, "Why Today's Tools Fail", "Forms, helplines, chatbots — each misses something critical", time="0:45")
    flow.append(text_box([
        "__TITLE__ Why Today's Tools Fail",
        "__SUB__ Each existing tool solves only one piece of the puzzle",
        "<b>CPGRAMS web form:</b> partial Hindi · no auto-routing · no dedup · no audit",
        "<b>MP CM Helpline 181:</b> voice only · manual operator routing · no dedup · no audit",
        "<b>MyGov chatbot:</b> English-first · no portal routing · no submission · no tracking",
        "<b>Margdarshan.ai:</b> Hindi/English/Hinglish · auto-routing across 70 portals · S-BERT dedup · "
        "adaptive polling · SHA-256 audit · reviewer override loop",
    ]))
    flow.append(Spacer(1, 0.15 * cm))
    flow.append(image_box(
        "Create a 4-column comparison TABLE diagram (not photo). "
        "Columns: 'CPGRAMS', 'MP 181', 'MyGov chatbot', 'Margdarshan.ai'. "
        "Rows: 'Native Hindi/Hinglish input', 'Auto-routing across portals', 'Semantic deduplication', "
        "'Adaptive status polling', 'Tamper-evident audit trail', 'Reviewer feedback loop'. "
        "Cells: red × for No, amber for Partial, green ✓ for Yes. "
        "Margdarshan column should be all green ✓ — highlight it with a soft amber column background. "
        "Style: clean, minimalist, infographic, white background, blue #1E3A8A header row. "
        "RECOMMENDED TOOL: use Napkin AI or Figma to build this as a table — image AI struggles with text-heavy tables. "
        "Or just build the table natively in PowerPoint using the brand colours."
    ))
    flow.append(layout_box(
        "Full-width comparison table fills 80% of the slide. Title centred at top. Below the table, one-line takeaway: "
        "‘<b>We're not competing with a feature — we're competing with all of them at once.</b>’"
    ))
    flow.append(PageBreak())

    # ════════════════════════════════════════════════════════════════════════
    # SLIDE 4 — INTRODUCING THE PRODUCT
    # ════════════════════════════════════════════════════════════════════════
    flow += slide_header(4, "Introducing Margdarshan.ai", "Speak the problem — we do the rest", time="0:30")
    flow.append(text_box([
        "__TITLE__ Introducing Margdarshan.ai",
        "__SUB__ One conversational pipeline — two audiences",
        "__PARA__ <b>A multilingual AI grievance pipeline.</b> Citizens describe a problem in Hindi, English, or Hinglish — "
        "by typing or speaking. We classify across 25 departments and 142 sub-categories, deduplicate with multilingual "
        "S-BERT, route to the correct portal out of 70+, submit, track end-to-end, and notify on WhatsApp — "
        "all with a tamper-evident audit chain.",
        "<b>Citizen UI</b> — chat (typed + voice), location pin, bilingual notifications",
        "<b>Department Dashboard</b> — stats, drill-down, override, duplicate clusters, audit timeline",
        "<b>REST API</b> — pluggable by any other citizen-services app",
    ]))
    flow.append(Spacer(1, 0.15 * cm))
    flow.append(image_box(
        "Side-by-side product mockup illustration. LEFT: a smartphone in portrait orientation showing a "
        "chat interface with messages in Devanagari Hindi and Hinglish; a microphone icon glowing. "
        "RIGHT: a laptop in front view showing a clean admin dashboard with KPI cards, a complaint list, "
        "and a map of India with dots. Between them: a curved bidirectional arrow with the label "
        "'one backend · same data · two audiences' in small caps. "
        "Style: isometric or 3/4 perspective, flat vector, brand palette (deep blue, amber, white). "
        "16:9, clean drop shadows, no real brand names on screens. Hyper-realistic UI fidelity, not cartoon."
    ))
    flow.append(layout_box(
        "Top: title + subtitle. Middle 60%: the side-by-side mockup. Bottom: three thin badges in a row — "
        "‘Citizen UI’ · ‘Department Dashboard’ · ‘REST API’."
    ))
    flow.append(PageBreak())

    # ════════════════════════════════════════════════════════════════════════
    # SLIDE 5 — LIVE DEMO FLOW
    # ════════════════════════════════════════════════════════════════════════
    flow += slide_header(5, "Live Demo — The Citizen Journey", "One complaint, ten stages, ninety seconds", time="1:00")
    flow.append(text_box([
        "__TITLE__ Live Demo — The Citizen Journey",
        "__SUB__ One complaint → ten stages → under a second per stage",
        "<b>1. Chat</b> — “bijli 3 din se nahi aa rahi, Bhopal MP” (typed or spoken)",
        "<b>2. NLU</b> — Claude Haiku 4.5 extracts intent, entities, language",
        "<b>3. Classify</b> — MuRIL → ELECTRICITY · POWER_OUTAGE · HIGH · FRUSTRATED",
        "<b>4. Location</b> — Leaflet map pin → LocationIQ reverse-geocode → Bhopal 462001",
        "<b>5. Route</b> — 70-portal lookup → MPPKVVCL (regional discom)",
        "<b>6. Dedup</b> — S-BERT cosine vs last 30 days · threshold 0.85",
        "<b>7. Field collection</b> — portal-specific fields · 11 regex validators",
        "<b>8. Submit</b> — adapter POST → ticket ID <b>ELE/MPB/0042</b>",
        "<b>9. Track</b> — 1h / 6h / 24h adaptive polling cadence",
        "<b>10. Close loop</b> — bilingual WhatsApp · ‘1=satisfied · 2=reopen’",
    ]))
    flow.append(Spacer(1, 0.15 * cm))
    flow.append(image_box(
        "A horizontal 10-step journey-map infographic. Each step is a numbered circle (1 through 10) "
        "connected by a flowing curved line that snakes across the canvas left to right. "
        "Each circle has a small icon inside: (1) chat bubble, (2) brain, (3) tag, (4) map pin, "
        "(5) hierarchical tree, (6) overlapping circles, (7) form, (8) paper plane, (9) clock, (10) checkmark. "
        "Below each circle: short 2-3 word label. The line should pulse with an amber glow indicating live flow. "
        "Style: flat vector, deep blue #1E3A8A circles with amber accents, white background. "
        "Aspect 16:9 widescreen. RECOMMENDED TOOL: build this in Figma or Canva for editability; "
        "or use Napkin AI with prompt 'horizontal 10-step process flow with icons'."
    ))
    flow.append(layout_box(
        "Top quarter: title + subtitle. Middle half: the 10-step horizontal journey graphic (full width). "
        "Bottom quarter: a thin band showing a LIVE demo embed — either an actual screen-mirror "
        "frame of the running app, or a 30-second mp4 loop. Backup if WiFi fails: keep mp4 pre-loaded."
    ))
    flow.append(PageBreak())

    # ════════════════════════════════════════════════════════════════════════
    # SLIDE 6 — ARCHITECTURE
    # ════════════════════════════════════════════════════════════════════════
    flow += slide_header(6, "System Architecture", "Ten microservices on Docker Compose · independently deployable", time="0:45")
    flow.append(text_box([
        "__TITLE__ System Architecture",
        "__SUB__ 10 services · FastAPI · Postgres · Redis · Docker Compose",
        "<b>Frontend</b> (5173) — React 18 + Vite + Tailwind + Leaflet · Citizen + Admin in one SPA",
        "<b>Gateway</b> (8000) — public REST + WebSocket · JWT · pipeline orchestrator · SHA-256 audit chain",
        "<b>Chatbot</b> (8001) — Claude Haiku-driven field-collection",
        "<b>NLU</b> (8003) — state machine · intent · entities · language detect",
        "<b>Classifier</b> (8004) — MuRIL + 4 sklearn heads · rule-based fallback toggle",
        "<b>Routing</b> (8005) — 70-portal hierarchical lookup (Regional &gt; State &gt; Central)",
        "<b>Submission</b> (8006) — adapter pattern · 7-attempt exponential backoff",
        "<b>Tracker</b> (8007) — adaptive polling · status normaliser · WhatsApp notify",
        "<b>Location</b> (8002) — LocationIQ → OSM Nominatim → India Post pincode",
        "<b>Data layer</b> — Postgres (JSONB UCO + FLOAT8[] vectors) · Redis pub/sub (pipeline:all)",
    ]))
    flow.append(Spacer(1, 0.15 * cm))
    flow.append(image_box(
        "A clean architecture DIAGRAM (not photo). Build in draw.io / Eraser.io / Mermaid / Excalidraw — "
        "do NOT use Midjourney for this (it can't render boxes/arrows correctly). "
        "Layout: top row — single rounded box 'Web Frontend (React, 5173)'. "
        "Second row — single wider box 'Service Gateway (8000) · Orchestrator · Auth · Audit'. "
        "Third row — 6 boxes in a row: 'Chatbot 8001', 'NLU 8003', 'Classifier 8004', 'Routing 8005', "
        "'Location 8002', 'Submission 8006'. "
        "Below those, one centred box: 'Tracker 8007'. "
        "Bottom row — two cylindrical icons side by side: 'PostgreSQL (UCO + vectors)' and 'Redis (pub/sub bus)'. "
        "Arrows: Frontend ↔ Gateway (REST + WebSocket). Gateway ↔ each worker service. "
        "All services ↔ Redis (dotted line, 'pipeline:all'). "
        "All services ↔ Postgres (solid line). "
        "Use brand colours: boxes filled with #1E3A8A (white text), Redis box in amber #F59E0B. "
        "Output: SVG or high-res PNG, white background, 16:9."
    ))
    flow.append(layout_box(
        "Title top. Full-bleed diagram fills the rest. Add a tiny footer chip: ‘Each box = own Dockerfile + requirements.txt — independent deploy.’"
    ))
    flow.append(PageBreak())

    # ════════════════════════════════════════════════════════════════════════
    # SLIDE 7 — AI/ML STACK
    # ════════════════════════════════════════════════════════════════════════
    flow += slide_header(7, "AI / ML Stack", "Three models, each chosen for a different job", time="0:45")
    flow.append(text_box([
        "__TITLE__ AI / ML Stack",
        "__SUB__ Right tool for each job — not one giant LLM for everything",
        "<b>Conversational LLM</b> — Anthropic Claude Haiku 4.5 · ~700 ms · temperature 0.2",
        "<b>Classifier</b> — Fine-tuned MuRIL (google/muril-base-cased) · dept F1 0.91 · sub-cat F1 ~0.85",
        "<b>Dedup embeddings</b> — paraphrase-multilingual-MiniLM-L12-v2 · 384-dim · cosine ≥ 0.85",
        "<b>Why split?</b> Latency budget · cost · determinism · rule-based fallback for reliability",
        "<b>Confidence-aware UX</b> — low-confidence triggers a clarifying question instead of mis-routing",
        "<b>Human-in-loop</b> — reviewer overrides feed back into the next MuRIL training cycle",
    ]))
    flow.append(Spacer(1, 0.15 * cm))
    flow.append(image_box(
        "Three side-by-side vertical 'model cards' in a row, infographic style. "
        "Card 1 (BLUE): icon of a speech bubble with sparkles; label 'Claude Haiku 4.5'; "
        "stat '~700 ms · temp 0.2'; role 'Conversation + extraction'. "
        "Card 2 (GREEN): icon of a tag/label classifier with branching tree; label 'MuRIL Fine-Tuned'; "
        "stat '25 depts · 142 sub-cats · F1 0.91'; role 'Classification + priority'. "
        "Card 3 (AMBER): icon of overlapping circles forming a Venn-like pattern; label 'S-BERT Multilingual'; "
        "stat '384-dim · cosine ≥ 0.85'; role 'Cross-language deduplication'. "
        "Below the three cards, a horizontal stacked bar showing combined pipeline latency under 1 second. "
        "Style: clean infographic, white background, branded blue/amber, drop shadows. 16:9."
    ))
    flow.append(layout_box(
        "Title + subtitle on top. Three model cards in the middle (each occupies ~30% width). "
        "Bottom: thin horizontal latency bar with markers Haiku 700ms, MuRIL 30ms, S-BERT 50ms, "
        "totalling under 1s."
    ))
    flow.append(PageBreak())

    # ════════════════════════════════════════════════════════════════════════
    # SLIDE 8 — 70-PORTAL ROUTING
    # ════════════════════════════════════════════════════════════════════════
    flow += slide_header(8, "70-Portal Routing", "Hierarchical specificity — never the catch-all when a regional desk exists", time="0:30")
    flow.append(text_box([
        "__TITLE__ 70-Portal Routing",
        "__SUB__ Send the complaint where it can actually be solved",
        "<b>Tier 1 · Regional</b> — e.g., MPPKVVCL for Bhopal electricity",
        "<b>Tier 2 · State-specific</b> — e.g., MP CM Helpline 181",
        "<b>Tier 3 · State catch-all</b> — e.g., state CMO portal",
        "<b>Tier 4 · Central-specific</b> — e.g., Railways grievance",
        "<b>Tier 5 · Central catch-all</b> — CPGRAMS (last resort, not default)",
        "__PARA__ <b>Why it matters:</b> a Bhopal power cut sent to CPGRAMS sits in a national queue for weeks. "
        "Sent to MPPKVVCL, the discom owns it immediately. Specificity-sorted match across portals.csv.",
    ]))
    flow.append(Spacer(1, 0.15 * cm))
    flow.append(image_box(
        "A 5-tier PYRAMID infographic — pyramid is INVERTED (point at bottom, wide at top). "
        "Top widest layer labelled 'Tier 5 · Central catch-all (CPGRAMS)' in lightest amber. "
        "Each layer below narrower and progressively darker amber/blue: "
        "Tier 4 'Central-specific', Tier 3 'State catch-all', Tier 2 'State-specific', "
        "Tier 1 'Regional' (smallest, darkest blue at bottom). "
        "Animate a 'Bhopal electricity' complaint chip falling THROUGH the layers and locking onto Tier 1. "
        "A second 'pan-India IT' chip falls only to Tier 4. "
        "Style: clean vector infographic, brand colours, white background. "
        "Below the pyramid: small text — ‘Specificity wins: solver-owner-portal > catch-all’. 16:9."
    ))
    flow.append(layout_box(
        "Left half: the inverted pyramid graphic. Right half: bullet list of 5 tiers with one example each. "
        "Bottom strip: italic one-liner ‘We made CPGRAMS our fallback — not our front door.’"
    ))
    flow.append(PageBreak())

    # ════════════════════════════════════════════════════════════════════════
    # SLIDE 9 — DEDUP
    # ════════════════════════════════════════════════════════════════════════
    flow += slide_header(9, "Semantic Deduplication", "30 households · 1 transformer fault · 1 ticket", time="0:30")
    flow.append(text_box([
        "__TITLE__ Semantic Deduplication",
        "__SUB__ S-BERT multilingual embeddings · cosine ≥ 0.85",
        "<b>Embedding model</b> — paraphrase-multilingual-MiniLM-L12-v2 (117 MB · 384-dim · runs locally)",
        "<b>Scope</b> — last 30 days · same district · partial Postgres FLOAT8[] index",
        "<b>Cross-language</b> — “bijli nahi aa rahi” ≈ “no electricity since yesterday” (cosine ~0.91)",
        "<b>Cluster view</b> — dashboard surfaces all linked complaints to one parent ticket",
        "<b>Why this beats keyword/full-text</b> — paraphrases and Hindi/Hinglish are caught natively",
    ]))
    flow.append(Spacer(1, 0.15 * cm))
    flow.append(image_box(
        "A network-graph CLUSTER diagram. Central large node (deep blue) labelled 'Parent Complaint: "
        "Transformer fault, Bhopal sector 12'. Around it, 30 smaller orange/amber dots, each labelled "
        "with a different house number, all connected to the centre by thin lines. Each line has a tiny "
        "label showing cosine similarity value between 0.85 and 0.97. "
        "Two dots in red highlight cross-language pairs: one labelled in Hindi ('बिजली नहीं आ रही'), "
        "one in English ('no power since morning'). "
        "Add a dashed horizontal threshold line marked '0.85 cosine threshold'. "
        "Style: clean data-viz infographic, brand colours, white background, drop shadows. 16:9."
    ))
    flow.append(layout_box(
        "Left 55%: the cluster diagram. Right 45%: 5 short bullets and a callout box reading "
        "‘<b>Officers love this most</b> — saved hours/day on manual dedup.’"
    ))
    flow.append(PageBreak())

    # ════════════════════════════════════════════════════════════════════════
    # SLIDE 10 — SUBMISSION + RETRY
    # ════════════════════════════════════════════════════════════════════════
    flow += slide_header(10, "Submission &amp; Reliability", "Adapter pattern + 7-attempt exponential backoff", time="0:30")
    flow.append(text_box([
        "__TITLE__ Submission &amp; Reliability",
        "__SUB__ Plug-in adapters · resilient to portal outages",
        "__MONO__ submit() · check_status() · list_fields() · validate()",
        "<b>Adapters shipped:</b> CPGRAMS · MP CM 181 · MPPKVVCL · Generic fallback",
        "<b>Retry schedule:</b> 1m → 2m → 5m → 15m → 1h → 4h → 24h (7 attempts)",
        "<b>After 7 fails</b> → moves to 'manual intervention' queue in dashboard (never silently dropped)",
        "<b>Adding a new portal</b> = one Python class + one row in portals.csv (no core changes)",
    ]))
    flow.append(Spacer(1, 0.15 * cm))
    flow.append(image_box(
        "An infographic timeline showing 7 progressively wider boxes left-to-right. "
        "Each box is labelled: '1 min', '2 min', '5 min', '15 min', '1 hour', '4 hours', '24 hours'. "
        "Above the timeline: a thin curve depicting the exponential backoff growth. "
        "Below each box: a small icon showing the type of failure that interval absorbs "
        "(network blip, portal maintenance, weekend, DNS issue, certificate renewal, full outage, multi-day downtime). "
        "At the right end: an arrow leading to a final 'Manual Queue' box in amber. "
        "Style: clean flat infographic, brand colours, white background. 16:9 horizontal."
    ))
    flow.append(layout_box(
        "Top: title + adapter contract line in monospace. Middle: full-width 7-box timeline graphic. "
        "Bottom: 1-line takeaway ‘<b>Government portals fail — we don't.</b>’"
    ))
    flow.append(PageBreak())

    # ════════════════════════════════════════════════════════════════════════
    # SLIDE 11 — STATUS TRACKING
    # ════════════════════════════════════════════════════════════════════════
    flow += slide_header(11, "Adaptive Status Tracking", "Polls hard early · relaxes once stable", time="0:30")
    flow.append(text_box([
        "__TITLE__ Adaptive Status Tracking",
        "__SUB__ The citizen never has to log in again to check status",
        "<b>Day 1</b> — poll every 1 hour (status changes most often early)",
        "<b>Day 2–7</b> — poll every 6 hours",
        "<b>Day 8+</b> — poll every 24 hours",
        "<b>Stops on</b> — RESOLVED or REJECTED terminal state",
        "<b>Status normaliser</b> — maps portal vocabulary to: SUBMITTED · UNDER_REVIEW · IN_PROGRESS · RESOLVED · REJECTED · ESCALATED",
        "<b>Bilingual WhatsApp</b> — Hindi first, English second · ‘1 = satisfied · 2 = reopen’",
    ]))
    flow.append(Spacer(1, 0.15 * cm))
    flow.append(image_box(
        "Split-view infographic. LEFT HALF: a line chart showing polling frequency on Y-axis (24/day → 4/day → 1/day) "
        "vs days on X-axis (1 to 30). The curve drops sharply after day 1, plateaus, drops again after day 7. "
        "Label spikes with '1h cadence', '6h cadence', '24h cadence'. "
        "RIGHT HALF: a smartphone mockup showing a WhatsApp conversation. Two message bubbles visible — "
        "one in Hindi Devanagari (‘आपकी शिकायत हल हो गई है — संतुष्ट हैं? 1 = हाँ, 2 = फिर से खोलें’), "
        "one in English below it (‘Your complaint is resolved — satisfied? 1 = yes, 2 = reopen’). "
        "Style: clean editorial infographic, brand colours, light grey background. 16:9."
    ))
    flow.append(layout_box(
        "Left half: title + 6 bullets. Right half: split image (chart top, phone bottom). "
        "Bottom-right corner: amber tag ‘<b>Closure loop closed.</b>’"
    ))
    flow.append(PageBreak())

    # ════════════════════════════════════════════════════════════════════════
    # SLIDE 12 — DASHBOARD
    # ════════════════════════════════════════════════════════════════════════
    flow += slide_header(12, "Government Dashboard", "Same backend · different audience", time="0:45")
    flow.append(text_box([
        "__TITLE__ Government Dashboard",
        "__SUB__ Stats · drill-down · override · audit",
        "<b>Stats overview</b> — total · duplicates · by status · by dept · by district",
        "<b>Portal registry</b> — all 70 portals with authority, helpline, complaint count",
        "<b>Complaints list</b> — filterable; priority and sentiment badges; duplicate flags",
        "<b>Drill-down</b> — PII-masked filer info · top-3 classification alternatives · routing rule · SHA-256 audit chain",
        "<b>Review form</b> — thumbs ↑/↓ · override dept · sub-cat · priority · sentiment → trains next model",
        "<b>Duplicate-filer view</b> — repeat filers + cross-user clusters (the 30-household case)",
        "<b>API trace</b> — animated 5-step demo of live JSON exchanges between services",
    ]))
    flow.append(Spacer(1, 0.15 * cm))
    flow.append(image_box(
        "A 4-panel laptop SCREENSHOT collage of the dashboard. "
        "Top-left panel: KPI hero cards (Total: 1,247 · Resolved: 892 · Duplicates: 134 · Avg Resolution: 9.2 days) "
        "and a horizontal bar chart of complaints-by-department. "
        "Top-right: complaint drill-down view with filer info (PII masked as ****), "
        "classification confidence scores (top 3), and a vertical timeline showing SHA-256 audit chain entries. "
        "Bottom-left: duplicate cluster graph with one parent complaint and 12 child complaints. "
        "Bottom-right: review form with thumbs-up/down buttons, override dropdowns. "
        "Style: clean modern dashboard UI, deep-blue header, white background, amber accent buttons. "
        "USE ACTUAL SCREENSHOTS from your running app — these mockups are descriptive, replace with real screen-captures. "
        "16:9 layout, drop shadows under each panel."
    ))
    flow.append(layout_box(
        "Full-bleed 2x2 collage of dashboard screenshots. Tiny labels in each corner identifying the panel. "
        "Title overlay top-left in white on a translucent dark band."
    ))
    flow.append(PageBreak())

    # ════════════════════════════════════════════════════════════════════════
    # SLIDE 13 — MULTILINGUAL UX
    # ════════════════════════════════════════════════════════════════════════
    flow += slide_header(13, "Multilingual UX &amp; Voice", "Speak · type · mix · we hear you", time="0:30")
    flow.append(text_box([
        "__TITLE__ Multilingual UX &amp; Voice",
        "__SUB__ Hindi · English · Hinglish — full UI, bot replies, notifications, voice input",
        "<b>हिन्दी</b> (Devanagari) — full UI + replies + WhatsApp",
        "<b>English</b> — same coverage",
        "<b>Hinglish</b> (Roman-script Hindi) — default for new users · most common comfort-language in tier-2/3 India",
        "<b>Voice input</b> — Web Speech API · hi-IN / en-IN locales · tested on Chrome Android",
        "<b>Auto-detect</b> — bot replies in the SAME language the citizen typed/spoke, not their stored preference",
        "<b>Switchable</b> — top-right language toggle persists per user",
    ]))
    flow.append(Spacer(1, 0.15 * cm))
    flow.append(image_box(
        "Three side-by-side smartphone screen mockups, same chat conversation in three languages. "
        "PHONE 1 (left): chat in Devanagari Hindi — user types ‘बिजली तीन दिन से नहीं आ रही’, bot replies in Hindi. "
        "PHONE 2 (centre): chat in English — user types ‘no electricity for 3 days’, bot replies in English. "
        "PHONE 3 (right): chat in Hinglish — user types ‘bijli 3 din se nahi aa rahi’, bot replies in Hinglish. "
        "All three phones have a glowing microphone icon at the bottom. Above each phone: small flag/icon "
        "(devanagari character अ, English A, mixed ‘अA’). "
        "Style: clean isometric or 3/4 perspective, brand colours, white background, drop shadows. 16:9."
    ))
    flow.append(layout_box(
        "Three phones occupying middle 70% of the slide. Title + subtitle top. "
        "Bottom: one line ‘<b>Bot replies in the language it heard, not the language you configured.</b>’"
    ))
    flow.append(PageBreak())

    # ════════════════════════════════════════════════════════════════════════
    # SLIDE 14 — SECURITY + AUDIT
    # ════════════════════════════════════════════════════════════════════════
    flow += slide_header(14, "Security, Audit &amp; Trust", "Tamper-evident by construction · not by policy", time="0:30")
    flow.append(text_box([
        "__TITLE__ Security, Audit &amp; Trust",
        "__SUB__ SHA-256 hash chain · JWT auth · PII masking · 11 field validators",
        "<b>Audit chain</b> — every state change in complaint_events stores SHA-256 of previous event; any tampering breaks the chain",
        "<b>Authentication</b> — bcrypt (cost 12) · JWT HS256 · 24h expiry · roles citizen/reviewer/admin",
        "<b>PII handling</b> — mobile/Aadhaar/email masked to last-4 in list view; full only on drill-down behind reviewer role",
        "<b>Aadhaar Verhoeff checksum</b> — invalid Aadhaars rejected at input; never stored",
        "<b>11 field validators</b> — pincode · mobile · email · Aadhaar · vehicle reg · service no · "
        "consumer no · IFSC · GSTIN · date · time",
        "<b>DPDP-ready</b> — role-gated access, audit on every read",
    ]))
    flow.append(Spacer(1, 0.15 * cm))
    flow.append(image_box(
        "An infographic of a HASH CHAIN as a stylised metal chain. Each link of the chain represents one event "
        "(SUBMITTED → CLASSIFIED → ROUTED → DEDUP_CHECKED → SUBMITTED_TO_PORTAL → STATUS_UPDATE → RESOLVED). "
        "Each link is labelled with the event name and shows a short SHA-256 hex prefix (e.g., '8a3f2c…'). "
        "Inside each link, a small icon: shield, brain, map, magnifier, paper-plane, clock, checkmark. "
        "One link in the middle is highlighted RED with a 'broken' look — captioned ‘Tampering visible immediately’. "
        "Background: dark blue gradient with subtle circuit pattern. Chain in metallic silver with amber glow at intact links. "
        "Style: cyberpunk-meets-government, professional, vector infographic. 16:9."
    ))
    flow.append(layout_box(
        "Top: title + subtitle. Middle 60%: the hash-chain graphic. "
        "Right side: 6 short bullets stacked vertically. Bottom: tag chip ‘<b>DPDP-Act-ready</b>’."
    ))
    flow.append(PageBreak())

    # ════════════════════════════════════════════════════════════════════════
    # SLIDE 15 — DIFFERENTIATORS
    # ════════════════════════════════════════════════════════════════════════
    flow += slide_header(15, "What Sets Us Apart", "Six things we have that the alternatives don't", time="0:30")
    flow.append(text_box([
        "__TITLE__ What Sets Us Apart",
        "__SUB__ Not a chatbot in front of a form — a full pipeline where the form is the last 10%",
        "<b>True multilingual + voice</b> from message 1 — not a translation layer bolted on",
        "<b>70-portal hierarchical routing</b> — regional desks beat central catch-all",
        "<b>Multilingual S-BERT dedup</b> across citizens, not just per-user",
        "<b>Adapter pattern</b> — new portal = 1 Python class + 1 CSV row · no core changes",
        "<b>Adaptive polling + bilingual notifications</b> — citizen never has to come back",
        "<b>SHA-256 audit chain + reviewer override loop</b> — every override trains next model",
    ]))
    flow.append(Spacer(1, 0.15 * cm))
    flow.append(image_box(
        "A 3x2 icon grid (six tiles, two rows of three). Each tile has: a large outlined icon in deep blue, "
        "a 2-3 word title in bold, and a 1-line supporting phrase. "
        "Icons: (1) speech bubble with microphone, (2) hierarchical tree, (3) overlapping rings, "
        "(4) puzzle piece, (5) bell with clock, (6) chain link with shield. "
        "Each tile has a soft amber bottom-border accent. "
        "Style: clean flat-design icon grid, white background, generous spacing. 16:9."
    ))
    flow.append(layout_box(
        "Top: title + subtitle. Middle: the 6-tile icon grid (full width). "
        "Bottom band: italic one-liner — ‘<i>We're not competing with a feature. We're competing with the whole status quo.</i>’"
    ))
    flow.append(PageBreak())

    # ════════════════════════════════════════════════════════════════════════
    # SLIDE 16 — IMPACT + ROADMAP
    # ════════════════════════════════════════════════════════════════════════
    flow += slide_header(16, "Impact, Scale &amp; Roadmap", "Hackathon prototype → national infrastructure", time="0:45")
    flow.append(text_box([
        "__TITLE__ Impact, Scale &amp; Roadmap",
        "__SUB__ Cost per complaint &lt; ₹0.30 · target 500 RPS · pluggable nationwide",
        "<b>TODAY</b> — 70 portals · 25 depts · 142 sub-cats · 3 languages · Docker Compose, single host",
        "<b>3 MONTHS</b> — MP state pilot (real CPGRAMS + 181 + MPPKVVCL POSTs) · voice IVR fallback · weekly auto-retrain",
        "<b>12 MONTHS</b> — 200 portals · 8 states · Kubernetes + HPA · open API for FIR, ambulance, ration apps",
        "<b>Cost economics</b> — &lt; ₹0.30 per complaint (Claude Haiku tokens dominate)",
        "<b>Scale path</b> — CPU-only classifier · Redis horizontal shard · pgvector ready",
    ]))
    flow.append(Spacer(1, 0.15 * cm))
    flow.append(image_box(
        "A horizontal ROADMAP timeline with three milestone markers along it: 'Today', '+3 months', '+12 months'. "
        "Above each marker: a small illustration. Today = a laptop with the dashboard. +3 months = a smartphone "
        "with WhatsApp notification + outline map of Madhya Pradesh. +12 months = an outline map of India with "
        "8 states highlighted in amber and a Kubernetes cluster icon. "
        "Below each marker: 2-3 line caption of what unlocks. "
        "A growth curve runs along the bottom in amber, sloping upward from left to right. "
        "Style: clean editorial infographic, deep blue + amber + white. 16:9 widescreen."
    ))
    flow.append(layout_box(
        "Top: title + subtitle. Middle 70%: the horizontal roadmap timeline. "
        "Bottom: 3 KPI chips in a row — ‘< ₹0.30/complaint’ · ‘500 RPS target’ · ‘1 new portal = 1 Python class’."
    ))
    flow.append(PageBreak())

    # ════════════════════════════════════════════════════════════════════════
    # SLIDE 17 — TEAM
    # ════════════════════════════════════════════════════════════════════════
    flow += slide_header(17, "Team Merge Conflict", "Team ID 2515 · BGI Hackathon 2026 · BT1P1", time="0:15")
    flow.append(text_box([
        "__TITLE__ Team Merge Conflict",
        "__SUB__ Built in 8 weeks · shipped 10 services · onboarded 70 portals",
        "<b>[Name 1] — Backend / Pipeline</b> · gateway orchestrator · audit chain · adapter pattern",
        "<b>[Name 2] — AI / ML</b> · MuRIL fine-tune · S-BERT dedup · classifier rules · Claude prompts",
        "<b>[Name 3] — Frontend</b> · React + Vite SPA · Leaflet · i18n · dashboard · chat UX",
        "<b>[Name 4] — DevOps / Data</b> · Docker Compose · Postgres · training dataset · portals.csv",
        "<b>10 services shipped</b> · <b>70 portals onboarded</b> · <b>3 languages supported</b>",
    ]))
    flow.append(Spacer(1, 0.15 * cm))
    flow.append(image_box(
        "A team photo strip — four square headshot placeholders side by side, each with a name and role badge "
        "below it. Below the strip: a small footer band with GitHub octocat icon + LinkedIn icon + email icon. "
        "REPLACE WITH ACTUAL TEAM PHOTOS in final deck — keep image consistent (same lighting, same neutral background). "
        "If you don't have photos: use plain coloured circles with initials (e.g., ‘HK’) on a deep-blue background. "
        "Style: editorial team page, clean grid, professional. 16:9."
    ))
    flow.append(layout_box(
        "Top: title. Middle 50%: 4-photo strip with names + roles. "
        "Bottom 30%: three big KPI cards — '10 services', '70 portals', '3 languages'. "
        "Bottom-right corner: QR codes to team's GitHub / LinkedIn."
    ))
    flow.append(PageBreak())

    # ════════════════════════════════════════════════════════════════════════
    # SLIDE 18 — THANK YOU + ASK
    # ════════════════════════════════════════════════════════════════════════
    flow += slide_header(18, "Thank You", "Q&amp;A · the ask · the closing line", time="0:15")
    flow.append(text_box([
        "__TITLE__ Thank You",
        "__SUB__ Margdarshan.ai — bolo, bot sunega",
        "<b>The Ask</b>",
        "Pilot opportunity with one state government department",
        "Introduction to DARPG / state CMOs for CPGRAMS MoU",
        "Mentorship on government procurement &amp; DPDP-Act compliance",
        "<b>Try It Live</b>",
        "Citizen UI · <b>http://localhost:5173</b>",
        "Gateway API docs · <b>http://localhost:8000/docs</b>",
        "Admin login · <b>admin@margdarshan.ai / Admin@1234</b>",
        "Technical doc · <i>docs/Margdarshan-ai-Technical-Doc.pdf</i> (35 pages)",
    ]))
    flow.append(Spacer(1, 0.15 * cm))
    flow.append(image_box(
        "A heroic full-bleed closing visual — same illustration family as Slide 1 (citizens looking up at a "
        "glowing chat bubble with a compass needle). This time the scene is brighter, hopeful sunrise tones; "
        "the chat bubble emits soft rays. Add a subtle ‘Q&amp;A’ word-art in the centre in elegant typography. "
        "Style: clean editorial, brand colours, 16:9, leaves whitespace at the bottom for contact info."
    ))
    flow.append(layout_box(
        "Hero illustration as background at 25% opacity. Centre: huge ‘Thank You’ (72pt) + ‘Q&amp;A’ chip. "
        "Bottom: 2 columns — left ‘The Ask’ with 3 bullets, right ‘Try It Live’ with 4 bullets. "
        "Bottom-right corner: QR code to GitHub repo + team handle."
    ))
    flow.append(PageBreak())

    # ════════════════════════════════════════════════════════════════════════
    # APPENDIX A — Tool guide for generating images
    # ════════════════════════════════════════════════════════════════════════
    flow.append(Paragraph("APPENDIX A", S["slide_no"]))
    flow.append(Paragraph("Tool guide — which tool for which visual", S["slide_title"]))
    flow.append(HRFlowable(width="100%", thickness=1.2, color=BRAND_ACCENT, spaceAfter=8))
    tool_rows = [
        ["Visual type", "Best tool", "Notes"],
        ["Hero illustrations (Slides 1, 18)", "Midjourney v6 / DALL·E 3 / Ideogram",
         "Use the full prompt verbatim; --ar 16:9 --style raw on MJ."],
        ["Architecture diagram (Slide 6)", "draw.io / Eraser.io / Excalidraw / Mermaid",
         "Image AI cannot render boxes + arrows + text reliably. Use a diagramming tool."],
        ["Comparison table (Slide 3)", "Native PowerPoint table OR Figma",
         "Build directly in PPT with brand colours — keep text editable."],
        ["KPI / stat infographics (Slides 7, 16, 17)", "Napkin AI / Canva / Figma",
         "These tools handle text-heavy infographics better than Midjourney."],
        ["Process flow (Slide 5 journey, Slide 10 retry)", "Napkin AI / Whimsical / Lucid",
         "Generate a base flow, then re-style in your brand palette."],
        ["Cluster / network graph (Slide 9)", "Napkin AI / D3 export / hand-drawn in Figma",
         "Easier to fake convincingly than generate via image AI."],
        ["Pyramid / tier (Slide 8)", "PowerPoint SmartArt 'Pyramid' OR Figma",
         "Native SmartArt looks fine; saves time."],
        ["Hash chain (Slide 14)", "Midjourney with brand-tinted prompt + overlay text in PPT",
         "Generate the chain image only; overlay event labels in PowerPoint text boxes."],
        ["Phone mockups (Slides 4, 11, 13)", "Mockuuups Studio / Shotsnapp / Figma",
         "Drop real screenshots of YOUR running app into a phone frame template."],
        ["Dashboard collage (Slide 12)", "Real screenshots from your running app, arranged in PPT",
         "Strongly prefer real screenshots over generated images — adds credibility."],
    ]
    tools = Table(tool_rows, colWidths=[5 * cm, 5 * cm, 6.5 * cm])
    tools.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), BRAND_PRIMARY),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTNAME", (0, 1), (0, -1), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [LIGHT_GREY, colors.white]),
        ("GRID", (0, 0), (-1, -1), 0.3, MID_GREY),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 5),
        ("RIGHTPADDING", (0, 0), (-1, -1), 5),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
    ]))
    flow.append(tools)
    flow.append(PageBreak())

    # ════════════════════════════════════════════════════════════════════════
    # APPENDIX B — Master slide template
    # ════════════════════════════════════════════════════════════════════════
    flow.append(Paragraph("APPENDIX B", S["slide_no"]))
    flow.append(Paragraph("Master slide layout (16:9)", S["slide_title"]))
    flow.append(HRFlowable(width="100%", thickness=1.2, color=BRAND_ACCENT, spaceAfter=8))
    flow.append(Paragraph(
        "Set this up ONCE as your slide master in PowerPoint / Keynote / Google Slides so every slide is consistent.",
        S["text"]))
    flow.append(Spacer(1, 0.2 * cm))
    flow.append(Paragraph("Layout structure", S["block_h"]))
    flow += [
        Paragraph("&bull;&nbsp;&nbsp;<b>Top bar</b> (5% height, 1.5cm) — fill #1E3A8A; left: ‘MARGDARSHAN.AI’ in white Helvetica Bold 11pt; right: small slide number in white.", S["bullet"]),
        Paragraph("&bull;&nbsp;&nbsp;<b>Slide title area</b> (10% height) — 36pt bold #1E3A8A, left-aligned, 60px from left edge.", S["bullet"]),
        Paragraph("&bull;&nbsp;&nbsp;<b>Subtitle</b> (italic 18pt, #475569) under the title.", S["bullet"]),
        Paragraph("&bull;&nbsp;&nbsp;<b>Accent rule</b> 2px solid #F59E0B between subtitle and content (gives the deck consistency).", S["bullet"]),
        Paragraph("&bull;&nbsp;&nbsp;<b>Content area</b> (75% height) — 60px margins, 20pt body.", S["bullet"]),
        Paragraph("&bull;&nbsp;&nbsp;<b>Footer</b> (5% height) — light grey; centred page indicator; bottom-right ‘Team Merge Conflict · 2515’ in 9pt.", S["bullet"]),
    ]
    flow.append(Spacer(1, 0.3 * cm))
    flow.append(Paragraph("Standard content blocks", S["block_h"]))
    flow += [
        Paragraph("&bull;&nbsp;&nbsp;<b>KPI Card</b> — 200x140px tile, #EFF6FF fill, 0.5pt #1E3A8A border; big number 36pt bold; small label 11pt grey.", S["bullet"]),
        Paragraph("&bull;&nbsp;&nbsp;<b>Bullet list</b> — 20pt; • bullet in #F59E0B amber; line height 1.4.", S["bullet"]),
        Paragraph("&bull;&nbsp;&nbsp;<b>Code/monospace</b> — JetBrains Mono / Courier 14pt; dark navy fill, white text, 6px corner radius.", S["bullet"]),
        Paragraph("&bull;&nbsp;&nbsp;<b>Callout chip</b> — pill shape, amber fill, white text 11pt; used for taglines / takeaways.", S["bullet"]),
    ]
    flow.append(PageBreak())

    # ════════════════════════════════════════════════════════════════════════
    # APPENDIX C — Single mega-prompt for image AI
    # ════════════════════════════════════════════════════════════════════════
    flow.append(Paragraph("APPENDIX C", S["slide_no"]))
    flow.append(Paragraph("Master style prompt (append to every image AI request)", S["slide_title"]))
    flow.append(HRFlowable(width="100%", thickness=1.2, color=BRAND_ACCENT, spaceAfter=8))
    flow.append(Paragraph(
        "To keep all generated visuals stylistically consistent, append this style suffix to each image prompt above:",
        S["text"]))
    flow.append(Spacer(1, 0.2 * cm))
    style_box = Table([[Paragraph(
        "<i>Style: clean modern editorial infographic, flat vector illustration, Indian-government-grade professional. "
        "Colour palette deep blue #1E3A8A primary, amber #F59E0B accent, off-white background, "
        "dark text #0F172A. Generous whitespace, soft drop shadows, no photo-realism, no faces close-up, "
        "no real brand logos. Aspect ratio 16:9, 4K resolution, high detail, vector style.</i>",
        S["text"])]], colWidths=[16.5 * cm])
    style_box.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), LIGHT_GREY),
        ("BOX", (0, 0), (-1, -1), 0.5, BRAND_PRIMARY),
        ("LEFTPADDING", (0, 0), (-1, -1), 10),
        ("RIGHTPADDING", (0, 0), (-1, -1), 10),
        ("TOPPADDING", (0, 0), (-1, -1), 10),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 10),
    ]))
    flow.append(style_box)

    flow.append(Spacer(1, 0.4 * cm))
    flow.append(Paragraph("Midjourney parameter suffix", S["block_h"]))
    flow.append(Paragraph(
        "If using Midjourney v6, append: <code>--ar 16:9 --style raw --stylize 150 --quality 1</code>",
        S["text"]))

    flow.append(Spacer(1, 0.3 * cm))
    flow.append(Paragraph("DALL·E 3 hint", S["block_h"]))
    flow.append(Paragraph(
        "Prefix prompts with: <i>‘A clean editorial vector infographic in the style of New York Times explainer graphics, …’</i>",
        S["text"]))

    flow.append(Spacer(1, 0.3 * cm))
    flow.append(Paragraph("Things to avoid", S["block_h"]))
    flow += [
        Paragraph("&bull;&nbsp;&nbsp;Close-up human faces with eyes — image AI gets these uncanny. Use silhouettes or 3/4 angles.", S["bullet"]),
        Paragraph("&bull;&nbsp;&nbsp;Real government logos (CPGRAMS, MyGov, etc.) — legal risk; use generic 'portal' icons.", S["bullet"]),
        Paragraph("&bull;&nbsp;&nbsp;Real Devanagari text inside generated images — most AIs garble it. Overlay Hindi text in PowerPoint instead.", S["bullet"]),
        Paragraph("&bull;&nbsp;&nbsp;Complex diagrams with arrows and labels — image AI fails at these. Use draw.io / Mermaid / Excalidraw instead.", S["bullet"]),
    ]

    flow.append(Spacer(1, 0.4 * cm))
    flow.append(Paragraph("Build order recommendation", S["block_h"]))
    flow += [
        Paragraph("&bull;&nbsp;&nbsp;<b>Step 1</b> — set up master slide template (Appendix B) in PowerPoint.", S["bullet"]),
        Paragraph("&bull;&nbsp;&nbsp;<b>Step 2</b> — paste all slide text first (every slide gets text, no images yet).", S["bullet"]),
        Paragraph("&bull;&nbsp;&nbsp;<b>Step 3</b> — generate all images in batch (sit with this PDF and run the prompts).", S["bullet"]),
        Paragraph("&bull;&nbsp;&nbsp;<b>Step 4</b> — drop images into slides; adjust per Layout Note.", S["bullet"]),
        Paragraph("&bull;&nbsp;&nbsp;<b>Step 5</b> — replace Slide 12 dashboard mockup with REAL screenshots from your running app.", S["bullet"]),
        Paragraph("&bull;&nbsp;&nbsp;<b>Step 6</b> — replace Slide 17 placeholder photos with actual team headshots.", S["bullet"]),
        Paragraph("&bull;&nbsp;&nbsp;<b>Step 7</b> — record a 30-second mp4 of the live citizen flow and embed in Slide 5 as backup.", S["bullet"]),
        Paragraph("&bull;&nbsp;&nbsp;<b>Step 8</b> — full rehearsal × 3, time each slide.", S["bullet"]),
    ]

    doc.build(flow)
    print(f"✓ Wrote {OUT_PATH}")


if __name__ == "__main__":
    build()
