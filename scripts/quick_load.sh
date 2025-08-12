#!/usr/bin/env bash

# Quick Load Test for The Commons Production Endpoints
# 
# Usage: ./scripts/quick_load.sh
# 
# Environment variables (with defaults):
#   BACKEND=http://localhost:8001
#   TOKEN (optional)
#   SMOKE_USER=alice_community
#   SMOKE_PASS=password123
#   CONCURRENCY=20
#   REQUESTS=100
#   ENDPOINTS="/api/activity/ /api/polls/"
#   THRESHOLD_P95_MS=800
#
# Dependencies: curl, jq
# Optional: GNU parallel or xargs -P
#
# Exit codes:
#   0: All endpoints under threshold
#   1: Any endpoint exceeds threshold

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration with defaults
BACKEND=${BACKEND:-http://localhost:8001}
SMOKE_USER=${SMOKE_USER:-alice_community}
SMOKE_PASS=${SMOKE_PASS:-password123}
CONCURRENCY=${CONCURRENCY:-20}
REQUESTS=${REQUESTS:-100}
ENDPOINTS=${ENDPOINTS:-"/api/activity/ /api/polls/"}
THRESHOLD_P95_MS=${THRESHOLD_P95_MS:-800}

# Results tracking
declare -A results
declare -A p50_times
declare -A p95_times

# Helper functions
log() {
    echo -e "${BLUE}[$(date +'%H:%M:%S')]${NC} $1"
}

pass() {
    echo -e "${GREEN}PASS${NC} $1"
    results["$2"]="PASS"
}

fail() {
    echo -e "${RED}FAIL${NC} $1"
    results["$2"]="FAIL"
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

log "Starting quick load test..."

# Check dependencies
if ! command -v curl >/dev/null 2>&1; then
    echo "ERROR: curl is required but not installed" >&2
    exit 1
fi

if ! command -v jq >/dev/null 2>&1; then
    echo "ERROR: jq is required but not installed" >&2
    exit 1
fi

# Get token if not provided
if [ -z "${TOKEN:-}" ]; then
    log "No token provided, attempting login..."
    if login_response=$(curl -sS -X POST "$BACKEND/api/token" \
        -H "Content-Type: application/x-www-form-urlencoded" \
        -d "username=$SMOKE_USER&password=$SMOKE_PASS" 2>/dev/null); then
        
        if token=$(echo "$login_response" | jq -r '.access_token // empty' 2>/dev/null); then
            if [ "$token" != "null" ] && [ -n "$token" ]; then
                TOKEN="$token"
                masked_token=$(mask_token "$token")
                log "Login successful, token: $masked_token"
            else
                echo "ERROR: Login failed: no access_token in response" >&2
                exit 1
            fi
        else
            echo "ERROR: Login failed: invalid JSON response" >&2
            exit 1
        fi
    else
        echo "ERROR: Login request failed" >&2
        exit 1
    fi
else
    masked_token=$(mask_token "$TOKEN")
    log "Using provided token: $masked_token"
fi

# Function to test a single endpoint
test_endpoint() {
    local endpoint="$1"
    local slug="$2"
    local log_file="./system-check-logs/load-${slug}.txt"
    
    log "Testing endpoint: $endpoint"
    echo "Endpoint: $endpoint" > "$log_file"
    echo "Timestamp: $(date)" >> "$log_file"
    echo "Concurrency: $CONCURRENCY" >> "$log_file"
    echo "Requests: $REQUESTS" >> "$log_file"
    echo "" >> "$log_file"
    echo "Response times (seconds):" >> "$log_file"
    
    # Prepare curl command
    local curl_cmd="curl -sS -w '%{time_total}\n' -o /dev/null"
    if [ -n "${TOKEN:-}" ]; then
        curl_cmd="$curl_cmd -H 'Authorization: Bearer $TOKEN'"
    fi
    curl_cmd="$curl_cmd '$BACKEND$endpoint'"
    
    # Run concurrent requests and capture times
    local times=()
    local success_count=0
    local error_count=0
    
    # Use parallel if available, otherwise xargs
    if command -v parallel >/dev/null 2>&1; then
        log "Using GNU parallel for concurrency"
        while IFS= read -r time; do
            if [ -n "$time" ]; then
                times+=("$time")
                echo "$time" >> "$log_file"
                success_count=$((success_count + 1))
            fi
        done < <(parallel -j "$CONCURRENCY" --bar "$curl_cmd" ::: $(seq 1 "$REQUESTS") 2>/dev/null)
    else
        log "Using xargs for concurrency"
        while IFS= read -r time; do
            if [ -n "$time" ]; then
                times+=("$time")
                echo "$time" >> "$log_file"
                success_count=$((success_count + 1))
            fi
        done < <(seq 1 "$REQUESTS" | xargs -P "$CONCURRENCY" -I {} bash -c "$curl_cmd" 2>/dev/null)
    fi
    
    # Calculate statistics
    if [ ${#times[@]} -eq 0 ]; then
        fail "No successful requests for $endpoint" "$slug"
        p50_times["$slug"]="N/A"
        p95_times["$slug"]="N/A"
        return 1
    fi
    
    # Sort times numerically
    IFS=$'\n' sorted_times=($(sort -n <<<"${times[*]}"))
    unset IFS
    
    local count=${#sorted_times[@]}
    local p50_idx=$((count * 50 / 100))
    local p95_idx=$((count * 95 / 100))
    
    # Ensure indices are within bounds
    [ $p50_idx -ge $count ] && p50_idx=$((count - 1))
    [ $p95_idx -ge $count ] && p95_idx=$((count - 1))
    
    local p50_time=${sorted_times[$p50_idx]}
    local p95_time=${sorted_times[$p95_idx]}
    
    # Convert to milliseconds
    local p50_ms=$(echo "$p50_time * 1000" | bc -l 2>/dev/null | cut -d. -f1)
    local p95_ms=$(echo "$p95_time * 1000" | bc -l 2>/dev/null | cut -d. -f1)
    
    # Store results
    p50_times["$slug"]="$p50_ms"
    p95_times["$slug"]="$p95_ms"
    
    # Log statistics
    echo "" >> "$log_file"
    echo "Statistics:" >> "$log_file"
    echo "  Total requests: $REQUESTS" >> "$log_file"
    echo "  Successful: $success_count" >> "$log_file"
    echo "  P50: ${p50_ms}ms" >> "$log_file"
    echo "  P95: ${p95_ms}ms" >> "$log_file"
    echo "  Threshold: ${THRESHOLD_P95_MS}ms" >> "$log_file"
    
    # Check threshold
    if [ "$p95_ms" -le "$THRESHOLD_P95_MS" ]; then
        pass "P95: ${p95_ms}ms (≤${THRESHOLD_P95_MS}ms)" "$slug"
        return 0
    else
        fail "P95: ${p95_ms}ms (>${THRESHOLD_P95_MS}ms)" "$slug"
        return 1
    fi
}

# Test each endpoint
log "=== Load Testing Endpoints ==="

for endpoint in $ENDPOINTS; do
    # Create slug from endpoint
    slug=$(echo "$endpoint" | sed 's/[^a-zA-Z0-9]/_/g' | sed 's/_\+/_/g' | sed 's/^_//' | sed 's/_$//')
    
    if test_endpoint "$endpoint" "$slug"; then
        : # Success
    else
        : # Failure tracked in function
    fi
done

# Summary
log "=== Load Test Summary ==="
echo "┌─────────────────────┬─────────┬──────────┬──────────┬─────────────────┐"
echo "│ Endpoint            │ Status  │ P50 (ms) │ P95 (ms) │ Threshold (ms)  │"
echo "├─────────────────────┼─────────┼──────────┼──────────┼─────────────────┤"

for endpoint in $ENDPOINTS; do
    slug=$(echo "$endpoint" | sed 's/[^a-zA-Z0-9]/_/g' | sed 's/_\+/_/g' | sed 's/^_//' | sed 's/_$//')
    status="${results[$slug]:-UNKNOWN}"
    p50="${p50_times[$slug]:-N/A}"
    p95="${p95_times[$slug]:-N/A}"
    
    case $status in
        PASS)
            status_color="${GREEN}PASS${NC}"
            ;;
        FAIL)
            status_color="${RED}FAIL${NC}"
            ;;
        *)
            status_color="${YELLOW}UNKNOWN${NC}"
            ;;
    esac
    
    printf "│ %-19s │ %-7s │ %-8s │ %-8s │ %-15s │\n" "$endpoint" "$status_color" "$p50" "$p95" "$THRESHOLD_P95_MS"
done

echo "└─────────────────────┴─────────┴──────────┴──────────┴─────────────────┘"

# Determine exit code
failures=0
for endpoint in $ENDPOINTS; do
    slug=$(echo "$endpoint" | sed 's/[^a-zA-Z0-9]/_/g' | sed 's/_\+/_/g' | sed 's/^_//' | sed 's/_$//')
    if [ "${results[$slug]:-UNKNOWN}" = "FAIL" ]; then
        failures=$((failures + 1))
    fi
done

if [ $failures -eq 0 ]; then
    log "All endpoints under threshold!"
    exit 0
else
    log "Failures detected: $failures endpoint(s) exceeded threshold"
    exit 1
fi
