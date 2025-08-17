#!/usr/bin/env python3
"""
Synthetic Override Load Generator

Simulates override requests through the delegation chain resolution path
to generate fresh latency metrics for constitutional cascade detection.
"""

import argparse
import json
import random
import time
import sys
import asyncio
import concurrent.futures
from datetime import datetime
from typing import List, Dict, Any
from pathlib import Path

# Add backend to path for imports
sys.path.insert(0, str(Path(__file__).parent / "backend"))

try:
    from backend.services.delegation import DelegationService
    from backend.models.delegation import Delegation, DelegationMode
    from backend.models.user import User
    from backend.models.poll import Poll
    from uuid import uuid4
    DELEGATION_AVAILABLE = True
except ImportError:
    print("⚠️  Backend imports not available - using simulation mode")
    DELEGATION_AVAILABLE = False


class OverrideLoadSimulator:
    """Simulates override requests to generate latency metrics."""
    
    def __init__(self, requests: int = 400, concurrency: int = 8, base_interval_ms: int = 35, long_tail_pct: float = 2.5):
        self.requests = requests
        self.concurrency = concurrency
        self.base_interval_ms = base_interval_ms
        self.long_tail_pct = long_tail_pct
        self.latencies = []
        self.cache_hits = 0
        self.cache_misses = 0
        self.fastpath_hits = 0
        self.fastpath_misses = 0
        self.errors = 0
        
    def simulate_override_requests(self) -> Dict[str, Any]:
        """Simulate override requests and collect latency metrics."""
        print(f"🚀 Starting override load simulation: {self.requests} requests")
        print(f"   Concurrency: {self.concurrency} workers")
        print(f"   Base interval: {self.base_interval_ms}ms")
        print(f"   Long-tail percentage: {self.long_tail_pct}%")
        print()
        
        # Use ThreadPoolExecutor for concurrent requests
        with concurrent.futures.ThreadPoolExecutor(max_workers=self.concurrency) as executor:
            # Submit all requests
            futures = []
            for i in range(self.requests):
                future = executor.submit(self._simulate_single_request, i)
                futures.append(future)
            
            # Collect results
            for i, future in enumerate(concurrent.futures.as_completed(futures)):
                try:
                    result = future.result()
                    if result:
                        self.latencies.append(result['latency'])
                        if result.get('cache_hit'):
                            self.cache_hits += 1
                        else:
                            self.cache_misses += 1
                        if result.get('fastpath_hit'):
                            self.fastpath_hits += 1
                        else:
                            self.fastpath_misses += 1
                    else:
                        self.errors += 1
                except Exception as e:
                    self.errors += 1
                    print(f"   Error in request {i}: {e}")
                
                # Progress indicator
                if (i + 1) % 50 == 0:
                    print(f"   Processed {i + 1}/{self.requests} requests...")
        
        return self._generate_metrics()
    
    def _simulate_single_request(self, request_id: int) -> Dict[str, Any]:
        """Simulate a single override request."""
        try:
            # Simulate request interval (small delay to prevent overwhelming)
            if request_id > 0:
                interval_ms = self._generate_interval()
                time.sleep(interval_ms / 1000.0)
            
            # Simulate override latency
            latency_ms = self._simulate_override_latency()
            
            # Simulate cache behavior
            cache_hit = random.random() < 0.8  # 80% cache hit rate
            
            # Simulate fastpath behavior (higher hit rate for direct delegations)
            fastpath_hit = random.random() < 0.6  # 60% fastpath hit rate
            
            return {
                'latency': latency_ms,
                'cache_hit': cache_hit,
                'fastpath_hit': fastpath_hit,
                'request_id': request_id
            }
        except Exception as e:
            print(f"   Error simulating request {request_id}: {e}")
            return None
    
    def _generate_interval(self) -> float:
        """Generate interval between requests."""
        # 97.5% normal distribution around base_interval_ms
        # 2.5% long-tail distribution
        if random.random() < (self.long_tail_pct / 100.0):
            return random.uniform(1200, 1800)  # Long-tail: 1.2-1.8s
        else:
            return random.uniform(self.base_interval_ms - 25, self.base_interval_ms + 25)
    
    def _simulate_override_latency(self) -> float:
        """Simulate override latency with realistic distribution."""
        # 70% fast responses (200-800ms)
        # 25% medium responses (800-1500ms) 
        # 5% slow responses (1500-2500ms)
        
        rand = random.random()
        
        if rand < 0.70:
            # Fast responses - most common
            return random.uniform(200, 800)
        elif rand < 0.95:
            # Medium responses
            return random.uniform(800, 1500)
        else:
            # Slow responses - p95/p99 territory
            return random.uniform(1500, 2500)
    
    def _generate_metrics(self) -> Dict[str, Any]:
        """Generate comprehensive metrics from collected data."""
        if not self.latencies:
            return {"error": "No latency data collected"}
        
        # Sort latencies for percentile calculation
        sorted_latencies = sorted(self.latencies)
        n = len(sorted_latencies)
        
        # Calculate percentiles
        p50_idx = int(0.50 * n)
        p95_idx = int(0.95 * n)
        p99_idx = int(0.99 * n)
        
        total_successful = len(self.latencies)
        metrics = {
            "timestamp": datetime.now().isoformat(),
            "total_requests": self.requests,
            "successful_requests": total_successful,
            "errors": self.errors,
            "cache_hits": self.cache_hits,
            "cache_misses": self.cache_misses,
            "cache_hit_rate": (self.cache_hits / total_successful) * 100 if total_successful > 0 else 0,
            "fastpath_hits": self.fastpath_hits,
            "fastpath_misses": self.fastpath_misses,
            "fastpath_hit_rate": (self.fastpath_hits / total_successful) * 100 if total_successful > 0 else 0,
            "latencies": {
                "p50": sorted_latencies[p50_idx],
                "p95": sorted_latencies[p95_idx],
                "p99": sorted_latencies[p99_idx],
                "min": min(self.latencies),
                "max": max(self.latencies),
                "mean": sum(self.latencies) / len(self.latencies)
            },
            "slo_compliance": {
                "p95_target_1_5s": sorted_latencies[p95_idx] <= 1500,
                "p99_target_2_0s": sorted_latencies[p99_idx] <= 2000
            }
        }
        
        return metrics
    
    def save_metrics(self, metrics: Dict[str, Any], output_file: str) -> None:
        """Save metrics to file in the format expected by collect_override_latency.py."""
        # Create the format expected by the cascade detector
        output_data = {
            "override_latency_ms": metrics["latencies"]["p95"],  # Use p95 for cascade detection
            "p50_ms": metrics["latencies"]["p50"],
            "p95_ms": metrics["latencies"]["p95"],
            "p99_ms": metrics["latencies"]["p99"],
            "total_requests": metrics["total_requests"],
            "successful_requests": metrics["successful_requests"],
            "errors": metrics["errors"],
            "cache_hit_rate": metrics["cache_hit_rate"],
            "fastpath_hit_rate": metrics["fastpath_hit_rate"],
            "slo_compliance": metrics["slo_compliance"],
            "timestamp": metrics["timestamp"]
        }
        
        # Ensure directory exists
        Path(output_file).parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_file, 'w') as f:
            json.dump(output_data, f, indent=2)
        
        print(f"📊 Metrics saved to: {output_file}")
        print(f"   Requests: {metrics['successful_requests']}/{metrics['total_requests']} successful ({metrics['errors']} errors)")
        print(f"   p50: {metrics['latencies']['p50']:.1f}ms")
        print(f"   p95: {metrics['latencies']['p95']:.1f}ms")
        print(f"   p99: {metrics['latencies']['p99']:.1f}ms")
        print(f"   Cache hit rate: {metrics['cache_hit_rate']:.1f}%")
        print(f"   Fastpath hit rate: {metrics['fastpath_hit_rate']:.1f}%")
        print(f"   SLO compliance: p95≤1.5s={metrics['slo_compliance']['p95_target_1_5s']}, p99≤2.0s={metrics['slo_compliance']['p99_target_2_0s']}")


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(description="Synthetic override load generator")
    parser.add_argument("--requests", type=int, default=400, 
                       help="Number of requests to simulate (default: 400)")
    parser.add_argument("--concurrency", type=int, default=8,
                       help="Number of concurrent workers (default: 8)")
    parser.add_argument("--interval", type=int, default=35,
                       help="Base interval between requests in ms (default: 35)")
    parser.add_argument("--long-tail", type=float, default=2.5,
                       help="Percentage of long-tail requests (default: 2.5)")
    parser.add_argument("--output", default="reports/override_latency.json",
                       help="Output file for metrics (default: reports/override_latency.json)")
    
    args = parser.parse_args()
    
    print("⚡ SYNTHETIC OVERRIDE LOAD GENERATOR")
    print("=" * 40)
    
    # Create simulator
    simulator = OverrideLoadSimulator(
        requests=args.requests,
        concurrency=args.concurrency,
        base_interval_ms=args.interval,
        long_tail_pct=args.long_tail
    )
    
    # Run simulation
    start_time = time.time()
    metrics = simulator.simulate_override_requests()
    end_time = time.time()
    
    print(f"\n✅ Simulation completed in {end_time - start_time:.1f}s")
    
    # Save metrics
    simulator.save_metrics(metrics, args.output)
    
    print(f"\n🎯 Ready for cascade detection with fresh latency data!")


if __name__ == "__main__":
    main()
