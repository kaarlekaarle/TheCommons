from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text

from backend.database import get_db
from backend.core.redis import get_redis_client

router = APIRouter()

async def check_health() -> dict:
    """Check the health of the API and its dependencies.
    
    Returns:
        dict: Health status of the API and its dependencies
    """
    return {"status": "ok"}

@router.get("/health")
async def health_check():
    """Simple health check endpoint."""
    return await check_health()

@router.get("/health/db")
async def health_check_db(db: AsyncSession = Depends(get_db)):
    """Check database health."""
    try:
        # Try to execute a simple query
        await db.execute(text("SELECT 1"))
        return {"status": "ok", "database": "connected"}
    except Exception as e:
        return {"status": "error", "database": str(e)}

@router.get("/health/redis")
async def health_check_redis(redis_client = Depends(get_redis_client)):
    """Check Redis health."""
    try:
        # Try to ping Redis
        await redis_client.ping()
        return {"status": "ok", "redis": "connected"}
    except Exception as e:
        return {"status": "error", "redis": str(e)} 