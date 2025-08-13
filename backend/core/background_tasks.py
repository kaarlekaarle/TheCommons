"""Background tasks module."""

import asyncio
from datetime import datetime, timedelta
from typing import Any, Dict, Optional
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import delete

from backend.core.logging_config import get_logger
from backend.models.delegation_stats import DelegationStats

logger = get_logger(__name__)

DEFAULT_DELEGATION_STATS = {
    "active_delegations": 0,
    "unique_delegators": 0,
    "unique_delegatees": 0,
    "avg_chain_length": 0.0,
    "max_chain_length": 0,
    "cycles_detected": 0,
    "orphaned_delegations": 0,
    "top_delegatees": [],  # list of [delegatee_id, count]
}

def _merge_stats_with_defaults(stats: dict | None) -> dict:
    # Defensive merge so missing keys don't blow up the cache step
    base = DEFAULT_DELEGATION_STATS.copy()
    if stats:
        base.update(stats)
        # If a provider accidentally returns None for a key, coerce to default
        for k, v in DEFAULT_DELEGATION_STATS.items():
            if base.get(k) is None:
                base[k] = v
    return base

class StatsCalculationTask:
    """Background task for calculating delegation statistics."""

    def __init__(
        self, db: AsyncSession, delegation_service: Any
    ) -> None:
        self.db = db
        self.delegation_service = delegation_service
        self.retry_attempts = 3
        self.retry_delay = timedelta(seconds=5)

    async def calculate_stats(self, poll_id: Optional[UUID] = None) -> None:
        """Calculate and cache delegation statistics.

        Args:
            poll_id: Optional poll ID to calculate stats for
        """
        for attempt in range(self.retry_attempts):
            try:
                # Calculate fresh stats
                stats = await self.delegation_service._calculate_delegation_stats(
                    poll_id
                )

                # Cache the stats
                await self._cache_stats(stats, poll_id)

                logger.info(
                    "Successfully calculated and cached delegation stats",
                    extra={"poll_id": poll_id, "attempt": attempt + 1},
                )
                return

            except Exception as e:
                logger.error(
                    "Failed to calculate delegation stats",
                    extra={"poll_id": poll_id, "attempt": attempt + 1, "error": str(e)},
                    exc_info=True,
                )

                if attempt < self.retry_attempts - 1:
                    # Wait before retrying
                    await asyncio.sleep(self.retry_delay.total_seconds())
                else:
                    # Log final failure
                    logger.error(
                        "Failed to calculate delegation stats after all retries",
                        extra={"poll_id": poll_id},
                    )
                    raise

    async def _cache_stats(
        self, stats: Dict[str, Any], poll_id: Optional[UUID] = None
    ) -> None:
        """Cache delegation statistics.

        Args:
            stats: Statistics to cache
            poll_id: Optional poll ID the stats are for
        """
        try:
            # Apply defensive defaults to prevent KeyError
            stats = _merge_stats_with_defaults(stats)
            
            # Log if defaults were applied
            if stats != _merge_stats_with_defaults({k: stats.get(k) for k in DEFAULT_DELEGATION_STATS}):
                logger.warning("delegation_stats: applied defaults for missing/None keys")
            
            # Convert top_delegatees to a JSON-serializable format
            top_delegatees = [
                {"delegatee_id": str(delegatee_id), "count": count}
                for delegatee_id, count in stats.get("top_delegatees", [])
            ]

            delegation_stats = DelegationStats(
                poll_id=poll_id,
                top_delegatees=top_delegatees,
                avg_chain_length=float(stats["avg_chain_length"]),
                longest_chain=int(stats["max_chain_length"]),  # Use max_chain_length from defaults
                active_delegations=int(stats["active_delegations"]),
                calculated_at=datetime.utcnow()
            )
            self.db.add(delegation_stats)
            await self.db.commit()
        except Exception as e:
            logger.error(f"Error caching delegation stats: {e}")
            await self.db.rollback()
            raise

    async def cleanup_old_stats(self, max_age: timedelta = timedelta(days=7)) -> None:
        """Clean up old statistics entries.

        Args:
            max_age: Maximum age of stats entries to keep
        """
        try:
            cutoff_date = datetime.utcnow() - max_age
            await self.db.execute(
                delete(DelegationStats).where(
                    DelegationStats.calculated_at < cutoff_date
                )
            )
            await self.db.commit()

            logger.info(
                "Cleaned up old delegation stats", extra={"cutoff_date": cutoff_date}
            )
        except Exception as e:
            logger.error(
                "Failed to clean up old delegation stats",
                extra={"error": str(e)},
                exc_info=True,
            )
            await self.db.rollback()
            raise 