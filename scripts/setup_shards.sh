#!/usr/bin/env bash
# setup_shards.sh — provision N PostgreSQL shard databases
set -euo pipefail

SHARD_COUNT=${1:-3}
BASE_PORT=${2:-5432}
DB_NAME=${DB_NAME:-sharddb}

echo "[setup_shards] Provisioning $SHARD_COUNT shards starting at port $BASE_PORT"

for i in $(seq 0 $((SHARD_COUNT - 1))); do
  PORT=$((BASE_PORT + i))
  CONTAINER="shard-${i}"
  echo "  → Starting $CONTAINER on port $PORT"
  docker run -d \
    --name "$CONTAINER" \
    -e POSTGRES_DB="$DB_NAME" \
    -e POSTGRES_USER=shard_user \
    -e POSTGRES_PASSWORD=shard_pass \
    -p "${PORT}:5432" \
    postgres:16-alpine
done

echo "[setup_shards] Done. Waiting 5s for Postgres to initialize..."
sleep 5

for i in $(seq 0 $((SHARD_COUNT - 1))); do
  PORT=$((BASE_PORT + i))
  echo "  ✓ shard-${i} listening on localhost:${PORT}"
done
