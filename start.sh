#!/bin/bash

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}Starting AIToday...${NC}"

# Get the directory where the script is located
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

# Start Backend
echo -e "${GREEN}Starting Backend (Port 8000)...${NC}"
cd "$DIR/backend"
# Check if virtual environment exists, activate if so (optional, assuming user environment)
# source venv/bin/activate 2>/dev/null 
nohup uvicorn app.main:app --reload --port 8000 > "$DIR/backend.log" 2>&1 &
BACKEND_PID=$!
echo "Backend started with PID: $BACKEND_PID"

# Start Frontend
echo -e "${GREEN}Starting Frontend (Port 3000)...${NC}"
cd "$DIR/frontend"
nohup npm run dev > "$DIR/frontend.log" 2>&1 &
FRONTEND_PID=$!
echo "Frontend started with PID: $FRONTEND_PID"

echo -e "${BLUE}AIToday is running!${NC}"
echo "Backend logs: $DIR/backend.log"
echo "Frontend logs: $DIR/frontend.log"
echo "To stop the servers, run ./stop.sh"
