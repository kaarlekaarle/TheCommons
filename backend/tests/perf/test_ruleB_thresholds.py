#!/usr/bin/env python3
"""
Unit tests for Rule B threshold logic with unified thresholds and grace periods.
"""

import json
import tempfile
import os
from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock

import pytest

from backend.scripts.constitutional_cascade_detector import ConstitutionalCascadeDetector


class TestRuleBThresholds:
    """Test Rule B threshold logic with unified thresholds."""

    def setup_method(self):
        """Set up test fixtures."""
        # Create a temporary config file
        self.config_data = {
            "rules": {
                "B": {
                    "description": "Opacity + complexity",
                    "signals": ["#2", "#3"],
                    "window_days": 7,
                    "modes": {
                        "shadow": "info",
                        "warn": "warn",
                        "enforce": "block"
                    }
                }
            },
            "thresholds": {
                "override_latency_ms": {
                    "warn": 1200,
                    "high": 1500,
                    "critical": 2000
                }
            }
        }
        
        # Create perf thresholds config
        self.perf_thresholds_data = {
            "override_latency": {
                "p95_slo_ms": 1500,
                "grace_ms": 50,
                "stale_hours": 24
            }
        }

    def create_latency_file(self, p95_ms, p99_ms=2000, cache_hit_rate=80.0, timestamp=None):
        """Create a temporary latency file with specified values."""
        if timestamp is None:
            timestamp = datetime.now().isoformat()
        
        data = {
            "override_latency_ms": p95_ms,
            "p50_ms": p95_ms * 0.4,  # Rough estimate
            "p95_ms": p95_ms,
            "p99_ms": p99_ms,
            "total_requests": 400,
            "successful_requests": 398,
            "errors": 2,
            "cache_hit_rate": cache_hit_rate,
            "fastpath_hit_rate": 65.0,
            "timestamp": timestamp
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(data, f)
            return f.name

    @patch('backend.scripts.constitutional_cascade_detector.ConstitutionalCascadeDetector._load_config')
    @patch('backend.scripts.constitutional_cascade_detector.ConstitutionalCascadeDetector._load_perf_thresholds')
    def test_p95_1499_info(self, mock_load_perf, mock_load_config):
        """Test p95=1499ms → INFO severity."""
        mock_load_config.return_value = self.config_data
        mock_load_perf.return_value = self.perf_thresholds_data
        
        detector = ConstitutionalCascadeDetector()
        latency_file = self.create_latency_file(1499)
        
        try:
            with patch('os.path.exists', return_value=True):
                with patch('builtins.open', create=True) as mock_open:
                    mock_open.return_value.__enter__.return_value.read.return_value = open(latency_file).read()
                    
                    signal = detector.collect_signal_2_override_latency()
                    
                    assert signal is not None
                    assert signal["severity"] == "info"
                    assert signal["is_blocking"] is False
                    assert signal["p95_ms"] == 1499
                    assert signal["slo_ms"] == 1500
                    assert signal["grace_ms"] == 50
                    assert signal["effective_block_ms"] == 1550
        finally:
            os.unlink(latency_file)

    @patch('backend.scripts.constitutional_cascade_detector.ConstitutionalCascadeDetector._load_config')
    @patch('backend.scripts.constitutional_cascade_detector.ConstitutionalCascadeDetector._load_perf_thresholds')
    def test_p95_1500_high(self, mock_load_perf, mock_load_config):
        """Test p95=1500ms → HIGH severity (non-blocking)."""
        mock_load_config.return_value = self.config_data
        mock_load_perf.return_value = self.perf_thresholds_data
        
        detector = ConstitutionalCascadeDetector()
        latency_file = self.create_latency_file(1500)
        
        try:
            with patch('os.path.exists', return_value=True):
                with patch('builtins.open', create=True) as mock_open:
                    mock_open.return_value.__enter__.return_value.read.return_value = open(latency_file).read()
                    
                    signal = detector.collect_signal_2_override_latency()
                    
                    assert signal is not None
                    assert signal["severity"] == "high"
                    assert signal["is_blocking"] is False
                    assert signal["p95_ms"] == 1500
                    assert signal["slo_ms"] == 1500
                    assert signal["grace_ms"] == 50
                    assert signal["effective_block_ms"] == 1550
        finally:
            os.unlink(latency_file)

    @patch('backend.scripts.constitutional_cascade_detector.ConstitutionalCascadeDetector._load_config')
    @patch('backend.scripts.constitutional_cascade_detector.ConstitutionalCascadeDetector._load_perf_thresholds')
    def test_p95_1549_high(self, mock_load_perf, mock_load_config):
        """Test p95=1549ms → HIGH severity (non-blocking)."""
        mock_load_config.return_value = self.config_data
        mock_load_perf.return_value = self.perf_thresholds_data
        
        detector = ConstitutionalCascadeDetector()
        latency_file = self.create_latency_file(1549)
        
        try:
            with patch('os.path.exists', return_value=True):
                with patch('builtins.open', create=True) as mock_open:
                    mock_open.return_value.__enter__.return_value.read.return_value = open(latency_file).read()
                    
                    signal = detector.collect_signal_2_override_latency()
                    
                    assert signal is not None
                    assert signal["severity"] == "high"
                    assert signal["is_blocking"] is False
                    assert signal["p95_ms"] == 1549
                    assert signal["slo_ms"] == 1500
                    assert signal["grace_ms"] == 50
                    assert signal["effective_block_ms"] == 1550
        finally:
            os.unlink(latency_file)

    @patch('backend.scripts.constitutional_cascade_detector.ConstitutionalCascadeDetector._load_config')
    @patch('backend.scripts.constitutional_cascade_detector.ConstitutionalCascadeDetector._load_perf_thresholds')
    def test_p95_1550_critical(self, mock_load_perf, mock_load_config):
        """Test p95=1550ms → CRITICAL severity (blocking)."""
        mock_load_config.return_value = self.config_data
        mock_load_perf.return_value = self.perf_thresholds_data
        
        detector = ConstitutionalCascadeDetector()
        latency_file = self.create_latency_file(1550)
        
        try:
            with patch('os.path.exists', return_value=True):
                with patch('builtins.open', create=True) as mock_open:
                    mock_open.return_value.__enter__.return_value.read.return_value = open(latency_file).read()
                    
                    signal = detector.collect_signal_2_override_latency()
                    
                    assert signal is not None
                    assert signal["severity"] == "critical"
                    assert signal["is_blocking"] is True
                    assert signal["p95_ms"] == 1550
                    assert signal["slo_ms"] == 1500
                    assert signal["grace_ms"] == 50
                    assert signal["effective_block_ms"] == 1550
        finally:
            os.unlink(latency_file)

    @patch('backend.scripts.constitutional_cascade_detector.ConstitutionalCascadeDetector._load_config')
    @patch('backend.scripts.constitutional_cascade_detector.ConstitutionalCascadeDetector._load_perf_thresholds')
    def test_stale_snapshot_info(self, mock_load_perf, mock_load_config):
        """Test stale snapshot (>24h) → INFO with stale note."""
        mock_load_config.return_value = self.config_data
        mock_load_perf.return_value = self.perf_thresholds_data
        
        detector = ConstitutionalCascadeDetector()
        
        # Create a file with old timestamp (25 hours ago)
        old_timestamp = (datetime.now() - timedelta(hours=25)).isoformat()
        latency_file = self.create_latency_file(1600, timestamp=old_timestamp)
        
        try:
            with patch('os.path.exists', return_value=True):
                with patch('builtins.open', create=True) as mock_open:
                    mock_open.return_value.__enter__.return_value.read.return_value = open(latency_file).read()
                    
                    signal = detector.collect_signal_2_override_latency()
                    
                    assert signal is not None
                    assert signal["severity"] == "info"
                    assert signal["is_blocking"] is False
                    assert signal["value"] == "STALE"
                    assert "stale" in signal["description"].lower()
                    assert signal["file_age_hours"] > 24
        finally:
            os.unlink(latency_file)

    @patch('backend.scripts.constitutional_cascade_detector.ConstitutionalCascadeDetector._load_config')
    @patch('backend.scripts.constitutional_cascade_detector.ConstitutionalCascadeDetector._load_perf_thresholds')
    def test_warn_threshold_1400(self, mock_load_perf, mock_load_config):
        """Test p95=1400ms → WARN severity (early heads-up)."""
        mock_load_config.return_value = self.config_data
        mock_load_perf.return_value = self.perf_thresholds_data
        
        detector = ConstitutionalCascadeDetector()
        latency_file = self.create_latency_file(1400)
        
        try:
            with patch('os.path.exists', return_value=True):
                with patch('builtins.open', create=True) as mock_open:
                    mock_open.return_value.__enter__.return_value.read.return_value = open(latency_file).read()
                    
                    signal = detector.collect_signal_2_override_latency()
                    
                    assert signal is not None
                    assert signal["severity"] == "warn"
                    assert signal["is_blocking"] is False
                    assert signal["p95_ms"] == 1400
                    assert signal["slo_ms"] == 1500
                    assert signal["grace_ms"] == 50
                    assert signal["effective_block_ms"] == 1550
        finally:
            os.unlink(latency_file)

    @patch('backend.scripts.constitutional_cascade_detector.ConstitutionalCascadeDetector._load_config')
    @patch('backend.scripts.constitutional_cascade_detector.ConstitutionalCascadeDetector._load_perf_thresholds')
    def test_latency_source_logging(self, mock_load_perf, mock_load_config):
        """Test that latency source and timestamp are properly logged."""
        mock_load_config.return_value = self.config_data
        mock_load_perf.return_value = self.perf_thresholds_data
        
        detector = ConstitutionalCascadeDetector()
        latency_file = self.create_latency_file(1500)
        
        try:
            with patch('os.path.exists', return_value=True):
                with patch('builtins.open', create=True) as mock_open:
                    mock_open.return_value.__enter__.return_value.read.return_value = open(latency_file).read()
                    
                    signal = detector.collect_signal_2_override_latency()
                    
                    assert signal is not None
                    assert "latency_source" in signal
                    assert "latency_timestamp" in signal
                    assert signal["latency_source"] is not None
                    assert signal["latency_timestamp"] is not None
        finally:
            os.unlink(latency_file)


if __name__ == "__main__":
    pytest.main([__file__])
