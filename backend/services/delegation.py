from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional, Tuple
from uuid import UUID

from sqlalchemy import and_, delete, desc, func, or_, select, text
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
        """Create a new delegation."""
        # Validate self-delegation
        if delegator_id == delegatee_id:
            raise SelfDelegationError(str(delegator_id))

        # Set default dates if not provided
        if start_date is None:
            start_date = datetime.utcnow()
        if end_date is not None and end_date <= start_date:
            raise InvalidDelegationPeriodError(str(delegator_id))

        # Check if user has already voted
        if poll_id is not None:
            vote = await self.db.execute(
                select(Vote).where(
                    and_(Vote.user_id == delegator_id, Vote.poll_id == poll_id)
                )
            )
            if vote.scalar_one_or_none():
                raise PostVoteDelegationError(str(delegator_id), str(poll_id))

        # Check for existing active delegation with overlapping period for the same delegatee
        overlap_or_conditions = [
            # New delegation starts during an existing one
            and_(
                Delegation.start_date <= start_date,
                or_(Delegation.end_date.is_(None), Delegation.end_date > start_date),
            )
        ]
        if end_date is not None:
            overlap_or_conditions.append(
                # New delegation ends during an existing one
                and_(
                    Delegation.start_date <= end_date,
                    or_(Delegation.end_date.is_(None), Delegation.end_date > end_date),
                )
            )
            overlap_or_conditions.append(
                # New delegation completely contains an existing one
                and_(
                    Delegation.start_date >= start_date,
                    Delegation.end_date.isnot(None),
                    Delegation.end_date <= end_date,
                )
            )
        overlap_conditions = [
            Delegation.delegator_id == delegator_id,
            Delegation.delegatee_id == delegatee_id,
            or_(*overlap_or_conditions),
        ]

        # Add poll_id condition if specified
        if poll_id is not None:
            overlap_conditions.append(Delegation.poll_id == poll_id)
        else:
            overlap_conditions.append(Delegation.poll_id.is_(None))

        existing = await self.db.execute(
            select(Delegation).where(and_(*overlap_conditions))
        )
        if existing.scalar_one_or_none():
            raise DelegationAlreadyExistsError(str(delegator_id), str(delegatee_id))

        # Check for circular delegation
        if poll_id is not None:
            final_delegatee = await self.resolve_delegation_chain(delegatee_id, poll_id)
            if final_delegatee == delegator_id:
                raise CircularDelegationError(str(delegator_id), str(delegatee_id))

        # Check delegation limit
        if poll_id is not None:
            active_count = await self.db.execute(
                select(func.count())
                .select_from(Delegation)
                .where(
                    and_(
                        Delegation.delegator_id == delegator_id,
                        Delegation.poll_id == poll_id,
                        or_(
                            Delegation.end_date.is_(None),
                            Delegation.end_date > datetime.utcnow(),
                        ),
                    )
                )
            )
            if active_count.scalar_one() >= 5:
                raise DelegationLimitExceededError(str(delegator_id))

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

        # Trigger stats recalculation
        await self.stats_task.calculate_stats(poll_id)

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

        delegation.end_date = datetime.utcnow()
        await self.db.flush()

        # Trigger stats recalculation
        await self.stats_task.calculate_stats(delegation.poll_id)

    async def get_active_delegation(
        self, user_id: UUID, poll_id: Optional[UUID] = None
    ) -> Optional[Delegation]:
        """Get active delegation for a user and optional poll."""
        now = datetime.now(timezone.utc)

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
            .order_by(Delegation.created_at.desc())
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
        """Resolve a delegation chain to find the final delegatee.

        Args:
            user_id: ID of the user to start from
            poll_id: Optional poll ID to filter by
            include_path: Whether to include the full delegation path
            max_depth: Maximum chain depth to prevent infinite loops

        Returns:
            Tuple[UUID, Optional[List[UUID]]]: Final delegatee ID and optional path

        Raises:
            DelegationChainError: If chain is too long or circular
        """
        visited = set()
        path = [user_id]
        current_id = user_id
        depth = 0

        while depth < max_depth:
            # Get active delegation for current user
            delegation = await self.get_active_delegation(current_id, poll_id)
            if not delegation:
                break

            # Check for circular delegation
            if delegation.delegatee_id in visited:
                error_msg = (
                    f"Circular delegation detected: "
                    f"{path} -> {delegation.delegatee_id}"
                )
                raise DelegationChainError(error_msg)

            # Move to next delegatee
            current_id = delegation.delegatee_id
            visited.add(current_id)
            path.append(current_id)
            depth += 1

        if depth >= max_depth:
            error_msg = (
                f"Delegation chain too long (max {max_depth}): "
                f"{path}"
            )
            raise DelegationChainError(error_msg)

        return (current_id, path if include_path else None)

    async def _would_create_circular_delegation(
        self, delegator_id: UUID, delegatee_id: UUID, poll_id: Optional[UUID]
    ) -> bool:
        """Check if creating a delegation would create a circular chain."""
        visited = {delegator_id}
        current_id = delegatee_id
        depth = 0
        max_depth = 5

        while depth < max_depth:
            if current_id in visited:
                return True

            # Get active delegation
            delegation = await self.get_active_delegation(current_id, poll_id)
            if not delegation:
                # No active delegation, no circular chain possible
                return False

            visited.add(current_id)
            current_id = delegation.delegatee_id
            depth += 1

        # If we reach max depth without finding a cycle, assume no circular chain
        return False

    async def get_active_delegations(self, user_id: UUID) -> List[Delegation]:
        """Get all active delegations for a user."""
        now = datetime.now(timezone.utc)

        # Base conditions for active delegations
        conditions = [
            Delegation.delegator_id == user_id,
            Delegation.start_date <= now,
            or_(Delegation.end_date.is_(None), Delegation.end_date > now),
        ]

        query = (
            select(Delegation)
            .where(and_(*conditions))
            .order_by(desc(Delegation.start_date), desc(Delegation.created_at))
        )
        result = await self.db.execute(query)
        return result.scalars().all()

    async def check_voting_allowed(self, user_id: UUID, poll_id: UUID) -> bool:
        """Check if a user is allowed to vote (no active delegation)."""
        delegation = await self.get_active_delegation(user_id, poll_id)
        if delegation:
            raise ValueError("Cannot vote while having an active delegation")
        return True

    async def get_delegation_stats(
        self, poll_id: Optional[UUID] = None
    ) -> Dict[str, Any]:
        """Get delegation statistics.

        Args:
            poll_id: Optional poll ID to get stats for

        Returns:
            Dict[str, Any]: Dict containing delegation statistics
        """
        # Import here to avoid circular dependency with DelegationStats model
        from backend.models.delegation_stats import DelegationStats
        
        # Try to get cached stats
        cached_stats = await self._get_cached_stats(poll_id)
        if cached_stats:
            return self._format_stats(cached_stats)

        # Calculate new stats
        stats = await self._calculate_delegation_stats(poll_id)

        # Cache the stats
        await self._cache_stats(stats, poll_id)

        # Trigger background refresh
        await self._trigger_background_refresh(poll_id)

        return stats

    async def _get_cached_stats(
        self, poll_id: Optional[UUID] = None
    ) -> Optional[Any]:
        """Get cached stats if they exist and are not expired."""
        # Import here to avoid circular dependency with DelegationStats model
        from backend.models.delegation_stats import DelegationStats
        
        if poll_id is not None:
            query = (
                select(DelegationStats)
                .where(DelegationStats.poll_id == poll_id)
                .order_by(DelegationStats.calculated_at.desc())
            )
        else:
            query = (
                select(DelegationStats)
                .where(DelegationStats.poll_id.is_(None))
                .order_by(DelegationStats.calculated_at.desc())
            )
        result = await self.db.execute(query)
        stats = result.first()
        if not stats:
            return None
        stats = stats[0]  # unpack from tuple
        if datetime.utcnow() - stats.calculated_at > self.stats_cache_ttl:
            return None
        return stats

    def _format_stats(self, stats: Any) -> Dict[str, Any]:
        """Format cached stats into response format."""
        return {
            "top_delegatees": stats.top_delegatees,
            "avg_chain_length": stats.avg_chain_length,
            "longest_chain": stats.longest_chain,
            "active_delegations": stats.active_delegations,
        }

    async def _trigger_background_refresh(self, poll_id: Optional[UUID] = None) -> None:
        """Trigger background refresh of statistics."""
        try:
            await self.stats_task.calculate_stats(poll_id)
        except Exception as e:
            logger.error(
                "Failed to trigger background stats refresh",
                extra={"poll_id": poll_id, "error": str(e)},
                exc_info=True,
            )

    async def _cache_stats(
        self, stats: Dict[str, Any], poll_id: Optional[UUID] = None
    ) -> None:
        """Cache delegation statistics."""
        # Import here to avoid circular dependency with DelegationStats model
        from backend.models.delegation_stats import DelegationStats
        
        cached_stats = DelegationStats(
            top_delegatees=stats["top_delegatees"],
            avg_chain_length=stats["avg_chain_length"],
            longest_chain=stats["longest_chain"],
            active_delegations=stats["active_delegations"],
            poll_id=poll_id,
        )
        self.db.add(cached_stats)
        await self.db.commit()

    async def _calculate_delegation_stats(
        self, poll_id: Optional[UUID] = None
    ) -> Dict[str, Any]:
        """Calculate delegation statistics."""
        now = datetime.now(timezone.utc)

        # Base conditions for active delegations
        conditions = [
            Delegation.start_date <= now,
            or_(Delegation.end_date.is_(None), Delegation.end_date > now),
        ]

        # Add poll-specific condition if poll_id is provided
        if poll_id is not None:
            conditions.append(Delegation.poll_id == poll_id)
        else:
            conditions.append(Delegation.poll_id.is_(None))

        # Get count of active delegations
        count_query = (
            select(func.count()).select_from(Delegation).where(and_(*conditions))
        )
        result = await self.db.execute(count_query)
        active_delegations = result.scalar_one()

        # Get top delegatees with improved query
        delegatee_query = (
            select(
                Delegation.delegatee_id,
                func.count(Delegation.delegatee_id).label("count"),
            )
            .where(and_(*conditions))
            .group_by(Delegation.delegatee_id)
            .order_by(desc("count"))
            .limit(10)
        )
        result = await self.db.execute(delegatee_query)
        top_delegatees = result.all()

        # Calculate chain lengths with optimized query
        chain_lengths = []
        delegations_query = select(Delegation).where(and_(*conditions))
        result = await self.db.execute(delegations_query)
        active_delegations_list = result.scalars().all()

        for delegation in active_delegations_list:
            chain_length = 1
            current = delegation
            visited = {current.delegator_id}

            while (
                current.delegatee_id is not None and current.delegatee_id not in visited
            ):
                visited.add(current.delegatee_id)
                delegatee_query = select(Delegation).where(
                    and_(
                        Delegation.delegator_id == current.delegatee_id,
                        Delegation.start_date <= now,
                        or_(Delegation.end_date.is_(None), Delegation.end_date > now),
                    )
                )
                result = await self.db.execute(delegatee_query)
                next_delegation = result.scalar_one_or_none()
                if next_delegation is None:
                    break
                current = next_delegation
                chain_length += 1

                if chain_length >= 10:  # Prevent infinite loops
                    break

            chain_lengths.append(chain_length)

        return {
            "active_delegations": active_delegations,
            "top_delegatees": top_delegatees,
            "avg_chain_length": (
                sum(chain_lengths) / len(chain_lengths) if chain_lengths else 0
            ),
            "longest_chain": max(chain_lengths) if chain_lengths else 0,
            "calculated_at": now,
        }

    async def invalidate_stats_cache(self, poll_id: Optional[UUID] = None) -> None:
        """Invalidate cached statistics for a poll or all polls."""
        # Import here to avoid circular dependency with DelegationStats model
        from backend.models.delegation_stats import DelegationStats
        
        try:
            if poll_id is not None:
                query = select(DelegationStats).where(
                    DelegationStats.poll_id == poll_id
                )
            else:
                query = select(DelegationStats).where(DelegationStats.poll_id.is_(None))
            result = await self.db.execute(query)
            stats = result.scalars().all()

            for stat in stats:
                await self.db.delete(stat)
            await self.db.commit()

            # Trigger background refresh
            await self._trigger_background_refresh(poll_id)
        except Exception as e:
            logger.error(
                "Failed to invalidate stats cache",
                extra={"poll_id": poll_id, "error": str(e)},
                exc_info=True,
            )
            await self.db.rollback()
            raise

    async def get_delegation_history(self, user_id: UUID) -> List[Delegation]:
        """Get delegation history for a user."""
        now = datetime.now(timezone.utc)
        query = (
            select(Delegation)
            .where(
                and_(
                    Delegation.delegator_id == user_id,
                    or_(Delegation.end_date.is_(None), Delegation.end_date > now),
                )
            )
            .order_by(desc(Delegation.start_date), desc(Delegation.created_at))
        )

        result = await self.db.execute(query)
        delegations = result.scalars().all()
        return delegations
