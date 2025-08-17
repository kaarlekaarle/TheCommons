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
        
        # Early-exit fast path: Check for direct delegation case
        fast_path_start = time.time()
        fast_path_result = await self.cache.get_fast_path_result(
            user_id, poll_id, label_id, field_id, institution_id, value_id, idea_id
        )
        fast_path_time = time.time() - fast_path_start
        
        if fast_path_result and fast_path_result.get("is_direct"):
            # Fast path hit - return direct delegation result
            total_time = time.time() - start_time
            DelegationTelemetry.log_fast_path_cache_hit(
                user_id, total_time, fast_path_time, 0, 1, True, True,
                poll_id, label_id, field_id, institution_id, value_id, idea_id
            )
            
            # Create a minimal delegation object for the direct case
            from backend.models.delegation import Delegation
            direct_delegation = Delegation()
            direct_delegation.id = UUID(fast_path_result["delegation_id"])
            direct_delegation.delegator_id = user_id
            direct_delegation.delegatee_id = UUID(fast_path_result["delegatee_id"])
            direct_delegation.mode = fast_path_result["mode"]
            
            return [direct_delegation]
        
        # Fast path miss - continue with normal resolution
        DelegationTelemetry.log_fast_path_cache_miss(
            user_id, fast_path_time, poll_id, label_id, field_id, institution_id, value_id, idea_id
        )
        
        # Check if this is a direct delegation case we can cache
        direct_check_start = time.time()
        direct_case = await self.repository.check_direct_delegation_case(
            user_id, poll_id, label_id, field_id, institution_id, value_id, idea_id
        )
        direct_check_time = time.time() - direct_check_start
        
        if direct_case:
            # This is a direct case - cache it and return
            await self.cache.cache_fast_path_result(
                user_id, direct_case, poll_id, label_id, field_id, institution_id, value_id, idea_id
            )
            
            # Create delegation object and return
            from backend.models.delegation import Delegation
            direct_delegation = Delegation()
            direct_delegation.id = UUID(direct_case["delegation_id"])
            direct_delegation.delegator_id = user_id
            direct_delegation.delegatee_id = UUID(direct_case["delegatee_id"])
            direct_delegation.mode = direct_case["mode"]
            
            total_time = time.time() - start_time
            DelegationTelemetry.log_direct_delegation_detected(
                user_id, total_time, direct_check_time, 1, True,
                poll_id, label_id, field_id, institution_id, value_id, idea_id
            )
            
            return [direct_delegation]
        
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
