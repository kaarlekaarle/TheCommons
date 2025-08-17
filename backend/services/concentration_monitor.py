"""Concentration monitoring service for anti-hierarchy delegation features.

This service monitors delegation concentration to prevent power accumulation.
"""

from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple
from uuid import UUID

from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.core.logging_config import get_logger
from backend.models.delegation import Delegation

logger = get_logger(__name__)


class ConcentrationMonitorService:
    """Service for monitoring delegation concentration."""

    def __init__(self, db: AsyncSession) -> None:
        """Initialize the concentration monitor service.
        
        Args:
            db: Database session for queries
        """
        self.db = db
        self.warn_threshold = 0.075  # 7.5% threshold for warning
        self.high_threshold = 0.15  # 15% threshold for high concentration

    async def percent_to_delegatee(
        self, delegatee_id: UUID, field_id: Optional[UUID] = None
    ) -> float:
        """Calculate what percentage of delegations go to a specific delegatee.

        Args:
            delegatee_id: ID of the delegatee to check
            field_id: Optional field ID to scope the calculation

        Returns:
            float: Percentage (0.0 to 1.0) of delegations going to this delegatee
        """
        try:
            # Build base query for active delegations
            base_query = select(Delegation).where(
                and_(
                    Delegation.is_deleted.is_(False),
                    Delegation.revoked_at.is_(None),
                    Delegation.end_date.is_(None)
                    | (Delegation.end_date > datetime.utcnow()),
                )
            )

            # Add field scope if provided
            if field_id:
                base_query = base_query.where(Delegation.field_id == field_id)

            # Count total active delegations
            total_result = await self.db.execute(
                select(func.count()).select_from(base_query.subquery())
            )
            total_delegations = total_result.scalar() or 0

            if total_delegations == 0:
                return 0.0

            # Count delegations to this delegatee
            delegatee_query = base_query.where(Delegation.delegatee_id == delegatee_id)
            delegatee_result = await self.db.execute(
                select(func.count()).select_from(delegatee_query.subquery())
            )
            delegatee_delegations = delegatee_result.scalar() or 0

            return delegatee_delegations / total_delegations

        except Exception as e:
            logger.error(
                f"Error calculating concentration for delegatee {delegatee_id}: {e}"
            )
            return 0.0

    async def is_high_concentration(
        self,
        delegatee_id: UUID,
        field_id: Optional[UUID] = None,
        warn: float = 0.075,
        high: float = 0.15,
    ) -> Tuple[bool, str, float]:
        """Check if a delegatee has high concentration of delegations.

        Args:
            delegatee_id: ID of the delegatee to check
            field_id: Optional field ID to scope the check
            warn: Warning threshold (default 7.5%)
            high: High concentration threshold (default 15%)

        Returns:
            Tuple[bool, str, float]: (is_high, level, percent)
                - is_high: True if concentration exceeds warn threshold
                - level: "warn" or "high" indicating severity
                - percent: Actual concentration percentage (0.0 to 1.0)
        """
        try:
            percent = await self.percent_to_delegatee(delegatee_id, field_id)

            if percent >= high:
                return True, "high", percent
            elif percent >= warn:
                return True, "warn", percent
            else:
                return False, "", percent

        except Exception as e:
            logger.error(
                f"Error checking concentration for delegatee {delegatee_id}: {e}"
            )
            return False, "", 0.0

    async def calculate_delegation_concentration(
        self, poll_id: Optional[UUID] = None
    ) -> Dict[str, Any]:
        """Calculate delegation concentration for all delegates."""
        try:
            # Get all active delegations
            query = select(Delegation).where(
                and_(
                    Delegation.is_deleted.is_(False),
                    Delegation.revoked_at.is_(None),
                    Delegation.end_date.is_(None)
                    | (Delegation.end_date > datetime.utcnow()),
                )
            )

            if poll_id:
                query = query.where(Delegation.poll_id == poll_id)

            result = await self.db.execute(query)
            delegations = result.scalars().all()

            # Count delegations per delegatee
            delegatee_counts: Dict[str, int] = {}
            total_delegations = len(delegations)

            for delegation in delegations:
                delegatee_id = str(delegation.delegatee_id)
                delegatee_counts[delegatee_id] = (
                    delegatee_counts.get(delegatee_id, 0) + 1
                )

            # Calculate concentrations
            concentration_data = []
            alerts = []

            for delegatee_id, count in delegatee_counts.items():
                percent = count / total_delegations if total_delegations > 0 else 0.0
                concentration_data.append(
                    {
                        "delegatee_id": delegatee_id,
                        "delegation_count": count,
                        "percentage": percent,
                    }
                )

                # Check for alerts
                if percent >= self.high_threshold:
                    alerts.append(
                        {
                            "delegatee_id": delegatee_id,
                            "level": "high",
                            "percentage": percent,
                            "message": f"High concentration: {percent:.1%} of delegations",
                        }
                    )
                elif percent >= self.warn_threshold:
                    alerts.append(
                        {
                            "delegatee_id": delegatee_id,
                            "level": "warn",
                            "percentage": percent,
                            "message": f"Warning concentration: {percent:.1%} of delegations",
                        }
                    )

            return {
                "concentration_data": concentration_data,
                "alerts": alerts,
                "total_delegations": total_delegations,
                "calculated_at": datetime.utcnow(),
            }

        except Exception as e:
            logger.error(f"Error calculating delegation concentration: {e}")
            return {
                "concentration_data": [],
                "alerts": [],
                "total_delegations": 0,
                "calculated_at": datetime.utcnow(),
                "error": str(e),
            }

    async def check_concentration_alerts(
        self, poll_id: Optional[UUID] = None
    ) -> List[Dict[str, Any]]:
        """Check for concentration alerts above threshold."""
        try:
            concentration_data = await self.calculate_delegation_concentration(poll_id)
            return concentration_data.get("alerts", [])
        except Exception as e:
            logger.error(f"Error checking concentration alerts: {e}")
            return []

    async def get_soft_cap_warnings(
        self, poll_id: Optional[UUID] = None
    ) -> List[Dict[str, Any]]:
        """Get soft cap warnings for high concentration delegates."""
        try:
            alerts = await self.check_concentration_alerts(poll_id)
            return [alert for alert in alerts if alert["level"] == "high"]
        except Exception as e:
            logger.error(f"Error getting soft cap warnings: {e}")
            return []
