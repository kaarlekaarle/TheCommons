#!/usr/bin/env python3
"""
Constitutional Warnings Ledger Builder

This script harvests warnings from all constitutional enforcement systems
and creates a unified, deduplicated ledger of constitutional warnings.
"""

import json
import os
import sys
import re
from datetime import datetime
from typing import Dict, List, Any, Optional
from pathlib import Path

# Core principle proxy detection patterns
CORE_PRINCIPLE_PATTERNS = {
    "power_circulation": [
        r"override\s+latency", r"user\s+override\s+delay", r"intent\s+not\s+winning",
        r"race\s+conditions", r"frozen.*delegation", r"persistent.*delegation",
        r"non-revocable", r"permanent.*delegation", r"unalterable.*delegation"
    ],
    "transparency": [
        r"transparency\s+drop", r"chain\s+visibility\s+decrease", r"hidden\s+layer",
        r"opacity", r"obscured", r"concealed"
    ],
    "delegation_concentration": [
        r"delegation\s+concentration", r"super-delegate", r">\s*5%\s*share",
        r"maintainer\s+concentration", r"power\s+concentration"
    ],
    "anti_hierarchy": [
        r"hierarchy", r"authority", r"centralized", r"top-down", r"command.*control"
    ]
}

def detect_core_principle_proxies(text: str) -> List[str]:
    """Detect if text touches core principle proxies."""
    text_lower = text.lower()
    touched_principles = []
    
    for principle, patterns in CORE_PRINCIPLE_PATTERNS.items():
        for pattern in patterns:
            if re.search(pattern, text_lower):
                touched_principles.append(principle)
                break
    
    return list(set(touched_principles))

def normalize_warning(warning_data: Dict[str, Any], source: str, tool: str) -> Dict[str, Any]:
    """Normalize a warning to the standard schema."""
    timestamp = warning_data.get("timestamp", datetime.now().isoformat())
    
    # Extract severity
    severity = warning_data.get("severity", "warning")
    if isinstance(severity, str) and severity.lower() in ["critical", "high", "medium", "low"]:
        severity = severity.lower()
    else:
        severity = "warning"
    
    # Extract summary and details
    summary = warning_data.get("summary", warning_data.get("description", warning_data.get("message", "")))
    details = warning_data.get("details", warning_data.get("reasoning", ""))
    
    # Detect core principle proxies
    full_text = f"{summary} {details}".lower()
    core_principles = detect_core_principle_proxies(full_text)
    
    # Determine phase based on tool
    phase_map = {
        "cdr_integration_cli": "5.5",
        "constitutional_drift_detector": "5.5", 
        "constitutional_amendment_validator": "6.4",
        "constitutional_feasibility_validator": "6.3",
        "constitutional_dependency_validator": "6.4"
    }
    phase = phase_map.get(tool, "unknown")
    
    # Determine category
    category = warning_data.get("category", "general")
    
    # Determine impact budget points (1-5 scale)
    impact_budget = 1
    if "critical" in severity or "high" in severity:
        impact_budget = 4
    elif "medium" in severity:
        impact_budget = 3
    elif "low" in severity:
        impact_budget = 2
    
    # Determine hard/soft classification
    hard_or_soft = "hard" if "critical" in severity or "high" in severity else "soft"
    
    return {
        "timestamp": timestamp,
        "phase": phase,
        "component": tool,
        "category": category,
        "severity": severity,
        "summary": summary,
        "details": details,
        "pr": warning_data.get("pr", ""),
        "commit": warning_data.get("commit", ""),
        "files": warning_data.get("files", []),
        "owner": warning_data.get("owner", ""),
        "mitigation_ticket": warning_data.get("mitigation_ticket", ""),
        "status": warning_data.get("status", "open"),
        "impact_budget_points": impact_budget,
        "hard_or_soft": hard_or_soft,
        "source": source,
        "tool": tool,
        "core_principles_touched": core_principles
    }

def extract_warnings_from_cdr_analysis(file_path: str) -> List[Dict[str, Any]]:
    """Extract warnings from CDR integration CLI analysis."""
    warnings = []
    
    try:
        with open(file_path, 'r') as f:
            data = json.load(f)
        
        # Extract from drift detection
        if "components" in data and "drift_detection" in data["components"]:
            drift_data = data["components"]["drift_detection"]
            
            for category, cat_data in drift_data.get("categories", {}).items():
                for signal_name, signal_data in cat_data.get("signals", {}).items():
                    if signal_data.get("severity") in ["medium", "high"]:
                        warnings.append({
                            "timestamp": data.get("timestamp", ""),
                            "severity": signal_data.get("severity", "warning"),
                            "summary": f"{category.replace('_', ' ').title()} drift detected",
                            "details": signal_data.get("description", ""),
                            "category": category,
                            "value": signal_data.get("value", 0)
                        })
        
        # Extract from recommendations
        for component_name, component_data in data.get("components", {}).items():
            if "recommendations" in component_data:
                for rec in component_data["recommendations"]:
                    if any(word in rec.lower() for word in ["review", "improve", "activate", "reinforce"]):
                        warnings.append({
                            "timestamp": data.get("timestamp", ""),
                            "severity": "medium",
                            "summary": f"{component_name} recommendation",
                            "details": rec,
                            "category": "recommendation"
                        })
    
    except Exception as e:
        print(f"Error processing CDR analysis: {e}")
    
    return warnings

def extract_warnings_from_health_check(file_path: str) -> List[Dict[str, Any]]:
    """Extract warnings from constitutional health check."""
    warnings = []
    
    try:
        with open(file_path, 'r') as f:
            data = json.load(f)
        
        # Look for health issues
        if data.get("overall_status") == "ERROR":
            warnings.append({
                "timestamp": data.get("last_updated", ""),
                "severity": "high",
                "summary": "Constitutional health check failed",
                "details": "Overall status is ERROR",
                "category": "health_check"
            })
        
        # Look for compliance issues
        compliance_rate = data.get("compliance_rate", 100)
        if compliance_rate < 100:
            warnings.append({
                "timestamp": data.get("last_updated", ""),
                "severity": "medium",
                "summary": f"Constitutional compliance rate is {compliance_rate}%",
                "details": "Below 100% compliance rate",
                "category": "compliance"
            })
    
    except Exception as e:
        print(f"Error processing health check: {e}")
    
    return warnings

def extract_warnings_from_amendment_db(file_path: str) -> List[Dict[str, Any]]:
    """Extract warnings from amendment database."""
    warnings = []
    
    try:
        with open(file_path, 'r') as f:
            data = json.load(f)
        
        for amendment in data:
            for warning in amendment.get("warnings", []):
                warnings.append({
                    "timestamp": amendment.get("timestamp", ""),
                    "severity": warning.get("severity", "warning"),
                    "summary": f"Amendment {amendment.get('amendment_id', 'unknown')} warning",
                    "details": warning.get("message", ""),
                    "category": warning.get("check", "amendment"),
                    "amendment_id": amendment.get("amendment_id"),
                    "amendment_type": amendment.get("type")
                })
    
    except Exception as e:
        print(f"Error processing amendment DB: {e}")
    
    return warnings

def deduplicate_warnings(warnings: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Deduplicate warnings based on key fields."""
    seen = set()
    deduplicated = []
    
    for warning in warnings:
        # Create a unique key for deduplication
        key = (
            warning.get("phase", ""),
            warning.get("tool", ""),
            warning.get("summary", ""),
            tuple(sorted(warning.get("files", []))),
            warning.get("commit", "")
        )
        
        if key not in seen:
            seen.add(key)
            deduplicated.append(warning)
    
    return deduplicated

def generate_warnings_summary(warnings: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Generate summary statistics for warnings."""
    summary = {
        "total_warnings": len(warnings),
        "by_phase": {},
        "by_category": {},
        "by_severity": {},
        "by_owner": {},
        "core_principles_touched": 0,
        "promote_to_fail_candidates": []
    }
    
    for warning in warnings:
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
        
        # Core principles touched
        if warning.get("core_principles_touched"):
            summary["core_principles_touched"] += 1
        
        # Promote to fail candidates
        if warning.get("core_principles_touched") and warning.get("severity") in ["medium", "low"]:
            summary["promote_to_fail_candidates"].append({
                "summary": warning.get("summary"),
                "core_principles": warning.get("core_principles_touched"),
                "current_severity": warning.get("severity")
            })
    
    return summary

def main():
    """Main function to build the warnings ledger."""
    print("🔍 Building Constitutional Warnings Ledger...")
    
    warnings = []
    
    # Process CDR integration CLI analysis
    cdr_file = "reports/_cli_full_analysis.json"
    if os.path.exists(cdr_file):
        print(f"📊 Processing {cdr_file}...")
        cdr_warnings = extract_warnings_from_cdr_analysis(cdr_file)
        for warning in cdr_warnings:
            warning["source"] = "local"
            warning["tool"] = "cdr_integration_cli"
        warnings.extend(cdr_warnings)
    
    # Process health check
    health_file = "reports/_health.json"
    if os.path.exists(health_file):
        print(f"🏥 Processing {health_file}...")
        health_warnings = extract_warnings_from_health_check(health_file)
        for warning in health_warnings:
            warning["source"] = "local"
            warning["tool"] = "constitutional_health"
        warnings.extend(health_warnings)
    
    # Process amendment database
    amendment_db_file = "reports/_amendment_db_warnings.json"
    if os.path.exists(amendment_db_file):
        print(f"📝 Processing {amendment_db_file}...")
        amendment_warnings = extract_warnings_from_amendment_db(amendment_db_file)
        for warning in amendment_warnings:
            warning["source"] = "local"
            warning["tool"] = "constitutional_amendment_validator"
        warnings.extend(amendment_warnings)
    
    # Normalize all warnings
    print("🔄 Normalizing warnings...")
    normalized_warnings = []
    for warning in warnings:
        normalized = normalize_warning(warning, warning.get("source", "local"), warning.get("tool", "unknown"))
        normalized_warnings.append(normalized)
    
    # Deduplicate warnings
    print("🔗 Deduplicating warnings...")
    deduplicated_warnings = deduplicate_warnings(normalized_warnings)
    
    # Generate summary
    print("📈 Generating summary...")
    summary = generate_warnings_summary(deduplicated_warnings)
    
    # Write JSON output
    output_data = {
        "metadata": {
            "generated_at": datetime.now().isoformat(),
            "total_warnings": len(deduplicated_warnings),
            "sources_processed": ["cdr_integration_cli", "constitutional_health", "amendment_db"],
            "missing_sources": []
        },
        "summary": summary,
        "warnings": deduplicated_warnings
    }
    
    with open("reports/constitutional_warnings.json", "w") as f:
        json.dump(output_data, f, indent=2)
    
    # Generate markdown report
    generate_markdown_report(output_data)
    
    # Print console summary
    print("\n" + "="*60)
    print("📋 CONSTITUTIONAL WARNINGS LEDGER SUMMARY")
    print("="*60)
    print(f"Total warnings found: {len(deduplicated_warnings)}")
    print(f"Warnings touching core principles: {summary['core_principles_touched']}")
    print(f"Promote-to-fail candidates: {len(summary['promote_to_fail_candidates'])}")
    
    if summary['promote_to_fail_candidates']:
        print("\n🚨 SUGGESTED IMMEDIATE PROMOTE-TO-FAIL CANDIDATES:")
        for candidate in summary['promote_to_fail_candidates'][:3]:
            print(f"  • {candidate['summary']} (touches: {', '.join(candidate['core_principles'])})")
    
    print(f"\n📄 Files ready for review:")
    print(f"  • reports/constitutional_warnings.json")
    print(f"  • reports/constitutional_warnings.md")

def generate_markdown_report(data: Dict[str, Any]):
    """Generate human-friendly markdown report."""
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
    main()
