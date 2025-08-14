# Labels Playbook: Practical Guide

## Adding a New Label Safely

### 1. Development Environment

```bash
# Ensure labels are enabled
export LABELS_ENABLED=true

# Start the server
PYTHONPATH=. uvicorn backend.main:app --reload
```

### 2. Create the Label

```bash
# Create a new label via API
curl -X POST http://localhost:8000/api/labels/ \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"name": "Public Safety", "slug": "public-safety"}'
```

### 3. Verify Creation

```bash
# List all labels
curl -H "Authorization: Bearer $TOKEN" http://localhost:8000/api/labels/
```

### 4. Test Integration

```bash
# Create a poll with the new label
curl -X POST http://localhost:8000/api/polls/ \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Test Proposal",
    "description": "Testing new label",
    "decision_type": "level_b",
    "labels": ["public-safety"]
  }'
```

## Seeding Default Labels

### Using the Seeder Script

```bash
# Run the default seeder
cd backend
python scripts/seed_labels.py
```

### Custom Seeding

```python
# backend/scripts/custom_seed.py
from backend.models.label import Label
from backend.database import get_db
from sqlalchemy.ext.asyncio import AsyncSession

async def seed_custom_labels():
    async for db in get_db():
        labels = [
            {"name": "Transportation", "slug": "transportation"},
            {"name": "Housing", "slug": "housing"},
            {"name": "Education", "slug": "education"},
            # Add more as needed
        ]
        
        for label_data in labels:
            label = Label(**label_data)
            db.add(label)
        
        await db.commit()
```

### Make Targets

```makefile
# Add to Makefile
seed-labels:
	cd backend && python scripts/seed_labels.py

seed-stress: seed-labels
	cd backend && python scripts/seed_stress_polls.py

wipe-dev:
	cd backend && python scripts/wipe_dev_data.py

labels-check-dupes:
	cd backend && python scripts/find_dup_poll_labels.py

labels-fix:
	cd backend && alembic upgrade head
```

## Database Integrity

### Poll-Label Relationship Invariant

The `poll_labels` table maintains a critical invariant: **no duplicate (poll_id, label_id) pairs**. This prevents:
- Duplicate polls appearing in topic pages
- Incorrect count calculations
- React duplicate key warnings in the frontend

### Checking for Duplicates

```bash
# Check for duplicate poll-label relationships
make labels-check-dupes

# This runs: backend/scripts/find_dup_poll_labels.py
# Exits with code 1 if duplicates found, 0 if clean
```

### Fixing Duplicates

```bash
# Remove duplicates and add unique constraint
make labels-fix

# This runs the migration that:
# 1. Deletes duplicate rows (keeping first occurrence)
# 2. Adds UNIQUE(poll_id, label_id) constraint
# 3. Verifies no duplicates remain
```

### Prevention

The unique constraint prevents future duplicates at the database level. The API also includes:
- EXISTS-based queries to avoid row multiplication
- Frontend deduplication as a safety net
- Debug logging when duplicates are detected

## Filtering Lists by Label

### Backend API

```bash
# Filter polls by label
curl "http://localhost:8000/api/polls/?label=mobility"

# Filter with multiple labels (comma-separated)
curl "http://localhost:8000/api/polls/?label=mobility,education"

# Combine with decision type
curl "http://localhost:8000/api/polls/?decision_type=level_b&label=mobility"
```

### Frontend Integration

```typescript
// In React components
const polls = await listPolls({ 
  decision_type: 'level_b', 
  label: 'mobility' 
});

// URL-based filtering
const [searchParams] = useSearchParams();
const labelFilter = searchParams.get('label');
```

### UI Components

```tsx
// LabelFilterBar component
<LabelFilterBar
  activeSlug={searchParams.get('label')}
  onChange={(slug) => setSearchParams(slug ? { label: slug } : {})}
/>

// Individual label chips
<LabelChip
  label={label}
  onClick={(slug) => navigate(`/proposals?label=${slug}`)}
/>
```

## Testing Label-Aware Flows

### 1. Backend Smoke Tests

```bash
# Start server
export LABELS_ENABLED=true
PYTHONPATH=. uvicorn backend.main:app --reload

# Create test user
curl -X POST http://localhost:8000/api/users/ \
  -H "Content-Type: application/json" \
  -d '{"username":"testuser","email":"test@example.com","password":"password123"}'

# Get token
TOKEN=$(curl -s -X POST -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=testuser&password=password123" \
  http://localhost:8000/api/token | jq -r .access_token)

# Test label operations
curl -H "Authorization: Bearer $TOKEN" http://localhost:8000/api/labels/
```

### 2. Frontend Testing

```bash
# Start frontend
cd frontend
VITE_LABELS_ENABLED=true npm run dev
```

### 3. Manual Testing Checklist

- [ ] Labels appear in proposal creation form
- [ ] Labels display on proposal detail pages
- [ ] Label filtering works in proposal lists
- [ ] Label chips navigate to filtered views
- [ ] Dashboard shows label-specific delegations
- [ ] Topics dropdown appears in navigation

### 4. Performance Testing

```bash
# Seed stress data
make seed-stress

# Test list performance
curl "http://localhost:8000/api/polls/?limit=100" | jq length

# Test label selector with many labels
# Verify no lag when typing in search
```

## Troubleshooting

### Common Issues

1. **Labels not appearing**
   - Check `LABELS_ENABLED=true`
   - Verify labels are seeded in database
   - Check browser console for API errors

2. **MissingGreenlet errors**
   - Ensure `lazy="selectin"` is set on relationships
   - Use `selectinload()` in queries
   - Check for proper eager loading

3. **Label filtering not working**
   - Verify label slugs match exactly
   - Check URL encoding for special characters
   - Ensure backend API supports label filtering

4. **Delegation issues**
   - Verify delegation summary includes per-label data
   - Check label_slug vs label_id usage
   - Ensure proper precedence logic

### Debug Commands

```bash
# Check database state
sqlite3 backend/test.db "SELECT * FROM labels;"
sqlite3 backend/test.db "SELECT * FROM poll_labels LIMIT 10;"

# Check API responses
curl -H "Authorization: Bearer $TOKEN" http://localhost:8000/api/delegations/me | jq

# Frontend debugging
# Open browser dev tools and check Network tab for API calls
```

## Best Practices

1. **Label Naming**
   - Use clear, community-focused names
   - Keep slugs URL-safe and consistent
   - Avoid overly specific or temporary labels

2. **Performance**
   - Limit polls to 5 labels maximum
   - Use eager loading for label relationships
   - Consider caching for frequently accessed labels

3. **User Experience**
   - Provide clear visual feedback for label interactions
   - Use consistent styling across label components
   - Ensure keyboard accessibility

4. **Testing**
   - Test with various label combinations
   - Verify delegation precedence with label-specific delegates
   - Test edge cases (no labels, many labels, etc.)
