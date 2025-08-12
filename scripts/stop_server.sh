#!/bin/bash

# Stop Server Script for The Commons
# Gracefully stops the server

set -e

# Configuration
PID_FILE="backend/backend.pid"
LOG_DIR="logs"

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
RED='\033[0;31m'
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

log_error() {
    echo -e "${RED}[$(date '+%Y-%m-%d %H:%M:%S')] ERROR:${NC} $1"
}

# Ensure we're in the right directory
cd "$(dirname "$0")/.."

# Check if PID file exists
if [ ! -f "$PID_FILE" ]; then
    log_warning "No PID file found. Server may not be running."
    
    # Check if there are any uvicorn processes
    UVICORN_PIDS=$(pgrep -f "uvicorn.*backend.main:app" 2>/dev/null || true)
    if [ -n "$UVICORN_PIDS" ]; then
        log "Found uvicorn processes: $UVICORN_PIDS"
        echo "Do you want to stop these processes? (y/N)"
        read -r response
        if [[ "$response" =~ ^[Yy]$ ]]; then
            echo "$UVICORN_PIDS" | xargs kill -TERM 2>/dev/null || true
            sleep 2
            echo "$UVICORN_PIDS" | xargs kill -KILL 2>/dev/null || true
            log_success "Stopped uvicorn processes"
        fi
    else
        log "No server processes found"
    fi
    exit 0
fi

# Read PID from file
PID=$(cat "$PID_FILE")

# Check if process is running
if ! ps -p "$PID" > /dev/null 2>&1; then
    log_warning "Server process (PID: $PID) is not running"
    log "Removing stale PID file"
    rm -f "$PID_FILE"
    exit 0
fi

log "Stopping server (PID: $PID)..."

# Try graceful shutdown first
kill -TERM "$PID" 2>/dev/null || true

# Wait for graceful shutdown
for i in {1..10}; do
    if ! ps -p "$PID" > /dev/null 2>&1; then
        log_success "Server stopped gracefully"
        rm -f "$PID_FILE"
        exit 0
    fi
    sleep 1
done

# Force kill if still running
if ps -p "$PID" > /dev/null 2>&1; then
    log_warning "Server did not stop gracefully, forcing shutdown..."
    kill -KILL "$PID" 2>/dev/null || true
    sleep 1
    
    if ! ps -p "$PID" > /dev/null 2>&1; then
        log_success "Server stopped forcefully"
        rm -f "$PID_FILE"
    else
        log_error "Failed to stop server process"
        exit 1
    fi
fi

# Clean up any remaining processes
REMAINING_PIDS=$(pgrep -f "uvicorn.*backend.main:app" 2>/dev/null || true)
if [ -n "$REMAINING_PIDS" ]; then
    log_warning "Found remaining uvicorn processes: $REMAINING_PIDS"
    echo "$REMAINING_PIDS" | xargs kill -KILL 2>/dev/null || true
fi

log_success "Server shutdown complete"
