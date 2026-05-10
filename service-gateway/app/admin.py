"""Government dashboard admin endpoints.

All data is read-only. No auth guard for prototype — add role check in production.

GET /api/v1/admin/stats                       — system-wide metrics
GET /api/v1/admin/portals                     — portal list with complaint counts
GET /api/v1/admin/portals/{portal_id}         — portal detail + complaints routed to it
GET /api/v1/admin/complaints                  — paginated complaint list (filterable)
GET /api/v1/admin/complaints/{complaint_id}   — full complaint with audit chain + dup filers
"""

import json
import logging
import os
from typing import Optional

import httpx
from fastapi import APIRouter, Query

from . import db
from .audit import get_chain

logger = logging.getLogger(__name__)

ROUTING_URL = os.getenv("ROUTING_URL", "http://service-routing:8005")

router = APIRouter(prefix="/api/v1/admin", tags=["admin"])

_http: Optional[httpx.AsyncClient] = None


def set_http_client(client: httpx.AsyncClient):
    global _http
    _http = client


# ── Stats ─────────────────────────────────────────────────────────────

@router.get("/stats")
async def stats():
    async with db.pool().acquire() as conn:
        total = await conn.fetchval("SELECT COUNT(*) FROM complaints")
        by_status = await conn.fetch(
            "SELECT status, COUNT(*) AS n FROM complaints GROUP BY status ORDER BY n DESC"
        )
        by_dept = await conn.fetch(
            "SELECT department, COUNT(*) AS n FROM complaints "
            "WHERE department IS NOT NULL GROUP BY department ORDER BY n DESC LIMIT 8"
        )
        by_district = await conn.fetch(
            "SELECT district, COUNT(*) AS n FROM complaints "
            "WHERE district IS NOT NULL GROUP BY district ORDER BY n DESC LIMIT 8"
        )
        recent = await conn.fetch(
            "SELECT complaint_id, summary, status, department, created_at "
            "FROM complaints ORDER BY created_at DESC LIMIT 10"
        )
        duplicate_total = await conn.fetchval(
            "SELECT COUNT(*) FROM complaints "
            "WHERE (pipeline_data->'dedup'->>'is_duplicate')::boolean = true"
        )

    return {
        "total_complaints": total,
        "duplicate_complaints": duplicate_total or 0,
        "by_status":   [{"status": r["status"], "count": r["n"]} for r in by_status],
        "by_department": [{"department": r["department"], "count": r["n"]} for r in by_dept],
        "by_district": [{"district": r["district"], "count": r["n"]} for r in by_district],
        "recent": [
            {
                "complaint_id": str(r["complaint_id"]),
                "summary": r["summary"],
                "status": r["status"],
                "department": r["department"],
                "created_at": int(r["created_at"].timestamp() * 1000),
            }
            for r in recent
        ],
    }


# ── Portals ────────────────────────────────────────────────────────────

@router.get("/portals")
async def admin_portals():
    # Complaint counts from Postgres.
    async with db.pool().acquire() as conn:
        counts_rows = await conn.fetch(
            "SELECT portal_id, COUNT(*) AS n FROM complaints "
            "WHERE portal_id IS NOT NULL GROUP BY portal_id"
        )
    counts = {r["portal_id"]: r["n"] for r in counts_rows}

    # Portal metadata from service-routing.
    portals_meta = []
    try:
        resp = await _http.get(f"{ROUTING_URL}/api/v1/portals", timeout=5.0)
        portals_meta = resp.json()
    except Exception as e:
        logger.warning("Could not fetch portals from routing: %s", e)

    # Merge.
    result = []
    for p in portals_meta:
        pid = p["portal_id"]
        result.append({**p, "complaint_count": counts.get(pid, 0)})

    # Also include portals that have complaints but no metadata (shouldn't happen).
    known_ids = {p["portal_id"] for p in portals_meta}
    for pid, n in counts.items():
        if pid not in known_ids:
            result.append({"portal_id": pid, "portal_name": pid, "complaint_count": n})

    result.sort(key=lambda x: x["complaint_count"], reverse=True)
    return result


@router.get("/portals/{portal_id}")
async def admin_portal_detail(portal_id: str, limit: int = Query(50, le=200)):
    # Portal metadata.
    portal_meta = {}
    try:
        resp = await _http.get(f"{ROUTING_URL}/api/v1/portals/{portal_id}", timeout=5.0)
        portal_meta = resp.json() if resp.status_code == 200 else {}
    except Exception:
        pass

    # Complaints routed to this portal.
    async with db.pool().acquire() as conn:
        rows = await conn.fetch(
            """
            SELECT c.complaint_id, c.summary, c.status, c.department, c.sub_category,
                   c.district, c.ticket_id, c.created_at, c.updated_at,
                   c.pipeline_data,
                   u.name AS user_name, u.mobile AS user_mobile
            FROM complaints c
            JOIN users u ON c.user_id = u.id
            WHERE c.portal_id = $1
            ORDER BY c.created_at DESC
            LIMIT $2
            """,
            portal_id, limit,
        )

    complaints = []
    for r in rows:
        pd = r["pipeline_data"] or {}
        classification = pd.get("classification", {})
        dedup = pd.get("dedup", {})
        complaints.append({
            "complaint_id":  str(r["complaint_id"]),
            "summary":       r["summary"],
            "status":        r["status"],
            "department":    r["department"],
            "sub_category":  r["sub_category"],
            "district":      r["district"],
            "ticket_id":     r["ticket_id"],
            "user_name":     r["user_name"],
            "user_mobile":   r["user_mobile"][-4:].rjust(10, "*") if r["user_mobile"] else "",
            "priority":      classification.get("priority"),
            "sentiment":     classification.get("sentiment"),
            "is_duplicate":  bool(dedup.get("is_duplicate")),
            "duplicate_count": dedup.get("duplicate_count", 0),
            "created_at":    int(r["created_at"].timestamp() * 1000),
            "updated_at":    int(r["updated_at"].timestamp() * 1000),
        })

    return {"portal": portal_meta, "complaints": complaints, "total": len(complaints)}


# ── Complaints ─────────────────────────────────────────────────────────

@router.get("/complaints")
async def admin_complaints(
    status: Optional[str] = None,
    department: Optional[str] = None,
    district: Optional[str] = None,
    limit: int = Query(50, le=200),
    offset: int = 0,
):
    filters = ["1=1"]
    params: list = []
    i = 1
    if status:
        filters.append(f"c.status = ${i}"); params.append(status); i += 1
    if department:
        filters.append(f"c.department = ${i}"); params.append(department); i += 1
    if district:
        filters.append(f"c.district = ${i}"); params.append(district); i += 1

    where = " AND ".join(filters)
    params += [limit, offset]

    async with db.pool().acquire() as conn:
        rows = await conn.fetch(
            f"""
            SELECT c.complaint_id, c.summary, c.status, c.department, c.sub_category,
                   c.district, c.portal_id, c.ticket_id, c.created_at,
                   u.name AS user_name
            FROM complaints c
            JOIN users u ON c.user_id = u.id
            WHERE {where}
            ORDER BY c.created_at DESC
            LIMIT ${i} OFFSET ${i+1}
            """,
            *params,
        )
        total = await conn.fetchval(
            f"SELECT COUNT(*) FROM complaints c JOIN users u ON c.user_id = u.id WHERE {where}",
            *params[:-2],
        )

    return {
        "complaints": [
            {
                "complaint_id": str(r["complaint_id"]),
                "summary":      r["summary"],
                "status":       r["status"],
                "department":   r["department"],
                "sub_category": r["sub_category"],
                "district":     r["district"],
                "portal_id":    r["portal_id"],
                "ticket_id":    r["ticket_id"],
                "user_name":    r["user_name"],
                "created_at":   int(r["created_at"].timestamp() * 1000),
            }
            for r in rows
        ],
        "total": total,
        "limit": limit,
        "offset": offset,
    }


@router.get("/complaints/{complaint_id}")
async def admin_complaint_detail(complaint_id: str):
    async with db.pool().acquire() as conn:
        row = await conn.fetchrow(
            """
            SELECT c.*, u.name AS user_name, u.mobile AS user_mobile,
                   u.email AS user_email, u.district AS user_district
            FROM complaints c
            JOIN users u ON c.user_id = u.id
            WHERE c.complaint_id = $1
            """,
            complaint_id,
        )
    if not row:
        from fastapi import HTTPException
        raise HTTPException(404, "Complaint not found")

    pd = row["pipeline_data"] or {}

    # Routing explanation: why this portal was chosen.
    routing = pd.get("routing", {})
    routing_explanation = None
    if routing:
        routing_explanation = {
            "portal_id":    routing.get("portal_id"),
            "portal_name":  routing.get("portal_name"),
            "level":        routing.get("jurisdiction_level"),
            "reason":       f"Department '{row['department']}' in district '{row['district']}' matched {routing.get('portal_name')} at {routing.get('jurisdiction_level')} level.",
        }

    # Duplicate filers.
    dedup = pd.get("dedup", {})
    duplicate_filers = dedup.get("duplicate_details", [])

    # Audit chain.
    chain = await get_chain(complaint_id)

    raw_mobile = row["user_mobile"] or ""
    masked = ("*" * (len(raw_mobile) - 4) + raw_mobile[-4:]) if len(raw_mobile) >= 4 else "****"

    return {
        "complaint_id":   str(row["complaint_id"]),
        "summary":        row["summary"],
        "status":         row["status"],
        "department":     row["department"],
        "sub_category":   row["sub_category"],
        "district":       row["district"],
        "portal_id":      row["portal_id"],
        "ticket_id":      row["ticket_id"],
        "created_at":     int(row["created_at"].timestamp() * 1000),
        "updated_at":     int(row["updated_at"].timestamp() * 1000),
        "filer": {
            "name":     row["user_name"],
            "mobile":   masked,
            "email":    row["user_email"],
            "district": row["user_district"],
        },
        "pipeline": {
            "location":       pd.get("location"),
            "nlu":            pd.get("nlu"),
            "classification": pd.get("classification"),
            "routing":        pd.get("routing"),
            "portal_fields":  pd.get("portal_fields"),
            "submission":     pd.get("submission"),
        },
        "routing_explanation": routing_explanation,
        "dedup": {
            "is_duplicate":    bool(dedup.get("is_duplicate")),
            "is_same_user":    bool(dedup.get("is_same_user")),
            "duplicate_count": dedup.get("duplicate_count", 0),
            "duplicate_filers": duplicate_filers,
        },
        "audit_chain": chain,
    }
