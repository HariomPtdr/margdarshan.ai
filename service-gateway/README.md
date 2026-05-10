# service-gateway

Single public API + WebSocket bridge. Also runs the pipeline orchestrator loop.

## Endpoints

```
POST /api/v1/chat                          → proxies to chatbot
POST /api/v1/location/reverse-geocode      → proxies to location
GET  /api/v1/location/pincode/{pin}        → proxies to location
POST /api/v1/complaint/attach-location     → reverse-geocode + advance pipeline
WS   /ws/pipeline/{complaint_id}           → live updates
GET  /healthz
```

## Orchestrator loop

Subscribes to `pipeline:all` Redis channel. On each event, triggers the next stage:

```
stage_0_chat:completed       → POST /nlu
stage_2_nlu:completed        → POST /classifier
stage_3_classify:completed   → POST /routing
... (extend as services come online)
```

This decouples services completely — they never call each other directly.
