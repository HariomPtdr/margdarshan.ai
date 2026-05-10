"""PII detection + masking.

Extract values for downstream use, replace with type tokens for the classifier.
"""

import re

PATTERNS = {
    "PHONE": r"\b[6-9]\d{9}\b",
    "PINCODE": r"\b[1-9]\d{5}\b",
    "VEHICLE_NO": r"\b[A-Z]{2}\s?\d{1,2}\s?[A-Z]{1,3}\s?\d{1,4}\b",
    "AADHAAR": r"\b\d{4}\s?\d{4}\s?\d{4}\b",
    "EMAIL": r"[\w.+-]+@[\w-]+\.[\w.-]+",
    "CONSUMER_NO": r"\b\d{10,15}\b",
}


def extract_pii(text: str) -> tuple[dict, str]:
    """Returns (entities_dict, masked_text)."""
    pii: dict[str, list[str]] = {}
    masked = text
    for label, pattern in PATTERNS.items():
        matches = re.findall(pattern, text, re.IGNORECASE)
        if matches:
            pii[label] = list(set(matches))
            for m in matches:
                masked = masked.replace(m, f"[{label}]")
    return pii, masked
