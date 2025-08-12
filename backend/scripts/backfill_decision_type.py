#!/usr/bin/env python3
"""
Backfill script for decision_type and direction_choice fields.

This script ensures data consistency by:
1. Setting decision_type="level_b" where NULL
2. Setting direction_choice=NULL where decision_type="level_b"
3. Logging any corrections made
"""

import asyncio
import sys
from pathlib import Path
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

# Add the project root to Python path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from backend.config import settings

# Database configuration
DATABASE_URL = settings.DATABASE_URL

# Create async engine and session maker
engine = create_async_engine(DATABASE_URL, echo=False)
async_session_maker = sessionmaker(
    engine, class_=AsyncSession, expire_on_commit=False
)


async def backfill_decision_type():
    """Backfill decision_type and direction_choice fields."""
    print("🔄 Starting decision_type backfill...")
    
    async with async_session_maker() as session:
        try:
            # 1. Set decision_type="level_b" where NULL
            result = await session.execute(
                text("UPDATE polls SET decision_type = 'level_b' WHERE decision_type IS NULL")
            )
            null_updates = result.rowcount
            print(f"✅ Set decision_type='level_b' for {null_updates} polls with NULL decision_type")
            
            # 2. Set direction_choice=NULL where decision_type="level_b" but direction_choice is not NULL
            result = await session.execute(
                text("""
                    UPDATE polls 
                    SET direction_choice = NULL 
                    WHERE decision_type = 'level_b' AND direction_choice IS NOT NULL
                """)
            )
            direction_corrections = result.rowcount
            if direction_corrections > 0:
                print(f"⚠️  Corrected direction_choice=NULL for {direction_corrections} Level B polls")
            
            # 3. Verify the data
            result = await session.execute(text("SELECT COUNT(*) FROM polls"))
            total_polls = result.scalar()
            
            result = await session.execute(
                text("SELECT COUNT(*) FROM polls WHERE decision_type IS NULL")
            )
            null_decision_type = result.scalar()
            
            result = await session.execute(
                text("""
                    SELECT COUNT(*) FROM polls 
                    WHERE decision_type = 'level_b' AND direction_choice IS NOT NULL
                """)
            )
            level_b_with_direction = result.scalar()
            
            await session.commit()
            
            print(f"\n📊 Backfill Summary:")
            print(f"   Total polls: {total_polls}")
            print(f"   Polls with NULL decision_type: {null_decision_type}")
            print(f"   Level B polls with direction_choice: {level_b_with_direction}")
            
            if null_decision_type == 0 and level_b_with_direction == 0:
                print("✅ All data is consistent!")
            else:
                print("⚠️  Some data inconsistencies remain")
                
        except Exception as e:
            await session.rollback()
            print(f"❌ Error during backfill: {e}")
            raise


async def main():
    """Main function."""
    print("🎯 Decision Type Backfill Script")
    print("=" * 50)
    
    try:
        await backfill_decision_type()
        print("\n✅ Backfill completed successfully!")
    except Exception as e:
        print(f"\n❌ Backfill failed: {e}")
        sys.exit(1)
    finally:
        await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())
