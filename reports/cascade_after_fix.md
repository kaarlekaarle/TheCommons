# Constitutional Cascade Report

**Generated**: 2025-08-17T19:20:36.769849

## Cascade Summary

```
CASCADE: rule=B, signals=[#2=CRITICAL(1436.287697172077ms)], window=7d, decision=BLOCK, next=reduce_complexity+optimize_latency
```

## Collected Signals

### Signal #2: CRITICAL

- **Type**: Override latency
- **P95**: 1436.287697172077ms
- **P99**: 2260.99424848836ms
- **Cache Hit Rate**: 78.0%
- **Snapshot**: reports/test_override_latency.json (age: 1.2h)

### Signal #3: INFO

- **Type**: Delegation complexity
- **Flows**: 0 in delegations

### Signal #4: CRITICAL

- **Type**: Maintainer concentration
- **Percentage**: 100.0%
- **Commits**: 23

### Signal #5: INFO

- **Type**: Delegation mode distribution
- **Legacy Usage**: 25.0%
- **Meta**: {"mode_distribution": {"legacy_fixed_term": 25, "flexible_domain": 60, "hybrid_seed": 15}, "total_delegations": 100, "transition_health": "moderate"}

## Triggered Cascade Rules

### Rule B

- **Decision**: BLOCK
- **Rationale**: Opacity + complexity
- **Window**: 7 days
