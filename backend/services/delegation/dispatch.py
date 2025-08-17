"""Delegation dispatch and routing layer.

This module provides a thin façade over sync and async dispatch operations
to maintain backward compatibility while reducing complexity.
"""

from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from backend.core.exceptions.delegation import (
    CircularDelegationError,
    DelegationAlreadyExistsError,
    DelegationNotFoundError,
    InvalidDelegationPeriodError,
    SelfDelegationError,
)
from backend.models.delegation import Delegation, DelegationMode
from backend.models.delegation_stats import DelegationStats

from .chain_resolution import ChainResolutionCore
from .repository import DelegationRepository
from .cache import DelegationCache
from .telemetry import DelegationTelemetry
from .dispatch_sync import DelegationSyncDispatch
from .dispatch_async import DelegationAsyncDispatch


class DelegationTarget:
    """Represents a delegation target with type and ID."""
    
    def __init__(self, target_type: str, target_id: UUID):
        self.type = target_type
        self.id = target_id
    
    def __repr__(self) -> str:
        return f"DelegationTarget(type='{self.type}', id='{self.id}')"


class DelegationDispatch:
    """Dispatch layer for delegation operations (thin façade)."""
    
    def __init__(self, db: AsyncSession, cache: DelegationCache):
        self.db = db
        self.cache = cache
        self.repository = DelegationRepository(db)
        self.stats_cache_ttl = timedelta(minutes=5)
        
        # Initialize sync and async dispatch layers
        self.sync_dispatch = DelegationSyncDispatch(db, cache)
        self.async_dispatch = DelegationAsyncDispatch(db, cache)
        
        # Import here to avoid circular dependency
        from backend.core.background_tasks import StatsCalculationTask
        self.stats_task = StatsCalculationTask(db, self)
    
    # Delegate to async dispatch for chain resolution
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
        return await self.async_dispatch.resolve_delegation_chain(
            user_id, poll_id, label_id, field_id, institution_id, value_id, idea_id, max_depth
        )
    
    # Delegate to sync dispatch for creation
    async def create_delegation(
        self,
        delegator_id: UUID,
        delegatee_id: UUID,
        mode: DelegationMode = DelegationMode.FLEXIBLE_DOMAIN,
        target: Optional[DelegationTarget] = None,
        poll_id: Optional[UUID] = None,
        label_id: Optional[UUID] = None,
        field_id: Optional[UUID] = None,
        institution_id: Optional[UUID] = None,
        value_id: Optional[UUID] = None,
        idea_id: Optional[UUID] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        is_anonymous: bool = False,
        legacy_term_ends_at: Optional[datetime] = None,
    ) -> Delegation:
        """Create a new delegation with validation and side effects."""
        return await self.sync_dispatch.create_delegation(
            delegator_id, delegatee_id, mode, poll_id, label_id, field_id,
            institution_id, value_id, idea_id, start_date, end_date,
            is_anonymous, legacy_term_ends_at
        )
    
    # Delegate to sync dispatch for revocation (without stats)
    async def revoke_delegation(self, delegation_id: UUID) -> None:
        """Revoke a delegation with side effects."""
        await self.sync_dispatch.revoke_delegation(delegation_id)
    
    # Delegate to async dispatch for revocation with stats
    async def revoke_delegation_with_stats(self, delegation_id: UUID) -> None:
        """Revoke a delegation with background stats recalculation."""
        await self.async_dispatch.revoke_delegation_with_stats(delegation_id)
