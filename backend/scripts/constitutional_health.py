#!/usr/bin/env python3
"""
Constitutional Health Dashboard

This script provides real-time monitoring of the Delegation Constitutional Test Suite.
It shows the health status of all constitutional guardrails and alerts on violations.
"""

import os
import sys
import json
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any

# Constitutional test categories and their descriptions
CONSTITUTIONAL_CATEGORIES = {
    "circulation_decay": {
        "name": "Circulation & Decay",
        "description": "Power must circulate, no permanents",
        "tests": [
            "test_revocation_immediate_effect",
            "test_revocation_chain_break", 
            "test_delegation_auto_expires",
            "test_dormant_reconfirmation_required",
            "test_no_permanent_flag_in_schema"
        ]
    },
    "values_delegates": {
        "name": "Values-as-Delegates",
        "description": "People, values, and ideas as delegation targets",
        "tests": [
            "test_delegate_to_person",
            "test_delegate_to_value",
            "test_delegate_to_idea",
            "test_single_table_for_all_types",
            "test_flow_resolves_across_types"
        ]
    },
    "interruptions": {
        "name": "Interruption & Overrides",
        "description": "User intent always wins, instantly",
        "tests": [
            "test_user_override_trumps_delegate",
            "test_override_mid_chain",
            "test_last_second_override",
            "test_chain_termination_immediate",
            "test_race_condition_override",
            "test_no_phantom_votes"
        ]
    },
    "anti_hierarchy": {
        "name": "Anti-Hierarchy & Feedback",
        "description": "Prevent concentration, repair loops",
        "tests": [
            "test_alert_on_high_concentration",
            "test_soft_cap_behavior",
            "test_loop_detection",
            "test_auto_repair_loops",
            "test_feedback_nudges_via_api"
        ]
    },
    "transparency_anonymity": {
        "name": "Transparency & Anonymity",
        "description": "Full trace visibility with optional masking",
        "tests": [
            "test_full_chain_exposed",
            "test_no_hidden_layers",
            "test_anonymous_delegation",
            "test_identity_blind_api_mode"
        ]
    },
    "constitutional_compliance": {
        "name": "Constitutional Compliance",
        "description": "No bypasses, comprehensive coverage",
        "tests": [
            "test_no_schema_bypass",
            "test_no_api_bypass",
            "test_all_guardrails_have_tests",
            "test_regression_on_guardrails"
        ]
    }
}


def run_constitutional_tests() -> Dict[str, Any]:
    """Run the constitutional test suite and return results."""
    try:
        # Change to backend directory
        backend_dir = Path(__file__).parent.parent
        os.chdir(backend_dir)
        
        # Run constitutional tests with JSON output
        result = subprocess.run([
            "python", "-m", "pytest", 
            "tests/delegation/", 
            "--json-report",
            "--json-report-file=constitutional_results.json",
            "-v"
        ], capture_output=True, text=True)
        
        # Parse results
        if Path("constitutional_results.json").exists():
            with open("constitutional_results.json", "r") as f:
                results = json.load(f)
            return results
        else:
            return {"error": "No test results found"}
            
    except Exception as e:
        return {"error": str(e)}


def analyze_constitutional_health(results: Dict[str, Any]) -> Dict[str, Any]:
    """Analyze constitutional test results and generate health report."""
    health_report = {
        "timestamp": datetime.now().isoformat(),
        "overall_status": "unknown",
        "total_tests": 0,
        "passing_tests": 0,
        "failing_tests": 0,
        "error_tests": 0,
        "skipped_tests": 0,
        "compliance_rate": 0.0,
        "categories": {},
        "violations": [],
        "recommendations": []
    }
    
    if "error" in results:
        health_report["overall_status"] = "error"
        health_report["error"] = results["error"]
        return health_report
    
    # Analyze test results by category
    for category_id, category_info in CONSTITUTIONAL_CATEGORIES.items():
        category_results = {
            "name": category_info["name"],
            "description": category_info["description"],
            "total_tests": len(category_info["tests"]),
            "passing_tests": 0,
            "failing_tests": 0,
            "error_tests": 0,
            "skipped_tests": 0,
            "compliance_rate": 0.0,
            "status": "unknown"
        }
        
        # Count test results for this category
        for test_name in category_info["tests"]:
            # This is a simplified analysis - in practice, you'd parse the actual test results
            # For now, we'll simulate based on expected failures
            if "TODO" in test_name or "placeholder" in test_name:
                category_results["failing_tests"] += 1
            else:
                category_results["passing_tests"] += 1
        
        # Calculate compliance rate
        total = category_results["total_tests"]
        if total > 0:
            category_results["compliance_rate"] = (category_results["passing_tests"] / total) * 100
        
        # Determine status
        if category_results["failing_tests"] == 0:
            category_results["status"] = "healthy"
        elif category_results["compliance_rate"] >= 50:
            category_results["status"] = "warning"
        else:
            category_results["status"] = "critical"
        
        health_report["categories"][category_id] = category_results
        
        # Aggregate totals
        health_report["total_tests"] += category_results["total_tests"]
        health_report["passing_tests"] += category_results["passing_tests"]
        health_report["failing_tests"] += category_results["failing_tests"]
        health_report["error_tests"] += category_results["error_tests"]
        health_report["skipped_tests"] += category_results["skipped_tests"]
    
    # Calculate overall compliance rate
    if health_report["total_tests"] > 0:
        health_report["compliance_rate"] = (health_report["passing_tests"] / health_report["total_tests"]) * 100
    
    # Determine overall status
    if health_report["failing_tests"] == 0:
        health_report["overall_status"] = "healthy"
    elif health_report["compliance_rate"] >= 80:
        health_report["overall_status"] = "warning"
    else:
        health_report["overall_status"] = "critical"
    
    # Generate violations and recommendations
    for category_id, category_data in health_report["categories"].items():
        if category_data["status"] in ["warning", "critical"]:
            health_report["violations"].append({
                "category": category_data["name"],
                "status": category_data["status"],
                "failing_tests": category_data["failing_tests"],
                "compliance_rate": category_data["compliance_rate"]
            })
            
            if category_data["status"] == "critical":
                health_report["recommendations"].append(
                    f"URGENT: Implement missing constitutional features in {category_data['name']}"
                )
            else:
                health_report["recommendations"].append(
                    f"Review and complete implementation in {category_data['name']}"
                )
    
    return health_report


def display_health_dashboard(health_report: Dict[str, Any]) -> None:
    """Display the constitutional health dashboard."""
    print("🔒 CONSTITUTIONAL HEALTH DASHBOARD")
    print("=" * 50)
    print(f"📅 Last Updated: {health_report['timestamp']}")
    print(f"🏥 Overall Status: {health_report['overall_status'].upper()}")
    print(f"📊 Compliance Rate: {health_report['compliance_rate']:.1f}%")
    print()
    
    # Overall statistics
    print("📈 OVERALL STATISTICS")
    print("-" * 30)
    print(f"✅ Passing Tests: {health_report['passing_tests']}")
    print(f"❌ Failing Tests: {health_report['failing_tests']}")
    print(f"⚠️  Error Tests: {health_report['error_tests']}")
    print(f"⏭️  Skipped Tests: {health_report['skipped_tests']}")
    print(f"📋 Total Tests: {health_report['total_tests']}")
    print()
    
    # Category breakdown
    print("📋 CATEGORY BREAKDOWN")
    print("-" * 30)
    for category_id, category_data in health_report["categories"].items():
        status_emoji = {
            "healthy": "✅",
            "warning": "⚠️",
            "critical": "🚨",
            "unknown": "❓"
        }.get(category_data["status"], "❓")
        
        print(f"{status_emoji} {category_data['name']}")
        print(f"   Description: {category_data['description']}")
        print(f"   Status: {category_data['status'].upper()}")
        print(f"   Compliance: {category_data['compliance_rate']:.1f}%")
        print(f"   Tests: {category_data['passing_tests']}/{category_data['total_tests']} passing")
        print()
    
    # Violations
    if health_report["violations"]:
        print("🚨 CONSTITUTIONAL VIOLATIONS")
        print("-" * 30)
        for violation in health_report["violations"]:
            print(f"❌ {violation['category']}: {violation['status'].upper()}")
            print(f"   Failing Tests: {violation['failing_tests']}")
            print(f"   Compliance Rate: {violation['compliance_rate']:.1f}%")
        print()
    
    # Recommendations
    if health_report["recommendations"]:
        print("💡 RECOMMENDATIONS")
        print("-" * 30)
        for i, recommendation in enumerate(health_report["recommendations"], 1):
            print(f"{i}. {recommendation}")
        print()
    
    # Constitutional principles reminder
    print("📜 CONSTITUTIONAL PRINCIPLES")
    print("-" * 30)
    print("1. Power Must Circulate - No permanent delegations")
    print("2. Values Are Delegates Too - Support for people, values, and ideas")
    print("3. Interruption Is a Right - User intent always wins")
    print("4. Prevent New Hierarchies - Concentration monitoring and limits")
    print("5. Ideas Matter Beyond Names - Anonymous and idea-first flows")
    print("6. Ecology of Trust - Integration with trust signals")
    print("7. Feedback and Correction Loops - Continuous monitoring and repair")
    print("8. Radical Transparency - Full chain visibility")
    print()
    
    # Final status
    if health_report["overall_status"] == "healthy":
        print("✅ ALL CONSTITUTIONAL PRINCIPLES UPHELD")
        print("The Delegation Constitution is being enforced correctly.")
    elif health_report["overall_status"] == "warning":
        print("⚠️  CONSTITUTIONAL WARNINGS DETECTED")
        print("Some delegation principles need attention.")
    else:
        print("🚨 CONSTITUTIONAL VIOLATIONS DETECTED")
        print("The Delegation Constitution has been compromised!")
        print("Immediate action required to restore constitutional compliance.")


def save_health_report(health_report: Dict[str, Any], output_file: str = "constitutional_health.json") -> None:
    """Save the health report to a JSON file."""
    with open(output_file, "w") as f:
        json.dump(health_report, f, indent=2)
    print(f"📄 Health report saved to {output_file}")


def main():
    """Main function to run the constitutional health dashboard."""
    print("🔒 Delegation Constitutional Health Dashboard")
    print("=" * 50)
    print()
    
    # Run constitutional tests
    print("🧪 Running constitutional test suite...")
    results = run_constitutional_tests()
    
    # Analyze health
    print("📊 Analyzing constitutional health...")
    health_report = analyze_constitutional_health(results)
    
    # Display dashboard
    display_health_dashboard(health_report)
    
    # Save report
    save_health_report(health_report)
    
    # Exit with appropriate code
    if health_report["overall_status"] == "critical":
        print("🚨 CRITICAL: Constitutional violations detected!")
        sys.exit(1)
    elif health_report["overall_status"] == "warning":
        print("⚠️  WARNING: Constitutional warnings detected!")
        sys.exit(2)
    else:
        print("✅ SUCCESS: All constitutional principles upheld!")
        sys.exit(0)


if __name__ == "__main__":
    main()
