#!/usr/bin/env python3
"""
Load Seed Content from Files Script

Loads content from JSON files and creates proposal drafts in the database.
This is an optional utility for converting file-based content into actual proposals.

Usage:
    python scripts/load_seed_from_files.py [--principles|--actions|--all] [--dry-run]

Options:
    --principles    Load only principles (Level A)
    --actions       Load only actions (Level B)
    --all           Load both principles and actions (default)
    --dry-run       Show what would be created without actually creating
"""

import asyncio
import argparse
import sys
import os
from datetime import datetime
from typing import List, Dict, Any
from uuid import uuid4, UUID

# Add the backend directory to the path
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from backend.database import get_db
from backend.models.user import User
from backend.models.poll import Poll, DecisionType
from backend.models.option import Option
from backend.services.content_loader import content_loader
from backend.config import settings


async def create_proposal_from_content(
    session: AsyncSession,
    content_item: Dict[str, Any],
    decision_type: DecisionType,
    creator_id: UUID
) -> Poll:
    """Create a proposal from content item."""
    
    # Create the poll
    poll = Poll(
        title=content_item['title'],
        description=content_item['description'],
        created_by=creator_id,
        decision_type=decision_type,
        direction_choice=None if decision_type == DecisionType.LEVEL_B else "Support",
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    session.add(poll)
    await session.commit()
    await session.refresh(poll)
    
    # Create options based on decision type
    if decision_type == DecisionType.LEVEL_A:
        # Level A: Support/Oppose/Abstain
        options = [
            Option(poll_id=poll.id, text="Support", created_at=datetime.utcnow()),
            Option(poll_id=poll.id, text="Oppose", created_at=datetime.utcnow()),
            Option(poll_id=poll.id, text="Abstain", created_at=datetime.utcnow())
        ]
    else:
        # Level B: Approve/Reject/Abstain
        options = [
            Option(poll_id=poll.id, text="Approve", created_at=datetime.utcnow()),
            Option(poll_id=poll.id, text="Reject", created_at=datetime.utcnow()),
            Option(poll_id=poll.id, text="Abstain", created_at=datetime.utcnow())
        ]
    
    for option in options:
        session.add(option)
    
    await session.commit()
    return poll


async def load_principles(session: AsyncSession, creator_id: UUID, dry_run: bool = False) -> List[Poll]:
    """Load principles from file and create Level A proposals."""
    print("Loading principles...")
    
    principles = content_loader.load_principles()
    created_polls = []
    
    for principle in principles:
        if dry_run:
            print(f"  [DRY RUN] Would create Level A proposal: {principle.title}")
            continue
            
        try:
            poll = await create_proposal_from_content(
                session, 
                principle.dict(), 
                DecisionType.LEVEL_A, 
                creator_id
            )
            created_polls.append(poll)
            print(f"  Created Level A proposal: {poll.title}")
        except Exception as e:
            print(f"  Error creating proposal '{principle.title}': {e}")
    
    return created_polls


async def load_actions(session: AsyncSession, creator_id: UUID, dry_run: bool = False) -> List[Poll]:
    """Load actions from file and create Level B proposals."""
    print("Loading actions...")
    
    actions = content_loader.load_actions()
    created_polls = []
    
    for action in actions:
        if dry_run:
            print(f"  [DRY RUN] Would create Level B proposal: {action.title}")
            continue
            
        try:
            poll = await create_proposal_from_content(
                session, 
                action.dict(), 
                DecisionType.LEVEL_B, 
                creator_id
            )
            created_polls.append(poll)
            print(f"  Created Level B proposal: {poll.title}")
        except Exception as e:
            print(f"  Error creating proposal '{action.title}': {e}")
    
    return created_polls


async def main():
    parser = argparse.ArgumentParser(description='Load content from files into database as proposals')
    parser.add_argument('--principles', action='store_true', help='Load only principles (Level A)')
    parser.add_argument('--actions', action='store_true', help='Load only actions (Level B)')
    parser.add_argument('--all', action='store_true', help='Load both principles and actions (default)')
    parser.add_argument('--dry-run', action='store_true', help='Show what would be created without actually creating')
    
    args = parser.parse_args()
    
    # Determine what to load
    load_principles_flag = args.principles or args.all or (not args.actions)
    load_actions_flag = args.actions or args.all or (not args.principles)
    
    if args.dry_run:
        print("DRY RUN MODE - No proposals will be created")
    
    # Get database URL from environment
    db_url = os.getenv('DATABASE_URL', 'sqlite+aiosqlite:///test.db')
    
    # Create async engine and session maker
    engine = create_async_engine(db_url, echo=False)
    async_session_maker = sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )
    
    try:
        async with async_session_maker() as session:
            # Find or create a system user for content creation
            system_user = await session.execute(
                select(User).where(User.username == "system")
            )
            system_user = system_user.scalar_one_or_none()
            
            if not system_user:
                print("Creating system user for content creation...")
                from backend.core.security import get_password_hash
                system_user = User(
                    username="system",
                    email="system@thecommons.example",
                    hashed_password=get_password_hash("system-password-not-for-login"),
                    is_active=True,
                    created_at=datetime.utcnow()
                )
                session.add(system_user)
                await session.commit()
                await session.refresh(system_user)
            
            creator_id = system_user.id
            total_created = 0
            
            if load_principles_flag:
                principles_polls = await load_principles(session, creator_id, args.dry_run)
                total_created += len(principles_polls)
            
            if load_actions_flag:
                actions_polls = await load_actions(session, creator_id, args.dry_run)
                total_created += len(actions_polls)
            
            print(f"\nSummary:")
            if args.dry_run:
                print(f"  Would create {total_created} proposals")
            else:
                print(f"  Created {total_created} proposals")
            print(f"  Content source: {settings.CONTENT_DATA_DIR}")
            
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)
    finally:
        await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())
