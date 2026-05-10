# service-submission

Stage 8 — submits to the chosen portal via plug-and-play adapter.

**Current:** mock adapter that returns a fake ticket ID. Lets the demo flow end-to-end.

**Next:** real adapters per portal. Each adapter implements:
- `authenticate()`
- `submit(payload)`
- `check_status(ticket_id)`
- `append_update(ticket_id, message)`

## Endpoint

```
POST /api/v1/submit
  body: { complaint_id, portal_id, payload }
  returns: { portal_ticket_id, portal_status_raw, canonical_status, submitted_at }
```
