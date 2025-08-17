#!/usr/bin/env python3
"""
Constitutional Cascade Detector.

This script implements cascade rules that escalate certain pairs/clusters of constitutional warnings
into hard blockers when they indicate constitutional drift toward hierarchy or opacity.
"""

import argparse
import json
import os
import subprocess
import sys
from datetime import datetime
from typing import Any, Dict, List, Optional

# Exit codes
EXIT_OK = 0
EXIT_WARN = 8
EXIT_BLOCK = 10


class ConstitutionalCascadeDetector:
    """Detector for constitutional cascade rules."""

    def __init__(self, config_path: str = "backend/config/constitutional_cascade_rules.json"):
        """Initialize the cascade detector."""
        self.config_path = config_path
        self.config = self._load_config()
        self.signals: List[Dict[str, Any]] = []
        self.cascade_results: List[Dict[str, Any]] = []
        self.current_branch = self._detect_current_branch()
    
    def _detect_current_branch(self) -> str:
        """Detect current branch from environment variables."""
        # Try GITHUB_REF_NAME first (GitHub Actions)
        branch = os.environ.get("GITHUB_REF_NAME")
        if branch:
            return branch
        
        # Fallback to GITHUB_REF (remove refs/heads/ prefix)
        ref = os.environ.get("GITHUB_REF")
        if ref and ref.startswith("refs/heads/"):
            return ref[11:]  # Remove "refs/heads/" prefix
        
        # Fallback to git command
        try:
            result = subprocess.run(
                ["git", "rev-parse", "--abbrev-ref", "HEAD"],
                capture_output=True,
                text=True,
                check=False
            )
            if result.returncode == 0:
                return result.stdout.strip()
        except Exception:
            pass
        
        # Final fallback
        return "unknown"
    
    def _is_branch_enforced(self, rule_id: str, branch: str) -> bool:
        """Check if a rule should be enforced on the current branch."""
        branch_overrides = self.config.get("branch_overrides", {})
        
        if rule_id not in branch_overrides:
            return False
        
        enforce_patterns = branch_overrides[rule_id].get("enforce_on", [])
        
        for pattern in enforce_patterns:
            if self._matches_branch_pattern(branch, pattern):
                return True
        
        return False
    
    def _matches_branch_pattern(self, branch: str, pattern: str) -> bool:
        """Check if branch matches a pattern (supports wildcards)."""
        if pattern == branch:
            return True
        
        # Handle wildcard patterns like "release/*"
        if "*" in pattern:
            # Convert pattern to regex
            regex_pattern = pattern.replace("*", ".*")
            import re
            return bool(re.match(regex_pattern, branch))
        
        return False

    def _load_config(self) -> Dict[str, Any]:
        """Load cascade rules configuration."""
        try:
            with open(self.config_path, "r") as f:
                return json.load(f)
        except Exception as e:
            print(f"Error loading config {self.config_path}: {e}")
            sys.exit(1)

    def collect_signal_1_super_delegate(self) -> Optional[Dict[str, Any]]:
        """Collect signal #1: Super-delegate pattern (always critical)."""
        print("🔍 Collecting signal #1: Super-delegate pattern...")

        try:
            # Call constitutional_principle_matrix.py
            subprocess.run(
                [
                    "python3",
                    "backend/scripts/constitutional_principle_matrix.py",
                    "--detect-super-delegates",
                    "--json-out",
                    "reports/signal_super_delegate.json",
                ],
                capture_output=True,
                text=True,
                check=False,
            )

            # Read the JSON output
            if os.path.exists("reports/signal_super_delegate.json"):
                with open("reports/signal_super_delegate.json", "r") as f:
                    data = json.load(f)

                if data.get("super_delegate_detected", False):
                    return {
                        "id": "#1",
                        "severity": "critical",
                        "ts": datetime.now().isoformat(),
                        "meta": {
                            "files": data.get("files", []),
                            "patterns": data.get("patterns", []),
                        },
                    }

            return None

        except Exception as e:
            print(f"Warning: Could not collect super-delegate signal: {e}")
            return None

    def collect_signal_2_override_latency(self) -> Optional[Dict[str, Any]]:
        """Collect signal #2: Override latency."""
        print("🔍 Collecting signal #2: Override latency...")

        try:
            # Call constitutional_drift_detector.py
            subprocess.run(
                [
                    "python3",
                    "backend/scripts/constitutional_drift_detector.py",
                    "--test-override-latency",
                    "--json-out",
                    "reports/signal_override_latency.json",
                ],
                capture_output=True,
                text=True,
                check=False,
            )

            # Read the JSON output
            if os.path.exists("reports/signal_override_latency.json"):
                with open("reports/signal_override_latency.json", "r") as f:
                    data = json.load(f)

                latency_ms = data.get("override_latency_ms", 0)

                # Determine severity based on thresholds
                thresholds = self.config["thresholds"]["override_latency_ms"]
                if latency_ms >= thresholds["critical"]:
                    severity = "critical"
                elif latency_ms >= thresholds["high"]:
                    severity = "high"
                elif latency_ms >= thresholds["warn"]:
                    severity = "warn"
                else:
                    severity = "info"

                return {
                    "id": "#2",
                    "severity": severity,
                    "value_ms": latency_ms,
                    "ts": datetime.now().isoformat(),
                }

            return None

        except Exception as e:
            print(f"Warning: Could not collect override latency signal: {e}")
            return None

    def collect_signal_3_complexity(self) -> Optional[Dict[str, Any]]:
        """Collect signal #3: Delegation API complexity."""
        print("🔍 Collecting signal #3: Delegation API complexity...")

        try:
            # Call constitutional_dependency_validator.py
            subprocess.run(
                [
                    "python3",
                    "backend/scripts/constitutional_dependency_validator.py",
                    "--emit-complexity-json",
                    "--json-out",
                    "reports/signal_complexity.json",
                ],
                capture_output=True,
                text=True,
                check=False,
            )

            # Read the JSON output
            if os.path.exists("reports/signal_complexity.json"):
                with open("reports/signal_complexity.json", "r") as f:
                    data = json.load(f)

                flows_per_module = data.get("flows_per_module", 0)

                # Determine severity based on thresholds
                thresholds = self.config["thresholds"]["complexity_flows_per_module"]
                if flows_per_module >= thresholds["critical"]:
                    severity = "critical"
                elif flows_per_module >= thresholds["high"]:
                    severity = "high"
                elif flows_per_module >= thresholds["warn"]:
                    severity = "warn"
                else:
                    severity = "info"

                return {
                    "id": "#3",
                    "severity": severity,
                    "flows": flows_per_module,
                    "module": data.get("module", "unknown"),
                    "ts": datetime.now().isoformat(),
                }

            return None

        except Exception as e:
            print(f"Warning: Could not collect complexity signal: {e}")
            return None

    def collect_signal_4_maintainer_concentration(self) -> Optional[Dict[str, Any]]:
        """Collect signal #4: Maintainer concentration."""
        print("🔍 Collecting signal #4: Maintainer concentration...")

        try:
            # Call constitutional_dependency_validator.py
            subprocess.run(
                [
                    "python3",
                    "backend/scripts/constitutional_dependency_validator.py",
                    "--emit-maintainer-json",
                    "--json-out",
                    "reports/signal_maintainer.json",
                ],
                capture_output=True,
                text=True,
                check=False,
            )

            # Read the JSON output
            if os.path.exists("reports/signal_maintainer.json"):
                with open("reports/signal_maintainer.json", "r") as f:
                    data = json.load(f)

                concentration_pct = data.get("concentration_pct", 0)

                # Determine severity based on thresholds
                thresholds = self.config["thresholds"]["maintainer_concentration_pct"]
                if concentration_pct >= thresholds["critical"]:
                    severity = "critical"
                elif concentration_pct >= thresholds["high"]:
                    severity = "high"
                elif concentration_pct >= thresholds["warn"]:
                    severity = "warn"
                else:
                    severity = "info"

                return {
                    "id": "#4",
                    "severity": severity,
                    "pct": concentration_pct,
                    "top_maintainer": data.get("top_maintainer", "unknown"),
                    "ts": datetime.now().isoformat(),
                }

            return None

        except Exception as e:
            print(f"Warning: Could not collect maintainer concentration signal: {e}")
            return None

    def collect_all_signals(self) -> List[Dict[str, Any]]:
        """Collect all four signals."""
        print("📊 COLLECTING CONSTITUTIONAL SIGNALS")
        print("=" * 40)

        signals = []

        # Collect each signal
        signal_1 = self.collect_signal_1_super_delegate()
        if signal_1:
            signals.append(signal_1)

        signal_2 = self.collect_signal_2_override_latency()
        if signal_2:
            signals.append(signal_2)

        signal_3 = self.collect_signal_3_complexity()
        if signal_3:
            signals.append(signal_3)

        signal_4 = self.collect_signal_4_maintainer_concentration()
        if signal_4:
            signals.append(signal_4)

        self.signals = signals
        return signals

    def _get_effective_mode(self, rule_id: str) -> str:
        """Get effective mode for a specific rule, considering mode and branch overrides."""
        global_mode = self.config.get("mode", "warn")
        mode_overrides = self.config.get("mode_overrides", {})
        
        # Check if there's a specific mode override for this rule
        if rule_id in mode_overrides:
            base_mode = mode_overrides[rule_id]
        else:
            base_mode = global_mode
        
        # Check if this rule should be enforced on the current branch
        if self._is_branch_enforced(rule_id, self.current_branch):
            return "enforce"
        
        # Return the base mode (from mode_overrides or global)
        return base_mode

    def evaluate_cascade_rules(self) -> List[Dict[str, Any]]:
        """Evaluate cascade rules against collected signals."""
        print("\n🔍 EVALUATING CASCADE RULES")
        print("=" * 30)
        
        # Print cascade modes summary
        print(f"Branch: {self.current_branch}")
        mode_summary = []
        for rule in self.config["rules"]:
            rule_id = rule["id"]
            effective_mode = self._get_effective_mode(rule_id)
            mode_summary.append(f"{rule_id}={effective_mode}")
        print(f"Cascade Modes: {' '.join(mode_summary)} on {self.current_branch}")
        print("")
        
        results = []
        
        for rule in self.config["rules"]:
            rule_id = rule["id"]
            rule_signals = rule["signals"]
            window_days = rule["window_days"]
            decision = rule["decision"]
            rationale = rule["rationale"]
            
            # Get effective mode for this rule
            effective_mode = self._get_effective_mode(rule_id)
            
            print(f"Evaluating Rule {rule_id}: {rationale} (mode: {effective_mode})")
            
            # Check if rule conditions are met
            triggered_signals = self._check_rule_conditions(rule_signals)
            
            if triggered_signals:
                result = {
                    "rule_id": rule_id,
                    "decision": decision,
                    "rationale": rationale,
                    "window_days": window_days,
                    "triggered_signals": triggered_signals,
                    "effective_mode": effective_mode,
                    "branch": self.current_branch,
                    "ts": datetime.now().isoformat(),
                }
                results.append(result)
                print(f"  ✅ Rule {rule_id} TRIGGERED ({effective_mode.upper()})")
            else:
                print(f"  ❌ Rule {rule_id} not triggered")
        
        self.cascade_results = results
        return results

    def _check_rule_conditions(self, rule_signals: List[str]) -> List[Dict[str, Any]]:
        """Check if rule conditions are met by current signals."""
        triggered_signals = []

        for signal_spec in rule_signals:
            if ">=" in signal_spec:
                # Parse signal with severity requirement
                signal_id, severity_req = signal_spec.split(">=")
                severity_req = severity_req.strip()
            else:
                # Signal without severity requirement (e.g., "#1" for super-delegate)
                signal_id = signal_spec
                severity_req = None

            # Find matching signal
            for signal in self.signals:
                if signal["id"] == signal_id:
                    if severity_req is None or signal["severity"] == severity_req:
                        triggered_signals.append(signal)
                    break

        return triggered_signals

    def generate_cascade_summary(self) -> str:
        """Generate cascade summary line."""
        if not self.cascade_results:
            return "CASCADE: clean, no rules triggered"

        # Get the first triggered rule
        rule = self.cascade_results[0]
        rule_id = rule["rule_id"]
        decision = rule["decision"].upper()
        window_days = rule["window_days"]

        # Format triggered signals
        signal_strs = []
        for signal in rule["triggered_signals"]:
            signal_id = signal["id"]
            severity = signal["severity"].upper()

            if signal_id == "#2":
                value = f"{signal['value_ms']}ms"
            elif signal_id == "#3":
                value = f"{signal['flows']}flows"
            elif signal_id == "#4":
                value = f"{signal['pct']}%"
            else:
                value = ""

            if value:
                signal_strs.append(f"{signal_id}={severity}({value})")
            else:
                signal_strs.append(f"{signal_id}={severity}")

        signals_str = ", ".join(signal_strs)

        # Generate next actions
        next_actions = self._generate_next_actions(rule)

        return f"CASCADE: rule={rule_id}, signals=[{signals_str}], window={window_days}d, decision={decision}, next={next_actions}"

    def _generate_next_actions(self, rule: Dict[str, Any]) -> str:
        """Generate next actions based on triggered rule."""
        rule_id = rule["rule_id"]

        if rule_id == "A":
            return "remove_hierarchy+spread_knowledge"
        elif rule_id == "B":
            return "reduce_complexity+optimize_latency"
        elif rule_id == "C":
            return "reduce_complexity+spread_knowledge"
        elif rule_id == "D":
            return "optimize_latency+spread_knowledge"
        else:
            return "review_constitutional_drift"

    def save_results(self, json_path: str, md_path: str) -> None:
        """Save cascade results to JSON and Markdown files."""
        # Prepare JSON output
        json_output = {
            "timestamp": datetime.now().isoformat(),
            "summary": self.generate_cascade_summary(),
            "exit_code": self._determine_exit_code(),
            "cascade_results": self.cascade_results,
            "signals": self.signals,
        }

        # Save JSON
        os.makedirs(os.path.dirname(json_path), exist_ok=True)
        with open(json_path, "w") as f:
            json.dump(json_output, f, indent=2)

        # Save Markdown
        os.makedirs(os.path.dirname(md_path), exist_ok=True)
        with open(md_path, 'w') as f:
            f.write(self._generate_markdown_report())

    def _generate_markdown_report(self) -> str:
        """Generate human-readable markdown report."""
        md = []
        md.append("# Constitutional Cascade Report")
        md.append("")
        md.append(f"**Generated**: {datetime.now().isoformat()}")
        md.append("")

        # Summary
        md.append("## Cascade Summary")
        md.append("")
        md.append(f"```")
        md.append(self.generate_cascade_summary())
        md.append("```")
        md.append("")

        # Signals
        md.append("## Collected Signals")
        md.append("")
        for signal in self.signals:
            signal_id = signal["id"]
            severity = signal["severity"].upper()
            md.append(f"### Signal {signal_id}: {severity}")
            md.append("")

            if signal_id == "#1":
                md.append(f"- **Type**: Super-delegate pattern")
                md.append(f"- **Files**: {', '.join(signal['meta']['files'])}")
            elif signal_id == "#2":
                md.append(f"- **Type**: Override latency")
                md.append(f"- **Value**: {signal['value_ms']}ms")
            elif signal_id == "#3":
                md.append(f"- **Type**: Delegation complexity")
                md.append(f"- **Flows**: {signal['flows']} in {signal['module']}")
            elif signal_id == "#4":
                md.append(f"- **Type**: Maintainer concentration")
                md.append(f"- **Percentage**: {signal['pct']}%")
                md.append(f"- **Commits**: {signal['commits']}")

            md.append("")

        # Cascade Results
        if self.cascade_results:
            md.append("## Triggered Cascade Rules")
            md.append("")
            for result in self.cascade_results:
                md.append(f"### Rule {result['rule_id']}")
                md.append("")
                md.append(f"- **Decision**: {result['decision'].upper()}")
                md.append(f"- **Rationale**: {result['rationale']}")
                md.append(f"- **Window**: {result['window_days']} days")
                md.append("")
        else:
            md.append("## Cascade Results")
            md.append("")
            md.append("✅ No cascade rules triggered")
            md.append("")

        return "\n".join(md)

    def _determine_exit_code(self) -> int:
        """Determine exit code based on cascade results and effective modes."""
        if not self.cascade_results:
            return EXIT_OK

        # Check if any enforce-mode rule results in BLOCK
        for result in self.cascade_results:
            if (
                result["decision"] == "block"
                and result.get("effective_mode") == "enforce"
            ):
                return EXIT_BLOCK

        # Check if any warn-mode rules are triggered (for warnings)
        for result in self.cascade_results:
            if result["decision"] == "block" and result.get("effective_mode") == "warn":
                return EXIT_WARN

        return EXIT_OK


def main() -> None:
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Constitutional Cascade Detector",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    parser.add_argument(
        "--mode",
        choices=["shadow", "warn", "enforce"],
        default="shadow",
        help="Cascade detection mode",
    )

    parser.add_argument(
        "--json-out",
        default="reports/constitutional_cascade.json",
        help="Output JSON file path",
    )

    parser.add_argument(
        "--config",
        default="backend/config/constitutional_cascade_rules.json",
        help="Cascade rules configuration file",
    )

    args = parser.parse_args()

    print("🚀 CONSTITUTIONAL CASCADE DETECTOR")
    print("=" * 40)
    print(f"Mode: {args.mode}")
    print(f"Config: {args.config}")
    print("")

    # Initialize detector
    detector = ConstitutionalCascadeDetector(args.config)

    # Collect signals
    signals = detector.collect_all_signals()
    print(f"\n📊 Collected {len(signals)} signals")

    # Evaluate cascade rules
    results = detector.evaluate_cascade_rules()
    print(f"\n🔍 Evaluated {len(results)} cascade rules")

    # Save results
    md_out = args.json_out.replace(".json", ".md")
    detector.save_results(args.json_out, md_out)

    # Determine exit code
    exit_code = detector._determine_exit_code()

    print(f"\n📄 Results saved to:")
    print(f"  JSON: {args.json_out}")
    print(f"  Markdown: {md_out}")
    print(f"\n🎯 Exit code: {exit_code}")
    print(f"📋 Summary: {detector.generate_cascade_summary()}")

    sys.exit(exit_code)


if __name__ == "__main__":
    main()
