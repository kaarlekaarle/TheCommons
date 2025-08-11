#!/usr/bin/env python3
"""
Fix user active status script.
"""

import sys
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

import asyncio
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from backend.models.user import User

# Database configuration
DATABASE_URL = "postgresql+asyncpg://postgres:postgres@localhost:5432/the_commons"

# Create async engine and session maker
engine = create_async_engine(DATABASE_URL, echo=False)
async_session_maker = sessionmaker(
    engine, class_=AsyncSession, expire_on_commit=False
)


async def fix_user_status():
    """Fix user active status."""
    username = "test_creator_1754909462"
    
    print(f"🔧 Fixing user status for: {username}")
    print("=" * 50)
    
    async with async_session_maker() as session:
        # Find the user
        result = await session.execute(
            select(User).where(User.username == username)
        )
        user = result.scalar_one_or_none()
        
        if not user:
            print(f"❌ User '{username}' not found")
            return
        
        print(f"✅ Found user: {user.username}")
        print(f"   Before - Is Active: {user.is_active}")
        print(f"   Before - Is Superuser: {user.is_superuser}")
        
        # Update the user
        await session.execute(
            update(User)
            .where(User.id == user.id)
            .values(is_active=True, is_superuser=False)
        )
        await session.commit()
        
        # Refresh and check
        await session.refresh(user)
        print(f"   After - Is Active: {user.is_active}")
        print(f"   After - Is Superuser: {user.is_superuser}")
        print(f"   Method - Is Active: {user.is_user_active()}")
        print(f"   Method - Is Superuser: {user.is_user_superuser()}")
        
        print("✅ User status updated successfully!")


async def main():
    """Main function."""
    await fix_user_status()
    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())
