"""Performance tests for override latency fastpath.

Tests that the delegation chain resolution meets SLO requirements:
- First request (cold): <= 1.5s
- Second request (warm): <= 400ms
- Cache invalidation works correctly
"""

import pytest
import asyncio
import time
from uuid import uuid4
from datetime import datetime, timedelta

from backend.models.delegation import Delegation, DelegationMode
from backend.models.user import User
from backend.models.poll import Poll
from backend.services.delegation import DelegationService
from backend.database import get_db


class TestOverrideLatencyFastpath:
    @pytest.mark.asyncio
    async def test_3_hop_chain_cold_warm_performance(self, db_session):
        """Test 3-hop delegation chain performance with cold and warm requests."""
        # Create test users
        users = []
        for i in range(4):
            user = User(
                username=f"testuser{i}",
                email=f"test{i}@example.com",
                display_name=f"Test User {i}",
            )
            db_session.add(user)
            users.append(user)
        await db_session.flush()
        
        # Create test poll
        poll = Poll(
            title="Performance Test Poll",
            description="Test poll for override latency",
            created_by=users[0].id,
        )
        db_session.add(poll)
        await db_session.flush()
        
        # Create 3-hop delegation chain: user0 -> user1 -> user2 -> user3
        delegations = []
        for i in range(3):
            delegation = Delegation(
                delegator_id=users[i].id,
                delegatee_id=users[i + 1].id,
                mode=DelegationMode.FLEXIBLE_DOMAIN,
                poll_id=poll.id,
                start_date=datetime.utcnow(),
            )
            db_session.add(delegation)
            delegations.append(delegation)
        await db_session.flush()
        
        # Test cold request (first time)
        delegation_service = DelegationService(db_session)
        
        cold_start = time.time()
        chain = await delegation_service.resolve_delegation_chain(
            users[0].id, poll.id
        )
        cold_time = time.time() - cold_start
        
        # Verify chain is correct
        assert len(chain) == 3
        assert chain[0].delegator_id == users[0].id
        assert chain[0].delegatee_id == users[1].id
        assert chain[1].delegator_id == users[1].id
        assert chain[1].delegatee_id == users[2].id
        assert chain[2].delegator_id == users[2].id
        assert chain[2].delegatee_id == users[3].id
        
        # Test warm request (cached)
        warm_start = time.time()
        chain_warm = await delegation_service.resolve_delegation_chain(
            users[0].id, poll.id
        )
        warm_time = time.time() - warm_start
        
        # Verify warm chain is identical
        assert len(chain_warm) == 3
        assert chain_warm[0].id == chain[0].id
        assert chain_warm[1].id == chain[1].id
        assert chain_warm[2].id == chain[2].id
        
        # Performance assertions
        assert cold_time <= 1.5, f"Cold request took {cold_time:.3f}s, expected <= 1.5s"
        assert warm_time <= 0.4, f"Warm request took {warm_time:.3f}s, expected <= 0.4s"
        
        print(f"✅ Cold request: {cold_time:.3f}s")
        print(f"✅ Warm request: {warm_time:.3f}s")
    
    @pytest.mark.asyncio
    async def test_cache_invalidation_on_revoke(self, db_session):
        """Test that cache is invalidated when delegation is revoked."""
        # Create test users
        users = []
        for i in range(3):
            user = User(
                username=f"testuser{i}",
                email=f"test{i}@example.com",
                display_name=f"Test User {i}",
            )
            db_session.add(user)
            users.append(user)
        await db_session.flush()
        
        # Create test poll
        poll = Poll(
            title="Cache Invalidation Test Poll",
            description="Test poll for cache invalidation",
            created_by=users[0].id,
        )
        db_session.add(poll)
        await db_session.flush()
        
        # Create delegation: user0 -> user1
        delegation = Delegation(
            delegator_id=users[0].id,
            delegatee_id=users[1].id,
            mode=DelegationMode.FLEXIBLE_DOMAIN,
            poll_id=poll.id,
            start_date=datetime.utcnow(),
        )
        db_session.add(delegation)
        await db_session.flush()
        
        delegation_service = DelegationService(db_session)
        
        # First request - should cache
        chain1 = await delegation_service.resolve_delegation_chain(
            users[0].id, poll.id
        )
        assert len(chain1) == 1
        assert chain1[0].id == delegation.id
        
        # Revoke delegation
        await delegation_service.revoke_delegation(delegation.id)
        
        # Second request - should be cache miss and return empty chain
        chain2 = await delegation_service.resolve_delegation_chain(
            users[0].id, poll.id
        )
        assert len(chain2) == 0
        
        print("✅ Cache invalidation on revoke works correctly")
    
    @pytest.mark.asyncio
    async def test_cache_invalidation_on_new_delegation(self, db_session):
        """Test that cache is invalidated when new delegation is created."""
        # Create test users
        users = []
        for i in range(3):
            user = User(
                username=f"testuser{i}",
                email=f"test{i}@example.com",
                display_name=f"Test User {i}",
            )
            db_session.add(user)
            users.append(user)
        await db_session.flush()
        
        # Create test poll
        poll = Poll(
            title="New Delegation Cache Test Poll",
            description="Test poll for new delegation cache invalidation",
            created_by=users[0].id,
        )
        db_session.add(poll)
        await db_session.flush()
        
        delegation_service = DelegationService(db_session)
        
        # First request - should return empty chain
        chain1 = await delegation_service.resolve_delegation_chain(
            users[0].id, poll.id
        )
        assert len(chain1) == 0
        
        # Create new delegation
        new_delegation = await delegation_service.create_delegation(
            delegator_id=users[0].id,
            delegatee_id=users[1].id,
            mode=DelegationMode.FLEXIBLE_DOMAIN,
            poll_id=poll.id,
        )
        
        # Second request - should be cache miss and return new delegation
        chain2 = await delegation_service.resolve_delegation_chain(
            users[0].id, poll.id
        )
        assert len(chain2) == 1
        assert chain2[0].id == new_delegation.id
        
        print("✅ Cache invalidation on new delegation works correctly")
    
    @pytest.mark.asyncio
    async def test_memoization_performance(self, db_session):
        """Test that memoization reduces database queries."""
        # Create test users
        users = []
        for i in range(5):
            user = User(
                username=f"testuser{i}",
                email=f"test{i}@example.com",
                display_name=f"Test User {i}",
            )
            db_session.add(user)
            users.append(user)
        await db_session.flush()
        
        # Create test poll
        poll = Poll(
            title="Memoization Test Poll",
            description="Test poll for memoization performance",
            created_by=users[0].id,
        )
        db_session.add(poll)
        await db_session.flush()
        
        # Create complex delegation chain with some users appearing multiple times
        # user0 -> user1 -> user2 -> user1 -> user3 -> user2 -> user4
        delegation_chain = [
            (users[0].id, users[1].id),
            (users[1].id, users[2].id),
            (users[2].id, users[1].id),  # user1 appears again
            (users[1].id, users[3].id),
            (users[3].id, users[2].id),  # user2 appears again
            (users[2].id, users[4].id),
        ]
        
        delegations = []
        for delegator_id, delegatee_id in delegation_chain:
            delegation = Delegation(
                delegator_id=delegator_id,
                delegatee_id=delegatee_id,
                mode=DelegationMode.FLEXIBLE_DOMAIN,
                poll_id=poll.id,
                start_date=datetime.utcnow(),
            )
            db_session.add(delegation)
            delegations.append(delegation)
        await db_session.flush()
        
        delegation_service = DelegationService(db_session)
        
        # Test chain resolution
        start_time = time.time()
        chain = await delegation_service.resolve_delegation_chain(
            users[0].id, poll.id
        )
        total_time = time.time() - start_time
        
        # Verify chain is correct (should stop at user4)
        assert len(chain) == 6
        assert chain[-1].delegatee_id == users[4].id
        
        # Performance assertion - should be fast due to memoization
        assert total_time <= 1.0, f"Memoized chain resolution took {total_time:.3f}s, expected <= 1.0s"
        
        print(f"✅ Memoization performance: {total_time:.3f}s")
    
    @pytest.mark.asyncio
    async def test_legacy_mode_performance(self, db_session):
        """Test performance with legacy mode delegations."""
        # Create test users
        users = []
        for i in range(3):
            user = User(
                username=f"testuser{i}",
                email=f"test{i}@example.com",
                display_name=f"Test User {i}",
            )
            db_session.add(user)
            users.append(user)
        await db_session.flush()
        
        # Create test poll
        poll = Poll(
            title="Legacy Mode Test Poll",
            description="Test poll for legacy mode performance",
            created_by=users[0].id,
        )
        db_session.add(poll)
        await db_session.flush()
        
        # Create legacy delegation
        legacy_delegation = Delegation(
            delegator_id=users[0].id,
            delegatee_id=users[1].id,
            mode=DelegationMode.LEGACY_FIXED_TERM,
            poll_id=poll.id,
            start_date=datetime.utcnow(),
            legacy_term_ends_at=datetime.utcnow() + timedelta(days=365),
        )
        db_session.add(legacy_delegation)
        await db_session.flush()
        
        delegation_service = DelegationService(db_session)
        
        # Test legacy delegation resolution
        start_time = time.time()
        chain = await delegation_service.resolve_delegation_chain(
            users[0].id, poll.id
        )
        total_time = time.time() - start_time
        
        # Verify chain is correct
        assert len(chain) == 1
        assert chain[0].id == legacy_delegation.id
        assert chain[0].mode == DelegationMode.LEGACY_FIXED_TERM
        
        # Performance assertion
        assert total_time <= 1.0, f"Legacy mode resolution took {total_time:.3f}s, expected <= 1.0s"
        
        print(f"✅ Legacy mode performance: {total_time:.3f}s")
    
    @pytest.mark.asyncio
    async def test_hybrid_mode_performance(self, db_session):
        """Test performance with hybrid mode delegations."""
        # Create test users
        users = []
        for i in range(3):
            user = User(
                username=f"testuser{i}",
                email=f"test{i}@example.com",
                display_name=f"Test User {i}",
            )
            db_session.add(user)
            users.append(user)
        await db_session.flush()
        
        # Create test poll
        poll = Poll(
            title="Hybrid Mode Test Poll",
            description="Test poll for hybrid mode performance",
            created_by=users[0].id,
        )
        db_session.add(poll)
        await db_session.flush()
        
        # Create hybrid delegation (global fallback)
        hybrid_delegation = Delegation(
            delegator_id=users[0].id,
            delegatee_id=users[1].id,
            mode=DelegationMode.HYBRID_SEED,
            # No poll_id = global fallback
            start_date=datetime.utcnow(),
        )
        db_session.add(hybrid_delegation)
        await db_session.flush()
        
        delegation_service = DelegationService(db_session)
        
        # Test hybrid delegation resolution
        start_time = time.time()
        chain = await delegation_service.resolve_delegation_chain(
            users[0].id, poll.id
        )
        total_time = time.time() - start_time
        
        # Verify chain is correct
        assert len(chain) == 1
        assert chain[0].id == hybrid_delegation.id
        assert chain[0].mode == DelegationMode.HYBRID_SEED
        
        # Performance assertion
        assert total_time <= 1.0, f"Hybrid mode resolution took {total_time:.3f}s, expected <= 1.0s"
        
        print(f"✅ Hybrid mode performance: {total_time:.3f}s")
