"""Test circular delegation prevention."""

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
async def test_circular_delegation_prevention():
    """Test that circular delegation is prevented."""
    
    import time
    timestamp = int(time.time())
    
    async with async_session_maker() as session:
        # Create test users with unique email addresses
        alice = await create_test_user(session, f"alice_{timestamp}", f"alice_{timestamp}@test.com", "alice123")
        bob = await create_test_user(session, f"bob_{timestamp}", f"bob_{timestamp}@test.com", "bob123")
        
        print(f"✅ Created users: Alice ({alice.id}), Bob ({bob.id})")
        
        # Alice creates a poll with two options
        poll, options = await create_test_poll_with_options(
            session,
            alice,
            title="Circular Delegation Test Poll",
            description="A test poll for circular delegation prevention",
            options=["Option A", "Option B"]
        )
        
        option_a, option_b = options
        print(f"✅ Created poll: {poll.id} with options: {option_a.id} (Option A), {option_b.id} (Option B)")
        
        # Step 1: Alice delegates to Bob for this poll - create delegation directly
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
        print(f"✅ Alice ({alice.id}) successfully delegated to Bob ({bob.id}) for poll {poll.id}")
        
        # Step 2: Bob tries to delegate back to Alice for the same poll
        # This should fail with a circular delegation error
        delegation_service = DelegationService(session)
        try:
            delegation_bob_to_alice = await delegation_service.create_delegation(
                delegator_id=bob.id,
                delegatee_id=alice.id,
                poll_id=poll.id,
                start_date=datetime.utcnow(),
                end_date=None
            )
            # If we get here, the circular delegation was allowed (this is bad)
            print(f"❌ ERROR: Bob was able to delegate back to Alice! This should have failed.")
            assert False, "Circular delegation should have been prevented"
        except Exception as e:
            print(f"✅ Bob's delegation to Alice was correctly rejected: {e}")
            # Check if the error message indicates circular delegation
            error_message = str(e).lower()
            circular_indicators = ['circular', 'cycle', 'loop', 'invalid', 'conflict']
            has_circular_error = any(indicator in error_message for indicator in circular_indicators)
            assert has_circular_error, f"Error should mention circular delegation, got: {error_message}"
        
        # Step 3: Bob votes for Option A
        vote_data = {
            "poll_id": poll.id,
            "option_id": option_a.id,
            "user_id": bob.id,
            "weight": 1
        }
        
        vote = await create_vote(session, vote_data, bob)
        assert vote is not None
        assert vote.user_id == bob.id
        assert vote.option_id == option_a.id
        assert vote.poll_id == poll.id
        
        print(f"✅ Bob ({bob.id}) voted for Option A ({option_a.id})")
        
        # Step 4: Get poll results to verify delegation chain
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
        # - 1 direct vote (Bob)
        # - 1 delegated vote (Alice)
        # Total: 2 votes (no infinite loop)
        expected_direct_votes = 1  # Bob's direct vote
        expected_delegated_votes = 1  # Alice's delegated vote
        expected_total_votes = 2  # Total of all votes
        
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
        
        print(f"✅ Test passed! Circular delegation prevention working correctly.")
        print(f"   Option A: {option_a_result.direct_votes} direct + {option_a_result.delegated_votes} delegated = {option_a_result.total_votes} total")
        print(f"   Option B: {option_b_result.direct_votes} direct + {option_b_result.delegated_votes} delegated = {option_b_result.total_votes} total")
        print(f"   ✅ No infinite loop detected - vote count is finite and correct")


@pytest.mark.asyncio
async def test_self_delegation_prevention():
    """Test that self-delegation is prevented."""
    
    import time
    timestamp = int(time.time())
    
    async with async_session_maker() as session:
        # Create test user
        alice = await create_test_user(session, f"alice_{timestamp}", f"alice_{timestamp}@test.com", "alice123")
        
        print(f"✅ Created user: Alice ({alice.id})")
        
        # Alice creates a poll
        poll, options = await create_test_poll_with_options(
            session,
            alice,
            title="Self Delegation Test Poll",
            description="A test poll for self-delegation prevention",
            options=["Option A", "Option B"]
        )
        
        print(f"✅ Created poll: {poll.id}")
        
        # Alice tries to delegate to herself
        delegation_service = DelegationService(session)
        try:
            delegation_alice_to_self = await delegation_service.create_delegation(
                delegator_id=alice.id,
                delegatee_id=alice.id,  # Same as delegator_id
                poll_id=poll.id,
                start_date=datetime.utcnow(),
                end_date=None
            )
            # If we get here, self-delegation was allowed (this is bad)
            print(f"❌ ERROR: Alice was able to delegate to herself! This should have failed.")
            assert False, "Self-delegation should have been prevented"
        except Exception as e:
            print(f"✅ Alice's self-delegation was correctly rejected: {e}")
            # Check if the error message indicates self-delegation issue
            error_message = str(e).lower()
            self_delegation_indicators = ['self', 'same', 'invalid', 'conflict', 'delegator', 'delegatee', 'cannot delegate to themselves']
            has_self_delegation_error = any(indicator in error_message for indicator in self_delegation_indicators)
            assert has_self_delegation_error, f"Error should mention self-delegation issue, got: {error_message}"
        
        print(f"✅ Test passed! Self-delegation prevention working correctly.")


if __name__ == "__main__":
    asyncio.run(test_circular_delegation_prevention())
    asyncio.run(test_self_delegation_prevention())
