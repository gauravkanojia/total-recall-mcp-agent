#!/usr/bin/env bash
# Cursor MCP stdio launcher. Resolves project root from this script's location.
set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
UV_BIN="${UV_BIN:-$(command -v uv)}"

if [[ -z "${UV_BIN}" ]]; then
  echo "uv not found in PATH" >&2
  exit 1
fi

exec "${UV_BIN}" run --frozen --directory "${PROJECT_ROOT}" total-recall-mcp-agent
