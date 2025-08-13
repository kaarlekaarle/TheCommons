# The Commons

The Commons is an open platform for continuous decision-making, where users can dynamically delegate their voting power, vote on issues, and see all actions transparently in a public log. It's not just a voting system—it's a foundation for participatory, trust-based decision models.

For a deeper exploration of the philosophy behind The Commons, see [VISION.md](VISION.md).

## Features

- 🔐 Secure user authentication and authorization
- 🔄 Dynamic delegation system (delegate voting power, revoke anytime)
- 📝 Public activity feed (see who did what, when)
- 🗳️ Robust voting system with integrity checks
- 🏷️ Topic Labels (A↔B connector) - controlled categories linking principles to actions
- 🚀 High-performance RESTful API
- 🗄️ PostgreSQL database with async support
- 📊 Comprehensive test suite
- 🔄 Database migrations with Alembic
- 🐳 Docker support for easy deployment
- 📝 API documentation with Swagger and ReDoc
- 📈 Structured logging and audit trails
- 🔍 Observability with Sentry and structured JSON logs
- 💾 Automated backup and restore system
- 🛡️ Enhanced security with rate limiting and admin audit
- 🧹 Data hygiene with GDPR compliance endpoints
- 🧪 E2E testing with Playwright

## Project Structure
Detailed architecture in [docs/architecture.md](docs/architecture.md).

## Topic Labels (A↔B connector)
Topic Labels serve as connective tissue between Level A (Principles) and Level B (Actions) decisions, enabling:
- **Delegation by topic area** - delegate specific subjects to trusted experts
- **A↔B relationships** - see how immediate actions connect to long-term values  
- **Controlled categorization** - consistent, community-focused topic areas

📖 **Documentation**: [Labels Overview](docs/labels_overview.md) | [Labels Playbook](docs/labels_playbook.md)

## Prerequisites
- Python 3.8 or higher
- Docker and Docker Compose
- Git
- PostgreSQL (if running locally)
- Redis (if running locally)

## Setup
1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/the-commons.git
   cd the-commons
   ```

2. Create a virtual environment and activate it:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows use `venv\\Scripts\\activate`
   ```

3. Install the required packages:
   ```bash
   pip install -r requirements.txt
   ```

4. Create a `.env` file in the project root:
   ```bash
   cp .env.example .env
   ```
   Edit `.env` and set your environment variables:
   - `SECRET_KEY`: Your secret key for JWT tokens
   - `ALGORITHM`: JWT algorithm (default: HS256)
   - `ACCESS_TOKEN_EXPIRE_MINUTES`: Token expiration time
   - `ALLOWED_ORIGINS`: Comma-separated list of allowed origins
   - `LEVEL_A_ENABLED`: Enable Level A decisions (default: true)
   - `USE_DEMO_CONTENT`: Use demo content instead of file-based content (default: false)
   - `CONTENT_DATA_DIR`: Directory for content files (default: ./data/real_content)

5. Run the application:
   ```bash
   uvicorn main:app --reload
   ```

6. Access the API documentation:
   - Swagger UI: http://localhost:8000/docs
   - ReDoc: http://localhost:8000/redoc

7. Test the content API:
   ```bash
   # Get principles (Level A content)
   curl http://localhost:8000/api/content/principles
   
   # Get actions (Level B content)
   curl http://localhost:8000/api/content/actions
   
   # Get stories (case studies)
   curl http://localhost:8000/api/content/stories
   ```

## Development

To set up the development environment:

1. Create a virtual environment and activate it:
   ```bash
   python -m venv venv && source venv/bin/activate
   ```

2. Install development dependencies:
   ```bash
   pip install -U pip && pip install -r requirements-dev.txt
   ```

3. Run tests:
   ```bash
   pytest -q
   ```

## Content Pipeline

The Commons includes a flexible content pipeline that allows you to serve real community data instead of demo content. This system is feature-flagged and can be easily switched between demo and real data sources.

### Content Types
- **Principles** (Level A): Long-term baseline policies and values
- **Actions** (Level B): Specific proposals and initiatives  
- **Stories**: Case studies and success stories for the landing page

### Configuration
```bash
# Backend
USE_DEMO_CONTENT=false                    # Default: false (use real data)
CONTENT_DATA_DIR=./data/real_content     # Default: ./data/real_content

# Frontend
VITE_USE_DEMO_CONTENT=false              # Default: false (use real data)
```

### Adding Real Data
1. Replace the sample files in `data/real_content/` with your municipal data
2. Follow the JSON schema documented in `docs/content-pipeline.md`
3. Test the API endpoints to verify your content loads correctly

For detailed documentation, see [Content Pipeline Guide](docs/content-pipeline.md).

## Two-Level Decision Model

The Commons implements a two-level decision model for proposals:

### Level A (Baseline Policy)
- **Purpose**: High-level, slow-changing principles that are rarely updated
- **Example**: "Environmental Policy", "Transportation Safety"
- **Voting**: Establishes direction for future Level B decisions
- **Feature Flag**: Controlled by `LEVEL_A_ENABLED` environment variable

### Level B (Poll)
- **Purpose**: Quick action on specific issues
- **Voting**: Yes/No/Abstain on concrete proposals
- **Example**: "Should we install solar panels on the community center?"

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `LEVEL_A_ENABLED` | Enable Level A decisions | `true` |
| `VITE_LEVEL_A_ENABLED` | Frontend Level A feature flag | `true` |

### Data Backfill

After deploying the two-level model, run the backfill script to ensure data consistency:

```bash
# Backend
make backfill-decisions

# Or manually
cd backend && python scripts/backfill_decision_type.py
```

This script:
- Sets `decision_type="level_b"` where NULL
- Sets `direction_choice=NULL` for Level B polls
- Logs any corrections made

### Demo Data / Direction Presets

The Commons uses standardized Level-A direction categories. To modify these presets:

1. **Frontend Configuration**: Edit `frontend/src/config/levelA.ts`
   - Add/remove categories from `LEVEL_A_PRESETS`
   - Categories are used in proposal creation and display

2. **Cleanup Old Data**: If you have old demo direction strings, run:
   ```bash
   # Preview changes (dry run)
   make fix-old-directions
   
   # Apply changes
   make fix-old-directions FORCE=1
   
   # Or wipe all Level-A demo data
   cd backend && python scripts/cleanup_old_directions.py --wipe-level-a --force
   ```

3. **Clear Frontend Cache**: If you see stale data in the browser:
   ```bash
   # Clear localStorage and reload
   npm run clear-local
   # Then hard refresh your browser (Ctrl+F5 / Cmd+Shift+R)
   ```
   
   Or use the Debug Overlay (when `VITE_DEBUG_OVERLAY=true`):
   - Click the "D" button in the top-right corner
   - Click "Clear Local Storage" button

### Migration Safety

**Upgrade**: The migration adds new columns with defaults, so it's safe to run on existing data.

**Rollback**: To rollback the migration:
```bash
# Downgrade the migration
alembic downgrade -1

# The backfill script can be run again after re-upgrading
```

## Observability

The Commons includes comprehensive observability features for monitoring and debugging:

### Sentry Integration

Sentry is automatically initialized if a DSN is provided:

```bash
# Backend
export SENTRY_DSN="https://your-sentry-dsn@sentry.io/project-id"
export ENVIRONMENT="production"
export SENTRY_TRACES_SAMPLE_RATE="0.1"

# Frontend
export VITE_SENTRY_DSN="https://your-sentry-dsn@sentry.io/project-id"
export VITE_ENVIRONMENT="production"
```

### Structured JSON Logging

All logs are structured JSON with request context:

```json
{
  "timestamp": "2024-01-15T10:30:00.000Z",
  "level": "info",
  "message": "Request completed",
  "request_id": "uuid-here",
  "method": "POST",
  "path": "/api/token",
  "status_code": 200,
  "response_time_ms": 45.2,
  "user_id": "user-uuid",
  "service": "the-commons-api"
}
```

### Request ID Tracking

Every request gets a unique ID that's included in:
- Response headers (`X-Request-ID`)
- All log entries
- Error reports

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `SENTRY_DSN` | Sentry DSN for error tracking | None |
| `ENVIRONMENT` | Environment name | `dev` |
| `LOG_LEVEL` | Logging level | `INFO` |
| `SENTRY_TRACES_SAMPLE_RATE` | Sentry trace sampling rate | `0.1` |

### Verifying Observability

1. **Check logs are structured**:
   ```bash
   curl http://localhost:8000/health
   # Check logs show JSON format with request_id
   ```

2. **Test Sentry integration**:
   ```bash
   # Trigger an error (if Sentry is configured)
   curl http://localhost:8000/nonexistent
   # Check Sentry dashboard for error
   ```

3. **Verify request ID tracking**:
   ```bash
   curl -H "X-Request-ID: test-123" http://localhost:8000/health
   # Response should include X-Request-ID header
   ```

## Docker Setup

### Prerequisites
- Docker and Docker Compose installed
- Git (to clone the repository)

### Quick Start
1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/the-commons.git
   cd the-commons
   ```

2. Create a `.env` file in the project root:
   ```bash
   cp .env.example .env
   ```
   Edit `.env` and set your environment variables:
   - `SECRET_KEY`: Your secret key for JWT tokens
   - `ALGORITHM`: JWT algorithm (default: HS256)
   - `ACCESS_TOKEN_EXPIRE_MINUTES`: Token expiration time
   - `ALLOWED_ORIGINS`: Comma-separated list of allowed origins

3. Build and start the services:
   ```bash
   docker-compose up --build
   ```
   This will start:
   - FastAPI application on http://localhost:8000
   - PostgreSQL database on localhost:5432
   - Redis server on localhost:6379
   - Load testing interface on http://localhost:8089 (optional)

4. Access the API documentation:
   - Swagger UI: http://localhost:8000/docs
   - ReDoc: http://localhost:8000/redoc

### Development with Docker
- The application code is mounted as a volume, so changes are reflected immediately
- Logs are available in the `logs` directory
- Database data persists in Docker volumes
- Redis data persists in Docker volumes

### Stopping the Services
```bash
docker-compose down
```
To remove all data (including database and Redis):
```bash
docker-compose down -v
```

### Troubleshooting
1. If the application fails to start:
   ```bash
   docker-compose logs web
   ```

2. If the database connection fails:
   ```bash
   docker-compose logs db
   ```

3. If Redis connection fails:
   ```bash
   docker-compose logs redis
   ```

4. To check service health:
   ```bash
   curl http://localhost:8000/health
   ```

## Testing

### Quick Start

**Local Backend Tests (Recommended)**
```bash
cd backend
make test
```

This runs the full test suite with SQLite database and no external services (Redis/PostgreSQL).

### Testing Options

**Online (normal)**
```bash
make dev-deps
make test
```

**Offline / Sandboxed (e.g., Codex)**
1. Pre-build and commit wheels once (do this locally with internet):
```bash
python3 -m pip install --upgrade pip wheel build
mkdir -p tools/offline_wheels
pip wheel --wheel-dir tools/offline_wheels -r requirements-dev.txt
git add tools/offline_wheels
git commit -m "chore: vendor test wheels for offline runs"
```

2. In offline environments:
```bash
make offline-deps
make test
```

**Dockerized tests (alternative)**
```bash
make test-docker
```

### Backend Tests

**Makefile Targets (in backend/)**
- `make test`: Full pytest run with proper test environment
- `make test-fast`: Fast tests only (excludes slow tests)
- `make clean-testdb`: Remove test database file
- `make cov`: Run tests with coverage report

**Manual Test Run**
```bash
cd backend
python -m pip install -r requirements-test.txt
TESTING=true SECRET_KEY="test-secret-key-for-testing-only" USE_DEMO_CONTENT=false CONTENT_DATA_DIR="../data/real_content" pytest
```

**Test Environment**
- Uses SQLite in-memory database (no PostgreSQL required)
- Rate limiting disabled (no Redis required)
- Test-specific secret key and content settings
- All external services mocked or disabled

**Offline Test Suite**

The project includes a comprehensive offline, self-contained test suite that runs without network or real Redis:

- **Rate Limiting Tests** (`tests/test_rate_limit.py`): Tests rate limiting with fake Redis and fallback behavior
- **WebSocket Manager Tests** (`tests/test_websocket_manager.py`): Tests WebSocket room broadcasting and connection management
- **Soft Delete Visibility Tests** (`tests/test_soft_delete.py`): Tests that soft deleted records are properly excluded from queries
- **Delegation Chain Safety Tests** (`tests/test_delegation_chain.py`): Tests delegation chain resolution and cycle detection

All tests use in-memory SQLite and fake Redis for fast, deterministic execution.

### E2E Tests

Install and run Playwright tests:
```bash
cd frontend
npm install
npx playwright install --with-deps
npx playwright test
```

Run smoke tests only:
```bash
npx playwright test -g @smoke
```

The test suite includes unit tests, integration tests, and end-to-end tests.
Ensure all tests pass before submitting a pull request.

## Data Management

### Backup & Restore

Create a backup:
```bash
chmod +x scripts/backup_db.sh
./scripts/backup_db.sh
```

Restore from backup:
```bash
chmod +x scripts/restore_db.sh
./scripts/restore_db.sh backups/2024-01-15
```

### Data Hygiene

Run soft-delete sweep:
```bash
chmod +x scripts/sweep_soft_deletes.py
python scripts/sweep_soft_deletes.py --dry-run  # See what would be deleted
python scripts/sweep_soft_deletes.py            # Actually delete
```

### GDPR Compliance

Export user data:
```bash
curl -H "Authorization: Bearer <token>" http://localhost:8000/api/users/me/export
```

Delete user account (Right to be Forgotten):
```bash
curl -X DELETE -H "Authorization: Bearer <token>" http://localhost:8000/api/users/me
```

## Operations

For comprehensive operational procedures, see [docs/RUNBOOK.md](docs/RUNBOOK.md).

Key operational tasks:
- [Backup & Restore Guide](docs/BACKUP_RESTORE.md)
- [Operations Runbook](docs/RUNBOOK.md)
- [Architecture Documentation](docs/architecture.md)

## Rate Limiting

The application includes configurable rate limiting with automatic fallback:

### Configuration

- `RATE_LIMIT_ENABLED=true|false` (default: `true`) - Enable/disable rate limiting
- `REDIS_URL` - Redis connection URL (required for rate limiting)

### Behavior

- **With Redis**: Rate limiting is enforced (5 requests/minute on `/api/token`)
- **Without Redis**: Automatic fallback to no-op mode (no rate limiting)
- **Disabled**: Set `RATE_LIMIT_ENABLED=false` to disable completely

### Health Check

Check rate limiter status (admin only):
```bash
curl -H "Authorization: Bearer <admin_token>" http://localhost:8000/api/limiter/health
```

Response:
```json
{
  "enabled": true,
  "backend": "redis"
}
```

### Fallback Scenarios

1. **Redis unavailable**: Rate limiting gracefully falls back to no-op
2. **Dependencies missing**: Application continues without rate limiting
3. **Configuration error**: Logs warning and continues operation

## API Documentation
- Access the API documentation at:
  - Swagger UI: http://localhost:8000/docs
  - ReDoc: http://localhost:8000/redoc
- The API supports RESTful endpoints for user management, voting, and delegation.
- Authentication is required for most endpoints using JWT tokens.

## Development Guidelines
- Follow the PEP 8 style guide for Python code.
- Use meaningful variable and function names.
- Write comments and docstrings for complex logic.
- Create a new branch for each feature or bug fix.
- Submit pull requests with a clear description of changes.

## Contributing

We welcome contributors of all skill levels! See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines, or ask questions in our community chat.

Join the discussion on Discord: [your-discord-invite-link]

## License

MIT License - see [LICENSE](LICENSE) for details.