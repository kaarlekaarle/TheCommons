# CI Restoration Checklist

This document tracks the changes made to exclude unstable test groups from CI and provides a checklist for restoring full coverage when the issues are resolved.

## Current CI Configuration

### Backend Tests
- **Excluded Groups**: `offline`, `delegation_edge`
- **Command**: `pytest backend/tests/ -k "not offline and not delegation_edge"`
- **Coverage**: Maintains 80% minimum coverage requirement

### Frontend Tests
- **Unit Tests**: Full coverage maintained
- **E2E Tests**: Minimal smoke test only (login → dashboard → content load)
- **Excluded**: Full E2E test suite

## Marked as xfail (Expected to Fail)

### WebSocket Offline Tests
- `test_websocket_disconnect_broadcasting` - TODO: Fix race condition in offline WebSocket disconnect handling
- `test_websocket_heartbeat_shutdown` - TODO: Fix timing issues in offline heartbeat shutdown
- `test_websocket_error_handling` - TODO: Fix error handling in offline WebSocket message sending

### Delegation Edge Tests
- `test_concurrent_delegation_creation` - TODO: Fix race conditions in concurrent delegation creation

### Soft Delete Tests
- Already marked as xfail in `test_soft_delete_offline.py`

## Restoration Checklist

### Phase 1: Fix Known Issues

#### WebSocket Offline Issues
- [ ] **Race Condition Fix**: Investigate and fix race condition in `test_websocket_disconnect_broadcasting`
  - [ ] Add proper synchronization for disconnect operations
  - [ ] Ensure atomic cleanup of connection state
  - [ ] Test with multiple concurrent disconnections

- [ ] **Timing Issues Fix**: Resolve timing issues in `test_websocket_heartbeat_shutdown`
  - [ ] Implement proper task cancellation handling
  - [ ] Add timeout mechanisms for heartbeat operations
  - [ ] Ensure clean shutdown without resource leaks

- [ ] **Error Handling Fix**: Improve error handling in `test_websocket_error_handling`
  - [ ] Implement robust error recovery mechanisms
  - [ ] Add proper exception handling for failed message sends
  - [ ] Ensure graceful degradation on connection failures

#### Delegation Edge Issues
- [ ] **Concurrent Delegation Fix**: Resolve race conditions in `test_concurrent_delegation_creation`
  - [ ] Implement database-level constraints for delegation uniqueness
  - [ ] Add proper transaction isolation
  - [ ] Test with high concurrency scenarios

### Phase 2: Test Stability Improvements

#### Offline Mode Tests
- [ ] **Test Isolation**: Ensure offline tests don't interfere with each other
  - [ ] Implement proper test cleanup between runs
  - [ ] Add database state reset mechanisms
  - [ ] Verify no shared state between test runs

- [ ] **Timing Robustness**: Make offline tests more resilient to timing variations
  - [ ] Add retry mechanisms for flaky operations
  - [ ] Implement proper wait conditions
  - [ ] Use deterministic timeouts

#### Delegation Edge Tests
- [ ] **Database Consistency**: Ensure delegation tests maintain database consistency
  - [ ] Add proper transaction rollback mechanisms
  - [ ] Implement cleanup for failed test scenarios
  - [ ] Verify referential integrity constraints

### Phase 3: CI Configuration Updates

#### Backend Test Restoration
- [ ] **Remove Test Exclusions**: Update CI to include all test groups
  ```yaml
  # Change from:
  pytest backend/tests/ -k "not offline and not delegation_edge"
  
  # To:
  pytest backend/tests/ -v --cov=backend --cov-report=xml --cov-fail-under=80
  ```

- [ ] **Remove xfail Markers**: Remove `@pytest.mark.xfail` from fixed tests
  - [ ] Remove from `test_websocket_manager_offline.py`
  - [ ] Remove from `test_concurrent_delegations.py`
  - [ ] Remove from `test_soft_delete_offline.py`

#### Frontend E2E Test Restoration
- [ ] **Restore Full E2E Suite**: Update CI to run complete E2E tests
  ```yaml
  # Change from:
  npx playwright test smoke.spec.ts --config=e2e/playwright.config.ts
  
  # To:
  npm run test:e2e
  ```

- [ ] **Remove Smoke Test Limitation**: Run all E2E tests in CI
  - [ ] `basic.spec.ts` - Complete user journey
  - [ ] `delegation.smoke.spec.ts` - Delegation functionality
  - [ ] `accessibility.spec.ts` - Accessibility compliance

### Phase 4: Validation

#### Test Coverage Verification
- [ ] **Backend Coverage**: Ensure coverage remains above 80%
  - [ ] Run full test suite locally
  - [ ] Verify coverage report
  - [ ] Check for any new uncovered code paths

- [ ] **Frontend Coverage**: Verify frontend test coverage
  - [ ] Run unit tests with coverage
  - [ ] Verify E2E tests pass consistently
  - [ ] Check for any broken functionality

#### Performance Validation
- [ ] **CI Duration**: Ensure CI pipeline doesn't become too slow
  - [ ] Monitor total CI execution time
  - [ ] Optimize slow tests if needed
  - [ ] Consider parallel test execution

- [ ] **Test Reliability**: Verify tests are stable
  - [ ] Run CI multiple times to check for flakiness
  - [ ] Monitor test failure rates
  - [ ] Address any remaining instability

### Phase 5: Documentation Updates

- [ ] **Update Documentation**: Reflect restored test coverage
  - [ ] Update README with full test instructions
  - [ ] Document any new test requirements
  - [ ] Update development setup instructions

- [ ] **Remove This Checklist**: Once restoration is complete
  - [ ] Archive this document
  - [ ] Update team on restored capabilities

## Monitoring During Restoration

### Metrics to Track
- **Test Pass Rate**: Should be >95% for all test groups
- **CI Duration**: Should not increase by more than 50%
- **Flaky Test Rate**: Should be <5% for any test group
- **Coverage**: Should maintain or improve current levels

### Rollback Plan
If issues persist during restoration:
1. Revert CI configuration changes
2. Keep xfail markers on problematic tests
3. Document specific issues encountered
4. Plan targeted fixes for specific problems

## Notes

- **Priority**: Focus on WebSocket offline issues first as they affect core functionality
- **Timeline**: Allow 2-4 weeks for complete restoration
- **Communication**: Update team on progress and any blockers
- **Testing**: Test restoration changes in feature branches before merging to main
