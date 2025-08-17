"""Read-only delegation repository operations.

This module handles all read operations for delegations,
separated from write operations to reduce complexity.
"""

from datetime import datetime
from typing import List, Optional
from uuid import UUID

from sqlalchemy import and_, desc, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.models.delegation import Delegation, DelegationMode


class DelegationReadRepository:
    """Read-only repository for delegation data access operations."""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def get_delegation_by_id(self, delegation_id: UUID) -> Optional[Delegation]:
        """Get delegation by ID."""
        return await self.db.get(Delegation, delegation_id)
    
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
        conditions = [
            Delegation.delegator_id == user_id,
            Delegation.is_deleted == False,
            Delegation.revoked_at.is_(None),
        ]

        # Add target-specific conditions
        if poll_id is not None:
            conditions.append(Delegation.poll_id == poll_id)
        elif label_id is not None:
            conditions.append(Delegation.label_id == label_id)
        elif field_id is not None:
            conditions.append(Delegation.field_id == field_id)
        elif institution_id is not None:
            conditions.append(Delegation.institution_id == institution_id)
        elif value_id is not None:
            conditions.append(Delegation.value_id == value_id)
        elif idea_id is not None:
            conditions.append(Delegation.idea_id == idea_id)
        else:
            # Global delegation (no specific target)
            conditions.extend([
                Delegation.poll_id.is_(None),
                Delegation.label_id.is_(None),
                Delegation.field_id.is_(None),
                Delegation.institution_id.is_(None),
                Delegation.value_id.is_(None),
                Delegation.idea_id.is_(None),
            ])

        # Add active date conditions
        conditions.extend([
            or_(
                Delegation.end_date.is_(None),
                Delegation.end_date > func.now(),
            ),
            or_(
                Delegation.start_date.is_(None),
                Delegation.start_date <= func.now(),
            ),
        ])

        # Optimized query with lean column selection
        query = (
            select(
                Delegation.id,
                Delegation.delegator_id,
                Delegation.delegatee_id,
                Delegation.mode,
                Delegation.poll_id,
                Delegation.label_id,
                Delegation.field_id,
                Delegation.institution_id,
                Delegation.value_id,
                Delegation.idea_id,
                Delegation.start_date,
                Delegation.end_date,
                Delegation.legacy_term_ends_at,
                Delegation.created_at,
            )
            .where(and_(*conditions))
            .order_by(
                Delegation.mode == DelegationMode.HYBRID_SEED.desc(),
                Delegation.created_at.asc(),
            )
        )

        result = await self.db.execute(query)
        rows = result.fetchall()
        
        # Convert rows to Delegation objects
        delegations = []
        for row in rows:
            delegation = Delegation()
            delegation.id = row.id
            delegation.delegator_id = row.delegator_id
            delegation.delegatee_id = row.delegatee_id
            delegation.mode = row.mode
            delegation.poll_id = row.poll_id
            delegation.label_id = row.label_id
            delegation.field_id = row.field_id
            delegation.institution_id = row.institution_id
            delegation.value_id = row.value_id
            delegation.idea_id = row.idea_id
            delegation.start_date = row.start_date
            delegation.end_date = row.end_date
            delegation.legacy_term_ends_at = row.legacy_term_ends_at
            delegation.created_at = row.created_at
            delegations.append(delegation)
        
        return delegations
    
    async def get_all_active_delegations(self) -> List[Delegation]:
        """Get all active delegations (for chain resolution)."""
        conditions = [
            Delegation.is_deleted == False,
            Delegation.revoked_at.is_(None),
            or_(
                Delegation.end_date.is_(None),
                Delegation.end_date > func.now(),
            ),
            or_(
                Delegation.start_date.is_(None),
                Delegation.start_date <= func.now(),
            ),
        ]

        query = (
            select(
                Delegation.id,
                Delegation.delegator_id,
                Delegation.delegatee_id,
                Delegation.mode,
                Delegation.poll_id,
                Delegation.label_id,
                Delegation.field_id,
                Delegation.institution_id,
                Delegation.value_id,
                Delegation.idea_id,
                Delegation.start_date,
                Delegation.end_date,
                Delegation.legacy_term_ends_at,
                Delegation.created_at,
            )
            .where(and_(*conditions))
        )

        result = await self.db.execute(query)
        rows = result.fetchall()
        
        # Convert rows to Delegation objects
        delegations = []
        for row in rows:
            delegation = Delegation()
            delegation.id = row.id
            delegation.delegator_id = row.delegator_id
            delegation.delegatee_id = row.delegatee_id
            delegation.mode = row.mode
            delegation.poll_id = row.poll_id
            delegation.label_id = row.label_id
            delegation.field_id = row.field_id
            delegation.institution_id = row.institution_id
            delegation.value_id = row.value_id
            delegation.idea_id = row.idea_id
            delegation.start_date = row.start_date
            delegation.end_date = row.end_date
            delegation.legacy_term_ends_at = row.legacy_term_ends_at
            delegation.created_at = row.created_at
            delegations.append(delegation)
        
        return delegations
    
    async def get_delegation_history(self, user_id: UUID) -> List[Delegation]:
        """Get delegation history for a user."""
        query = (
            select(Delegation)
            .where(Delegation.delegator_id == user_id)
            .order_by(desc(Delegation.created_at))
        )
        result = await self.db.execute(query)
        return result.scalars().all()
    
    async def get_poll_delegations(self, poll_id: UUID) -> List[Delegation]:
        """Get all delegations for a specific poll."""
        query = select(Delegation).where(Delegation.poll_id == poll_id)
        result = await self.db.execute(query)
        return result.scalars().all()
    
    async def get_expired_legacy_delegations(self) -> List[Delegation]:
        """Get expired legacy fixed-term delegations."""
        now = datetime.utcnow()
        query = select(Delegation).where(
            and_(
                Delegation.mode == DelegationMode.LEGACY_FIXED_TERM,
                Delegation.legacy_term_ends_at <= now,
                Delegation.is_deleted == False,
                Delegation.revoked_at.is_(None),
            )
        )
        result = await self.db.execute(query)
        return result.scalars().all()
