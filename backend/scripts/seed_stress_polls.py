#!/usr/bin/env python3
"""
Stress test poll seeding script.
Creates ~300 polls with random labels for performance testing.
"""

import asyncio
import os
import sys
import random
from datetime import datetime, timedelta
from pathlib import Path
from typing import List

# Add the backend directory to the Python path
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

from backend.database import get_db
from backend.models.poll import Poll
from backend.models.option import Option
from backend.models.poll_label import poll_labels
from backend.models.label import Label
from backend.models.user import User
from backend.config import settings

# Sample poll data for stress testing
SAMPLE_POLLS = [
    # Level A Principles (1 total)
    {
        "title": "Level A Principle (Placeholder)",
        "description": "This is a placeholder example for Level A. It demonstrates how a single evolving document could be revised and countered.",
        "decision_type": "level_a",
        "direction_choice": "Placeholder"
    },
    
    # Level B Actions (1 total) - Sample templates
    {
        "title": "Level B Principle (Placeholder)",
        "description": "This is a placeholder example for Level B. It demonstrates how community-level or technical sub-questions could be explored.",
        "decision_type": "level_b"
    }
]

# Label combinations for different types of proposals
LABEL_COMBINATIONS = {
    "environment": ["environment", "climate-action", "green-infrastructure"],
    "mobility": ["mobility", "transportation", "public-safety"],
    "housing": ["housing", "economic-development", "equity-inclusion"],
    "education": ["education", "childcare", "libraries"],
    "health": ["health", "social-services", "accessibility"],
    "governance": ["governance", "community-engagement", "budget"],
    "arts": ["arts-culture", "parks-recreation", "public-spaces"],
    "technology": ["technology", "energy", "waste-management"]
}

async def get_or_create_test_user(db) -> User:
    """Get or create a test user for seeding polls."""
    # Try to find an existing user
    result = await db.execute("SELECT * FROM users LIMIT 1")
    user = result.scalar_one_or_none()
    
    if not user:
        # Create a test user if none exists
        user = User(
            username="stress-test-user",
            email="stress-test@example.com",
            hashed_password="hashed_password_placeholder",
            is_active=True,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        db.add(user)
        await db.commit()
        await db.refresh(user)
    
    return user

async def get_available_labels(db) -> List[Label]:
    """Get all available labels from the database."""
    result = await db.execute("SELECT * FROM labels WHERE is_active = true")
    return result.scalars().all()

async def create_poll_with_labels(db, poll_data: dict, user: User, labels: List[Label], created_at: datetime):
    """Create a poll with associated labels."""
    # Create the poll
    poll = Poll(
        title=poll_data["title"],
        description=poll_data["description"],
        created_by=user.id,
        created_at=created_at,
        updated_at=created_at,
        is_active=True,
        decision_type=poll_data["decision_type"],
        direction_choice=poll_data.get("direction_choice"),
        end_date=created_at + timedelta(days=30)
    )
    db.add(poll)
    await db.flush()  # Get the poll ID
    
    # Create voting options
    if poll_data["decision_type"] == "level_a":
        options = [
            Option(poll_id=poll.id, text="Support", created_at=created_at, updated_at=created_at),
            Option(poll_id=poll.id, text="Oppose", created_at=created_at, updated_at=created_at),
            Option(poll_id=poll.id, text="Abstain", created_at=created_at, updated_at=created_at)
        ]
    else:
        options = [
            Option(poll_id=poll.id, text="Yes", created_at=created_at, updated_at=created_at),
            Option(poll_id=poll.id, text="No", created_at=created_at, updated_at=created_at),
            Option(poll_id=poll.id, text="Abstain", created_at=created_at, updated_at=created_at)
        ]
    
    db.add_all(options)
    
    # Associate labels
    if labels:
        label_associations = [
            {"poll_id": str(poll.id), "label_id": str(label.id)}
            for label in labels
        ]
        await db.execute(
            "INSERT INTO poll_labels (poll_id, label_id) VALUES (:poll_id, :label_id)",
            label_associations
        )
    
    return poll

async def seed_stress_polls():
    """Seed stress test polls with labels."""
    if not settings.LABELS_ENABLED:
        print("❌ Labels feature is not enabled. Set LABELS_ENABLED=true")
        return
    
    print("🌱 Seeding stress test polls...")
    
    async for db in get_db():
        try:
            # Get or create test user
            user = await get_or_create_test_user(db)
            print(f"👤 Using user: {user.username}")
            
            # Get available labels
            available_labels = await get_available_labels(db)
            if not available_labels:
                print("❌ No labels found. Run seed_stress_labels.py first.")
                return
            
            print(f"🏷️ Found {len(available_labels)} available labels")
            
            # Create label lookup
            label_lookup = {label.slug: label for label in available_labels}
            
            # Generate polls
            polls_created = 0
            start_date = datetime.utcnow() - timedelta(days=90)
            
            # Create Level A principles (60 total)
            for i in range(60):
                poll_template = random.choice(SAMPLE_POLLS[:5])  # First 5 are Level A
                
                # Randomize the title slightly
                title = f"{poll_template['title']} #{i+1}"
                description = poll_template['description']
                
                # Randomize creation date
                created_at = start_date + timedelta(
                    days=random.randint(0, 90),
                    hours=random.randint(0, 23),
                    minutes=random.randint(0, 59)
                )
                
                # Select 1-3 random labels
                selected_labels = random.sample(available_labels, random.randint(1, 3))
                
                await create_poll_with_labels(db, {
                    "title": title,
                    "description": description,
                    "decision_type": "level_a",
                    "direction_choice": poll_template["direction_choice"]
                }, user, selected_labels, created_at)
                
                polls_created += 1
                if polls_created % 20 == 0:
                    print(f"📊 Created {polls_created} polls...")
            
            # Create Level B actions (240 total)
            for i in range(240):
                poll_template = random.choice(SAMPLE_POLLS[5:])  # Rest are Level B
                
                # Randomize the title slightly
                title = f"{poll_template['title']} #{i+1}"
                description = poll_template['description']
                
                # Randomize creation date
                created_at = start_date + timedelta(
                    days=random.randint(0, 90),
                    hours=random.randint(0, 23),
                    minutes=random.randint(0, 59)
                )
                
                # Select 1-3 random labels
                selected_labels = random.sample(available_labels, random.randint(1, 3))
                
                await create_poll_with_labels(db, {
                    "title": title,
                    "description": description,
                    "decision_type": "level_b"
                }, user, selected_labels, created_at)
                
                polls_created += 1
                if polls_created % 50 == 0:
                    print(f"📊 Created {polls_created} polls...")
            
            await db.commit()
            print(f"✅ Created {polls_created} polls with labels")
            
            # Count total polls
            total_polls = await db.execute("SELECT COUNT(*) as count FROM polls")
            total_count = total_polls.scalar()
            print(f"📊 Total polls in database: {total_count}")
            
            # Count poll-label associations
            total_associations = await db.execute("SELECT COUNT(*) as count FROM poll_labels")
            association_count = total_associations.scalar()
            print(f"🏷️ Total poll-label associations: {association_count}")
            
        except Exception as e:
            print(f"❌ Error seeding polls: {e}")
            await db.rollback()
            raise

if __name__ == "__main__":
    # Environment guard
    if os.getenv("ENVIRONMENT") == "production":
        print("❌ This script should not be run in production")
        sys.exit(1)
    
    asyncio.run(seed_stress_polls())
    print("🎉 Stress poll seeding complete!")
