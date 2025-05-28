import pytest
from datetime import datetime
from uuid import UUID

from backend.models.user import User
from backend.models.poll import Poll
from backend.models.option import Option
from backend.models.vote import Vote
from backend.models.delegation import Delegation
from backend.models.activity_log import ActivityLog
from backend.models.delegation_stats import DelegationStats

@pytest.mark.asyncio
async def test_soft_delete_user(db_session, test_user):
    """Test soft delete functionality for User model."""
    # Verify user exists
    user = await db_session.get(User, test_user.id)
    assert user is not None
    assert user.is_deleted is False
    assert user.deleted_at is None

    # Soft delete the user
    test_user.soft_delete()
    await db_session.commit()

    # Verify user is soft deleted
    user = await db_session.get(User, test_user.id)
    assert user.is_deleted is True
    assert user.deleted_at is not None

    # Verify user is not returned in normal queries
    users = (await db_session.execute(
        User.__table__.select().where(User.is_deleted == False)
    )).fetchall()
    assert len(users) == 0

    # Restore the user
    test_user.restore()
    await db_session.commit()

    # Verify user is restored
    user = await db_session.get(User, test_user.id)
    assert user.is_deleted is False
    assert user.deleted_at is None

@pytest.mark.asyncio
async def test_soft_delete_poll(db_session, test_user):
    """Test soft delete functionality for Poll model."""
    # Create a test poll
    poll = Poll(
        title="Test Poll",
        description="Test Description",
        created_by=test_user.id
    )
    db_session.add(poll)
    await db_session.commit()
    await db_session.refresh(poll)

    # Verify poll exists
    poll_record = await db_session.get(Poll, poll.id)
    assert poll_record is not None
    assert poll_record.is_deleted is False
    assert poll_record.deleted_at is None

    # Soft delete the poll
    poll.soft_delete()
    await db_session.commit()

    # Verify poll is soft deleted
    poll_record = await db_session.get(Poll, poll.id)
    assert poll_record.is_deleted is True
    assert poll_record.deleted_at is not None

    # Verify poll is not returned in normal queries
    polls = (await db_session.execute(
        Poll.__table__.select().where(Poll.is_deleted == False)
    )).fetchall()
    assert len(polls) == 0

@pytest.mark.asyncio
async def test_soft_delete_cascade(db_session, test_user):
    """Test that soft delete cascades to related records."""
    # Create a test poll
    poll = Poll(
        title="Test Poll",
        description="Test Description",
        created_by=test_user.id
    )
    db_session.add(poll)
    await db_session.commit()
    await db_session.refresh(poll)

    # Create a test option
    option = Option(
        text="Test Option",
        poll_id=poll.id
    )
    db_session.add(option)
    await db_session.commit()
    await db_session.refresh(option)

    # Create a test vote
    vote = Vote(
        user_id=test_user.id,
        poll_id=poll.id,
        option_id=option.id
    )
    db_session.add(vote)
    await db_session.commit()
    await db_session.refresh(vote)

    # Soft delete the poll
    poll.soft_delete()
    await db_session.commit()

    # Verify all related records are soft deleted
    option_record = await db_session.get(Option, option.id)
    assert option_record.is_deleted is True
    assert option_record.deleted_at is not None

    vote_record = await db_session.get(Vote, vote.id)
    assert vote_record.is_deleted is True
    assert vote_record.deleted_at is not None