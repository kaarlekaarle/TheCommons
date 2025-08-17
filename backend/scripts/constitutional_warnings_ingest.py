#!/usr/bin/env python3
"""
Constitutional Warnings Ingest

Ingests cascade decisions into the warnings ledger for unified constitutional signal review.
"""

import os
import sys
import json
import argparse
from datetime import datetime
from typing import Dict, List, Any, Optional
from pathlib import Path


def load_warnings_ledger(ledger_path: str) -> List[Dict[str, Any]]:
    """Load existing warnings ledger or create new one."""
    if os.path.exists(ledger_path):
        try:
            with open(ledger_path, 'r') as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError) as e:
            print(f"Warning: Could not load warnings ledger: {e}")
            return []
    return []


def save_warnings_ledger(ledger_path: str, warnings: List[Dict[str, Any]]) -> None:
    """Save warnings ledger to file."""
    os.makedirs(os.path.dirname(ledger_path), exist_ok=True)
    with open(ledger_path, 'w') as f:
        json.dump(warnings, f, indent=2)


def normalize_cascade_to_warning(cascade_data: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Convert cascade decision to normalized warning format."""
    warnings = []
    
    # Extract basic cascade info
    timestamp = cascade_data.get("timestamp", datetime.now().isoformat())
    cascade_results = cascade_data.get("cascade_results", [])
    
    for result in cascade_results:
        rule_id = result.get("rule_id", "unknown")
        decision = result.get("decision", "unknown")
        rationale = result.get("rationale", "")
        triggered_signals = result.get("triggered_signals", [])
        
        # Map decision to severity
        if decision.lower() == "block":
            severity = "critical"
        elif decision.lower() == "warn":
            severity = "warning"
        else:
            severity = "info"
        
        # Create normalized warning
        warning = {
            "timestamp": timestamp,
            "phase": "6.4",  # Cascade phase
            "component": "constitutional_cascade_detector",
            "category": f"cascade_rule_{rule_id.lower()}",
            "severity": severity,
            "summary": f"Cascade Rule {rule_id} triggered: {rationale}",
            "details": f"Decision: {decision.upper()}, Signals: {len(triggered_signals)}",
            "pr": None,  # Will be filled by workflow
            "commit": None,  # Will be filled by workflow
            "files": [],  # Could be extracted from signals if available
            "owner": None,
            "mitigation_ticket": None,
            "status": "open",
            "impact_budget_points": 5 if severity == "critical" else 3 if severity == "warning" else 1,
            "hard_or_soft": "hard" if severity == "critical" else "soft",
            "source": "ci",
            "tool": "constitutional_cascade_detector.py",
            "cascade_rule_id": rule_id,
            "cascade_decision": decision,
            "cascade_signals": [s.get("id", "unknown") for s in triggered_signals]
        }
        
        warnings.append(warning)
    
    return warnings


def deduplicate_warnings(warnings: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Deduplicate warnings by (rule, signals, timestamp minute)."""
    seen = set()
    unique_warnings = []
    
    for warning in warnings:
        # Create deduplication key
        rule_id = warning.get("cascade_rule_id", "unknown")
        signals = tuple(sorted(warning.get("cascade_signals", [])))
        timestamp = warning.get("timestamp", "")
        # Round to minute for deduplication
        if timestamp:
            try:
                dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                minute_key = dt.strftime('%Y-%m-%d %H:%M')
            except:
                minute_key = timestamp[:16]  # First 16 chars for YYYY-MM-DD HH:MM
        else:
            minute_key = "unknown"
        
        dedup_key = (rule_id, signals, minute_key)
        
        if dedup_key not in seen:
            seen.add(dedup_key)
            unique_warnings.append(warning)
    
    return unique_warnings


def ingest_cascade_to_ledger(cascade_path: str, ledger_path: str, append: bool = True) -> None:
    """Ingest cascade decisions into warnings ledger."""
    print(f"📥 Ingesting cascade decisions from {cascade_path} to {ledger_path}")
    
    # Load cascade data
    if not os.path.exists(cascade_path):
        print(f"❌ Cascade file not found: {cascade_path}")
        return
    
    try:
        with open(cascade_path, 'r') as f:
            cascade_data = json.load(f)
    except (json.JSONDecodeError, IOError) as e:
        print(f"❌ Could not load cascade data: {e}")
        return
    
    # Load existing warnings
    warnings = load_warnings_ledger(ledger_path) if append else []
    
    # Convert cascade to warnings
    new_warnings = normalize_cascade_to_warning(cascade_data)
    
    if not new_warnings:
        print("ℹ️  No cascade decisions to ingest")
        return
    
    # Add new warnings
    warnings.extend(new_warnings)
    
    # Deduplicate
    original_count = len(warnings)
    warnings = deduplicate_warnings(warnings)
    removed_count = original_count - len(warnings)
    
    # Save updated ledger
    save_warnings_ledger(ledger_path, warnings)
    
    print(f"✅ Ingested {len(new_warnings)} cascade decisions")
    if removed_count > 0:
        print(f"ℹ️  Removed {removed_count} duplicate warnings")
    print(f"📊 Total warnings in ledger: {len(warnings)}")


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(description="Ingest cascade decisions into warnings ledger")
    parser.add_argument("--from-cascade", required=True, help="Path to cascade JSON file")
    parser.add_argument("--to", required=True, help="Path to warnings ledger JSON file")
    parser.add_argument("--append", action="store_true", default=True, help="Append to existing ledger (default)")
    parser.add_argument("--replace", action="store_true", help="Replace existing ledger")
    
    args = parser.parse_args()
    
    # Validate arguments
    if args.append and args.replace:
        print("❌ Cannot specify both --append and --replace")
        sys.exit(1)
    
    append = args.append and not args.replace
    
    # Run ingestion
    ingest_cascade_to_ledger(args.from_cascade, args.to, append)
    
    print("✅ Cascade ingestion complete")


if __name__ == "__main__":
    main()
