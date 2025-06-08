"""Tests for model relationships."""

import pytest
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession
import uuid
from datetime import datetime

from backend.models.user import User
from backend.models.poll import Poll, PollStatus, PollVisibility
from backend.models.base import Base
from tests.db_config import get_test_db, test_engine, init_test_db
from backend.models.option import Option
from backend.models.vote import Vote
from backend.models.delegation import Delegation

@pytest.fixture(autouse=True)
async def setup_database():
    """Set up the test database before each test."""
    await init_test_db()
    yield
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

@pytest.mark.asyncio
async def test_user_poll_relationship(db_session: AsyncSession):
    """Test the relationship between User and Poll models."""
    # 1. Create a user
    user = User(
        email="test@example.com",
        username="testuser",
        hashed_password="hashed_password",
        is_active=True
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)

    # 2. Create polls for the user
    poll1 = Poll(
        title="Test Poll 1",
        description="Description 1",
        created_by=user.id,
        status=PollStatus.DRAFT,
        visibility=PollVisibility.PUBLIC
    )
    poll2 = Poll(
        title="Test Poll 2",
        description="Description 2",
        created_by=user.id,
        status=PollStatus.ACTIVE,
        visibility=PollVisibility.PUBLIC
    )
    db_session.add_all([poll1, poll2])
    await db_session.commit()

    # 3. Test relationship from user to polls
    result = await db_session.execute(select(Poll).where(Poll.created_by == user.id))
    user_polls = result.scalars().all()
    assert len(user_polls) == 2, f"Expected 2 polls, got {len(user_polls)}"
    assert any(p.title == "Test Poll 1" for p in user_polls)
    assert any(p.title == "Test Poll 2" for p in user_polls)

    # 4. Test relationship from poll to user
    result = await db_session.execute(select(Poll).where(Poll.id == poll1.id))
    poll = result.scalar_one()
    assert poll.user.id == user.id, f"Expected user id {user.id}, got {poll.user.id}"
    assert poll.user.email == user.email, f"Expected email {user.email}, got {poll.user.email}"

    # 5. Test cascade delete
    await db_session.delete(user)
    await db_session.commit()
    
    # Verify polls are deleted
    result = await db_session.execute(select(Poll).where(Poll.created_by == user.id))
    remaining_polls = result.scalars().all()
    assert len(remaining_polls) == 0, f"Expected 0 polls after user deletion, got {len(remaining_polls)}"

@pytest.mark.asyncio
async def test_poll_option_relationship(db_session):
    """Test the relationship between Poll and Option models."""
    # Create a user first
    user = User(
        id=str(uuid.uuid4()),
        email="test@example.com",
        username="testuser",
        hashed_password="hashed_password",
        email_verified=True
    )
    db_session.add(user)
    await db_session.commit()
    
    # Create a poll
    poll = Poll(
        id=str(uuid.uuid4()),
        title="Option Test Poll",
        description="Poll for option relationship test",
        created_by=user.id,
        status="DRAFT",
        visibility="PUBLIC",
        allow_delegation=True,
        require_authentication=True,
        max_votes_per_user=1
    )
    db_session.add(poll)
    await db_session.commit()
    
    # Create options
    option1 = Option(
        id=str(uuid.uuid4()),
        text="Option 1",
        description="First option",
        poll_id=poll.id,
        order=1
    )
    option2 = Option(
        id=str(uuid.uuid4()),
        text="Option 2",
        description="Second option",
        poll_id=poll.id,
        order=2
    )
    db_session.add_all([option1, option2])
    await db_session.commit()
    
    # Test relationship from poll to options
    poll_options = await db_session.execute(
        select(Option).where(Option.poll_id == poll.id).order_by(Option.order)
    )
    options = poll_options.scalars().all()
    assert len(options) == 2
    assert options[0].text == "Option 1"
    assert options[1].text == "Option 2"
    
    # Test relationship from option to poll
    option = await db_session.get(Option, option1.id)
    assert option.poll.title == "Option Test Poll"
    
    # Test cascade delete
    await db_session.delete(poll)
    await db_session.commit()
    
    # Verify options are deleted
    remaining_options = await db_session.execute(
        select(Option).where(Option.poll_id == poll.id)
    )
    assert len(remaining_options.scalars().all()) == 0 

@pytest.mark.asyncio
async def test_option_vote_relationship(db_session):
    """Test the relationship between Option and Vote models, and Poll-Vote as well."""
    # Create a user
    user = User(
        id=str(uuid.uuid4()),
        email="voteuser@example.com",
        username="voteuser",
        hashed_password="hashed_password",
        email_verified=True
    )
    db_session.add(user)
    await db_session.commit()

    # Create a poll
    poll = Poll(
        id=str(uuid.uuid4()),
        title="Vote Test Poll",
        description="Poll for vote relationship test",
        created_by=user.id,
        status="DRAFT",
        visibility="PUBLIC",
        allow_delegation=True,
        require_authentication=True,
        max_votes_per_user=1
    )
    db_session.add(poll)
    await db_session.commit()

    # Create options
    option1 = Option(
        id=str(uuid.uuid4()),
        text="Option 1",
        description="First option",
        poll_id=poll.id,
        order=1
    )
    option2 = Option(
        id=str(uuid.uuid4()),
        text="Option 2",
        description="Second option",
        poll_id=poll.id,
        order=2
    )
    db_session.add_all([option1, option2])
    await db_session.commit()

    # Create votes
    vote1 = Vote(
        id=str(uuid.uuid4()),
        user_id=user.id,
        poll_id=poll.id,
        option_id=option1.id,
        weight=1
    )
    vote2 = Vote(
        id=str(uuid.uuid4()),
        user_id=user.id,
        poll_id=poll.id,
        option_id=option2.id,
        weight=1
    )
    db_session.add_all([vote1, vote2])
    await db_session.commit()

    # Test relationship from option to votes
    option1_votes = await db_session.execute(
        select(Vote).where(Vote.option_id == option1.id)
    )
    assert len(option1_votes.scalars().all()) == 1

    # Test relationship from poll to votes
    poll_votes = await db_session.execute(
        select(Vote).where(Vote.poll_id == poll.id)
    )
    assert len(poll_votes.scalars().all()) == 2

    # Test cascade delete: delete option1, its vote should be deleted
    await db_session.delete(option1)
    await db_session.commit()
    remaining_votes = await db_session.execute(
        select(Vote).where(Vote.option_id == option1.id)
    )
    assert len(remaining_votes.scalars().all()) == 0

    # Test cascade delete: delete poll, all votes for poll should be deleted
    await db_session.delete(poll)
    await db_session.commit()
    poll_votes_after = await db_session.execute(
        select(Vote).where(Vote.poll_id == poll.id)
    )
    assert len(poll_votes_after.scalars().all()) == 0 

@pytest.mark.asyncio
async def test_user_vote_relationship(db_session):
    """Test the relationship between User and Vote models."""
    # Create a user
    user = User(
        id=str(uuid.uuid4()),
        email="voter@example.com",
        username="voter",
        hashed_password="hashed_password",
        email_verified=True
    )
    db_session.add(user)
    await db_session.commit()

    # Create a poll
    poll = Poll(
        id=str(uuid.uuid4()),
        title="User Vote Test Poll",
        description="Poll for testing user vote relationships",
        created_by=user.id,
        status="DRAFT",
        visibility="PUBLIC",
        allow_delegation=True,
        require_authentication=True,
        max_votes_per_user=2  # Allow multiple votes for testing
    )
    db_session.add(poll)
    await db_session.commit()

    # Create options
    option1 = Option(
        id=str(uuid.uuid4()),
        text="Option 1",
        description="First option",
        poll_id=poll.id,
        order=1
    )
    option2 = Option(
        id=str(uuid.uuid4()),
        text="Option 2",
        description="Second option",
        poll_id=poll.id,
        order=2
    )
    db_session.add_all([option1, option2])
    await db_session.commit()

    # Create votes with different weights
    vote1 = Vote(
        id=str(uuid.uuid4()),
        user_id=user.id,
        poll_id=poll.id,
        option_id=option1.id,
        weight=2,  # Higher weight for first option
        comment="First vote"
    )
    vote2 = Vote(
        id=str(uuid.uuid4()),
        user_id=user.id,
        poll_id=poll.id,
        option_id=option2.id,
        weight=1,  # Lower weight for second option
        comment="Second vote"
    )
    db_session.add_all([vote1, vote2])
    await db_session.commit()

    # Test relationship from user to votes
    user_votes = await db_session.execute(
        select(Vote).where(Vote.user_id == user.id).order_by(Vote.created_at)
    )
    votes = user_votes.scalars().all()
    assert len(votes) == 2
    assert votes[0].weight == 2
    assert votes[1].weight == 1
    assert votes[0].comment == "First vote"
    assert votes[1].comment == "Second vote"

    # Test relationship from vote to user
    vote = await db_session.get(Vote, vote1.id)
    assert vote.user.email == "voter@example.com"
    assert vote.user.username == "voter"

    # Test cascade delete: delete user, their votes should be deleted
    await db_session.delete(user)
    await db_session.commit()
    
    # Verify votes are deleted
    remaining_votes = await db_session.execute(
        select(Vote).where(Vote.user_id == user.id)
    )
    assert len(remaining_votes.scalars().all()) == 0

    # Verify poll and options still exist
    poll_exists = await db_session.get(Poll, poll.id)
    assert poll_exists is not None
    option_exists = await db_session.get(Option, option1.id)
    assert option_exists is not None 

@pytest.mark.asyncio
async def test_delegation_relationships(db_session):
    """Test the delegation relationships between users."""
    # Create three users: delegator, delegatee, and chain delegatee
    delegator = User(
        id=str(uuid.uuid4()),
        email="delegator@example.com",
        username="delegator",
        hashed_password="hashed_password",
        email_verified=True
    )
    delegatee = User(
        id=str(uuid.uuid4()),
        email="delegatee@example.com",
        username="delegatee",
        hashed_password="hashed_password",
        email_verified=True
    )
    chain_delegatee = User(
        id=str(uuid.uuid4()),
        email="chain_delegatee@example.com",
        username="chain_delegatee",
        hashed_password="hashed_password",
        email_verified=True
    )
    db_session.add_all([delegator, delegatee, chain_delegatee])
    await db_session.commit()

    # Create a poll
    poll = Poll(
        id=str(uuid.uuid4()),
        title="Delegation Test Poll",
        description="Poll for testing delegation relationships",
        created_by=delegator.id,
        status="DRAFT",
        visibility="PUBLIC",
        allow_delegation=True,
        require_authentication=True,
        max_votes_per_user=1
    )
    db_session.add(poll)
    await db_session.commit()

    # Create direct delegation
    direct_delegation = Delegation(
        id=str(uuid.uuid4()),
        delegator_id=delegator.id,
        delegatee_id=delegatee.id,
        poll_id=poll.id,
        start_date=datetime.utcnow(),
        chain_origin_id=delegator.id  # Direct delegation, so origin is the delegator
    )
    db_session.add(direct_delegation)
    await db_session.commit()

    # Create chain delegation (delegatee delegates to chain_delegatee)
    chain_delegation = Delegation(
        id=str(uuid.uuid4()),
        delegator_id=delegatee.id,
        delegatee_id=chain_delegatee.id,
        poll_id=poll.id,
        start_date=datetime.utcnow(),
        chain_origin_id=delegator.id  # Chain delegation, so origin is the original delegator
    )
    db_session.add(chain_delegation)
    await db_session.commit()

    # Test direct delegation relationship
    delegations = await db_session.execute(
        select(Delegation).where(
            and_(
                Delegation.delegator_id == delegator.id,
                Delegation.poll_id == poll.id
            )
        )
    )
    direct_delegations = delegations.scalars().all()
    assert len(direct_delegations) == 1
    assert str(direct_delegations[0].delegatee_id) == delegatee.id
    assert str(direct_delegations[0].chain_origin_id) == delegator.id

    # Test chain delegation relationship
    chain_delegations = await db_session.execute(
        select(Delegation).where(
            and_(
                Delegation.delegator_id == delegatee.id,
                Delegation.poll_id == poll.id
            )
        )
    )
    chain_delegations_list = chain_delegations.scalars().all()
    assert len(chain_delegations_list) == 1
    assert str(chain_delegations_list[0].delegatee_id) == chain_delegatee.id
    assert str(chain_delegations_list[0].chain_origin_id) == delegator.id

    # Test delegation revocation
    direct_delegation.revoked_at = datetime.utcnow()
    await db_session.commit()

    # Verify delegation is revoked
    active_delegations = await db_session.execute(
        select(Delegation).where(
            and_(
                Delegation.delegator_id == delegator.id,
                Delegation.poll_id == poll.id,
                Delegation.revoked_at.is_(None)
            )
        )
    )
    assert len(active_delegations.scalars().all()) == 0

    # Test cascade delete: delete poll should delete delegations
    await db_session.delete(poll)
    await db_session.commit()

    # Verify delegations are deleted
    remaining_delegations = await db_session.execute(
        select(Delegation).where(Delegation.poll_id == poll.id)
    )
    assert len(remaining_delegations.scalars().all()) == 0

    # Verify users still exist
    delegator_exists = await db_session.get(User, delegator.id)
    assert delegator_exists is not None
    delegatee_exists = await db_session.get(User, delegatee.id)
    assert delegatee_exists is not None
    chain_delegatee_exists = await db_session.get(User, chain_delegatee.id)
    assert chain_delegatee_exists is not None 