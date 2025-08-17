"""
Concentration monitoring service for delegation patterns.

Detects when a single delegatee has too high a percentage of delegations,
which could indicate concentration of power.
"""

import logging
from typing import Optional, Tuple
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import func, select, and_
from sqlalchemy.orm import selectinload

from backend.models.delegation import Delegation
from backend.models.user import User
from backend.models.field import Field

logger = logging.getLogger(__name__)


class ConcentrationMonitorService:
    """Service for monitoring delegation concentration patterns."""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def percent_to_delegatee(
        self, 
        delegatee_id: UUID, 
        field_id: Optional[UUID] = None
    ) -> float:
        """
        Calculate the percentage of active delegations going to a specific delegatee.
        
        Args:
            delegatee_id: The delegatee to check
            field_id: Optional field to scope the calculation to
            
        Returns:
            Percentage as float (0.0 to 1.0)
        """
        try:
            # Build base query for active delegations
            base_query = select(Delegation).where(
                and_(
                    Delegation.is_active == True,
                    Delegation.delegatee_id == delegatee_id
                )
            )
            
            # Add field filter if specified
            if field_id:
                base_query = base_query.where(Delegation.field_id == field_id)
            
            # Count delegations to this delegatee
            delegatee_count_query = select(func.count()).select_from(base_query.subquery())
            delegatee_count_result = await self.db.execute(delegatee_count_query)
            delegatee_count = delegatee_count_result.scalar() or 0
            
            # Count total active delegations (same scope)
            total_query = select(func.count()).select_from(Delegation).where(
                Delegation.is_active == True
            )
            if field_id:
                total_query = total_query.where(Delegation.field_id == field_id)
            
            total_result = await self.db.execute(total_query)
            total_count = total_result.scalar() or 0
            
            # Calculate percentage
            if total_count == 0:
                return 0.0
            
            return delegatee_count / total_count
            
        except Exception as e:
            logger.error(f"Error calculating concentration for delegatee {delegatee_id}: {e}")
            return 0.0
    
    async def is_high_concentration(
        self, 
        delegatee_id: UUID, 
        field_id: Optional[UUID] = None,
        warn: float = 0.08,
        high: float = 0.15
    ) -> Tuple[bool, str, float]:
        """
        Check if a delegatee has high concentration of delegations.
        
        Args:
            delegatee_id: The delegatee to check
            field_id: Optional field to scope the check to
            warn: Warning threshold (default 8%)
            high: High concentration threshold (default 15%)
            
        Returns:
            Tuple of (is_high, level, percent) where:
            - is_high: Boolean indicating if concentration is concerning
            - level: "warn" or "high" if concerning, empty string otherwise
            - percent: Actual percentage as float
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
            logger.error(f"Error checking concentration for delegatee {delegatee_id}: {e}")
            return False, "", 0.0
