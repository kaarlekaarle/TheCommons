import asyncio
from datetime import datetime
from uuid import uuid4

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from backend.core.exceptions.delegation import (
    CircularDelegationError,
    DelegationAlreadyExistsError,
    SelfDelegationError,
)
from backend.models.delegation import Delegation
from backend.services.delegation import DelegationService

# Use in-memory SQLite for isolation
database_url = "sqlite+aiosqlite:///:memory:"
engine = create_async_engine(database_url, echo=True)
AsyncSessionLocal = sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)


async def setup_db():
    # Import all models and create tables
    from backend.models.base import Base

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def main():
    await setup_db()
    async with AsyncSessionLocal() as session:
        service = DelegationService(session)
        user1 = uuid4()
        user2 = uuid4()
        try:
            print("Creating delegation...")
            delegation = await service.create_delegation(
                delegator_id=user1,
                delegatee_id=user2,
                start_date=datetime.utcnow(),
                end_date=None,
            )
            print("Delegation created:", delegation)
        except Exception as e:
            print("Exception occurred:", repr(e))
            import traceback

            traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
