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
        "title": "Complete Streets Policy",
        "description": "Design and maintain streets to safely accommodate all users including pedestrians, cyclists, transit riders, and motorists of all ages and abilities.",
        "direction_choice": "Transportation Safety"
    },
    {
        "title": "Public Records Transparency Policy",
        "description": "Make all public records and datasets available online unless specifically exempted by law, with clear processes for requesting information.",
        "direction_choice": "Government Transparency"
    },
    {
        "title": "Green Building Standards for Municipal Construction",
        "description": "Require all new municipal buildings and major renovations to meet LEED Silver certification or equivalent energy efficiency standards.",
        "direction_choice": "Environmental Policy"
    },
    {
        "title": "Inclusive Housing Development Policy",
        "description": "Ensure 20% of all new residential development includes affordable housing units or equivalent contributions to the housing trust fund.",
        "direction_choice": "Housing & Development"
    },
    {
        "title": "Parks and Recreation Access Standards",
        "description": "Maintain a minimum of 10 acres of parkland per 1,000 residents and ensure all neighborhoods have access to recreational facilities within a 10-minute walk.",
        "direction_choice": "Parks & Recreation"
    },
    {
        "title": "Municipal Climate Action Plan",
        "description": "Reduce city government greenhouse gas emissions by 50% by 2030 and achieve carbon neutrality by 2040 through energy efficiency and renewable energy.",
        "direction_choice": "Climate & Sustainability"
    },
    {
        "title": "Digital Equity and Broadband Access Policy",
        "description": "Ensure all residents have access to affordable high-speed internet and digital literacy training through partnerships with service providers and community organizations.",
        "direction_choice": "Technology & Innovation"
    },
    {
        "title": "Local Food System Development Policy",
        "description": "Support local food production and distribution by providing incentives for urban agriculture, farmers markets, and food processing facilities.",
        "direction_choice": "Food Security"
    },
    {
        "title": "Transit-Oriented Development Framework",
        "description": "Prioritize mixed-use development within 1/2 mile of transit stations to reduce car dependency and increase transit ridership.",
        "direction_choice": "Public Transit"
    },
    {
        "title": "Zero Waste and Circular Economy Policy",
        "description": "Achieve 90% waste diversion from landfills by 2030 through comprehensive recycling, composting, and waste reduction programs.",
        "direction_choice": "Waste Management"
    }
]

# Level B Proposals (Actions - specific, immediate steps)
LEVEL_B_PROPOSALS = [
    {
        "title": "Install protected bike lanes on Washington Avenue from downtown to university district",
        "description": "Add dedicated, protected bicycle lanes along Washington Avenue to improve cyclist safety and encourage active transportation between downtown and the university.",
        "options": ["Approve", "Modify plan", "Reject"]
    },
    {
        "title": "Launch 18-month curbside composting pilot in four residential neighborhoods",
        "description": "Begin organic waste collection service in Downtown, Westside, Riverside, and Eastside neighborhoods to reduce landfill waste and create compost for city parks.",
        "options": ["Approve", "Reduce scope", "Reject"]
    },
    {
        "title": "Extend public library hours to 9 PM on weekdays for six-month trial",
        "description": "Extend operating hours at the main library to better serve students, working families, and evening library users.",
        "options": ["Approve", "Modify hours", "Reject"]
    },
    {
        "title": "Plant 750 street trees along major transit corridors and in underserved neighborhoods",
        "description": "Add urban trees along bus routes and in neighborhoods with low tree canopy to improve air quality, provide shade, and enhance walkability.",
        "options": ["Approve", "Reduce number", "Reject"]
    },
    {
        "title": "Install 25 public water refill stations in parks, schools, and community centers",
        "description": "Add drinking water stations to reduce plastic bottle waste, improve public health, and encourage hydration during outdoor activities.",
        "options": ["Approve", "Reduce locations", "Reject"]
    },
    {
        "title": "Retrofit lighting in all municipal buildings with energy-efficient LED systems",
        "description": "Replace existing lighting systems in 15 municipal buildings to reduce energy consumption by 40% and lower operating costs.",
        "options": ["Approve", "Phase implementation", "Reject"]
    },
    {
        "title": "Add wheelchair-accessible seating and improved pathways in Central Park",
        "description": "Install accessible benches, improve pathway surfaces, and add shade structures to ensure park access for residents of all abilities.",
        "options": ["Approve", "Modify scope", "Reject"]
    },
    {
        "title": "Create monthly 'Open Streets' program on Main Street during summer months",
        "description": "Close Main Street to vehicle traffic on the first Sunday of each month from June through September for community events and recreation.",
        "options": ["Approve", "Reduce frequency", "Reject"]
    },
    {
        "title": "Launch local food voucher program for 300 low-income households",
        "description": "Provide $75 monthly vouchers redeemable at farmers markets and local food co-ops for qualifying households to improve food access.",
        "options": ["Approve", "Reduce amount", "Reject"]
    },
    {
        "title": "Replace diesel buses on Route 8 with electric buses within 24 months",
        "description": "Purchase 12 electric buses to replace aging diesel vehicles on the downtown-to-airport route, reducing emissions and noise pollution.",
        "options": ["Approve", "Extend timeline", "Reject"]
    },
    {
        "title": "Start youth apprenticeship program in city maintenance and parks departments",
        "description": "Create 20 paid apprenticeship positions for youth aged 16-24 in parks maintenance, street repair, and facilities management.",
        "options": ["Approve", "Reduce positions", "Reject"]
    },
    {
        "title": "Create protected pedestrian crossing at 3rd and Market intersection",
        "description": "Install signalized crosswalk with pedestrian refuge island and countdown timers at the busy 3rd and Market intersection.",
        "options": ["Approve", "Modify design", "Reject"]
    },
    {
        "title": "Run public art mural program in underutilized downtown spaces",
        "description": "Commission 15 murals on blank walls and underpasses to improve visual appeal, support local artists, and reduce graffiti.",
        "options": ["Approve", "Reduce number", "Reject"]
    },
    {
        "title": "Upgrade stormwater drainage system in flood-prone areas",
        "description": "Replace and expand drainage infrastructure in four neighborhoods that experience regular flooding during heavy rain events.",
        "options": ["Approve", "Prioritize areas", "Reject"]
    },
    {
        "title": "Pilot mobile mental health crisis response unit operating five days per week",
        "description": "Deploy a mobile crisis intervention team with mental health professionals to provide immediate support in high-need areas.",
        "options": ["Approve", "Reduce days", "Reject"]
    },
    {
        "title": "Offer free Wi-Fi in all public libraries, recreation centers, and community spaces",
        "description": "Install and maintain wireless internet access in 12 public facilities to improve digital access and support remote work and learning.",
        "options": ["Approve", "Limit locations", "Reject"]
    },
    {
        "title": "Expand community policing foot patrols to three additional neighborhoods",
        "description": "Add walking patrols in Eastside, Southside, and Northside neighborhoods to improve community-police relations and crime prevention.",
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
