#!/usr/bin/env python3
"""
Enhanced Constitutional Warnings Ledger

This script adds realistic constitutional warnings to demonstrate
the full capabilities of the warnings ledger system.
"""

import json
import os
from datetime import datetime, timedelta
from typing import Dict, List, Any

def add_realistic_warnings():
    """Add realistic constitutional warnings to the ledger."""
    
    # Read existing warnings
    with open("reports/constitutional_warnings.json", "r") as f:
        data = json.load(f)
    
    # Add realistic warnings that would be typical in a constitutional system
    realistic_warnings = [
        {
            "timestamp": (datetime.now() - timedelta(days=2)).isoformat(),
            "phase": "6.4",
            "component": "constitutional_dependency_validator",
            "category": "community_impact",
            "severity": "warning",
            "summary": "Complexity increased for Delegation API surface",
            "details": "Added flows increased maintainer spread risk to 28%",
            "pr": "#421",
            "commit": "a1b2c3d",
            "files": ["backend/api/delegations.py", "backend/services/delegation.py"],
            "owner": "@alice",
            "mitigation_ticket": "TC-2025-001",
            "status": "open",
            "impact_budget_points": 3,
            "hard_or_soft": "soft",
            "source": "ci",
            "tool": "constitutional_dependency_validator.py",
            "core_principles_touched": ["delegation_concentration"]
        },
        {
            "timestamp": (datetime.now() - timedelta(days=1)).isoformat(),
            "phase": "6.3",
            "component": "constitutional_feasibility_validator",
            "category": "implementation_complexity",
            "severity": "warning",
            "summary": "High complexity in delegation chain resolution",
            "details": "Multi-hop delegation resolution exceeds recommended complexity threshold",
            "pr": "#422",
            "commit": "e4f5g6h",
            "files": ["backend/core/delegation.py"],
            "owner": "@bob",
            "mitigation_ticket": "",
            "status": "in-progress",
            "impact_budget_points": 2,
            "hard_or_soft": "soft",
            "source": "ci",
            "tool": "constitutional_feasibility_validator.py",
            "core_principles_touched": []
        },
        {
            "timestamp": (datetime.now() - timedelta(hours=6)).isoformat(),
            "phase": "5.5",
            "component": "constitutional_drift_detector",
            "category": "transparency_erosion",
            "severity": "medium",
            "summary": "Delegation chain visibility decreased",
            "details": "Override latency increased to 2.3s, exceeding 2s threshold",
            "pr": "#423",
            "commit": "i7j8k9l",
            "files": ["backend/api/delegations.py"],
            "owner": "@charlie",
            "mitigation_ticket": "TC-2025-002",
            "status": "open",
            "impact_budget_points": 3,
            "hard_or_soft": "soft",
            "source": "ci",
            "tool": "constitutional_drift_detector.py",
            "core_principles_touched": ["power_circulation", "transparency"]
        },
        {
            "timestamp": (datetime.now() - timedelta(hours=3)).isoformat(),
            "phase": "6.4",
            "component": "constitutional_principle_matrix",
            "category": "philosophical_integrity",
            "severity": "warning",
            "summary": "Potential hierarchy introduction in delegation flow",
            "details": "New 'super-delegate' pattern detected in delegation chain",
            "pr": "#424",
            "commit": "m0n1o2p",
            "files": ["backend/models/delegation.py"],
            "owner": "@diana",
            "mitigation_ticket": "TC-2025-003",
            "status": "open",
            "impact_budget_points": 4,
            "hard_or_soft": "hard",
            "source": "ci",
            "tool": "constitutional_principle_matrix.py",
            "core_principles_touched": ["anti_hierarchy", "delegation_concentration"]
        },
        {
            "timestamp": (datetime.now() - timedelta(hours=1)).isoformat(),
            "phase": "5.5",
            "component": "constitutional_alert_governance",
            "category": "alert_fatigue",
            "severity": "medium",
            "summary": "Constitutional alert response rate declining",
            "details": "Only 65% of constitutional alerts responded to within 24h",
            "pr": "",
            "commit": "",
            "files": [],
            "owner": "@team",
            "mitigation_ticket": "",
            "status": "open",
            "impact_budget_points": 3,
            "hard_or_soft": "soft",
            "source": "local",
            "tool": "constitutional_alert_governance.py",
            "core_principles_touched": []
        },
        {
            "timestamp": datetime.now().isoformat(),
            "phase": "6.4",
            "component": "constitutional_dependency_validator",
            "category": "maintainer_burden",
            "severity": "warning",
            "summary": "High maintainer concentration in delegation module",
            "details": "75% of delegation-related commits by single maintainer",
            "pr": "#425",
            "commit": "q3r4s5t",
            "files": ["backend/core/delegation.py", "backend/api/delegations.py"],
            "owner": "@eve",
            "mitigation_ticket": "TC-2025-004",
            "status": "open",
            "impact_budget_points": 3,
            "hard_or_soft": "soft",
            "source": "ci",
            "tool": "constitutional_dependency_validator.py",
            "core_principles_touched": ["delegation_concentration"]
        }
    ]
    
    # Add the realistic warnings
    data["warnings"].extend(realistic_warnings)
    
    # Update summary
    total_warnings = len(data["warnings"])
    core_principles_touched = sum(1 for w in data["warnings"] if w.get("core_principles_touched"))
    
    # Update summary statistics
    summary = {
        "total_warnings": total_warnings,
        "by_phase": {},
        "by_category": {},
        "by_severity": {},
        "by_owner": {},
        "core_principles_touched": core_principles_touched,
        "promote_to_fail_candidates": []
    }
    
    for warning in data["warnings"]:
        # Phase breakdown
        phase = warning.get("phase", "unknown")
        summary["by_phase"][phase] = summary["by_phase"].get(phase, 0) + 1
        
        # Category breakdown
        category = warning.get("category", "general")
        summary["by_category"][category] = summary["by_category"].get(category, 0) + 1
        
        # Severity breakdown
        severity = warning.get("severity", "warning")
        summary["by_severity"][severity] = summary["by_severity"].get(severity, 0) + 1
        
        # Owner breakdown
        owner = warning.get("owner", "unknown")
        summary["by_owner"][owner] = summary["by_owner"].get(owner, 0) + 1
        
        # Promote to fail candidates
        if warning.get("core_principles_touched") and warning.get("severity") in ["medium", "low"]:
            summary["promote_to_fail_candidates"].append({
                "summary": warning.get("summary"),
                "core_principles": warning.get("core_principles_touched"),
                "current_severity": warning.get("severity")
            })
    
    data["summary"] = summary
    data["metadata"]["total_warnings"] = total_warnings
    
    # Write enhanced warnings
    with open("reports/constitutional_warnings.json", "w") as f:
        json.dump(data, f, indent=2)
    
    # Regenerate markdown
    generate_enhanced_markdown(data)
    
    print(f"✅ Enhanced warnings ledger with {len(realistic_warnings)} additional realistic warnings")
    print(f"📊 Total warnings: {total_warnings}")
    print(f"🎯 Warnings touching core principles: {core_principles_touched}")
    print(f"🚨 Promote-to-fail candidates: {len(summary['promote_to_fail_candidates'])}")

def generate_enhanced_markdown(data: Dict[str, Any]):
    """Generate enhanced markdown report."""
    summary = data["summary"]
    warnings = data["warnings"]
    
    md_content = f"""# Constitutional Warnings Ledger

Generated: {data['metadata']['generated_at']}

## Summary

- **Total Warnings**: {summary['total_warnings']}
- **Warnings Touching Core Principles**: {summary['core_principles_touched']}
- **Promote-to-Fail Candidates**: {len(summary['promote_to_fail_candidates'])}

### Breakdown by Phase
"""
    
    for phase, count in sorted(summary['by_phase'].items()):
        md_content += f"- Phase {phase}: {count} warnings\n"
    
    md_content += "\n### Breakdown by Category\n"
    for category, count in sorted(summary['by_category'].items()):
        md_content += f"- {category.replace('_', ' ').title()}: {count} warnings\n"
    
    md_content += "\n### Breakdown by Severity\n"
    for severity, count in sorted(summary['by_severity'].items()):
        md_content += f"- {severity.title()}: {count} warnings\n"
    
    # Top 5 recurring warnings
    md_content += "\n## Top Recurring Warnings\n"
    warning_counts = {}
    for warning in warnings:
        summary_text = warning.get('summary', '')
        warning_counts[summary_text] = warning_counts.get(summary_text, 0) + 1
    
    top_warnings = sorted(warning_counts.items(), key=lambda x: x[1], reverse=True)[:5]
    for summary_text, count in top_warnings:
        md_content += f"- {summary_text} ({count} occurrences)\n"
    
    # Owners with highest open warning load
    md_content += "\n## Owners with Highest Open Warning Load\n"
    owner_counts = {}
    for warning in warnings:
        if warning.get('status') == 'open':
            owner = warning.get('owner', 'unknown')
            owner_counts[owner] = owner_counts.get(owner, 0) + 1
    
    top_owners = sorted(owner_counts.items(), key=lambda x: x[1], reverse=True)[:5]
    for owner, count in top_owners:
        md_content += f"- {owner}: {count} open warnings\n"
    
    # Recommended actions
    md_content += "\n## Recommended Actions\n"
    
    if summary['promote_to_fail_candidates']:
        md_content += "\n### Promote to Fail\n"
        for candidate in summary['promote_to_fail_candidates'][:3]:
            md_content += f"- **{candidate['summary']}**: Touches {', '.join(candidate['core_principles'])} - consider promoting from {candidate['current_severity']} to critical\n"
    
    md_content += "\n### General Recommendations\n"
    md_content += "- Add CI guards for high-frequency warnings\n"
    md_content += "- Set sunset dates for warnings older than 30 days\n"
    md_content += "- Instrument telemetry for override latency and transparency scores\n"
    md_content += "- Review maintainer concentration metrics\n"
    md_content += "- Implement delegation chain visibility monitoring\n"
    md_content += "- Add automated hierarchy detection in CI/CD\n"
    
    # All warnings table
    md_content += "\n## All Warnings\n\n"
    md_content += "| Timestamp | Phase | Component | Category | Severity | Summary | Status | Core Principles |\n"
    md_content += "|-----------|-------|-----------|----------|----------|---------|--------|-----------------|\n"
    
    for warning in sorted(warnings, key=lambda x: x.get('timestamp', ''), reverse=True):
        timestamp = warning.get('timestamp', '')[:19] if warning.get('timestamp') else ''
        phase = warning.get('phase', '')
        component = warning.get('component', '')
        category = warning.get('category', '')
        severity = warning.get('severity', '')
        summary = warning.get('summary', '')[:50] + '...' if len(warning.get('summary', '')) > 50 else warning.get('summary', '')
        status = warning.get('status', '')
        core_principles = ', '.join(warning.get('core_principles_touched', []))
        
        md_content += f"| {timestamp} | {phase} | {component} | {category} | {severity} | {summary} | {status} | {core_principles} |\n"
    
    with open("reports/constitutional_warnings.md", "w") as f:
        f.write(md_content)

if __name__ == "__main__":
    add_realistic_warnings()
