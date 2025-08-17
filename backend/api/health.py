"""Health check endpoints for the API."""

import json
from pathlib import Path
from typing import Any, Dict, Optional

from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from backend.core.redis import get_redis_client
from backend.database import get_db

router = APIRouter()


async def check_health() -> Dict[str, str]:
    """Check the health of the API and its dependencies.

    Returns:
        dict: Health status of the API and its dependencies
    """
    return {"status": "ok"}


@router.get("/health")
async def health_check() -> Dict[str, str]:
    """Simple health check endpoint."""
    return await check_health()


@router.get("/health/db")
async def health_check_db(db: AsyncSession = Depends(get_db)) -> Dict[str, str]:
    """Check database health."""
    try:
        # Try to execute a simple query
        await db.execute(text("SELECT 1"))
        return {"status": "ok", "database": "connected"}
    except Exception as e:
        return {"status": "error", "database": str(e)}


@router.get("/health/redis")
async def health_check_redis(redis_client=Depends(get_redis_client)) -> Dict[str, str]:
    """Check Redis health."""
    try:
        # Try to ping Redis
        await redis_client.ping()
        return {"status": "ok", "redis": "connected"}
    except Exception as e:
        return {"status": "error", "redis": str(e)}


@router.get("/health/cascade")
async def health_check_cascade() -> Dict[str, Any]:
    """Check constitutional cascade performance metrics."""
    try:
        # Look for the most recent cascade report
        reports_dir = Path("reports")
        
        # Check if reports directory exists
        if not reports_dir.exists():
            return {
                "ruleB": "unknown", 
                "effectiveBlockMs": None, 
                "p95Ms": None,
                "message": "No reports directory found"
            }

        cascade_files = list(reports_dir.glob("*cascade*.json"))

        if not cascade_files:
            return {
                "ruleB": "unknown", 
                "effectiveBlockMs": None, 
                "p95Ms": None,
                "message": "No cascade reports found"
            }

        # Get the most recent cascade file
        latest_file = max(cascade_files, key=lambda f: f.stat().st_mtime)

        try:
            with open(latest_file, "r") as f:
                cascade_data = json.load(f)
        except (json.JSONDecodeError, UnicodeDecodeError) as e:
            return {
                "ruleB": "error",
                "effectiveBlockMs": None,
                "p95Ms": None,
                "error": f"Invalid JSON in {latest_file.name}: {str(e)}"
            }

        # Extract performance metrics
        rule_b_status = "unknown"
        effective_block_ms: Optional[float] = None
        p95_ms: Optional[float] = None

        # Check for Rule B signals
        if "cascade_results" in cascade_data:
            for result in cascade_data["cascade_results"]:
                if result.get("rule_id") == "B":
                    rule_b_status = result.get("decision", "unknown")

                    # Look for override latency signal (#2)
                    if "triggered_signals" in result:
                        for signal in result["triggered_signals"]:
                            if signal.get("id") == "#2":  # Override latency signal
                                p95_ms = signal.get("p95_ms")
                                effective_block_ms = signal.get("value")
                                break
                    break

        return {
            "ruleB": rule_b_status,
            "effectiveBlockMs": effective_block_ms,
            "p95Ms": p95_ms,
        }

    except Exception as e:
        return {
            "ruleB": "error",
            "effectiveBlockMs": None,
            "p95Ms": None,
            "error": str(e),
        }
