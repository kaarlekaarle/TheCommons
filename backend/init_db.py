import asyncio
import logging
import sys
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from backend.database import init_db

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def init():
    logger.info("Creating initial database...")
    await init_db()
    logger.info("Database initialization completed.")


if __name__ == "__main__":
    asyncio.run(init())
