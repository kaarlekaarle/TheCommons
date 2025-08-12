# Test Suites

This repository contains two separate test suites that can be run independently or together.

## Test Suite Structure

### 1. Backend Tests (`backend/tests/`)
- **Location**: `backend/tests/`
- **Purpose**: Core backend functionality tests
- **Default**: Always runs
- **Scope**: API endpoints, database models, business logic, integration tests

### 2. Root Tests (`tests/`)
- **Location**: `tests/` (repo root)
- **Purpose**: Higher-level integration and system tests
- **Default**: Disabled (requires explicit flag)
- **Scope**: End-to-end flows, performance tests, security tests, infrastructure tests

## Running Tests

### Default Behavior (Backend Tests Only)
```bash
# Run only backend tests (default)
pytest

# Or explicitly
pytest backend/tests/
```

### Include Root Tests
```bash
# Run both test suites
RUN_ROOT_TESTS=1 pytest

# Or with specific test files
RUN_ROOT_TESTS=1 pytest tests/test_critical_flows.py
```

### Specific Test Suites
```bash
# Backend tests only
pytest backend/tests/

# Root tests only (when enabled)
RUN_ROOT_TESTS=1 pytest tests/

# Specific test categories
pytest backend/tests/api/          # API tests only
RUN_ROOT_TESTS=1 pytest tests/integration/  # Integration tests only
```

## Environment Variables

- `RUN_ROOT_TESTS=1`: Enables root-level test discovery
- Without this flag, only `backend/tests/` are discovered

## CI Configuration

- **Default job**: Runs only backend tests for faster feedback
- **Extended job**: Sets `RUN_ROOT_TESTS=1` to include root tests
- **Matrix strategy**: Allows running both suites in parallel

## Test Categories

### Backend Tests (`backend/tests/`)
- Unit tests for models and services
- API endpoint tests
- Database integration tests
- Authentication and authorization tests
- WebSocket tests

### Root Tests (`tests/`)
- End-to-end critical flows
- Performance and load tests
- Security validation tests
- Infrastructure and deployment tests
- Cross-component integration tests

## Best Practices

1. **Backend tests**: Write for fast feedback during development
2. **Root tests**: Write for comprehensive validation before deployment
3. **Use appropriate suite**: Don't put unit tests in root tests
4. **CI optimization**: Use matrix strategy to run suites in parallel
