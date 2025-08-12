#!/bin/bash

# Server Monitor Script for The Commons
# Automatically restarts the server if it crashes

set -e

# Configuration
SERVER_PORT=8000
SERVER_HOST="0.0.0.0"
LOG_FILE="logs/server_monitor.log"
PID_FILE="backend/backend.pid"
MAX_RESTARTS=10
RESTART_COOLDOWN=30  # seconds
HEALTH_CHECK_INTERVAL=30  # seconds

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging function
log() {
    echo -e "${BLUE}[$(date '+%Y-%m-%d %H:%M:%S')]${NC} $1" | tee -a "$LOG_FILE"
}

log_error() {
    echo -e "${RED}[$(date '+%Y-%m-%d %H:%M:%S')] ERROR:${NC} $1" | tee -a "$LOG_FILE"
}

log_warning() {
    echo -e "${YELLOW}[$(date '+%Y-%m-%d %H:%M:%S')] WARNING:${NC} $1" | tee -a "$LOG_FILE"
}

log_success() {
    echo -e "${GREEN}[$(date '+%Y-%m-%d %H:%M:%S')] SUCCESS:${NC} $1" | tee -a "$LOG_FILE"
}

# Ensure log directory exists
mkdir -p logs

# Initialize restart counter
restart_count=0
last_restart_time=0

# Function to check if server is running
is_server_running() {
    if [ -f "$PID_FILE" ]; then
        local pid=$(cat "$PID_FILE")
        if ps -p "$pid" > /dev/null 2>&1; then
            return 0
        fi
    fi
    return 1
}

# Function to check server health
check_server_health() {
    local response
    response=$(curl -s -o /dev/null -w "%{http_code}" "http://localhost:$SERVER_PORT/health" 2>/dev/null || echo "000")
    
    if [ "$response" = "200" ]; then
        return 0
    else
        return 1
    fi
}

# Function to start server
start_server() {
    log "Starting server..."
    
    # Kill any existing server process
    if [ -f "$PID_FILE" ]; then
        local pid=$(cat "$PID_FILE")
        if ps -p "$pid" > /dev/null 2>&1; then
            log "Killing existing server process (PID: $pid)"
            kill "$pid" 2>/dev/null || true
            sleep 2
        fi
    fi
    
    # Start server in background
    cd "$(dirname "$0")/.."
    python -m uvicorn backend.main:app --host "$SERVER_HOST" --port "$SERVER_PORT" --reload > logs/server.log 2>&1 &
    local server_pid=$!
    
    # Save PID
    echo "$server_pid" > "$PID_FILE"
    
    # Wait for server to start
    local attempts=0
    while [ $attempts -lt 30 ]; do
        if check_server_health; then
            log_success "Server started successfully (PID: $server_pid)"
            return 0
        fi
        sleep 1
        attempts=$((attempts + 1))
    done
    
    log_error "Server failed to start within 30 seconds"
    return 1
}

# Function to stop server
stop_server() {
    log "Stopping server..."
    
    if [ -f "$PID_FILE" ]; then
        local pid=$(cat "$PID_FILE")
        if ps -p "$pid" > /dev/null 2>&1; then
            kill "$pid" 2>/dev/null || true
            sleep 2
            # Force kill if still running
            if ps -p "$pid" > /dev/null 2>&1; then
                kill -9 "$pid" 2>/dev/null || true
            fi
        fi
        rm -f "$PID_FILE"
    fi
    
    log_success "Server stopped"
}

# Function to restart server
restart_server() {
    local current_time=$(date +%s)
    
    # Check restart cooldown
    if [ $((current_time - last_restart_time)) -lt $RESTART_COOLDOWN ]; then
        log_warning "Restart cooldown active, waiting..."
        sleep $RESTART_COOLDOWN
    fi
    
    # Check max restarts
    if [ $restart_count -ge $MAX_RESTARTS ]; then
        log_error "Maximum restart attempts ($MAX_RESTARTS) reached. Stopping monitor."
        exit 1
    fi
    
    restart_count=$((restart_count + 1))
    last_restart_time=$current_time
    
    log_warning "Restarting server (attempt $restart_count/$MAX_RESTARTS)"
    
    stop_server
    sleep 2
    
    if start_server; then
        restart_count=0  # Reset counter on successful start
        log_success "Server restarted successfully"
    else
        log_error "Server restart failed"
    fi
}

# Signal handlers
cleanup() {
    log "Shutting down server monitor..."
    stop_server
    exit 0
}

trap cleanup SIGINT SIGTERM

# Main monitoring loop
main() {
    log "Starting server monitor..."
    log "Server port: $SERVER_PORT"
    log "Health check interval: ${HEALTH_CHECK_INTERVAL}s"
    log "Max restarts: $MAX_RESTARTS"
    log "Restart cooldown: ${RESTART_COOLDOWN}s"
    
    # Start server initially
    if ! start_server; then
        log_error "Failed to start server initially"
        exit 1
    fi
    
    log_success "Server monitor started successfully"
    
    # Monitoring loop
    while true; do
        sleep $HEALTH_CHECK_INTERVAL
        
        if ! is_server_running; then
            log_error "Server process not running"
            restart_server
            continue
        fi
        
        if ! check_server_health; then
            log_error "Server health check failed"
            restart_server
            continue
        fi
        
        # Reset restart count if server is healthy for a while
        if [ $restart_count -gt 0 ]; then
            log "Server is healthy, resetting restart counter"
            restart_count=0
        fi
    done
}

# Run main function
main "$@"
