#!/usr/bin/env python3
"""
Stress test label seeding script.
Creates ~25 labels covering common community decision areas.
"""

import asyncio
import os
import sys
from datetime import datetime
from pathlib import Path

# Add the backend directory to the Python path
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

from backend.database import get_db
from backend.models.label import Label
from backend.config import settings

# Comprehensive list of community-focused labels
STRESS_LABELS = [
    # Core infrastructure
    {"name": "Environment", "slug": "environment"},
    {"name": "Mobility", "slug": "mobility"},
    {"name": "Governance", "slug": "governance"},
    {"name": "Budget", "slug": "budget"},
    {"name": "Education", "slug": "education"},
    {"name": "Health", "slug": "health"},
    {"name": "Housing", "slug": "housing"},
    
    # Public services
    {"name": "Public Safety", "slug": "public-safety"},
    {"name": "Energy", "slug": "energy"},
    {"name": "Transportation", "slug": "transportation"},
    {"name": "Childcare", "slug": "childcare"},
    {"name": "Arts & Culture", "slug": "arts-culture"},
    {"name": "Technology", "slug": "technology"},
    
    # Community development
    {"name": "Economic Development", "slug": "economic-development"},
    {"name": "Social Services", "slug": "social-services"},
    {"name": "Parks & Recreation", "slug": "parks-recreation"},
    {"name": "Libraries", "slug": "libraries"},
    {"name": "Public Spaces", "slug": "public-spaces"},
    
    # Sustainability
    {"name": "Climate Action", "slug": "climate-action"},
    {"name": "Waste Management", "slug": "waste-management"},
    {"name": "Water Resources", "slug": "water-resources"},
    {"name": "Green Infrastructure", "slug": "green-infrastructure"},
    
    # Equity & inclusion
    {"name": "Equity & Inclusion", "slug": "equity-inclusion"},
    {"name": "Accessibility", "slug": "accessibility"},
    {"name": "Community Engagement", "slug": "community-engagement"},
]

async def seed_stress_labels():
    """Seed stress test labels."""
    if not settings.LABELS_ENABLED:
        print("❌ Labels feature is not enabled. Set LABELS_ENABLED=true")
        return
    
    print("🌱 Seeding stress test labels...")
    
    async for db in get_db():
        try:
            # Check if labels already exist
            existing_labels = await db.execute(
                "SELECT slug FROM labels WHERE slug IN :slugs",
                {"slugs": tuple(label["slug"] for label in STRESS_LABELS)}
            )
            existing_slugs = {row.slug for row in existing_labels}
            
            # Create new labels
            new_labels = []
            for label_data in STRESS_LABELS:
                if label_data["slug"] not in existing_slugs:
                    label = Label(
                        name=label_data["name"],
                        slug=label_data["slug"],
                        is_active=True,
                        created_at=datetime.utcnow(),
                        updated_at=datetime.utcnow()
                    )
                    new_labels.append(label)
            
            if new_labels:
                db.add_all(new_labels)
                await db.commit()
                print(f"✅ Created {len(new_labels)} new labels")
            else:
                print("✅ All stress test labels already exist")
            
            # Count total labels
            total_labels = await db.execute("SELECT COUNT(*) as count FROM labels")
            total_count = total_labels.scalar()
            print(f"📊 Total labels in database: {total_count}")
            
        except Exception as e:
            print(f"❌ Error seeding labels: {e}")
            await db.rollback()
            raise

if __name__ == "__main__":
    # Environment guard
    if os.getenv("ENVIRONMENT") == "production":
        print("❌ This script should not be run in production")
        sys.exit(1)
    
    asyncio.run(seed_stress_labels())
    print("🎉 Stress label seeding complete!")
