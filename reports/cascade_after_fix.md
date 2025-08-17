# Constitutional Cascade Report

**Generated**: 2025-08-17T17:59:17.550147

## Cascade Summary

```
CASCADE: rule=B, signals=[#2=CRITICAL(2100ms)], window=7d, decision=BLOCK, next=reduce_complexity+optimize_latency
```

## Collected Signals

### Signal #2: CRITICAL

- **Type**: Override latency
- **Value**: 2100ms

### Signal #3: INFO

- **Type**: Delegation complexity
- **Flows**: 0 in delegations

### Signal #4: CRITICAL

- **Type**: Maintainer concentration
- **Percentage**: 100.0%
- **Commits**: 30

### Signal #5: INFO

- **Type**: Delegation mode distribution
- **Legacy Usage**: 25.0%
- **Meta**: {"mode_distribution": {"legacy_fixed_term": 25, "flexible_domain": 60, "hybrid_seed": 15}, "total_delegations": 100, "transition_health": "moderate"}

## Triggered Cascade Rules

### Rule B

- **Decision**: BLOCK
- **Rationale**: Opacity + complexity
- **Window**: 7 days
