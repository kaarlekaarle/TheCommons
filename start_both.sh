#!/bin/bash

# Start Both Servers Script
# Starts backend and frontend servers

set -e

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}Starting The Commons servers...${NC}"

# Check if backend is already running
if curl -s http://localhost:8000/api/health > /dev/null 2>&1; then
    echo -e "${GREEN}✓ Backend is already running${NC}"
else
    echo -e "${BLUE}Starting backend...${NC}"
    ./scripts/start_server.sh &
    sleep 5
fi

# Start frontend
echo -e "${BLUE}Starting frontend...${NC}"
cd frontend
npm run dev &
FRONTEND_PID=$!

# Wait for frontend to start
sleep 5

# Check if both servers are running
echo -e "${BLUE}Checking server status...${NC}"

if curl -s http://localhost:8000/api/health > /dev/null 2>&1; then
    echo -e "${GREEN}✓ Backend is running at http://localhost:8000${NC}"
else
    echo -e "${RED}✗ Backend is not responding${NC}"
fi

if curl -s http://localhost:5173/ > /dev/null 2>&1; then
    echo -e "${GREEN}✓ Frontend is running at http://localhost:5173${NC}"
else
    echo -e "${RED}✗ Frontend is not responding${NC}"
fi

echo -e "${BLUE}Servers started!${NC}"
echo -e "${BLUE}Frontend: http://localhost:5173${NC}"
echo -e "${BLUE}Backend: http://localhost:8000${NC}"
echo -e "${BLUE}API Docs: http://localhost:8000/docs${NC}"

# Keep script running
wait $FRONTEND_PID
