import time
import uuid
from typing import Optional, Dict, Any
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response
from fastapi import Depends
from backend.core.logging_json import get_json_logger
# from backend.core.auth import get_current_active_user_optional  # This function doesn't exist

logger = get_json_logger(__name__)

# Paths to skip for audit logging (noisy endpoints)
SKIP_AUDIT_PATHS = {
    "/api/health",
    "/health",
    "/health/db", 
    "/health/redis",
    "/docs",
    "/openapi.json",
    "/redoc",
    "/favicon.ico",
    "/",
}

# HTTP methods that are considered mutating
MUTATING_METHODS = {"POST", "PUT", "PATCH", "DELETE"}


class AuditMiddleware(BaseHTTPMiddleware):
    """Middleware for automatic audit logging of mutating requests."""
    
    async def dispatch(self, request: Request, call_next):
        # Generate or propagate request ID
        request_id = request.headers.get("X-Request-ID")
        if not request_id:
            request_id = str(uuid.uuid4())
        
        # Store request ID in request state
        request.state.request_id = request_id
        
        # Add request ID to response headers
        start_time = time.time()
        
        # Get user ID if available (best effort)
        user_id = None
        try:
            # Try to get current user without raising exceptions
            user = await get_current_active_user_optional(request)
            if user:
                user_id = str(user.id)
        except Exception:
            # User resolution failed, continue without user ID
            pass
        
        # Process the request
        response = await call_next(request)
        
        # Add request ID to response headers
        response.headers["X-Request-ID"] = request_id
        
        # Calculate duration
        duration_ms = int((time.time() - start_time) * 1000)
        
        # Log audit event for mutating requests
        if (request.method in MUTATING_METHODS and 
            request.url.path not in SKIP_AUDIT_PATHS):
            
            audit_data = {
                "ts": time.time(),
                "request_id": request_id,
                "user_id": user_id,
                "method": request.method,
                "path": request.url.path,
                "status": response.status_code,
                "duration_ms": duration_ms,
                "query_params": dict(request.query_params) if request.query_params else None,
            }
            
            logger.info(
                "audit_request",
                **audit_data
            )
        
        return response


async def get_current_active_user_optional(request: Request):
    """Get current user without raising exceptions if not authenticated."""
    try:
        from backend.core.auth import get_current_user_optional
        from backend.database import get_db
        from fastapi import Depends
        
        # Extract token from request headers
        auth_header = request.headers.get("Authorization")
        if not auth_header or not auth_header.startswith("Bearer "):
            return None
        
        token = auth_header.split(" ")[1]
        if not token:
            return None
        
        # Get database session
        db = await anext(get_db())
        
        # Get user from token
        return await get_current_user_optional(token, db)
    except Exception:
        return None


def audit_event(kind: str, data: Dict[str, Any], request: Request) -> None:
    """Log an explicit audit event with structured data."""
    request_id = getattr(request.state, "request_id", None)
    user_id = None
    
    # Try to get user ID from request state
    try:
        if hasattr(request.state, "user"):
            user_id = str(request.state.user.id)
    except Exception:
        pass
    
    audit_data = {
        "ts": time.time(),
        "request_id": request_id,
        "user_id": user_id,
        "kind": kind,
        "data": data,
    }
    
    logger.info(
        "audit_event",
        **audit_data
    )
