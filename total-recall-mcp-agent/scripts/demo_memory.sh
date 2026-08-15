#!/usr/bin/env bash
# End-to-end semantic memory demo over MCP — local stdio or live cloud HTTP.
#
# Exercises the full memory lifecycle:
#   1. remember_memory  — store a memory
#   2. recall_memory    — find it again via vector search
#   3. list_memories    — see it in the caller's memory list
#   4. forget_memory    — delete it (best-effort; skipped if the id can't be
#                         parsed from the remember response, never a hard
#                         failure)
#   5. list_memories    — confirm it's gone
#
# Every step logs with a uniform [HH:MM:SS] LEVEL prefix. Any tool error
# aborts the script with a non-zero exit code. Run with -h/--help for usage.
set -euo pipefail

usage() {
  cat <<'EOF'
Usage:
  ./scripts/demo_memory.sh [local|cloud] [options]

Modes:
  local   (default) stdio MCP against a fresh local agent process per call
          (DATABASE_URL from .env). No network dependency beyond CockroachDB.
  cloud   Streamable HTTP MCP against a deployed AWS ALB endpoint, with
          GitHub bearer auth (HTTP_AUTH_MODE=github). Requires --endpoint.

Options (cloud mode):
  --endpoint URL   REQUIRED. The MCP endpoint base URL to test — this
                   script does not know or guess it. Get yours from project
                   submission details
  --token TOKEN    Bearer token. Default: $TOKEN, or auto-fetched via
                   ./scripts/get_github_token.sh if `gh` is installed.

Examples:
  ./scripts/demo_memory.sh                                    # local (default)
  ./scripts/demo_memory.sh local
  ./scripts/demo_memory.sh cloud --endpoint http://<your-alb-dns-name>
  ./scripts/demo_memory.sh cloud --endpoint http://<your-alb-dns-name> --token ghp_xxx
EOF
}

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
UV_BIN="${UV_BIN:-$(command -v uv || true)}"
RESPONSE_WAIT="${RESPONSE_WAIT:-4}"    # stdio mode: seconds to let the agent answer after sending a call
HTTP_TIMEOUT="${HTTP_TIMEOUT:-15}"     # cloud mode: curl --max-time per call

MODE="local"
ENDPOINT_OVERRIDE=""
TOKEN_OVERRIDE=""

case "${1:-}" in
  local|cloud)
    MODE="$1"
    shift
    ;;
  -h|--help)
    usage
    exit 0
    ;;
esac

while [[ $# -gt 0 ]]; do
  case "$1" in
    --endpoint)
      ENDPOINT_OVERRIDE="${2:?--endpoint requires a URL}"
      shift 2
      ;;
    --token)
      TOKEN_OVERRIDE="${2:?--token requires a value}"
      shift 2
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      echo "Unknown argument: $1" >&2
      usage >&2
      exit 1
      ;;
  esac
done

# ---------------------------------------------------------------------------
# Uniform logging — [HH:MM:SS] LEVEL message. Colors auto-disable when not
# attached to a terminal (e.g. output redirected to a log file).
# ---------------------------------------------------------------------------
if [[ -t 1 ]]; then
  C_CYAN=$'\033[1;36m'; C_GREEN=$'\033[1;32m'; C_YELLOW=$'\033[1;33m'
  C_RED=$'\033[1;31m'; C_DIM=$'\033[2m'; C_RESET=$'\033[0m'
else
  C_CYAN=""; C_GREEN=""; C_YELLOW=""; C_RED=""; C_DIM=""; C_RESET=""
fi

_ts() { date '+%H:%M:%S'; }
log_step()  { printf '\n%s[%s] STEP  %s%s\n' "${C_CYAN}"  "$(_ts)" "$*" "${C_RESET}"; }
log_info()  { printf '%s[%s] INFO  %s%s\n'   "${C_DIM}"   "$(_ts)" "$*" "${C_RESET}"; }
log_ok()    { printf '%s[%s] OK    %s%s\n'   "${C_GREEN}" "$(_ts)" "$*" "${C_RESET}"; }
log_warn()  { printf '%s[%s] WARN  %s%s\n'   "${C_YELLOW}" "$(_ts)" "$*" "${C_RESET}" >&2; }
log_error() { printf '%s[%s] ERROR %s%s\n'   "${C_RED}"   "$(_ts)" "$*" "${C_RESET}" >&2; }
fail() { log_error "$*"; exit 1; }

pretty_json() {
  python3 -c '
import json, sys
try:
    print(json.dumps(json.loads(sys.stdin.read()), indent=2))
except Exception:
    print(sys.stdin.read())
'
}

# ---------------------------------------------------------------------------
# Preflight
# ---------------------------------------------------------------------------
log_step "Preflight checks (mode: ${MODE})"

[[ -f "${PROJECT_ROOT}/pyproject.toml" ]] || fail "pyproject.toml not found under ${PROJECT_ROOT} — is this script in scripts/ of the project?"
log_ok "project root: ${PROJECT_ROOT}"

if [[ "${MODE}" == "local" ]]; then
  [[ -n "${UV_BIN}" ]] || fail "uv not found in PATH. Install: https://docs.astral.sh/uv/"
  log_ok "uv found: ${UV_BIN}"

  if [[ -f "${PROJECT_ROOT}/.env" ]]; then
    log_ok ".env found"
  else
    log_warn ".env not found — the agent will fail unless DATABASE_URL is set another way"
  fi
else
  command -v curl >/dev/null 2>&1 || fail "curl not found in PATH"

  [[ -n "${ENDPOINT_OVERRIDE}" ]] || fail "cloud mode requires --endpoint <url> (get yours from submission details)."
  MCP_ENDPOINT_URL="${ENDPOINT_OVERRIDE%/mcp}"
  MCP_ENDPOINT_URL="${MCP_ENDPOINT_URL%/}"
  log_ok "cloud endpoint: ${MCP_ENDPOINT_URL}"

  TOKEN="${TOKEN_OVERRIDE:-${TOKEN:-}}"
  if [[ -z "${TOKEN}" ]]; then
    if [[ -x "${PROJECT_ROOT}/scripts/get_github_token.sh" ]] && command -v gh >/dev/null 2>&1; then
      log_info "no --token given — fetching one via scripts/get_github_token.sh"
      TOKEN="$("${PROJECT_ROOT}/scripts/get_github_token.sh" 2>/dev/null || true)"
    fi
  fi
  [[ -n "${TOKEN}" ]] || fail "No bearer token found. Pass --token <token>, set \$TOKEN, or install gh so scripts/get_github_token.sh can fetch one."
  log_ok "bearer token acquired"

  health_code="$(curl -s -X GET -o /dev/null -w '%{http_code}' --max-time "${HTTP_TIMEOUT}" "${MCP_ENDPOINT_URL}/health" || echo "000")"
  [[ "${health_code}" == "200" ]] || fail "${MCP_ENDPOINT_URL}/health returned ${health_code} — is the deployment up?"
  log_ok "endpoint healthy"
fi

# ---------------------------------------------------------------------------
# mcp_call NAME TOOL PARAMS_JSON
#
# Dispatches to the stdio or HTTP implementation based on $MODE, logs the
# outcome, and sets:
#   LAST_RESULT_JSON  — the "result" object as compact JSON (empty on failure)
#   LAST_CALL_OK      — "true" / "false"
# ---------------------------------------------------------------------------
mcp_call() {
  if [[ "${MODE}" == "cloud" ]]; then
    mcp_call_http "$@"
  else
    mcp_call_stdio "$@"
  fi
}

mcp_call_stdio() {
  local name="$1" tool="$2" params="$3"
  local err_log
  err_log="$(mktemp)"

  log_step "${name}"
  log_info "tool=${tool} args=${params}"

  local output
  output=$(
    (
      echo '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"demo_memory","version":"1.0"}}}'
      sleep 1
      echo '{"jsonrpc":"2.0","method":"notifications/initialized"}'
      sleep 1
      echo "{\"jsonrpc\":\"2.0\",\"id\":2,\"method\":\"tools/call\",\"params\":{\"name\":\"${tool}\",\"arguments\":${params}}}"
      sleep "${RESPONSE_WAIT}"
    ) | "${UV_BIN}" run --frozen --directory "${PROJECT_ROOT}" total-recall-mcp-agent 2>"${err_log}" \
      | python3 -c '
import json, sys
for line in sys.stdin:
    line = line.strip()
    if not line:
        continue
    try:
        msg = json.loads(line)
    except json.JSONDecodeError:
        continue
    if msg.get("id") == 2:
        print(json.dumps(msg.get("result", {})))
'
  ) || true
  # ^ the || true matters: with pipefail, a hard crash in the uv process
  # would otherwise trip `set -e` here and skip the diagnostics below.

  if [[ -z "${output}" ]]; then
    log_error "${name}: no response from agent within ${RESPONSE_WAIT}s"
    log_error "--- agent stderr ---"
    cat "${err_log}" >&2
    rm -f "${err_log}"
    LAST_RESULT_JSON=""
    LAST_CALL_OK=false
    return 1
  fi
  rm -f "${err_log}"

  _finish_mcp_call "${name}" "${output}"
}

mcp_call_http() {
  local name="$1" tool="$2" params="$3"

  log_step "${name}"
  log_info "tool=${tool} args=${params} endpoint=${MCP_ENDPOINT_URL}/mcp"

  local body raw
  body="{\"jsonrpc\":\"2.0\",\"id\":2,\"method\":\"tools/call\",\"params\":{\"name\":\"${tool}\",\"arguments\":${params}}}"
  raw="$(
    curl -sS -X POST --max-time "${HTTP_TIMEOUT}" "${MCP_ENDPOINT_URL}/mcp" \
      -H "Content-Type: application/json" \
      -H "Accept: application/json, text/event-stream" \
      -H "Authorization: Bearer ${TOKEN}" \
      -d "${body}"
  )" || true

  # Streamable HTTP responses are SSE ("event: message\ndata: {...}"); pull
  # the JSON-RPC result out regardless of whether it's wrapped in SSE or
  # returned as a bare JSON body.
  local output
  output=$(python3 -c '
import json, sys
raw = sys.stdin.read()
payload = None
for line in raw.splitlines():
    line = line.strip()
    if line.startswith("data:"):
        line = line[len("data:"):].strip()
    if not line:
        continue
    try:
        msg = json.loads(line)
    except json.JSONDecodeError:
        continue
    if msg.get("id") == 2:
        payload = msg.get("result", msg.get("error", {}))
if payload is not None:
    print(json.dumps(payload))
' <<<"${raw}")

  if [[ -z "${output}" ]]; then
    log_error "${name}: no usable response from ${MCP_ENDPOINT_URL}/mcp"
    log_error "--- raw response ---"
    printf '%s\n' "${raw}" >&2
    LAST_RESULT_JSON=""
    LAST_CALL_OK=false
    return 1
  fi

  _finish_mcp_call "${name}" "${output}"
}

# Shared success/error handling for both transports.
_finish_mcp_call() {
  local name="$1" output="$2"

  if [[ "${output}" == *'"isError": true'* || "${output}" == *'"isError":true'* ]]; then
    log_error "${name}: tool returned an error"
    echo "${output}" | pretty_json >&2
    LAST_RESULT_JSON="${output}"
    LAST_CALL_OK=false
    return 1
  fi

  log_ok "${name}: succeeded"
  echo "${output}" | pretty_json
  LAST_RESULT_JSON="${output}"
  LAST_CALL_OK=true
  return 0
}

# Best-effort extraction of the "id" field from a remember_memory result,
# regardless of exactly how the MCP SDK shapes structured tool output.
extract_memory_id() {
  python3 -c '
import json, re, sys
raw = sys.stdin.read()
try:
    result = json.loads(raw)
except Exception:
    print("")
    sys.exit(0)

def find_id(obj):
    if isinstance(obj, dict):
        if "id" in obj and isinstance(obj["id"], str):
            return obj["id"]
        for v in obj.values():
            found = find_id(v)
            if found:
                return found
    elif isinstance(obj, list):
        for v in obj:
            found = find_id(v)
            if found:
                return found
    elif isinstance(obj, str):
        m = re.search(
            r"[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}",
            obj,
        )
        if m:
            return m.group(0)
    return None

# content[0].text is often itself a JSON string — try to parse it too.
content = result.get("content")
if isinstance(content, list):
    for item in content:
        text = item.get("text") if isinstance(item, dict) else None
        if text:
            try:
                parsed = json.loads(text)
                found = find_id(parsed)
                if found:
                    print(found)
                    sys.exit(0)
            except Exception:
                pass

found = find_id(result)
print(found or "")
' <<<"${1}"
}

echo "=== Total Recall MCP — memory lifecycle demo (${MODE}) ==="
if [[ "${MODE}" == "cloud" ]]; then
  echo "Each MCP call below is an authenticated HTTP request to ${MCP_ENDPOINT_URL}/mcp."
else
  echo "Each MCP call below spawns a fresh stdio agent process; ${RESPONSE_WAIT}s is allowed for a reply."
fi

# ---------------------------------------------------------------------------
# 1. Remember
# ---------------------------------------------------------------------------
mcp_call "1/5 Remember a memory" "remember_memory" \
  '{"content":"User prefers dark mode","kind":"preference"}' \
  || fail "remember_memory failed — aborting demo"

memory_id="$(extract_memory_id "${LAST_RESULT_JSON}")"
if [[ -n "${memory_id}" ]]; then
  log_info "captured memory id: ${memory_id}"
else
  log_warn "could not parse a memory id from the response — forget_memory step will be skipped"
fi

# ---------------------------------------------------------------------------
# 2. Recall
# ---------------------------------------------------------------------------
mcp_call "2/5 Recall via semantic search" "recall_memory" \
  '{"query":"theme preference","kind":"preference","limit":3}' \
  || fail "recall_memory failed — aborting demo"

# ---------------------------------------------------------------------------
# 3. List
# ---------------------------------------------------------------------------
mcp_call "3/5 List memories" "list_memories" \
  '{"kind":"preference","limit":20}' \
  || log_warn "list_memories failed — continuing anyway"

# ---------------------------------------------------------------------------
# 4. Forget (best-effort — only if we captured an id)
# ---------------------------------------------------------------------------
if [[ -n "${memory_id}" ]]; then
  mcp_call "4/5 Forget the memory" "forget_memory" \
    "{\"memory_id\":\"${memory_id}\"}" \
    || log_warn "forget_memory failed — leaving the memory in place"
else
  log_step "4/5 Forget the memory"
  log_warn "skipped: no memory id available"
fi

# ---------------------------------------------------------------------------
# 5. List again — confirm deletion
# ---------------------------------------------------------------------------
if [[ -n "${memory_id}" ]]; then
  mcp_call "5/5 List memories again (confirm deletion)" "list_memories" \
    '{"kind":"preference","limit":20}' \
    || log_warn "list_memories failed — continuing anyway"
else
  log_step "5/5 List memories again (confirm deletion)"
  log_warn "skipped: forget_memory did not run"
fi

echo
echo "=== Verify in CockroachDB (optional) ==="
echo "SELECT kind, content, principal_id FROM memories ORDER BY created_at DESC LIMIT 5;"
echo "SELECT tool_name, status, principal_id FROM audit_logs ORDER BY created_at DESC LIMIT 10;"

log_ok "Demo complete (${MODE})."
