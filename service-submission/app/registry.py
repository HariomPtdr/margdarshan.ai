"""Adapter registry — add a portal by dropping a file in adapters/ and registering here.

Zero changes elsewhere when onboarding a new portal.
"""

from .adapters import CPGRAMSAdapter, MPCM181Adapter
from .adapters.base import PortalAdapter

_REGISTRY: dict[str, type[PortalAdapter]] = {
    "P001": CPGRAMSAdapter,
    "P002": CPGRAMSAdapter,   # PMO routes to CPGRAMS
    "P031": MPCM181Adapter,
}

_FALLBACK = CPGRAMSAdapter


def get_adapter(portal_id: str) -> PortalAdapter:
    """Return an instantiated adapter for the given portal_id.
    Falls back to CPGRAMSAdapter if no specific adapter is registered."""
    cls = _REGISTRY.get(portal_id, _FALLBACK)
    return cls()


def registered_portals() -> list[str]:
    return list(_REGISTRY.keys())
