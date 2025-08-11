#!/usr/bin/env python3
"""
Verify user script to check if a user exists and their password hash.
"""

import sys
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

import asyncio
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from backend.core.security import get_password_hash, verify_password
from backend.models.user import User

# Database configuration
DATABASE_URL = "postgresql+asyncpg://postgres:postgres@localhost:5432/the_commons"

# Create async engine and session maker
engine = create_async_engine(DATABASE_URL, echo=False)
async_session_maker = sessionmaker(
    engine, class_=AsyncSession, expire_on_commit=False
)


async def verify_user(username: str, password: str):
    """Verify a user exists and can authenticate."""
    async with async_session_maker() as session:
        # Find the user
        result = await session.execute(
            select(User).where(User.username == username)
        )
        user = result.scalar_one_or_none()
        
        if not user:
            print(f"❌ User '{username}' not found in database")
            return
        
        print(f"✅ User '{username}' found:")
        print(f"   ID: {user.id}")
        print(f"   Email: {user.email}")
        print(f"   Is Active (column): {user.is_active}")
        print(f"   Is Superuser (column): {user.is_superuser}")
        print(f"   Is Active (method): {user.is_user_active()}")
        print(f"   Is Superuser (method): {user.is_user_superuser()}")
        print(f"   Password Hash: [REDACTED]")
        
        # Test password verification
        is_valid = verify_password(password, user.hashed_password)
        print(f"   Password Verification: {'✅ Valid' if is_valid else '❌ Invalid'}")
        
        # Generate new hash for comparison
        new_hash = get_password_hash(password)
        print(f"   New Hash: [REDACTED]")
        print(f"   Hash Match: {'✅ Yes' if new_hash == user.hashed_password else '❌ No'}")


async def main():
    """Main function."""
    username = "test_creator_1754909462"
    password = "creator123"
    
    print(f"🔍 Verifying user: {username}")
    print("=" * 50)
    
    await verify_user(username, password)
    
    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())
