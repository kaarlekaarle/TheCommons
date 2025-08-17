# Delegation Modes: Transition Philosophy

This document explains the three delegation modes that support the transition from old politics to The Commons while maintaining constitutional protections.

## Overview

The delegation system supports three modes that enable a gradual transition from traditional political delegation patterns to more flexible, domain-specific delegation:

1. **Legacy Fixed-Term** (`legacy_fixed_term`): Old politics pattern with 4-year terms
2. **Flexible Domain** (`flexible_domain`): Commons pattern with per-poll/label/field values  
3. **Hybrid Seed** (`hybrid_seed`): Transition pattern with global fallback + per-field refinement

## Constitutional Principles

All delegation modes maintain these constitutional protections:

- **Revocability**: All delegations are revocable at any time
- **Transparency**: Delegation chains are fully traceable
- **User Override**: Direct user actions stop chain resolution immediately
- **Anti-Hierarchy**: No special authority based on delegation mode

## Mode Details

### Legacy Fixed-Term Mode

**Purpose**: Support users transitioning from traditional political systems

**Characteristics**:
- 4-year maximum term (constitutional limit)
- Always revocable (constitutional principle)
- Auto-expires at term end with renewal nudges
- Default mode for users familiar with traditional politics

**Use Cases**:
- Users new to The Commons
- Traditional political party members
- Users who prefer set terms with automatic renewal

**Example**:
```json
{
  "delegator_id": "user-123",
  "delegatee_id": "user-456", 
  "mode": "legacy_fixed_term",
  "legacy_term_ends_at": "2029-08-17T16:00:00Z"
}
```

### Flexible Domain Mode

**Purpose**: The Commons standard delegation pattern

**Characteristics**:
- Per-poll, per-label, or per-field delegation
- No fixed terms
- Immediate revocation
- Domain-specific expertise matching

**Use Cases**:
- Domain experts delegating specific topics
- Poll-specific delegation
- Label-based delegation
- Field-based delegation

**Example**:
```json
{
  "delegator_id": "user-123",
  "delegatee_id": "user-456",
  "mode": "flexible_domain", 
  "field_id": "climate-policy"
}
```

### Hybrid Seed Mode

**Purpose**: Transition pattern combining global fallback with field refinement

**Characteristics**:
- Global fallback delegation (like legacy)
- Can be overridden by field-specific delegations
- Supports gradual transition to domain-specific delegation
- Maintains comfort of global delegation while enabling refinement

**Use Cases**:
- Users transitioning from legacy to flexible domain
- Users who want global fallback but field-specific expertise
- Gradual adoption of domain-specific delegation

**Example**:
```json
{
  "delegator_id": "user-123",
  "delegatee_id": "user-456",
  "mode": "hybrid_seed"
}
```

## Target Types

Delegations can target different entities:

- **User**: Traditional person-to-person delegation
- **Field**: Domain of expertise (e.g., "climate-policy")
- **Institution**: Organization (e.g., "greenpeace", "world-bank")
- **Value**: Constitutional value as delegate
- **Idea**: Specific idea as delegate
- **Poll**: Poll-specific delegation
- **Label**: Label-specific delegation

## API Examples

### Create Legacy Delegation

```bash
curl -X POST /api/delegations \
  -H "Authorization: Bearer <token>" \
  -d '{
    "delegatee_id": "user-456",
    "mode": "legacy_fixed_term",
    "target": {
      "type": "user",
      "id": "user-456"
    }
  }'
```

### Create Field-Specific Delegation

```bash
curl -X POST /api/delegations \
  -H "Authorization: Bearer <token>" \
  -d '{
    "delegatee_id": "user-456",
    "mode": "flexible_domain",
    "target": {
      "type": "field", 
      "id": "climate-policy"
    }
  }'
```

### Create Hybrid Delegation

```bash
curl -X POST /api/delegations \
  -H "Authorization: Bearer <token>" \
  -d '{
    "delegatee_id": "user-456",
    "mode": "hybrid_seed",
    "target": {
      "type": "user",
      "id": "user-456"
    }
  }'
```

### Get Delegation Modes

```bash
curl -X GET /api/delegations/modes \
  -H "Authorization: Bearer <token>"
```

Response:
```json
{
  "modes": {
    "legacy_fixed_term": {
      "enabled": true,
      "description": "Old politics: 4-year term, always revocable",
      "max_term_years": 4,
      "default_term_years": 4
    },
    "flexible_domain": {
      "enabled": true,
      "description": "Commons: per-poll/label/field values",
      "default": true
    },
    "hybrid_seed": {
      "enabled": true,
      "description": "Hybrid: global fallback + per-field refinement"
    }
  },
  "targets": {
    "user": {"enabled": true},
    "field": {"enabled": true},
    "institution": {"enabled": true},
    "value": {"enabled": true},
    "idea": {"enabled": true}
  }
}
```

## Chain Resolution

Delegation chains are resolved with these priorities:

1. **User Override**: Direct user actions stop chain immediately
2. **Target-Specific**: Field/poll/label-specific delegations
3. **Hybrid Seed**: Global fallback delegations
4. **Flexible Domain**: General domain delegations

### Example Chain Resolution

```
User A -> User B (hybrid_seed, global)
User A -> User C (flexible_domain, climate-policy)

For climate policy: User A -> User C (field-specific wins)
For other topics: User A -> User B (global fallback)
```

## Transition Guidance

### From Legacy to Hybrid

1. Create hybrid seed delegation with trusted delegatee
2. Add field-specific delegations for expertise areas
3. Monitor and refine field delegations over time
4. Eventually transition to flexible domain mode

### From Hybrid to Flexible Domain

1. Identify domains where you want specific expertise
2. Create field-specific delegations
3. Remove hybrid seed delegation when comfortable
4. Use flexible domain mode for new delegations

## Constitutional Safeguards

### Revocability

All delegations are revocable regardless of mode:

```bash
curl -X POST /api/delegations/{delegation_id}/revoke \
  -H "Authorization: Bearer <token>"
```

### Transparency

All delegation chains are traceable:

```bash
curl -X GET /api/delegations/my \
  -H "Authorization: Bearer <token>"
```

### User Override

Direct user actions (votes, comments, etc.) stop delegation chain resolution immediately, ensuring user intent supremacy.

## Monitoring and Telemetry

### Adoption Tracking

Track mode adoption over time:

```bash
curl -X GET /api/delegations/telemetry/adoption \
  -H "Authorization: Bearer <token>"
```

### Health Metrics

- Legacy mode usage percentage
- Hybrid mode adoption rate
- Transition health assessment
- User satisfaction metrics

## Best Practices

1. **Start with Legacy**: Use legacy mode for users new to The Commons
2. **Gradual Transition**: Move to hybrid mode when comfortable
3. **Field Expertise**: Use flexible domain mode for domain-specific expertise
4. **Regular Review**: Periodically review and adjust delegations
5. **User Education**: Help users understand the benefits of each mode

## Troubleshooting

### Common Issues

**Legacy delegation expired**: Create new delegation or transition to hybrid mode

**Chain resolution confusion**: Check for user overrides and target-specific delegations

**Mode transition issues**: Ensure constitutional protections are maintained

### Support

For questions about delegation modes:
- Check the API documentation
- Review constitutional principles
- Contact the development team
