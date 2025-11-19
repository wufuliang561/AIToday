#!/bin/bash

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
NC='\033[0m' # No Color

echo -e "${RED}Stopping AIToday...${NC}"

# Find and kill Backend (uvicorn)
# We look for uvicorn running app.main:app
BACKEND_PIDS=$(ps aux | grep "uvicorn app.main:app" | grep -v grep | awk '{print $2}')

if [ -n "$BACKEND_PIDS" ]; then
    echo -e "${RED}Killing Backend processes: $BACKEND_PIDS${NC}"
    kill $BACKEND_PIDS
else
    echo "No Backend process found."
fi

# Find and kill Frontend (next dev)
# We look for next-server or node running next
# This is a bit trickier, usually it's a node process.
# We can look for the process started by npm run dev, but that spawns children.
# A safer bet for dev environment is looking for the port 3000 user
FRONTEND_PIDS=$(lsof -t -i:3000)

if [ -n "$FRONTEND_PIDS" ]; then
    echo -e "${RED}Killing Frontend processes (Port 3000): $FRONTEND_PIDS${NC}"
    kill $FRONTEND_PIDS
else
    echo "No Frontend process found on port 3000."
fi

echo -e "${GREEN}AIToday stopped.${NC}"
