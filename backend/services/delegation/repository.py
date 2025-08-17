"""Delegation repository layer for data persistence.

This module provides a thin façade over read and write repositories
to maintain backward compatibility while reducing complexity.
"""

from typing import List, Optional
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from backend.models.delegation import Delegation
from backend.models.delegation_stats import DelegationStats

from .repository_read import DelegationReadRepository
from .repository_write import DelegationWriteRepository


class DelegationRepository:
    """Repository for delegation data access operations (thin façade)."""
    
    def __init__(self, db: AsyncSession):
        self.db = db
        self.read_repo = DelegationReadRepository(db)
        self.write_repo = DelegationWriteRepository(db)
    
    # Read operations delegated to read repository
    async def get_delegation_by_id(self, delegation_id: UUID) -> Optional[Delegation]:
        """Get delegation by ID."""
        return await self.read_repo.get_delegation_by_id(delegation_id)
    
    async def get_active_delegations_for_user(
        self,
        user_id: UUID,
        poll_id: Optional[UUID] = None,
        label_id: Optional[UUID] = None,
        field_id: Optional[UUID] = None,
        institution_id: Optional[UUID] = None,
        value_id: Optional[UUID] = None,
        idea_id: Optional[UUID] = None,
    ) -> List[Delegation]:
        """Get active delegations for a user with target scope filtering."""
        return await self.read_repo.get_active_delegations_for_user(
            user_id, poll_id, label_id, field_id, institution_id, value_id, idea_id
        )
    
    async def get_all_active_delegations(self) -> List[Delegation]:
        """Get all active delegations (for chain resolution)."""
        return await self.read_repo.get_all_active_delegations()
    
    async def get_delegation_history(self, user_id: UUID) -> List[Delegation]:
        """Get delegation history for a user."""
        return await self.read_repo.get_delegation_history(user_id)
    
    async def get_poll_delegations(self, poll_id: UUID) -> List[Delegation]:
        """Get all delegations for a specific poll."""
        return await self.read_repo.get_poll_delegations(poll_id)
    
    async def get_expired_legacy_delegations(self) -> List[Delegation]:
        """Get expired legacy fixed-term delegations."""
        return await self.read_repo.get_expired_legacy_delegations()
    
    # Write operations delegated to write repository
    async def create_delegation(self, delegation: Delegation) -> Delegation:
        """Create a new delegation."""
        return await self.write_repo.create_delegation(delegation)
    
    async def revoke_delegation(self, delegation_id: UUID) -> None:
        """Revoke a delegation by setting revoked_at timestamp."""
        await self.write_repo.revoke_delegation(delegation_id)
    
    async def invalidate_stats_cache(self, poll_id: Optional[UUID] = None) -> None:
        """Invalidate cached delegation stats."""
        await self.write_repo.invalidate_stats_cache(poll_id)
    
    async def save_delegation_stats(self, stats_record: DelegationStats) -> None:
        """Save delegation statistics record."""
        await self.write_repo.save_delegation_stats(stats_record)
