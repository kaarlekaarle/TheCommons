#!/usr/bin/env python3
"""
Seed script to create default labels for the Topic Label system.
"""

import asyncio
import uuid
from sqlalchemy.ext.asyncio import AsyncSession

from backend.database import async_session_maker
from backend.models.label import Label
from backend.schemas.label import generate_slug
from backend.config import settings


DEFAULT_LABELS = [
    "Environment",
    "Mobility", 
    "Governance",
    "Budget",
    "Education",
    "Health",
    "Housing"
]


async def seed_labels(db: AsyncSession) -> None:
    """Create default labels if they don't exist."""
    print("Seeding default labels...")
    
    for label_name in DEFAULT_LABELS:
        # Check if label already exists
        from sqlalchemy import select
        slug = generate_slug(label_name)
        
        existing_result = await db.execute(
            select(Label).where(Label.slug == slug)
        )
        existing_label = existing_result.scalar_one_or_none()
        
        if existing_label:
            print(f"Label '{label_name}' ({slug}) already exists, skipping...")
            continue
        
        # Create new label
        from datetime import datetime
        label = Label(
            id=str(uuid.uuid4()),
            name=label_name,
            slug=slug,
            is_active=True,
            created_at=datetime.utcnow()
        )
        
        db.add(label)
        print(f"Created label: {label_name} ({slug})")
    
    await db.commit()
    print("Label seeding completed!")


async def main():
    """Main function to run the seeder."""
    if not settings.LABELS_ENABLED:
        print("Labels feature is disabled. Skipping label seeding.")
        return
    
    async with async_session_maker() as db:
        await seed_labels(db)


if __name__ == "__main__":
    asyncio.run(main())
