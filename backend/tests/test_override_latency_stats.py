#!/usr/bin/env python3
"""
Test Override Latency Stats

Tests the override latency statistics collection functionality.
"""

import os
import sys
import json
import tempfile
import unittest
from pathlib import Path

# Add backend/scripts to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'scripts'))

from collect_override_latency import (
    parse_log_line,
    collect_from_logs,
    calculate_statistics,
    save_latency_stats
)


class TestOverrideLatencyStats(unittest.TestCase):
    """Test override latency statistics functionality."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.test_dir = tempfile.mkdtemp()
        self.log_file = os.path.join(self.test_dir, "test_app.log")
        self.stats_file = os.path.join(self.test_dir, "test_stats.json")
    
    def tearDown(self):
        """Clean up test fixtures."""
        import shutil
        shutil.rmtree(self.test_dir)
    
    def test_parse_log_line_structured(self):
        """Test parsing structured log lines."""
        structured_line = '2025-08-17T15:00:00.000Z INFO {"evt":"override_latency_ms","ms":150,"poll_id":"123","user_id":"user1","ts":"2025-08-17T15:00:00.000Z"}'
        
        result = parse_log_line(structured_line)
        self.assertIsNotNone(result)
        self.assertEqual(result["ms"], 150)
        self.assertEqual(result["poll_id"], "123")
        self.assertEqual(result["user_id"], "user1")
    
    def test_parse_log_line_unstructured(self):
        """Test parsing unstructured log lines."""
        unstructured_lines = [
            'Override latency 200ms detected in delegation chain',
            'Latency 300ms override resolution completed',
            'Override 250ms latency for user intent'
        ]
        
        for line in unstructured_lines:
            result = parse_log_line(line)
            self.assertIsNotNone(result)
            self.assertIn("ms", result)
            self.assertIsInstance(result["ms"], int)
    
    def test_parse_log_line_no_match(self):
        """Test parsing log lines with no latency data."""
        no_latency_line = 'Normal log message without latency information'
        
        result = parse_log_line(no_latency_line)
        self.assertIsNone(result)
    
    def test_collect_from_logs(self):
        """Test collecting latency data from log file."""
        # Create test log file with latency entries
        log_content = [
            '2025-08-17T15:00:00.000Z INFO {"evt":"override_latency_ms","ms":150,"poll_id":"123","user_id":"user1","ts":"2025-08-17T15:00:00.000Z"}',
            '2025-08-17T15:01:00.000Z INFO {"evt":"override_latency_ms","ms":200,"poll_id":"124","user_id":"user2","ts":"2025-08-17T15:01:00.000Z"}',
            '2025-08-17T15:02:00.000Z INFO {"evt":"override_latency_ms","ms":180,"poll_id":"125","user_id":"user3","ts":"2025-08-17T15:02:00.000Z"}',
            'Normal log message without latency',
            'Override latency 250ms detected'
        ]
        
        with open(self.log_file, 'w') as f:
            f.write('\n'.join(log_content))
        
        latencies = collect_from_logs(self.log_file, lines=10)
        
        # Should find 4 latency entries (3 structured + 1 unstructured)
        self.assertEqual(len(latencies), 4)
        
        # Check that structured entries are parsed correctly
        structured_entries = [lat for lat in latencies if lat.get("poll_id")]
        self.assertEqual(len(structured_entries), 3)
        
        # Check that unstructured entry is parsed
        unstructured_entries = [lat for lat in latencies if not lat.get("poll_id")]
        self.assertEqual(len(unstructured_entries), 1)
        self.assertEqual(unstructured_entries[0]["ms"], 250)
    
    def test_calculate_statistics(self):
        """Test latency statistics calculation."""
        latencies = [
            {"ms": 100, "poll_id": "1"},
            {"ms": 150, "poll_id": "2"},
            {"ms": 200, "poll_id": "3"},
            {"ms": 250, "poll_id": "4"},
            {"ms": 300, "poll_id": "5"}
        ]
        
        stats = calculate_statistics(latencies)
        
        self.assertEqual(stats["count"], 5)
        self.assertEqual(stats["min"], 100)
        self.assertEqual(stats["max"], 300)
        self.assertEqual(stats["mean"], 200.0)
        self.assertEqual(stats["p50"], 200)  # Median
        self.assertEqual(stats["p95"], 300)  # 95th percentile
        self.assertEqual(stats["p99"], 300)  # 99th percentile
    
    def test_calculate_statistics_empty(self):
        """Test statistics calculation with empty data."""
        stats = calculate_statistics([])
        
        self.assertEqual(stats["count"], 0)
        self.assertEqual(stats["min"], 0)
        self.assertEqual(stats["max"], 0)
        self.assertEqual(stats["mean"], 0)
        self.assertEqual(stats["p50"], 0)
        self.assertEqual(stats["p95"], 0)
        self.assertEqual(stats["p99"], 0)
    
    def test_save_latency_stats(self):
        """Test saving latency statistics to file."""
        stats = {
            "count": 5,
            "p50": 200,
            "p95": 300,
            "p99": 300,
            "min": 100,
            "max": 300,
            "mean": 200.0,
            "window_size": "5 samples"
        }
        
        save_latency_stats(stats, self.stats_file)
        
        # Verify file was created
        self.assertTrue(os.path.exists(self.stats_file))
        
        # Verify file contains correct data
        with open(self.stats_file, 'r') as f:
            saved_data = json.load(f)
        
        self.assertEqual(saved_data["source"], "real_metrics")
        self.assertEqual(saved_data["collection_method"], "logs_and_redis")
        self.assertIn("timestamp", saved_data)
        self.assertEqual(saved_data["statistics"], stats)
    
    def test_collect_from_logs_missing_file(self):
        """Test collecting from missing log file."""
        latencies = collect_from_logs("nonexistent_file.log")
        self.assertEqual(latencies, [])
    
    def test_collect_from_logs_empty_file(self):
        """Test collecting from empty log file."""
        with open(self.log_file, 'w') as f:
            f.write("")
        
        latencies = collect_from_logs(self.log_file)
        self.assertEqual(latencies, [])
    
    def test_calculate_statistics_single_value(self):
        """Test statistics calculation with single value."""
        latencies = [{"ms": 150, "poll_id": "1"}]
        
        stats = calculate_statistics(latencies)
        
        self.assertEqual(stats["count"], 1)
        self.assertEqual(stats["min"], 150)
        self.assertEqual(stats["max"], 150)
        self.assertEqual(stats["mean"], 150.0)
        self.assertEqual(stats["p50"], 150)
        self.assertEqual(stats["p95"], 150)
        self.assertEqual(stats["p99"], 150)


if __name__ == "__main__":
    unittest.main()
