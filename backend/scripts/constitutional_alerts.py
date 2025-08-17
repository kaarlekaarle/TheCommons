#!/usr/bin/env python3
"""
Constitutional Alerting System

This script sends alerts when constitutional violations are detected in the Delegation Constitution.
It provides real-time notifications to stakeholders about constitutional health.
"""

import os
import sys
import json
import smtplib
import requests
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# Alert severity levels
SEVERITY_LEVELS = {
    "critical": "🚨 CRITICAL",
    "warning": "⚠️  WARNING", 
    "info": "ℹ️  INFO"
}

# Alert channels
ALERT_CHANNELS = {
    "email": "email",
    "slack": "slack",
    "webhook": "webhook",
    "console": "console"
}


class ConstitutionalAlert:
    """Represents a constitutional violation alert."""
    
    def __init__(self, severity: str, category: str, message: str, details: Dict[str, Any]):
        self.severity = severity
        self.category = category
        self.message = message
        self.details = details
        self.timestamp = datetime.now().isoformat()
        self.id = f"constitutional_alert_{self.timestamp}"
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert alert to dictionary."""
        return {
            "id": self.id,
            "severity": self.severity,
            "category": self.category,
            "message": self.message,
            "details": self.details,
            "timestamp": self.timestamp
        }
    
    def to_text(self) -> str:
        """Convert alert to text format."""
        severity_emoji = SEVERITY_LEVELS.get(self.severity, "❓")
        
        text = f"{severity_emoji} CONSTITUTIONAL VIOLATION ALERT\n"
        text += "=" * 50 + "\n\n"
        text += f"Category: {self.category}\n"
        text += f"Severity: {self.severity.upper()}\n"
        text += f"Timestamp: {self.timestamp}\n\n"
        text += f"Message: {self.message}\n\n"
        
        if self.details:
            text += "Details:\n"
            text += "-" * 20 + "\n"
            for key, value in self.details.items():
                text += f"{key}: {value}\n"
        
        return text
    
    def to_html(self) -> str:
        """Convert alert to HTML format."""
        severity_emoji = SEVERITY_LEVELS.get(self.severity, "❓")
        severity_color = {
            "critical": "#dc3545",
            "warning": "#ffc107", 
            "info": "#17a2b8"
        }.get(self.severity, "#6c757d")
        
        html = f"""
        <div style="border: 2px solid {severity_color}; padding: 20px; margin: 20px; border-radius: 8px;">
            <h2 style="color: {severity_color}; margin-top: 0;">
                {severity_emoji} CONSTITUTIONAL VIOLATION ALERT
            </h2>
            <hr style="border-color: {severity_color};">
            <p><strong>Category:</strong> {self.category}</p>
            <p><strong>Severity:</strong> {self.severity.upper()}</p>
            <p><strong>Timestamp:</strong> {self.timestamp}</p>
            <p><strong>Message:</strong> {self.message}</p>
        """
        
        if self.details:
            html += "<h3>Details:</h3><ul>"
            for key, value in self.details.items():
                html += f"<li><strong>{key}:</strong> {value}</li>"
            html += "</ul>"
        
        html += "</div>"
        return html


class ConstitutionalAlertManager:
    """Manages constitutional alerts and notifications."""
    
    def __init__(self, config_file: Optional[str] = None):
        self.config = self._load_config(config_file)
        self.alerts: List[ConstitutionalAlert] = []
    
    def _load_config(self, config_file: Optional[str]) -> Dict[str, Any]:
        """Load alert configuration."""
        default_config = {
            "channels": {
                "email": {
                    "enabled": False,
                    "smtp_server": "localhost",
                    "smtp_port": 587,
                    "username": "",
                    "password": "",
                    "from_email": "",
                    "to_emails": []
                },
                "slack": {
                    "enabled": False,
                    "webhook_url": "",
                    "channel": "#constitutional-alerts"
                },
                "webhook": {
                    "enabled": False,
                    "url": "",
                    "headers": {}
                },
                "console": {
                    "enabled": True
                }
            },
            "severity_threshold": "warning",  # Only alert on warning and above
            "cooldown_minutes": 30  # Minimum time between alerts for same issue
        }
        
        if config_file and Path(config_file).exists():
            try:
                with open(config_file, "r") as f:
                    user_config = json.load(f)
                default_config.update(user_config)
            except Exception as e:
                print(f"Warning: Could not load config file {config_file}: {e}")
        
        return default_config
    
    def create_alert(self, severity: str, category: str, message: str, details: Dict[str, Any]) -> ConstitutionalAlert:
        """Create a new constitutional alert."""
        alert = ConstitutionalAlert(severity, category, message, details)
        self.alerts.append(alert)
        return alert
    
    def should_send_alert(self, alert: ConstitutionalAlert) -> bool:
        """Determine if an alert should be sent based on severity threshold."""
        severity_levels = ["info", "warning", "critical"]
        threshold = self.config["severity_threshold"]
        
        alert_level = severity_levels.index(alert.severity)
        threshold_level = severity_levels.index(threshold)
        
        return alert_level >= threshold_level
    
    def send_alert(self, alert: ConstitutionalAlert) -> bool:
        """Send an alert through configured channels."""
        if not self.should_send_alert(alert):
            return True
        
        success = True
        
        # Send to console
        if self.config["channels"]["console"]["enabled"]:
            if not self._send_console_alert(alert):
                success = False
        
        # Send email
        if self.config["channels"]["email"]["enabled"]:
            if not self._send_email_alert(alert):
                success = False
        
        # Send Slack notification
        if self.config["channels"]["slack"]["enabled"]:
            if not self._send_slack_alert(alert):
                success = False
        
        # Send webhook
        if self.config["channels"]["webhook"]["enabled"]:
            if not self._send_webhook_alert(alert):
                success = False
        
        return success
    
    def _send_console_alert(self, alert: ConstitutionalAlert) -> bool:
        """Send alert to console."""
        try:
            print("\n" + "="*60)
            print(alert.to_text())
            print("="*60 + "\n")
            return True
        except Exception as e:
            print(f"Error sending console alert: {e}")
            return False
    
    def _send_email_alert(self, alert: ConstitutionalAlert) -> bool:
        """Send alert via email."""
        try:
            email_config = self.config["channels"]["email"]
            
            msg = MIMEMultipart("alternative")
            msg["Subject"] = f"Constitutional Violation Alert: {alert.category}"
            msg["From"] = email_config["from_email"]
            msg["To"] = ", ".join(email_config["to_emails"])
            
            # Add text and HTML versions
            text_part = MIMEText(alert.to_text(), "plain")
            html_part = MIMEText(alert.to_html(), "html")
            
            msg.attach(text_part)
            msg.attach(html_part)
            
            # Send email
            with smtplib.SMTP(email_config["smtp_server"], email_config["smtp_port"]) as server:
                server.starttls()
                server.login(email_config["username"], email_config["password"])
                server.send_message(msg)
            
            return True
        except Exception as e:
            print(f"Error sending email alert: {e}")
            return False
    
    def _send_slack_alert(self, alert: ConstitutionalAlert) -> bool:
        """Send alert to Slack."""
        try:
            slack_config = self.config["channels"]["slack"]
            
            payload = {
                "channel": slack_config["channel"],
                "text": f"🚨 Constitutional Violation Alert",
                "attachments": [
                    {
                        "color": "danger" if alert.severity == "critical" else "warning",
                        "title": f"Constitutional Violation: {alert.category}",
                        "text": alert.message,
                        "fields": [
                            {
                                "title": "Severity",
                                "value": alert.severity.upper(),
                                "short": True
                            },
                            {
                                "title": "Timestamp",
                                "value": alert.timestamp,
                                "short": True
                            }
                        ],
                        "footer": "Delegation Constitutional Enforcement"
                    }
                ]
            }
            
            response = requests.post(slack_config["webhook_url"], json=payload)
            response.raise_for_status()
            
            return True
        except Exception as e:
            print(f"Error sending Slack alert: {e}")
            return False
    
    def _send_webhook_alert(self, alert: ConstitutionalAlert) -> bool:
        """Send alert via webhook."""
        try:
            webhook_config = self.config["channels"]["webhook"]
            
            payload = {
                "alert": alert.to_dict(),
                "source": "constitutional_enforcement",
                "timestamp": datetime.now().isoformat()
            }
            
            response = requests.post(
                webhook_config["url"],
                json=payload,
                headers=webhook_config.get("headers", {})
            )
            response.raise_for_status()
            
            return True
        except Exception as e:
            print(f"Error sending webhook alert: {e}")
            return False
    
    def analyze_health_report(self, health_report: Dict[str, Any]) -> List[ConstitutionalAlert]:
        """Analyze health report and create alerts for violations."""
        alerts = []
        
        # Overall status alert
        if health_report["overall_status"] == "critical":
            alerts.append(self.create_alert(
                "critical",
                "Overall System",
                "Critical constitutional violations detected across multiple categories",
                {
                    "compliance_rate": f"{health_report['compliance_rate']:.1f}%",
                    "failing_tests": health_report["failing_tests"],
                    "total_tests": health_report["total_tests"]
                }
            ))
        elif health_report["overall_status"] == "warning":
            alerts.append(self.create_alert(
                "warning",
                "Overall System", 
                "Constitutional warnings detected - attention required",
                {
                    "compliance_rate": f"{health_report['compliance_rate']:.1f}%",
                    "failing_tests": health_report["failing_tests"],
                    "total_tests": health_report["total_tests"]
                }
            ))
        
        # Category-specific alerts
        for category_id, category_data in health_report["categories"].items():
            if category_data["status"] == "critical":
                alerts.append(self.create_alert(
                    "critical",
                    category_data["name"],
                    f"Critical violations in {category_data['name']} - immediate action required",
                    {
                        "compliance_rate": f"{category_data['compliance_rate']:.1f}%",
                        "failing_tests": category_data["failing_tests"],
                        "total_tests": category_data["total_tests"],
                        "description": category_data["description"]
                    }
                ))
            elif category_data["status"] == "warning":
                alerts.append(self.create_alert(
                    "warning",
                    category_data["name"],
                    f"Warnings detected in {category_data['name']} - review recommended",
                    {
                        "compliance_rate": f"{category_data['compliance_rate']:.1f}%",
                        "failing_tests": category_data["failing_tests"],
                        "total_tests": category_data["total_tests"],
                        "description": category_data["description"]
                    }
                ))
        
        return alerts


def main():
    """Main function to run constitutional alerting."""
    print("🔒 Constitutional Alerting System")
    print("=" * 40)
    
    # Load health report
    health_report_file = "constitutional_health.json"
    if not Path(health_report_file).exists():
        print(f"❌ Health report not found: {health_report_file}")
        print("Run constitutional_health.py first to generate health report.")
        sys.exit(1)
    
    try:
        with open(health_report_file, "r") as f:
            health_report = json.load(f)
    except Exception as e:
        print(f"❌ Error loading health report: {e}")
        sys.exit(1)
    
    # Initialize alert manager
    alert_manager = ConstitutionalAlertManager()
    
    # Analyze health report and create alerts
    print("📊 Analyzing constitutional health for violations...")
    alerts = alert_manager.analyze_health_report(health_report)
    
    if not alerts:
        print("✅ No constitutional violations detected - no alerts needed.")
        sys.exit(0)
    
    # Send alerts
    print(f"🚨 Sending {len(alerts)} constitutional violation alerts...")
    
    success_count = 0
    for alert in alerts:
        if alert_manager.send_alert(alert):
            success_count += 1
            print(f"✅ Alert sent: {alert.category} ({alert.severity})")
        else:
            print(f"❌ Failed to send alert: {alert.category} ({alert.severity})")
    
    print(f"\n📊 Alert Summary: {success_count}/{len(alerts)} alerts sent successfully")
    
    if success_count < len(alerts):
        print("⚠️  Some alerts failed to send - check configuration")
        sys.exit(1)
    else:
        print("✅ All constitutional violation alerts sent successfully")
        sys.exit(0)


if __name__ == "__main__":
    main()
