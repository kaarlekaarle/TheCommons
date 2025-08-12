"""Middleware for The Commons."""
import time
import uuid
from typing import Callable

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

from backend.core.logging_json import (
    get_json_logger,
    set_request_context,
    clear_request_context,
    log_request_start,
    log_request_end,
    log_error
)

logger = get_json_logger(__name__)

class RequestContextMiddleware(BaseHTTPMiddleware):
    """Middleware to add request context to logs and handle request IDs."""
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Add request context to logs and measure request timing.
        
        Args:
            request: The incoming request.
            call_next: The next middleware or route handler.
            
        Returns:
            The response from the next middleware or route handler.
        """
        # Get or generate request ID
        request_id = request.headers.get("X-Request-ID")
        if not request_id:
            request_id = str(uuid.uuid4())
        
        # Set request context for logging
        set_request_context(request_id=request_id)
        
        # Store request ID in request state for access in handlers
        request.state.request_id = request_id
        
        # Log request start
        log_request_start(
            logger=logger,
            request_id=request_id,
            method=request.method,
            path=request.url.path,
            client_host=request.client.host if request.client else None,
        )
        
        # Measure request timing
        start_time = time.time()
        
        try:
            response = await call_next(request)
            
            # Add request ID to response headers
            response.headers["X-Request-ID"] = request_id
            
            # Log request completion
            log_request_end(
                logger=logger,
                request_id=request_id,
                method=request.method,
                path=request.url.path,
                status_code=response.status_code,
                response_time=time.time() - start_time,
            )
            
            return response
            
        except Exception as e:
            # Log request error
            log_error(
                logger=logger,
                error=e,
                request_id=request_id,
                method=request.method,
                path=request.url.path,
            )
            raise
        finally:
            # Clear request context
            clear_request_context() 