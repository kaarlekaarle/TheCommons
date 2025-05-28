# The Commons

The Commons is an open platform for continuous decision-making, where users can dynamically delegate their voting power, vote on issues, and see all actions transparently in a public log. It's not just a voting system—it's a foundation for participatory, trust-based decision models.

For a deeper exploration of the philosophy behind The Commons, see [VISION.md](VISION.md).

## Features

- 🔐 Secure user authentication and authorization
- 🔄 Dynamic delegation system (delegate voting power, revoke anytime)
- 📝 Public activity feed (see who did what, when)
- 🗳️ Robust voting system with integrity checks
- 🚀 High-performance RESTful API
- 🗄️ PostgreSQL database with async support
- 📊 Comprehensive test suite
- 🔄 Database migrations with Alembic
- 🐳 Docker support for easy deployment
- 📝 API documentation with Swagger and ReDoc
- 📈 Structured logging and audit trails

## Project Structure
Detailed architecture in [docs/architecture.md](docs/architecture.md).

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

5. Run the application:
   ```bash
   uvicorn main:app --reload
   ```

6. Access the API documentation:
   - Swagger UI: http://localhost:8000/docs
   - ReDoc: http://localhost:8000/redoc

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
- Run the test suite using pytest:
  ```bash
  pytest
  ```
- The test suite includes unit tests, integration tests, and end-to-end tests.
- Ensure all tests pass before submitting a pull request.

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