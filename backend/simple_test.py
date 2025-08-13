#!/usr/bin/env python3

import asyncio
import sys
import os
from datetime import datetime

# Add the parent directory to the path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.services.delegation import DelegationService
from backend.models.user import User
from backend.core.security import get_password_hash
from backend.database import async_session_maker
from backend.models.poll import Poll

async def test_delegation_chain_depth():
    """Test the delegation chain depth functionality."""
    
    # Create a database session
    async with async_session_maker() as session:
        # Create test users
        users = []
        for i in range(10):
            u = User(
                email=f"u{i}@example.com",
                username=f"u{i}",
                hashed_password=get_password_hash("pw"),
                is_active=True,
            )
            session.add(u)
            await session.commit()
            await session.refresh(u)
            users.append(u)
        
        service = DelegationService(session)
        
        # Create delegations in a chain
        for i in range(len(users) - 1):
            await service.create_delegation(
                delegator_id=users[i].id,
                delegatee_id=users[i + 1].id,
                start_date=datetime.utcnow(),
                end_date=None,
                poll_id=None,
            )
        
        print(f"Created chain of {len(users)} users")
        
        # Try to create delegation that would exceed depth limit
        try:
            await service.create_delegation(
                delegator_id=users[-1].id,  # Last user in chain
                delegatee_id=users[0].id,   # First user in chain
                start_date=datetime.utcnow(),
                end_date=None,
                poll_id=None,
            )
            print("ERROR: Expected exception but none was raised!")
        except Exception as e:
            print(f"Exception raised: {type(e).__name__}")
            print(f"Exception message: {str(e)}")
            print(f"Exception details: {getattr(e, 'details', 'No details')}")

if __name__ == "__main__":
    asyncio.run(test_delegation_chain_depth())
