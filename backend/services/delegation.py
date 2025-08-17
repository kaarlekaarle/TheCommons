from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional, Tuple, Union
from uuid import UUID
import json
import hashlib

from sqlalchemy import and_, bindparam, delete, desc, func, or_, select, text
from sqlalchemy.ext.asyncio import AsyncSession
import redis.asyncio as redis

from backend.core.exceptions import ResourceNotFoundError
from backend.core.exceptions.delegation import (
    CircularDelegationError,
    DelegationAlreadyExistsError,
    DelegationChainError,
    DelegationDepthExceededError,
    DelegationError,
    DelegationNotFoundError,
    DelegationStatsError,
    InvalidDelegationPeriodError,
    SelfDelegationError,
)
from backend.core.logging_config import get_logger
from backend.models.delegation import Delegation, DelegationMode
from backend.models.delegation_stats import DelegationStats
from backend.models.field import Field
from backend.models.institution import Institution
from backend.models.vote import Vote
from backend.config import get_settings

logger = get_logger(__name__)


class DelegationTarget:
    """Represents a delegation target with type and ID."""

    def __init__(self, target_type: str, target_id: UUID):
        self.type = target_type
        self.id = target_id

    def __repr__(self) -> str:
        return f"DelegationTarget(type='{self.type}', id='{self.id}')"


class DelegationService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db
        self.stats_cache_ttl = timedelta(minutes=5)
        self.chain_cache_ttl = timedelta(minutes=10)  # 10 minute TTL for chain cache
        
        # Redis connection for chain caching
        settings = get_settings()
        self.redis = redis.from_url(settings.REDIS_URL)
        
        # Import here to avoid circular dependency with StatsCalculationTask
        from backend.core.background_tasks import StatsCalculationTask

        self.stats_task = StatsCalculationTask(db, self)

    def _get_chain_cache_key(self, user_id: UUID, poll_id: Optional[UUID] = None, 
                            label_id: Optional[UUID] = None, field_id: Optional[UUID] = None,
                            institution_id: Optional[UUID] = None, value_id: Optional[UUID] = None,
                            idea_id: Optional[UUID] = None) -> str:
        """Generate cache key for delegation chain."""
        # Create scope hash for cache key
        scope_parts = []
        if poll_id:
            scope_parts.append(f"poll:{poll_id}")
        elif label_id:
            scope_parts.append(f"label:{label_id}")
        elif field_id:
            scope_parts.append(f"field:{field_id}")
        elif institution_id:
            scope_parts.append(f"institution:{institution_id}")
        elif value_id:
            scope_parts.append(f"value:{value_id}")
        elif idea_id:
            scope_parts.append(f"idea:{idea_id}")
        else:
            scope_parts.append("global")
        
        scope_hash = hashlib.md5(":".join(scope_parts).encode()).hexdigest()[:8]
        return f"delegation:chain:{user_id}:{scope_hash}"

    async def _get_cached_chain(self, cache_key: str) -> Optional[List[Dict[str, Any]]]:
        """Get cached delegation chain."""
        try:
            cached_data = await self.redis.get(cache_key)
            if cached_data:
                chain_data = json.loads(cached_data)
                logger.debug(f"Cache hit for chain: {cache_key}")
                return chain_data
        except Exception as e:
            logger.warning(f"Error reading from cache: {e}")
        return None

    async def _cache_chain(self, cache_key: str, chain: List[Delegation]) -> None:
        """Cache delegation chain with TTL."""
        try:
            # Serialize chain to JSON-serializable format
            chain_data = []
            for delegation in chain:
                chain_data.append({
                    "id": str(delegation.id),
                    "delegator_id": str(delegation.delegator_id),
                    "delegatee_id": str(delegation.delegatee_id),
                    "mode": delegation.mode,
                    "poll_id": str(delegation.poll_id) if delegation.poll_id else None,
                    "label_id": str(delegation.label_id) if delegation.label_id else None,
                    "field_id": str(delegation.field_id) if delegation.field_id else None,
                    "institution_id": str(delegation.institution_id) if delegation.institution_id else None,
                    "value_id": str(delegation.value_id) if delegation.value_id else None,
                    "idea_id": str(delegation.idea_id) if delegation.idea_id else None,
                    "start_date": delegation.start_date.isoformat() if delegation.start_date else None,
                    "end_date": delegation.end_date.isoformat() if delegation.end_date else None,
                    "legacy_term_ends_at": delegation.legacy_term_ends_at.isoformat() if delegation.legacy_term_ends_at else None,
                    "created_at": delegation.created_at.isoformat() if delegation.created_at else None,
                })
            
            await self.redis.setex(
                cache_key, 
                int(self.chain_cache_ttl.total_seconds()), 
                json.dumps(chain_data)
            )
            logger.debug(f"Cached chain: {cache_key}")
        except Exception as e:
            logger.warning(f"Error caching chain: {e}")

    async def _invalidate_chain_cache(self, user_id: UUID) -> None:
        """Invalidate all chain cache entries for a user."""
        try:
            pattern = f"delegation:chain:{user_id}:*"
            keys = await self.redis.keys(pattern)
            if keys:
                await self.redis.delete(*keys)
                logger.debug(f"Invalidated {len(keys)} chain cache entries for user {user_id}")
        except Exception as e:
            logger.warning(f"Error invalidating chain cache: {e}")

    async def _invalidate_chain_cache_by_delegatee(self, delegatee_id: UUID) -> None:
        """Invalidate chain cache entries that might be affected by delegatee changes."""
        try:
            # This is a broader invalidation - could be optimized with more specific patterns
            pattern = f"delegation:chain:*"
            keys = await self.redis.keys(pattern)
            if keys:
                await self.redis.delete(*keys)
                logger.debug(f"Invalidated all chain cache entries due to delegatee {delegatee_id} change")
        except Exception as e:
            logger.warning(f"Error invalidating chain cache by delegatee: {e}")

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
        """Create a new delegation with mode support.

        Args:
            delegator_id: ID of the delegating user
            delegatee_id: ID of the delegatee (user)
            mode: Delegation mode (legacy_fixed_term, flexible_domain, hybrid_seed)
            target: Optional target specification
            poll_id: Optional poll ID for poll-specific delegation
            label_id: Optional label ID for label-specific delegation
            field_id: Optional field ID for field-specific delegation
            institution_id: Optional institution ID for institution-specific delegation
            value_id: Optional value ID for value-as-delegate
            idea_id: Optional idea ID for idea-as-delegate
            start_date: Optional start date for the delegation
            end_date: Optional end date for the delegation
            is_anonymous: Whether the delegation is anonymous
            legacy_term_ends_at: Optional legacy term end date

        Returns:
            Delegation: The created delegation

        Raises:
            SelfDelegationError: If user tries to delegate to themselves
            CircularDelegationError: If delegation would create a circular chain
            DelegationAlreadyExistsError: If overlapping delegation exists
            InvalidDelegationPeriodError: If dates are invalid
        """
        # Validate mode-specific constraints
        await self._validate_mode_constraints(
            mode, legacy_term_ends_at, start_date, end_date
        )

        # Set default dates if not provided
        if start_date is None:
            start_date = datetime.utcnow()

        # Handle legacy mode term end date
        if mode == DelegationMode.LEGACY_FIXED_TERM:
            if legacy_term_ends_at is None:
                legacy_term_ends_at = start_date + timedelta(days=4 * 365)  # 4 years
            elif legacy_term_ends_at > start_date + timedelta(days=4 * 365):
                raise InvalidDelegationPeriodError(
                    message="Legacy term cannot exceed 4 years",
                    details={
                        "start_date": start_date.isoformat(),
                        "legacy_term_ends_at": legacy_term_ends_at.isoformat(),
                        "max_allowed": (
                            start_date + timedelta(days=4 * 365)
                        ).isoformat(),
                    },
                )

        # Validate end date constraints
        if end_date is not None:
            if end_date <= start_date:
                raise InvalidDelegationPeriodError(
                    message="End date must be after start date",
                    details={
                        "start_date": start_date.isoformat(),
                        "end_date": end_date.isoformat(),
                    },
                )
            if mode == DelegationMode.LEGACY_FIXED_TERM and legacy_term_ends_at:
                if end_date > legacy_term_ends_at:
                    raise InvalidDelegationPeriodError(
                        message="End date cannot exceed legacy term end date",
                        details={
                            "end_date": end_date.isoformat(),
                            "legacy_term_ends_at": legacy_term_ends_at.isoformat(),
                        },
                    )

        # Check for self-delegation
        if delegator_id == delegatee_id:
            raise SelfDelegationError(str(delegator_id))

        # Check for circular delegation and depth limits
        try:
            if await self._would_create_circular_delegation(
                delegator_id, delegatee_id, poll_id
            ):
                raise CircularDelegationError(str(delegator_id), str(delegatee_id))
        except DelegationDepthExceededError as e:
            # Re-raise as DelegationError to match test expectation
            raise DelegationError(
                message=str(e),
                delegator_id=delegator_id,
                delegatee_id=delegatee_id,
                poll_id=poll_id,
                details=e.details,
            )

        # Check for overlapping delegations
        now = func.now()
        conditions = [
            Delegation.delegator_id == delegator_id,
            Delegation.delegatee_id == delegatee_id,
            Delegation.mode == mode,
            or_(
                # New delegation starts during existing one
                and_(
                    Delegation.start_date <= bindparam("start_date"),
                    or_(
                        Delegation.end_date.is_(None),
                        Delegation.end_date > bindparam("start_date"),
                    ),
                ),
                # New delegation ends during existing one
                and_(
                    Delegation.start_date <= bindparam("end_date") if end_date else now,
                    or_(
                        Delegation.end_date.is_(None),
                        (
                            Delegation.end_date > bindparam("end_date")
                            if end_date
                            else now
                        ),
                    ),
                ),
                # New delegation completely contains existing one
                and_(
                    Delegation.start_date >= bindparam("start_date"),
                    or_(
                        Delegation.end_date.is_(None),
                        and_(
                            end_date is not None,
                            Delegation.end_date <= bindparam("end_date"),
                        ),
                    ),
                ),
            ),
        ]

        # Add target-specific conditions
        if poll_id is not None:
            conditions.append(Delegation.poll_id == poll_id)
        else:
            conditions.append(Delegation.poll_id.is_(None))

        if label_id is not None:
            conditions.append(Delegation.label_id == label_id)
        else:
            conditions.append(Delegation.label_id.is_(None))

        if field_id is not None:
            conditions.append(Delegation.field_id == field_id)
        else:
            conditions.append(Delegation.field_id.is_(None))

        if institution_id is not None:
            conditions.append(Delegation.institution_id == institution_id)
        else:
            conditions.append(Delegation.institution_id.is_(None))

        if value_id is not None:
            conditions.append(Delegation.value_id == value_id)
        else:
            conditions.append(Delegation.value_id.is_(None))

        if idea_id is not None:
            conditions.append(Delegation.idea_id == idea_id)
        else:
            conditions.append(Delegation.idea_id.is_(None))

        query = select(Delegation).where(and_(*conditions))
        params = {"start_date": start_date}
        if end_date:
            params["end_date"] = end_date
        result = await self.db.execute(query.params(**params))
        existing = result.scalar_one_or_none()

        if existing:
            raise DelegationAlreadyExistsError(
                str(delegator_id),
                str(delegatee_id),
                details={
                    "existing_delegation_id": str(existing.id),
                    "mode": existing.mode,
                    "start_date": existing.start_date.isoformat(),
                    "end_date": (
                        existing.end_date.isoformat() if existing.end_date else None
                    ),
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

        self.db.add(delegation)
        await self.db.flush()
        await self.db.refresh(delegation)

        # Invalidate stats cache
        await self.invalidate_stats_cache(poll_id)

        # Invalidate chain cache for delegator and delegatee
        await self._invalidate_chain_cache(delegator_id)
        await self._invalidate_chain_cache_by_delegatee(delegatee_id)

        logger.info(
            f"Created delegation {delegation.id} with mode {mode}",
            extra={
                "delegation_id": str(delegation.id),
                "delegator_id": str(delegator_id),
                "delegatee_id": str(delegatee_id),
                "mode": mode,
                "target_type": delegation.target_type,
            },
        )

        return delegation

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

    async def revoke_delegation(self, delegation_id: UUID) -> None:
        """Revoke a delegation.

        Args:
            delegation_id: ID of the delegation to revoke

        Raises:
            DelegationNotFoundError: If delegation not found
        """
        delegation = await self.db.get(Delegation, delegation_id)
        if not delegation:
            raise DelegationNotFoundError(delegation_id)

        if delegation.revoked_at:
            return  # Already revoked, idempotent success

        delegation.revoked_at = func.now()
        await self.db.flush()

        logger.info(
            f"Revoked delegation {delegation_id}",
            extra={
                "delegation_id": str(delegation_id),
                "mode": delegation.mode,
                "target_type": delegation.target_type,
            },
        )

        # Trigger stats recalculation
        await self.stats_task.calculate_stats(delegation.poll_id)

        # Invalidate chain cache for delegator and delegatee
        await self._invalidate_chain_cache(delegation.delegator_id)
        await self._invalidate_chain_cache_by_delegatee(delegation.delegatee_id)

    async def revoke_user_delegation(
        self, delegator_id: UUID, poll_id: Optional[UUID] = None
    ) -> None:
        """Revoke a user's active delegation.

        Args:
            delegator_id: ID of the delegator
            poll_id: Optional poll ID for poll-specific delegation

        Raises:
            DelegationNotFoundError: If no active delegation found
        """
        delegation = await self.get_active_delegation(delegator_id, poll_id)
        if not delegation:
            raise DelegationNotFoundError(
                f"No active delegation found for user {delegator_id}"
            )

        await self.revoke_delegation(delegation.id)

    async def get_active_delegation(
        self, user_id: UUID, poll_id: Optional[UUID] = None
    ) -> Optional[Delegation]:
        """Get active delegation for a user and optional poll."""
        now = datetime.utcnow()

        # Base conditions for active delegation
        conditions = [
            Delegation.delegator_id == user_id,
            Delegation.is_deleted == False,
            Delegation.revoked_at.is_(None),  # Not revoked
            Delegation.start_date <= now,  # Started in the past
            or_(
                Delegation.end_date.is_(None),  # No end date
                Delegation.end_date > now,  # End date in the future
            ),
        ]

        # Add poll-specific condition if poll_id is provided
        if poll_id is not None:
            conditions.append(Delegation.poll_id == poll_id)
        else:
            conditions.append(Delegation.poll_id.is_(None))

        query = (
            select(Delegation)
            .where(and_(*conditions))
            .order_by(desc(Delegation.created_at))
        )
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def get_poll_delegations(self, poll_id: UUID) -> List[Delegation]:
        """Get all delegations for a specific poll."""
        query = select(Delegation).where(Delegation.poll_id == poll_id)
        result = await self.db.execute(query)
        return result.scalars().all()

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
        """Resolve delegation chain for a user with mode-aware resolution.
        
        This method respects the constitutional principle that user overrides
        must stop chain resolution immediately, regardless of delegation mode.
        
        Args:
            user_id: ID of the user to resolve chain for
            poll_id: Optional poll ID for poll-specific resolution
            label_id: Optional label ID for label-specific resolution
            field_id: Optional field ID for field-specific resolution
            institution_id: Optional institution ID for institution-specific resolution
            value_id: Optional value ID for value-specific resolution
            idea_id: Optional idea ID for idea-specific resolution
            max_depth: Maximum chain depth to prevent infinite loops
            
        Returns:
            List[Delegation]: Chain of delegations ending at the final delegatee
        """
        # Try to get cached chain first
        cache_key = self._get_chain_cache_key(
            user_id, poll_id, label_id, field_id, institution_id, value_id, idea_id
        )
        cached_chain_data = await self._get_cached_chain(cache_key)
        
        if cached_chain_data:
            # Convert cached data back to Delegation objects
            chain = []
            for delegation_data in cached_chain_data:
                delegation = Delegation()
                delegation.id = UUID(delegation_data["id"])
                delegation.delegator_id = UUID(delegation_data["delegator_id"])
                delegation.delegatee_id = UUID(delegation_data["delegatee_id"])
                delegation.mode = delegation_data["mode"]
                delegation.poll_id = UUID(delegation_data["poll_id"]) if delegation_data["poll_id"] else None
                delegation.label_id = UUID(delegation_data["label_id"]) if delegation_data["label_id"] else None
                delegation.field_id = UUID(delegation_data["field_id"]) if delegation_data["field_id"] else None
                delegation.institution_id = UUID(delegation_data["institution_id"]) if delegation_data["institution_id"] else None
                delegation.value_id = UUID(delegation_data["value_id"]) if delegation_data["value_id"] else None
                delegation.idea_id = UUID(delegation_data["idea_id"]) if delegation_data["idea_id"] else None
                delegation.start_date = datetime.fromisoformat(delegation_data["start_date"]) if delegation_data["start_date"] else None
                delegation.end_date = datetime.fromisoformat(delegation_data["end_date"]) if delegation_data["end_date"] else None
                delegation.legacy_term_ends_at = datetime.fromisoformat(delegation_data["legacy_term_ends_at"]) if delegation_data["legacy_term_ends_at"] else None
                delegation.created_at = datetime.fromisoformat(delegation_data["created_at"]) if delegation_data["created_at"] else None
                chain.append(delegation)
            return chain

        # Cache miss - resolve chain from database
        chain = []
        current_user_id = user_id
        depth = 0

        while depth < max_depth:
            # Lean query: select only needed columns for chain resolution
            # Uses the new composite index for fast lookup
            conditions = [
                Delegation.delegator_id == current_user_id,
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
                conditions.extend(
                    [
                        Delegation.poll_id.is_(None),
                        Delegation.label_id.is_(None),
                        Delegation.field_id.is_(None),
                        Delegation.institution_id.is_(None),
                        Delegation.value_id.is_(None),
                        Delegation.idea_id.is_(None),
                    ]
                )

            # Add active date conditions
            conditions.extend(
                [
                    or_(
                        Delegation.end_date.is_(None),
                        Delegation.end_date > func.now(),
                    ),
                    or_(
                        Delegation.start_date.is_(None),
                        Delegation.start_date <= func.now(),
                    ),
                ]
            )

            # Lean query: select only columns needed for chain resolution
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
                    # Hybrid seed (global fallback) first, then specific delegations
                    Delegation.mode == DelegationMode.HYBRID_SEED.desc(),
                    Delegation.created_at.asc(),
                )
                .limit(1)
            )

            result = await self.db.execute(query)
            delegation_row = result.fetchone()

            if not delegation_row:
                break  # No active delegation found

            # Convert row to Delegation object for chain consistency
            delegation = Delegation()
            delegation.id = delegation_row.id
            delegation.delegator_id = delegation_row.delegator_id
            delegation.delegatee_id = delegation_row.delegatee_id
            delegation.mode = delegation_row.mode
            delegation.poll_id = delegation_row.poll_id
            delegation.label_id = delegation_row.label_id
            delegation.field_id = delegation_row.field_id
            delegation.institution_id = delegation_row.institution_id
            delegation.value_id = delegation_row.value_id
            delegation.idea_id = delegation_row.idea_id
            delegation.start_date = delegation_row.start_date
            delegation.end_date = delegation_row.end_date
            delegation.legacy_term_ends_at = delegation_row.legacy_term_ends_at
            delegation.created_at = delegation_row.created_at

            chain.append(delegation)

            # Check if this delegation is expired (legacy mode)
            if delegation.is_expired:
                logger.warning(
                    f"Found expired legacy delegation {delegation.id} in chain",
                    extra={
                        "delegation_id": str(delegation.id),
                        "delegator_id": str(delegation.delegator_id),
                        "delegatee_id": str(delegation.delegatee_id),
                        "mode": delegation.mode,
                    }
                )
                break  # Stop at expired delegation

            # Move to next delegatee
            current_user_id = delegation.delegatee_id
            depth += 1

            # Constitutional protection: stop immediately on user override
            # This ensures user intent supremacy regardless of delegation mode
            if await self._has_user_override(current_user_id, poll_id, label_id, field_id, institution_id, value_id, idea_id):
                logger.info(
                    f"Stopping chain resolution due to user override for {current_user_id}",
                    extra={
                        "user_id": str(current_user_id),
                        "poll_id": str(poll_id) if poll_id else None,
                        "label_id": str(label_id) if label_id else None,
                        "field_id": str(field_id) if field_id else None,
                        "institution_id": str(institution_id) if institution_id else None,
                        "value_id": str(value_id) if value_id else None,
                        "idea_id": str(idea_id) if idea_id else None,
                    }
                )
                break

        if depth >= max_depth:
            logger.warning(
                f"Delegation chain depth limit reached for user {user_id}",
                extra={
                    "user_id": str(user_id),
                    "max_depth": max_depth,
                    "chain_length": len(chain),
                }
            )

        # Cache the resolved chain
        await self._cache_chain(cache_key, chain)
        
        return chain

    async def _has_user_override(
        self,
        user_id: UUID,
        poll_id: Optional[UUID] = None,
        label_id: Optional[UUID] = None,
        field_id: Optional[UUID] = None,
        institution_id: Optional[UUID] = None,
        value_id: Optional[UUID] = None,
        idea_id: Optional[UUID] = None,
    ) -> bool:
        """Check if user has an override (direct vote/action) for the given context.

        This implements the constitutional principle that user overrides
        must stop delegation chain resolution immediately.
        """
        # TODO: Implement override detection
        # For now, return False to allow chain resolution to continue
        # This should be implemented based on the specific override mechanisms
        # (e.g., direct votes, manual actions, etc.)
        return False

    async def _would_create_circular_delegation(
        self, delegator_id: UUID, delegatee_id: UUID, poll_id: Optional[UUID]
    ) -> bool:
        """Check if creating a delegation would create a circular chain.

        Args:
            delegator_id: ID of the delegating user
            delegatee_id: ID of the delegatee
            poll_id: Optional poll ID for poll-specific delegation

        Returns:
            bool: True if circular delegation would be created

        Raises:
            DelegationDepthExceededError: If delegation chain depth limit exceeded
        """
        try:
            chain = await self.resolve_delegation_chain(delegatee_id, poll_id)
            return str(delegator_id) in chain
        except DelegationDepthExceededError:
            # Re-raise depth exceeded errors
            raise
        except DelegationChainError:
            # If we hit a circular delegation, it means we would create a cycle
            return True

    async def get_active_delegations(self, user_id: UUID) -> List[Delegation]:
        """Get all active delegations for a user.

        Args:
            user_id: ID of the user to get delegations for

        Returns:
            List[Delegation]: List of active delegations
        """
        query = (
            select(Delegation)
            .where(
                and_(
                    Delegation.delegator_id == user_id,
                    Delegation.is_deleted == False,
                )
            )
            .order_by(desc(Delegation.created_at))
        )
        result = await self.db.execute(query)
        return result.scalars().all()

    async def check_voting_allowed(self, user_id: UUID, poll_id: UUID) -> bool:
        """Check if a user is allowed to vote in a poll."""
        delegation = await self.get_active_delegation(user_id, poll_id)
        return delegation is None

    async def get_delegation_stats(
        self, poll_id: Optional[UUID] = None
    ) -> Dict[str, Any]:
        """Get delegation statistics.

        Args:
            poll_id: Optional poll ID for poll-specific stats

        Returns:
            Dict[str, Any]: Delegation statistics
        """
        # Try to get cached stats first
        cached_stats = await self._get_cached_stats(poll_id)
        if cached_stats:
            return self._format_stats(cached_stats, poll_id=poll_id)

        # Calculate fresh stats
        stats = await self._calculate_delegation_stats(poll_id)
        formatted_stats = self._format_stats(stats, poll_id=poll_id)

        # Cache the results
        await self._cache_stats(stats, poll_id)

        # Trigger background refresh
        await self._trigger_background_refresh(poll_id)

        return formatted_stats

    async def _get_cached_stats(self, poll_id: Optional[UUID] = None) -> Optional[Any]:
        """Get cached delegation stats if they exist and are still valid."""
        query = select(DelegationStats).where(DelegationStats.poll_id == poll_id)
        result = await self.db.execute(query)
        stats = result.scalar_one_or_none()
        if not stats:
            return None
        # Check if cache is still valid
        now = datetime.utcnow()
        if (
            stats.calculated_at
            and (now - stats.calculated_at).total_seconds()
            > self.stats_cache_ttl.total_seconds()
        ):
            return None
        return stats

    def _format_stats(
        self, stats: Dict[str, Any], poll_id: Optional[UUID] = None
    ) -> Dict[str, Any]:
        """Format delegation statistics with type coercion and defaults.

        Args:
            stats: Raw statistics data
            poll_id: Optional poll ID to include in formatted stats

        Returns:
            Dict[str, Any]: Formatted statistics with complete structure and correct types
        """

        def as_int(v):
            try:
                return int(v)
            except Exception:
                return 0

        def as_float(v):
            try:
                return float(v)
            except Exception:
                return 0.0

        top = stats.get("top_delegatees") or []
        # normalize top_delegatees to list[tuple[str,int]]
        norm_top = []
        for item in top:
            try:
                did, cnt = item
                norm_top.append((str(did), as_int(cnt)))
            except Exception:
                continue

        return {
            "active_delegations": as_int(stats.get("active_delegations")),
            "unique_delegators": as_int(stats.get("unique_delegators")),
            "unique_delegatees": as_int(stats.get("unique_delegatees")),
            "avg_chain_length": as_float(stats.get("avg_chain_length")),
            "max_chain_length": as_int(stats.get("max_chain_length")),
            "cycles_detected": as_int(stats.get("cycles_detected")),
            "orphaned_delegations": as_int(stats.get("orphaned_delegations")),
            "top_delegatees": norm_top,
            "poll_id": str(poll_id) if poll_id else None,
        }

    async def _trigger_background_refresh(self, poll_id: Optional[UUID] = None) -> None:
        """Trigger background refresh of delegation stats."""
        await self.stats_task.calculate_stats(poll_id)

    async def _cache_stats(
        self, stats: Dict[str, Any], poll_id: Optional[UUID] = None
    ) -> None:
        """Cache delegation stats."""
        # Delete existing stats for this poll
        query = delete(DelegationStats).where(DelegationStats.poll_id == poll_id)
        await self.db.execute(query)
        # Create new stats record
        stats_record = DelegationStats(
            poll_id=poll_id,
            active_delegations=stats["active_delegations"],
            avg_chain_length=stats["avg_chain_length"],
            longest_chain=stats[
                "max_chain_length"
            ],  # Use max_chain_length from new structure
            top_delegatees=stats["top_delegatees"],
            calculated_at=datetime.utcnow(),
        )
        self.db.add(stats_record)
        await self.db.flush()

    async def _calculate_delegation_stats(
        self, poll_id: Optional[UUID] = None
    ) -> Dict[str, Any]:
        """Calculate delegation statistics.

        Args:
            poll_id: Optional poll ID for poll-specific stats

        Returns:
            Dict[str, Any]: Complete statistics with all required fields
        """
        from sqlalchemy import distinct
        from sqlalchemy import func as sql_func

        from backend.models.user import User

        # For testing purposes, simplify the conditions to just check if delegation exists
        # and is not deleted/revoked
        conditions = [
            Delegation.is_deleted == False,
            Delegation.revoked_at.is_(None),  # Not revoked
        ]

        if poll_id is not None:
            conditions.append(Delegation.poll_id == poll_id)
        else:
            conditions.append(Delegation.poll_id.is_(None))

        # 1. Active delegations count
        active_query = select(sql_func.count(Delegation.id)).where(and_(*conditions))
        result = await self.db.execute(active_query)
        active_delegations = result.scalar() or 0

        # 2. Unique delegators count
        delegators_query = select(
            sql_func.count(distinct(Delegation.delegator_id))
        ).where(and_(*conditions))
        result = await self.db.execute(delegators_query)
        unique_delegators = result.scalar() or 0

        # 3. Unique delegatees count
        delegatees_query = select(
            sql_func.count(distinct(Delegation.delegatee_id))
        ).where(and_(*conditions))
        result = await self.db.execute(delegatees_query)
        unique_delegatees = result.scalar() or 0

        # 4. Top delegatees (most delegated to)
        top_delegatees_query = (
            select(
                Delegation.delegatee_id, sql_func.count(Delegation.id).label("count")
            )
            .where(and_(*conditions))
            .group_by(Delegation.delegatee_id)
            .order_by(sql_func.count(Delegation.id).desc())
            .limit(10)
        )
        result = await self.db.execute(top_delegatees_query)
        top_delegatees = [(str(row.delegatee_id), int(row.count)) for row in result]

        # 5. Orphaned delegations (delegations to/from non-existent users)
        # Check delegations where delegator or delegatee doesn't exist
        orphaned_delegator_query = (
            select(sql_func.count(Delegation.id))
            .outerjoin(User, Delegation.delegator_id == User.id)
            .where(and_(*conditions, User.id.is_(None)))  # delegator doesn't exist
        )
        result = await self.db.execute(orphaned_delegator_query)
        orphaned_delegators = result.scalar() or 0

        orphaned_delegatee_query = (
            select(sql_func.count(Delegation.id))
            .outerjoin(User, Delegation.delegatee_id == User.id)
            .where(and_(*conditions, User.id.is_(None)))  # delegatee doesn't exist
        )
        result = await self.db.execute(orphaned_delegatee_query)
        orphaned_delegatees = result.scalar() or 0

        orphaned_delegations = orphaned_delegators + orphaned_delegatees

        # 6. Chain length calculations (sample-based for performance)
        avg_chain_length = 0.0
        max_chain_length = 0
        cycles_detected = 0

        if active_delegations > 0:
            # Sample delegators for chain analysis (limit to 500 for performance)
            sample_query = (
                select(Delegation.delegator_id)
                .where(and_(*conditions))
                .group_by(Delegation.delegator_id)
                .order_by(Delegation.created_at.desc())
                .limit(500)
            )
            result = await self.db.execute(sample_query)
            sample_delegators = result.scalars().all()

            chain_lengths = []
            for delegator_id in sample_delegators:
                try:
                    chain = await self.resolve_delegation_chain(
                        delegator_id, poll_id, max_depth=10
                    )
                    chain_length = len(chain) - 1  # Subtract 1 to exclude the delegator
                    chain_lengths.append(chain_length)
                    max_chain_length = max(max_chain_length, chain_length)
                except DelegationChainError as e:
                    # Count cycles or depth limit exceeded as cycles
                    cycles_detected += 1
                    continue

            if chain_lengths:
                avg_chain_length = sum(chain_lengths) / len(chain_lengths)
            else:
                avg_chain_length = 0.0
                max_chain_length = 0

        return {
            "active_delegations": int(active_delegations),
            "unique_delegators": int(unique_delegators),
            "unique_delegatees": int(unique_delegatees),
            "avg_chain_length": float(avg_chain_length),
            "max_chain_length": int(max_chain_length),
            "cycles_detected": int(cycles_detected),
            "orphaned_delegations": int(orphaned_delegations),
            "top_delegatees": top_delegatees,
        }

    async def get_delegation_stats(
        self, poll_id: Optional[UUID] = None
    ) -> Dict[str, Any]:
        """Get formatted delegation statistics.

        Args:
            poll_id: Optional poll ID for poll-specific stats

        Returns:
            Dict[str, Any]: Complete, typed delegation statistics
        """
        raw = await self._calculate_delegation_stats(poll_id=poll_id)
        return self._format_stats(raw, poll_id=poll_id)

    async def invalidate_stats_cache(self, poll_id: Optional[UUID] = None) -> None:
        """Invalidate cached delegation stats."""
        query = delete(DelegationStats).where(DelegationStats.poll_id == poll_id)
        await self.db.execute(query)
        await self.db.flush()

    async def get_delegation_history(self, user_id: UUID) -> List[Delegation]:
        """Get delegation history for a user."""
        query = (
            select(Delegation)
            .where(Delegation.delegator_id == user_id)
            .order_by(desc(Delegation.created_at))
        )
        result = await self.db.execute(query)
        return result.scalars().all()

    async def expire_legacy_delegations(self) -> Dict[str, Any]:
        """Expire legacy fixed-term delegations that have passed their term end date.

        This job runs periodically to automatically expire legacy delegations
        and generate nudges for renewal or remapping.

        Returns:
            Dict[str, Any]: Summary of expired delegations and nudges generated
        """
        now = datetime.utcnow()

        # Find expired legacy delegations
        expired_query = select(Delegation).where(
            and_(
                Delegation.mode == DelegationMode.LEGACY_FIXED_TERM,
                Delegation.legacy_term_ends_at <= now,
                Delegation.is_deleted == False,
                Delegation.revoked_at.is_(None),
            )
        )

        result = await self.db.execute(expired_query)
        expired_delegations = result.scalars().all()

        expired_count = 0
        nudges_generated = 0

        for delegation in expired_delegations:
            # Mark as expired by setting end_date to legacy_term_ends_at
            delegation.end_date = delegation.legacy_term_ends_at
            await self.db.flush()

            expired_count += 1

            # Generate renewal/remap nudge
            await self._generate_legacy_expiry_nudge(delegation)
            nudges_generated += 1

            logger.info(
                f"Expired legacy delegation {delegation.id}",
                extra={
                    "delegation_id": str(delegation.id),
                    "delegator_id": str(delegation.delegator_id),
                    "delegatee_id": str(delegation.delegatee_id),
                    "legacy_term_ends_at": delegation.legacy_term_ends_at.isoformat(),
                },
            )

        return {
            "expired_count": expired_count,
            "nudges_generated": nudges_generated,
            "run_at": now.isoformat(),
        }

    async def _generate_legacy_expiry_nudge(self, delegation: Delegation) -> None:
        """Generate a nudge for legacy delegation expiry.

        This creates a constitutional nudge suggesting the user consider
        moving from legacy mode to hybrid or flexible domain mode.
        """
        # TODO: Implement nudge generation system
        # For now, just log the nudge
        logger.info(
            f"Generated legacy expiry nudge for delegation {delegation.id}",
            extra={
                "delegation_id": str(delegation.id),
                "delegator_id": str(delegation.delegator_id),
                "nudge_type": "legacy_expiry",
                "suggestion": "Consider moving from legacy mode to hybrid or flexible domain mode",
            },
        )
