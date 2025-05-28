import asyncio
import logging

from backend.database import init_db

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def init():
    logger.info("Creating initial database...")
    await init_db()
    logger.info("Database initialization completed.")


if __name__ == "__main__":
    asyncio.run(init())
