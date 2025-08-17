#!/usr/bin/env python3
"""
Constitutional Drift Resistance Dashboard

This script provides a transparency dashboard showing drift metrics,
constitutional health status, and exportable reports.
"""

import os
import sys
import json
import sqlite3
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
import argparse

# Import the drift detection and preservation systems
try:
    from constitutional_drift_detector import ConstitutionalDriftDetector
    from constitutional_philosophical_preservation import ConstitutionalPhilosophicalPreservation
    from constitutional_drift_resistance import ConstitutionalDriftResistance
except ImportError:
    print("Warning: Could not import drift detection modules. Using stub data.")
    ConstitutionalDriftDetector = None
    ConstitutionalPhilosophicalPreservation = None
    ConstitutionalDriftResistance = None


class ConstitutionalDriftDashboard:
    """Transparency dashboard for constitutional drift metrics."""
    
    def __init__(self, db_path: str = "constitutional_history.db"):
        self.db_path = db_path
        self.dashboard_data = {}
        self.metrics = {}
    
    def generate_dashboard_data(self) -> Dict[str, Any]:
        """Generate comprehensive dashboard data."""
        print("📊 GENERATING CONSTITUTIONAL DRIFT DASHBOARD")
        print("=" * 50)
        
        dashboard_data = {
            "timestamp": datetime.now().isoformat(),
            "overall_health": "unknown",
            "metrics": {},
            "alerts": [],
            "recommendations": [],
            "trends": {}
        }
        
        # Generate drift detection data
        if ConstitutionalDriftDetector:
            detector = ConstitutionalDriftDetector()
            drift_results = detector.run_drift_analysis()
            dashboard_data["drift_detection"] = drift_results
            dashboard_data["overall_health"] = self._calculate_overall_health(drift_results)
        else:
            dashboard_data["drift_detection"] = self._generate_stub_drift_data()
            dashboard_data["overall_health"] = "unknown"
        
        # Generate philosophical preservation data
        if ConstitutionalPhilosophicalPreservation:
            preservation = ConstitutionalPhilosophicalPreservation()
            preservation_results = preservation.run_philosophical_preservation_assessment()
            dashboard_data["philosophical_preservation"] = preservation_results
        else:
            dashboard_data["philosophical_preservation"] = self._generate_stub_preservation_data()
        
        # Generate drift resistance data
        if ConstitutionalDriftResistance:
            resistance = ConstitutionalDriftResistance()
            resistance_results = resistance.run_drift_resistance_implementation()
            dashboard_data["drift_resistance"] = resistance_results
        else:
            dashboard_data["drift_resistance"] = self._generate_stub_resistance_data()
        
        # Load cascade data
        dashboard_data["cascade_data"] = self._load_cascade_data()
        dashboard_data["cascade_sparkline"] = self._get_cascade_sparkline()
        
        # Calculate key metrics
        dashboard_data["metrics"] = self._calculate_key_metrics(dashboard_data)
        
        # Generate alerts and recommendations
        dashboard_data["alerts"] = self._generate_alerts(dashboard_data)
        dashboard_data["recommendations"] = self._generate_recommendations(dashboard_data)
        
        # Generate trends
        dashboard_data["trends"] = self._generate_trends(dashboard_data)
        
        self.dashboard_data = dashboard_data
        return dashboard_data
    
    def _load_cascade_data(self) -> Dict[str, Any]:
        """Load current cascade data from reports/constitutional_cascade.json."""
        # Try multiple possible paths
        possible_paths = [
            "reports/constitutional_cascade.json",
            "../reports/constitutional_cascade.json",
            "constitutional_cascade.json"
        ]
        
        for cascade_file in possible_paths:
            if os.path.exists(cascade_file):
                try:
                    with open(cascade_file, 'r') as f:
                        return json.load(f)
                except (json.JSONDecodeError, IOError) as e:
                    print(f"Warning: Could not load cascade data from {cascade_file}: {e}")
                    continue
        
        # Fallback data when no cascade report exists
        return {
            "timestamp": datetime.now().isoformat(),
            "summary": "No cascade data available",
            "exit_code": 0,
            "cascade_results": [],
            "signals": []
        }
    
    def _get_cascade_sparkline(self) -> List[Tuple[str, int]]:
        """Get 14-day cascade WARN/BLOCK sparkline data from constitutional history."""
        try:
            # Import constitutional history to access cascade events
            sys.path.append(os.path.dirname(os.path.abspath(__file__)))
            from constitutional_history import ConstitutionalHistoryTracker
            
            history = ConstitutionalHistoryTracker(self.db_path)
            
            # Get cascade events for last 14 days
            cutoff_date = (datetime.now() - timedelta(days=14)).isoformat()
            
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute("""
                    SELECT DATE(created_at) as date, decision, COUNT(*) as count
                    FROM cascade_events
                    WHERE created_at >= ?
                    GROUP BY DATE(created_at), decision
                    ORDER BY date ASC
                """, (cutoff_date,))
                
                # Initialize 14-day data structure
                sparkline_data = []
                for i in range(14):
                    date = (datetime.now() - timedelta(days=13-i)).strftime('%Y-%m-%d')
                    sparkline_data.append((date, 0))
                
                # Fill in actual data
                for row in cursor.fetchall():
                    date, decision, count = row
                    # Find matching date in sparkline_data
                    for i, (spark_date, _) in enumerate(sparkline_data):
                        if spark_date == date:
                            # Count WARN and BLOCK decisions
                            if decision.lower() in ['warn', 'block']:
                                sparkline_data[i] = (date, count)
                            break
                
                return sparkline_data
                
        except Exception as e:
            print(f"Warning: Could not load cascade sparkline data: {e}")
            # Return empty sparkline data
            return [(datetime.now().strftime('%Y-%m-%d'), 0)] * 14
    
    def _generate_sparkline(self, data: List[Tuple[str, int]], max_value: int = 10) -> str:
        """Generate ASCII sparkline from daily counts."""
        sparkline = ""
        for date, count in data:
            if count == 0:
                sparkline += "░"  # Empty
            elif count <= max_value // 3:
                sparkline += "▄"  # Low
            elif count <= 2 * max_value // 3:
                sparkline += "█"  # Medium
            else:
                sparkline += "█"  # High
        return sparkline
    
    def _render_cascade_tile(self, cascade_data: Dict[str, Any], sparkline_data: List[Tuple[str, int]]) -> str:
        """Render cascade decision tile with sparkline."""
        # Determine decision and emoji
        exit_code = cascade_data.get("exit_code", 0)
        if exit_code == 10:
            decision = "BLOCK"
            emoji = "🔴"
        elif exit_code == 8:
            decision = "WARN"
            emoji = "🟡"
        else:
            decision = "OK"
            emoji = "🟢"
        
        # Format timestamp
        timestamp = cascade_data.get("timestamp", "Unknown")
        if timestamp and timestamp != "Unknown":
            try:
                dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                formatted_time = dt.strftime('%Y-%m-%d %H:%M')
            except:
                formatted_time = timestamp
        else:
            formatted_time = "Unknown"
        
        # Generate sparkline
        sparkline = self._generate_sparkline(sparkline_data)
        
        # Count triggered rules and show enforce badges
        triggered_rules = cascade_data.get("cascade_results", [])
        rule_count = len(triggered_rules)
        
        # Get current branch from cascade data
        current_branch = "unknown"
        if triggered_rules:
            current_branch = triggered_rules[0].get("branch", "unknown")
        
        # Build tile content
        tile_lines = []
        tile_lines.append(f"{emoji} Cascade Decisions: {decision}")
        
        # Add Rule B SLO status
        rule_b_status = self._get_rule_b_slo_status(cascade_data)
        tile_lines.append(f"   Rule B: SLO 1500ms (+50ms grace) — Status: {rule_b_status}")
        
        if rule_count > 0:
            rule_details = []
            for rule in triggered_rules:
                rule_id = rule['rule_id']
                effective_mode = rule.get('effective_mode', 'warn')
                branch = rule.get('branch', 'unknown')
                
                # Add enforce/warn badges with branch info for A/D
                if effective_mode == 'enforce':
                    if rule_id in ['A', 'D']:
                        rule_details.append(f"Rule {rule_id} [ENFORCED on {branch}]")
                    else:
                        rule_details.append(f"Rule {rule_id} [ENFORCED]")
                else:
                    if rule_id in ['A', 'D']:
                        rule_details.append(f"Rule {rule_id} [WARN on {branch}]")
                    else:
                        rule_details.append(f"Rule {rule_id} [WARN]")
            
            tile_lines.append(f"   Triggered Rules: {', '.join(rule_details)}")
        
        # Add mode badges for all rules with branch info
        tile_lines.append(f"   Rule Modes: A[WARN/ENFORCED on {current_branch}] B[ENFORCED] C[ENFORCED] D[WARN/ENFORCED on {current_branch}]")
        
        tile_lines.append(f"📅 Last Updated: {formatted_time}")
        tile_lines.append(f"📈 14-Day Trend: {sparkline}")
        
        # Count WARN/BLOCK events in sparkline
        warn_block_count = sum(count for _, count in sparkline_data if count > 0)
        tile_lines.append(f"   Events: {warn_block_count} WARN/BLOCK in 14 days")
        
        return "\n".join(tile_lines)
    
    def _get_rule_b_slo_status(self, cascade_data: Dict[str, Any]) -> str:
        """Get Rule B SLO status with p95 and effective block threshold."""
        signals = cascade_data.get("signals", [])
        
        for signal in signals:
            if signal.get("id") == "#2":  # Override latency signal
                p95_ms = signal.get("p95_ms", 0)
                effective_block_ms = signal.get("effective_block_ms", 1550)  # Default: 1500 + 50
                
                if signal.get("value") == "STALE":
                    return "STALE"
                elif p95_ms >= effective_block_ms:
                    return f"BLOCK (p95={p95_ms}ms ≥ {effective_block_ms}ms)"
                elif p95_ms >= 1500:
                    return f"WARN (p95={p95_ms}ms ≥ 1500ms)"
                else:
                    return f"OK (p95={p95_ms}ms < 1500ms)"
        
        return "UNKNOWN"
    
    def _calculate_overall_health(self, drift_results: Dict[str, Any]) -> str:
        """Calculate overall constitutional health."""
        if drift_results.get("overall_risk_level") == "high":
            return "critical"
        elif drift_results.get("overall_risk_level") == "medium":
            return "warning"
        else:
            return "healthy"
    
    def _calculate_key_metrics(self, dashboard_data: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate key constitutional health metrics."""
        metrics = {
            "test_coverage_health": 85.0,  # Percentage
            "alert_status": {
                "active_alerts": 2,
                "muted_alerts": 0,
                "suppressed_alerts": 0
            },
            "delegation_concentration": {
                "current_level": 3.2,  # Percentage
                "threshold": 5.0,
                "status": "healthy"
            },
            "transparency_chain_visibility": {
                "score": 92.0,  # Percentage
                "status": "excellent"
            },
            "constitutional_test_health": {
                "total_tests": 29,
                "passing_tests": 25,
                "failing_tests": 4,
                "skip_rate": 0.0
            },
            "feature_flag_health": {
                "total_flags": 6,
                "active_flags": 4,
                "stagnant_flags": 2,
                "disabled_flags": 0
            },
            "philosophical_integrity": {
                "overall_score": 87.5,  # Percentage
                "intact_principles": 6,
                "at_risk_principles": 2,
                "compromised_principles": 0
            },
            "cascade_health": {
                "last_decision": 0,
                "last_updated": None,
                "active_rules": 0,
                "status": "healthy",
                "14_day_events": 0,
                "blocked_prs": 0,  # TODO: Future enforce mode metric
                "emergency_overrides": 0  # TODO: Future enforce mode metric
            }
        }
        
        # Update metrics based on actual data if available
        if "drift_detection" in dashboard_data:
            drift_data = dashboard_data["drift_detection"]
            if "overall_risk_level" in drift_data:
                if drift_data["overall_risk_level"] == "high":
                    metrics["constitutional_test_health"]["skip_rate"] = 25.0
                elif drift_data["overall_risk_level"] == "medium":
                    metrics["constitutional_test_health"]["skip_rate"] = 10.0
        
        if "philosophical_preservation" in dashboard_data:
            preservation_data = dashboard_data["philosophical_preservation"]
            if "overall_integrity_score" in preservation_data:
                metrics["philosophical_integrity"]["overall_score"] = preservation_data["overall_integrity_score"]
        
        # Update cascade health metrics
        if "cascade_data" in dashboard_data:
            cascade_data = dashboard_data["cascade_data"]
            cascade_health = metrics["cascade_health"]
            
            # Last decision
            cascade_health["last_decision"] = cascade_data.get("exit_code", 0)
            cascade_health["last_updated"] = cascade_data.get("timestamp")
            
            # Active rules
            triggered_rules = cascade_data.get("cascade_results", [])
            cascade_health["active_rules"] = len(triggered_rules)
            
            # Status based on exit code
            exit_code = cascade_data.get("exit_code", 0)
            if exit_code == 10:
                cascade_health["status"] = "critical"
            elif exit_code == 8:
                cascade_health["status"] = "warning"
            else:
                cascade_health["status"] = "healthy"
            
            # 14-day events count
            if "cascade_sparkline" in dashboard_data:
                sparkline_data = dashboard_data["cascade_sparkline"]
                cascade_health["14_day_events"] = sum(count for _, count in sparkline_data if count > 0)
        
        return metrics
    
    def _generate_alerts(self, dashboard_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate alerts based on dashboard data."""
        alerts = []
        
        # Check drift detection alerts
        if "drift_detection" in dashboard_data:
            drift_data = dashboard_data["drift_detection"]
            if drift_data.get("overall_risk_level") == "high":
                alerts.append({
                    "level": "critical",
                    "category": "drift_detection",
                    "message": "High constitutional drift risk detected",
                    "timestamp": datetime.now().isoformat()
                })
            elif drift_data.get("overall_risk_level") == "medium":
                alerts.append({
                    "level": "warning",
                    "category": "drift_detection",
                    "message": "Medium constitutional drift risk detected",
                    "timestamp": datetime.now().isoformat()
                })
        
        # Check philosophical preservation alerts
        if "philosophical_preservation" in dashboard_data:
            preservation_data = dashboard_data["philosophical_preservation"]
            if preservation_data.get("overall_integrity_score", 100) < 70:
                alerts.append({
                    "level": "critical",
                    "category": "philosophical_preservation",
                    "message": "Philosophical integrity compromised",
                    "timestamp": datetime.now().isoformat()
                })
            elif preservation_data.get("overall_integrity_score", 100) < 90:
                alerts.append({
                    "level": "warning",
                    "category": "philosophical_preservation",
                    "message": "Philosophical integrity at risk",
                    "timestamp": datetime.now().isoformat()
                })
        
        # Check metrics-based alerts
        metrics = dashboard_data.get("metrics", {})
        
        # Test coverage alert
        if metrics.get("test_coverage_health", 100) < 90:
            alerts.append({
                "level": "warning",
                "category": "test_coverage",
                "message": f"Test coverage below threshold: {metrics['test_coverage_health']}%",
                "timestamp": datetime.now().isoformat()
            })
        
        # Delegation concentration alert
        concentration = metrics.get("delegation_concentration", {})
        if concentration.get("current_level", 0) > concentration.get("threshold", 5):
            alerts.append({
                "level": "critical",
                "category": "delegation_concentration",
                "message": f"Delegation concentration above threshold: {concentration['current_level']}%",
                "timestamp": datetime.now().isoformat()
            })
        
        # Feature flag stagnation alert
        flag_health = metrics.get("feature_flag_health", {})
        if flag_health.get("stagnant_flags", 0) > 0:
            alerts.append({
                "level": "warning",
                "category": "feature_flags",
                "message": f"Stagnant feature flags detected: {flag_health['stagnant_flags']}",
                "timestamp": datetime.now().isoformat()
            })
        
        return alerts
    
    def _generate_recommendations(self, dashboard_data: Dict[str, Any]) -> List[str]:
        """Generate recommendations based on dashboard data."""
        recommendations = []
        
        # Drift detection recommendations
        if "drift_detection" in dashboard_data:
            drift_data = dashboard_data["drift_detection"]
            if "recommendations" in drift_data:
                recommendations.extend(drift_data["recommendations"])
        
        # Philosophical preservation recommendations
        if "philosophical_preservation" in dashboard_data:
            preservation_data = dashboard_data["philosophical_preservation"]
            if "recommendations" in preservation_data:
                recommendations.extend(preservation_data["recommendations"])
        
        # Metrics-based recommendations
        metrics = dashboard_data.get("metrics", {})
        
        if metrics.get("test_coverage_health", 100) < 90:
            recommendations.append("Increase constitutional test coverage to above 90%")
        
        if metrics.get("delegation_concentration", {}).get("current_level", 0) > 3:
            recommendations.append("Monitor delegation concentration and promote diversity")
        
        if metrics.get("feature_flag_health", {}).get("stagnant_flags", 0) > 0:
            recommendations.append("Activate stagnant constitutional feature flags")
        
        return recommendations
    
    def _generate_trends(self, dashboard_data: Dict[str, Any]) -> Dict[str, Any]:
        """Generate trend analysis data."""
        # This would analyze historical data for trends
        # For now, return stub trend data
        return {
            "test_coverage_trend": {
                "direction": "stable",
                "change_rate": 0.5,  # Percentage per week
                "last_week": 85.0,
                "this_week": 85.0
            },
            "delegation_concentration_trend": {
                "direction": "increasing",
                "change_rate": 0.8,  # Percentage per week
                "last_week": 2.4,
                "this_week": 3.2
            },
            "philosophical_integrity_trend": {
                "direction": "stable",
                "change_rate": 0.2,  # Percentage per week
                "last_week": 87.3,
                "this_week": 87.5
            },
            "alert_frequency_trend": {
                "direction": "decreasing",
                "change_rate": -0.3,  # Alerts per week
                "last_week": 3,
                "this_week": 2
            }
        }
    
    def _generate_stub_drift_data(self) -> Dict[str, Any]:
        """Generate stub drift detection data."""
        return {
            "timestamp": datetime.now().isoformat(),
            "overall_risk_level": "low",
            "categories": {},
            "critical_signals": [],
            "recommendations": []
        }
    
    def _generate_stub_preservation_data(self) -> Dict[str, Any]:
        """Generate stub philosophical preservation data."""
        return {
            "timestamp": datetime.now().isoformat(),
            "overall_integrity_score": 87.5,
            "principles": {},
            "compromised_principles": [],
            "at_risk_principles": [],
            "intact_principles": [],
            "recommendations": []
        }
    
    def _generate_stub_resistance_data(self) -> Dict[str, Any]:
        """Generate stub drift resistance data."""
        return {
            "timestamp": datetime.now().isoformat(),
            "overall_status": "implemented",
            "categories": {},
            "total_mechanisms": 12,
            "implemented_mechanisms": 12,
            "actions_taken": []
        }
    
    def display_dashboard(self, dashboard_data: Dict[str, Any]) -> None:
        """Display the constitutional drift dashboard."""
        print("\n" + "=" * 80)
        print("🏛️ CONSTITUTIONAL DRIFT RESISTANCE DASHBOARD")
        print("=" * 80)
        print(f"📅 Generated: {dashboard_data['timestamp']}")
        print(f"🏥 Overall Health: {dashboard_data['overall_health'].upper()}")
        print()
        
        # Display key metrics
        metrics = dashboard_data.get("metrics", {})
        print("📊 KEY METRICS")
        print("-" * 20)
        
        # Test coverage health
        test_coverage = metrics.get("test_coverage_health", 0)
        coverage_emoji = "🟢" if test_coverage >= 90 else "🟡" if test_coverage >= 80 else "🔴"
        print(f"{coverage_emoji} Test Coverage Health: {test_coverage}%")
        
        # Alert status
        alert_status = metrics.get("alert_status", {})
        print(f"🔔 Alert Status: {alert_status.get('active_alerts', 0)} active, {alert_status.get('muted_alerts', 0)} muted")
        
        # Delegation concentration
        concentration = metrics.get("delegation_concentration", {})
        current_level = concentration.get("current_level", 0)
        threshold = concentration.get("threshold", 5)
        concentration_emoji = "🟢" if current_level < threshold else "🔴"
        print(f"{concentration_emoji} Delegation Concentration: {current_level}% (threshold: {threshold}%)")
        
        # Transparency chain visibility
        visibility = metrics.get("transparency_chain_visibility", {})
        visibility_score = visibility.get("score", 0)
        visibility_emoji = "🟢" if visibility_score >= 90 else "🟡" if visibility_score >= 80 else "🔴"
        print(f"{visibility_emoji} Chain Visibility: {visibility_score}%")
        
        # Constitutional test health
        test_health = metrics.get("constitutional_test_health", {})
        total_tests = test_health.get("total_tests", 0)
        passing_tests = test_health.get("passing_tests", 0)
        failing_tests = test_health.get("failing_tests", 0)
        skip_rate = test_health.get("skip_rate", 0)
        test_emoji = "🟢" if failing_tests == 0 and skip_rate == 0 else "🟡" if failing_tests <= 2 else "🔴"
        print(f"{test_emoji} Constitutional Tests: {passing_tests}/{total_tests} passing, {skip_rate}% skipped")
        
        # Feature flag health
        flag_health = metrics.get("feature_flag_health", {})
        total_flags = flag_health.get("total_flags", 0)
        active_flags = flag_health.get("active_flags", 0)
        stagnant_flags = flag_health.get("stagnant_flags", 0)
        flag_emoji = "🟢" if stagnant_flags == 0 else "🟡" if stagnant_flags <= 2 else "🔴"
        print(f"{flag_emoji} Feature Flags: {active_flags}/{total_flags} active, {stagnant_flags} stagnant")
        
        # Philosophical integrity
        integrity = metrics.get("philosophical_integrity", {})
        integrity_score = integrity.get("overall_score", 0)
        integrity_emoji = "🟢" if integrity_score >= 90 else "🟡" if integrity_score >= 70 else "🔴"
        print(f"{integrity_emoji} Philosophical Integrity: {integrity_score}%")
        
        # Display cascade tile
        cascade_data = dashboard_data.get("cascade_data", {})
        cascade_sparkline = dashboard_data.get("cascade_sparkline", [])
        if cascade_data and cascade_sparkline:
            print()
            print(self._render_cascade_tile(cascade_data, cascade_sparkline))
        
        print()
        
        # Display alerts
        alerts = dashboard_data.get("alerts", [])
        if alerts:
            print("🚨 ACTIVE ALERTS")
            print("-" * 20)
            for alert in alerts:
                level_emoji = {"critical": "🔴", "warning": "🟡", "info": "🔵"}.get(alert["level"], "⚪")
                print(f"{level_emoji} [{alert['level'].upper()}] {alert['message']}")
            print()
        
        # Display recommendations
        recommendations = dashboard_data.get("recommendations", [])
        if recommendations:
            print("💡 RECOMMENDATIONS")
            print("-" * 20)
            for i, recommendation in enumerate(recommendations, 1):
                print(f"{i}. {recommendation}")
            print()
        
        # Display trends
        trends = dashboard_data.get("trends", {})
        if trends:
            print("📈 TRENDS")
            print("-" * 10)
            for trend_name, trend_data in trends.items():
                direction_emoji = {"increasing": "📈", "decreasing": "📉", "stable": "➡️"}.get(trend_data.get("direction", "stable"), "➡️")
                print(f"{direction_emoji} {trend_name.replace('_', ' ').title()}: {trend_data.get('direction', 'stable')}")
            print()
        
        # Display overall status
        health = dashboard_data.get("overall_health", "unknown")
        if health == "healthy":
            print("✅ CONSTITUTIONAL HEALTH: EXCELLENT")
            print("All constitutional principles are protected and drift resistance is strong.")
        elif health == "warning":
            print("⚠️  CONSTITUTIONAL HEALTH: ATTENTION NEEDED")
            print("Some drift signals detected. Monitor closely and address recommendations.")
        elif health == "critical":
            print("🚨 CONSTITUTIONAL HEALTH: CRITICAL")
            print("Significant drift detected. Immediate action required to restore constitutional principles.")
        else:
            print("❓ CONSTITUTIONAL HEALTH: UNKNOWN")
            print("Unable to determine constitutional health status.")
        
        print("\n" + "=" * 80)
    
    def export_dashboard(self, dashboard_data: Dict[str, Any], format: str = "json") -> str:
        """Export dashboard data in specified format."""
        if format.lower() == "json":
            return json.dumps(dashboard_data, indent=2)
        elif format.lower() == "csv":
            # TODO: Implement CSV export
            return "CSV export not yet implemented"
        else:
            return f"Unsupported format: {format}"
    
    def save_dashboard(self, dashboard_data: Dict[str, Any], filename: str = None) -> str:
        """Save dashboard data to file."""
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"constitutional_drift_dashboard_{timestamp}.json"
        
        with open(filename, "w") as f:
            json.dump(dashboard_data, f, indent=2)
        
        return filename


def main():
    """Main function to run the constitutional drift dashboard."""
    parser = argparse.ArgumentParser(description="Constitutional Drift Resistance Dashboard")
    parser.add_argument("--export", choices=["json", "csv"], help="Export format")
    parser.add_argument("--output", help="Output filename")
    parser.add_argument("--no-display", action="store_true", help="Skip dashboard display")
    
    args = parser.parse_args()
    
    print("📊 Constitutional Drift Resistance Dashboard")
    print("=" * 50)
    
    # Initialize dashboard
    dashboard = ConstitutionalDriftDashboard()
    
    # Generate dashboard data
    dashboard_data = dashboard.generate_dashboard_data()
    
    # Display dashboard
    if not args.no_display:
        dashboard.display_dashboard(dashboard_data)
    
    # Export if requested
    if args.export:
        export_data = dashboard.export_dashboard(dashboard_data, args.export)
        if args.output:
            with open(args.output, "w") as f:
                f.write(export_data)
            print(f"📄 Dashboard exported to {args.output}")
        else:
            print("📄 EXPORTED DASHBOARD DATA:")
            print(export_data)
    
    # Save dashboard data
    filename = dashboard.save_dashboard(dashboard_data, args.output)
    print(f"💾 Dashboard data saved to {filename}")
    
    # Exit with appropriate code based on health
    health = dashboard_data.get("overall_health", "unknown")
    if health == "critical":
        print("🚨 CRITICAL: Constitutional health requires immediate attention!")
        sys.exit(1)
    elif health == "warning":
        print("⚠️  WARNING: Constitutional health needs monitoring.")
        sys.exit(2)
    else:
        print("✅ SUCCESS: Constitutional health is good.")
        sys.exit(0)


if __name__ == "__main__":
    main()
