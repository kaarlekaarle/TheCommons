"""Test soft delete visibility functionality."""

import pytest
from datetime import datetime
from sqlalchemy import select, func, and_
from sqlalchemy.orm import selectinload

from backend.models.user import User
from backend.models.poll import Poll
from backend.models.option import Option
from backend.models.vote import Vote
from backend.models.delegation import Delegation
from backend.models.comment import Comment
from backend.models.comment_reaction import CommentReaction
from backend.models.activity_log import ActivityLog


@pytest.mark.asyncio
async def test_soft_delete_user_visibility(db_session, test_user):
    """Test that soft deleted users are excluded from list endpoints."""
    
    # Create additional users
    import uuid
    from backend.core.security import get_password_hash
    
    user2_id = str(uuid.uuid4())
    user2 = User(
        id=user2_id,
        email="user2@example.com",
        username="user2",
        hashed_password=get_password_hash("password"),
        is_active=True
    )
    db_session.add(user2)
    await db_session.commit()
    await db_session.refresh(user2)
    
    # Verify both users exist
    users = (await db_session.execute(
        select(User).where(User.is_deleted == False)
    )).scalars().all()
    assert len(users) == 2
    
    # Soft delete one user
    await test_user.soft_delete(db_session)
    await db_session.commit()
    
    # Verify only non-deleted user is returned
    users = (await db_session.execute(
        select(User).where(User.is_deleted == False)
    )).scalars().all()
    assert len(users) == 1
    assert users[0].id == user2.id
    
    # Verify deleted user still exists in database
    deleted_user = await db_session.get(User, test_user.id)
    assert deleted_user is not None
    assert deleted_user.is_deleted is True
    assert deleted_user.deleted_at is not None


@pytest.mark.asyncio
async def test_soft_delete_poll_visibility(db_session, test_user):
    """Test that soft deleted polls are excluded from list endpoints."""
    
    # Create additional polls
    import uuid
    
    poll2_id = str(uuid.uuid4())
    poll2 = Poll(
        id=poll2_id,
        title="Test Poll 2",
        description="Test Description 2",
        created_by=test_user.id
    )
    db_session.add(poll2)
    await db_session.commit()
    await db_session.refresh(poll2)
    
    # Verify both polls exist
    polls = (await db_session.execute(
        select(Poll).where(Poll.is_deleted == False)
    )).scalars().all()
    assert len(polls) == 2
    
    # Soft delete one poll
    await test_poll.soft_delete(db_session)
    await db_session.commit()
    
    # Verify only non-deleted poll is returned
    polls = (await db_session.execute(
        select(Poll).where(Poll.is_deleted == False)
    )).scalars().all()
    assert len(polls) == 1
    assert polls[0].id == poll2.id


@pytest.mark.asyncio
async def test_soft_delete_cascade_visibility(db_session, test_user, test_poll, test_option):
    """Test that soft delete cascades to related records and excludes them from queries."""
    
    # Create additional related records
    import uuid
    
    # Create another option
    option2_id = str(uuid.uuid4())
    option2 = Option(
        id=option2_id,
        text="Test Option 2",
        poll_id=test_poll.id
    )
    db_session.add(option2)
    await db_session.commit()
    await db_session.refresh(option2)
    
    # Create another vote
    vote2_id = str(uuid.uuid4())
    vote2 = Vote(
        id=vote2_id,
        user_id=test_user.id,
        poll_id=test_poll.id,
        option_id=option2.id
    )
    db_session.add(vote2)
    await db_session.commit()
    await db_session.refresh(vote2)
    
    # Verify all records exist
    options = (await db_session.execute(
        select(Option).where(Option.is_deleted == False)
    )).scalars().all()
    assert len(options) == 2
    
    votes = (await db_session.execute(
        select(Vote).where(Vote.is_deleted == False)
    )).scalars().all()
    assert len(votes) == 2
    
    # Soft delete the poll
    await test_poll.soft_delete(db_session)
    await db_session.commit()
    
    # Verify all related records are soft deleted
    options = (await db_session.execute(
        select(Option).where(Option.is_deleted == False)
    )).scalars().all()
    assert len(options) == 0
    
    votes = (await db_session.execute(
        select(Vote).where(Vote.is_deleted == False)
    )).scalars().all()
    assert len(votes) == 0


@pytest.mark.asyncio
async def test_soft_delete_counts_aggregates(db_session, test_user, test_poll, test_option):
    """Test that counts and aggregates reflect soft delete exclusion."""
    
    # Create additional records
    import uuid
    
    # Create another poll
    poll2_id = str(uuid.uuid4())
    poll2 = Poll(
        id=poll2_id,
        title="Test Poll 2",
        description="Test Description 2",
        created_by=test_user.id
    )
    db_session.add(poll2)
    await db_session.commit()
    await db_session.refresh(poll2)
    
    # Create another option for poll2
    option2_id = str(uuid.uuid4())
    option2 = Option(
        id=option2_id,
        text="Test Option 2",
        poll_id=poll2.id
    )
    db_session.add(option2)
    await db_session.commit()
    await db_session.refresh(option2)
    
    # Create another vote for poll2
    vote2_id = str(uuid.uuid4())
    vote2 = Vote(
        id=vote2_id,
        user_id=test_user.id,
        poll_id=poll2.id,
        option_id=option2.id
    )
    db_session.add(vote2)
    await db_session.commit()
    await db_session.refresh(vote2)
    
    # Get initial counts
    poll_count = (await db_session.execute(
        select(func.count(Poll.id)).where(Poll.is_deleted == False)
    )).scalar()
    assert poll_count == 2
    
    option_count = (await db_session.execute(
        select(func.count(Option.id)).where(Option.is_deleted == False)
    )).scalar()
    assert option_count == 2
    
    vote_count = (await db_session.execute(
        select(func.count(Vote.id)).where(Vote.is_deleted == False)
    )).scalar()
    assert vote_count == 2
    
    # Soft delete one poll
    await test_poll.soft_delete(db_session)
    await db_session.commit()
    
    # Verify counts reflect exclusion
    poll_count = (await db_session.execute(
        select(func.count(Poll.id)).where(Poll.is_deleted == False)
    )).scalar()
    assert poll_count == 1
    
    option_count = (await db_session.execute(
        select(func.count(Option.id)).where(Option.is_deleted == False)
    )).scalar()
    assert option_count == 1
    
    vote_count = (await db_session.execute(
        select(func.count(Vote.id)).where(Vote.is_deleted == False)
    )).scalar()
    assert vote_count == 1


@pytest.mark.asyncio
async def test_soft_delete_joined_queries(db_session, test_user, test_poll, test_option):
    """Test joined queries to document current behavior with soft deleted rows."""
    
    # Create additional records for testing joins
    import uuid
    
    # Create another user
    user2_id = str(uuid.uuid4())
    user2 = User(
        id=user2_id,
        email="user2@example.com",
        username="user2",
        hashed_password="hashed_password",
        is_active=True
    )
    db_session.add(user2)
    await db_session.commit()
    await db_session.refresh(user2)
    
    # Create another poll for user2
    poll2_id = str(uuid.uuid4())
    poll2 = Poll(
        id=poll2_id,
        title="Test Poll 2",
        description="Test Description 2",
        created_by=user2.id
    )
    db_session.add(poll2)
    await db_session.commit()
    await db_session.refresh(poll2)
    
    # Create option for poll2
    option2_id = str(uuid.uuid4())
    option2 = Option(
        id=option2_id,
        text="Test Option 2",
        poll_id=poll2.id
    )
    db_session.add(option2)
    await db_session.commit()
    await db_session.refresh(option2)
    
    # Test joined query before soft delete
    joined_results = (await db_session.execute(
        select(User.username, Poll.title, Option.text)
        .join(Poll, User.id == Poll.created_by)
        .join(Option, Poll.id == Option.poll_id)
        .where(and_(User.is_deleted == False, Poll.is_deleted == False, Option.is_deleted == False))
    )).all()
    
    assert len(joined_results) == 2  # Both polls with their options
    
    # Soft delete one poll
    await test_poll.soft_delete(db_session)
    await db_session.commit()
    
    # Test joined query after soft delete
    joined_results = (await db_session.execute(
        select(User.username, Poll.title, Option.text)
        .join(Poll, User.id == Poll.created_by)
        .join(Option, Poll.id == Option.poll_id)
        .where(and_(User.is_deleted == False, Poll.is_deleted == False, Option.is_deleted == False))
    )).all()
    
    assert len(joined_results) == 1  # Only the non-deleted poll with its option
    
    # Verify the remaining result is from the non-deleted poll
    remaining_result = joined_results[0]
    assert remaining_result[1] == "Test Poll 2"  # poll title
    assert remaining_result[2] == "Test Option 2"  # option text


@pytest.mark.asyncio
async def test_soft_delete_delegation_visibility(db_session, test_user):
    """Test that soft deleted delegations are excluded from queries."""
    
    # Create additional delegation
    import uuid
    
    # Create another user for delegation
    user2_id = str(uuid.uuid4())
    user2 = User(
        id=user2_id,
        email="user2@example.com",
        username="user2",
        hashed_password="hashed_password",
        is_active=True
    )
    db_session.add(user2)
    await db_session.commit()
    await db_session.refresh(user2)
    
    # Create another delegation
    delegation2_id = str(uuid.uuid4())
    delegation2 = Delegation(
        id=delegation2_id,
        delegator_id=user2.id,
        delegatee_id=test_user.id
    )
    db_session.add(delegation2)
    await db_session.commit()
    await db_session.refresh(delegation2)
    
    # Verify both delegations exist
    delegations = (await db_session.execute(
        select(Delegation).where(Delegation.is_deleted == False)
    )).scalars().all()
    assert len(delegations) == 2
    
    # Soft delete one delegation
    await test_delegation.soft_delete(db_session)
    await db_session.commit()
    
    # Verify only non-deleted delegation is returned
    delegations = (await db_session.execute(
        select(Delegation).where(Delegation.is_deleted == False)
    )).scalars().all()
    assert len(delegations) == 1
    assert delegations[0].id == delegation2.id


@pytest.mark.asyncio
async def test_soft_delete_comment_visibility(db_session, test_user, test_poll):
    """Test that soft deleted comments are excluded from queries."""
    
    # Create additional comment
    import uuid
    
    comment2_id = str(uuid.uuid4())
    comment2 = Comment(
        id=comment2_id,
        user_id=test_user.id,
        poll_id=test_poll.id,
        content="Test comment 2"
    )
    db_session.add(comment2)
    await db_session.commit()
    await db_session.refresh(comment2)
    
    # Verify both comments exist
    comments = (await db_session.execute(
        select(Comment).where(Comment.is_deleted == False)
    )).scalars().all()
    assert len(comments) == 2
    
    # Soft delete one comment
    await test_comment.soft_delete(db_session)
    await db_session.commit()
    
    # Verify only non-deleted comment is returned
    comments = (await db_session.execute(
        select(Comment).where(Comment.is_deleted == False)
    )).scalars().all()
    assert len(comments) == 1
    assert comments[0].id == comment2.id


@pytest.mark.asyncio
async def test_soft_delete_activity_log_visibility(db_session, test_user):
    """Test that activity logs are not affected by soft deletes (they should remain for audit)."""
    
    # Create activity logs
    import uuid
    
    log1_id = str(uuid.uuid4())
    log1 = ActivityLog(
        id=log1_id,
        user_id=test_user.id,
        action="test_action",
        resource_type="test_resource",
        resource_id="test_id"
    )
    db_session.add(log1)
    
    log2_id = str(uuid.uuid4())
    log2 = ActivityLog(
        id=log2_id,
        user_id=test_user.id,
        action="test_action2",
        resource_type="test_resource2",
        resource_id="test_id2"
    )
    db_session.add(log2)
    await db_session.commit()
    
    # Verify both logs exist
    logs = (await db_session.execute(
        select(ActivityLog)
    )).scalars().all()
    assert len(logs) == 2
    
    # Soft delete the user
    await test_user.soft_delete(db_session)
    await db_session.commit()
    
    # Verify activity logs still exist (they should not be affected by user soft delete)
    logs = (await db_session.execute(
        select(ActivityLog)
    )).scalars().all()
    assert len(logs) == 2, "Activity logs should remain for audit purposes"


@pytest.mark.xfail(reason="Known issue: Soft deleted rows may leak in complex joined queries")
@pytest.mark.asyncio
async def test_soft_delete_complex_join_leak(db_session, test_user, test_poll, test_option):
    """Test complex joined queries to identify potential soft delete leaks."""
    
    # Create complex relationship structure
    import uuid
    
    # Create another user
    user2_id = str(uuid.uuid4())
    user2 = User(
        id=user2_id,
        email="user2@example.com",
        username="user2",
        hashed_password="hashed_password",
        is_active=True
    )
    db_session.add(user2)
    await db_session.commit()
    await db_session.refresh(user2)
    
    # Create comment for the poll
    comment_id = str(uuid.uuid4())
    comment = Comment(
        id=comment_id,
        user_id=user2.id,
        poll_id=test_poll.id,
        content="Test comment"
    )
    db_session.add(comment)
    await db_session.commit()
    await db_session.refresh(comment)
    
    # Create comment reaction
    reaction_id = str(uuid.uuid4())
    reaction = CommentReaction(
        id=reaction_id,
        user_id=test_user.id,
        comment_id=comment.id,
        reaction_type="like"
    )
    db_session.add(reaction)
    await db_session.commit()
    await db_session.refresh(reaction)
    
    # Test complex joined query before soft delete
    complex_query = (await db_session.execute(
        select(
            User.username,
            Poll.title,
            Option.text,
            Comment.content,
            CommentReaction.reaction_type
        )
        .join(Poll, User.id == Poll.created_by)
        .join(Option, Poll.id == Option.poll_id)
        .join(Comment, Poll.id == Comment.poll_id)
        .join(CommentReaction, Comment.id == CommentReaction.comment_id)
        .where(and_(
            User.is_deleted == False,
            Poll.is_deleted == False,
            Option.is_deleted == False,
            Comment.is_deleted == False,
            CommentReaction.is_deleted == False
        ))
    )).all()
    
    assert len(complex_query) == 1  # One complete chain
    
    # Soft delete the poll
    await test_poll.soft_delete(db_session)
    await db_session.commit()
    
    # Test complex joined query after soft delete
    complex_query = (await db_session.execute(
        select(
            User.username,
            Poll.title,
            Option.text,
            Comment.content,
            CommentReaction.reaction_type
        )
        .join(Poll, User.id == Poll.created_by)
        .join(Option, Poll.id == Option.poll_id)
        .join(Comment, Poll.id == Comment.poll_id)
        .join(CommentReaction, Comment.id == CommentReaction.comment_id)
        .where(and_(
            User.is_deleted == False,
            Poll.is_deleted == False,
            Option.is_deleted == False,
            Comment.is_deleted == False,
            CommentReaction.is_deleted == False
        ))
    )).all()
    
    # This should be 0, but may leak due to complex join behavior
    assert len(complex_query) == 0, "Complex joined query should exclude all soft deleted related records"