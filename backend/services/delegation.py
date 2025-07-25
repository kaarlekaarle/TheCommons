from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional, Tuple
from uuid import UUID

from sqlalchemy import and_, delete, desc, func, or_, select, text, bindparam
from sqlalchemy.ext.asyncio import AsyncSession

from backend.core.exceptions import ResourceNotFoundError
from backend.core.exceptions.delegation import (
    CircularDelegationError,
    DelegationAlreadyExistsError,
    DelegationChainError,
    DelegationLimitExceededError,
    DelegationNotFoundError,
    DelegationStatsError,
    InvalidDelegationPeriodError,
    PostVoteDelegationError,
    SelfDelegationError,
)
from backend.models.delegation import Delegation
from backend.models.vote import Vote
from backend.core.logging_config import get_logger
from backend.models.delegation_stats import DelegationStats

logger = get_logger(__name__)



class DelegationService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db
        self.stats_cache_ttl = timedelta(minutes=5)
        # Import here to avoid circular dependency with StatsCalculationTask
        from backend.core.background_tasks import StatsCalculationTask
        self.stats_task = StatsCalculationTask(db, self)

    async def create_delegation(
        self,
        delegator_id: UUID,
        delegatee_id: UUID,
        poll_id: Optional[UUID] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> Delegation:
        """Create a new delegation.

        Args:
            delegator_id: ID of the delegating user
            delegatee_id: ID of the delegatee
            poll_id: Optional poll ID for poll-specific delegation
            start_date: Optional start date for the delegation
            end_date: Optional end date for the delegation

        Returns:
            Delegation: The created delegation

        Raises:
            SelfDelegationError: If user tries to delegate to themselves
            CircularDelegationError: If delegation would create a circular chain
            DelegationAlreadyExistsError: If overlapping delegation exists
            InvalidDelegationPeriodError: If dates are invalid
        """
        # Set default dates if not provided
        if start_date is None:
            start_date = func.now()
        if end_date is not None and end_date <= start_date:
            raise InvalidDelegationPeriodError(
                message="End date must be after start date",
                details={
                    "start_date": start_date.isoformat(),
                    "end_date": end_date.isoformat(),
                },
            )

        # Check for self-delegation
        if delegator_id == delegatee_id:
            raise SelfDelegationError(str(delegator_id))

        # Check for circular delegation
        if await self._would_create_circular_delegation(delegator_id, delegatee_id, poll_id):
            raise CircularDelegationError(str(delegator_id), str(delegatee_id))

        # Check for overlapping delegations
        now = func.now()
        conditions = [
            Delegation.delegator_id == delegator_id,
            Delegation.delegatee_id == delegatee_id,
            or_(
                # New delegation starts during existing one
                and_(
                    Delegation.start_date <= bindparam('start_date'),
                    or_(
                        Delegation.end_date.is_(None),
                        Delegation.end_date > bindparam('start_date'),
                    ),
                ),
                # New delegation ends during existing one
                and_(
                    Delegation.start_date <= bindparam('end_date') if end_date else now,
                    or_(
                        Delegation.end_date.is_(None),
                        Delegation.end_date > bindparam('end_date') if end_date else now,
                    ),
                ),
                # New delegation completely contains existing one
                and_(
                    Delegation.start_date >= bindparam('start_date'),
                    or_(
                        Delegation.end_date.is_(None),
                        and_(
                            end_date is not None,
                            Delegation.end_date <= bindparam('end_date'),
                        ),
                    ),
                ),
            ),
        ]

        if poll_id is not None:
            conditions.append(Delegation.poll_id == poll_id)
        else:
            conditions.append(Delegation.poll_id.is_(None))

        query = select(Delegation).where(and_(*conditions))
        params = {'start_date': start_date}
        if end_date:
            params['end_date'] = end_date
        result = await self.db.execute(query.params(**params))
        existing = result.scalar_one_or_none()

        if existing:
            raise DelegationAlreadyExistsError(
                str(delegator_id),
                str(delegatee_id),
                details={
                    "existing_delegation_id": str(existing.id),
                    "start_date": existing.start_date.isoformat(),
                    "end_date": existing.end_date.isoformat() if existing.end_date else None,
                },
            )

        # Create new delegation
        delegation = Delegation(
            delegator_id=delegator_id,
            delegatee_id=delegatee_id,
            poll_id=poll_id,
            start_date=start_date,
            end_date=end_date,
            chain_origin_id=delegator_id,
        )

        self.db.add(delegation)
        await self.db.flush()
        await self.db.refresh(delegation)

        # Invalidate stats cache
        await self.invalidate_stats_cache(poll_id)

        return delegation

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

        if delegation.end_date:
            return  # Already revoked, idempotent success

        delegation.end_date = func.now()
        await self.db.flush()

        # Trigger stats recalculation
        await self.stats_task.calculate_stats(delegation.poll_id)

    async def get_active_delegation(
        self, user_id: UUID, poll_id: Optional[UUID] = None
    ) -> Optional[Delegation]:
        """Get active delegation for a user and optional poll."""
        now = func.now()

        # Base conditions for active delegation
        conditions = [
            Delegation.delegator_id == user_id,
            or_(Delegation.end_date.is_(None), Delegation.end_date > now),
            Delegation.start_date <= now,
        ]

        # Add poll-specific condition
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
        include_path: bool = False,
        max_depth: int = 10,
    ) -> Tuple[UUID, Optional[List[UUID]]]:
        """Resolve the delegation chain for a user.

        Args:
            user_id: ID of the user to resolve chain for
            poll_id: Optional poll ID for poll-specific delegation
            include_path: Whether to include the full delegation path
            max_depth: Maximum chain depth to prevent infinite loops

        Returns:
            Tuple[UUID, Optional[List[UUID]]]: Final delegatee ID and optional path

        Raises:
            DelegationChainError: If circular delegation detected or max depth exceeded
        """
        current_id = user_id
        path = [current_id] if include_path else None
        depth = 0

        while depth < max_depth:
            delegation = await self.get_active_delegation(current_id, poll_id)
            if not delegation:
                break

            current_id = delegation.delegatee_id
            if include_path:
                if current_id in path:
                    raise DelegationChainError(
                        message="Circular delegation detected",
                        details={"path": [str(p) for p in path]},
                    )
                path.append(current_id)
            depth += 1

        if depth >= max_depth:
            raise DelegationChainError(
                message="Delegation chain depth limit exceeded",
                details={"max_depth": max_depth},
            )

        return current_id, path

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
        """
        try:
            final_delegatee, _ = await self.resolve_delegation_chain(
                delegatee_id, poll_id, include_path=True
            )
            return final_delegatee == delegator_id
        except DelegationChainError:
            # If we hit a circular delegation or depth limit, it means we would create a cycle
            return True

    async def get_active_delegations(self, user_id: UUID) -> List[Delegation]:
        """Get all active delegations for a user.

        Args:
            user_id: ID of the user to get delegations for

        Returns:
            List[Delegation]: List of active delegations
        """
        now = func.now()
        query = (
            select(Delegation)
            .where(
                and_(
                    Delegation.delegator_id == user_id,
                    or_(Delegation.end_date.is_(None), Delegation.end_date > now),
                    Delegation.start_date <= now,
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
            return self._format_stats(cached_stats)

        # Calculate fresh stats
        stats = await self._calculate_delegation_stats(poll_id)
        formatted_stats = self._format_stats(stats)

        # Cache the results
        await self._cache_stats(stats, poll_id)

        # Trigger background refresh
        await self._trigger_background_refresh(poll_id)

        return formatted_stats

    async def _get_cached_stats(
        self, poll_id: Optional[UUID] = None
    ) -> Optional[Any]:
        """Get cached delegation stats if they exist and are still valid."""
        query = select(DelegationStats).where(
            DelegationStats.poll_id == poll_id
        )
        result = await self.db.execute(query)
        stats = result.scalar_one_or_none()
        if not stats:
            return None
        # Check if cache is still valid
        now = datetime.utcnow()
        if stats.calculated_at and (now - stats.calculated_at).total_seconds() > self.stats_cache_ttl.total_seconds():
            return None
        return stats

    def _format_stats(self, stats: Any) -> Dict[str, Any]:
        """Format delegation statistics.

        Args:
            stats: Raw statistics data

        Returns:
            Dict[str, Any]: Formatted statistics
        """
        return {
            "active_delegations": stats.get("active_delegations", 0),
            "total_delegations": stats.get("total_delegations", 0),
            "delegation_chains": stats.get("delegation_chains", []),
            "delegation_depth": stats.get("delegation_depth", {}),
            "poll_specific": stats.get("poll_specific", False),
            "poll_id": str(stats.get("poll_id")) if stats.get("poll_id") else None,
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
            longest_chain=stats["longest_chain"],
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
            Dict[str, Any]: Calculated statistics
        """
        now = func.now()
        conditions = [
            or_(Delegation.end_date.is_(None), Delegation.end_date > now),
            Delegation.start_date <= now,
        ]

        if poll_id is not None:
            conditions.append(Delegation.poll_id == poll_id)
        else:
            conditions.append(Delegation.poll_id.is_(None))

        # Get active delegations
        query = select(Delegation).where(and_(*conditions))
        result = await self.db.execute(query)
        active_delegations = result.scalars().all()

        # Calculate chain depths and paths
        delegation_chains = []
        delegation_depth = {}
        for delegation in active_delegations:
            try:
                final_delegatee, path = await self.resolve_delegation_chain(
                    delegation.delegator_id,
                    poll_id,
                    include_path=True,
                )
                chain_length = len(path) - 1  # Subtract 1 to exclude the delegator
                delegation_chains.append({
                    "delegator_id": str(delegation.delegator_id),
                    "final_delegatee_id": str(final_delegatee),
                    "chain_length": chain_length,
                    "path": [str(p) for p in path],
                })
                delegation_depth[str(delegation.delegator_id)] = chain_length
            except DelegationChainError:
                # Skip invalid chains
                continue

        return {
            "active_delegations": len(active_delegations),
            "total_delegations": len(active_delegations),
            "delegation_chains": delegation_chains,
            "delegation_depth": delegation_depth,
            "poll_specific": poll_id is not None,
            "poll_id": poll_id,
        }

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
