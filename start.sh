#!/usr/bin/env bash
set -euo pipefail

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${BLUE}Starting AIToday...${NC}"

# Get the directory where the script is located
ROOT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

# Config file (YAML) for backend to load; allow override via first arg or env.
# Fallback order: CLI arg -> env -> ./sources.yaml -> ./backend/sources.yaml
if [[ -n "${1:-}" ]]; then
  CONFIG_FILE="$1"
elif [[ -n "${SOURCES_CONFIG_PATH:-}" ]]; then
  CONFIG_FILE="$SOURCES_CONFIG_PATH"
elif [[ -f "$ROOT_DIR/sources.yaml" ]]; then
  CONFIG_FILE="$ROOT_DIR/sources.yaml"
elif [[ -f "$ROOT_DIR/backend/sources.yaml" ]]; then
  CONFIG_FILE="$ROOT_DIR/backend/sources.yaml"
else
  CONFIG_FILE=""
fi

if [[ -z "$CONFIG_FILE" || ! -f "$CONFIG_FILE" ]]; then
  echo -e "${RED}Config file not found. Provide a path (./start.sh <config>) or place sources.yaml at repo root/backend.${NC}"
  exit 1
fi
export SOURCES_CONFIG_PATH="$CONFIG_FILE"
echo "Using config: $SOURCES_CONFIG_PATH"

# Activate virtual environment if present
if [[ -d "$ROOT_DIR/.venv" ]]; then
  # shellcheck source=/dev/null
  source "$ROOT_DIR/.venv/bin/activate"
  echo "Activated virtualenv at $ROOT_DIR/.venv"
else
  echo -e "${RED}Warning: .venv not found; using system Python/Node${NC}"
fi

# Start Backend
echo -e "${GREEN}Starting Backend (Port 8000)...${NC}"
cd "$ROOT_DIR/backend"
nohup uvicorn app.main:app --reload --port 8000 > "$ROOT_DIR/backend.log" 2>&1 &
BACKEND_PID=$!
echo "Backend started with PID: $BACKEND_PID"

# Start Frontend
echo -e "${GREEN}Starting Frontend (Port 3000)...${NC}"
cd "$ROOT_DIR/frontend"
nohup npm run dev > "$ROOT_DIR/frontend.log" 2>&1 &
FRONTEND_PID=$!
echo "Frontend started with PID: $FRONTEND_PID"

echo -e "${BLUE}AIToday is running!${NC}"
echo "Backend logs: $ROOT_DIR/backend.log"
echo "Frontend logs: $ROOT_DIR/frontend.log"
echo "To stop the servers, run ./stop.sh"
