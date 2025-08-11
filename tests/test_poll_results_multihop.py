"""Test multi-hop delegation scenarios for poll results."""

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
from backend.core.security import get_password_hash


# Use the same database as the main application
DATABASE_URL = "postgresql+asyncpg://postgres:postgres@localhost:5432/the_commons"

# Create async engine and session maker
engine = create_async_engine(DATABASE_URL, echo=True)
async_session_maker = sessionmaker(
    engine, class_=AsyncSession, expire_on_commit=False
)


async def create_test_user(session: AsyncSession, username: str, email: str, password: str) -> User:
    """Create a test user."""
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


async def create_test_poll_with_options(
    session: AsyncSession, 
    creator: User, 
    title: str, 
    description: str, 
    options: list[str]
) -> tuple[Poll, list[Option]]:
    """Create a test poll with options."""
    # Create poll
    poll = Poll(
        title=title,
        description=description,
        created_by=creator.id,
        status="active"
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


@pytest.mark.asyncio
async def test_poll_results_multihop_delegation():
    """Test poll results with multi-hop delegation support."""
    
    import time
    timestamp = int(time.time())
    
    async with async_session_maker() as session:
        # Create test users with unique email addresses
        alice = await create_test_user(session, f"alice_{timestamp}", f"alice_{timestamp}@test.com", "alice123")
        bob = await create_test_user(session, f"bob_{timestamp}", f"bob_{timestamp}@test.com", "bob123")
        charlie = await create_test_user(session, f"charlie_{timestamp}", f"charlie_{timestamp}@test.com", "charlie123")
        
        print(f"✅ Created users: Alice ({alice.id}), Bob ({bob.id}), Charlie ({charlie.id})")
        
        # Charlie creates a poll with two options
        poll, options = await create_test_poll_with_options(
            session,
            charlie,
            title="Multi-hop Delegation Test Poll",
            description="A test poll for multi-hop delegation voting",
            options=["Option A", "Option B"]
        )
        
        option_a, option_b = options
        print(f"✅ Created poll: {poll.id} with options: {option_a.id} (Option A), {option_b.id} (Option B)")
        
        # Step 1: Alice delegates to Bob for this poll
        delegation_alice_to_bob = Delegation(
            delegator_id=alice.id,
            delegatee_id=bob.id,
            poll_id=poll.id,
            start_date=datetime.utcnow(),
            end_date=None
        )
        session.add(delegation_alice_to_bob)
        await session.commit()
        await session.refresh(delegation_alice_to_bob)
        
        print(f"✅ Alice ({alice.id}) delegated to Bob ({bob.id}) for poll {poll.id}")
        
        # Step 2: Bob delegates to Charlie for the same poll
        delegation_bob_to_charlie = Delegation(
            delegator_id=bob.id,
            delegatee_id=charlie.id,
            poll_id=poll.id,
            start_date=datetime.utcnow(),
            end_date=None
        )
        session.add(delegation_bob_to_charlie)
        await session.commit()
        await session.refresh(delegation_bob_to_charlie)
        
        print(f"✅ Bob ({bob.id}) delegated to Charlie ({charlie.id}) for poll {poll.id}")
        
        # Step 3: Charlie votes for Option A
        vote_data = {
            "poll_id": poll.id,
            "option_id": option_a.id,
            "user_id": charlie.id,
            "weight": 1
        }
        
        vote = await create_vote(session, vote_data, charlie)
        assert vote is not None
        assert vote.user_id == charlie.id
        assert vote.option_id == option_a.id
        assert vote.poll_id == poll.id
        
        print(f"✅ Charlie ({charlie.id}) voted for Option A ({option_a.id})")
        
        # Step 4: Get poll results
        results = await get_poll_results(poll.id, session)
        
        print(f"✅ Retrieved poll results: {len(results)} options")
        
        # Step 5: Verify results
        assert len(results) == 2, f"Expected 2 options, got {len(results)}"
        
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
        
        # Step 6: Assert the expected vote counts
        # Option A should have:
        # - 1 direct vote (Charlie)
        # - 1 delegated vote (Alice via Bob -> Charlie)
        # - 1 delegated vote (Bob -> Charlie)
        # Total: 3 votes
        expected_direct_votes = 1  # Charlie's direct vote
        expected_delegated_votes = 2  # Alice's vote via Bob + Bob's vote
        expected_total_votes = 3  # Total of all votes
        
        assert option_a_result.direct_votes == expected_direct_votes, \
            f"Expected {expected_direct_votes} direct votes, got {option_a_result.direct_votes}"
        assert option_a_result.delegated_votes == expected_delegated_votes, \
            f"Expected {expected_delegated_votes} delegated votes, got {option_a_result.delegated_votes}"
        assert option_a_result.total_votes == expected_total_votes, \
            f"Expected {expected_total_votes} total votes, got {option_a_result.total_votes}"
        
        # Option B should have 0 votes
        assert option_b_result.direct_votes == 0, \
            f"Expected 0 direct votes for Option B, got {option_b_result.direct_votes}"
        assert option_b_result.delegated_votes == 0, \
            f"Expected 0 delegated votes for Option B, got {option_b_result.delegated_votes}"
        assert option_b_result.total_votes == 0, \
            f"Expected 0 total votes for Option B, got {option_b_result.total_votes}"
        
        # Verify results are sorted by total votes (descending)
        assert results[0].total_votes >= results[1].total_votes
        
        print(f"✅ Test passed! Multi-hop delegation poll results working correctly.")
        print(f"   Option A: {option_a_result.direct_votes} direct + {option_a_result.delegated_votes} delegated = {option_a_result.total_votes} total")
        print(f"   Option B: {option_b_result.direct_votes} direct + {option_b_result.delegated_votes} delegated = {option_b_result.total_votes} total")


if __name__ == "__main__":
    asyncio.run(test_poll_results_multihop_delegation())
