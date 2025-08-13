# Label System Validation Script

This document provides a comprehensive validation script for the Topic Label system implementation.

## Prerequisites

1. Backend server running on `http://127.0.0.1:8000`
2. Database with seeded labels
3. Test user created

## Validation Steps

### 1. Environment Setup

```bash
# Set environment variables
export DATABASE_URL="sqlite+aiosqlite:///./backend/test.db"
export LABELS_ENABLED=true
export ALLOW_PUBLIC_LABELS=false

# Start server
pkill -f uvicorn || true
PYTHONPATH=. uvicorn backend.main:app --reload --host 127.0.0.1 --port 8000 &

# Wait for server to start
sleep 3
```

### 2. Create Test User and Get Token

```bash
# Create test user
curl -s -X POST -H "Content-Type: application/json" \
  -d '{"username":"testuser","email":"test@example.com","password":"password123"}' \
  http://127.0.0.1:8000/api/users/ >/dev/null

# Get authentication token
TOKEN=$(curl -s -X POST -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=testuser&password=password123" \
  http://127.0.0.1:8000/api/token | jq -r .access_token)

echo "Token: $TOKEN"
```

### 3. Test Labels API

```bash
# List all labels
echo "=== Testing Labels API ==="
curl -s -H "Authorization: Bearer $TOKEN" http://127.0.0.1:8000/api/labels/ | jq '.[].slug'

# Expected output:
# "environment"
# "mobility"
# "governance"
# "budget"
# "education"
# "health"
# "housing"
```

### 4. Test Poll Creation with Labels

```bash
echo "=== Testing Poll Creation with Labels ==="
curl -s -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" \
  -d '{"title":"Safer School Routes","description":"Add zebra crossings near the school","decision_type":"level_b","labels":["mobility","education"]}' \
  http://127.0.0.1:8000/api/polls/ | jq '{id,title,labels:[.labels[].slug]}'

# Expected output:
# {
#   "id": "some-uuid",
#   "title": "Safer School Routes",
#   "labels": ["mobility", "education"]
# }
```

### 5. Test Label Filtering

```bash
echo "=== Testing Label Filtering ==="
curl -s -H "Authorization: Bearer $TOKEN" "http://127.0.0.1:8000/api/polls/?label=mobility" | jq '.[0] | {id,title,labels:[.labels[].slug]}'

# Expected output: Poll with mobility label
```

### 6. Test Poll Detail with Labels

```bash
echo "=== Testing Poll Detail with Labels ==="
# Get the poll ID from the previous response
POLL_ID=$(curl -s -H "Authorization: Bearer $TOKEN" "http://127.0.0.1:8000/api/polls/?label=mobility" | jq -r '.[0].id')

curl -s -H "Authorization: Bearer $TOKEN" "http://127.0.0.1:8000/api/polls/$POLL_ID" | jq '{id,title,labels:[.labels[].slug]}'

# Expected output: Poll with labels array populated
```

### 7. Test Error Cases

```bash
echo "=== Testing Error Cases ==="

# Test creating poll with non-existent label
curl -s -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" \
  -d '{"title":"Test Poll","description":"Test","decision_type":"level_b","labels":["non-existent"]}' \
  http://127.0.0.1:8000/api/polls/ | jq .

# Expected: 404 error with "Labels not found" message

# Test creating poll with too many labels
curl -s -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" \
  -d '{"title":"Test Poll","description":"Test","decision_type":"level_b","labels":["mobility","education","health","housing","budget","governance"]}' \
  http://127.0.0.1:8000/api/polls/ | jq .

# Expected: 422 error with "Maximum 5 labels allowed" message
```

### 8. Test Admin-Only Label Operations

```bash
echo "=== Testing Admin-Only Operations ==="

# Try to create a label (should fail for non-admin user)
curl -s -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" \
  -d '{"name":"Test Label"}' \
  http://127.0.0.1:8000/api/labels/ | jq .

# Expected: 403 error with "Not authorized" message
```

## Success Criteria

✅ **All tests pass without MissingGreenlet errors**
✅ **Labels are properly associated with polls**
✅ **Label filtering works correctly**
✅ **Error handling works as expected**
✅ **Admin guards are in place**
✅ **Eager loading prevents lazy load issues**

## Performance Notes

- The implementation uses `selectinload` for eager loading
- Association tables are used for many-to-many relationships
- Bulk inserts are used for label associations
- No lazy loading occurs during serialization

## Next Steps

1. **Frontend Integration**: Test the frontend components with the working backend
2. **Delegation Testing**: Test label-aware delegation functionality
3. **Performance Testing**: Load test with many polls and labels
4. **Documentation**: Update API documentation with label endpoints
