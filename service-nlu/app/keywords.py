"""Domain dictionary keyword extraction.

Maps surface words → canonical domain hint. Used both for keyword tags and
as a hint prepended to the classifier input.
"""

DOMAIN_DICT = {
    # Electricity
    "bijli": "electricity", "बिजली": "electricity",
    "current": "electricity", "transformer": "electricity",
    "meter": "electricity", "load shedding": "electricity",
    "voltage": "electricity", "power cut": "electricity",
    "power": "electricity", "electric": "electricity",

    # Water
    "paani": "water", "पानी": "water", "water": "water",
    "tap": "water", "pipe": "water", "leak": "water",
    "supply": "water", "tanker": "water", "नल": "water",

    # Roads
    "sadak": "roads", "सड़क": "roads", "road": "roads",
    "pothole": "roads", "गड्ढा": "roads", "gaddha": "roads",
    "highway": "roads", "footpath": "roads",

    # Waste
    "kachra": "waste", "कचरा": "waste", "garbage": "waste",
    "trash": "waste", "dustbin": "waste",

    # Police
    "police": "police", "FIR": "police", "fir": "police",
    "thana": "police", "थाना": "police", "crime": "police",

    # Banking
    "bank": "banking", "atm": "banking", "एटीएम": "banking",
    "transaction": "banking", "refund": "banking",

    # Health
    "hospital": "health", "doctor": "health", "अस्पताल": "health",
    "medicine": "health", "ambulance": "health",

    # Education
    "school": "education", "scholarship": "education", "स्कूल": "education",
    "fee": "education", "teacher": "education",

    # Transport
    "bus": "transport", "rto": "transport", "license": "transport",
    "vehicle": "transport", "trafic": "transport", "traffic": "transport",

    # Pension
    "pension": "pension", "पेंशन": "pension", "retirement": "pension",
    "vridha": "pension", "widow": "pension", "vidhwa": "pension",
    "disability": "pension", "viklang": "pension",

    # Ration / PDS
    "ration": "ration", "राशन": "ration", "fps": "ration",
    "ration card": "ration", "fair price": "ration", "pds": "ration",
    "anaj": "ration", "anaaj": "ration", "gehu": "ration", "chawal": "ration",

    # Agriculture
    "kisan": "agriculture", "किसान": "agriculture", "farmer": "agriculture",
    "crop": "agriculture", "fasal": "agriculture", "fertilizer": "agriculture",
    "khet": "agriculture", "खेत": "agriculture",

    # Cyber / fraud
    "cyber": "cyber", "fraud": "cyber", "online fraud": "cyber",
    "scam": "cyber", "hacking": "cyber", "phishing": "cyber",

    # Housing
    "housing": "housing", "property": "housing", "plot": "housing",
    "makaan": "housing", "मकान": "housing", "ghar": "housing",

    # Corruption
    "bribery": "corruption", "corruption": "corruption", "rishwat": "corruption",
    "भ्रष्टाचार": "corruption", "illegal": "corruption",

    # Accident (for roads priority)
    "accident": "roads", "crash": "roads", "ghayel": "roads",
    "injured": "roads", "durghatna": "roads",
}


def extract_keywords(text: str) -> tuple[list[str], list[str]]:
    """Returns (matched_keywords, domain_hints)."""
    matched: list[str] = []
    domains: set[str] = set()
    text_lower = text.lower()
    for word, domain in DOMAIN_DICT.items():
        if word in text_lower:
            matched.append(word)
            domains.add(domain)
    return matched, sorted(domains)
