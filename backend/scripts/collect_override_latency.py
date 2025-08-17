#!/usr/bin/env python3
"""
Override Latency Collection

Collects real override latency metrics from backend logs and Redis for cascade detection.
"""

import os
import sys
import json
import argparse
import re
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from pathlib import Path


def parse_log_line(line: str) -> Optional[Dict[str, Any]]:
    """Parse a log line for override latency metrics."""
    try:
        # Look for structured log format
        if '"evt":"override_latency_ms"' in line:
            # Extract JSON from log line
            json_start = line.find('{')
            if json_start != -1:
                json_str = line[json_start:]
                data = json.loads(json_str)
                return {
                    "ms": data.get("ms", 0),
                    "poll_id": data.get("poll_id"),
                    "user_id": data.get("user_id"),
                    "ts": data.get("ts", datetime.now().isoformat())
                }
    except (json.JSONDecodeError, KeyError):
        pass
    
    # Fallback: look for latency patterns in unstructured logs
    latency_patterns = [
        r'override.*latency.*?(\d+)ms',
        r'latency.*?(\d+)ms.*override',
        r'override.*?(\d+)ms.*latency'
    ]
    
    for pattern in latency_patterns:
        match = re.search(pattern, line, re.IGNORECASE)
        if match:
            return {
                "ms": int(match.group(1)),
                "poll_id": None,
                "user_id": None,
                "ts": datetime.now().isoformat()
            }
    
    return None


def collect_from_logs(log_path: str, lines: int = 1000) -> List[Dict[str, Any]]:
    """Collect override latency metrics from log file."""
    latencies = []
    
    if not os.path.exists(log_path):
        print(f"⚠️  Log file not found: {log_path}")
        return latencies
    
    try:
        with open(log_path, 'r') as f:
            # Read last N lines
            all_lines = f.readlines()
            recent_lines = all_lines[-lines:] if len(all_lines) > lines else all_lines
            
            for line in recent_lines:
                latency_data = parse_log_line(line.strip())
                if latency_data:
                    latencies.append(latency_data)
    
    except IOError as e:
        print(f"❌ Could not read log file: {e}")
    
    return latencies


def collect_from_redis() -> List[Dict[str, Any]]:
    """Collect override latency metrics from Redis (if available)."""
    latencies = []
    
    try:
        import redis
        
        # Try to connect to Redis
        r = redis.Redis(host='localhost', port=6379, db=0, decode_responses=True)
        
        # Get metrics from Redis list
        redis_key = "metrics:override_latency"
        if r.exists(redis_key):
            # Get last 100 entries (cap at reasonable size)
            entries = r.lrange(redis_key, 0, 99)
            
            for entry in entries:
                try:
                    data = json.loads(entry)
                    latencies.append(data)
                except json.JSONDecodeError:
                    continue
        
        r.close()
        
    except ImportError:
        print("⚠️  Redis module not available - skipping Redis collection")
    except Exception as e:
        print(f"⚠️  Redis collection failed: {e}")
    
    return latencies


def calculate_statistics(latencies: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Calculate latency statistics."""
    if not latencies:
        return {
            "count": 0,
            "p50": 0,
            "p95": 0,
            "p99": 0,
            "min": 0,
            "max": 0,
            "mean": 0,
            "window_size": "0s"
        }
    
    # Extract latency values
    values = [lat["ms"] for lat in latencies if lat.get("ms")]
    values.sort()
    
    if not values:
        return {
            "count": 0,
            "p50": 0,
            "p95": 0,
            "p99": 0,
            "min": 0,
            "max": 0,
            "mean": 0,
            "window_size": "0s"
        }
    
    # Calculate percentiles
    count = len(values)
    p50_idx = int(count * 0.5)
    p95_idx = int(count * 0.95)
    p99_idx = int(count * 0.99)
    
    stats = {
        "count": count,
        "p50": values[p50_idx] if p50_idx < count else values[-1],
        "p95": values[p95_idx] if p95_idx < count else values[-1],
        "p99": values[p99_idx] if p99_idx < count else values[-1],
        "min": values[0],
        "max": values[-1],
        "mean": sum(values) / count,
        "window_size": f"{count} samples"
    }
    
    return stats


def save_latency_stats(stats: Dict[str, Any], output_path: str) -> None:
    """Save latency statistics to file."""
    output_data = {
        "timestamp": datetime.now().isoformat(),
        "source": "real_metrics",
        "statistics": stats,
        "collection_method": "logs_and_redis"
    }
    
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump(output_data, f, indent=2)
    
    print(f"✅ Latency stats saved to {output_path}")


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(description="Collect real override latency metrics")
    parser.add_argument("--log-file", default="logs/app.log", help="Path to application log file")
    parser.add_argument("--lines", type=int, default=1000, help="Number of log lines to analyze")
    parser.add_argument("--output", default="reports/override_latency_stats.json", 
                       help="Output path for latency statistics")
    parser.add_argument("--redis-only", action="store_true", help="Only collect from Redis")
    parser.add_argument("--logs-only", action="store_true", help="Only collect from logs")
    
    args = parser.parse_args()
    
    print("📊 COLLECTING OVERRIDE LATENCY METRICS")
    print("=" * 40)
    
    latencies = []
    
    # Collect from logs
    if not args.redis_only:
        print(f"📄 Collecting from logs: {args.log_file}")
        log_latencies = collect_from_logs(args.log_file, args.lines)
        latencies.extend(log_latencies)
        print(f"   Found {len(log_latencies)} latency entries in logs")
    
    # Collect from Redis
    if not args.logs_only:
        print("🔴 Collecting from Redis")
        redis_latencies = collect_from_redis()
        latencies.extend(redis_latencies)
        print(f"   Found {len(redis_latencies)} latency entries in Redis")
    
    # Calculate statistics
    print("📈 Calculating statistics...")
    stats = calculate_statistics(latencies)
    
    print(f"📊 Latency Statistics:")
    print(f"   Count: {stats['count']}")
    print(f"   P50: {stats['p50']}ms")
    print(f"   P95: {stats['p95']}ms")
    print(f"   P99: {stats['p99']}ms")
    print(f"   Min: {stats['min']}ms")
    print(f"   Max: {stats['max']}ms")
    print(f"   Mean: {stats['mean']:.1f}ms")
    print(f"   Window: {stats['window_size']}")
    
    # Save statistics
    save_latency_stats(stats, args.output)
    
    print("✅ Override latency collection complete")


if __name__ == "__main__":
    main()
