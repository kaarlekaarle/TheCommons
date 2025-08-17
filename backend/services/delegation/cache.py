"""Cache management for delegation chains.

This module handles Redis caching operations for delegation chains,
including key generation, cache operations, and invalidation.
"""

import hashlib
import json
from typing import Any, Dict, List, Optional, Set
from uuid import UUID

import redis.asyncio as redis

from backend.models.delegation import Delegation


class DelegationCache:
    """Cache management for delegation chains."""

    def __init__(self, redis_client: redis.Redis, ttl_seconds: int = 600):
        self.redis = redis_client
        self.ttl_seconds = ttl_seconds
        # Fast-path cache TTL (shorter for override path)
        self.fast_path_ttl = 120  # 2 minutes

    def generate_cache_key(
        self,
        user_id: UUID,
        poll_id: Optional[UUID] = None,
        label_id: Optional[UUID] = None,
        field_id: Optional[UUID] = None,
        institution_id: Optional[UUID] = None,
        value_id: Optional[UUID] = None,
        idea_id: Optional[UUID] = None,
    ) -> str:
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

    def generate_fast_path_key(
        self,
        user_id: UUID,
        poll_id: Optional[UUID] = None,
        label_id: Optional[UUID] = None,
        field_id: Optional[UUID] = None,
        institution_id: Optional[UUID] = None,
        value_id: Optional[UUID] = None,
        idea_id: Optional[UUID] = None,
    ) -> str:
        """Generate fast-path cache key for override resolution."""
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
        return f"delegation:fastpath:{user_id}:{scope_hash}"

    async def get_cached_chain(self, cache_key: str) -> Optional[List[Dict[str, Any]]]:
        """Get cached delegation chain."""
        try:
            cached_data = await self.redis.get(cache_key)
            if cached_data:
                chain_data = json.loads(cached_data)
                return chain_data
        except Exception:
            # Log error but don't fail the operation
            pass
        return None

    async def get_fast_path_result(
        self,
        user_id: UUID,
        poll_id: Optional[UUID] = None,
        label_id: Optional[UUID] = None,
        field_id: Optional[UUID] = None,
        institution_id: Optional[UUID] = None,
        value_id: Optional[UUID] = None,
        idea_id: Optional[UUID] = None,
    ) -> Optional[Dict[str, Any]]:
        """Get fast-path override result."""
        try:
            fast_path_key = self.generate_fast_path_key(
                user_id, poll_id, label_id, field_id, institution_id, value_id, idea_id
            )
            cached_data = await self.redis.get(fast_path_key)
            if cached_data:
                return json.loads(cached_data)
        except Exception:
            # Log error but don't fail the operation
            pass
        return None

    async def cache_fast_path_result(
        self,
        user_id: UUID,
        result: Dict[str, Any],
        poll_id: Optional[UUID] = None,
        label_id: Optional[UUID] = None,
        field_id: Optional[UUID] = None,
        institution_id: Optional[UUID] = None,
        value_id: Optional[UUID] = None,
        idea_id: Optional[UUID] = None,
    ) -> None:
        """Cache fast-path override result."""
        try:
            fast_path_key = self.generate_fast_path_key(
                user_id, poll_id, label_id, field_id, institution_id, value_id, idea_id
            )
            await self.redis.setex(
                fast_path_key, self.fast_path_ttl, json.dumps(result)
            )
        except Exception:
            # Log error but don't fail the operation
            pass

    async def batch_get_cached_chains(
        self, cache_keys: List[str]
    ) -> Dict[str, Optional[List[Dict[str, Any]]]]:
        """Batch get multiple cached chains using mget."""
        if not cache_keys:
            return {}

        try:
            # Use mget for batch retrieval
            cached_data_list = await self.redis.mget(cache_keys)
            results = {}

            for i, cached_data in enumerate(cached_data_list):
                cache_key = cache_keys[i]
                if cached_data:
                    try:
                        chain_data = json.loads(cached_data)
                        results[cache_key] = chain_data
                    except json.JSONDecodeError:
                        results[cache_key] = None
                else:
                    results[cache_key] = None

            return results
        except Exception:
            # Fallback to individual gets if mget fails
            results = {}
            for cache_key in cache_keys:
                results[cache_key] = await self.get_cached_chain(cache_key)
            return results

    async def cache_chain(self, cache_key: str, chain: List[Delegation]) -> None:
        """Cache delegation chain with TTL."""
        try:
            # Serialize chain to JSON-serializable format
            chain_data = []
            for delegation in chain:
                chain_data.append(
                    {
                        "id": str(delegation.id),
                        "delegator_id": str(delegation.delegator_id),
                        "delegatee_id": str(delegation.delegatee_id),
                        "mode": delegation.mode,
                        "poll_id": (
                            str(delegation.poll_id) if delegation.poll_id else None
                        ),
                        "label_id": (
                            str(delegation.label_id) if delegation.label_id else None
                        ),
                        "field_id": (
                            str(delegation.field_id) if delegation.field_id else None
                        ),
                        "institution_id": (
                            str(delegation.institution_id)
                            if delegation.institution_id
                            else None
                        ),
                        "value_id": (
                            str(delegation.value_id) if delegation.value_id else None
                        ),
                        "idea_id": (
                            str(delegation.idea_id) if delegation.idea_id else None
                        ),
                        "start_date": (
                            delegation.start_date.isoformat()
                            if delegation.start_date
                            else None
                        ),
                        "end_date": (
                            delegation.end_date.isoformat()
                            if delegation.end_date
                            else None
                        ),
                        "legacy_term_ends_at": (
                            delegation.legacy_term_ends_at.isoformat()
                            if delegation.legacy_term_ends_at
                            else None
                        ),
                        "created_at": (
                            delegation.created_at.isoformat()
                            if delegation.created_at
                            else None
                        ),
                    }
                )

            await self.redis.setex(cache_key, self.ttl_seconds, json.dumps(chain_data))
        except Exception:
            # Log error but don't fail the operation
            pass

    async def invalidate_user_cache(self, user_id: UUID) -> None:
        """Invalidate all chain cache entries for a user."""
        try:
            # Invalidate both chain cache and fast-path cache
            patterns = [
                f"delegation:chain:{user_id}:*",
                f"delegation:fastpath:{user_id}:*",
            ]

            for pattern in patterns:
                keys = await self.redis.keys(pattern)
                if keys:
                    await self.redis.delete(*keys)
        except Exception:
            # Log error but don't fail the operation
            pass

    async def invalidate_all_chain_cache(self) -> None:
        """Invalidate all chain cache entries (use sparingly)."""
        try:
            patterns = [f"delegation:chain:*", f"delegation:fastpath:*"]

            for pattern in patterns:
                keys = await self.redis.keys(pattern)
                if keys:
                    await self.redis.delete(*keys)
        except Exception:
            # Log error but don't fail the operation
            pass

    async def invalidate_delegatee_cache(self, delegatee_id: UUID) -> None:
        """Invalidate chain cache entries that might be affected by delegatee changes."""
        # This is a broader invalidation - could be optimized with more specific patterns
        await self.invalidate_all_chain_cache()

    async def invalidate_fast_path_cache(
        self,
        user_id: Optional[UUID] = None,
        poll_id: Optional[UUID] = None,
        label_id: Optional[UUID] = None,
        field_id: Optional[UUID] = None,
        institution_id: Optional[UUID] = None,
        value_id: Optional[UUID] = None,
        idea_id: Optional[UUID] = None,
    ) -> None:
        """Invalidate fast-path cache entries."""
        try:
            if user_id:
                # Invalidate specific user's fast-path cache
                pattern = f"delegation:fastpath:{user_id}:*"
                keys = await self.redis.keys(pattern)
                if keys:
                    await self.redis.delete(*keys)
            else:
                # Invalidate all fast-path cache
                pattern = f"delegation:fastpath:*"
                keys = await self.redis.keys(pattern)
                if keys:
                    await self.redis.delete(*keys)
        except Exception:
            # Log error but don't fail the operation
            pass

    async def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        try:
            chain_pattern = f"delegation:chain:*"
            fast_path_pattern = f"delegation:fastpath:*"

            chain_keys = await self.redis.keys(chain_pattern)
            fast_path_keys = await self.redis.keys(fast_path_pattern)

            return {
                "chain_keys": len(chain_keys),
                "fast_path_keys": len(fast_path_keys),
                "total_keys": len(chain_keys) + len(fast_path_keys),
                "cache_size": (
                    sum(len(k) for k in chain_keys + fast_path_keys)
                    if chain_keys or fast_path_keys
                    else 0
                ),
            }
        except Exception:
            return {
                "chain_keys": 0,
                "fast_path_keys": 0,
                "total_keys": 0,
                "cache_size": 0,
            }
