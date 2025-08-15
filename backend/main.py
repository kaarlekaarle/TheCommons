import os
import asyncio
from contextlib import asynccontextmanager
from datetime import datetime

import redis.asyncio as redis
from fastapi import Depends, FastAPI, HTTPException, status, Request, Query, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordBearer
from fastapi_cache import FastAPICache
from fastapi_cache.backends.redis import RedisBackend
from fastapi_limiter import FastAPILimiter
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi.openapi.docs import get_swagger_ui_html
from fastapi.openapi.utils import get_openapi
from fastapi.responses import JSONResponse
import time
import structlog

# Initialize Sentry if DSN is provided
if os.getenv("SENTRY_DSN"):
    import sentry_sdk
    from sentry_sdk.integrations.fastapi import FastApiIntegration
    from sentry_sdk.integrations.redis import RedisIntegration
    from sentry_sdk.integrations.sqlalchemy import SqlalchemyIntegration
    
    sentry_sdk.init(
        dsn=os.getenv("SENTRY_DSN"),
        environment=os.getenv("ENVIRONMENT", "dev"),
        traces_sample_rate=float(os.getenv("SENTRY_TRACES_SAMPLE_RATE", "0.1")),
        integrations=[
            FastApiIntegration(),
            RedisIntegration(),
            SqlalchemyIntegration(),
        ],
        # Capture request data
        send_default_pii=True,
    )

from backend.api import auth, delegations, options, polls, users, votes, health, activity, comments, reactions, websocket, content, labels
from backend.config import settings
from backend.core.exception_handlers import configure_exception_handlers
from backend.core.logging_json import configure_json_logging, get_json_logger
from backend.core.middleware import RequestContextMiddleware
# from backend.core.audit import audit_log, AuditAction  # Replaced with middleware-based audit
from backend.core.audit_mw import AuditMiddleware
from backend.database import async_session_maker, get_db, init_db
from backend.core.redis import get_redis_client, close_redis_client
from backend.core.limiter import initialize_limiter, limiter_health
from backend.core.auth import get_current_user
from backend.models.user import User

# Configure JSON logging
configure_json_logging(
    log_level=settings.LOG_LEVEL if hasattr(settings, "LOG_LEVEL") else "INFO",
    environment=settings.ENVIRONMENT,
)

# Get logger
logger = get_json_logger(__name__)

# Configure OAuth2
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/token", auto_error=False)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup logic
    logger.info("starting_application")
    await init_db()
    logger.info("database_initialized")

    # Initialize Redis
    try:
        redis_client = await get_redis_client()
        await FastAPICache.init(RedisBackend(redis_client), prefix="fastapi-cache")
        logger.info("redis_initialized")
    except Exception as e:
        logger.error("redis_initialization_failed", error=str(e))
        logger.warning("Continuing without Redis - caching will be disabled")
    
    # Initialize rate limiter
    try:
        await initialize_limiter(settings.REDIS_URL)
        logger.info("rate_limiter_initialized")
    except Exception as e:
        logger.error("rate_limiter_initialization_failed", error=str(e))
        logger.warning("Continuing without rate limiting")
    
    # Start WebSocket heartbeat
    try:
        from backend.core.websocket import manager
        manager.heartbeat_task = asyncio.create_task(manager.start_heartbeat())
        logger.info("websocket_heartbeat_started")
    except Exception as e:
        logger.error("websocket_heartbeat_failed", error=str(e))

    # Log all available routes
    routes = []
    for route in app.routes:
        if hasattr(route, 'methods'):
            routes.append(f"{route.methods} {route.path}")
        elif hasattr(route, 'path'):
            routes.append(f"WS {route.path}")
    logger.info("available_routes", routes=routes)
    yield
    # Shutdown logic
    logger.info("shutting_down_application")
    
    try:
        # Stop WebSocket heartbeat
        from backend.core.websocket import manager
        if manager.heartbeat_task:
            manager.heartbeat_task.cancel()
            try:
                await manager.heartbeat_task
            except asyncio.CancelledError:
                pass
        logger.info("websocket_heartbeat_stopped")
    except Exception as e:
        logger.error("Error stopping WebSocket heartbeat", error=str(e))
    
    try:
        await close_redis_client()
        logger.info("redis_client_closed")
    except Exception as e:
        logger.error("Error closing Redis client", error=str(e))
    
    try:
        from backend.database import close_db_connections
        await close_db_connections()
        logger.info("database_connections_closed")
    except Exception as e:
        logger.error("Error closing database connections", error=str(e))
    
    logger.info("application_shutdown_complete")


# Create FastAPI app
app = FastAPI(
    title="The Commons API",
    description="""
    A secure and scalable voting system API built with FastAPI.
    
    ## Features
    
    * 🔐 Secure user authentication and authorization
    * 📊 Poll creation and management
    * 🗳️ Secure voting with delegation support
    * 📈 Real-time results and analytics
    * 🔄 Activity logging and audit trails
    
    ## Authentication
    
    All endpoints except `/health` and `/docs` require authentication using JWT tokens.
    Include the token in the Authorization header:
    
    ```
    Authorization: Bearer <your_token>
    ```
    
    ## Rate Limiting
    
    API endpoints are rate-limited to prevent abuse. The current limits are:
    
    * 100 requests per minute for authenticated users
    * 20 requests per minute for unauthenticated users
    
    ## Error Handling
    
    The API uses standard HTTP status codes and returns detailed error messages in the following format:
    
    ```json
    {
        "detail": "Error message",
        "code": "ERROR_CODE",
        "status_code": 400
    }
    ```
    """,
    version="1.0.0",
    docs_url=None,  # Disable default docs
    redoc_url=None,  # Disable default redoc
    openapi_url="/openapi.json",
    lifespan=lifespan,
)

# Add request context middleware
app.add_middleware(RequestContextMiddleware)

# Add audit middleware (before CORS) - temporarily disabled for debugging
# app.add_middleware(AuditMiddleware)

# Configure CORS based on environment
allowed_origins = (
    settings.ALLOWED_ORIGINS if isinstance(settings.ALLOWED_ORIGINS, list)
    else settings.ALLOWED_ORIGINS.split(",") if settings.ALLOWED_ORIGINS
    else ["http://localhost:5173", "http://localhost:5174"]  # Default to common dev ports
)

# Add development origins if in debug mode
if settings.DEBUG:
    dev_origins = ["http://localhost:3000", "http://127.0.0.1:5173", "http://127.0.0.1:5174", "http://127.0.0.1:5175", "http://localhost:5175"]
    allowed_origins.extend(dev_origins)

# Always add common development ports for local development
dev_ports = ["5173", "5174", "5175", "5176", "5177", "3000", "3001"]
for port in dev_ports:
    allowed_origins.extend([
        f"http://localhost:{port}",
        f"http://127.0.0.1:{port}"
    ])

# Remove duplicates while preserving order
seen = set()
allowed_origins = [x for x in allowed_origins if not (x in seen or seen.add(x))]

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Temporarily allow all origins for testing
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["Authorization", "Content-Type"],
    max_age=3600,  # Cache preflight requests for 1 hour
)

# Add security headers middleware
@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    response.headers["Content-Security-Policy"] = "default-src 'self'"
    return response

# Custom OpenAPI schema
def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema
    
    openapi_schema = get_openapi(
        title=app.title,
        version=app.version,
        description=app.description,
        routes=app.routes,
    )
    
    # Add security schemes
    openapi_schema["components"]["securitySchemes"] = {
        "Bearer": {
            "type": "http",
            "scheme": "bearer",
            "bearerFormat": "JWT",
        }
    }
    
    # Add global security requirement - removed to allow public endpoints
    # openapi_schema["security"] = [{"Bearer": []}]
    
    app.openapi_schema = openapi_schema
    return app.openapi_schema

app.openapi = custom_openapi

# Custom docs endpoint
@app.get("/docs", include_in_schema=False)
async def custom_swagger_ui_html():
    return get_swagger_ui_html(
        openapi_url="/openapi.json",
        title=f"{app.title} - Swagger UI",
        oauth2_redirect_url=app.swagger_ui_oauth2_redirect_url,
        swagger_js_url="https://cdn.jsdelivr.net/npm/swagger-ui-dist@5.9.0/swagger-ui-bundle.js",
        swagger_css_url="https://cdn.jsdelivr.net/npm/swagger-ui-dist@5.9.0/swagger-ui.css",
    )

# Include routers with rate limiting
logger.info("Registering routers...")
app.include_router(
    health.router,
    prefix="/api",
    tags=["health"],
)  # No rate limiting for health checks
app.include_router(
    auth.router,
    prefix="/api",
    tags=["auth"],
    # dependencies=[sensitive_rate_limiter],  # Temporarily disabled for Redis issues
)
app.include_router(
    users.router,
    prefix="/api/users",
    tags=["users"],
    # dependencies=[authenticated_rate_limiter],  # Temporarily disabled for Redis issues
)
app.include_router(
    votes.router,
    prefix="/api/votes",
    tags=["votes"],
    # dependencies=[authenticated_rate_limiter],  # Temporarily disabled for Redis issues
)
app.include_router(
    polls.router,
    prefix="/api/polls",
    tags=["polls"],
    # dependencies=[authenticated_rate_limiter],  # Temporarily disabled for Redis issues
)
app.include_router(
    options.router,
    prefix="/api/options",
    tags=["options"],
    # dependencies=[authenticated_rate_limiter],  # Temporarily disabled for Redis issues
)
app.include_router(
    delegations.router,
    prefix="/api/delegations",
    tags=["delegations"],
    # dependencies=[authenticated_rate_limiter],  # Temporarily disabled for Redis issues
)
app.include_router(
    activity.router,
    prefix="/api/activity",
    tags=["activity"],
    # dependencies=[public_rate_limiter],  # Temporarily disabled for Redis issues
)
app.include_router(
    comments.router,
    prefix="/api/polls",
    tags=["comments"],
    # dependencies=[authenticated_rate_limiter],  # Temporarily disabled for Redis issues
)
app.include_router(
    reactions.router,
    prefix="/api/comments",
    tags=["reactions"],
    # dependencies=[authenticated_rate_limiter],  # Temporarily disabled for Redis issues
)
app.include_router(
    websocket.router,
    tags=["websocket"],
)  # No rate limiting for WebSocket connections
app.include_router(
    content.router,
    prefix="/api",
    tags=["content"],
)  # No rate limiting for content endpoints
app.include_router(
    labels.router,
    prefix="/api/labels",
    tags=["labels"],
    # dependencies=[authenticated_rate_limiter],  # Temporarily disabled for Redis issues
)
app.include_router(
    labels.public_router,
    prefix="/api/labels",
    tags=["labels"],
)
logger.info("Routers registered successfully")

# Add exception handlers
configure_exception_handlers(app)

# Global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    from backend.core.logging_json import log_error
    
    request_id = getattr(request.state, "request_id", None)
    user_id = None
    
    # Try to get user ID from request if available
    try:
        if hasattr(request.state, "user"):
            user_id = str(request.state.user.id)
    except:
        pass
    
    # Log the error with additional context
    log_error(
        logger=logger,
        error=exc,
        request_id=request_id,
        user_id=user_id,
        path=request.url.path,
        method=request.method,
    )
    
    # Check for specific error types that might indicate server instability
    error_type = type(exc).__name__
    if error_type in ["ConnectionError", "TimeoutError", "DatabaseError", "OperationalError"]:
        logger.error("critical_error_detected", 
                    error_type=error_type, 
                    error=str(exc),
                    request_path=request.url.path)
    
    # Generate unified error response
    from backend.core.exception_handlers import get_error_response
    response = get_error_response(exc, include_details=settings.DEBUG, request_id=request_id)
    
    return JSONResponse(
        status_code=response["status_code"],
        content=response,
    )


@app.get("/")
async def root():
    return {"message": "Welcome to The Commons API"}


@app.get("/health")
async def health_check():
    """Basic health check endpoint."""
    return {
        "status": "healthy",
        "message": "Service is running",
        "timestamp": datetime.utcnow().isoformat(),
    }

@app.get("/api/labels/popular/public")
async def get_popular_labels_public(
    limit: int = Query(8, ge=1, le=24, description="Number of popular labels to return (max 24)"),
    request: Request = None,
    response: Response = None,
    db: AsyncSession = Depends(get_db),
):
    """Get popular labels by attached poll count (public endpoint)."""
    from backend.config import settings
    from backend.core.exceptions import UnavailableFeatureError
    from backend.models.label import Label
    from backend.models.poll_label import poll_labels
    from sqlalchemy import select, and_, func, desc
    import hashlib
    
    if not settings.LABELS_ENABLED:
        raise UnavailableFeatureError("Labels feature is disabled")
    
    # ETag support (skip in testing)
    if not settings.TESTING:
        # Get the most recent label update time for ETag
        latest_label_result = await db.execute(
            select(Label.updated_at).where(
                and_(
                    Label.is_active == True,
                    Label.is_deleted == False
                )
            ).order_by(desc(Label.updated_at)).limit(1)
        )
        latest_label_updated_at = latest_label_result.scalar_one_or_none()
        
        # Create weak ETag from limit and latest label update time
        etag_data = f"popular:{limit}:{latest_label_updated_at}"
        etag = f'W/"{hashlib.md5(etag_data.encode()).hexdigest()}"'
        
        # Check If-None-Match header
        if_none_match = request.headers.get("if-none-match") if request else None
        if if_none_match and if_none_match == etag:
            response.status_code = 304
            return None
        
        # Set ETag header
        if response:
            response.headers["ETag"] = etag
    
    # Get labels with poll counts
    result = await db.execute(
        select(
            Label.id,
            Label.name,
            Label.slug,
            func.count(poll_labels.c.poll_id).label('poll_count')
        ).outerjoin(poll_labels).where(
            and_(
                Label.is_active == True,
                Label.is_deleted == False
            )
        ).group_by(Label.id, Label.name, Label.slug)
        .order_by(desc(func.count(poll_labels.c.poll_id)), Label.slug)
        .limit(limit)
    )
    
    labels_with_counts = result.all()
    
    popular_labels = [
        {
            "id": str(row.id),
            "name": row.name,
            "slug": row.slug,
            "poll_count": row.poll_count
        }
        for row in labels_with_counts
    ]
    
    return popular_labels


@app.get("/health/db")
async def health_check_db():
    """Check database health."""
    try:
        logger.debug("checking_database_health")
        from backend.database import check_db_health
        
        is_healthy = await check_db_health()
        if is_healthy:
            return {
                "status": "healthy",
                "message": "Database connection is healthy",
                "connection": "connected",
                "timestamp": datetime.utcnow().isoformat(),
            }
        else:
            raise Exception("Database health check failed")
    except Exception as e:
        logger.error("database_health_check_failed", error=str(e))
        from backend.schemas.error import ErrorCodes
        raise HTTPException(
            status_code=503,
            detail={
                "detail": "Database connection error",
                "code": ErrorCodes.DATABASE_UNAVAILABLE,
                "status_code": 503,
                "error_type": "DatabaseError",
                "timestamp": datetime.utcnow().isoformat(),
                "details": {
                    "status": "unhealthy",
                    "connection": "disconnected",
                    "error": str(e),
                },
            },
        )


@app.get("/health/redis")
async def redis_health(redis_client=Depends(get_redis_client)):
    """Redis health check endpoint."""
    try:
        await redis_client.ping()
        return {
            "status": "healthy",
            "message": "Redis connection is healthy",
            "connection": "connected",
            "timestamp": datetime.utcnow().isoformat(),
        }
    except Exception as e:
        error_msg = str(e)
        logger.error("redis_health_check_failed", error=error_msg)
        if hasattr(redis_client, "is_mock") and redis_client.is_mock:
            error_msg = "Mock Redis client error"
        from backend.schemas.error import ErrorCodes
        raise HTTPException(
            status_code=503,
            detail={
                "detail": "Redis connection error",
                "code": ErrorCodes.REDIS_UNAVAILABLE,
                "status_code": 503,
                "error_type": "RedisError",
                "timestamp": datetime.utcnow().isoformat(),
                "details": {
                    "status": "unhealthy",
                    "connection": "disconnected",
                    "error": error_msg,
                },
            },
        )


@app.get("/health/comprehensive")
async def comprehensive_health_check():
    """Comprehensive health check for all services."""
    health_status = {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "services": {},
        "overall_status": "healthy"
    }
    
    # Check database
    try:
        from backend.database import check_db_health
        db_healthy = await check_db_health()
        health_status["services"]["database"] = {
            "status": "healthy" if db_healthy else "unhealthy",
            "message": "Database connection is healthy" if db_healthy else "Database connection failed"
        }
        if not db_healthy:
            health_status["overall_status"] = "unhealthy"
    except Exception as e:
        health_status["services"]["database"] = {
            "status": "unhealthy",
            "message": f"Database error: {str(e)}"
        }
        health_status["overall_status"] = "unhealthy"
    
    # Check Redis
    try:
        redis_client = await get_redis_client()
        await redis_client.ping()
        health_status["services"]["redis"] = {
            "status": "healthy",
            "message": "Redis connection is healthy"
        }
    except Exception as e:
        health_status["services"]["redis"] = {
            "status": "unhealthy",
            "message": f"Redis error: {str(e)}"
        }
        health_status["overall_status"] = "unhealthy"
    
    # Check rate limiter
    try:
        from backend.core.limiter import limiter_health
        limiter_status = limiter_health()
        health_status["services"]["rate_limiter"] = {
            "status": "healthy" if limiter_status.get("status") == "healthy" else "unhealthy",
            "message": limiter_status.get("message", "Rate limiter status unknown")
        }
        if limiter_status.get("status") != "healthy":
            health_status["overall_status"] = "unhealthy"
    except Exception as e:
        health_status["services"]["rate_limiter"] = {
            "status": "unhealthy",
            "message": f"Rate limiter error: {str(e)}"
        }
        health_status["overall_status"] = "unhealthy"
    
    # Check WebSocket manager
    try:
        from backend.core.websocket import manager
        ws_healthy = manager.is_healthy()
        health_status["services"]["websocket"] = {
            "status": "healthy" if ws_healthy else "unhealthy",
            "message": "WebSocket manager is healthy" if ws_healthy else "WebSocket manager is unhealthy",
            "stats": manager.get_connection_stats()
        }
        if not ws_healthy:
            health_status["overall_status"] = "unhealthy"
    except Exception as e:
        health_status["services"]["websocket"] = {
            "status": "unhealthy",
            "message": f"WebSocket error: {str(e)}"
        }
        health_status["overall_status"] = "unhealthy"
    
    # Return appropriate status code
    status_code = 200 if health_status["overall_status"] == "healthy" else 503
    
    return JSONResponse(
        status_code=status_code,
        content=health_status
    )


@app.get("/api/limiter/health")
async def limiter_health_check(user: User = Depends(get_current_user)):
    """Rate limiter health check endpoint (admin only)."""
    from backend.core.admin_audit import require_admin
    from backend.core.admin_audit import log_admin_action
    
    # Check if user is admin
    require_admin(user)
    
    # Log the admin action
    log_admin_action(
        action="limiter_health_check",
        target_resource="rate_limiter",
        user=user,
        result="success"
    )
    
    return limiter_health()
