#!/bin/bash

# Demo script for testing cascade detector cases
# This script runs 6 scenarios mirroring the spec's Test Plan

set -e

echo "🧪 CASCADE DETECTOR DEMO CASES"
echo "==============================="
echo ""

# Create reports directory
mkdir -p reports

# Case 1: Single WARN (should not block)
echo "📋 Case 1: Single WARN (should not block)"
echo "----------------------------------------"
cp reports/examples/signal_complexity.json reports/signal_complexity.json
python3 backend/scripts/constitutional_cascade_detector.py --mode shadow --json-out reports/case1_cascade.json
echo "Expected: No cascade rules triggered"
echo ""

# Case 2: (#3 high + #4 high) within 14d → BLOCK
echo "📋 Case 2: (#3 high + #4 high) within 14d → BLOCK"
echo "------------------------------------------------"
cp reports/examples/signal_complexity.json reports/signal_complexity.json
cp reports/examples/signal_maintainers.json reports/signal_maintainers.json
python3 backend/scripts/constitutional_cascade_detector.py --mode shadow --json-out reports/case2_cascade.json
echo "Expected: Rule C triggered (knowledge silos)"
echo ""

# Case 3: (#2 critical + #3 high) same PR → BLOCK
echo "📋 Case 3: (#2 critical + #3 high) same PR → BLOCK"
echo "------------------------------------------------"
cp reports/examples/signal_override_latency.json reports/signal_override_latency.json
cp reports/examples/signal_complexity.json reports/signal_complexity.json
python3 backend/scripts/constitutional_cascade_detector.py --mode shadow --json-out reports/case3_cascade.json
echo "Expected: Rule B triggered (opacity + complexity)"
echo ""

# Case 4: (#1 + #4) → BLOCK (hierarchy in model + hierarchy in maintainers)
echo "📋 Case 4: (#1 + #4) → BLOCK (hierarchy in model + hierarchy in maintainers)"
echo "---------------------------------------------------------------------------"
cp reports/examples/signal_super_delegate.json reports/signal_super_delegate.json
cp reports/examples/signal_maintainers.json reports/signal_maintainers.json
python3 backend/scripts/constitutional_cascade_detector.py --mode shadow --json-out reports/case4_cascade.json
echo "Expected: Rule A triggered (formal + informal hierarchy)"
echo ""

# Case 5: Recovery (unblocks after metrics improve)
echo "📋 Case 5: Recovery (unblocks after metrics improve)"
echo "---------------------------------------------------"
# Create a "recovered" signal with low values
cat > reports/signal_override_latency.json << EOF
{
  "override_latency_ms": 800,
  "threshold_exceeded": false,
  "timestamp": "2025-08-17T12:00:00Z"
}
EOF
cat > reports/signal_complexity.json << EOF
{
  "timestamp": "2025-08-17T12:00:00Z",
  "modules": {
    "delegations": 3,
    "delegation_service": 2
  },
  "total_flows": 5,
  "files_analyzed": 8
}
EOF
python3 backend/scripts/constitutional_cascade_detector.py --mode shadow --json-out reports/case5_cascade.json
echo "Expected: No cascade rules triggered (recovery)"
echo ""

# Case 6: Insufficient maintainer sample → ignored
echo "📋 Case 6: Insufficient maintainer sample → ignored"
echo "--------------------------------------------------"
cat > reports/signal_maintainers.json << EOF
{
  "timestamp": "2025-08-17T12:00:00Z",
  "concentration_percentage": 100.0,
  "top_maintainer": "alice",
  "total_commits": 3,
  "maintainer_stats": {
    "alice": 3
  },
  "lookback_days": 30,
  "files_analyzed": 5
}
EOF
python3 backend/scripts/constitutional_cascade_detector.py --mode shadow --json-out reports/case6_cascade.json
echo "Expected: Signal #4 ignored due to insufficient commits (<5)"
echo ""

echo "✅ All demo cases completed!"
echo ""
echo "📊 Results summary:"
echo "Case 1: $(jq -r '.summary' reports/case1_cascade.json)"
echo "Case 2: $(jq -r '.summary' reports/case2_cascade.json)"
echo "Case 3: $(jq -r '.summary' reports/case3_cascade.json)"
echo "Case 4: $(jq -r '.summary' reports/case4_cascade.json)"
echo "Case 5: $(jq -r '.summary' reports/case5_cascade.json)"
echo "Case 6: $(jq -r '.summary' reports/case6_cascade.json)"
echo ""
echo "📄 Detailed reports saved in reports/case*_cascade.json"
