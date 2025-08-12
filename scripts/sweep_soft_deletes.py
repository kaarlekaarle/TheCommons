#!/usr/bin/env python3
"""Soft-delete sweep script for The Commons.

This script permanently deletes soft-deleted records older than the grace period.
Use with caution as this operation is irreversible.
"""

import argparse
import asyncio
import os
import sys
from datetime import datetime, timedelta
from typing import Dict, List, Optional

# Add the backend directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from backend.database import async_session_maker
from backend.models.user import User
from backend.models.poll import Poll
from backend.models.vote import Vote
from backend.models.comment import Comment
from backend.models.delegation import Delegation
from backend.core.logging_json import configure_json_logging, get_json_logger

# Configure logging
configure_json_logging(log_level="INFO")
logger = get_json_logger(__name__)

class SoftDeleteSweeper:
    """Handles sweeping of soft-deleted records."""
    
    def __init__(self, grace_days: int = 30, dry_run: bool = False):
        """Initialize the sweeper.
        
        Args:
            grace_days: Number of days to keep soft-deleted records
            dry_run: If True, only show what would be deleted
        """
        self.grace_days = grace_days
        self.dry_run = dry_run
        self.cutoff_date = datetime.utcnow() - timedelta(days=grace_days)
        
    async def sweep_users(self, session: AsyncSession) -> int:
        """Sweep soft-deleted users.
        
        Args:
            session: Database session
            
        Returns:
            Number of users deleted
        """
        query = select(User).where(
            and_(
                User.is_deleted == True,
                User.deleted_at < self.cutoff_date
            )
        )
        
        result = await session.execute(query)
        users = result.scalars().all()
        
        if not users:
            return 0
            
        if self.dry_run:
            logger.info(f"DRY RUN: Would delete {len(users)} soft-deleted users")
            for user in users:
                logger.info(f"  - User {user.username} (deleted {user.deleted_at})")
        else:
            for user in users:
                await session.delete(user)
            await session.commit()
            logger.info(f"Deleted {len(users)} soft-deleted users")
            
        return len(users)
    
    async def sweep_polls(self, session: AsyncSession) -> int:
        """Sweep soft-deleted polls.
        
        Args:
            session: Database session
            
        Returns:
            Number of polls deleted
        """
        query = select(Poll).where(
            and_(
                Poll.is_deleted == True,
                Poll.deleted_at < self.cutoff_date
            )
        )
        
        result = await session.execute(query)
        polls = result.scalars().all()
        
        if not polls:
            return 0
            
        if self.dry_run:
            logger.info(f"DRY RUN: Would delete {len(polls)} soft-deleted polls")
            for poll in polls:
                logger.info(f"  - Poll '{poll.title}' (deleted {poll.deleted_at})")
        else:
            for poll in polls:
                await session.delete(poll)
            await session.commit()
            logger.info(f"Deleted {len(polls)} soft-deleted polls")
            
        return len(polls)
    
    async def sweep_votes(self, session: AsyncSession) -> int:
        """Sweep soft-deleted votes.
        
        Args:
            session: Database session
            
        Returns:
            Number of votes deleted
        """
        query = select(Vote).where(
            and_(
                Vote.is_deleted == True,
                Vote.deleted_at < self.cutoff_date
            )
        )
        
        result = await session.execute(query)
        votes = result.scalars().all()
        
        if not votes:
            return 0
            
        if self.dry_run:
            logger.info(f"DRY RUN: Would delete {len(votes)} soft-deleted votes")
        else:
            for vote in votes:
                await session.delete(vote)
            await session.commit()
            logger.info(f"Deleted {len(votes)} soft-deleted votes")
            
        return len(votes)
    
    async def sweep_comments(self, session: AsyncSession) -> int:
        """Sweep soft-deleted comments.
        
        Args:
            session: Database session
            
        Returns:
            Number of comments deleted
        """
        query = select(Comment).where(
            and_(
                Comment.is_deleted == True,
                Comment.deleted_at < self.cutoff_date
            )
        )
        
        result = await session.execute(query)
        comments = result.scalars().all()
        
        if not comments:
            return 0
            
        if self.dry_run:
            logger.info(f"DRY RUN: Would delete {len(comments)} soft-deleted comments")
        else:
            for comment in comments:
                await session.delete(comment)
            await session.commit()
            logger.info(f"Deleted {len(comments)} soft-deleted comments")
            
        return len(comments)
    
    async def sweep_delegations(self, session: AsyncSession) -> int:
        """Sweep soft-deleted delegations.
        
        Args:
            session: Database session
            
        Returns:
            Number of delegations deleted
        """
        query = select(Delegation).where(
            and_(
                Delegation.is_deleted == True,
                Delegation.deleted_at < self.cutoff_date
            )
        )
        
        result = await session.execute(query)
        delegations = result.scalars().all()
        
        if not delegations:
            return 0
            
        if self.dry_run:
            logger.info(f"DRY RUN: Would delete {len(delegations)} soft-deleted delegations")
        else:
            for delegation in delegations:
                await session.delete(delegation)
            await session.commit()
            logger.info(f"Deleted {len(delegations)} soft-deleted delegations")
            
        return len(delegations)
    
    async def run_sweep(self) -> Dict[str, int]:
        """Run the complete sweep operation.
        
        Returns:
            Dictionary with counts of deleted records by type
        """
        logger.info(f"Starting soft-delete sweep (grace period: {self.grace_days} days)")
        logger.info(f"Cutoff date: {self.cutoff_date.isoformat()}")
        
        if self.dry_run:
            logger.info("DRY RUN MODE - No records will be actually deleted")
        
        async with async_session_maker() as session:
            results = {
                "users": await self.sweep_users(session),
                "polls": await self.sweep_polls(session),
                "votes": await self.sweep_votes(session),
                "comments": await self.sweep_comments(session),
                "delegations": await self.sweep_delegations(session),
            }
        
        total_deleted = sum(results.values())
        
        if self.dry_run:
            logger.info(f"DRY RUN: Would delete {total_deleted} total records")
        else:
            logger.info(f"Sweep completed: {total_deleted} records deleted")
        
        return results

def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Sweep soft-deleted records older than the grace period"
    )
    parser.add_argument(
        "--grace-days",
        type=int,
        default=int(os.getenv("SWEEP_GRACE_DAYS", "30")),
        help="Number of days to keep soft-deleted records (default: 30)"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be deleted without actually deleting"
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable verbose output"
    )
    
    args = parser.parse_args()
    
    if args.verbose:
        configure_json_logging(log_level="DEBUG")
    
    # Validate grace period
    if args.grace_days < 1:
        logger.error("Grace period must be at least 1 day")
        sys.exit(1)
    
    # Run the sweep
    try:
        sweeper = SoftDeleteSweeper(
            grace_days=args.grace_days,
            dry_run=args.dry_run
        )
        
        results = asyncio.run(sweeper.run_sweep())
        
        # Print summary
        print("\n" + "="*50)
        print("SWEEP SUMMARY")
        print("="*50)
        for record_type, count in results.items():
            print(f"{record_type.capitalize()}: {count}")
        print(f"Total: {sum(results.values())}")
        print("="*50)
        
        if args.dry_run:
            print("\nThis was a dry run. No records were actually deleted.")
            print("Run without --dry-run to perform the actual deletion.")
        
    except KeyboardInterrupt:
        logger.info("Sweep interrupted by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Sweep failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
