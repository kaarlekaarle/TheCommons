#!/usr/bin/env python3
"""
Seed script to create dummy activity data for testing the activity feed.
"""

import asyncio
import sys
from datetime import datetime, timedelta
from pathlib import Path

# Add the backend directory to the Python path
backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from backend.database import async_session_maker
from backend.models.user import User
from backend.models.poll import Poll
from backend.models.option import Option
from backend.models.vote import Vote
from backend.models.delegation import Delegation
from backend.core.security import get_password_hash


async def create_seed_data():
    """Create seed data for activity feed testing."""
    async with async_session_maker() as db:
        print("🌱 Creating seed data for activity feed...")
        
        # Create users if they don't exist
        users_data = [
            {
                "username": "alex",
                "email": "alex@example.com",
                "password": "password123"
            },
            {
                "username": "jordan", 
                "email": "jordan@example.com",
                "password": "password123"
            },
            {
                "username": "maria",
                "email": "maria@example.com", 
                "password": "password123"
            }
        ]
        
        created_users = {}
        for user_data in users_data:
            # Check if user exists
            result = await db.execute(
                text("SELECT id FROM users WHERE username = :username"),
                {"username": user_data["username"]}
            )
            existing_user = result.scalar_one_or_none()
            
            if existing_user:
                print(f"✅ User {user_data['username']} already exists")
                created_users[user_data["username"]] = str(existing_user)
            else:
                # Create new user
                user = User(
                    username=user_data["username"],
                    email=user_data["email"],
                    hashed_password=get_password_hash(user_data["password"]),
                    is_active=True,
                    email_verified=True,
                    is_deleted=False
                )
                db.add(user)
                await db.commit()
                await db.refresh(user)
                created_users[user_data["username"]] = str(user.id)
                print(f"✅ Created user {user_data['username']}")
        
        # Create proposals with spaced timestamps
        proposals_data = [
            {
                "title": "Complete Streets Policy",
                "description": "Design and maintain streets to safely accommodate all users including pedestrians, cyclists, transit riders, and motorists of all ages and abilities.",
                "created_by": created_users["alex"],
                "hours_ago": 2  # 2 hours ago
            },
            {
                "title": "Install protected bike lanes on Washington Avenue from downtown to university district", 
                "description": "Add dedicated, protected bicycle lanes along Washington Avenue to improve cyclist safety and encourage active transportation between downtown and the university.",
                "created_by": created_users["jordan"],
                "hours_ago": 4  # 4 hours ago
            },
            {
                "title": "Launch 18-month curbside composting pilot in four residential neighborhoods",
                "description": "Begin organic waste collection service in Downtown, Westside, Riverside, and Eastside neighborhoods to reduce landfill waste and create compost for city parks.",
                "created_by": created_users["maria"], 
                "hours_ago": 6  # 6 hours ago
            },
            {
                "title": "Public Records Transparency Policy",
                "description": "Make all public records and datasets available online unless specifically exempted by law, with clear processes for requesting information.",
                "created_by": created_users["sam"],
                "hours_ago": 8  # 8 hours ago
            },
            {
                "title": "Extend public library hours to 9 PM on weekdays for six-month trial",
                "description": "Extend operating hours at the main library to better serve students, working families, and evening library users.",
                "created_by": created_users["taylor"],
                "hours_ago": 10  # 10 hours ago
            },
            {
                "title": "Green Building Standards for Municipal Construction",
                "description": "Require all new municipal buildings and major renovations to meet LEED Silver certification or equivalent energy efficiency standards.",
                "created_by": created_users["casey"],
                "hours_ago": 12  # 12 hours ago
            }
        ]
        
        created_proposals = {}
        for proposal_data in proposals_data:
            # Create proposal with custom timestamp
            created_at = datetime.utcnow() - timedelta(hours=proposal_data["hours_ago"])
            
            poll = Poll(
                title=proposal_data["title"],
                description=proposal_data["description"],
                created_by=proposal_data["created_by"],
                created_at=created_at,
                is_active=True,
                is_deleted=False
            )
            db.add(poll)
            await db.commit()
            await db.refresh(poll)
            created_proposals[proposal_data["title"]] = str(poll.id)
            print(f"✅ Created proposal: {proposal_data['title']}")
            
            # Create default options for each proposal
            options_data = ["Yes", "No", "Abstain"]
            for option_text in options_data:
                option = Option(
                    poll_id=poll.id,
                    text=option_text
                )
                db.add(option)
                await db.commit()
            print(f"   📝 Added options: {', '.join(options_data)}")
        
        # Create votes
        votes_data = [
            {
                "poll_title": "Complete Streets Policy",
                "voter": "jordan",
                "option_text": "Yes",
                "hours_ago": 1  # 1 hour ago
            },
            {
                "poll_title": "Municipal Climate Action Plan",
                "voter": "alex", 
                "option_text": "Yes",
                "hours_ago": 3  # 3 hours ago
            },
            {
                "poll_title": "Public Records Transparency Policy",
                "voter": "jordan",
                "option_text": "No", 
                "hours_ago": 5  # 5 hours ago
            }
        ]
        
        for vote_data in votes_data:
            # Get poll and option IDs
            poll_id = created_proposals[vote_data["poll_title"]]
            voter_id = created_users[vote_data["voter"]]
            
            # Get option ID
            result = await db.execute(
                text("SELECT id FROM options WHERE poll_id = :poll_id AND text = :text"),
                {"poll_id": poll_id, "text": vote_data["option_text"]}
            )
            option_id = result.scalar_one()
            
            # Create vote with custom timestamp
            created_at = datetime.utcnow() - timedelta(hours=vote_data["hours_ago"])
            
            vote = Vote(
                poll_id=poll_id,
                option_id=option_id,
                user_id=voter_id,
                created_at=created_at,
                is_deleted=False
            )
            db.add(vote)
            await db.commit()
            print(f"✅ {vote_data['voter']} voted {vote_data['option_text']} on {vote_data['poll_title']}")
        
        # Create delegation
        delegation_data = {
            "delegator": "maria",
            "delegate": "jordan", 
            "hours_ago": 7  # 7 hours ago
        }
        
        # Check if delegation already exists
        result = await db.execute(
            text("SELECT id FROM delegations WHERE delegator_id = :delegator_id AND delegate_id = :delegate_id"),
            {
                "delegator_id": created_users[delegation_data["delegator"]],
                "delegate_id": created_users[delegation_data["delegate"]]
            }
        )
        existing_delegation = result.scalar_one_or_none()
        
        if existing_delegation:
            print(f"✅ Delegation from {delegation_data['delegator']} to {delegation_data['delegate']} already exists")
        else:
            # Create delegation with custom timestamp
            created_at = datetime.utcnow() - timedelta(hours=delegation_data["hours_ago"])
            
            delegation = Delegation(
                delegator_id=created_users[delegation_data["delegator"]],
                delegate_id=created_users[delegation_data["delegate"]],
                created_at=created_at,
                updated_at=created_at,
                is_deleted=False
            )
            db.add(delegation)
            await db.commit()
            print(f"✅ {delegation_data['delegator']} delegated to {delegation_data['delegate']}")
        
        print("\n🎉 Seed data created successfully!")
        print("\n📊 Activity Feed should now show:")
        print("   • 3 proposals (from alex, jordan, maria)")
        print("   • 3 votes (from different users on different proposals)")
        print("   • 1 delegation (maria → jordan)")
        print("\n🕐 Items are timestamped within the last 7 hours for proper ordering")


if __name__ == "__main__":
    print("🚀 Starting activity feed seed script...")
    asyncio.run(create_seed_data())
    print("✨ Done!")
