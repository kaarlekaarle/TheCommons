"""Delegation service module - thin façade for backward compatibility.

This module provides a thin façade over the refactored delegation services
to maintain backward compatibility with existing imports.
"""

from sqlalchemy.ext.asyncio import AsyncSession
import redis.asyncio as redis

from backend.config import get_settings

from .dispatch import DelegationDispatch, DelegationTarget
from .cache import DelegationCache
from .repository import DelegationRepository
from .chain_resolution import ChainResolutionCore
from .telemetry import DelegationTelemetry


class DelegationService:
    """Thin façade over refactored delegation services for backward compatibility."""
    
    def __init__(self, db: AsyncSession):
        self.db = db
        
        # Initialize cache
        settings = get_settings()
        redis_client = redis.from_url(settings.REDIS_URL)
        self.cache = DelegationCache(redis_client)
        
        # Initialize dispatch layer
        self.dispatch = DelegationDispatch(db, self.cache)
        
        # Expose components for advanced usage
        self.repository = self.dispatch.repository
        self.chain_resolution = ChainResolutionCore
        self.telemetry = DelegationTelemetry
    
    # Delegate all public methods to dispatch layer
    async def resolve_delegation_chain(self, *args, **kwargs):
        """Resolve delegation chain."""
        return await self.dispatch.resolve_delegation_chain(*args, **kwargs)
    
    async def create_delegation(self, *args, **kwargs):
        """Create a new delegation."""
        return await self.dispatch.create_delegation(*args, **kwargs)
    
    async def revoke_delegation(self, *args, **kwargs):
        """Revoke a delegation."""
        return await self.dispatch.revoke_delegation(*args, **kwargs)
    
    # Additional methods that might be needed
    async def get_active_delegations(self, user_id, *args, **kwargs):
        """Get active delegations for a user."""
        return await self.repository.get_active_delegations_for_user(user_id, *args, **kwargs)
    
    async def get_delegation_history(self, user_id):
        """Get delegation history for a user."""
        return await self.repository.get_delegation_history(user_id)
    
    async def get_poll_delegations(self, poll_id):
        """Get all delegations for a specific poll."""
        return await self.repository.get_poll_delegations(poll_id)
    
    async def expire_legacy_delegations(self):
        """Expire legacy fixed-term delegations."""
        expired_delegations = await self.repository.get_expired_legacy_delegations()
        
        expired_count = 0
        for delegation in expired_delegations:
            # Mark as expired by setting end_date to legacy_term_ends_at
            delegation.end_date = delegation.legacy_term_ends_at
            await self.db.flush()
            expired_count += 1
        
        return {
            "expired_count": expired_count,
            "expired_delegations": [str(d.id) for d in expired_delegations]
        }


# Export the main classes for backward compatibility
__all__ = [
    "DelegationService",
    "DelegationTarget", 
    "DelegationDispatch",
    "DelegationRepository",
    "DelegationCache",
    "ChainResolutionCore",
    "DelegationTelemetry",
]
