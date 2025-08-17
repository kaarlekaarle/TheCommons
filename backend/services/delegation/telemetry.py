"""Telemetry hooks for delegation operations.

This module provides telemetry and monitoring capabilities
for delegation operations, including performance metrics and logging.
"""

import time
from typing import Dict, Any, Optional
from uuid import UUID

from backend.core.logging_config import get_logger

logger = get_logger(__name__)


class DelegationTelemetry:
    """Telemetry hooks for delegation operations."""
    
    @staticmethod
    def log_chain_resolution_start(
        user_id: UUID,
        poll_id: Optional[UUID] = None,
        label_id: Optional[UUID] = None,
        field_id: Optional[UUID] = None,
        institution_id: Optional[UUID] = None,
        value_id: Optional[UUID] = None,
        idea_id: Optional[UUID] = None,
    ) -> float:
        """Log the start of chain resolution and return start time."""
        start_time = time.time()
        logger.debug(
            "Starting chain resolution",
            extra={
                "user_id": str(user_id),
                "poll_id": str(poll_id) if poll_id else None,
                "label_id": str(label_id) if label_id else None,
                "field_id": str(field_id) if field_id else None,
                "institution_id": str(institution_id) if institution_id else None,
                "value_id": str(value_id) if value_id else None,
                "idea_id": str(idea_id) if idea_id else None,
                "start_time": start_time,
            }
        )
        return start_time
    
    @staticmethod
    def log_override_resolution_start(
        user_id: UUID,
        poll_id: Optional[UUID] = None,
        label_id: Optional[UUID] = None,
        field_id: Optional[UUID] = None,
        institution_id: Optional[UUID] = None,
        value_id: Optional[UUID] = None,
        idea_id: Optional[UUID] = None,
    ) -> float:
        """Log the start of override resolution and return start time."""
        start_time = time.time()
        logger.debug(
            "Starting override resolution",
            extra={
                "user_id": str(user_id),
                "poll_id": str(poll_id) if poll_id else None,
                "label_id": str(label_id) if label_id else None,
                "field_id": str(field_id) if field_id else None,
                "institution_id": str(institution_id) if institution_id else None,
                "value_id": str(value_id) if value_id else None,
                "idea_id": str(idea_id) if idea_id else None,
                "start_time": start_time,
                "operation": "override_resolution",
            }
        )
        return start_time
    
    @staticmethod
    def log_override_resolution_complete(
        user_id: UUID,
        total_time: float,
        db_time: float,
        cache_time: float,
        chain_length: int,
        cache_hit: bool,
        fast_path_hit: bool,
        poll_id: Optional[UUID] = None,
        label_id: Optional[UUID] = None,
        field_id: Optional[UUID] = None,
        institution_id: Optional[UUID] = None,
        value_id: Optional[UUID] = None,
        idea_id: Optional[UUID] = None,
    ) -> None:
        """Log override resolution completion with detailed timing."""
        logger.info(
            f"Override resolution completed: {total_time:.3f}s total (db: {db_time:.3f}s, cache: {cache_time:.3f}s)",
            extra={
                "user_id": str(user_id),
                "poll_id": str(poll_id) if poll_id else None,
                "label_id": str(label_id) if label_id else None,
                "field_id": str(field_id) if field_id else None,
                "institution_id": str(institution_id) if institution_id else None,
                "value_id": str(value_id) if value_id else None,
                "idea_id": str(idea_id) if idea_id else None,
                "total_time_ms": int(total_time * 1000),
                "db_time_ms": int(db_time * 1000),
                "cache_time_ms": int(cache_time * 1000),
                "chain_length": chain_length,
                "cache_hit": cache_hit,
                "fast_path_hit": fast_path_hit,
                "operation": "override_resolution",
                "slo_p95_target": total_time <= 1.5,  # 1.5s target
                "slo_p99_target": total_time <= 2.0,  # 2.0s target
            }
        )
    
    @staticmethod
    def log_fast_path_cache_hit(
        user_id: UUID,
        cache_time: float,
        total_time: float,
        chain_length: int,
        poll_id: Optional[UUID] = None,
        label_id: Optional[UUID] = None,
        field_id: Optional[UUID] = None,
        institution_id: Optional[UUID] = None,
        value_id: Optional[UUID] = None,
        idea_id: Optional[UUID] = None,
    ) -> None:
        """Log fast-path cache hit metrics."""
        logger.info(
            f"Override fast-path cache hit: {total_time:.3f}s total (cache: {cache_time:.3f}s)",
            extra={
                "user_id": str(user_id),
                "poll_id": str(poll_id) if poll_id else None,
                "label_id": str(label_id) if label_id else None,
                "field_id": str(field_id) if field_id else None,
                "institution_id": str(institution_id) if institution_id else None,
                "value_id": str(value_id) if value_id else None,
                "idea_id": str(idea_id) if idea_id else None,
                "cache_time_ms": int(cache_time * 1000),
                "total_time_ms": int(total_time * 1000),
                "chain_length": chain_length,
                "cache_hit": True,
                "fast_path_hit": True,
                "operation": "override_resolution",
                "slo_p95_target": total_time <= 1.5,
                "slo_p99_target": total_time <= 2.0,
            }
        )
    
    @staticmethod
    def log_cache_hit(
        cache_key: str,
        cache_time: float,
        deserialize_time: float,
        total_time: float,
        chain_length: int,
        user_id: UUID,
        poll_id: Optional[UUID] = None,
    ) -> None:
        """Log cache hit metrics."""
        logger.info(
            f"Chain resolution cache hit: {total_time:.3f}s total (cache: {cache_time:.3f}s, deserialize: {deserialize_time:.3f}s)",
            extra={
                "user_id": str(user_id),
                "poll_id": str(poll_id) if poll_id else None,
                "cache_time_ms": int(cache_time * 1000),
                "deserialize_time_ms": int(deserialize_time * 1000),
                "total_time_ms": int(total_time * 1000),
                "chain_length": chain_length,
                "cache_hit": True,
                "cache_key": cache_key,
            }
        )
    
    @staticmethod
    def log_cache_miss(
        db_time: float,
        cache_time: float,
        total_time: float,
        db_queries: int,
        chain_length: int,
        memoization_hits: int,
        user_id: UUID,
        poll_id: Optional[UUID] = None,
    ) -> None:
        """Log cache miss metrics."""
        logger.info(
            f"Chain resolution completed: {total_time:.3f}s total (db: {db_time:.3f}s, cache: {cache_time:.3f}s, queries: {db_queries})",
            extra={
                "user_id": str(user_id),
                "poll_id": str(poll_id) if poll_id else None,
                "db_time_ms": int(db_time * 1000),
                "cache_time_ms": int(cache_time * 1000),
                "total_time_ms": int(total_time * 1000),
                "db_queries": db_queries,
                "chain_length": chain_length,
                "cache_hit": False,
                "memoization_hits": memoization_hits,
            }
        )
    
    @staticmethod
    def log_delegation_creation(
        delegation_id: UUID,
        delegator_id: UUID,
        delegatee_id: UUID,
        mode: str,
        target_type: str,
    ) -> None:
        """Log delegation creation."""
        logger.info(
            f"Created delegation {delegation_id} with mode {mode}",
            extra={
                "delegation_id": str(delegation_id),
                "delegator_id": str(delegator_id),
                "delegatee_id": str(delegatee_id),
                "mode": mode,
                "target_type": target_type,
            }
        )
    
    @staticmethod
    def log_delegation_revocation(
        delegation_id: UUID,
        mode: str,
        target_type: str,
    ) -> None:
        """Log delegation revocation."""
        logger.info(
            f"Revoked delegation {delegation_id}",
            extra={
                "delegation_id": str(delegation_id),
                "mode": mode,
                "target_type": target_type,
            }
        )
    
    @staticmethod
    def log_expired_legacy_delegation(
        delegation_id: UUID,
        delegator_id: UUID,
        delegatee_id: UUID,
        mode: str,
    ) -> None:
        """Log expired legacy delegation."""
        logger.warning(
            f"Found expired legacy delegation {delegation_id} in chain",
            extra={
                "delegation_id": str(delegation_id),
                "delegator_id": str(delegator_id),
                "delegatee_id": str(delegatee_id),
                "mode": mode,
            }
        )
    
    @staticmethod
    def log_user_override(
        user_id: UUID,
        poll_id: Optional[UUID] = None,
        label_id: Optional[UUID] = None,
        field_id: Optional[UUID] = None,
        institution_id: Optional[UUID] = None,
        value_id: Optional[UUID] = None,
        idea_id: Optional[UUID] = None,
        override_check_time: Optional[float] = None,
    ) -> None:
        """Log user override detection."""
        extra_data = {
            "user_id": str(user_id),
            "poll_id": str(poll_id) if poll_id else None,
            "label_id": str(label_id) if label_id else None,
            "field_id": str(field_id) if field_id else None,
            "institution_id": str(institution_id) if institution_id else None,
            "value_id": str(value_id) if value_id else None,
            "idea_id": str(idea_id) if idea_id else None,
        }
        
        if override_check_time is not None:
            extra_data["override_check_time_ms"] = int(override_check_time * 1000)
        
        logger.info(
            f"Stopping chain resolution due to user override for {user_id}",
            extra=extra_data
        )
    
    @staticmethod
    def log_chain_depth_limit(
        user_id: UUID,
        max_depth: int,
        chain_length: int,
    ) -> None:
        """Log chain depth limit reached."""
        logger.warning(
            f"Delegation chain depth limit reached for user {user_id}",
            extra={
                "user_id": str(user_id),
                "max_depth": max_depth,
                "chain_length": chain_length,
            }
        )
    
    @staticmethod
    def log_cache_invalidation(
        user_id: Optional[UUID] = None,
        delegatee_id: Optional[UUID] = None,
        keys_invalidated: int = 0,
    ) -> None:
        """Log cache invalidation."""
        if user_id:
            logger.debug(f"Invalidated {keys_invalidated} chain cache entries for user {user_id}")
        elif delegatee_id:
            logger.debug(f"Invalidated all chain cache entries due to delegatee {delegatee_id} change")
        else:
            logger.debug(f"Invalidated {keys_invalidated} chain cache entries")
    
    @staticmethod
    def log_cache_error(operation: str, error: str) -> None:
        """Log cache operation errors."""
        logger.warning(f"Cache {operation} error: {error}")
    
    @staticmethod
    def get_performance_metrics() -> Dict[str, Any]:
        """Get current performance metrics (placeholder for metrics collection)."""
        return {
            "cache_hit_rate": 0.0,
            "avg_chain_resolution_time_ms": 0,
            "total_chain_resolutions": 0,
            "cache_keys_count": 0,
        }
