# Cascade WARN Mode Runbook

## Overview

This runbook covers the operation of the Constitutional Cascade system in WARN mode. In WARN mode, cascade decisions are logged and reported but do not block PRs unless specific red-flag conditions are met.

## WARN Mode Behavior

### What Happens in WARN Mode

1. **Cascade Detection**: All cascade rules (A, B, C, D) are evaluated normally
2. **Decision Logging**: Cascade decisions are stored in `reports/constitutional_cascade.json`
3. **Ledger Integration**: Cascade decisions are ingested into the warnings ledger
4. **History Storage**: Cascade events are stored in the constitutional history database
5. **Dashboard Display**: Cascade tile shows current decision and 14-day sparkline
6. **Non-blocking**: PRs continue unless promote-to-fail conditions are triggered

## Selective Enforce Mode

### Per-Rule Mode Overrides

The cascade system now supports selective enforcement where individual rules can be in different modes:

- **Rules B & C**: ENFORCE mode (block PRs when triggered)
- **Rules A & D**: WARN mode (log warnings but don't block)

### Configuration

The selective enforcement is configured in `backend/config/constitutional_cascade_rules.json`:

```json
{
  "mode": "warn",
  "mode_overrides": {
    "B": "enforce",
    "C": "enforce", 
    "A": "warn",
    "D": "warn"
  }
}
```

### What Developers See

#### Rule B/C Block (Enforce Mode)
```
❌ CASCADE BLOCK DETECTED
=========================

A cascade rule has been triggered that blocks this PR.
Review the cascade report and address the underlying constitutional drift.

📄 Full report: reports/constitutional_cascade.md
📋 Rules documentation: docs/cascade_rules.md

🔒 BUILD FAILED - Rule B/C triggered in enforce mode
```

#### Rule A/D Warning (Warn Mode)
```
⚠️  CASCADE WARNINGS DETECTED
============================

Cascade warnings detected. Review and consider addressing before enforce mode.

📄 Full report: reports/constitutional_cascade.md
📋 Rules documentation: docs/cascade_rules.md

✅ BUILD CONTINUES - Rule A/D triggered in warn mode
```

### Emergency Override

The `constitutional-override` label remains available for emergency situations:

1. **Add Label**: Add `constitutional-override` label to PR
2. **Provide Justification**: Explain the emergency in PR description
3. **24h Re-check**: A ticket will be auto-generated for 24-hour re-check

**Override Behavior**:
- **Enforce Mode Rules**: Override bypasses the block but generates re-check ticket
- **Warn Mode Rules**: Override has no effect (warnings don't block anyway)

### Dashboard Display

The cascade tile now shows enforce badges:

```
🔴 Cascade Decisions: BLOCK
   Triggered Rules: Rule B [ENFORCED], Rule C [ENFORCED]
   Rule Modes: A[WARN] B[ENFORCED] C[ENFORCED] D[WARN]
📅 Last Updated: 2025-08-17 14:37
📈 14-Day Trend: ░░░░░░░░░░░░░▄
   Events: 2 WARN/BLOCK in 14 days
```

### Testing Selective Enforcement

Run the cascade smoke tests to verify selective enforcement:

```bash
# Manual dispatch in GitHub Actions
# Or run locally:
./scripts/cascade_smoke.sh
```

**Expected Results**:
- ✅ Rule B: BLOCK (exit code 10) - enforce mode
- ✅ Rule C: BLOCK (exit code 10) - enforce mode  
- ✅ Rule A: WARN (exit code 8) - warn mode
- ✅ Rule D: WARN (exit code 8) - warn mode

### Reading the CASCADE Line

The CASCADE line appears in CI logs and follows this format:

```
CASCADE: rule=B, signals=[#2=CRITICAL(2100ms), #3=HIGH(7flows)], window=7d, decision=BLOCK, next=reduce_complexity+optimize_latency
```

**Components:**
- `rule=B`: Triggered cascade rule (A, B, C, or D)
- `signals=[...]`: List of signals that triggered the rule
- `window=7d`: Time window for the cascade evaluation
- `decision=BLOCK`: Cascade decision (OK, WARN, or BLOCK)
- `next=...`: Recommended next actions

### Cascade Rules Reference

| Rule | Signals | Window | Decision | Rationale |
|------|---------|--------|----------|-----------|
| A | #1 + #4≥HIGH | 3 days | BLOCK | Formal + informal hierarchy |
| B | #2≥CRITICAL + #3≥HIGH | 7 days | BLOCK | Opacity + complexity |
| C | #3≥HIGH + #4≥HIGH | 14 days | BLOCK | Knowledge silos |
| D | #2≥HIGH + #4≥HIGH | 5 days | BLOCK | Unresponsive + concentrated |

## Promote-to-Fail Conditions

Even in WARN mode, the following red-flag conditions will fail the build:

### 1. Delegation Chain Visibility Regression
- **Trigger**: Any warning containing "delegation chain visibility decreased" with HIGH/CRITICAL severity
- **Keywords**: "chain visibility decrease", "transparency drop", "hidden layer", "opacity increase"
- **Action**: Build fails with exit code 20

### 2. Override Latency Regression
- **Trigger**: Signal #2 (override latency) with HIGH/CRITICAL severity and latency ≥1600ms
- **Threshold**: 1600ms (configurable)
- **Action**: Build fails with exit code 20

### Override Process

To override promote-to-fail conditions:

1. **Add Label**: Add `constitutional-override` label to PR
2. **Provide Justification**: Explain the emergency in PR description
3. **24h Re-check**: A ticket will be auto-generated for 24-hour re-check

**Valid Override Reasons:**
- Deployment failures
- Security patches
- Critical bug fixes

**Invalid Override Reasons:**
- Feature requests
- Performance optimizations
- Convenience changes

## Dashboard Interpretation

### Cascade Tile
```
🔴 Cascade Decisions: BLOCK
   Triggered Rules: Rule B, Rule C
📅 Last Updated: 2025-08-17 14:37
📈 14-Day Trend: ░░░░░░░░░░░░░▄
   Events: 1 WARN/BLOCK in 14 days
```

**Status Indicators:**
- 🟢 OK: No cascade rules triggered
- 🟡 WARN: Cascade warnings detected
- 🔴 BLOCK: Cascade rules triggered (would block in enforce mode)

### Sparkline Interpretation
- `░`: No events on that day
- `▄`: Low activity (1-2 events)
- `█`: High activity (3+ events)

## Remediation Actions

### For Complexity Issues (≥7 flows/module)
1. **Split delegation_manager.py** into routing.py (chain resolution) + interrupts.py (overrides)
2. **Move storage adapters** under delegation/store/ and inject via interface
3. **Collapse duplicate handlers**: merge apply_override + interrupt_vote
4. **Extract delegation state machine** into separate state.py module
5. **Create delegation/validators.py** for chain validation logic

### For Maintainer Concentration (≥75%)
1. **Pair programming** with other team members
2. **Reviewer swap** for delegation-related PRs
3. **Knowledge sharing sessions** on delegation system
4. **Document delegation patterns** and best practices

### For Override Latency Issues (≥1600ms)
1. **Optimize delegation override path**
2. **Review database query performance**
3. **Consider caching strategies**
4. **Profile override resolution logic**

## Monitoring and Alerts

### Daily Review Checklist
- [ ] Check cascade dashboard for new decisions
- [ ] Review 14-day sparkline trends
- [ ] Address any promote-to-fail conditions
- [ ] Monitor complexity and maintainer concentration

### Weekly Threshold Tuning
- [ ] Review false positive/negative rates
- [ ] Adjust latency thresholds if needed
- [ ] Update complexity ceilings based on team capacity
- [ ] Evaluate maintainer concentration trends

### Monthly Health Review
- [ ] Analyze cascade rule effectiveness
- [ ] Review constitutional drift patterns
- [ ] Update remediation strategies
- [ ] Plan enforce mode transition

## Troubleshooting

### Common Issues

**Cascade tile shows "No cascade data available"**
- Check if `reports/constitutional_cascade.json` exists
- Verify cascade detector ran successfully
- Check file permissions and paths

**Sparkline shows no events**
- Verify cascade events are being stored in history database
- Check constitutional_history.py --store-cascade execution
- Ensure database schema is correct

**Promote-to-fail not triggering**
- Verify warnings ledger contains expected data
- Check severity levels match promote-to-fail criteria
- Ensure signal #2 has correct latency values

### Debug Commands

```bash
# Check cascade data
cat reports/constitutional_cascade.json

# View warnings ledger
cat reports/constitutional_warnings.json

# Test promote-to-fail
python3 scripts/promote_to_fail.py --warnings reports/constitutional_warnings.json

# Check cascade history
python3 backend/scripts/constitutional_history.py --days 14

# Run dashboard
python3 backend/scripts/constitutional_drift_dashboard.py
```

## Transition to Enforce Mode

When ready to transition to enforce mode:

1. **Update CASCADE_MODE**: Set to "enforce" in workflow
2. **Monitor Impact**: Watch for legitimate blocks
3. **Adjust Thresholds**: Fine-tune based on enforce mode data
4. **Team Training**: Ensure all developers understand cascade rules
5. **Documentation**: Update this runbook for enforce mode

## Emergency Procedures

### Immediate Cascade Block
If cascade blocks are preventing critical deployments:

1. **Use constitutional-override label**
2. **Document emergency in PR description**
3. **Create 24h re-check ticket**
4. **Address root cause within 24 hours**

### System Failure
If cascade system is not functioning:

1. **Check CI logs for errors**
2. **Verify all required files exist**
3. **Test cascade detector locally**
4. **Contact constitutional enforcement team**

## Support and Contacts

- **Constitutional Enforcement Team**: @alice @bob @charlie
- **Documentation**: docs/cascade_rules.md
- **Dashboard**: reports/constitutional_cascade.md
- **History**: constitutional_history.db
