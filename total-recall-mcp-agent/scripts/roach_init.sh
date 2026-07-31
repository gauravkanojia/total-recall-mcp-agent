#!/usr/bin/env bash
# Runs inside the roach-init container (see docker-compose.yml).
#
# 1. Wait for roach1 to accept SQL connections (nodes take a few seconds).
# 2. Initialize the cluster — idempotent, 'already initialized' is expected
#    and ignored on restarts.
# 3. Create the application database — idempotent via IF NOT EXISTS — so
#    Alembic has somewhere to migrate.
set -uo pipefail

CRDB="/cockroach/cockroach"
HOST="roach1:26257"

echo "Waiting for roach1 to accept SQL connections..."
for i in $(seq 1 30); do
  if "${CRDB}" sql --insecure --host="${HOST}" -e "SELECT 1" >/dev/null 2>&1; then
    break
  fi
  echo "  ($i/30) not ready yet..."
  sleep 1
done

echo "Initializing cluster (safe to ignore 'already initialized')..."
"${CRDB}" init --insecure --host="${HOST}" || true

echo "Ensuring database total_recall_mcp_db exists..."
for i in $(seq 1 30); do
  if "${CRDB}" sql --insecure --host="${HOST}" \
    -e "CREATE DATABASE IF NOT EXISTS total_recall_mcp_db"; then
    echo "Done."
    exit 0
  fi
  echo "  ($i/30) cluster not accepting SQL yet..."
  sleep 1
done

echo "Failed to create database after 30 attempts." >&2
exit 1
