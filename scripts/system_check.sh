#!/bin/bash

# The Commons Development Environment System Check
# Performs comprehensive health and stack validation

set -euo pipefail

# Configuration
BACKEND="${BACKEND:-http://localhost:8000}"
FRONTEND="${FRONTEND:-http://localhost:5174}"
DB_FILE="${DB_FILE:-test.db}"
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

# Helper functions
log_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

log_success() {
    echo -e "${GREEN}✅ $1${NC}"
    TOTAL_CHECKS=$((TOTAL_CHECKS + 1))
}

log_error() {
    echo -e "${RED}❌ $1${NC}"
    FAILED_CHECKS=$((FAILED_CHECKS + 1))
    TOTAL_CHECKS=$((TOTAL_CHECKS + 1))
}

log_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
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
        log_error "Missing dependencies: ${missing_deps[*]}"
        echo "Please install missing dependencies and try again."
        exit 1
    fi
    
    log_success "All required dependencies found"
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
    log_info "Checking backend..."
    
    # Check port listening
    if nc -z localhost 8000 2>/dev/null; then
        log_success "Backend port 8000 is listening"
    else
        log_error "Backend port 8000 is not listening"
        return 1
    fi
    
    # Health endpoint
    local health_response
    if health_response=$(curl -s -w '\nHTTP Status: %{http_code}\n' "$BACKEND/api/health" 2>/dev/null); then
        local health_status
        local health_body
        
        health_status=$(echo "$health_response" | tail -n 1 | sed 's/HTTP Status: //')
        health_body=$(echo "$health_response" | sed '$d')
        
        if [[ "$health_status" == "200" ]]; then
            log_success "Backend health endpoint: $health_status"
            echo "Response: $health_body" | jq '.' 2>/dev/null || echo "Response: $health_body"
        else
            log_error "Backend health endpoint failed: $health_status"
            return 1
        fi
    else
        log_error "Failed to connect to backend health endpoint"
        return 1
    fi
    
    # API docs
    local docs_status
    if docs_status=$(curl -s -o /dev/null -w '%{http_code}' "$BACKEND/docs" 2>/dev/null); then
        if [[ "$docs_status" == "200" ]]; then
            log_success "API docs accessible: $docs_status"
        else
            log_error "API docs failed: $docs_status"
            return 1
        fi
    else
        log_error "Failed to connect to API docs"
        return 1
    fi
    
    echo ""
}

# Check database
check_database() {
    log_info "Checking database..."
    
    # Check DB file exists
    if [[ -f "$DB_FILE" ]]; then
        log_success "Database file exists: $DB_FILE"
    else
        log_error "Database file not found: $DB_FILE"
        return 1
    fi
    
    # Check sqlite3 availability
    if ! command -v sqlite3 >/dev/null 2>&1; then
        log_warning "sqlite3 not available, skipping database queries"
        return 0
    fi
    
    # Get table list
    local tables
    if tables=$(sqlite3 "$DB_FILE" ".tables" 2>/dev/null); then
        log_success "Database tables: $tables"
    else
        log_error "Failed to get database tables"
        return 1
    fi
    
    # Get table counts
    local key_tables=("users" "polls" "votes" "delegations" "comments")
    for table in "${key_tables[@]}"; do
        local count
        if count=$(sqlite3 "$DB_FILE" "SELECT COUNT(*) FROM $table;" 2>/dev/null); then
            log_success "$table count: $count"
        else
            log_warning "Could not get count for table: $table"
        fi
    done
    
    echo ""
}

# Check frontend
check_frontend() {
    log_info "Checking frontend..."
    
    # Check port listening
    if nc -z localhost 5174 2>/dev/null; then
        log_success "Frontend port 5174 is listening"
    else
        log_error "Frontend port 5174 is not listening"
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
            log_success "Frontend accessible: $frontend_status"
            
            # Try to extract title
            local title
            if title=$(echo "$frontend_body" | grep -i '<title>' | sed 's/.*<title>\(.*\)<\/title>.*/\1/' | head -n1); then
                if [[ -n "$title" ]]; then
                    log_success "Page title: $title"
                fi
            fi
        else
            log_error "Frontend failed: $frontend_status"
            return 1
        fi
    else
        log_error "Failed to connect to frontend"
        return 1
    fi
    
    echo ""
}

# API core flow check
check_api_flow() {
    log_info "Checking API core flow..."
    
    local smoke_user="${SMOKE_USER:-alice_community}"
    local smoke_pass="${SMOKE_PASS:-password123}"
    
    # Login
    local login_response
    if login_response=$(curl -s -w '\nHTTP Status: %{http_code}\n' \
        -X POST \
        -H 'Content-Type: application/x-www-form-urlencoded' \
        -H 'Accept: application/json' \
        -d "username=${smoke_user}&password=${smoke_pass}" \
        "${BACKEND}/api/token" 2>/dev/null); then
        
        local login_status
        local login_body
        
        login_status=$(echo "$login_response" | tail -n 1 | sed 's/HTTP Status: //')
        login_body=$(echo "$login_response" | sed '$d')
        
        if [[ "$login_status" == "200" ]]; then
            local token
            token=$(echo "$login_body" | jq -r '.access_token')
            if [[ -n "$token" && "$token" != "null" ]]; then
                log_success "Login successful"
                
                # GET polls
                local polls_response
                if polls_response=$(curl -s -w '\nHTTP Status: %{http_code}\n' \
                    -H "Authorization: Bearer $token" \
                    -H 'Accept: application/json' \
                    "${BACKEND}/api/polls/" 2>/dev/null); then
                    
                    local polls_status
                    local polls_body
                    
                    polls_status=$(echo "$polls_response" | tail -n 1 | sed 's/HTTP Status: //')
                    polls_body=$(echo "$polls_response" | sed '$d')
                    
                    if [[ "$polls_status" == "200" ]]; then
                        log_success "GET /api/polls/ successful"
                        
                        # Get first poll ID
                        local first_poll_id
                        first_poll_id=$(echo "$polls_body" | jq -r '.[0].id // empty')
                        if [[ -n "$first_poll_id" && "$first_poll_id" != "null" ]]; then
                            log_success "First poll ID: $first_poll_id"
                            
                            # GET poll details
                            local poll_response
                            if poll_response=$(curl -s -w '\nHTTP Status: %{http_code}\n' \
                                -H "Authorization: Bearer $token" \
                                -H 'Accept: application/json' \
                                "${BACKEND}/api/polls/${first_poll_id}" 2>/dev/null); then
                                
                                local poll_status
                                poll_status=$(echo "$poll_response" | tail -n 1 | sed 's/HTTP Status: //')
                                
                                if [[ "$poll_status" == "200" ]]; then
                                    log_success "GET poll details successful"
                                else
                                    log_error "GET poll details failed: $poll_status"
                                fi
                            else
                                log_error "Failed to get poll details"
                            fi
                        else
                            log_warning "No polls found to test details endpoint"
                        fi
                    else
                        log_error "GET /api/polls/ failed: $polls_status"
                    fi
                else
                    log_error "Failed to get polls"
                fi
                
                # GET delegations
                local delegations_response
                if delegations_response=$(curl -s -w '\nHTTP Status: %{http_code}\n' \
                    -H "Authorization: Bearer $token" \
                    -H 'Accept: application/json' \
                    "${BACKEND}/api/delegations/me" 2>/dev/null); then
                    
                    local delegations_status
                    delegations_status=$(echo "$delegations_response" | tail -n 1 | sed 's/HTTP Status: //')
                    
                    if [[ "$delegations_status" == "200" ]]; then
                        log_success "GET /api/delegations/me successful"
                    else
                        log_error "GET /api/delegations/me failed: $delegations_status"
                    fi
                else
                    log_error "Failed to get delegations"
                fi
            else
                log_error "Failed to extract token from login response"
            fi
        else
            log_error "Login failed: $login_status"
        fi
    else
        log_error "Failed to connect to login endpoint"
    fi
    
    echo ""
}

# Check WebSocket
check_websocket() {
    log_info "Checking WebSocket..."
    
    # Check if wscat or websocat is available
    local ws_client=""
    if command -v wscat >/dev/null 2>&1; then
        ws_client="wscat"
    elif command -v websocat >/dev/null 2>&1; then
        ws_client="websocat"
    else
        log_warning "No WebSocket client (wscat/websocat) available, skipping WebSocket test"
        return 0
    fi
    
    # Test WebSocket connection
    local ws_test_result
    if [[ "$ws_client" == "wscat" ]]; then
        # Use timeout to limit the test duration
        if timeout 10 bash -c "echo 'ping' | wscat -c '$WS_URL' 2>/dev/null | grep -q 'pong'"; then
            log_success "WebSocket connection and ping/pong test successful"
        else
            log_error "WebSocket connection or ping/pong test failed"
        fi
    elif [[ "$ws_client" == "websocat" ]]; then
        if timeout 10 bash -c "echo 'ping' | websocat '$WS_URL' 2>/dev/null | grep -q 'pong'"; then
            log_success "WebSocket connection and ping/pong test successful"
        else
            log_error "WebSocket connection or ping/pong test failed"
        fi
    fi
    
    echo ""
}

# Print summary
print_summary() {
    log_info "System Check Summary"
    echo "===================="
    echo "Total checks: $TOTAL_CHECKS"
    echo "Passed: $((TOTAL_CHECKS - FAILED_CHECKS))"
    echo "Failed: $FAILED_CHECKS"
    
    if [[ $FAILED_CHECKS -eq 0 ]]; then
        log_success "All checks passed! The Commons development environment is healthy."
        exit 0
    else
        log_error "Some checks failed. Please review the errors above."
        exit 1
    fi
}

# Main execution
main() {
    echo "🔍 The Commons Development Environment System Check"
    echo "=================================================="
    echo ""
    
    # Check dependencies first
    check_dependencies
    echo ""
    
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
