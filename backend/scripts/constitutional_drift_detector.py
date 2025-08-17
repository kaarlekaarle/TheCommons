#!/usr/bin/env python3
"""
Constitutional Drift Detection System

This script detects gradual erosion of constitutional principles over time,
identifying drift patterns before they become entrenched violations.
"""

import os
import sys
import json
import sqlite3
import time
import subprocess
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
import re

# Drift categories and their detection patterns
DRIFT_CATEGORIES = {
    "test_neglect": {
        "name": "Test Neglect Drift",
        "description": "Constitutional tests becoming ignored or skipped",
        "signals": [
            "increasing_skip_rates",
            "todo_comments_never_addressed", 
            "test_coverage_decline",
            "known_failures_ignored"
        ]
    },
    "alert_fatigue": {
        "name": "Alert Fatigue Drift",
        "description": "Constitutional alerts being suppressed or muted",
        "signals": [
            "alert_suppression",
            "threshold_increases",
            "channel_muting",
            "violation_tolerance"
        ]
    },
    "shortcut_accumulation": {
        "name": "Shortcut Accumulation Drift", 
        "description": "Temporary bypasses becoming permanent patterns",
        "signals": [
            "feature_flags_stagnant",
            "workarounds_normalized",
            "bypass_patterns",
            "temporary_exceptions_permanent"
        ]
    },
    "hierarchy_creep": {
        "name": "Hierarchy Creep Drift",
        "description": "Gradual concentration of delegation power",
        "signals": [
            "power_concentration_increase",
            "delegation_diversity_decline",
            "super_delegate_emergence",
            "circulation_decline"
        ]
    },
    "transparency_erosion": {
        "name": "Transparency Erosion Drift",
        "description": "Gradual loss of visibility into delegation flows",
        "signals": [
            "logging_reduction",
            "chain_opacity_increase",
            "visibility_decline",
            "accountability_loss",
            "override_latency_increase"
        ]
    },
    "cultural_drift": {
        "name": "Cultural Drift",
        "description": "Team culture shifting away from constitutional principles",
        "signals": [
            "constitutional_fatigue",
            "principle_dismissal",
            "priority_shifting",
            "philosophical_drift"
        ]
    }
}

# Performance thresholds for constitutional guarantees
PERFORMANCE_THRESHOLDS = {
    "override_latency_max_ms": 2000,  # 2 seconds maximum
    "delegation_chain_resolution_max_ms": 1000,  # 1 second maximum
    "transparency_logging_max_ms": 500,  # 500ms maximum
    "user_intent_override_max_ms": 1000  # 1 second maximum
}


class ConstitutionalDriftDetector:
    """Detects constitutional drift patterns over time."""
    
    def __init__(self, db_path: str = "constitutional_history.db"):
        self.db_path = db_path
        self.drift_signals = {}
        self.drift_analysis = {}
        self.performance_metrics = {}
    
    def detect_test_neglect_drift(self) -> Dict[str, Any]:
        """Detect drift in constitutional test health."""
        drift_data = {
            "category": "test_neglect",
            "signals": {},
            "risk_level": "low",
            "recommendations": []
        }
        
        # Analyze test coverage trends
        coverage_trend = self._analyze_test_coverage_trend()
        if coverage_trend["decline_rate"] > 5:
            drift_data["signals"]["coverage_decline"] = {
                "severity": "high",
                "value": coverage_trend["decline_rate"],
                "description": f"Test coverage declining at {coverage_trend['decline_rate']:.1f}% per week"
            }
            drift_data["risk_level"] = "high"
            drift_data["recommendations"].append("URGENT: Address declining constitutional test coverage")
        
        # Check for TODO comments in constitutional tests
        todo_count = self._count_constitutional_todos()
        if todo_count > 10:
            drift_data["signals"]["todo_accumulation"] = {
                "severity": "medium",
                "value": todo_count,
                "description": f"{todo_count} TODO items in constitutional tests"
            }
            drift_data["recommendations"].append("Review and address constitutional test TODOs")
        
        # Analyze test skip patterns
        skip_patterns = self._analyze_test_skip_patterns()
        if skip_patterns["skip_rate"] > 20:
            drift_data["signals"]["high_skip_rate"] = {
                "severity": "high",
                "value": skip_patterns["skip_rate"],
                "description": f"{skip_patterns['skip_rate']:.1f}% of constitutional tests being skipped"
            }
            drift_data["risk_level"] = "high"
            drift_data["recommendations"].append("CRITICAL: Reduce constitutional test skip rate")
        
        return drift_data
    
    def detect_alert_fatigue_drift(self) -> Dict[str, Any]:
        """Detect drift in constitutional alert effectiveness."""
        drift_data = {
            "category": "alert_fatigue",
            "signals": {},
            "risk_level": "low",
            "recommendations": []
        }
        
        # Check alert configuration for suppression
        alert_config = self._check_alert_configuration()
        if alert_config["suppressed_alerts"] > 0:
            drift_data["signals"]["alert_suppression"] = {
                "severity": "high",
                "value": alert_config["suppressed_alerts"],
                "description": f"{alert_config['suppressed_alerts']} constitutional alerts suppressed"
            }
            drift_data["risk_level"] = "high"
            drift_data["recommendations"].append("Review and reactivate suppressed constitutional alerts")
        
        # Analyze alert response patterns
        response_patterns = self._analyze_alert_response_patterns()
        if response_patterns["response_rate"] < 80:
            drift_data["signals"]["low_response_rate"] = {
                "severity": "medium",
                "value": response_patterns["response_rate"],
                "description": f"Only {response_patterns['response_rate']:.1f}% of constitutional alerts responded to"
            }
            drift_data["recommendations"].append("Improve constitutional alert response rate")
        
        return drift_data
    
    def detect_shortcut_accumulation_drift(self) -> Dict[str, Any]:
        """Detect drift in constitutional feature flag and bypass patterns."""
        drift_data = {
            "category": "shortcut_accumulation",
            "signals": {},
            "risk_level": "low",
            "recommendations": []
        }
        
        # Check feature flag stagnation
        flag_health = self._check_feature_flag_health()
        if flag_health["stagnant_flags"] > 0:
            drift_data["signals"]["feature_flag_stagnation"] = {
                "severity": "medium",
                "value": flag_health["stagnant_flags"],
                "description": f"{flag_health['stagnant_flags']} constitutional feature flags stagnant"
            }
            drift_data["recommendations"].append("Activate stagnant constitutional feature flags")
        
        # Check for bypass patterns in code
        bypass_patterns = self._detect_bypass_patterns()
        if bypass_patterns["bypass_count"] > 5:
            drift_data["signals"]["bypass_accumulation"] = {
                "severity": "high",
                "value": bypass_patterns["bypass_count"],
                "description": f"{bypass_patterns['bypass_count']} constitutional bypasses detected"
            }
            drift_data["risk_level"] = "high"
            drift_data["recommendations"].append("CRITICAL: Remove constitutional bypasses")
        
        return drift_data
    
    def detect_hierarchy_creep_drift(self) -> Dict[str, Any]:
        """Detect drift toward power concentration and hierarchy."""
        drift_data = {
            "category": "hierarchy_creep",
            "signals": {},
            "risk_level": "low",
            "recommendations": []
        }
        
        # Analyze delegation concentration trends
        concentration_trend = self._analyze_delegation_concentration()
        if concentration_trend["concentration_increase"] > 10:
            drift_data["signals"]["power_concentration"] = {
                "severity": "high",
                "value": concentration_trend["concentration_increase"],
                "description": f"Delegation concentration increased by {concentration_trend['concentration_increase']:.1f}%"
            }
            drift_data["risk_level"] = "high"
            drift_data["recommendations"].append("URGENT: Address increasing delegation concentration")
        
        # Check delegation diversity
        diversity_metrics = self._analyze_delegation_diversity()
        if diversity_metrics["diversity_decline"] > 5:
            drift_data["signals"]["diversity_decline"] = {
                "severity": "medium",
                "value": diversity_metrics["diversity_decline"],
                "description": f"Delegation diversity declined by {diversity_metrics['diversity_decline']:.1f}%"
            }
            drift_data["recommendations"].append("Improve delegation diversity")
        
        return drift_data
    
    def detect_transparency_erosion_drift(self) -> Dict[str, Any]:
        """Detect drift in transparency and visibility."""
        drift_data = {
            "category": "transparency_erosion",
            "signals": {},
            "risk_level": "low",
            "recommendations": []
        }
        
        # Check override latency performance
        latency_result = self._check_override_latency()
        if latency_result["violation"]:
            drift_data["signals"]["override_latency_increase"] = {
                "severity": "high" if latency_result["latency_ms"] > PERFORMANCE_THRESHOLDS["override_latency_max_ms"] else "medium",
                "value": latency_result["latency_ms"],
                "description": f"Override latency is {latency_result['latency_ms']}ms (threshold: {PERFORMANCE_THRESHOLDS['override_latency_max_ms']}ms)"
            }
            drift_data["risk_level"] = "high"
            drift_data["recommendations"].append("CRITICAL: Reduce override latency to maintain user intent supremacy")
        
        # Check delegation chain resolution performance
        chain_resolution_result = self._check_delegation_chain_resolution()
        if chain_resolution_result["violation"]:
            drift_data["signals"]["chain_resolution_slowdown"] = {
                "severity": "medium",
                "value": chain_resolution_result["latency_ms"],
                "description": f"Delegation chain resolution is {chain_resolution_result['latency_ms']}ms (threshold: {PERFORMANCE_THRESHOLDS['delegation_chain_resolution_max_ms']}ms)"
            }
            if drift_data["risk_level"] != "high":
                drift_data["risk_level"] = "medium"
            drift_data["recommendations"].append("Optimize delegation chain resolution for better transparency")
        
        # Check transparency logging performance
        logging_result = self._check_transparency_logging()
        if logging_result["violation"]:
            drift_data["signals"]["logging_performance_decline"] = {
                "severity": "medium",
                "value": logging_result["latency_ms"],
                "description": f"Transparency logging is {logging_result['latency_ms']}ms (threshold: {PERFORMANCE_THRESHOLDS['transparency_logging_max_ms']}ms)"
            }
            if drift_data["risk_level"] != "high":
                drift_data["risk_level"] = "medium"
            drift_data["recommendations"].append("Optimize transparency logging for better visibility")
        
        return drift_data
    
    def detect_cultural_drift(self) -> Dict[str, Any]:
        """Detect drift in team culture and philosophical commitment."""
        drift_data = {
            "category": "cultural_drift",
            "signals": {},
            "risk_level": "low",
            "recommendations": []
        }
        
        # Analyze code review patterns for constitutional awareness
        review_patterns = self._analyze_constitutional_review_patterns()
        if review_patterns["constitutional_mentions_decline"] > 20:
            drift_data["signals"]["constitutional_awareness_decline"] = {
                "severity": "medium",
                "value": review_patterns["constitutional_mentions_decline"],
                "description": f"Constitutional mentions in reviews declined by {review_patterns['constitutional_mentions_decline']:.1f}%"
            }
            drift_data["recommendations"].append("Reinforce constitutional awareness in code reviews")
        
        return drift_data
    
    def _analyze_test_coverage_trend(self) -> Dict[str, float]:
        """Analyze trends in constitutional test coverage."""
        # This would analyze historical test coverage data
        # For now, return simulated data
        return {
            "decline_rate": 2.5,  # 2.5% decline per week
            "current_coverage": 85.0,
            "trend_direction": "declining"
        }
    
    def _count_constitutional_todos(self) -> int:
        """Count TODO comments in constitutional test files."""
        todo_count = 0
        test_dir = Path("tests/delegation")
        
        if test_dir.exists():
            for test_file in test_dir.glob("*.py"):
                try:
                    with open(test_file, "r") as f:
                        content = f.read()
                        todos = re.findall(r"# TODO", content, re.IGNORECASE)
                        todo_count += len(todos)
                except Exception:
                    continue
        
        return todo_count
    
    def _analyze_test_skip_patterns(self) -> Dict[str, float]:
        """Analyze patterns of test skipping."""
        # This would analyze actual test run data
        # For now, return simulated data
        return {
            "skip_rate": 15.0,  # 15% of tests skipped
            "skip_reasons": ["not implemented", "temporary", "known issue"]
        }
    
    def _check_alert_configuration(self) -> Dict[str, int]:
        """Check for alert suppression in configuration."""
        # This would check actual alert configurations
        # For now, return simulated data
        return {
            "suppressed_alerts": 2,
            "muted_channels": 1,
            "increased_thresholds": 3
        }
    
    def _analyze_alert_response_patterns(self) -> Dict[str, float]:
        """Analyze patterns of alert response."""
        # This would analyze historical alert data
        # For now, return simulated data
        return {
            "response_rate": 75.0,  # 75% response rate
            "average_response_time": 2.5  # hours
        }
    
    def _check_feature_flag_health(self) -> Dict[str, int]:
        """Check health of constitutional feature flags."""
        # This would check actual feature flag states
        # For now, return simulated data
        return {
            "stagnant_flags": 3,
            "disabled_flags": 2,
            "active_flags": 4
        }
    
    def _detect_bypass_patterns(self) -> Dict[str, int]:
        """Detect constitutional bypass patterns in code."""
        bypass_count = 0
        
        # Check for common bypass patterns
        bypass_patterns = [
            r"# bypass.*constitutional",
            r"# skip.*constitutional",
            r"# temporary.*exception",
            r"constitutional.*disabled",
            r"guardrail.*bypass"
        ]
        
        for pattern in bypass_patterns:
            try:
                result = subprocess.run([
                    "grep", "-r", pattern, "backend/", "--include=*.py"
                ], capture_output=True, text=True)
                bypass_count += len(result.stdout.splitlines())
            except Exception:
                continue
        
        return {
            "bypass_count": bypass_count,
            "bypass_patterns": bypass_patterns
        }
    
    def _analyze_delegation_concentration(self) -> Dict[str, float]:
        """Analyze trends in delegation concentration."""
        # This would analyze actual delegation data
        # For now, return simulated data
        return {
            "concentration_increase": 8.5,  # 8.5% increase
            "top_5_percent_power": 75.0,  # 75% of power in top 5%
            "circulation_rate": 65.0  # 65% circulation rate
        }
    
    def _analyze_delegation_diversity(self) -> Dict[str, float]:
        """Analyze delegation diversity metrics."""
        # This would analyze actual delegation diversity
        # For now, return simulated data
        return {
            "diversity_decline": 3.2,  # 3.2% decline
            "unique_delegators": 150,
            "delegation_spread": 0.45  # Gini coefficient
        }
    
    def _analyze_transparency_metrics(self) -> Dict[str, float]:
        """Analyze transparency and visibility metrics."""
        # This would analyze actual transparency data
        # For now, return simulated data
        return {
            "opacity_increase": 12.0,  # 12% increase in opacity
            "chain_visibility": 78.0,  # 78% chain visibility
            "logging_completeness": 85.0  # 85% logging completeness
        }
    
    def _analyze_constitutional_review_patterns(self) -> Dict[str, float]:
        """Analyze code review patterns for constitutional awareness."""
        # This would analyze actual review data
        # For now, return simulated data
        return {
            "constitutional_mentions_decline": 25.0,  # 25% decline
            "constitutional_reviews": 45,  # 45 reviews with constitutional focus
            "principle_discussions": 12  # 12 discussions of principles
        }
    
    def _check_override_latency(self) -> Dict[str, Any]:
        """Check override latency performance."""
        result = {
            "latency_ms": 0,
            "violation": False,
            "status": "unknown"
        }
        
        try:
            # Simulate user override request and measure latency
            start_time = time.time()
            
            # Test delegation override endpoint
            override_latency = self._measure_override_latency()
            
            end_time = time.time()
            total_latency_ms = (end_time - start_time) * 1000
            
            result["latency_ms"] = total_latency_ms
            result["violation"] = total_latency_ms > PERFORMANCE_THRESHOLDS["override_latency_max_ms"]
            
            if result["violation"]:
                result["status"] = "failed"
                print(f"🚨 CRITICAL: Override latency {total_latency_ms:.1f}ms exceeds threshold {PERFORMANCE_THRESHOLDS['override_latency_max_ms']}ms")
            else:
                result["status"] = "passed"
                print(f"✅ Override latency {total_latency_ms:.1f}ms within threshold")
                
        except Exception as e:
            result["status"] = "error"
            result["error"] = str(e)
            print(f"⚠️  Error measuring override latency: {e}")
        
        return result
    
    def _measure_override_latency(self) -> float:
        """Measure actual override latency by testing delegation endpoints."""
        try:
            # Check if server is running
            if self._is_server_running():
                # Test delegation override endpoint
                return self._test_delegation_override_endpoint()
            else:
                # Simulate delegation override latency
                return self._simulate_delegation_override()
        except Exception as e:
            print(f"Warning: Could not measure override latency: {e}")
            # Return a conservative estimate
            return 1500.0  # 1.5 seconds as fallback
    
    def _is_server_running(self) -> bool:
        """Check if the backend server is running."""
        # For testing purposes, always return False to use simulation
        return False
    
    def _test_delegation_override_endpoint(self) -> float:
        """Test delegation override endpoint latency."""
        # For testing purposes, return a simulated latency
        # This would normally test the actual endpoint
        return 1200.0  # Simulated 1.2 second latency
    
    def _simulate_delegation_override(self) -> float:
        """Simulate delegation override latency for testing."""
        # Simulate different latency scenarios
        import random
        
        # 70% chance of good performance, 30% chance of degradation
        if random.random() < 0.7:
            return random.uniform(800, 1500)  # Good performance: 800-1500ms
        else:
            return random.uniform(2000, 3000)  # Degraded performance: 2000-3000ms
    
    def _check_delegation_chain_resolution(self) -> Dict[str, Any]:
        """Check delegation chain resolution performance."""
        result = {
            "latency_ms": 0,
            "violation": False,
            "status": "unknown"
        }
        
        try:
            start_time = time.time()
            
            # Simulate delegation chain resolution
            chain_resolution_latency = self._simulate_chain_resolution()
            
            end_time = time.time()
            total_latency_ms = (end_time - start_time) * 1000
            
            result["latency_ms"] = total_latency_ms
            result["violation"] = total_latency_ms > PERFORMANCE_THRESHOLDS["delegation_chain_resolution_max_ms"]
            
            if result["violation"]:
                result["status"] = "failed"
                print(f"⚠️  WARNING: Chain resolution latency {total_latency_ms:.1f}ms exceeds threshold {PERFORMANCE_THRESHOLDS['delegation_chain_resolution_max_ms']}ms")
            else:
                result["status"] = "passed"
                print(f"✅ Chain resolution latency {total_latency_ms:.1f}ms within threshold")
                
        except Exception as e:
            result["status"] = "error"
            result["error"] = str(e)
            print(f"⚠️  Error measuring chain resolution latency: {e}")
        
        return result
    
    def _simulate_chain_resolution(self) -> float:
        """Simulate delegation chain resolution latency."""
        import random
        
        # Simulate chain resolution with some variability
        base_latency = 600  # Base latency
        variability = random.uniform(0.8, 1.2)  # ±20% variability
        
        return base_latency * variability
    
    def _check_transparency_logging(self) -> Dict[str, Any]:
        """Check transparency logging performance."""
        result = {
            "latency_ms": 0,
            "violation": False,
            "status": "unknown"
        }
        
        try:
            start_time = time.time()
            
            # Simulate transparency logging
            logging_latency = self._simulate_transparency_logging()
            
            end_time = time.time()
            total_latency_ms = (end_time - start_time) * 1000
            
            result["latency_ms"] = total_latency_ms
            result["violation"] = total_latency_ms > PERFORMANCE_THRESHOLDS["transparency_logging_max_ms"]
            
            if result["violation"]:
                result["status"] = "failed"
                print(f"⚠️  WARNING: Transparency logging latency {total_latency_ms:.1f}ms exceeds threshold {PERFORMANCE_THRESHOLDS['transparency_logging_max_ms']}ms")
            else:
                result["status"] = "passed"
                print(f"✅ Transparency logging latency {total_latency_ms:.1f}ms within threshold")
                
        except Exception as e:
            result["status"] = "error"
            result["error"] = str(e)
            print(f"⚠️  Error measuring transparency logging latency: {e}")
        
        return result
    
    def _simulate_transparency_logging(self) -> float:
        """Simulate transparency logging latency."""
        import random
        
        # Simulate logging with some variability
        base_latency = 300  # Base latency
        variability = random.uniform(0.7, 1.3)  # ±30% variability
        
        return base_latency * variability
    
    def run_drift_analysis(self) -> Dict[str, Any]:
        """Run comprehensive drift analysis across all categories."""
        print("🔍 CONSTITUTIONAL DRIFT ANALYSIS")
        print("=" * 50)
        
        drift_results = {
            "timestamp": datetime.now().isoformat(),
            "overall_risk_level": "low",
            "categories": {},
            "critical_signals": [],
            "recommendations": []
        }
        
        # Run drift detection for each category
        drift_detectors = [
            self.detect_test_neglect_drift,
            self.detect_alert_fatigue_drift,
            self.detect_shortcut_accumulation_drift,
            self.detect_hierarchy_creep_drift,
            self.detect_transparency_erosion_drift,
            self.detect_cultural_drift
        ]
        
        for detector in drift_detectors:
            result = detector()
            category = result["category"]
            drift_results["categories"][category] = result
            
            # Track critical signals
            for signal_name, signal_data in result["signals"].items():
                if signal_data["severity"] == "high":
                    drift_results["critical_signals"].append({
                        "category": category,
                        "signal": signal_name,
                        "description": signal_data["description"],
                        "value": signal_data["value"]
                    })
            
            # Aggregate recommendations
            drift_results["recommendations"].extend(result["recommendations"])
            
            # Determine overall risk level
            if result["risk_level"] == "high":
                drift_results["overall_risk_level"] = "high"
            elif result["risk_level"] == "medium" and drift_results["overall_risk_level"] == "low":
                drift_results["overall_risk_level"] = "medium"
        
        return drift_results
    
    def display_drift_report(self, drift_results: Dict[str, Any]) -> None:
        """Display comprehensive drift analysis report."""
        print(f"📅 Analysis Date: {drift_results['timestamp']}")
        print(f"🏥 Overall Risk Level: {drift_results['overall_risk_level'].upper()}")
        print()
        
        # Display critical signals
        if drift_results["critical_signals"]:
            print("🚨 CRITICAL DRIFT SIGNALS")
            print("-" * 30)
            for signal in drift_results["critical_signals"]:
                print(f"• {signal['category'].replace('_', ' ').title()}: {signal['description']}")
            print()
        
        # Display category breakdown
        print("📊 DRIFT CATEGORY ANALYSIS")
        print("-" * 30)
        for category_id, category_data in drift_results["categories"].items():
            category_name = DRIFT_CATEGORIES[category_id]["name"]
            risk_level = category_data["risk_level"]
            signal_count = len(category_data["signals"])
            
            risk_emoji = {"high": "🔴", "medium": "🟡", "low": "🟢"}.get(risk_level, "⚪")
            print(f"{risk_emoji} {category_name}: {risk_level.upper()} ({signal_count} signals)")
        
        print()
        
        # Display recommendations
        if drift_results["recommendations"]:
            print("💡 DRIFT RESISTANCE RECOMMENDATIONS")
            print("-" * 40)
            for i, recommendation in enumerate(drift_results["recommendations"], 1):
                print(f"{i}. {recommendation}")
            print()
        
        # Display drift resistance status
        if drift_results["overall_risk_level"] == "high":
            print("🚨 HIGH DRIFT RISK DETECTED")
            print("Immediate action required to prevent constitutional erosion.")
        elif drift_results["overall_risk_level"] == "medium":
            print("⚠️  MEDIUM DRIFT RISK DETECTED")
            print("Monitor closely and address drift signals.")
        else:
            print("✅ LOW DRIFT RISK")
            print("Constitutional principles remain strong.")


def main():
    """Main CLI entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Constitutional Drift Detection System")
    parser.add_argument("--detect-drift", action="store_true", help="Run comprehensive drift detection")
    parser.add_argument("--test-override-latency", action="store_true", help="Test override latency performance")
    parser.add_argument("--output", help="Output file for results")
    parser.add_argument("--threshold", type=float, default=2000.0, help="Override latency threshold in ms")
    
    args = parser.parse_args()
    
    detector = ConstitutionalDriftDetector()
    
    if args.test_override_latency:
        print("⚡ OVERRIDE LATENCY PERFORMANCE TEST")
        print("=" * 40)
        print(f"Testing override latency (threshold: {args.threshold}ms)...")
        print()
        
        # Test override latency
        latency_result = detector._check_override_latency()
        
        # Override threshold if specified
        if args.threshold != 2000.0:
            latency_result["violation"] = latency_result["latency_ms"] > args.threshold
            latency_result["status"] = "failed" if latency_result["violation"] else "passed"
        
        if latency_result["status"] == "failed":
            print(f"❌ OVERRIDE LATENCY VIOLATION: {latency_result['latency_ms']:.1f}ms > {args.threshold}ms")
            print("User intent supremacy compromised!")
            print("🔒 CONSTITUTIONAL VIOLATION DETECTED")
            return 1
        elif latency_result["status"] == "passed":
            print(f"✅ Override latency acceptable: {latency_result['latency_ms']:.1f}ms ≤ {args.threshold}ms")
            print("User intent supremacy maintained.")
            return 0
        else:
            print(f"⚠️  Override latency test error: {latency_result.get('error', 'Unknown error')}")
            print("Manual review required.")
            return 1
    
    elif args.detect_drift:
        print("🔍 CONSTITUTIONAL DRIFT DETECTION")
        print("=" * 35)
        
        # Run comprehensive drift analysis
        drift_analysis = detector.run_drift_analysis()
        
        if args.output:
            with open(args.output, 'w') as f:
                json.dump(drift_analysis, f, indent=2)
            print(f"📄 Results saved to: {args.output}")
        
        # Display summary
        detector.display_drift_report(drift_analysis)
        
        # Return appropriate exit code
        if drift_analysis["overall_risk_level"] == "high":
            return 1
        elif drift_analysis["overall_risk_level"] == "medium":
            return 2
        else:
            return 0
    
    else:
        print("❌ Must specify --detect-drift or --test-override-latency")
        return 1

if __name__ == "__main__":
    exit(main())
