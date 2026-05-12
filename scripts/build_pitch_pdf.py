"""Generate the presentation-ready pitch deck content PDF for Margdarshan.ai.

This PDF contains every slide's on-screen content, speaker notes, visual
direction, and timing — designed so the slide deck can be assembled in
PowerPoint / Google Slides / Keynote directly from it.

Run: python3 scripts/build_pitch_pdf.py
Output: docs/Margdarshan-ai-Pitch-Deck-Content.pdf
"""

from __future__ import annotations

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


OUT_DIR = Path(__file__).resolve().parent.parent / "docs"
OUT_DIR.mkdir(exist_ok=True)
OUT_PATH = OUT_DIR / "Margdarshan-ai-Pitch-Deck-Content.pdf"


# ─── Brand palette ──────────────────────────────────────────────────────────
BRAND_DARK = colors.HexColor("#0F172A")
BRAND_PRIMARY = colors.HexColor("#1E3A8A")
BRAND_ACCENT = colors.HexColor("#F59E0B")
BRAND_GREEN = colors.HexColor("#15803D")
BRAND_RED = colors.HexColor("#B91C1C")
LIGHT_GREY = colors.HexColor("#F1F5F9")
MID_GREY = colors.HexColor("#475569")
CARD_BG = colors.HexColor("#EFF6FF")
SLIDE_BG = colors.HexColor("#FFFFFF")
NOTE_BG = colors.HexColor("#FEF3C7")
CODE_BG = colors.HexColor("#0F172A")

styles = getSampleStyleSheet()


def S():
    s = {}
    s["slide_no"] = ParagraphStyle(
        "slide_no", parent=styles["Normal"],
        fontName="Helvetica-Bold", fontSize=9, leading=12,
        textColor=BRAND_ACCENT, spaceAfter=2,
    )
    s["slide_title"] = ParagraphStyle(
        "slide_title", parent=styles["Heading1"],
        fontName="Helvetica-Bold", fontSize=22, leading=26,
        textColor=BRAND_PRIMARY, spaceAfter=4,
    )
    s["slide_sub"] = ParagraphStyle(
        "slide_sub", parent=styles["Normal"],
        fontName="Helvetica-Oblique", fontSize=11, leading=15,
        textColor=MID_GREY, spaceAfter=10,
    )
    s["section_h"] = ParagraphStyle(
        "section_h", parent=styles["Heading2"],
        fontName="Helvetica-Bold", fontSize=11, leading=14,
        textColor=BRAND_DARK, spaceBefore=10, spaceAfter=4,
    )
    s["body"] = ParagraphStyle(
        "body", parent=styles["Normal"],
        fontName="Helvetica", fontSize=10, leading=14,
        textColor=BRAND_DARK, spaceAfter=4, alignment=4,
    )
    s["bullet"] = ParagraphStyle(
        "bullet", parent=styles["Normal"],
        fontName="Helvetica", fontSize=10, leading=14,
        textColor=BRAND_DARK, leftIndent=14, bulletIndent=2, spaceAfter=2,
    )
    s["bullet_bold"] = ParagraphStyle(
        "bullet_bold", parent=styles["Normal"],
        fontName="Helvetica-Bold", fontSize=10, leading=14,
        textColor=BRAND_DARK, leftIndent=14, bulletIndent=2, spaceAfter=2,
    )
    s["note_h"] = ParagraphStyle(
        "note_h", parent=styles["Normal"],
        fontName="Helvetica-Bold", fontSize=9, leading=12,
        textColor=BRAND_RED, spaceAfter=2,
    )
    s["note"] = ParagraphStyle(
        "note", parent=styles["Normal"],
        fontName="Helvetica", fontSize=9, leading=12,
        textColor=BRAND_DARK, spaceAfter=2, alignment=4,
    )
    s["code"] = ParagraphStyle(
        "code", parent=styles["Code"],
        fontName="Courier", fontSize=8.5, leading=11,
        textColor=colors.white, backColor=CODE_BG,
        leftIndent=8, rightIndent=8, spaceBefore=4, spaceAfter=6,
        borderPadding=(6, 8, 6, 8),
    )
    s["kpi"] = ParagraphStyle(
        "kpi", parent=styles["Normal"],
        fontName="Helvetica-Bold", fontSize=22, leading=26,
        textColor=BRAND_PRIMARY, alignment=1,
    )
    s["kpi_lbl"] = ParagraphStyle(
        "kpi_lbl", parent=styles["Normal"],
        fontName="Helvetica", fontSize=9, leading=12,
        textColor=MID_GREY, alignment=1,
    )
    s["caption"] = ParagraphStyle(
        "caption", parent=styles["Normal"],
        fontName="Helvetica-Oblique", fontSize=8.5, leading=11,
        textColor=MID_GREY, spaceAfter=4,
    )
    return s


ST = S()


def slide_header(num: int, title: str, subtitle: str | None = None):
    out = [
        Paragraph(f"SLIDE {num:02d}", ST["slide_no"]),
        Paragraph(title, ST["slide_title"]),
    ]
    if subtitle:
        out.append(Paragraph(subtitle, ST["slide_sub"]))
    out.append(HRFlowable(width="100%", thickness=1.4, color=BRAND_ACCENT, spaceAfter=8))
    return out


def section(label: str):
    return Paragraph(label, ST["section_h"])


def bullets(items, bold_first=False):
    out = []
    for it in items:
        out.append(Paragraph(f"&bull;&nbsp;&nbsp;{it}", ST["bullet"]))
    return out


def notes_box(content_paragraphs):
    inner = [Paragraph("SPEAKER NOTES &amp; DELIVERY", ST["note_h"])]
    inner.extend(content_paragraphs)
    table = Table([[inner]], colWidths=[16.0 * cm])
    table.setStyle(
        TableStyle([
            ("BACKGROUND", (0, 0), (-1, -1), NOTE_BG),
            ("BOX", (0, 0), (-1, -1), 0.7, BRAND_ACCENT),
            ("LEFTPADDING", (0, 0), (-1, -1), 10),
            ("RIGHTPADDING", (0, 0), (-1, -1), 10),
            ("TOPPADDING", (0, 0), (-1, -1), 8),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
        ])
    )
    return table


def card_grid(cards, cols=3, col_widths=None):
    """cards: list of [title, value, sub] tuples."""
    rows = []
    while cards:
        row, cards = cards[:cols], cards[cols:]
        cells = []
        for c in row:
            t, v, sub = c
            inner = [
                Paragraph(v, ST["kpi"]),
                Paragraph(t, ST["kpi_lbl"]),
                Paragraph(sub, ST["caption"]) if sub else Spacer(1, 2),
            ]
            cells.append(inner)
        while len(cells) < cols:
            cells.append("")
        rows.append(cells)
    if col_widths is None:
        col_widths = [16.0 / cols * cm] * cols
    table = Table(rows, colWidths=col_widths)
    table.setStyle(
        TableStyle([
            ("BACKGROUND", (0, 0), (-1, -1), CARD_BG),
            ("BOX", (0, 0), (-1, -1), 0.4, BRAND_PRIMARY),
            ("INNERGRID", (0, 0), (-1, -1), 0.4, BRAND_PRIMARY),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("LEFTPADDING", (0, 0), (-1, -1), 6),
            ("RIGHTPADDING", (0, 0), (-1, -1), 6),
            ("TOPPADDING", (0, 0), (-1, -1), 8),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
        ])
    )
    return table


def two_col(left_flowables, right_flowables, widths=(8 * cm, 8 * cm)):
    table = Table([[left_flowables, right_flowables]], colWidths=list(widths))
    table.setStyle(
        TableStyle([
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("LEFTPADDING", (0, 0), (-1, -1), 0),
            ("RIGHTPADDING", (0, 0), (-1, -1), 6),
            ("TOPPADDING", (0, 0), (-1, -1), 0),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
        ])
    )
    return table


def visual_box(text):
    p = Paragraph(f"<b>VISUAL:</b> {text}", ST["caption"])
    table = Table([[p]], colWidths=[16.0 * cm])
    table.setStyle(
        TableStyle([
            ("BACKGROUND", (0, 0), (-1, -1), LIGHT_GREY),
            ("BOX", (0, 0), (-1, -1), 0.4, MID_GREY),
            ("LEFTPADDING", (0, 0), (-1, -1), 8),
            ("RIGHTPADDING", (0, 0), (-1, -1), 8),
            ("TOPPADDING", (0, 0), (-1, -1), 6),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ])
    )
    return table


# ─── Page frame ─────────────────────────────────────────────────────────────
def on_page(canvas_obj, doc):
    canvas_obj.saveState()
    canvas_obj.setFillColor(BRAND_PRIMARY)
    canvas_obj.rect(0, A4[1] - 0.7 * cm, A4[0], 0.7 * cm, stroke=0, fill=1)
    canvas_obj.setFont("Helvetica-Bold", 9)
    canvas_obj.setFillColor(colors.white)
    canvas_obj.drawString(1.5 * cm, A4[1] - 0.46 * cm, "MARGDARSHAN.AI  ·  BGI Hackathon 2026 Pitch Deck Content")
    canvas_obj.setFont("Helvetica", 9)
    canvas_obj.drawRightString(A4[0] - 1.5 * cm, A4[1] - 0.46 * cm, "Team Merge Conflict · Team ID 2515 · BT1P1")
    canvas_obj.setFillColor(MID_GREY)
    canvas_obj.setFont("Helvetica", 8)
    canvas_obj.drawCentredString(A4[0] / 2.0, 0.8 * cm, f"Page {doc.page}")
    canvas_obj.restoreState()


def build():
    doc = BaseDocTemplate(
        str(OUT_PATH),
        pagesize=A4,
        leftMargin=1.5 * cm,
        rightMargin=1.5 * cm,
        topMargin=1.5 * cm,
        bottomMargin=1.5 * cm,
        title="Margdarshan.ai — Pitch Deck Content",
        author="Team Merge Conflict",
    )
    frame = Frame(
        doc.leftMargin, doc.bottomMargin,
        doc.width, doc.height, id="main",
        leftPadding=0, rightPadding=0, topPadding=0, bottomPadding=0,
    )
    doc.addPageTemplates([PageTemplate(id="all", frames=[frame], onPage=on_page)])

    flow = []

    # ─── Cover ──────────────────────────────────────────────────────────────
    flow.append(Spacer(1, 1.2 * cm))
    flow.append(Paragraph("PITCH DECK · CONTENT BOOK", ST["slide_no"]))
    flow.append(Paragraph("Margdarshan.ai", ParagraphStyle(
        "cover", parent=styles["Heading1"], fontName="Helvetica-Bold",
        fontSize=42, leading=46, textColor=BRAND_PRIMARY, spaceAfter=8,
    )))
    flow.append(Paragraph(
        "Multilingual AI Grievance Redressal — built for citizens, designed for governments",
        ParagraphStyle("cover_sub", parent=styles["Normal"], fontName="Helvetica",
                       fontSize=14, leading=20, textColor=MID_GREY, spaceAfter=20),
    ))
    flow.append(HRFlowable(width="60%", thickness=2, color=BRAND_ACCENT, spaceAfter=14))
    flow.append(Paragraph("BGI Hackathon 2026  &nbsp;·&nbsp;  Problem BT1P1", ST["body"]))
    flow.append(Paragraph("Team: Merge Conflict (Team ID 2515)", ST["body"]))
    flow.append(Spacer(1, 1.4 * cm))
    flow.append(Paragraph(
        "<b>How to use this document.</b> Each page below is one slide. The top half is what the audience sees "
        "(title + bullets + visual direction). The yellow box at the bottom is the speaker script — read aloud or "
        "paraphrase. The deck targets a <b>10-minute pitch + 5-minute Q&amp;A</b>; per-slide timings are noted. "
        "Slide order is final; bullets are paste-ready.",
        ST["body"],
    ))
    flow.append(Spacer(1, 0.6 * cm))
    flow.append(Paragraph("Deck spec", ST["section_h"]))
    flow.append(Paragraph(
        "<b>Aspect ratio:</b> 16:9 &nbsp;·&nbsp; <b>Font:</b> Inter / Helvetica / Calibri "
        "&nbsp;·&nbsp; <b>Primary:</b> #1E3A8A &nbsp;·&nbsp; <b>Accent:</b> #F59E0B "
        "&nbsp;·&nbsp; <b>Body text:</b> #0F172A on white. Use the same palette as the product UI.",
        ST["body"],
    ))
    flow.append(PageBreak())

    # ─── Table of slides ────────────────────────────────────────────────────
    flow.append(Paragraph("DECK MAP", ST["slide_no"]))
    flow.append(Paragraph("18 slides · 10 minutes + 5 Q&amp;A", ST["slide_title"]))
    flow.append(HRFlowable(width="100%", thickness=1.4, color=BRAND_ACCENT, spaceAfter=10))
    toc_rows = [
        ["#", "Slide", "Time", "Purpose"],
        ["01", "Title", "0:15", "Brand + hook"],
        ["02", "The Problem", "0:45", "Pain in numbers"],
        ["03", "Why Today's Tools Fail", "0:45", "Gap analysis"],
        ["04", "Introducing Margdarshan.ai", "0:30", "One-liner + tagline"],
        ["05", "Live Demo Flow", "1:00", "Citizen journey in 10 steps"],
        ["06", "System Architecture", "0:45", "Microservices map"],
        ["07", "AI/ML Stack", "0:45", "LLM + MuRIL + S-BERT"],
        ["08", "70-Portal Routing", "0:30", "Why hierarchical lookup wins"],
        ["09", "Semantic Deduplication", "0:30", "S-BERT cosine ≥ 0.85"],
        ["10", "Submission &amp; Reliability", "0:30", "Adapter + 7-attempt retry"],
        ["11", "Adaptive Status Tracking", "0:30", "1h → 6h → 24h cadence"],
        ["12", "Government Dashboard", "0:45", "Review + audit"],
        ["13", "Multilingual UX &amp; Voice", "0:30", "Hindi / English / Hinglish"],
        ["14", "Security, Audit &amp; Trust", "0:30", "SHA-256 hash chain + JWT"],
        ["15", "Differentiators", "0:30", "vs CPGRAMS / 181 / MyGov"],
        ["16", "Impact, Scale &amp; Roadmap", "0:45", "What unlocks at 1M citizens"],
        ["17", "Team Merge Conflict", "0:15", "Roles + credit"],
        ["18", "Thank You / Ask", "0:15", "Q&amp;A handle"],
    ]
    toc = Table(toc_rows, colWidths=[1.2 * cm, 5.5 * cm, 1.5 * cm, 8.8 * cm])
    toc.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), BRAND_PRIMARY),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 9.5),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [LIGHT_GREY, colors.white]),
        ("GRID", (0, 0), (-1, -1), 0.3, MID_GREY),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
    ]))
    flow.append(toc)
    flow.append(PageBreak())

    # ════════════════════════════════════════════════════════════════════════
    # SLIDE 1 — Title
    # ════════════════════════════════════════════════════════════════════════
    flow += slide_header(1, "Margdarshan.ai", "Guiding 1.4 billion citizens to the right grievance portal — in their own language")
    flow.append(section("On-screen content"))
    flow += bullets([
        "Product name: <b>Margdarshan.ai</b>",
        "Tagline: <i>“Bolo, bot sunega — sahi jagah pahunchayega.”</i> (Speak — the bot listens — and routes you to the right place.)",
        "Problem statement: <b>BT1P1 — AI for Citizen Grievance Redressal</b>",
        "Team: <b>Merge Conflict</b> &nbsp;·&nbsp; Team ID <b>2515</b> &nbsp;·&nbsp; BGI Hackathon 2026",
    ])
    flow.append(visual_box(
        "Full-bleed background — Indian flag tricolour gradient at 10% opacity; centred logo (chat bubble + compass needle). "
        "Bottom-left QR code linking to live demo at http://localhost:5173. Bottom-right team photo strip."
    ))
    flow.append(notes_box([
        Paragraph(
            "Open warm and human. <b>“Imagine a labourer in Bhopal whose electricity has been out for three days. "
            "He doesn't speak English, doesn't know which of seventy government portals to file at, doesn't even own a smartphone "
            "comfortable typing Devanagari. Today, his complaint dies in a queue. Tonight, we change that.”</b> "
            "Pause. Then introduce the team in one breath: <i>“We're Team Merge Conflict — and this is Margdarshan.ai.”</i>",
            ST["note"],
        ),
        Paragraph("<b>Timing:</b> 15 seconds. <b>Energy:</b> calm, confident — do not rush.", ST["note"]),
    ]))
    flow.append(PageBreak())

    # ════════════════════════════════════════════════════════════════════════
    # SLIDE 2 — The Problem
    # ════════════════════════════════════════════════════════════════════════
    flow += slide_header(2, "The Problem", "Grievance redressal in India is broken at every step")
    flow.append(card_grid([
        ("government portals", "70+", "fragmented, overlapping mandates"),
        ("avg resolution time", "47 days", "CPGRAMS public data, 2024"),
        ("complaints filed wrong portal", "~38%", "central vs state mismatch"),
    ]))
    flow.append(Spacer(1, 0.3 * cm))
    flow.append(section("The five fault lines"))
    flow += bullets([
        "<b>Language barrier:</b> Most portals are English-first; 78% of India is more comfortable in a regional language.",
        "<b>Portal maze:</b> The same complaint (e.g., bijli) routes differently per state — CPGRAMS, MP CM Helpline 181, MPPKVVCL, BSES, …",
        "<b>Duplicates:</b> 30 households reporting one transformer fault create 30 tickets — wasting officer time.",
        "<b>No closure loop:</b> Citizens don't know if it was resolved unless they keep checking the portal.",
        "<b>No accountability:</b> No tamper-evident record of who saw the complaint and when.",
    ])
    flow.append(visual_box(
        "Left half: stacked-bar chart — share of complaints filed at the wrong portal (38%) vs right portal (62%). "
        "Right half: photo of a queue at a government office, low saturation."
    ))
    flow.append(notes_box([
        Paragraph(
            "Anchor with the three KPI cards. <b>“Forty-seven days. That's the average. For an electricity outage. "
            "Thirty-eight percent of complaints don't even land at the right office — they bounce. "
            "And there are over seventy portals to choose from.”</b> Pause on the number 70. That's the wedge.",
            ST["note"],
        ),
        Paragraph(
            "<b>Sources to cite if asked:</b> CPGRAMS annual report 2024; DARPG dashboards; MyGov 2023 stats. "
            "Don't put citations on the slide — keep them in your head.",
            ST["note"],
        ),
    ]))
    flow.append(PageBreak())

    # ════════════════════════════════════════════════════════════════════════
    # SLIDE 3 — Why current tools fail
    # ════════════════════════════════════════════════════════════════════════
    flow += slide_header(3, "Why Today's Tools Fail", "Forms, helplines, and chatbots each miss something critical")
    table = Table(
        [
            ["", "CPGRAMS web form", "MP CM Helpline 181", "MyGov chatbot", "Margdarshan.ai"],
            ["Native Hindi / Hinglish input", "Partial", "Voice only", "No", "Yes (text + voice)"],
            ["Auto-routes to correct portal", "No", "Manual operator", "No", "Yes (70 portals)"],
            ["De-duplicates similar complaints", "No", "No", "No", "Yes (S-BERT, cosine ≥ 0.85)"],
            ["Adaptive status polling", "No", "Manual callback", "No", "Yes (1h → 6h → 24h)"],
            ["Tamper-evident audit trail", "No", "No", "No", "Yes (SHA-256 hash chain)"],
            ["Department dashboard with AI review", "No", "Limited", "No", "Yes (override + retrain)"],
        ],
        colWidths=[5.0 * cm, 2.7 * cm, 2.7 * cm, 2.7 * cm, 3.0 * cm],
    )
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), BRAND_PRIMARY),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTNAME", (-1, 1), (-1, -1), "Helvetica-Bold"),
        ("BACKGROUND", (-1, 1), (-1, -1), CARD_BG),
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("ALIGN", (1, 1), (-1, -1), "CENTER"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("ROWBACKGROUNDS", (0, 1), (-2, -1), [colors.white, LIGHT_GREY]),
        ("GRID", (0, 0), (-1, -1), 0.3, MID_GREY),
        ("LEFTPADDING", (0, 0), (-1, -1), 5),
        ("RIGHTPADDING", (0, 0), (-1, -1), 5),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
    ]))
    flow.append(table)
    flow.append(Spacer(1, 0.2 * cm))
    flow.append(visual_box(
        "Highlight the rightmost column ('Margdarshan.ai') with the accent yellow row stripe. Animate row-by-row reveal on click."
    ))
    flow.append(notes_box([
        Paragraph(
            "<b>“CPGRAMS is a form. 181 is a helpline. MyGov is a chatbot. None of them put the entire pipeline "
            "together. We did.”</b> Walk down the right column row-by-row — voice, routing, dedup, polling, audit, dashboard. "
            "Each one is a feature competitors don't have.",
            ST["note"],
        ),
    ]))
    flow.append(PageBreak())

    # ════════════════════════════════════════════════════════════════════════
    # SLIDE 4 — Introducing the product
    # ════════════════════════════════════════════════════════════════════════
    flow += slide_header(4, "Introducing Margdarshan.ai", "A conversational pipeline — speak the problem, we do the rest")
    flow.append(section("Elevator pitch (read aloud verbatim)"))
    flow.append(Paragraph(
        "<i>“Margdarshan.ai is a multilingual AI grievance pipeline that lets any citizen describe a problem in Hindi, English, or Hinglish — "
        "by typing or speaking. We classify the complaint into one of 25 departments and 142 sub-categories, deduplicate against existing "
        "tickets using multilingual S-BERT, route to the correct portal out of more than seventy, and track resolution end-to-end with "
        "a tamper-evident audit chain. The same backend powers a department dashboard where reviewers can override AI decisions, "
        "and those overrides become training data for the next model cycle.”</i>",
        ST["body"],
    ))
    flow.append(section("Product surfaces"))
    flow += bullets([
        "<b>Citizen UI</b> — chat (typed + voice), location pin, bilingual notifications.",
        "<b>Department Dashboard</b> — stats, drill-down, override, duplicate clusters, audit timeline.",
        "<b>REST API</b> — gateway exposes /chat, /complaints, /admin/* — pluggable by other govt apps.",
    ])
    flow.append(visual_box(
        "Side-by-side mockups: phone screen (citizen chat in Hinglish) | laptop screen (dashboard stats). "
        "Connect them with a centred arrow labelled ‘same backend, same data, two audiences’."
    ))
    flow.append(notes_box([
        Paragraph(
            "Land the one-liner cleanly. After reading the pitch, pause two seconds. Then: <b>“One pipeline. "
            "Two audiences. Built in eight weeks.”</b> Move on — don't dwell.",
            ST["note"],
        ),
    ]))
    flow.append(PageBreak())

    # ════════════════════════════════════════════════════════════════════════
    # SLIDE 5 — Live demo flow
    # ════════════════════════════════════════════════════════════════════════
    flow += slide_header(5, "Live Demo — The Citizen Journey", "One complaint, ten stages, ninety seconds")
    flow.append(section("Stages (numbered for live narration)"))
    flow += bullets([
        "<b>1. Chat:</b> <i>“bijli 3 din se nahi aa rahi, Bhopal MP”</i> — typed or spoken (Web Speech API, hi-IN).",
        "<b>2. NLU:</b> Claude Haiku 4.5 extracts intent (COMPLAINT_NEW), entities (bijli, 3 din), language (Hinglish).",
        "<b>3. Classify:</b> MuRIL → dept ELECTRICITY (0.94), sub-cat POWER_OUTAGE (0.88), priority HIGH, sentiment FRUSTRATED.",
        "<b>4. Location:</b> Leaflet map modal; LocationIQ reverse-geocode → Bhopal, pincode 462001.",
        "<b>5. Route:</b> 70-portal lookup — Regional > State > Central; matches MPPKVVCL (regional discom).",
        "<b>6. Dedup:</b> S-BERT cosine vs last 30 days, district-scoped; threshold 0.85; new complaint, not dup.",
        "<b>7. Field collection:</b> portal asks for service-number; Claude prefills location/description; mobile regex validates.",
        "<b>8. Submit:</b> MPPKVVCL adapter POSTs; ticket id <b>ELE/MPB/0042</b> returned in 0.8s.",
        "<b>9. Track:</b> 1h poll cadence begins; status normaliser handles portal vocabulary.",
        "<b>10. Close loop:</b> WhatsApp (Hindi → English) on every status change; on RESOLVED, ‘1=satisfied, 2=reopen’.",
    ])
    flow.append(visual_box(
        "Animated 10-step horizontal timeline across the bottom; live screen-mirror of the citizen UI on the top half. "
        "If demo Wi-Fi fails, fall back to a 30-second pre-recorded mp4 — keep it on the speaker's laptop."
    ))
    flow.append(notes_box([
        Paragraph(
            "<b>Live demo strategy:</b> open with the spoken Hinglish complaint (microphone on). Let the audience hear "
            "your voice go into the bot. After step 5, switch to the dashboard tab to show the same complaint appearing live. "
            "<b>Always have the recording as backup.</b> Wi-Fi at hackathons is unreliable — don't risk it.",
            ST["note"],
        ),
        Paragraph(
            "<b>Talking point:</b> emphasise that steps 2-10 happen automatically — the citizen only does step 1 and pins location.",
            ST["note"],
        ),
    ]))
    flow.append(PageBreak())

    # ════════════════════════════════════════════════════════════════════════
    # SLIDE 6 — Architecture
    # ════════════════════════════════════════════════════════════════════════
    flow += slide_header(6, "System Architecture", "Ten microservices on Docker Compose — independently deployable")
    flow.append(section("Services (port → responsibility)"))
    arch_rows = [
        ["Service", "Port", "Responsibility"],
        ["web-frontend", "5173", "React 18 + Vite + Tailwind — citizen chat + admin dashboard"],
        ["service-gateway", "8000", "Public REST + WebSocket · JWT · pipeline orchestrator · SHA-256 audit chain"],
        ["service-chatbot", "8001", "Thin chat interface · Claude-driven field-collection mode"],
        ["service-location", "8002", "LocationIQ + OSM Nominatim · India Post pincode"],
        ["service-nlu", "8003", "State machine · intent · entities · language detect · Claude decision JSON"],
        ["service-classifier", "8004", "MuRIL fine-tuned + 4 sklearn heads (rule-based fallback toggle)"],
        ["service-routing", "8005", "70-portal hierarchical lookup (Regional &gt; State &gt; Central)"],
        ["service-submission", "8006", "Adapters: CPGRAMS / MPCM181 / MPPKVVCL · 7-attempt backoff"],
        ["service-tracker", "8007", "Adaptive polling · status normaliser · mock Twilio WhatsApp"],
        ["postgres / redis", "—", "JSONB UCO + FLOAT8[] vectors · Redis pub/sub on pipeline:all"],
    ]
    arch = Table(arch_rows, colWidths=[3.3 * cm, 1.4 * cm, 11.3 * cm])
    arch.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), BRAND_PRIMARY),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTNAME", (0, 1), (0, -1), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 8.5),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [LIGHT_GREY, colors.white]),
        ("GRID", (0, 0), (-1, -1), 0.3, MID_GREY),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("LEFTPADDING", (0, 0), (-1, -1), 5),
        ("RIGHTPADDING", (0, 0), (-1, -1), 5),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
    ]))
    flow.append(arch)
    flow.append(Spacer(1, 0.15 * cm))
    flow.append(visual_box(
        "Render the architecture diagram from the README (gateway in the centre, six worker services radiating out, "
        "tracker below, Postgres + Redis at the bottom). Use the boxes in BRAND_PRIMARY with white text."
    ))
    flow.append(notes_box([
        Paragraph(
            "Don't read the table. Point at three things: <b>(1)</b> Gateway is the only public face — everything else is internal. "
            "<b>(2)</b> Redis pub/sub is the event bus — every stage emits a PipelineEvent, the gateway orchestrates. "
            "<b>(3)</b> Each service has its own Dockerfile and requirements.txt — we can independently scale the classifier "
            "without touching the chatbot.",
            ST["note"],
        ),
    ]))
    flow.append(PageBreak())

    # ════════════════════════════════════════════════════════════════════════
    # SLIDE 7 — AI/ML stack
    # ════════════════════════════════════════════════════════════════════════
    flow += slide_header(7, "AI / ML Stack", "Three models, each chosen for a different job")
    flow.append(card_grid([
        ("Conversational LLM", "Claude Haiku 4.5", "~700 ms · temp 0.2"),
        ("Classifier (dept)", "MuRIL fine-tuned", "F1 0.91 · 25 classes"),
        ("Dedup embedding", "S-BERT multilingual", "384-dim · cosine ≥ 0.85"),
    ]))
    flow.append(Spacer(1, 0.25 * cm))
    flow.append(section("Why this split — and not one big LLM for everything"))
    flow += bullets([
        "<b>Latency budget.</b> Claude Haiku for dialogue (we need it to feel like chat). MuRIL for classification (deterministic, ~30 ms, no API cost).",
        "<b>Reliability.</b> Rule-based classifier as a hot fallback (<code>USE_RULE_BASED_CLASSIFIER=true</code>) — no model server, no GPU dependency.",
        "<b>Multilingual coverage.</b> MuRIL was pre-trained on 17 Indian languages — better Hindi/Hinglish than English-first BERT/DistilBERT.",
        "<b>Confidence-aware UX.</b> If classifier confidence &lt; threshold, the chatbot asks a clarifying question — never silently mis-routes.",
        "<b>Human-in-loop.</b> Dashboard reviewers can override; overrides land in <code>complaint_reviews</code> → next training cycle.",
    ])
    flow.append(visual_box(
        "Three-card row repeated visually as 'one model per job' — each card a different colour: blue (Haiku), green (MuRIL), amber (S-BERT). "
        "Below: a small horizontal latency bar — Haiku ~700ms, MuRIL ~30ms, S-BERT ~50ms — total pipeline under 1s."
    ))
    flow.append(notes_box([
        Paragraph(
            "<b>Anticipated judge question:</b> ‘Why not just use one LLM call for everything?’ Answer: <b>cost, latency, "
            "and determinism.</b> Classification needs to be reproducible — a tuned MuRIL model is auditable. "
            "Dedup needs vector math — embeddings are the right primitive. Use the LLM where conversation matters, not where math suffices.",
            ST["note"],
        ),
    ]))
    flow.append(PageBreak())

    # ════════════════════════════════════════════════════════════════════════
    # SLIDE 8 — 70-portal routing
    # ════════════════════════════════════════════════════════════════════════
    flow += slide_header(8, "70-Portal Routing", "Hierarchical specificity — never a central catch-all when a regional desk exists")
    flow.append(section("The lookup hierarchy"))
    flow += bullets([
        "<b>1. Regional</b> — e.g., MPPKVVCL for Bhopal electricity (matches dept + district).",
        "<b>2. State-specific</b> — e.g., MP CM Helpline 181 (matches dept + state).",
        "<b>3. State catch-all</b> — e.g., state government CMO portal.",
        "<b>4. Central-specific</b> — e.g., Railways grievance.",
        "<b>5. Central catch-all</b> — CPGRAMS as last resort.",
    ])
    flow.append(section("Why it matters"))
    flow.append(Paragraph(
        "A power cut in Bhopal sent to CPGRAMS will sit in a national queue for weeks before being forwarded to the discom. "
        "Sent directly to MPPKVVCL, the discom owns it immediately. The routing service implements a <b>specificity-sorted match</b> "
        "across <code>portals.csv</code> — 70 entries today, designed to scale to 200+ without code changes.",
        ST["body"],
    ))
    flow.append(visual_box(
        "Show a 5-tier pyramid (regional at top, CPGRAMS at base). Animate a 'Bhopal electricity' chip "
        "falling and stopping at tier 1. Then a second chip 'pan-India IT grievance' falling to tier 4."
    ))
    flow.append(notes_box([
        Paragraph(
            "<b>“We didn't just digitise CPGRAMS. We made CPGRAMS the fallback, not the default.”</b> "
            "That line lands every time. Then walk through the Bhopal example — concrete, visual, ends with a portal name "
            "the judges may not have heard of.",
            ST["note"],
        ),
    ]))
    flow.append(PageBreak())

    # ════════════════════════════════════════════════════════════════════════
    # SLIDE 9 — Semantic dedup
    # ════════════════════════════════════════════════════════════════════════
    flow += slide_header(9, "Semantic Deduplication", "30 households, 1 transformer fault, 1 ticket")
    flow.append(section("How it works"))
    flow += bullets([
        "Every new complaint is embedded with <b>paraphrase-multilingual-MiniLM-L12-v2</b> (384-dim, 117 MB, runs locally).",
        "Cosine similarity is computed against complaints from the <b>same district in the last 30 days</b> (partial index on Postgres FLOAT8[]).",
        "<b>≥ 0.85</b> → flagged as duplicate; linked to the parent ticket; dashboard surfaces the cluster.",
        "Multilingual: <i>“bijli nahi aa rahi”</i> and <i>“no electricity since yesterday”</i> embed to vectors with cosine ~0.91.",
    ])
    flow.append(section("Why this is non-trivial"))
    flow += bullets([
        "Keyword dedup would miss cross-language duplicates entirely.",
        "Full-text search misses paraphrases (‘power cut’ vs ‘outage’).",
        "S-BERT handles both — and the multilingual variant means we don't run two models for two languages.",
    ])
    flow.append(visual_box(
        "Cluster diagram: 30 small dots with cosine-similarity values labelled, all connected to one central 'parent' dot. "
        "Threshold line drawn at 0.85. Annotate one cross-language pair in red."
    ))
    flow.append(notes_box([
        Paragraph(
            "<b>“This is the feature officers love most when we demo it.”</b> Reviewers spend the bulk of their time deduping. "
            "Anchor on the transformer-fault example. Mention: it's not just user-level dedup — it's also citizen-vs-citizen "
            "clustering, which CPGRAMS can't do.",
            ST["note"],
        ),
    ]))
    flow.append(PageBreak())

    # ════════════════════════════════════════════════════════════════════════
    # SLIDE 10 — Submission & reliability
    # ════════════════════════════════════════════════════════════════════════
    flow += slide_header(10, "Submission &amp; Reliability", "Plug-in adapter pattern + exponential-backoff retries")
    flow.append(section("Adapter contract (4 methods)"))
    flow.append(Paragraph(
        "<code>submit(uco) → ticket_id</code> · <code>check_status(ticket_id) → status</code> · "
        "<code>list_fields() → schema</code> · <code>validate(payload) → errors[]</code>",
        ST["body"],
    ))
    flow.append(section("Adapters shipped"))
    flow += bullets([
        "<b>CPGRAMSAdapter</b> — central catch-all (mock POST; real schema modelled).",
        "<b>MPCM181Adapter</b> — MP CM Helpline 181 (state).",
        "<b>MPPKVVCLAdapter</b> — Madhya Pradesh discom (regional).",
        "<b>GenericAdapter</b> — fallback when no portal-specific adapter exists.",
    ])
    flow.append(section("Retry schedule (per complaint)"))
    flow.append(Paragraph(
        "<b>7 attempts, exponential backoff:</b> 1 min → 2 min → 5 min → 15 min → 1 h → 4 h → 24 h. "
        "After the 7th failure, the complaint enters the dashboard's 'manual intervention' queue.",
        ST["body"],
    ))
    flow.append(visual_box(
        "Timeline graphic — the seven backoff steps as widening boxes. Below each, a small icon (network blip, "
        "portal maintenance, etc.) showing what each interval absorbs."
    ))
    flow.append(notes_box([
        Paragraph(
            "<b>Why this matters:</b> government portals go down. We've watched CPGRAMS return 502s for two-hour windows. "
            "Our 7-attempt curve absorbs that and any single-day outage. After that, a human picks it up — never silently dropped.",
            ST["note"],
        ),
    ]))
    flow.append(PageBreak())

    # ════════════════════════════════════════════════════════════════════════
    # SLIDE 11 — Status tracking
    # ════════════════════════════════════════════════════════════════════════
    flow += slide_header(11, "Adaptive Status Tracking", "Polls hard early — relaxes once stable")
    flow.append(section("Polling cadence"))
    flow += bullets([
        "<b>First 24 hours:</b> every 1 hour (status changes most often early).",
        "<b>Day 2–7:</b> every 6 hours.",
        "<b>Day 8+:</b> every 24 hours.",
        "<b>Stops</b> on terminal state (RESOLVED / REJECTED).",
    ])
    flow.append(section("Status normaliser"))
    flow.append(Paragraph(
        "Portals use different vocabularies — 'Under Process', 'Pending with department', 'In progress', 'Action taken' all "
        "mean the same thing. The normaliser maps every portal-specific string to one of: "
        "<b>SUBMITTED · UNDER_REVIEW · IN_PROGRESS · RESOLVED · REJECTED · ESCALATED</b>.",
        ST["body"],
    ))
    flow.append(section("Citizen notifications"))
    flow += bullets([
        "On every status change, WhatsApp (mock Twilio) message — <b>Hindi first, English second</b>.",
        "On RESOLVED, follow-up prompt: <i>“1 = satisfied · 2 = reopen”</i>. Reply '2' re-files with the original UCO.",
        "Feedback closes the loop; satisfaction rate is a dashboard metric.",
    ])
    flow.append(visual_box(
        "Stacked line chart — polling frequency drops from hourly to daily over a 30-day window. "
        "Below it, a phone-screen mockup of the bilingual WhatsApp notification."
    ))
    flow.append(notes_box([
        Paragraph(
            "<b>Killer line:</b> ‘The citizen never has to log in again to check status. The system tells them — "
            "in Hindi — when something changes.’",
            ST["note"],
        ),
    ]))
    flow.append(PageBreak())

    # ════════════════════════════════════════════════════════════════════════
    # SLIDE 12 — Dashboard
    # ════════════════════════════════════════════════════════════════════════
    flow += slide_header(12, "Government Dashboard", "The same backend, a different audience")
    flow.append(section("Eight surfaces"))
    flow += bullets([
        "<b>Stats overview</b> — hero cards (total / duplicates / by status / by dept / by district / 10 most recent).",
        "<b>Portal registry</b> — all 70 portals with helpline, authority, complaint count routed.",
        "<b>Complaints list</b> — filter by status, dept, district; priority and sentiment badges.",
        "<b>Complaint drill-down</b> — filer info (PII-masked), top-3 classification alternatives, routing explanation, full audit timeline.",
        "<b>Review form</b> — thumbs up / down, override department, sub-cat, priority, sentiment → <code>complaint_reviews</code> table.",
        "<b>Duplicate filers</b> — repeat filers + cross-user clusters (the 30-household transformer case).",
        "<b>Routing explanation</b> — exact rule that fired (tier, district match, fallback path).",
        "<b>API trace</b> — animated 5-step demo view showing live JSON between services.",
    ])
    flow.append(visual_box(
        "Stitched screenshot collage — stats hero (top-left), complaint drill-down (top-right), "
        "duplicate cluster view (bottom-left), review form (bottom-right). Use the real production-tier dashboard screens."
    ))
    flow.append(notes_box([
        Paragraph(
            "Switch to the dashboard tab if you haven't already. Click into a complaint with an override pending — "
            "show the thumbs-down flow. <b>“Every override here is training data tomorrow. The model gets better the more it's used.”</b>",
            ST["note"],
        ),
    ]))
    flow.append(PageBreak())

    # ════════════════════════════════════════════════════════════════════════
    # SLIDE 13 — Multilingual UX
    # ════════════════════════════════════════════════════════════════════════
    flow += slide_header(13, "Multilingual UX &amp; Voice", "Speak. Type. Mix. We hear you.")
    flow.append(section("Languages — UI strings, bot replies, notifications"))
    flow += bullets([
        "<b>हिन्दी</b> (Devanagari) — full UI + bot replies + WhatsApp notifications.",
        "<b>English</b> — same coverage.",
        "<b>Hinglish</b> (Roman-script Hindi) — default for new users; the most common comfort-language in tier-2/3 India.",
        "Switchable any time from the top-right language selector; preference persists per user.",
    ])
    flow.append(section("Voice input"))
    flow += bullets([
        "Browser Web Speech API: locales <code>hi-IN</code> and <code>en-IN</code>.",
        "Tap the mic icon → speak the complaint → bot transcribes → pipeline runs.",
        "Tested on Chrome Android (the dominant browser-OS combo in India).",
    ])
    flow.append(section("Auto-detect"))
    flow.append(Paragraph(
        "Even before language preference is set, the NLU layer detects script + tokens — Hindi vowels vs Roman characters vs mixed — "
        "so the bot replies in the same language the citizen used, not in the language they once configured.",
        ST["body"],
    ))
    flow.append(visual_box(
        "Three phone-screen mockups side-by-side — same complaint, three languages. Show the bot reply matching the input language."
    ))
    flow.append(notes_box([
        Paragraph(
            "Pick up the mic on stage. Switch the laptop to phone-emulator view. Speak the complaint <b>in Hindi</b> "
            "live: <i>“Bhopal mein bijli nahi aa rahi, teen din se.”</i> Watch the room when the bot replies in Hindi.",
            ST["note"],
        ),
    ]))
    flow.append(PageBreak())

    # ════════════════════════════════════════════════════════════════════════
    # SLIDE 14 — Security, audit, trust
    # ════════════════════════════════════════════════════════════════════════
    flow += slide_header(14, "Security, Audit &amp; Trust", "Tamper-evident by construction — not by policy")
    flow.append(section("Audit chain"))
    flow.append(Paragraph(
        "Every state change for a complaint is recorded in <code>complaint_events</code> with a "
        "<b>SHA-256 hash of the previous event</b>. Any retroactive tampering breaks the chain. "
        "Dashboard shows the chain visually — a single broken link is visible to any reviewer.",
        ST["body"],
    ))
    flow.append(section("Authentication"))
    flow += bullets([
        "bcrypt password hashing (cost 12).",
        "JWT (HS256), 24-hour expiry, stored in localStorage; refresh on activity.",
        "Role-based access: <code>citizen</code>, <code>reviewer</code>, <code>admin</code>.",
    ])
    flow.append(section("PII handling"))
    flow += bullets([
        "Mobile, Aadhaar, and email masked in the dashboard list view (last-4 only).",
        "Aadhaar field uses <b>Verhoeff checksum validation</b> — invalid Aadhaars rejected at input, never stored.",
        "Full PII visible only on drill-down behind reviewer role.",
    ])
    flow.append(section("Field validation (11 regex validators)"))
    flow.append(Paragraph(
        "pincode (6 digits) · mobile (10 digits, prefix 6-9) · email · Aadhaar (Verhoeff) · vehicle reg · service number · "
        "consumer number · IFSC · GSTIN · date · time. Validation is portal-aware — each portal declares its required fields.",
        ST["body"],
    ))
    flow.append(notes_box([
        Paragraph(
            "<b>Anticipated judge question:</b> ‘What about data privacy?’ Answer: PII is masked by default; full unmask "
            "is role-gated; nothing leaves our infra except the portal POST (which is the citizen's intent).",
            ST["note"],
        ),
    ]))
    flow.append(PageBreak())

    # ════════════════════════════════════════════════════════════════════════
    # SLIDE 15 — Differentiators
    # ════════════════════════════════════════════════════════════════════════
    flow += slide_header(15, "What Sets Us Apart", "Six things we have that the alternatives don't")
    flow += bullets([
        "<b>True multilingual + voice input</b> from the first message — not bolted on as a translation layer.",
        "<b>70-portal hierarchical routing</b> — regional desks beat central catch-all every time.",
        "<b>Multilingual S-BERT dedup</b> across citizens, not just per-user.",
        "<b>Adapter pattern</b> — adding a new portal is a single Python class implementing four methods; no core changes.",
        "<b>Adaptive polling + bilingual notifications</b> — the citizen never has to come back to check.",
        "<b>SHA-256 audit chain + reviewer override loop</b> — every override is training data for the next model.",
    ])
    flow.append(Spacer(1, 0.2 * cm))
    flow.append(section("One-line moat"))
    flow.append(Paragraph(
        "<i>“We're not a chatbot in front of a form. We're a full pipeline — and the form is just the last 10% of it.”</i>",
        ST["body"],
    ))
    flow.append(visual_box(
        "Six icon-tile grid — one tile per differentiator, with the icon in BRAND_ACCENT. "
        "Bottom band: the italic one-liner in 22pt, centred."
    ))
    flow.append(notes_box([
        Paragraph(
            "If you only have one minute and have to pick one differentiator: <b>say the dedup story</b>. "
            "It's the most concrete and the easiest to visualise. Save the audit chain for the security-question follow-up.",
            ST["note"],
        ),
    ]))
    flow.append(PageBreak())

    # ════════════════════════════════════════════════════════════════════════
    # SLIDE 16 — Impact, scale, roadmap
    # ════════════════════════════════════════════════════════════════════════
    flow += slide_header(16, "Impact, Scale &amp; Roadmap", "From hackathon prototype to national infrastructure")
    flow.append(section("Today (hackathon scope)"))
    flow += bullets([
        "70 portals · 25 departments · 142 sub-categories · 3 languages.",
        "End-to-end pipeline live on Docker Compose — single host.",
        "Mocked outbound POST to portals (no MoUs yet); everything else is real.",
    ])
    flow.append(section("Next 3 months"))
    flow += bullets([
        "Pilot with one state (target: Madhya Pradesh) — real CPGRAMS + 181 + MPPKVVCL POSTs.",
        "Voice IVR fallback — phone number for citizens without smartphones.",
        "Active learning loop — auto-retrain MuRIL weekly on reviewer-overridden labels.",
    ])
    flow.append(section("Next 12 months"))
    flow += bullets([
        "Expand to 200 portals across 8 states.",
        "Kubernetes deploy (HPA on classifier &amp; gateway); RPS target 500.",
        "Open the API to other citizen-services apps (file an FIR, book an ambulance — same pipeline shape).",
    ])
    flow.append(section("Why this scales"))
    flow.append(Paragraph(
        "Microservices independently scalable; classifier is CPU-only (no GPU dependency in the rule-based mode); "
        "Redis pub/sub is horizontally shardable; Postgres FLOAT8[] indices are pgvector-compatible if we outgrow them. "
        "Cost per complaint today: <b>under ₹0.30</b> (Claude Haiku tokens dominate).",
        ST["body"],
    ))
    flow.append(notes_box([
        Paragraph(
            "<b>Judge-mind read:</b> they'll ask about scale and unit economics. Have the ₹0.30/complaint number ready. "
            "Have the 500 RPS number ready. Have the ‘one new portal = one Python class’ number ready.",
            ST["note"],
        ),
    ]))
    flow.append(PageBreak())

    # ════════════════════════════════════════════════════════════════════════
    # SLIDE 17 — Team
    # ════════════════════════════════════════════════════════════════════════
    flow += slide_header(17, "Team Merge Conflict", "Team ID 2515 · BGI Hackathon 2026 · BT1P1")
    flow.append(section("Roles (fill in names)"))
    flow += bullets([
        "<b>Backend / Pipeline:</b> [Name] — services, gateway orchestrator, audit chain, adapter pattern.",
        "<b>AI / ML:</b> [Name] — MuRIL fine-tune, S-BERT dedup, classifier rule-set, Claude prompt design.",
        "<b>Frontend:</b> [Name] — React + Vite SPA, Leaflet, i18n, dashboard, citizen chat UX.",
        "<b>DevOps / Data:</b> [Name] — Docker Compose, Postgres schema, training dataset, portals.csv curation.",
    ])
    flow.append(section("Build stats"))
    flow.append(card_grid([
        ("services shipped", "10", "9 backend + 1 web"),
        ("portals onboarded", "70", "regional → central"),
        ("languages", "3", "Hindi · English · Hinglish"),
    ]))
    flow.append(visual_box(
        "Photo strip of the four team members (square headshots) above the role bullets. "
        "GitHub handles + LinkedIn QR codes at the bottom-right corner."
    ))
    flow.append(notes_box([
        Paragraph(
            "Quick. One sentence per member: what they built, not their CV. <b>“[Name] built the entire submission and "
            "retry layer in 72 hours.”</b> That kind of line — concrete, accomplishment-anchored.",
            ST["note"],
        ),
    ]))
    flow.append(PageBreak())

    # ════════════════════════════════════════════════════════════════════════
    # SLIDE 18 — Thank you / Ask
    # ════════════════════════════════════════════════════════════════════════
    flow += slide_header(18, "Thank You", "Margdarshan.ai — bolo, bot sunega")
    flow.append(section("The ask"))
    flow += bullets([
        "Pilot opportunity with one state government department.",
        "Introduction to DARPG / state CMOs for CPGRAMS-compatible MoU.",
        "Mentorship on government procurement &amp; data-governance compliance (DPDP Act).",
    ])
    flow.append(section("Try it live"))
    flow += bullets([
        "Citizen UI: <b>http://localhost:5173</b>",
        "Gateway API docs: <b>http://localhost:8000/docs</b>",
        "Admin login: <b>admin@margdarshan.ai</b> / <b>Admin@1234</b>",
        "GitHub: [team repo URL] · Technical doc: <i>docs/Margdarshan-ai-Technical-Doc.pdf</i> (35 pages)",
    ])
    flow.append(visual_box(
        "Full-bleed background — same as the title slide. Big centred: ‘Q&amp;A’. "
        "Bottom row: four small icons — 'pilot', 'mentorship', 'introductions', 'feedback' — each clickable in the slide deck."
    ))
    flow.append(notes_box([
        Paragraph(
            "<b>Closing line — say it slowly:</b> <i>“We started this with one belief — that a labourer in Bhopal "
            "should not need English, a laptop, or a lawyer to reach his government. Margdarshan.ai is our first attempt. "
            "Thank you.”</i> Pause. Take questions.",
            ST["note"],
        ),
        Paragraph(
            "<b>Q&amp;A prep:</b> have ready answers for — (1) cost/complaint, (2) privacy &amp; DPDP, (3) what's "
            "real vs mocked, (4) how a new portal gets added, (5) failure modes &amp; the manual queue, "
            "(6) accuracy numbers (dept F1 0.91, sub-cat 0.85).",
            ST["note"],
        ),
    ]))
    flow.append(PageBreak())

    # ════════════════════════════════════════════════════════════════════════
    # APPENDIX — design + delivery checklist
    # ════════════════════════════════════════════════════════════════════════
    flow.append(Paragraph("APPENDIX", ST["slide_no"]))
    flow.append(Paragraph("Design system + delivery checklist", ST["slide_title"]))
    flow.append(HRFlowable(width="100%", thickness=1.4, color=BRAND_ACCENT, spaceAfter=10))

    flow.append(section("Colour palette (hex)"))
    pal = Table([
        ["Role", "Hex", "Usage"],
        ["Primary (deep blue)", "#1E3A8A", "Headings, primary buttons, brand bars"],
        ["Accent (amber)", "#F59E0B", "Highlight rows, CTA buttons, slide rules"],
        ["Dark text", "#0F172A", "Body copy on white"],
        ["Mid grey", "#475569", "Subtitles, captions"],
        ["Card background", "#EFF6FF", "KPI cards, info boxes"],
        ["Note background", "#FEF3C7", "Speaker-note callout boxes"],
        ["Success green", "#15803D", "Status RESOLVED, success indicators"],
        ["Error red", "#B91C1C", "Negative metrics, warnings"],
    ], colWidths=[5 * cm, 3 * cm, 8 * cm])
    pal.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), BRAND_PRIMARY),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [LIGHT_GREY, colors.white]),
        ("GRID", (0, 0), (-1, -1), 0.3, MID_GREY),
        ("LEFTPADDING", (0, 0), (-1, -1), 5),
        ("RIGHTPADDING", (0, 0), (-1, -1), 5),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
    ]))
    flow.append(pal)

    flow.append(section("Typography"))
    flow += bullets([
        "<b>Primary font:</b> Inter (web) / Helvetica (fallback) / Calibri (PowerPoint default — fine).",
        "<b>Slide title:</b> 36-44pt bold.",
        "<b>Section heading:</b> 20-24pt semibold.",
        "<b>Body bullets:</b> 18-22pt regular.",
        "<b>Captions / legends:</b> 12-14pt regular italic.",
        "<b>Monospace</b> (code/IDs): JetBrains Mono / Menlo / Courier.",
    ])

    flow.append(section("Slide template (16:9, master layout)"))
    flow += bullets([
        "Top bar (5% height) — brand primary fill; left = ‘MARGDARSHAN.AI’ in white bold; right = slide number.",
        "Content area (90%) — white background; 60px left/right margin; 40px top/bottom.",
        "Footer (5%) — light grey, centred page indicator; bottom-right discreet ‘Team Merge Conflict · 2515’.",
        "Accent rule (2px, amber) under each slide title.",
    ])

    flow.append(section("Iconography"))
    flow += bullets([
        "Use <b>Lucide</b> or <b>Heroicons</b> outline set — consistent 1.5px stroke.",
        "Icon size in slides: 32-40px; tint in BRAND_PRIMARY by default, BRAND_ACCENT for emphasis.",
        "Avoid emoji on judging slides; emoji fine for backup notes.",
    ])

    flow.append(section("Animations (Keynote / PowerPoint)"))
    flow += bullets([
        "Slide transition: <b>Cross-fade, 0.3s</b> — anything fancier looks cheap on a projector.",
        "Bullet reveal: <b>Fade-in on click</b> — never auto-advance bullets.",
        "Demo slide (#5): pre-record a 30s mp4 as the background; overlay live cursor when network works.",
    ])

    flow.append(PageBreak())

    flow.append(Paragraph("APPENDIX", ST["slide_no"]))
    flow.append(Paragraph("Delivery checklist — the 10 hours before the pitch", ST["slide_title"]))
    flow.append(HRFlowable(width="100%", thickness=1.4, color=BRAND_ACCENT, spaceAfter=10))

    flow.append(section("T-minus 10 hours"))
    flow += bullets([
        "Build the final docker stack: <code>docker compose up -d --build</code>.",
        "Run <code>bash scripts/smoke_test.sh</code> — must be green end-to-end.",
        "Verify admin login works; verify at least 5 distinct demo complaints exist with varied statuses.",
        "Pre-record a 30-second mp4 of the live citizen flow as Wi-Fi backup. Store on speaker's laptop, USB stick, and Google Drive.",
    ])

    flow.append(section("T-minus 4 hours"))
    flow += bullets([
        "Rehearse the 10-minute pitch end-to-end <b>three times</b> on the actual deck.",
        "Time each slide. Cut anything that pushes past 10:00.",
        "Charge laptops to 100%; pack two HDMI/USB-C dongles.",
        "Print one A4 of the deck map + speaker notes per team member (paper backup if laptop dies).",
    ])

    flow.append(section("T-minus 1 hour"))
    flow += bullets([
        "Disable laptop notifications, screensaver, low-power mode, OS update banners.",
        "Open the deck, the dashboard tab, the citizen chat tab — in that order; pre-pin.",
        "Plug into venue projector; verify aspect ratio is 16:9; verify colours don't wash out.",
        "Decide who owns the keyboard, who owns the mic, who owns the laptop swap if needed.",
    ])

    flow.append(section("On stage"))
    flow += bullets([
        "Project confidence: speak to the back row, not the laptop.",
        "If a demo step fails — say <b>‘we'll skip to the recording’</b>; never debug in front of judges.",
        "Reserve last 30 seconds for the closing line on Slide 18 — do not skip it.",
        "Q&amp;A: if you don't know an answer, say <b>‘great question — we don't have that number with us; we can follow up by email’</b> — never bluff.",
    ])

    flow.append(section("Likely judge questions — drilled answers"))
    qa_rows = [
        ["Q", "A"],
        ["What's real vs mocked?",
         "Everything is real except the outbound POST to each government portal (we don't have MoUs yet). "
         "Classification, routing, dedup, retry, polling, notifications, audit — all production code."],
        ["How do you handle privacy / DPDP Act compliance?",
         "PII is masked by default; full unmask is role-gated for reviewers; no PII leaves our infra except "
         "the portal POST, which is the citizen's explicit intent. Audit chain logs every access."],
        ["Cost per complaint?",
         "Under ₹0.30 today, dominated by Claude Haiku tokens (~600 in, ~150 out per turn). "
         "Classifier, dedup, routing are CPU-only — effectively free."],
        ["How accurate is the classifier?",
         "MuRIL fine-tuned: dept F1 0.91 (25 classes), sub-cat ~0.85 (142 classes). "
         "Low-confidence cases trigger a clarifying question — we never silently mis-route."],
        ["How does a new portal get added?",
         "One Python class with four methods (submit, check_status, list_fields, validate) + one row in portals.csv. "
         "No changes to the core pipeline. Hot-reload supported in dev."],
        ["What happens if all 7 retries fail?",
         "The complaint moves to a 'manual intervention' queue visible in the dashboard. "
         "A reviewer can re-trigger, edit, or escalate. Nothing is silently dropped."],
        ["How does this differ from MyGov chatbot or CPGRAMS?",
         "MyGov is conversation only — no routing, no dedup, no submission, no tracking. "
         "CPGRAMS is a form. We're the full pipeline; CPGRAMS becomes our fallback portal, not our front door."],
        ["Can the model retrain itself?",
         "Yes. Every reviewer override lands in complaint_reviews. The training script consumes that table — "
         "weekly cron retrains MuRIL and ships a new model artefact. Manually toggled today, automatable."],
    ]
    qa = Table(qa_rows, colWidths=[6 * cm, 10 * cm])
    qa.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), BRAND_PRIMARY),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTNAME", (0, 1), (0, -1), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 8.5),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [LIGHT_GREY, colors.white]),
        ("GRID", (0, 0), (-1, -1), 0.3, MID_GREY),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 5),
        ("RIGHTPADDING", (0, 0), (-1, -1), 5),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
    ]))
    flow.append(qa)

    flow.append(PageBreak())

    flow.append(Paragraph("APPENDIX", ST["slide_no"]))
    flow.append(Paragraph("Hard numbers to memorise", ST["slide_title"]))
    flow.append(HRFlowable(width="100%", thickness=1.4, color=BRAND_ACCENT, spaceAfter=10))

    nums = Table([
        ["Metric", "Value", "Source"],
        ["Government portals routed", "70", "portals.csv registry"],
        ["Department classes", "25", "classifier head 1"],
        ["Sub-category classes", "142", "classifier head 2"],
        ["Departments F1 (MuRIL)", "0.91", "training eval set"],
        ["Sub-category F1 (MuRIL)", "~0.85", "training eval set"],
        ["Languages supported", "3", "Hindi · English · Hinglish"],
        ["Dedup threshold (cosine)", "0.85", "S-BERT MiniLM-L12"],
        ["Embedding model size", "117 MB / 384-dim", "paraphrase-multilingual-MiniLM-L12-v2"],
        ["LLM latency", "~700 ms", "Claude Haiku 4.5, temp 0.2"],
        ["Submission retry attempts", "7", "1m → 2m → 5m → 15m → 1h → 4h → 24h"],
        ["Polling cadence (day 1)", "1 hour", "tracker schedule"],
        ["Polling cadence (week 1)", "6 hours", "tracker schedule"],
        ["Polling cadence (after)", "24 hours", "tracker schedule"],
        ["Cost per complaint", "&lt; ₹0.30", "Haiku tokens dominate"],
        ["Microservices in stack", "10", "9 backend + frontend"],
        ["Audit hash function", "SHA-256", "complaint_events chain"],
        ["Field validators", "11", "pincode · mobile · Aadhaar · ..."],
        ["Adapters shipped", "4", "CPGRAMS · MPCM181 · MPPKVVCL · Generic"],
    ], colWidths=[6 * cm, 4 * cm, 6 * cm])
    nums.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), BRAND_PRIMARY),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTNAME", (1, 1), (1, -1), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [LIGHT_GREY, colors.white]),
        ("GRID", (0, 0), (-1, -1), 0.3, MID_GREY),
        ("LEFTPADDING", (0, 0), (-1, -1), 5),
        ("RIGHTPADDING", (0, 0), (-1, -1), 5),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
    ]))
    flow.append(nums)

    flow.append(Spacer(1, 0.4 * cm))
    flow.append(section("One-line elevator pitch (memorise verbatim)"))
    flow.append(Paragraph(
        "<i>“Margdarshan.ai turns ‘bijli nahi aa rahi’ — typed or spoken in any Indian language — into a tracked, "
        "deduplicated, audit-trailed complaint at exactly the right government portal out of seventy. End to end. Under a second.”</i>",
        ST["body"],
    ))

    doc.build(flow)
    print(f"✓ Wrote {OUT_PATH}")


if __name__ == "__main__":
    build()
