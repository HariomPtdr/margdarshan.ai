#!/usr/bin/env bash
# End-to-end smoke test for Shikayat Saathi.
# Requires stack to be up: docker compose up -d
# Usage: bash scripts/smoke_test.sh

GATEWAY="${GATEWAY:-http://localhost:8000}"
PASS=0; FAIL=0

green() { printf '\033[32m✓\033[0m %s\n' "$*"; }
red()   { printf '\033[31m✗\033[0m %s\n' "$*"; }

check() {
  local label="$1"; local url="$2"; local method="${3:-GET}"; local body="$4"
  local resp rc
  if [ -n "$body" ]; then
    resp=$(curl -sf -X "$method" "$url" -H "Content-Type: application/json" -d "$body" 2>/dev/null); rc=$?
  else
    resp=$(curl -sf "$url" 2>/dev/null); rc=$?
  fi
  if [ $rc -eq 0 ] && [ -n "$resp" ]; then
    green "$label"
    PASS=$((PASS+1))
    echo "$resp"
    return 0
  else
    red "$label"
    FAIL=$((FAIL+1))
    return 1
  fi
}

# ── 1. Healthchecks ────────────────────────────────────────────────────────────
echo ""
echo "══ 1. Health checks ══"
for port_svc in "8000:gateway" "8001:chatbot" "8002:location" "8003:nlu" "8004:classifier" "8005:routing" "8006:submission" "8007:tracker"; do
  port="${port_svc%%:*}"; svc="${port_svc##*:}"
  if curl -sf "http://localhost:$port/healthz" > /dev/null 2>&1; then
    green "$svc :$port"
    PASS=$((PASS+1))
  else
    red "$svc :$port"
    FAIL=$((FAIL+1))
  fi
done

# ── 2. Classifier model ────────────────────────────────────────────────────────
echo ""
echo "══ 2. Classifier model check ══"
clf_health=$(curl -sf "http://localhost:8004/healthz" 2>/dev/null)
model=$(echo "$clf_health" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('model','unknown'))" 2>/dev/null)
if [ "$model" = "muril" ]; then
  green "MuRIL model loaded (not rule-based)"
  PASS=$((PASS+1))
else
  red "MuRIL not loaded — running rule-based (model=$model)"
  FAIL=$((FAIL+1))
fi

# ── 3. Portal registry ────────────────────────────────────────────────────────
echo ""
echo "══ 3. Portal registry ══"
portals_resp=$(curl -sf "http://localhost:8005/api/v1/portals" 2>/dev/null)
count=$(echo "$portals_resp" | python3 -c "import sys,json; print(len(json.load(sys.stdin)))" 2>/dev/null)
if [ -n "$count" ] && [ "$count" -ge 10 ]; then
  green "Portal registry: $count portals loaded"
  PASS=$((PASS+1))
else
  red "Portal registry empty or unavailable (count=$count)"
  FAIL=$((FAIL+1))
fi

# ── 4. Auth – register + login ────────────────────────────────────────────────
echo ""
echo "══ 4. Auth ══"
SMOKE_USER="smoke_$(date +%s)"
SMOKE_MOBILE=$(python3 -c "import random,time; random.seed(int(time.time()*1000)); print('9'+''.join([str(random.randint(0,9)) for _ in range(9)]))" 2>/dev/null || echo "9$(date +%s | tail -c 9)")
SMOKE_PASS="Test@1234"

reg_resp=$(curl -sf -X POST "$GATEWAY/api/v1/auth/register" \
  -H "Content-Type: application/json" \
  -d "{\"name\":\"Smoke Tester\",\"email\":\"${SMOKE_USER}@example.com\",\"mobile\":\"${SMOKE_MOBILE}\",\"password\":\"$SMOKE_PASS\",\"gender\":\"Male\",\"state\":\"Delhi\",\"district\":\"Delhi\"}" 2>/dev/null)
if echo "$reg_resp" | python3 -c "import sys,json; d=json.load(sys.stdin); assert 'token' in d or 'user_id' in d" 2>/dev/null; then
  green "Register new user"
  PASS=$((PASS+1))
  TOKEN=$(echo "$reg_resp" | python3 -c "import sys,json; print(json.load(sys.stdin).get('token',''))" 2>/dev/null)
else
  red "Register new user"
  echo "  $reg_resp"
  FAIL=$((FAIL+1))
  TOKEN=""
fi

# ── 5. Chat – grievance flow (electricity complaint) ──────────────────────────
echo ""
echo "══ 5. Chat pipeline ══"
AUTH_ARGS=()
[ -n "$TOKEN" ] && AUTH_ARGS=(-H "Authorization: Bearer $TOKEN")

chat_resp=$(curl -sf -X POST "$GATEWAY/api/v1/chat" \
  -H "Content-Type: application/json" \
  "${AUTH_ARGS[@]}" \
  -d '{
    "message": "bijli nahi aa rahi 3 din se, Bhopal MP",
    "language_preference": "hinglish"
  }' 2>/dev/null)

if [ -n "$chat_resp" ]; then
  green "POST /api/v1/chat (electricity, Bhopal)"
  PASS=$((PASS+1))
  echo "$chat_resp" | python3 -m json.tool 2>/dev/null || echo "$chat_resp"

  # Extract complaint_id and session_id for follow-up
  COMPLAINT_ID=$(echo "$chat_resp" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('complaint_id',''))" 2>/dev/null)
  SESSION_ID=$(echo "$chat_resp" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('session_id',''))" 2>/dev/null)
else
  red "POST /api/v1/chat"
  FAIL=$((FAIL+1))
  COMPLAINT_ID=""
  SESSION_ID=""
fi

# Second message: provide location (same session)
if [ -n "$SESSION_ID" ]; then
  chat2_resp=$(curl -sf -X POST "$GATEWAY/api/v1/chat" \
    -H "Content-Type: application/json" \
    "${AUTH_ARGS[@]}" \
    -d "{
      \"message\": \"mera address hai 15 Civil Lines, Bhopal, Madhya Pradesh 462001\",
      \"session_id\": \"$SESSION_ID\"
    }" 2>/dev/null)
  if [ -n "$chat2_resp" ]; then
    green "POST /api/v1/chat (follow-up: address)"
    PASS=$((PASS+1))
  else
    red "POST /api/v1/chat (follow-up: address)"
    FAIL=$((FAIL+1))
  fi
fi

# ── 6. Reverse-geocode ─────────────────────────────────────────────────────────
echo ""
echo "══ 6. Location reverse-geocode ══"
check "POST /api/v1/location/reverse-geocode (Bhopal)" \
  "$GATEWAY/api/v1/location/reverse-geocode" POST \
  '{"lat": 23.2599, "lon": 77.4126}'

# ── 7. Complaint tracker ───────────────────────────────────────────────────────
if [ -n "$COMPLAINT_ID" ]; then
  echo ""
  echo "══ 7. Complaint tracker ══"
  track_resp=$(curl -sf "$GATEWAY/api/v1/complaints/$COMPLAINT_ID" "${AUTH_ARGS[@]}" 2>/dev/null || true)
  if [ -n "$track_resp" ]; then
    green "GET /api/v1/complaints/$COMPLAINT_ID/status"
    PASS=$((PASS+1))
    echo "$track_resp" | python3 -m json.tool 2>/dev/null || echo "$track_resp"
  else
    red "GET /api/v1/complaints/$COMPLAINT_ID/status (not found or not yet persisted)"
    FAIL=$((FAIL+1))
  fi
fi

# ── 8. Admin endpoints ─────────────────────────────────────────────────────────
echo ""
echo "══ 8. Admin stats ══"
if curl -sf "$GATEWAY/api/v1/admin/stats" > /dev/null 2>&1; then
  green "GET /api/v1/admin/stats (accessible)"
  PASS=$((PASS+1))
else
  # Admin may require auth — try with token
  if [ -n "$TOKEN" ] && curl -sf "$GATEWAY/api/v1/admin/stats" -H "Authorization: Bearer $TOKEN" > /dev/null 2>&1; then
    green "GET /api/v1/admin/stats (with auth)"
    PASS=$((PASS+1))
  else
    red "GET /api/v1/admin/stats (unavailable)"
    FAIL=$((FAIL+1))
  fi
fi

# ── Summary ────────────────────────────────────────────────────────────────────
echo ""
echo "════════════════════════════════════"
echo "  Passed: $PASS   Failed: $FAIL"
echo "════════════════════════════════════"
[ "$FAIL" -eq 0 ] && exit 0 || exit 1
