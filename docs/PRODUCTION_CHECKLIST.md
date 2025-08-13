# Production Checklist - Content Features

## Overview
This runbook provides a step-by-step checklist for deploying The Commons to production with a focus on content features, security, and reliability.

## Pre-Deployment Checklist

### 1. Environment Configuration

#### 1.1 Content Feature Flags
```bash
# Backend Environment Variables
USE_DEMO_CONTENT=false                    # Use real Austin content
CONTENT_DATA_DIR="./data/real_content"   # Path to real content data
VITE_USE_DEMO_CONTENT=false              # Frontend demo content flag

# Delegation Feature Flag (decide based on readiness)
VITE_DELEGATION_ENABLED=true             # Enable delegation features
# OR
VITE_DELEGATION_ENABLED=false            # Disable delegation features

# Environment
ENVIRONMENT=production
DEBUG=false
```

#### 1.2 Security Configuration
```bash
# Required Security Variables
SECRET_KEY=<strong-secret-key>           # 32+ character random string
CSRF_SECRET_KEY=<csrf-secret-key>        # CSRF protection secret
POSTGRES_PASSWORD=<strong-db-password>   # Database password
REDIS_PASSWORD=<redis-password>          # Redis password (if enabled)

# Admin Configuration
ADMIN_USERNAMES="admin1,admin2"          # Comma-separated admin usernames
```

#### 1.3 Database Configuration
```bash
# Production Database
DATABASE_URL="postgresql+asyncpg://user:pass@host:5432/dbname"
POSTGRES_USER=the_commons_user
POSTGRES_DB=the_commons_prod

# Redis Configuration
REDIS_URL="redis://:password@host:6379/0"
REDIS_PASSWORD=<redis-password>
```

### 2. Database Migration Status

#### 2.1 Verify Migration Status
```bash
# Check current migration status
cd backend
alembic current

# Expected output should show latest migration:
# add_chain_origin_and_revoked_fields (head)

# List all migrations
alembic history --verbose

# Verify no pending migrations
alembic heads
# Should show only one head: add_chain_origin_and_revoked_fields
```

#### 2.2 Run Migrations (if needed)
```bash
# Apply any pending migrations
alembic upgrade head

# Verify migration success
alembic current
```

#### 2.3 Migration Rollback Plan
```bash
# If rollback is needed, identify target revision
alembic history --verbose

# Rollback to specific revision (use with caution)
alembic downgrade <revision-id>

# Verify rollback success
alembic current
```

### 3. Content Data Verification

#### 3.1 Real Content Data
```bash
# Verify real content files exist
ls -la data/real_content/
# Expected files:
# - principles.json
# - actions.json  
# - stories.json

# Validate JSON structure
python -m json.tool data/real_content/principles.json
python -m json.tool data/real_content/actions.json
python -m json.tool data/real_content/stories.json
```

#### 3.2 Content API Endpoints
```bash
# Test content endpoints (with demo content disabled)
curl -X GET "http://localhost:8000/api/content/principles" \
  -H "Content-Type: application/json"

curl -X GET "http://localhost:8000/api/content/actions" \
  -H "Content-Type: application/json"

curl -X GET "http://localhost:8000/api/content/stories" \
  -H "Content-Type: application/json"

# Verify responses contain real Austin content, not demo data
```

### 4. Health Checks Configuration

#### 4.1 Health Check Endpoints
```bash
# Test all health check endpoints
curl -X GET "http://localhost:8000/health/comprehensive"
# Expected: {"status": "healthy", "services": {...}}

curl -X GET "http://localhost:8000/health/db"
# Expected: {"status": "healthy", "message": "Database connection is healthy"}

curl -X GET "http://localhost:8000/health/redis"
# Expected: {"status": "healthy", "message": "Redis connection is healthy"}

# Admin-only health checks (requires authentication)
curl -X GET "http://localhost:8000/api/limiter/health" \
  -H "Authorization: Bearer <admin-token>"
```

#### 4.2 Health Check Monitoring
```bash
# Set up monitoring for health endpoints
# - /health/comprehensive (main health check)
# - /health/db (database health)
# - /health/redis (Redis health)
# - /api/limiter/health (rate limiter health - admin only)

# Configure alerts for:
# - HTTP 503 responses
# - Response time > 5 seconds
# - Any service showing "unhealthy" status
```

### 5. Logging Configuration

#### 5.1 Logging Setup
```bash
# Environment variables for logging
LOG_LEVEL=INFO                    # Production logging level
LOG_FORMAT=json                   # Structured JSON logging
LOG_FILE=/var/log/the_commons/app.log  # Log file path (optional)

# Verify logging configuration
# Check that logs are being written to configured destination
# Ensure log rotation is configured
```

#### 5.2 Log Monitoring
```bash
# Monitor for critical log patterns:
# - ERROR level logs
# - Database connection failures
# - Rate limiting violations
# - Authentication failures
# - Content API errors
```

### 6. Sentry Configuration

#### 6.1 Sentry Setup
```bash
# Backend Sentry Configuration
SENTRY_DSN=https://<key>@<org>.ingest.sentry.io/<project>
SENTRY_TRACES_SAMPLE_RATE=0.1
ENVIRONMENT=production

# Frontend Sentry Configuration (in .env)
VITE_SENTRY_DSN=https://<key>@<org>.ingest.sentry.io/<project>
VITE_SENTRY_ENVIRONMENT=production
```

#### 6.2 Sentry Verification
```bash
# Test Sentry integration
# Trigger a test error and verify it appears in Sentry dashboard
# Check that environment is correctly set to "production"
# Verify sampling rate is appropriate for production traffic
```

### 7. Rate Limiting Configuration

#### 7.1 Rate Limiter Setup
```bash
# Rate limiting configuration
RATE_LIMIT_ENABLED=true
RATE_LIMIT_PER_MINUTE=60

# Verify rate limiter is active
curl -X GET "http://localhost:8000/api/limiter/health" \
  -H "Authorization: Bearer <admin-token>"
# Expected: {"status": "healthy", "rate_limit_per_minute": 60}
```

#### 7.2 Rate Limiting Testing
```bash
# Test rate limiting behavior
# Make 61 requests in 1 minute to a rate-limited endpoint
# Verify 429 response on the 61st request
# Check that rate limit headers are present:
# - X-RateLimit-Limit
# - X-RateLimit-Remaining
# - X-RateLimit-Reset
```

### 8. Cache Warmup for Content Endpoints

#### 8.1 Content Cache Warmup
```bash
# Warm up content endpoint caches
curl -X GET "http://localhost:8000/api/content/principles"
curl -X GET "http://localhost:8000/api/content/actions"
curl -X GET "http://localhost:8000/api/content/stories"

# Verify cache hit rates in Redis
redis-cli -h <redis-host> -p 6379 -a <password>
> INFO memory
> INFO stats
```

#### 8.2 Cache Configuration Verification
```bash
# Verify Redis cache is working
# Check cache hit/miss ratios
# Monitor cache memory usage
# Ensure cache TTL is appropriate for content
```

### 9. Access Control Verification

#### 9.1 Public vs Protected Endpoints
```bash
# Test public endpoints (no auth required)
curl -X GET "http://localhost:8000/health/comprehensive"
curl -X GET "http://localhost:8000/docs"
curl -X GET "http://localhost:8000/api/content/principles"

# Test protected endpoints (auth required)
curl -X GET "http://localhost:8000/api/users/me"
# Expected: 401 Unauthorized

curl -X GET "http://localhost:8000/api/users/me" \
  -H "Authorization: Bearer <valid-token>"
# Expected: 200 OK with user data
```

#### 9.2 Content Access Control
```bash
# Verify content endpoints are public (no auth required)
curl -X GET "http://localhost:8000/api/content/principles"
curl -X GET "http://localhost:8000/api/content/actions"
curl -X GET "http://localhost:8000/api/content/stories"

# All should return 200 OK with content data
```

### 10. Security Headers and CORS

#### 10.1 Security Headers Verification
```bash
# Test security headers
curl -I "http://localhost:8000/health/comprehensive"

# Verify presence of security headers:
# - X-Content-Type-Options: nosniff
# - X-Frame-Options: DENY
# - X-XSS-Protection: 1; mode=block
# - Strict-Transport-Security: max-age=31536000; includeSubDomains
# - Content-Security-Policy: default-src 'self'
```

#### 10.2 CORS Configuration
```bash
# Test CORS configuration
curl -H "Origin: https://yourdomain.com" \
  -H "Access-Control-Request-Method: GET" \
  -H "Access-Control-Request-Headers: Content-Type" \
  -X OPTIONS "http://localhost:8000/api/content/principles"

# Verify CORS headers are present and correct:
# - Access-Control-Allow-Origin: https://yourdomain.com
# - Access-Control-Allow-Methods: GET, POST, PUT, DELETE
# - Access-Control-Allow-Headers: Content-Type, Authorization
```

#### 10.3 CORS Origins Configuration
```bash
# Verify ALLOWED_ORIGINS is set correctly
ALLOWED_ORIGINS=["https://yourdomain.com", "https://www.yourdomain.com"]

# Test from allowed origin
curl -H "Origin: https://yourdomain.com" \
  -X GET "http://localhost:8000/api/content/principles"

# Test from disallowed origin (should be blocked)
curl -H "Origin: https://malicious-site.com" \
  -X GET "http://localhost:8000/api/content/principles"
```

### 11. Feature Flag Verification

#### 11.1 Delegation Feature Flag
```bash
# Test delegation feature flag
# Frontend: Check VITE_DELEGATION_ENABLED value
# Backend: Verify delegation endpoints behavior

# If delegation is enabled:
curl -X GET "http://localhost:8000/api/delegations/me" \
  -H "Authorization: Bearer <valid-token>"

# If delegation is disabled:
# Frontend should not show delegation UI
# Backend delegation endpoints should return 404 or be disabled
```

#### 11.2 Demo Content Flag
```bash
# Verify demo content is disabled
USE_DEMO_CONTENT=false
VITE_USE_DEMO_CONTENT=false

# Test content endpoints return real Austin content
curl -X GET "http://localhost:8000/api/content/principles"
# Verify response contains real Austin principles, not demo data
```

### 12. Rollback Plan and Feature Toggles

#### 12.1 Database Rollback Plan
```bash
# Identify current migration
alembic current

# Rollback commands (use with extreme caution)
alembic downgrade <previous-revision>

# Verify rollback success
alembic current
```

#### 12.2 Feature Flag Rollback
```bash
# Quick feature flag changes (no deployment needed)
# Backend: Update environment variables
USE_DEMO_CONTENT=true                    # Enable demo content if needed
VITE_DELEGATION_ENABLED=false            # Disable delegation if issues arise

# Frontend: Update environment variables
VITE_USE_DEMO_CONTENT=true               # Enable demo content if needed
VITE_DELEGATION_ENABLED=false            # Disable delegation if issues arise

# Restart application to apply changes
```

#### 12.3 Application Rollback
```bash
# If full application rollback is needed:
# 1. Revert to previous Docker image
docker pull kaarlekaarle/the-commons:<previous-tag>

# 2. Update deployment
kubectl set image deployment/the-commons the-commons=kaarlekaarle/the-commons:<previous-tag>

# 3. Verify rollback
kubectl rollout status deployment/the-commons
```

### 13. Post-Deployment Verification

#### 13.1 Content Functionality Test
```bash
# Test complete content flow
# 1. Load homepage
# 2. Verify content displays correctly
# 3. Test content navigation
# 4. Verify content search (if applicable)
# 5. Test content filtering (if applicable)

# Automated test
npm run test:e2e:smoke
```

#### 13.2 Performance Verification
```bash
# Test content endpoint performance
curl -w "@curl-format.txt" -o /dev/null -s "http://localhost:8000/api/content/principles"
curl -w "@curl-format.txt" -o /dev/null -s "http://localhost:8000/api/content/actions"
curl -w "@curl-format.txt" -o /dev/null -s "http://localhost:8000/api/content/stories"

# Expected response times < 500ms for cached content
```

#### 13.3 Monitoring Verification
```bash
# Verify all monitoring is working:
# - Health checks are green
# - Logs are being collected
# - Sentry is receiving events
# - Rate limiting is active
# - Cache hit rates are good
# - Error rates are low
```

## Emergency Procedures

### Content Issues
```bash
# If content is not loading:
# 1. Check USE_DEMO_CONTENT flag
# 2. Verify content files exist and are valid JSON
# 3. Check content API endpoints
# 4. Verify database content tables
# 5. Check Redis cache

# Quick fix: Enable demo content temporarily
USE_DEMO_CONTENT=true
VITE_USE_DEMO_CONTENT=true
```

### Performance Issues
```bash
# If performance is poor:
# 1. Check Redis cache hit rates
# 2. Verify database connection pool
# 3. Check rate limiting configuration
# 4. Monitor resource usage
# 5. Check for memory leaks
```

### Security Issues
```bash
# If security issues are detected:
# 1. Check CORS configuration
# 2. Verify security headers
# 3. Review access control
# 4. Check authentication/authorization
# 5. Review logs for suspicious activity
```

## Contact Information

- **On-Call Engineer**: [Contact Info]
- **DevOps Team**: [Contact Info]
- **Security Team**: [Contact Info]
- **Database Admin**: [Contact Info]

## Notes

- Always test in staging environment first
- Keep deployment logs for audit purposes
- Monitor application for 24 hours after deployment
- Have rollback plan ready before deployment
- Document any issues and resolutions
