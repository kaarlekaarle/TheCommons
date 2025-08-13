#!/usr/bin/env python3

import asyncio
import sys
import os
from datetime import datetime
from uuid import uuid4

# Add the parent directory to the path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.services.delegation import DelegationService
from backend.models.user import User
from backend.core.security import get_password_hash
from backend.database import async_session_maker
from backend.models.poll import Poll

async def debug_delegation_chain_depth():
    """Debug the delegation chain depth test."""
    
    # Create a database session
    async with async_session_maker() as session:
        # Create test users
        users = []
        for i in range(10):
            u = User(
                email=f"u{i}@example.com",
                username=f"u{i}",
                hashed_password=get_password_hash("pw"),
            )
            session.add(u)
            users.append(u)
        
        await session.commit()
        
        # Refresh users to get their IDs
        for u in users:
            await session.refresh(u)
        
        service = DelegationService(session)
        
        # Create a chain of delegations: u0 -> u1 -> u2 -> ... -> u9
        for i in range(9):
            try:
                await service.create_delegation(
                    delegator_id=users[i].id,
                    delegatee_id=users[i + 1].id,
                    start_date=datetime.utcnow(),
                    end_date=None,
                    poll_id=None,
                )
                print(f"Created delegation {i}: {users[i].id} -> {users[i + 1].id}")
            except Exception as e:
                print(f"Error creating delegation {i}: {e}")
                return
        
        # Now try to create a delegation that would exceed depth limit
        try:
            await service.create_delegation(
                delegator_id=users[-1].id,  # Last user
                delegatee_id=users[0].id,   # First user (creates cycle)
                start_date=datetime.utcnow(),
                end_date=None,
                poll_id=None,
            )
            print("ERROR: Should have raised an exception!")
        except Exception as e:
            print(f"Expected exception: {type(e).__name__}: {e}")
            print(f"Exception message: {str(e)}")

if __name__ == "__main__":
    asyncio.run(debug_delegation_chain_depth())
