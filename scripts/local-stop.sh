#!/bin/bash

# Stop the local development environment and reset the database.
# Mirrors gas-rag-system/scripts/local-stop.sh.

BACKEND_DIR="$(cd "$(dirname "$0")/.." && pwd)"
cd "$BACKEND_DIR"

echo "Stopping local development environment..."

# Stop containers and remove volumes (drops the local DB data).
docker compose -f docker-compose.local.yml down -v --remove-orphans

echo "Local environment stopped (database reset)."
