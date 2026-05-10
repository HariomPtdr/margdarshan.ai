# service-routing

Stage 5 — picks the best portal for a complaint.

Hierarchical strategy: **municipal > district > state > national**. Local resolves faster.

## Endpoint

```
POST /api/v1/route
  body: { complaint_id, department, sub_category?, priority? }
  returns: { portal_id, portal_name, jurisdiction_level, required_fields, collected_fields }
```

## Portal registry

Hardcoded in `main.py` for the prototype (4 departments × 2-3 portals each). Move to Postgres for prod.
