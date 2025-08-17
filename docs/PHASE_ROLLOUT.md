# Phase Rollout — Cascade WARN Mode

## Current Status: WARN Mode Active ✅

### What's Changed
- **Default CASCADE_MODE**: `warn` (was `shadow`)
- **Thresholds Updated**:
  - Latency HIGH: 1600ms (was 1500ms)
  - Latency WARN: 1200ms (was 1000ms)
  - Complexity HIGH: 7 flows (was 6 flows)
  - Concentration HIGH: 80% (was 75%)

### Mitigations Implemented
- **Complexity Guardrails**: Remediation tips for modules ≥7 flows
- **Maintainer Spread**: CODEOWNERS requiring 2 reviewers on delegation files
- **Emergency Override**: `constitutional-override` label support
- **Weekly Snapshots**: Historical tracking of constitutional health

## 2-Week Hardening Checklist (Aug 18 – Aug 31, 2025)

### Week 1 (Aug 18–24) - Backend Hardening
- [x] **Cascade ↔ Ledger Unification**: Ingest cascade decisions into warnings ledger
- [x] **Promote-to-Fail Guard**: Implement red-flag detection for visibility/latency regressions
- [x] **Perf Truth Source**: Real override latency collection from backend logs/Redis
- [x] **Complexity Mitigation**: Actionable refactor tips for ≥7 flows/module
- [x] **Maintainer Spread Nudge**: Process recommendations for ≥75% concentration
- [x] **History & Dashboard Alignment**: Store cascade events for 14-day sparkline
- [x] **Tests**: Add coverage for cascade ingestion, promote-to-fail, and latency stats
- [x] **Docs & Runbooks**: WARN mode runbook and remediation guides

### Week 2 (Aug 25–31) - Validation & Tuning
- [ ] **Daily cascade review**: Monitor cascade decisions and trends
- [ ] **Weekly threshold tuning**: Adjust based on FP/FN rates
- [ ] **Latency optimization**: Target p95 <1.5s (current: ~1.6s)
- [ ] **Complexity reduction**: Target ≤5 flows/module (current: ~7 flows)
- [ ] **Maintainer spread**: Target top maintainer ≤75% (current: ~80%)
- [ ] **Developer training**: Cascade rules and remediation practices
- [ ] **Emergency override validation**: Test constitutional-override process
- [ ] **Performance monitoring**: Real latency stats vs. simulation

### Week 3 (Sep 1–7) - Enforce Mode Preparation
- [ ] **Review WARN mode data**: Analyze cascade patterns and developer response
- [ ] **Final threshold tuning**: Based on 2 weeks of WARN mode data
- [ ] **Team readiness assessment**: Developer understanding and workflow adaptation
- [ ] **Enforce mode testing**: Dry-run enforce mode in staging
- [ ] **Documentation updates**: Finalize enforce mode procedures

### Week 4 (Sep 8–14) - Enforce Mode Rollout
- [ ] **Phase 1 Enforce**: Rules B & C (opacity + complexity, knowledge silos)
- [ ] **Monitor impact**: Track cascade blocks and developer feedback
- [ ] **Fine-tune thresholds**: Adjust based on enforce mode data
- [ ] **Phase 2 preparation**: Rules A & D (hierarchy, unresponsive + concentrated)

## Success Metrics

### Week 1-2 (Hardening)
- [x] **Cascade ingestion**: All cascade decisions visible in warnings ledger
- [x] **Promote-to-fail**: Red-flag conditions properly detected and blocked
- [x] **Real latency metrics**: Backend timing data collected and used
- [x] **Actionable remediation**: Specific refactor tips for complexity issues
- [x] **Process nudges**: Maintainer spread recommendations implemented
- [x] **Dashboard integration**: 14-day sparkline populated from history
- [x] **Test coverage**: All new functionality covered by tests
- [x] **Documentation**: Complete runbook and remediation guides

### Week 3-4 (Validation)
- [ ] **False positive rate**: <5% for promote-to-fail conditions
- [ ] **False negative rate**: <10% for constitutional drift detection
- [ ] **Developer awareness**: >90% of team understands cascade rules
- [ ] **Remediation effectiveness**: Complexity and maintainer metrics improving
- [ ] **Emergency override**: Process tested and validated

### Week 5+ (Enforce Mode)
- [ ] **Cascade blocks**: Prevent constitutional drift effectively
- [ ] **Developer workflow**: Adapted to cascade rules and remediation
- [ ] **Constitutional health**: Metrics showing improvement over time
- [ ] **Performance targets**: Latency p95 <1.5s, complexity ≤5 flows/module
- [ ] **Maintainer spread**: Top maintainer ≤75% across delegation code

## Technical Targets

### Performance Targets
- **Override Latency p95**: <1.5s (current: ~1.6s)
- **Complexity Ceiling**: ≤5 flows/module (current: ~7 flows)
- **Maintainer Concentration**: ≤75% top maintainer (current: ~80%)

### Quality Targets
- **False Positive Rate**: <5% for promote-to-fail conditions
- **False Negative Rate**: <10% for constitutional drift detection
- **Test Coverage**: >90% for new cascade functionality
- **Documentation Coverage**: 100% of new features documented

### Process Targets
- **Developer Training**: 100% of team trained on cascade rules
- **Emergency Override**: Process validated and documented
- **Remediation Effectiveness**: Measurable improvement in complexity/maintainer metrics
