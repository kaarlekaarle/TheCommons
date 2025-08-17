# Adoption Telemetry Runbook

Quick reference for working with the adoption telemetry system.

## Overview

The adoption telemetry system tracks how users adopt different delegation modes (traditional vs commons) and transition between them. This helps monitor constitutional drift and user experience patterns.

## Quick Commands

### 1. Seed Sample Data

```bash
# Seed 10 adoption events (3 legacy, 7 commons) + 2 transitions
cd backend/scripts
python adoption_seed.py
```

**Output:**
```
🌱 SEEDING ADOPTION TELEMETRY EVENTS
========================================
📊 Seeding 10 adoption events...
  1. legacy_fixed_term → First-time user, traditional delegation
  2. legacy_fixed_term → User with concentration warning
  3. legacy_fixed_term → Experienced user choosing traditional
  4. flexible_domain → User transitioning to commons mode
  5. flexible_domain → Field-specific delegation
  ...

🔄 Seeding 2 transition events...
  1. legacy_fixed_term → flexible_domain
  2. legacy_fixed_term → flexible_domain

✅ Successfully seeded 10 adoptions and 2 transitions
📅 Events timestamped for: 2025-01-27 15:30:45

📈 Quick stats (last 24h):
  Total adoptions: 10
  Mode breakdown: {'legacy_fixed_term': 3, 'flexible_domain': 7}
  Transitions: 2
```

### 2. Print Statistics

```bash
# Print stats for last 14 days (default)
python adoption_print_stats.py

# Print stats for last 7 days
python adoption_print_stats.py --days 7

# Use database directly (skip API)
python adoption_print_stats.py --no-api
```

**Output:**
```
============================================================
📊 ADOPTION TELEMETRY STATISTICS
============================================================
📡 Data source: API endpoint

============================================================
📊 MODE ADOPTION BREAKDOWN
============================================================
📅 Period: Last 14 days
📈 Total adoptions: 10

🎯 ADOPTION PATTERNS:
  Traditional (Legacy):   3 events ( 30.0%)
  Commons (Flexible):     7 events ( 70.0%)

📊 Status: 🟢 EXCELLENT - Strong commons adoption

============================================================
📊 TRANSITION PATTERNS
============================================================
🔄 Total transitions: 2

  legacy_fixed_term    → flexible_domain     :   2 users

============================================================
📊 CONTEXTUAL INSIGHTS
============================================================
📅 Data generated: 2025-01-27 15:30:45 UTC
⏱️  Analysis window: 14 days

============================================================
📊 RECOMMENDATIONS
============================================================
  ✅ Excellent commons adoption - maintain momentum
  📊 Consider advanced analytics for power distribution
  🔄 2 users transitioned from legacy to commons

============================================================
```

### 3. Run Full Dashboard

```bash
# Generate comprehensive constitutional drift dashboard
cd backend/scripts
python constitutional_drift_dashboard.py

# View the dashboard output
cat constitutional_drift_dashboard_*.json | jq '.metrics.mode_adoption'
```

**Dashboard Output:**
```json
{
  "mode_adoption": {
    "legacy_percentage": 30.0,
    "commons_percentage": 70.0,
    "transitions_count": 2,
    "period_days": 14,
    "status": "excellent"
  }
}
```

## Database Schema

The adoption events are stored in `constitutional_history.db`:

```sql
CREATE TABLE adoption_events (
    timestamp DATETIME,
    user_hash TEXT,        -- Privacy-preserving hash of user ID
    mode TEXT,             -- 'legacy_fixed_term' or 'flexible_domain'
    from_mode TEXT,        -- NULL for new adoptions, populated for transitions
    context JSON           -- Additional metadata (field_id, warnings, etc.)
);
```

## API Endpoints

### Get Adoption Statistics

```bash
# Via API
curl "http://localhost:8000/api/delegations/adoption/stats?days=14"

# Response
{
  "period_days": 14,
  "total_adoptions": 10,
  "mode_counts": {
    "legacy_fixed_term": 3,
    "flexible_domain": 7
  },
  "mode_percentages": {
    "legacy_fixed_term": 30.0,
    "flexible_domain": 70.0
  },
  "transitions": {
    "legacy_fixed_term_to_flexible_domain": 2
  },
  "generated_at": "2025-01-27T15:30:45.123456"
}
```

## Status Indicators

### Adoption Status

- **🟢 EXCELLENT**: >70% commons adoption
- **🟡 GOOD**: >50% commons adoption
- **🟠 FAIR**: >30% commons adoption
- **🔴 NEEDS ATTENTION**: <30% commons adoption

### Constitutional Health

- **Excellent**: Strong transition to commons patterns
- **Good**: Balanced adoption with some commons usage
- **Fair**: Limited commons adoption, needs encouragement
- **Needs Attention**: Low commons adoption, potential drift risk

## Troubleshooting

### No Data Found

```bash
# Check if database exists
ls -la constitutional_history.db

# Check if table exists
sqlite3 constitutional_history.db ".tables"

# Check for adoption events
sqlite3 constitutional_history.db "SELECT COUNT(*) FROM adoption_events;"
```

### API Unavailable

```bash
# Use database directly
python adoption_print_stats.py --no-api

# Check API status
curl http://localhost:8000/health
```

### Permission Issues

```bash
# Make scripts executable
chmod +x backend/scripts/adoption_*.py

# Run with proper Python path
PYTHONPATH=backend python backend/scripts/adoption_seed.py
```

## Integration Points

### Frontend Telemetry

The frontend automatically tracks:
- **Composer Open**: When user opens delegation composer
- **Delegation Created**: When user creates a delegation

### Backend Integration

Telemetry is automatically captured on:
- **Delegation Creation**: Via `POST /api/delegations`
- **Mode Selection**: Tracks which mode was chosen
- **Warning Interactions**: Records if warnings were shown

### Dashboard Integration

The constitutional drift dashboard includes:
- **Mode Adoption Tile**: Shows adoption percentages and status
- **Transition Tracking**: Monitors user journey patterns
- **Health Indicators**: Overall constitutional health assessment

## Privacy & Security

- **User Hashing**: All user IDs are hashed (SHA-256, 16 chars)
- **No PII**: Only mode usage patterns, no personal data
- **Optional Context**: Rich metadata without compromising privacy
- **Local Storage**: Data stays in constitutional_history.db

## Future Enhancements

- **Real-time Dashboard**: Live adoption metrics
- **User Journey Analysis**: Detailed transition patterns
- **Predictive Analytics**: Forecast adoption trends
- **A/B Testing**: Compare different UI approaches
- **Export Capabilities**: CSV/JSON data export
