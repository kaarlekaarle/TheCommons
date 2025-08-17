#!/usr/bin/env python3
"""
Promote to Fail Guard.

Checks for specific constitutional red-flags that should fail the build even in WARN mode.
"""

import argparse
import json
import os
import sys
from typing import Any, Dict, List, Optional


def load_perf_thresholds() -> Dict[str, Any]:
    """Load performance thresholds configuration."""
    try:
        with open("backend/config/perf_thresholds.json", "r") as f:
            return json.load(f)
    except Exception as e:
        print(f"Error loading perf thresholds: {e}")
        # Fallback to default thresholds
        return {
            "override_latency": {
                "p95_slo_ms": 1500,
                "grace_ms": 50,
                "stale_hours": 24
            }
        }

def load_warnings_ledger(ledger_path: str) -> List[Dict[str, Any]]:
    """Load warnings ledger from file."""
    if not os.path.exists(ledger_path):
        print(f"⚠️  Warnings ledger not found: {ledger_path}")
        return []

    try:
        with open(ledger_path, "r") as f:
            data = json.load(f)
            return data if isinstance(data, list) else data.get("warnings", [])
    except (json.JSONDecodeError, IOError) as e:
        print(f"❌ Could not load warnings ledger: {e}")
        return []


def check_visibility_regression(warnings: List[Dict[str, Any]]) -> Optional[str]:
    """Check for delegation chain visibility regression."""
    visibility_keywords = [
        "delegation chain visibility decreased",
        "chain visibility decrease",
        "transparency drop",
        "hidden layer",
        "opacity increase",
    ]

    for warning in warnings:
        summary = warning.get("summary", "").lower()
        details = warning.get("details", "").lower()
        severity = warning.get("severity", "").upper()

        # Check for visibility regression keywords
        for keyword in visibility_keywords:
            if keyword in summary or keyword in details:
                if severity in ["HIGH", "CRITICAL"]:
                    return f"Visibility regression detected: {warning.get('summary', 'Unknown')}"

    return None


def check_override_latency_regression(warnings: List[Dict[str, Any]]) -> Optional[str]:
    """Check for override latency regression (signal #2 with HIGH/CRITICAL severity)."""
    # Load unified performance thresholds
    perf_thresholds = load_perf_thresholds()
    slo = perf_thresholds["override_latency"]["p95_slo_ms"]
    grace = perf_thresholds["override_latency"]["grace_ms"]
    stale_hours = perf_thresholds["override_latency"]["stale_hours"]
    effective_block = slo + grace
    
    for warning in warnings:
        # Check if this is a cascade rule with signal #2
        cascade_signals = warning.get("cascade_signals", [])
        if "#2" in cascade_signals:
            severity = warning.get("severity", "").upper()
            if severity in ["HIGH", "CRITICAL"]:
                # Check for stale snapshot first
                details = warning.get("details", "").lower()
                if "stale" in details or "snapshot stale" in details:
                    print(f"⚠️  Stale latency snapshot detected (>{stale_hours}h) - not failing build")
                    return None

                # Check for latency threshold in details
                if "latency" in details:
                    # Extract p95 value if present (preferred metric)
                    import re

                    p95_match = re.search(r"p95[:\s]*(\d+)ms", details, re.IGNORECASE)
                    if p95_match:
                        p95_ms = int(p95_match.group(1))
                        # Extract p99 for context
                        p99_match = re.search(
                            r"p99[:\s]*(\d+)ms", details, re.IGNORECASE
                        )
                        p99_ms = int(p99_match.group(1)) if p99_match else 0

                        if p95_ms >= effective_block:
                            return (
                                f"Override latency regression: p95={p95_ms}ms, "
                                f"p99={p99_ms}ms, slo={slo}ms, grace={grace}ms, effective_block={effective_block}ms"
                            )
                    else:
                        # Fallback to general latency extraction
                        latency_match = re.search(r"(\d+)ms", details)
                        if latency_match:
                            latency_ms = int(latency_match.group(1))
                            if latency_ms >= effective_block:
                                return (
                                    f"Override latency regression: p95={latency_ms}ms, "
                                    f"p99=unknown, slo={slo}ms, grace={grace}ms, effective_block={effective_block}ms"
                                )
                        else:
                            return (
                                f"Override latency regression detected "
                                f"(signal #2, {severity})"
                            )

    return None


def check_promote_to_fail_conditions(warnings: List[Dict[str, Any]]) -> List[str]:
    """Check all promote-to-fail conditions."""
    failures = []

    # Check visibility regression
    visibility_issue = check_visibility_regression(warnings)
    if visibility_issue:
        failures.append(visibility_issue)

    # Check override latency regression
    latency_issue = check_override_latency_regression(warnings)
    if latency_issue:
        failures.append(latency_issue)

    return failures


def main() -> None:
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Promote to fail guard for constitutional red-flags"
    )
    parser.add_argument(
        "--warnings",
        default="reports/constitutional_warnings.json",
        help="Path to warnings ledger JSON file",
    )
    parser.add_argument(
        "--override",
        action="store_true",
        help="Override flag is set (constitutional-override label)",
    )

    args = parser.parse_args()

    print("🔍 PROMOTE TO FAIL GUARD")
    print("=" * 30)

    # Load warnings
    warnings = load_warnings_ledger(args.warnings)
    print(f"📊 Loaded {len(warnings)} warnings from ledger")

    # Check conditions
    failures = check_promote_to_fail_conditions(warnings)

    if failures:
        print("")
        print("❌ PROMOTE TO FAIL CONDITIONS DETECTED")
        print("=" * 40)
        for failure in failures:
            print(f"• {failure}")
        print("")

        if args.override:
            print("🚨 OVERRIDE DETECTED - Build will continue")
            print("⚠️  24-hour re-check required")
            print("📋 Please address the constitutional drift before next deployment")
            sys.exit(0)
        else:
            print("🔒 BUILD FAILED - Constitutional red-flags detected")
            print("")
            print("To override (emergency only):")
            print("1. Add 'constitutional-override' label to PR")
            print("2. Provide justification in PR description")
            print("3. Create 24-hour re-check ticket")
            print("")
            print("Red-flag conditions:")
            print("• Delegation chain visibility decreased (HIGH/CRITICAL)")
            print("• Override latency ≥1600ms (signal #2, HIGH/CRITICAL)")
            sys.exit(20)
    else:
        print("✅ No promote-to-fail conditions detected")
        print("🚀 Build can proceed normally")
        sys.exit(0)


if __name__ == "__main__":
    main()
