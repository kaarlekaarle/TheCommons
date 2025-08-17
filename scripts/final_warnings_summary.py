#!/usr/bin/env python3
"""
Final Constitutional Warnings Summary

This script provides the final console summary for the Past Warnings Ledger.
"""

import json
from datetime import datetime

def main():
    """Print the final console summary."""
    
    # Read the warnings ledger
    with open("reports/constitutional_warnings.json", "r") as f:
        data = json.load(f)
    
    summary = data["summary"]
    warnings = data["warnings"]
    
    # Count warnings touching core principles
    core_principle_warnings = [w for w in warnings if w.get("core_principles_touched")]
    
    # Find promote-to-fail candidates
    promote_candidates = []
    for warning in warnings:
        if warning.get("core_principles_touched") and warning.get("severity") in ["medium", "low"]:
            promote_candidates.append({
                "summary": warning.get("summary"),
                "core_principles": warning.get("core_principles_touched"),
                "current_severity": warning.get("severity"),
                "timestamp": warning.get("timestamp")
            })
    
    # Sort by timestamp (most recent first)
    promote_candidates.sort(key=lambda x: x["timestamp"], reverse=True)
    
    print("\n" + "="*80)
    print("🎯 CONSTITUTIONAL WARNINGS LEDGER - FINAL SUMMARY")
    print("="*80)
    print(f"📊 Total warnings found: {summary['total_warnings']}")
    print(f"🎯 Count touching core-principle proxies: {len(core_principle_warnings)}")
    print(f"🚨 Suggested immediate 'promote-to-fail' candidates: {len(promote_candidates)}")
    
    if promote_candidates:
        print(f"\n🚨 SUGGESTED IMMEDIATE 'PROMOTE-TO-FAIL' CANDIDATES:")
        for i, candidate in enumerate(promote_candidates[:3], 1):
            print(f"  {i}. {candidate['summary']}")
            print(f"     Touches: {', '.join(candidate['core_principles'])}")
            print(f"     Current: {candidate['current_severity']} → Suggested: critical")
            print()
    
    print(f"\n📄 Files ready for review:")
    print(f"  ✅ reports/constitutional_warnings.json")
    print(f"  ✅ reports/constitutional_warnings.md")
    
    print(f"\n🔍 Sources processed:")
    for source in data["metadata"]["sources_processed"]:
        print(f"  • {source}")
    
    print(f"\n📈 Key metrics:")
    print(f"  • Phase 5.5 warnings: {summary['by_phase'].get('5.5', 0)}")
    print(f"  • Phase 6.3 warnings: {summary['by_phase'].get('6.3', 0)}")
    print(f"  • Phase 6.4 warnings: {summary['by_phase'].get('6.4', 0)}")
    print(f"  • High severity: {summary['by_severity'].get('high', 0)}")
    print(f"  • Medium severity: {summary['by_severity'].get('medium', 0)}")
    print(f"  • Warning severity: {summary['by_severity'].get('warning', 0)}")
    
    print(f"\n🎯 Core principles touched:")
    principle_counts = {}
    for warning in core_principle_warnings:
        for principle in warning.get("core_principles_touched", []):
            principle_counts[principle] = principle_counts.get(principle, 0) + 1
    
    for principle, count in sorted(principle_counts.items()):
        print(f"  • {principle.replace('_', ' ').title()}: {count} warnings")
    
    print(f"\n✅ Past Warnings Ledger complete and operational!")
    print("="*80)

if __name__ == "__main__":
    main()
