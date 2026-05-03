#!/usr/bin/env bash

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
REPO_ROOT="$SCRIPT_DIR/.."
AGENCIES_DIR="$REPO_ROOT/option3_perception_actuation"

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${GREEN}=== Task 3.1 Demo: LISTENER with Fallback and Recovery ===${NC}"
echo ""
echo -e "${YELLOW}Stopping any stale demo processes...${NC}"
pkill -f "uvicorn agencies.agency_a:app" 2>/dev/null || true
pkill -f "uvicorn agencies.agency_b:app" 2>/dev/null || true
pkill -f "python listener_demo.py" 2>/dev/null || true
rm -f /tmp/agency_a.pid /tmp/agency_b.pid

echo -e "${YELLOW}Clearing Python cache to ensure fresh imports...${NC}"

# Remove all __pycache__ directories and .pyc files to ensure fresh module imports
find "$AGENCIES_DIR" -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
find "$AGENCIES_DIR" -type f -name "*.pyc" -delete 2>/dev/null || true

echo -e "${YELLOW}Starting services...${NC}"
echo ""

mkdir -p "$REPO_ROOT/data"

echo -e "${GREEN}Starting Agency A on http://127.0.0.1:8001${NC}"
(cd "$AGENCIES_DIR" && uvicorn agencies.agency_a:app --host 127.0.0.1 --port 8001 --log-level info) > /tmp/agency_a.log 2>&1 &
AGENCY_A_PID=$!
sleep 1

echo -e "${GREEN}Starting Agency B on http://127.0.0.1:8002${NC}"
(cd "$AGENCIES_DIR" && uvicorn agencies.agency_b:app --host 127.0.0.1 --port 8002 --log-level info) > /tmp/agency_b.log 2>&1 &
AGENCY_B_PID=$!
sleep 1

echo -e "${GREEN}Starting LISTENER on http://127.0.0.1:8000${NC}"
echo ""
echo -e "${YELLOW}Logs from LISTENER below (Agency logs in /tmp/agency_*.log):${NC}"
echo ""
echo -e "${YELLOW}Demo commands (run in separate terminal):${NC}"
echo -e "  curl http://127.0.0.1:8000/health"
echo -e "  curl -X POST http://127.0.0.1:8000/pull_now"
echo -e "  make stop_agency_a    # Trigger fallback to B"
echo -e "  make start_agency_a   # Trigger recovery"
echo ""

cleanup() {
    echo ""
    echo -e "${RED}Shutting down...${NC}"
    kill $AGENCY_A_PID 2>/dev/null || true
    kill $AGENCY_B_PID 2>/dev/null || true
    sleep 1
    echo -e "${GREEN}Demo stopped.${NC}"
    exit 0
}

trap cleanup INT TERM

cd "$AGENCIES_DIR"
python listener_demo.py