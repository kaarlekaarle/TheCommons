"""Synchronous delegation dispatch operations.

This module handles synchronous delegation operations that don't require
async processing or background tasks.
"""

from datetime import datetime, timedelta
from typing import Optional
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

from .repository import DelegationRepository
from .cache import DelegationCache
from .telemetry import DelegationTelemetry


class DelegationSyncDispatch:
    """Synchronous dispatch layer for delegation operations."""
    
    def __init__(self, db: AsyncSession, cache: DelegationCache):
        self.db = db
        self.cache = cache
        self.repository = DelegationRepository(db)
    
    async def create_delegation(
        self,
        delegator_id: UUID,
        delegatee_id: UUID,
        mode: DelegationMode = DelegationMode.FLEXIBLE_DOMAIN,
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
        """Create a new delegation with validation and immediate side effects."""
        # Validate mode-specific constraints
        await self._validate_mode_constraints(
            mode, legacy_term_ends_at, start_date, end_date
        )

        # Set default dates if not provided
        if start_date is None:
            start_date = datetime.utcnow()

        # Validate self-delegation
        if delegator_id == delegatee_id:
            raise SelfDelegationError(
                message="Users cannot delegate to themselves",
                details={"delegator_id": str(delegator_id)},
            )

        # Check for circular delegation
        if await self._would_create_circular_delegation(delegator_id, delegatee_id, poll_id):
            raise CircularDelegationError(
                message="Creating this delegation would create a circular chain",
                details={
                    "delegator_id": str(delegator_id),
                    "delegatee_id": str(delegatee_id),
                    "poll_id": str(poll_id) if poll_id else None,
                },
            )

        # Check for overlapping delegations
        existing_delegations = await self.repository.get_active_delegations_for_user(
            delegator_id, poll_id, label_id, field_id, institution_id, value_id, idea_id
        )
        
        if existing_delegations:
            raise DelegationAlreadyExistsError(
                message="User already has an active delegation for this scope",
                details={
                    "delegator_id": str(delegator_id),
                    "existing_delegations": [str(d.id) for d in existing_delegations],
                },
            )

        # Create new delegation
        delegation = Delegation(
            delegator_id=delegator_id,
            delegatee_id=delegatee_id,
            mode=mode,
            poll_id=poll_id,
            label_id=label_id,
            field_id=field_id,
            institution_id=institution_id,
            value_id=value_id,
            idea_id=idea_id,
            start_date=start_date,
            end_date=end_date,
            legacy_term_ends_at=legacy_term_ends_at,
            is_anonymous=is_anonymous,
            chain_origin_id=delegator_id,
        )

        # Persist delegation
        delegation = await self.repository.create_delegation(delegation)

        # Invalidate stats cache
        await self.repository.invalidate_stats_cache(poll_id)

        # Invalidate chain cache for delegator and delegatee
        await self.cache.invalidate_user_cache(delegator_id)
        await self.cache.invalidate_delegatee_cache(delegatee_id)
        
        # Invalidate fast-path cache for delegator and delegatee
        await self.cache.invalidate_fast_path_cache(
            delegator_id, poll_id, label_id, field_id, institution_id, value_id, idea_id
        )
        await self.cache.invalidate_fast_path_cache(
            delegatee_id, poll_id, label_id, field_id, institution_id, value_id, idea_id
        )

        # Log delegation creation
        DelegationTelemetry.log_delegation_creation(
            delegation.id, delegator_id, delegatee_id, mode, delegation.target_type
        )

        return delegation
    
    async def revoke_delegation(self, delegation_id: UUID) -> None:
        """Revoke a delegation with immediate side effects."""
        delegation = await self.repository.get_delegation_by_id(delegation_id)
        if not delegation:
            raise DelegationNotFoundError(delegation_id)

        if delegation.revoked_at:
            return  # Already revoked, idempotent success

        # Revoke delegation
        await self.repository.revoke_delegation(delegation_id)

        # Invalidate chain cache for delegator and delegatee
        await self.cache.invalidate_user_cache(delegation.delegator_id)
        await self.cache.invalidate_delegatee_cache(delegation.delegatee_id)
        
        # Invalidate fast-path cache for delegator and delegatee
        await self.cache.invalidate_fast_path_cache(
            delegation.delegator_id, 
            delegation.poll_id, delegation.label_id, delegation.field_id,
            delegation.institution_id, delegation.value_id, delegation.idea_id
        )
        await self.cache.invalidate_fast_path_cache(
            delegation.delegatee_id,
            delegation.poll_id, delegation.label_id, delegation.field_id,
            delegation.institution_id, delegation.value_id, delegation.idea_id
        )

        # Log delegation revocation
        DelegationTelemetry.log_delegation_revocation(
            delegation_id, delegation.mode, delegation.target_type
        )
    
    async def _validate_mode_constraints(
        self,
        mode: DelegationMode,
        legacy_term_ends_at: Optional[datetime],
        start_date: Optional[datetime],
        end_date: Optional[datetime],
    ) -> None:
        """Validate mode-specific constraints."""
        if mode == DelegationMode.LEGACY_FIXED_TERM:
            if start_date and legacy_term_ends_at:
                max_allowed = start_date + timedelta(days=4 * 365)
                if legacy_term_ends_at > max_allowed:
                    raise InvalidDelegationPeriodError(
                        message="Legacy term cannot exceed 4 years from start date",
                        details={
                            "start_date": start_date.isoformat(),
                            "legacy_term_ends_at": legacy_term_ends_at.isoformat(),
                            "max_allowed": max_allowed.isoformat(),
                        },
                    )
    
    async def _would_create_circular_delegation(
        self, delegator_id: UUID, delegatee_id: UUID, poll_id: Optional[UUID]
    ) -> bool:
        """Check if creating a delegation would create a circular chain."""
        # This is a simplified check - in practice, you'd want to do a full chain traversal
        # For now, just check if the delegatee has any delegation back to the delegator
        delegatee_delegations = await self.repository.get_active_delegations_for_user(
            delegatee_id, poll_id
        )
        
        for delegation in delegatee_delegations:
            if delegation.delegatee_id == delegator_id:
                return True
        
        return False
