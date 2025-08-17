"""
Adoption telemetry service for tracking delegation mode usage and transitions.

Tracks how users adopt different delegation modes and transition between them
to understand adoption patterns and constitutional drift.
"""

import logging
import hashlib
import json
from datetime import datetime
from typing import Optional, Dict, Any
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text, select, func
from sqlalchemy.orm import selectinload

from backend.models.user import User
from backend.models.delegation import Delegation, DelegationMode

logger = logging.getLogger(__name__)


class AdoptionTelemetryService:
    """Service for tracking delegation mode adoption and transitions."""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    def _hash_user_id(self, user_id: UUID) -> str:
        """Create a privacy-preserving hash of user ID."""
        return hashlib.sha256(str(user_id).encode()).hexdigest()[:16]
    
    async def track_delegation_mode(
        self, 
        user_id: UUID, 
        mode: DelegationMode, 
        context: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        Track when a user creates a delegation with a specific mode.
        
        Args:
            user_id: ID of the user creating the delegation
            mode: Delegation mode being used
            context: Optional context data (e.g., field_id, target_type)
        """
        try:
            user_hash = self._hash_user_id(user_id)
            timestamp = datetime.utcnow()
            
            # Store adoption event
            await self.db.execute(
                text("""
                INSERT INTO adoption_events (timestamp, user_hash, mode, from_mode, context)
                VALUES (:timestamp, :user_hash, :mode, NULL, :context)
                """),
                {
                    "timestamp": timestamp,
                    "user_hash": user_hash,
                    "mode": mode.value,
                    "context": json.dumps(context) if context else None
                }
            )
            
            await self.db.commit()
            
            logger.info(
                "Tracked delegation mode adoption",
                extra={
                    "user_hash": user_hash,
                    "mode": mode.value,
                    "context": context
                }
            )
            
        except Exception as e:
            await self.db.rollback()
            logger.error(f"Failed to track delegation mode: {e}")
    
    async def track_transition(
        self, 
        user_id: UUID, 
        from_mode: DelegationMode, 
        to_mode: DelegationMode, 
        context: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        Track when a user transitions from one delegation mode to another.
        
        Args:
            user_id: ID of the user making the transition
            from_mode: Previous delegation mode
            to_mode: New delegation mode
            context: Optional context data about the transition
        """
        try:
            user_hash = self._hash_user_id(user_id)
            timestamp = datetime.utcnow()
            
            # Store transition event
            await self.db.execute(
                text("""
                INSERT INTO adoption_events (timestamp, user_hash, mode, from_mode, context)
                VALUES (:timestamp, :user_hash, :mode, :from_mode, :context)
                """),
                {
                    "timestamp": timestamp,
                    "user_hash": user_hash,
                    "mode": to_mode.value,
                    "from_mode": from_mode.value,
                    "context": json.dumps(context) if context else None
                }
            )
            
            await self.db.commit()
            
            logger.info(
                "Tracked delegation mode transition",
                extra={
                    "user_hash": user_hash,
                    "from_mode": from_mode.value,
                    "to_mode": to_mode.value,
                    "context": context
                }
            )
            
        except Exception as e:
            await self.db.rollback()
            logger.error(f"Failed to track transition: {e}")
    
    async def get_adoption_stats(self, days: int = 14) -> Dict[str, Any]:
        """
        Get adoption statistics for the specified time period.
        
        Args:
            days: Number of days to look back
            
        Returns:
            Dict with adoption statistics
        """
        try:
            # Get mode adoption counts
            adoption_query = text("""
                SELECT mode, COUNT(*) as count
                FROM adoption_events
                WHERE timestamp >= datetime('now', '-:days days')
                AND from_mode IS NULL
                GROUP BY mode
            """)
            
            adoption_result = await self.db.execute(adoption_query, {"days": days})
            adoption_counts = {row.mode: row.count for row in adoption_result.fetchall()}
            
            # Get transition counts
            transition_query = text("""
                SELECT from_mode, mode as to_mode, COUNT(*) as count
                FROM adoption_events
                WHERE timestamp >= datetime('now', '-:days days')
                AND from_mode IS NOT NULL
                GROUP BY from_mode, mode
            """)
            
            transition_result = await self.db.execute(transition_query, {"days": days})
            transitions = {}
            for row in transition_result.fetchall():
                key = f"{row.from_mode}_to_{row.to_mode}"
                transitions[key] = row.count
            
            # Calculate percentages
            total_adoptions = sum(adoption_counts.values())
            percentages = {}
            if total_adoptions > 0:
                for mode, count in adoption_counts.items():
                    percentages[mode] = (count / total_adoptions) * 100
            
            return {
                "period_days": days,
                "total_adoptions": total_adoptions,
                "mode_counts": adoption_counts,
                "mode_percentages": percentages,
                "transitions": transitions,
                "generated_at": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Failed to get adoption stats: {e}")
            return {
                "period_days": days,
                "total_adoptions": 0,
                "mode_counts": {},
                "mode_percentages": {},
                "transitions": {},
                "error": str(e),
                "generated_at": datetime.utcnow().isoformat()
            }
    
    async def get_user_transitions(self, user_id: UUID, days: int = 30) -> Dict[str, Any]:
        """
        Get transition history for a specific user.
        
        Args:
            user_id: ID of the user
            days: Number of days to look back
            
        Returns:
            Dict with user's transition history
        """
        try:
            user_hash = self._hash_user_id(user_id)
            
            query = text("""
                SELECT timestamp, mode, from_mode, context
                FROM adoption_events
                WHERE user_hash = :user_hash
                AND timestamp >= datetime('now', '-:days days')
                ORDER BY timestamp DESC
            """)
            
            result = await self.db.execute(query, {
                "user_hash": user_hash,
                "days": days
            })
            
            events = []
            for row in result.fetchall():
                events.append({
                    "timestamp": row.timestamp.isoformat() if row.timestamp else None,
                    "mode": row.mode,
                    "from_mode": row.from_mode,
                    "context": json.loads(row.context) if row.context else None
                })
            
            return {
                "user_hash": user_hash,
                "period_days": days,
                "events": events,
                "total_events": len(events)
            }
            
        except Exception as e:
            logger.error(f"Failed to get user transitions: {e}")
            return {
                "user_hash": self._hash_user_id(user_id),
                "period_days": days,
                "events": [],
                "total_events": 0,
                "error": str(e)
            }
