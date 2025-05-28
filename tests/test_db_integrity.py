"""Test database integrity and constraints."""

import asyncio
import uuid

import pytest
from sqlalchemy import func, select, text

from backend.models.option import Option
from backend.models.poll import Poll
from backend.models.user import User
from backend.models.vote import Vote
from tests.utils import (
    create_test_user,
    create_test_poll,
    create_test_option,
    create_test_vote,
    generate_unique_username,
    generate_unique_email,
)

pytestmark = pytest.mark.asyncio

async def test_database_constraints(db_session):
    """Test database constraints and integrity."""
    # Create test user
    test_user = await create_test_user(db_session)

    # Test unique constraints
    duplicate_user = User(
        email=test_user.email,  # Duplicate email
        username=generate_unique_username(),
        hashed_password="test_password",
        is_active=True,
    )
    with pytest.raises(Exception):  # Should raise unique constraint violation
        db_session.add(duplicate_user)
        await db_session.commit()
    await db_session.rollback()

    # Create a test poll
    test_poll = await create_test_poll(db_session, test_user)

    # Create a test option
    test_option = await create_test_option(db_session, test_poll)

    # Test foreign key constraints
    invalid_vote = Vote(
        user_id=99999,  # Non-existent user_id
        poll_id=test_poll.id,
        option_id=test_option.id,
    )
    with pytest.raises(Exception):  # Should raise foreign key constraint violation
        db_session.add(invalid_vote)
        await db_session.commit()
    await db_session.rollback()

async def test_concurrent_operations(db_session):
    """Test concurrent database operations."""
    # Create test data
    test_user = await create_test_user(db_session)
    test_poll = await create_test_poll(db_session, test_user)
    test_option = await create_test_option(db_session, test_poll)

    # Test concurrent vote creation
    async def create_vote(i: int):
        return await create_test_vote(db_session, test_user, test_poll, test_option)

    # Create multiple votes concurrently
    tasks = [create_vote(i) for i in range(5)]
    votes = await asyncio.gather(*tasks)

    # Verify all votes were created
    assert len(votes) == 5
    for vote in votes:
        assert vote.user_id == test_user.id
        assert vote.poll_id == test_poll.id
        assert vote.option_id == test_option.id

async def test_transaction_rollback(db_session):
    """Test transaction rollback functionality."""
    # Create test data
    test_user = await create_test_user(db_session)
    test_poll = await create_test_poll(db_session, test_user)
    test_option = await create_test_option(db_session, test_poll)

    # Try to create a vote with an error to trigger rollback
    try:
        vote = Vote(
            user_id=test_user.id,
            poll_id=test_poll.id,
            option_id=test_option.id,
        )
        db_session.add(vote)
        # Simulate an error
        raise ValueError("Simulated error")
        await db_session.commit()
    except ValueError:
        await db_session.rollback()

    # Verify no vote was committed
    result = await db_session.execute(select(Vote).where(Vote.user_id == test_user.id))
    assert result.scalar_one_or_none() is None, "Vote was not rolled back"

async def test_unique_constraints(db_session):
    """Test unique constraints."""
    # Create a user with a unique email and username
    user = await create_test_user(db_session)

    # Try to create another user with the same email
    duplicate_user = User(
        email=user.email,  # Duplicate email
        username=generate_unique_username(),
        hashed_password="test_password",
    )
    with pytest.raises(Exception):  # Should raise unique constraint violation
        db_session.add(duplicate_user)
        await db_session.commit()
    await db_session.rollback()

    # Try to create another user with the same username
    duplicate_user = User(
        email=generate_unique_email(),
        username=user.username,  # Duplicate username
        hashed_password="test_password",
    )
    with pytest.raises(Exception):  # Should raise unique constraint violation
        db_session.add(duplicate_user)
        await db_session.commit()
    await db_session.rollback()
