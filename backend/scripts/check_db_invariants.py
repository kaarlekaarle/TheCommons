#!/usr/bin/env python3
"""
Database invariant checker for The Commons.

This script checks for critical database invariants that should never be violated.
Currently checks:
- No duplicate poll-label relationships
"""

import asyncio
import sys
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
import os
from typing import Optional


async def check_poll_label_duplicates(session: AsyncSession) -> bool:
    """Check for duplicate poll-label relationships."""
    print("🔍 Checking for duplicate poll-label relationships...")
    
    # Query to count total vs distinct relationships
    # Use different syntax for SQLite vs PostgreSQL
    result = await session.execute(text("SELECT name FROM sqlite_master WHERE type='table' AND name='poll_labels'"))
    table_exists = result.scalar()
    
    if not table_exists:
        print("⚠️  poll_labels table does not exist, skipping check")
        return True
    
    # Check if we're using SQLite or PostgreSQL
    result = await session.execute(text("SELECT sqlite_version()"))
    sqlite_version = result.scalar()
    
    if sqlite_version:
        # SQLite syntax
        query = text("""
            SELECT 
                COUNT(*) as total_count,
                COUNT(DISTINCT poll_id || ':' || label_id) as unique_count
            FROM poll_labels
        """)
    else:
        # PostgreSQL syntax
        query = text("""
            SELECT 
                COUNT(*) as total_count,
                COUNT(DISTINCT (poll_id, label_id)) as unique_count
            FROM poll_labels
        """)
    
    result = await session.execute(query)
    row = result.fetchone()
    
    if not row:
        print("✅ No poll-label relationships found")
        return True
    
    total_count, unique_count = row
    
    print(f"📊 Total poll-label relationships: {total_count}")
    print(f"📊 Unique poll-label relationships: {unique_count}")
    
    if total_count != unique_count:
        duplicates = total_count - unique_count
        print(f"❌ Found {duplicates} duplicate poll-label relationships!")
        
        # Show some examples of duplicates
        if sqlite_version:
            dup_query = text("""
                SELECT poll_id, label_id, COUNT(*) as count
                FROM poll_labels
                GROUP BY poll_id || ':' || label_id
                HAVING COUNT(*) > 1
                LIMIT 5
            """)
        else:
            dup_query = text("""
                SELECT poll_id, label_id, COUNT(*) as count
                FROM poll_labels
                GROUP BY (poll_id, label_id)
                HAVING COUNT(*) > 1
                LIMIT 5
            """)
        
        dup_result = await session.execute(dup_query)
        duplicates_examples = dup_result.fetchall()
        
        print("🔍 Example duplicates:")
        for poll_id, label_id, count in duplicates_examples:
            print(f"   Poll {poll_id} -> Label {label_id}: {count} times")
        
        return False
    else:
        print("✅ No duplicate poll-label relationships found")
        return True


async def check_soft_deleted_visibility(session: AsyncSession) -> bool:
    """Check that soft-deleted records are not visible in normal queries."""
    print("🔍 Checking soft-delete visibility...")
    
    # Check polls table
    result = await session.execute(text("SELECT COUNT(*) FROM polls WHERE is_deleted = 1"))
    soft_deleted_polls = result.scalar()
    
    if soft_deleted_polls > 0:
        print(f"📊 Found {soft_deleted_polls} soft-deleted polls")
        
        # Check if any soft-deleted polls appear in normal queries
        result = await session.execute(text("""
            SELECT COUNT(*) FROM polls 
            WHERE is_deleted = 1 
            AND id IN (
                SELECT DISTINCT poll_id 
                FROM poll_labels 
                JOIN labels ON poll_labels.label_id = labels.id 
                WHERE labels.is_active = 1 AND labels.is_deleted = 0
            )
        """))
        
        visible_deleted = result.scalar()
        if visible_deleted > 0:
            print(f"❌ Found {visible_deleted} soft-deleted polls that are still visible!")
            return False
        else:
            print("✅ Soft-deleted polls are properly hidden")
    else:
        print("✅ No soft-deleted polls found")
    
    return True


async def check_label_consistency(session: AsyncSession) -> bool:
    """Check label consistency invariants."""
    print("🔍 Checking label consistency...")
    
    # Check for labels that are both active and deleted
    result = await session.execute(text("""
        SELECT COUNT(*) FROM labels 
        WHERE is_active = 1 AND is_deleted = 1
    """))
    
    inconsistent_labels = result.scalar()
    if inconsistent_labels > 0:
        print(f"❌ Found {inconsistent_labels} labels that are both active and deleted!")
        return False
    
    print("✅ Label consistency checks passed")
    return True


async def main():
    """Main function to run all invariant checks."""
    # Get database URL from environment
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        print("❌ DATABASE_URL environment variable not set")
        sys.exit(1)
    
    # Create engine
    engine = create_async_engine(database_url, echo=False)
    
    try:
        async with engine.begin() as conn:
            # Create session
            async_session = sessionmaker(
                engine, class_=AsyncSession, expire_on_commit=False
            )
            
            async with async_session() as session:
                print("🚀 Starting database invariant checks...")
                print("=" * 50)
                
                all_passed = True
                
                # Run all checks
                checks = [
                    ("Poll-Label Duplicates", check_poll_label_duplicates),
                    ("Soft-Delete Visibility", check_soft_deleted_visibility),
                    ("Label Consistency", check_label_consistency),
                ]
                
                for check_name, check_func in checks:
                    print(f"\n🔍 Running: {check_name}")
                    print("-" * 30)
                    
                    try:
                        passed = await check_func(session)
                        if not passed:
                            all_passed = False
                    except Exception as e:
                        print(f"❌ Error in {check_name}: {e}")
                        all_passed = False
                
                print("\n" + "=" * 50)
                if all_passed:
                    print("✅ All database invariants passed!")
                    sys.exit(0)
                else:
                    print("❌ Some database invariants failed!")
                    sys.exit(1)
    
    except Exception as e:
        print(f"❌ Database connection error: {e}")
        sys.exit(1)
    finally:
        await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())
