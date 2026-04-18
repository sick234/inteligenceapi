"""
Health check endpoint for monitoring and container orchestration.

Returns the status of all critical dependencies (database, Redis)
so orchestrators like Docker/Kubernetes know if the service is ready.
"""
from fastapi import APIRouter
from sqlalchemy import text
from redis.asyncio import Redis

from app.core.config import settings
from app.core.database import AsyncSessionLocal
from app.core.logging import get_logger

router = APIRouter()
logger = get_logger(__name__)


@router.get("", summary="Health Check")
async def health_check():
    """
    Checks the status of all critical dependencies.

    Returns HTTP 200 with component status if the API is operational.
    Returns HTTP 503 if any critical dependency is down.
    """
    health = {
        "status": "healthy",
        "version": settings.VERSION,
        "components": {},
    }

    # ── Check Database ────────────────────────────────────────────
    try:
        async with AsyncSessionLocal() as session:
            await session.execute(text("SELECT 1"))
        health["components"]["database"] = {"status": "up"}
    except Exception as e:
        logger.error("Database health check failed: %s", str(e))
        health["components"]["database"] = {"status": "down", "error": str(e)}
        health["status"] = "unhealthy"

    # ── Check Redis ───────────────────────────────────────────────
    try:
        redis = Redis.from_url(settings.REDIS_URL)
        await redis.ping()
        await redis.aclose()
        health["components"]["redis"] = {"status": "up"}
    except Exception as e:
        logger.error("Redis health check failed: %s", str(e))
        health["components"]["redis"] = {"status": "down", "error": str(e)}
        health["status"] = "unhealthy"

    status_code = 200 if health["status"] == "healthy" else 503
    from fastapi.responses import JSONResponse
    return JSONResponse(content=health, status_code=status_code)
