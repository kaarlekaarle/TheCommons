"""Delegation Constitutional Test Suite.

This package contains comprehensive tests for the Delegation Constitution,
ensuring all Phase 1 and Phase 2 guardrails are properly enforced.

Test Categories:
- Circulation & Decay: Power must circulate, no permanents
- Values-as-Delegates: People, values, and ideas as delegation targets  
- Interruption & Overrides: User intent always wins, instantly
- Anti-Hierarchy & Feedback: Prevent concentration, repair loops
- Transparency & Anonymity: Full trace visibility with optional masking
- Constitutional Compliance: No bypasses, comprehensive coverage
"""

__all__ = [
    "test_circulation_decay",
    "test_values_delegates", 
    "test_interruptions",
    "test_anti_hierarchy",
    "test_transparency_anonymity",
    "test_constitutional_compliance"
]
