#!/usr/bin/env python3
"""
Test authentication script.
"""

import sys
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

import asyncio
import httpx
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from backend.core.auth import authenticate_user, create_access_token
from backend.database import get_db
from backend.models.user import User

# Database configuration
DATABASE_URL = "postgresql+asyncpg://postgres:postgres@localhost:5432/the_commons"

# Create async engine and session maker
engine = create_async_engine(DATABASE_URL, echo=False)
async_session_maker = sessionmaker(
    engine, class_=AsyncSession, expire_on_commit=False
)


async def test_direct_auth():
    """Test authentication directly."""
    username = "test_creator_1754909462"
    password = "creator123"
    
    print(f"🔐 Testing direct authentication for: {username}")
    print("=" * 50)
    
    async with async_session_maker() as session:
        # Test direct authentication
        user = await authenticate_user(session, username, password)
        if user:
            print(f"✅ Direct authentication successful!")
            print(f"   User ID: {user.id}")
            print(f"   Username: {user.username}")
            print(f"   Is Active (column): {user.is_active}")
            print(f"   Is Active (method): {user.is_user_active()}")
            
            # Create token
            token = create_access_token({"sub": str(user.id)})
            print(f"   Token: [REDACTED]")
            
            return token
        else:
            print("❌ Direct authentication failed")
            return None


async def test_api_auth():
    """Test API authentication."""
    username = "test_creator_1754909462"
    password = "creator123"
    
    print(f"\n🌐 Testing API authentication for: {username}")
    print("=" * 50)
    
    async with httpx.AsyncClient(base_url="http://localhost:8000") as client:
        auth_response = await client.post("/api/token", data={
            "username": username,
            "password": password
        })
        
        print(f"   Status Code: {auth_response.status_code}")
        print(f"   Response: {auth_response.text}")
        
        if auth_response.status_code == 200:
            token_data = auth_response.json()
            print(f"   ✅ API authentication successful!")
            print(f"   Token: [REDACTED]")
            return token_data['access_token']
        else:
            print(f"   ❌ API authentication failed")
            return None


async def main():
    """Main function."""
    print("🎯 Authentication Test")
    print("=" * 50)
    
    # Test direct authentication
    direct_token = await test_direct_auth()
    
    # Test API authentication
    api_token = await test_api_auth()
    
    # Compare results
    print(f"\n📊 Results Summary:")
    print(f"   Direct Auth: {'✅ Success' if direct_token else '❌ Failed'}")
    print(f"   API Auth: {'✅ Success' if api_token else '❌ Failed'}")
    
    if direct_token and api_token:
        print(f"   Token Match: {'✅ Yes' if direct_token == api_token else '❌ No'} (tokens redacted)")
    
    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())
