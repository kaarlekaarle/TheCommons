#!/bin/bash

# The Commons Development Environment System Check
# Performs comprehensive health and stack validation

set -euo pipefail

# Configuration
BACKEND="${BACKEND:-http://localhost:8000}"
FRONTEND="${FRONTEND:-http://localhost:5174}"
WS_URL="${WS_URL:-ws://localhost:8000/ws}"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Status tracking
FAILED_CHECKS=0
TOTAL_CHECKS=0
CRITICAL_FAILURES=0
JSON_MODE=false
CHECK_BACKEND=true
CHECK_FRONTEND=true
CHECK_DB=true
CHECK_WS=true

# Temporary files for artifacts
TEMP_DIR="/tmp/commons_system_check_$$"
HEALTH_FILE="$TEMP_DIR/health.json"
POLLS_FILE="$TEMP_DIR/polls.json"
POLL_DETAIL_FILE="$TEMP_DIR/poll_detail.json"

# Results storage for JSON output
declare -A CHECK_RESULTS

# Helper functions
log_info() {
    if [[ "$JSON_MODE" == "false" ]]; then
        echo -e "${BLUE}ℹ️  $1${NC}" >&2
    fi
}

log_success() {
    if [[ "$JSON_MODE" == "false" ]]; then
        echo -e "${GREEN}✅ $1${NC}" >&2
    fi
    TOTAL_CHECKS=$((TOTAL_CHECKS + 1))
    CHECK_RESULTS["$2"]="success"
}

log_error() {
    if [[ "$JSON_MODE" == "false" ]]; then
        echo -e "${RED}❌ $1${NC}" >&2
    fi
    FAILED_CHECKS=$((FAILED_CHECKS + 1))
    TOTAL_CHECKS=$((TOTAL_CHECKS + 1))
    CHECK_RESULTS["$2"]="failed"
    if [[ "$3" == "critical" ]]; then
        CRITICAL_FAILURES=$((CRITICAL_FAILURES + 1))
    fi
}

log_warning() {
    if [[ "$JSON_MODE" == "false" ]]; then
        echo -e "${YELLOW}⚠️  $1${NC}" >&2
    fi
    TOTAL_CHECKS=$((TOTAL_CHECKS + 1))
    CHECK_RESULTS["$2"]="warning"
}

log_skipped() {
    if [[ "$JSON_MODE" == "false" ]]; then
        echo -e "${YELLOW}⏭️  $1${NC}" >&2
    fi
    TOTAL_CHECKS=$((TOTAL_CHECKS + 1))
    CHECK_RESULTS["$2"]="skipped"
}

# Show help
show_help() {
    cat << EOF
Usage: $0 [OPTIONS]

The Commons Development Environment System Check

Options:
  --backend     Check backend health and API endpoints
  --frontend    Check frontend accessibility
  --db          Check database connectivity
  --ws          Check WebSocket connectivity
  --json        Output results in JSON format
  -h, --help    Show this help message

Environment Variables:
  BACKEND       Backend URL [default: http://localhost:8000]
  FRONTEND      Frontend URL [default: http://localhost:5174]
  WS_URL        WebSocket URL [default: ws://localhost:8000/ws]
  SMOKE_USER    Username for auto-login [default: alice_community]
  SMOKE_PASS    Password for auto-login [default: password123]
  TOKEN         JWT token (if not set, will auto-login)
  POSTGRES_HOST PostgreSQL host for pg_isready check
  POSTGRES_PORT PostgreSQL port for pg_isready check
  POSTGRES_USER PostgreSQL user for pg_isready check
  POSTGRES_DB   PostgreSQL database for pg_isready check

Examples:
  $0                    # Run all checks
  $0 --backend --db     # Check only backend and database
  $0 --json             # Output results in JSON format
  TOKEN=mytoken $0      # Use existing token
EOF
}

# Parse command line arguments
parse_args() {
    while [[ $# -gt 0 ]]; do
        case $1 in
            --backend)
                CHECK_BACKEND=true
                shift
                ;;
            --frontend)
                CHECK_FRONTEND=true
                shift
                ;;
            --db)
                CHECK_DB=true
                shift
                ;;
            --ws)
                CHECK_WS=true
                shift
                ;;
            --json)
                JSON_MODE=true
                shift
                ;;
            -h|--help)
                show_help
                exit 0
                ;;
            *)
                echo "Unknown option: $1" >&2
                show_help
                exit 1
                ;;
        esac
    done
}

# Check dependencies
check_dependencies() {
    log_info "Checking dependencies..."
    
    local missing_deps=()
    
    for dep in curl jq nc lsof; do
        if ! command -v "$dep" >/dev/null 2>&1; then
            missing_deps+=("$dep")
        fi
    done
    
    if [[ ${#missing_deps[@]} -gt 0 ]]; then
        log_error "Missing dependencies: ${missing_deps[*]}" "dependencies" "critical"
        echo "Please install missing dependencies and try again." >&2
        exit 1
    fi
    
    log_success "All required dependencies found" "dependencies"
}

# Auto-login function
auto_login() {
    local smoke_user="${SMOKE_USER:-alice_community}"
    local smoke_pass="${SMOKE_PASS:-password123}"
    
    if [[ -n "${TOKEN:-}" ]]; then
        log_info "Using existing TOKEN environment variable"
        return 0
    fi
    
    log_info "Auto-login as: $smoke_user"
    
    # Make login request
    local response
    response=$(curl -s -w '\nHTTP Status: %{http_code}\n' \
        -X POST \
        -H 'Content-Type: application/x-www-form-urlencoded' \
        -H 'Accept: application/json' \
        -d "username=${smoke_user}&password=${smoke_pass}" \
        "${BACKEND}/api/token")
    
    # Parse response
    local http_status
    local response_body
    
    http_status=$(echo "$response" | tail -n 1 | sed 's/HTTP Status: //')
    response_body=$(echo "$response" | sed '$d')
    
    if [[ "$http_status" == "200" ]]; then
        TOKEN=$(echo "$response_body" | jq -r '.access_token')
        
        if [[ -n "$TOKEN" && "$TOKEN" != "null" ]]; then
            log_success "Auto-login successful" "auto_login"
            # Print masked token summary
            local masked_token="${TOKEN:0:10}...${TOKEN: -10}"
            log_info "Token: $masked_token"
        else
            log_error "Failed to extract token from response" "auto_login" "critical"
            return 1
        fi
    else
        log_error "Auto-login failed (HTTP $http_status)" "auto_login" "critical"
        return 1
    fi
}

# Detect SQLite database file
detect_sqlite_file() {
    local candidates=("test.db" "backend/app.db" "backend/test.db" "./app.db")
    
    for candidate in "${candidates[@]}"; do
        if [[ -f "$candidate" ]]; then
            echo "$candidate"
            return 0
        fi
    done
    
    return 1
}

# Print system information
print_system_info() {
    log_info "System Information"
    echo "=================="
    
    # OS and bash version
    echo "OS: $(uname -s) $(uname -r)"
    echo "Bash: $(bash --version | head -n1)"
    
    # Docker status
    if command -v docker >/dev/null 2>&1; then
        if docker info >/dev/null 2>&1; then
            echo "Docker: Running"
        else
            echo "Docker: Installed but not running"
        fi
    else
        echo "Docker: Not installed"
    fi
    
    # Node & npm versions
    if command -v node >/dev/null 2>&1; then
        echo "Node: $(node --version)"
    else
        echo "Node: Not installed"
    fi
    
    if command -v npm >/dev/null 2>&1; then
        echo "NPM: $(npm --version)"
    else
        echo "NPM: Not installed"
    fi
    
    # Python version
    if command -v python3 >/dev/null 2>&1; then
        echo "Python: $(python3 --version)"
    elif command -v python >/dev/null 2>&1; then
        echo "Python: $(python --version)"
    else
        echo "Python: Not installed"
    fi
    
    echo ""
}

# Check backend health
check_backend() {
    if [[ "$CHECK_BACKEND" == "false" ]]; then
        log_skipped "Backend check disabled" "backend"
        return 0
    fi
    
    log_info "Checking backend..."
    
    # Check port listening
    if nc -z localhost 8000 2>/dev/null; then
        log_success "Backend port 8000 is listening" "backend_port"
    else
        log_error "Backend port 8000 is not listening" "backend_port" "critical"
        return 1
    fi
    
    # Health endpoint
    local health_response
    if health_response=$(curl -s -w '\nHTTP Status: %{http_code}\n' "$BACKEND/api/health" 2>/dev/null); then
        local health_status
        local health_body
        
        health_status=$(echo "$health_response" | tail -n 1 | sed 's/HTTP Status: //')
        health_body=$(echo "$health_response" | sed '$d')
        
        # Save health response to artifact
        echo "$health_body" > "$HEALTH_FILE"
        
        if [[ "$health_status" == "200" ]]; then
            log_success "Backend health endpoint: $health_status" "backend_health"
            if [[ "$JSON_MODE" == "false" ]]; then
                echo "Response: $health_body" | jq '.' 2>/dev/null || echo "Response: $health_body"
            fi
        else
            log_error "Backend health endpoint failed: $health_status" "backend_health" "critical"
            return 1
        fi
    else
        log_error "Failed to connect to backend health endpoint" "backend_health" "critical"
        return 1
    fi
    
    # API docs
    local docs_status
    if docs_status=$(curl -s -o /dev/null -w '%{http_code}' "$BACKEND/docs" 2>/dev/null); then
        if [[ "$docs_status" == "200" ]]; then
            log_success "API docs accessible: $docs_status" "backend_docs"
        else
            log_error "API docs failed: $docs_status" "backend_docs"
        fi
    else
        log_error "Failed to connect to API docs" "backend_docs"
    fi
}

# Check database
check_database() {
    if [[ "$CHECK_DB" == "false" ]]; then
        log_skipped "Database check disabled" "database"
        return 0
    fi
    
    log_info "Checking database..."
    
    # Check SQLite
    local db_file
    if db_file=$(detect_sqlite_file); then
        log_success "SQLite database found: $db_file" "sqlite_file"
        
        # Check sqlite3 availability
        if ! command -v sqlite3 >/dev/null 2>&1; then
            log_warning "sqlite3 not available, skipping database queries" "sqlite_queries"
            return 0
        fi
        
        # Get table list
        local tables
        if tables=$(sqlite3 "$db_file" ".tables" 2>/dev/null); then
            log_success "Database tables: $tables" "sqlite_tables"
        else
            log_error "Failed to get database tables" "sqlite_tables"
        fi
        
        # Get table counts
        local key_tables=("users" "polls" "votes" "delegations" "comments")
        for table in "${key_tables[@]}"; do
            local count
            if count=$(sqlite3 "$db_file" "SELECT COUNT(*) FROM $table;" 2>/dev/null); then
                log_success "$table count: $count" "sqlite_${table}_count"
            else
                log_warning "Could not get count for table: $table" "sqlite_${table}_count"
            fi
        done
    else
        log_warning "No SQLite database file found" "sqlite_file"
    fi
    
    # Check PostgreSQL if available
    if command -v pg_isready >/dev/null 2>&1 && [[ -n "${POSTGRES_HOST:-}" ]]; then
        log_info "Checking PostgreSQL..."
        
        local pg_host="${POSTGRES_HOST:-localhost}"
        local pg_port="${POSTGRES_PORT:-5432}"
        local pg_user="${POSTGRES_USER:-postgres}"
        local pg_db="${POSTGRES_DB:-postgres}"
        
        # Check if PostgreSQL is ready
        if pg_isready -h "$pg_host" -p "$pg_port" -U "$pg_user" >/dev/null 2>&1; then
            log_success "PostgreSQL is ready" "postgres_ready"
            
            # Test simple query
            if PGPASSWORD="${POSTGRES_PASSWORD:-}" psql -h "$pg_host" -p "$pg_port" -U "$pg_user" -d "$pg_db" -c "SELECT 1;" >/dev/null 2>&1; then
                log_success "PostgreSQL query test passed" "postgres_query"
            else
                log_error "PostgreSQL query test failed" "postgres_query"
            fi
        else
            log_error "PostgreSQL is not ready" "postgres_ready"
        fi
    else
        log_skipped "PostgreSQL check (pg_isready not available or POSTGRES_HOST not set)" "postgres_ready"
    fi
}

# Check frontend
check_frontend() {
    if [[ "$CHECK_FRONTEND" == "false" ]]; then
        log_skipped "Frontend check disabled" "frontend"
        return 0
    fi
    
    log_info "Checking frontend..."
    
    # Check port listening
    if nc -z localhost 5174 2>/dev/null; then
        log_success "Frontend port 5174 is listening" "frontend_port"
    else
        log_error "Frontend port 5174 is not listening" "frontend_port"
        return 1
    fi
    
    # GET frontend
    local frontend_response
    if frontend_response=$(curl -s -w '\nHTTP Status: %{http_code}\n' "$FRONTEND" 2>/dev/null); then
        local frontend_status
        local frontend_body
        
        frontend_status=$(echo "$frontend_response" | tail -n 1 | sed 's/HTTP Status: //')
        frontend_body=$(echo "$frontend_response" | sed '$d')
        
        if [[ "$frontend_status" == "200" ]]; then
            log_success "Frontend accessible: $frontend_status" "frontend_accessible"
            
            # Try to extract title
            local title
            if title=$(echo "$frontend_body" | grep -i '<title>' | sed 's/.*<title>\(.*\)<\/title>.*/\1/' | head -n1); then
                if [[ -n "$title" ]]; then
                    log_success "Page title: $title" "frontend_title"
                fi
            fi
        else
            log_error "Frontend failed: $frontend_status" "frontend_accessible"
            return 1
        fi
    else
        log_error "Failed to connect to frontend" "frontend_accessible"
        return 1
    fi
}

# API core flow check
check_api_flow() {
    if [[ "$CHECK_BACKEND" == "false" ]]; then
        log_skipped "API flow check disabled (backend check disabled)" "api_flow"
        return 0
    fi
    
    log_info "Checking API core flow..."
    
    # Auto-login if needed
    if ! auto_login; then
        log_error "Failed to authenticate for API flow check" "api_flow" "critical"
        return 1
    fi
    
    # GET polls
    local polls_response
    if polls_response=$(curl -s -w '\nHTTP Status: %{http_code}\n' \
        -H "Authorization: Bearer $TOKEN" \
        -H 'Accept: application/json' \
        "${BACKEND}/api/polls/" 2>/dev/null); then
        
        local polls_status
        local polls_body
        
        polls_status=$(echo "$polls_response" | tail -n 1 | sed 's/HTTP Status: //')
        polls_body=$(echo "$polls_response" | sed '$d')
        
        # Save polls response to artifact
        echo "$polls_body" > "$POLLS_FILE"
        
        if [[ "$polls_status" == "200" ]]; then
            log_success "GET /api/polls/ successful" "api_polls"
            
            # Get first poll ID
            local first_poll_id
            first_poll_id=$(echo "$polls_body" | jq -r '.[0].id // empty')
            if [[ -n "$first_poll_id" && "$first_poll_id" != "null" ]]; then
                log_success "First poll ID: $first_poll_id" "api_poll_id"
                
                # GET poll details
                local poll_response
                if poll_response=$(curl -s -w '\nHTTP Status: %{http_code}\n' \
                    -H "Authorization: Bearer $TOKEN" \
                    -H 'Accept: application/json' \
                    "${BACKEND}/api/polls/${first_poll_id}" 2>/dev/null); then
                    
                    local poll_status
                    local poll_body
                    
                    poll_status=$(echo "$poll_response" | tail -n 1 | sed 's/HTTP Status: //')
                    poll_body=$(echo "$poll_response" | sed '$d')
                    
                    # Save poll detail response to artifact
                    echo "$poll_body" > "$POLL_DETAIL_FILE"
                    
                    if [[ "$poll_status" == "200" ]]; then
                        log_success "GET poll details successful" "api_poll_detail"
                    else
                        log_error "GET poll details failed: $poll_status" "api_poll_detail" "critical"
                    fi
                else
                    log_error "Failed to get poll details" "api_poll_detail" "critical"
                fi
            else
                log_warning "No polls found to test details endpoint" "api_poll_detail"
            fi
        else
            log_error "GET /api/polls/ failed: $polls_status" "api_polls" "critical"
        fi
    else
        log_error "Failed to get polls" "api_polls" "critical"
    fi
    
    # GET delegations
    local delegations_response
    if delegations_response=$(curl -s -w '\nHTTP Status: %{http_code}\n' \
        -H "Authorization: Bearer $TOKEN" \
        -H 'Accept: application/json' \
        "${BACKEND}/api/delegations/me" 2>/dev/null); then
        
        local delegations_status
        delegations_status=$(echo "$delegations_response" | tail -n 1 | sed 's/HTTP Status: //')
        
        if [[ "$delegations_status" == "200" ]]; then
            log_success "GET /api/delegations/me successful" "api_delegations"
        else
            log_error "GET /api/delegations/me failed: $delegations_status" "api_delegations"
        fi
    else
        log_error "Failed to get delegations" "api_delegations"
    fi
}

# Check WebSocket
check_websocket() {
    if [[ "$CHECK_WS" == "false" ]]; then
        log_skipped "WebSocket check disabled" "websocket"
        return 0
    fi
    
    log_info "Checking WebSocket..."
    
    # Check if wscat or websocat is available
    local ws_client=""
    if command -v wscat >/dev/null 2>&1; then
        ws_client="wscat"
    elif command -v websocat >/dev/null 2>&1; then
        ws_client="websocat"
    else
        log_skipped "No WebSocket client (wscat/websocat) available" "websocket"
        return 0
    fi
    
    # Test WebSocket connection
    local ws_test_result
    if [[ "$ws_client" == "wscat" ]]; then
        # Use timeout to limit the test duration
        if timeout 10 bash -c "echo 'ping' | wscat -c '$WS_URL' 2>/dev/null | grep -q 'pong'"; then
            log_success "WebSocket connection and ping/pong test successful" "websocket"
        else
            log_error "WebSocket connection or ping/pong test failed" "websocket"
        fi
    elif [[ "$ws_client" == "websocat" ]]; then
        if timeout 10 bash -c "echo 'ping' | websocat '$WS_URL' 2>/dev/null | grep -q 'pong'"; then
            log_success "WebSocket connection and ping/pong test successful" "websocket"
        else
            log_error "WebSocket connection or ping/pong test failed" "websocket"
        fi
    fi
}

# Print JSON summary
print_json_summary() {
    local summary
    summary=$(cat << EOF
{
  "timestamp": "$(date -u +"%Y-%m-%dT%H:%M:%SZ")",
  "total_checks": $TOTAL_CHECKS,
  "passed": $((TOTAL_CHECKS - FAILED_CHECKS)),
  "failed": $FAILED_CHECKS,
  "critical_failures": $CRITICAL_FAILURES,
  "overall_status": "$([[ $CRITICAL_FAILURES -eq 0 ]] && echo "healthy" || echo "unhealthy")",
  "artifacts": {
    "health": "$HEALTH_FILE",
    "polls": "$POLLS_FILE",
    "poll_detail": "$POLL_DETAIL_FILE"
  },
  "checks": {
$(for key in "${!CHECK_RESULTS[@]}"; do
    echo "    \"$key\": \"${CHECK_RESULTS[$key]}\""
done | sort | sed '$s/,$//')
  }
}
EOF
)
    echo "$summary"
}

# Print summary
print_summary() {
    if [[ "$JSON_MODE" == "true" ]]; then
        print_json_summary
        return
    fi
    
    log_info "System Check Summary"
    echo "===================="
    echo "Total checks: $TOTAL_CHECKS"
    echo "Passed: $((TOTAL_CHECKS - FAILED_CHECKS))"
    echo "Failed: $FAILED_CHECKS"
    echo "Critical failures: $CRITICAL_FAILURES"
    echo ""
    echo "Artifacts saved to:"
    echo "  Health: $HEALTH_FILE"
    echo "  Polls: $POLLS_FILE"
    echo "  Poll Detail: $POLL_DETAIL_FILE"
    echo ""
    
    if [[ $CRITICAL_FAILURES -eq 0 ]]; then
        log_success "All critical checks passed! The Commons development environment is healthy."
        exit 0
    else
        log_error "Critical checks failed. Please review the errors above."
        exit 1
    fi
}

# Cleanup function
cleanup() {
    # Remove temporary directory if it exists
    if [[ -d "$TEMP_DIR" ]]; then
        rm -rf "$TEMP_DIR"
    fi
}

# Main execution
main() {
    # Set up cleanup trap
    trap cleanup EXIT
    
    # Create temporary directory for artifacts
    mkdir -p "$TEMP_DIR"
    
    # Parse command line arguments
    parse_args "$@"
    
    if [[ "$JSON_MODE" == "false" ]]; then
        echo "🔍 The Commons Development Environment System Check"
        echo "=================================================="
        echo ""
    fi
    
    # Check dependencies first
    check_dependencies
    if [[ "$JSON_MODE" == "false" ]]; then
        echo ""
    fi
    
    # Run all checks
    print_system_info
    check_backend
    check_database
    check_frontend
    check_api_flow
    check_websocket
    
    # Print summary
    print_summary
}

# Run main function
main "$@"
