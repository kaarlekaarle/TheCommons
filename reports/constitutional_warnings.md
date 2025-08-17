# Constitutional Warnings Ledger

Generated: 2025-08-17T14:01:48.897321

## Summary

- **Total Warnings**: 11
- **Warnings Touching Core Principles**: 4
- **Promote-to-Fail Candidates**: 1

### Breakdown by Phase
- Phase 5.5: 7 warnings
- Phase 6.3: 1 warnings
- Phase 6.4: 3 warnings

### Breakdown by Category
- Alert Fatigue: 2 warnings
- Community Impact: 1 warnings
- Cultural Drift: 1 warnings
- Implementation Complexity: 1 warnings
- Maintainer Burden: 1 warnings
- Philosophical Integrity: 1 warnings
- Recommendation: 2 warnings
- Shortcut Accumulation: 1 warnings
- Transparency Erosion: 1 warnings

### Breakdown by Severity
- High: 1 warnings
- Medium: 6 warnings
- Warning: 4 warnings

## Top Recurring Warnings
- Alert Fatigue drift detected (1 occurrences)
- Shortcut Accumulation drift detected (1 occurrences)
- Cultural Drift drift detected (1 occurrences)
- drift_detection recommendation (1 occurrences)
- transparency_dashboard recommendation (1 occurrences)

## Owners with Highest Open Warning Load
- : 5 open warnings
- @alice: 1 open warnings
- @charlie: 1 open warnings
- @diana: 1 open warnings
- @team: 1 open warnings

## Recommended Actions

### Promote to Fail
- **Delegation chain visibility decreased**: Touches power_circulation, transparency - consider promoting from medium to critical

### General Recommendations
- Add CI guards for high-frequency warnings
- Set sunset dates for warnings older than 30 days
- Instrument telemetry for override latency and transparency scores
- Review maintainer concentration metrics
- Implement delegation chain visibility monitoring
- Add automated hierarchy detection in CI/CD

## All Warnings

| Timestamp | Phase | Component | Category | Severity | Summary | Status | Core Principles |
|-----------|-------|-----------|----------|----------|---------|--------|-----------------|
| 2025-08-17T14:02:48 | 6.4 | constitutional_dependency_validator | maintainer_burden | warning | High maintainer concentration in delegation module | open | delegation_concentration |
| 2025-08-17T13:51:59 | 5.5 | cdr_integration_cli | alert_fatigue | high | Alert Fatigue drift detected | open |  |
| 2025-08-17T13:51:59 | 5.5 | cdr_integration_cli | shortcut_accumulation | medium | Shortcut Accumulation drift detected | open |  |
| 2025-08-17T13:51:59 | 5.5 | cdr_integration_cli | cultural_drift | medium | Cultural Drift drift detected | open |  |
| 2025-08-17T13:51:59 | 5.5 | cdr_integration_cli | recommendation | medium | drift_detection recommendation | open |  |
| 2025-08-17T13:51:59 | 5.5 | cdr_integration_cli | recommendation | medium | transparency_dashboard recommendation | open |  |
| 2025-08-17T13:02:48 | 5.5 | constitutional_alert_governance | alert_fatigue | medium | Constitutional alert response rate declining | open |  |
| 2025-08-17T11:02:48 | 6.4 | constitutional_principle_matrix | philosophical_integrity | warning | Potential hierarchy introduction in delegation flo... | open | anti_hierarchy, delegation_concentration |
| 2025-08-17T08:02:48 | 5.5 | constitutional_drift_detector | transparency_erosion | medium | Delegation chain visibility decreased | open | power_circulation, transparency |
| 2025-08-16T14:02:48 | 6.3 | constitutional_feasibility_validator | implementation_complexity | warning | High complexity in delegation chain resolution | in-progress |  |
| 2025-08-15T14:02:48 | 6.4 | constitutional_dependency_validator | community_impact | warning | Complexity increased for Delegation API surface | open | delegation_concentration |
