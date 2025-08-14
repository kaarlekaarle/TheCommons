# Topic Labels: Connective Tissue Between Values and Actions

## What Are Labels?

Topic Labels are **controlled, flat categories** that serve as connective tissue between Level A (Principles) and Level B (Actions) decisions. They're not arbitrary tags—they're **delegation drivers** and **relationship surfaces** that help users understand how immediate actions connect to long-term values.

### Why Labels Exist

1. **A↔B Linkage**: Labels surface the relationship between "what we value" (Level A) and "what we do" (Level B)
2. **Delegation Scoping**: Users can delegate by topic area, not just globally
3. **Discoverability**: Find related proposals across decision levels
4. **Context Preservation**: Understand the broader principles behind specific actions

## Data Model

### Core Entities

```sql
-- Labels table
CREATE TABLE labels (
    id UUID PRIMARY KEY,
    name VARCHAR(40) UNIQUE NOT NULL,  -- "Environmental Protection"
    slug VARCHAR(40) UNIQUE NOT NULL,  -- "environmental-protection"
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP,
    updated_at TIMESTAMP
);

-- Many-to-many association
CREATE TABLE poll_labels (
    poll_id UUID REFERENCES polls(id) ON DELETE CASCADE,
    label_id UUID REFERENCES labels(id) ON DELETE CASCADE,
    UNIQUE(poll_id, label_id)
);

-- Extended delegations
CREATE TABLE delegations (
    -- ... existing fields ...
    label_id UUID REFERENCES labels(id) ON DELETE SET NULL,  -- NULL = global
    UNIQUE(delegator_id, label_id)  -- One per label per user
);
```

### Key Relationships

- **Poll ↔ Label**: Many-to-many via `poll_labels`
- **Delegation ↔ Label**: One-to-many (delegation can be global or label-specific)
- **User → Delegation**: One-to-many (user can have multiple label-specific delegations)

## Delegation Precedence

When calculating effective votes, the system follows this precedence:

1. **Direct Vote** - User voted directly on the proposal
2. **Label-Specific Delegate** - User delegated this topic to someone
3. **Global Delegate** - User has a global delegate (no label-specific)
4. **Follow-Delegation** - User chose to follow their delegate's delegation
5. **True Abstain** - No delegation path found

### Example Flow

```
User Alice → Label "environment" → User Bob → Label "climate" → User Carol → Direct Vote
```

## API Surfaces

### Labels Management

```http
GET /api/labels/                    # List active labels
POST /api/labels/                   # Create (admin only)
PATCH /api/labels/{id}              # Update (admin only)
```

### Poll Integration

```http
POST /api/polls/                    # Create with labels: ["mobility", "education"]
GET /api/polls/?label=mobility      # Filter by label
GET /api/polls/{id}                 # Returns poll with labels array
```

### Delegation

```http
POST /api/delegations/              # Set delegation with label_slug
GET /api/delegations/me             # Summary with per-label delegates
```

## Feature Flags

### Backend
```bash
LABELS_ENABLED=true                 # Enable label system
ALLOW_PUBLIC_LABELS=false           # Restrict label creation to admins
```

### Frontend
```bash
VITE_LABELS_ENABLED=true           # Show label UI components
VITE_ALLOW_PUBLIC_LABELS=false     # Control label creation access
```

## Why Not Arbitrary Tags?

Labels are **controlled categories** rather than free-form tags because:

1. **Delegation Semantics**: Label-specific delegation requires consistent, predictable categories
2. **A↔B Relationships**: Meaningful connections require shared vocabulary
3. **User Experience**: Too many tags create noise; controlled set provides focus
4. **Performance**: Bounded set enables efficient indexing and caching
5. **Governance**: Labels represent community priorities, not personal preferences

## Eager Loading Rationale

The label system uses `lazy="selectin"` and `selectinload()` to prevent async `MissingGreenlet` errors:

```python
# Models
labels = relationship("Label", secondary="poll_labels", lazy="selectin")

# API
poll = await db.execute(
    select(Poll).options(selectinload(Poll.labels)).where(Poll.id == poll_id)
)
```

**Why**: Pydantic serialization triggers lazy loading, which fails in async contexts. Eager loading ensures all related data is fetched in a single query.

## Default Labels

The system seeds these default labels:
- environment, mobility, governance, budget, education, health, housing

These represent common community decision areas and provide a foundation for delegation patterns.

## Performance Considerations

- **Indexing**: `idx_label_slug`, `idx_poll_labels_poll`, `idx_poll_labels_label`
- **Eager Loading**: Prevents N+1 queries during serialization
- **Bulk Operations**: Association inserts use `insert()` for efficiency
- **Caching**: Labels are relatively static and good candidates for caching

## Security & Access Control

- **Label Creation**: Admin-only by default, configurable via `ALLOW_PUBLIC_LABELS`
- **Delegation**: Users can only set delegations for themselves
- **Poll Labels**: Validated against existing labels, max 5 per poll
- **API Rate Limiting**: Standard rate limits apply to label operations
