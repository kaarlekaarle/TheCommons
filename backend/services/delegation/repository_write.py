"""Write-only delegation repository operations.

This module handles all write operations for delegations,
separated from read operations to reduce complexity.
"""

from typing import Optional
from uuid import UUID

from sqlalchemy import delete, func
from sqlalchemy.ext.asyncio import AsyncSession

from backend.models.delegation import Delegation
from backend.models.delegation_stats import DelegationStats


class DelegationWriteRepository:
    """Write-only repository for delegation data modification operations."""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def create_delegation(self, delegation: Delegation) -> Delegation:
        """Create a new delegation."""
        self.db.add(delegation)
        await self.db.flush()
        await self.db.refresh(delegation)
        return delegation
    
    async def revoke_delegation(self, delegation_id: UUID) -> None:
        """Revoke a delegation by setting revoked_at timestamp."""
        delegation = await self.db.get(Delegation, delegation_id)
        if delegation:
            delegation.revoked_at = func.now()
            await self.db.flush()
    
    async def invalidate_stats_cache(self, poll_id: Optional[UUID] = None) -> None:
        """Invalidate cached delegation stats."""
        query = delete(DelegationStats).where(DelegationStats.poll_id == poll_id)
        await self.db.execute(query)
        await self.db.flush()
    
    async def save_delegation_stats(self, stats_record: DelegationStats) -> None:
        """Save delegation statistics record."""
        self.db.add(stats_record)
        await self.db.flush()
