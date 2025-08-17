# Phase 3: Delegation Constitutional Test Suite

## Overview

This directory contains the comprehensive test suite for the Delegation Constitution (Phase 1 + Phase 2) implementation. The test suite ensures that all constitutional guardrails are properly enforced and tested.

## Test Structure

### 1. Circulation & Decay (`test_circulation_decay.py`)
Tests that power must circulate, no permanents, and delegation decay mechanisms.

**Test Functions:**
- `test_revocation_immediate_effect` - Tests immediate revocation capability
- `test_revocation_chain_break` - Tests chain termination on revocation
- `test_delegation_auto_expires` - Tests automatic expiry based on end_date
- `test_dormant_reconfirmation_required` - Tests dormant delegation reconfirmation
- `test_no_permanent_flag_in_schema` - Verifies no permanent delegation flags exist

**Status:** ✅ Basic revocation tests pass, ⚠️ Expiry/decay features need implementation

### 2. Values-as-Delegates (`test_values_delegates.py`)
Tests that people, values, and ideas are equally supported as delegation targets.

**Test Functions:**
- `test_delegate_to_person` - Tests delegation to users (existing functionality)
- `test_delegate_to_value` - Tests delegation to value/principle entities
- `test_delegate_to_idea` - Tests delegation to idea/proposal entities
- `test_single_table_for_all_types` - Tests unified schema for all delegation types
- `test_flow_resolves_across_types` - Tests cross-type delegation resolution

**Status:** ✅ Person delegation works, ❌ Values/ideas delegation needs implementation

### 3. Interruption & Overrides (`test_interruptions.py`)
Tests that user intent always wins, instantly, and overrides delegation.

**Test Functions:**
- `test_user_override_trumps_delegate` - Tests user vote overrides delegation
- `test_override_mid_chain` - Tests override during chain resolution
- `test_last_second_override` - Tests race condition handling
- `test_chain_termination_immediate` - Tests instant chain termination
- `test_race_condition_override` - Tests concurrent override scenarios
- `test_no_phantom_votes` - Tests phantom vote prevention

**Status:** ❌ Override logic needs implementation

### 4. Anti-Hierarchy & Feedback (`test_anti_hierarchy.py`)
Tests that prevent concentration, repair loops, and provide feedback nudges.

**Test Functions:**
- `test_alert_on_high_concentration` - Tests concentration monitoring (>5% alerts)
- `test_soft_cap_behavior` - Tests soft cap enforcement
- `test_loop_detection` - Tests circular delegation detection
- `test_auto_repair_loops` - Tests automatic loop breaking
- `test_feedback_nudges_via_api` - Tests feedback nudge delivery

**Status:** ✅ Loop detection works, ❌ Concentration monitoring and feedback need implementation

### 5. Transparency & Anonymity (`test_transparency_anonymity.py`)
Tests that ensure full trace visibility with optional identity masking.

**Test Functions:**
- `test_full_chain_exposed` - Tests complete delegation chain visibility
- `test_no_hidden_layers` - Tests no invisible delegation layers
- `test_anonymous_delegation` - Tests anonymous delegation flows
- `test_identity_blind_api_mode` - Tests identity-blind API functionality

**Status:** ✅ Chain visibility works, ❌ Anonymity features need implementation

### 6. Constitutional Compliance (`test_constitutional_compliance.py`)
Meta-tests that ensure no bypasses exist and all constitutional principles are enforced.

**Test Functions:**
- `test_no_schema_bypass` - Tests no schema bypasses exist
- `test_no_api_bypass` - Tests no API bypasses exist
- `test_all_guardrails_have_tests` - Meta-test ensuring all guardrails are tested
- `test_regression_on_guardrails` - Tests regression prevention

**Status:** ✅ Schema validation works, ❌ Comprehensive bypass testing needs implementation

## Backend Stubs Created

### Models
- `models/value.py` - Value entity model for values-as-delegates
- `models/idea.py` - Idea entity model for idea-based delegation

### Services
- `services/concentration_monitor.py` - Concentration monitoring service
- `services/feedback_service.py` - Feedback nudge generation service

### API
- `api/feedback.py` - Feedback nudges API endpoints

### Configuration
- Added constitutional feature flags to `config.py`

## Feature Flags

The following environment variables control constitutional features:

```bash
# Constitutional delegation features
VALUES_AS_DELEGATES_ENABLED=false
IDEA_DELEGATION_ENABLED=false
DELEGATION_EXPIRY_ENABLED=false
CONCENTRATION_MONITORING_ENABLED=false
ANONYMOUS_DELEGATION_ENABLED=false
FEEDBACK_NUDGES_ENABLED=false
```

## Test Coverage Status

| Category | Tests | Passing | Failing | Implementation Needed |
|----------|-------|---------|---------|----------------------|
| Circulation & Decay | 5 | 3 | 2 | Expiry/decay mechanisms |
| Values-as-Delegates | 5 | 1 | 4 | Value/idea delegation |
| Interruption & Overrides | 6 | 0 | 6 | Override logic |
| Anti-Hierarchy & Feedback | 5 | 1 | 4 | Concentration monitoring, feedback |
| Transparency & Anonymity | 4 | 2 | 2 | Anonymity features |
| Constitutional Compliance | 4 | 1 | 3 | Comprehensive bypass testing |

**Total:** 29 tests, 8 passing, 21 failing

## Next Steps

### Phase 1: Foundation (Red → Green)
1. ✅ Test structure created
2. ✅ Backend stubs in place
3. ⏳ Implement basic constitutional logic behind feature flags
4. ⏳ Add missing fixtures and test utilities

### Phase 2: Constitutional Features
1. ⏳ Add values-as-delegates schema support
2. ⏳ Implement expiry/decay mechanisms
3. ⏳ Add concentration monitoring
4. ⏳ Implement identity masking
5. ⏳ Create feedback API

### Phase 3: Integration & Validation
1. ⏳ Integrate all constitutional features
2. ⏳ Run full test suite
3. ⏳ Validate constitutional compliance
4. ⏳ Remove temporary endpoints
5. ⏳ Document constitutional guarantees

## Running Tests

```bash
# Run all delegation constitutional tests
pytest tests/delegation/ -v

# Run specific category
pytest tests/delegation/test_circulation_decay.py -v

# Run specific test
pytest tests/delegation/test_circulation_decay.py::test_revocation_immediate_effect -v
```

## Constitutional Compliance

All tests are designed to enforce the Delegation Constitution:

1. **Power Must Circulate** - No permanent delegations
2. **Values Are Delegates Too** - Support for people, values, and ideas
3. **Interruption Is a Right** - User intent always wins
4. **Prevent New Hierarchies** - Concentration monitoring and limits
5. **Ideas Matter Beyond Names** - Anonymous and idea-first flows
6. **Ecology of Trust** - Integration with trust signals
7. **Feedback and Correction Loops** - Continuous monitoring and repair
8. **Radical Transparency** - Full chain visibility

## TODO Items

- [ ] Implement dormant delegation detection
- [ ] Add value/idea delegation support
- [ ] Create override resolution logic
- [ ] Implement concentration monitoring
- [ ] Add anonymity features
- [ ] Create comprehensive bypass testing
- [ ] Add test fixtures for all entity types
- [ ] Implement race condition handling
- [ ] Add phantom vote prevention
- [ ] Create feedback delivery system
