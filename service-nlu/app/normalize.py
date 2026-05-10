"""Text normalization — runs before NER + classifier.

WhatsApp complaints are messy: typos, ALL CAPS, Devanagari digits,
abbreviations. This cleans without losing meaning.
"""

import re
import unicodedata

DEVANAGARI_TO_ARABIC = str.maketrans("०१२३४५६७८९", "0123456789")

ABBREV_MAP = {
    "nhi": "nahi", "nah": "nahi", "nai": "nahi",
    "h": "hai", "hn": "hai", "hai.": "hai",
    "kr": "kar", "krta": "karta", "krna": "karna",
    "kb": "kab", "tk": "tak",
    "bjli": "bijli", "bijly": "bijli", "bjly": "bijli",
    "pani": "paani", "pny": "paani", "panni": "paani",
    "sadk": "sadak", "sdk": "sadak",
    "complant": "complaint", "complent": "complaint",
    "plz": "please", "pls": "please",
    "u": "you", "ur": "your",
    "yr": "yaar",
    "mein": "mein", "me": "mein",
}


def normalize(text: str) -> str:
    text = unicodedata.normalize("NFC", text)
    text = text.translate(DEVANAGARI_TO_ARABIC)
    text = text.lower()
    words = text.split()
    expanded = [ABBREV_MAP.get(w, w) for w in words]
    text = " ".join(expanded)
    text = re.sub(r"\s+", " ", text)
    text = re.sub(r"([!?.,])\1+", r"\1", text)
    return text.strip()
