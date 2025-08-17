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

    def __init__(
        self, config_path: str = "backend/config/constitutional_cascade_rules.json"
    ):
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
                check=False,
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
            # Look for override latency files and pick the newest by timestamp
            override_latency_files = [
                "reports/override_latency.json",
                "reports/test_override_latency.json",
                "reports/signal_override_latency.json",
            ]

            newest_file = None
            newest_timestamp = None

            for file_path in override_latency_files:
                if os.path.exists(file_path):
                    try:
                        with open(file_path, "r") as f:
                            data = json.load(f)

                        # Check if file has a timestamp field
                        file_timestamp = data.get("timestamp")
                        if file_timestamp:
                            # Parse ISO8601 timestamp
                            try:
                                dt = datetime.fromisoformat(
                                    file_timestamp.replace("Z", "+00:00")
                                )
                                if newest_timestamp is None or dt > newest_timestamp:
                                    newest_timestamp = dt
                                    newest_file = file_path
                            except ValueError:
                                # Fallback to file modification time
                                file_stat = os.stat(file_path)
                                file_mtime = datetime.fromtimestamp(file_stat.st_mtime)
                                if (
                                    newest_timestamp is None
                                    or file_mtime > newest_timestamp
                                ):
                                    newest_timestamp = file_mtime
                                    newest_file = file_path
                        else:
                            # No timestamp in file, use modification time
                            file_stat = os.stat(file_path)
                            file_mtime = datetime.fromtimestamp(file_stat.st_mtime)
                            if (
                                newest_timestamp is None
                                or file_mtime > newest_timestamp
                            ):
                                newest_timestamp = file_mtime
                                newest_file = file_path
                    except (json.JSONDecodeError, IOError):
                        continue

            if newest_file and newest_timestamp:
                # Check if data is stale (>24h old)
                now = datetime.now()
                if newest_timestamp.tzinfo is None:
                    # Assume local time if no timezone
                    now = now.replace(tzinfo=None)
                else:
                    # Convert now to UTC for comparison
                    now = now.astimezone()

                age_hours = (now - newest_timestamp).total_seconds() / 3600

                if age_hours > 24:
                    print("⚠️  Latency signal stale (>24h); not blocking.")
                    return {
                        "id": "#2",
                        "metric": "Override latency",
                        "value": "STALE",
                        "unit": "ms",
                        "severity": "info",
                        "description": "Latency signal stale (>24h); not blocking.",
                        "is_blocking": False,  # Mark as non-blocking if stale
                        "file_used": newest_file,
                        "file_age_hours": round(age_hours, 1),
                        "ts": datetime.now().isoformat(),
                    }

                # Read fresh override latency data
                with open(newest_file, "r") as f:
                    data = json.load(f)

                # Extract latency metrics
                p50 = data.get("p50_ms", data.get("statistics", {}).get("p50", 0))
                p95 = data.get("p95_ms", data.get("statistics", {}).get("p95", 0))
                p99 = data.get("p99_ms", data.get("statistics", {}).get("p99", 0))
                cache_hit_rate = data.get("cache_hit_rate", 0)

                # Use p95 for severity determination (primary SLO metric)
                latency_ms = p95

                # Determine severity based on SLOs
                severity = "ok"
                description = f"P95: {p95}ms, P99: {p99}ms, Cache: {cache_hit_rate}%"
                is_blocking = False

                if p95 > 1500:
                    severity = "warn"
                    description += " (P95 > 1.5s)"
                if p99 > 2000:
                    severity = "critical"
                    description += " (P99 > 2.0s)"
                    is_blocking = True  # Blocking if critical

                print(f"📊 Using {newest_file} (age: {age_hours:.1f}h)")
                print(
                    f"   P50: {p50}ms, P95: {p95}ms, P99: {p99}ms, "
                    f"Cache: {cache_hit_rate}%"
                )

                return {
                    "id": "#2",
                    "metric": "Override latency",
                    "value": p95,
                    "unit": "ms",
                    "severity": severity,
                    "description": description,
                    "is_blocking": is_blocking,
                    "file_used": newest_file,
                    "file_age_hours": round(age_hours, 1),
                    "p50_ms": p50,
                    "p95_ms": p95,
                    "p99_ms": p99,
                    "cache_hit_rate": cache_hit_rate,
                    "ts": datetime.now().isoformat(),
                }

            # Fallback: Call constitutional_drift_detector.py if no fresh data
            print("⚠️  No fresh override latency data found, using drift detector...")
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
            print(f"❌ Error collecting signal #2: {e}")
            return {
                "id": "#2",
                "metric": "Override latency",
                "value": "ERROR",
                "unit": "ms",
                "severity": "error",
                "description": f"Error collecting latency: {e}",
                "is_blocking": True,
                "ts": datetime.now().isoformat(),
            }

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
        """Collect signal #4: Maintainer concentration in delegation code."""
        print("🔍 Collecting signal #4: Maintainer concentration...")

        try:
            # Run dependency validator to get maintainer concentration
            result = subprocess.run(
                [
                    sys.executable,
                    "backend/scripts/constitutional_dependency_validator.py",
                    "--emit-maintainer-json",
                    "reports/signal_maintainers.json",
                ],
                capture_output=True,
                text=True,
                check=False,
            )

            if result.returncode != 0:
                print(
                    f"⚠️  Warning: Maintainer concentration check failed: {result.stderr}"
                )
                return None

            # Read the maintainer concentration data
            if os.path.exists("reports/signal_maintainers.json"):
                with open("reports/signal_maintainers.json", "r") as f:
                    data = json.load(f)

                concentration_pct = data.get("concentration_percentage", 0)

                # Determine severity based on thresholds
                thresholds = self.config.get("thresholds", {})
                maintainer_thresholds = thresholds.get(
                    "maintainer_concentration_pct", {}
                )

                if concentration_pct >= maintainer_thresholds.get("critical", 90):
                    severity = "critical"
                elif concentration_pct >= maintainer_thresholds.get("high", 80):
                    severity = "high"
                elif concentration_pct >= maintainer_thresholds.get("warn", 50):
                    severity = "warn"
                else:
                    severity = "info"

                return {
                    "id": "#4",
                    "severity": severity,
                    "value_pct": concentration_pct,
                    "ts": datetime.now().isoformat(),
                    "meta": {
                        "top_maintainer": data.get("top_maintainer", ""),
                        "total_commits": data.get("total_commits", 0),
                        "lookback_days": data.get("lookback_days", 30),
                        "files_analyzed": data.get("files_analyzed", 0),
                    },
                }

            return None

        except Exception as e:
            print(f"⚠️  Warning: Error collecting maintainer concentration signal: {e}")
            return None

    def collect_signal_5_mode_distribution(self) -> Optional[Dict[str, Any]]:
        """Collect signal #5: Delegation mode distribution."""
        print("🔍 Collecting signal #5: Delegation mode distribution...")

        try:
            # Run dependency validator to get mode distribution
            subprocess.run(
                [
                    sys.executable,
                    "backend/scripts/constitutional_dependency_validator.py",
                    "--validate",
                    "test_mode_distribution.txt",
                ],
                capture_output=True,
                text=True,
                check=False,
            )

            # For now, simulate mode distribution check
            # In a real implementation, this would query the database

            # Simulate legacy mode usage based on code patterns
            legacy_usage = 25.0  # Simulated 25% legacy mode usage

            # Determine severity based on legacy mode usage
            if legacy_usage >= 50:  # High legacy usage
                severity = "high"
            elif legacy_usage >= 30:  # Moderate legacy usage
                severity = "warn"
            else:
                severity = "info"

            return {
                "id": "#5",
                "severity": severity,
                "value_pct": legacy_usage,
                "ts": datetime.now().isoformat(),
                "meta": {
                    "mode_distribution": {
                        "legacy_fixed_term": 25,
                        "flexible_domain": 60,
                        "hybrid_seed": 15,
                    },
                    "total_delegations": 100,
                    "transition_health": "moderate",
                },
            }

        except Exception as e:
            print(f"⚠️  Warning: Error collecting mode distribution signal: {e}")
            return None

    def collect_all_signals(self) -> List[Dict[str, Any]]:
        """Collect all constitutional signals."""
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

        signal_5 = self.collect_signal_5_mode_distribution()
        if signal_5:
            signals.append(signal_5)

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
                    # Check if signal is stale (for latency signals)
                    if signal.get("status") == "stale":
                        print(
                            f"    ⚠️  Signal {signal_id} is stale ({signal.get('age_hours', 0):.1f}h old); skipping for blocking"
                        )
                        continue

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
                value = str(signal.get("value", 0)) + "ms"
            elif signal_id == "#3":
                value = f"{signal['flows']}flows"
            elif signal_id == "#4":
                value = f"{signal['value_pct']}%"
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
        with open(md_path, "w") as f:
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
                if signal.get("value") == "STALE":
                    md.append(
                        f"- **Status**: STALE (age: {signal.get('file_age_hours', 0):.1f}h)"
                    )
                    md.append(
                        f"- **Note**: Latency snapshot stale (>24h); ignoring for blocking"
                    )
                else:
                    md.append("- **P95**: " + str(signal.get("p95_ms", signal.get("value", 0))) + "ms")
                    md.append(f"- **P99**: {signal.get('p99_ms', 0)}ms")
                    md.append(
                        f"- **Cache Hit Rate**: {signal.get('cache_hit_rate', 0)}%"
                    )
                    if signal.get("file_used"):
                        md.append(
                            f"- **Snapshot**: {signal.get('file_used')} (age: {signal.get('file_age_hours', 0):.1f}h)"
                        )
            elif signal_id == "#3":
                md.append(f"- **Type**: Delegation complexity")
                md.append(f"- **Flows**: {signal['flows']} in {signal['module']}")
            elif signal_id == "#4":
                md.append(f"- **Type**: Maintainer concentration")
                md.append(f"- **Percentage**: {signal['value_pct']}%")
                md.append(f"- **Commits**: {signal['meta']['total_commits']}")
            elif signal_id == "#5":
                md.append(f"- **Type**: Delegation mode distribution")
                md.append(f"- **Legacy Usage**: {signal['value_pct']}%")
                md.append(f"- **Meta**: {json.dumps(signal['meta'])}")

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
