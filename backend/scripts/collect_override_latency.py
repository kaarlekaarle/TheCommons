#!/usr/bin/env python3
"""
Override Latency Metrics Collector

This script collects and analyzes override latency metrics from application logs
to monitor SLO compliance and identify performance bottlenecks.
"""

import argparse
import json
import os
import re
import statistics
import tempfile
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional


class OverrideLatencyCollector:
    def __init__(self, log_file: str):
        self.log_file = log_file
        self.metrics = {
            "total_requests": 0,
            "cache_hits": 0,
            "cache_misses": 0,
            "fast_path_hits": 0,
            "latencies": {
                "total": [],
                "db": [],
                "cache": [],
                "deserialize": [],
                "override_check": [],
            },
            "chain_lengths": [],
            "db_queries": [],
            "memoization_hits": [],
            "errors": [],
        }

    def collect_metrics(self, hours_back: int = 24) -> Dict[str, Any]:
        """Collect metrics from log file for the specified time period."""
        cutoff_time = datetime.now(timezone.utc) - timedelta(hours=hours_back)

        # Log patterns for chain resolution
        cache_hit_pattern = r"Chain resolution cache hit: ([\d.]+)s total \(cache: ([\d.]+)s, deserialize: ([\d.]+)s\)"
        cache_miss_pattern = r"Chain resolution completed: ([\d.]+)s total \(db: ([\d.]+)s, cache: ([\d.]+)s, queries: (\d+)\)"
        override_pattern = r"Override resolution completed: ([\d.]+)s total \(db: ([\d.]+)s, cache: ([\d.]+)s\)"
        fast_path_pattern = (
            r"Override fast-path cache hit: ([\d.]+)s total \(cache: ([\d.]+)s\)"
        )

        with open(self.log_file, "r") as f:
            for line in f:
                # Check if line contains chain resolution metrics
                if "Chain resolution cache hit:" in line:
                    self._parse_cache_hit(line, cache_hit_pattern, cutoff_time)
                elif "Chain resolution completed:" in line:
                    self._parse_cache_miss(line, cache_miss_pattern, cutoff_time)
                elif "Override resolution completed:" in line:
                    self._parse_override_resolution(line, override_pattern, cutoff_time)
                elif "Override fast-path cache hit:" in line:
                    self._parse_fast_path_hit(line, fast_path_pattern, cutoff_time)

        return self._calculate_statistics()

    def _parse_cache_hit(self, line: str, pattern: str, cutoff_time: datetime) -> None:
        """Parse cache hit log line."""
        match = re.search(pattern, line)
        if not match:
            return

        # Extract timestamps and check if within time window
        timestamp_match = re.search(r"(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})", line)
        if timestamp_match:
            try:
                log_time = datetime.strptime(
                    timestamp_match.group(1), "%Y-%m-%d %H:%M:%S"
                )
                if log_time < cutoff_time:
                    return
            except ValueError:
                pass

        total_time = float(match.group(1))
        cache_time = float(match.group(2))
        deserialize_time = float(match.group(3))

        self.metrics["total_requests"] += 1
        self.metrics["cache_hits"] += 1
        self.metrics["latencies"]["total"].append(total_time)
        self.metrics["latencies"]["cache"].append(cache_time)
        self.metrics["latencies"]["deserialize"].append(deserialize_time)

        # Extract additional metrics from JSON
        json_match = re.search(r"\{.*\}", line)
        if json_match:
            try:
                extra_data = json.loads(json_match.group())
                self.metrics["chain_lengths"].append(extra_data.get("chain_length", 0))
            except json.JSONDecodeError:
                pass

    def _parse_cache_miss(self, line: str, pattern: str, cutoff_time: datetime) -> None:
        """Parse cache miss log line."""
        match = re.search(pattern, line)
        if not match:
            return

        # Extract timestamps and check if within time window
        timestamp_match = re.search(r"(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})", line)
        if timestamp_match:
            try:
                log_time = datetime.strptime(
                    timestamp_match.group(1), "%Y-%m-%d %H:%M:%S"
                )
                if log_time < cutoff_time:
                    return
            except ValueError:
                pass

        total_time = float(match.group(1))
        db_time = float(match.group(2))
        cache_time = float(match.group(3))
        db_queries = int(match.group(4))

        self.metrics["total_requests"] += 1
        self.metrics["cache_misses"] += 1
        self.metrics["latencies"]["total"].append(total_time)
        self.metrics["latencies"]["db"].append(db_time)
        self.metrics["latencies"]["cache"].append(cache_time)
        self.metrics["db_queries"].append(db_queries)

        # Extract additional metrics from JSON
        json_match = re.search(r"\{.*\}", line)
        if json_match:
            try:
                extra_data = json.loads(json_match.group())
                self.metrics["chain_lengths"].append(extra_data.get("chain_length", 0))
                self.metrics["memoization_hits"].append(
                    extra_data.get("memoization_hits", 0)
                )
            except json.JSONDecodeError:
                pass

    def _parse_override_resolution(
        self, line: str, pattern: str, cutoff_time: datetime
    ) -> None:
        """Parse override resolution log line."""
        match = re.search(pattern, line)
        if not match:
            return

        # Extract timestamps and check if within time window
        timestamp_match = re.search(r"(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})", line)
        if timestamp_match:
            try:
                log_time = datetime.strptime(
                    timestamp_match.group(1), "%Y-%m-%d %H:%M:%S"
                )
                if log_time < cutoff_time:
                    return
            except ValueError:
                pass

        total_time = float(match.group(1))
        db_time = float(match.group(2))
        cache_time = float(match.group(3))

        self.metrics["total_requests"] += 1
        self.metrics["latencies"]["total"].append(total_time)
        self.metrics["latencies"]["db"].append(db_time)
        self.metrics["latencies"]["cache"].append(cache_time)

        # Extract additional metrics from JSON
        json_match = re.search(r"\{.*\}", line)
        if json_match:
            try:
                extra_data = json.loads(json_match.group())
                self.metrics["chain_lengths"].append(extra_data.get("chain_length", 0))
                if extra_data.get("fast_path_hit", False):
                    self.metrics["fast_path_hits"] += 1
            except json.JSONDecodeError:
                pass

    def _parse_fast_path_hit(
        self, line: str, pattern: str, cutoff_time: datetime
    ) -> None:
        """Parse fast-path cache hit log line."""
        match = re.search(pattern, line)
        if not match:
            return

        # Extract timestamps and check if within time window
        timestamp_match = re.search(r"(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})", line)
        if timestamp_match:
            try:
                log_time = datetime.strptime(
                    timestamp_match.group(1), "%Y-%m-%d %H:%M:%S"
                )
                if log_time < cutoff_time:
                    return
            except ValueError:
                pass

        total_time = float(match.group(1))
        cache_time = float(match.group(2))

        self.metrics["total_requests"] += 1
        self.metrics["fast_path_hits"] += 1
        self.metrics["latencies"]["total"].append(total_time)
        self.metrics["latencies"]["cache"].append(cache_time)

        # Extract additional metrics from JSON
        json_match = re.search(r"\{.*\}", line)
        if json_match:
            try:
                extra_data = json.loads(json_match.group())
                self.metrics["chain_lengths"].append(extra_data.get("chain_length", 0))
            except json.JSONDecodeError:
                pass

    def _calculate_statistics(self) -> Dict[str, Any]:
        """Calculate statistics from collected metrics."""
        stats = {
            "summary": {
                "total_requests": self.metrics["total_requests"],
                "cache_hit_rate": 0.0,
                "avg_chain_length": 0.0,
                "avg_db_queries": 0.0,
            },
            "latency_percentiles": {},
            "slo_compliance": {},
        }

        # Calculate cache hit rate
        if self.metrics["total_requests"] > 0:
            stats["summary"]["cache_hit_rate"] = (
                self.metrics["cache_hits"] / self.metrics["total_requests"]
            )

        # Calculate average chain length
        if self.metrics["chain_lengths"]:
            stats["summary"]["avg_chain_length"] = statistics.mean(
                self.metrics["chain_lengths"]
            )

        # Calculate average DB queries
        if self.metrics["db_queries"]:
            stats["summary"]["avg_db_queries"] = statistics.mean(
                self.metrics["db_queries"]
            )

        # Calculate latency percentiles
        for latency_type, values in self.metrics["latencies"].items():
            if values:
                stats["latency_percentiles"][latency_type] = {
                    "p50": (
                        statistics.quantiles(values, n=2)[0]
                        if len(values) > 1
                        else values[0]
                    ),
                    "p95": (
                        statistics.quantiles(values, n=20)[18]
                        if len(values) > 19
                        else max(values)
                    ),
                    "p99": (
                        statistics.quantiles(values, n=100)[98]
                        if len(values) > 99
                        else max(values)
                    ),
                    "min": min(values),
                    "max": max(values),
                    "count": len(values),
                }

        # Check SLO compliance
        total_latencies = self.metrics["latencies"]["total"]
        if total_latencies:
            p95_latency = (
                statistics.quantiles(total_latencies, n=20)[18]
                if len(total_latencies) > 19
                else max(total_latencies)
            )
            p99_latency = (
                statistics.quantiles(total_latencies, n=100)[98]
                if len(total_latencies) > 99
                else max(total_latencies)
            )

            stats["slo_compliance"] = {
                "p95_target_1_5s": p95_latency <= 1.5,
                "p99_target_2s": p99_latency <= 2.0,
                "p95_latency_ms": int(p95_latency * 1000),
                "p99_latency_ms": int(p99_latency * 1000),
            }

        return stats


def main():
    parser = argparse.ArgumentParser(description="Collect override latency metrics")
    parser.add_argument(
        "--log-file", default="backend/logs/app.log", help="Path to log file"
    )
    parser.add_argument("--hours-back", type=int, default=24, help="Hours to look back")
    parser.add_argument("--json-out", help="Output JSON file path")
    parser.add_argument(
        "--format", choices=["json", "text"], default="text", help="Output format"
    )

    args = parser.parse_args()

    if not Path(args.log_file).exists():
        print(f"Error: Log file {args.log_file} not found")
        return 1

    collector = OverrideLatencyCollector(args.log_file)
    stats = collector.collect_metrics(args.hours_back)

    # Add UTC timestamp
    stats["timestamp"] = datetime.now(timezone.utc).isoformat()

    if args.format == "json":
        output = json.dumps(stats, indent=2)
    else:
        output = format_text_output(stats)

    if args.json_out:
        # Atomic write using temporary file
        output_path = Path(args.json_out)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        # Create temporary file in the same directory
        with tempfile.NamedTemporaryFile(
            mode="w",
            dir=output_path.parent,
            prefix=f"{output_path.stem}_tmp_",
            suffix=output_path.suffix,
            delete=False,
        ) as tmp_file:
            tmp_file.write(output)
            tmp_file.flush()
            os.fsync(tmp_file.fileno())  # Ensure data is written to disk

        # Atomic rename
        os.rename(tmp_file.name, output_path)

        print(f"Metrics saved to {args.json_out}")
    else:
        print(output)

    return 0


def format_text_output(stats: Dict[str, Any]) -> str:
    """Format statistics as human-readable text."""
    output = []
    output.append("Override Latency Metrics Report")
    output.append("=" * 40)
    output.append(f"Total Requests: {stats['summary']['total_requests']}")
    output.append(f"Cache Hit Rate: {stats['summary']['cache_hit_rate']:.1%}")
    output.append(f"Average Chain Length: {stats['summary']['avg_chain_length']:.1f}")
    output.append(f"Average DB Queries: {stats['summary']['avg_db_queries']:.1f}")
    output.append("")

    output.append("Latency Percentiles (seconds):")
    for latency_type, percentiles in stats["latency_percentiles"].items():
        output.append(f"  {latency_type.upper()}:")
        output.append(f"    P50: {percentiles['p50']:.3f}s")
        output.append(f"    P95: {percentiles['p95']:.3f}s")
        output.append(f"    P99: {percentiles['p99']:.3f}s")
        output.append(f"    Min: {percentiles['min']:.3f}s")
        output.append(f"    Max: {percentiles['max']:.3f}s")
        output.append(f"    Count: {percentiles['count']}")
        output.append("")

    output.append("SLO Compliance:")
    slo = stats.get("slo_compliance", {})
    if slo:
        output.append(
            f"  P95 ≤ 1.5s: {'✅' if slo.get('p95_target_1_5s', False) else '❌'} ({slo.get('p95_latency_ms', 0)}ms)"
        )
        output.append(
            f"  P99 ≤ 2.0s: {'✅' if slo.get('p99_target_2s', False) else '❌'} ({slo.get('p99_latency_ms', 0)}ms)"
        )
    else:
        output.append("  No latency data available for SLO compliance check")

    return "\n".join(output)


if __name__ == "__main__":
    exit(main())
