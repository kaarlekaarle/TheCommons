#!/bin/bash

# Start Server Script for The Commons
# Launches the server with monitoring and health checks

set -e

# Configuration
SERVER_PORT=8000
SERVER_HOST="0.0.0.0"
LOG_DIR="logs"
PID_FILE="backend/backend.pid"

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging function
log() {
    echo -e "${BLUE}[$(date '+%Y-%m-%d %H:%M:%S')]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[$(date '+%Y-%m-%d %H:%M:%S')] SUCCESS:${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[$(date '+%Y-%m-%d %H:%M:%S')] WARNING:${NC} $1"
}

# Ensure we're in the right directory
cd "$(dirname "$0")/.."

# Create log directory
mkdir -p "$LOG_DIR"

# Check if server is already running
if [ -f "$PID_FILE" ]; then
    PID=$(cat "$PID_FILE")
    if ps -p "$PID" > /dev/null 2>&1; then
        log_warning "Server is already running (PID: $PID)"
        echo "Use './scripts/stop_server.sh' to stop the server first"
        exit 1
    else
        log "Removing stale PID file"
        rm -f "$PID_FILE"
    fi
fi

# Check if port is already in use
if lsof -Pi :$SERVER_PORT -sTCP:LISTEN -t >/dev/null 2>&1; then
    log_warning "Port $SERVER_PORT is already in use"
    echo "Please stop the process using port $SERVER_PORT or change the port"
    exit 1
fi

# Check Python environment
if ! command -v python &> /dev/null; then
    log_warning "Python not found in PATH"
    echo "Please ensure Python is installed and in your PATH"
    exit 1
fi

# Check if virtual environment is activated
if [[ "$VIRTUAL_ENV" == "" ]]; then
    log_warning "Virtual environment not detected"
    echo "Consider activating your virtual environment for better dependency management"
fi

# Check required dependencies
log "Checking dependencies..."
python -c "import uvicorn, fastapi, sqlalchemy" 2>/dev/null || {
    log_warning "Missing required dependencies"
    echo "Please install dependencies: pip install -r requirements.txt"
    exit 1
}

# Start server
log "Starting The Commons server..."
log "Server will be available at: http://localhost:$SERVER_PORT"
log "Health check: http://localhost:$SERVER_PORT/health"
log "API docs: http://localhost:$SERVER_PORT/docs"

# Start server in background with monitoring
python -m uvicorn backend.main:app \
    --host "$SERVER_HOST" \
    --port "$SERVER_PORT" \
    --reload \
    --log-level info \
    --access-log \
    > "$LOG_DIR/server.log" 2>&1 &

SERVER_PID=$!

# Save PID
echo "$SERVER_PID" > "$PID_FILE"

# Wait for server to start
log "Waiting for server to start..."
for i in {1..30}; do
    if curl -s "http://localhost:$SERVER_PORT/api/health" > /dev/null 2>&1; then
        log_success "Server started successfully (PID: $SERVER_PID)"
        log_success "Server is running at http://localhost:$SERVER_PORT"
        log_success "Press Ctrl+C to stop the server"
        
        # Show server logs
        echo ""
        log "Server logs (last 10 lines):"
        tail -n 10 "$LOG_DIR/server.log"
        echo ""
        
        # Wait for user interrupt
        trap 'echo ""; log "Stopping server..."; kill $SERVER_PID 2>/dev/null || true; rm -f "$PID_FILE"; log_success "Server stopped"; exit 0' INT
        
        # Monitor server
        while kill -0 "$SERVER_PID" 2>/dev/null; do
            sleep 1
        done
        
        log_warning "Server process ended unexpectedly"
        rm -f "$PID_FILE"
        exit 1
    fi
    sleep 1
done

log_warning "Server failed to start within 30 seconds"
kill "$SERVER_PID" 2>/dev/null || true
rm -f "$PID_FILE"

# Show error logs
echo ""
log "Server startup failed. Last 20 lines of server log:"
tail -n 20 "$LOG_DIR/server.log"
echo ""

exit 1
