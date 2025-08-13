from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from backend.models.user import User
from backend.models.poll import Poll, DecisionType, PollStatus, PollVisibility
from backend.models.activity_log import ActivityLog, ActionType
from backend.core.security import get_password_hash


async def seed_minimal_user(db: AsyncSession, email="u@example.com", username="u1") -> User:
    u = User(email=email, username=username, hashed_password=get_password_hash("password"), is_active=True)
    db.add(u)
    await db.flush()
    return u


async def seed_minimal_poll(db: AsyncSession, owner_id: str) -> Poll:
    p = Poll(
        title="Test Poll",
        description="seeded",
        decision_type=DecisionType.LEVEL_B,
        status=PollStatus.ACTIVE,
        visibility=PollVisibility.PUBLIC,
        created_by=owner_id,
        start_date=datetime.utcnow() - timedelta(days=1),
        end_date=datetime.utcnow() + timedelta(days=1),
        allow_delegation=True,
        require_authentication=False,
        max_votes_per_user=1,
        direction_choice="up_down",
    )
    db.add(p)
    await db.flush()
    return p


async def seed_minimal_activity(db: AsyncSession, user_id: str, poll_id: str) -> ActivityLog:
    a = ActivityLog(
        user_id=user_id,
        action_type=ActionType.POLL_CREATED,
        reference_id=poll_id,
        meta={"source": "seed"},
    )
    db.add(a)
    await db.flush()
    return a
