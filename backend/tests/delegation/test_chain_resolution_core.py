"""Unit tests for pure chain resolution core.

Tests that the pure chain resolution logic produces the same outputs
and maintains the same trace as the original implementation.
"""

import pytest
from datetime import datetime, timedelta
from uuid import uuid4

from backend.services.delegation.chain_resolution import ChainResolutionCore
from backend.models.delegation import Delegation, DelegationMode


class TestChainResolutionCore:
    """Test pure chain resolution logic."""
    
    def test_resolve_simple_chain(self):
        """Test resolving a simple 2-hop delegation chain."""
        # Create test users
        user1_id = uuid4()
        user2_id = uuid4()
        user3_id = uuid4()
        
        # Create delegations: user1 -> user2 -> user3
        delegation1 = Delegation()
        delegation1.id = uuid4()
        delegation1.delegator_id = user1_id
        delegation1.delegatee_id = user2_id
        delegation1.mode = DelegationMode.FLEXIBLE_DOMAIN
        delegation1.start_date = datetime.utcnow()
        delegation1.created_at = datetime.utcnow()
        
        delegation2 = Delegation()
        delegation2.id = uuid4()
        delegation2.delegator_id = user2_id
        delegation2.delegatee_id = user3_id
        delegation2.mode = DelegationMode.FLEXIBLE_DOMAIN
        delegation2.start_date = datetime.utcnow()
        delegation2.created_at = datetime.utcnow()
        
        available_delegations = [delegation1, delegation2]
        
        # Resolve chain
        chain = ChainResolutionCore.resolve_chain_from_delegations(
            user1_id, available_delegations
        )
        
        # Verify chain
        assert len(chain) == 2
        assert chain[0].id == delegation1.id
        assert chain[0].delegator_id == user1_id
        assert chain[0].delegatee_id == user2_id
        assert chain[1].id == delegation2.id
        assert chain[1].delegator_id == user2_id
        assert chain[1].delegatee_id == user3_id
    
    def test_resolve_chain_with_poll_scope(self):
        """Test resolving chain with poll-specific scope."""
        # Create test users and poll
        user1_id = uuid4()
        user2_id = uuid4()
        poll_id = uuid4()
        
        # Create poll-specific delegation
        delegation = Delegation()
        delegation.id = uuid4()
        delegation.delegator_id = user1_id
        delegation.delegatee_id = user2_id
        delegation.mode = DelegationMode.FLEXIBLE_DOMAIN
        delegation.poll_id = poll_id
        delegation.start_date = datetime.utcnow()
        delegation.created_at = datetime.utcnow()
        
        available_delegations = [delegation]
        
        # Resolve chain with poll scope
        chain = ChainResolutionCore.resolve_chain_from_delegations(
            user1_id, available_delegations, poll_id=poll_id
        )
        
        # Verify chain
        assert len(chain) == 1
        assert chain[0].id == delegation.id
        assert chain[0].poll_id == poll_id
    
    def test_resolve_chain_with_hybrid_mode_priority(self):
        """Test that hybrid mode delegations are prioritized."""
        # Create test users
        user1_id = uuid4()
        user2_id = uuid4()
        user3_id = uuid4()
        
        # Create specific delegation (newer)
        specific_delegation = Delegation()
        specific_delegation.id = uuid4()
        specific_delegation.delegator_id = user1_id
        specific_delegation.delegatee_id = user2_id
        specific_delegation.mode = DelegationMode.FLEXIBLE_DOMAIN
        specific_delegation.poll_id = uuid4()
        specific_delegation.start_date = datetime.utcnow()
        specific_delegation.created_at = datetime.utcnow() + timedelta(hours=1)
        
        # Create hybrid delegation (older, but should be prioritized)
        hybrid_delegation = Delegation()
        hybrid_delegation.id = uuid4()
        hybrid_delegation.delegator_id = user1_id
        hybrid_delegation.delegatee_id = user3_id
        hybrid_delegation.mode = DelegationMode.HYBRID_SEED
        hybrid_delegation.start_date = datetime.utcnow()
        hybrid_delegation.created_at = datetime.utcnow()
        
        available_delegations = [specific_delegation, hybrid_delegation]
        
        # Resolve chain (should prioritize hybrid)
        chain = ChainResolutionCore.resolve_chain_from_delegations(
            user1_id, available_delegations
        )
        
        # Verify hybrid delegation is chosen
        assert len(chain) == 1
        assert chain[0].id == hybrid_delegation.id
        assert chain[0].mode == DelegationMode.HYBRID_SEED
        assert chain[0].delegatee_id == user3_id
    
    def test_resolve_chain_with_expired_legacy_delegation(self):
        """Test that expired legacy delegations stop chain resolution."""
        # Create test users
        user1_id = uuid4()
        user2_id = uuid4()
        user3_id = uuid4()
        
        # Create expired legacy delegation
        expired_delegation = Delegation()
        expired_delegation.id = uuid4()
        expired_delegation.delegator_id = user1_id
        expired_delegation.delegatee_id = user2_id
        expired_delegation.mode = DelegationMode.LEGACY_FIXED_TERM
        expired_delegation.start_date = datetime.utcnow() - timedelta(days=365)
        expired_delegation.legacy_term_ends_at = datetime.utcnow() - timedelta(days=1)
        expired_delegation.created_at = datetime.utcnow() - timedelta(days=365)
        
        # Create delegation after expired one
        next_delegation = Delegation()
        next_delegation.id = uuid4()
        next_delegation.delegator_id = user2_id
        next_delegation.delegatee_id = user3_id
        next_delegation.mode = DelegationMode.FLEXIBLE_DOMAIN
        next_delegation.start_date = datetime.utcnow()
        next_delegation.created_at = datetime.utcnow()
        
        available_delegations = [expired_delegation, next_delegation]
        
        # Resolve chain
        chain = ChainResolutionCore.resolve_chain_from_delegations(
            user1_id, available_delegations
        )
        
        # Verify chain stops at expired delegation
        assert len(chain) == 1
        assert chain[0].id == expired_delegation.id
        assert chain[0].is_legacy_fixed_term
    
    def test_resolve_chain_with_max_depth_limit(self):
        """Test that chain resolution respects max depth limit."""
        # Create test users for a long chain
        users = [uuid4() for _ in range(15)]  # More than max_depth=10
        
        # Create delegations: user0 -> user1 -> user2 -> ... -> user14
        delegations = []
        for i in range(len(users) - 1):
            delegation = Delegation()
            delegation.id = uuid4()
            delegation.delegator_id = users[i]
            delegation.delegatee_id = users[i + 1]
            delegation.mode = DelegationMode.FLEXIBLE_DOMAIN
            delegation.start_date = datetime.utcnow()
            delegation.created_at = datetime.utcnow()
            delegations.append(delegation)
        
        # Resolve chain with max_depth=10
        chain = ChainResolutionCore.resolve_chain_from_delegations(
            users[0], delegations, max_depth=10
        )
        
        # Verify chain is limited to max_depth
        assert len(chain) == 10
        assert chain[0].delegator_id == users[0]
        assert chain[9].delegatee_id == users[10]
    
    def test_serialize_and_deserialize_chain(self):
        """Test chain serialization and deserialization."""
        # Create test delegation
        delegation = Delegation()
        delegation.id = uuid4()
        delegation.delegator_id = uuid4()
        delegation.delegatee_id = uuid4()
        delegation.mode = DelegationMode.FLEXIBLE_DOMAIN
        delegation.poll_id = uuid4()
        delegation.start_date = datetime.utcnow()
        delegation.end_date = datetime.utcnow() + timedelta(days=30)
        delegation.legacy_term_ends_at = datetime.utcnow() + timedelta(days=365)
        delegation.created_at = datetime.utcnow()
        
        chain = [delegation]
        
        # Serialize chain
        serialized = ChainResolutionCore.serialize_chain(chain)
        
        # Verify serialized format
        assert len(serialized) == 1
        assert serialized[0]["id"] == str(delegation.id)
        assert serialized[0]["delegator_id"] == str(delegation.delegator_id)
        assert serialized[0]["delegatee_id"] == str(delegation.delegatee_id)
        assert serialized[0]["mode"] == delegation.mode
        assert serialized[0]["poll_id"] == str(delegation.poll_id)
        
        # Deserialize chain
        deserialized = ChainResolutionCore.deserialize_chain(serialized)
        
        # Verify deserialized chain matches original
        assert len(deserialized) == 1
        assert deserialized[0].id == delegation.id
        assert deserialized[0].delegator_id == delegation.delegator_id
        assert deserialized[0].delegatee_id == delegation.delegatee_id
        assert deserialized[0].mode == delegation.mode
        assert deserialized[0].poll_id == delegation.poll_id
    
    def test_resolve_chain_with_no_delegations(self):
        """Test resolving chain when no delegations are available."""
        user_id = uuid4()
        available_delegations = []
        
        chain = ChainResolutionCore.resolve_chain_from_delegations(
            user_id, available_delegations
        )
        
        assert len(chain) == 0
    
    def test_resolve_chain_with_inactive_delegations(self):
        """Test that inactive delegations are ignored."""
        user1_id = uuid4()
        user2_id = uuid4()
        
        # Create inactive delegation (revoked)
        inactive_delegation = Delegation()
        inactive_delegation.id = uuid4()
        inactive_delegation.delegator_id = user1_id
        inactive_delegation.delegatee_id = user2_id
        inactive_delegation.mode = DelegationMode.FLEXIBLE_DOMAIN
        inactive_delegation.start_date = datetime.utcnow()
        inactive_delegation.revoked_at = datetime.utcnow()  # Revoked
        inactive_delegation.created_at = datetime.utcnow()
        
        available_delegations = [inactive_delegation]
        
        chain = ChainResolutionCore.resolve_chain_from_delegations(
            user1_id, available_delegations
        )
        
        # Should return empty chain since delegation is inactive
        assert len(chain) == 0
