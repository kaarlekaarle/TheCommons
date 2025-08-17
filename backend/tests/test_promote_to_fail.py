#!/usr/bin/env python3
"""
Test Promote to Fail

Tests the promote-to-fail guard functionality for constitutional red-flags.
"""

import os
import sys
import json
import tempfile
import unittest
from unittest.mock import patch
from pathlib import Path

# Add scripts to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', 'scripts'))

from promote_to_fail import (
    load_warnings_ledger,
    check_visibility_regression,
    check_override_latency_regression,
    check_promote_to_fail_conditions
)


class TestPromoteToFail(unittest.TestCase):
    """Test promote-to-fail functionality."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.test_dir = tempfile.mkdtemp()
        self.warnings_file = os.path.join(self.test_dir, "test_warnings.json")
    
    def tearDown(self):
        """Clean up test fixtures."""
        import shutil
        shutil.rmtree(self.test_dir)
    
    def test_check_visibility_regression(self):
        """Test visibility regression detection."""
        warnings = [
            {
                "summary": "Delegation chain visibility decreased",
                "details": "Chain visibility drop detected",
                "severity": "HIGH"
            },
            {
                "summary": "Normal warning",
                "details": "No visibility issues",
                "severity": "WARNING"
            }
        ]
        
        # Should detect visibility regression
        result = check_visibility_regression(warnings)
        self.assertIsNotNone(result)
        self.assertIn("Visibility regression detected", result)
        
        # Should not detect with low severity
        warnings[0]["severity"] = "LOW"
        result = check_visibility_regression(warnings)
        self.assertIsNone(result)
    
    def test_check_override_latency_regression(self):
        """Test override latency regression detection."""
        warnings = [
            {
                "cascade_signals": ["#2"],
                "severity": "CRITICAL",
                "details": "Override latency 1800ms detected"
            },
            {
                "cascade_signals": ["#1"],
                "severity": "HIGH",
                "details": "Other issue"
            }
        ]
        
        # Should detect latency regression
        result = check_override_latency_regression(warnings)
        self.assertIsNotNone(result)
        self.assertIn("Override latency regression", result)
        self.assertIn("1800ms >= 1600ms", result)
        
        # Should not detect with low latency
        warnings[0]["details"] = "Override latency 1500ms detected"
        result = check_override_latency_regression(warnings)
        self.assertIsNone(result)  # Should not detect because latency < 1600ms
        
        # Should not detect with different signal
        warnings[0]["cascade_signals"] = ["#1"]
        result = check_override_latency_regression(warnings)
        self.assertIsNone(result)
        
        # Test with HIGH severity and high latency
        warnings[0]["cascade_signals"] = ["#2"]
        warnings[0]["severity"] = "HIGH"
        warnings[0]["details"] = "Override latency 1800ms detected"
        result = check_override_latency_regression(warnings)
        self.assertIsNotNone(result)
        self.assertIn("1800ms >= 1600ms", result)
    
    def test_check_promote_to_fail_conditions(self):
        """Test overall promote-to-fail conditions."""
        warnings = [
            {
                "summary": "Delegation chain visibility decreased",
                "details": "Chain visibility drop detected",
                "severity": "HIGH"
            },
            {
                "cascade_signals": ["#2"],
                "severity": "CRITICAL",
                "details": "Override latency 1800ms detected"
            }
        ]
        
        failures = check_promote_to_fail_conditions(warnings)
        self.assertEqual(len(failures), 2)
        self.assertIn("Visibility regression", failures[0])
        self.assertIn("Override latency regression", failures[1])
    
    def test_load_warnings_ledger(self):
        """Test loading warnings ledger."""
        # Test with missing file
        warnings = load_warnings_ledger("nonexistent_file.json")
        self.assertEqual(warnings, [])
        
        # Test with valid file
        test_warnings = [
            {
                "summary": "Test warning",
                "severity": "WARNING"
            }
        ]
        
        with open(self.warnings_file, 'w') as f:
            json.dump(test_warnings, f)
        
        warnings = load_warnings_ledger(self.warnings_file)
        self.assertEqual(len(warnings), 1)
        self.assertEqual(warnings[0]["summary"], "Test warning")
    
    @patch('sys.exit')
    def test_main_with_red_flags(self, mock_exit):
        """Test main function with red-flag conditions."""
        # Create warnings with red-flags
        test_warnings = [
            {
                "summary": "Delegation chain visibility decreased",
                "details": "Chain visibility drop detected",
                "severity": "HIGH"
            }
        ]
        
        with open(self.warnings_file, 'w') as f:
            json.dump(test_warnings, f)
        
        # Mock command line arguments
        with patch('sys.argv', ['promote_to_fail.py', '--warnings', self.warnings_file]):
            from promote_to_fail import main
            main()
        
        # Should exit with code 20
        mock_exit.assert_called_with(20)
    
    @patch('sys.exit')
    def test_main_with_override(self, mock_exit):
        """Test main function with override flag."""
        # Create warnings with red-flags
        test_warnings = [
            {
                "summary": "Delegation chain visibility decreased",
                "details": "Chain visibility drop detected",
                "severity": "HIGH"
            }
        ]
        
        with open(self.warnings_file, 'w') as f:
            json.dump(test_warnings, f)
        
        # Mock command line arguments with override
        with patch('sys.argv', ['promote_to_fail.py', '--warnings', self.warnings_file, '--override']):
            from promote_to_fail import main
            main()
        
        # Should exit with code 0 (override allows build to continue)
        mock_exit.assert_called_with(0)
    
    @patch('sys.exit')
    def test_main_no_red_flags(self, mock_exit):
        """Test main function with no red-flag conditions."""
        # Create warnings without red-flags
        test_warnings = [
            {
                "summary": "Normal warning",
                "details": "No red-flags here",
                "severity": "LOW"
            }
        ]
        
        with open(self.warnings_file, 'w') as f:
            json.dump(test_warnings, f)
        
        # Mock command line arguments
        with patch('sys.argv', ['promote_to_fail.py', '--warnings', self.warnings_file]):
            from promote_to_fail import main
            main()
        
        # Should exit with code 0 (no red-flags)
        mock_exit.assert_called_with(0)


if __name__ == "__main__":
    unittest.main()
