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
        "title": "Vision Zero Commitment",
        "description": "Commit to designing streets so that no one is killed or seriously injured in traffic.",
        "direction_choice": "Transportation Safety"
    },
    {
        "title": "Open Government Policy",
        "description": "Publish public records and datasets unless there's a clear legal reason not to.",
        "direction_choice": "Government Transparency"
    },
    {
        "title": "Green Building Standard",
        "description": "Require all new public buildings to meet the city's highest energy-efficiency code.",
        "direction_choice": "Environmental Policy"
    },
    {
        "title": "Affordable Housing Priority",
        "description": "Prioritize affordable housing in land-use and zoning decisions.",
        "direction_choice": "Housing & Development"
    },
    {
        "title": "Public Space Access",
        "description": "Ensure all residents live within a 10-minute walk of a safe, accessible public space.",
        "direction_choice": "Parks & Recreation"
    },
    {
        "title": "Climate Action Framework",
        "description": "Cut greenhouse gas emissions 50% by 2035, across all city operations.",
        "direction_choice": "Climate & Sustainability"
    },
    {
        "title": "Transparent Budgeting",
        "description": "Publish budgets in plain language with year-to-year comparisons.",
        "direction_choice": "Financial Management"
    },
    {
        "title": "Digital Inclusion",
        "description": "Guarantee all households affordable access to high-speed internet.",
        "direction_choice": "Technology & Innovation"
    },
    {
        "title": "Cultural Access for All",
        "description": "Support year-round, low-cost access to arts and culture for all residents.",
        "direction_choice": "Arts & Culture"
    },
    {
        "title": "Local Food Commitment",
        "description": "Increase the share of food consumed in the city that is grown or produced locally.",
        "direction_choice": "Food Security"
    },
    {
        "title": "Mobility for All",
        "description": "Design transport systems that serve all ages and abilities.",
        "direction_choice": "Public Transit"
    },
    {
        "title": "Public Health First",
        "description": "Ensure every resident can reach primary health care within 30 minutes by public transport.",
        "direction_choice": "Public Health"
    },
    {
        "title": "Water Stewardship",
        "description": "Manage water resources sustainably, ensuring safe drinking water for all.",
        "direction_choice": "Water Management"
    },
    {
        "title": "Zero Waste Commitment",
        "description": "Commit to diverting all recyclable and compostable materials from landfills.",
        "direction_choice": "Waste Management"
    },
    {
        "title": "Participatory Governance",
        "description": "Include residents in decisions through open forums, surveys, and digital platforms.",
        "direction_choice": "Civic Engagement"
    },
    {
        "title": "Fair Work Charter",
        "description": "Prioritize fair wages, safe working conditions, and worker voice in city contracts.",
        "direction_choice": "Labor & Employment"
    },
    {
        "title": "Noise Management Policy",
        "description": "Reduce harmful noise levels in residential areas.",
        "direction_choice": "Public Safety"
    },
    {
        "title": "Tree Canopy Preservation",
        "description": "Maintain and expand the urban tree canopy across all neighborhoods.",
        "direction_choice": "Urban Forestry"
    },
    {
        "title": "Historical Preservation",
        "description": "Protect and maintain historically significant buildings and sites.",
        "direction_choice": "Heritage Conservation"
    },
    {
        "title": "Community Safety Framework",
        "description": "Build community safety through prevention, intervention, and support services.",
        "direction_choice": "Public Safety"
    }
]

# Level B Proposals (Actions - specific, immediate steps)
LEVEL_B_PROPOSALS = [
    {
        "title": "Install protected bike lanes on Oak Street from Central Park to City Hall",
        "description": "Add dedicated, protected bicycle lanes along Oak Street to improve cyclist safety and encourage active transportation.",
        "options": ["Approve", "Modify plan", "Reject"]
    },
    {
        "title": "Launch 12-month curbside compost pickup pilot in three neighborhoods",
        "description": "Begin organic waste collection service in Downtown, Westside, and Riverside neighborhoods to reduce landfill waste.",
        "options": ["Approve", "Reduce scope", "Reject"]
    },
    {
        "title": "Extend Saturday library hours from 5 PM to 8 PM for six-month trial",
        "description": "Extend operating hours at the main library to better serve students and working families.",
        "options": ["Approve", "Modify hours", "Reject"]
    },
    {
        "title": "Plant 500 street trees along major bus routes",
        "description": "Add urban trees along transit corridors to improve air quality and provide shade for transit users.",
        "options": ["Approve", "Reduce number", "Reject"]
    },
    {
        "title": "Install 20 public water refill stations in parks and downtown areas",
        "description": "Add drinking water stations to reduce plastic bottle waste and improve public health.",
        "options": ["Approve", "Reduce locations", "Reject"]
    },
    {
        "title": "Retrofit lighting in all public schools with energy-efficient LEDs",
        "description": "Replace existing lighting systems in 12 public school buildings to reduce energy consumption and costs.",
        "options": ["Approve", "Phase implementation", "Reject"]
    },
    {
        "title": "Add wheelchair-accessible seating and pathways in Riverside Park",
        "description": "Install accessible benches and improve pathway surfaces to ensure park access for all residents.",
        "options": ["Approve", "Modify scope", "Reject"]
    },
    {
        "title": "Create weekly 'car-free Sunday' on Main Avenue during summer months",
        "description": "Close Main Avenue to vehicle traffic every Sunday from June through August for community events and recreation.",
        "options": ["Approve", "Reduce frequency", "Reject"]
    },
    {
        "title": "Launch local food voucher program for low-income households",
        "description": "Provide $50 monthly vouchers redeemable at farmers' markets for 200 qualifying households.",
        "options": ["Approve", "Reduce amount", "Reject"]
    },
    {
        "title": "Replace diesel buses on Route 6 with electric buses within 18 months",
        "description": "Purchase 8 electric buses to replace aging diesel vehicles on the downtown-to-airport route.",
        "options": ["Approve", "Extend timeline", "Reject"]
    },
    {
        "title": "Start youth apprenticeship program in city maintenance departments",
        "description": "Create 15 paid apprenticeship positions for youth aged 16-24 in parks, streets, and facilities maintenance.",
        "options": ["Approve", "Reduce positions", "Reject"]
    },
    {
        "title": "Create protected pedestrian crossing at 5th and Market",
        "description": "Install signalized crosswalk with pedestrian refuge island at the busy 5th and Market intersection.",
        "options": ["Approve", "Modify design", "Reject"]
    },
    {
        "title": "Run public art mural program in underutilized spaces downtown",
        "description": "Commission 10 murals on blank walls and underpasses to improve visual appeal and support local artists.",
        "options": ["Approve", "Reduce number", "Reject"]
    },
    {
        "title": "Upgrade stormwater drains in flood-prone neighborhoods",
        "description": "Replace and expand drainage infrastructure in three neighborhoods that experience regular flooding.",
        "options": ["Approve", "Prioritize areas", "Reject"]
    },
    {
        "title": "Pilot mobile mental health support unit operating three days a week",
        "description": "Deploy a mobile crisis intervention team to provide immediate mental health support in high-need areas.",
        "options": ["Approve", "Reduce days", "Reject"]
    },
    {
        "title": "Offer free Wi-Fi in all public libraries and recreation centers",
        "description": "Install and maintain wireless internet access in 8 public facilities to improve digital access.",
        "options": ["Approve", "Limit locations", "Reject"]
    },
    {
        "title": "Expand community policing foot patrols to two additional neighborhoods",
        "description": "Add walking patrols in Eastside and Southside neighborhoods to improve community-police relations.",
        "options": ["Approve", "Add one area", "Reject"]
    },
    {
        "title": "Begin construction of skate park in Westside Recreation Area",
        "description": "Build a 15,000 square foot skate park with beginner and advanced areas for youth recreation.",
        "options": ["Approve", "Reduce size", "Reject"]
    },
    {
        "title": "Install traffic-calming speed tables on Oak Drive near elementary school",
        "description": "Add three speed tables on Oak Drive to reduce vehicle speeds and improve pedestrian safety near the school.",
        "options": ["Approve", "Reduce number", "Reject"]
    },
    {
        "title": "Provide grants for storefront energy-efficiency upgrades to 20 small businesses",
        "description": "Offer $5,000 grants to small businesses for lighting, HVAC, and insulation improvements.",
        "options": ["Approve", "Reduce amount", "Reject"]
    },
    {
        "title": "Introduce on-demand evening bus service for shift workers in industrial park",
        "description": "Launch flexible bus service from 6 PM to 2 AM to serve workers at the industrial park and surrounding areas.",
        "options": ["Approve", "Reduce hours", "Reject"]
    },
    {
        "title": "Convert vacant lot at 14th and Pine into temporary community garden for two years",
        "description": "Transform the 0.5-acre vacant lot into a community garden with 30 plots and shared composting area.",
        "options": ["Approve", "Reduce size", "Reject"]
    },
    {
        "title": "Offer free weekend transit for youth under 18 for one-year pilot",
        "description": "Provide free bus and train rides on Saturdays and Sundays for all youth to encourage independent mobility.",
        "options": ["Approve", "Limit days", "Reject"]
    },
    {
        "title": "Create citywide tool library where residents can borrow equipment for home projects",
        "description": "Establish a lending library with 200 tools and equipment items available for 7-day borrowing periods.",
        "options": ["Approve", "Reduce inventory", "Reject"]
    },
    {
        "title": "Add shaded seating areas to three senior housing complexes",
        "description": "Install covered benches and tables with shade structures at senior housing facilities to improve outdoor access.",
        "options": ["Approve", "Reduce locations", "Reject"]
    },
    {
        "title": "Implement bilingual signage in all city-owned buildings",
        "description": "Add Spanish-language signs alongside English in all municipal buildings to improve accessibility.",
        "options": ["Approve", "Phase implementation", "Reject"]
    },
    {
        "title": "Start bike-share program with 100 bikes at 10 docking stations",
        "description": "Launch a public bicycle sharing system with stations throughout downtown and adjacent neighborhoods.",
        "options": ["Approve", "Reduce scale", "Reject"]
    },
    {
        "title": "Build public charging station hub for electric vehicles in central parking lot",
        "description": "Install 12 electric vehicle charging stations in the main downtown parking facility to support EV adoption.",
        "options": ["Approve", "Reduce stations", "Reject"]
    },
    {
        "title": "Restore historic fountain in Civic Plaza",
        "description": "Repair and restore the 1920s fountain in Civic Plaza, including plumbing, electrical, and decorative elements.",
        "options": ["Approve", "Modify scope", "Reject"]
    },
    {
        "title": "Add two new trash and recycling bins per block in downtown core",
        "description": "Install 40 new waste receptacles with separate recycling compartments throughout the downtown area.",
        "options": ["Approve", "Reduce number", "Reject"]
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
