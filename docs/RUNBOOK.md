# Operations Runbook

This runbook provides step-by-step instructions for common operational tasks for The Commons application.

## Table of Contents

- [Quick Start](#quick-start)
- [Service Management](#service-management)
- [Database Operations](#database-operations)
- [Security Operations](#security-operations)
- [Monitoring & Logging](#monitoring--logging)
- [Backup & Recovery](#backup--recovery)
- [Troubleshooting](#troubleshooting)
- [Emergency Procedures](#emergency-procedures)

## Quick Start

### Development Environment

```bash
# Clone and setup
git clone <repository-url>
cd the-commons
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt

# Start backend
cd backend
uvicorn main:app --reload --port 8000

# Start frontend (in another terminal)
cd frontend
npm install
npm run dev
```

### Production Environment

```bash
# Using Docker Compose
docker-compose -f docker-compose.prod.yml up -d

# Check status
docker-compose -f docker-compose.prod.yml ps
```

## Service Management

### Start Services

```bash
# Development
cd backend && uvicorn main:app --reload --port 8000
cd frontend && npm run dev

# Production
docker-compose -f docker-compose.prod.yml up -d
```

### Stop Services

```bash
# Development
# Use Ctrl+C in terminal

# Production
docker-compose -f docker-compose.prod.yml down
```

### Restart Services

```bash
# Development
# Stop and start again

# Production
docker-compose -f docker-compose.prod.yml restart

# Restart specific service
docker-compose -f docker-compose.prod.yml restart backend
```

### Check Service Status

```bash
# Health check
curl http://localhost:8000/health

# Database health
curl http://localhost:8000/health/db

# Redis health
curl http://localhost:8000/health/redis

# Docker services
docker-compose -f docker-compose.prod.yml ps
```

## Database Operations

### Initialize Database

```bash
# Development
cd backend
alembic upgrade head

# Production
docker-compose -f docker-compose.prod.yml exec backend alembic upgrade head
```

### Reset Database

```bash
# Development
cd backend
alembic downgrade base
alembic upgrade head

# Production (WARNING: This will delete all data)
docker-compose -f docker-compose.prod.yml exec backend alembic downgrade base
docker-compose -f docker-compose.prod.yml exec backend alembic upgrade head
```

### Run Migrations

```bash
# Development
cd backend
alembic upgrade head

# Production
docker-compose -f docker-compose.prod.yml exec backend alembic upgrade head
```

### Create Migration

```bash
cd backend
alembic revision --autogenerate -m "Description of changes"
```

## Security Operations

### Rotate JWT Secret

```bash
# Generate new secret
openssl rand -hex 32

# Update environment variable
export SECRET_KEY="new_secret_here"

# Restart services
docker-compose -f docker-compose.prod.yml restart backend
```

### Update Admin Users

```bash
# Set admin usernames (comma-separated)
export ADMIN_USERNAMES="admin1,admin2,admin3"

# Restart services
docker-compose -f docker-compose.prod.yml restart backend
```

### Check Rate Limits

```bash
# View current rate limit settings
grep -r "RATE_LIMIT" backend/config.py

# Adjust rate limits in environment
export RATE_LIMIT_PER_MINUTE=100
```

### CORS Configuration

```bash
# Update allowed origins
export ALLOWED_ORIGINS="https://yourdomain.com,https://app.yourdomain.com"

# Restart services
docker-compose -f docker-compose.prod.yml restart backend
```

## Monitoring & Logging

### Enable Sentry

```bash
# Set Sentry DSN
export SENTRY_DSN="https://your-sentry-dsn@sentry.io/project-id"

# Set environment
export ENVIRONMENT="production"

# Restart services
docker-compose -f docker-compose.prod.yml restart backend
```

### Disable Sentry

```bash
# Unset Sentry DSN
unset SENTRY_DSN

# Restart services
docker-compose -f docker-compose.prod.yml restart backend
```

### View Logs

```bash
# Application logs
docker-compose -f docker-compose.prod.yml logs backend

# Follow logs
docker-compose -f docker-compose.prod.yml logs -f backend

# View specific log file
tail -f logs/app.log

# Search logs
grep "ERROR" logs/app.log
```

### Check Log Levels

```bash
# Set log level
export LOG_LEVEL="DEBUG"  # or INFO, WARNING, ERROR

# Restart services
docker-compose -f docker-compose.prod.yml restart backend
```

## Backup & Recovery

### Create Backup

```bash
# Make script executable
chmod +x scripts/backup_db.sh

# Create backup
./scripts/backup_db.sh

# Backup will be created in backups/YYYY-MM-DD/
```

### Restore from Backup

```bash
# Make script executable
chmod +x scripts/restore_db.sh

# Restore from backup (with confirmation)
./scripts/restore_db.sh backups/2024-01-15

# Restore without confirmation
./scripts/restore_db.sh backups/2024-01-15 --force

# Dry run (see what would be restored)
./scripts/restore_db.sh backups/2024-01-15 --dry-run
```

### Automated Backups

```bash
# Add to crontab for daily backups at 2 AM
crontab -e

# Add this line:
0 2 * * * cd /path/to/the-commons && ./scripts/backup_db.sh >> /var/log/backup.log 2>&1
```

### Clean Old Backups

```bash
# Remove backups older than 30 days
find backups/ -type d -mtime +30 -exec rm -rf {} \;
```

## Data Hygiene

### Run Soft-Delete Sweep

```bash
# Make script executable
chmod +x scripts/sweep_soft_deletes.py

# Dry run (see what would be deleted)
python scripts/sweep_soft_deletes.py --dry-run

# Run sweep with default grace period (30 days)
python scripts/sweep_soft_deletes.py

# Run sweep with custom grace period
python scripts/sweep_soft_deletes.py --grace-days 60

# Verbose output
python scripts/sweep_soft_deletes.py --verbose
```

### Automated Sweep

```bash
# Add to crontab for monthly sweep
crontab -e

# Add this line (first Sunday of each month at 3 AM):
0 3 1-7 * 0 cd /path/to/the-commons && python scripts/sweep_soft_deletes.py >> /var/log/sweep.log 2>&1
```

## Testing

### Run E2E Tests

```bash
# Install Playwright
cd frontend
npx playwright install --with-deps

# Run smoke tests
npx playwright test -g @smoke

# Run all tests
npx playwright test

# Run tests in headed mode
npx playwright test --headed

# Run tests on specific browser
npx playwright test --project=chromium
```

### Run Backend Tests

```bash
# Run all tests
cd backend
pytest

# Run specific test file
pytest tests/test_auth.py

# Run with coverage
pytest --cov=backend

# Run integration tests
pytest tests/integration/
```

## Troubleshooting

### Common Issues

#### Service Won't Start

```bash
# Check logs
docker-compose -f docker-compose.prod.yml logs backend

# Check port conflicts
netstat -tulpn | grep :8000

# Check disk space
df -h

# Check memory
free -h
```

#### Database Connection Issues

```bash
# Check database status
curl http://localhost:8000/health/db

# Check database logs
docker-compose -f docker-compose.prod.yml logs db

# Test database connection
docker-compose -f docker-compose.prod.yml exec backend python -c "
from backend.database import async_session_maker
import asyncio
async def test():
    async with async_session_maker() as session:
        result = await session.execute('SELECT 1')
        print('Database connection OK')
asyncio.run(test())
"
```

#### Redis Connection Issues

```bash
# Check Redis status
curl http://localhost:8000/health/redis

# Check Redis logs
docker-compose -f docker-compose.prod.yml logs redis

# Test Redis connection
docker-compose -f docker-compose.prod.yml exec backend python -c "
from backend.core.redis import get_redis_client
import asyncio
async def test():
    redis = await get_redis_client()
    await redis.ping()
    print('Redis connection OK')
asyncio.run(test())
"
```

#### Frontend Build Issues

```bash
# Clear node modules and reinstall
cd frontend
rm -rf node_modules package-lock.json
npm install

# Clear build cache
npm run build -- --force

# Check for TypeScript errors
npx tsc --noEmit
```

### Performance Issues

```bash
# Check resource usage
docker stats

# Check slow queries
grep "slow" logs/app.log

# Check memory usage
docker-compose -f docker-compose.prod.yml exec backend python -c "
import psutil
print(f'Memory usage: {psutil.virtual_memory().percent}%')
print(f'CPU usage: {psutil.cpu_percent()}%')
"
```

### Rate Limiting Issues

```bash
# Check rate limit logs
grep "rate_limit" logs/app.log

# Temporarily increase limits
export RATE_LIMIT_PER_MINUTE=1000
docker-compose -f docker-compose.prod.yml restart backend

# Check Redis rate limit data
docker-compose -f docker-compose.prod.yml exec redis redis-cli KEYS "*rate_limit*"
```

## Emergency Procedures

### Emergency Rollback

```bash
# Stop all services
docker-compose -f docker-compose.prod.yml down

# Restore from backup
./scripts/restore_db.sh backups/previous-working-backup --force

# Start services
docker-compose -f docker-compose.prod.yml up -d

# Verify health
curl http://localhost:8000/health
```

### Emergency Maintenance Mode

```bash
# Set maintenance environment variable
export MAINTENANCE_MODE=true

# Restart services
docker-compose -f docker-compose.prod.yml restart backend

# Users will see maintenance page
```

### Data Recovery

```bash
# If database is corrupted
docker-compose -f docker-compose.prod.yml stop backend

# Restore from latest backup
./scripts/restore_db.sh backups/$(ls -t backups/ | head -1) --force

# Start services
docker-compose -f docker-compose.prod.yml start backend
```

### Security Incident Response

```bash
# 1. Stop affected services
docker-compose -f docker-compose.prod.yml stop backend

# 2. Rotate secrets
openssl rand -hex 32 > new_secret.txt
export SECRET_KEY=$(cat new_secret.txt)

# 3. Check logs for suspicious activity
grep -i "error\|failed\|unauthorized" logs/app.log

# 4. Restart with new secrets
docker-compose -f docker-compose.prod.yml start backend

# 5. Monitor for continued issues
docker-compose -f docker-compose.prod.yml logs -f backend
```

## Maintenance Schedule

### Daily
- [ ] Check service health
- [ ] Review error logs
- [ ] Monitor resource usage

### Weekly
- [ ] Review backup success
- [ ] Check disk space
- [ ] Update dependencies (if needed)

### Monthly
- [ ] Run soft-delete sweep
- [ ] Review and rotate secrets
- [ ] Update documentation
- [ ] Performance review

### Quarterly
- [ ] Security audit
- [ ] Backup restoration test
- [ ] Disaster recovery drill
- [ ] Capacity planning

## Contact Information

- **On-call Engineer**: [Contact Info]
- **System Administrator**: [Contact Info]
- **Security Team**: [Contact Info]
- **Emergency**: [Emergency Contact]

## Useful Commands Reference

```bash
# Quick health check
curl -f http://localhost:8000/health || echo "Service down"

# Check all environment variables
docker-compose -f docker-compose.prod.yml exec backend env

# View real-time logs
docker-compose -f docker-compose.prod.yml logs -f --tail=100

# Execute command in container
docker-compose -f docker-compose.prod.yml exec backend bash

# Check disk usage
docker system df

# Clean up unused resources
docker system prune -a
```
