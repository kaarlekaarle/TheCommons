#!/usr/bin/env python3
"""
Smoke test script for label assignments.

This script provides a quick overview of how polls are tagged with labels
for verification purposes.
"""

import asyncio
from collections import defaultdict
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload

from backend.config import settings
from backend.database import async_session_maker
from backend.models.poll import Poll
from backend.models.label import Label


async def main():
    """Main smoke test function."""
    if not settings.LABELS_ENABLED:
        print("LABELS_ENABLED is false; aborting.")
        return

    async with async_session_maker() as session:
        # Get all labels
        labels_result = await session.execute(select(Label).order_by(Label.name))
        labels = labels_result.scalars().all()
        
        print("=== LABEL ASSIGNMENT SUMMARY ===")
        print(f"Total labels: {len(labels)}")
        print()
        
        # Count polls per label
        label_counts = defaultdict(int)
        label_samples = defaultdict(list)
        
        for label in labels:
            # Count polls with this label
            polls_result = await session.execute(
                select(Poll)
                .options(selectinload(Poll.labels))
                .where(Poll.labels.any(id=label.id))
            )
            polls = polls_result.scalars().all()
            
            label_counts[label.name] = len(polls)
            
            # Get sample titles (up to 3)
            sample_titles = [poll.title for poll in polls[:3]]
            label_samples[label.name] = sample_titles
        
        # Print summary
        for label in labels:
            count = label_counts[label.name]
            samples = label_samples[label.name]
            
            print(f"📊 {label.name} ({label.slug}): {count} polls")
            if samples:
                for title in samples:
                    print(f"   • {title}")
            else:
                print("   • (no polls tagged)")
            print()
        
        # Show polls with no labels
        polls_result = await session.execute(
            select(Poll).options(selectinload(Poll.labels))
        )
        all_polls = polls_result.scalars().all()
        
        untagged = [poll for poll in all_polls if not poll.labels]
        if untagged:
            print(f"📋 {len(untagged)} polls with no labels:")
            for poll in untagged[:5]:  # Show first 5
                print(f"   • {poll.title}")
            if len(untagged) > 5:
                print(f"   ... and {len(untagged) - 5} more")
            print()
        
        # Show polls with multiple labels
        multi_labeled = [poll for poll in all_polls if len(poll.labels) > 1]
        if multi_labeled:
            print(f"🏷️  {len(multi_labeled)} polls with multiple labels:")
            for poll in multi_labeled[:5]:  # Show first 5
                label_names = [label.name for label in poll.labels]
                print(f"   • {poll.title}: {', '.join(label_names)}")
            if len(multi_labeled) > 5:
                print(f"   ... and {len(multi_labeled) - 5} more")
            print()
        
        print("=== END SUMMARY ===")


if __name__ == "__main__":
    asyncio.run(main())
