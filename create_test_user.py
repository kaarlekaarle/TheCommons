#!/usr/bin/env python3
"""
Script to create a test user for development.
Run this script to create a user that can be used to log into the application.
"""

import asyncio
import sys
import os

# Add the backend directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

from backend.database import async_session_maker
from backend.models.user import User
from backend.core.security import get_password_hash


async def create_test_user():
    """Create a test user for development."""
    async with async_session_maker() as session:
        # Check if user already exists
        from sqlalchemy import select
        result = await session.execute(select(User).where(User.username == "testuser"))
        existing_user = result.scalar_one_or_none()
        
        if existing_user:
            print("Test user already exists!")
            print(f"Username: {existing_user.username}")
            print(f"Email: {existing_user.email}")
            print("Password: password")
            return
        
        # Create new test user
        test_user = User(
            email="test@example.com",
            username="testuser",
            hashed_password=get_password_hash("password"),
            is_active=True
        )
        
        session.add(test_user)
        await session.commit()
        
        print("Test user created successfully!")
        print("Username: testuser")
        print("Email: test@example.com")
        print("Password: password")
        print("\nYou can now log in at http://localhost:5173/auth")


if __name__ == "__main__":
    asyncio.run(create_test_user())
