#!/usr/bin/env bash
# Get a GitHub bearer token for testing Total Recall MCP's HTTP auth.
#
# HTTP_AUTH_MODE=github validates the token via GET /user and derives the
# caller's principal from the login — no GitHub permissions are needed for
# that check. This script drives a browser-based GitHub login via the
# GitHub CLI's own OAuth app and prints the resulting token.
#
# NOTE: this issues a token with gh's standard OAuth scopes (repo,
# read:org, gist, workflow) — the GitHub CLI doesn't support requesting an
# empty scope set. That's broader than the zero-scope fine-grained PAT
# recommended in README.md "Authentication & security" for this exact
# purpose, though it still works fine for the identity check the agent
# does. Treat the printed token like any credential: don't commit or share
# it, and revoke it afterward at https://github.com/settings/tokens if you
# want a clean slate. For a token that truly can't do anything beyond
# prove identity, create a fine-grained PAT with zero permissions by hand
# instead (see README.md).
#
# Usage:
#   ./scripts/get_github_token.sh                # opens a browser to sign in if needed
#   TOKEN=$(./scripts/get_github_token.sh)        # capture just the token
set -euo pipefail

if ! command -v gh >/dev/null 2>&1; then
  echo "GitHub CLI (gh) not found. Install it: https://cli.github.com" >&2
  exit 1
fi

if ! gh auth status >/dev/null 2>&1; then
  echo "Opening a browser to sign in to GitHub..." >&2
  gh auth login --hostname github.com --git-protocol https --web
fi

TOKEN="$(gh auth token)"

{
  echo "=== GitHub bearer token (use as: Authorization: Bearer <token>) ==="
  echo
  echo "Example:"
  echo "  curl -s \$MCP_ENDPOINT_URL/mcp \\"
  echo "    -H 'Content-Type: application/json' \\"
  echo "    -H 'Accept: application/json, text/event-stream' \\"
  echo "    -H \"Authorization: Bearer \${TOKEN}\" \\"
  echo "    -d '{\"jsonrpc\":\"2.0\",\"id\":1,\"method\":\"tools/list\",\"params\":{}}'"
  echo
} >&2

echo "${TOKEN}"
