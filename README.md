# The Commons

A modern, secure, and scalable voting system built with FastAPI and SQLAlchemy. The Commons provides a robust platform for conducting polls and votes with strong security measures, comprehensive testing, and detailed audit trails.

## Features

- 🔐 Secure user authentication and authorization
- 🗳️ Robust voting system with integrity checks
- 🚀 High-performance RESTful API
- 🗄️ PostgreSQL database with async support
- 📊 Comprehensive test suite with load testing
- 🔄 Database migrations with Alembic
- 🐳 Docker support for easy deployment
- 📝 API documentation with Swagger and ReDoc
- 📈 Structured logging and audit trails
- 🔍 Request context tracking
- 🛡️ Security logging and monitoring

## Project Structure

```
the-commons/
├── backend/                 # Main application code
│   ├── api/                # API endpoints
│   ├── core/               # Core functionality
│   ├── models/             # Database models
│   ├── schemas/            # Pydantic schemas
│   ├── services/           # Business logic
│   └── utils/              # Utility functions
├── tests/                  # Test suite
│   ├── api/               # API tests
│   ├── services/          # Service tests
│   └── load/              # Load tests
├── migrations/             # Database migrations
├── scripts/               # Utility scripts
├── logs/                  # Application logs
└── docker-compose.yml     # Docker configuration
```

## Prerequisites

- Python 3.10+
- PostgreSQL 12+
- Redis 6+
- Docker and Docker Compose (optional)

## Setup

### Local Development

1. Clone the repository:
```bash
git clone https://github.com/kaarlehurtig/the-commons.git
cd the-commons
```

2. Create and activate a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
pip install -r backend/requirements-test.txt
```

4. Set up environment variables:
   - Copy `.env.example` to `.env`
   - Update the following variables in `.env`:
     ```
     DATABASE_URL=postgresql+asyncpg://postgres:TheCommons123@localhost:5432/the_commons
     REDIS_URL=redis://localhost:6379/0
     SECRET_KEY=your-secret-key
     POSTGRES_PASSWORD=TheCommons123
     ```

5. Initialize the database:
```bash
alembic upgrade head
```

6. Run the application:
```bash
uvicorn backend.main:app --reload
```

### Docker Setup

1. Build and start the containers:
```bash
docker-compose up --build
```

2. The application will be available at http://localhost:8000

## Testing

The project includes a comprehensive test suite:

1. Run all tests:
```bash
pytest
```

2. Run specific test categories:
```bash
pytest tests/api/          # API tests
pytest tests/services/     # Service tests
pytest tests/load/         # Load tests
```

3. Run with coverage:
```bash
pytest --cov=backend
```

## API Documentation

Once the server is running, access the API documentation:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## Development Guidelines

1. **Code Style**
   - Follow PEP 8 guidelines
   - Use type hints
   - Write docstrings for all functions and classes
   - Use pre-commit hooks for code quality

2. **Testing**
   - Write tests for new features
   - Maintain test coverage
   - Run tests before committing
   - Include load tests for performance-critical features

3. **Database**
   - Use Alembic for all database changes
   - Write migration scripts for schema changes
   - Test migrations before deployment
   - Use async SQLAlchemy for database operations

4. **Security**
   - Never commit sensitive data
   - Use environment variables for secrets
   - Follow security best practices
   - Implement proper audit logging

5. **Logging**
   - Use structured logging
   - Include request context
   - Log security-relevant events
   - Maintain audit trails

## Contributing

Please read [CONTRIBUTING.md](CONTRIBUTING.md) for details on our code of conduct and the process for submitting pull requests.

## License

MIT License - see [LICENSE](LICENSE) file for details