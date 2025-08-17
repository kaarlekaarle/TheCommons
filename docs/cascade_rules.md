# Constitutional Cascade Rules

This document describes the cascade rules that monitor constitutional compliance and trigger warnings or blocks when certain thresholds are exceeded.

## Rule B: Opacity + Complexity

Rule B monitors delegation system complexity and performance to prevent opacity and maintain constitutional principles.

### Signal #2: Override Latency
- **Metric**: P95 latency for override resolution
- **Thresholds**:
  - WARN: > 1.5s
  - CRITICAL: > 2.0s
- **Data Source**: `reports/override_latency.json`
- **Staleness Guard**: Data older than 48h is marked as STALE and non-blocking

### Signal #3: Delegation Complexity
- **Metric**: Flow count per module
- **Thresholds**:
  - WARN: > 5 flows per module
  - CRITICAL: > 7 flows per module
- **Data Source**: `reports/complexity_stats.json`
- **Scope**: Production code only (test files excluded by default)
- **Test Files**: Excluded from WARN/BLOCK logic to prevent false signals
  - Pattern: `**/tests/**, test_*.py, *_test.py, **/reports/**`
  - Use `--include-tests` flag for diagnostic analysis only

### Signal #4: Maintainer Concentration
- **Metric**: Percentage of commits by top maintainer
- **Thresholds**:
  - WARN: > 50%
  - CRITICAL: > 80%
- **Lookback**: 30 days
- **Scope**: Production code only (test files excluded by default)

### Signal #5: Delegation Mode Distribution
- **Metric**: Percentage of legacy fixed-term delegations
- **Thresholds**:
  - WARN: > 30%
  - CRITICAL: > 50%
- **Target**: < 20% hybrid mode adoption

## Rule A: Hierarchy Prevention

Rule A monitors for super-delegate patterns that could create hierarchical structures.

### Signal #1: Super-Delegate Detection
- **Metric**: Number of users delegating to a single user
- **Thresholds**:
  - WARN: > 3 delegations to same user
  - CRITICAL: > 5 delegations to same user

## Rule C: Knowledge Concentration

Rule C monitors for knowledge concentration in specific domains.

## Rule D: Performance Degradation

Rule D monitors overall system performance degradation.

## Cascade Decision Matrix

| Rule | WARN Mode | BLOCK Mode |
|------|-----------|------------|
| A    | Signal #1 ≥ WARN | Signal #1 = CRITICAL |
| B    | Signal #2 ≥ WARN OR Signal #3 ≥ WARN | Signal #2 = CRITICAL OR Signal #3 = CRITICAL |
| C    | Signal #4 ≥ WARN | Signal #4 = CRITICAL |
| D    | Signal #5 ≥ WARN | Signal #5 = CRITICAL |

## Complexity Analysis Notes

- **Production Focus**: Complexity analysis focuses on production code to avoid false signals from test complexity
- **Test Exclusion**: Test files are automatically excluded from flow counting
- **Diagnostic Mode**: Use `--include-tests` flag for comprehensive analysis including tests
- **File Patterns**: Test files match patterns: `/tests/`, `test_`, `_test.py`, `/reports/`
- **JSON Output**: Includes `counted_files` and `excluded_tests` counts for transparency
