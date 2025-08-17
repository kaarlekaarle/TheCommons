#!/usr/bin/env python3
"""
Constitutional Warnings Tools

CLI tools for managing and cleaning up constitutional warnings ledger.
"""

import os
import sys
import json
import argparse
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from pathlib import Path


def load_warnings_ledger(ledger_path: str) -> List[Dict[str, Any]]:
    """Load warnings ledger from file."""
    if not os.path.exists(ledger_path):
        print(f"❌ Warnings ledger not found: {ledger_path}")
        return []

    try:
        with open(ledger_path, "r") as f:
            data = json.load(f)
            return data if isinstance(data, list) else data.get("warnings", [])
    except (json.JSONDecodeError, IOError) as e:
        print(f"❌ Could not load warnings ledger: {e}")
        return []


def save_warnings_ledger(ledger_path: str, warnings: List[Dict[str, Any]]) -> None:
    """Save warnings ledger to file."""
    os.makedirs(os.path.dirname(ledger_path), exist_ok=True)
    with open(ledger_path, "w") as f:
        json.dump(warnings, f, indent=2)


def dedupe_latency_warnings(warnings: List[Dict[str, Any]], max_age_hours: int = 24) -> List[Dict[str, Any]]:
    """Deduplicate and downshift stale latency warnings."""
    print(f"🔍 Processing {len(warnings)} warnings for stale latency deduplication...")
    
    processed_warnings = []
    downshifted_count = 0
    
    for warning in warnings:
        # Check if this is a latency-related warning
        is_latency_warning = False
        
        # Check cascade signals for #2 (override latency)
        cascade_signals = warning.get("cascade_signals", [])
        if "#2" in cascade_signals:
            is_latency_warning = True
        
        # Check summary/details for latency keywords
        summary = warning.get("summary", "").lower()
        details = warning.get("details", "").lower()
        if "latency" in summary or "latency" in details or "override" in summary or "override" in details:
            is_latency_warning = True
        
        if is_latency_warning:
            # Check snapshot age
            snapshot_age_hours = warning.get("snapshot_age_hours")
            if snapshot_age_hours and snapshot_age_hours > max_age_hours:
                # Downshift stale latency warnings
                original_severity = warning.get("severity", "unknown")
                warning["severity"] = "info"
                warning["tags"] = warning.get("tags", []) + ["stale-snapshot"]
                warning["details"] = warning.get("details", "") + f" [NOTE: Stale snapshot ({snapshot_age_hours:.1f}h old) - downshifted from {original_severity}]"
                downshifted_count += 1
                print(f"   ⚠️  Downshifted stale latency warning: {original_severity} → info (age: {snapshot_age_hours:.1f}h)")
        
        processed_warnings.append(warning)
    
    print(f"✅ Processed {len(warnings)} warnings, downshifted {downshifted_count} stale latency entries")
    return processed_warnings


def main() -> None:
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Constitutional Warnings Tools",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    
    subparsers = parser.add_subparsers(dest="command", help="Available commands")
    
    # Dedupe latency subcommand
    dedupe_parser = subparsers.add_parser(
        "warnings:dedupe-latency",
        help="Deduplicate and downshift stale latency warnings"
    )
    dedupe_parser.add_argument(
        "--max-age-hours",
        type=int,
        default=24,
        help="Maximum age in hours before considering snapshot stale (default: 24)"
    )
    dedupe_parser.add_argument(
        "--file",
        default="reports/constitutional_warnings.json",
        help="Path to warnings ledger file (default: reports/constitutional_warnings.json)"
    )
    
    args = parser.parse_args()
    
    if args.command == "warnings:dedupe-latency":
        print("🧹 CONSTITUTIONAL WARNINGS LATENCY DEDUPLICATION")
        print("=" * 50)
        
        # Load warnings
        warnings = load_warnings_ledger(args.file)
        if not warnings:
            print("ℹ️  No warnings found to process")
            return
        
        print(f"📊 Loaded {len(warnings)} warnings from {args.file}")
        print(f"⏰ Max age threshold: {args.max_age_hours} hours")
        
        # Process warnings
        processed_warnings = dedupe_latency_warnings(warnings, args.max_age_hours)
        
        # Save back to file
        save_warnings_ledger(args.file, processed_warnings)
        print(f"💾 Updated warnings saved to {args.file}")
        
        # Summary
        print("")
        print("📋 SUMMARY")
        print("=" * 20)
        print(f"• Total warnings processed: {len(warnings)}")
        print(f"• Stale latency warnings downshifted: {sum(1 for w in processed_warnings if 'stale-snapshot' in w.get('tags', []))}")
        print(f"• File updated: {args.file}")
        
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
