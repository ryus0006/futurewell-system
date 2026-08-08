#!/bin/bash

# Start local development environment for futurewell-system (the backend).
# Brings up MySQL in Docker, loads the schema + seed, then runs the FastAPI app.
# Mirrors gas-rag-system/scripts/local-start.sh.

set -e

# Run from the backend project root regardless of where this is invoked.
BACKEND_DIR="$(cd "$(dirname "$0")/.." && pwd)"
cd "$BACKEND_DIR"

echo "Starting local development environment..."

# Check if docker is running
if ! docker info > /dev/null 2>&1; then
    echo "Error: Docker is not running. Please start Docker first."
    exit 1
fi

# Start MySQL and Adminer
echo "Starting MySQL and Adminer..."
docker compose -f docker-compose.local.yml up -d

# Wait for MySQL to accept connections
echo "Waiting for MySQL to be ready..."
until docker exec onboarding-mysql-local \
    mysqladmin ping -h localhost -papppass --silent > /dev/null 2>&1; do
    sleep 2
done

# Load schema + seed. The import is idempotent (DROP/CREATE/INSERT), so this
# refreshes the reference tables to a known state on every start.
echo "Loading schema and seed data..."
docker exec -i onboarding-mysql-local \
    mysql -uappuser -papppass appdb < db/futurewell_erd_data_import.sql

echo ""
echo "=========================================="
echo "Local environment is ready!"
echo "=========================================="
echo ""
echo "MySQL:   localhost:3306  (database: appdb, user: appuser, password: apppass)"
echo "Adminer (DB Browser): http://localhost:8082"
echo ""
echo "To stop the environment:"
echo "  ./scripts/local-stop.sh"
echo ""
echo "Starting application..."
echo ""

# Tee uvicorn output to var/local-app.log for the current session.
LOG_DIR="${BACKEND_DIR}/var"
LOG_FILE="${LOG_DIR}/local-app.log"
mkdir -p "$LOG_DIR"
: > "$LOG_FILE"
echo "App log: $LOG_FILE"
echo ""

# Run the app. Uses the local default DATABASE_URL (localhost:3306). Set
# GEMINI_API_KEY in your shell first to enable Gemini guidance.
bash ./docker-cmd.sh 2>&1 | tee "$LOG_FILE"
