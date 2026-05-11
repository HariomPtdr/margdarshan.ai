"""Prompts for Shikayat Saathi.

SYSTEM_PROMPT has been removed — the State Machine + NLU architecture no longer
uses a monolithic LLM system prompt for conversation control.

FIELD_EXTRACTION_PROMPT is kept here for reference; the canonical copy now lives
in chatbot.py alongside extract_field().
"""

FIELD_EXTRACTION_PROMPT = """\
You are collecting form fields for a government grievance portal. The user is answering one field at a time.

Current field to collect: {field_name}
User's language: {language}
Next field (if any): {next_field}

Rules:
- Extract the value for "{field_name}" from the user's message.
- If the user clearly provided a value, set extracted to that value (string).
- If the user says they don't know, says "skip", or gives a non-answer, set extracted to null.
- Keep reply to 1 short sentence in the user's language.
- If extracted is not null and next_field is given, mention the next field in your reply.
- If extracted is null, give a brief hint about where to find "{field_name}".

Respond ONLY with this JSON (no markdown, no extra text):
{{"extracted": "<value or null>", "reply": "<1 sentence>"}}

Examples:
Field="Mobile Number", message="mera number 9876543210 hai"
→ {{"extracted": "9876543210", "reply": "9876543210 note kar liya."}}

Field="Full Name", message="Hariom Patidar"
→ {{"extracted": "Hariom Patidar", "reply": "Theek hai. Ab batayein: {next_field}"}}

Field="PNR Number", message="nahi pata"
→ {{"extracted": null, "reply": "PNR number aapki train ticket par hota hai — 10 digit ka number."}}
"""
