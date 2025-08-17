#!/usr/bin/env python3
"""
Test Amendment: Override Latency Violation

This amendment intentionally introduces slow override latency to test
the constitutional blocking rules. This should FAIL validation.
"""

import time
import asyncio

class SlowDelegationOverride:
    """Slow delegation override that violates user intent supremacy."""
    
    def __init__(self):
        self.processing_delay = 3.0  # ❌ VIOLATION: 3 seconds > 2s threshold
    
    async def override_delegation(self, user_id, delegation_id):
        """❌ VIOLATION: Override latency >2.0 seconds"""
        # Simulate slow processing
        await asyncio.sleep(self.processing_delay)  # 3 second delay
        
        # Additional slow operations
        time.sleep(0.5)  # Blocking operation
        
        return {"status": "overridden", "latency": "3000ms"}
    
    def resolve_delegation_chain(self):
        """❌ VIOLATION: Chain resolution >1.0 seconds"""
        time.sleep(1.5)  # 1.5 seconds > 1s threshold
        return {"chain_resolved": True, "latency": "1500ms"}
    
    def log_transparency_event(self):
        """❌ VIOLATION: Transparency logging >0.5 seconds"""
        time.sleep(0.8)  # 0.8 seconds > 0.5s threshold
        return {"logged": True, "latency": "800ms"}

class PerformanceViolation:
    """Performance violations that affect constitutional guarantees."""
    
    def __init__(self):
        self.override_latency_ms = 2500  # ❌ VIOLATION: 2.5 seconds
    
    def check_user_intent_override(self):
        """❌ VIOLATION: User intent override >1.0 seconds"""
        time.sleep(1.2)  # 1.2 seconds > 1s threshold
        return {"user_intent": "overridden", "latency": "1200ms"}

# ❌ VIOLATION: Comments indicating performance issues
# This amendment introduces slow override latency
# User intent supremacy is compromised by delays
# Override latency exceeds constitutional limits
