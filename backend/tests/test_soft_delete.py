from datetime import datetime

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.models.activity_log import ActivityLog
from backend.models.delegation import Delegation
from backend.models.option import Option
from backend.models.poll import Poll
from backend.models.user import User
from backend.models.vote import Vote


@pytest.mark.asyncio
async def test_basic_soft_delete(db_session: AsyncSession, test_user):
    test_user = await test_user
    """Test basic soft delete functionality on a User model."""
    # Verify user exists and is not deleted
    assert not test_user.is_deleted
    assert test_user.deleted_at is None

    # Soft delete the user
    await test_user.soft_delete(db_session)
    await db_session.commit()
    await db_session.refresh(test_user)

    # Verify soft delete fields
    assert test_user.is_deleted
    assert isinstance(test_user.deleted_at, datetime)

    # Verify user is not returned in normal queries
    result = await db_session.execute(
        select(User).where(User.id == test_user.id, User.is_deleted == False)
    )
    user = result.scalar_one_or_none()
    assert user is None

    # Verify user can be found with explicit include_deleted
    result = await db_session.execute(
        select(User).where(User.id == test_user.id, User.is_deleted.is_(True))
    )
    user = result.scalar_one_or_none()
    assert user is not None
    assert user.id == test_user.id

    # Verify user is not deleted
    assert user.is_deleted is False
    assert user.deleted_at is None

    # Verify user is deleted
    assert user.is_deleted is True
    assert user.deleted_at is not None


@pytest.mark.asyncio
async def test_cascade_soft_delete(db_session: AsyncSession, test_user):
    test_user = await test_user
    """Test cascade soft delete from Poll to Options and Votes."""
    # Create a poll
    poll = Poll(
        title="Test Poll", description="Test Description", created_by=test_user.id
    )
    db_session.add(poll)
    await db_session.commit()
    await db_session.refresh(poll)

    # Create options for the poll
    options = []
    for i in range(2):
        option = Option(text=f"Option {i}", poll_id=poll.id)
        db_session.add(option)
        options.append(option)
    await db_session.commit()

    # Create votes for each option
    votes = []
    for option in options:
        vote = Vote(user_id=test_user.id, poll_id=poll.id, option_id=option.id)
        db_session.add(vote)
        votes.append(vote)
    await db_session.commit()

    # Soft delete the poll
    await poll.soft_delete(db_session)

    # Refresh all objects
    await db_session.refresh(poll)
    for option in options:
        await db_session.refresh(option)
    for vote in votes:
        await db_session.refresh(vote)

    # Verify cascade soft delete
    assert poll.is_deleted
    assert poll.deleted_at is not None
    for option in options:
        assert option.is_deleted
        assert option.deleted_at is not None
    for vote in votes:
        assert vote.is_deleted
        assert vote.deleted_at is not None


@pytest.mark.asyncio
async def test_restore_soft_deleted(db_session: AsyncSession, test_user):
    test_user = await test_user
    """Test restoring a soft-deleted record."""
    # Create and soft delete a poll
    poll = Poll(
        title="Test Poll", description="Test Description", created_by=test_user.id
    )
    db_session.add(poll)
    await db_session.commit()
    await db_session.refresh(poll)

    # Soft delete the poll
    await poll.soft_delete(db_session)
    await db_session.commit()
    await db_session.refresh(poll)

    # Verify it's soft deleted
    assert poll.is_deleted
    assert poll.deleted_at is not None

    # Restore the poll
    poll.restore()
    await db_session.commit()
    await db_session.refresh(poll)

    # Verify it's restored
    assert not poll.is_deleted
    assert poll.deleted_at is None

    # Verify it's returned in normal queries
    result = await db_session.execute(
        select(Poll).where(Poll.id == poll.id, Poll.is_deleted == False)
    )
    restored_poll = result.scalar_one_or_none()
    assert restored_poll is not None
    assert restored_poll.id == poll.id


@pytest.mark.asyncio
async def test_get_active_query(db_session: AsyncSession, test_user):
    test_user = await test_user
    """Test the get_active_query class method."""
    # Create multiple polls
    polls = []
    for i in range(3):
        poll = Poll(
            title=f"Test Poll {i}",
            description=f"Test Description {i}",
            created_by=test_user.id,
        )
        db_session.add(poll)
        polls.append(poll)
    await db_session.commit()

    # Soft delete one poll
    await polls[0].soft_delete(db_session)
    await db_session.commit()

    # Debug print
    print("DEBUG: Poll.get_active_query() type:", type(Poll.get_active_query()))
    print("DEBUG: Poll.get_active_query() value:", Poll.get_active_query())

    # Query active polls using get_active_query() in where clause
    result = await db_session.execute(select(Poll).where(Poll.get_active_query()))
    print("DEBUG: result type:", type(result))
    print("DEBUG: result.scalars() type:", type(result.scalars()))
    # Now call .all()
    active_polls = result.scalars().all()
    print("DEBUG: active_polls:", active_polls)
    print("DEBUG: active_polls type:", type(active_polls))

    # Verify only non-deleted polls are returned
    assert len(active_polls) == 2
    assert all(not poll.is_deleted for poll in active_polls)
    assert all(poll.id in [p.id for p in polls[1:]] for poll in active_polls)


@pytest.mark.asyncio
async def test_soft_delete_with_relationships(db_session: AsyncSession, test_user):
    test_user = await test_user
    """Test soft delete behavior with complex relationships."""
    # Create a poll with options and votes
    poll = Poll(
        title="Test Poll", description="Test Description", created_by=test_user.id
    )
    db_session.add(poll)
    await db_session.commit()
    await db_session.refresh(poll)

    # Create options
    option = Option(text="Test Option", poll_id=poll.id)
    db_session.add(option)
    await db_session.commit()
    await db_session.refresh(option)

    # Create a vote
    vote = Vote(user_id=test_user.id, poll_id=poll.id, option_id=option.id)
    db_session.add(vote)
    await db_session.commit()

    # Create a delegation
    delegation = Delegation(
        delegator_id=test_user.id,
        delegatee_id=test_user.id,  # Self-delegation for test
        poll_id=poll.id,
        start_date=datetime.utcnow(),
    )
    db_session.add(delegation)
    await db_session.commit()

    # Create an activity log
    activity = ActivityLog(
        user_id=test_user.id, action_type="POLL_CREATED", reference_id=poll.id
    )
    db_session.add(activity)
    await db_session.commit()

    # Soft delete the poll
    await poll.soft_delete(db_session)
    await db_session.commit()

    # Refresh all objects
    await db_session.refresh(poll)
    await db_session.refresh(option)
    await db_session.refresh(vote)
    await db_session.refresh(delegation)
    await db_session.refresh(activity)

    # Verify cascade soft delete
    assert poll.is_deleted
    assert option.is_deleted
    assert vote.is_deleted
    assert delegation.is_deleted
    assert activity.is_deleted

    # Verify timestamps
    assert poll.deleted_at is not None
    assert option.deleted_at is not None
    assert vote.deleted_at is not None
    assert delegation.deleted_at is not None
    assert activity.deleted_at is not None

    # Verify relationships are maintained
    assert option.poll_id == poll.id
    assert vote.poll_id == poll.id
    assert vote.option_id == option.id
    assert delegation.poll_id == poll.id
    assert activity.reference_id == poll.id
