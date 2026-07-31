#!/usr/bin/env bash
# Install CockroachDB Agent Skills from the open-source skills ecosystem.
# Source: https://github.com/cockroachlabs/cockroachdb-skills
#
# Installs a curated subset into .agents/skills/ for Cursor (via npx skills CLI).
#
# Usage:
#   ./scripts/install_cockroachdb_skills.sh          # curated skills for this project
#   ./scripts/install_cockroachdb_skills.sh --all    # all 34 upstream skills
set -euo pipefail

REPO="cockroachlabs/cockroachdb-skills"
AGENT="cursor"

if ! command -v npx >/dev/null 2>&1; then
  echo "npx not found. Install Node.js 18+: https://nodejs.org/" >&2
  exit 1
fi

if [[ "${1:-}" == "--all" ]]; then
  echo "Installing all CockroachDB Agent Skills..."
  npx skills add "${REPO}" --agent "${AGENT}" --skill '*' --yes
  exit 0
fi

echo "Installing curated CockroachDB Agent Skills for Total Recall MCP..."
npx skills add "${REPO}" --agent "${AGENT}" --yes \
  --skill cockroachdb-sql \
  --skill setting-up-local-cluster \
  --skill reviewing-cluster-health \
  --skill designing-application-transactions \
  --skill configuring-audit-logging

echo
echo "Project skill: .agents/skills/total-recall-agentic-memory/ (committed with repo)"
echo "Upstream skills: https://github.com/cockroachlabs/cockroachdb-skills"
