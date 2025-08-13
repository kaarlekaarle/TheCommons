#!/usr/bin/env python3
"""
Cleanup script for old Level-A direction strings.

This script updates old demo direction strings to the new standardized categories
and optionally wipes all Level-A demo data.
"""

import argparse
import asyncio
import sys
from pathlib import Path
from typing import Dict, List, Optional

# Add the project root to Python path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from sqlalchemy import text
from backend.database import async_session_maker
from backend.models.poll import Poll


# Mapping of old strings to new standardized categories
OLD_TO_NEW_MAPPING = {
    "Let's take care of nature": "Environmental Policy",
    "Open by default": "Government Transparency", 
    "People-first streets": "Transportation Safety",
    # Add any other old strings that might exist
}

# New standardized Level-A categories
NEW_LEVEL_A_CATEGORIES = [
    "Transportation Safety",
    "Government Transparency",
    "Environmental Policy",
    "Housing & Development",
    "Parks & Recreation",
    "Climate & Sustainability",
    "Financial Management",
    "Technology & Innovation",
    "Arts & Culture",
    "Food Security",
    "Public Transit",
    "Public Health",
    "Water Management",
    "Waste Management",
    "Civic Engagement",
    "Labor & Employment",
    "Public Safety",
    "Urban Forestry",
    "Heritage Conservation"
]


async def get_poll_counts() -> Dict[str, int]:
    """Get counts of polls by decision type and direction."""
    async with async_session_maker() as session:
        # Count Level A polls
        level_a_count = await session.execute(
            text("SELECT COUNT(*) FROM polls WHERE decision_type = 'level_a'")
        )
        level_a_total = level_a_count.scalar()
        
        # Count Level B polls with direction_choice (should be 0)
        level_b_with_direction = await session.execute(
            text("SELECT COUNT(*) FROM polls WHERE decision_type = 'level_b' AND direction_choice IS NOT NULL")
        )
        level_b_with_direction_count = level_b_with_direction.scalar()
        
        # Count old direction strings
        old_directions = []
        for old_string in OLD_TO_NEW_MAPPING.keys():
            count_result = await session.execute(
                text("SELECT COUNT(*) FROM polls WHERE direction_choice = :old_string"),
                {"old_string": old_string}
            )
            count = count_result.scalar()
            if count > 0:
                old_directions.append((old_string, count))
        
        return {
            "level_a_total": level_a_total,
            "level_b_with_direction": level_b_with_direction_count,
            "old_directions": old_directions
        }


async def cleanup_old_directions(dry_run: bool = True) -> Dict[str, int]:
    """Clean up old direction strings and fix Level B polls."""
    async with async_session_maker() as session:
        updates = {}
        
        # 1. Fix Level B polls that have direction_choice (should be NULL)
        if not dry_run:
            level_b_fix_result = await session.execute(
                text("""
                    UPDATE polls 
                    SET direction_choice = NULL 
                    WHERE decision_type = 'level_b' AND direction_choice IS NOT NULL
                """)
            )
            level_b_fixes = level_b_fix_result.rowcount
        else:
            # Count how many would be fixed
            level_b_count_result = await session.execute(
                text("SELECT COUNT(*) FROM polls WHERE decision_type = 'level_b' AND direction_choice IS NOT NULL")
            )
            level_b_fixes = level_b_count_result.scalar()
        
        updates["level_b_fixes"] = level_b_fixes
        
        # 2. Update old direction strings to new categories
        direction_updates = 0
        for old_string, new_string in OLD_TO_NEW_MAPPING.items():
            if not dry_run:
                result = await session.execute(
                    text("""
                        UPDATE polls 
                        SET direction_choice = :new_string 
                        WHERE decision_type = 'level_a' AND direction_choice = :old_string
                    """),
                    {"old_string": old_string, "new_string": new_string}
                )
                direction_updates += result.rowcount
            else:
                # Count how many would be updated
                count_result = await session.execute(
                    text("SELECT COUNT(*) FROM polls WHERE decision_type = 'level_a' AND direction_choice = :old_string"),
                    {"old_string": old_string}
                )
                direction_updates += count_result.scalar()
        
        updates["direction_updates"] = direction_updates
        
        if not dry_run:
            await session.commit()
        
        return updates


async def wipe_level_a_demo_data(dry_run: bool = True) -> int:
    """Wipe all Level-A demo data."""
    async with async_session_maker() as session:
        if not dry_run:
            result = await session.execute(
                text("DELETE FROM polls WHERE decision_type = 'level_a'")
            )
            deleted_count = result.rowcount
            await session.commit()
        else:
            # Count how many would be deleted
            count_result = await session.execute(
                text("SELECT COUNT(*) FROM polls WHERE decision_type = 'level_a'")
            )
            deleted_count = count_result.scalar()
        
        return deleted_count


async def main():
    parser = argparse.ArgumentParser(description="Clean up old Level-A direction strings")
    parser.add_argument("--dry-run", action="store_true", help="Show what would be changed without making changes")
    parser.add_argument("--wipe-level-a", action="store_true", help="Delete all Level-A demo data")
    parser.add_argument("--force", action="store_true", help="Skip confirmation prompts")
    
    args = parser.parse_args()
    
    print("🔍 Analyzing current poll data...")
    counts = await get_poll_counts()
    
    print(f"\n📊 Current poll counts:")
    print(f"   Level A polls: {counts['level_a_total']}")
    print(f"   Level B polls with direction_choice: {counts['level_b_with_direction']}")
    
    if counts['old_directions']:
        print(f"   Old direction strings found:")
        for old_string, count in counts['old_directions']:
            print(f"     '{old_string}': {count} polls")
    else:
        print("   ✅ No old direction strings found")
    
    if counts['level_b_with_direction'] > 0:
        print(f"   ⚠️  {counts['level_b_with_direction']} Level B polls have direction_choice (should be NULL)")
    
    if args.wipe_level_a:
        print(f"\n🗑️  WIPE MODE: Would delete all {counts['level_a_total']} Level A polls")
        if not args.force:
            response = input("Are you sure? This cannot be undone! (y/N): ")
            if response.lower() != 'y':
                print("Aborted.")
                return
        
        deleted_count = await wipe_level_a_demo_data(dry_run=args.dry_run)
        if args.dry_run:
            print(f"   Would delete {deleted_count} Level A polls")
        else:
            print(f"   ✅ Deleted {deleted_count} Level A polls")
    else:
        print(f"\n🧹 Cleaning up old direction strings...")
        updates = await cleanup_old_directions(dry_run=args.dry_run)
        
        if updates['level_b_fixes'] > 0:
            if args.dry_run:
                print(f"   Would fix {updates['level_b_fixes']} Level B polls (set direction_choice to NULL)")
            else:
                print(f"   ✅ Fixed {updates['level_b_fixes']} Level B polls")
        
        if updates['direction_updates'] > 0:
            if args.dry_run:
                print(f"   Would update {updates['direction_updates']} old direction strings")
            else:
                print(f"   ✅ Updated {updates['direction_updates']} old direction strings")
        
        if updates['level_b_fixes'] == 0 and updates['direction_updates'] == 0:
            print("   ✅ No cleanup needed")
    
    if args.dry_run:
        print(f"\n💡 This was a dry run. Use --force to apply changes.")


if __name__ == "__main__":
    asyncio.run(main())
