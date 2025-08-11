"""Simple test for poll results functionality."""

import pytest
import asyncio
from datetime import datetime
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from backend.models.base import Base
from backend.models.user import User
from backend.models.poll import Poll
from backend.models.option import Option
from backend.models.vote import Vote
from backend.models.delegation import Delegation
from backend.services.delegation import DelegationService
from backend.services.poll import get_poll_results
from backend.core.voting import create_vote


# Use the same database as the main application
DATABASE_URL = "postgresql+asyncpg://postgres:postgres@localhost:5432/the_commons"

# Create engine and session factory
engine = create_async_engine(DATABASE_URL, echo=True)
async_session_maker = sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)


async def create_test_user(session: AsyncSession, username: str, email: str, password: str) -> User:
    """Create a test user."""
    from backend.core.security import get_password_hash
    
    user = User(
        username=username,
        email=email,
        hashed_password=get_password_hash(password),
        is_active=True
    )
    session.add(user)
    await session.commit()
    await session.refresh(user)
    return user


async def create_test_poll(session: AsyncSession, creator: User, title: str, description: str) -> Poll:
    """Create a test poll."""
    poll = Poll(
        title=title,
        description=description,
        created_by=creator.id,
        status="active"
    )
    session.add(poll)
    await session.commit()
    await session.refresh(poll)
    return poll


async def create_test_option(session: AsyncSession, poll: Poll, text: str) -> Option:
    """Create a test option."""
    option = Option(
        text=text,
        poll_id=poll.id
    )
    session.add(option)
    await session.commit()
    await session.refresh(option)
    return option


@pytest.mark.asyncio
async def test_poll_results_with_delegation():
    """Test poll results with delegation support."""
    
    import time
    timestamp = int(time.time())
    
    async with async_session_maker() as session:
        # Create test users with unique email addresses
        alice = await create_test_user(session, f"alice_{timestamp}", f"alice_{timestamp}@test.com", "alice123")
        bob = await create_test_user(session, f"bob_{timestamp}", f"bob_{timestamp}@test.com", "bob123")
        
        # Create a test poll
        poll = await create_test_poll(
            session, 
            alice, 
            "Test Poll", 
            "A test poll for delegation voting"
        )
        
        # Create options
        option_a = await create_test_option(session, poll, "Option A")
        option_b = await create_test_option(session, poll, "Option B")
        
        # Bob delegates to Alice for this poll - create delegation directly
        from backend.models.delegation import Delegation
        
        delegation = Delegation(
            delegator_id=bob.id,
            delegatee_id=alice.id,
            poll_id=poll.id,
            start_date=datetime.utcnow(),
            end_date=None,
            chain_origin_id=bob.id
        )
        session.add(delegation)
        await session.commit()
        await session.refresh(delegation)
        
        # Verify delegation was created
        assert delegation is not None
        assert delegation.delegator_id == bob.id
        assert delegation.delegatee_id == alice.id
        assert delegation.poll_id == poll.id
        
        # Alice votes for Option A
        vote_data = {
            "poll_id": poll.id,
            "option_id": option_a.id,
            "user_id": alice.id,
            "weight": 1
        }
        
        vote = await create_vote(session, vote_data, alice)
        assert vote is not None
        assert vote.user_id == alice.id
        assert vote.option_id == option_a.id
        assert vote.poll_id == poll.id
        
        # Get poll results
        results = await get_poll_results(poll.id, session)
        
        # Verify we have results for both options
        assert len(results) == 2
        
        # Find Option A and Option B in results
        option_a_result = None
        option_b_result = None
        
        for result in results:
            if result.text == "Option A":
                option_a_result = result
            elif result.text == "Option B":
                option_b_result = result
        
        assert option_a_result is not None, "Option A result not found"
        assert option_b_result is not None, "Option B result not found"
        
        # Assert the expected vote counts
        # Option A should have 1 direct vote (Alice) + 1 delegated vote (Bob) = 2 total
        assert option_a_result.direct_votes == 1, f"Expected 1 direct vote, got {option_a_result.direct_votes}"
        assert option_a_result.delegated_votes == 1, f"Expected 1 delegated vote, got {option_a_result.delegated_votes}"
        assert option_a_result.total_votes == 2, f"Expected 2 total votes, got {option_a_result.total_votes}"
        
        # Option B should have 0 votes
        assert option_b_result.direct_votes == 0, f"Expected 0 direct votes, got {option_b_result.direct_votes}"
        assert option_b_result.delegated_votes == 0, f"Expected 0 delegated votes, got {option_b_result.delegated_votes}"
        assert option_b_result.total_votes == 0, f"Expected 0 total votes, got {option_b_result.total_votes}"
        
        print("✅ Test passed! Poll results with delegation working correctly.")


if __name__ == "__main__":
    asyncio.run(test_poll_results_with_delegation())
