#!/usr/bin/env bash

# Production System Health Check for The Commons
# 
# Usage: ./scripts/system_check.prod.sh
# 
# Environment variables (with defaults):
#   BACKEND=http://localhost:8001
#   WS_URL=ws://localhost:8001/ws
#   REDIS_HOST=localhost
#   REDIS_PORT=6379
#   POSTGRES_HOST=localhost
#   POSTGRES_PORT=5432
#   POSTGRES_DB=the_commons
#   POSTGRES_USER=postgres
#   POSTGRES_PASSWORD (optional)
#   TOKEN (optional)
#   SMOKE_USER=alice_community
#   SMOKE_PASS=password123
#   TIMEOUT=5
#
# Dependencies: curl, jq, nc
# Optional: psql, redis-cli, wscat, websocat
#
# Exit codes:
#   0: All critical checks pass
#   1: Any critical check fails

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration with defaults
BACKEND=${BACKEND:-http://localhost:8001}
WS_URL=${WS_URL:-ws://localhost:8001/ws}
REDIS_HOST=${REDIS_HOST:-localhost}
REDIS_PORT=${REDIS_PORT:-6379}
POSTGRES_HOST=${POSTGRES_HOST:-localhost}
POSTGRES_PORT=${POSTGRES_PORT:-5432}
POSTGRES_DB=${POSTGRES_DB:-the_commons}
POSTGRES_USER=${POSTGRES_USER:-postgres}
SMOKE_USER=${SMOKE_USER:-alice_community}
SMOKE_PASS=${SMOKE_PASS:-password123}
TIMEOUT=${TIMEOUT:-5}

# Extract host from BACKEND URL for port checks
BACKEND_HOST=$(echo "$BACKEND" | sed -E 's|^https?://([^:/]+).*|\1|')

# Results tracking
declare -A results
declare -A notes

# Helper functions
log() {
    echo -e "${BLUE}[$(date +'%H:%M:%S')]${NC} $1"
}

pass() {
    echo -e "${GREEN}PASS${NC} $1"
    results["$2"]="PASS"
    notes["$2"]="$1"
}

fail() {
    echo -e "${RED}FAIL${NC} $1"
    results["$2"]="FAIL"
    notes["$2"]="$1"
}

skip() {
    echo -e "${YELLOW}SKIP${NC} $1"
    results["$2"]="SKIP"
    notes["$2"]="$1"
}

mask_token() {
    local token="$1"
    if [ ${#token} -le 10 ]; then
        echo "***"
    else
        echo "${token:0:5}...${token: -5}"
    fi
}

# Create logs directory
mkdir -p ./system-check-logs

log "Starting production system health check..."

# A) System info
log "=== System Information ==="
echo "OS: $(uname -s) $(uname -r)"
echo "Bash: $(bash --version | head -n1)"
echo "Optional tools:"
[ -n "$(command -v psql)" ] && echo "  psql: found" || echo "  psql: not found"
[ -n "$(command -v redis-cli)" ] && echo "  redis-cli: found" || echo "  redis-cli: not found"
[ -n "$(command -v wscat)" ] && echo "  wscat: found" || echo "  wscat: not found"
[ -n "$(command -v websocat)" ] && echo "  websocat: found" || echo "  websocat: not found"

# B) Backend checks
log "=== Backend Health ==="

# Port check
if nc -z -w "$TIMEOUT" "$BACKEND_HOST" 8001 2>/dev/null; then
    pass "Backend port 8001 is open" "backend_port"
else
    fail "Backend port 8001 is not accessible" "backend_port"
fi

# Health endpoint
if response=$(curl -sS -m "$TIMEOUT" -w "\nHTTP_STATUS=%{http_code}\n" "$BACKEND/api/health" 2>/dev/null); then
    http_status=$(echo "$response" | grep "HTTP_STATUS=" | cut -d'=' -f2)
    body=$(echo "$response" | sed '/HTTP_STATUS=/d')
    echo "$body" > ./system-check-logs/health.json
    
    if [ "$http_status" = "200" ]; then
        pass "Health endpoint returns 200" "backend_health"
    else
        fail "Health endpoint returns $http_status" "backend_health"
    fi
else
    fail "Health endpoint request failed" "backend_health"
fi

# Docs endpoint
if response=$(curl -sS -m "$TIMEOUT" -w "\nHTTP_STATUS=%{http_code}\n" "$BACKEND/docs" 2>/dev/null); then
    http_status=$(echo "$response" | grep "HTTP_STATUS=" | cut -d'=' -f2)
    echo "HTTP_STATUS=$http_status" > ./system-check-logs/docs.http
    
    if [ "$http_status" = "200" ]; then
        pass "Docs endpoint returns 200" "backend_docs"
    else
        fail "Docs endpoint returns $http_status" "backend_docs"
    fi
else
    fail "Docs endpoint request failed" "backend_docs"
fi

# C) Postgres checks
log "=== Postgres Health ==="

if [ -n "$(command -v pg_isready)" ]; then
    if pg_isready -h "$POSTGRES_HOST" -p "$POSTGRES_PORT" -d "$POSTGRES_DB" -U "$POSTGRES_USER" >/dev/null 2>&1; then
        pass "Postgres is ready (pg_isready)" "postgres"
        
        # Optional table counts
        if [ -n "$(command -v psql)" ]; then
            if [ -n "${POSTGRES_PASSWORD:-}" ]; then
                export PGPASSWORD="$POSTGRES_PASSWORD"
            fi
            
            if user_count=$(psql -h "$POSTGRES_HOST" -p "$POSTGRES_PORT" -U "$POSTGRES_USER" -d "$POSTGRES_DB" -t -c "SELECT count(*) FROM users;" 2>/dev/null | tr -d ' '); then
                echo "  Users: $user_count"
            fi
            
            if poll_count=$(psql -h "$POSTGRES_HOST" -p "$POSTGRES_PORT" -U "$POSTGRES_USER" -d "$POSTGRES_DB" -t -c "SELECT count(*) FROM polls;" 2>/dev/null | tr -d ' '); then
                echo "  Polls: $poll_count"
            fi
        fi
    else
        fail "Postgres is not ready (pg_isready)" "postgres"
    fi
elif [ -n "$(command -v psql)" ]; then
    if [ -n "${POSTGRES_PASSWORD:-}" ]; then
        export PGPASSWORD="$POSTGRES_PASSWORD"
    fi
    
    if psql -h "$POSTGRES_HOST" -p "$POSTGRES_PORT" -U "$POSTGRES_USER" -d "$POSTGRES_DB" -c "SELECT 1;" >/dev/null 2>&1; then
        pass "Postgres is accessible (psql)" "postgres"
    else
        fail "Postgres is not accessible (psql)" "postgres"
    fi
else
    skip "No Postgres tools available" "postgres"
fi

# D) Redis checks
log "=== Redis Health ==="

if [ -n "$(command -v redis-cli)" ]; then
    if response=$(redis-cli -h "$REDIS_HOST" -p "$REDIS_PORT" ping 2>/dev/null); then
        if [ "$response" = "PONG" ]; then
            pass "Redis responds with PONG" "redis"
        else
            fail "Redis unexpected response: $response" "redis"
        fi
    else
        fail "Redis ping failed" "redis"
    fi
else
    skip "redis-cli not available" "redis"
fi

# E) Auth + core API
log "=== API Authentication & Core Endpoints ==="

# Get token if not provided
if [ -z "${TOKEN:-}" ]; then
    log "No token provided, attempting login..."
    if login_response=$(curl -sS -m "$TIMEOUT" -X POST "$BACKEND/api/token" \
        -H "Content-Type: application/x-www-form-urlencoded" \
        -d "username=$SMOKE_USER&password=$SMOKE_PASS" 2>/dev/null); then
        
        if token=$(echo "$login_response" | jq -r '.access_token // empty' 2>/dev/null); then
            if [ "$token" != "null" ] && [ -n "$token" ]; then
                TOKEN="$token"
                masked_token=$(mask_token "$token")
                pass "Login successful, token: $masked_token" "auth"
            else
                fail "Login failed: no access_token in response" "auth"
            fi
        else
            fail "Login failed: invalid JSON response" "auth"
        fi
    else
        fail "Login request failed" "auth"
    fi
else
    masked_token=$(mask_token "$TOKEN")
    pass "Using provided token: $masked_token" "auth"
fi

# Test polls endpoint
if [ -n "${TOKEN:-}" ]; then
    if response=$(curl -sS -m "$TIMEOUT" -w "\nHTTP_STATUS=%{http_code}\n" \
        -H "Authorization: Bearer $TOKEN" \
        "$BACKEND/api/polls/" 2>/dev/null); then
        
        http_status=$(echo "$response" | grep "HTTP_STATUS=" | cut -d'=' -f2)
        body=$(echo "$response" | sed '/HTTP_STATUS=/d')
        echo "$body" > ./system-check-logs/polls.json
        
        if [ "$http_status" = "200" ]; then
            pass "Polls endpoint returns 200" "api_polls"
            
            # Try to get first poll ID for detail test
            if first_poll_id=$(echo "$body" | jq -r '.[0].id // empty' 2>/dev/null); then
                if [ -n "$first_poll_id" ] && [ "$first_poll_id" != "null" ]; then
                    log "Testing poll detail with ID: $first_poll_id"
                    
                    if detail_response=$(curl -sS -m "$TIMEOUT" -w "\nHTTP_STATUS=%{http_code}\n" \
                        -H "Authorization: Bearer $TOKEN" \
                        "$BACKEND/api/polls/$first_poll_id" 2>/dev/null); then
                        
                        detail_status=$(echo "$detail_response" | grep "HTTP_STATUS=" | cut -d'=' -f2)
                        detail_body=$(echo "$detail_response" | sed '/HTTP_STATUS=/d')
                        echo "$detail_body" > ./system-check-logs/poll_detail.json
                        
                        if [ "$detail_status" = "200" ]; then
                            pass "Poll detail endpoint returns 200" "api_poll_detail"
                        else
                            fail "Poll detail endpoint returns $detail_status" "api_poll_detail"
                        fi
                    else
                        fail "Poll detail request failed" "api_poll_detail"
                    fi
                else
                    skip "No polls available for detail test" "api_poll_detail"
                fi
            else
                skip "Could not extract poll ID for detail test" "api_poll_detail"
            fi
        else
            fail "Polls endpoint returns $http_status" "api_polls"
            skip "Skipping poll detail test due to polls failure" "api_poll_detail"
        fi
    else
        fail "Polls request failed" "api_polls"
        skip "Skipping poll detail test due to polls failure" "api_poll_detail"
    fi
else
    skip "No token available for API tests" "api_polls"
    skip "No token available for API tests" "api_poll_detail"
fi

# F) WebSocket checks
log "=== WebSocket Health ==="

if [ -n "$(command -v wscat)" ]; then
    log "Testing WebSocket with wscat..."
    if timeout 10 wscat -c "$WS_URL" > ./system-check-logs/ws.txt 2>&1; then
        pass "WebSocket connection successful (wscat)" "websocket"
    else
        fail "WebSocket connection failed (wscat)" "websocket"
    fi
elif [ -n "$(command -v websocat)" ]; then
    log "Testing WebSocket with websocat..."
    if timeout 10 websocat "$WS_URL" > ./system-check-logs/ws.txt 2>&1; then
        pass "WebSocket connection successful (websocat)" "websocket"
    else
        fail "WebSocket connection failed (websocat)" "websocket"
    fi
else
    skip "No WebSocket tools available (wscat/websocat)" "websocket"
fi

# G) Summary
log "=== Summary ==="
echo "┌─────────────────────┬─────────┬─────────────────────────────────┐"
echo "│ Section             │ Status  │ Note                            │"
echo "├─────────────────────┼─────────┼─────────────────────────────────┤"

for section in "backend_port" "backend_health" "backend_docs" "postgres" "redis" "auth" "api_polls" "api_poll_detail" "websocket"; do
    status="${results[$section]:-UNKNOWN}"
    note="${notes[$section]:-No note}"
    
    case $status in
        PASS)
            status_color="${GREEN}PASS${NC}"
            ;;
        FAIL)
            status_color="${RED}FAIL${NC}"
            ;;
        SKIP)
            status_color="${YELLOW}SKIP${NC}"
            ;;
        *)
            status_color="${YELLOW}UNKNOWN${NC}"
            ;;
    esac
    
    printf "│ %-19s │ %-7s │ %-31s │\n" "$section" "$status_color" "$note"
done

echo "└─────────────────────┴─────────┴─────────────────────────────────┘"

# Determine exit code
critical_failures=0
for section in "backend_port" "backend_health" "backend_docs" "postgres" "redis"; do
    if [ "${results[$section]:-UNKNOWN}" = "FAIL" ]; then
        critical_failures=$((critical_failures + 1))
    fi
done

if [ $critical_failures -eq 0 ]; then
    log "All critical checks passed!"
    exit 0
else
    log "Critical failures detected: $critical_failures"
    exit 1
fi
