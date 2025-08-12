# Backend Changelog

## [Unreleased]

### Fix: poll detail 500
- **Issue**: GET `/api/polls/{poll_id}` was returning 500 error due to `AttributeError: type object 'Delegation' has no attribute 'end_date'`
- **Root Cause**: The `DelegationService` was trying to use `start_date` and `end_date` fields that were removed from the `Delegation` model in migration `update_delegations_table.py`
- **Fix**: Updated `DelegationService.get_active_delegation()` and `get_active_delegations()` methods to work with the current model structure (no start_date/end_date, only is_deleted flag)
- **Added**: Comprehensive error logging to the poll detail endpoint with DEBUG environment variable support
- **Added**: Test suite for poll detail endpoint covering authenticated users (voted/not voted), unauthenticated users, and delegation scenarios
- **Developer Experience**: Added DEBUG environment variable to enable stack traces in logs for local development

### Technical Details
- **Files Modified**: 
  - `backend/services/delegation.py` - Fixed delegation queries to match current model
  - `backend/api/polls.py` - Added comprehensive logging and error handling
  - `backend/config.py` - Added DEBUG environment variable support
- **Files Added**:
  - `backend/tests/test_poll_detail.py` - Comprehensive test suite
  - `backend/CHANGELOG.md` - This changelog file

### Testing
The fix includes comprehensive tests covering:
- Authenticated user who voted (status: "voted")
- Authenticated user who didn't vote (status: "none") 
- Unauthenticated user (401 Unauthorized)
- User with delegation (status: "delegated")
- Non-existent poll (404 Not Found)
- Invalid UUID (422 Validation Error)
- Schema validation (all required fields present)

### Environment Variables
- `DEBUG=true` - Enables stack traces in error logs for local development
