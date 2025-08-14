#!/usr/bin/env python3
"""
Script to find duplicate poll-label relationships in the database.
Exits with code 1 if duplicates are found, 0 otherwise.
"""

import asyncio
import sys
from sqlalchemy import select, func, text
from sqlalchemy.ext.asyncio import create_async_engine

from backend.database import get_db
from backend.models.poll_label import poll_labels
from backend.config import settings


async def find_duplicate_poll_labels():
    """Find duplicate poll-label relationships."""
    engine = create_async_engine(settings.DATABASE_URL)
    
    async with engine.begin() as conn:
        # Check for duplicates using SQLAlchemy
        query = select(
            poll_labels.c.poll_id,
            poll_labels.c.label_id,
            func.count().label('count')
        ).group_by(
            poll_labels.c.poll_id,
            poll_labels.c.label_id
        ).having(func.count() > 1)
        
        result = await conn.execute(query)
        duplicates = result.fetchall()
        
        if duplicates:
            print("❌ Found duplicate poll-label relationships:")
            print("poll_id | label_id | count")
            print("-" * 40)
            for dup in duplicates:
                print(f"{dup.poll_id} | {dup.label_id} | {dup.count}")
            print(f"\nTotal duplicate groups: {len(duplicates)}")
            return False
        else:
            print("✅ No duplicate poll-label relationships found")
            return True


async def main():
    """Main function."""
    try:
        success = await find_duplicate_poll_labels()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"❌ Error checking for duplicates: {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
