# Transparency Endpoints Reference

This document provides a quick reference for the transparency endpoints that enable users to see delegation chains and patterns.

## Overview

The transparency endpoints provide visibility into delegation patterns while respecting privacy rules. They help users understand:
- Their own delegation chains
- Who has delegated to specific people
- Overall delegation health and patterns

## Endpoints

### 1. GET /api/delegations/me/chain

**Purpose**: Get current user's outbound delegation chain(s) by field.

**Authentication**: Required (JWT token)

**Response**:
```json
{
  "chains": [
    {
      "fieldId": "uuid-or-null",
      "path": [
        {
          "delegator": "user-uuid",
          "delegatee": "user-uuid", 
          "delegateeName": "username",
          "mode": "flexible_domain",
          "startsAt": "2025-01-01T00:00:00Z",
          "endsAt": "2025-01-01T00:00:00Z",
          "legacyTermEndsAt": "2025-01-01T00:00:00Z"
        }
      ]
    }
  ],
  "totalChains": 2
}
```

**Notes**:
- `fieldId` is `null` for global delegations
- `path` shows the delegation chain for each field
- Only active (non-revoked, non-expired) delegations are included

### 2. GET /api/delegations/{delegateeId}/inbound

**Purpose**: Get who has delegated to a specific person.

**Authentication**: Required (JWT token)

**Query Parameters**:
- `fieldId` (optional): Filter by specific field
- `limit` (optional, default 50): Maximum number of results (1-100)

**Response**:
```json
{
  "delegateeId": "user-uuid",
  "delegateeName": "username",
  "inbound": [
    {
      "delegatorId": "user-uuid",
      "delegatorName": "username",
      "fieldId": "field-uuid-or-null",
      "mode": "flexible_domain",
      "createdAt": "2025-01-01T00:00:00Z",
      "expiresAt": "2025-01-01T00:00:00Z",
      "legacyTermEndsAt": "2025-01-01T00:00:00Z"
    }
  ],
  "counts": {
    "total": 5,
    "byField": {
      "global": 2,
      "field-uuid": 3
    }
  }
}
```

**Notes**:
- `fieldId` is `null` for global delegations
- `counts.byField` shows breakdown by field
- Only active delegations are included

### 3. GET /api/delegations/health/summary

**Purpose**: Get lightweight transparency summary of delegation patterns.

**Authentication**: Required (JWT token)

**Query Parameters**:
- `limit` (optional, default 10): Maximum number of top delegatees to return (1-50)

**Response**:
```json
{
  "topDelegatees": [
    {
      "id": "user-uuid",
      "name": "username",
      "count": 15,
      "percent": 25.5
    }
  ],
  "byField": {
    "field-uuid": [
      {
        "id": "user-uuid",
        "name": "username", 
        "count": 8,
        "fieldName": "Field Label"
      }
    ]
  },
  "totalDelegations": 100,
  "generatedAt": "2025-01-01T00:00:00Z"
}
```

**Notes**:
- `topDelegatees` shows global top delegatees by delegation count
- `byField` shows top delegatees per field
- Percentages are calculated against total active delegations

## Privacy Rules

All transparency endpoints respect privacy rules:

- **No PII exposure**: Only usernames are exposed, never emails or other sensitive data
- **Active delegations only**: Expired or revoked delegations are excluded
- **Authentication required**: All endpoints require valid JWT tokens
- **User context**: Users can only see data they have permission to access

## Error Responses

All endpoints return standard error responses:

```json
{
  "detail": "Error message"
}
```

**Common HTTP Status Codes**:
- `200 OK`: Success
- `401 Unauthorized`: Invalid or missing authentication
- `404 Not Found`: Resource not found (e.g., delegatee doesn't exist)
- `500 Internal Server Error`: Server error

## Usage Examples

### View My Delegation Chains
```bash
curl -H "Authorization: Bearer <token>" \
  https://api.example.com/api/delegations/me/chain
```

### Check Who Delegated to Someone
```bash
curl -H "Authorization: Bearer <token>" \
  "https://api.example.com/api/delegations/user-uuid/inbound?limit=20"
```

### Get Delegation Health Summary
```bash
curl -H "Authorization: Bearer <token>" \
  "https://api.example.com/api/delegations/health/summary?limit=15"
```

## Integration Notes

- **Frontend Integration**: These endpoints can be used to build transparency dashboards
- **Caching**: Consider caching health summary data as it's computationally expensive
- **Rate Limiting**: Endpoints are subject to standard rate limiting
- **Pagination**: Inbound endpoint supports pagination via `limit` parameter
