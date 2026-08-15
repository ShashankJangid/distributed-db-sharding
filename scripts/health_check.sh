#!/usr/bin/env bash
# health_check.sh — ping all registered shard containers
set -euo pipefail

SHARD_COUNT=${1:-3}
BASE_PORT=${2:-5432}
FAILED=0

echo "[health_check] Checking $SHARD_COUNT shards..."

for i in $(seq 0 $((SHARD_COUNT - 1))); do
  PORT=$((BASE_PORT + i))
  if pg_isready -h localhost -p "$PORT" -U shard_user -q; then
    echo "  ✓ shard-${i} (localhost:${PORT}) — healthy"
  else
    echo "  ✗ shard-${i} (localhost:${PORT}) — UNREACHABLE" >&2
    FAILED=$((FAILED + 1))
  fi
done

if [[ $FAILED -gt 0 ]]; then
  echo "[health_check] $FAILED shard(s) unreachable." >&2
  exit 1
fi

echo "[health_check] All shards healthy."
