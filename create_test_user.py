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
        result = await session.execute(select(User).where(User.username == "mayor"))
        existing_user = result.scalar_one_or_none()
        
        if existing_user:
            print("Mayor user already exists!")
            print(f"Username: {existing_user.username}")
            print(f"Email: {existing_user.email}")
            print("Password: mayor123")
            return
        
        # Create new mayor user
        test_user = User(
            email="mayor@springfield.example",
            username="mayor",
            hashed_password=get_password_hash("mayor123"),
            is_active=True
        )
        
        session.add(test_user)
        await session.commit()
        
        print("Mayor user created successfully!")
        print("Username: mayor")
        print("Email: mayor@springfield.example")
        print("Password: mayor123")
        print("\nYou can now log in at http://localhost:5173/auth")


if __name__ == "__main__":
    asyncio.run(create_test_user())
