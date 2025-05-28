"""Middleware for The Commons."""
import time
import uuid
from typing import Callable

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

from backend.core.logging import add_context, get_logger

logger = get_logger(__name__)

class RequestContextMiddleware(BaseHTTPMiddleware):
    """Middleware to add request context to logs."""
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Add request context to logs and measure request timing.
        
        Args:
            request: The incoming request.
            call_next: The next middleware or route handler.
            
        Returns:
            The response from the next middleware or route handler.
        """
        # Generate request ID
        request_id = str(uuid.uuid4())
        
        # Add request context
        add_context(
            request_id=request_id,
            method=request.method,
            path=request.url.path,
            client_host=request.client.host if request.client else None,
        )
        
        # Log request start
        logger.info(
            "request_started",
            request_id=request_id,
            method=request.method,
            path=request.url.path,
        )
        
        # Measure request timing
        start_time = time.time()
        
        try:
            response = await call_next(request)
            
            # Add response context
            add_context(
                status_code=response.status_code,
                response_time=time.time() - start_time,
            )
            
            # Log request completion
            logger.info(
                "request_completed",
                request_id=request_id,
                status_code=response.status_code,
                response_time=time.time() - start_time,
            )
            
            return response
            
        except Exception as e:
            # Log request error
            logger.error(
                "request_failed",
                request_id=request_id,
                error=str(e),
                response_time=time.time() - start_time,
            )
            raise 