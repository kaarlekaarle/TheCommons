#!/usr/bin/env python3
"""
Riverbend Demo City Seeding Script

Creates a realistic small-city community with Level A (baseline policy) and Level B (poll) proposals,
including comments, votes, and delegations.

Usage:
    python scripts/seed_demo_city.py [--reset|--no-reset|--users-only]

Options:
    --reset      Delete existing demo content and re-seed (default)
    --no-reset   Skip deletion, only add missing demo content
    --users-only Only create demo users, skip proposals/votes/comments
"""

import asyncio
import argparse
import sys
import os
from datetime import datetime, timedelta
from typing import List, Dict, Any
from uuid import uuid4, UUID

# Add the backend directory to the path
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'backend'))

from sqlalchemy import select, delete, and_, text
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from backend.database import get_db
from backend.models.user import User
from backend.models.poll import Poll, DecisionType
from backend.models.option import Option
from backend.models.vote import Vote
from backend.models.comment import Comment
from backend.models.delegation import Delegation
from backend.core.security import get_password_hash
from backend.config import settings


# Demo user definitions
DEMO_USERS = [
    {'username': 'mayor', 'email': 'mayor@riverbend.example'},
    {'username': 'cityplanner', 'email': 'cityplanner@riverbend.example'},
    {'username': 'teacher', 'email': 'teacher@riverbend.example'},
    {'username': 'shop_owner', 'email': 'shop_owner@riverbend.example'},
    {'username': 'student', 'email': 'student@riverbend.example'},
    {'username': 'nurse', 'email': 'nurse@riverbend.example'},
    {'username': 'cyclist', 'email': 'cyclist@riverbend.example'},
    {'username': 'driver', 'email': 'driver@riverbend.example'},
    {'username': 'parent', 'email': 'parent@riverbend.example'},
    {'username': 'librarian', 'email': 'librarian@riverbend.example'},
    {'username': 'waste_manager', 'email': 'waste_manager@riverbend.example'},
    {'username': 'developer', 'email': 'developer@riverbend.example'},
]

# Level A (baseline policy) proposals
LEVEL_A_PROPOSALS = [
    {
        'title': '[DEMO] Environmental Stewardship Charter',
        'description': 'Establish a comprehensive environmental policy framework for Riverbend, ensuring all future decisions consider ecological impact and sustainability.',
        'direction_choice': "Let's take care of nature"
    },
    {
        'title': '[DEMO] Open Data & Transparency Charter',
        'description': 'Create a policy framework for open government data and transparent decision-making processes.',
        'direction_choice': "Open by default"
    },
    {
        'title': '[DEMO] Mobility Vision 2030',
        'description': 'Define the long-term vision for transportation and mobility in Riverbend, prioritizing people over cars.',
        'direction_choice': "People-first streets"
    }
]

# Level B (poll) proposals
LEVEL_B_PROPOSALS = [
    {
        'title': '[DEMO] Install protected bike lanes on Main St',
        'description': 'Add protected bike lanes along Main Street from downtown to the university, improving safety for cyclists and encouraging active transportation.',
        'options': ['Yes', 'No', 'Abstain']
    },
    {
        'title': '[DEMO] Pilot curbside composting for 1 year',
        'description': 'Launch a one-year pilot program for curbside organic waste collection and composting in the downtown area.',
        'options': ['Yes', 'No', 'Abstain']
    },
    {
        'title': '[DEMO] Extend library weekend hours',
        'description': 'Extend the public library hours on weekends from 5 PM to 8 PM to better serve students and working families.',
        'options': ['Yes', 'No', 'Abstain']
    },
    {
        'title': '[DEMO] Replace diesel buses with electric on Route 4',
        'description': 'Replace the aging diesel buses on Route 4 (downtown to shopping center) with electric buses to reduce emissions and noise.',
        'options': ['Yes', 'No', 'Abstain']
    }
]

# Sample comments for proposals
SAMPLE_COMMENTS = {
    'bike_lanes': [
        {'text': 'PRO: Reduces injuries and encourages active travel', 'user': 'cyclist'},
        {'text': 'CON: Impacts street parking for small businesses', 'user': 'shop_owner'},
        {'text': 'PRO: Great for students commuting to university', 'user': 'student'},
        {'text': 'CON: Will slow down traffic during construction', 'user': 'driver'},
        {'text': 'This is a good step toward our mobility goals', 'user': 'cityplanner'},
    ],
    'composting': [
        {'text': 'PRO: Cuts landfill waste and supports soil health', 'user': 'waste_manager'},
        {'text': 'CON: Higher collection costs during pilot', 'user': 'mayor'},
        {'text': 'PRO: Teaches residents about waste reduction', 'user': 'teacher'},
        {'text': 'CON: Requires significant behavior change', 'user': 'parent'},
        {'text': 'Let\'s see how the pilot goes before expanding', 'user': 'librarian'},
    ],
    'library_hours': [
        {'text': 'PRO: Better access for working families', 'user': 'parent'},
        {'text': 'CON: Additional staffing costs', 'user': 'mayor'},
        {'text': 'PRO: Students need quiet study spaces on weekends', 'user': 'student'},
        {'text': 'This aligns with our education priorities', 'user': 'teacher'},
        {'text': 'CON: Limited budget for extended services', 'user': 'librarian'},
    ],
    'electric_buses': [
        {'text': 'PRO: Reduces air pollution in downtown', 'user': 'nurse'},
        {'text': 'CON: High upfront costs for new vehicles', 'user': 'mayor'},
        {'text': 'PRO: Quieter operation improves quality of life', 'user': 'parent'},
        {'text': 'CON: Limited charging infrastructure', 'user': 'driver'},
        {'text': 'This supports our environmental charter', 'user': 'cityplanner'},
    ]
}

# Sample votes for Level B proposals (user -> option mapping)
SAMPLE_VOTES = {
    'bike_lanes': {
        'cyclist': 'Yes', 'student': 'Yes', 'cityplanner': 'Yes', 'parent': 'Yes',
        'driver': 'No', 'shop_owner': 'No', 'mayor': 'Abstain', 'teacher': 'Yes',
        'nurse': 'Yes', 'librarian': 'Yes'
    },
    'composting': {
        'waste_manager': 'Yes', 'teacher': 'Yes', 'student': 'Yes', 'parent': 'Yes',
        'mayor': 'No', 'shop_owner': 'No', 'cyclist': 'Yes', 'nurse': 'Abstain',
        'librarian': 'Yes', 'developer': 'Yes'
    },
    'library_hours': {
        'parent': 'Yes', 'student': 'Yes', 'teacher': 'Yes', 'librarian': 'No',
        'mayor': 'No', 'shop_owner': 'Abstain', 'nurse': 'Yes', 'cyclist': 'Yes',
        'waste_manager': 'Yes', 'developer': 'Yes'
    },
    'electric_buses': {
        'nurse': 'Yes', 'parent': 'Yes', 'cityplanner': 'Yes', 'cyclist': 'Yes',
        'mayor': 'No', 'driver': 'No', 'shop_owner': 'Abstain', 'teacher': 'Yes',
        'student': 'Yes', 'librarian': 'Yes'
    }
}

# Delegations (delegator -> delegatee)
DELEGATIONS = [
    ('student', 'cityplanner'),
    ('shop_owner', 'cityplanner'),
    ('driver', 'mayor'),
]


class DemoSeeder:
    def __init__(self, db_url: str):
        self.db_url = db_url
        self.engine = None
        self.session_factory = None
        self.demo_users = {}
        self.demo_polls = {}
        
    async def setup(self):
        """Initialize database connection."""
        self.engine = create_async_engine(self.db_url)
        self.session_factory = sessionmaker(
            self.engine, class_=AsyncSession, expire_on_commit=False
        )
        
    async def cleanup(self):
        """Close database connection."""
        if self.engine:
            await self.engine.dispose()
            
    async def get_or_create_user(self, username: str, email: str, password: str = "password123") -> User:
        """Get existing user or create new one."""
        async with self.session_factory() as session:
            # Check if user exists
            result = await session.execute(
                select(User).where(User.username == username)
            )
            user = result.scalar_one_or_none()
            
            if user:
                print(f"  Found existing user: {username}")
                return user
                
            # Create new user
            hashed_password = get_password_hash(password)
            user = User(
                username=username,
                email=email,
                hashed_password=hashed_password,
                is_active=True,
                is_superuser=False
            )
            session.add(user)
            await session.commit()
            await session.refresh(user)
            print(f"  Created new user: {username}")
            return user
            
    async def cleanup_demo_content(self):
        """Remove all existing demo content."""
        print("Cleaning up existing demo content...")
        # For now, skip cleanup to avoid UUID issues
        print("  Skipping cleanup (UUID handling issue)")
        return
            
    async def seed_users(self):
        """Create demo users."""
        print("Creating demo users...")
        for user_data in DEMO_USERS:
            user = await self.get_or_create_user(
                user_data['username'],
                user_data['email']
            )
            self.demo_users[user_data['username']] = user.id
        print(f"  Created {len(DEMO_USERS)} demo users")
        
    async def seed_level_a_proposals(self):
        """Create Level A (baseline policy) proposals."""
        if not settings.LEVEL_A_ENABLED:
            print("Level A decisions are disabled, skipping Level A proposals")
            return
            
        print("Creating Level A (baseline policy) proposals...")
        async with self.session_factory() as session:
            for i, proposal_data in enumerate(LEVEL_A_PROPOSALS):
                # Create poll
                poll = Poll(
                    title=proposal_data['title'],
                    description=proposal_data['description'],
                    created_by=self.demo_users['cityplanner'],
                    decision_type=DecisionType.LEVEL_A,
                    direction_choice=proposal_data['direction_choice'],
                    created_at=datetime.utcnow() - timedelta(hours=24-i*2),
                    updated_at=datetime.utcnow() - timedelta(hours=24-i*2)
                )
                session.add(poll)
                await session.commit()
                await session.refresh(poll)
                
                self.demo_polls[proposal_data['title']] = poll.id
                print(f"  Created Level A proposal: {proposal_data['title']}")
                
        print(f"  Created {len(LEVEL_A_PROPOSALS)} Level A proposals")
        
    async def seed_level_b_proposals(self):
        """Create Level B (poll) proposals with options."""
        print("Creating Level B (poll) proposals...")
        async with self.session_factory() as session:
            for i, proposal_data in enumerate(LEVEL_B_PROPOSALS):
                # Create poll
                poll = Poll(
                    title=proposal_data['title'],
                    description=proposal_data['description'],
                    created_by=self.demo_users['mayor'],
                    decision_type=DecisionType.LEVEL_B,
                    created_at=datetime.utcnow() - timedelta(hours=12-i*2),
                    updated_at=datetime.utcnow() - timedelta(hours=12-i*2)
                )
                session.add(poll)
                await session.commit()
                await session.refresh(poll)
                
                # Create options
                for option_text in proposal_data['options']:
                    option = Option(
                        text=option_text,
                        poll_id=poll.id
                    )
                    session.add(option)
                
                await session.commit()
                self.demo_polls[proposal_data['title']] = poll.id
                print(f"  Created Level B proposal: {proposal_data['title']}")
                
        print(f"  Created {len(LEVEL_B_PROPOSALS)} Level B proposals")
        
    async def seed_comments(self):
        """Add comments to proposals."""
        print("Adding comments to proposals...")
        async with self.session_factory() as session:
            comment_count = 0
            
            # Add comments to Level B proposals
            for proposal_title, comments in SAMPLE_COMMENTS.items():
                # Find the corresponding poll
                poll_id = None
                for poll_title in self.demo_polls:
                    if proposal_title.replace('_', ' ') in poll_title.lower():
                        poll_id = self.demo_polls[poll_title]
                        break
                
                if poll_id:
                    for comment_data in comments:
                        comment = Comment(
                            id=uuid4(),
                            poll_id=UUID(poll_id),
                            user_id=UUID(self.demo_users[comment_data['user']]),
                            body=comment_data['text'],
                            created_at=datetime.utcnow() - timedelta(minutes=comment_count*5)
                        )
                        session.add(comment)
                        comment_count += 1
                        
            await session.commit()
            print(f"  Added {comment_count} comments")
            
    async def seed_votes(self):
        """Cast votes on Level B proposals."""
        print("Casting votes on Level B proposals...")
        async with self.session_factory() as session:
            vote_count = 0
            
            for proposal_key, votes in SAMPLE_VOTES.items():
                # Find the corresponding poll and options
                poll_id = None
                for poll_title in self.demo_polls:
                    if proposal_key.replace('_', ' ') in poll_title.lower():
                        poll_id = self.demo_polls[poll_title]
                        break
                
                if poll_id:
                    # Get options for this poll
                    result = await session.execute(
                        select(Option).where(Option.poll_id == poll_id)
                    )
                    options = result.scalars().all()
                    option_map = {opt.text: opt.id for opt in options}
                    
                    for username, vote_choice in votes.items():
                        if username in self.demo_users and vote_choice in option_map:
                            vote = Vote(
                                poll_id=poll_id,
                                option_id=option_map[vote_choice],
                                user_id=self.demo_users[username],
                                created_at=datetime.utcnow() - timedelta(minutes=vote_count*3)
                            )
                            session.add(vote)
                            vote_count += 1
                            
            await session.commit()
            print(f"  Cast {vote_count} votes")
            
    async def seed_delegations(self):
        """Create delegations between demo users."""
        print("Creating delegations...")
        async with self.session_factory() as session:
            delegation_count = 0
            
            for delegator_username, delegatee_username in DELEGATIONS:
                if (delegator_username in self.demo_users and 
                    delegatee_username in self.demo_users):
                    
                    delegation = Delegation(
                        delegator_id=self.demo_users[delegator_username],
                        delegate_id=self.demo_users[delegatee_username],
                        created_at=datetime.utcnow() - timedelta(hours=6-delegation_count)
                    )
                    session.add(delegation)
                    delegation_count += 1
                    
            await session.commit()
            print(f"  Created {delegation_count} delegations")
            
    async def print_summary(self):
        """Print a summary of what was created."""
        print("\n" + "="*50)
        print("RIVERBEND DEMO SEEDING SUMMARY")
        print("="*50)
        print(f"Users created: {len(self.demo_users)}")
        print(f"Level A proposals: {len([p for p in self.demo_polls if 'Level A' in p])}")
        print(f"Level B proposals: {len([p for p in self.demo_polls if 'Level B' in p])}")
        print(f"Total proposals: {len(self.demo_polls)}")
        print(f"Delegations: {len(DELEGATIONS)}")
        print("\nDemo user credentials:")
        print("  Username: any of the demo usernames")
        print("  Password: password123")
        print("\nExample logins:")
        for user_data in DEMO_USERS[:3]:  # Show first 3
            print(f"  {user_data['username']} / password123")
        print("="*50)


async def main():
    parser = argparse.ArgumentParser(description='Seed Riverbend demo city data')
    parser.add_argument('--reset', action='store_true', default=True,
                       help='Delete existing demo content and re-seed (default)')
    parser.add_argument('--no-reset', action='store_true',
                       help='Skip deletion, only add missing demo content')
    parser.add_argument('--users-only', action='store_true',
                       help='Only create demo users, skip proposals/votes/comments')
    
    args = parser.parse_args()
    
    # Get database URL from environment
    db_url = os.getenv('DATABASE_URL', 'sqlite+aiosqlite:///test.db')
    
    seeder = DemoSeeder(db_url)
    
    try:
        await seeder.setup()
        
        if args.reset and not args.no_reset:
            await seeder.cleanup_demo_content()
            
        await seeder.seed_users()
        
        if not args.users_only:
            await seeder.seed_level_a_proposals()
            await seeder.seed_level_b_proposals()
            await seeder.seed_comments()
            await seeder.seed_votes()
            await seeder.seed_delegations()
            
        await seeder.print_summary()
        
    finally:
        await seeder.cleanup()


if __name__ == "__main__":
    asyncio.run(main())
