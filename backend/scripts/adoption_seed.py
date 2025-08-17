#!/usr/bin/env python3
"""
Adoption Telemetry Seeding Script

Seeds sample adoption events for testing and demonstration purposes.
Creates a realistic mix of legacy and commons delegation adoptions.
"""

import asyncio
import sys
import os
from datetime import datetime, timedelta
from uuid import uuid4
from pathlib import Path

# Add backend to path for imports
sys.path.append(str(Path(__file__).parent.parent))

from backend.services.adoption_telemetry import AdoptionTelemetryService
from backend.models.delegation import DelegationMode
from backend.database import get_db


async def seed_adoption_events():
    """Seed sample adoption events for testing."""
    print("🌱 SEEDING ADOPTION TELEMETRY EVENTS")
    print("=" * 40)
    
    # Create sample user IDs
    user_ids = [uuid4() for _ in range(5)]
    
    # Sample events: 3 legacy, 7 commons
    events = [
        # Legacy adoptions (traditional mode)
        {
            "user_id": user_ids[0],
            "mode": DelegationMode.LEGACY_FIXED_TERM,
            "context": {
                "target_type": "user",
                "field_id": None,
                "has_warnings": False,
                "note": "First-time user, traditional delegation"
            }
        },
        {
            "user_id": user_ids[1], 
            "mode": DelegationMode.LEGACY_FIXED_TERM,
            "context": {
                "target_type": "user",
                "field_id": None,
                "has_warnings": True,
                "note": "User with concentration warning"
            }
        },
        {
            "user_id": user_ids[2],
            "mode": DelegationMode.LEGACY_FIXED_TERM,
            "context": {
                "target_type": "user", 
                "field_id": None,
                "has_warnings": False,
                "note": "Experienced user choosing traditional"
            }
        },
        
        # Commons adoptions (flexible domain mode)
        {
            "user_id": user_ids[0],
            "mode": DelegationMode.FLEXIBLE_DOMAIN,
            "context": {
                "target_type": "field",
                "field_id": "climate-action",
                "has_warnings": False,
                "note": "User transitioning to commons mode"
            }
        },
        {
            "user_id": user_ids[1],
            "mode": DelegationMode.FLEXIBLE_DOMAIN,
            "context": {
                "target_type": "field",
                "field_id": "housing-policy",
                "has_warnings": False,
                "note": "Field-specific delegation"
            }
        },
        {
            "user_id": user_ids[3],
            "mode": DelegationMode.FLEXIBLE_DOMAIN,
            "context": {
                "target_type": "field",
                "field_id": "energy-transition",
                "has_warnings": True,
                "note": "New user with super-delegate warning"
            }
        },
        {
            "user_id": user_ids[4],
            "mode": DelegationMode.FLEXIBLE_DOMAIN,
            "context": {
                "target_type": "field",
                "field_id": "healthcare-reform",
                "has_warnings": False,
                "note": "First-time commons user"
            }
        },
        {
            "user_id": user_ids[0],
            "mode": DelegationMode.FLEXIBLE_DOMAIN,
            "context": {
                "target_type": "field",
                "field_id": "education-funding",
                "has_warnings": False,
                "note": "Multiple field delegations"
            }
        },
        {
            "user_id": user_ids[2],
            "mode": DelegationMode.FLEXIBLE_DOMAIN,
            "context": {
                "target_type": "field",
                "field_id": "transportation",
                "has_warnings": False,
                "note": "Experienced user adopting commons"
            }
        },
        {
            "user_id": user_ids[4],
            "mode": DelegationMode.FLEXIBLE_DOMAIN,
            "context": {
                "target_type": "field",
                "field_id": "digital-rights",
                "has_warnings": True,
                "note": "User with concentration warning in commons"
            }
        }
    ]
    
    # Add some transitions (users changing modes)
    transitions = [
        {
            "user_id": user_ids[0],
            "from_mode": DelegationMode.LEGACY_FIXED_TERM,
            "to_mode": DelegationMode.FLEXIBLE_DOMAIN,
            "context": {
                "trigger": "user_choice",
                "note": "User discovered field-based delegation"
            }
        },
        {
            "user_id": user_ids[2],
            "from_mode": DelegationMode.LEGACY_FIXED_TERM,
            "to_mode": DelegationMode.FLEXIBLE_DOMAIN,
            "context": {
                "trigger": "feature_discovery",
                "note": "User explored commons features"
            }
        }
    ]
    
    try:
        # Get database session
        db = next(get_db())
        telemetry_service = AdoptionTelemetryService(db)
        
        # Seed adoption events
        print(f"📊 Seeding {len(events)} adoption events...")
        for i, event in enumerate(events, 1):
            await telemetry_service.track_delegation_mode(
                event["user_id"],
                event["mode"],
                event["context"]
            )
            print(f"  {i:2d}. {event['mode'].value} → {event['context']['note']}")
        
        # Seed transition events
        print(f"\n🔄 Seeding {len(transitions)} transition events...")
        for i, transition in enumerate(transitions, 1):
            await telemetry_service.track_transition(
                transition["user_id"],
                transition["from_mode"],
                transition["to_mode"],
                transition["context"]
            )
            print(f"  {i:2d}. {transition['from_mode'].value} → {transition['to_mode'].value}")
        
        print(f"\n✅ Successfully seeded {len(events)} adoptions and {len(transitions)} transitions")
        print(f"📅 Events timestamped for: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        # Show quick stats
        stats = await telemetry_service.get_adoption_stats(days=1)
        print(f"\n📈 Quick stats (last 24h):")
        print(f"  Total adoptions: {stats['total_adoptions']}")
        print(f"  Mode breakdown: {stats['mode_counts']}")
        print(f"  Transitions: {sum(stats['transitions'].values())}")
        
    except Exception as e:
        print(f"❌ Error seeding adoption events: {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(seed_adoption_events())
