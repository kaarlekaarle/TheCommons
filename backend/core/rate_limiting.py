"""Rate limiting configuration and dependencies."""

import os
from enum import Enum
from typing import Optional, Callable, Any
from fastapi import Depends, Request, Response
from fastapi_limiter.depends import RateLimiter
from backend.config import settings
from backend.core.logging import get_logger

TESTING = os.getenv("TESTING", "false").lower() == "true"

logger = get_logger(__name__)

class RateLimitTier(str, Enum):
    """Rate limit tiers for different types of endpoints."""
    PUBLIC = "public"           # Unauthenticated endpoints
    AUTHENTICATED = "auth"      # Regular authenticated endpoints
    SENSITIVE = "sensitive"     # Sensitive operations (login, password reset)
    ADMIN = "admin"            # Administrative operations

# Rate limit configurations for different tiers
RATE_LIMITS = {
    RateLimitTier.PUBLIC: {
        "times": 20,           # 20 requests
        "minutes": 1           # per minute
    },
    RateLimitTier.AUTHENTICATED: {
        "times": settings.RATE_LIMIT_PER_MINUTE,  # From settings
        "minutes": 1
    },
    RateLimitTier.SENSITIVE: {
        "times": 5,            # 5 requests
        "seconds": 60          # per minute
    },
    RateLimitTier.ADMIN: {
        "times": 100,          # 100 requests
        "minutes": 1
    }
}

def get_rate_limiter(tier: RateLimitTier) -> Callable:
    """
    Get a rate limiter dependency for the specified tier.
    
    Args:
        tier: The rate limit tier to use
        
    Returns:
        A FastAPI dependency that applies the rate limit
    """
    if TESTING:
        class _Noop:
            async def __aenter__(self): return None
            async def __aexit__(self, *args): return False
        return Depends(lambda: _Noop())
    
    limit_config = RATE_LIMITS[tier]
    
    async def rate_limiter_dependency(request: Request, response: Response) -> Any:
        """
        Rate limiter dependency that applies the configured limit.
        
        Args:
            request: The FastAPI request object
            response: The FastAPI response object
            
        Returns:
            The result of the rate limiter check
        """
        # Get the appropriate rate limit configuration
        if "seconds" in limit_config:
            limiter = RateLimiter(
                times=limit_config["times"],
                seconds=limit_config["seconds"]
            )
        else:
            limiter = RateLimiter(
                times=limit_config["times"],
                minutes=limit_config["minutes"]
            )
            
        # Apply the rate limit
        return await limiter(request, response)
    
    return Depends(rate_limiter_dependency)

# Common rate limiter dependencies
public_rate_limiter = get_rate_limiter(RateLimitTier.PUBLIC)
authenticated_rate_limiter = get_rate_limiter(RateLimitTier.AUTHENTICATED)
sensitive_rate_limiter = get_rate_limiter(RateLimitTier.SENSITIVE)
admin_rate_limiter = get_rate_limiter(RateLimitTier.ADMIN) 