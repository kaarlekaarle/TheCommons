import asyncio
import os

from dotenv import load_dotenv
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine

# Load environment variables
load_dotenv()

# Get database URL from environment
DATABASE_URL = os.getenv(
    "DATABASE_URL", "postgresql+asyncpg://postgres:postgres@localhost:5432/the_commons"
)


async def reset_alembic():
    engine = create_async_engine(DATABASE_URL)

    async with engine.begin() as conn:
        # Drop all tables and recreate schema
        await conn.execute(text("DROP SCHEMA public CASCADE;"))
        await conn.execute(text("CREATE SCHEMA public;"))

    # Connect again to drop alembic_version if it exists (safeguard)
    async with engine.begin() as conn:
        await conn.execute(text("DROP TABLE IF EXISTS alembic_version;"))

    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(reset_alembic())
