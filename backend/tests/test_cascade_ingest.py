#!/usr/bin/env python3
"""
Test Cascade Ingestion

Tests the cascade ingestion functionality for warnings ledger integration.
"""

import os
import sys
import json
import tempfile
import unittest
from pathlib import Path

# Add backend/scripts to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'scripts'))

from constitutional_warnings_ingest import (
    load_warnings_ledger,
    save_warnings_ledger,
    normalize_cascade_to_warning,
    deduplicate_warnings,
    ingest_cascade_to_ledger
)


class TestCascadeIngest(unittest.TestCase):
    """Test cascade ingestion functionality."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.test_dir = tempfile.mkdtemp()
        self.cascade_file = os.path.join(self.test_dir, "test_cascade.json")
        self.ledger_file = os.path.join(self.test_dir, "test_warnings.json")
        
        # Sample cascade data with Rule B BLOCK
        self.sample_cascade = {
            "timestamp": "2025-08-17T15:00:00.000000",
            "summary": "CASCADE: rule=B, signals=[#2=CRITICAL(2100ms), #3=HIGH(7flows)], window=7d, decision=BLOCK",
            "exit_code": 10,
            "cascade_results": [
                {
                    "rule_id": "B",
                    "decision": "block",
                    "rationale": "Opacity + complexity",
                    "window_days": 7,
                    "triggered_signals": [
                        {
                            "id": "#2",
                            "severity": "critical",
                            "value_ms": 2100,
                            "ts": "2025-08-17T15:00:00.000000"
                        },
                        {
                            "id": "#3",
                            "severity": "high",
                            "flows": 7,
                            "module": "delegations",
                            "ts": "2025-08-17T15:00:00.000000"
                        }
                    ]
                }
            ]
        }
    
    def tearDown(self):
        """Clean up test fixtures."""
        import shutil
        shutil.rmtree(self.test_dir)
    
    def test_normalize_cascade_to_warning(self):
        """Test cascade to warning normalization."""
        warnings = normalize_cascade_to_warning(self.sample_cascade)
        
        self.assertEqual(len(warnings), 1)
        warning = warnings[0]
        
        # Check required fields
        self.assertEqual(warning["phase"], "6.4")
        self.assertEqual(warning["component"], "constitutional_cascade_detector")
        self.assertEqual(warning["category"], "cascade_rule_b")
        self.assertEqual(warning["severity"], "critical")
        self.assertEqual(warning["cascade_rule_id"], "B")
        self.assertEqual(warning["cascade_decision"], "block")
        self.assertEqual(warning["cascade_signals"], ["#2", "#3"])
        
        # Check summary and details
        self.assertIn("Cascade Rule B triggered", warning["summary"])
        self.assertIn("Opacity + complexity", warning["summary"])
        self.assertIn("Decision: BLOCK", warning["details"])
        self.assertIn("Signals: 2", warning["details"])
    
    def test_deduplicate_warnings(self):
        """Test warning deduplication."""
        # Create duplicate warnings
        warnings = [
            {
                "cascade_rule_id": "B",
                "cascade_signals": ["#2", "#3"],
                "timestamp": "2025-08-17T15:00:00.000000"
            },
            {
                "cascade_rule_id": "B",
                "cascade_signals": ["#2", "#3"],
                "timestamp": "2025-08-17T15:00:00.000000"  # Same minute
            },
            {
                "cascade_rule_id": "B",
                "cascade_signals": ["#2", "#3"],
                "timestamp": "2025-08-17T15:01:00.000000"  # Different minute
            }
        ]
        
        unique_warnings = deduplicate_warnings(warnings)
        self.assertEqual(len(unique_warnings), 2)  # Should dedupe the first two
    
    def test_ingest_cascade_to_ledger(self):
        """Test full cascade ingestion to ledger."""
        # Save sample cascade data
        with open(self.cascade_file, 'w') as f:
            json.dump(self.sample_cascade, f)
        
        # Create empty ledger
        save_warnings_ledger(self.ledger_file, [])
        
        # Run ingestion
        ingest_cascade_to_ledger(self.cascade_file, self.ledger_file, append=True)
        
        # Verify ledger was updated
        warnings = load_warnings_ledger(self.ledger_file)
        self.assertEqual(len(warnings), 1)
        
        warning = warnings[0]
        self.assertEqual(warning["cascade_rule_id"], "B")
        self.assertEqual(warning["severity"], "critical")
    
    def test_ingest_cascade_to_ledger_replace(self):
        """Test cascade ingestion with replace mode."""
        # Save sample cascade data
        with open(self.cascade_file, 'w') as f:
            json.dump(self.sample_cascade, f)
        
        # Create ledger with existing warnings
        existing_warnings = [
            {
                "timestamp": "2025-08-17T14:00:00.000000",
                "summary": "Existing warning",
                "severity": "warning"
            }
        ]
        save_warnings_ledger(self.ledger_file, existing_warnings)
        
        # Run ingestion with replace
        ingest_cascade_to_ledger(self.cascade_file, self.ledger_file, append=False)
        
        # Verify ledger was replaced
        warnings = load_warnings_ledger(self.ledger_file)
        self.assertEqual(len(warnings), 1)  # Only cascade warning, no existing warnings
        
        warning = warnings[0]
        self.assertEqual(warning["cascade_rule_id"], "B")
    
    def test_load_warnings_ledger_missing(self):
        """Test loading missing warnings ledger."""
        warnings = load_warnings_ledger("nonexistent_file.json")
        self.assertEqual(warnings, [])
    
    def test_save_warnings_ledger(self):
        """Test saving warnings ledger."""
        test_warnings = [
            {
                "timestamp": "2025-08-17T15:00:00.000000",
                "summary": "Test warning",
                "severity": "warning"
            }
        ]
        
        save_warnings_ledger(self.ledger_file, test_warnings)
        
        # Verify file was created and contains correct data
        self.assertTrue(os.path.exists(self.ledger_file))
        
        with open(self.ledger_file, 'r') as f:
            saved_warnings = json.load(f)
        
        self.assertEqual(len(saved_warnings), 1)
        self.assertEqual(saved_warnings[0]["summary"], "Test warning")


if __name__ == "__main__":
    unittest.main()
