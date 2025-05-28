from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from backend.models.user import User
from backend.models.vote import Vote


async def create_vote(db: AsyncSession, vote_data: dict, user: User) -> Vote:
    """Create a new vote."""
    # Remove user_id from vote_data if it exists to avoid duplicate argument
    vote_data.pop("user_id", None)
    vote = Vote(**vote_data, user_id=user.id)
    db.add(vote)
    await db.commit()
    await db.refresh(vote)
    return vote


async def get_vote(db: AsyncSession, vote_id: int) -> Vote:
    """Get a vote by ID."""
    result = await db.execute(select(Vote).where(Vote.id == vote_id))
    vote = result.scalar_one_or_none()
    if not vote:
        raise ValueError(f"Vote with id {vote_id} not found")
    return vote


async def update_vote(
    db: AsyncSession, vote_id: int, vote_data: dict, user: User
) -> Vote:
    """Update a vote."""
    vote = await get_vote(db, vote_id)
    if vote.user_id != user.id:
        raise ValueError("Not authorized to update this vote")

    for key, value in vote_data.items():
        setattr(vote, key, value)

    try:
        await db.commit()
        await db.refresh(vote)
    except IntegrityError as e:
        await db.rollback()
        if "foreign key constraint" in str(e).lower():
            raise ValueError("Referenced option or poll does not exist")
        raise
    return vote


async def delete_vote(db: AsyncSession, vote_id: int, user: User) -> Vote:
    """Delete a vote."""
    vote = await get_vote(db, vote_id)
    if vote.user_id != user.id:
        raise ValueError("Not authorized to delete this vote")

    await db.delete(vote)
    await db.commit()
    return vote


async def cast_vote(db: AsyncSession, vote_id: int, user: User) -> Vote:
    """Cast a vote."""
    vote = await get_vote(db, vote_id)
    if vote.user_id != user.id:
        raise ValueError("Not authorized to cast this vote")

    vote.is_cast = True
    await db.commit()
    await db.refresh(vote)
    return vote
