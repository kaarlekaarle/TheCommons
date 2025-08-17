"""Cache management for delegation chains.

This module handles Redis caching operations for delegation chains,
including key generation, cache operations, and invalidation.
"""

import hashlib
import json
import random
from typing import Any, Dict, List, Optional, Set, Tuple
from uuid import UUID

import redis.asyncio as redis

from backend.models.delegation import Delegation
from backend.services.delegation.telemetry import DelegationTelemetry

# Try to import msgpack, fallback to JSON if not available
try:
    import msgpack
    MSGPACK_AVAILABLE = True
except ImportError:
    MSGPACK_AVAILABLE = False
    msgpack = None


class DelegationCache:
    """Cache management for delegation chains."""

    def __init__(self, redis_client: redis.Redis, ttl_seconds: int = 600):
        self.redis = redis_client
        self.ttl_seconds = ttl_seconds
        # Fast-path cache TTL (shorter for override path)
        self.fast_path_ttl = 90  # 90 seconds
        # Sample rate for telemetry (1%)
        self.telemetry_sample_rate = 0.01

    def _should_sample_telemetry(self) -> bool:
        """Determine if we should sample telemetry for this operation."""
        return random.random() < self.telemetry_sample_rate

    def _serialize_data(self, data: Any, sample_telemetry: bool = False) -> Tuple[bytes, str, Dict[str, Any]]:
        """Serialize data using msgpack with JSON fallback.
        
        Returns:
            Tuple of (serialized_data, format_used, telemetry_info)
        """
        telemetry_info = {}
        start_time = None
        
        if sample_telemetry:
            import time
            start_time = time.time()
        
        if MSGPACK_AVAILABLE:
            try:
                serialized = msgpack.packb(data, use_bin_type=True)
                format_used = "msgpack"
                
                if sample_telemetry and start_time:
                    telemetry_info = {
                        "serialization_time_ms": int((time.time() - start_time) * 1000),
                        "payload_size_bytes": len(serialized),
                        "format": format_used,
                    }
                
                return serialized, format_used, telemetry_info
            except Exception:
                # Fallback to JSON if msgpack fails
                pass
        
        # JSON fallback
        try:
            serialized = json.dumps(data).encode('utf-8')
            format_used = "json"
            
            if sample_telemetry and start_time:
                telemetry_info = {
                    "serialization_time_ms": int((time.time() - start_time) * 1000),
                    "payload_size_bytes": len(serialized),
                    "format": format_used,
                }
            
            return serialized, format_used, telemetry_info
        except Exception as e:
            raise ValueError(f"Failed to serialize data: {e}")

    def _deserialize_data(self, data: bytes, sample_telemetry: bool = False) -> Tuple[Any, str, Dict[str, Any]]:
        """Deserialize data, trying msgpack first, then JSON.
        
        Returns:
            Tuple of (deserialized_data, format_used, telemetry_info)
        """
        telemetry_info = {}
        start_time = None
        
        if sample_telemetry:
            import time
            start_time = time.time()
        
        # Try msgpack first (if available)
        if MSGPACK_AVAILABLE:
            try:
                deserialized = msgpack.unpackb(data, raw=False)
                format_used = "msgpack"
                
                if sample_telemetry and start_time:
                    telemetry_info = {
                        "deserialization_time_ms": int((time.time() - start_time) * 1000),
                        "payload_size_bytes": len(data),
                        "format": format_used,
                    }
                
                return deserialized, format_used, telemetry_info
            except Exception:
                # Fallback to JSON
                pass
        
        # JSON fallback
        try:
            deserialized = json.loads(data.decode('utf-8'))
            format_used = "json"
            
            if sample_telemetry and start_time:
                telemetry_info = {
                    "deserialization_time_ms": int((time.time() - start_time) * 1000),
                    "payload_size_bytes": len(data),
                    "format": format_used,
                }
            
            return deserialized, format_used, telemetry_info
        except Exception as e:
            raise ValueError(f"Failed to deserialize data: {e}")

    def _add_format_suffix(self, key: str, format_used: str) -> str:
        """Add format suffix to cache key."""
        return f"{key}:fmt={format_used[:2]}"

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
            # Try msgpack format first
            msgpack_key = self._add_format_suffix(cache_key, "msgpack")
            cached_data = await self.redis.get(msgpack_key)
            
            if cached_data:
                sample_telemetry = self._should_sample_telemetry()
                chain_data, format_used, telemetry_info = self._deserialize_data(cached_data, sample_telemetry)
                
                if sample_telemetry:
                    self._log_cache_telemetry("get_cached_chain", telemetry_info)
                
                return chain_data
            
            # Try JSON format (backward compatibility)
            json_key = self._add_format_suffix(cache_key, "json")
            cached_data = await self.redis.get(json_key)
            
            if cached_data:
                sample_telemetry = self._should_sample_telemetry()
                chain_data, format_used, telemetry_info = self._deserialize_data(cached_data, sample_telemetry)
                
                if sample_telemetry:
                    self._log_cache_telemetry("get_cached_chain", telemetry_info)
                
                return chain_data
            
            # Try legacy format (no suffix)
            cached_data = await self.redis.get(cache_key)
            if cached_data:
                sample_telemetry = self._should_sample_telemetry()
                chain_data, format_used, telemetry_info = self._deserialize_data(cached_data, sample_telemetry)
                
                if sample_telemetry:
                    self._log_cache_telemetry("get_cached_chain", telemetry_info)
                
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
            
            # Try msgpack format first
            msgpack_key = self._add_format_suffix(fast_path_key, "msgpack")
            cached_data = await self.redis.get(msgpack_key)
            
            if cached_data:
                sample_telemetry = self._should_sample_telemetry()
                result, format_used, telemetry_info = self._deserialize_data(cached_data, sample_telemetry)
                
                if sample_telemetry:
                    self._log_cache_telemetry("get_fast_path_result", telemetry_info)
                
                return result
            
            # Try JSON format (backward compatibility)
            json_key = self._add_format_suffix(fast_path_key, "json")
            cached_data = await self.redis.get(json_key)
            
            if cached_data:
                sample_telemetry = self._should_sample_telemetry()
                result, format_used, telemetry_info = self._deserialize_data(cached_data, sample_telemetry)
                
                if sample_telemetry:
                    self._log_cache_telemetry("get_fast_path_result", telemetry_info)
                
                return result
            
            # Try legacy format (no suffix)
            cached_data = await self.redis.get(fast_path_key)
            if cached_data:
                sample_telemetry = self._should_sample_telemetry()
                result, format_used, telemetry_info = self._deserialize_data(cached_data, sample_telemetry)
                
                if sample_telemetry:
                    self._log_cache_telemetry("get_fast_path_result", telemetry_info)
                
                return result
                
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
            
            # Use msgpack serialization with telemetry sampling
            sample_telemetry = self._should_sample_telemetry()
            serialized_data, format_used, telemetry_info = self._serialize_data(result, sample_telemetry)
            
            # Store with format suffix
            formatted_key = self._add_format_suffix(fast_path_key, format_used)
            await self.redis.setex(formatted_key, self.fast_path_ttl, serialized_data)
            
            if sample_telemetry:
                self._log_cache_telemetry("cache_fast_path_result", telemetry_info)
                
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

            # Use msgpack serialization with telemetry sampling
            sample_telemetry = self._should_sample_telemetry()
            serialized_data, format_used, telemetry_info = self._serialize_data(chain_data, sample_telemetry)
            
            # Store with format suffix
            formatted_key = self._add_format_suffix(cache_key, format_used)
            await self.redis.setex(formatted_key, self.ttl_seconds, serialized_data)
            
            if sample_telemetry:
                self._log_cache_telemetry("cache_chain", telemetry_info)
                
        except Exception:
            # Log error but don't fail the operation
            pass

    async def invalidate_user_cache(self, user_id: UUID) -> None:
        """Invalidate all chain cache entries for a user."""
        try:
            # Invalidate both chain cache and fast-path cache with format suffixes
            patterns = [
                f"delegation:chain:{user_id}:*fmt=*",
                f"delegation:fastpath:{user_id}:*fmt=*",
                # Also invalidate legacy format (no suffix) for backward compatibility
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
            patterns = [
                f"delegation:chain:*fmt=*", 
                f"delegation:fastpath:*fmt=*",
                # Also invalidate legacy format (no suffix) for backward compatibility
                f"delegation:chain:*", 
                f"delegation:fastpath:*"
            ]

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
        user_id: UUID,
        poll_id: Optional[UUID] = None,
        label_id: Optional[UUID] = None,
        field_id: Optional[UUID] = None,
        institution_id: Optional[UUID] = None,
        value_id: Optional[UUID] = None,
        idea_id: Optional[UUID] = None,
    ) -> None:
        """Invalidate fast-path cache for a specific user and scope."""
        try:
            fast_path_key = self.generate_fast_path_key(
                user_id, poll_id, label_id, field_id, institution_id, value_id, idea_id
            )
            
            # Invalidate both msgpack and JSON formats
            msgpack_key = self._add_format_suffix(fast_path_key, "msgpack")
            json_key = self._add_format_suffix(fast_path_key, "json")
            
            await self.redis.delete(msgpack_key, json_key, fast_path_key)
        except Exception:
            # Log error but don't fail the operation
            pass

    async def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        try:
            # Count different formats
            msgpack_chain_pattern = "delegation:chain:*fmt=ms"
            json_chain_pattern = "delegation:chain:*fmt=js"
            legacy_chain_pattern = "delegation:chain:*"
            
            msgpack_fast_pattern = "delegation:fastpath:*fmt=ms"
            json_fast_pattern = "delegation:fastpath:*fmt=js"
            legacy_fast_pattern = "delegation:fastpath:*"

            msgpack_chain_keys = await self.redis.keys(msgpack_chain_pattern)
            json_chain_keys = await self.redis.keys(json_chain_pattern)
            legacy_chain_keys = await self.redis.keys(legacy_chain_pattern)
            
            msgpack_fast_keys = await self.redis.keys(msgpack_fast_pattern)
            json_fast_keys = await self.redis.keys(json_fast_pattern)
            legacy_fast_keys = await self.redis.keys(legacy_fast_pattern)

            chain_stats = {
                "msgpack": len(msgpack_chain_keys),
                "json": len(json_chain_keys),
                "legacy": len(legacy_chain_keys),
                "total": len(msgpack_chain_keys) + len(json_chain_keys) + len(legacy_chain_keys),
            }
            
            fast_path_stats = {
                "msgpack": len(msgpack_fast_keys),
                "json": len(json_fast_keys),
                "legacy": len(legacy_fast_keys),
                "total": len(msgpack_fast_keys) + len(json_fast_keys) + len(legacy_fast_keys),
            }
            
            # Log format statistics using telemetry
            DelegationTelemetry.log_cache_format_stats(
                msgpack_keys=chain_stats["msgpack"] + fast_path_stats["msgpack"],
                json_keys=chain_stats["json"] + fast_path_stats["json"],
                legacy_keys=chain_stats["legacy"] + fast_path_stats["legacy"],
                total_keys=chain_stats["total"] + fast_path_stats["total"],
            )
            
            return {
                "chain_keys": chain_stats,
                "fast_path_keys": fast_path_stats,
                "msgpack_available": MSGPACK_AVAILABLE,
                "telemetry_sample_rate": self.telemetry_sample_rate,
            }
        except Exception:
            return {
                "chain_keys": {"total": 0},
                "fast_path_keys": {"total": 0},
                "msgpack_available": MSGPACK_AVAILABLE,
                "telemetry_sample_rate": self.telemetry_sample_rate,
            }

    def _log_cache_telemetry(self, operation: str, telemetry_info: Dict[str, Any]) -> None:
        """Log cache telemetry information."""
        try:
            # Use the new telemetry methods for serialization timing
            if "serialization_time_ms" in telemetry_info:
                DelegationTelemetry.log_serialization_timing(
                    operation=operation,
                    format_type=telemetry_info.get("format", "unknown"),
                    serialization_time_ms=telemetry_info["serialization_time_ms"],
                    payload_size_bytes=telemetry_info.get("payload_size_bytes", 0),
                    sample_rate=self.telemetry_sample_rate,
                )
            elif "deserialization_time_ms" in telemetry_info:
                DelegationTelemetry.log_serialization_timing(
                    operation=f"{operation}_deserialize",
                    format_type=telemetry_info.get("format", "unknown"),
                    serialization_time_ms=telemetry_info["deserialization_time_ms"],
                    payload_size_bytes=telemetry_info.get("payload_size_bytes", 0),
                    sample_rate=self.telemetry_sample_rate,
                )
        except Exception:
            # Don't fail if telemetry fails
            pass
