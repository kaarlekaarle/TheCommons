"""Asynchronous delegation dispatch operations.

This module handles asynchronous delegation operations that require
background tasks or async processing.
"""

import time
from datetime import timedelta
from typing import Any, Dict, List, Optional
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from backend.core.exceptions.delegation import DelegationNotFoundError
from backend.models.delegation import Delegation

from .chain_resolution import ChainResolutionCore
from .repository import DelegationRepository
from .cache import DelegationCache
from .telemetry import DelegationTelemetry


class DelegationAsyncDispatch:
    """Asynchronous dispatch layer for delegation operations."""
    
    def __init__(self, db: AsyncSession, cache: DelegationCache):
        self.db = db
        self.cache = cache
        self.repository = DelegationRepository(db)
        self.stats_cache_ttl = timedelta(minutes=5)
        
        # Import here to avoid circular dependency
        from backend.core.background_tasks import StatsCalculationTask
        self.stats_task = StatsCalculationTask(db, self)
    
    async def resolve_delegation_chain(
        self,
        user_id: UUID,
        poll_id: Optional[UUID] = None,
        label_id: Optional[UUID] = None,
        field_id: Optional[UUID] = None,
        institution_id: Optional[UUID] = None,
        value_id: Optional[UUID] = None,
        idea_id: Optional[UUID] = None,
        max_depth: int = 10,
    ) -> List[Delegation]:
        """Resolve delegation chain with caching and telemetry."""
        # Start telemetry
        start_time = DelegationTelemetry.log_chain_resolution_start(
            user_id, poll_id, label_id, field_id, institution_id, value_id, idea_id
        )
        
        # Try cache first
        cache_start = time.time()
        cache_key = self.cache.generate_cache_key(
            user_id, poll_id, label_id, field_id, institution_id, value_id, idea_id
        )
        cached_chain_data = await self.cache.get_cached_chain(cache_key)
        cache_time = time.time() - cache_start
        
        if cached_chain_data:
            # Cache hit
            deserialize_start = time.time()
            chain = ChainResolutionCore.deserialize_chain(cached_chain_data)
            deserialize_time = time.time() - deserialize_start
            total_time = time.time() - start_time
            
            DelegationTelemetry.log_cache_hit(
                cache_key, cache_time, deserialize_time, total_time,
                len(chain), user_id, poll_id
            )
            return chain

        # Cache miss - resolve chain from database
        db_start = time.time()
        all_delegations = await self.repository.get_all_active_delegations()
        
        # Use pure chain resolution core
        chain = ChainResolutionCore.resolve_chain_from_delegations(
            user_id, all_delegations, poll_id, label_id, field_id,
            institution_id, value_id, idea_id, max_depth
        )
        
        db_time = time.time() - db_start

        # Cache the resolved chain
        cache_start = time.time()
        await self.cache.cache_chain(cache_key, chain)
        cache_time = time.time() - cache_start
        
        total_time = time.time() - start_time
        
        DelegationTelemetry.log_cache_miss(
            db_time, cache_time, total_time, 1, len(chain), 0,
            user_id, poll_id
        )
        
        return chain
    
    async def revoke_delegation_with_stats(self, delegation_id: UUID) -> None:
        """Revoke a delegation with background stats recalculation."""
        delegation = await self.repository.get_delegation_by_id(delegation_id)
        if not delegation:
            raise DelegationNotFoundError(delegation_id)

        if delegation.revoked_at:
            return  # Already revoked, idempotent success

        # Revoke delegation
        await self.repository.revoke_delegation(delegation_id)

        # Trigger stats recalculation in background
        await self.stats_task.calculate_stats(delegation.poll_id)

        # Invalidate chain cache for delegator and delegatee
        await self.cache.invalidate_user_cache(delegation.delegator_id)
        await self.cache.invalidate_delegatee_cache(delegation.delegatee_id)

        # Log delegation revocation
        DelegationTelemetry.log_delegation_revocation(
            delegation_id, delegation.mode, delegation.target_type
        )
