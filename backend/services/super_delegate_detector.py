"""
Super-delegate detection service for delegation patterns.

Detects when a delegatee would become a "super-delegate" with too much power
across multiple fields or too many total delegations.
"""

import logging
from typing import Optional, Tuple, Dict, Any
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import func, select, and_, distinct
from sqlalchemy.orm import selectinload

from backend.models.delegation import Delegation
from backend.models.user import User
from backend.models.field import Field

logger = logging.getLogger(__name__)


class SuperDelegateDetectorService:
    """Service for detecting super-delegate patterns."""
    
    def __init__(self, db: AsyncSession):
        self.db = db
        # Thresholds for super-delegate detection
        self.global_in_degree_threshold = 500  # Total delegations
        self.distinct_fields_threshold = 12     # Distinct fields delegated in
        self.percentile_threshold = 0.05        # Top 5% of delegatees by count
    
    async def count_delegations_to_delegatee(
        self, 
        delegatee_id: UUID, 
        field_id: Optional[UUID] = None
    ) -> int:
        """Count total active delegations to a delegatee."""
        try:
            query = select(func.count()).select_from(Delegation).where(
                and_(
                    Delegation.is_active == True,
                    Delegation.delegatee_id == delegatee_id
                )
            )
            
            if field_id:
                query = query.where(Delegation.field_id == field_id)
            
            result = await self.db.execute(query)
            return result.scalar() or 0
            
        except Exception as e:
            logger.error(f"Error counting delegations to delegatee {delegatee_id}: {e}")
            return 0
    
    async def count_distinct_fields_for_delegatee(
        self, 
        delegatee_id: UUID
    ) -> int:
        """Count distinct fields a delegatee is delegated in."""
        try:
            query = select(func.count(distinct(Delegation.field_id))).select_from(Delegation).where(
                and_(
                    Delegation.is_active == True,
                    Delegation.delegatee_id == delegatee_id,
                    Delegation.field_id.isnot(None)
                )
            )
            
            result = await self.db.execute(query)
            return result.scalar() or 0
            
        except Exception as e:
            logger.error(f"Error counting distinct fields for delegatee {delegatee_id}: {e}")
            return 0
    
    async def get_delegatee_percentile_rank(
        self, 
        delegatee_id: UUID
    ) -> float:
        """Get the percentile rank of a delegatee by delegation count."""
        try:
            # Get all delegatee counts
            subquery = select(
                Delegation.delegatee_id,
                func.count().label('delegation_count')
            ).where(
                Delegation.is_active == True
            ).group_by(Delegation.delegatee_id).subquery()
            
            # Count total delegatees
            total_query = select(func.count()).select_from(subquery)
            total_result = await self.db.execute(total_query)
            total_delegatees = total_result.scalar() or 1
            
            # Get this delegatee's count
            delegatee_query = select(subquery.c.delegation_count).where(
                subquery.c.delegatee_id == delegatee_id
            )
            delegatee_result = await self.db.execute(delegatee_query)
            delegatee_count = delegatee_result.scalar() or 0
            
            # Count delegatees with higher counts
            higher_query = select(func.count()).select_from(subquery).where(
                subquery.c.delegation_count > delegatee_count
            )
            higher_result = await self.db.execute(higher_query)
            higher_count = higher_result.scalar() or 0
            
            # Calculate percentile rank (0.0 = top, 1.0 = bottom)
            return higher_count / total_delegatees
            
        except Exception as e:
            logger.error(f"Error calculating percentile rank for delegatee {delegatee_id}: {e}")
            return 0.5  # Default to middle rank
    
    async def would_create_super_delegate(
        self, 
        delegatee_id: UUID, 
        added_field_id: Optional[UUID] = None
    ) -> Tuple[bool, str, Dict[str, Any]]:
        """
        Check if adding a delegation would create a super-delegate pattern.
        
        Args:
            delegatee_id: The delegatee to check
            added_field_id: Optional field ID being added (for projection)
            
        Returns:
            Tuple of (risk_detected, reason, stats) where:
            - risk_detected: Boolean indicating super-delegate risk
            - reason: Human-readable reason for the risk
            - stats: Detailed statistics about the delegatee
        """
        try:
            # Get current stats
            current_delegations = await self.count_delegations_to_delegatee(delegatee_id)
            current_distinct_fields = await self.count_distinct_fields_for_delegatee(delegatee_id)
            percentile_rank = await self.get_delegatee_percentile_rank(delegatee_id)
            
            # Project future stats if adding a new field
            projected_delegations = current_delegations
            projected_distinct_fields = current_distinct_fields
            
            if added_field_id:
                # Check if this field would be new for this delegatee
                existing_field_query = select(func.count()).select_from(Delegation).where(
                    and_(
                        Delegation.is_active == True,
                        Delegation.delegatee_id == delegatee_id,
                        Delegation.field_id == added_field_id
                    )
                )
                existing_field_result = await self.db.execute(existing_field_query)
                existing_field_count = existing_field_result.scalar() or 0
                
                if existing_field_count == 0:
                    projected_distinct_fields += 1
                
                projected_delegations += 1
            
            # Check risk factors
            risk_detected = False
            reasons = []
            
            if projected_delegations >= self.global_in_degree_threshold:
                risk_detected = True
                reasons.append(f"Would have {projected_delegations} total delegations (threshold: {self.global_in_degree_threshold})")
            
            if projected_distinct_fields >= self.distinct_fields_threshold:
                risk_detected = True
                reasons.append(f"Would be delegated in {projected_distinct_fields} distinct fields (threshold: {self.distinct_fields_threshold})")
            
            if percentile_rank <= self.percentile_threshold:
                risk_detected = True
                reasons.append(f"Already in top {self.percentile_threshold:.1%} of delegatees by delegation count")
            
            # Compile reason
            reason = "; ".join(reasons) if reasons else "No super-delegate risk detected"
            
            # Compile stats
            stats = {
                "current_delegations": current_delegations,
                "projected_delegations": projected_delegations,
                "current_distinct_fields": current_distinct_fields,
                "projected_distinct_fields": projected_distinct_fields,
                "percentile_rank": percentile_rank,
                "thresholds": {
                    "global_in_degree": self.global_in_degree_threshold,
                    "distinct_fields": self.distinct_fields_threshold,
                    "percentile": self.percentile_threshold
                }
            }
            
            return risk_detected, reason, stats
            
        except Exception as e:
            logger.error(f"Error checking super-delegate risk for {delegatee_id}: {e}")
            return False, f"Error checking super-delegate risk: {e}", {}
