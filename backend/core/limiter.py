import os
import logging
from typing import Optional, Dict, Any
from functools import wraps
from fastapi import HTTPException, Request, Response
from fastapi.responses import JSONResponse

logger = logging.getLogger(__name__)

class NoOpLimiter:
    """No-op limiter that passes through all requests when Redis is unavailable."""
    
    def limit(self, rate_limit: str):
        """Decorator that does nothing - passes through all requests."""
        def decorator(func):
            @wraps(func)
            async def wrapper(*args, **kwargs):
                return await func(*args, **kwargs)
            return wrapper
        return decorator

class RedisLimiter:
    """Redis-based rate limiter using fastapi-limiter."""
    
    def __init__(self):
        try:
            from fastapi_limiter import FastAPILimiter
            from fastapi_limiter.depends import RateLimiter
            import redis.asyncio as redis
            
            self.FastAPILimiter = FastAPILimiter
            self.RateLimiter = RateLimiter
            self.redis = redis
            self._initialized = False
        except ImportError as e:
            logger.error(f"Rate limiting dependencies not available: {e}")
            raise
    
    async def initialize(self, redis_url: str) -> bool:
        """Initialize the Redis limiter."""
        try:
            redis_client = self.redis.from_url(redis_url, encoding="utf-8", decode_responses=True)
            await self.FastAPILimiter.init(redis_client)
            self._initialized = True
            logger.info("Rate limiting initialized with Redis backend")
            return True
        except Exception as e:
            logger.error(f"Failed to initialize Redis limiter: {e}")
            return False
    
    def limit(self, rate_limit: str):
        """Decorator that applies rate limiting."""
        if not self._initialized:
            logger.warning("Rate limiter not initialized, falling back to no-op")
            return NoOpLimiter().limit(rate_limit)
        
        return self.RateLimiter(times=rate_limit)

# Global limiter instance
limiter: Optional[RedisLimiter] = None
noop_limiter = NoOpLimiter()

async def initialize_limiter(redis_url: Optional[str] = None) -> None:
    """Initialize the rate limiter based on configuration."""
    global limiter
    
    enabled = os.getenv("RATE_LIMIT_ENABLED", "true").lower() == "true"
    
    if not enabled:
        logger.info("Rate limiting disabled via RATE_LIMIT_ENABLED=false")
        limiter = noop_limiter
        return
    
    if not redis_url:
        logger.warning("Rate limiting enabled but REDIS_URL not provided, falling back to no-op")
        limiter = noop_limiter
        return
    
    try:
        limiter = RedisLimiter()
        success = await limiter.initialize(redis_url)
        if not success:
            logger.warning("Failed to initialize Redis limiter, falling back to no-op")
            limiter = noop_limiter
    except Exception as e:
        logger.warning(f"Rate limiter initialization failed: {e}, falling back to no-op")
        limiter = noop_limiter

def get_limiter():
    """Get the current limiter instance."""
    return limiter if limiter is not None else noop_limiter

def limiter_health() -> Dict[str, Any]:
    """Get the health status of the rate limiter."""
    if limiter is None:
        return {"enabled": False, "backend": "noop"}
    
    if isinstance(limiter, NoOpLimiter):
        return {"enabled": False, "backend": "noop"}
    
    if hasattr(limiter, '_initialized') and limiter._initialized:
        return {"enabled": True, "backend": "redis"}
    else:
        return {"enabled": False, "backend": "redis_failed"}
