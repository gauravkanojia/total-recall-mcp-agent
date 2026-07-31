#!/usr/bin/env bash
# Resilience demo: memory survives the loss of a CockroachDB node.
#
# Self-contained — starts the stack and migrates the schema itself. Only
# requirement: podman + uv installed, and this repo's Python deps synced
# (`uv sync`).
#
# What it does:
#   1. start the 3-node compose cluster + agent, apply Alembic migrations
#   2. remember a memory via MCP (stdio, DB = roach1)
#   3. stop roach3 — one of three nodes is now dead
#   4. recall the memory — still there (3x replication, quorum of 2)
#   5. restart roach3, then tear the whole stack down
set -euo pipefail

export PODMAN_COMPOSE_WARNING_LOGS=false
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
UV_BIN="${UV_BIN:-$(command -v uv)}"
COMPOSE="podman compose"

if [[ -z "${UV_BIN}" ]]; then
  echo "uv not found in PATH" >&2
  exit 1
fi

if ! command -v podman >/dev/null 2>&1; then
  echo "podman not found in PATH" >&2
  exit 1
fi

mcp_call() {
  # Run one MCP tools/call through the stdio agent; print the JSON-RPC reply
  # for the call (id=2). Each invocation boots a fresh agent process (cold
  # DB connection + embedding), so sleeps are generous. On empty output,
  # dumps the agent's stderr so failures are diagnosable instead of silent.
  local tool_json="$1"
  local err_log
  err_log="$(mktemp)"

  local output
  output=$(
    (
      echo '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"resilience-demo","version":"1.0"}}}'
      sleep 1
      echo '{"jsonrpc":"2.0","method":"notifications/initialized"}'
      sleep 1
      echo "${tool_json}"
      sleep 4
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
        print(json.dumps(msg.get("result", msg), indent=2))
'
  ) || true
  # ^ the || true matters: with pipefail, a hard crash in the uv process
  # (not just "no id=2 reply") would otherwise trip `set -e` right here and
  # skip the diagnostic branch below entirely.

  if [[ -z "${output}" ]]; then
    echo "(no MCP response received — agent stderr follows)" >&2
    cat "${err_log}" >&2
  else
    echo "${output}"
  fi
  rm -f "${err_log}"
}

echo "=== Step 1/7: Start the DB cluster and MCP Agent ==="
${COMPOSE} up -d

echo
echo "=== Step 2/7: Applying schema migrations (safe to re-run; no-op if already current)..."
# On a fresh cluster, roach-init is still creating the database when
# `compose up -d` returns, so the first attempt or two can race it.
migrated=false
for attempt in 1 2 3 4 5; do
  if (cd "${PROJECT_ROOT}" && "${UV_BIN}" run alembic upgrade head); then
    migrated=true
    break
  fi
  echo "(migration attempt ${attempt}/5 failed — database may still be initializing; retrying in 3s)"
  sleep 3
done
if [[ "${migrated}" != true ]]; then
  echo "Could not apply migrations after 5 attempts. Check 'podman compose logs roach-init'." >&2
  exit 1
fi

echo
echo "=== Step 3/7: Remember/Persist a Memory (cluster healthy, 3/3 nodes) ==="
mcp_call '{"jsonrpc":"2.0","id":2,"method":"tools/call","params":{"name":"remember_memory","arguments":{"content":"Resilience check: the answer is 42","kind":"fact"}}}'

echo
echo "=== Step 4/7: Killing one DB node: [roach3] ==="
${COMPOSE} stop roach3
# Safety net: if anything below fails before Step 5 explicitly restarts
# roach3 (including a hard script abort), make a best-effort attempt to
# bring it back so a mid-demo error doesn't leave the cluster degraded.
# Cleared right before the intentional final teardown.
trap '${COMPOSE} up -d roach3 >/dev/null 2>&1 || true' EXIT
echo "Cluster is now running on 2 of 3 nodes."
echo "Letting Raft re-elect leaders / transfer leases for ranges roach3 led..."
sleep 5

echo
echo "=== Step 5/7: Memory Recall with one DB node down ==="
recall_ok=false
for attempt in 1 2 3; do
  result="$(mcp_call '{"jsonrpc":"2.0","id":2,"method":"tools/call","params":{"name":"recall_memory","arguments":{"query":"Resilience check: the answer is 42","kind":"fact","limit":3}}}')"
  echo "${result}"
  if [[ -n "${result}" && "${result}" != *'"isError": true'* ]]; then
    recall_ok=true
    break
  fi
  echo "(attempt ${attempt}/3 didn't return cleanly yet — cluster may still be settling; retrying)"
  sleep 3
done

echo
if [[ "${recall_ok}" == true ]]; then
  echo ">>> Memory survived the node failure. This is the point. <<<"
else
  echo ">>> Recall did not return cleanly after retries — see output/stderr above. <<<"
fi

echo
echo "=== Step 6/7: Restarting roach3 ==="
${COMPOSE} up -d roach3
trap - EXIT
echo "Cluster healed. Done."

echo
echo "=== Step 7/7: Cleanup - Tear Down Cluster ==="
echo "(This stops every container — cluster, agent, everything. Comment this"
echo " line out if you want the stack to stay up for other demo segments.)"
${COMPOSE} down
