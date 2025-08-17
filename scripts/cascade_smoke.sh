#!/bin/bash
# Cascade Smoke Test
#
# This script synthesizes test signals to verify selective enforcement behavior:
# - Rule B: Should BLOCK (enforce mode) when #2=CRITICAL + #3=HIGH
# - Rule C: Should BLOCK (enforce mode) when #3=HIGH + #4=HIGH
# - Rule A: Should WARN (warn mode) when #1=CRITICAL + #4=HIGH
# - Rule D: Should WARN (warn mode) when #2=HIGH + #4=HIGH

set -e

echo "🚀 CASCADE SMOKE TEST"
echo "===================="
echo ""

# Create temporary directory for test artifacts
TEMP_DIR=$(mktemp -d)
echo "📁 Test directory: $TEMP_DIR"

# Function to create test signals
create_test_signals() {
    local test_name=$1
    local signal_2_ms=$2
    local signal_3_flows=$3
    local signal_4_pct=$4
    
    echo "🧪 Creating test: $test_name"
    
    # Create signal #2 (override latency) if specified
    if [ -n "$signal_2_ms" ]; then
        cat > "$TEMP_DIR/signal_override_latency.json" << EOF
{
  "override_latency_ms": $signal_2_ms,
  "poll_id": "test-poll-123",
  "user_id": "test-user",
  "ts": "$(date -u +"%Y-%m-%dT%H:%M:%S.%3NZ")"
}
EOF
        echo "  ✅ Created signal #2: ${signal_2_ms}ms override latency"
    fi
    
    # Create signal #3 (complexity) if specified
    if [ -n "$signal_3_flows" ]; then
        cat > "$TEMP_DIR/signal_complexity.json" << EOF
{
  "flows": $signal_3_flows,
  "module": "delegations",
  "ts": "$(date -u +"%Y-%m-%dT%H:%M:%S.%3NZ")"
}
EOF
        echo "  ✅ Created signal #3: ${signal_3_flows} flows complexity"
    fi
    
    # Create signal #4 (maintainer concentration) if specified
    if [ -n "$signal_4_pct" ]; then
        cat > "$TEMP_DIR/signal_maintainer.json" << EOF
{
  "pct": $signal_4_pct,
  "top_maintainer": "test-maintainer",
  "ts": "$(date -u +"%Y-%m-%dT%H:%M:%S.%3NZ")"
}
EOF
        echo "  ✅ Created signal #4: ${signal_4_pct}% maintainer concentration"
    fi
}

# Function to run cascade detector and check exit code
run_cascade_test() {
    local test_name=$1
    local expected_exit=$2
    
    echo ""
    echo "🔍 Running cascade test: $test_name"
    echo "Expected exit code: $expected_exit"
    echo ""
    
    # Run cascade detector
    python3 backend/scripts/constitutional_cascade_detector.py \
        --mode warn \
        --json-out "$TEMP_DIR/cascade_result.json" \
        --config backend/config/constitutional_cascade_rules.json
    
    actual_exit=$?
    echo ""
    echo "📊 Test Results:"
    echo "  Expected exit: $expected_exit"
    echo "  Actual exit: $actual_exit"
    
    if [ "$actual_exit" -eq "$expected_exit" ]; then
        echo "  ✅ PASS: Exit code matches expectation"
    else
        echo "  ❌ FAIL: Exit code mismatch"
        echo "  Expected $expected_exit but got $actual_exit"
        exit 1
    fi
    
    # Show cascade summary
    if [ -f "$TEMP_DIR/cascade_result.json" ]; then
        echo ""
        echo "📋 Cascade Summary:"
        jq -r '.summary // "No summary"' "$TEMP_DIR/cascade_result.json"
        
        echo ""
        echo "🔍 Triggered Rules:"
        jq -r '.cascade_results[] | "Rule \(.rule_id): \(.decision) (\(.effective_mode))"' "$TEMP_DIR/cascade_result.json" 2>/dev/null || echo "No rules triggered"
    fi
}

# Test 1: Rule B should BLOCK (enforce mode)
echo "🧪 TEST 1: Rule B Enforcement"
echo "============================="
echo "Signal #2: CRITICAL (2100ms) + Signal #3: HIGH (7 flows)"
echo "Expected: BLOCK (exit code 10) - Rule B is in enforce mode"
echo ""

create_test_signals "Rule B Test" 2100 7

# Mock the signal collection by creating expected files
mkdir -p reports
cp "$TEMP_DIR/signal_override_latency.json" reports/signal_override_latency.json 2>/dev/null || true
cp "$TEMP_DIR/signal_complexity.json" reports/signal_complexity.json 2>/dev/null || true

run_cascade_test "Rule B" 10

# Test 2: Rule C should BLOCK (enforce mode)
echo ""
echo "🧪 TEST 2: Rule C Enforcement"
echo "============================="
echo "Signal #3: HIGH (7 flows) + Signal #4: HIGH (80%)"
echo "Expected: BLOCK (exit code 10) - Rule C is in enforce mode"
echo ""

create_test_signals "Rule C Test" "" 7 80

# Mock the signal collection
cp "$TEMP_DIR/signal_complexity.json" reports/signal_complexity.json 2>/dev/null || true
cp "$TEMP_DIR/signal_maintainer.json" reports/signal_maintainer.json 2>/dev/null || true

run_cascade_test "Rule C" 10

# Test 3: Rule A should WARN (warn mode)
echo ""
echo "🧪 TEST 3: Rule A Warning"
echo "========================="
echo "Signal #1: CRITICAL + Signal #4: HIGH (80%)"
echo "Expected: WARN (exit code 8) - Rule A is in warn mode"
echo ""

# Create super-delegate signal
cat > reports/signal_super_delegate.json << EOF
{
  "super_delegate_detected": true,
  "files": ["test_delegation.py"],
  "patterns": ["multiple override authority"]
}
EOF

create_test_signals "Rule A Test" "" "" 80
cp "$TEMP_DIR/signal_maintainer.json" reports/signal_maintainer.json 2>/dev/null || true

run_cascade_test "Rule A" 8

# Test 4: Rule D should WARN (warn mode)
echo ""
echo "🧪 TEST 4: Rule D Warning"
echo "========================="
echo "Signal #2: HIGH (1600ms) + Signal #4: HIGH (80%)"
echo "Expected: WARN (exit code 8) - Rule D is in warn mode"
echo ""

create_test_signals "Rule D Test" 1600 "" 80
cp "$TEMP_DIR/signal_override_latency.json" reports/signal_override_latency.json 2>/dev/null || true
cp "$TEMP_DIR/signal_maintainer.json" reports/signal_maintainer.json 2>/dev/null || true

run_cascade_test "Rule D" 8

# Cleanup
echo ""
echo "🧹 Cleaning up test artifacts..."
rm -rf "$TEMP_DIR"
rm -f reports/signal_*.json

echo ""
echo "✅ ALL CASCADE SMOKE TESTS PASSED"
echo "=================================="
echo ""
echo "Summary:"
echo "  ✅ Rule B: Properly enforced (BLOCK on CRITICAL + HIGH)"
echo "  ✅ Rule C: Properly enforced (BLOCK on HIGH + HIGH)"
echo "  ✅ Rule A: Properly warned (WARN on CRITICAL + HIGH)"
echo "  ✅ Rule D: Properly warned (WARN on HIGH + HIGH)"
echo ""
echo "Selective enforcement is working correctly!"
echo "Rules B and C are in enforce mode, A and D are in warn mode."
