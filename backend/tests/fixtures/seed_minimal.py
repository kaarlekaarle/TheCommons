"""
Minimal seeding helpers for tests.

Provides deterministic, lightweight data seeding for test scenarios.
No network calls, no Redis dependencies.
"""

import asyncio
from datetime import datetime, timedelta
from typing import Optional
from uuid import uuid4

from sqlalchemy.ext.asyncio import AsyncSession

from backend.models.activity_log import ActivityLog, ActionType
from backend.models.poll import Poll, PollStatus, PollVisibility, DecisionType
from backend.models.user import User


async def seed_minimal_activity(db_session: AsyncSession) -> dict:
    """
    Seed minimal data required for activity feed tests.
    
    Creates: one user, one poll, one activity log entry.
    
    Args:
        db_session: Database session
        
    Returns:
        dict: Created entities for test assertions
    """
    # Create test user
    user = User(
        id=uuid4(),
        email="activity-test@example.com",
        username="activityuser",
        hashed_password="hashed_password_for_testing",
        is_active=True,
    )
    db_session.add(user)
    await db_session.flush()
    
    # Create test poll
    poll = Poll(
        id=uuid4(),
        title="Activity Test Poll",
        description="Test poll for activity feed",
        created_by=user.id,
        status=PollStatus.ACTIVE,
        visibility=PollVisibility.PUBLIC,
        start_date=datetime.utcnow(),
        end_date=datetime.utcnow() + timedelta(days=7),
        allow_delegation=True,
        require_authentication=False,
        max_votes_per_user=1,
        decision_type=DecisionType.LEVEL_B,
        direction_choice="up_down",
    )
    db_session.add(poll)
    await db_session.flush()
    
    # Create activity log entry
    activity = ActivityLog(
        id=uuid4(),
        user_id=user.id,
        action_type=ActionType.POLL_CREATED,
        reference_id=poll.id,
        meta={"poll_title": poll.title},
    )
    db_session.add(activity)
    await db_session.flush()
    
    await db_session.commit()
    
    return {
        "user": user,
        "poll": poll,
        "activity": activity,
    }


async def seed_minimal_user(db_session: AsyncSession, 
                          email: str = "test@example.com",
                          username: str = "testuser") -> User:
    """
    Create a minimal test user.
    
    Args:
        db_session: Database session
        email: User email
        username: Username
        
    Returns:
        User: Created user
    """
    user = User(
        id=uuid4(),
        email=email,
        username=username,
        hashed_password="hashed_password_for_testing",
        is_active=True,
    )
    db_session.add(user)
    await db_session.flush()
    await db_session.commit()
    return user


async def seed_minimal_poll(db_session: AsyncSession, 
                          created_by: User,
                          title: str = "Test Poll") -> Poll:
    """
    Create a minimal test poll.
    
    Args:
        db_session: Database session
        created_by: User who created the poll
        title: Poll title
        
    Returns:
        Poll: Created poll
    """
    poll = Poll(
        id=uuid4(),
        title=title,
        description="Test poll description",
        created_by=created_by.id,
        status=PollStatus.ACTIVE,
        visibility=PollVisibility.PUBLIC,
        start_date=datetime.utcnow(),
        end_date=datetime.utcnow() + timedelta(days=7),
        allow_delegation=True,
        require_authentication=False,
        max_votes_per_user=1,
        decision_type=DecisionType.LEVEL_B,
        direction_choice="up_down",
    )
    db_session.add(poll)
    await db_session.flush()
    await db_session.commit()
    return poll
