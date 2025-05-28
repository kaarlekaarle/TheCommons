import os
from contextlib import asynccontextmanager

import redis.asyncio as redis
from fastapi import Depends, FastAPI, HTTPException, status, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordBearer
from fastapi_cache import FastAPICache
from fastapi_cache.backends.redis import RedisBackend
from fastapi_limiter import FastAPILimiter
from fastapi_limiter.depends import RateLimiter
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi.openapi.docs import get_swagger_ui_html
from fastapi.openapi.utils import get_openapi
from fastapi.responses import JSONResponse
import time
import structlog

from backend.api import auth, delegations, options, polls, users, votes, health
from backend.config import settings
from backend.core.exception_handlers import configure_exception_handlers
from backend.core.logging import configure_logging, get_logger
from backend.core.middleware import RequestContextMiddleware
from backend.core.audit import audit_log, AuditAction
from backend.database import async_session_maker, get_db, init_db

# Configure logging
configure_logging(
    log_level=settings.LOG_LEVEL if hasattr(settings, "LOG_LEVEL") else "INFO",
    json_format=not settings.DEBUG,
    console_output=True,
    log_file=settings.LOG_FILE,
)

# Get logger
logger = get_logger(__name__)

# Configure OAuth2
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/token")


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup logic
    logger.info("starting_application")
    await init_db()
    logger.info("database_initialized")

    # Initialize Redis
    try:
        redis_client = redis.from_url(settings.REDIS_URL)
        await FastAPILimiter.init(redis_client)
        await FastAPICache.init(RedisBackend(redis_client), prefix="fastapi-cache")
        logger.info("redis_initialized")
    except Exception as e:
        logger.error("redis_initialization_failed", error=str(e))
        raise

    # Log all available routes
    routes = [f"{route.methods} {route.path}" for route in app.routes]
    logger.info("available_routes", routes=routes)
    yield
    # Shutdown logic
    logger.info("shutting_down_application")


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

# Configure CORS based on environment
allowed_origins = (
    settings.ALLOWED_ORIGINS.split(",") if settings.ALLOWED_ORIGINS else []
)
if settings.DEBUG:
    allowed_origins.append("http://localhost:3000")  # Add localhost for development

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
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
    
    # Add global security requirement
    openapi_schema["security"] = [{"Bearer": []}]
    
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

# Initialize rate limiter
@app.on_event("startup")
async def startup():
    redis = await redis.from_url(settings.REDIS_URL, encoding="utf-8", decode_responses=True)
    await FastAPILimiter.init(redis)

# Health check endpoint
@app.get(
    "/health",
    tags=["Health"],
    summary="Health Check",
    description="Check the health of the API and its dependencies",
    response_description="Health status of the API and its dependencies",
)
async def health_check():
    return await health.check_health()

# Include routers with rate limiting
logger.info("Registering routers...")
app.include_router(
    auth.router,
    prefix="/api",
    tags=["auth"],
    dependencies=[
        Depends(RateLimiter(times=settings.RATE_LIMIT_PER_MINUTE, minutes=1))
    ],
)
app.include_router(
    users.router,
    prefix="/api/users",
    tags=["users"],
    dependencies=[
        Depends(RateLimiter(times=settings.RATE_LIMIT_PER_MINUTE, minutes=1))
    ],
)
app.include_router(
    votes.router,
    prefix="/api/votes",
    tags=["votes"],
    dependencies=[
        Depends(RateLimiter(times=settings.RATE_LIMIT_PER_MINUTE, minutes=1))
    ],
)
app.include_router(
    polls.router,
    prefix="/api/polls",
    tags=["polls"],
    dependencies=[
        Depends(RateLimiter(times=settings.RATE_LIMIT_PER_MINUTE, minutes=1))
    ],
)
app.include_router(
    options.router,
    prefix="/api/options",
    tags=["options"],
    dependencies=[
        Depends(RateLimiter(times=settings.RATE_LIMIT_PER_MINUTE, minutes=1))
    ],
)
app.include_router(
    delegations.router,
    prefix="/api/delegations",
    tags=["delegations"],
    dependencies=[
        Depends(RateLimiter(times=settings.RATE_LIMIT_PER_MINUTE, minutes=1))
    ],
)
logger.info("Routers registered successfully")

# Add exception handlers
configure_exception_handlers(app)

# Global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(
        "Unhandled exception",
        exc_info=exc,
        request_id=request.state.request_id,
        path=request.url.path,
        method=request.method,
    )
    return JSONResponse(
        status_code=500,
        content={
            "detail": "Internal server error",
            "code": "INTERNAL_ERROR",
            "status_code": 500,
        },
    )


@app.get("/")
async def root():
    return {"message": "Welcome to The Commons API"}


@app.get("/health/db")
async def health_check_db():
    """Check database health."""
    try:
        logger.debug("checking_database_health", database_url=settings.DATABASE_URL)
        async with async_session_maker() as session:
            await session.execute(text("SELECT 1"))
            await session.commit()
        return {
            "status": "healthy",
            "message": "Database connection is healthy",
            "connection": "connected",
        }
    except Exception as e:
        logger.error("database_health_check_failed", error=str(e))
        raise HTTPException(
            status_code=503,
            detail={
                "status": "unhealthy",
                "message": "Database connection error",
                "error": str(e),
                "connection": "disconnected",
            },
        )


async def get_redis_client():
    return await redis.from_url(settings.REDIS_URL)


@app.get("/health/redis")
async def redis_health(redis_client=Depends(get_redis_client)):
    """Redis health check endpoint."""
    try:
        await redis_client.ping()
        return {
            "status": "healthy",
            "message": "Redis connection is healthy",
            "connection": "connected",
        }
    except Exception as e:
        error_msg = str(e)
        logger.error("redis_health_check_failed", error=error_msg)
        if hasattr(redis_client, "is_mock") and redis_client.is_mock:
            error_msg = "Mock Redis client error"
        raise HTTPException(
            status_code=503,
            detail={
                "status": "unhealthy",
                "message": "Redis connection error",
                "error": error_msg,
                "connection": "disconnected",
            },
        )
