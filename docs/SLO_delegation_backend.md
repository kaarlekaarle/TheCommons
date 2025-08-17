# Delegation Backend SLOs

This document defines Service Level Objectives (SLOs) for the delegation backend system, focusing on performance, complexity, and maintainability metrics.

## Override Latency SLOs

### Primary Metrics
- **p95 Override Latency**: < 1.5s
- **p99 Override Latency**: < 2.0s
- **Measurement Source**: `collect_override_latency.py` from backend logs and Redis

### Measurement Methodology
1. **Data Collection**: Real override latency metrics from backend logs
2. **Structured Logs**: `{"evt":"override_latency_ms","ms":<int>,"poll_id":...,"user_id":...,"ts":...}`
3. **Redis Fallback**: Rolling list `metrics:override_latency` (capped at 5k entries)
4. **Statistics**: Calculated using `collect_override_latency.py`

### SLO Violation Response
- **Warning**: p95 > 1.2s or p99 > 1.6s
- **Critical**: p95 > 1.5s or p99 > 2.0s
- **Action**: Immediate performance investigation and optimization

## Complexity Ceiling SLOs

### Primary Metrics
- **Flows per Module**: ≤ 5 flows/module for delegation code
- **Measurement Source**: `constitutional_dependency_validator.py`

### Complexity Levels
- **Target**: ≤ 5 flows/module
- **Warning**: 6-7 flows/module
- **Critical**: ≥ 8 flows/module

### Measurement Methodology
1. **File Analysis**: Scan delegation-related files for active flows
2. **Flow Counting**: Count delegation handlers, resolvers, and state machines
3. **Module Boundaries**: Per-file complexity assessment
4. **Remediation**: Actionable refactor tips for high complexity

## Maintainer Concentration SLOs

### Primary Metrics
- **Top Maintainer**: ≤ 75% of delegation commits in 30-day window
- **Minimum Activity**: ≥ 5 commits for analysis validity

### Concentration Levels
- **Target**: ≤ 75% top maintainer
- **Warning**: 75-80% top maintainer
- **Critical**: ≥ 80% top maintainer

### Measurement Methodology
1. **Git History**: 30-day lookback on delegation files
2. **Author Analysis**: Commit count per author
3. **Concentration Calculation**: Top author percentage
4. **Process Nudges**: Pair programming and reviewer swap recommendations

## SLO Monitoring

### Automated Collection
- **Override Latency**: CI job runs `collect_override_latency.py`
- **Complexity**: CI job runs `constitutional_dependency_validator.py`
- **Concentration**: CI job analyzes git history for delegation files

### Reporting
- **SLO Summary**: Posted to CI logs after each collection
- **Artifacts**: `reports/override_latency_stats.json` attached to CI runs
- **Dashboard**: Constitutional drift dashboard shows current SLO status

### Alerting
- **SLO Violations**: Trigger cascade rules B and C (enforce mode)
- **Trend Analysis**: 14-day sparkline shows SLO trend
- **Escalation**: Promote-to-fail conditions for critical violations

## SLO Targets Summary

| Metric | Target | Warning | Critical | Measurement |
|--------|--------|---------|----------|-------------|
| Override Latency p95 | < 1.5s | > 1.2s | > 1.5s | Real backend logs |
| Override Latency p99 | < 2.0s | > 1.6s | > 2.0s | Real backend logs |
| Complexity (flows/module) | ≤ 5 | 6-7 | ≥ 8 | Code analysis |
| Maintainer Concentration | ≤ 75% | 75-80% | ≥ 80% | Git history |

## Remediation Actions

### For Override Latency Violations
1. **Profile override path** for bottlenecks
2. **Optimize database queries** in delegation resolution
3. **Implement caching** for frequently accessed delegation chains
4. **Review async/await patterns** for performance

### For Complexity Violations
1. **Split large modules** into smaller, focused components
2. **Extract delegation handlers** into separate classes
3. **Consolidate similar flows** to reduce duplication
4. **Implement delegation patterns** (factory, state machine, etc.)

### For Maintainer Concentration Violations
1. **Pair programming** with other team members
2. **Reviewer swap** for delegation-related PRs
3. **Knowledge sharing sessions** on delegation system
4. **Document delegation patterns** and best practices

## SLO Review Process

### Weekly Review
- [ ] Review SLO metrics from CI runs
- [ ] Identify trends and patterns
- [ ] Plan remediation actions
- [ ] Update SLO targets if needed

### Monthly Review
- [ ] Analyze SLO effectiveness
- [ ] Review false positive/negative rates
- [ ] Adjust thresholds based on team capacity
- [ ] Plan SLO expansion to other areas

### Quarterly Review
- [ ] Comprehensive SLO performance analysis
- [ ] Team feedback on SLO targets
- [ ] Strategic SLO adjustments
- [ ] Documentation updates
