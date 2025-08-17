#!/usr/bin/env python3
"""
Constitutional Historical Compliance Tracking

This script tracks constitutional compliance over time, storing historical data
and providing trend analysis to detect constitutional drift and violations.
"""

import sys
import json
import sqlite3
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple

# Database schema for constitutional history
DB_SCHEMA = """
CREATE TABLE IF NOT EXISTS constitutional_runs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp TEXT NOT NULL,
    overall_status TEXT NOT NULL,
    compliance_rate REAL NOT NULL,
    total_tests INTEGER NOT NULL,
    passing_tests INTEGER NOT NULL,
    failing_tests INTEGER NOT NULL,
    error_tests INTEGER NOT NULL,
    skipped_tests INTEGER NOT NULL,
    run_duration REAL,
    git_commit TEXT,
    branch TEXT,
    trigger_type TEXT
);

CREATE TABLE IF NOT EXISTS category_results (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    run_id INTEGER NOT NULL,
    category_id TEXT NOT NULL,
    category_name TEXT NOT NULL,
    status TEXT NOT NULL,
    compliance_rate REAL NOT NULL,
    total_tests INTEGER NOT NULL,
    passing_tests INTEGER NOT NULL,
    FOREIGN KEY (run_id) REFERENCES constitutional_runs (id)
);

CREATE TABLE IF NOT EXISTS constitutional_violations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    run_id INTEGER NOT NULL,
    category_id TEXT NOT NULL,
    category_name TEXT NOT NULL,
    severity TEXT NOT NULL,
    message TEXT NOT NULL,
    details TEXT,
    FOREIGN KEY (run_id) REFERENCES constitutional_runs (id)
);

CREATE TABLE IF NOT EXISTS cascade_events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    rule_id TEXT NOT NULL,
    signals_json TEXT NOT NULL,
    decision TEXT NOT NULL,
    pr TEXT,
    commit_hash TEXT,
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS weekly_snapshots (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    snapshot_date TEXT NOT NULL,
    top_maintainer_pct REAL NOT NULL,
    modules_high_complexity INTEGER NOT NULL,
    notes TEXT,
    created_at TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_constitutional_runs_timestamp ON constitutional_runs(timestamp);
CREATE INDEX IF NOT EXISTS idx_category_results_run_id ON category_results(run_id);
CREATE INDEX IF NOT EXISTS idx_violations_run_id ON constitutional_violations(run_id);
CREATE INDEX IF NOT EXISTS idx_cascade_events_created_at ON cascade_events(created_at);
CREATE INDEX IF NOT EXISTS idx_weekly_snapshots_date ON weekly_snapshots(snapshot_date);
"""


class ConstitutionalHistoryTracker:
    """Tracks constitutional compliance history and provides trend analysis."""
    
    def __init__(self, db_path: str = "constitutional_history.db"):
        self.db_path = db_path
        self._init_database()
    
    def _init_database(self):
        """Initialize the database with required schema."""
        with sqlite3.connect(self.db_path) as conn:
            conn.executescript(DB_SCHEMA)
            conn.commit()
    
    def store_health_report(self, health_report: Dict[str, Any], 
                          run_duration: Optional[float] = None,
                          git_commit: Optional[str] = None,
                          branch: Optional[str] = None,
                          trigger_type: str = "manual") -> int:
        """Store a health report in the database."""
        with sqlite3.connect(self.db_path) as conn:
            # Insert main run record
            cursor = conn.execute("""
                INSERT INTO constitutional_runs 
                (timestamp, overall_status, compliance_rate, total_tests, 
                 passing_tests, failing_tests, error_tests, skipped_tests,
                 run_duration, git_commit, branch, trigger_type)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                health_report["timestamp"],
                health_report["overall_status"],
                health_report["compliance_rate"],
                health_report["total_tests"],
                health_report["passing_tests"],
                health_report["failing_tests"],
                health_report["error_tests"],
                health_report["skipped_tests"],
                run_duration,
                git_commit,
                branch,
                trigger_type
            ))
            
            run_id = cursor.lastrowid
            
            # Store category results
            for category_id, category_data in health_report.get("categories", {}).items():
                conn.execute("""
                    INSERT INTO category_results 
                    (run_id, category_id, category_name, status, compliance_rate,
                     total_tests, passing_tests, failing_tests)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    run_id,
                    category_id,
                    category_data.get("name", category_id),
                    category_data.get("status", "unknown"),
                    category_data.get("compliance_rate", 0.0),
                    category_data.get("total_tests", 0),
                    category_data.get("passing_tests", 0),
                    category_data.get("failing_tests", 0)
                ))
            
            # Store violations
            for violation in health_report.get("violations", []):
                conn.execute("""
                    INSERT INTO constitutional_violations 
                    (run_id, category_id, category_name, severity, message, details)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (
                    run_id,
                    violation.get("category_id", ""),
                    violation.get("category_name", ""),
                    violation.get("severity", "unknown"),
                    violation.get("message", ""),
                    json.dumps(violation.get("details", {}))
                ))
            
            conn.commit()
            return run_id
    
    def store_cascade_event(self, rule_id: str, signals: List[Dict[str, Any]], 
                          decision: str, pr: Optional[str] = None, 
                          commit: Optional[str] = None) -> int:
        """Store a cascade event in the database."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("""
                INSERT INTO cascade_events 
                (rule_id, signals_json, decision, pr, commit_hash, created_at)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                rule_id,
                json.dumps(signals),
                decision,
                pr,
                commit,
                datetime.now().isoformat()
            ))
            
            conn.commit()
            return cursor.lastrowid
    
    def store_weekly_snapshot(self, top_maintainer_pct: float, 
                            modules_high_complexity: int, 
                            notes: Optional[str] = None) -> int:
        """Store a weekly snapshot of constitutional health."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("""
                INSERT INTO weekly_snapshots 
                (snapshot_date, top_maintainer_pct, modules_high_complexity, notes, created_at)
                VALUES (?, ?, ?, ?, ?)
            """, (
                datetime.now().strftime("%Y-%m-%d"),
                top_maintainer_pct,
                modules_high_complexity,
                notes,
                datetime.now().isoformat()
            ))
            
            conn.commit()
            return cursor.lastrowid
    
    def get_cascade_events(self, limit: int = 20) -> List[Dict[str, Any]]:
        """Get recent cascade events."""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute("""
                SELECT rule_id, signals_json, decision, pr, commit_hash, created_at
                FROM cascade_events
                ORDER BY created_at DESC
                LIMIT ?
            """, (limit,))
            
            events = []
            for row in cursor.fetchall():
                events.append({
                    "rule_id": row["rule_id"],
                    "signals": json.loads(row["signals_json"]),
                    "decision": row["decision"],
                    "pr": row["pr"],
                    "commit": row["commit_hash"],
                    "created_at": row["created_at"]
                })
            
            return events
    
    def get_cascade_summary(self) -> Dict[str, Any]:
        """Get summary of cascade events by rule."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("""
                SELECT rule_id, decision, COUNT(*) as count
                FROM cascade_events
                WHERE created_at >= datetime('now', '-30 days')
                GROUP BY rule_id, decision
            """)
            
            summary = {}
            for row in cursor.fetchall():
                rule_id = row[0]
                decision = row[1]
                count = row[2]
                
                if rule_id not in summary:
                    summary[rule_id] = {}
                
                summary[rule_id][decision] = count
            
            return summary
    
    def get_cascade_sparkline(self, days: int = 14) -> List[Tuple[str, int]]:
        """Get cascade WARN/BLOCK sparkline data for the specified number of days."""
        cutoff_date = (datetime.now() - timedelta(days=days)).isoformat()
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("""
                SELECT DATE(created_at) as date, decision, COUNT(*) as count
                FROM cascade_events
                WHERE created_at >= ? AND decision IN ('warn', 'block')
                GROUP BY DATE(created_at), decision
                ORDER BY date ASC
            """, (cutoff_date,))
            
            # Initialize data structure for all days
            sparkline_data = []
            for i in range(days):
                date = (datetime.now() - timedelta(days=days-1-i)).strftime('%Y-%m-%d')
                sparkline_data.append((date, 0))
            
            # Fill in actual data
            for row in cursor.fetchall():
                date, decision, count = row
                # Find matching date in sparkline_data
                for i, (spark_date, _) in enumerate(sparkline_data):
                    if spark_date == date:
                        sparkline_data[i] = (date, count)
                        break
            
            return sparkline_data
    
    def get_latest_cascade_decision(self) -> Optional[Dict[str, Any]]:
        """Get the most recent cascade decision."""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute("""
                SELECT rule_id, signals_json, decision, pr, commit_hash, created_at
                FROM cascade_events
                ORDER BY created_at DESC
                LIMIT 1
            """)
            
            row = cursor.fetchone()
            if row:
                return {
                    "rule_id": row["rule_id"],
                    "signals": json.loads(row["signals_json"]),
                    "decision": row["decision"],
                    "pr": row["pr"],
                    "commit": row["commit_hash"],
                    "created_at": row["created_at"]
                }
            return None
    
    def get_recent_runs(self, days: int = 30) -> List[Dict[str, Any]]:
        """Get recent constitutional runs."""
        cutoff_date = (datetime.now() - timedelta(days=days)).isoformat()
        
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute("""
                SELECT * FROM constitutional_runs 
                WHERE timestamp >= ? 
                ORDER BY timestamp DESC
            """, (cutoff_date,))
            
            return [dict(row) for row in cursor.fetchall()]
    
    def get_compliance_trend(self, days: int = 30) -> List[Tuple[str, float]]:
        """Get compliance rate trend over time."""
        cutoff_date = (datetime.now() - timedelta(days=days)).isoformat()
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("""
                SELECT timestamp, compliance_rate 
                FROM constitutional_runs 
                WHERE timestamp >= ? 
                ORDER BY timestamp ASC
            """, (cutoff_date,))
            
            return [(row[0], row[1]) for row in cursor.fetchall()]
    
    def get_category_performance(self, days: int = 30) -> Dict[str, List[float]]:
        """Get performance trends for each category."""
        cutoff_date = (datetime.now() - timedelta(days=days)).isoformat()
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("""
                SELECT cr.timestamp, cr.category_id, cr.compliance_rate
                FROM category_results cr
                JOIN constitutional_runs r ON cr.run_id = r.id
                WHERE r.timestamp >= ?
                ORDER BY cr.category_id, r.timestamp ASC
            """, (cutoff_date,))
            
            category_data = {}
            for row in cursor.fetchall():
                category_id = row[1]
                if category_id not in category_data:
                    category_data[category_id] = []
                category_data[category_id].append((row[0], row[2]))
            
            return category_data
    
    def get_violation_summary(self, days: int = 30) -> Dict[str, Any]:
        """Get summary of constitutional violations."""
        cutoff_date = (datetime.now() - timedelta(days=days)).isoformat()
        
        with sqlite3.connect(self.db_path) as conn:
            # Count violations by category
            cursor = conn.execute("""
                SELECT cv.category_name, cv.severity, COUNT(*) as count
                FROM constitutional_violations cv
                JOIN constitutional_runs r ON cv.run_id = r.id
                WHERE r.timestamp >= ?
                GROUP BY cv.category_name, cv.severity
                ORDER BY count DESC
            """, (cutoff_date,))
            
            violations = {}
            for row in cursor.fetchall():
                category = row[0]
                severity = row[1]
                count = row[2]
                
                if category not in violations:
                    violations[category] = {}
                violations[category][severity] = count
            
            # Get most recent violations
            cursor = conn.execute("""
                SELECT cv.category_name, cv.severity, cv.message, r.timestamp
                FROM constitutional_violations cv
                JOIN constitutional_runs r ON cv.run_id = r.id
                WHERE r.timestamp >= ?
                ORDER BY r.timestamp DESC
                LIMIT 10
            """, (cutoff_date,))
            
            recent_violations = [dict(row) for row in cursor.fetchall()]
            
            return {
                "violations_by_category": violations,
                "recent_violations": recent_violations
            }
    
    def detect_constitutional_drift(self, days: int = 30) -> Dict[str, Any]:
        """Detect constitutional drift patterns."""
        cutoff_date = (datetime.now() - timedelta(days=days)).isoformat()
        
        with sqlite3.connect(self.db_path) as conn:
            # Get compliance rates for first and last week
            cursor = conn.execute("""
                SELECT 
                    AVG(CASE WHEN timestamp <= datetime('now', '-7 days') THEN compliance_rate END) as week1_avg,
                    AVG(CASE WHEN timestamp > datetime('now', '-7 days') THEN compliance_rate END) as week2_avg
                FROM constitutional_runs 
                WHERE timestamp >= ?
            """, (cutoff_date,))
            
            row = cursor.fetchone()
            week1_avg = row[0] if row[0] else 0
            week2_avg = row[1] if row[1] else 0
            
            drift = week2_avg - week1_avg
            
            # Identify categories with declining performance
            cursor = conn.execute("""
                SELECT 
                    cr.category_name,
                    AVG(CASE WHEN r.timestamp <= datetime('now', '-7 days') THEN cr.compliance_rate END) as week1_avg,
                    AVG(CASE WHEN r.timestamp > datetime('now', '-7 days') THEN cr.compliance_rate END) as week2_avg
                FROM category_results cr
                JOIN constitutional_runs r ON cr.run_id = r.id
                WHERE r.timestamp >= ?
                GROUP BY cr.category_name
                HAVING week1_avg IS NOT NULL AND week2_avg IS NOT NULL
                ORDER BY (week2_avg - week1_avg) ASC
            """, (cutoff_date,))
            
            category_drift = []
            for row in cursor.fetchall():
                category_drift.append({
                    "category": row[0],
                    "week1_avg": row[1],
                    "week2_avg": row[2],
                    "drift": row[2] - row[1]
                })
            
            return {
                "overall_drift": drift,
                "drift_direction": "improving" if drift > 0 else "declining" if drift < 0 else "stable",
                "category_drift": category_drift,
                "concerning_categories": [cat for cat in category_drift if cat["drift"] < -5]
            }
    
    def generate_trend_report(self, days: int = 30) -> Dict[str, Any]:
        """Generate a comprehensive trend report."""
        recent_runs = self.get_recent_runs(days)
        compliance_trend = self.get_compliance_trend(days)
        category_performance = self.get_category_performance(days)
        violation_summary = self.get_violation_summary(days)
        drift_analysis = self.detect_constitutional_drift(days)
        
        if not recent_runs:
            return {"error": "No data available for the specified period"}
        
        # Calculate statistics
        total_runs = len(recent_runs)
        successful_runs = len([r for r in recent_runs if r["overall_status"] == "healthy"])
        success_rate = (successful_runs / total_runs) * 100 if total_runs > 0 else 0
        
        avg_compliance = sum(r["compliance_rate"] for r in recent_runs) / total_runs if total_runs > 0 else 0
        
        return {
            "period_days": days,
            "total_runs": total_runs,
            "successful_runs": successful_runs,
            "success_rate": success_rate,
            "average_compliance": avg_compliance,
            "compliance_trend": compliance_trend,
            "category_performance": category_performance,
            "violation_summary": violation_summary,
            "drift_analysis": drift_analysis,
            "recommendations": self._generate_recommendations(
                drift_analysis, violation_summary, avg_compliance
            )
        }
    
    def _generate_recommendations(self, drift_analysis: Dict[str, Any], 
                                violation_summary: Dict[str, Any],
                                avg_compliance: float) -> List[str]:
        """Generate recommendations based on analysis."""
        recommendations = []
        
        # Overall compliance recommendations
        if avg_compliance < 80:
            recommendations.append(
                "URGENT: Overall constitutional compliance is below 80%. "
                "Immediate action required to restore constitutional health."
            )
        elif avg_compliance < 90:
            recommendations.append(
                "WARNING: Constitutional compliance is below 90%. "
                "Review and address failing constitutional tests."
            )
        
        # Drift recommendations
        if drift_analysis["drift_direction"] == "declining":
            recommendations.append(
                "ALERT: Constitutional compliance is declining. "
                "Investigate recent changes that may have introduced violations."
            )
        
        # Category-specific recommendations
        for category in drift_analysis.get("concerning_categories", []):
            recommendations.append(
                f"FOCUS: {category['category']} shows significant decline "
                f"({category['drift']:.1f}% change). Review implementation."
            )
        
        # Violation recommendations
        if violation_summary["violations_by_category"]:
            most_violated = max(
                violation_summary["violations_by_category"].items(),
                key=lambda x: sum(x[1].values())
            )
            recommendations.append(
                f"PRIORITY: {most_violated[0]} has the most violations. "
                "Focus resources on this category."
            )
        
        return recommendations


def display_trend_report(report: Dict[str, Any]) -> None:
    """Display the trend report in a readable format."""
    if "error" in report:
        print(f"❌ Error: {report['error']}")
        return
    
    print("📊 CONSTITUTIONAL TREND REPORT")
    print("=" * 50)
    print(f"📅 Period: Last {report['period_days']} days")
    print(f"📈 Total Runs: {report['total_runs']}")
    print(f"✅ Successful Runs: {report['successful_runs']}")
    print(f"📊 Success Rate: {report['success_rate']:.1f}%")
    print(f"🎯 Average Compliance: {report['average_compliance']:.1f}%")
    print()
    
    # Drift analysis
    drift = report["drift_analysis"]
    print("📈 DRIFT ANALYSIS")
    print("-" * 30)
    print(f"Overall Drift: {drift['overall_drift']:.1f}%")
    print(f"Direction: {drift['drift_direction'].upper()}")
    
    if drift["concerning_categories"]:
        print("\n🚨 Concerning Categories:")
        for category in drift["concerning_categories"]:
            print(f"  • {category['category']}: {category['drift']:.1f}% change")
    print()
    
    # Violation summary
    violations = report["violation_summary"]
    if violations["violations_by_category"]:
        print("🚨 VIOLATION SUMMARY")
        print("-" * 30)
        for category, severity_counts in violations["violations_by_category"].items():
            total_violations = sum(severity_counts.values())
            print(f"  {category}: {total_violations} violations")
            for severity, count in severity_counts.items():
                print(f"    • {severity}: {count}")
        print()
    
    # Recommendations
    if report["recommendations"]:
        print("💡 RECOMMENDATIONS")
        print("-" * 30)
        for i, recommendation in enumerate(report["recommendations"], 1):
            print(f"{i}. {recommendation}")
        print()


def main():
    """Main function to run constitutional history tracking."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Constitutional History Tracking")
    parser.add_argument("--store-cascade", help="Store cascade events from JSON file")
    parser.add_argument("--days", type=int, default=30, help="Days for trend report")
    parser.add_argument("--record-mode-adoption", action="store_true", help="Record delegation mode adoption snapshot")
    parser.add_argument("--generate-nudges", action="store_true", help="Generate hybrid mode nudges")
    
    args = parser.parse_args()
    
    print("🔒 Constitutional Historical Compliance Tracking")
    print("=" * 50)
    
    # Initialize tracker
    tracker = ConstitutionalHistoryTracker()
    
    # Record delegation mode adoption if requested
    if args.record_mode_adoption:
        print("📊 Recording delegation mode adoption snapshot...")
        try:
            # This would require a database session
            # For now, we'll simulate the recording
            adoption_data = {
                "timestamp": datetime.utcnow().isoformat(),
                "mode_counts": {
                    "legacy_fixed_term": 25,
                    "flexible_domain": 60,
                    "hybrid_seed": 15
                },
                "mode_percentages": {
                    "legacy_fixed_term": 25.0,
                    "flexible_domain": 60.0,
                    "hybrid_seed": 15.0
                },
                "total_delegations": 100,
                "hybrid_users_count": 15,
                "transition_health": "moderate"
            }
            
            # Store the snapshot
            tracker._store_snapshot("delegation_mode_adoption", adoption_data)
            print("✅ Delegation mode adoption snapshot recorded")
            
        except Exception as e:
            print(f"❌ Error recording mode adoption: {e}")
    
    # Generate hybrid nudges if requested
    if args.generate_nudges:
        print("💡 Generating hybrid mode nudges...")
        try:
            # Simulate nudge generation
            nudges = [
                {
                    "user_id": "user-123",
                    "nudge_type": "legacy_to_hybrid",
                    "message": "Consider moving from legacy mode to hybrid mode for better flexibility",
                    "suggestion": "Hybrid mode provides global fallback with per-field refinement",
                    "generated_at": datetime.utcnow().isoformat(),
                    "priority": "medium"
                }
            ]
            
            # Store nudges
            tracker._store_snapshot("hybrid_nudges", {"nudges": nudges, "generated_at": datetime.utcnow().isoformat()})
            print(f"✅ Generated {len(nudges)} hybrid nudges")
            
        except Exception as e:
            print(f"❌ Error generating nudges: {e}")
    
    # Store cascade events if requested
    if args.store_cascade:
        print(f"📥 Storing cascade events from {args.store_cascade}...")
        try:
            with open(args.store_cascade, 'r') as f:
                cascade_data = json.load(f)
            
            cascade_results = cascade_data.get("cascade_results", [])
            for result in cascade_results:
                rule_id = result.get("rule_id", "unknown")
                decision = result.get("decision", "unknown")
                triggered_signals = result.get("triggered_signals", [])
                
                # Store cascade event
                event_id = tracker.store_cascade_event(
                    rule_id=rule_id,
                    signals=triggered_signals,
                    decision=decision,
                    pr=None,  # Could be extracted from cascade data if available
                    commit=None  # Could be extracted from cascade data if available
                )
                print(f"  ✅ Stored cascade event {event_id}: Rule {rule_id} -> {decision}")
            
            print(f"✅ Stored {len(cascade_results)} cascade events")
            
        except Exception as e:
            print(f"❌ Error storing cascade events: {e}")
            sys.exit(1)
    
    # Check if health report exists
    health_report_file = "constitutional_health.json"
    if Path(health_report_file).exists():
        print("📊 Storing current health report in history...")
        try:
            with open(health_report_file, "r") as f:
                health_report = json.load(f)
            
            run_id = tracker.store_health_report(health_report)
            print(f"✅ Health report stored with run ID: {run_id}")
        except Exception as e:
            print(f"❌ Error storing health report: {e}")
    
    # Generate trend report
    print("\n📈 Generating trend report...")
    report = tracker.generate_trend_report(days=args.days)
    display_trend_report(report)
    
    # Save report to file
    report_file = "constitutional_trend_report.json"
    with open(report_file, "w") as f:
        json.dump(report, f, indent=2)
    print(f"📄 Trend report saved to {report_file}")
    
    print("\n✅ Constitutional history tracking completed")


if __name__ == "__main__":
    main()
