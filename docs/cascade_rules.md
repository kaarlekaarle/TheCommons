# Constitutional Cascade Rules

This document describes the cascade rules that escalate certain pairs/clusters of constitutional warnings into hard blockers when they indicate constitutional drift toward hierarchy or opacity.

## WARN Mode Behavior

### Current Status: WARN Mode Active

The cascade system is currently operating in **WARN mode**. In WARN mode:

- **Cascade Detection**: All cascade rules (A, B, C, D) are evaluated normally
- **Decision Logging**: Cascade decisions are stored and reported
- **Non-blocking**: PRs continue unless specific promote-to-fail conditions are met
- **Dashboard Integration**: Cascade tile shows current decision and 14-day sparkline
- **History Tracking**: Cascade events are stored for trend analysis

### Promote-to-Fail Conditions (Even in WARN Mode)

The following red-flag conditions will fail the build even in WARN mode:

1. **Delegation Chain Visibility Regression**
   - Trigger: Any warning containing "delegation chain visibility decreased" with HIGH/CRITICAL severity
   - Keywords: "chain visibility decrease", "transparency drop", "hidden layer", "opacity increase"

2. **Override Latency Regression**
   - Trigger: Signal #2 (override latency) with HIGH/CRITICAL severity and latency ≥1600ms
   - Threshold: 1600ms (tuned from original 2000ms)

### Override Process

To override promote-to-fail conditions:
1. Add `constitutional-override` label to PR
2. Provide emergency justification in PR description
3. 24-hour re-check ticket will be auto-generated

**Valid Override Reasons**: Deployment failures, security patches, critical bug fixes
**Invalid Override Reasons**: Feature requests, performance optimizations, convenience changes

### Remediation Resources

- **Complexity Issues**: See [Complexity Remediation](#complexity-remediation) section
- **Maintainer Spread**: See [Maintainer Concentration](#maintainer-concentration) section
- **Override Latency**: See [Override Latency](#override-latency) section
- **Full Runbook**: See [docs/RUNBOOK_cascade_warn.md](RUNBOOK_cascade_warn.md)

## Decision Matrix

| Rule | Signals | Thresholds | Window | Decision | Rationale |
|------|---------|------------|--------|----------|-----------|
| A | #1 + #4 | #1=CRITICAL, #4≥80% | ≤3d | BLOCK | Formal + informal hierarchy |
| B | #2 + #3 | #2≥1.6s, #3≥7flows | ≤7d | BLOCK | Opacity + complexity |
| C | #3 + #4 | #3≥7flows, #4≥80% | ≤14d | BLOCK | Knowledge silos |
| D | #2 + #4 | #2≥1.6s, #4≥80% | ≤5d | BLOCK | Unresponsive + concentrated |

## Signal Taxonomy

### Signal #1: Super-delegate Pattern (HARD BLOCK)
- **Core Principles**: Anti-hierarchy, Power circulation
- **Philosophical Impact**: Direct violation of anti-hierarchy principle by creating privileged nodes with multiple override authorities, enabling power concentration and hierarchy formation.

### Signal #2: Override Latency > 1.6s (HARD BLOCK)
- **Core Principles**: User intent supremacy, Radical transparency
- **Philosophical Impact**: Erodes user supremacy by making intent overrides too slow to be meaningful, while simultaneously reducing transparency by hiding delegation chains behind delays.

### Signal #3: Delegation API Complexity Ceiling (WARNING)
- **Core Principles**: Power circulation, Anti-hierarchy
- **Philosophical Impact**: High complexity creates maintainer bottlenecks and knowledge silos, concentrating power in fewer hands and making delegation flows harder to understand and audit.

### Signal #4: Maintainer Concentration in Delegation Code (WARNING)
- **Core Principles**: Anti-hierarchy, Power circulation
- **Philosophical Impact**: Single maintainer dominance creates knowledge silos and decision bottlenecks, effectively concentrating power and creating informal hierarchy through expertise monopolization.

## Severity Ladder & Thresholds

### Severity Levels
- **INFO**: No action required, monitoring only
- **WARN**: Warning issued, non-blocking
- **HIGH**: Warning issued, blocks when combined
- **CRITICAL**: Hard block, always blocks

### Numeric Thresholds (Tuned for WARN Mode)

#### Override Latency
- **CRITICAL**: ≥2.0s (hard block)
- **HIGH**: ≥1.6s (blocks when combined) - *tuned from 1.5s*
- **WARN**: ≥1.2s (warning only) - *tuned from 1.0s*
- **INFO**: <1.2s

#### Complexity Ceiling (flows per module)
- **CRITICAL**: ≥8 flows (hard block)
- **HIGH**: ≥7 flows (blocks when combined) - *tuned from 6 flows*
- **WARN**: ≥4 flows (warning only)
- **INFO**: <4 flows

#### Maintainer Concentration
- **CRITICAL**: ≥90% (hard block)
- **HIGH**: ≥80% (blocks when combined) - *tuned from 75%*
- **WARN**: ≥50% (warning only)
- **INFO**: <50%
- **Lookback**: 30 days
- **Minimum Activity**: 5 commits

## Complexity Remediation

When delegation complexity reaches ≥7 flows per module, consider these specific refactors:

1. **Split delegation_manager.py** into routing.py (chain resolution) + interrupts.py (overrides)
2. **Move storage adapters** under delegation/store/ and inject via interface
3. **Collapse duplicate handlers**: merge apply_override + interrupt_vote
4. **Extract delegation state machine** into separate state.py module
5. **Create delegation/validators.py** for chain validation logic

## Maintainer Concentration

When maintainer concentration reaches ≥75% and ≥10 commits in lookback:

- **Pair programming** or **reviewer swap** recommended for next PR on delegation/*
- **Knowledge sharing sessions** on delegation system
- **Document delegation patterns** and best practices
- **Rotate delegation-related tasks** occasionally

## Override Latency

When override latency exceeds thresholds:

1. **Optimize delegation override path**
2. **Review database query performance**
3. **Consider caching strategies**
4. **Profile override resolution logic**
5. **Target**: Reduce p95 latency to <1.5s

## Escalation Logic

### Rule A: (#1 + #4) → BLOCK
- **Required Severities**: #1 = critical, #4 = high (≥80% concentration)
- **Time Window**: Same PR or ≤3 days across PRs
- **Rationale**: Formal hierarchy (super-delegate) combined with informal hierarchy (maintainer concentration) creates a complete power concentration pattern that fundamentally violates anti-hierarchy principles.

### Rule B: (#2 + #3) → BLOCK
- **Required Severities**: #2 = critical (≥2.0s), #3 = high (≥7 flows/module)
- **Time Window**: Same PR or ≤7 days across PRs
- **Rationale**: Slow overrides combined with high complexity create opacity and user disempowerment, making the delegation system effectively non-transparent and non-responsive to user intent.

### Rule C: (#3 + #4) → BLOCK
- **Required Severities**: #3 = high (≥7 flows/module), #4 = high (≥80% concentration)
- **Time Window**: Same PR or ≤14 days across PRs
- **Rationale**: High complexity plus maintainer concentration creates a perfect storm of knowledge silos and power concentration, making delegation flows opaque and unmaintainable.

### Rule D: (#2 + #4) → BLOCK
- **Required Severities**: #2 = high (≥1.6s), #4 = high (≥80% concentration)
- **Time Window**: Same PR or ≤5 days across PRs
- **Rationale**: Slow overrides combined with maintainer concentration suggests the system is becoming opaque and unresponsive, with knowledge bottlenecks preventing quick resolution.

## Temporal Model

### Co-occurrence Windows
- **Same PR**: All signals in single PR trigger immediate evaluation
- **Cross-PR Windows**: 
  - Hierarchy signals (#1, #4): ≤3 days
  - Transparency signals (#2, #3): ≤7 days
  - Mixed signals: ≤5 days

### Anti-Flapping Controls
- **Hysteresis**: Once a cascade block is triggered, require 2 consecutive clean runs to clear
- **Cool-down**: 24-hour minimum between cascade evaluations for same rule
- **Trend Requirement**: For temporal drift, require 3 consecutive measurements above threshold

## Fail-Open vs. Fail-Closed Policy

### Default Policy: Fail-Closed (BLOCK)
- **All cascade rules default to BLOCK** when triggered
- **Conservative approach** protects constitutional principles

### Emergency Override Path
- **Label**: `constitutional-override`
- **Auto-ticket**: Creates ticket with 24-hour re-check requirement
- **Scope**: Infrastructure emergencies only (deployment failures, security patches)
- **Not Allowed**: Feature requests, convenience, performance optimizations
- **Documentation**: Override must include justification and timeline for resolution

## Rollout Plan

### Phase 1: Shadow Mode (Week 1-2)
- Cascade detector runs but doesn't block PRs
- Logs all cascade decisions for analysis
- Collects baseline data on signal patterns

### Phase 2: Warn Mode (Week 3-4) - **CURRENT**
- Cascade detector shows warnings in CI
- **Doesn't block PRs** but alerts developers
- Allows adjustment to thresholds and rules
- Emergency override process available

### Phase 3: Enforce Mode (Week 5+)
- Full cascade blocking enabled
- PRs fail if cascade rules are triggered
- Emergency override process available

## What Happens in WARN Mode?

### Non-Blocking Behavior
- **Cascade rules are evaluated** but do not block PRs
- **Warnings are displayed** in CI logs with clear explanations
- **Reports are generated** (JSON + Markdown) for review
- **Emergency overrides** are still available via `constitutional-override` label

### Developer Experience
- **CASCADE summary line** appears in CI logs
- **Detailed reports** available in `reports/constitutional_cascade.md`
- **Remediation tips** provided for each triggered rule
- **Time to address** issues before enforce mode

### Remediation Process
1. **Review the cascade report** to understand triggered rules
2. **Address underlying issues** using provided remediation tips
3. **Test changes** to ensure cascade rules no longer trigger
4. **Document improvements** for team knowledge sharing

### Example WARN Mode Output
```
🔍 CONSTITUTIONAL CASCADE SUMMARY
=================================

📋 CASCADE: rule=B, signals=[#2=CRITICAL(2100ms), #3=HIGH(7flows)], window=7d, decision=BLOCK, next=reduce_complexity+optimize_latency

❌ CASCADE BLOCK DETECTED
=========================

A cascade rule has been triggered that would block this PR in enforce mode.
Review the cascade report and address the underlying constitutional drift.

📄 Full report: reports/constitutional_cascade.md
📋 Rules documentation: docs/cascade_rules.md
```

## Updated Thresholds (WARN Mode)

### Override Latency
- **CRITICAL**: ≥2.0s (hard block)
- **HIGH**: ≥1.6s (blocks when combined) - *increased from 1.5s*
- **WARN**: ≥1.2s (warning only) - *increased from 1.0s*
- **INFO**: <1.2s

### Complexity Ceiling (flows per module)
- **CRITICAL**: ≥8 flows (hard block)
- **HIGH**: ≥7 flows (blocks when combined) - *increased from 6 flows*
- **WARN**: ≥4 flows (warning only)
- **INFO**: <4 flows

### Maintainer Concentration
- **CRITICAL**: ≥90% (hard block)
- **HIGH**: ≥80% (blocks when combined) - *increased from 75%*
- **WARN**: ≥50% (warning only)
- **INFO**: <50%
- **Lookback**: 30 days
- **Minimum Activity**: 5 commits

## Governance

### Rule Changes
- **Amendment Required**: Changes to core logic, new signal types, principle mapping
- **Routine Tuning**: Threshold adjustments, temporal windows, severity bands
- **Process**: Tuning requires 2-week notice, amendment requires full CEF process

### Integration
- **Phase 5 CDR**: Cascade detector feeds into drift resistance system
- **Phase 6 CEF**: Cascade rules evolve through amendment process
- **Living Mechanism**: Regular review and adaptation as system evolves

## Usage

### Local Testing
```bash
# Shadow mode (default)
CASCADE_MODE=shadow python3 backend/scripts/constitutional_cascade_detector.py --json-out reports/constitutional_cascade.json

# Warn mode
CASCADE_MODE=warn python3 backend/scripts/constitutional_cascade_detector.py --json-out reports/constitutional_cascade.json

# Enforce mode
CASCADE_MODE=enforce python3 backend/scripts/constitutional_cascade_detector.py --json-out reports/constitutional_cascade.json
```

### CI/CD Integration
The cascade detector is automatically integrated into the constitutional amendment workflow:
- Runs after all individual checks
- Respects `CASCADE_MODE` environment variable
- Fails builds in enforce mode when cascade rules are triggered
- Supports emergency override via `constitutional-override` label

### Emergency Override
To override a cascade block in emergency situations:
1. Add `constitutional-override` label to PR
2. Include justification in PR description
3. Auto-ticket will be created for 24-hour re-check
4. Override only valid for infrastructure emergencies
