#!/usr/bin/env python3
"""
Constitutional Scheduled Audits System

This script provides scheduled audits for constitutional drift detection,
storing results in persistent logs with timestamped reports and trend analysis.
"""

import os
import sys
import json
import sqlite3
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
import argparse
import subprocess

# Import the drift detection and preservation systems
try:
    from constitutional_drift_detector import ConstitutionalDriftDetector
    from constitutional_philosophical_preservation import ConstitutionalPhilosophicalPreservation
    from constitutional_drift_resistance import ConstitutionalDriftResistance
    from constitutional_drift_dashboard import ConstitutionalDriftDashboard
except ImportError:
    print("Warning: Could not import drift detection modules. Using stub data.")
    ConstitutionalDriftDetector = None
    ConstitutionalPhilosophicalPreservation = None
    ConstitutionalDriftResistance = None
    ConstitutionalDriftDashboard = None


class ConstitutionalScheduledAudits:
    """Scheduled audit system for constitutional drift detection."""
    
    def __init__(self, db_path: str = "constitutional_history.db"):
        self.db_path = db_path
        self.audit_history = []
        self.trend_analysis = {}
        
        # Initialize database
        self._init_database()
    
    def _init_database(self):
        """Initialize the audit history database."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Create audit history table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS audit_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                audit_type TEXT NOT NULL,
                overall_health TEXT NOT NULL,
                risk_level TEXT,
                integrity_score REAL,
                drift_signals_count INTEGER,
                alerts_count INTEGER,
                recommendations_count INTEGER,
                audit_data TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Create trend analysis table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS trend_analysis (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                metric_name TEXT NOT NULL,
                value REAL NOT NULL,
                timestamp TEXT NOT NULL,
                trend_direction TEXT,
                change_rate REAL,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Create alert history table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS alert_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                alert_level TEXT NOT NULL,
                alert_category TEXT NOT NULL,
                alert_message TEXT NOT NULL,
                timestamp TEXT NOT NULL,
                resolved BOOLEAN DEFAULT FALSE,
                resolved_at TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def run_scheduled_audit(self, audit_type: str = "daily") -> Dict[str, Any]:
        """Run a scheduled constitutional audit."""
        print(f"🔍 RUNNING SCHEDULED CONSTITUTIONAL AUDIT: {audit_type.upper()}")
        print("=" * 60)
        
        audit_data = {
            "timestamp": datetime.now().isoformat(),
            "audit_type": audit_type,
            "overall_health": "unknown",
            "risk_level": "unknown",
            "integrity_score": 0.0,
            "drift_signals_count": 0,
            "alerts_count": 0,
            "recommendations_count": 0,
            "audit_results": {},
            "trend_analysis": {},
            "escalation_required": False
        }
        
        # Run drift detection audit
        if ConstitutionalDriftDetector:
            print("🔍 Running drift detection audit...")
            detector = ConstitutionalDriftDetector()
            drift_results = detector.run_drift_analysis()
            audit_data["audit_results"]["drift_detection"] = drift_results
            audit_data["risk_level"] = drift_results.get("overall_risk_level", "unknown")
            audit_data["drift_signals_count"] = len(drift_results.get("critical_signals", []))
            audit_data["recommendations_count"] = len(drift_results.get("recommendations", []))
        else:
            print("⚠️  Using stub drift detection data...")
            audit_data["audit_results"]["drift_detection"] = self._generate_stub_drift_data()
        
        # Run philosophical preservation audit
        if ConstitutionalPhilosophicalPreservation:
            print("🏛️ Running philosophical preservation audit...")
            preservation = ConstitutionalPhilosophicalPreservation()
            preservation_results = preservation.run_philosophical_preservation_assessment()
            audit_data["audit_results"]["philosophical_preservation"] = preservation_results
            audit_data["integrity_score"] = preservation_results.get("overall_integrity_score", 0.0)
        else:
            print("⚠️  Using stub philosophical preservation data...")
            audit_data["audit_results"]["philosophical_preservation"] = self._generate_stub_preservation_data()
        
        # Run drift resistance audit
        if ConstitutionalDriftResistance:
            print("🛡️ Running drift resistance audit...")
            resistance = ConstitutionalDriftResistance()
            resistance_results = resistance.run_drift_resistance_implementation()
            audit_data["audit_results"]["drift_resistance"] = resistance_results
        else:
            print("⚠️  Using stub drift resistance data...")
            audit_data["audit_results"]["drift_resistance"] = self._generate_stub_resistance_data()
        
        # Generate dashboard data
        if ConstitutionalDriftDashboard:
            print("📊 Generating dashboard data...")
            dashboard = ConstitutionalDriftDashboard()
            dashboard_data = dashboard.generate_dashboard_data()
            audit_data["audit_results"]["dashboard"] = dashboard_data
            audit_data["overall_health"] = dashboard_data.get("overall_health", "unknown")
            audit_data["alerts_count"] = len(dashboard_data.get("alerts", []))
        else:
            print("⚠️  Using stub dashboard data...")
            audit_data["audit_results"]["dashboard"] = self._generate_stub_dashboard_data()
        
        # Perform trend analysis
        print("📈 Performing trend analysis...")
        audit_data["trend_analysis"] = self._perform_trend_analysis(audit_data)
        
        # Determine if escalation is required
        audit_data["escalation_required"] = self._check_escalation_required(audit_data)
        
        # Store audit results
        self._store_audit_results(audit_data)
        
        # Store trend data
        self._store_trend_data(audit_data)
        
        # Store alerts
        self._store_alerts(audit_data)
        
        print("✅ Scheduled audit completed successfully!")
        return audit_data
    
    def _perform_trend_analysis(self, audit_data: Dict[str, Any]) -> Dict[str, Any]:
        """Perform trend analysis on audit data."""
        trends = {
            "health_trend": self._analyze_health_trend(),
            "integrity_trend": self._analyze_integrity_trend(),
            "drift_signals_trend": self._analyze_drift_signals_trend(),
            "alert_frequency_trend": self._analyze_alert_frequency_trend(),
            "escalation_trend": self._analyze_escalation_trend()
        }
        
        return trends
    
    def _analyze_health_trend(self) -> Dict[str, Any]:
        """Analyze health trend over time."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Get last 7 days of health data
        cursor.execute('''
            SELECT overall_health, timestamp 
            FROM audit_history 
            WHERE timestamp >= datetime('now', '-7 days')
            ORDER BY timestamp DESC
        ''')
        
        health_data = cursor.fetchall()
        conn.close()
        
        if len(health_data) < 2:
            return {
                "direction": "insufficient_data",
                "change_rate": 0.0,
                "last_week": "unknown",
                "this_week": "unknown"
            }
        
        # Analyze trend
        recent_health = health_data[0][0]
        previous_health = health_data[-1][0]
        
        health_scores = {"healthy": 3, "warning": 2, "critical": 1, "unknown": 0}
        current_score = health_scores.get(recent_health, 0)
        previous_score = health_scores.get(previous_health, 0)
        
        change_rate = current_score - previous_score
        
        if change_rate > 0:
            direction = "improving"
        elif change_rate < 0:
            direction = "declining"
        else:
            direction = "stable"
        
        return {
            "direction": direction,
            "change_rate": change_rate,
            "last_week": previous_health,
            "this_week": recent_health
        }
    
    def _analyze_integrity_trend(self) -> Dict[str, Any]:
        """Analyze integrity score trend over time."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Get last 7 days of integrity scores
        cursor.execute('''
            SELECT integrity_score, timestamp 
            FROM audit_history 
            WHERE integrity_score IS NOT NULL
            AND timestamp >= datetime('now', '-7 days')
            ORDER BY timestamp DESC
        ''')
        
        integrity_data = cursor.fetchall()
        conn.close()
        
        if len(integrity_data) < 2:
            return {
                "direction": "insufficient_data",
                "change_rate": 0.0,
                "last_week": 0.0,
                "this_week": 0.0
            }
        
        # Analyze trend
        recent_score = integrity_data[0][0]
        previous_score = integrity_data[-1][0]
        change_rate = recent_score - previous_score
        
        if change_rate > 1.0:
            direction = "improving"
        elif change_rate < -1.0:
            direction = "declining"
        else:
            direction = "stable"
        
        return {
            "direction": direction,
            "change_rate": change_rate,
            "last_week": previous_score,
            "this_week": recent_score
        }
    
    def _analyze_drift_signals_trend(self) -> Dict[str, Any]:
        """Analyze drift signals trend over time."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Get last 7 days of drift signals
        cursor.execute('''
            SELECT drift_signals_count, timestamp 
            FROM audit_history 
            WHERE timestamp >= datetime('now', '-7 days')
            ORDER BY timestamp DESC
        ''')
        
        signals_data = cursor.fetchall()
        conn.close()
        
        if len(signals_data) < 2:
            return {
                "direction": "insufficient_data",
                "change_rate": 0.0,
                "last_week": 0,
                "this_week": 0
            }
        
        # Analyze trend
        recent_count = signals_data[0][0]
        previous_count = signals_data[-1][0]
        change_rate = recent_count - previous_count
        
        if change_rate < 0:
            direction = "decreasing"
        elif change_rate > 0:
            direction = "increasing"
        else:
            direction = "stable"
        
        return {
            "direction": direction,
            "change_rate": change_rate,
            "last_week": previous_count,
            "this_week": recent_count
        }
    
    def _analyze_alert_frequency_trend(self) -> Dict[str, Any]:
        """Analyze alert frequency trend over time."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Get last 7 days of alerts
        cursor.execute('''
            SELECT alerts_count, timestamp 
            FROM audit_history 
            WHERE timestamp >= datetime('now', '-7 days')
            ORDER BY timestamp DESC
        ''')
        
        alerts_data = cursor.fetchall()
        conn.close()
        
        if len(alerts_data) < 2:
            return {
                "direction": "insufficient_data",
                "change_rate": 0.0,
                "last_week": 0,
                "this_week": 0
            }
        
        # Analyze trend
        recent_count = alerts_data[0][0]
        previous_count = alerts_data[-1][0]
        change_rate = recent_count - previous_count
        
        if change_rate < 0:
            direction = "decreasing"
        elif change_rate > 0:
            direction = "increasing"
        else:
            direction = "stable"
        
        return {
            "direction": direction,
            "change_rate": change_rate,
            "last_week": previous_count,
            "this_week": recent_count
        }
    
    def _analyze_escalation_trend(self) -> Dict[str, Any]:
        """Analyze escalation frequency trend over time."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Get last 7 days of escalations
        cursor.execute('''
            SELECT COUNT(*) as escalation_count
            FROM audit_history 
            WHERE escalation_required = 1
            AND timestamp >= datetime('now', '-7 days')
        ''')
        
        escalation_count = cursor.fetchone()[0]
        conn.close()
        
        # Compare with previous week
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('''
            SELECT COUNT(*) as escalation_count
            FROM audit_history 
            WHERE escalation_required = 1
            AND timestamp >= datetime('now', '-14 days')
            AND timestamp < datetime('now', '-7 days')
        ''')
        
        previous_escalation_count = cursor.fetchone()[0]
        conn.close()
        
        change_rate = escalation_count - previous_escalation_count
        
        if change_rate < 0:
            direction = "decreasing"
        elif change_rate > 0:
            direction = "increasing"
        else:
            direction = "stable"
        
        return {
            "direction": direction,
            "change_rate": change_rate,
            "last_week": previous_escalation_count,
            "this_week": escalation_count
        }
    
    def _check_escalation_required(self, audit_data: Dict[str, Any]) -> bool:
        """Check if escalation is required based on audit data."""
        # Escalation triggers
        escalation_triggers = [
            audit_data.get("overall_health") == "critical",
            audit_data.get("risk_level") == "high",
            audit_data.get("integrity_score", 100) < 70,
            audit_data.get("drift_signals_count", 0) > 5,
            audit_data.get("alerts_count", 0) > 3
        ]
        
        return any(escalation_triggers)
    
    def _store_audit_results(self, audit_data: Dict[str, Any]):
        """Store audit results in database."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO audit_history (
                timestamp, audit_type, overall_health, risk_level, 
                integrity_score, drift_signals_count, alerts_count, 
                recommendations_count, audit_data
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            audit_data["timestamp"],
            audit_data["audit_type"],
            audit_data["overall_health"],
            audit_data["risk_level"],
            audit_data["integrity_score"],
            audit_data["drift_signals_count"],
            audit_data["alerts_count"],
            audit_data["recommendations_count"],
            json.dumps(audit_data["audit_results"])
        ))
        
        conn.commit()
        conn.close()
    
    def _store_trend_data(self, audit_data: Dict[str, Any]):
        """Store trend data in database."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        timestamp = audit_data["timestamp"]
        trends = audit_data.get("trend_analysis", {})
        
        for metric_name, trend_data in trends.items():
            if isinstance(trend_data, dict) and "change_rate" in trend_data:
                cursor.execute('''
                    INSERT INTO trend_analysis (
                        metric_name, value, timestamp, trend_direction, change_rate
                    ) VALUES (?, ?, ?, ?, ?)
                ''', (
                    metric_name,
                    trend_data.get("change_rate", 0.0),
                    timestamp,
                    trend_data.get("direction", "unknown"),
                    trend_data.get("change_rate", 0.0)
                ))
        
        conn.commit()
        conn.close()
    
    def _store_alerts(self, audit_data: Dict[str, Any]):
        """Store alerts in database."""
        dashboard_data = audit_data.get("audit_results", {}).get("dashboard", {})
        alerts = dashboard_data.get("alerts", [])
        
        if not alerts:
            return
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        for alert in alerts:
            cursor.execute('''
                INSERT INTO alert_history (
                    alert_level, alert_category, alert_message, timestamp
                ) VALUES (?, ?, ?, ?)
            ''', (
                alert.get("level", "unknown"),
                alert.get("category", "unknown"),
                alert.get("message", ""),
                alert.get("timestamp", datetime.now().isoformat())
            ))
        
        conn.commit()
        conn.close()
    
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
    
    def _generate_stub_dashboard_data(self) -> Dict[str, Any]:
        """Generate stub dashboard data."""
        return {
            "timestamp": datetime.now().isoformat(),
            "overall_health": "healthy",
            "metrics": {},
            "alerts": [],
            "recommendations": [],
            "trends": {}
        }
    
    def display_audit_report(self, audit_data: Dict[str, Any]):
        """Display comprehensive audit report."""
        print("\n" + "=" * 80)
        print("📋 CONSTITUTIONAL SCHEDULED AUDIT REPORT")
        print("=" * 80)
        print(f"📅 Audit Date: {audit_data['timestamp']}")
        print(f"🔍 Audit Type: {audit_data['audit_type'].upper()}")
        print(f"🏥 Overall Health: {audit_data['overall_health'].upper()}")
        print(f"⚠️  Risk Level: {audit_data['risk_level'].upper()}")
        print(f"🏛️ Integrity Score: {audit_data['integrity_score']:.1f}%")
        print()
        
        # Display key metrics
        print("📊 AUDIT METRICS")
        print("-" * 20)
        print(f"🔍 Drift Signals: {audit_data['drift_signals_count']}")
        print(f"🚨 Active Alerts: {audit_data['alerts_count']}")
        print(f"💡 Recommendations: {audit_data['recommendations_count']}")
        print(f"🔄 Escalation Required: {'YES' if audit_data['escalation_required'] else 'NO'}")
        print()
        
        # Display trend analysis
        trends = audit_data.get("trend_analysis", {})
        if trends:
            print("📈 TREND ANALYSIS")
            print("-" * 20)
            for trend_name, trend_data in trends.items():
                if isinstance(trend_data, dict):
                    direction_emoji = {
                        "improving": "📈",
                        "declining": "📉", 
                        "increasing": "📈",
                        "decreasing": "📉",
                        "stable": "➡️",
                        "insufficient_data": "❓"
                    }.get(trend_data.get("direction", "unknown"), "❓")
                    
                    print(f"{direction_emoji} {trend_name.replace('_', ' ').title()}: {trend_data.get('direction', 'unknown')}")
            print()
        
        # Display escalation status
        if audit_data["escalation_required"]:
            print("🚨 ESCALATION REQUIRED")
            print("-" * 25)
            print("This audit has triggered escalation requirements.")
            print("Immediate attention and action are required.")
            print()
        
        # Display overall status
        health = audit_data.get("overall_health", "unknown")
        if health == "healthy":
            print("✅ AUDIT STATUS: EXCELLENT")
            print("Constitutional principles are well-protected.")
        elif health == "warning":
            print("⚠️  AUDIT STATUS: ATTENTION NEEDED")
            print("Some drift signals detected. Monitor closely.")
        elif health == "critical":
            print("🚨 AUDIT STATUS: CRITICAL")
            print("Significant drift detected. Immediate action required.")
        else:
            print("❓ AUDIT STATUS: UNKNOWN")
            print("Unable to determine audit status.")
        
        print("\n" + "=" * 80)
    
    def get_audit_history(self, days: int = 30) -> List[Dict[str, Any]]:
        """Get audit history for the specified number of days."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT timestamp, audit_type, overall_health, risk_level, 
                   integrity_score, drift_signals_count, alerts_count, 
                   recommendations_count, escalation_required
            FROM audit_history 
            WHERE timestamp >= datetime('now', '-{} days')
            ORDER BY timestamp DESC
        '''.format(days))
        
        history_data = cursor.fetchall()
        conn.close()
        
        history = []
        for row in history_data:
            history.append({
                "timestamp": row[0],
                "audit_type": row[1],
                "overall_health": row[2],
                "risk_level": row[3],
                "integrity_score": row[4],
                "drift_signals_count": row[5],
                "alerts_count": row[6],
                "recommendations_count": row[7],
                "escalation_required": bool(row[8])
            })
        
        return history


def main():
    """Main function to run scheduled constitutional audits."""
    parser = argparse.ArgumentParser(description="Constitutional Scheduled Audits")
    parser.add_argument("--audit-type", choices=["daily", "weekly", "monthly"], default="daily", help="Type of audit to run")
    parser.add_argument("--history", type=int, help="Show audit history for N days")
    parser.add_argument("--no-display", action="store_true", help="Skip audit report display")
    
    args = parser.parse_args()
    
    print("📋 Constitutional Scheduled Audits System")
    print("=" * 50)
    
    # Initialize audit system
    audits = ConstitutionalScheduledAudits()
    
    if args.history:
        # Show audit history
        print(f"📊 Showing audit history for last {args.history} days...")
        history = audits.get_audit_history(args.history)
        
        print(f"\n📋 AUDIT HISTORY ({len(history)} audits)")
        print("-" * 40)
        for audit in history:
            health_emoji = {"healthy": "🟢", "warning": "🟡", "critical": "🔴"}.get(audit["overall_health"], "⚪")
            print(f"{health_emoji} {audit['timestamp']} - {audit['audit_type']} - {audit['overall_health']} - {audit['integrity_score']:.1f}%")
        
        return
    
    # Run scheduled audit
    print(f"🔍 Running {args.audit_type} constitutional audit...")
    audit_data = audits.run_scheduled_audit(args.audit_type)
    
    # Display audit report
    if not args.no_display:
        audits.display_audit_report(audit_data)
    
    # Save audit report
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"constitutional_audit_{args.audit_type}_{timestamp}.json"
    
    with open(filename, "w") as f:
        json.dump(audit_data, f, indent=2)
    
    print(f"💾 Audit report saved to {filename}")
    
    # Exit with appropriate code
    if audit_data["escalation_required"]:
        print("🚨 CRITICAL: Escalation required!")
        sys.exit(1)
    elif audit_data.get("overall_health") == "warning":
        print("⚠️  WARNING: Attention needed.")
        sys.exit(2)
    else:
        print("✅ SUCCESS: Audit completed successfully.")
        sys.exit(0)


if __name__ == "__main__":
    main()
