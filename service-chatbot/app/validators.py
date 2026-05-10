"""Field validators for portal form fields.

Each validator is a compiled regex.
FIELD_VALIDATOR_MAP maps lowercased field-name keywords → validator key.
On invalid input the chatbot re-asks once with a hint, then accepts on the 2nd retry.
"""

import re

_VALIDATORS: dict[str, re.Pattern] = {
    "mobile":       re.compile(r"^[6-9]\d{9}$"),
    "pincode":      re.compile(r"^\d{6}$"),
    "aadhaar_4":    re.compile(r"^\d{4}$"),
    "aadhaar_12":   re.compile(r"^\d{12}$"),
    "pan":          re.compile(r"^[A-Z]{5}[0-9]{4}[A-Z]$"),
    "vehicle_no":   re.compile(r"^[A-Z]{2}\d{2}[A-Z]{1,2}\d{4}$"),
    "email":        re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$"),
    "gstin":        re.compile(r"^\d{2}[A-Z]{5}\d{4}[A-Z][1-9A-Z]Z[0-9A-Z]$"),
    "pnr":          re.compile(r"^\d{10}$"),
    "consumer_no":  re.compile(r"^\d{7,12}$"),
    "account_no":   re.compile(r"^\d{9,18}$"),
    "uan":          re.compile(r"^\d{12}$"),
    "ppe_id":       re.compile(r"^\d{8,}$"),
}

# keyword (must appear in lowercased field name) → validator key
_KEYWORD_MAP: list[tuple[str, str]] = [
    ("aadhaar number (last 4",  "aadhaar_4"),
    ("aadhaar number",          "aadhaar_12"),
    ("aadhaar",                 "aadhaar_12"),
    ("mobile number",           "mobile"),
    ("mobile",                  "mobile"),
    ("phone",                   "mobile"),
    ("pincode",                 "pincode"),
    ("pin code",                "pincode"),
    ("pan number",              "pan"),
    ("vehicle number",          "vehicle_no"),
    ("vehicle no",              "vehicle_no"),
    ("email address",           "email"),
    ("email",                   "email"),
    ("gstin",                   "gstin"),
    ("pnr number",              "pnr"),
    ("ivrs consumer number",    "consumer_no"),
    ("consumer number",         "consumer_no"),
    ("consumer no",             "consumer_no"),
    ("bank account number",     "account_no"),
    ("account number",          "account_no"),
    ("uan",                     "uan"),
]

_HINTS: dict[str, str] = {
    "mobile":      "10-digit mobile number starting with 6, 7, 8 or 9 (e.g. 9876543210)",
    "pincode":     "6-digit pincode (e.g. 462001)",
    "aadhaar_4":   "last 4 digits of your Aadhaar card",
    "aadhaar_12":  "12-digit Aadhaar number (no spaces)",
    "pan":         "10-character PAN — 5 letters, 4 digits, 1 letter (e.g. ABCDE1234F)",
    "vehicle_no":  "registration number on your RC (e.g. MP09AB1234)",
    "email":       "valid email address (e.g. name@example.com)",
    "gstin":       "15-character GSTIN on your GST registration certificate",
    "pnr":         "10-digit PNR from your train ticket",
    "consumer_no": "7-12 digit consumer / IVRS number from your electricity bill",
    "account_no":  "bank account number (9-18 digits)",
    "uan":         "12-digit UAN from your PF passbook or payslip",
    "ppe_id":      "policy or PPO number from your document",
}


def validate(field_name: str, value: str) -> tuple[bool, str]:
    """Return (is_valid, hint_message).

    is_valid=True means the value passes the validator (or no validator exists for this field).
    hint_message is empty when valid; contains guidance text when invalid.
    """
    field_lower = field_name.lower()
    validator_key: str | None = None

    for keyword, key in _KEYWORD_MAP:
        if keyword in field_lower:
            validator_key = key
            break

    if validator_key is None:
        return True, ""  # no rule for this field — accept anything

    pattern = _VALIDATORS.get(validator_key)
    if pattern is None:
        return True, ""

    # normalise before matching
    clean = value.strip().replace(" ", "")
    if validator_key in ("pan", "vehicle_no", "gstin"):
        clean = clean.upper()

    if pattern.fullmatch(clean):
        return True, ""
    return False, _HINTS.get(validator_key, "")
