"""Super-delegate detection service for anti-hierarchy delegation features.

This service detects when delegations would create super-delegate patterns
that violate the anti-hierarchy principle.
"""

from datetime import datetime
from typing import Dict, List, Optional, Any, Tuple
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import func, select, and_, distinct

from backend.models.delegation import Delegation
from backend.models.user import User
from backend.core.logging_config import get_logger

logger = get_logger(__name__)


class SuperDelegateDetectorService:
    """Service for detecting super-delegate patterns."""
    
    def __init__(self, db: AsyncSession):
        self.db = db
        # Thresholds for super-delegate detection
        self.global_in_degree_threshold = 500  # Max delegations to one person
        self.distinct_fields_threshold = 12    # Max distinct fields delegated to
        self.percentile_threshold = 0.05       # Top 5% percentile threshold
    
    async def count_delegations_to_delegatee(self, delegatee_id: UUID) -> int:
        """Count total active delegations to a delegatee."""
        try:
            result = await self.db.execute(
                select(func.count(Delegation.id)).where(
                    and_(
                        Delegation.delegatee_id == delegatee_id,
                        Delegation.is_deleted == False,
                        Delegation.revoked_at.is_(None),
                        Delegation.end_date.is_(None) | (Delegation.end_date > datetime.utcnow())
                    )
                )
            )
            return result.scalar() or 0
        except Exception as e:
            logger.error(f"Error counting delegations to delegatee {delegatee_id}: {e}")
            return 0
    
    async def count_distinct_fields_for_delegatee(self, delegatee_id: UUID) -> int:
        """Count distinct fields that a delegatee has delegations for."""
        try:
            result = await self.db.execute(
                select(func.count(distinct(Delegation.field_id))).where(
                    and_(
                        Delegation.delegatee_id == delegatee_id,
                        Delegation.is_deleted == False,
                        Delegation.revoked_at.is_(None),
                        Delegation.end_date.is_(None) | (Delegation.end_date > datetime.utcnow()),
                        Delegation.field_id.is_not(None)
                    )
                )
            )
            return result.scalar() or 0
        except Exception as e:
            logger.error(f"Error counting distinct fields for delegatee {delegatee_id}: {e}")
            return 0
    
    async def get_delegatee_percentile_rank(self, delegatee_id: UUID) -> float:
        """Get the percentile rank of a delegatee based on delegation count."""
        try:
            # Get all delegatee counts
            result = await self.db.execute(
                select(
                    Delegation.delegatee_id,
                    func.count(Delegation.id).label('delegation_count')
                ).where(
                    and_(
                        Delegation.is_deleted == False,
                        Delegation.revoked_at.is_(None),
                        Delegation.end_date.is_(None) | (Delegation.end_date > datetime.utcnow())
                    )
                ).group_by(Delegation.delegatee_id)
            )
            
            delegatee_counts = result.fetchall()
            if not delegatee_counts:
                return 0.0
            
            # Sort by delegation count
            sorted_counts = sorted([count for _, count in delegatee_counts], reverse=True)
            total_delegatees = len(sorted_counts)
            
            # Find this delegatee's count
            target_count = await self.count_delegations_to_delegatee(delegatee_id)
            
            # Calculate percentile rank
            rank = 0
            for count in sorted_counts:
                if count > target_count:
                    rank += 1
                else:
                    break
            
            return rank / total_delegatees if total_delegatees > 0 else 0.0
            
        except Exception as e:
            logger.error(f"Error calculating percentile rank for delegatee {delegatee_id}: {e}")
            return 0.0
    
    async def would_create_super_delegate(
        self, 
        delegatee_id: UUID, 
        added_field_id: Optional[UUID] = None
    ) -> Tuple[bool, str, Dict[str, Any]]:
        """Check if adding a delegation would create a super-delegate pattern.
        
        Args:
            delegatee_id: ID of the delegatee to check
            added_field_id: Optional field ID being added (for field-specific checks)
            
        Returns:
            Tuple[bool, str, Dict]: (risk, reason, stats)
                - risk: True if super-delegate risk detected
                - reason: Human-readable reason for the risk
                - stats: Detailed statistics about the delegatee
        """
        try:
            # Get current stats
            current_delegations = await self.count_delegations_to_delegatee(delegatee_id)
            current_distinct_fields = await self.count_distinct_fields_for_delegatee(delegatee_id)
            percentile_rank = await self.get_delegatee_percentile_rank(delegatee_id)
            
            # Calculate projected stats (including the new delegation)
            projected_delegations = current_delegations + 1
            projected_distinct_fields = current_distinct_fields
            if added_field_id:
                # Check if this field is new for this delegatee
                existing_field_result = await self.db.execute(
                    select(Delegation.id).where(
                        and_(
                            Delegation.delegatee_id == delegatee_id,
                            Delegation.field_id == added_field_id,
                            Delegation.is_deleted == False,
                            Delegation.revoked_at.is_(None),
                            Delegation.end_date.is_(None) | (Delegation.end_date > datetime.utcnow())
                        )
                    )
                )
                if not existing_field_result.scalar():
                    projected_distinct_fields += 1
            
            # Check thresholds
            risk_detected = False
            reasons = []
            
            # Global in-degree threshold
            if projected_delegations >= self.global_in_degree_threshold:
                risk_detected = True
                reasons.append(f"Would have {projected_delegations} total delegations (threshold: {self.global_in_degree_threshold})")
            
            # Distinct fields threshold
            if projected_distinct_fields >= self.distinct_fields_threshold:
                risk_detected = True
                reasons.append(f"Would be delegated in {projected_distinct_fields} distinct fields (threshold: {self.distinct_fields_threshold})")
            
            # Percentile threshold
            if percentile_rank <= self.percentile_threshold:
                risk_detected = True
                reasons.append(f"Already in top {self.percentile_threshold:.1%} of delegatees by delegation count")
            
            # Compile stats
            stats = {
                "current_delegations": current_delegations,
                "projected_delegations": projected_delegations,
                "current_distinct_fields": current_distinct_fields,
                "projected_distinct_fields": projected_distinct_fields,
                "percentile_rank": percentile_rank,
                "global_in_degree_threshold": self.global_in_degree_threshold,
                "distinct_fields_threshold": self.distinct_fields_threshold,
                "percentile_threshold": self.percentile_threshold
            }
            
            # Determine reason
            if risk_detected:
                if len(reasons) == 1:
                    reason = reasons[0]
                else:
                    reason = f"Multiple risk factors: {'; '.join(reasons)}"
            else:
                reason = "No super-delegate risk detected"
            
            return risk_detected, reason, stats
            
        except Exception as e:
            logger.error(f"Error checking super-delegate risk for {delegatee_id}: {e}")
            return False, f"Error checking super-delegate risk: {e}", {}
    
    async def get_all_super_delegate_risks(self) -> List[Dict[str, Any]]:
        """Get all current super-delegate risks in the system."""
        try:
            # Get all delegatees with their stats
            result = await self.db.execute(
                select(
                    Delegation.delegatee_id,
                    func.count(Delegation.id).label('delegation_count'),
                    func.count(distinct(Delegation.field_id)).label('distinct_fields')
                ).where(
                    and_(
                        Delegation.is_deleted == False,
                        Delegation.revoked_at.is_(None),
                        Delegation.end_date.is_(None) | (Delegation.end_date > datetime.utcnow())
                    )
                ).group_by(Delegation.delegatee_id)
            )
            
            risks = []
            for delegatee_id, delegation_count, distinct_fields in result.fetchall():
                risk, reason, stats = await self.would_create_super_delegate(delegatee_id)
                if risk:
                    risks.append({
                        "delegatee_id": str(delegatee_id),
                        "reason": reason,
                        "stats": stats,
                        "delegation_count": delegation_count,
                        "distinct_fields": distinct_fields
                    })
            
            return risks
            
        except Exception as e:
            logger.error(f"Error getting all super-delegate risks: {e}")
            return []
