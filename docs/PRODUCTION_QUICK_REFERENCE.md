# Production Quick Reference

## Essential Environment Variables

```bash
# Content Configuration
USE_DEMO_CONTENT=false
CONTENT_DATA_DIR="./data/real_content"
VITE_USE_DEMO_CONTENT=false

# Delegation Feature (decide based on readiness)
VITE_DELEGATION_ENABLED=true  # or false

# Security (REQUIRED)
SECRET_KEY=<32+ char random string>
CSRF_SECRET_KEY=<csrf secret>
POSTGRES_PASSWORD=<strong password>
REDIS_PASSWORD=<redis password>

# Environment
ENVIRONMENT=production
DEBUG=false
```

## Pre-Deployment Commands

```bash
# 1. Check migration status
cd backend && alembic current

# 2. Verify content files
ls -la data/real_content/
python -m json.tool data/real_content/principles.json

# 3. Test health endpoints
curl http://localhost:8000/health/comprehensive
curl http://localhost:8000/health/db
curl http://localhost:8000/health/redis

# 4. Test content endpoints
curl http://localhost:8000/api/content/principles
curl http://localhost:8000/api/content/actions
curl http://localhost:8000/api/content/stories

# 5. Verify security headers
curl -I http://localhost:8000/health/comprehensive
```

## Critical Checks

### ✅ Must Pass
- [ ] Health checks return 200 OK
- [ ] Content endpoints return real Austin data (not demo)
- [ ] Security headers present
- [ ] CORS configured correctly
- [ ] Rate limiting active
- [ ] Sentry receiving events
- [ ] Logs being written
- [ ] Cache hit rates > 80%

### ⚠️ Warning Signs
- Health checks return 503
- Content endpoints return demo data
- Missing security headers
- CORS errors in browser console
- High error rates in Sentry
- Cache miss rates > 50%

## Emergency Rollback

```bash
# Quick feature flag rollback
USE_DEMO_CONTENT=true          # Enable demo content
VITE_DELEGATION_ENABLED=false  # Disable delegation

# Database rollback (CAUTION)
alembic downgrade <previous-revision>

# Full application rollback
docker pull kaarlekaarle/the-commons:<previous-tag>
kubectl set image deployment/the-commons the-commons=kaarlekaarle/the-commons:<previous-tag>
```

## Monitoring URLs

- **Health Check**: `/health/comprehensive`
- **Database Health**: `/health/db`
- **Redis Health**: `/health/redis`
- **Rate Limiter Health**: `/api/limiter/health` (admin only)
- **Content API**: `/api/content/principles`, `/api/content/actions`, `/api/content/stories`

## Contact Info

- **On-Call**: [Contact]
- **DevOps**: [Contact]
- **Security**: [Contact]
- **DB Admin**: [Contact]
