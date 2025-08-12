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
                "title": "Vision Zero Commitment",
                "description": "Commit to designing streets so that no one is killed or seriously injured in traffic.",
                "created_by": created_users["alex"],
                "hours_ago": 2  # 2 hours ago
            },
            {
                "title": "Install protected bike lanes on Oak Street from Central Park to City Hall", 
                "description": "Add dedicated, protected bicycle lanes along Oak Street to improve cyclist safety and encourage active transportation.",
                "created_by": created_users["jordan"],
                "hours_ago": 4  # 4 hours ago
            },
            {
                "title": "Launch 12-month curbside compost pickup pilot in three neighborhoods",
                "description": "Begin organic waste collection service in Downtown, Westside, and Riverside neighborhoods to reduce landfill waste.",
                "created_by": created_users["maria"], 
                "hours_ago": 6  # 6 hours ago
            },
            {
                "title": "Open Government Policy",
                "description": "Publish public records and datasets unless there's a clear legal reason not to.",
                "created_by": created_users["sam"],
                "hours_ago": 8  # 8 hours ago
            },
            {
                "title": "Extend Saturday library hours from 5 PM to 8 PM for six-month trial",
                "description": "Extend operating hours at the main library to better serve students and working families.",
                "created_by": created_users["taylor"],
                "hours_ago": 10  # 10 hours ago
            },
            {
                "title": "Green Building Standard",
                "description": "Require all new public buildings to meet the city's highest energy-efficiency code.",
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
                "poll_title": "Universal Basic Income",
                "voter": "jordan",
                "option_text": "Yes",
                "hours_ago": 1  # 1 hour ago
            },
            {
                "poll_title": "Climate Action Plan",
                "voter": "alex", 
                "option_text": "Yes",
                "hours_ago": 3  # 3 hours ago
            },
            {
                "poll_title": "Open Data Initiative",
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
