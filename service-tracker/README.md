# service-tracker

Stage 10 — polls portals for status, normalizes to canonical UCO statuses.

## Endpoints

```
POST /api/v1/lookup-latest         body: { user_id }   → user's complaints
POST /api/v1/normalize-status      body: { portal_status_raw } → canonical
GET  /healthz
```

## Status mapping

`STATUS_MAP` in main.py — extend per portal.
