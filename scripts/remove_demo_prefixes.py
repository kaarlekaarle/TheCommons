#!/usr/bin/env python3
"""
Remove [DEMO] prefixes from existing database records

This script updates existing poll titles in the database to remove [DEMO] prefixes
that were created before the prefixes were removed from the seeding scripts.
"""

import asyncio
import sys
import os
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from backend.models.poll import Poll

# Database configuration
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite+aiosqlite:///test.db")

# Create async engine and session maker
engine = create_async_engine(DATABASE_URL, echo=False)
async_session_maker = sessionmaker(
    engine, class_=AsyncSession, expire_on_commit=False
)

async def remove_demo_prefixes():
    """Remove [DEMO] prefixes from existing poll titles."""
    print("🔧 Removing [DEMO] prefixes from existing database records...")
    
    async with async_session_maker() as session:
        # Find all polls with [DEMO] prefix
        result = await session.execute(
            select(Poll).where(Poll.title.like('[DEMO]%'))
        )
        polls_with_demo = result.scalars().all()
        
        if not polls_with_demo:
            print("✅ No polls with [DEMO] prefix found in database.")
            return
        
        print(f"📋 Found {len(polls_with_demo)} polls with [DEMO] prefix:")
        
        # Update each poll title
        updated_count = 0
        for poll in polls_with_demo:
            old_title = poll.title
            new_title = poll.title.replace('[DEMO] ', '')
            
            if old_title != new_title:
                poll.title = new_title
                print(f"   ✅ Updated: '{old_title}' → '{new_title}'")
                updated_count += 1
        
        # Commit changes
        await session.commit()
        
        print(f"\n✅ Successfully updated {updated_count} poll titles.")
        
        # Verify no [DEMO] prefixes remain
        result = await session.execute(
            select(Poll).where(Poll.title.like('[DEMO]%'))
        )
        remaining_demo_polls = result.scalars().all()
        
        if remaining_demo_polls:
            print(f"⚠️  Warning: {len(remaining_demo_polls)} polls still have [DEMO] prefix:")
            for poll in remaining_demo_polls:
                print(f"   - {poll.title}")
        else:
            print("✅ All [DEMO] prefixes have been successfully removed.")

async def main():
    """Main function to run the cleanup."""
    print("🎯 Remove [DEMO] Prefixes from Database")
    print("=" * 50)
    
    try:
        await remove_demo_prefixes()
        print(f"\n🏁 Cleanup completed successfully!")
        
    except Exception as e:
        print(f"❌ Error during cleanup: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        # Close the engine
        await engine.dispose()
        print("\n🔚 Database connection closed")

if __name__ == "__main__":
    asyncio.run(main())
