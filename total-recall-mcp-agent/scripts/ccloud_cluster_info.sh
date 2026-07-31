#!/usr/bin/env bash
# Query CockroachDB Cloud cluster metadata via the agent-ready ccloud CLI (JSON output).
# Requires: ccloud CLI installed and authenticated (`ccloud auth login`).
#
# Usage:
#   ./scripts/ccloud_cluster_info.sh <cluster-name>
#   CCLOUD_CLUSTER_NAME=my-cluster ./scripts/ccloud_cluster_info.sh
set -euo pipefail

if ! command -v ccloud >/dev/null 2>&1; then
  echo "ccloud CLI not found." >&2
  echo "Install: https://www.cockroachlabs.com/docs/cockroachcloud/ccloud-get-started" >&2
  echo "Or: brew install cockroachdb/tap/ccloud" >&2
  exit 1
fi

CLUSTER_NAME="${1:-${CCLOUD_CLUSTER_NAME:-}}"

if [[ -z "${CLUSTER_NAME}" ]]; then
  cat >&2 <<'EOF'
USAGE:
    $0 <cluster-name>
    
    e.g. 
      - ccloud_cluster_info.sh my-cluster-1
      - ccloud_cluster_info.sh my-cluster-2

    Cluster name is required.

    Set up a CockroachDB Cloud cluster first:
      1. Create a cluster: https://cockroachlabs.cloud
      2. Authenticate the CLI: ccloud auth login
      3. Note your cluster name from: ccloud cluster list

    Then run this script with the cluster name:
      cloud_cluster_info.sh <cluster-name>

    Or set CCLOUD_CLUSTER_NAME in your environment/.env:
      export CCLOUD_CLUSTER_NAME=<cluster-name>
      ccloud_cluster_info.sh
EOF
  exit 1
fi

echo "=== ccloud organization info ==="
ccloud organization get --output json

echo ""
echo "=== ccloud cluster info: ${CLUSTER_NAME} ==="
ccloud cluster get "${CLUSTER_NAME}" --output json
echo ""
