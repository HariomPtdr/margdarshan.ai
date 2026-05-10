"""Load portals.csv once at startup and expose a lookup function.

Hierarchy: Regional (city-match) > State (ALL_MP) > Central (ALL_INDIA)
Within each tier, prefer the most-specific portal (fewest dept tags) over catch-alls.
Non-MP states go straight to the best-matching Central portal.
"""

import csv
from dataclasses import dataclass, field
from pathlib import Path

_DATA_FILE = Path(__file__).parent.parent / "data" / "portals.csv"

MP_STATE_NAMES = {"madhya pradesh", "mp", "m.p."}

# These are broad catch-alls — skip them when picking a "specific" portal.
# They are used only as explicit fallbacks at the end.
_CATCH_ALL_IDS = {"P001", "P002", "P031"}


@dataclass
class PortalEntry:
    portal_id: str
    portal_name: str
    portal_level: str           # Regional | State | Central
    authority_name: str
    covers_districts: list[str] # ["ALL_MP"] | ["ALL_INDIA"] | ["Bhopal", ...]
    website: str
    has_online: bool
    classifier_dept_tags: list[str]
    complaint_categories: str
    required_fields: list[str]
    helpline: str
    whatsapp: str
    fallback_portal_id: str
    # derived
    tag_count: int = field(init=False)

    def __post_init__(self):
        self.tag_count = len(self.classifier_dept_tags)


_portals: list[PortalEntry] = []
_by_id: dict[str, PortalEntry] = {}
_index: dict[str, list[PortalEntry]] = {}


def load_portals(path: Path = _DATA_FILE) -> None:
    global _portals, _by_id, _index
    entries: list[PortalEntry] = []

    with open(path, newline="", encoding="utf-8") as fh:
        reader = csv.DictReader(fh)
        for row in reader:
            entry = PortalEntry(
                portal_id=row["portal_id"].strip(),
                portal_name=row["portal_name"].strip(),
                portal_level=row["portal_level"].strip(),
                authority_name=row["authority_name"].strip(),
                covers_districts=[d.strip() for d in row["covers_districts"].split("|")],
                website=row["website"].strip(),
                has_online=row["has_online"].strip().lower() == "yes",
                classifier_dept_tags=[t.strip() for t in row["classifier_dept_tags"].split("|")],
                complaint_categories=row["complaint_categories"].strip(),
                required_fields=[f.strip() for f in row["required_fields"].split("|")],
                helpline=row["helpline"].strip(),
                whatsapp=row["whatsapp"].strip(),
                fallback_portal_id=row["fallback_portal_id"].strip(),
            )
            entries.append(entry)

    _portals = entries
    _by_id = {e.portal_id: e for e in entries}

    idx: dict[str, list[PortalEntry]] = {}
    for entry in entries:
        for tag in entry.classifier_dept_tags:
            idx.setdefault(tag, []).append(entry)
    _index = idx


def _specificity_key(p: PortalEntry) -> int:
    """Lower is better — fewer tags means the portal is more specialised."""
    return p.tag_count


def find_portal(dept_tag: str, district: str, state: str) -> PortalEntry:
    """Return the best portal for (dept_tag, district, state).

    MP priority:   Regional (district match) > State-specific > P031 > Central-specific > P001
    Non-MP priority: Central-specific > P001
    Catch-alls (P001, P002, P031) are only returned as explicit fallbacks, not as "specific" picks.
    """
    candidates = [p for p in _index.get(dept_tag, []) if p.has_online]

    is_mp = state.strip().lower() in MP_STATE_NAMES
    district_norm = district.strip().lower()

    if not is_mp:
        # Central-specific portals only (skip P001/P002 catch-alls)
        central_specific = sorted(
            [p for p in candidates if p.portal_level == "Central" and p.portal_id not in _CATCH_ALL_IDS],
            key=_specificity_key,
        )
        return central_specific[0] if central_specific else _by_id["P001"]

    # --- MP user ---

    # 1. Regional: portal whose covers_districts contains this district
    regional = sorted(
        [
            p for p in candidates
            if p.portal_level == "Regional"
            and any(d.strip().lower() == district_norm for d in p.covers_districts)
        ],
        key=_specificity_key,
    )
    if regional:
        return regional[0]

    # 2. State-specific (ALL_MP portals, not catch-all P031)
    state_specific = sorted(
        [
            p for p in candidates
            if p.portal_level == "State"
            and "ALL_MP" in p.covers_districts
            and p.portal_id not in _CATCH_ALL_IDS
        ],
        key=_specificity_key,
    )
    if state_specific:
        return state_specific[0]

    # 3. P031 catch-all — only if it actually handles this dept
    p031 = _by_id.get("P031")
    if p031 and dept_tag in p031.classifier_dept_tags:
        return p031

    # 4. Central-specific (not P001/P002 — this covers things like INCOME_TAX, RAILWAY)
    central_specific = sorted(
        [p for p in candidates if p.portal_level == "Central" and p.portal_id not in _CATCH_ALL_IDS],
        key=_specificity_key,
    )
    if central_specific:
        return central_specific[0]

    # 5. CPGRAMS — ultimate fallback
    return _by_id["P001"]


def get_by_id(portal_id: str) -> PortalEntry | None:
    return _by_id.get(portal_id)


def portal_count() -> int:
    return len(_portals)
