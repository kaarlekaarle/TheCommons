#!/usr/bin/env python3
"""
Small Poll Seeding Test Script

Creates a small poll with:
- 1 poll with 2 options
- 5 users voting directly for Option A
- 5 users delegating their votes to direct voters
- Measures performance of poll results endpoint
"""

import asyncio
import sys
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import List
from uuid import UUID

# Add the project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

import httpx
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from backend.core.security import get_password_hash
from backend.models.delegation import Delegation
from backend.models.option import Option
from backend.models.poll import Poll
from backend.models.user import User
from backend.models.vote import Vote


# Database configuration - Use Docker service name when running in container
import os
DATABASE_URL = os.getenv(
    "DATABASE_URL", 
    "postgresql+asyncpg://postgres:postgres@db:5432/the_commons"
)

# Create async engine and session maker
engine = create_async_engine(DATABASE_URL, echo=False)
async_session_maker = sessionmaker(
    engine, class_=AsyncSession, expire_on_commit=False
)


async def create_test_user(session: AsyncSession, username: str, email: str, password: str) -> User:
    """Create a test user."""
    try:
        user = User(
            username=username,
            email=email,
            hashed_password=get_password_hash(password),
            is_active=True,
            is_superuser=False
        )
        session.add(user)
        await session.commit()
        await session.refresh(user)
        print(f"   ✅ Created user: {username} (ID: {user.id})")
        return user
    except Exception as e:
        print(f"   ❌ Failed to create user {username}: {e}")
        await session.rollback()
        raise


async def create_test_poll_with_options(
    session: AsyncSession, 
    creator: User, 
    title: str, 
    description: str, 
    options: List[str]
) -> tuple[Poll, List[Option]]:
    """Create a test poll with options."""
    # Create poll
    poll = Poll(
        title=title,
        description=description,
        created_by=creator.id,
        status="active",
        start_date=datetime.utcnow(),
        end_date=datetime.utcnow() + timedelta(days=30),
        allow_delegation=True,
        require_authentication=True,
        max_votes_per_user=1
    )
    session.add(poll)
    await session.commit()
    await session.refresh(poll)
    
    # Create options one at a time to avoid UUID bulk insert issues
    option_objects = []
    for option_text in options:
        option = Option(
            poll_id=poll.id,
            text=option_text
        )
        session.add(option)
        await session.commit()
        await session.refresh(option)
        option_objects.append(option)
    
    return poll, option_objects


async def create_direct_vote(session: AsyncSession, user: User, poll: Poll, option: Option) -> Vote:
    """Create a direct vote for a user."""
    vote = Vote(
        user_id=user.id,
        poll_id=poll.id,
        option_id=option.id,
        weight=1,
        created_at=datetime.utcnow()
    )
    session.add(vote)
    await session.commit()
    await session.refresh(vote)
    return vote


async def create_delegation(session: AsyncSession, delegator: User, delegatee: User, poll: Poll) -> Delegation:
    """Create a delegation from delegator to delegatee for a specific poll."""
    delegation = Delegation(
        delegator_id=delegator.id,
        delegatee_id=delegatee.id,
        poll_id=poll.id,
        start_date=datetime.utcnow(),
        end_date=None  # Active delegation
    )
    session.add(delegation)
    await session.commit()
    await session.refresh(delegation)
    return delegation


async def seed_small_poll():
    """Seed a small poll with direct votes and delegations."""
    print("🚀 Starting small poll seeding...")
    
    # Use timestamp to make usernames unique
    import time
    timestamp = int(time.time())
    
    async with async_session_maker() as session:
        # Create poll creator
        creator = await create_test_user(
            session, 
            f"test_creator_{timestamp}", 
            f"test_creator_{timestamp}@test.com", 
            "creator123"
        )
        print(f"✅ Created poll creator: {creator.username}")
        
        # Create poll with 2 options
        poll, options = await create_test_poll_with_options(
            session,
            creator,
            title="Small Test Poll",
            description="A small poll to test the seeding script",
            options=["Option A", "Option B"]
        )
        
        option_a, option_b = options
        print(f"✅ Created poll: {poll.id}")
        print(f"   - Option A: {option_a.id}")
        print(f"   - Option B: {option_b.id}")
        
        # Create 5 direct voters
        print("📝 Creating 5 direct voters...")
        direct_voters = []
        for i in range(5):
            user = await create_test_user(
                session,
                f"direct_voter_{i}_{timestamp}",
                f"direct_voter_{i}_{timestamp}@test.com",
                f"password_{i}"
            )
            direct_voters.append(user)
            
            # Create vote for Option A
            await create_direct_vote(session, user, poll, option_a)
            print(f"   Created direct voter {i + 1}/5")
        
        print(f"✅ Created {len(direct_voters)} direct voters")
        
        # Create 5 users who delegate their votes
        print("🔗 Creating 5 users with delegations...")
        delegation_users = []
        
        # Create delegation chains: each direct voter gets 1 delegate
        for i in range(5):
            # Create delegator
            delegator = await create_test_user(
                session,
                f"delegator_{i}_{timestamp}",
                f"delegator_{i}_{timestamp}@test.com",
                f"password_{i}"
            )
            delegation_users.append(delegator)
            
            # Delegate to the corresponding direct voter
            delegatee = direct_voters[i]
            await create_delegation(session, delegator, delegatee, poll)
            print(f"   Created delegation {i + 1}/5")
        
        print(f"✅ Created {len(delegation_users)} users with delegations")
        
        # Verify the data
        print("🔍 Verifying data...")
        
        # Count direct votes
        votes_result = await session.execute(
            select(Vote).where(Vote.poll_id == poll.id)
        )
        direct_votes = votes_result.scalars().all()
        print(f"   Direct votes: {len(direct_votes)}")
        
        # Count delegations
        delegations_result = await session.execute(
            select(Delegation).where(Delegation.poll_id == poll.id)
        )
        delegations = delegations_result.scalars().all()
        print(f"   Delegations: {len(delegations)}")
        
        # Count total users
        total_users = len(direct_voters) + len(delegation_users) + 1  # +1 for creator
        print(f"   Total users: {total_users}")
        
        return poll.id, total_users, len(direct_votes), len(delegations), f"test_creator_{timestamp}"


async def measure_poll_results_performance(poll_id: UUID, creator_username: str):
    """Measure the performance of the poll results endpoint."""
    print(f"\n⏱️  Measuring performance for poll {poll_id}...")
    
    # Create test client - Use Docker service name when running in container
    api_base_url = os.getenv("API_BASE_URL", "http://web:8000")
    async with httpx.AsyncClient(base_url=api_base_url) as client:
        # First, get a token for authentication
        print(f"   🔐 Attempting authentication for user: {creator_username}")
        auth_response = await client.post("/api/token", data={
            "username": creator_username,
            "password": "creator123"
        })
        
        if auth_response.status_code != 200:
            print(f"❌ Authentication failed: {auth_response.text}")
            print(f"   Status code: {auth_response.status_code}")
            print(f"   Response: {auth_response.text}")
            return
        
        token_data = auth_response.json()
        access_token = token_data["access_token"]
        
        # Set authorization header
        headers = {"Authorization": f"Bearer {access_token}"}
        
        # Measure response time
        start_time = time.time()
        
        response = await client.get(f"/api/polls/{poll_id}/results", headers=headers)
        
        end_time = time.time()
        response_time_ms = (end_time - start_time) * 1000
        
        if response.status_code == 200:
            results = response.json()
            print(f"✅ Poll results retrieved successfully")
            print(f"   Response time: {response_time_ms:.2f} ms")
            print(f"   Results count: {len(results)}")
            
            # Display results
            for result in results:
                print(f"   - {result['text']}: {result['direct_votes']} direct + {result['delegated_votes']} delegated = {result['total_votes']} total")
        else:
            print(f"❌ Failed to get poll results: {response.status_code}")
            print(f"   Response: {response.text}")
        
        return response_time_ms


async def main():
    """Main function to run the seeding and performance test."""
    print("🎯 Small Poll Seeding and Performance Test")
    print("=" * 50)
    
    try:
        # Seed the small poll
        poll_id, total_users, direct_votes, delegations, creator_username = await seed_small_poll()
        
        print(f"\n📊 Seeding Summary:")
        print(f"   Total users: {total_users}")
        print(f"   Direct votes: {direct_votes}")
        print(f"   Delegations: {delegations}")
        
        # Measure performance
        response_time = await measure_poll_results_performance(poll_id, creator_username)
        
        print(f"\n🏁 Final Results:")
        print(f"   Total users: {total_users}")
        print(f"   Direct votes: {direct_votes}")
        print(f"   Delegations: {delegations}")
        if response_time is not None:
            print(f"   Response time: {response_time:.2f} ms")
        else:
            print(f"   Response time: Failed to measure")
        
    except Exception as e:
        print(f"❌ Error during seeding: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        # Close the engine
        await engine.dispose()
        print("\n🔚 Database connection closed")


if __name__ == "__main__":
    asyncio.run(main())
