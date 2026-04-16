#!/usr/bin/env bash
set -euo pipefail

if [[ "${BASH_SOURCE[0]}" != "$0" ]]; then
  echo "Do not source this script. Run with bash scripts/canary_admin_job.sh <scrape|generate>"
  return 2 2>/dev/null || exit 2
fi

# JOB_TYPE="${1:-generate}"
JOB_TYPE="${1:-scrape}"
BASE_URL="${BASE_URL:-http://localhost:8000}"
COUNT="${COUNT:-1}"
POLL_INTERVAL="${POLL_INTERVAL:-1}"
MAX_WAIT="${MAX_WAIT:-60}"
CONFIRM_OPENAI="${CONFIRM_OPENAI:-0}"

CONFIRM_OPENAI="${CONFIRM_OPENAI:-0}"

if command -v python3 >/dev/null 2>&1; then
  PYTHON_BIN="python3"
elif command -v python >/dev/null 2>&1; then
  PYTHON_BIN="python"
else
  echo "Python is required but was not found in PATH" >&2
  exit 2
fi

die() {
  echo "$*" >&2
  exit 2
}

require_uint_in_range() {
  local name="$1"
  local value="$2"
  local min="$3"
  local max="$4"

  [[ "$value" =~ ^[0-9]+$ ]] || die "$name must be an integer"
  (( value >= min && value <= max )) || die "$name must be between $min and $max"
}

json_field() {
  local field="$1"
  "$PYTHON_BIN" -c 'import json,sys; data=json.load(sys.stdin); print(data[sys.argv[1]])' "$field"
}

assert_generate_provenance() {
  local resp="$1"

  RESP_JSON="$resp" "$PYTHON_BIN" - <<'PY'
import json
import os
import sys

body = json.loads(os.environ["RESP_JSON"])
if body.get("job_type") != "generate":
    sys.exit(0)

if body.get("status") != "completed":
    raise SystemExit("Generate canary did not complete")

summary = body.get("result_summary")
if not isinstance(summary, str) or not summary.strip():
    raise SystemExit("Generate result_summary missing or empty")

lines = [line for line in summary.splitlines() if line.startswith("Provenance: ")]
if len(lines) != 1:
    raise SystemExit(f"Expected exactly one Provenance line, got {len(lines)}")

payload = json.loads(lines[0][len("Provenance: "):])

required = {
    "schema_version",
    "provider",
    "requested_count",
    "recent_real_context_count",
    "recent_real_context",
}
missing = sorted(required - payload.keys())
if missing:
    raise SystemExit(f"Provenance missing keys: {missing}")

if payload["requested_count"] != body.get("requested_count"):
    raise SystemExit("Provenance requested_count mismatch")

if payload["provider"] not in {"openai_primary", "template_fallback"}:
    raise SystemExit(f"Unexpected provider: {payload['provider']}")

if not isinstance(payload["recent_real_context"], list):
    raise SystemExit("recent_real_context must be a list")

if payload["recent_real_context_count"] != len(payload["recent_real_context"]):
    raise SystemExit("recent_real_context_count mismatch")

audit_id = body.get("result_audit_id")
if not isinstance(audit_id, int) or audit_id < 1:
    raise SystemExit("result_audit_id missing or invalid for generate job")

print("provenance_assertions=pass")
PY
}

[[ "$JOB_TYPE" == "scrape" || "$JOB_TYPE" == "generate" ]] || die "Usage: $0 <scrape|generate>"

require_uint_in_range "COUNT" "$COUNT" 1 3
require_uint_in_range "POLL_INTERVAL" "$POLL_INTERVAL" 1 30
require_uint_in_range "MAX_WAIT" "$MAX_WAIT" 10 120

if [[ "$JOB_TYPE" == "generate" ]]; then
  [[ "$CONFIRM_OPENAI" == "1" ]] || die "Refusing generate canary. Set CONFIRM_OPENAI=1 explicitly."
  (( COUNT == 1 )) || die "For generate canary, COUNT must be 1 to minimize token burn."
fi

CREATE_RESP="$(curl -fsS -X POST "$BASE_URL/api/admin/$JOB_TYPE" \
  -H "Content-Type: application/json" \
  -d "{\"count\":$COUNT}")"

printf '%s\n' "$CREATE_RESP" | "$PYTHON_BIN" -m json.tool
JOB_ID="$(printf '%s' "$CREATE_RESP" | json_field "job_id")"
printf 'JOB_ID=%s\n' "$JOB_ID"

start_ts="$(date +%s)"
while true; do
  RESP="$(curl -fsS "$BASE_URL/api/admin/jobs/$JOB_ID")"
  STATUS="$(printf '%s' "$RESP" | json_field "status")"
  printf 'status=%s\n' "$STATUS"

  if [[ "$STATUS" == "completed" || "$STATUS" == "failed" ]]; then
    printf '%s\n' "$RESP" | "$PYTHON_BIN" -m json.tool

    if [[ "$JOB_TYPE" == "generate" && "$STATUS" == "completed" ]]; then
      assert_generate_provenance "$RESP"
    fi
    
    [[ "$STATUS" == "completed" ]] && exit 0 || exit 1
  fi

  now_ts="$(date +%s)"
  (( now_ts - start_ts < MAX_WAIT )) || { echo "Timed out after ${MAX_WAIT}s" >&2; exit 1; }

  sleep "$POLL_INTERVAL"
done