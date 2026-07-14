#!/usr/bin/env bash
# End-to-end semantic memory demo over MCP stdio.
set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
UV_BIN="${UV_BIN:-$(command -v uv)}"

if [[ -z "${UV_BIN}" ]]; then
  echo "uv not found in PATH" >&2
  exit 1
fi

echo "=== Total Recall memory demo (MCP stdio) ==="

(
  echo '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"demo","version":"1.0"}}}'
  sleep 0.5
  echo '{"jsonrpc":"2.0","method":"notifications/initialized"}'
  sleep 0.5
  echo '{"jsonrpc":"2.0","id":2,"method":"tools/call","params":{"name":"remember_memory","arguments":{"content":"User prefers dark mode","kind":"preference"}}}'
  sleep 0.5
  echo '{"jsonrpc":"2.0","id":3,"method":"tools/call","params":{"name":"recall_memory","arguments":{"query":"theme preference","kind":"preference","limit":3}}}'
  sleep 1
) | "${UV_BIN}" run --frozen --directory "${PROJECT_ROOT}" total-recall-mcp-agent 2>/dev/null

echo
echo "=== Verify in CockroachDB (optional) ==="
echo "SELECT kind, content FROM memories ORDER BY created_at DESC LIMIT 5;"
