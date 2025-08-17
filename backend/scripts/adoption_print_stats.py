#!/usr/bin/env python3
"""
Adoption Telemetry Stats Printer

Fetches and pretty-prints adoption statistics from the telemetry system.
Can fetch from API endpoint or directly from database.
"""

import asyncio
import sys
import json
import requests
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Any, Optional

# Add backend to path for imports
sys.path.append(str(Path(__file__).parent.parent))

from backend.services.adoption_telemetry import AdoptionTelemetryService
from backend.database import get_db


def print_header(title: str):
    """Print a formatted header."""
    print(f"\n{'='*60}")
    print(f"📊 {title}")
    print(f"{'='*60}")


def print_mode_breakdown(stats: Dict[str, Any]):
    """Print mode adoption breakdown."""
    print_header("MODE ADOPTION BREAKDOWN")
    
    mode_counts = stats.get("mode_counts", {})
    mode_percentages = stats.get("mode_percentages", {})
    total = stats.get("total_adoptions", 0)
    
    if total == 0:
        print("❌ No adoption events found in the specified period")
        return
    
    print(f"📅 Period: Last {stats.get('period_days', 14)} days")
    print(f"📈 Total adoptions: {total}")
    print()
    
    # Legacy vs Commons breakdown
    legacy_count = mode_counts.get("legacy_fixed_term", 0)
    commons_count = mode_counts.get("flexible_domain", 0)
    legacy_pct = mode_percentages.get("legacy_fixed_term", 0.0)
    commons_pct = mode_percentages.get("flexible_domain", 0.0)
    
    print("🎯 ADOPTION PATTERNS:")
    print(f"  Traditional (Legacy): {legacy_count:3d} events ({legacy_pct:5.1f}%)")
    print(f"  Commons (Flexible):  {commons_count:3d} events ({commons_pct:5.1f}%)")
    
    # Status indicator
    if commons_pct > 70:
        status = "🟢 EXCELLENT - Strong commons adoption"
    elif commons_pct > 50:
        status = "🟡 GOOD - Balanced adoption"
    elif commons_pct > 30:
        status = "🟠 FAIR - Some commons adoption"
    else:
        status = "🔴 NEEDS ATTENTION - Low commons adoption"
    
    print(f"\n📊 Status: {status}")


def print_transitions(stats: Dict[str, Any]):
    """Print transition patterns."""
    print_header("TRANSITION PATTERNS")
    
    transitions = stats.get("transitions", {})
    total_transitions = sum(transitions.values())
    
    if total_transitions == 0:
        print("❌ No transition events found in the specified period")
        return
    
    print(f"🔄 Total transitions: {total_transitions}")
    print()
    
    for transition_key, count in transitions.items():
        if "_to_" in transition_key:
            from_mode, to_mode = transition_key.split("_to_", 1)
            print(f"  {from_mode:20} → {to_mode:20} : {count:3d} users")
        else:
            print(f"  {transition_key:40} : {count:3d} users")


def print_context_insights(stats: Dict[str, Any]):
    """Print contextual insights if available."""
    print_header("CONTEXTUAL INSIGHTS")
    
    # This would require additional queries to get context breakdown
    # For now, show basic metadata
    generated_at = stats.get("generated_at")
    if generated_at:
        try:
            dt = datetime.fromisoformat(generated_at.replace('Z', '+00:00'))
            print(f"📅 Data generated: {dt.strftime('%Y-%m-%d %H:%M:%S UTC')}")
        except:
            print(f"📅 Data generated: {generated_at}")
    
    period_days = stats.get("period_days", 14)
    print(f"⏱️  Analysis window: {period_days} days")
    
    # Show any errors
    if "error" in stats:
        print(f"⚠️  Warning: {stats['error']}")


def print_recommendations(stats: Dict[str, Any]):
    """Print recommendations based on adoption patterns."""
    print_header("RECOMMENDATIONS")
    
    mode_percentages = stats.get("mode_percentages", {})
    commons_pct = mode_percentages.get("flexible_domain", 0.0)
    transitions = stats.get("transitions", {})
    
    recommendations = []
    
    if commons_pct < 30:
        recommendations.append("🎯 Focus on promoting commons delegation features")
        recommendations.append("📚 Consider user education about field-based delegation")
        recommendations.append("🔍 Investigate barriers to commons adoption")
    
    elif commons_pct < 50:
        recommendations.append("📈 Continue encouraging commons mode adoption")
        recommendations.append("🎨 Optimize UI/UX for commons delegation flow")
    
    elif commons_pct > 70:
        recommendations.append("✅ Excellent commons adoption - maintain momentum")
        recommendations.append("📊 Consider advanced analytics for power distribution")
    
    # Transition insights
    legacy_to_commons = transitions.get("legacy_fixed_term_to_flexible_domain", 0)
    if legacy_to_commons > 0:
        recommendations.append(f"🔄 {legacy_to_commons} users transitioned from legacy to commons")
    
    if not recommendations:
        recommendations.append("📊 Continue monitoring adoption patterns")
        recommendations.append("🔍 Collect user feedback on delegation preferences")
    
    for rec in recommendations:
        print(f"  {rec}")


async def fetch_stats_from_api(days: int = 14) -> Optional[Dict[str, Any]]:
    """Fetch stats from API endpoint."""
    try:
        # Try to connect to local API
        response = requests.get(f"http://localhost:8000/api/delegations/adoption/stats?days={days}", timeout=5)
        if response.status_code == 200:
            return response.json()
    except requests.exceptions.RequestException:
        pass
    
    return None


async def fetch_stats_from_db(days: int = 14) -> Dict[str, Any]:
    """Fetch stats directly from database."""
    try:
        db = next(get_db())
        telemetry_service = AdoptionTelemetryService(db)
        return await telemetry_service.get_adoption_stats(days)
    except Exception as e:
        return {
            "error": f"Failed to fetch from database: {e}",
            "period_days": days,
            "total_adoptions": 0,
            "mode_counts": {},
            "mode_percentages": {},
            "transitions": {}
        }


async def print_adoption_stats(days: int = 14, use_api: bool = True):
    """Print comprehensive adoption statistics."""
    print_header("ADOPTION TELEMETRY STATISTICS")
    
    # Try API first, fallback to database
    stats = None
    if use_api:
        stats = await fetch_stats_from_api(days)
        if stats:
            print("📡 Data source: API endpoint")
        else:
            print("📡 Data source: Database (API unavailable)")
    
    if not stats:
        stats = await fetch_stats_from_db(days)
    
    # Print all sections
    print_mode_breakdown(stats)
    print_transitions(stats)
    print_context_insights(stats)
    print_recommendations(stats)
    
    print(f"\n{'='*60}")


def main():
    """Main entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Print adoption telemetry statistics")
    parser.add_argument(
        "--days", 
        type=int, 
        default=14,
        help="Number of days to analyze (default: 14)"
    )
    parser.add_argument(
        "--no-api",
        action="store_true",
        help="Skip API and use database directly"
    )
    
    args = parser.parse_args()
    
    try:
        asyncio.run(print_adoption_stats(args.days, not args.no_api))
    except KeyboardInterrupt:
        print("\n\n👋 Interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
