# Audit System

The Commons includes a comprehensive audit system that tracks user actions and system events for security, compliance, and debugging purposes.

## Overview

The audit system consists of two complementary components:

1. **Middleware-based audit logging** - Automatic logging of all mutating requests
2. **Explicit audit events** - Targeted logging of specific business actions

## Middleware-based Audit Logging

### How it Works

The `AuditMiddleware` automatically logs all mutating HTTP requests (POST, PUT, PATCH, DELETE) that are not on noisy paths.

### Request ID Propagation

- **Incoming**: Uses `X-Request-ID` header if provided, otherwise generates a UUID
- **Outgoing**: Adds `X-Request-ID` to response headers
- **Internal**: Stores request ID in `request.state.request_id` for use throughout the request lifecycle

### Logged Data

For each mutating request, the middleware logs:

```json
{
  "ts": 1640995200.123,
  "request_id": "550e8400-e29b-41d4-a716-446655440000",
  "user_id": "user-123",
  "method": "POST",
  "path": "/api/polls",
  "status": 201,
  "duration_ms": 45,
  "query_params": {"limit": "10"}
}
```

### Skipped Paths

The following paths are excluded from audit logging to reduce noise:

- `/api/health`
- `/health`
- `/health/db`
- `/health/redis`
- `/docs`
- `/openapi.json`
- `/redoc`
- `/favicon.ico`
- `/`

### User Resolution

The middleware attempts to resolve the current user using the `get_current_active_user_optional` function. If user resolution fails (e.g., unauthenticated request), the audit log will have `user_id: null`.

## Explicit Audit Events

### Purpose

Explicit audit events provide detailed logging of specific business actions that may not be captured by the middleware alone.

### Usage

```python
from backend.core.audit_mw import audit_event

# In your handler
audit_event(
    "poll_created",
    {
        "poll_id": str(poll.id),
        "title": poll.title,
        "description": poll.description,
    },
    request
)
```

### Logged Data

Explicit audit events include:

```json
{
  "ts": 1640995200.123,
  "request_id": "550e8400-e29b-41d4-a716-446655440000",
  "user_id": "user-123",
  "kind": "poll_created",
  "data": {
    "poll_id": "poll-456",
    "title": "New Proposal",
    "description": "This is a new proposal..."
  }
}
```

## Current Explicit Audit Events

### Poll Management

- **`poll_created`** - When a new poll/proposal is created
  - Data: `poll_id`, `title`, `description`

### Voting

- **`vote_cast`** - When a user casts a vote
  - Data: `vote_id`, `poll_id`, `option_id`

### Delegations

- **`delegation_created`** - When a user creates a delegation
  - Data: `delegation_id`, `delegator_id`, `delegatee_id`
- **`delegation_removed`** - When a user removes their delegation
  - Data: `delegation_id`, `delegator_id`, `delegatee_id`

### Comments

- **`comment_created`** - When a comment is created
  - Data: `comment_id`, `poll_id`, `body` (truncated to 100 chars)
- **`comment_deleted`** - When a comment is deleted
  - Data: `comment_id`, `poll_id`, `is_admin_delete`

## Logging Configuration

### Structured JSON Logging

All audit logs use structured JSON format for easy parsing and analysis:

```json
{
  "timestamp": "2024-01-01T12:00:00.123Z",
  "level": "info",
  "logger": "backend.core.audit_mw",
  "message": "audit_request",
  "ts": 1640995200.123,
  "request_id": "550e8400-e29b-41d4-a716-446655440000",
  "user_id": "user-123",
  "method": "POST",
  "path": "/api/polls",
  "status": 201,
  "duration_ms": 45
}
```

### Log Levels

- **INFO** - Normal audit events
- **WARNING** - Audit system issues (e.g., user resolution failures)
- **ERROR** - Audit system failures

## Security Considerations

### Data Privacy

- **User IDs**: Only user IDs are logged, not usernames or other PII
- **Content**: Comment bodies are truncated to 100 characters
- **Sensitive Data**: Passwords and tokens are never logged

### Access Control

- **Admin Health Endpoint**: `/api/limiter/health` requires admin authentication
- **Audit Logs**: Should be protected with appropriate access controls
- **Retention**: Consider implementing log retention policies

## Monitoring and Alerting

### Key Metrics

Monitor these audit-related metrics:

- **Request Volume**: Number of audit events per time period
- **Error Rate**: Failed user resolutions or audit logging
- **Response Times**: Duration of audited requests
- **User Activity**: Most active users and actions

### Alerts

Consider setting up alerts for:

- **High Error Rates**: Audit system failures
- **Unusual Activity**: Spikes in specific action types
- **Failed Authentication**: High rate of unauthenticated requests
- **Admin Actions**: All admin-level operations

## Troubleshooting

### Common Issues

1. **Missing Request IDs**: Check that `X-Request-ID` headers are being set
2. **User Resolution Failures**: Verify authentication middleware is working
3. **High Log Volume**: Review skipped paths configuration
4. **Performance Impact**: Monitor middleware duration overhead

### Debugging

Enable debug logging to see detailed audit system behavior:

```bash
export LOG_LEVEL=DEBUG
```

### Testing

Run audit tests to verify functionality:

```bash
pytest backend/tests/test_audit.py -v
```

## Best Practices

### Adding New Audit Events

1. **Choose Descriptive Names**: Use clear, action-oriented event names
2. **Include Relevant Data**: Log enough context for analysis
3. **Avoid PII**: Never log sensitive personal information
4. **Test Thoroughly**: Verify events are logged correctly

### Performance

1. **Minimize Data**: Only log essential information
2. **Async Logging**: Audit events are logged asynchronously
3. **Batch Processing**: Consider batching for high-volume scenarios

### Compliance

1. **Retention Policies**: Implement appropriate log retention
2. **Access Controls**: Restrict access to audit logs
3. **Encryption**: Encrypt audit logs at rest
4. **Backup**: Include audit logs in backup strategies
