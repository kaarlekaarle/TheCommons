#!/bin/bash

# The Commons API CLI Tool
# A comprehensive command-line interface for testing The Commons backend API

set -euo pipefail

# Configuration
BASE_URL="${BASE_URL:-http://localhost:8000}"
DEFAULT_METHOD="GET"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Helper functions
log_info() {
    echo -e "${BLUE}ℹ️  $1${NC}" >&2
}

log_success() {
    echo -e "${GREEN}✅ $1${NC}" >&2
}

log_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}" >&2
}

log_error() {
    echo -e "${RED}❌ $1${NC}" >&2
}

# Check dependencies
check_dependencies() {
    if ! command -v curl >/dev/null 2>&1; then
        log_error "curl is required but not installed"
        exit 1
    fi
    
    if ! command -v jq >/dev/null 2>&1; then
        log_error "jq is required but not installed"
        log_info "Install with: brew install jq (macOS) or apt-get install jq (Ubuntu)"
        exit 1
    fi
}

# Pretty print JSON response
pretty_print_response() {
    local response_body="$1"
    local content_type="$2"
    
    if [[ "$content_type" == *"application/json"* ]]; then
        echo "$response_body" | jq '.' 2>/dev/null || echo "$response_body"
    else
        echo "$response_body"
    fi
}

# Make HTTP request and handle response
make_request() {
    local method="$1"
    local url="$2"
    local token="$3"
    local json_data="$4"
    local json_file="$5"
    
    # Build curl command
    local curl_cmd="curl -s -w '\nHTTP Status: %{http_code}\nContent-Type: %{content_type}\n'"
    curl_cmd="$curl_cmd -X $method"
    
    # Add authorization if token provided
    if [[ -n "$token" ]]; then
        curl_cmd="$curl_cmd -H 'Authorization: Bearer $token'"
    fi
    
    # Add content type and other headers
    curl_cmd="$curl_cmd -H 'Content-Type: application/json'"
    curl_cmd="$curl_cmd -H 'Accept: application/json'"
    
    # Add JSON data or file
    if [[ -n "$json_file" ]]; then
        curl_cmd="$curl_cmd -d @$json_file"
    elif [[ -n "$json_data" ]]; then
        curl_cmd="$curl_cmd -d '$json_data'"
    fi
    
    # Add the URL
    curl_cmd="$curl_cmd '$url'"
    
    # Execute request
    local response
    response=$(eval "$curl_cmd")
    
    # Parse response
    local http_status
    local content_type
    local response_body
    
    http_status=$(echo "$response" | tail -n 2 | head -n 1 | sed 's/HTTP Status: //' | tr -d '\n')
    content_type=$(echo "$response" | tail -n 1 | sed 's/Content-Type: //' | tr -d '\n')
    response_body=$(echo "$response" | sed '$d' | sed '$d')
    
    # Print request info
    echo "🔍 $method $url" >&2
    if [[ -n "$token" ]]; then
        echo "🔑 Token: ${token:0:20}..." >&2
    fi
    
    # Print response
    echo ""
    echo "📊 HTTP Status: $http_status" >&2
    echo "📄 Response Body:" >&2
    pretty_print_response "$response_body" "$content_type" >&2
    
    # Return status for error handling (only the numeric part)
    echo "$http_status" | tr -d '\n'
}

# Login subcommand
login() {
    local username="$1"
    local password="$2"
    
    log_info "Logging in as: $username"
    
    # Make login request
    local response
    response=$(curl -s -w '\nHTTP Status: %{http_code}\n' \
        -X POST \
        -H 'Content-Type: application/x-www-form-urlencoded' \
        -H 'Accept: application/json' \
        -d "username=${username}&password=${password}" \
        "${BASE_URL}/api/token")
    
    # Parse response
    local http_status
    local response_body
    
    http_status=$(echo "$response" | tail -n 1 | sed 's/HTTP Status: //')
    response_body=$(echo "$response" | sed '$d')
    
    if [[ "$http_status" == "200" ]]; then
        local token
        token=$(echo "$response_body" | jq -r '.access_token')
        
        if [[ -n "$token" && "$token" != "null" ]]; then
            log_success "Login successful!"
            echo "$token"
        else
            log_error "Failed to extract token from response"
            echo "Response: $response_body" >&2
            exit 1
        fi
    else
        log_error "Login failed (HTTP $http_status)"
        echo "Response: $response_body" >&2
        exit 1
    fi
}

# Smoke test subcommand
smoke() {
    local smoke_user="${SMOKE_USER:-alice_community}"
    local smoke_pass="${SMOKE_PASS:-password123}"
    
    log_info "Running smoke test with user: $smoke_user"
    echo ""
    
    # Step 1: Login
    log_info "Step 1: Login"
    local token
    token=$(login "$smoke_user" "$smoke_pass")
    log_success "Got token: ${token:0:20}..."
    echo ""
    
    # Step 2: Health check
    log_info "Step 2: Health check"
    local health_status
    health_status=$(make_request "GET" "${BASE_URL}/api/health" "" "" "")
    if [[ "$health_status" -ge 400 ]]; then
        log_error "Health check failed"
        exit 1
    fi
    log_success "Health check passed"
    echo ""
    
    # Step 3: Get polls
    log_info "Step 3: Get polls"
    local polls_status
    polls_status=$(make_request "GET" "${BASE_URL}/api/polls/" "$token" "" "")
    if [[ "$polls_status" -ge 400 ]]; then
        log_error "Get polls failed"
        exit 1
    fi
    log_success "Get polls passed"
    echo ""
    
    # Step 4: Create poll
    log_info "Step 4: Create poll"
    local poll_data='{"title":"Smoke Test","description":"via script"}'
    local create_response
    create_response=$(curl -s -w '\nHTTP Status: %{http_code}\n' \
        -X POST \
        -H "Authorization: Bearer $token" \
        -H 'Content-Type: application/json' \
        -H 'Accept: application/json' \
        -d "$poll_data" \
        "${BASE_URL}/api/polls/")
    
    local create_status
    local create_body
    
    create_status=$(echo "$create_response" | tail -n 1 | sed 's/HTTP Status: //')
    create_body=$(echo "$create_response" | sed '$d')
    
    if [[ "$create_status" -ge 400 ]]; then
        log_error "Create poll failed"
        echo "Response: $create_body" >&2
        exit 1
    fi
    
    local poll_id
    poll_id=$(echo "$create_body" | jq -r '.id')
    log_success "Created poll with ID: $poll_id"
    echo ""
    
    # Step 5: Create options (Yes, No, Abstain)
    log_info "Step 5: Create options"
    local options=("Yes" "No" "Abstain")
    local option_ids=()
    
    for option_text in "${options[@]}"; do
        local option_data="{\"poll_id\":\"$poll_id\",\"text\":\"$option_text\"}"
        local option_response
        option_response=$(curl -s -w '\nHTTP Status: %{http_code}\n' \
            -X POST \
            -H "Authorization: Bearer $token" \
            -H 'Content-Type: application/json' \
            -H 'Accept: application/json' \
            -d "$option_data" \
            "${BASE_URL}/api/options/")
        
        local option_status
        local option_body
        
        option_status=$(echo "$option_response" | tail -n 1 | sed 's/HTTP Status: //')
        option_body=$(echo "$option_response" | sed '$d')
        
        if [[ "$option_status" -ge 400 ]]; then
            log_error "Create option '$option_text' failed"
            echo "Response: $option_body" >&2
            exit 1
        fi
        
        local option_id
        option_id=$(echo "$option_body" | jq -r '.id')
        option_ids+=("$option_id")
        log_success "Created option '$option_text' with ID: $option_id"
    done
    echo ""
    
    # Step 6: Vote on "Yes" option
    log_info "Step 6: Vote on 'Yes' option"
    local yes_option_id="${option_ids[0]}"
    local vote_data="{\"poll_id\":\"$poll_id\",\"option_id\":\"$yes_option_id\"}"
    local vote_response
    vote_response=$(curl -s -w '\nHTTP Status: %{http_code}\n' \
        -X POST \
        -H "Authorization: Bearer $token" \
        -H 'Content-Type: application/json' \
        -H 'Accept: application/json' \
        -d "$vote_data" \
        "${BASE_URL}/api/votes/")
    
    local vote_status
    local vote_body
    
    vote_status=$(echo "$vote_response" | tail -n 1 | sed 's/HTTP Status: //')
    vote_body=$(echo "$vote_response" | sed '$d')
    
    if [[ "$vote_status" -ge 400 ]]; then
        log_error "Vote failed"
        echo "Response: $vote_body" >&2
        exit 1
    fi
    log_success "Vote submitted successfully"
    echo ""
    
    # Step 7: Get poll results
    log_info "Step 7: Get poll results"
    local results_status
    results_status=$(make_request "GET" "${BASE_URL}/api/polls/${poll_id}/results" "$token" "" "")
    if [[ "$results_status" -ge 400 ]]; then
        log_error "Get poll results failed"
        exit 1
    fi
    log_success "Get poll results passed"
    echo ""
    
    # Success!
    log_success "SMOKE OK - All tests passed!"
}

# Main API request function
api_request() {
    local method="$1"
    local path="$2"
    local token="$3"
    local json_data="$4"
    local json_file="$5"
    
    local url="${BASE_URL}${path}"
    local http_status
    
    http_status=$(make_request "$method" "$url" "$token" "$json_data" "$json_file")
    
    # Exit with error status for HTTP 4xx/5xx (except for login)
    if [[ "$http_status" -ge 400 ]]; then
        return 1
    fi
    return 0
}

# Show help
show_help() {
    cat << EOF
Usage: $0 [-X METHOD] [-d JSON] [-f FILE.json] [-t TOKEN] <PATH>
       $0 login <username> <password>
       $0 smoke

The Commons API CLI Tool

Commands:
  login <username> <password>    Authenticate and print access token
  smoke                          Run end-to-end smoke test

Options:
  -X METHOD    HTTP method (GET, POST, PUT, DELETE, PATCH) [default: GET]
  -d JSON      JSON data to send in request body
  -f FILE.json JSON file to send in request body
  -t TOKEN     JWT token for authentication
  -h, --help   Show this help message

Environment Variables:
  BASE_URL     API base URL [default: http://localhost:8000]
  SMOKE_USER   Username for smoke test [default: alice_community]
  SMOKE_PASS   Password for smoke test [default: password123]

Examples:
  $0 /api/health
  $0 -X POST -d '{"title":"Test"}' /api/polls/
  $0 -X POST -f data.json /api/polls/ -t \$TOKEN
  $0 login alice_community password123
  $0 smoke

  # Login and use token in one command:
  TOKEN=\$($0 login alice_community password123)
  $0 /api/polls/ -t "\$TOKEN"
EOF
}

# Main script logic
main() {
    # Check dependencies first
    check_dependencies
    
    # Handle subcommands
    case "${1:-}" in
        "login")
            if [[ $# -ne 3 ]]; then
                log_error "Login requires username and password"
                echo "Usage: $0 login <username> <password>" >&2
                exit 1
            fi
            login "$2" "$3"
            exit 0
            ;;
        "smoke")
            smoke
            exit 0
            ;;
        "-h"|"--help"|"help")
            show_help
            exit 0
            ;;
    esac
    
    # Parse options for API requests
    local method="$DEFAULT_METHOD"
    local json_data=""
    local json_file=""
    local token=""
    local path=""
    
    # Parse command line arguments
    while [[ $# -gt 0 ]]; do
        case $1 in
            -X)
                method="$2"
                shift 2
                ;;
            -d)
                json_data="$2"
                shift 2
                ;;
            -f)
                json_file="$2"
                shift 2
                ;;
            -t)
                token="$2"
                shift 2
                ;;
            -h|--help)
                show_help
                exit 0
                ;;
            -*)
                log_error "Unknown option: $1"
                echo "Use -h for help" >&2
                exit 1
                ;;
            *)
                if [[ -z "$path" ]]; then
                    path="$1"
                else
                    log_error "Too many arguments"
                    echo "Use -h for help" >&2
                    exit 1
                fi
                shift
                ;;
        esac
    done
    
    # Set default path if not provided
    path="${path:-/api/polls/}"
    
    # Validate inputs
    if [[ -n "$json_data" && -n "$json_file" ]]; then
        log_error "Cannot use both -d and -f options"
        exit 1
    fi
    
    if [[ -n "$json_file" && ! -f "$json_file" ]]; then
        log_error "JSON file not found: $json_file"
        exit 1
    fi
    
    # Make the API request
    if ! api_request "$method" "$path" "$token" "$json_data" "$json_file"; then
        exit 1
    fi
}

# Run main function with all arguments
main "$@"
