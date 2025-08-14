#!/usr/bin/env python3
"""
Auto-tagging script for polls with topic labels.

This script analyzes poll titles and descriptions to automatically assign
relevant topic labels based on keyword matching and predefined nudges.
"""

import argparse
import asyncio
import re
from collections import defaultdict
from typing import List, Dict, Set

from sqlalchemy import select, insert, delete, text
from sqlalchemy.orm import selectinload

from backend.config import settings
from backend.database import async_session_maker
from backend.models.poll import Poll
from backend.models.label import Label
from backend.models.poll_label import poll_labels

# Keyword mapping for label assignment
LABEL_KEYWORDS = {
    "environment": [
        "environment", "climate", "emission", "diesel", "electric", "compost", "recycling",
        "greenhouse", "stewardship", "sustainable", "sustainability", "waste", "garden", "park"
    ],
    "mobility": [
        "mobility", "bike", "bikelane", "bicycle", "bus", "transit", "route", "street",
        "traffic", "pedestrian", "sidewalk", "lane"
    ],
    "governance": [
        "governance", "charter", "policy", "framework", "vision", "open data", "transparency",
        "process", "procedures"
    ],
    "budget": [
        "budget", "funding", "allocate", "cost", "spend", "revenue", "tax"
    ],
    "education": [
        "education", "school", "library", "curriculum", "student", "teacher"
    ],
    "health": [
        "health", "clinic", "hospital", "public health", "wellbeing", "sanitation"
    ],
    "housing": [
        "housing", "zoning", "rent", "shelter", "affordable", "home"
    ],
}

# Explicit nudges for specific poll titles
NUDGES = {
    "environmental stewardship charter": ["environment", "governance"],
    "open data & transparency charter": ["governance"],
    "mobility vision 2030": ["mobility", "governance"],
    "install protected bike lanes on main st": ["mobility", "environment"],
    "pilot curbside composting for 1 year": ["environment", "health"],
    "extend library weekend hours": ["education", "budget"],
    "replace diesel buses with electric on route 4": ["mobility", "environment"],
}

# Simple word tokenizer
TOKENIZER = re.compile(r"[a-z0-9]+")


def normalize(text: str) -> str:
    """Normalize text for comparison."""
    return (text or "").lower().strip()


def tokenize(text: str) -> Set[str]:
    """Tokenize text into words."""
    return set(TOKENIZER.findall(normalize(text)))


def score_labels(title: str, description: str) -> Dict[str, int]:
    """Score labels based on keyword matching in title and description."""
    tokens = tokenize(f"{title} {description}")
    scores = defaultdict(int)
    
    # Score based on keyword matching
    for slug, keywords in LABEL_KEYWORDS.items():
        for kw in keywords:
            kw_tokens = kw.split()
            if len(kw_tokens) == 1:
                if kw in tokens:
                    scores[slug] += 2
            else:
                if kw in normalize(f"{title} {description}"):
                    scores[slug] += 3
    
    # Apply explicit nudges for specific titles
    tnorm = normalize(title)
    if tnorm in NUDGES:
        for slug in NUDGES[tnorm]:
            scores[slug] += 5
    
    return dict(scores)


async def main(dry_run: bool, clear_existing: bool, max_labels: int):
    """Main auto-tagging function."""
    if not settings.LABELS_ENABLED:
        print("LABELS_ENABLED is false; aborting.")
        return

    async with async_session_maker() as session:
        # Load all labels into a slug -> Label mapping
        labels_result = await session.execute(select(Label))
        labels = labels_result.scalars().all()
        slug_map = {label.slug: label for label in labels}
        
        if not slug_map:
            print("No labels found. Seed labels first.")
            return

        print(f"Loaded {len(slug_map)} labels: {list(slug_map.keys())}")

        # Check total polls count first
        total_count_result = await session.execute(text("SELECT COUNT(*) FROM polls"))
        total_count = total_count_result.scalar()
        print(f"Total polls in database: {total_count}")

        # Load all polls using raw SQL to bypass soft delete filter
        polls_result = await session.execute(text("""
            SELECT p.id, p.title, p.description, p.decision_type 
            FROM polls p 
            WHERE p.is_deleted = 0 OR p.is_deleted IS NULL
        """))
        polls_data = polls_result.fetchall()

        print(f"Processing {len(polls_data)} active polls...")

        # Load existing label associations for all polls
        poll_labels_result = await session.execute(text("""
            SELECT pl.poll_id, l.slug 
            FROM poll_labels pl 
            JOIN labels l ON pl.label_id = l.id
        """))
        existing_labels = defaultdict(list)
        for poll_id, slug in poll_labels_result.fetchall():
            existing_labels[poll_id].append(slug)

        total, changed = 0, 0
        for poll_data in polls_data:
            poll_id, title, description, decision_type = poll_data
            total += 1
            
            # Score labels for this poll
            scores = score_labels(title, description or "")
            if not scores:
                print(f"- {title}: no matching keywords")
                continue
            
            # Choose top labels (stable order by (-score, slug))
            chosen = [
                slug for slug, _ in sorted(scores.items(), key=lambda kv: (-kv[1], kv[0]))[:max_labels]
            ]
            
            # Ensure labels exist
            chosen_ids = [slug_map[slug].id for slug in chosen if slug in slug_map]
            
            # Get current label IDs
            current_slugs = existing_labels.get(poll_id, [])
            current_ids = {slug_map[slug].id for slug in current_slugs if slug in slug_map}
            
            if clear_existing:
                to_delete = current_ids - set(chosen_ids)
                if to_delete and not dry_run:
                    await session.execute(
                        delete(poll_labels).where(
                            (poll_labels.c.poll_id == poll_id) & 
                            (poll_labels.c.label_id.in_(to_delete))
                        )
                    )
                current_ids = current_ids - to_delete

            # Add new labels
            to_add = [label_id for label_id in chosen_ids if label_id not in current_ids]
            if to_add and not dry_run:
                await session.execute(
                    insert(poll_labels),
                    [{"poll_id": poll_id, "label_id": label_id} for label_id in to_add],
                )
                changed += 1

            # Log the changes
            print(f"- {title}: existing={current_slugs}  chosen={chosen}  add={len(to_add)}")

        if dry_run:
            print(f"[DRY-RUN] processed {total} polls, would change {changed}")
        else:
            await session.commit()
            print(f"[APPLIED] processed {total} polls, changed {changed}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Auto-tag polls with topic labels.")
    parser.add_argument("--dry-run", action="store_true", help="Do not write changes.")
    parser.add_argument("--clear-existing", action="store_true", help="Remove labels not in the chosen set before adding.")
    parser.add_argument("--max-labels", type=int, default=3, help="Max labels to add per poll (<=5 hard cap).")
    args = parser.parse_args()
    
    asyncio.run(main(args.dry_run, args.clear_existing, min(args.max_labels, 5)))
