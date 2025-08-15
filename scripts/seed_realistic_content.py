#!/usr/bin/env python3
"""
Realistic Content Seeding Script

Creates realistic content for The Commons application:
- Multiple users with different roles
- Various proposals with different topics
- Votes and delegations
- Comments on proposals
"""

import asyncio
import sys
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import List
from uuid import UUID
import random

# Add the project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from backend.core.security import get_password_hash
from backend.models.delegation import Delegation
from backend.models.option import Option
from backend.models.poll import Poll
from backend.models.user import User
from backend.models.vote import Vote
from backend.models.comment import Comment

# Database configuration
import os
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite+aiosqlite:///test.db")

# Create async engine and session maker
engine = create_async_engine(DATABASE_URL, echo=False)
async_session_maker = sessionmaker(
    engine, class_=AsyncSession, expire_on_commit=False
)

# Sample data
USERS = [
    {"username": "alex", "email": "alex@example.com", "password": "password123"},
    {"username": "jordan", "email": "jordan@example.com", "password": "password123"},
    {"username": "maria", "email": "maria@example.com", "password": "password123"},
    {"username": "sam", "email": "sam@example.com", "password": "password123"},
    {"username": "taylor", "email": "taylor@example.com", "password": "password123"},
    {"username": "casey", "email": "casey@example.com", "password": "password123"},
    {"username": "riley", "email": "riley@example.com", "password": "password123"},
    {"username": "quinn", "email": "quinn@example.com", "password": "password123"},
]

# Level A Proposals (Principles - long-term direction)
LEVEL_A_PROPOSALS = [
    {
        "title": "Level A Principle (Placeholder)",
        "description": "This is a placeholder example for Level A. It demonstrates how a single evolving document could be revised and countered.",
        "direction_choice": "Placeholder"
    }
]

# Level B Proposals (Actions - specific, immediate steps)
LEVEL_B_PROPOSALS = [
    {
        "title": "Level B Principle (Placeholder)",
        "description": "This is a placeholder example for Level B. It demonstrates how community-level or technical sub-questions could be explored.",
        "options": ["Approve", "Modify", "Reject"]
    }
]

# Combine Level A and Level B proposals for the main PROPOSALS array
PROPOSALS = LEVEL_A_PROPOSALS + LEVEL_B_PROPOSALS

COMMENTS = [
    "This is exactly what our community needs! I've been hoping for something like this.",
    "I have some concerns about the implementation timeline. Can we discuss this further?",
    "Great idea! I'd be happy to volunteer my time to help make this happen.",
    "I think we should consider the long-term maintenance costs before proceeding.",
    "This proposal aligns perfectly with our community values. I fully support it.",
    "Have we considered the environmental impact of this proposal?",
    "I love this idea! It will bring our community closer together.",
    "We need to make sure this is accessible to everyone in our community.",
    "This is a step in the right direction. Let's make it happen!",
    "I have some suggestions for improving this proposal. Can we discuss them?"
]

async def create_user(session: AsyncSession, user_data: dict) -> User:
    """Create a user."""
    try:
        user = User(
            username=user_data["username"],
            email=user_data["email"],
            hashed_password=get_password_hash(user_data["password"]),
            is_active=True,
            is_superuser=False
        )
        session.add(user)
        await session.commit()
        await session.refresh(user)
        print(f"   ✅ Created user: {user.username}")
        return user
    except Exception as e:
        print(f"   ❌ Failed to create user {user_data['username']}: {e}")
        await session.rollback()
        raise

async def create_poll_with_options(session: AsyncSession, creator: User, proposal_data: dict) -> tuple[Poll, List[Option]]:
    """Create a poll with options."""
    # Create poll
    poll = Poll(
        title=proposal_data["title"],
        description=proposal_data["description"],
        created_by=creator.id,
        status="active",
        start_date=datetime.utcnow() - timedelta(days=random.randint(1, 30)),
        end_date=datetime.utcnow() + timedelta(days=random.randint(30, 90)),
        allow_delegation=True,
        require_authentication=True,
        max_votes_per_user=1
    )
    session.add(poll)
    await session.commit()
    await session.refresh(poll)
    
    # Create options
    option_objects = []
    for option_text in proposal_data["options"]:
        option = Option(
            poll_id=poll.id,
            text=option_text
        )
        session.add(option)
        await session.commit()
        await session.refresh(option)
        option_objects.append(option)
    
    return poll, option_objects

async def create_vote(session: AsyncSession, user: User, poll: Poll, option: Option) -> Vote:
    """Create a vote for a user."""
    vote = Vote(
        user_id=user.id,
        poll_id=poll.id,
        option_id=option.id,
        weight=1,
        created_at=datetime.utcnow() - timedelta(days=random.randint(0, 10))
    )
    session.add(vote)
    await session.commit()
    await session.refresh(vote)
    return vote

async def create_delegation(session: AsyncSession, delegator: User, delegate: User) -> Delegation:
    """Create a delegation from delegator to delegate."""
    delegation = Delegation(
        delegator_id=delegator.id,
        delegate_id=delegate.id
    )
    session.add(delegation)
    await session.commit()
    await session.refresh(delegation)
    return delegation

async def create_comment(session: AsyncSession, user: User, poll: Poll, comment_text: str) -> Comment:
    """Create a comment on a poll."""
    comment = Comment(
        user_id=user.id,
        poll_id=poll.id,
        body=comment_text,
        created_at=datetime.utcnow() - timedelta(days=random.randint(0, 5))
    )
    session.add(comment)
    await session.commit()
    await session.refresh(comment)
    return comment

async def seed_realistic_content():
    """Seed realistic content for the application."""
    print("🌱 Starting realistic content seeding...")
    
    async with async_session_maker() as session:
        # Create users
        print("👥 Creating users...")
        users = []
        for user_data in USERS:
            user = await create_user(session, user_data)
            users.append(user)
        
        print(f"✅ Created {len(users)} users")
        
        # Create proposals
        print("📋 Creating proposals...")
        polls = []
        for i, proposal_data in enumerate(PROPOSALS):
            creator = users[i % len(users)]  # Distribute creation among users
            poll, options = await create_poll_with_options(session, creator, proposal_data)
            polls.append((poll, options))
            print(f"   ✅ Created proposal: {poll.title}")
        
        print(f"✅ Created {len(polls)} proposals")
        
        # Create votes
        print("🗳️ Creating votes...")
        total_votes = 0
        for poll, options in polls:
            # Get a random subset of users to vote
            voters = random.sample(users, random.randint(3, len(users)))
            for voter in voters:
                # Randomly choose an option
                option = random.choice(options)
                await create_vote(session, voter, poll, option)
                total_votes += 1
                print(f"   ✅ {voter.username} voted for '{option.text}' on '{poll.title}'")
        
        print(f"✅ Created {total_votes} votes")
        
        # Create delegations
        print("🔗 Creating delegations...")
        total_delegations = 0
        # Create some delegation chains
        for i in range(0, len(users), 2):
            if i + 1 < len(users):
                delegator = users[i]
                delegate = users[i + 1]
                await create_delegation(session, delegator, delegate)
                total_delegations += 1
                print(f"   ✅ {delegator.username} delegates to {delegate.username}")
        
        # Add some additional random delegations
        for _ in range(3):
            delegator = random.choice(users)
            delegate = random.choice(users)
            if delegator != delegate:
                await create_delegation(session, delegator, delegate)
                total_delegations += 1
                print(f"   ✅ {delegator.username} delegates to {delegate.username}")
        
        print(f"✅ Created {total_delegations} delegations")
        
        # Create comments
        print("💬 Creating comments...")
        total_comments = 0
        for poll, _ in polls:
            # Add 2-4 comments per poll
            num_comments = random.randint(2, 4)
            commenters = random.sample(users, min(num_comments, len(users)))
            for commenter in commenters:
                comment_text = random.choice(COMMENTS)
                await create_comment(session, commenter, poll, comment_text)
                total_comments += 1
                print(f"   ✅ {commenter.username} commented on '{poll.title}'")
        
        print(f"✅ Created {total_comments} comments")
        
        # Verify the data
        print("🔍 Verifying data...")
        
        # Count votes
        votes_result = await session.execute(select(Vote))
        all_votes = votes_result.scalars().all()
        print(f"   Total votes: {len(all_votes)}")
        
        # Count delegations
        delegations_result = await session.execute(select(Delegation))
        all_delegations = delegations_result.scalars().all()
        print(f"   Total delegations: {len(all_delegations)}")
        
        # Count comments
        comments_result = await session.execute(select(Comment))
        all_comments = comments_result.scalars().all()
        print(f"   Total comments: {len(all_comments)}")
        
        print(f"   Total users: {len(users)}")
        print(f"   Total polls: {len(polls)}")
        
        return users, polls, len(all_votes), len(all_delegations), len(all_comments)

async def main():
    """Main function to run the seeding."""
    print("🎯 Realistic Content Seeding")
    print("=" * 50)
    
    try:
        # Seed the content
        users, polls, total_votes, total_delegations, total_comments = await seed_realistic_content()
        
        print(f"\n📊 Seeding Summary:")
        print(f"   Users: {len(users)}")
        print(f"   Proposals: {len(polls)}")
        print(f"   Votes: {total_votes}")
        print(f"   Delegations: {total_delegations}")
        print(f"   Comments: {total_comments}")
        
        print(f"\n🔑 Login Credentials:")
        print(f"   You can log in with any of these accounts:")
        for user in users[:5]:  # Show first 5 users
            print(f"   - Username: {user.username}, Password: password123")
        
        print(f"\n🏁 Seeding completed successfully!")
        
    except Exception as e:
        print(f"❌ Error during seeding: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        # Close the engine
        await engine.dispose()
        print("\n🔚 Database connection closed")

if __name__ == "__main__":
    asyncio.run(main())
