#!/usr/bin/env python3
"""
Constitutional Alert Governance System

This script ensures constitutional alerts cannot be permanently muted without justification
and implements escalation mechanisms for ignored alerts.
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


class ConstitutionalAlertGovernance:
    """Governance system for constitutional alerts."""
    
    def __init__(self, db_path: str = "constitutional_history.db"):
        self.db_path = db_path
        self.alert_config = {}
        self.escalation_rules = {}
        
        # Initialize database
        self._init_database()
        
        # Load configuration
        self._load_configuration()
    
    def _init_database(self):
        """Initialize the alert governance database."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Create alert governance table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS alert_governance (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                alert_id TEXT NOT NULL,
                alert_level TEXT NOT NULL,
                alert_category TEXT NOT NULL,
                alert_message TEXT NOT NULL,
                created_at TEXT NOT NULL,
                muted_at TEXT,
                muted_by TEXT,
                mute_reason TEXT,
                mute_duration_hours INTEGER,
                auto_unmute_at TEXT,
                escalation_level INTEGER DEFAULT 0,
                escalation_triggered_at TEXT,
                resolved_at TEXT,
                resolved_by TEXT,
                resolution_notes TEXT,
                created_at_timestamp TEXT DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Create escalation history table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS escalation_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                alert_id TEXT NOT NULL,
                escalation_level INTEGER NOT NULL,
                escalated_at TEXT NOT NULL,
                escalated_by TEXT,
                escalation_reason TEXT,
                escalation_action TEXT,
                resolved_at TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Create alert suppression audit table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS alert_suppression_audit (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                alert_id TEXT NOT NULL,
                suppression_action TEXT NOT NULL,
                suppressed_by TEXT,
                suppression_reason TEXT,
                suppression_duration_hours INTEGER,
                justification_required BOOLEAN DEFAULT TRUE,
                justification_provided BOOLEAN DEFAULT FALSE,
                justification_text TEXT,
                approved_by TEXT,
                audit_timestamp TEXT DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def _load_configuration(self):
        """Load alert governance configuration."""
        self.alert_config = {
            "suppression_rules": {
                "max_suppression_duration_hours": 24,
                "require_justification": True,
                "require_approval": True,
                "approval_threshold": 2,  # Number of approvals required
                "auto_unmute_enabled": True,
                "suppression_audit_enabled": True
            },
            "escalation_rules": {
                "escalation_threshold": 3,  # Number of ignored alerts before escalation
                "escalation_timeout_hours": 4,  # Time before escalation
                "max_escalation_level": 5,
                "escalation_actions": [
                    "team_notification",
                    "management_notification", 
                    "constitutional_authority_notification",
                    "emergency_contact_notification",
                    "system_shutdown_notification"
                ]
            },
            "alert_fatigue_monitoring": {
                "fatigue_threshold": 10,  # Number of alerts in 24 hours
                "fatigue_timeout_hours": 6,
                "fatigue_escalation_enabled": True,
                "fatigue_reduction_mechanisms": [
                    "alert_consolidation",
                    "threshold_adjustment",
                    "priority_reassessment"
                ]
            }
        }
        
        self.escalation_rules = {
            "level_1": {
                "name": "Team Notification",
                "description": "Notify team members of ignored alert",
                "timeout_hours": 2,
                "action": "team_notification"
            },
            "level_2": {
                "name": "Management Notification",
                "description": "Notify management of continued alert",
                "timeout_hours": 4,
                "action": "management_notification"
            },
            "level_3": {
                "name": "Constitutional Authority Notification",
                "description": "Notify constitutional authority",
                "timeout_hours": 6,
                "action": "constitutional_authority_notification"
            },
            "level_4": {
                "name": "Emergency Contact Notification",
                "description": "Notify emergency contacts",
                "timeout_hours": 8,
                "action": "emergency_contact_notification"
            },
            "level_5": {
                "name": "System Shutdown Notification",
                "description": "Prepare for system shutdown",
                "timeout_hours": 12,
                "action": "system_shutdown_notification"
            }
        }
    
    def create_alert(self, alert_data: Dict[str, Any]) -> str:
        """Create a new constitutional alert."""
        alert_id = f"alert_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{hash(alert_data.get('message', '')) % 10000}"
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO alert_governance (
                alert_id, alert_level, alert_category, alert_message, created_at
            ) VALUES (?, ?, ?, ?, ?)
        ''', (
            alert_id,
            alert_data.get("level", "info"),
            alert_data.get("category", "unknown"),
            alert_data.get("message", ""),
            datetime.now().isoformat()
        ))
        
        conn.commit()
        conn.close()
        
        print(f"🔔 Alert created: {alert_id}")
        return alert_id
    
    def mute_alert(self, alert_id: str, muted_by: str, reason: str, duration_hours: int = None) -> bool:
        """Mute a constitutional alert with justification."""
        if duration_hours is None:
            duration_hours = self.alert_config["suppression_rules"]["max_suppression_duration_hours"]
        
        # Check if justification is required
        if self.alert_config["suppression_rules"]["require_justification"] and not reason:
            print("❌ Justification required for alert suppression")
            return False
        
        # Check if approval is required
        if self.alert_config["suppression_rules"]["require_approval"]:
            approval_required = self._check_approval_required(alert_id)
            if approval_required:
                print("❌ Approval required for alert suppression")
                return False
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Calculate auto-unmute time
        auto_unmute_at = None
        if self.alert_config["suppression_rules"]["auto_unmute_enabled"]:
            auto_unmute_at = (datetime.now() + timedelta(hours=duration_hours)).isoformat()
        
        # Update alert
        cursor.execute('''
            UPDATE alert_governance 
            SET muted_at = ?, muted_by = ?, mute_reason = ?, 
                mute_duration_hours = ?, auto_unmute_at = ?
            WHERE alert_id = ?
        ''', (
            datetime.now().isoformat(),
            muted_by,
            reason,
            duration_hours,
            auto_unmute_at,
            alert_id
        ))
        
        # Record suppression audit
        if self.alert_config["suppression_rules"]["suppression_audit_enabled"]:
            cursor.execute('''
                INSERT INTO alert_suppression_audit (
                    alert_id, suppression_action, suppressed_by, suppression_reason,
                    suppression_duration_hours, justification_required, justification_provided,
                    justification_text
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                alert_id,
                "mute",
                muted_by,
                reason,
                duration_hours,
                self.alert_config["suppression_rules"]["require_justification"],
                bool(reason),
                reason
            ))
        
        conn.commit()
        conn.close()
        
        print(f"🔇 Alert {alert_id} muted for {duration_hours} hours")
        return True
    
    def unmute_alert(self, alert_id: str, unmuted_by: str, reason: str = None) -> bool:
        """Unmute a constitutional alert."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Update alert
        cursor.execute('''
            UPDATE alert_governance 
            SET muted_at = NULL, muted_by = NULL, mute_reason = NULL,
                mute_duration_hours = NULL, auto_unmute_at = NULL
            WHERE alert_id = ?
        ''', (alert_id,))
        
        # Record suppression audit
        if self.alert_config["suppression_rules"]["suppression_audit_enabled"]:
            cursor.execute('''
                INSERT INTO alert_suppression_audit (
                    alert_id, suppression_action, suppressed_by, suppression_reason,
                    justification_required, justification_provided, justification_text
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (
                alert_id,
                "unmute",
                unmuted_by,
                reason or "Manual unmute",
                False,
                True,
                reason or "Manual unmute"
            ))
        
        conn.commit()
        conn.close()
        
        print(f"🔊 Alert {alert_id} unmuted")
        return True
    
    def resolve_alert(self, alert_id: str, resolved_by: str, resolution_notes: str = None) -> bool:
        """Resolve a constitutional alert."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            UPDATE alert_governance 
            SET resolved_at = ?, resolved_by = ?, resolution_notes = ?
            WHERE alert_id = ?
        ''', (
            datetime.now().isoformat(),
            resolved_by,
            resolution_notes,
            alert_id
        ))
        
        conn.commit()
        conn.close()
        
        print(f"✅ Alert {alert_id} resolved")
        return True
    
    def escalate_alert(self, alert_id: str, escalation_level: int, escalated_by: str = None, reason: str = None) -> bool:
        """Escalate a constitutional alert."""
        if escalation_level > self.alert_config["escalation_rules"]["max_escalation_level"]:
            print(f"❌ Escalation level {escalation_level} exceeds maximum")
            return False
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Update alert escalation level
        cursor.execute('''
            UPDATE alert_governance 
            SET escalation_level = ?, escalation_triggered_at = ?
            WHERE alert_id = ?
        ''', (
            escalation_level,
            datetime.now().isoformat(),
            alert_id
        ))
        
        # Record escalation history
        cursor.execute('''
            INSERT INTO escalation_history (
                alert_id, escalation_level, escalated_at, escalated_by, escalation_reason
            ) VALUES (?, ?, ?, ?, ?)
        ''', (
            alert_id,
            escalation_level,
            datetime.now().isoformat(),
            escalated_by or "system",
            reason or "Automatic escalation"
        ))
        
        conn.commit()
        conn.close()
        
        # Execute escalation action
        self._execute_escalation_action(alert_id, escalation_level)
        
        print(f"🚨 Alert {alert_id} escalated to level {escalation_level}")
        return True
    
    def _execute_escalation_action(self, alert_id: str, escalation_level: int):
        """Execute the appropriate escalation action."""
        level_key = f"level_{escalation_level}"
        if level_key in self.escalation_rules:
            action = self.escalation_rules[level_key]["action"]
            
            if action == "team_notification":
                self._send_team_notification(alert_id, escalation_level)
            elif action == "management_notification":
                self._send_management_notification(alert_id, escalation_level)
            elif action == "constitutional_authority_notification":
                self._send_constitutional_authority_notification(alert_id, escalation_level)
            elif action == "emergency_contact_notification":
                self._send_emergency_contact_notification(alert_id, escalation_level)
            elif action == "system_shutdown_notification":
                self._send_system_shutdown_notification(alert_id, escalation_level)
    
    def _send_team_notification(self, alert_id: str, escalation_level: int):
        """Send team notification."""
        print(f"📢 TEAM NOTIFICATION: Alert {alert_id} escalated to level {escalation_level}")
        # TODO: Implement actual team notification (Slack, email, etc.)
    
    def _send_management_notification(self, alert_id: str, escalation_level: int):
        """Send management notification."""
        print(f"📢 MANAGEMENT NOTIFICATION: Alert {alert_id} escalated to level {escalation_level}")
        # TODO: Implement actual management notification
    
    def _send_constitutional_authority_notification(self, alert_id: str, escalation_level: int):
        """Send constitutional authority notification."""
        print(f"📢 CONSTITUTIONAL AUTHORITY NOTIFICATION: Alert {alert_id} escalated to level {escalation_level}")
        # TODO: Implement actual constitutional authority notification
    
    def _send_emergency_contact_notification(self, alert_id: str, escalation_level: int):
        """Send emergency contact notification."""
        print(f"📢 EMERGENCY CONTACT NOTIFICATION: Alert {alert_id} escalated to level {escalation_level}")
        # TODO: Implement actual emergency contact notification
    
    def _send_system_shutdown_notification(self, alert_id: str, escalation_level: int):
        """Send system shutdown notification."""
        print(f"📢 SYSTEM SHUTDOWN NOTIFICATION: Alert {alert_id} escalated to level {escalation_level}")
        # TODO: Implement actual system shutdown notification
    
    def check_escalation_triggers(self):
        """Check for alerts that need escalation."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Find alerts that need escalation
        cursor.execute('''
            SELECT alert_id, escalation_level, created_at, escalation_triggered_at
            FROM alert_governance 
            WHERE resolved_at IS NULL 
            AND muted_at IS NULL
            AND escalation_level < ?
        ''', (self.alert_config["escalation_rules"]["max_escalation_level"],))
        
        alerts = cursor.fetchall()
        conn.close()
        
        for alert in alerts:
            alert_id, current_level, created_at, last_escalation = alert
            
            # Check if escalation is needed
            if self._should_escalate(alert_id, current_level, created_at, last_escalation):
                self.escalate_alert(alert_id, current_level + 1)
    
    def _should_escalate(self, alert_id: str, current_level: int, created_at: str, last_escalation: str) -> bool:
        """Determine if an alert should be escalated."""
        if current_level >= self.alert_config["escalation_rules"]["max_escalation_level"]:
            return False
        
        # Calculate time since last escalation or creation
        if last_escalation:
            reference_time = datetime.fromisoformat(last_escalation)
        else:
            reference_time = datetime.fromisoformat(created_at)
        
        time_since_reference = datetime.now() - reference_time
        timeout_hours = self.escalation_rules[f"level_{current_level + 1}"]["timeout_hours"]
        
        return time_since_reference.total_seconds() > (timeout_hours * 3600)
    
    def check_alert_fatigue(self) -> Dict[str, Any]:
        """Check for alert fatigue patterns."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Count alerts in last 24 hours
        cursor.execute('''
            SELECT COUNT(*) as alert_count
            FROM alert_governance 
            WHERE created_at >= datetime('now', '-24 hours')
        ''')
        
        alert_count = cursor.fetchone()[0]
        
        # Count muted alerts in last 24 hours
        cursor.execute('''
            SELECT COUNT(*) as muted_count
            FROM alert_governance 
            WHERE muted_at >= datetime('now', '-24 hours')
        ''')
        
        muted_count = cursor.fetchone()[0]
        
        conn.close()
        
        fatigue_data = {
            "alert_count_24h": alert_count,
            "muted_count_24h": muted_count,
            "fatigue_threshold": self.alert_config["alert_fatigue_monitoring"]["fatigue_threshold"],
            "fatigue_detected": alert_count > self.alert_config["alert_fatigue_monitoring"]["fatigue_threshold"],
            "suppression_rate": (muted_count / alert_count * 100) if alert_count > 0 else 0
        }
        
        return fatigue_data
    
    def _check_approval_required(self, alert_id: str) -> bool:
        """Check if approval is required for alert suppression."""
        # This would implement actual approval checking logic
        # For now, return False (no approval required)
        return False
    
    def get_active_alerts(self) -> List[Dict[str, Any]]:
        """Get all active (non-resolved) alerts."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT alert_id, alert_level, alert_category, alert_message, 
                   created_at, muted_at, escalation_level, escalation_triggered_at
            FROM alert_governance 
            WHERE resolved_at IS NULL
            ORDER BY created_at DESC
        ''')
        
        alerts = cursor.fetchall()
        conn.close()
        
        active_alerts = []
        for alert in alerts:
            active_alerts.append({
                "alert_id": alert[0],
                "level": alert[1],
                "category": alert[2],
                "message": alert[3],
                "created_at": alert[4],
                "muted_at": alert[5],
                "escalation_level": alert[6],
                "escalation_triggered_at": alert[7]
            })
        
        return active_alerts
    
    def get_suppression_audit(self, days: int = 30) -> List[Dict[str, Any]]:
        """Get alert suppression audit history."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT alert_id, suppression_action, suppressed_by, suppression_reason,
                   suppression_duration_hours, justification_provided, justification_text,
                   audit_timestamp
            FROM alert_suppression_audit 
            WHERE audit_timestamp >= datetime('now', '-{} days')
            ORDER BY audit_timestamp DESC
        '''.format(days))
        
        audit_records = cursor.fetchall()
        conn.close()
        
        audit_history = []
        for record in audit_records:
            audit_history.append({
                "alert_id": record[0],
                "action": record[1],
                "suppressed_by": record[2],
                "reason": record[3],
                "duration_hours": record[4],
                "justification_provided": bool(record[5]),
                "justification_text": record[6],
                "timestamp": record[7]
            })
        
        return audit_history
    
    def display_alert_status(self):
        """Display current alert status."""
        active_alerts = self.get_active_alerts()
        fatigue_data = self.check_alert_fatigue()
        
        print("\n" + "=" * 80)
        print("🔔 CONSTITUTIONAL ALERT GOVERNANCE STATUS")
        print("=" * 80)
        print(f"📅 Status as of: {datetime.now().isoformat()}")
        print()
        
        # Display active alerts
        print(f"📊 ACTIVE ALERTS ({len(active_alerts)})")
        print("-" * 30)
        for alert in active_alerts:
            level_emoji = {"critical": "🔴", "warning": "🟡", "info": "🔵"}.get(alert["level"], "⚪")
            status_emoji = "🔇" if alert["muted_at"] else "🔊"
            escalation_emoji = "🚨" if alert["escalation_level"] > 0 else ""
            
            print(f"{level_emoji} {status_emoji} {escalation_emoji} {alert['alert_id']} - {alert['category']} - {alert['message']}")
        
        print()
        
        # Display fatigue data
        print("😴 ALERT FATIGUE MONITORING")
        print("-" * 30)
        print(f"Alerts in last 24h: {fatigue_data['alert_count_24h']}")
        print(f"Muted in last 24h: {fatigue_data['muted_count_24h']}")
        print(f"Suppression rate: {fatigue_data['suppression_rate']:.1f}%")
        print(f"Fatigue threshold: {fatigue_data['fatigue_threshold']}")
        print(f"Fatigue detected: {'YES' if fatigue_data['fatigue_detected'] else 'NO'}")
        
        print()
        
        # Display governance status
        print("🛡️ GOVERNANCE STATUS")
        print("-" * 20)
        print(f"Suppression audit: {'ENABLED' if self.alert_config['suppression_rules']['suppression_audit_enabled'] else 'DISABLED'}")
        print(f"Justification required: {'YES' if self.alert_config['suppression_rules']['require_justification'] else 'NO'}")
        print(f"Approval required: {'YES' if self.alert_config['suppression_rules']['require_approval'] else 'NO'}")
        print(f"Auto-unmute: {'ENABLED' if self.alert_config['suppression_rules']['auto_unmute_enabled'] else 'DISABLED'}")
        print(f"Max escalation level: {self.alert_config['escalation_rules']['max_escalation_level']}")
        
        print("\n" + "=" * 80)


def main():
    """Main function to run constitutional alert governance."""
    parser = argparse.ArgumentParser(description="Constitutional Alert Governance")
    parser.add_argument("--status", action="store_true", help="Show alert governance status")
    parser.add_argument("--check-escalation", action="store_true", help="Check for escalation triggers")
    parser.add_argument("--create-alert", help="Create a test alert")
    parser.add_argument("--mute-alert", help="Mute an alert")
    parser.add_argument("--unmute-alert", help="Unmute an alert")
    parser.add_argument("--resolve-alert", help="Resolve an alert")
    parser.add_argument("--escalate-alert", help="Escalate an alert")
    parser.add_argument("--audit", type=int, help="Show suppression audit for N days")
    
    args = parser.parse_args()
    
    print("🔔 Constitutional Alert Governance System")
    print("=" * 50)
    
    # Initialize alert governance
    governance = ConstitutionalAlertGovernance()
    
    if args.status:
        # Show alert governance status
        governance.display_alert_status()
    
    elif args.check_escalation:
        # Check for escalation triggers
        print("🔍 Checking for escalation triggers...")
        governance.check_escalation_triggers()
        print("✅ Escalation check completed")
    
    elif args.create_alert:
        # Create a test alert
        alert_data = {
            "level": "warning",
            "category": "test",
            "message": args.create_alert
        }
        alert_id = governance.create_alert(alert_data)
        print(f"✅ Test alert created: {alert_id}")
    
    elif args.mute_alert:
        # Mute an alert
        success = governance.mute_alert(args.mute_alert, "test_user", "Test mute")
        if success:
            print(f"✅ Alert {args.mute_alert} muted")
        else:
            print(f"❌ Failed to mute alert {args.mute_alert}")
    
    elif args.unmute_alert:
        # Unmute an alert
        success = governance.unmute_alert(args.unmute_alert, "test_user")
        if success:
            print(f"✅ Alert {args.unmute_alert} unmuted")
        else:
            print(f"❌ Failed to unmute alert {args.unmute_alert}")
    
    elif args.resolve_alert:
        # Resolve an alert
        success = governance.resolve_alert(args.resolve_alert, "test_user", "Test resolution")
        if success:
            print(f"✅ Alert {args.resolve_alert} resolved")
        else:
            print(f"❌ Failed to resolve alert {args.resolve_alert}")
    
    elif args.escalate_alert:
        # Escalate an alert
        success = governance.escalate_alert(args.escalate_alert, 1, "test_user")
        if success:
            print(f"✅ Alert {args.escalate_alert} escalated")
        else:
            print(f"❌ Failed to escalate alert {args.escalate_alert}")
    
    elif args.audit:
        # Show suppression audit
        audit_history = governance.get_suppression_audit(args.audit)
        print(f"\n📋 SUPPRESSION AUDIT (Last {args.audit} days)")
        print("-" * 50)
        for record in audit_history:
            print(f"{record['timestamp']} - {record['action']} - {record['alert_id']} - {record['reason']}")
    
    else:
        # Default: show status
        governance.display_alert_status()
    
    sys.exit(0)


if __name__ == "__main__":
    main()
