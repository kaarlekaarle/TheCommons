#!/usr/bin/env python3
"""
Constitutional Drift Resistance (CDR) Integration CLI

This script provides a unified command-line interface for all CDR operations,
integrating drift detection, resistance mechanisms, philosophical preservation,
alert governance, scheduled audits, and transparency dashboard functionality.
"""

import os
import sys
import json
import argparse
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
import subprocess

# Import all CDR components
try:
    from constitutional_drift_detector import ConstitutionalDriftDetector
    from constitutional_drift_resistance import ConstitutionalDriftResistance
    from constitutional_philosophical_preservation import ConstitutionalPhilosophicalPreservation
    from constitutional_alert_governance import ConstitutionalAlertGovernance
    from constitutional_scheduled_audits import ConstitutionalScheduledAudits
    from constitutional_drift_dashboard import ConstitutionalDriftDashboard
    from constitutional_philosophical_hooks import ConstitutionalPhilosophicalHooks
except ImportError as e:
    print(f"Warning: Could not import CDR modules: {e}")
    print("Some functionality may be limited.")
    ConstitutionalDriftDetector = None
    ConstitutionalDriftResistance = None
    ConstitutionalPhilosophicalPreservation = None
    ConstitutionalAlertGovernance = None
    ConstitutionalScheduledAudits = None
    ConstitutionalDriftDashboard = None
    ConstitutionalPhilosophicalHooks = None


class CDRIntegrationCLI:
    """Unified CLI for Constitutional Drift Resistance operations."""
    
    def __init__(self):
        self.components = {
            'detector': ConstitutionalDriftDetector() if ConstitutionalDriftDetector else None,
            'resistance': ConstitutionalDriftResistance() if ConstitutionalDriftResistance else None,
            'preservation': ConstitutionalPhilosophicalPreservation() if ConstitutionalPhilosophicalPreservation else None,
            'governance': ConstitutionalAlertGovernance() if ConstitutionalAlertGovernance else None,
            'audits': ConstitutionalScheduledAudits() if ConstitutionalScheduledAudits else None,
            'dashboard': ConstitutionalDriftDashboard() if ConstitutionalDriftDashboard else None,
            'hooks': ConstitutionalPhilosophicalHooks() if ConstitutionalPhilosophicalHooks else None
        }
    
    def run_full_cdr_analysis(self, output_file: Optional[str] = None) -> Dict[str, Any]:
        """Run comprehensive CDR analysis across all components."""
        print("🔍 CONSTITUTIONAL DRIFT RESISTANCE - FULL ANALYSIS")
        print("=" * 60)
        print(f"Timestamp: {datetime.now().isoformat()}")
        print()
        
        results = {
            "timestamp": datetime.now().isoformat(),
            "overall_status": "unknown",
            "components": {},
            "recommendations": [],
            "critical_issues": [],
            "health_score": 0.0
        }
        
        # Run drift detection
        if self.components['detector']:
            print("1️⃣ Running Constitutional Drift Detection...")
            try:
                drift_results = self.components['detector'].run_drift_analysis()
                results["components"]["drift_detection"] = drift_results
                print(f"   ✅ Drift Detection: {drift_results.get('overall_risk_level', 'unknown')} risk")
            except Exception as e:
                print(f"   ❌ Drift Detection failed: {e}")
                results["components"]["drift_detection"] = {"error": str(e)}
        
        # Run philosophical preservation
        if self.components['preservation']:
            print("2️⃣ Running Philosophical Preservation Assessment...")
            try:
                preservation_results = self.components['preservation'].run_philosophical_preservation_assessment()
                results["components"]["philosophical_preservation"] = preservation_results
                print(f"   ✅ Philosophical Preservation: {preservation_results.get('overall_integrity', 'unknown')} integrity")
            except Exception as e:
                print(f"   ❌ Philosophical Preservation failed: {e}")
                results["components"]["philosophical_preservation"] = {"error": str(e)}
        
        # Run drift resistance status
        if self.components['resistance']:
            print("3️⃣ Checking Drift Resistance Mechanisms...")
            try:
                resistance_results = self.components['resistance'].run_drift_resistance_implementation()
                results["components"]["drift_resistance"] = resistance_results
                print(f"   ✅ Drift Resistance: {resistance_results.get('overall_status', 'unknown')} status")
            except Exception as e:
                print(f"   ❌ Drift Resistance failed: {e}")
                results["components"]["drift_resistance"] = {"error": str(e)}
        
        # Run alert governance
        if self.components['governance']:
            print("4️⃣ Checking Alert Governance...")
            try:
                governance_results = self.components['governance'].run_alert_governance_assessment()
                results["components"]["alert_governance"] = governance_results
                print(f"   ✅ Alert Governance: {governance_results.get('overall_status', 'unknown')} status")
            except Exception as e:
                print(f"   ❌ Alert Governance failed: {e}")
                results["components"]["alert_governance"] = {"error": str(e)}
        
        # Run scheduled audit
        if self.components['audits']:
            print("5️⃣ Running Scheduled Audit...")
            try:
                audit_results = self.components['audits'].run_scheduled_audit("manual")
                results["components"]["scheduled_audit"] = audit_results
                print(f"   ✅ Scheduled Audit: {audit_results.get('overall_health', 'unknown')} health")
            except Exception as e:
                print(f"   ❌ Scheduled Audit failed: {e}")
                results["components"]["scheduled_audit"] = {"error": str(e)}
        
        # Generate dashboard
        if self.components['dashboard']:
            print("6️⃣ Generating Transparency Dashboard...")
            try:
                dashboard_results = self.components['dashboard'].generate_dashboard_data()
                results["components"]["transparency_dashboard"] = dashboard_results
                print(f"   ✅ Transparency Dashboard: {dashboard_results.get('overall_health', 'unknown')} health")
            except Exception as e:
                print(f"   ❌ Transparency Dashboard failed: {e}")
                results["components"]["transparency_dashboard"] = {"error": str(e)}
        
        # Calculate overall status
        results["overall_status"] = self._calculate_overall_status(results)
        results["health_score"] = self._calculate_health_score(results)
        results["recommendations"] = self._generate_recommendations(results)
        results["critical_issues"] = self._identify_critical_issues(results)
        
        # Display summary
        print()
        print("📊 ANALYSIS SUMMARY")
        print("=" * 30)
        print(f"Overall Status: {results['overall_status']}")
        print(f"Health Score: {results['health_score']:.1f}%")
        print(f"Critical Issues: {len(results['critical_issues'])}")
        print(f"Recommendations: {len(results['recommendations'])}")
        
        if results["critical_issues"]:
            print()
            print("🚨 CRITICAL ISSUES:")
            for issue in results["critical_issues"]:
                print(f"   • {issue}")
        
        if results["recommendations"]:
            print()
            print("💡 RECOMMENDATIONS:")
            for rec in results["recommendations"][:5]:  # Show top 5
                print(f"   • {rec}")
        
        # Save results if requested
        if output_file:
            with open(output_file, 'w') as f:
                json.dump(results, f, indent=2)
            print(f"\n📄 Results saved to: {output_file}")
        
        return results
    
    def run_drift_detection(self, output_file: Optional[str] = None) -> Dict[str, Any]:
        """Run constitutional drift detection."""
        if not self.components['detector']:
            print("❌ Drift detection component not available")
            return {}
        
        print("🔍 RUNNING CONSTITUTIONAL DRIFT DETECTION")
        print("=" * 40)
        
        results = self.components['detector'].run_drift_analysis()
        
        if output_file:
            with open(output_file, 'w') as f:
                json.dump(results, f, indent=2)
            print(f"📄 Results saved to: {output_file}")
        
        return results
    
    def run_philosophical_preservation(self, output_file: Optional[str] = None) -> Dict[str, Any]:
        """Run philosophical preservation assessment."""
        if not self.components['preservation']:
            print("❌ Philosophical preservation component not available")
            return {}
        
        print("🏛️ RUNNING PHILOSOPHICAL PRESERVATION ASSESSMENT")
        print("=" * 50)
        
        results = self.components['preservation'].run_philosophical_preservation_assessment()
        
        if output_file:
            with open(output_file, 'w') as f:
                json.dump(results, f, indent=2)
            print(f"📄 Results saved to: {output_file}")
        
        return results
    
    def run_drift_resistance(self, output_file: Optional[str] = None) -> Dict[str, Any]:
        """Run drift resistance implementation."""
        if not self.components['resistance']:
            print("❌ Drift resistance component not available")
            return {}
        
        print("🛡️ RUNNING DRIFT RESISTANCE IMPLEMENTATION")
        print("=" * 45)
        
        results = self.components['resistance'].run_drift_resistance_implementation()
        
        if output_file:
            with open(output_file, 'w') as f:
                json.dump(results, f, indent=2)
            print(f"📄 Results saved to: {output_file}")
        
        return results
    
    def run_alert_governance(self, output_file: Optional[str] = None) -> Dict[str, Any]:
        """Run alert governance assessment."""
        if not self.components['governance']:
            print("❌ Alert governance component not available")
            return {}
        
        print("🔔 RUNNING ALERT GOVERNANCE ASSESSMENT")
        print("=" * 40)
        
        results = self.components['governance'].run_alert_governance_assessment()
        
        if output_file:
            with open(output_file, 'w') as f:
                json.dump(results, f, indent=2)
            print(f"📄 Results saved to: {output_file}")
        
        return results
    
    def run_scheduled_audit(self, audit_type: str = "daily", output_file: Optional[str] = None) -> Dict[str, Any]:
        """Run scheduled constitutional audit."""
        if not self.components['audits']:
            print("❌ Scheduled audits component not available")
            return {}
        
        print(f"📅 RUNNING SCHEDULED CONSTITUTIONAL AUDIT: {audit_type.upper()}")
        print("=" * 55)
        
        results = self.components['audits'].run_scheduled_audit(audit_type)
        
        if output_file:
            with open(output_file, 'w') as f:
                json.dump(results, f, indent=2)
            print(f"📄 Results saved to: {output_file}")
        
        return results
    
    def generate_dashboard(self, output_file: Optional[str] = None) -> Dict[str, Any]:
        """Generate transparency dashboard."""
        if not self.components['dashboard']:
            print("❌ Dashboard component not available")
            return {}
        
        print("📊 GENERATING TRANSPARENCY DASHBOARD")
        print("=" * 35)
        
        results = self.components['dashboard'].generate_dashboard_data()
        
        if output_file:
            with open(output_file, 'w') as f:
                json.dump(results, f, indent=2)
            print(f"📄 Results saved to: {output_file}")
        
        return results
    
    def run_philosophical_hooks(self, output_file: Optional[str] = None) -> Dict[str, Any]:
        """Run philosophical hooks validation."""
        if not self.components['hooks']:
            print("❌ Philosophical hooks component not available")
            return {}
        
        print("🔗 RUNNING PHILOSOPHICAL HOOKS VALIDATION")
        print("=" * 40)
        
        results = self.components['hooks'].run_philosophical_hooks_validation()
        
        if output_file:
            with open(output_file, 'w') as f:
                json.dump(results, f, indent=2)
            print(f"📄 Results saved to: {output_file}")
        
        return results
    
    def show_status(self) -> None:
        """Show current CDR system status."""
        print("📋 CONSTITUTIONAL DRIFT RESISTANCE - SYSTEM STATUS")
        print("=" * 55)
        print(f"Timestamp: {datetime.now().isoformat()}")
        print()
        
        components_status = {
            "Drift Detection": ConstitutionalDriftDetector is not None,
            "Drift Resistance": ConstitutionalDriftResistance is not None,
            "Philosophical Preservation": ConstitutionalPhilosophicalPreservation is not None,
            "Alert Governance": ConstitutionalAlertGovernance is not None,
            "Scheduled Audits": ConstitutionalScheduledAudits is not None,
            "Transparency Dashboard": ConstitutionalDriftDashboard is not None,
            "Philosophical Hooks": ConstitutionalPhilosophicalHooks is not None
        }
        
        for component, available in components_status.items():
            status = "✅ Available" if available else "❌ Not Available"
            print(f"{component:<25} {status}")
        
        print()
        print("🔧 Available Commands:")
        print("  full-analysis     - Run comprehensive CDR analysis")
        print("  drift-detection   - Run constitutional drift detection")
        print("  preservation      - Run philosophical preservation assessment")
        print("  resistance        - Run drift resistance implementation")
        print("  governance        - Run alert governance assessment")
        print("  audit             - Run scheduled constitutional audit")
        print("  dashboard         - Generate transparency dashboard")
        print("  hooks             - Run philosophical hooks validation")
        print("  status            - Show system status")
    
    def _calculate_overall_status(self, results: Dict[str, Any]) -> str:
        """Calculate overall CDR status."""
        critical_issues = len(results.get("critical_issues", []))
        
        if critical_issues > 0:
            return "critical"
        
        health_score = results.get("health_score", 0)
        if health_score >= 90:
            return "healthy"
        elif health_score >= 70:
            return "warning"
        else:
            return "unhealthy"
    
    def _calculate_health_score(self, results: Dict[str, Any]) -> float:
        """Calculate overall health score."""
        scores = []
        
        # Drift detection score
        if "drift_detection" in results["components"]:
            drift_data = results["components"]["drift_detection"]
            if "overall_risk_level" in drift_data:
                risk_level = drift_data["overall_risk_level"]
                if risk_level == "low":
                    scores.append(100)
                elif risk_level == "medium":
                    scores.append(70)
                else:
                    scores.append(30)
        
        # Philosophical preservation score
        if "philosophical_preservation" in results["components"]:
            preservation_data = results["components"]["philosophical_preservation"]
            if "overall_integrity" in preservation_data:
                integrity = preservation_data["overall_integrity"]
                if integrity == "high":
                    scores.append(100)
                elif integrity == "medium":
                    scores.append(70)
                else:
                    scores.append(30)
        
        # Dashboard health score
        if "transparency_dashboard" in results["components"]:
            dashboard_data = results["components"]["transparency_dashboard"]
            if "overall_health" in dashboard_data:
                health = dashboard_data["overall_health"]
                if health == "healthy":
                    scores.append(100)
                elif health == "warning":
                    scores.append(70)
                else:
                    scores.append(30)
        
        return sum(scores) / len(scores) if scores else 0.0
    
    def _generate_recommendations(self, results: Dict[str, Any]) -> List[str]:
        """Generate recommendations based on analysis results."""
        recommendations = []
        
        # Check drift detection
        if "drift_detection" in results["components"]:
            drift_data = results["components"]["drift_detection"]
            if drift_data.get("overall_risk_level") == "high":
                recommendations.append("Address high-risk drift signals immediately")
            elif drift_data.get("overall_risk_level") == "medium":
                recommendations.append("Monitor medium-risk drift signals closely")
        
        # Check philosophical preservation
        if "philosophical_preservation" in results["components"]:
            preservation_data = results["components"]["philosophical_preservation"]
            if preservation_data.get("overall_integrity") == "low":
                recommendations.append("Restore philosophical integrity of constitutional principles")
        
        # Check dashboard health
        if "transparency_dashboard" in results["components"]:
            dashboard_data = results["components"]["transparency_dashboard"]
            if dashboard_data.get("overall_health") == "critical":
                recommendations.append("Immediate attention required for transparency dashboard issues")
        
        return recommendations
    
    def _identify_critical_issues(self, results: Dict[str, Any]) -> List[str]:
        """Identify critical issues from analysis results."""
        issues = []
        
        # Check for high-risk drift
        if "drift_detection" in results["components"]:
            drift_data = results["components"]["drift_detection"]
            if drift_data.get("overall_risk_level") == "high":
                issues.append("High-risk constitutional drift detected")
        
        # Check for low integrity
        if "philosophical_preservation" in results["components"]:
            preservation_data = results["components"]["philosophical_preservation"]
            if preservation_data.get("overall_integrity") == "low":
                issues.append("Low philosophical integrity detected")
        
        # Check for critical dashboard health
        if "transparency_dashboard" in results["components"]:
            dashboard_data = results["components"]["transparency_dashboard"]
            if dashboard_data.get("overall_health") == "critical":
                issues.append("Critical transparency dashboard issues")
        
        return issues


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Constitutional Drift Resistance (CDR) Integration CLI",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python cdr_integration_cli.py full-analysis
  python cdr_integration_cli.py drift-detection --output drift_report.json
  python cdr_integration_cli.py audit --type weekly
  python cdr_integration_cli.py dashboard --output dashboard.json
  python cdr_integration_cli.py status
        """
    )
    
    parser.add_argument(
        'command',
        choices=[
            'full-analysis', 'drift-detection', 'preservation', 'resistance',
            'governance', 'audit', 'dashboard', 'hooks', 'status'
        ],
        help='CDR command to execute'
    )
    
    parser.add_argument(
        '--output', '-o',
        help='Output file for results (JSON format)'
    )
    
    parser.add_argument(
        '--type', '-t',
        choices=['daily', 'weekly', 'monthly'],
        default='daily',
        help='Audit type (for audit command)'
    )
    
    args = parser.parse_args()
    
    cli = CDRIntegrationCLI()
    
    try:
        if args.command == 'full-analysis':
            cli.run_full_cdr_analysis(args.output)
        elif args.command == 'drift-detection':
            cli.run_drift_detection(args.output)
        elif args.command == 'preservation':
            cli.run_philosophical_preservation(args.output)
        elif args.command == 'resistance':
            cli.run_drift_resistance(args.output)
        elif args.command == 'governance':
            cli.run_alert_governance(args.output)
        elif args.command == 'audit':
            cli.run_scheduled_audit(args.type, args.output)
        elif args.command == 'dashboard':
            cli.generate_dashboard(args.output)
        elif args.command == 'hooks':
            cli.run_philosophical_hooks(args.output)
        elif args.command == 'status':
            cli.show_status()
    
    except KeyboardInterrupt:
        print("\n\n⚠️  Operation cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
